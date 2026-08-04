# 架構指南

本文檔說明爬爬小隊網站的代碼結構、慣例與最佳實踐。適合開發者和內容編輯參考。

**名詞看 [`CONTEXT.md`](CONTEXT.md)**（行程、航點、航點短名、最高點 vs 山頂），
**承重的決策看 [`docs/adr/`](docs/adr/)**。本檔管的是版面與結構規格。

## 整體架構

```
主首頁 (index.html)
  ├─ 導覽列 (固定頂部)
  ├─ 英雄區 (hero banner)
  ├─ 計畫行程 (planned)
  ├─ 候選清單 (candidate)
  ├─ 歷史紀錄 (completed)
  └─ 頁腳 (footer)

詳情頁 (22 頁，正規規格見下)
  ├─ skip link
  ├─ 導覽列 (fixed 頂部，站徽 + 5 顆藥丸)
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

最早的 10 個詳情頁出自兩套模板世代，結構相同但命名與版面各行其是。本節定義**唯一一份正規規格**：
新頁一律照此建立，既有頁逐步收斂到此。規格若要改，改這裡，不要只改某一頁。
2026-08-02 起新增的頁面（`hushan`、`nangangshan`、`datongshan`、`shanying`）都是照本規格
從零建起的，不帶模板世代的包袱。

### 正規頁：`nanshijiao.html`

以它為基準的理由：

- 段落 id 與順序屬多數派（另 3 頁相同）
- 功能最完整：`TRIP_DATE` 單一日期來源、行程結束提示、航點含預計時間、
  天氣標題與內文同步、skip link、aria-label、44px 觸控目標
- 對比度是刻意調過的（見 `READABILITY_AUDIT.md`），不是碰巧合格

**它自己的已知偏離**（複製時不要跟著抄）：深色專題面板與語意色（`#1c1c1c` 的
深底、`#7c9e52` 的山頂綠等）仍是行內十六進位值，未納入 `--accent` 層。那是刻意的
——理由見文末「尚未收斂的一件事」。主色本身早已收成 token，複製時照抄無妨。

收斂已完成，22 頁的結構現在都符合本規格；仍未補齊的內容缺口見文末「尚未收斂的一件事」。

### 段落規格

id、順序、導覽文字三者都是規格的一部分，不可自由發揮。

| 順序 | `<section id>` | 導覽鍵文字 | `<h2>` 標題 | 必要性 |
|:--:|---|---|---|---|
| 1 | `overview` | 行程總覽 | 自由（含路線名） | 必要 |
| 2 | `map-section` | 路線圖 | 互動路線圖 | 必要 |
| 3 | `elevation` | 海拔剖面 | 海拔高度剖面圖 | 必要 |
| 4 | `spots` | 景點介紹 | 自由（含「導覽」或「亮點」） | 必要 |
| 5 | `timeline` | 預估進度 / 實走紀錄 | 預計行程進度 / 實走時間軸 | 必要 |

四條規則：

- **`timeline` 是唯一容許二選一的文字**，且不是喜好問題：行程日之前用「預估進度」，
  行程結束後改「實走紀錄」。判斷依據是頁面性質，不是編輯當下的心情。
- **`<h2>` 容許加括號後綴，但主詞必須一字不差。** `預計行程進度（約 4H）`、
  `互動路線圖與航點切換` 都合法；`稜線縱走地圖`、`全線航點導航`、`海拔高度剖面`
  （漏「圖」）則否。後綴是補充，不是改名——讀者靠主詞認出這是哪一段。
- **不新增段落。** 影片、文史專題、地質專題這類內容放進 `spots` 段內的卡片，
  不要另開 `<section>`——多一個段落就多一顆導覽鍵，各頁導覽列長度就會不一致。
- **`overview` 必須有一排統計數字**：總里程、耗時、爬升、最高海拔。版面各家族略有不同
  （多數是 `grid-cols-2 md:grid-cols-4` 的大字，`bishan` 是五格卡片），但**總里程一定要
  出現在畫面上**。已完成頁標「實走里程」，計畫／候選頁標「總里程 km（估）」。
  `shiqiulinling` 先前只有集合資訊、整頁看不到總里程，是這條規則的由來。

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
  <script src="assets/site.js"></script>
