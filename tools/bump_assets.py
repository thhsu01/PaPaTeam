#!/usr/bin/env python3
"""把共用資產的 URL 換成帶內容雜湊的版本：assets/detail.js → assets/detail.js?v=1a2b3c4d。

為什麼要有這支：2026-09 把導覽列等六個區塊收進 detail.js 之後，頁面骨架開始依賴
JS 的版本。HTML 與 JS 各自快取——正式站換了新版 HTML（導覽列只剩空的掃載點），
瀏覽器或 GitHub Pages 的邊緣快取卻還拿著舊版 detail.js（沒有 WIDGETS），
站徽與回首頁的連結就整個不見。這是實際發生過的事。

雜湊跟著內容走：改了任何一支共用檔就跑一次本工具，23 頁（含首頁）的 URL 一起換，
新 URL 必然抓到新檔。忘了跑會被 spec_sweep 擋下來——它用同一個 asset_hash()。

用法：python3 tools/bump_assets.py          改寫所有頁面
      python3 tools/bump_assets.py --check  只報告哪些頁面過期（spec_sweep 用的就是這個）"""
import hashlib, re, glob, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from papa_common import chdir_root
chdir_root()

ASSETS = ['assets/site.css', 'assets/detail.css', 'assets/site.js', 'assets/detail.js']
REF = re.compile(r'(assets/(?:site|detail)\.(?:css|js))(?:\?v=[0-9a-f]*)?(?=")')


def asset_hash(path):
    return hashlib.sha1(open(path, 'rb').read()).hexdigest()[:8]


def stale(s, hashes):
    """回傳頁面裡版本不對的資產清單。沒帶 ?v= 算過期，帶了別的查詢字串也算。

    尾巴用 [^"]* 收乾淨是刻意的：第一版寫成 `(\\?v=([0-9a-f]*))?"`，於是
    `?v=deadbeef&x=1a2b3c4d` 這種帶別的參數的寫法整段比對不上、直接沒被看見
    ——那正是這條規則要擋的東西（2026-09 第四輪的注入測試發現）。
    也因此只認 href=／src= 裡的引用：散文與註解裡提到檔名（「見 assets/detail.css 的…」）
    不是引用，而收乾淨的尾巴會一路吃到下一個引號。"""
    bad = []
    for m in re.finditer(r'(?:href|src)="(assets/(?:site|detail)\.(?:css|js))([^"]*)"', s):
        path, tail = m.group(1), m.group(2)
        if path in hashes and tail != '?v=' + hashes[path]:
            bad.append(path)
    return bad


def main():
    hashes = {a: asset_hash(a) for a in ASSETS if os.path.exists(a)}
    check = '--check' in sys.argv
    pages = sorted(glob.glob('*.html'))
    n = 0
    for p in pages:
        s = open(p, encoding='utf-8').read()
        old = stale(s, hashes)
        if not old:
            continue
        if check:
            print('%-16s 過期：%s' % (p[:-5], '、'.join(old)))
            n += 1
            continue
        s2 = REF.sub(lambda m: '%s?v=%s' % (m.group(1), hashes[m.group(1)]) if m.group(1) in hashes else m.group(0), s)
        open(p, 'w', encoding='utf-8').write(s2)
        print('%-16s 更新：%s' % (p[:-5], '、'.join(old)))
        n += 1
    print('\n%d 頁%s' % (n, '過期' if check else '已更新'))
    return 1 if (check and n) else 0


if __name__ == '__main__':
    sys.exit(main())
