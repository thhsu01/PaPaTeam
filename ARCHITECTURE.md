# 架構指南

本文檔說明爬爬小隊網站的代碼結構、慣例與最佳實踐。適合開發者和內容編輯參考。

## 整體架構

```
主首頁 (index.html)
  ├─ 導覽列 (固定頂部)
  ├─ 英雄區 (hero banner)
  ├─ 計畫行程 (planned)
  ├─ 候選清單 (candidate)
  ├─ 歷史紀錄 (completed)
  └─ 頁腳 (footer)

詳情頁 (10 頁，正規規格見下)
  ├─ skip link
  ├─ 返回按鈕 (fixed 左上)
  ├─ 導覽列 (fixed 頂部，5 顆藥丸)
  ├─ main#main-content
  │    ├─ #overview      行程總覽
  │    ├─ #map-section   路線圖 (Leaflet)
  │    ├─ #elevation     海拔剖面 (Chart.js)
  │    ├─ #spots         景點介紹
  │    └─ #timeline      預估進度／實際行程
  └─ 頁腳 (在 main 之外)
```

詳情頁**只能有這五個段落**，id 與順序如上。詳見「詳情頁正規規格」。

## 主首頁 (index.html)

### 資料結構

所有行程資訊集中在 JavaScript `data` 物件中：

```javascript
const data = {
  planned: [
    {
      title: "路線名稱",
      location: "地點",
      date: "8月2日",
      desc: "單句簡述",
      img: "https://images.unsplash.com/...",
      tag: "PLANNED",
      url: "filename.html"  // 詳情頁路徑，無檔案則設為 "#"
    }
  ],
  candidate: [
    {
      title: "候選路線",
      location: "地點",
      desc: "簡述",
      img: "https://...",
      tag: "候選",
      url: "filename.html"
    }
  ],
  completed: [
    {
      title: "已完成行程",
      date: "YYYY/MM/DD",
      location: "地點",
      desc: "簡述",
      img: "https://...",
      isLatest: true,  // 只有最新的一筆設為 true，顯示「NEW」徽章
      url: "filename.html"  // 若無詳情頁，設為 "#"
    }
  ]
}
```

### 渲染邏輯

- `renderUI()` 函式根據 `data` 物件的三個陣列動態生成卡片 HTML
- 計畫行程：3 欄網格（lg:grid-cols-3）
- 候選清單：2 欄網格（md:grid-cols-2）
- 歷史紀錄：3 欄網格（lg:grid-cols-3），最新項目標上「NEW」徽章

### 樣式

- **主色系**：翠綠色（`#064e3b`, `#059669`）
- **次色系**：琥珀色（用於候選清單）、灰色（用於歷史紀錄）
- **字型**：Google Fonts `Noto Sans TC` 中文字
- **框架**：Tailwind CSS (CDN)
- **背景**：淺灰色網格（`#fcfdfd`）
- **玻璃態效果**（Glass Morphism）：模糊背景 + 透明白色卡片

## 詳情頁正規規格

10 個詳情頁出自兩套模板世代，結構相同但命名與版面各行其是。本節定義**唯一一份正規規格**：
新頁一律照此建立，既有頁逐步收斂到此。規格若要改，改這裡，不要只改某一頁。

### 正規頁：`nanshijiao.html`

以它為基準的理由：

- 段落 id 與順序屬多數派（另 3 頁相同）
- 功能最完整：`TRIP_DATE` 單一日期來源、行程結束提示、航點含預計時間、
  天氣標題與內文同步、skip link、aria-label、44px 觸控目標
- 對比度是刻意調過的（見 `READABILITY_AUDIT.md`），不是碰巧合格

**它自己的已知偏離**（複製時不要跟著抄）：主色以 `style="color:#9a6030"` 之類的
行內樣式散在 markup 各處，尚未收成 CSS 變數。這是全站待辦，不是正規做法。

收斂已完成，10 頁的結構現在都符合本規格；仍未統一的三項見文末「尚未收斂的三件事」。

### 段落規格

id、順序、導覽文字三者都是規格的一部分，不可自由發揮。

