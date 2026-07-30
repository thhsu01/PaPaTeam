# 可讀性與對比度審計

**日期**：2026-07-30
**標準**：WCAG 2.1 AA（一般文字 4.5:1、大文字 ≥18.66px 粗體或 ≥24px 為 3:1）

> **修訂說明**：本文件第一版的對比度數字是憑印象填寫的，其中兩項（`#7c9e52`、`#059669`）錯誤地標記為「通過 AA」。本版所有數值均以 WCAG 2.1 相對亮度公式實際計算，計算腳本見文末。

---

## 1. 對比度實測

### 內文色（白底）— 全部通過

| 類別 | Hex | 對比度 | AA |
|---|---|---|---|
| `text-slate-900` | `#0f172a` | 17.85:1 | ✅ |
| `text-stone-800` | `#292524` | 15.17:1 | ✅ |
| `text-slate-800` | `#1e293b` | 14.63:1 | ✅ |
| `text-stone-600` | `#57534e` | 7.63:1 | ✅ |

### 小字標籤色 × 各頁實際背景

詳情頁背景不是白色，而是米色系，因此需按各頁背景分別計算。

| 背景 | 使用頁面 | `stone-500` | `stone-600` |
|---|---|---|---|
| `#ffffff` | index 卡片 | 4.80:1 ✅ | 7.63:1 ✅ |
| `#fefaf6` | huoyianshan | 4.62:1 ✅ | 7.35:1 ✅ |
| `#fcfaf7` | bishan | 4.60:1 ✅ | 7.32:1 ✅ |
| `#f8fafc` | shiqiulinling | 4.59:1 ✅ | 7.29:1 ✅ |
| `#f8f7f4` | datunshan / dinghu / qixingshan / laojiujianshan / meihuashan / mochashan | **4.48:1 ❌** | 7.12:1 ✅ |
| `#f5f3ef` | nanshijiao | **4.33:1 ❌** | 6.88:1 ✅ |
| `#e7e5e4` | 部分卡片區塊 | **3.82:1 ❌** | 6.08:1 ✅ |

**已修正**：`text-stone-500` 在 7 種背景中有 3 種未達 4.5:1（影響 8 個檔案的 `text-xs` 小字標籤 —— 12px 屬一般文字，不適用 3:1 放寬）。已將 9 個 stone 家族詳情頁共 255 處全部改為 `text-stone-600`，所有背景現達 6.08:1 以上。

`text-slate-500`（index.html 6 處 4.67:1、shiqiulinling.html 18 處 4.55:1）**兩者均已通過**，故未改動 —— 避免無無障礙理由的視覺變更。

> 沿革：原先使用 `text-stone-400`（白底僅 2.52:1，明確不合格），commit `80ecb77` 改為 `stone-500` 方向正確但幅度不足（未考慮詳情頁是米色底而非白底），本次補足。

### 品牌色 — 已修正（2026-07-30 第二輪）

> **數字修正**：本節先前以白底計算，低估了嚴重程度。`nanshijiao.html` 實際頁面背景是 `#f5f3ef`，`#c77c3e` 在其上僅 **2.97:1** —— 不只未達一般文字的 4.5:1，**連大文字的 3:1 也不合格**（先前誤記為 3.29:1 ✅ 通過大文字）。

`nanshijiao.html` 文字用途一律改用 `#9a6030`（該值原本已存在於此頁調色盤，非新增顏色）：

