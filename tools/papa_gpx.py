"""gpx_cluster.py 與 trip_from_gpx.py 共用的 GPX 幾何：讀檔、Haversine、累計距離、
Douglas–Peucker 簡化、移動中位數爬升。放在一起的理由跟 papa_common.py 一樣——
2026-11-03 之前這些算法每次評估路線都在對話裡重寫一遍，兩次寫出來的爬升視窗不同，
數字就不同；收成一份，算法有問題只改一處。

GPX 命名空間用 https（https://www.topografix.com/GPX/1/1）——健行筆記匯出的檔是這個，
用 http 的 ns 會一個點都讀不到。時間 UTC（尾碼 Z）轉台灣時間。"""
import math
import statistics
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

NS = {'g': 'https://www.topografix.com/GPX/1/1'}
NS_HTTP = {'g': 'http://www.topografix.com/GPX/1/1'}
TST = timezone(timedelta(hours=8))


def hav(a, b, c, d):
    """兩點直線距離（公尺）。與 spec_sweep.hav 同一條公式。"""
    R = 6371000.0
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def parse_time(t):
    if not t:
        return None
    return datetime.fromisoformat(t.replace('Z', '+00:00')).astimezone(TST)


def read_gpx(path):
    """回傳 {'name', 'points': [(lat, lng, ele, time)], 'waypoints': [(name, lat, lng, ele)]}。
    多段 <trkseg> 接成一條；ele／time 缺的點給 None。"""
    root = ET.parse(path).getroot()
    ns = NS if root.tag.startswith('{https') else NS_HTTP
    pts = []
    for p in root.iterfind('.//g:trkpt', ns):
        ele = p.find('g:ele', ns)
        tm = p.find('g:time', ns)
        pts.append((float(p.get('lat')), float(p.get('lon')),
                    float(ele.text) if ele is not None and ele.text else None,
                    parse_time(tm.text) if tm is not None else None))
    wps = []
    for w in root.iterfind('.//g:wpt', ns):
        nm, ele = w.find('g:name', ns), w.find('g:ele', ns)
        wps.append(((nm.text or '').strip() if nm is not None else '', float(w.get('lat')), float(w.get('lon')),
                    float(ele.text) if ele is not None and ele.text else None))
    name = root.find('.//g:trk/g:name', ns)
    return {'name': (name.text or '').strip() if name is not None else '', 'points': pts, 'waypoints': wps}


def cum_dist(pts):
    """每一點的累計距離（公尺）。"""
    out = [0.0]
    for i in range(1, len(pts)):
        out.append(out[-1] + hav(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1]))
    return out


def douglas_peucker(pts, tol_m):
    """Douglas–Peucker 簡化，容許偏差 tol_m 公尺。pts 是 (lat, lng, …) 序列，回傳保留的索引。
    垂距用本地平面近似（緯度一度 ≈ 111.32 km、經度乘 cos 緯度），在台灣的尺度下誤差遠小於容差。"""
    if len(pts) < 3:
        return list(range(len(pts)))
    lat0 = math.radians(pts[0][0])
    kx, ky = 111320.0 * math.cos(lat0), 111320.0
    xy = [((p[1] - pts[0][1]) * kx, (p[0] - pts[0][0]) * ky) for p in pts]
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = xy[a]
        bx, by = xy[b]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            px, py = xy[i]
            if L == 0:
                d = math.hypot(px - ax, py - ay)
            else:
                d = abs(dy * px - dx * py + bx * ay - by * ax) / L
            if d > best:
                best, bi = d, i
        if best > tol_m and bi > 0:
            keep[bi] = True
            stack.append((a, bi))
            stack.append((bi, b))
    return [i for i, k in enumerate(keep) if k]


def moving_median(xs, win):
    half = win // 2
    return [statistics.median(xs[max(0, i - half):i + half + 1]) for i in range(len(xs))]


def gain_estimate(pts, windows=(15, 31, 61)):
    """累計上升的推估：高程先取移動中位數壓掉停留時的抖動，再累加正增量
    （manifest conventions.elevation_gain）。回傳 {視窗: 爬升}，三個視窗要收斂才可信。"""
    eles = [p[2] for p in pts if p[2] is not None]
    if len(eles) < max(windows):
        return {}
    out = {}
    for w in windows:
        sm = moving_median(eles, w)
        out[w] = round(sum(max(0.0, sm[i] - sm[i - 1]) for i in range(1, len(sm))))
    return out


def nearest(pts, lat, lng):
    """離 (lat, lng) 最近的軌跡點：回傳 (索引, 距離公尺)。"""
    best, bi = float('inf'), -1
    for i, p in enumerate(pts):
        d = hav(p[0], p[1], lat, lng)
        if d < best:
            best, bi = d, i
    return bi, best


def ele_median_near(pts, lat, lng, radius=50.0):
    """該點 radius 公尺內的 GPS 高程中位數，取整到 5 m；沒有就 None（PLANNING_RULES §三「海拔」）。"""
    es = [p[2] for p in pts if p[2] is not None and hav(p[0], p[1], lat, lng) <= radius]
    return int(round(statistics.median(es) / 5.0) * 5) if es else None


def fmt_hm(minutes):
    return '%d:%02d' % (minutes // 60, minutes % 60)


def round5(minutes):
    return int(5 * round(minutes / 5.0))
