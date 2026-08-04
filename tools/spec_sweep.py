#!/usr/bin/env python3
"""全站規格掃描。ARCHITECTURE.md 的段落規格表寫了卻沒人檢查，導覽文字與 <h2>
因此長期漂移（2026-08-04 的雙軸審查才發現）。這支腳本把那張表變成可執行的檢查。"""
import re, glob, math, sys, os

os.chdir(os.environ.get('PAPA_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SECTIONS = ['overview', 'map-section', 'elevation', 'spots', 'timeline']
NAV = {'overview': '行程總覽', 'map-section': '路線圖', 'elevation': '海拔剖面',
       'spots': '景點介紹'}
NAV_TIMELINE = {'預估進度', '實走紀錄'}          # 規格表：二選一
H2 = {'map-section': '互動路線圖', 'elevation': '海拔高度剖面圖'}
H2_TIMELINE = ('預計行程進度', '實走時間軸')     # 主詞須為其一，容許括號後綴
SLATE_HEX = ('#f8fafc', '#334155', '#e2e8f0', '#f1f5f9', '#64748b')
PEAK = '#7c9e52'


def hav(a, b, c, d):
    R = 6371000.0
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def schedule_objects(s):
    """以括號配對切出 schedule 的每個物件。用貪婪 regex 會跨物件吃字元，
    2026-08-03 就是這樣漏讀了 nanshijiao 17 個航點裡的 3 個。"""
    i = s.find('const schedule')
    if i < 0:
        return []
    i = s.index('[', i)
    depth, out, cur = 0, [], None
    for j in range(i, len(s)):
        ch = s[j]
        if ch == '{':
            if depth == 0:
                cur = j
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                out.append(s[cur:j + 1])
        elif ch == ']' and depth == 0:
            break
    return out


def js_block(s, key):
    """切出 `key` 後面第一個大括號區塊（含巢狀）。同樣不用 regex——
    marker 與 timeline 的區塊裡有巢狀物件與三元運算，貪婪比對會吃過頭。"""
    i = s.find(key)
    if i < 0:
        return None
    j = s.find('{', i)
    if j < 0:
        return None
    depth = 0
    for k in range(j, len(s)):
        if s[k] == '{':
            depth += 1
        elif s[k] == '}':
            depth -= 1
            if depth == 0:
                return s[j:k + 1]
    return None


def h2_of(s, sec):
    i = s.find('id="%s"' % sec)
    j = s.find('</h2>', i)
    if i < 0 or j < i:
        return None
    m = re.search(r'</span>\s*([^<\n]+)', s[i:j])
    return m.group(1).strip() if m else None


def check(f):
    s = open(f, encoding='utf-8').read()
    p = []

    # ── 結構 ────────────────────────────────────────────────
    if [x for x in re.findall(r'<section[^>]*id="([a-z-]+)"', s) if x in SECTIONS] != SECTIONS:
        p.append('段落 id 或順序異常')
    for need, why in (('wp-pos-label', ''), ('wp-advice', ''), ('elevation-chart', ''),
                      ('爬爬小隊首頁', '站徽 aria-label')):
        if need not in s:
            p.append('缺 %s%s' % (need, why and '（%s）' % why))
    if re.search(r'返回首頁|←\s*首頁', s):
        p.append('疑似左上返回鍵')

    # ── 導覽鍵文字（規格表）─────────────────────────────────
    for sec, want in NAV.items():
        if 'aria-label="滾動到%s"' % want not in s:
            p.append('導覽鍵文字：%s 應為「%s」' % (sec, want))
    tl = re.findall(r'aria-label="滾動到([^"]+)"', s)
    tl = [x for x in tl if x not in NAV.values()]
    if len(tl) != 1 or tl[0] not in NAV_TIMELINE:
        p.append('導覽第 5 鍵 %s，規格只允許 %s' % (tl or '缺', '／'.join(sorted(NAV_TIMELINE))))

    # ── <h2> 主詞（容許括號後綴）───────────────────────────
    for sec, want in H2.items():
        h = h2_of(s, sec)
        if h is None or not h.startswith(want):
            p.append('#%s 的 h2「%s」主詞應為「%s」' % (sec, h, want))
    h = h2_of(s, 'timeline')
    if h is None or not h.startswith(H2_TIMELINE):
        p.append('#timeline 的 h2「%s」主詞應為 %s 之一' % (h, '／'.join(H2_TIMELINE)))

    # ── 灰階（先剝註解：dinghu 的 slate 只在說明遷移的註解裡）─
    code = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.S)
    code = re.sub(r'(?m)(?<!:)//.*$', '', code)   # 行尾註解也要剝；(?<!:) 保住 https://
    for hexv in SLATE_HEX:
        if hexv in code.lower():
            p.append('slate 色值 %s' % hexv)
    if re.search(r'\bslate-\d', code):
        p.append('slate class')

    # ── 語意色：最高點一律 #7c9e52 ─────────────────────────
    # 用 PaPaDetail.palette() 的頁面，顏色來自 detail.js 的預設（由 check_shared()
    # 把關），此處只查有沒有覆寫成別的顏色；沒用 palette() 的頁面才逐處查三元運算。
    for m in re.finditer(r'palette\(\{([^}]*)\}', s):
        ov = re.search(r'peak:\s*[\'"]?(#[0-9a-fA-F]{6})', m.group(1))
        if ov and ov.group(1).lower() != PEAK:
            p.append('palette() 把最高點覆寫成 %s，應為 %s' % (ov.group(1), PEAK))
    if 'PaPaDetail.palette(' not in s:
        for m in re.finditer(r'最高點"?\s*\?\s*([^\s:,]+)', s):
            v = m.group(1).strip("'\"")
            if v.startswith('#') and v.lower() != PEAK:
                p.append('最高點語意色 %s，應為 %s' % (v, PEAK))
            if v.startswith('bg-') and 'peak' not in v:
                p.append('最高點用了 %s，應為山頂綠' % v)

    # 上面那條只認「最高點 ? 顏色」的字面寫法，會漏掉用變數表達的頁面。
    # 2026-08-04 抓到五頁就是這樣溜過去的：它們寫 `isPeak ? HIGH`，而 isPeak 的定義
    # 其實是 `wp.ele >= 950`——依海拔高低帶上色，山頂只是剛好落在高帶，
    # 等於整頁沒有標示山頂，而 isPeak 這個名字掩蓋了這件事。
    # 所以改查結果而非寫法：航點著色邏輯裡必須真的出現山頂綠。
    script = s[s.find('const schedule'):] if 'const schedule' in s else s
    if 'PaPaDetail.palette(' not in script and PEAK not in script.lower() and 'peak-dot' not in script:
        p.append('航點著色看不到山頂綠 %s——山頂在圖上與其他點沒有區別' % PEAK)

    # ── 三個介面必須共用同一個航點配色 ───────────────────────
    # manifest 的 waypoint_palette 寫著「地圖標記、圖表資料點、時間軸圓點一律走
    # PaPaDetail.palette」。2026-08-04 量下來只有圖表 18/18，地圖與時間軸各 6/18——
    # 規約寫了但沒有檢查，於是同一頁的最高點在海拔圖上是綠、在地圖與時間軸上是琥珀。
    # 「宣告了 PAL」不算數，要真的用在那個介面上，所以逐區塊查。
    for key, label in (('chart:', '海拔圖'), ('marker:', '地圖標記'), ('timeline:', '時間軸')):
        blk = js_block(s, key)
        if blk is not None and 'PAL' not in blk and 'palette' not in blk:
            p.append('%s 沒有走 palette()——同一個航點會在不同介面上是不同顏色' % label)

    # ── overview 統計列必須看得到總里程 ─────────────────────
    if not re.search(r'(實走里程|總里程|里程 km)', s):
        p.append('overview 看不到總里程')

    # ── 航點資料 ────────────────────────────────────────────
    wps = []
    for o in schedule_objects(s):
        g = lambda k, pat: (lambda m: m.group(1) if m else None)(re.search(k + r':\s*' + pat, o))
        loc, d, la, ln = g('loc', '"([^"]*)"'), g('dist', r'([\d.]+)'), g('lat', r'([-\d.]+)'), g('lng', r'([-\d.]+)')
        if loc and d and la:
            wps.append((loc, float(d), float(la), float(ln), g('advice', '"([^"]*)"') or ''))
    for w in wps:
        if not w[4].strip():
            p.append('%s 缺 advice' % w[0])
    for i in range(1, len(wps)):
        if wps[i][1] < wps[i - 1][1] - 1e-9:
            p.append('里程倒退 %s' % wps[i][0])
        sl = hav(wps[i - 1][2], wps[i - 1][3], wps[i][2], wps[i][3]) / 1000
        seg = wps[i][1] - wps[i - 1][1]
        if seg != 0 and seg + 0.005 < sl and sl > 0.03:   # seg==0 為交通接駁段，豁免
            p.append('段短於直線 %s（%.2f < %.2f）' % (wps[i][0], seg, sl))
    return len(wps), p


def check_shared():
    """共用檔本身的把關。最高點的顏色自 2026-08-04 起收在 detail.js 的 palette()
    預設值裡，這裡是它唯一的來源，所以要有人看著。"""
    p = []
    js = open('assets/detail.js', encoding='utf-8').read()
    m = re.search(r"function palette\(opt\)[\s\S]{0,400}?peak\s*=\s*opt\.peak\s*\|\|\s*'(#[0-9a-fA-F]{6})'", js)
    if not m:
        p.append('detail.js 找不到 palette() 的山頂綠預設值')
    elif m.group(1).lower() != PEAK:
        p.append('detail.js 的 palette() 山頂綠是 %s，應為 %s' % (m.group(1), PEAK))
    if 'hideEmptyAdvice' in js:
        p.append('detail.js 又出現 hideEmptyAdvice：advice 現為必填，空的建議框該看得見')
    return p


def main():
    bad = 0
    shared = check_shared()
    print('%-16s %s' % ('assets/detail.js', 'OK' if not shared else ' / '.join(shared)))
    bad += bool(shared)
    for f in sorted(glob.glob('*.html')):
        if f == 'index.html':
            continue        # 首頁自成一套視覺系統，見 manifest.conventions.greyscale
        n, p = check(f)
        bad += bool(p)
        print('%-16s %2d點  %s' % (f[:-5], n, 'OK' if not p else ' / '.join(p)))
    total = len(glob.glob('*.html')) - 1
    print('\n%d 頁，有問題 %d 頁' % (total, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
