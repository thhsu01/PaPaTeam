# 快速參考卡片 📋

複製貼上即用的常見元件與模板。編輯內容時快速查閱。

---

## 1. 首頁資料項目（index.html）

### 新增計畫行程

```javascript
{
  title: "路線名稱",
  location: "地點",
  date: "8月2日",
  desc: "單句簡述路線特色與路線名稱",
  img: "https://images.unsplash.com/photo-XXXXX?auto=format&fit=crop&q=80&w=800",
  tag: "PLANNED",
  url: "filename.html"  // 對應的 HTML 檔案，若無則設為 "#"
}
```

### 新增候選路線

```javascript
{
  title: "路線名稱",
  location: "台北內湖",
  desc: "簡短描述（1-2 句）",
  img: "https://images.unsplash.com/photo-XXXXX?auto=format&fit=crop&q=80&w=800",
  tag: "候選",
  url: "filename.html"
}
```

### 新增已完成行程

```javascript
{
  title: "行程名稱",
  date: "YYYY/MM/DD",  // 例如 "2026/06/20"
  location: "地點",
  desc: "簡短敘述路線特色",
  img: "https://images.unsplash.com/photo-XXXXX?auto=format&fit=crop&q=80&w=800",
  isLatest: true,  // 只有最新的設為 true，顯示「NEW」徽章；其餘設 false
  url: "filename.html"  // 若無詳情頁，設為 "#"
}
```

**提示**：
- `date` 格式務必正確（"2026/06/20" 而非 "06/20/2026"）
- `isLatest: true` 最多只有一筆應設為 true
- 圖片 URL 以 `?auto=format&fit=crop&q=80&w=800` 結尾可自動最佳化

---

## 2. 詳情頁卡片與元件

### 統計卡片（Stat Card）

```html
<div class="stat-card rounded-2xl p-4 shadow-sm">
  <div class="text-xs text-stone-400 mb-1">標籤文字</div>
  <div class="font-bold text-stone-800">數值或主標題</div>
  <div class="text-xs text-stone-400 mt-1">子標題或補充</div>
</div>
```

### 信息提示橫幅

```html
<div class="mb-8 max-w-2xl bg-amber-50 border-l-4 rounded-xl px-5 py-4 flex items-start gap-3 shadow-sm" style="border-color:#c77c3e;">
  <span class="text-2xl mt-0.5">🏛️</span>
  <div>
    <div class="font-bold text-amber-900 text-base mb-1">提醒標題</div>
    <p class="text-sm text-amber-800 leading-relaxed">詳細說明與注意事項。</p>
  </div>
</div>
```

### 景點卡片（Waypoint Card）

```html
<div class="waypoint-card bg-white p-6 rounded-2xl border border-stone-200 shadow-sm hover:shadow-md transition-all">
  <div class="flex items-start justify-between mb-4">
    <div>
      <h4 class="font-bold text-lg text-stone-900">景點名稱</h4>
      <p class="text-xs text-stone-400 mt-1">里程 x.xx km | 海拔 xxxm</p>
    </div>
    <span class="text-2xl">🏔️</span>  <!-- 可選的 emoji -->
  </div>
  <p class="text-sm text-stone-600 leading-relaxed">景點描述與觀景要點。</p>
  <div class="text-xs text-stone-400 mt-3">座標：25.0123° N, 121.5456° E</div>
</div>
```

### 戳記徽章（Stamp Badge）

```html
<span class="stamp">8月2日</span>
```

**CSS**（若未在 `<style>` 中定義）：
```css
.stamp {
  display: inline-block;
  border: 3px solid #c77c3e;
  color: #c77c3e;
  font-weight: 900;
  font-size: 11px;
  letter-spacing: 0.15em;
  padding: 4px 10px;
  border-radius: 3px;
  transform: rotate(-1.5deg);
  text-transform: uppercase;
}
```

---

## 3. 地圖初始化（Leaflet）

### 基本地圖模板

```javascript
// HTML：
<section id="map-section" class="py-16 px-6 bg-white">
  <div class="max-w-4xl mx-auto">
    <h2 class="text-2xl font-black text-stone-900 mb-4">路線圖</h2>
    <div id="map"></div>
  </div>
</section>

// JavaScript：
function initMap() {
  // 台灣坐標中心
  const map = L.map('map').setView([25.0, 121.5], 12);
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map);
  
  // 標記起點
  L.marker([25.0123, 121.5456], {
    title: "捷運南勢角站"
  }).addTo(map)
    .bindPopup('<strong>捷運南勢角站</strong><br>集合點');
  
  // 標記終點
  L.marker([25.0456, 121.5789], {
    title: "終點"
  }).addTo(map)
    .bindPopup('<strong>終點</strong>');
}

// 頁面載入時執行
window.addEventListener('load', initMap);
```