| 元素 | 字級 | 背景 | 改前 | 改後 | 門檻 |
|---|---|---|---|---|---|
| `.stamp` | 11px bold | `#f5f3ef` | 2.97:1 ❌ | **4.63:1 ✅** | 4.5 |
| h1 強調段 | 36–60px | `#f5f3ef` | 2.97:1 ❌ | **4.63:1 ✅** | 3.0 |
| 「320」數字 | 30px bold | `#f5f3ef` | 2.97:1 ❌ | **4.63:1 ✅** | 3.0 |
| GPX 連結 | 14px | `#f5f3ef` | 2.97:1 ❌ | **4.63:1 ✅** | 4.5 |
| 時間軸時刻 | 14px bold | `#f5f3ef` | 2.97:1 ❌ | **4.63:1 ✅** | 4.5 |
| 隊友建議 `#b07040` | 12px | `#fef9f0` | 3.82:1 ❌ | **4.90:1 ✅** | 4.5 |
| 五尖山標題 `#6d8940` | 16px bold | `#ffffff` | 3.96:1 ❌ | **5.02:1 ✅**（`#5f7738`） | 4.5 |

**按鈕背景**（對比度公式對稱，前後景互換不改變比值）：

| 位置 | 改前 | 改後 | |
|---|---|---|---|
| nanshijiao 導航鍵（白字） | `#c77c3e` 3.29:1 ❌ | `#9a6030` **5.13:1 ✅** | |
| `.nav-arrow:hover`（白字）— huoyianshan / meihuashan / laojiujianshan | `#ea580c` 3.56:1 ❌ | `#cd4d0b` **4.50:1 ✅** | |
| `.nav-arrow:hover`（白字）— mochashan | `#16a34a` 3.30:1 ❌ | `#12883e` **4.55:1 ✅** | |
| 航點鍵 hover（白字）— shiqiulinling | `sky-600` 4.10:1 ❌ | `sky-700` **5.93:1 ✅** | |
| 航點鍵 hover（白字）— bishan | `pink-600` 4.60:1 ✅ | 未改動 | |

**刻意保留 `#c77c3e` / `#7c9e52` 的位置** —— 這些不受 4.5:1 約束，或本已合格：

- 深色專題區塊的 `text-xs` 標籤：`#c77c3e` on `#1c1c1c` = **5.18:1 ✅**（若一併改深反而降到 3.32:1 ❌）
- 非文字裝飾：`.section-bar-*` 色條、`.timeline-line` 漸層、`.hero-accent` 斜紋、提醒橫幅左邊框、`w-2 h-2` 小圓點
- Leaflet 路線與標記、Chart.js 線條與資料點

其他 9 頁的強調色（`#ea580c`、`#16a34a`、`#0284c7`、`#0ea5e9`、`#ec4899`、`#d97706`）經逐頁清查，**除上表的 hover 態外均只用於非文字元素**，無須調整。

---

## 2. 字級

| 用途 | 類別 | px | 評估 |
|---|---|---|---|
| 標題 | `text-2xl`–`text-6xl` | 24–60 | 階層清晰 |
| 卡片標題 | `text-xl`–`text-2xl` | 20–24 | 合適 |
| 內文 | `text-base` | 16 | 合適 |
| 小字標籤 | `text-xs` | 12 | 大量使用；因屬一般文字，對比度須 4.5:1（見上表） |

---

## 3. 已完成的無障礙改動

- `<img>` 的 `alt`：index.html 3 個圖片全部補齊。**其餘 10 個詳情頁沒有 `<img>` 標籤**，無需處理（先前版本誤稱涵蓋 11 個檔案）。
- 返回鍵、導覽鍵、航點前後鍵、地圖導航鍵：補 `aria-label`。
- `<nav>`：補 `aria-label`。
- 圖表與地圖容器：補 `role="region"` + `aria-label`。
- 觸控目標放大至 44×44px：index.html 選單鍵、nanshijiao.html 航點鍵（第一輪），以及其餘 9 個詳情頁的航點前後鍵共 18 個（第二輪補齊 —— 第一輪只改了 nanshijiao，其他頁仍是 `w-8 h-8`（32px）或 `w-10 h-10`（40px），造成不一致）。
- **skip link**：11 頁均加入「跳至主要內容」，預設移出畫面、鍵盤聚焦時滑入；`<main>` 補 `id="main-content"` 作為跳轉目標。
- **鍵盤焦點指示**：新增 `:focus-visible` 雙環樣式（深色 outline + 白色 halo），同時涵蓋淺色頁面與 index.html 的深色頁腳。此前 Tailwind preflight 移除了預設 outline 而全站無替代樣式。
- **減少動態**：`@media (prefers-reduced-motion: reduce)` 關閉轉場與動畫；因 `scrollIntoView({behavior:'smooth'})` 依規範會覆蓋 CSS，另以 `assets/site.js` 在該偏好啟用時改寫為 `auto`。

