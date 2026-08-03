# 快速參考卡片 📋

複製貼上即用的片段。**規範權威是 `ARCHITECTURE.md`**——本檔只是它的速查版，
兩邊若有出入，以 `ARCHITECTURE.md` 為準。

> **本檔於 2026-08-03 全面重寫。** 舊版描述的是 `assets/detail.js` 抽出以前的寫法
> （`routeData` 物件、各頁自己寫 `initMap()` 與 `initElevationChart()`），那套結構
> 早已不存在，照抄會做出一頁不符規格的東西。

---

## 1. 首頁資料項目（index.html）

三個陣列都在 `index.html` 底部的 `data` 物件裡。

### 計畫行程 `data.planned`

```javascript
{
  title: "路線名稱",
  location: "地點",
  date: "8月2日",              // 顯示用的口語日期
  desc: "單句簡述路線特色",
  img: "https://images.unsplash.com/photo-XXXXX?auto=format&fit=crop&q=80&w=800",
  tag: "PLANNED",
  url: "filename.html"          // 沒有詳情頁就填 "#"
}
```

陣列留空時 `renderUI()` 會渲染「目前尚無計畫行程」的虛線佔位卡，不需另外處理。

### 候選路線 `data.candidate`

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

### 已完成行程 `data.completed`

```javascript
{
  title: "行程名稱",
  date: "2026/06/20",           // 站上一律 YYYY/MM/DD
  location: "地點",
  desc: "簡短敘述路線特色",
  img: "https://images.unsplash.com/photo-XXXXX?auto=format&fit=crop&q=80&w=800",
  isLatest: true,               // 只有最新那筆為 true，顯示「NEW」徽章
  url: "filename.html"
}
```

**提示**：

- 行程編號（`#1`–`#21` 徽章）**不要寫進資料**。`renderUI()` 依日期排序後推導，
  補登舊行程時後面的編號會自動遞補。
- `isLatest: true` 最多只有一筆。新行程歸檔時記得把舊的那筆改成 `false`。
- 補登舊行程直接插進陣列即可，順序不影響編號。

---

## 2. 詳情頁：資料與設定

詳情頁**不各自實作地圖與圖表**。機制全在 `assets/detail.js`，各頁只提供
`schedule` 陣列與一份 `PaPaDetail.init({...})` 設定。

### 航點物件 `schedule`

```javascript
const schedule = [
  { lat: 25.036395, lng: 121.587461, time: "09:48", loc: "松山慈惠堂登山口",
    dist: 0.00, ele: 60, pos: "集合起點",
    desc: "行程起點。GPS 於 09:48 開始記錄。" },

  { lat: 25.031220, lng: 121.583710, time: "10:57", loc: "虎山峰 (H142m)",
    dist: 2.82, ele: 142, pos: "瞭望台",
    desc: "累計 2.82 km。虎山山頂的瞭望台，標高 142 m。" },
];
```

| 欄位 | 說明 |
|---|---|
| `lat` / `lng` | 座標，地圖標記與軌跡對位都靠它 |
| `time` | 已完成頁是實際時刻；計畫／候選頁是預估時刻 |
| `loc` | 航點名稱，`(H142m)` 這類標高後綴會被圖表標籤剝掉 |
| `short` | 選填。圖表標籤太長時用它取代 `loc` |
| `dist` | 累計里程（km）。**GPS 實測優先** |
| `ele` | 海拔（m）。**採地形圖數值，不用 GPS 高程** |
| `pos` | 航點類型，決定標記大小與顏色（見 `map.marker`） |
| `desc` | 景點卡內文 |
| `advice` | 選填。隊友建議，**沒走過就留空，不要編** |
| `plan` | 選填，僅已完成頁。當初的預估時刻，時間軸會並排顯示 |

**不得編造**：`dist` 與 `advice` 都是實走才知道的東西。缺就留空——
`hideEmptyAdvice` 會把空的建議框整塊收起來，不會留一個空框在卡片下方。

### `PaPaDetail.init()` 設定

