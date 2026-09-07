#!/usr/bin/env python3
"""README 的檔案樹由 manifest.json 產生。

為什麼：README 的樹（每個檔一句註解）跟 manifest.json（每個檔一段用途）是同一件事的
兩份，靠人手同步。2026-08 的審查發現樹漏了四個已完成頁，2026-09 又漏了 CONTEXT.md 與
ADR——manifest 反而一直是齊的。所以清單只留 manifest 一份：每個條目多一個 short 欄位
（樹上那一句），這支把樹印出來寫進 README 的標記區塊；spec_sweep 比對區塊與產生結果，
不一致就紅。加一個檔案只改 manifest。

已完成頁的日期從軌跡檔名推導（assets/tracks/<頁名>-<日期>.js），不另外寫；分組標題的
頁數也是算出來的，所以「十六頁附實走 GPS 軌跡」這種數字不會再漂。

用法：python3 tools/manifest_tree.py          印出樹
      python3 tools/manifest_tree.py --write  寫進 README.md 的 manifest-tree 標記區塊
      python3 tools/manifest_tree.py --check  README 的區塊跟產生結果不同就回傳 1"""
import json, re, os, sys

os.chdir(os.environ.get('PAPA_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

START, END = '<!-- manifest-tree:start -->', '<!-- manifest-tree:end -->'
COL = 32        # 註解對齊的欄位
CN = '零一二三四五六七八九十'


def cn(n):
    if n < 11:
        return CN[n]
    return CN[10] + (CN[n - 10] if n < 20 else '') if n < 20 else CN[n // 10] + CN[10] + (CN[n % 10] if n % 10 else '')


def entries():
    m = json.load(open('manifest.json', encoding='utf-8'))
    out = []

    def walk(x):
        if isinstance(x, dict):
            if isinstance(x.get('path'), str):
                out.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(m)
    # 同一個路徑可能出現在 read_first 與 docs 兩處：留第一條，short 缺的話從後面那條補
    # （spec_sweep 也拿這份清單核對倉庫與 short，兩邊看到的是同一組條目）
    by, uniq = {}, []
    for e in out:
        first = by.get(e['path'])
        if first is None:
            by[e['path']] = e
            uniq.append(e)
        elif not first.get('short') and e.get('short'):
            first['short'] = e['short']
    return uniq


def render():
    items = entries()
    by = {e['path']: e for e in items}
    order = [e['path'] for e in items]

    def short(path):
        e = by.get(path, {})
        return e.get('short') or ''

    tracks = sorted(p for p in by if p.startswith('assets/tracks/') and p.endswith('.js'))
    date_of = {}
    for t in tracks:
        mm = re.match(r'assets/tracks/(.+)-(\d{4}-\d{2}-\d{2})\.js$', t)
        if mm:
            date_of[mm.group(1)] = mm.group(2)
    pages = [p for p in order if p.endswith('.html') and '/' not in p and p != 'index.html']
    done = sorted([p for p in pages if p[:-5] in date_of], key=lambda p: date_of[p[:-5]], reverse=True)
    cand = [p for p in pages if p[:-5] not in date_of]

    lines = ['PaPaTeam/']

    def row(prefix, name, note, last):
        left = prefix + ('└── ' if last else '├── ') + name
        lines.append((left.ljust(COL) + ' # ' + note) if note else left)

    def children(dirpath):
        """manifest 順序：先檔案再子目錄；子目錄以第一個成員出現的位置排。"""
        files, subdirs = [], []
        for p in order:
            if not p.startswith(dirpath) or p == dirpath:
                continue
            rest = p[len(dirpath):]
            if '/' in rest.rstrip('/'):
                d = dirpath + rest.split('/')[0] + '/'
                if d not in subdirs:
                    subdirs.append(d)
            elif rest.endswith('/'):
                if p not in subdirs:
                    subdirs.append(p)
            else:
                files.append(p)
        if dirpath == 'assets/tracks/':
            files.sort(key=lambda p: re.search(r'(\d{4}-\d{2}-\d{2})', p).group(1) if re.search(r'\d{4}-\d{2}-\d{2}', p) else '', reverse=True)
        return files, subdirs

    def render_dir(dirpath, prefix, last_dir):
        files, subdirs = children(dirpath)
        kids = [(f, False) for f in files] + [(d, True) for d in subdirs]
        for i, (p, is_dir) in enumerate(kids):
            last = i == len(kids) - 1
            name = p[len(dirpath):]
            row(prefix, name, short(p), last)
            if is_dir:
                render_dir(p, prefix + ('    ' if last else '│   '), last)

    # 首頁與詳情頁
    row('', 'index.html', short('index.html'), False)
    lines.append('│')
    lines.append('│   已完成（%s頁附實走 GPS 軌跡）' % cn(len(done)))
    for p in done:
        row('', p, '%s（%s）' % (by[p].get('title', ''), date_of[p[:-5]]), False)
    lines.append('│   候選（%s頁）' % cn(len(cand)))
    for p in cand:
        row('', p, by[p].get('title', ''), False)
    lines.append('│')

    # 目錄與其餘檔案：照這個順序分組，各目錄內部照 manifest 順序
    groups = [['assets/'], ['tools/'], ['manifest.json', 'integrity.json', '.github/workflows/'], ['.gitignore'],
              [p for p in order if p.endswith('.md') and '/' not in p] + ['docs/adr/']]
    # 分組是寫死的，但清單不是：manifest 裡任何不屬於上面任一組、也不歸任一組目錄管的
    # 頂層條目，另成最後一組印出來。2026-09 的審查抓到之前是靜靜漏印——樹上看不到，
    # spec_sweep 又只比對「README 等於產生結果」，所以漏了也不會紅。
    covered = [p for g in groups for p in g]
    under = lambda p, dirs: any(p != d and p.startswith(d) for d in dirs if d.endswith('/'))
    rest = [p for p in order if p not in covered and p not in pages and p != 'index.html' and not under(p, covered)]
    # 目錄條目底下的檔案交給 render_dir 印，不重複列
    rest = [p for p in rest if not under(p, rest)]
    if rest:
        groups.append(rest)
    flat = [p for g in groups for p in g]
    for gi, g in enumerate(groups):
        for p in g:
            last = p == flat[-1]
            row('', p, short(p), last)
            if p.endswith('/'):
                render_dir(p, '    ' if last else '│   ', last)
        if gi < len(groups) - 1:
            lines.append('│')
    return '```\n' + '\n'.join(lines) + '\n```'


def readme_block():
    s = open('README.md', encoding='utf-8').read()
    mm = re.search(re.escape(START) + r'\n([\s\S]*?)\n' + re.escape(END), s)
    return mm.group(1) if mm else None


def main():
    tree = render()
    if '--write' in sys.argv:
        s = open('README.md', encoding='utf-8').read()
        if START not in s or END not in s:
            print('README.md 沒有 manifest-tree 標記，先放好 %s 與 %s' % (START, END))
            return 1
        s = re.sub(re.escape(START) + r'\n[\s\S]*?\n' + re.escape(END),
                   lambda _: START + '\n' + tree + '\n' + END, s)
        open('README.md', 'w', encoding='utf-8').write(s)
        print('README.md 的檔案樹已更新（%d 行）' % tree.count('\n'))
        return 0
    if '--check' in sys.argv:
        ok = readme_block() == tree
        print('README 檔案樹%s' % ('與 manifest 一致' if ok else '過期——跑 --write'))
        return 0 if ok else 1
    print(tree)
    return 0


if __name__ == '__main__':
    sys.exit(main())
