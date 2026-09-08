#!/usr/bin/env python3
"""同一趟行程的事實一致性檢查。

一趟行程的日期與總里程，2026-08 之前在自己的詳情頁裡會出現七、八次（meta、導覽副標、
日期戳、統計列、頁腳、軌跡檔名…），首頁的卡片又各有一份。2026-08-04 量測：12 趟已完成
行程在自己頁內就重複了 165 次，全部手打，目前一致純粹是靠人維護的。

改一個數字要同時改五、六個地方，漏一個畫面就會自相矛盾——把 henglingguidao 從
5.30 改成 5.36 時就得逐一改過。這支腳本讓「漏改」變成會被擋下來的事。

## 為什麼是交叉核對，不是拿資料當權威

一度想拿 schedule 最後一個航點的 dist 當總里程的權威，但那是錯的：
caolingguidao 末點 7.87、總里程 7.88；nanshijiao 末點 10.96、總里程 11.09
——軌跡在最後一個航點之後還有一段。總里程沒有單一的資料來源。

所以改成「畫面上所有講同一件事的地方必須彼此一致」。缺某個欄位不算錯，
各頁的版面家族本來就不同；只有「同時存在且互相矛盾」才是問題。

## 2026-09：事實改成宣告一次

已完成頁的事實現在只在 PaPaDetail.init 的 trip 物件宣告一次，版面上的槽
（data-trip="date:md" 之類）由 detail.js 填。165 處手打縮到剩下 JS 填不到的地方：
<meta description>、首頁卡片，以及散文與航點 desc 裡順口提到的數字。本檔把 trip 當成
事實的一個「出現位置」——跟其他位置一樣進交叉核對，所以殘留的手打副本若跟 trip 不合，
一樣會被抓到。導覽副標、已完成提示、頁腳、日期戳、統計列那些位置 2026-09 起由共用區塊
或事實槽產生，對應的規則已經刪掉（第三輪審查：七條在 22 頁零命中的死槽）。
"""
import re
import sys
import os
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from papa_common import chdir_root, schedule_objects
chdir_root()


def norm_date(y, m, d):
    return '%04d-%02d-%02d' % (int(y), int(m), int(d))


# (來源標籤, 樣式)。只取結構化的位置，不掃整篇內文：內文合法地會提到別的日期
# （「2026 年整理 GPX 時補回」「同治六年」）。散文裡的行程日另有一條規則（見下）。
TRIP = r'\btrip:\s*\{[^}]*?'          # trip 物件是扁的，[^}] 走不出它

DATE_SLOTS = [
    ('trip.date',      TRIP + r'\bdate:\s*"(\d{4})-(\d{2})-(\d{2})"'),
    ('meta description', r'<meta name="description" content="(\d{4})/(\d{1,2})/(\d{1,2})'),
]


def page_dates(s):
    """回傳 [(來源, 正規化日期)]。"""
    out = []
    for label, pat in DATE_SLOTS:
        m = re.search(pat, s)
        if m:
            out.append((label, norm_date(*m.groups())))
    return out


TOTAL_SLOTS = [
    ('trip.km',         TRIP + r'\bkm:\s*([\d.]+)'),
    ('meta description', r'<meta name="description" content="[^"]*?全程 *約? *([\d.]+) *公里'),
]


def page_totals(s):
    """回傳 [(來源, 里程字串)]。只取「講總里程」的位置。"""
    out = []
    for label, pat in TOTAL_SLOTS:
        m = re.search(pat, s)
        if m:
            out.append((label, m.group(1)))
    return out


def page_durations(s):
    """回傳 [(來源, 分鐘)]。行程時長的寫法有兩種（「3 小時 26 分」與「3:26」），
    所以一律換算成分鐘再比。「全程 N 小時 M 分」多半出現在末航點的 desc——那是 JS 資料，
    槽填不到，所以要核對。"""
    out = []
    def mins(h, m):
        return int(h) * 60 + int(m)
    m = re.search(TRIP + r'\bduration:\s*"(\d+):(\d{2})"', s)
    if m:
        out.append(('trip.duration', mins(*m.groups())))
    for m in re.finditer(r'全程\s*(\d+)\s*小時\s*(\d+)\s*分', s):
        out.append(('「全程 N 小時 M 分」', mins(*m.groups())))
    m = re.search(r'<meta name="description"[^"]*?(\d+)\s*小時\s*(\d+)\s*分', s)
    if m:
        out.append(('meta description', mins(*m.groups())))
    return out