### 繪製路線（Polyline）

```javascript
// 在 initMap() 中增加：
const routeCoordinates = [
  [25.0123, 121.5456],  // 起點
  [25.0145, 121.5478],  // 中間點
  [25.0167, 121.5501],  // 終點
];

L.polyline(routeCoordinates, {
  color: '#c77c3e',
  weight: 3,
  opacity: 0.7,
  dashArray: '5, 5'  // 虛線效果
}).addTo(map);
```

---

## 4. 高度圖表（Chart.js）

### 基本海拔圖表

```html
<!-- HTML 容器 -->
<section id="elevation" class="py-16 px-6 bg-stone-50">
  <div class="max-w-4xl mx-auto">
    <h2 class="text-2xl font-black text-stone-900 mb-4">海拔剖面</h2>
    <div style="position: relative; width: 100%; height: 300px;">
      <canvas id="elevation-chart" role="img" aria-label="海拔高度圖表"></canvas>
    </div>
  </div>
</section>

<!-- JavaScript -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
function initElevationChart() {
  const ctx = document.getElementById('elevation-chart').getContext('2d');
  
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['0', '2', '4', '6', '8', '10', '11.76'],  // 里程
      datasets: [{
        label: '海拔高度',
        data: [50, 120, 250, 320, 280, 150, 100],  // 對應海拔
        borderColor: '#c77c3e',
        backgroundColor: 'rgba(199, 124, 62, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        fill: true,
        pointRadius: 4,
        pointBackgroundColor: '#c77c3e',
        pointBorderColor: '#fff',
        pointBorderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#888780',
            font: { size: 12 }
          }
        }
      },
      scales: {
        y: {
          title: { display: true, text: '海拔 (m)' },
          ticks: { color: '#888780' },
          grid: { color: 'rgba(139, 135, 128, 0.1)' }
        },
        x: {
          title: { display: true, text: '里程 (km)' },
          ticks: { color: '#888780' },
          grid: { color: 'rgba(139, 135, 128, 0.1)' }
        }
      }
    }
  });
}

window.addEventListener('load', initElevationChart);
</script>
```

---

## 5. 導覽列按鈕（詳情頁）

### 頂部固定導覽列

```html
<nav class="fixed top-0 w-full z-50 bg-white/80 backdrop-blur border-b border-stone-200/50">
  <div class="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
    <!-- Logo 與品牌 -->
    <a href="index.html" class="flex items-center gap-2 hover:opacity-80 transition-opacity">
      <span class="w-9 h-9 rounded-full bg-emerald-600 flex items-center justify-center text-white font-bold text-base flex-shrink-0">爬</span>
      <span class="font-bold text-stone-800 tracking-tight text-lg">爬爬小隊</span>
    </a>
    
    <!-- 導覽按鈕 -->
    <div class="flex gap-1 overflow-x-auto">
      <button onclick="document.getElementById('overview').scrollIntoView({behavior:'smooth'})" class="nav-btn text-xs px-3 py-1.5 rounded-full text-stone-600 hover:bg-stone-100 whitespace-nowrap">
        行程總覽
      </button>
      <button onclick="document.getElementById('map-section').scrollIntoView({behavior:'smooth'})" class="nav-btn text-xs px-3 py-1.5 rounded-full text-stone-600 hover:bg-stone-100 whitespace-nowrap">
        路線圖
      </button>
      <button onclick="document.getElementById('elevation').scrollIntoView({behavior:'smooth'})" class="nav-btn text-xs px-3 py-1.5 rounded-full text-stone-600 hover:bg-stone-100 whitespace-nowrap">
        海拔剖面
      </button>
    </div>
  </div>
</nav>
```

---

## 6. 天氣 API 呼叫（可選）

### 簡單的天氣預報