```javascript
PaPaDetail.init({
  schedule,
  tripDate: TRIP_DATE,              // 日期只在這一處出現
  nav: [25.036395, 121.587461],     // 「開啟導航」的目的地

  card: { follow: 'popup', wrap: 'clamp', hideEmptyAdvice: true },

  weather: { lat: 25.0327, lng: 121.5849 },

  map: {
    setView: [[25.0330, 121.5855], 15],
    attribution: 'Leaflet | © OpenStreetMap',
    popup: true,
    marker: (wp, i, n) => {
      const isStartEnd = i === 0 || i === n - 1;
      const isPeak     = wp.pos === "瞭望台";
      return {
        radius: isStartEnd ? 9 : isPeak ? 8 : 6,
        fillColor: isStartEnd ? ACCENT : isPeak ? PEAK : '#888',
        opacity: 1, fillOpacity: 0.92
      };
    }
  },

  chart: {
    label: wp => wp.short || wp.loc.replace(/\s*\(H[^)]*\)/, ''),
    fillAlpha: 0.10,
    dataset: { borderWidth: 2.5, pointRadius: 5 },
    options: { /* Chart.js 選項，會與預設值合併 */ }
  }
});
```

`ACCENT` / `PEAK` / `STONE` 是頁面腳本開頭以 `getComputedStyle` 從 `:root`
取出的實際色值。**腳本裡不能直接寫 `var(--accent)`**——那些值最終進到 canvas 的
`fillStyle`，canvas 不解析 CSS 變數。

### 實走軌跡（僅已完成行程）

有 GPS 紀錄的行程，地圖畫實際軌跡而不是航點連成的直線——那條線會繞過航點之間
看不出來的髮夾彎。

```javascript
// assets/tracks/hushan-2024-04-20.js
window.PaPaTracks = window.PaPaTracks || {};
window.PaPaTracks['hushan-2024-04-20'] = [
  [25.03640,121.58746],
  [25.03612,121.58733],
  // …Douglas–Peucker 簡化後的座標，eps = 5 m
];
```

```html
<script src="assets/tracks/hushan-2024-04-20.js"></script>
```

```javascript
map: {
  track: { points: PaPaTracks['hushan-2024-04-20'], weight: 4, opacity: 0.85 },
  // …
}
```

沒給 `track.points` 就沿用航點直線，計畫與候選頁不受影響。

---

## 3. 詳情頁：常用 markup

### 航點卡欄位（`#spots`）

id 是固定的，`detail.js` 靠它們填值。`wp-pos-label` 不是 `wp-pos`。

```html
<div class="text-xs text-stone-600 uppercase tracking-widest mb-3" id="wp-pos-label">集合起點</div>
<div class="flex items-center gap-3 mb-3">
  <button onclick="prevWaypoint()" class="w-10 h-10 rounded-full bg-white border border-stone-200 text-stone-600 hover:bg-stone-100 flex items-center justify-center text-sm min-w-[44px] min-h-[44px]" aria-label="上一個航點">&lt;</button>
  <h3 class="text-lg font-bold text-stone-900 flex-1" id="wp-title">航點名稱</h3>
  <button onclick="nextWaypoint()" class="w-10 h-10 rounded-full bg-white border border-stone-200 text-stone-600 hover:bg-stone-100 flex items-center justify-center text-sm min-w-[44px] min-h-[44px]" aria-label="下一個航點">&gt;</button>
</div>
<div class="flex gap-4 mb-3 text-sm text-stone-600">
  <span>實際時間 <strong class="text-stone-800" id="wp-time">09:48</strong></span>
  <span>累計里程 <strong class="text-stone-800" id="wp-dist">0.00</strong> km</span>
  <span>海拔 <strong class="text-stone-800" id="wp-ele">60</strong> m</span>
</div>
<p class="text-base text-stone-700 mb-3" id="wp-desc">航點描述。</p>
<div class="rounded-xl p-3" style="background:var(--accent-tint); border:1px solid var(--accent-border);">
  <div class="text-xs font-medium mb-1" style="color:var(--accent-strong);">隊友建議</div>
  <p class="text-xs" style="color:var(--accent-strong);" id="wp-advice"></p>
</div>
```

`min-w-[44px] min-h-[44px]` 是無障礙觸控目標下限，別拿掉。

### 海拔圖容器（`#elevation`）

canvas 的 id 必須是 `elevation-chart`（不是 `elevationChart`）。

```html
<div class="chart-container">
  <canvas id="elevation-chart" role="img" aria-label="海拔剖面圖"></canvas>
</div>
```

### 時間軸容器（`#timeline`）

```html
<div id="timeline-container" class="relative max-w-2xl mx-auto">
  <div class="timeline-line"></div>
</div>
```

**渲染前不要清空容器**——那會連同 `.timeline-line` 一起清掉，時間軸的直線就不見了。

### 提示橫幅

