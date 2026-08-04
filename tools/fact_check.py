#!/usr/bin/env python3
"""同一趟行程的事實一致性檢查。

一趟行程的日期與總里程，在自己的詳情頁裡會出現七、八次（meta、導覽副標、日期戳、
統計列、頁腳、軌跡檔名…），首頁的卡片又各有一份。2026-08-04 量測：12 趟已完成行程
在自己頁內就重複了 165 次，全部手打，目前一致純粹是靠人維護的。

改一個數字要同時改五、六個地方，漏一個畫面就會自相矛盾——把 henglingguidao 從
5.30 改成 5.36 時就得逐一改過。這支腳本讓「漏改」變成會被擋下來的事。

## 為什麼是交叉核對，不是拿資料當權威

一度想拿 schedule 最後一個航點的 dist 當總里程的權威，但那是錯的：
caolingguidao 末點 7.87、總里程 7.88；nanshijiao 末點 10.96、總里程 11.09
——軌跡在最後一個航點之後還有一段。總里程沒有單一的資料來源。

所以改成「畫面上所有講同一件事的地方必須彼此一致」。缺某個欄位不算錯，
各頁的版面家族本來就不同；只有「同時存在且互相矛盾」才是問題。
"""
import re
import sys
import os
import glob

os.chdir(os.environ.get('PAPA_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def norm_date(y, m, d):
    return '%04d-%02d-%02d' % (int(y), int(m), int(d))


# (來源標籤, 樣式)。七段同形的 regex 原本各寫一次 out.append，(來源, 樣式) 一路
# 一起旅行——把它們收成一張表，新增一個出現位置只要加一行。
# 只取結構化的位置，不掃內文：內文合法地會提到別的日期（「2026 年整理 GPX 時補回」
# 「同治六年」）。軌跡檔名的樣式依頁名而定，所以留在函式裡組。
DATE_SLOTS = [
    ('TRIP_DATE',      r'TRIP_DATE\s*=\s*"(\d{4})-(\d{2})-(\d{2})"'),
    ('meta description', r'<meta name="description" content="(\d{4})/(\d{1,2})/(\d{1,2})'),
    ('導覽副標',        r'>(\d{4})/(\d{1,2})/(\d{1,2}) 活動紀錄<'),
    ('行程已完成提示',   r'時刻與里程來自 (\d{4})/(\d{1,2})/(\d{1,2}) 當天'),
    ('頁腳',           r'\|\s*(\d{4}) 年 (\d{1,2}) 月 (\d{1,2}) 日'),
]


def page_dates(s, name):
    """回傳 [(來源, 正規化日期 或 ('md', 月, 日))]。"""
    out = []
    for label, pat in DATE_SLOTS:
        m = re.search(pat, s)
        if m:
            out.append((label, norm_date(*m.groups())))
    m = re.search(r"tracks/%s-(\d{4})-(\d{2})-(\d{2})\.js" % re.escape(name), s)
    if m:
        out.append(('軌跡檔名', norm_date(*m.groups())))
    # 日期戳只有月日，另外比
    m = re.search(r'class="stamp">\s*(\d{1,2})月(\d{1,2})日', s)
    if m:
        out.append(('日期戳', ('md', int(m.group(1)), int(m.group(2)))))
    return out


TOTAL_SLOTS = [
    ('meta description', r'<meta name="description" content="[^"]*?全程 *約? *([\d.]+) *公里'),
    ('日期戳旁摘要',      r'(?:實走紀錄|實走)[^<]*?·\s*約?\s*([\d.]+)\s*KM'),
    # 統計列：大字後面跟著「實走里程」或「總里程」的標籤
    ('統計列',           r'>\s*約?\s*([\d.]+)\s*(?:<span[^>]*>)?\s*(?:km)?\s*</(?:span|div)>\s*'
                        r'(?:</div>)?\s*<div[^>]*>\s*(?:實走里程|總里程)'),
    ('頁腳',            r'·\s*約?\s*([\d.]+) km</p>'),
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
    """回傳 [(來源, 分鐘)]。行程時長同樣散在四、五處，寫法還有兩種
    （「3 小時 26 分」與「3:26」），所以一律換算成分鐘再比。"""
    out = []
    def mins(h, m):
        return int(h) * 60 + int(m)
    m = re.search(r'實走紀錄[^<]*?·\s*(\d+)\s*小時\s*(\d+)\s*分', s)
    if m:
        out.append(('日期戳旁摘要', mins(*m.groups())))
    m = re.search(r'>\s*(\d+):(\d{2})\s*</div>\s*<div[^>]*>\s*實走耗時', s)
    if m:
        out.append(('統計列', mins(*m.groups())))
    m = re.search(r'全程\s*(\d+)\s*小時\s*(\d+)\s*分', s)
    if m:
        out.append(('時間軸小標', mins(*m.groups())))
    m = re.search(r'<meta name="description"[^"]*?(\d+)\s*小時\s*(\d+)\s*分', s)
    if m:
        out.append(('meta description', mins(*m.groups())))
    return out


def page_gains(s):
    """回傳 [(來源, 公尺)]。累計上升在統計列與海拔圖說明各一份。"""
    out = []
    m = re.search(r'>\s*~?(\d+)\s*</div>\s*<div[^>]*>\s*累計上升', s)
    if m:
        out.append(('統計列', m.group(1)))
    m = re.search(r'因此標\s*<strong>~?(\d+)\s*公尺</strong>', s)
    if m:
        out.append(('海拔圖說明', m.group(1)))
    return out


def page_summits(s):
    """回傳 (統計列宣稱的最高點, schedule 的最高 ele)，缺任一邊回 None。

    這裡的關係是**不等式不是等式**。航點是軌跡的子集，所以統計列的最高點必然
    ≥ 最高航點的 ele；低於它才是錯的。第一版寫成等式，馬上把 hushan 誤判成錯——
    那頁的腳本明寫「全程最高處其實不在任何航點上：軌跡在 2.01 km 處讀到 184 m」，
    比最高航點的 175 高，是刻意且有說明的。與其加忽略名單，不如把判準改對。"""
    m = re.search(r'<div class="text-3xl font-black"[^>]*>\s*([\d,]+)\s*</div>\s*'
                  r'<div[^>]*>\s*最高點', s)
    eles = [int(x) for x in re.findall(r'\bele:\s*(\d+)', s)]
    if not m or not eles:
        return None
    return int(m.group(1).replace(',', '')), max(eles)


def loc_elevations(s):
    """航點名稱裡的 (H643m) 必須等於該航點的 ele。兩者都是人打的，會漂。"""
    bad = []
    for o in re.finditer(r'\{[^{}]*\bele:\s*(\d+)[^{}]*\}', s):
        blk = o.group(0)
        loc = re.search(r'loc:\s*"([^"]*)"', blk)
        h = re.search(r'[（(]\s*[Hh]\s*([\d,]+)\s*m\s*[)）]', loc.group(1)) if loc else None
        if h and h.group(1).replace(',', '') != o.group(1):
            bad.append((loc.group(1), h.group(1), o.group(1)))
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
    ds = page_dates(s, name)
    full = [(src, v) for src, v in ds if isinstance(v, str)]
    if name in idx:
        full.append(('index.html 的卡片', idx[name]['date']))
    if full:
        vals = {v for _, v in full}
        if len(vals) > 1:
            problems.append('日期不一致 → ' + '、'.join('%s=%s' % (s_, v) for s_, v in full))
        else:
            only = next(iter(vals))
            _, mo, d = only.split('-')
            for src, v in ds:
                if isinstance(v, tuple) and (v[1], v[2]) != (int(mo), int(d)):
                    problems.append('%s 是 %d月%d日，其餘是 %s' % (src, v[1], v[2], only))

    # ── 總里程 ────────────────────────────────────────────
    ts = page_totals(s)
    if name in idx and idx[name]['km']:
        ts.append(('index.html 的卡片', idx[name]['km']))
    if ts:
        vals = {float(v) for _, v in ts}
        if len(vals) > 1:
            problems.append('總里程不一致 → ' + '、'.join('%s=%s' % (s_, v) for s_, v in ts))

    # ── 行程時長 ──────────────────────────────────────────
    ds_ = page_durations(s)
    if len({v for _, v in ds_}) > 1:
        problems.append('行程時長不一致 → ' +
                        '、'.join('%s=%d:%02d' % (a, b // 60, b % 60) for a, b in ds_))

    # ── 累計上升 ──────────────────────────────────────────
    gs = page_gains(s)
    if len({v for _, v in gs}) > 1:
        problems.append('累計上升不一致 → ' + '、'.join('%s=%s' % x for x in gs))

    # ── 最高點海拔 ────────────────────────────────────────
    ss = page_summits(s)
    if ss and ss[0] < ss[1]:
        problems.append('統計列的最高點 %d m 低於最高航點的 %d m' % ss)

    for loc, h, ele in loc_elevations(s):
        problems.append('%s 的名稱寫 %s m，ele 卻是 %s' % (loc, h, ele))

    # ── 有天氣卡的已完成行程必須有 TRIP_DATE ──────────────
    # 這是真正會壞的組合：天氣卡沒有行程日就只會顯示今日天氣，而且不會說明
    # 為什麼——fetchWeather() 靠 cfg.tripDate 才知道要標「行程日預報」還是
    # 「行程日已過，顯示今日天氣」。
    # 反過來沒有天氣卡的頁不算問題：TRIP_DATE 對它們是空轉的。那是功能缺口，
    # 不是故障，別在這裡報。（2026-08-04：huoyianshan 與 meihuashan 原本是唯二
    # 沒有天氣卡的頁，已補上，現在 22 頁全有。這條規則仍然留著——候選頁若哪天
    # 加了天氣卡卻忘了 TRIP_DATE，一樣要擋。）
    if name in idx and 'id="weather-main"' in s and not any(src == 'TRIP_DATE' for src, _ in ds):
        problems.append('有天氣卡卻沒有 TRIP_DATE——會顯示今日天氣而不說明原因')

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
