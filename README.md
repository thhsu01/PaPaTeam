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

所有行程資訊位在各 HTML 頁面的 `<script>` 標籤內 `data` 物件中。

**編輯計畫行程：** `index.html` → `data.planned` 陣列

**編輯候選清單：** `index.html` → `data.candidate` 陣列

**編輯歷史紀錄：** `index.html` → `data.completed` 陣列

**編輯山峰詳情：** 修改對應 HTML 檔案（如 `nanshijiao.html`）的 JavaScript 資料區塊

## 檔案結構

```
PaPaTeam/
├── index.html              # 主首頁（行程總覽）
├── nanshijiao.html         # 微笑山線 × 南勢角山 × 一線天
├── qixingshan.html         # 七星山主東峰
├── datunshan.html          # 大屯山連峰
├── bishan.html             # 碧山 + 白石湖山
├── shiqiulinling.html      # 獅球嶺砲台
├── dinghu.html             # 頂湖O型
├── laojiujianshan.html     # 老鷲尖山
├── mochashan.html          # 聖母步道（抹茶山）
├── meihuashan.html         # 梅花山
├── huoyianshan.html        # 火炎山
└── README.md               # 本檔案
```

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

**最後更新**: 2026-07-30  
**維護者**: @thhsu01