```html
<div class="mb-8 max-w-2xl rounded-xl px-5 py-4 flex items-start gap-3 shadow-sm border-l-4"
     style="background:var(--accent-tint); border-color:var(--accent);">
  <span class="text-2xl mt-0.5">🏛️</span>
  <div>
    <div class="font-bold text-base mb-1" style="color:var(--accent-strong-deep);">提醒標題</div>
    <p class="text-sm leading-relaxed" style="color:var(--accent-strong-deep);">詳細說明與注意事項。</p>
  </div>
</div>
```

---

## 4. 色彩

### 主色層（每頁一份，只改 `:root`）

換主色**只動這一段**，markup 與腳本都不必改。

```css
:root {
  --accent:             #0d9488;   /* 裝飾：色條、圓點、地圖軌跡、圖表線 */
  --accent-strong:      #0f766e;   /* 淺底上的文字（4.94:1） */
  --accent-strong-deep: #115e59;   /* 淡底卡片上的內文，再深一階（6.84:1） */
  --accent-tint:        #f0fdfa;   /* 淡底 */
  --accent-border:      #cceee9;   /* 淡框線 */
  --accent-border-deep: #b8e3db;   /* 深一階的框線 */
}
```

新頁選色後**要實測對比度**再把數字寫進註解——底色是頁底 `#f5f3ef`，不是白色。

### 跨頁語意色（不進 `--accent`，刻意的）

| 意義 | 色值 |
|---|---|
| 山頂 | `#7c9e52` |
| 警告 | 紅 |
| 外部連結 | 藍 |
| 注意 | 琥珀 |

這些跨頁共用同一套意義，不屬於任何單頁的識別色。

### 灰階與背景

| 用途 | 值 |
|---|---|
| 頁底 | `#f5f3ef`（`--page-bg`，**不是** `bg-stone-50`） |
| 內文 | `#3a3632`（`--page-fg`） |

**灰階一律用 stone，不用 slate。**

### 小字顏色的鐵則

| 類別 | 白底 | 頁底 `#f5f3ef` | `bg-stone-100` |
|---|---|---|---|
| `text-stone-400` | ❌ | ❌ | ❌ |
| `text-stone-500` | 4.80:1 ✅ | 4.33:1 ❌ | 4.40:1 ❌ |
| `text-stone-600` | ✅ | 6.88:1 ✅ | 6.99:1 ✅ |

**小字一律 `text-stone-600` 起跳。** `text-stone-500` 只在白底安全，很容易漏看——
第七輪就是這樣踩到的，詳見 `READABILITY_AUDIT.md`。

---

## 5. 常用 Tailwind 速查

### 尺寸與間距

| 用途 | 類別 | 等同 CSS |
|---|---|---|
| 圓角（大） | `rounded-2xl` | `border-radius: 1rem;` |
| 圓角（滿） | `rounded-full` | `border-radius: 9999px;` |
| Padding | `p-4` | `padding: 1rem;` |
| Padding X | `px-6` | `padding-left/right: 1.5rem;` |
| Margin bottom | `mb-4` | `margin-bottom: 1rem;` |
| Gap | `gap-3` | `gap: 0.75rem;` |

### 字級

| 用途 | 類別 | px |
|---|---|---|
| 標題 | `text-2xl`–`text-6xl` | 24–60 |
| 卡片標題 | `text-lg`–`text-2xl` | 18–24 |
| 內文 | `text-base` | 16 |
| 小字 | `text-xs` | 12（屬一般文字，對比度門檻仍是 4.5:1） |

### 內容寬度

| 段落 | 類別 |
|---|---|
| 一般段落 | `max-w-4xl` |
| 時間軸 | `max-w-2xl` |

### 響應式

| 斷點 | 前綴 | 何時生效 |
|---|---|---|
| 行動 | 無 | 預設 |
| 平板 | `md:` | 768px 以上 |
| 桌機 | `lg:` | 1024px 以上 |

---

## 6. 建立新詳情頁

完整步驟與檢查清單在 **`ARCHITECTURE.md` §建立新詳情頁**，這裡只列最容易忘的三件事：

1. **複製 `nanshijiao.html`**，不要複製其他頁。
2. **五個段落 id 固定**：`overview` → `map-section` → `elevation` → `spots` → `timeline`，
   順序不可換、不可多開。
3. **日期只寫 `TRIP_DATE` 一處**；候選／計畫頁沒有 `TRIP_DATE`。

---

**最後更新**：2026-08-03（全面重寫以對應 `detail.js` 架構）
