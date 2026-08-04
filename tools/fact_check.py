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


def page_dates(s, name):
    """回傳 [(來源, 正規化日期 或 ('md', 月, 日))]。只取結構化的位置，不掃內文——
    內文合法地會提到別的日期（「2026 年整理 GPX 時補回」「同治六年」）。"""
    out = []
    m = re.search(r'TRIP_DATE\s*=\s*"(\d{4})-(\d{2})-(\d{2})"', s)
    if m:
        out.append(('TRIP_DATE', norm_date(*m.groups())))
    m = re.search(r'<meta name="description" content="(\d{4})/(\d{1,2})/(\d{1,2})', s)
    if m:
        out.append(('meta description', norm_date(*m.groups())))
    m = re.search(r'>(\d{4})/(\d{1,2})/(\d{1,2}) 活動紀錄<', s)
    if m:
        out.append(('導覽副標', norm_date(*m.groups())))
    m = re.search(r'時刻與里程來自 (\d{4})/(\d{1,2})/(\d{1,2}) 當天', s)
    if m:
        out.append(('行程已完成提示', norm_date(*m.groups())))
    m = re.search(r'\|\s*(\d{4}) 年 (\d{1,2}) 月 (\d{1,2}) 日', s)
    if m:
        out.append(('頁腳', norm_date(*m.groups())))
    m = re.search(r"tracks/%s-(\d{4})-(\d{2})-(\d{2})\.js" % re.escape(name), s)
    if m:
        out.append(('軌跡檔名', norm_date(*m.groups())))
    # 日期戳只有月日，另外比
    m = re.search(r'class="stamp">\s*(\d{1,2})月(\d{1,2})日', s)
    if m:
        out.append(('日期戳', ('md', int(m.group(1)), int(m.group(2)))))
    return out


def page_totals(s):
    """回傳 [(來源, 里程字串)]。只取「講總里程」的位置。"""
    out = []
    m = re.search(r'<meta name="description" content="[^"]*?全程 *約? *([\d.]+) *公里', s)
    if m:
        out.append(('meta description', m.group(1)))
    m = re.search(r'(?:實走紀錄|實走)[^<]*?·\s*約?\s*([\d.]+)\s*KM', s)
    if m:
        out.append(('日期戳旁摘要', m.group(1)))
    # 統計列：大字後面跟著「實走里程」或「總里程」的標籤
    for m in re.finditer(r'>\s*約?\s*([\d.]+)\s*(?:<span[^>]*>)?\s*(?:km)?\s*</(?:span|div)>\s*(?:</div>)?\s*'
                         r'<div[^>]*>\s*(實走里程|總里程)', s):
        out.append(('統計列', m.group(1)))
        break
    m = re.search(r'·\s*約?\s*([\d.]+) km</p>', s)
    if m:
        out.append(('頁腳', m.group(1)))
    return out


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

    # ── 有天氣卡的已完成行程必須有 TRIP_DATE ──────────────
    # 這是真正會壞的組合：天氣卡沒有行程日就只會顯示今日天氣，而且不會說明
    # 為什麼——fetchWeather() 靠 cfg.tripDate 才知道要標「行程日預報」還是
    # 「行程日已過，顯示今日天氣」。
    # 反過來沒有天氣卡的頁（huoyianshan、meihuashan）不算問題：TRIP_DATE 對它們
    # 是空轉的。那是功能缺口，不是故障，別在這裡報。
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
