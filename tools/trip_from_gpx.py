#!/usr/bin/env python3
"""已完成頁的數字從當天 GPS 軌跡重算（docs/PLANNING_RULES.md §四「已完成頁」）：
簡化軌跡存成 assets/tracks/<頁名>-<日期>.js、各航點的抵達時刻與累計里程、沒有地名的停留點、
爬升推估、最高點、總耗時。頁面本身仍由人（或 Claude）改，這支只給數字與軌跡檔——
數字的算法只有這一份，改頁的人不必再想一次視窗要取幾點。

用法：
  python3 tools/trip_from_gpx.py <GPX> --page <頁名> --date YYYY-MM-DD --waypoints 航點.json [選項]
  航點.json：[{"loc": "…", "lat": …, "lng": …, "plan": "08:10"（選填）, "shuttle": true（接駁段終點，選填）}…]
             通常直接從計畫頁的 schedule 抄出來（loc、lat、lng、time→plan）。
  選項：
    --tol 5          Douglas–Peucker 容許偏差（公尺）
    --snap 40        航點離軌跡最近點超過這個距離（公尺）就標「（未走）」候選，要人確認
    --stop-min 5     停留幾分鐘以上算休息點
    --stop-radius 30 停留的範圍（公尺）
    --from HH:MM     只從這個時刻起算（例：shanying 出發前在車站繞了一圈，自 08:35 起算）
    --write          真的寫 assets/tracks/<頁名>-<日期>.js（沒給就只印）
    --json           另印一份 JSON（schedule 的草稿）

印出的里程用**簡化後**的累計距離（與 detail.js 畫的線同源）；高程只用來推估爬升與最高點，
航點的 ele 仍照 PLANNING_RULES §三取公開標高，這裡印的 GPS 中位數是對照用。"""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from papa_gpx import read_gpx, cum_dist, douglas_peucker, gain_estimate, hav, nearest, ele_median_near, fmt_hm  # noqa: E402