</head>
<body class="antialiased">
  <a href="#main-content" class="skip-link">跳至主要內容</a>

  <!-- 不要另外加左上的 fixed 返回鍵：它會被這條導覽列蓋住。站徽就是回首頁的入口。 -->
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
站徽是識別標誌，每頁換一個就失去作用。它同時是**唯一的回首頁入口**，
所以 `aria-label` 必要。

```html
<a href="index.html" class="flex items-center gap-2 hover:opacity-80 transition-opacity" aria-label="爬爬小隊首頁">
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

各頁不直接設定 Chart.js，只給領域旋鈕；設定樹由 `detail.js` 的 `initChart()` 組出。
理由見 [ADR-0001](docs/adr/0001-chartjs-behind-the-seam.md)。

```javascript
chart: { elevationFloor: 450, lineColor: '--accent-deep', palette: PAL }
```

`elevationFloor` 是編輯判斷（高山路線從 0 起會浪費半張圖）；`elevationMax` 不給就讓
Chart.js 自己算——它的刻度演算法挑的數字不是固定百分比，硬推導會改掉畫面。

**航點配色**：地圖標記、圖表資料點、時間軸圓點三處是同一個決定，走
`PaPaDetail.palette({ accent, isPeak })` 取得，不要各寫一份。

```javascript
const PAL = PaPaDetail.palette({ accent: ACCENT, isPeak: wp => wp.pos === "最高點" });
// PAL.color(wp, i, n)  起訖點→主色、最高點→#7c9e52、其餘→#a09080
// PAL.radius(wp, i, n) 起訖點 9、最高點 8、其餘 6
```

各頁只宣告主色與「哪個 `pos` 算山頂」——`jiantanshan` 是觀機平台、`hushan` 是瞭望台。
第三種語意用 `palette({ extra })` 表達（`datongshan` 的展望台、`nanshijiao` 的信仰地標、
`bishan` 的賞櫻點、`mochashan` 的折返點、`huoyianshan` 的大峽谷），只開一層。

2026-08-04 導入的原因是這個決定寫三份就會漂：`caolingguidao` 加了集合地點之後只更新
地圖那份，同一個航點在地圖上是端點色、在圖表上卻是一般色。同日量測發現「三處共用」
這句話當時只有海拔圖做到（18/18），地圖標記與時間軸各只有 6/18——`datunshan`、
`qixingshan`、`shanying` 的最高點在海拔圖上是綠、在地圖與時間軸上是琥珀。
**22 頁三個介面現已全部收斂，並由 `tools/spec_sweep.py` 逐區塊檢查**：`chart`、`marker`、
`timeline` 三個區塊都必須真的引用 `palette`，光在頁首宣告 `PAL` 不算。

**時間軸**：`<div id="timeline-container">` 內含一個 `.timeline-line`，其餘由 JS 生成。
渲染前不要清空容器——那會連同直線一起清掉。meihuashan 先前就是這樣，
當時是唯一一頁沒有時間軸直線的（已修正）。

各頁不寫時間軸的 HTML 樣板，只說要顯示哪些欄位：

```javascript
timeline: { emoji: POS_EMOJI, palette: PAL }                              // 行列式，12 頁
timeline: { layout: 'card', fields: ['dist', 'ele'], palette: PAL }       // 卡片式，6 頁
```

| 旋鈕 | 意義 |
|---|---|
| `layout` | `'list'`（預設）或 `'card'`。兩種版面家族，不是喜好——卡片式頁面的時間軸沒有段落底色 |
| `fields` | 卡片主體顯示哪些欄位，預設 `['desc']`。目前用到 `desc` / `dist` / `ele` |
| `emoji` | `pos` → emoji 的對照表，省略則不顯示 |
| `palette` | 圓點色，見上方「航點配色」 |
| `hover` | 行列式專用。`'lighten'`（預設，暖底頁）或 `'darken'`（`bg-stone-50` 的頁） |

「原估時間」不設旋鈕：航點有 `plan` 且與實走 `time` 不同就標，跟航點短名的 `short`
是同一條「例外用資料表達」的規則。警示地形紅 `#ef4444` 的圓點會脈動——那是全站規則，
不是逐頁掛的 class。

2026-08-04 收進來之前，18 頁手寫了 201 行樣板。量下來只有兩種結構家族，其餘差異
（`mb-8`／`mb-10`／`mb-12`、`rounded-2xl`／`rounded-[1.5rem]`）是世代殘留，不是決定。

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

