"""四支 Python 工具共用的兩件小事。2026-09 第三輪審查抓到它們各抄一份：
切到倉庫根目錄的那一行寫了四次；fact_check 還自己用 `\\{[^{}]*\\}` 切航點物件，
而 spec_sweep 早有括號配對版、註明 regex 會漏讀（2026-08-03 就漏過 nanshijiao 三個航點）。"""
import functools
import os
import re


def chdir_root():
    """工具都以倉庫根目錄為工作目錄；PAPA_ROOT 可覆寫（CI 或從別處呼叫時）。"""
    os.chdir(os.environ.get('PAPA_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@functools.lru_cache(maxsize=None)
def schedule_objects(s):
    """以括號配對切出 schedule 的每個物件。用貪婪 regex 會跨物件吃字元，
    2026-08-03 就是這樣漏讀了 nanshijiao 17 個航點裡的 3 個。
    多個檢查各自呼叫一次，所以以整頁原始碼為鍵快取；回傳 tuple，不要就地改。"""
    i = s.find('const schedule')
    if i < 0:
        return ()
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


def page_state(path, tracked):
    """行程三態，跟 detail.js 的 isRecord() 同一套判準：有軌跡檔＝已完成；沒有軌跡檔但
    PaPaDetail.init 的 trip 給了日期（計畫頁只給日期、不給 km）＝計畫；都沒有＝候選。
    回傳 (狀態, 計畫日期或 None)。2026-09-24 shanying 定了出發日才有第一個計畫頁，
    在那之前 spec_sweep 與 manifest_tree 只認得已完成／候選兩種。"""
    if path[:-5] in tracked:
        return 'completed', None
    try:
        s = open(path, encoding='utf-8').read()
    except OSError:
        return 'candidate', None
    m = re.search(r'\btrip:\s*\{([^{}]*)\}', s)
    d = m and re.search(r'\bdate:\s*[\'"](\d{4}-\d{2}-\d{2})[\'"]', m.group(1))
    return ('planned', d.group(1)) if d else ('candidate', None)