def find_stops(pts, min_minutes, radius, exclude, exclude_radius):
    """30 m 內停留 5 分鐘以上、附近又沒有已知航點的地方。回傳 [(起索引, 迄索引)]。"""
    stops, i, n = [], 0, len(pts)
    while i < n:
        j = i
        while j + 1 < n and hav(pts[i][0], pts[i][1], pts[j + 1][0], pts[j + 1][1]) <= radius:
            j += 1
        if pts[j][3] and pts[i][3] and (pts[j][3] - pts[i][3]).total_seconds() >= min_minutes * 60:
            la = statistics.median(p[0] for p in pts[i:j + 1])
            ln = statistics.median(p[1] for p in pts[i:j + 1])
            if all(hav(la, ln, w['lat'], w['lng']) > exclude_radius for w in exclude):
                stops.append((i, j, la, ln))
            i = j + 1
        else:
            i += 1
    return stops


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('gpx')
    ap.add_argument('--page', required=True)
    ap.add_argument('--date', required=True)
    ap.add_argument('--waypoints', required=True)
    ap.add_argument('--tol', type=float, default=5.0)
    ap.add_argument('--snap', type=float, default=40.0)
    ap.add_argument('--stop-min', type=float, default=5.0)
    ap.add_argument('--stop-radius', type=float, default=30.0)
    ap.add_argument('--from', dest='from_t')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    g = read_gpx(a.gpx)
    pts = g['points']
    if a.from_t:
        h, m = map(int, a.from_t.split(':'))
        pts = [p for p in pts if p[3] and (p[3].hour, p[3].minute) >= (h, m)] or pts
    if len(pts) < 3:
        print('軌跡點不夠', file=sys.stderr)
        return 2
    wps = json.load(open(a.waypoints, encoding='utf-8'))

    keep = douglas_peucker(pts, a.tol)
    simp = [pts[i] for i in keep]
    cd_raw, cd_simp = cum_dist(pts), cum_dist(simp)
    total_km = cd_simp[-1] / 1000
    t0, t1 = pts[0][3], pts[-1][3]
    duration = int((t1 - t0).total_seconds() // 60) if t0 and t1 else None
    gains = gain_estimate(pts)
    eles = [p[2] for p in pts if p[2] is not None]
    summit = max(eles) if eles else None

    print('%s %s：原始 %d 點 → 簡化 %d 點（容差 %.0f m），總里程 %.2f km（原始 %.2f km）'
          % (a.page, a.date, len(pts), len(simp), a.tol, total_km, cd_raw[-1] / 1000))
    if duration is not None:
        print('起錄 %s、收錄 %s，耗時 %s' % (t0.strftime('%H:%M'), t1.strftime('%H:%M'), fmt_hm(duration)))
    if gains:
        print('爬升推估（移動中位數 15/31/61 點）：%s m——三個數字要收斂才採用，頁面上註明是推估'
              % '／'.join(str(gains[w]) for w in sorted(gains)))
    if summit is not None:
        print('GPS 最高高程 %.0f m（對照用；trip.summit 取最高點航點的公開標高）' % summit)

    # 各航點：抵達時刻＝軌跡最近點的時間；里程＝該點在簡化軌跡上的累計距離
    rows = []
    print('\n| # | 航點 | 時刻 | plan | 累計 km | 離軌跡 m | GPS 高程中位數 | 備註 |')
    print('|--:|---|--:|--:|--:|--:|--:|---|')
    for k, w in enumerate(wps):
        i, d = nearest(pts, w['lat'], w['lng'])
        si, _ = nearest(simp, w['lat'], w['lng'])
        em = ele_median_near(pts, w['lat'], w['lng'])
        note = ''
        if d > a.snap and not w.get('shuttle'):
            note = '離軌跡 %.0f m——沒走到？標「（未走）」、time 寫 —、不給 dist；或是接駁／集合點（dist 維持 0）' % d
        elif rows and cd_simp[si] / 1000 < rows[-1]['dist']:
            note = '里程倒退：軌跡先經過這裡再回頭，或航點順序不對'
        row = {'loc': w['loc'], 'time': pts[i][3].strftime('%H:%M') if pts[i][3] else '—',
               'plan': w.get('plan'), 'dist': round(cd_simp[si] / 1000, 2), 'off_m': round(d),
               'ele_gps': em, 'idx': i, 'note': note}
        rows.append(row)
        print('| %d | %s | %s | %s | %.2f | %d | %s | %s |' % (
            k, w['loc'], row['time'], w.get('plan') or '', row['dist'], row['off_m'],
            em if em is not None else '—', note))

    stops = find_stops(pts, a.stop_min, a.stop_radius, wps, a.stop_radius)
    if stops:
        print('\n沒有地名的停留點（%.0f m 內停 %.0f 分鐘以上、附近沒有航點）——命名「第N休息點」，desc 寫明「這個點沒有地名」：' % (a.stop_radius, a.stop_min))
        for n, (i, j, la, ln) in enumerate(stops, 1):
            si, _ = nearest(simp, la, ln)
            print('  第%d休息點  %s–%s（%d 分）  lat %.6f lng %.6f  累計 %.2f km  GPS 高程 %s' % (
                n, pts[i][3].strftime('%H:%M'), pts[j][3].strftime('%H:%M'),
                int((pts[j][3] - pts[i][3]).total_seconds() // 60), la, ln, cd_simp[si] / 1000,
                ele_median_near(pts, la, ln) or '—'))

    js_path = 'assets/tracks/%s-%s.js' % (a.page, a.date)
    key = '%s-%s' % (a.page, a.date)
    body = ',\n'.join('  ' + ', '.join('[%.5f,%.5f]' % (p[0], p[1]) for p in simp[r:r + 4])
                      for r in range(0, len(simp), 4))
    js = ('/* ============================================================\n'
          '   %s — %s 實走 GPS 軌跡\n'
          '   ------------------------------------------------------------\n'
          '   來源：GPX（原始 %d 點）。以 Douglas–Peucker 簡化，容許偏差 %.0f 公尺，\n'
          '   作法見 nanshijiao-2026-08-02.js 的說明；只留經緯度（高程不放，見\n'
          '   manifest.json 的 conventions.elevation_source）。簡化後 %d 點、%.2f km。\n'
          '   由 tools/trip_from_gpx.py 產生。\n'
          '   ============================================================ */\n'
          'window.PaPaTracks = window.PaPaTracks || {};\n'
          "window.PaPaTracks['%s'] = [\n%s\n];\n") % (a.page, a.date, len(pts), a.tol, len(simp), total_km, key, body)
    if a.write:
        os.makedirs(os.path.dirname(js_path), exist_ok=True)
        open(js_path, 'w', encoding='utf-8').write(js)
        print('\n已寫 %s（%d 點）。記得：manifest.json 加條目（purpose 寫簡化點數與起算點）、'
              '頁面 trip 填 date/km/duration/gain/summit、index.html 搬到 completed 並標 NEW、'
              'README 樹用 manifest_tree.py --write 重生。' % (js_path, len(simp)))
    else:
        print('\n（沒給 --write，軌跡檔沒寫；會寫到 %s，%d 點）' % (js_path, len(simp)))
    if a.json:
        print(json.dumps({'trip': {'date': a.date, 'km': round(total_km, 2),
                                   'duration': fmt_hm(duration) if duration is not None else None,
                                   'gain': gains.get(31) if gains else None, 'summit_gps': summit},
                          'schedule': rows,
                          'stops': [{'from': pts[i][3].strftime('%H:%M'), 'to': pts[j][3].strftime('%H:%M'),
                                     'lat': round(la, 6), 'lng': round(ln, 6)} for i, j, la, ln in stops]},
                         ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