### 共用檔（第一輪）

新增 `assets/site.css` 與 `assets/site.js`，只收 skip link、`:focus-visible`、`prefers-reduced-motion` 三項全新規則，未動各頁既有 CSS。

### 各頁 CSS 統一（第三輪，已完成）

第一輪判斷「抽出共用 CSS 等於統一各頁差異、會改動視覺」，這個判斷不完全正確。實際盤點後發現：**多數規則的結構完全相同，只差色值與尺寸**，因此可用 CSS 自訂屬性把結構抽出、把差異保留成各頁 `:root` 變數，外觀完全不變。

新增 `assets/detail.css`（10 個詳情頁共用，`index.html` 不載入 —— 它設計不同，且共用 `body` 規則會覆蓋掉它自己的背景色）。抽出 14 條規則：`body`、`.chart-container`、`#elevation-chart`、`#map`、`#realMap`、`.waypoint-card`、`.nav-btn`、`.card-hover:hover`、`.timeline-line`、`.nav-arrow:hover`、`.info-glass`、`.nav-link`、`.nav-link:after`、`.nav-link:hover:after`。

**刻意不抽出的 3 條**，因為會改變行為：

| 規則 | 原因 |
|---|---|
| `::-webkit-scrollbar*` | 對所有頁生效。家族 B 原本沒有自訂滾動條，抽出會讓它們從瀏覽器預設變成 6px 自訂樣式 |
| `.leaflet-container` | 由 Leaflet 自行加在地圖容器上，家族 B 也有地圖。抽出後變數未定義會讓背景變透明 |
| `html { scroll-behavior: smooth }` | 家族 B 原本沒有。加上會讓我新增的 skip link 變成平滑滾動 —— 對「跳過導覽」這個用途，瞬間跳轉才是正確行為 |

抽出安全性的判準：一條規則只在「所有 10 頁都有它」或「缺少它的頁面其 markup 根本沒有該 class/id」時才抽出。後者經逐頁清查確認 —— 9 個 class/id 選擇器全部符合「有 CSS 就有用到、有用到就有 CSS」。

順帶修正的等價寫法差異（原本看似不同、實際效果相同）：`margin: auto` 與 `margin-left/right: auto`；`transition: all 0.2s` 與 `all 0.2s ease`（`ease` 是預設值）；字型宣告的單引號與雙引號。

**成效**：各頁 inline CSS 由 16,095 降到 9,768 字元，加上 3,273 字元的共用檔（10 頁只需下載一次），淨減 3,054 字元。更重要的是後續調整只需改一處，不必再靠跨檔 sed —— 而 sed 正是本專案先前造成錯誤的手段。

**外觀不變的驗證方式**：先用像素比對，發現 10 頁都有 0.01–0.12% 差異；再以「同一版本連拍兩次」做對照組，測出雜訊底線同為 0.003–0.08%，證實那是 Leaflet 標記與 Chart.js canvas 的渲染非決定性。改以決定性方法複驗 —— 逐元素比對 `getBoundingClientRect` 與 19 項 computed style（`backgroundColor`、`color`、`backgroundImage`、`boxShadow`、`transition`、`backdropFilter`、`zIndex`、`maxWidth`、`overflowX`、`fontFamily`、`transform` 等），在 390px 與 1280px 兩種視窗下涵蓋 10 頁共 5,900 餘個元素快照，**全部一致**。