| 順序 | `<section id>` | 導覽鍵文字 | `<h2>` 標題 | 必要性 |
|:--:|---|---|---|---|
| 1 | `overview` | 行程總覽 | 自由（含路線名） | 必要 |
| 2 | `map-section` | 路線圖 | 互動路線圖 | 必要 |
| 3 | `elevation` | 海拔剖面 | 海拔高度剖面圖 | 必要 |
| 4 | `spots` | 景點介紹 | 自由（含「導覽」或「亮點」） | 必要 |
| 5 | `timeline` | 預估進度 / 實際行程 | 預計行程進度 / 實際行程紀錄 | 必要 |

兩條規則：

- **`timeline` 是唯一容許二選一的文字**，且不是喜好問題：行程日之前用「預估進度」，
  行程結束後改「實際行程」。判斷依據是頁面性質，不是編輯當下的心情。
- **不新增段落。** 影片、文史專題、地質專題這類內容放進 `spots` 段內的卡片，
  不要另開 `<section>`——多一個段落就多一顆導覽鍵，各頁導覽列長度就會不一致。

### 骨架

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>路線名 — 爬爬小隊</title>

  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap');
    :root {
      /* 本頁的尺寸與色值。結構規則在 assets/detail.css，此處只給值。 */
      --page-bg: #f5f3ef;
      --page-fg: #3a3632;
      --chart-max-w: 100%;
      --chart-h: 300px;
      --map-h: 420px;
      --map-radius: 16px;
      --timeline-left: 20px;
      --timeline-bg: linear-gradient(to bottom, #c77c3e, #7c9e52);
    }
    /* 本頁專屬樣式（僅限確實只有本頁用得到的東西） */
  </style>

  <!-- 順序固定：inline style → detail.css → site.css -->
  <link rel="stylesheet" href="assets/detail.css">
  <link rel="stylesheet" href="assets/site.css">
  <script src="assets/site.js" defer></script>
</head>
<body class="antialiased">
  <a href="#main-content" class="skip-link">跳至主要內容</a>

  <a href="index.html" class="fixed top-4 left-4 z-50 ..." aria-label="返回首頁">← 返回首頁</a>

  <nav class="fixed top-0 w-full z-50 ..." aria-label="頁面導覽">
    <!-- 左：站徽 + 站名（連回 index.html）／右：5 顆 .nav-btn 藥丸 -->
  </nav>

  <main id="main-content" class="pt-14">
    <section id="overview">...</section>
    <section id="map-section">...</section>
    <section id="elevation">...</section>
    <section id="spots">...</section>
    <section id="timeline">...</section>
  </main>

  <!-- footer 在 main 之外。放進 main 會讓 skip link 的目標範圍含頁腳。 -->
  <footer class="text-center py-12 border-t border-stone-200">...</footer>

  <script>/* 見「頁面腳本規格」 */</script>
</body>
</html>
```

### 元件規格

**導覽列**：`fixed`，搭配 `<main class="pt-14">` 讓出高度。不用 `sticky`——
`sticky` 版本另外需要 `z-[1000]` 才不會被 Leaflet 蓋住，是多餘的複雜度。

**站徽**：綠色圓形 `爬` 配「爬爬小隊」，**全站一律相同**，不隨頁面主色變。
站徽是識別標誌，每頁換一個就失去作用。

```html
<a href="index.html" class="flex items-center gap-2 hover:opacity-80 transition-opacity">
  <span class="w-9 h-9 rounded-full bg-emerald-700 flex items-center justify-center text-white font-bold text-base flex-shrink-0">爬</span>
  <span class="font-bold text-stone-800 tracking-tight text-lg">爬爬小隊</span>
</a>
```

紀錄頁在站名右側加一個副標，行前頁不加（尚無日期可寫）：

```html
<span class="text-stone-600 text-xs hidden sm:inline font-medium">2026/6/20 活動紀錄</span>
```

**導覽鍵**：五顆一致的藥丸，容器一律 `flex gap-1 overflow-x-auto`
（少了 `overflow-x-auto`，窄螢幕上五顆鍵會被擠壓而不是橫向捲動）。
`onclick` 直接寫 `scrollIntoView`，不要包 `scrollToSection()` 輔助函式。

```html
<button onclick="document.getElementById('elevation').scrollIntoView({behavior:'smooth'})"
        class="nav-btn text-xs px-3 py-1.5 rounded-full text-stone-600 hover:bg-stone-200 whitespace-nowrap"
        aria-label="滾動到海拔剖面">海拔剖面</button>
```

平滑滾動由 `assets/site.js` 統一處理 `prefers-reduced-motion`，各頁不必也不該自行判斷。
段落的 `scroll-margin-top` 在 `assets/detail.css`，用來讓捲動終點避開固定導覽列，
否則捲過去之後 `<h2>` 會躲在導覽列後面。改導覽列高度時要一起改。

**地圖與航點卡**：地圖在上、航點卡在下的**單欄堆疊**，不可並排。
（內容寬度尚未統一：正規頁各段自帶 `max-w-4xl`，家族 A 出身的 6 頁則靠
`<main class="max-w-6xl">`，因此地圖實寬 896px 對 1006px。見下方待辦。）
航點卡欄位 id 固定如下，`updateWaypointCard()` 只認這些名字：

| id | 內容 | 備註 |
|---|---|---|
| `wp-pos-label` | 位置類型（集合起點、最高點…） | 不叫 `wp-pos` |
| `wp-title` | 地點名稱 | |
| `wp-time` | 預計／實際到達時間 | 行前頁標「預計時間」，紀錄頁標「實際時間」 |
| `wp-dist` | 累計里程 km | `toFixed(2)` |
| `wp-ele` | 海拔 m | |
| `wp-desc` | 該點描述 | |
| `wp-advice` | 隊友建議 | 僅此欄位放建議，不要拿來塞到達時間 |

上/下一個航點鍵必要，`min-w-[44px] min-h-[44px]`，帶 `aria-label="上一個航點"` / `"下一個航點"`。

**海拔圖**：`<canvas id="elevation-chart">`（不是 `elevationChart`），
外層 `.chart-container`，並帶 `role="img"` 與 `aria-label`。

**時間軸**：`<div id="timeline-container">` 內含一個 `.timeline-line`，其餘由 JS 生成。

### 頁面腳本規格

資料一律放在名為 `schedule` 的陣列，一個航點一個物件。這是全站實際使用的結構
（先前本文件描述的 `routeData` 物件從未存在過）。

```javascript
const schedule = [
  {
    lat: 24.990128, lng: 121.509104,
    time: "07:30",           // 行前頁用預估時間；紀錄頁用實際時間
    loc:  "捷運南勢角站 (H20m)",
    dist: 0.00,              // 累計里程 km
    ele:  20,                // 海拔 m
    pos:  "集合起點",         // 位置類型，同時決定標記顏色與時間軸 emoji
    desc: "行程起點，07:30 準時出發。",
    advice: "在站內超商補充飲食。"
  },
  // ...
];
```

有確定日期的頁面，行程日只寫一次，其餘全部由它推導——天氣查詢日期、
天氣卡標題、行程結束提示。日期散寫在多處是先前實際發生過的 bug 來源：
`dinghu` 與 `laojiujianshan` 各把日期寫死兩次，結果行程過了以後，
天氣卡仍顯示「今日即時天氣 (目標日尚遠)」。

```javascript
const TRIP_DATE = "2026-08-02";
const tripMD = (() => { const [, m, d] = TRIP_DATE.split('-'); return `${+m}/${+d}`; })();
```

**候選行程沒有 `TRIP_DATE`**，因為它們本來就還沒定日期。這類頁面的天氣以
`forecast_days=1` 顯示今日天氣即可，不要為了湊規格而編一個日期出來。

必要函式：`initMap()`、`initChart()`、`renderTimeline()`、`updateWaypointCard(i)`、
`prevWaypoint()`、`nextWaypoint()`、`openNavigation()`。
已完成的行程頁另有 `fetchWeather()` 與 `markTripPast()` 的取捨——
行前頁必須有天氣預報，紀錄頁改為顯示當日實測天氣，此時兩者皆可省略。

### 色彩規格

每頁有自己的主色（碧山粉、七星藍、火炎山橘），**這是刻意的辨識設計，要保留**。
需要一致的是使用方式：

- 灰階一律用 **stone**，不用 slate
- 主色不可直接當小字顏色。品牌橙 `#c77c3e` 配淺底只有 2.97:1，
  文字要用加深版 `#9a6030`（4.63:1）。非文字的色條、圓點不受此限。
- 深色區塊上的文字方向相反：`stone-600` 在深底會掉到 2:1 以下，該用 `stone-300/400`。
  改色時務必確認該元素的實際背景，不要跨頁做全域字串替換——
  第三輪就是這樣一次改壞 136 處，詳見 `READABILITY_AUDIT.md`。

主色已全數收成 `--accent` 系列變數。各頁在 `:root` 給值，markup 用語意 class
（`.accent-text` / `.accent-fill` / `.accent-mark` …），腳本以 `getComputedStyle`
讀同一份值。換色與對比檢查因此只需面對 `:root` 的幾個值。

**腳本裡的顏色不能寫 `var(--accent)`**：那些值最終進到 canvas 的 `fillStyle`，
canvas 不解析 CSS 變數。必須先取出實際值再傳給 Leaflet / Chart.js。
（行內 `style` 字串裡的 `var()` 沒問題，瀏覽器會解析。）

### 收斂狀態

10 頁已全數符合本規格的結構部分。以瀏覽器實測（10 頁 × 手機/桌機兩種視窗）逐項確認：

| 項目 | 狀態 |
|---|---|
| 段落 id 與順序 | ✅ 10/10 為 `overview` → `map-section` → `elevation` → `spots` → `timeline` |
| 導覽鍵（五顆、規格文字） | ✅ 10/10 |
| 航點卡欄位 id | ✅ 10/10（含新增的 `wp-time`） |
| 導覽列 `fixed` | ✅ 10/10 |
| `<footer>` 在 `<main>` 外 | ✅ 10/10 |
| 地圖單欄堆疊 | ✅ 10/10 |
| 灰階用 stone | ✅ 10/10 |
| 無 `scrollToSection()` | ✅ 10/10 |
| 站徽（綠圓 + 爬爬小隊） | ✅ 10/10 |
| 段落 `scroll-margin-top` | ✅ 集中於 `detail.css` |
| 小字對比 ≥ 4.5:1 | ✅ 0 筆失敗 |
| 主色收成 `--accent` token | ✅ 10/10 |

### 尚未收斂的兩件事

**一、內容寬度**（結構待辦）
正規頁與 3 頁同世代者，各段自帶 `max-w-4xl`；家族 A 出身的 6 頁靠
`<main class="max-w-6xl">`。地圖實寬因此是 896px 對 1006px。
統一它會重排那 6 頁的每一段，比先前任何一步都大，故單獨列為待辦。

**二、內容缺口**（不是結構問題，需要實地資料才能補）

| 頁面 | 缺什麼 |
|---|---|
| `huoyianshan` | schedule 沒有 `dist`（累計里程）與 `advice`，故航點卡無此兩欄 |
| `meihuashan` | schedule 沒有 `advice`，該區塊在有資料前自動隱藏 |

里程與建議都是實走才知道的東西，不應為了填滿欄位而編造。

另有兩處**次要色**未納入主色層，是刻意的：語意色（紅=警告、綠=山頂、藍=外部連結、
琥珀=注意）跨頁共用同一套意義，不屬於任何單頁的識別色；`nanshijiao` 的深色專題面板
自成一套配色。兩者若要制度化，該是另一組 token，不是 `--accent`。

**改 id 的代價**：`bishan.html#analysis` 這類舊錨點連結會失效。本站規模小、對外連結少，
判斷為可接受，但收斂時要一併更新頁內所有 `onclick` 的 `getElementById`。

## 常見 CSS 模式

### 1. 卡片（Card）

```html
<div class="stat-card rounded-2xl p-4 shadow-sm">
  <!-- 統計或資訊卡 -->
  <div class="text-xs text-stone-600 mb-1">標籤</div>
  <div class="font-bold text-stone-800">數值或標題</div>
</div>
```

標籤用 `text-stone-600`（配白底 7.63:1）而非 `stone-400`（2.52:1）——小字一律要過 4.5:1。

**樣式要素**：
- `rounded-2xl` — 2rem 圓角
- `p-4` — 1rem padding
- `shadow-sm` — 細微陰影
- `stat-card` 類別 — 定義為 `background: rgba(255,255,255,0.72); backdrop-filter: blur(8px);`

### 2. 戳記（Stamp）

```html
<span class="stamp">8月2日</span>
```

**樣式定義**：
```css
.stamp {
  /* 文字與框線用加深版 #9a6030（4.63:1），不是品牌色 #c77c3e（2.97:1） */
  border: 3px solid #9a6030;
  color: #9a6030;
  font-weight: 900;
  font-size: 11px;
  letter-spacing: 0.15em;
  padding: 4px 10px;
  border-radius: 3px;
  transform: rotate(-1.5deg);
  text-transform: uppercase;
}
```

### 3. 色系

對比度均以頁面底色 `#f5f3ef` 計算：

| 用途 | 顏色 | 十六進制 | 可用於小字 |
|------|------|---------|:--:|
| 主橙色 | 琥珀 | `#c77c3e` | ✗ 2.97:1 |
| 主橙色（文字版） | 深琥珀 | `#9a6030` | ✓ 4.63:1 |
| 主綠色 | 嫩綠 | `#7c9e52` | ✗ 2.76:1 |
| 主綠色（文字版） | 深橄欖 | `#5f7738` | ✓ 4.53:1 |
| 灰色 | 石色 | `#a09080` | ✗ 2.79:1，僅供色塊 |

品牌色只用在色條、圓點、圖表線這類非文字元素；文字一律用對應的文字版。

### 4. 響應式斷點

使用 Tailwind 內建斷點：
- `md:` — 768px 以上
- `lg:` — 1024px 以上
- 預設為行動版（無前綴）

## 外部依賴

### CDN

所有 CDN 資源均通過 `<script>` 或 `<link>` 標籤載入，無需 npm 安裝。

| 資源 | 來源 | 用途 |
|------|------|------|
| Tailwind CSS | cdn.tailwindcss.com | 樣式框架 |
| Chart.js | cdn.jsdelivr.net | 圖表與統計 |
| Leaflet | unpkg.com | 互動地圖 |
| Google Fonts | fonts.googleapis.com | 中文字型 (Noto Sans TC) |
| Unsplash | images.unsplash.com | 背景與卡片圖片 |

### 網路相依性

- **完全離線**：不支援（所有資源均在雲端）
- **自訂圖片**：可下載 Unsplash 圖片至本機並更改 URL

## 建立新詳情頁

### 步驟

1. **複製正規頁**
   - 一律複製 `nanshijiao.html`，不要複製其他頁——其他頁都還有偏離（見上方對照表）
   - 存成新檔名（如 `newmountain.html`）

2. **更新標籤**
   - `<title>` — 更改為新路線名稱
   - `<h1>` — 更新標題
   - `<meta name="description">` — 新增頁面描述

3. **更新資料**
   - 改寫 `schedule` 陣列（座標、時間、里程、海拔、`pos` 類型、描述、建議）
   - 改 `TRIP_DATE` 為行程日；日期只寫這一處
   - 改 `openNavigation()` 的目的地座標與 `initMap()` 的 `setView` 中心點
   - 改 `initChart()` 的 `scales.y` 上下限，讓剖面圖填滿畫布

4. **更新本頁色彩**
   - 只改 `:root` 的 `--timeline-bg` 等變數與本頁主色
   - 文字用主色的「文字版」，見上方色系表

5. **關聯到首頁**
   - 在 `index.html` 的 `data` 物件中，設定 `url: "newmountain.html"`

6. **測試**
   - 本機開啟 http://localhost:8000/newmountain.html
   - 檢查地圖、圖表、連結

### 快速檢查清單

規格面（照上方「詳情頁正規規格」逐項對）：

- [ ] 五個段落 id 為 `overview` / `map-section` / `elevation` / `spots` / `timeline`，順序正確
- [ ] 導覽鍵文字為 行程總覽 / 路線圖 / 海拔剖面 / 景點介紹 / 預估進度（或實際行程）
- [ ] 沒有多開段落
- [ ] `<footer>` 在 `<main>` 外面
- [ ] 導覽列為 `fixed`，`<main class="pt-14">`
- [ ] 航點卡欄位 id 用 `wp-pos-label`（不是 `wp-pos`），且含 `wp-time`
- [ ] canvas id 為 `elevation-chart`
- [ ] 日期只在 `TRIP_DATE` 出現一次
- [ ] 灰階用 stone 不用 slate

功能面：

- [ ] 標題正確（瀏覽器標籤頁）
- [ ] 圖片正常載入
- [ ] 地圖顯示正確座標
- [ ] 海拔圖表繪製完整
- [ ] 上/下一個航點鍵可切換，地圖標記同步
- [ ] 返回首頁連結有效
- [ ] 手機版本響應式正常
- [ ] 無 JavaScript 控制台錯誤

無障礙面：

- [ ] skip link 存在且指向 `#main-content`
- [ ] 所有按鈕有 `aria-label`
- [ ] 觸控目標 ≥ 44×44px
- [ ] 小字對比度 ≥ 4.5:1（含深色區塊上的文字，方向與淺底相反）

## 開發流程

### 本機測試

```bash
# 啟動 HTTP 伺服器
python -m http.server 8000

# 訪問本機
open http://localhost:8000
```

### 除錯技巧

1. **檢查圖表是否繪製**
   - 開啟瀏覽器開發者工具 (F12)
   - 查看 Console 標籤是否有錯誤

2. **檢查地圖是否初始化**
   - 確認 Leaflet CDN 載入成功
   - 座標格式正確 (lat, lng)

3. **檢查圖片載入**
   - Network 標籤查看 Unsplash 圖片狀態
   - 若 404，檢查 URL 是否正確

## 命名慣例

### 檔案名稱

- **主首頁**：`index.html`（小寫）
- **詳情頁**：`[mountain-name].html`（使用拼音或英文，例如 `qixingshan.html`, `nanshijiao.html`）
- **文檔**：`README.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`

### CSS 類別

- **共用結構**（定義於 `assets/detail.css`）：`.nav-btn`, `.chart-container`,
  `.timeline-line`, `.waypoint-card`, `.card-hover`, `.info-glass`
- **本頁專屬**：`.stat-card`, `.stamp`, `.hero-accent`, `.section-bar-*`
- **回應式**：`hidden md:flex`, `grid-cols-1 md:grid-cols-2`

同一個元件不要有兩個名字。第五輪已把 `#realMap` 併入 `#map`、
`#elevationChart` 併入 `#elevation-chart`，別再分家。

### JavaScript 變數

- **資料**：`schedule`（航點陣列）、`TRIP_DATE`（行程日）、`data`（僅 index.html）
- **DOM id**：見上方「元件規格」的航點卡欄位表
- **函式**：`initMap()`, `initChart()`, `renderTimeline()`,
  `updateWaypointCard()`, `fetchWeather()`, `renderUI()`（僅 index.html）

## 最佳實踐

### HTML

- 使用語意化標籤（`<section>`, `<article>`, `<nav>`）
- 包含 `lang="zh-TW"` 屬性便於無障礙存取
- 完整的 meta 標籤（charset, viewport, description）

### CSS

- 優先使用 Tailwind 類別
- 避免內聯 `style` 屬性（用 `<style>` 標籤或 `:root` 變數）
- 結構規則寫進 `assets/detail.css`，各頁 `:root` 只給值
- 加新規則前先確認 `detail.css` 沒有同名規則；載入順序是
  inline `<style>` → `detail.css` → `site.css`，後者會蓋掉前者

### JavaScript

- 保持邏輯簡單（無複雜的框架依賴）
- 在頁面載入時呼叫初始化函式（`window.onload` 或 `DOMContentLoaded`）
- 註解應簡潔，說明「為什麼」而非「做什麼」

### 性能

- 圖片使用 `?auto=format&fit=crop&q=80&w=800` 參數自動最佳化
- 延遲載入非關鍵資源（如地圖只在需要時初始化）
- 避免過多的 DOM 操作（批量更新）

## 故障排除

| 問題 | 原因 | 解決 |
|------|------|------|
| 圖片不顯示 | Unsplash CDN 超時 | 檢查網路連接，或替換為其他免費圖庫 |
| 地圖為灰色 | Leaflet CDN 未載入 | 確認 network 標籤有加載 leaflet.css 和 .js |
| 圖表顯示不全 | Canvas 容器高度不足 | 設定父容器明確的 `height` |
| 字型顯示異常 | Google Fonts 未載入 | 檢查 `<link>` 標籤是否正確，網路連接 |
| 導覽按鈕無反應 | JavaScript 未執行 | 開啟開發者工具檢查 Console 錯誤 |

---

**最後更新**：2026-07-31（詳情頁正規規格；10 頁結構已全數收斂）  
如有疑問，參考 CONTRIBUTING.md 提出 issue。
