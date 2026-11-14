---
name: papateam-route-eval
description: 爬爬小隊（thhsu01/PaPaTeam）評估新路線並建候選頁：健行筆記步道頁＋公開 GPX 分群比較、推薦走法、依 docs/PLANNING_RULES.md 算航點距離與 1.5 km/h 時刻、複製 nanshijiao.html 建頁、跑檢查、推開發分支。TH 說「評估某條路線」「幫我看某某山」「建候選頁」「這條步道怎麼走」「規劃下一次爬山」「比較幾種走法」時一律用這個，即使他沒提到 GPX 或候選頁。
---

# 爬爬小隊：評估新路線 → 候選頁

> 本檔是正本。claude.ai 上安裝的同名技能只是薄殼（觸發描述＋「clone 後讀本檔照做」），
> 要改流程只改這裡，不必重裝技能。

規則只有一份：倉庫的 `docs/PLANNING_RULES.md`（§二評估、§三算法、§五頁面規格、§八回報）。
本技能是把那份規則走一遍的操作順序，與它衝突時以規則為準。

最高原則：**不編造**（查不到就說查不到）、**有疑點先問**（用選單）、**不開 PR、不合併**。

## 0. 前置（每次都做）

1. `add_repo thhsu01/PaPaTeam`（access: push）→ `git clone --depth 1` → 從 `origin/main` 開分支
   `route/<頁名>`。沙盒抓不到 codeload／api.github.com，單檔可用 raw.githubusercontent。
2. 讀 `docs/PLANNING_RULES.md`、`manifest.json` 的 `conventions`（至少 `distance_source`、
   `elevation_source`、`meeting_point`、`waypoint_coords`）。

## 1. 找資料

- 健行筆記官方步道頁（`hiking.biji.co/index.php?q=trail&act=detail&id=…`）：記下**里程、步道型態、
  海拔、路面、交通、路況回報**與頁面日期。沙盒與 WebFetch 可能被擋；擋了就用 Claude in Chrome 讀
  （依 `chrome-browser` skill 載入工具），收尾時關閉分頁。
- 山頭：健行筆記山岳頁的基點標高（`q=mountain`）與「台灣小百岳一覽」的編號。
- 該步道底下的**全部**公開 GPX：GPX 下載需要登入，只能在 Chrome 做。檔案會落在 TH 的下載資料夾
  `D:\Cloud\Dropbox\Temp`；請 TH 把那個資料夾加進對話（或直接附檔），再 stage 進沙盒的一個新空目錄。
  一條都拿不到就說拿不到，用步道頁的分段里程做，並在回報標明「無 GPX，距離為標示值」。

## 2. 分群比較

```
python3 tools/gpx_cluster.py <GPX目錄> \
  --anchor 登山口=lat,lng --anchor 某山=lat,lng --anchor 車站=lat,lng \
  --official <健行筆記標示 km> [--pace 1.5] [--json]
```
錨點用步道頁與山岳頁的座標（登山口、車站、每座山頭）。表格直接貼進回覆：
走法｜樣本數｜距離中位數（範圍）｜爬升｜他人耗時｜本隊預估。爬升三個視窗不收斂的軌跡要註明。

## 3. 推薦與選單

選一個走法說明理由；列注意事項：陡坡、拉繩、補給、近期路況回報、停車、交通（公車班次、台鐵車次用
TRA 開放資料並註明時刻表發布日期）；點對點路線以**上**技術段為原則（拉繩、陡坡往上走）。
然後 `AskUserQuestion`：走法（建議選項排第一並標「建議」）＋下一步（建候選頁／先不建）。
**TH 選了才建頁。**

## 4. 建候選頁（TH 選了之後）

1. 航點：以 TH 標的點為準，逐點比對公開 GPX／路點；偏離 40–60 m 以上先問。
   存成 `wps.json`（`[{"loc","lat","lng"}…]`，接駁段終點加 `"shuttle": true`）。
2. 距離與時刻：
   ```
   python3 tools/gpx_cluster.py <GPX目錄> --segments wps.json --start 08:00 --official <km> --json
   ```
   有「依序經過全部航點」的軌跡 → 用「照標示值縮放」那欄；沒有 → 用段距中位數。
   每段不得短於直線；查不到的段用直線標「補估」。集合時間未定用 08:00 並註明。
3. 海拔：山頭有公開標高 → `ele` 用它、`loc` 加 `(H___m)`（四位加千分位）；沒有 → TH 給的；
   都沒有 → GPS 中位數（`gpx_cluster` 沒印的話用 `papa_gpx.ele_median_near`），不加 `(H)`。
   小百岳：`xbaiyue: <編號>`，新的一座補進 `tools/spec_sweep.py` 的 `XBAIYUE`。
4. 複製 `nanshijiao.html`，照 `ARCHITECTURE.md` §建立新詳情頁 改：`<title>`、`<h1>`、
   `<meta description>`、`:root` 主色（`grep -h "^\s*--accent:" *.html` 列出各頁現有主色，不撞色；對比度實測寫註解）、
   `schedule`（每點 `desc`＋`advice`）、`init` 的 `nav`／`weather`／`map.setView`；
   候選頁**沒有 `trip`**、不放 `notice` 掃載點、`#timeline` h2 主詞「預計行程進度」。
   資料來源列在頁面「參考資料」，算法寫在 `schedule` 上方的註解。
5. 同步：`index.html` 的 `data.candidate` 加卡片；`manifest.json` 的 `pages` 加條目（`status: candidate`）。

## 5. 檢查與推分支

依 PLANNING_RULES §六：`spec_sweep.py` → `fact_check.py` → `redteam.py` → `manifest_tree.py --write` →
（新頁用到新的 Tailwind class 先 `bash tools/contrast/build-css.sh`）→ 起 `python3 -m http.server 8099` 後
`node tools/regress/check.js --update`（新頁本來就會變，逐條確認只有新頁）與 `node tools/contrast/check.js --all`。
全綠才 `git push -u origin route/<頁名>`。不開 PR。

## 6. 回報（§八）

表格：各地標｜累計 km｜海拔｜時刻。說明哪些是公開資料、哪些是 TH 給的、哪些是推估。
附 `https://raw.githack.com/thhsu01/PaPaTeam/route/<頁名>/<頁名>.html`。沒解決的疑點直接列。