### 天氣 API 日期處理（第二輪）

`nanshijiao.html` 原本以 `start_date=2026-08-02&end_date=2026-08-02` 硬指定單日。Open-Meteo 的 forecast 端點不提供過去日期，因此行程日一過，`data.daily.weathercode[0]` 即為 undefined，卡片會顯示「天氣代碼undefined」或落入 catch。

改為沿用 repo 內 `dinghu.html` / `laojiujianshan.html` 已有的模式：宣告 `targetDate`、取 `forecast_days=16` 視窗、以 `indexOf(targetDate)` 查找，查不到則退回今日（索引 0）。並在退回時區分兩種原因，比原模式的單一訊息更精確：

| 情境 | 顯示 |
|---|---|
| 行程日在 16 天視窗內 | `8/2 行程日預報` |
| 行程日早於視窗起點（已過） | `今日即時天氣（行程日已過）` |
| 行程日晚於視窗終點（尚遠） | `今日即時天氣（行程日尚遠）` |

三種分支均以模擬 API 回應實測通過。

### 已撤回的錯誤改動

| 改動 | 撤回原因 |
|---|---|
| `role="article"` 加在 `<a href>` | ARIA role 覆蓋原生語意，螢幕閱讀器不再將卡片播報為連結 |
| `role="navigation"` 加在 `<nav>` 內的 div | 巢狀 landmark，重複播報 |
| `min-width: 500px` 於圖表 canvas | Chart.js 本已自適應；反而在手機產生多餘橫向滾動 |
| `bindPopup(..., {'aria-label': ...})` | 非 Leaflet 選項，會被忽略 |
| `querySelector('button:has-text(...)')` | `:has-text()` 是 Playwright 語法非 CSS，每次點擊拋 SyntaxError |

---

## 4. 尚未處理的缺口

1. **`index.html` 的行程歸檔** —— 8/2 之後應把 `data.planned` 中的南勢角行程移到 `data.completed`，並將 `isLatest` 轉移。這是內容操作（需知道實際完成情況），非程式能代為判斷。

### 第六輪：全站對比度歸零

**檢查方法的改進**：先前幾輪只掃 inline `style="color:#..."`、`<style>` 規則與 class 屬性的字串比對，會漏掉「字級或顏色由父層繼承」的情況，也無法得知元素的實際背景。本輪改為在瀏覽器中逐一取得每個含文字元素的 **computed 顏色、字級、字重與實際背景色**（沿 DOM 往上找第一個不透明背景），直接計算對比度並依字級套用 4.5:1 或 3:1 門檻。

初次掃描：**136 個不合格文字元素，全部是小字**（大字 0 個 —— 印證了大標題本就達標，也印證了「只改小字」這個方向是對的）。

修正後：**11 頁全部 0 個**。

分成四類處理，方向不同：

**（一）我先前造成的迴歸 —— 深色底上的文字要「變淺」而非加深**

第三輪我用 `sed` 全域把 `text-stone-400` → `500` → `600`，但沒有區分背景明暗。落在深色區塊上的文字因此從合格掉到不合格：

| 位置 | 背景 | 我改壞成 | 修正為 |
|---|---|---|---|
| bishan 地質解說 ×4 | `#1c1917` | 2.29:1 | `stone-400` → 6.93:1 |
| meihuashan 石刻條目 ×3 | `#292524` | 1.99:1 | `stone-400` → 6.01:1 |
| index 頁尾連結與版權 ×2 | `#020617` | 2.66–4.20:1 | `slate-400` → 7.87:1 |
| shiqiulinling 深色專題 ×2 | `#0f172a`、`#451a03` | 3.15–3.75:1 | `slate-400` → 5.84:1 |

這些原本用的就是 `stone-400`／`slate-500` 之類的淺色，本來合格。

**（二）index.html 從未被修過的 `text-slate-400`（39 處，2.56:1）**

