"""四支 Python 工具共用的兩件小事。2026-09 第三輪審查抓到它們各抄一份：
切到倉庫根目錄的那一行寫了四次；fact_check 還自己用 `\\{[^{}]*\\}` 切航點物件，
而 spec_sweep 早有括號配對版、註明 regex 會漏讀（2026-08-03 就漏過 nanshijiao 三個航點）。"""
import functools
import os


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