**已完成的行程另有 `plan` 欄位**，放當初的預估時刻。時間軸把它並排在實際時刻
旁邊（`原估 07:30`），計畫與實走的落差不必另外解釋。行前頁不需要這個欄位。

**`xbaiyue`** 標記這個航點是台灣小百岳：`xbaiyue: 13` 顯示「⭐ 小百岳 #13」，
查不到編號時寫 `xbaiyue: true` 顯示「⭐ 小百岳」——不要編一個號碼出來。
它**不能**寫進 `pos`：一座山可以同時是最高點與小百岳（全站六座裡有三座就是），
`pos` 只能有一個值，塞進去就會逼出假的二選一（見 `CONTEXT.md`「小百岳」）。
表現全部由 `detail.js` 負責，各頁只加這個欄位。`tools/spec_sweep.py` 會擋兩件事：
`pos` 含「小百岳」、以及 `desc`／`advice` 宣稱是小百岳卻沒有這個欄位。

`short`、`plan`、`xbaiyue` 是同一條規則的三個實例：**例外用資料表達，不是每頁一個旋鈕。**

`ele` **優先採地形圖數值，不改用 GPS 高程**。GPS 高程雜訊很大：南勢角 8/2 的紀錄
在同一座五尖山前後讀到 281 與 316 m，起點捷運站（實際 20 m）讀到 10 m 甚至 -0.5 m。
同一份軌跡依平滑程度可以推出 400 到 550 m 的任一個總爬升值，沒有一個比地形圖可靠，
所以爬升統計也維持地形圖估算。`time` 與 `dist` 則相反——GPS 實測優先。

唯一的例外是**走完才補上的航點**：它們不在原計畫裡，沒有地形圖數值可對。此時取軌跡
前後 60 m 內取樣點的高程中位數再取整到 5 m，並在頁面腳本註明是 ±25 m 的估計值。
不要為了看起來精確而寫進 `loc` 的 `(H___m)` 標註——那個括號代表的是圖資高度。

補上的航點通常沒有 `advice`（當初沒寫、事後也不該補編）。這時要在 `card` 設定加上
`hideEmptyAdvice: true`，建議框才會整塊收起來，而不是留一個空框在卡片下方。

#### 集合地點與起錄點

這是兩件事，頁面上要分得開。**集合地點是隊伍實際會合的地方，GPS 起錄點是軌跡的第一個
點**——它們同一個位置只是巧合，目前三頁都不是：

| 頁面 | 集合地點 | 起錄點 | 兩者關係 |
|------|---------|--------|---------|
| `jiantanshan` | 銘傳大學校門口 | 東側 210 m 處 | 集合後走了一段才起錄 |
| `jinmianshan` | 金面山步道登山口 | 136 巷口（140 m 外） | 起錄點在集合點之前，隊伍在巷底會合 |
| `caolingguidao` | 福隆火車站 | 遠望坑口（1.9 km 外） | 集合後搭接駁車前往起登點 |

寫法四件事：航點 `pos` 標「集合地點」；`dist` 維持 `0.00` 不累計（接駁與走到起錄點
那段都不算進總里程）；`#overview` 第一張卡的標題從「起登點」改成「集合地點」；
導航鍵指向集合點——讀者要去的是那裡，不是軌跡碰巧開始的地方。

集合點常在 GPS 起錄前，所以它的**時刻往往沒有紀錄**。這時 `time` 填 `"—"`，不要
拿起錄時間頂替：`caolingguidao` 若把福隆車站也標成 09:44，時間軸上就會出現兩個
09:44 卻相距 1.9 km。海拔同理，沒量到就在 `desc` 裡講明是概略值。

#### 里程健全性

**每段 `dist` 的增量不得小於該段兩航點之間的直線距離**（Haversine）。走過的路不可能
比直線短，所以這條是純粹的物理下限，違反就一定是資料錯誤。交通接駁段例外——公車或
接駁車那一段里程不累計，維持與前一點相同的值。

這是本專案最便宜的資料檢查，改完任何 `schedule` 都該跑一次。2026-08-03 首次全站掃描
抓到 5 頁共 9 筆，兩種成因各半：

- **估算頁把段長猜得太短**（`bishan` 2 筆、`datongshan` 1 筆、`datunshan` 4 筆）。
  修法是重新分配段長，總里程有依據就別動。
