#!/usr/bin/env python3
"""評估新路線：把一疊公開 GPX 依走法分群，比較每種走法的樣本數、距離中位數（含範圍）、
爬升、別人的實際耗時與本隊預估（docs/PLANNING_RULES.md §二第 2 步、§三）。

為什麼要有這支：2026-11-03 之前這一步每次都在對話裡現寫——分群的半徑、爬升的視窗、
中位數怎麼取，每次略有不同，於是同一條步道兩次評估給出的數字對不上。這裡把算法固定下來，
評估時只剩「資料從哪來」與「怎麼選」兩件要人判斷的事。

用法：
  python3 tools/gpx_cluster.py <GPX目錄或檔案…> [選項]
  選項：
    --anchor 名稱=lat,lng   命名的錨點（登山口、車站、山頭…），可重複。軌跡的起訖點會對到
                           最近的錨點（60 m 內），經過的錨點則成為走法的一部分。
                           沒給錨點時，起訖點以 300 m 的格子自動命名為「起點 A」「終點 B」。
    --radius 60            錨點的命中半徑（公尺）
    --pace 1.5             本隊配速（km/h），預估時間＝距離中位數 ÷ 配速，取整到 5 分鐘
    --official 5.95        健行筆記標示的全程里程（km）；給了就另算「照標示值縮放」的距離
    --segments 航點.json   另一種模式：給一串航點（[{"loc","lat","lng"}…]），對每條軌跡找
                           這些航點（依序、半徑內），回報各段距離的中位數與直線下限，
                           並依 --pace 與 --start 推出行前頁的 time（PLANNING_RULES §三）
    --start 08:00          --segments 模式的出發時刻
    --json                 另印一份 JSON（給後續建頁用）

輸出的每個數字都是從 GPX 算的；GPX 本身從哪裡來、是不是這條步道，要在對話裡交代。"""
import argparse
import glob
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from papa_gpx import read_gpx, cum_dist, gain_estimate, hav, nearest, fmt_hm, round5  # noqa: E402


def gather(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, '**', '*.gpx'), recursive=True))
        else:
            files.append(p)
    return files


def track_stats(g):
    pts = g['points']
    if len(pts) < 2:
        return None
    cd = cum_dist(pts)
    times = [p[3] for p in pts if p[3] is not None]
    dur = (times[-1] - times[0]).total_seconds() / 60 if len(times) >= 2 else None
    gains = gain_estimate(pts)
    gain = gains.get(31) if gains else None
    return {'km': cd[-1] / 1000, 'min': dur, 'gain': gain, 'gains': gains, 'n': len(pts),
            'start': pts[0][:2], 'end': pts[-1][:2]}


def label_point(latlng, anchors, radius, grid_cache, kind):
    for name, (la, ln) in anchors.items():
        if hav(la, ln, *latlng) <= radius:
            return name
    key = (round(latlng[0] / 0.0027), round(latlng[1] / 0.003))      # 約 300 m 的格子
    if key not in grid_cache:
        grid_cache[key] = '%s%s' % (kind, chr(ord('A') + len(grid_cache) % 26))
    return grid_cache[key]


def passes(pts, anchors, radius):
    """軌跡經過哪些錨點（依首次命中的順序）。"""
    hit = []
    for name, (la, ln) in anchors.items():
        i, d = nearest(pts, la, ln)
        if d <= radius:
            hit.append((i, name))
    return [n for _, n in sorted(hit)]


def median_range(xs, fmt):
    xs = [x for x in xs if x is not None]
    if not xs:
        return '—'
    m = statistics.median(xs)
    if len(xs) == 1:
        return fmt(m)
    return '%s（%s–%s）' % (fmt(m), fmt(min(xs)), fmt(max(xs)))


def cluster_mode(files, anchors, radius, pace, official, want_json):
    grid = {}
    groups = {}
    rows = []
    for f in files:
        try:
            g = read_gpx(f)
        except Exception as e:                               # 壞檔不要讓整批停下來
            print('略過 %s：%s' % (f, e), file=sys.stderr)
            continue
        st = track_stats(g)
        if not st:
            continue
        s = label_point(st['start'], anchors, radius, grid, '起點')
        e = label_point(st['end'], anchors, radius, grid, '終點')
        via = [v for v in passes(g['points'], anchors, radius) if v not in (s, e)]
        key = '%s → %s' % (s, e) + ('（經 %s）' % '、'.join(via) if via else '')
        groups.setdefault(key, []).append(st)
        rows.append((os.path.basename(f), key, st))

    print('%d 條軌跡，%d 種走法\n' % (len(rows), len(groups)))
    hdr = '| 走法 | 樣本 | 距離中位數 km（範圍） | 爬升 m（移動中位數 31 點） | 他人耗時（範圍） | 本隊預估 @%.1f km/h |' % pace
    print(hdr)
    print('|---|--:|---|---|---|---|')
    out = []
    for key, sts in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        kms = [s['km'] for s in sts]
        med_km = statistics.median(kms)
        est = round5(med_km / pace * 60)
        note = ''
        if official:
            note = '；照標示 %.2f km 縮放' % official
        print('| %s | %d | %s | %s | %s | %s（%.2f km%s） |' % (
            key, len(sts), median_range(kms, lambda x: '%.2f' % x),
            median_range([s['gain'] for s in sts], lambda x: '%d' % x),
            median_range([s['min'] for s in sts], lambda x: fmt_hm(int(x))),
            fmt_hm(est), med_km, note))
        out.append({'route': key, 'n': len(sts), 'km_median': round(med_km, 2),
                    'km_range': [round(min(kms), 2), round(max(kms), 2)],
                    'gain_median': statistics.median([s['gain'] for s in sts if s['gain'] is not None]) if any(s['gain'] for s in sts) else None,
                    'minutes_median': statistics.median([s['min'] for s in sts if s['min'] is not None]) if any(s['min'] for s in sts) else None,
                    'estimate_minutes': est})
    print('\n逐條：')
    for name, key, st in rows:
        print('  %-40s %-30s %.2f km  爬升 %s  耗時 %s  %d 點' % (
            name[:40], key[:30], st['km'], st['gain'] if st['gain'] is not None else '—',
            fmt_hm(int(st['min'])) if st['min'] else '—', st['n']))
    print('\n爬升是三個視窗（15/31/61 點）的移動中位數推估，取 31；三個視窗若差很多，該條軌跡的高程不可信。')
    if want_json:
        print(json.dumps(out, ensure_ascii=False, indent=1))