```javascript
async function fetchWeather(date) {
  try {
    // 使用免費天氣 API（例如 Open-Meteo）
    const response = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=25.0&longitude=121.5&daily=temperature_2m_max,precipitation,weathercode&timezone=Asia/Taipei`
    );
    const data = await response.json();
    
    // 解析資料
    const weather = data.daily.weathercode[0];
    const temp = data.daily.temperature_2m_max[0];
    
    // 更新 HTML
    document.getElementById('weather-main').textContent = `${temp}°C`;
    document.getElementById('weather-sub').textContent = getWeatherDescription(weather);
  } catch (error) {
    console.log('天氣預報載入失敗');
  }
}

function getWeatherDescription(code) {
  const weatherMap = {
    0: '晴朗',
    1: '大致晴朗',
    2: '多雲',
    3: '陰天',
    45: '霧',
    61: '小雨',
    63: '中雨',
    65: '大雨'
  };
  return weatherMap[code] || '不詳';
}

// 呼叫
fetchWeather('2026-08-02');
```

---

## 7. 常用 Tailwind 類別速查表

### 尺寸與間距

| 用途 | 類別 | 等同 CSS |
|------|------|---------|
| 圓角（大） | `rounded-2xl` | `border-radius: 1rem;` |
| 圓角（小） | `rounded-full` | `border-radius: 9999px;` |
| Padding | `p-4` | `padding: 1rem;` |
| Padding X | `px-6` | `padding-left/right: 1.5rem;` |
| Padding Y | `py-4` | `padding-top/bottom: 1rem;` |
| Margin bottom | `mb-4` | `margin-bottom: 1rem;` |
| Gap | `gap-3` | `gap: 0.75rem;` |

### 文字與顏色

| 用途 | 類別 | 用途 |
|------|------|------|
| 大標題 | `text-2xl font-black` | h2 級標題 |
| 中標題 | `text-lg font-bold` | h4 級標題 |
| 小字 | `text-xs text-stone-400` | 次要資訊或提示 |
| 主色 | `text-stone-900` | 深灰（主文字） |
| 次色 | `text-stone-600` | 中灰（次要文字） |
| 淡色 | `text-stone-400` | 淺灰（提示） |

### 區塊與布局

| 用途 | 類別 | 說明 |
|------|------|------|
| Flexbox | `flex items-center justify-between` | 水平排列，間距均分 |
| Grid | `grid grid-cols-2 gap-4` | 2 欄網格 |
| 固定定位 | `fixed top-0 left-0 z-50` | 固定在視窗頂左 |
| 陰影 | `shadow-sm` | 細微陰影 |
| 邊框 | `border border-stone-200` | 1px 灰邊框 |

### 回應式

| 斷點 | 類別前綴 | 何時生效 |
|------|---------|---------|
| 行動 | 無前綴 | 預設（所有裝置） |
| 平板 | `md:` | 768px 以上 |
| 桌機 | `lg:` | 1024px 以上 |

**例子**：
```html
<!-- 行動版 1 欄，平板 2 欄，桌機 3 欄 -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
```

---

## 8. 色系快速參考

| 用途 | 十六進制 | 類別 | 場景 |
|------|---------|------|------|
| 主橙色 | `#c77c3e` | `.section-bar-orange` | 戳記、按鈕、強調 |
| 主綠色 | `#7c9e52` | `.section-bar-green` | 完成標記 |
| 石灰 | `#a09080` | `.section-bar-stone` | 分隔線、中性元素 |
| 深文字 | `#3a3632` | `text-stone-900` | 主要標題 |
| 淡背景 | `#f5f3ef` | `bg-stone-50` | 背景區塊 |

---

## 9. 快速建立新路線檢查清單

### Step 1：複製檔案
- [ ] 複製 `nanshijiao.html` → `newmountain.html`

### Step 2：更新基本資訊
- [ ] 修改 `<title>` 標籤
- [ ] 更新 `<h1>` 標題
- [ ] 修改 `routeData` 物件

### Step 3：更新數據
- [ ] 更新 `title`, `location`, `distance`, `elevation_gain`
- [ ] 修改座標（起終點、中間點）
- [ ] 更新海拔高度資料點

### Step 4：測試
- [ ] 本機開啟檢查
- [ ] 地圖顯示正確
- [ ] 圖表繪製完整
- [ ] 手機版本正常

### Step 5：關聯首頁
- [ ] 在 `index.html` 的 `data.candidate` 或 `data.planned` 中新增項目
- [ ] 設定 `url: "newmountain.html"`

---

**最後更新**：2026-07-30  
如需更多範例，參考 ARCHITECTURE.md