- **GPX 頁的 `dist` 與航點座標對不上**（`nanshijiao` 2 筆、`mochashan` 1 筆、
  `meihuashan` 1 筆）。這種要**回頭比對軌跡**，不能靠加大數字硬修——把
  `assets/tracks/` 的軌跡算出累計距離，找每個航點座標的最近軌跡點，看它讀到多少。
  簡化過的軌跡比原始 GPX 短 4–13%，所以要先用「頁面總里程 ÷ 簡化軌跡總長」求出校正
  倍率再比。`nanshijiao` 的青春嶺就是這樣抓出來的：頁面寫 8.91 km，軌跡上只有一次
  通過、讀數 7.85 km，差了整整一公里。

**座標要與里程同源。** 已完成行程的航點座標取自**軌跡在該時刻的位置**，不要另外從地圖
抓一個「這座山應該在哪」的點。兩者不同源時，段長就會與直線距離矛盾——而錯的往往是座標，
不是里程。

稽核方式是量每個航點到軌跡最近點的距離：正常在 15 m 以內，超過 40 m 就要查。
交通接駁的起訖點例外（公車站、停車場本來就不在步行軌跡上，`dinghu` 的陽明山立體停車場
離軌跡 1 km 是對的，因為那段搭小 9 路）。

`mochashan` 是這條規則的由來：**16 個航點座標全部偏離軌跡 124–526 m**，顯然不是從這份
GPX 產出的。症狀是下山第一段只有 570 m、短於當時兩點的 659 m 直線；我一度以為里程錯了
而去改里程，拿到原始 GPX 後才發現**里程一直是對的**（13:48 讀數就是 8.48 km），錯的是
座標。改以時刻回查 GPX 位置重設 16 個座標後，全部落在軌跡上、每段也都不再短於直線。

教訓：**段長短於直線只說明「座標與里程不一致」，沒說是哪一個錯。** 先看座標離軌跡多遠，
偏離大的那個才是嫌疑犯。

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

天氣請求一律走 `assets/detail.js` 的 `fetchWeather()`，各頁只在 `weather` 設定裡給
經緯度與文案。目前取回氣溫、體感溫度與降雨機率。

**必須帶 `elevation`。** 只給經緯度時 Open-Meteo 會用它自己地形網格的高度，
山區常常差很多——先前 `qixingshan` 的副標手寫「山頂較低 10–15°C」就是在補償這件事。
模組預設取 `schedule` 的最高點，那是最冷、風最大的地方，對行前判斷是保守的一側。

**附加欄位仍要逐項確認再顯示。** 實測 16 天視窗內體感與降雨機率都有值，
但欄位若因模型或參數組合而缺席，寧可整項不出現，也不要讓 null 變成畫面上的 NaN。

天氣代碼一律用 `assets/site.js` 的 `PaPaWeather.text(code)`，**不要在頁面裡自己寫對照表**。
Open-Meteo 回傳的 WMO 代碼有 28 種，先前五個頁面各寫一份、每份只涵蓋 10–17 種，
結果使用者看到「天氣代碼96」這種原始值（96 是雷雨伴冰雹）。
查不到時據實顯示未知，不要猜一個天氣填上去。

`assets/site.js` **不可加 `defer`**：各頁在 `await` 網路回應之後才查表，
但回應夠快時（快取命中）續行會搶在 defer 腳本之前執行，`PaPaWeather` 尚未定義。

必要函式：`initMap()`、`initChart()`、`renderTimeline()`、`updateWaypointCard(i)`、
`prevWaypoint()`、`nextWaypoint()`、`openNavigation()`。
已完成的行程頁另有 `fetchWeather()` 與 `markTripPast()` 的取捨——
行前頁必須有天氣預報，紀錄頁改為顯示當日實測天氣，此時兩者皆可省略。

**實走軌跡（僅已完成行程）。** 有 GPS 紀錄的行程，地圖畫實際軌跡而不是航點連成
的直線——那條線會繞過航點之間看不出來的髮夾彎。軌跡放在
`assets/tracks/<page>-<YYYY-MM-DD>.js`，掛在 `window.PaPaTracks[key]` 上，頁面以
`map.track.points` 傳給 `PaPaDetail`；沒給 `points` 就沿用航點直線，計畫與候選頁不受影響。

原始 GPX 動輒上千點、兩百多 KB，先用 Douglas–Peucker 簡化，容許偏差 5 公尺——
在整條路線塞滿地圖的縮放級別下約等於一個像素。只存經緯度，高度不放進來（見上方 `ele`）。


### 色彩規格