def page_summits(s):
    """回傳 (trip 宣稱的最高點, schedule 的最高 ele)，缺任一邊回 None。

    這裡的關係是**不等式不是等式**。航點是軌跡的子集，所以 trip 的最高點必然
    ≥ 最高航點的 ele；低於它才是錯的。第一版寫成等式，馬上把 hushan 誤判成錯——
    那頁的腳本明寫「全程最高處其實不在任何航點上：軌跡在 2.01 km 處讀到 184 m」，
    比最高航點的 175 高，是刻意且有說明的。與其加忽略名單，不如把判準改對。"""
    m = re.search(TRIP + r'\bsummit:\s*(\d+)', s)
    eles = [int(x) for x in re.findall(r'\bele:\s*(\d+)', s)]
    if not m or not eles:
        return None
    return int(m.group(1).replace(',', '')), max(eles)


# 散文與航點 desc 裡「最高點，標高 476 公尺」「這條路線最高 476 公尺」這種手打的最高海拔。
# 六個字的窗：夠放「的大崙頭山（」「，標高 」，但放不下 zhongzhengshan 的
# 「最高處，比中正山還高 184 公尺」——那個 184 是高差不是海拔，不能抓。
# 窗裡不能有「差」「在」：eweishan「兩份紀錄的最高點只差 4 公尺」、nangangshan
# 「最高的九五峰在 48 公尺外」講的也都不是海拔。
SUMMIT_PROSE = re.compile(r'最高(?:點|處|峰)?[^。<>\n差在]{0,6}?(?:海拔|標高)?\s*[（(]?\s*(\d[\d,]*)\s*(?:公尺|m\b)')


def summit_prose(s, summit):
    """回傳與 trip.summit 不合的 [(片段, 數字)]。註解不算（不渲染）。"""
    body = re.sub(r'(?m)<!--[\s\S]*?-->|/\*[\s\S]*?\*/|(?<!:)//.*$', '', s)
    bad = []
    for m in SUMMIT_PROSE.finditer(body):
        v = int(m.group(1).replace(',', ''))
        if v != summit:
            bad.append((m.group(0).strip(), v))
    return bad


def loc_elevations(s):
    """航點名稱裡的 (H643m) 必須等於該航點的 ele。兩者都是人打的，會漂。"""
    bad = []
    for blk in schedule_objects(s):
        ele = re.search(r'\bele:\s*(\d+)', blk)
        loc = re.search(r'loc:\s*"([^"]*)"', blk)
        h = re.search(r'[（(]\s*[Hh]\s*([\d,]+)\s*m\s*[)）]', loc.group(1)) if loc else None
        if ele and h and h.group(1).replace(',', '') != ele.group(1):
            bad.append((loc.group(1), h.group(1), ele.group(1)))
    return bad


def index_entries():
    """首頁每張卡片宣稱的日期與里程。只取 completed 區塊——候選與計畫行程沒有行程日，
    拿它們比對會產生假訊號。"""
    s = open('index.html', encoding='utf-8').read()
    i = s.find('completed:')
    s = s[i:] if i > 0 else s
    out = {}
    for m in re.finditer(r'\{ title: "([^"]*)", date: "(\d{4})/(\d{2})/(\d{2})"[^}]*?'
                         r'desc: "([^"]*)"[^}]*?url: "([^"]+\.html)" \}', s):
        title, y, mo, d, desc, url = m.groups()
        km = re.search(r'([\d.]+)\s*km', desc)
        out[url[:-5]] = {'date': norm_date(y, mo, d), 'km': km.group(1) if km else None,
                         'title': title}
    return out


