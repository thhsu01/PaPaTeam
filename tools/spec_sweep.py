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
H2_SPOTS = ('導覽', '亮點')                      # 規格表：自由，但要含其一
SLATE_HEX = ('#f8fafc', '#334155', '#e2e8f0', '#f1f5f9', '#64748b')
PEAK = '#7c9e52'

# 停留類的描述詞。GPS 停留點若當地沒有地名，名字就是自己取的，見下方的檢查。
STOP_SUFFIX = ('休息點', '折返點')

# detail.js 認得的設定鍵。介面寫在文件、實作在 detail.js，兩邊各自演化：
# 頁面寫錯一個鍵不會有任何反應——它就只是靜靜地不作用。2026-08-04 的雙軸審查
# 一次抓到三種都在站上的寫法：card.wrap: 'clamp'（detail.js 只認 'cycle'，
# 其餘任何字串等效於沒寫）、hideEmptyAdvice（SNIPPETS 教了，從來沒有實作）、
# 以及 chart.label/dataset/options（ADR-0001 之後 Chart.js 的設定樹由 detail.js
# 組出，這三個旋鈕已不存在）。共同點是「文件教了、頁面照做、實作不認」。
# 加旋鈕時要一併加進這張表，否則新旋鈕會被這條擋下來——那是刻意的：
# 一個沒人記得的介面，跟一個沒有實作的介面，讀起來一樣糟。
KNOWN = {
    '': {'schedule', 'tripDate', 'nav', 'card', 'palette', 'map', 'chart', 'timeline', 'weather'},
    'card': {'follow', 'flash', 'onUpdate', 'wrap'},
    'map': {'preferCanvas', 'center', 'zoom', 'setView', 'attribution', 'track',
            'palette', 'marker', 'popup', 'selected'},
    'map.track': {'points', 'slice', 'color', 'weight', 'opacity', 'dashArray'},
    'chart': {'lineColor', 'fillColor', 'fillAlpha', 'palette',
              'elevationFloor', 'elevationMax', 'advanced'},
    'timeline': {'layout', 'fields', 'emoji', 'palette', 'hover'},
    'weather': {'lat', 'lng', 'elevation', 'mainId', 'subId', 'subText',
                'sep', 'unit', 'errorMain'},
}

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
    pages = [f for f in sorted(glob.glob('*.html')) if f != 'index.html']
    n_pages = len(pages)
    n_tracks = len(glob.glob('assets/tracks/*.js'))
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
    CN = '零一二三四五六七八九十'

    def cn(n):
        return CN[n] if n < 11 else CN[10] + (CN[n - 10] if n < 20 else '')

    checks = [
        ('ARCHITECTURE.md', '小百岳座數', r'全站(\S+?)座裡有(\S+?)座就是', (cn(xb), cn(peak))),
        ('CONTEXT.md',      '小百岳座數', r'全站(\S+?)座小百岳裡有(\S+?)座', (cn(xb), cn(peak))),
        ('tools/spec_sweep.py', '小百岳座數', r'全站(\S+?)座裡有(\S+?)座就是', (cn(xb), cn(peak))),
        ('manifest.json', '有軌跡的頁數', r'目前(\S+?)頁有軌跡', (cn(n_tracks),)),
        ('manifest.json', 'advanced 未使用的頁數', r'advanced 目前 (\d+) 頁都沒用到', (str(n_pages),)),
        ('ARCHITECTURE.md', '行列式的頁數', r'// 行列式，(\d+) 頁', (str(n_pages - 6),)),
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
    counts = check_doc_counts()
    print('%-16s %s' % ('文件宣稱的數量', 'OK' if not counts else ' / '.join(counts)))
    bad += bool(counts)
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