def segments_mode(files, waypoints, radius, pace, start, official, want_json):
    """每一段取各軌跡的中位數；有剛好照順序走的軌跡時，另給「照標示值縮放」的版本。"""
    segs = [[] for _ in waypoints[1:]]
    ordered = []                                              # 依序經過全部航點的軌跡
    for f in files:
        try:
            g = read_gpx(f)
        except Exception as e:
            print('略過 %s：%s' % (f, e), file=sys.stderr)
            continue
        pts = g['points']
        if len(pts) < 2:
            continue
        cd = cum_dist(pts)
        idx = []
        for w in waypoints:
            i, d = nearest(pts, w['lat'], w['lng'])
            idx.append(i if d <= radius else None)
        for k in range(1, len(waypoints)):
            if idx[k - 1] is not None and idx[k] is not None and idx[k] > idx[k - 1]:
                segs[k - 1].append((cd[idx[k]] - cd[idx[k - 1]]) / 1000)
        if all(i is not None for i in idx) and idx == sorted(idx):
            ordered.append((os.path.basename(f), [cd[i] / 1000 for i in idx]))

    print('%d 條軌跡；依序經過全部 %d 個航點的有 %d 條' % (len(files), len(waypoints), len(ordered)))
    if ordered:
        print('  ' + '、'.join(n for n, _ in ordered))
    cum, t, rows = 0.0, start, []
    anchor_t, anchor_d = start, 0.0
    print('\n| # | 航點 | 段距中位數 km（樣本） | 直線下限 km | 累計 km | time |')
    print('|--:|---|---|--:|--:|--:|')
    for k, w in enumerate(waypoints):
        if k == 0:
            seg, n, sl = 0.0, 0, 0.0
        else:
            prev = waypoints[k - 1]
            sl = hav(prev['lat'], prev['lng'], w['lat'], w['lng']) / 1000
            if w.get('shuttle'):
                seg, n = 0.0, 0
            else:
                xs = segs[k - 1]
                n = len(xs)
                seg = statistics.median(xs) if xs else None
                if seg is not None and seg < sl:
                    seg = sl                                  # 每段不得短於直線距離
            cum += seg or 0.0
            if w.get('shuttle'):
                anchor_t, anchor_d = None, cum                # 接駁段之後以該點時刻重新起算（由人填）
        if k and w.get('shuttle'):
            t = None
        elif anchor_t is not None:
            t = anchor_t + round5((cum - anchor_d) / pace * 60)
        rows.append({'loc': w['loc'], 'seg_km': None if seg is None else round(seg, 2), 'samples': n,
                     'straight_km': round(sl, 2), 'dist': round(cum, 2), 'time': fmt_hm(t) if t is not None else '—'})
        print('| %d | %s | %s | %.2f | %.2f | %s |' % (
            k, w['loc'], ('%.2f（%d）' % (seg, n)) if seg is not None else '查不到（0）', sl, cum, rows[-1]['time']))
    if official and ordered:
        print('\n照標示值縮放（健行筆記 %.2f km）：' % official)
        name, cds = ordered[0]
        raw = cds[-1] - cds[0]
        for k, w in enumerate(waypoints):
            print('  %-24s %.2f km' % (w['loc'], (cds[k] - cds[0]) * official / raw))
        print('  依據 %s（原始累計 %.2f km）' % (name, raw))
    print('\n「查不到」的段是沒有任何軌跡依序經過兩端航點，要換資料或用直線距離標「補估」。')
    if want_json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('paths', nargs='+')
    ap.add_argument('--anchor', action='append', default=[])
    ap.add_argument('--radius', type=float, default=60.0)
    ap.add_argument('--pace', type=float, default=1.5)
    ap.add_argument('--official', type=float)
    ap.add_argument('--segments')
    ap.add_argument('--start', default='08:00')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    anchors = {}
    for s in a.anchor:
        name, _, ll = s.partition('=')
        la, ln = ll.split(',')
        anchors[name] = (float(la), float(ln))
    files = gather(a.paths)
    if not files:
        print('沒有 GPX', file=sys.stderr)
        return 2
    if a.segments:
        wps = json.load(open(a.segments, encoding='utf-8'))
        h, m = a.start.split(':')
        segments_mode(files, wps, a.radius, a.pace, int(h) * 60 + int(m), a.official, a.json)
    else:
        cluster_mode(files, anchors, a.radius, a.pace, a.official, a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
