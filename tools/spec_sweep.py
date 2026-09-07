#!/usr/bin/env python3
"""全站規格掃描。ARCHITECTURE.md 的段落規格表寫了卻沒人檢查，導覽文字與 <h2>
因此長期漂移（2026-08-04 的雙軸審查才發現）。這支腳本把那張表變成可執行的檢查。"""
import re, glob, math, sys, os, functools

os.chdir(os.environ.get('PAPA_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bump_assets                       # 共用資產的版本號：同一個雜湊函式，不另抄一份
import manifest_tree                     # manifest 條目與中文數字：README 檔案樹用的同一份
ASSET_HASHES = {a: bump_assets.asset_hash(a) for a in bump_assets.ASSETS if os.path.exists(a)}


@functools.lru_cache(maxsize=None)
def site_counts():
    """文件裡會被拿來核對的現況數字，全站只算一次：詳情頁數、有軌跡的頁數、卡片式時間軸的頁數。"""
    pages = tuple(f for f in sorted(glob.glob('*.html')) if f != 'index.html')
    n_card = sum(1 for f in pages if "layout: 'card'" in open(f, encoding='utf-8').read())
    return {'pages': pages, 'n': len(pages), 'n_tracks': len(glob.glob('assets/tracks/*.js')), 'n_card': n_card}


def pos_emoji_table():
    """detail.js 的 POS_EMOJI：pos → emoji 的全站表。從原始碼讀，不另抄一份。"""
    js = open('assets/detail.js', encoding='utf-8').read()
    i = js.find('var POS_EMOJI = {')
    if i < 0:
        return {}
    blk = js[i:js.index('};', i)]
    return dict(re.findall(r"'([^']+)':\s*'([^']+)'", blk))


POS_EMOJI = pos_emoji_table()

SECTIONS = ['overview', 'map-section', 'elevation', 'spots', 'timeline']
H2 = {'map-section': '互動路線圖', 'elevation': '海拔高度剖面圖'}
H2_TIMELINE = ('預計行程進度', '實走時間軸')     # 主詞須為其一，容許括號後綴
H2_SPOTS = ('導覽', '亮點')                      # 規格表：自由，但要含其一
SLATE_HEX = ('#f8fafc', '#334155', '#e2e8f0', '#f1f5f9', '#64748b')
PEAK = '#7c9e52'

# 停留類的描述詞。GPS 停留點若當地沒有地名，名字就是自己取的，見下方的檢查。
STOP_SUFFIX = ('休息點', '折返點')

# 行程事實槽：data-trip="<事實>[:<格式>]"。與 detail.js 的 TRIP_FORMAT 一致。
TRIP_SLOTS = {'date': {'ymd', 'md', 'zh', 'slash'}, 'km': {'n'}, 'duration': {'hm', 'zh', 'h', 'm'},
              'gain': {'n'}, 'summit': {'n'}}

# detail.js 認得的設定鍵。介面寫在文件、實作在 detail.js，兩邊各自演化：
# 頁面寫錯一個鍵不會有任何反應——它就只是靜靜地不作用。2026-08-04 的雙軸審查
# 一次抓到三種都在站上的寫法：card.wrap: 'clamp'（detail.js 只認 'cycle'，
# 其餘任何字串等效於沒寫）、hideEmptyAdvice（SNIPPETS 教了，從來沒有實作）、
# 以及 chart.label/dataset/options（ADR-0001 之後 Chart.js 的設定樹由 detail.js
# 組出，這三個旋鈕已不存在）。共同點是「文件教了、頁面照做、實作不認」。
# 加旋鈕時要一併加進這張表，否則新旋鈕會被這條擋下來——那是刻意的：
# 一個沒人記得的介面，跟一個沒有實作的介面，讀起來一樣糟。
KNOWN = {
    '': {'schedule', 'trip', 'nav', 'card', 'palette', 'map', 'chart', 'timeline', 'weather'},
    'trip': {'date', 'km', 'duration', 'gain', 'summit'},
    'card': {'follow', 'flash', 'onUpdate', 'wrap'},
    # palette 只在最上層：map/chart/timeline 各自的 palette 旋鈕 22 頁沒人用，
    # 2026-09 第二輪審查後拿掉（detail.js 三處改讀同一個 pal()）。
    'map': {'preferCanvas', 'center', 'zoom', 'setView', 'attribution', 'track',
            'marker', 'popup', 'selected'},
    'map.track': {'points', 'slice', 'color', 'weight', 'opacity', 'dashArray'},
    'chart': {'lineColor', 'fillColor', 'fillAlpha',
              'elevationFloor', 'elevationMax', 'advanced'},
    'timeline': {'layout', 'fields', 'emoji', 'hover'},
    'weather': {'lat', 'lng', 'elevation', 'subText', 'sep', 'unit', 'errorMain'},
}

# 由 detail.js 產生的共用區塊。頁面只放 <div data-widget="…"> 掃載點；
# 這些區塊的 id 與 class 若又出現在頁面原始碼裡，就是有人把它手寫回來了。
WIDGETS = {'nav', 'notice', 'weather', 'wp-card', 'chart', 'timeline'}
WIDGET_OWNED = [('id="wp-pos-label"', 'wp-card'), ('id="wp-advice"', 'wp-card'),
                ('id="elevation-chart"', 'chart'), ('id="timeline-container"', 'timeline'),
                ('id="trip-past-notice"', 'notice'), ('id="weather-main"', 'weather'),
                ('class="nav-btn', 'nav'), ('aria-label="滾動到', 'nav')]

# 本站出現過的台灣小百岳（山名 → 官方編號）。2026-08-04 查官方名單建立，
# 因為「這座山是不是小百岳」不可能從頁面內容推導出來，只能維護一張表。
# 比對的是航點 loc 的開頭，所以「大屯山主峰 (H1,092m)」對得上「大屯山主峰」。
# 新增行程若走到名單外的小百岳，要自己往這裡加一筆。
XBAIYUE = {
    '大屯山主峰': 1,      # 台北，1092 m
    '七星山主峰': 2,      # 台北，1120 m
    '七星山東峰': 2,      # 與主峰共用 002——名單上的編號給的是七星山這座山，
                         # 主東峰是它的兩個峰頭。本站兩個峰頭都標，但不算兩座
    '大崙頭山': 8,        # 台北內湖，476 m
    '南港山': 13,         # 台北信義，375 m
    '大棟山': 15,         # 新北樹林／桃園龜山交界，405 m
    '南勢角山': 16,       # 新北中和，302 m
    '火炎山': 35,         # 苗栗三義。官方名單標 596 m，本站的航點採地形圖 601 m
}


def hav(a, b, c, d):
    R = 6371000.0
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


@functools.lru_cache(maxsize=None)
def schedule_objects(s):
    """以括號配對切出 schedule 的每個物件。用貪婪 regex 會跨物件吃字元，
    2026-08-03 就是這樣漏讀了 nanshijiao 17 個航點裡的 3 個。
    五個檢查各自呼叫一次，所以以整頁原始碼為鍵快取；回傳的 list 不要就地改。"""
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
    return tuple(out)


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


def init_options(s):
    """走訪 PaPaDetail.init({...}) 的設定樹，回傳 [(路徑, 鍵, 值的開頭)]。

    同樣不用 regex：設定裡有箭頭函式、三元運算與巢狀物件，regex 分不清
    「物件的鍵」與「函式主體裡的鍵」。路徑就是用來分開兩者的——KNOWN 沒有的路徑
    （map.marker 的回傳物件、chart.advanced 的 Chart.js 設定樹、emoji 對照表）
    一律不查，那些地方本來就不歸 detail.js 的介面管。
    """
    blk = js_block(s, 'PaPaDetail.init(')
    if blk is None:
        return []
    out, stack, pending, prev = [], [], None, ''
    i, n = 0, len(blk)
    while i < n:
        ch = blk[i]
        if ch in '\'"`':                                  # 字串整段跳過
            i += 1
            while i < n and blk[i] != ch:
                i += 2 if blk[i] == '\\' else 1
            i, prev = i + 1, 'x'
            continue
        if blk.startswith('//', i):
            j = blk.find('\n', i)
            i = n if j < 0 else j
            continue
        if blk.startswith('/*', i):
            j = blk.find('*/', i)
            i = n if j < 0 else j + 2
            continue
        if ch == '{':
            stack.append(pending)
            pending, prev, i = None, ch, i + 1
            continue
        if ch == '}':
            if stack:
                stack.pop()
            pending, prev, i = None, ch, i + 1
            continue
        if ch.isspace():
            i += 1
            continue
        m = re.match(r'([A-Za-z_$][\w$]*)\s*:', blk[i:])
        if m and prev in '{,':
            comps = stack[1:]                              # stack[0] 是 init 自己的大括號
            path = '?' if any(c is None for c in comps) else '.'.join(comps)
            out.append((path, m.group(1), blk[i + m.end():i + m.end() + 40]))
            pending, prev, i = m.group(1), 'x', i + m.end()
            continue
        prev, i = ch, i + 1
    return out


def h2_of(s, sec):
    """該段落 <h2> 的文字。多數頁在標題前放一根色條 <span>，所以要剝標籤——
    第一版只認 `</span>` 後面的文字，於是 huoyianshan 那種沒有色條的
    「各景點深度導覽」整個讀成 None，明明合規卻查不到。"""
    i = s.find('id="%s"' % sec)
    if i < 0:
        return None
    j = s.find('</h2>', i)
    k = s.rfind('<h2', i, j)
    if j < 0 or k < 0:
        return None
    return re.sub(r'<[^>]+>', '', s[k:j]).strip() or None


def check(f):
    s = open(f, encoding='utf-8').read()
    p = []

    # ── 結構 ────────────────────────────────────────────────
    if [x for x in re.findall(r'<section[^>]*id="([a-z-]+)"', s) if x in SECTIONS] != SECTIONS:
        p.append('段落 id 或順序異常')
    if re.search(r'返回首頁|←\s*首頁', s):
        p.append('疑似左上返回鍵')

    # ── 共用區塊用到的主色 token 必須定義 ────────────────────
    # wp-card 的建議框用 var(--accent-tint) 與 var(--accent-border)。2026-09 候選 2 把航點卡
    # 收進 detail.js 之後，七頁沒定義這兩個 token，建議框就沒有底色與框線——執行期基準
    # 只記骨架、對比度量測不管框線，兩個都抓不到。token 是 :root 裡的事，這裡查。
    for tok in ('--accent', '--accent-strong', '--accent-tint', '--accent-border'):
        if not re.search(r'%s\s*:' % re.escape(tok), s):
            p.append('缺 %s——共用區塊（航點卡的建議框）靠它上色' % tok)

    # ── 共用資產的版本要跟內容走 ─────────────────────────────
    # 導覽列等區塊由 detail.js 產生之後，HTML 與 JS 的版本必須成對：新版 HTML 配上
    # 快取裡的舊版 detail.js，掃載點就填不進去，站徽與回首頁連結整個不見——
    # 2026-09-07 正式站實際發生過。URL 帶內容雜湊（?v=）就不會抓到舊檔；
    # 改了共用檔要跑 python3 tools/bump_assets.py，忘了就在這裡紅。
    for a in bump_assets.stale(s, ASSET_HASHES):
        p.append('%s 的版本號不是現在的內容——跑 python3 tools/bump_assets.py' % a)

    # ── 共用區塊：掃載點在、手寫的不在 ───────────────────────
    # 導覽列（含五顆鍵的文字）、航點卡、海拔圖容器、時間軸容器、已完成提示、天氣卡
    # 都由 detail.js 產生。原本這裡有十來條規則在查它們有沒有漂——現在只要查
    # 掃載點有沒有放對，以及有沒有人把區塊手寫回來。
    mounts = set(re.findall(r'data-widget="([^"]*)"', s))
    for name in mounts - WIDGETS:
        p.append('data-widget="%s"：detail.js 沒有這個共用區塊' % name)
    for name in ('nav', 'wp-card', 'chart', 'timeline'):
        if name not in mounts:
            p.append('缺 data-widget="%s" 掃載點' % name)
    if re.search(r'\bweather:\s*\{', s) and 'weather' not in mounts:
        p.append('有 weather 設定卻沒有 data-widget="weather" 掃載點——天氣會沒地方顯示')
    for marker, owner in WIDGET_OWNED:
        if marker in s:
            p.append('%s 是 detail.js 產生的（%s 區塊），頁面不要自己寫' % (marker, owner))

    # ── <h2> 主詞（容許括號後綴）───────────────────────────
    for sec, want in H2.items():
        h = h2_of(s, sec)
        if h is None or not h.startswith(want):
            p.append('#%s 的 h2「%s」主詞應為「%s」' % (sec, h, want))
    h = h2_of(s, 'timeline')
    if h is None or not h.startswith(H2_TIMELINE):
        p.append('#timeline 的 h2「%s」主詞應為 %s 之一' % (h, '／'.join(H2_TIMELINE)))
    # spots 的標題是自由的，規格表只要求看得出「這段是導覽」。20 頁寫「X亮點導覽」，
    # 漏網的兩頁寫成「百科」——讀者點進去看到的是同一種東西，標題卻自成一格。
    h = h2_of(s, 'spots')
    if h is None or not any(w in h for w in H2_SPOTS):
        p.append('#spots 的 h2「%s」要看得出是導覽（含 %s）' % (h, '／'.join(H2_SPOTS)))

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
    # 「宣告了 PAL」不算數，要真的送進去。2026-08-04 起各頁改成在 init 的頂層寫
    # 一次 palette: PAL，三個介面共用——那比在三個區塊各寫一次更好，所以頂層有就算過。
    # 只有頁面既沒有頂層 palette、該區塊自己也沒有時才報。
    # 「頂層有沒有 palette」要走剖析器，不能用 regex：第一版寫成
    # `init\(\{[^}]*?palette:`，[^}] 跨不過中間的 card: {...}，於是 huoyianshan
    # 明明在頂層宣告了卻被判成沒有。
    opts = init_options(s)
    keys = {(path, key) for path, key, _ in opts}
    if ('', 'palette') not in keys:
        for key, label in (('chart:', '海拔圖'), ('marker:', '地圖標記'), ('timeline:', '時間軸')):
            blk = js_block(s, key)
            if blk is not None and 'PAL' not in blk and 'palette' not in blk:
                p.append('%s 沒有走 palette()——同一個航點會在不同介面上是不同顏色' % label)

    # ── 設定鍵必須是 detail.js 認得的 ───────────────────────
    for path, key, val in opts:
        if path in KNOWN and key not in KNOWN[path]:
            p.append('%s%s 不是 detail.js 認得的設定——寫了不會有任何作用'
                     % (path + '.' if path else '', key))
        if (path, key) == ('card', 'wrap'):
            v = re.match(r"""\s*['"]([^'"]*)""", val)
            if v and v.group(1) != 'cycle':
                p.append("card.wrap: '%s' 沒有作用——detail.js 只認 'cycle'，"
                         "到頭就停是不寫時的預設" % v.group(1))

    # ── 行程事實槽 ──────────────────────────────────────────
    # data-trip="date:md" 的事實名與格式要是 detail.js 認得的，理由同上：寫錯的槽只會
    # 靜靜留白。另外，已完成頁的軌跡由 detail.js 依 trip.date 載入，頁面自己再寫
    # <script src="assets/tracks/…"> 或 PaPaTracks[…] 就是把第三份日期加回來。
    for m in re.finditer(r'data-trip="([^"]*)"', s):
        fact, _, fmt = m.group(1).partition(':')
        if fact not in TRIP_SLOTS:
            p.append('data-trip="%s"：沒有「%s」這個行程事實' % (m.group(1), fact))
        elif fmt and fmt not in TRIP_SLOTS[fact]:
            p.append('data-trip="%s"：%s 沒有「%s」這種格式' % (m.group(1), fact, fmt))
    if ('trip', 'date') in keys and 'notice' not in mounts:
        p.append('紀錄頁缺 data-widget="notice" 掃載點——行程日過後不會出現「此行程已完成」')
    if ('trip', 'date') in keys:
        if re.search(r'<script[^>]*src="assets/tracks/', s):
            p.append('頁面自己載入軌跡檔——軌跡由 detail.js 依 trip.date 載入，script 標籤要拿掉')
        if 'PaPaTracks[' in s:
            p.append('頁面自己查 PaPaTracks——map.track 不給 points，detail.js 會依 trip.date 找')

    # ── 時間軸的 emoji：開了就每個 pos 都要有 ────────────────
    # pos → emoji 的全站表在 detail.js（POS_EMOJI），頁面只覆寫例外。表上沒有的 pos
    # 會顯示 📍——那是無聲的退化，所以在這裡提醒；覆寫若跟全站表一樣就是多寫。
    tl = js_block(s, 'timeline:')
    em = re.search(r'\bemoji:\s*(true|\{[^}]*\})', tl) if tl else None
    if tl and not em and re.search(r'\bemoji:\s*[A-Za-z_$]', tl):
        p.append('timeline.emoji 要寫 true 或物件字面值——放變數，這裡讀不到、覆寫有沒有多餘就查不了')
    if em:
        over = dict(re.findall(r"""['"]([^'"]+)['"]\s*:\s*['"]([^'"]+)['"]""", em.group(1)))
        for k, v in over.items():
            if POS_EMOJI.get(k) == v:
                p.append('timeline.emoji 覆寫的 %s→%s 跟全站表一樣，刪掉' % (k, v))
        seen = set()
        for o in schedule_objects(s):
            pos = re.search(r'pos:\s*"([^"]*)"', o)
            if pos and pos.group(1) not in POS_EMOJI and pos.group(1) not in over and pos.group(1) not in seen:
                seen.add(pos.group(1))
                p.append('pos「%s」全站表沒有 emoji、頁面也沒覆寫——時間軸會顯示 📍' % pos.group(1))

    # ── 小百岳是航點的屬性，不是 pos 的一個值 ────────────────
    # 一座山可以同時是最高點與小百岳（全站七座裡有五座就是）。寫進 pos 會逼出
    # 一個假的二選一：nangangshan 與 nanshijiao 因此把 pos 設成「小百岳 #13／#16」，
    # 於是那兩頁真正的最高點（九五峰、五尖山）與小百岳共用同一個綠。
    # 反過來 datunshan／datongshan／qixingshan 的小百岳只寫在散文裡，資料層看不到，
    # 地圖與海拔圖上也就標不出來——這一條就是為了讓後者不再溜過去。
    for o in schedule_objects(s):
        pos = re.search(r'pos:\s*"([^"]*)"', o)
        loc = re.search(r'loc:\s*"([^"]*)"', o)
        who = (loc.group(1) if loc else '?')
        if pos and '小百岳' in pos.group(1):
            p.append('%s 的 pos 是「%s」——小百岳要放 xbaiyue 欄位，'
                     '佔著 pos 會讓它與最高點互斥' % (who, pos.group(1)))
        prose = ' '.join(m.group(1) for m in re.finditer(r'(?:desc|advice):\s*"([^"]*)"', o))
        # 兩種提到小百岳但不是在宣稱「本航點是小百岳」的寫法，都要先剔掉：
        #   帶數量詞——「兩座小百岳一次完成」是在講整趟行程（qixingshan 的回程終點）
        #   帶否定詞——「東峰不是獨立的小百岳」是在澄清它不是（qixingshan 的東峰）
        claims = re.sub(r'[一二兩三四五六七八九十百\d]+\s*座\s*小百岳', '', prose)
        claims = re.sub(r'(?:不是|並非|非)[^，。！？]{0,12}小百岳', '', claims)
        if '小百岳' in claims and 'xbaiyue' not in o:
            p.append('%s 的敘述提到小百岳卻沒有 xbaiyue 欄位——地圖與海拔圖上標不出來' % who)

        # 反過來的漏洞：這座山**是**小百岳，但頁面從頭到尾沒提，於是上面那條抓不到。
        # 2026-08-04 就是這樣漏掉三座：daluntouweishan 的大崙頭山（#8）、huoyianshan 的
        # 火炎山（#35），還有 datongshan 的大棟山當時只寫 true 沒有編號。查官方名單才發現。
        # 所以另外掛一張「本站出現過的小百岳」對照表，逐一比對航點名稱。
        # 新增航點若是名單上的山，這條會擋下來——這是唯一擋得住的作法，
        # 因為「某座山是不是小百岳」不可能從頁面內容推導出來。
        if loc:
            # 剝掉標高與狀態註記（與 detail.js 的 shortName 同一套規則），再比對。
            # 不能只用「開頭相符」——「大崙頭山親山步道入口」「火炎山大峽谷」
            # 「南港山南峰」都會誤中。山名之後只允許接標高數字或三角點／主峰／山頂。
            base = re.sub(r'\s*[（(][^)）]*[)）]', '', loc.group(1)).strip()
            for name, num in XBAIYUE.items():
                if re.fullmatch(re.escape(name) + r'[\s\d]*(三角點|主峰|山頂)?', base) \
                   and 'xbaiyue' not in o:
                    p.append('%s 是台灣小百岳 #%d，卻沒有 xbaiyue 欄位' % (who, num))

    # ── 無地名的停留點要自己講清楚 ──────────────────────────
    # 這類航點的名字是描述詞不是地名（「第一休息點」「古圳休息點」「折返點」），
    # 不講明的話讀者會拿去查一個不存在的地方。慣例見 ARCHITECTURE.md。
    #
    # 只認 STOP_SUFFIX 那幾個「停留」類的描述詞：它們是 GPS 停留點轉出來的，
    # 名字必然是自己取的。刻意不含「展望點／眺望點」——那是地形描述，該處究竟有沒有
    # 地名不是從頁面形狀看得出來的事，硬要求註明等於逼頁面宣稱一件沒查證過的事。
    # 也不含「休息站」：桂林峰休息站、一水休息站是有名字的既有設施。
    # 第一版還多要求 pos 為「休息點」，於是漏掉 zhongzhengshan 的折返點（pos 是最高點）。
    for o in schedule_objects(s):
        loc = re.search(r'loc:\s*"([^"]*)"', o)
        if loc and loc.group(1).endswith(STOP_SUFFIX):
            desc = re.search(r'desc:\s*"([^"]*)"', o)
            # 說法不必逐字相同：zhongzhengshan 寫的是「沒有可引用的地名」。
            if not desc or not re.search(r'沒有[^，。]{0,8}地名', desc.group(1)):
                p.append('%s 是沒有地名的停留點，desc 要寫明這件事' % loc.group(1))

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


def check_doc_counts():
    """文件裡宣稱的數量必須與實際相符。

    2026-08-04 的雙軸審查抓到三處漂掉的數字：ARCHITECTURE.md 與本檔還寫著小百岳
    「六座裡有三座」（實際七座五座）、manifest 的 track_source 還寫「十二頁有軌跡」
    （實際十六頁）、chart_config 還寫「18 頁都沒用到 advanced」（實際 22 頁）。

    三處都是**可以從倉庫算出來的數字**，卻靠人記得改。這一條把它們變成會被擋下來的事——
    與本檔開頭那句「規格表寫了卻沒有檢查就會漂移」是同一個道理，只是對象換成數量。
    刻意只查算得出來的那幾個，不做通用的「文件裡所有數字」掃描：那會誤報到不能用。
    """
    p = []
    c = site_counts()
    pages, cn = c['pages'], manifest_tree.cn
    # 以「不重複的編號」計數，不是以航點計數：七星山主峰與東峰共用 #2，
    # 標了兩個航點但仍然只有一座小百岳。算成兩座會讓文件跟著錯。
    seen = {}
    for f in pages:
        for o in schedule_objects(open(f, encoding='utf-8').read()):
            m0 = re.search(r'xbaiyue:\s*(\d+)', o)
            if m0:
                num = int(m0.group(1))
                seen[num] = seen.get(num, False) or bool(re.search(r'pos:\s*"最高點"', o))
    xb, peak = len(seen), sum(seen.values())

    checks = [
        ('ARCHITECTURE.md', '小百岳座數', r'全站(\S+?)座裡有(\S+?)座就是', (cn(xb), cn(peak))),
        ('CONTEXT.md',      '小百岳座數', r'全站(\S+?)座小百岳裡有(\S+?)座', (cn(xb), cn(peak))),
        ('tools/spec_sweep.py', '小百岳座數', r'全站(\S+?)座裡有(\S+?)座就是', (cn(xb), cn(peak))),
        ('manifest.json', '有軌跡的頁數', r'目前(\S+?)頁有軌跡', (cn(c['n_tracks']),)),
        ('manifest.json', 'advanced 未使用的頁數', r'advanced 目前 (\d+) 頁都沒用到', (str(c['n']),)),
        # 行列式＝不是卡片式的那些頁。2026-09 之前這裡寫死 n - 6，卡片式頁數一變就會靜靜錯掉
        ('ARCHITECTURE.md', '行列式的頁數', r'// 行列式，(\d+) 頁', (str(c['n'] - c['n_card']),)),
        ('ARCHITECTURE.md', '卡片式的頁數', r'// 卡片式，(\d+) 頁', (str(c['n_card']),)),
    ]
    for path, what, pat, want in checks:
        m = re.search(pat, open(path, encoding='utf-8').read())
        if not m:
            p.append('%s 找不到「%s」的敘述——樣式過期了，改文字時要一併改本檢查' % (path, what))
        elif m.groups() != want:
            p.append('%s 的%s寫成 %s，實際是 %s' % (path, what, '／'.join(m.groups()), '／'.join(want)))

    used = set()
    for f in pages:
        for o in schedule_objects(open(f, encoding='utf-8').read()):
            mm = re.search(r'xbaiyue:\s*(\d+)', o)
            if mm:
                used.add(int(mm.group(1)))
    extra = used - set(XBAIYUE.values())
    if extra:
        p.append('頁面用了對照表沒有的小百岳編號 %s——表要補' % sorted(extra))
    return p


def tracked_files():
    """倉庫追蹤的檔案。CI 與本機都有 git；沒有就退回走目錄。"""
    import subprocess
    try:
        # --others --exclude-standard：還沒 git add 的新檔也算，否則新檔會被判成「倉庫沒有」
        out = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard'],
                                      stderr=subprocess.DEVNULL).decode().split()
        return set(out)
    except Exception:
        out = set()
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
            out.update(os.path.join(root, f)[2:] for f in files)
        return out


def check_manifest():
    """manifest.json 是專案索引（給人也給 AI 的入口），必須跟倉庫一一對應：
    倉庫裡的檔案都要有條目，條目指的檔案也都要存在。2026-09 的架構檢視發現
    README 的檔案樹兩次漏檔（先漏四頁、後漏 CONTEXT.md 與 ADR），manifest 反而是齊的
    ——所以拿它當唯一的清單，這裡守住它不漂。"""
    p = []
    entries = manifest_tree.entries()       # 同一個路徑出現兩處時已併成一條，short 取有的那份
    paths = {e['path'] for e in entries}
    tracked = tracked_files()
    dirs = {x for x in paths if x.endswith('/')}          # 目錄條目：給檔案樹一句說明用
    for t in sorted(tracked - paths):
        p.append('倉庫有 %s，manifest.json 沒有它的條目' % t)
    for t in sorted(paths - dirs - tracked):
        p.append('manifest.json 列了 %s，倉庫裡沒有這個檔' % t)
    for d in sorted(dirs):
        if not os.path.isdir(d):
            p.append('manifest.json 列了目錄 %s，倉庫裡沒有' % d)
    # 非頁面、非軌跡的條目要有 short——README 的檔案樹就是拿它印的。
    for e in entries:
        path = e['path']
        # 頁面的那一句由 title 與軌跡日期組出來；軌跡檔不必註解；目錄可以沒有
        if path.endswith('.html') or path.startswith('assets/tracks/') or path.endswith('/'):
            continue
        if not e.get('short'):
            p.append('%s 的條目缺 short（檔案樹上那一句）' % path)
    # README 的檔案樹必須是 manifest 印出來的那一份
    if manifest_tree.readme_block() != manifest_tree.render():
        p.append('README.md 的檔案樹跟 manifest.json 不一致——跑 python3 tools/manifest_tree.py --write')
    return p


def check_live_counts():
    """文件裡「N 頁」這種活數字必須等於某個現況。

    check_doc_counts() 巡的是幾句指定的敘述；這裡補的是漏網的——2026-09 的審查在
    巡邏外又抓到四處（十二→十六頁軌跡、十八→二十二個詳情頁、detail.css 檔頭的 10 頁）。
    分兩種：有日期或「先前／之前／當時／曾」的句子是歷史敘述（「2026-08-04 量測 18 頁」），
    當時是真的、以後也還是真的，不查；其餘是在講現況，數字必須落在現況的集合裡
    （詳情頁數、含首頁的頁數、有軌跡的頁數、候選頁數、兩種時間軸版面的頁數）。
    「落在集合裡」比「指定它是哪一個」寬鬆，代價是一個過期的數字若剛好等於另一個
    現況會漏掉——那比逐句維護樣式要划算。"""
    p = []
    c = site_counts()
    n, n_tracks, n_card = c['n'], c['n_tracks'], c['n_card']
    live = {n, n + 1, n_tracks, n - n_tracks, n_card, n - n_card}
    CN = manifest_tree.CN

    def cn2int(t):
        if t.isdigit():
            return int(t)
        if t == '十':
            return 10
        if '十' in t:
            a, b = t.split('十')
            return (CN.index(a) if a else 1) * 10 + (CN.index(b) if b else 0)
        return CN.index(t)

    for path in ('README.md', 'ARCHITECTURE.md', 'CONTEXT.md', 'CONTRIBUTING.md', 'SNIPPETS.md', 'assets/detail.css'):
        text = open(path, encoding='utf-8').read()
        for i, sent in enumerate(re.split(r'[。；\n]', text)):
            if re.search(r'20\d\d[-/年]|先前|之前|當時|曾|原本|那時|上次|最早|早期|其餘|另', sent):
                continue
            for mm in re.finditer(r'(?<![\d.])(\d+|[一二三四五六七八九十]+)\s*(頁|個詳情頁)', sent):
                v = cn2int(mm.group(1))
                # 「一頁」「三頁」這種小數字多半是量詞或局部計數，不是在講全站
                if v > 5 and v not in live:
                    p.append('%s：「%s」——現況是 %d 頁（含首頁 %d、有軌跡 %d、候選 %d、卡片式 %d）'
                             % (path, mm.group(0), n, n + 1, n_tracks, n - n_tracks, n_card))
    return p


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
    counts = check_doc_counts() + check_live_counts()
    print('%-16s %s' % ('文件宣稱的數量', 'OK' if not counts else ' / '.join(counts)))
    bad += bool(counts)
    mf = check_manifest()
    print('%-16s %s' % ('manifest.json', 'OK' if not mf else ' / '.join(mf)))
    bad += bool(mf)
    # 首頁不走詳情頁的規格，但它也引用共用資產——版本號一樣要跟內容走
    idx = ['%s 的版本號不是現在的內容——跑 python3 tools/bump_assets.py' % a
           for a in bump_assets.stale(open('index.html', encoding='utf-8').read(), ASSET_HASHES)]
    print('%-16s %s' % ('index', 'OK' if not idx else ' / '.join(idx)))
    bad += bool(idx)
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