每頁有自己的主色（碧山粉、七星藍、火炎山橘），**這是刻意的辨識設計，要保留**。
需要一致的是使用方式：

- 灰階一律用 **stone**，不用 slate。**這條要連十六進位值一起查**，不能只 grep class
  名稱——`shiqiulinling` 的 slate 全藏在 `:root` 的 `--page-bg: #f8fafc`、
  `--page-fg: #334155`、`--timeline-bg: #e2e8f0` 裡，class 一個都沒用到，
  按 class 檢查會通過，但整頁看起來是冷灰的，跟其餘 13 頁的暖米色調對不上。
  對照表：`#f8fafc`→`#f8f7f4`、`#334155`→`#44403c`、`#e2e8f0`→`#e7e5e4`、
  `#f1f5f9`→`#f5f5f4`、`#64748b`→`#78716c`
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

22 頁已全數符合本規格的結構部分（2026-08-02 起新增的 `hushan`、`nangangshan`、
`datongshan`、`shanying`，以及 2026-08-03/04 補建的 `jiantanshan`、`jinmianshan`、
`caolingguidao`、`henglingguidao`、`zhongzhengshan`、`daluntouweishan`、`daqitou`、`eweishan` 是照本規格從零建起、而非事後收斂的）。以瀏覽器
實測逐項確認（2026-08-04 重跑）：

| 項目 | 狀態 |
|---|---|
**這張表由 `tools/spec_sweep.py` 產生，不是人工勾的。** 在專案根目錄跑 `python3 tools/spec_sweep.py`，全過會回傳 0。 標 🤖 的項目每次改完 `schedule` 或
版面都該重跑；標 👁 的仍靠人眼或瀏覽器實測。2026-08-04 的雙軸審查發現這張表先前有
兩項掛著 ✅ 卻不成立（導覽鍵文字、主色 token），原因就是規格寫了卻沒有人檢查——
**規格表寫了卻沒有檢查，等於沒寫**，這是加上掃描腳本的由來。

| 項目 | 檢查方式 | 狀態 |
|---|:--:|---|
| 段落 id 與順序 | 🤖 | ✅ 22/22 為 `overview` → `map-section` → `elevation` → `spots` → `timeline` |
| 導覽鍵（五顆、規格文字） | 🤖 | ✅ 22/22（2026-08-04 收斂：先前 7 頁用規格外的「實走紀錄」、5 頁用「實際行程」，已統一為「實走紀錄」並同步改規格表）|
| `<h2>` 主詞符合規格表 | 🤖 | ✅ 22/22（2026-08-04 收斂：`map-section` 5 頁、`elevation` 5 頁、`timeline` 2 頁曾各自命名）|
| 航點卡欄位 id | 🤖 | ✅ 22/22（含 `wp-pos-label`、`wp-time`、`wp-advice`）|
| canvas id 為 `elevation-chart` | 🤖 | ✅ 22/22 |
| 灰階用 stone | 🤖 | ✅ 22/22 — **class 名稱與十六進位值都查過**，且先剝掉註解再查 |
| 總覽有總里程 | 🤖 | ✅ 22/22（2026-08-04：`bishan` 標「徒步長度」不符規格，已改「總里程 km（估）」）|
| 站徽帶 `aria-label` | 🤖 | ✅ 22/22 |
| 無左上 `fixed` 返回鍵 | 🤖 | ✅ 22/22 |
| 每個航點都有 `advice` | 🤖 | ✅ 22/22，共 221 個航點 |
| 里程健全性（≥ 直線、單調） | 🤖 | ✅ 22/22，0 筆 |
| 最高點語意色為 `#7c9e52` | 🤖 | ✅ 22/22（2026-08-04 收斂：5 頁曾各自用琥珀／深綠／橘／紅，且都在註解裡自稱「語意色」）|
| 導覽列 `fixed` | 👁 | ✅ 22/22 |
| `<footer>` 在 `<main>` 外 | 👁 | ✅ 22/22 |
| 地圖單欄堆疊 | 👁 | ✅ 22/22 |
| 無 `scrollToSection()` | 👁 | ✅ 22/22 |
| 站徽（綠圓 + 爬爬小隊） | 👁 | ✅ 22/22 |
| 段落 `scroll-margin-top` | 👁 | ✅ 集中於 `detail.css` |
| 主色收成 `--accent` token | 👁 | ✅ 22/22 導航鍵與段落色條（2026-08-04 收斂：7 頁的導航鍵、6 頁的段落色條曾寫死 `bg-blue-600`／`bg-indigo-600` 等）。深色專題面板與語意色仍在例外之列，見「尚未收斂的一件事」|
| 小字對比 ≥ 4.5:1 | 👁 | ✅ 22/22（含 index）0 筆失敗。已知量測假陽性：skip link（聚焦前在畫面外）、index 的「詳情待補充」徽章、以及字佔滿整格的大標題（量到的底色會等於字色本身）|

