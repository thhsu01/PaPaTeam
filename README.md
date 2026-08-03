# 爬爬小隊 🏔️

探索台灣山林的登山隊伍網頁平台。紀錄每一次的山中冒險，分享路線攻略與群體回憶。

**線上網站**: [爬爬小隊官網](https://thhsu01.github.io/PaPaTeam/)

## 特色

- 📍 **計畫行程** — 即將出發的登山路線
- 📋 **候選清單** — 待探索的山峰與古道
- 🏅 **歷史紀錄** — 已完成登山的紀念冊

## 快速開始

### 檢視網站

1. Clone 本倉庫
```bash
git clone https://github.com/thhsu01/PaPaTeam.git
cd PaPaTeam
```

2. 用瀏覽器開啟 `index.html`
```bash
# macOS / Linux
open index.html

# Windows
start index.html
```

或用本機伺服器（推薦）
```bash
# Python 3
python -m http.server 8000

# Node.js (npx)
npx http-server
```

然後訪問 `http://localhost:8000`

### 編輯內容

首頁的行程清單放在 `index.html` 的 `data` 物件；各詳情頁的航點資料則在該頁底部的
`schedule` 陣列。兩者都在頁面自己的 `<script>` 標籤內，沒有資料庫。

**編輯計畫行程：** `index.html` → `data.planned` 陣列

**編輯候選清單：** `index.html` → `data.candidate` 陣列

**編輯歷史紀錄：** `index.html` → `data.completed` 陣列

**編輯山峰詳情：** 修改對應 HTML 檔案（如 `nanshijiao.html`）底部的 `schedule` 陣列。
詳情頁用的是 `schedule`，不是首頁的 `data` 物件；地圖、圖表、時間軸都由它推導。

**加入實走軌跡：** 已完成的行程若有 GPS 紀錄，把簡化後的座標陣列存成
`assets/tracks/<頁名>-<YYYY-MM-DD>.js`，頁面載入它並把 `map.track.points`
傳給 `PaPaDetail`，地圖就改畫實際軌跡而非航點直線。

## 檔案結構

```
PaPaTeam/
├── index.html                  # 主首頁：計畫／候選／歷史三區
│
│   已完成（九頁附實走 GPS 軌跡）
├── nanshijiao.html             # 微笑山線 × 南勢角山 × 一線天（2026-08-02）
├── dinghu.html                 # 猴崁水圳 × 青楓步道 × 頂湖O型（2026-06-20）
├── laojiujianshan.html         # 內溝山系 O 型全系列縱走（2026-05-01）
├── mochashan.html              # 聖母步道：抹茶山（2026-03-14）
├── meihuashan.html             # 梅花山全系列挑戰縱走（2026-01-10）
├── huoyianshan.html            # 火炎山、北鞍古道 O 走（2025-12-13）
├── jiantanshan.html            # 劍潭山親山步道 × 老地方觀機平台（2024-08-04）
├── nangangshan.html            # 南港山 + 九五峰 + 象山縱走（2024-06-30）
├── hushan.html                 # 虎山親山步道（2024-04-20）
│   候選
├── qixingshan.html             # 七星山主東峰 苗圃O型
├── datunshan.html              # 大屯山連峰四峰 O 型縱走
├── bishan.html                 # 碧山 + 白石湖山
├── shiqiulinling.html          # 獅球嶺砲台
├── datongshan.html             # 大同山 × 青龍嶺 × 大棟山縱走
├── shanying.html               # 山佳鶯歌縱走：石灰坑山 × 望湖山 × 鶯歌石
│
├── assets/
│   ├── site.css                # 全站共用樣式：skip link、鍵盤焦點、reduced-motion
│   ├── site.js                 # 全站共用腳本：天氣代碼對照表（PaPaWeather）
│   ├── detail.css              # 十五個詳情頁共用樣式：圖表、地圖、航點卡、時間軸
│   ├── detail.js               # 十五個詳情頁共用腳本：Leaflet、Chart.js、天氣、時間軸
│   └── tracks/                 # 已完成行程的實走 GPS 軌跡（簡化後的座標陣列）
│       ├── nanshijiao-2026-08-02.js
│       ├── dinghu-2026-06-20.js
│       ├── laojiujianshan-2026-05-01.js
│       ├── mochashan-2026-03-14.js
│       ├── meihuashan-2026-01-10.js
│       ├── huoyianshan-2025-12-13.js
│       ├── jiantanshan-2024-08-04.js
│       ├── nangangshan-2024-06-30.js
│       └── hushan-2024-04-20.js
│
├── manifest.json               # 專案入口索引：各檔案的意義、慣例、待辦
├── integrity.json              # 檔案清單與 blob SHA（由 GitHub Action 自動產生，勿手改）
├── .github/workflows/
│   └── integrity.yml           # push 到 main 後重算 integrity.json
│
├── .gitignore                  # 編輯器、系統檔、node_modules
│
├── ARCHITECTURE.md             # 架構指南（規範權威）：段落規格、色彩 token、腳本規格
├── READABILITY_AUDIT.md        # 可讀性與對比度審計紀錄（改顏色前必讀）
├── SNIPPETS.md                 # 元件片段快速參考
├── CONTRIBUTING.md             # 貢獻指南：編輯清單與代碼風格
└── README.md                   # 本檔案
```

十五個詳情頁不各自實作地圖與圖表——那些機制都在 `assets/detail.js`，各頁只寫自己的
`schedule` 陣列與 `PaPaDetail.init({...})` 設定。**動任何頁面前先讀 `ARCHITECTURE.md`**，
它規定了詳情頁只能有五個段落、id 與順序固定，以及色彩一律走 `--accent` token。

## 技術棧

- **HTML5** — 語意化標記
- **Tailwind CSS** — 整體樣式（CDN）
- **JavaScript** — 輕量級互動邏輯
- **Chart.js** — 高度與難度圖表
- **Leaflet** — 登山路線地圖

所有資源均通過 CDN 載入，無需本機構建或編譯步驟。

## 貢獻

歡迎協助改進！詳見 [CONTRIBUTING.md](CONTRIBUTING.md)

## 常見問題

**Q: 如何新增一條新的登山路線？**

A: 
1. 在 `index.html` 中的 `data.candidate` 或 `data.planned` 陣列新增物件
2. 按需建立對應的 HTML 詳情頁（參考現有 HTML 結構）
3. 在 index.html 卡片中設定 `url` 指向新頁面

**Q: 圖片和地圖無法載入？**

A: 檢查網路連接。本站依賴 Unsplash、CDN 等外部資源。如需離線版本，可將圖片和資源本地化（見 CONTRIBUTING.md）。

**Q: 如何自動部署更新？**

A: 本倉庫已設定 GitHub Pages 自動部署。Push 到 main 分支後，網站會自動更新。

## 授權

© 2026 爬爬小隊 PaPaTeam. 版權所有。

---

**最後更新**: 2026-08-03  
**維護者**: @thhsu01
