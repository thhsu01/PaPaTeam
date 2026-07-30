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

詳情頁 (individual route HTML)
  ├─ 返回按鈕 (back to index)
  ├─ 導覽列 (固定)
  ├─ 行程總覽 (overview section)
  ├─ 路線圖 (Leaflet map)
  ├─ 海拔剖面 (Chart.js elevation)
  ├─ 景點介紹 (waypoints)
  ├─ 預估進度 (timeline)
  └─ 頁腳
```

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

## 詳情頁結構

每個登山路線都有對應的 HTML 詳情頁（如 `nanshijiao.html`、`qixingshan.html`）。

### 基本架構

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <!-- Meta 標籤 -->
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>路線名 — 爬爬小隊</title>
  
  <!-- CDN 依賴 -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  
  <!-- 自訂樣式 -->
  <style>
    /* 頁面特有的樣式 */
  </style>
</head>

<body>
  <!-- 返回按鈕 (固定頂左) -->
  <a href="index.html" class="fixed top-4 left-4 ...">← 返回首頁</a>
  
  <!-- 導覽列 (固定頂部) -->
  <nav class="fixed top-0 ...">
    <!-- 導覽按鈕，點擊平滑滾動到各 section -->
  </nav>
  
  <main class="pt-14">
    <!-- ═══ OVERVIEW ═══ -->
    <section id="overview">
      <!-- Hero 標題、日期、提醒、地點資訊卡片、統計數據 -->
    </section>
    
    <!-- ═══ MAP ═══ -->
    <section id="map-section">
      <!-- Leaflet 地圖容器 -->
      <div id="map"></div>
    </section>
    
    <!-- ═══ ELEVATION ═══ -->
    <section id="elevation">
      <!-- Chart.js 海拔圖表 -->
      <canvas id="elevation-chart"></canvas>
    </section>
    
    <!-- ═══ WAYPOINTS / SPOTS ═══ -->
    <section id="spots">
      <!-- 景點卡片，每個卡片包含圖片、描述、座標 -->
    </section>
    
    <!-- ═══ TIMELINE ═══ -->
    <section id="timeline">
      <!-- 預估進度表，如時間表、難度指標 -->
    </section>
  </main>
  
  <!-- JavaScript 初始化 -->
  <script>
    // 路線資料
    const routeData = { ... }
    
    // 地圖初始化
    function initMap() { ... }
    
    // 圖表初始化
    function initElevationChart() { ... }
    
    // 天氣 API 呼叫（若需要）
    async function fetchWeather() { ... }
  </script>
</body>
</html>
```

### 典型的資料物件

```javascript
const routeData = {
  title: "微笑山線 × 南勢角山 × 一線天",
  description: "從捷運南勢角站出發...",
  location: "新北市中和",
  difficulty: "中等",
  duration: "6.5 小時",
  distance: "11.76 km",
  elevation_gain: "674 m",
  max_elevation: "320 m",
  start_point: { lat: 25.0123, lng: 121.5456, name: "捷運南勢角站" },
  waypoints: [
    { name: "圓通禪寺", lat: 25.0145, lng: 121.5478, desc: "一線天起點" },
    { name: "南勢角山", lat: 25.0167, lng: 121.5501, desc: "小百岳 #302" }
  ],
  elevation_data: [
    // 里程數, 海拔高度
    [0, 50], [1.5, 120], [3.2, 250], ...
  ],
  tips: ["務必帶足水", "防曬很重要", ...],
  weather_date: "2026-08-02"
};
```

## 常見 CSS 模式

### 1. 卡片（Card）

```html
<div class="stat-card rounded-2xl p-4 shadow-sm">
  <!-- 統計或資訊卡 -->
  <div class="text-xs text-stone-400 mb-1">標籤</div>
  <div class="font-bold text-stone-800">數值或標題</div>
</div>
```

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
  border: 3px solid #c77c3e;
  color: #c77c3e;
  font-weight: 900;
  padding: 4px 10px;
  border-radius: 3px;
  transform: rotate(-1.5deg);
  text-transform: uppercase;
}
```

### 3. 色系

| 用途 | 顏色 | 十六進制 |
|------|------|---------|
| 主橙色 | 琥珀 | `#c77c3e` |
| 主綠色 | 嫩綠 | `#7c9e52` |
| 灰色 | 石色 | `#a09080` |

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

1. **複製模板**
   - 選擇現有的詳情頁（如 `nanshijiao.html`）
   - 複製為新檔名（如 `newmountain.html`）

2. **更新標籤**
   - `<title>` — 更改為新路線名稱
   - `<h1>` — 更新標題
   - `<meta name="description">` — 新增頁面描述

3. **更新資料**
   - 修改 JavaScript 中的 `routeData` 物件
   - 更新座標、里程、海拔等

4. **關聯到首頁**
   - 在 `index.html` 的 `data` 物件中，設定 `url: "newmountain.html"`

5. **測試**
   - 本機開啟 http://localhost:8000/newmountain.html
   - 檢查地圖、圖表、連結

### 快速檢查清單

- [ ] 標題正確（瀏覽器標籤頁）
- [ ] 圖片正常載入
- [ ] 地圖顯示正確座標
- [ ] 海拔圖表繪製完整
- [ ] 返回首頁連結有效
- [ ] 手機版本響應式正常
- [ ] 無 JavaScript 控制台錯誤

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

- **容器**：`container`, `section`, `card`
- **狀態**：`active`, `disabled`, `hover`
- **工具**：`glass-card`, `stamp`, `stat-card`
- **回應式**：`hidden md:flex`, `grid-cols-1 md:grid-cols-2`

### JavaScript 變數

- **資料物件**：`routeData`, `data`, `weatherData`
- **DOM 元素**：`mapContainer`, `elevationChart`, `weatherMain`
- **函式**：`initMap()`, `fetchWeather()`, `renderUI()`

## 最佳實踐

### HTML

- 使用語意化標籤（`<section>`, `<article>`, `<nav>`）
- 包含 `lang="zh-TW"` 屬性便於無障礙存取
- 完整的 meta 標籤（charset, viewport, description）

### CSS

- 優先使用 Tailwind 類別
- 避免內聯 `style` 屬性（用 `<style>` 標籤）
- 使用有意義的顏色變數（如 `#c77c3e` 對應琥珀色）

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

**最後更新**：2026-07-30  
如有疑問，參考 CONTRIBUTING.md 提出 issue。
