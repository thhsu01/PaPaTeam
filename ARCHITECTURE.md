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

**導覽鍵**：五顆一致的藥丸，`onclick` 直接寫 `scrollIntoView`，不要包 `scrollToSection()` 輔助函式。

```html
<button onclick="document.getElementById('elevation').scrollIntoView({behavior:'smooth'})"
        class="nav-btn text-xs px-3 py-1.5 rounded-full text-stone-600 hover:bg-stone-200 whitespace-nowrap"
        aria-label="滾動到海拔剖面">海拔剖面</button>
```

平滑滾動由 `assets/site.js` 統一處理 `prefers-reduced-motion`，各頁不必也不該自行判斷。

**地圖與航點卡**：地圖在上、航點卡在下的**單欄堆疊**，外層 `max-w-4xl mx-auto`。
（家族 A 的 6 頁目前是 `lg:grid-cols-3` 地圖與卡片並排，這是全站最大的一處版面差異，
也是收斂成本最高的一項。）航點卡欄位 id 固定如下，`updateWaypointCard()` 只認這些名字：

| id | 內容 | 備註 |
|---|---|---|
| `wp-pos-label` | 位置類型（集合起點、最高點…） | 不叫 `wp-pos` |
| `wp-title` | 地點名稱 | |
| `wp-time` | 預計／實際到達時間 | |
| `wp-dist` | 累計里程 km | `toFixed(2)` |
| `wp-ele` | 海拔 m | |
| `wp-desc` | 該點描述 | |
| `wp-advice` | 隊友建議 | |

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

行程日只寫一次，其餘全部由它推導——天氣查詢日期、天氣卡標題、行程結束提示。
日期散寫在多處是先前實際發生過的 bug 來源。

```javascript
const TRIP_DATE = "2026-08-02";
const tripMD = (() => { const [, m, d] = TRIP_DATE.split('-'); return `${+m}/${+d}`; })();
```

必要函式：`initMap()`、`initChart()`、`renderTimeline()`、`updateWaypointCard(i)`、
`prevWaypoint()`、`nextWaypoint()`、`openNavigation()`。
已完成的行程頁另有 `fetchWeather()` 與 `markTripPast()` 的取捨——
行前頁必須有天氣預報，紀錄頁改為顯示當日實測天氣，此時兩者皆可省略。

### 色彩規格

每頁有自己的主色（碧山粉、七星藍、火炎山橘），**這是刻意的辨識設計，要保留**。
需要一致的是使用方式：

- 灰階一律用 **stone**，不用 slate（`shiqiulinling.html` 目前是 slate，屬偏離）
- 主色不可直接當小字顏色。品牌橙 `#c77c3e` 配淺底只有 2.97:1，
  文字要用加深版 `#9a6030`（4.63:1）。非文字的色條、圓點不受此限。
- 深色區塊上的文字方向相反：`stone-600` 在深底會掉到 2:1 以下，該用 `stone-300/400`。
  改色時務必確認該元素的實際背景，不要跨頁做全域字串替換——
  第三輪就是這樣一次改壞 136 處，詳見 `READABILITY_AUDIT.md`。

主色目前寫死在 markup 的 Tailwind class（`text-pink-700`、`bg-sky-600`…）。
待辦是收成 `--accent` 系列變數，讓換色與對比檢查變成改一個值的事。

### 各頁目前的偏離

| 頁面 | 海拔 id | 景點 id | 段落順序 | 航點類型 id | nav | footer | 灰階 | 地圖版面 |
|---|---|---|---|---|---|---|---|---|
| `nanshijiao` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `qixingshan` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `datunshan` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `dinghu` | ✅ | ✅ | ✅ | ✅ | sticky | ✅ | ✅ | ✅ |
| `bishan` | `analysis` | ✅ | 多 `videos`，景點在海拔前 | `wp-pos` | sticky | 在 main 內 | ✅ | 並排 |
| `huoyianshan` | `analysis` | `deep-dive` | ✅ | `wp-pos` | sticky | 在 main 內 | ✅ | 並排 |
| `laojiujianshan` | `analysis` | ✅ | ✅ | `wp-pos` | sticky | 在 main 內 | ✅ | 並排 |
| `meihuashan` | `analysis` | ✅ | ✅ | `wp-pos` | sticky | 在 main 內 | ✅ | 並排 |
| `mochashan` | `analysis` | ✅ | ✅ | `wp-pos` | sticky | 在 main 內 | ✅ | 並排 |
| `shiqiulinling` | `analysis` | ✅ | 景點在海拔前 | `wp-pos` | sticky | 在 main 內 | slate | 並排 |

表中打勾只代表該欄合規，不代表整頁合規。三項全頁性的落差另計：

- **導覽鍵文字**：10 頁各自為政（總覽／行程總覽／數據總覽／挑戰總覽等），全數需按段落規格表收斂
- **`wp-time` 與 `TRIP_DATE`**：目前只有 `nanshijiao` 有。其餘 9 頁的日期仍散寫在
  markup 與腳本多處，航點卡也看不到到達時間
- **`scrollToSection()` 輔助函式**：6 個家族 A 頁面有，應移除並改為 `onclick` 直接呼叫

**主色寫死在 markup** 是 10 頁共同的問題，不列入本表——那要等 `--accent` 變數層做完才談得上收斂。

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

**最後更新**：2026-07-31（新增詳情頁正規規格，正規頁定為 `nanshijiao.html`）  
如有疑問，參考 CONTRIBUTING.md 提出 issue。