第三輪的 sed 迴圈刻意排除了 `index.html`，導致首頁的小字標籤一直停在 2.56:1。改為 `slate-500`（4.76:1）。

**（三）強調色小字加深（淺底）**

`orange-600`→`700`、`amber-600`→`700`、`sky-500`/`sky-600`→`700`、`pink-500`→`600`、`pink-600`→`700`、`emerald-600`→`700`、`teal-600`→`700`；`huoyianshan` 有一處 `orange-700` 配 `#fed7aa` 仍只有 3.83:1，再降一階到 `orange-800`。每個 token 的替換階都是「在該 token 於該頁出現的所有背景上都達標」的最小幅度。

**（四）白字配色塊**

`bg-<強調色>-600` 配白字一律 3.19–4.10:1。含文字者改為 `-700`（5.02–5.93:1）；純裝飾的色條與圓點（`w-2.5 h-8`、`w-2 h-2`，共 40 處）不受對比度約束，維持原色。

另外兩項：

- index 卡片的「詳情待補充」標籤是白字配 `bg-black/40` 疊在照片上。疊在亮照片時僅 2.85:1，改為 `/60` 後最壞情況（純白照片）也有 5.74:1。
- Leaflet 彈出視窗的關閉鍵預設 `#757575` 配 `#ddd` 為 3.39:1，於 `detail.css` 覆寫為 `#404040`（7.63:1）。

**避免重蹈覆轍的關鍵一步**：動手前先掃出「同一 token 在同一頁同時出現於淺底與深底」的情況 —— 共 4 組（index 的 `slate-500`／`slate-600`、meihuashan 的 `stone-600`、shiqiulinling 的 `slate-500`）。這些若整頁替換，必然會像第三輪那樣改壞其中一側，因此改以逐處定位處理。

**驗證**：改動後重跑同一套 computed 掃描，11 頁皆為 0；另比對 22 組（11 頁 × 2 視窗）的逐元素幾何，全部相同，確認這批只改顏色、未動版面。

### 已於第五輪完成

**導覽鍵統一為藥丸樣式**

原本兩套設計：家族 A（6 頁）用 `.nav-link` 文字鍵配動畫底線，家族 B（4 頁）用 `.nav-btn` 藥丸配背景 hover。已全部統一為藥丸，`.nav-link` 相關的三條規則與 `--accent` 變數隨之移除。

實作時發現一個直接沿用家族 B 樣式會失敗的問題：家族 B 的 `hover:bg-stone-100`（`#f5f5f4`）在它自己的白色導覽列上只有 1.09:1，而家族 A 有三頁的導覽列底色是 `bg-[#f8f7f4]/90`——與 `stone-100` 幾乎同色（**1.018:1，藥丸等於看不見**）。因此全 10 頁改用 200 階（`hover:bg-stone-200` / shiqiulinling 用 `hover:bg-slate-200`），在白色與米色導覽列上分別為 1.256:1 與 1.172:1，兩者都能辨識；藥丸上的文字對比度為 6.08:1（stone）與 6.15:1（slate），均達標。

`huoyianshan` 有一顆「當前項目」鍵原本是 `text-orange-600`（3.56:1，小字不合格），改為填滿式藥丸 `bg-stone-200 text-stone-800`，兼顧狀態表達與對比度。三頁的藥丸鍵原本缺少 `whitespace-nowrap`，一併補上，避免標籤在窄螢幕的橫向滾動容器裡折行。

各頁的中性色仍依自身調色盤（shiqiulinling 為 slate，其餘為 stone）—— 統一的是藥丸形狀、內距與 hover 行為，而非把每頁的色系也一併抹平。

**驗證**：逐元素比對幾何與 13 項 computed style，10 頁 × 2 視窗，並判定每處差異是否位於 `<nav>` 內。結果為 nav 內 110 處、**nav 外 0 處** —— 證明改動完全侷限於導覽列。

### 已於第四輪完成