**回首頁的唯一入口是導覽列的站徽**（帶 `aria-label="爬爬小隊首頁"`）。
左上那顆 `fixed` 返回鍵已於 2026-08-03 全數移除（當時 15 頁）——它一直被導覽列蓋住，
是死 markup，原委見下方。此後新建的頁面一律不加。

### 內容寬度

一般段落 `max-w-4xl`、時間軸 `max-w-2xl`。兩種模板世代的達成方式不同但值相同：
正規頁那一系是各段自帶容器，家族 A 出身的 6 頁是 `<main class="max-w-4xl">`。

時間軸再窄一階不是隨意——它是一長串短敘述堆疊，行長越短越好掃。

**行長仍未齊。** 容器寬度統一了，但實際文字寬度還受內距與字級影響：
家族 A 的段落是圓角卡片，卡片自己有 `p-6 md:p-10`，文字實寬約 752px；
正規頁那一系是滿版色帶配內層容器，文字實寬 896px。
以最長正文行計，家族 A 現在是 52–54 字、正規頁那一系是 64–75 字。
中文一般認為 25–40 字好讀，兩邊都仍偏長，正規頁那一系更長。
要再收，該調的是字級與內距，不是容器寬度。

### 尚未收斂的一件事

**內容缺口**（不是結構問題，需要實地資料才能補）

目前**沒有內容缺口**。`advice` 全部 22 頁、每個航點都有（定義見下）。

**里程、時間、海拔不得編造。** 這三個是量測值，缺就留空，不要挑一個看起來合理的數字
填進去；座標對不上時同樣如實留著疑點，等走過的人確認。`nanshijiao` 的國旗嶺就是這樣
處理的——軌跡顯示它與外南勢角山是同一個山頭，先標為待查證，隊友確認後才合併兩列。

**`advice` 不在此列。** 它不是「隊友當天說了什麼」的紀錄，而是**下次走這條路的人用得上
的提示**：往哪走、這裡有什麼、要小心什麼。可以依路線資料與公開資訊撰寫，不必等實走。
（早期版本把它當成實走口述，因此有四頁一直空著；2026-08-03 澄清定義並補齊。）

判準是**這句話有沒有告訴讀者他原本不知道的事**：

| ✅ 值得寫 | ❌ 沒有資訊量 |
|---|---|
| 廟方允許登山客借用洗手間，一線天入口在寺廟右後方 | 注意安全 |
| 三角點在民航局管制區內不開放，以大縱走木樁打卡 | 補充水分 |
| 此段岔路多，必要時核對離線地圖 | 穩定呼吸節奏 |
| 隧道週一公休，排行程務必避開 | 快到終點了 |

同一頁的 `advice` 長度要一致。現行慣例約 25–50 字，一到兩句。

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
- [ ] 灰階用 stone 不用 slate（class **與** `:root` 的十六進位值都要查）
- [ ] `#overview` 有統計數字排，含**總里程**、耗時、爬升、最高海拔
- [ ] **每段 `dist` 增量 ≥ 該段兩航點的直線距離**（見下方「里程健全性」）

功能面：

- [ ] 標題正確（瀏覽器標籤頁）
- [ ] 圖片正常載入
- [ ] 地圖顯示正確座標
- [ ] 海拔圖表繪製完整
- [ ] 上/下一個航點鍵可切換，地圖標記同步
- [ ] 導覽列站徽可回首頁，且帶 `aria-label="爬爬小隊首頁"`（沒有左上返回鍵，不要加）
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

**最後更新**：2026-08-04（新增 `zhongzhengshan`、`daluntouweishan`、`daqitou`、`eweishan`，22 頁結構已全數收斂；導覽文字、`<h2>` 主詞與最高點語意色收斂，並加上 `tools/spec_sweep.py` 讓這張收斂表可被機器複驗）  
如有疑問，參考 CONTRIBUTING.md 提出 issue。