def check_page(name, idx):
    s = open(name + '.html', encoding='utf-8').read()
    problems = []

    # ── 日期 ──────────────────────────────────────────────
    ds = page_dates(s)
    full = list(ds)
    if name in idx:
        full.append(('index.html 的卡片', idx[name]['date']))
    if len({v for _, v in full}) > 1:
        problems.append('日期不一致 → ' + '、'.join('%s=%s' % (s_, v) for s_, v in full))

    # ── 總里程 ────────────────────────────────────────────
    ts = page_totals(s)
    if name in idx and idx[name]['km']:
        ts.append(('index.html 的卡片', idx[name]['km']))
    if len({float(v) for _, v in ts}) > 1:
        problems.append('總里程不一致 → ' + '、'.join('%s=%s' % (s_, v) for s_, v in ts))

    # ── 行程時長 ──────────────────────────────────────────
    ds_ = page_durations(s)
    if len({v for _, v in ds_}) > 1:
        problems.append('行程時長不一致 → ' +
                        '、'.join('%s=%d:%02d' % (a, b // 60, b % 60) for a, b in ds_))

    # ── 最高點海拔 ────────────────────────────────────────
    ss = page_summits(s)
    if ss and ss[0] < ss[1]:
        problems.append('trip 的最高點 %d m 低於最高航點的 %d m' % ss)
    if ss:
        for frag, v in summit_prose(s, ss[0]):
            problems.append('散文寫「%s」，trip.summit 是 %d——改用 data-trip="summit"' % (frag, ss[0]))

    for loc, h, ele in loc_elevations(s):
        problems.append('%s 的名稱寫 %s m，ele 卻是 %s' % (loc, h, ele))

    # ── 有天氣卡的已完成行程必須有 trip.date ──────────────
    # 這是真正會壞的組合：天氣卡沒有行程日就只會顯示今日天氣，而且不會說明為什麼——
    # detail.js 的 fetchWeather() 靠 trip.date 才知道要標「行程日預報」還是
    # 「行程日已過，顯示今日天氣」。沒有天氣卡的頁不算問題，別在這裡報。
    # 判準是 init 裡的 weather 設定，不是版面上的 id：真正決定「這頁會不會去要天氣」的是
    # detail.js 的 `if (cfg.weather) fetchWeather()`。
    has_date = any(src == 'trip.date' for src, _ in ds)
    if name in idx and re.search(r'\bweather:\s*\{', s) and not has_date:
        problems.append('有天氣卡卻沒有 trip.date——會顯示今日天氣而不說明原因')

    # ── 散文裡不該再有手打的行程日 ──────────────────────────
    # 事實只在 trip 宣告一次之後，散文裡「地圖上的線是 4/20 當天的 GPS 軌跡」這種
    # M/D 寫法就是漏網的副本——2026-09 的審查在 14 頁找到 40 處，改錯也沒人抓。
    # 版面要用 <span data-trip="date:slash"></span>。註解、script、meta、title 不算
    # （前兩者不會渲染，後兩者是刻意手寫給爬蟲的）。
    if has_date:
        d = next(v for src, v in ds if src == 'trip.date')
        mo, day = int(d[5:7]), int(d[8:10])
        body = re.sub(r'<script[\s\S]*?</script>|<!--[\s\S]*?-->|<meta[^>]*>|<title>[^<]*</title>', '', s)
        n = len(re.findall(r'(?<![\d/])%d/%d(?![\d/])' % (mo, day), body))
        if n:
            problems.append('散文裡還有 %d 處手打的行程日 %d/%d——改用 data-trip="date:slash"' % (n, mo, day))

    # ── 軌跡檔要真的存在 ──────────────────────────────────
    # 軌跡由 detail.js 依 trip.date 載入，檔名是 assets/tracks/<頁名>-<日期>.js。
    # 日期打錯不會有錯誤訊息，地圖只會靜靜退回航點直線——所以在這裡擋。
    if has_date and re.search(r'\btrack:\s*\{', s) and not re.search(r'\bpoints:|\bslice:', s):
        d = next(v for src, v in ds if src == 'trip.date')
        if not os.path.exists('assets/tracks/%s-%s.js' % (name, d)):
            problems.append('找不到軌跡檔 assets/tracks/%s-%s.js——trip.date 或檔名有一邊錯了' % (name, d))

    return problems


def main():
    idx = index_entries()
    bad = 0
    for f in sorted(glob.glob('*.html')):
        if f == 'index.html':
            continue
        name = f[:-5]
        p = check_page(name, idx)
        bad += bool(p)
        tag = '已完成' if name in idx else '候選／計畫'
        print('%-16s %-8s %s' % (name, tag, 'OK' if not p else ' / '.join(p)))
    n = len(glob.glob('*.html')) - 1
    print('\n%d 頁，事實不一致 %d 頁' % (n, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
