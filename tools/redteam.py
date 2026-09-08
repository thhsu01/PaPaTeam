#!/usr/bin/env python3
"""刻意把倉庫改壞，確認檢查器真的會紅。

為什麼要有這支：本專案的規矩是「檢查器先行、刻意紅字」——加一條規則之前，先讓它在真頁面上
紅一次。但那個動作一直是一次性的手工步驟，做完就沒了，於是規則**後來**壞掉時沒有人會發現。
2026-09 的第四輪審查抓到兩條規則已經紅不起來：

  - fact_check 的總里程只認 meta 裡的「全程 N 公里」，而 nangangshan 寫的是「單程」，
    於是那一頁的里程整段不受核對——把它改成 9.91 公里，全站照樣全綠。
  - spec_sweep 的「isPeak 跟預設一樣」是字面字串比對，`isPeak: (wp) => …` 多一對括號就穿過去。

兩條都是「規則還在，但已經對不到任何東西」。這支腳本把每條規則配一個最小的改壞動作，
在一份暫時的倉庫副本上跑（PAPA_ROOT 指過去），要求檢查器回傳非零且訊息裡出現預期的字。
規則之後被改窄、被繞開、或整條刪掉，這裡就會紅。

用法：python3 tools/redteam.py          全部跑一次
      python3 tools/redteam.py 行內      只跑名稱含「行內」的案例
新增規則時一併在 CASES 加一列——那一列就是這條規則的測試面。
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from papa_common import chdir_root
chdir_root()
ROOT = os.getcwd()

# (名稱, 檔案, 原文, 改成, 哪支檢查器, 訊息裡該出現的字)
# 原文用「這一刻真的在檔案裡」的字串；找不到就算失敗——那通常代表頁面改了而測試沒跟上。
CASES = [
    ('段落數量',   'hushan.html', '</main>', '<section id="extra"></section></main>',
     'spec_sweep', '段落 id、順序或數量異常'),
    ('title 格式', 'hushan.html', '<title>虎山親山步道 — 爬爬小隊</title>',
     '<title>虎山親山步道 - 爬爬小隊</title>', 'spec_sweep', '<title> 格式'),
    ('meta 必填',  'hushan.html', '<meta name="description"', '<meta name="x-description"',
     'spec_sweep', '缺 <meta name="description">'),
    ('首頁 meta',  'index.html', '<meta name="description"', '<meta name="x-description"',
     'spec_sweep', '缺 <meta name="description">'),
    ('頁內函式',   'hushan.html', "PaPaDetail.cssVar('--accent')",
     "getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()",
     'spec_sweep', '頁面自己呼叫 getComputedStyle'),
    ('detail.css 的 class', 'hushan.html', '</style>', '.stamp { color: red; }\n</style>',
     'spec_sweep', '已收進 detail.css'),
    ('行內主色',   'hushan.html', '<main id="main-content"',
     '<main style="color:var(--accent-strong);" id="main-content"',
     'spec_sweep', '行內 style 在寫 --accent'),
    ('死 token',   'hushan.html', ':root {', ':root {\n      --accent-nobody-reads: #123456;',
     'spec_sweep', '定義了卻沒人讀'),
    ('未知設定鍵', 'hushan.html', '      map: {', "      map: { attribution: 'x',",
     'spec_sweep', '不是 detail.js 認得的設定'),
    ('palette 選項', 'hushan.html', 'PaPaDetail.palette({ accent: ACCENT',
     "PaPaDetail.palette({ accent: ACCENT, peak: '#000000'",
     'spec_sweep', '不是 palette() 認得的選項'),
    # 括號那種寫法是 2026-09 第四輪抓到的漏洞：字面比對版會全綠
    ('多餘 isPeak', 'caolingguidao.html', 'PaPaDetail.palette({ accent: ACCENT',
     'PaPaDetail.palette({ accent: ACCENT, isPeak: (wp) => wp.pos === "最高點"',
     'spec_sweep', 'isPeak 跟預設一樣'),
    ('事實槽格式', 'hushan.html', 'data-trip="duration:zh"', 'data-trip="duration:zzz"',
     'spec_sweep', '沒有「zzz」這種格式'),
    ('掃載點',     'hushan.html', 'data-widget="notice"', 'data-widget="notice-x"',
     'spec_sweep', 'detail.js 沒有這個共用區塊'),
    ('手寫共用區塊', 'hushan.html', '<main id="main-content"',
     '<main id="wp-pos-label"><span id="main-content">',
     'spec_sweep', '是 detail.js 產生的'),
    # 多一個 0 仍是合法的十六進位，只是對不上內容雜湊
    ('資產版本號', 'hushan.html', 'assets/detail.js?v=', 'assets/detail.js?v=0',
     'spec_sweep', '版本號不是現在的內容'),
    ('首頁版本號', 'index.html', 'assets/site.js?v=', 'assets/site.js?v=0',
     'spec_sweep', '版本號不是現在的內容'),
    # 帶別的查詢參數：第一版的樣式整段比對不上，等於沒看見
    ('資產版本號雜訊', 'hushan.html', 'assets/detail.js?v=', 'assets/detail.js?x=1&v=',
     'spec_sweep', '版本號不是現在的內容'),
    ('manifest 條目', 'manifest.json', '"path": "tools/spec_sweep.py"', '"path": "tools/spec_sweep_x.py"',
     'spec_sweep', '倉庫有 tools/spec_sweep.py'),
    ('manifest status', 'manifest.json', '"title": "虎山親山步道",\n      "status": "completed"',
     '"title": "虎山親山步道",\n      "status": "candidate"',
     'spec_sweep', 'status 是 candidate，但有軌跡檔'),
    ('README 檔案樹', 'README.md', '├── index.html', '├── index-x.html',
     'spec_sweep', 'README.md 的檔案樹跟 manifest.json 不一致'),
    ('文件數量',   'ARCHITECTURE.md', '// 卡片式，6 頁', '// 卡片式，7 頁',
     'spec_sweep', '卡片式的頁數'),
    ('ADR 數量',   'docs/adr/0001-chartjs-behind-the-seam.md', '目前 22 頁都沒用到它',
     '目前 21 頁都沒用到它', 'spec_sweep', 'advanced 未使用的頁數'),
    ('山頂綠',     'assets/detail.js', "PEAK = '#7c9e52'", "PEAK = '#000000'",
     'spec_sweep', '山頂綠'),
    # ── fact_check ──────────────────────────────────────────
    ('meta 日期',  'hushan.html', 'content="2024/4/20', 'content="2024/4/21',
     'fact_check', '日期不一致'),
    ('meta 里程（全程）', 'hushan.html', '全程 4.35 公里', '全程 4.36 公里',
     'fact_check', '總里程不一致'),
    # nangangshan 寫的是「單程」，第一版的樣式認不出來，整頁里程等於沒查
    ('meta 里程（單程）', 'nangangshan.html', '單程 7.91 公里', '單程 9.91 公里',
     'fact_check', '總里程不一致'),
    ('散文時長',   'daluntouweishan.html', '全程 3 小時 44 分', '全程 3 小時 45 分',
     'fact_check', '行程時長不一致'),
    ('散文最高點', 'daqitou.html', '全程最高點，標高 523 公尺，士林', '全程最高點，標高 525 公尺，士林',
     'fact_check', '改用 data-trip="summit"'),
    ('航點標高',   'daqitou.html', 'loc: "鵝尾山 (H523m)"', 'loc: "鵝尾山 (H524m)"',
     'fact_check', '的名稱寫 524 m'),
    ('散文行程日', 'hushan.html', '<main id="main-content"', '<main id="main-content"><p>4/20 當天</p>',
     'fact_check', '手打的行程日'),
    ('軌跡檔存在', 'hushan.html', 'date: "2024-04-20"', 'date: "2024-04-21"',
     'fact_check', '找不到軌跡檔'),
]


def run(tool, root):
    r = subprocess.run([sys.executable, os.path.join(root, 'tools', tool + '.py')],
                       capture_output=True, text=True, env=dict(os.environ, PAPA_ROOT=root))
    return r.returncode, r.stdout + r.stderr


def main():
    only = [a for a in sys.argv[1:] if not a.startswith('-')]
    cases = [c for c in CASES if not only or any(o in c[0] for o in only)]
    tmp = tempfile.mkdtemp(prefix='papa-redteam-')
    work = os.path.join(tmp, 'repo')
    shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__'))

    # 先確認乾淨的副本是綠的，否則後面每一條都會「紅」而說明不了什麼
    bad = 0
    for tool in ('spec_sweep', 'fact_check'):
        code, out = run(tool, work)
        if code != 0:
            print('✗ 乾淨的副本 %s 就不是綠的，先修那個：\n%s' % (tool, out.strip()[-600:]))
            return 2

    for name, path, old, new, tool, want in cases:
        f = os.path.join(work, path)
        s = open(f, encoding='utf-8').read()
        if old not in s:
            print('%-16s ✗ 找不到要改壞的字串（頁面變了？）：%s' % (name, old[:40]))
            bad += 1
            continue
        open(f, 'w', encoding='utf-8').write(s.replace(old, new, 1))
        code, out = run(tool, work)
        open(f, 'w', encoding='utf-8').write(s)               # 立刻還原，案例之間不互相影響
        if code == 0:
            print('%-16s ✗ %s 沒有紅——這條規則已經抓不到它該抓的東西' % (name, tool))
            bad += 1
        elif want not in out:
            print('%-16s ✗ %s 紅了，但訊息不是預期的「%s」' % (name, tool, want))
            bad += 1
        else:
            print('%-16s ✓ %s 紅了' % (name, tool))

    shutil.rmtree(tmp, ignore_errors=True)
    print('\n%d 條規則，抓不到的 %d 條' % (len(cases), bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
