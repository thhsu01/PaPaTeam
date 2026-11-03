---
name: papateam-trip-complete
description: 爬爬小隊（thhsu01/PaPaTeam）走完一條路線後，依當天 GPS 軌跡把計畫頁或候選頁轉成已完成頁：Douglas–Peucker 簡化軌跡存 assets/tracks、各航點改成實走抵達時刻與里程、找出沒有地名的休息點、爬升推估、（未走）航點、trip 事實、首頁 NEW、manifest 與 README 樹同步、跑檢查、推開發分支。TH 說「走完了」「更新成已完成」「把 GPX 填進頁面」「歸檔行程」「這是昨天的軌跡」或附上 GPX 時一律用這個。
---

# 爬爬小隊：GPX → 已完成頁

規則在倉庫的 `docs/PLANNING_RULES.md` §四「已完成頁」與 §三；`manifest.json` 的
`conventions.elevation_gain`、`waypoint_coords`、`unnamed_stops`、`meeting_point`、`trip_facts`
寫了每條規則的來龍去脈。本技能是操作順序。**不編造、有疑點先問、不開 PR、不合併。**

## 0. 前置

1. `add_repo thhsu01/PaPaTeam`（push）→ clone → 從 `origin/main` 開分支 `trip/<頁名>-<日期>`。
2. 拿到 GPX：TH 附檔，或從他的電腦 stage（健行筆記 App 匯出）。放進沙盒一個新空目錄。
3. 確認是哪一頁、哪一天；頁面現在是計畫頁還是候選頁（`manifest.json` 的 `status`）。

## 1. 從頁面抄出航點

```
python3 - <<'EOF'
import re, json, sys; sys.path.insert(0, 'tools')
from papa_common import schedule_objects
s = open('<頁名>.html', encoding='utf-8').read()
out = []
for o in schedule_objects(s):
    g = lambda k, p: (lambda m: m.group(1) if m else None)(re.search(k + r':\s*' + p, o))
    out.append({'loc': g('loc', '"([^"]*)"'), 'lat': float(g('lat', r'([\d.]+)')),
                'lng': float(g('lng', r'([\d.]+)')), 'plan': g('time', '"([^"]*)"')})
json.dump(out, open('wps.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
EOF
```
接駁段的終點加 `"shuttle": true`（`dist` 要維持與前一點相同）。

## 2. 重算

```
python3 tools/trip_from_gpx.py <GPX> --page <頁名> --date YYYY-MM-DD --waypoints wps.json --json
```
看完再加 `--write` 寫軌跡檔。要注意的事：
- **起算點**：集合點與 GPS 起錄點不同時（出發前繞行、在車站等人），用 `--from HH:MM` 自起算時刻切，
  並在軌跡檔檔頭與 `manifest.json` 條目的 `purpose` 寫明；有走但沒錄到的路段，用同路線公開 GPX
  補估距離並標「補估」，補畫的軌跡標「模擬」。
- **離軌跡超過 40 m 的航點**：先問 TH——沒走到（標「（未走）」，`time` 寫 `—`、只留 `plan`、
  不給 `dist`）、還是接駁／集合點（`dist` 維持 0）。
- **沒有地名的停留點**（30 m 內停 5 分鐘以上）：加進 `schedule`，命名「第N休息點」，
  `desc` 寫明「這個點沒有地名」，`pos: "休息點"`。
- **爬升**：三個視窗（15/31/61）要收斂；頁面寫中間值並註明是推估。不收斂就問。
- **海拔**：航點 `ele` 照 §三（公開標高優先），工具印的 GPS 中位數只是對照；
  `trip.summit` 取最高點航點的公開標高。

## 3. 改頁面

- `schedule`：`time` 改抵達時刻、原本的 `time` 搬進 `plan`、`dist` 改簡化軌跡累計距離；
  `desc` 開頭「累計 X.XX km。」；休息點與（未走）依上節。
- `init`：`trip: { date, km, duration: "H:MM", gain, summit }`；`map.track` 只給樣式。
- 版面：第五鍵與 `#timeline` h2 改「實走時間軸」、英雄區改「實走紀錄」、加 `<div data-widget="notice">`
  （照 `nanshijiao.html`）；`<meta description>` 以行程日 `YYYY/M/D` 開頭、句尾「全程 N 公里」。
- 同步（§四「改狀態時要同步」）：`index.html` 把卡片從 `planned`／`candidate` 搬到 `completed`、
  `date: "YYYY/MM/DD"`、`isLatest: true` 移到這筆（舊的改 `false`）；`manifest.json` 頁面 `status: completed`
  與 `assets/tracks/` 條目（`purpose` 寫簡化點數、起算點、補估／模擬）；
  文件裡的頁數與小百岳座數由 `spec_sweep` 比對，紅了就改。

## 4. 檢查與推分支

`spec_sweep.py` → `fact_check.py` → `redteam.py` → `manifest_tree.py --write` →
起 `python3 -m http.server 8099` 後 `node tools/regress/check.js --update`（逐條確認只有這一頁與首頁變）
與 `node tools/contrast/check.js --all`。全綠才 `git push -u origin trip/<頁名>-<日期>`。不開 PR。

## 5. 回報（§八）

表格：各地標｜累計 km｜海拔｜時刻（實走）｜plan。說明哪些是 GPS、哪些是公開標高、哪些是推估
（爬升、補估段）。附 `https://raw.githack.com/thhsu01/PaPaTeam/trip/<頁名>-<日期>/<頁名>.html`。
沒解決的疑點（離軌跡的航點、不收斂的爬升）直接列。