**行程日期單一來源（`nanshijiao.html`）**

原本 `2026-08-02` / `8月2日` / `8/2` 散落在多處。現由 `TRIP_DATE` 一個常數推導天氣查詢、天氣卡標題與行程結束提示。

修正的實際矛盾：天氣卡標題原本寫死「8/2 天氣預報」，但行程日過後內文會退回顯示今日天氣 —— 標題與內文各指不同日期。現在兩者一律由同一判斷產出：

| 情境 | 標題 | 副標 |
|---|---|---|
| 行程日在 16 天視窗內 | `8/2 天氣預報` | `8/2 行程日預報` |
| 行程日已過 | `今日天氣` | `行程日已過，顯示今日天氣` |
| 行程日尚遠 | `今日天氣` | `行程日尚遠，顯示今日天氣` |

另新增「此行程已結束」提示，行程日過後自動顯示（預設 `hidden`），使頁面不會看起來仍是即將出發的行程。天氣 API 失敗時改以本地日期（`toLocaleDateString('en-CA', {timeZone:'Asia/Taipei'})`，輸出 `YYYY-MM-DD` 可直接與 `TRIP_DATE` 字串比較）判斷，故提示不依賴 API 可用性。四種日期情境與 API 失敗路徑均經實測。

頁面內文的敘述性日期（戳章「8月2日」、出發時間、頁腳）未改為動態 —— 那些在行程結束後仍然正確，只是變成歷史敘述，不構成矛盾。

**同物異名的 id 統一**

| 元件 | 家族 A（6 頁） | 家族 B（4 頁） | 統一為 |
|---|---|---|---|
| Leaflet 容器 | `#realMap` | `#map` | `#map` |
| 圖表 canvas | `#elevationChart` | `#elevation-chart` | `#elevation-chart` |

`detail.css` 中原本兩條分開的 `#map` 與 `#realMap` 規則已合併為一條參數化規則（`--map-h`、`--map-radius`、`--map-border`、`--map-z`、`--map-w`、`--map-max-w`）。

過程中發現一個只有 computed 值會顯現的陷阱：Tailwind preflight 對所有元素設 `border-style: solid; border-width: 0`。若合併後的規則寫 `border: var(--map-border, none)`，未設邊框的 4 頁其 `border-style` 會由 `solid` 變成 `none` —— 兩者都不顯示邊框，但為讓「零變化」的保證連 computed 值都成立，預設值改為明確重述 preflight 的 `0 solid #e5e7eb`。

**驗證**：同前輪的決定性比對，10 頁 × 2 視窗。`nanshijiao` 因新增提示 div 造成同層元素索引位移，故另做一次「移除該 div 後」的比對，結果 328／334 個元素 × 19 屬性全同 —— 證明除了刻意新增的提示之外沒有其他變化。

### 已於第三輪完成

- **各頁 CSS 統一** —— 見上節。
- **`bishan.html` 的 `.text-gradient` 死碼** —— 已刪除。該規則定義了漸層文字樣式（`#ec4899` → `#8b5cf6`）但 markup 中從未使用。附帶說明：漸層文字的對比度無法用單一比值評估，WCAG 未明確涵蓋，若日後要啟用需個別判斷。

---

## 5. 未執行的驗證

以下項目本次**未實際執行**，不應視為已通過：

- Lighthouse 無障礙評分
- 螢幕閱讀器（NVDA / VoiceOver）實測
- 實機測試（本環境無瀏覽器可驅動）
- 超小螢幕（280–375px）實際渲染

---

## 附錄：對比度計算腳本

```python
def lum(h):
    r, g, b = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def ratio(fg, bg):
    a, b = lum(fg), lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)

print(ratio('78716c', 'f5f3ef'))   # stone-500 on nanshijiao bg -> 4.33
```

參考：[WCAG 2.1 相對亮度定義](https://www.w3.org/TR/WCAG21/#dfn-relative-luminance)
