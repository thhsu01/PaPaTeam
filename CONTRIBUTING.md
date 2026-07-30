# 貢獻指南

感謝你有興趣為爬爬小隊貢獻！本文檔說明如何參與改進這個專案。

## 參與方式

### 1. 回報問題（Issue）

發現 bug 或有改進建議？

1. 檢查是否已有相同的 [issue](../../issues)
2. 開新 issue，包含：
   - **標題** — 簡潔說明問題
   - **描述** — 具體情況、瀏覽器版本、重現步驟
   - **截圖** — 若適用
   - **期望行為** — 應該怎樣運作

### 2. 提交改進（Pull Request）

準備好動手了？

#### 開發流程

1. **Fork** 本倉庫到自己的 GitHub 帳號
2. **Clone** 到本機
```bash
git clone https://github.com/YOUR_USERNAME/PaPaTeam.git
cd PaPaTeam
```

3. **建立功能分支**
```bash
git checkout -b feature/你的功能名稱
# 例如：feature/add-guanyin-mountain
```

4. **進行更改**
   - 編輯 HTML / CSS / JavaScript
   - 測試新功能（見下方「測試」段落）
   - 確保在多個瀏覽器和裝置上正常運作

5. **提交變更**
```bash
git add .
git commit -m "簡潔描述改動內容"
# 例如：git commit -m "Add Guanyin Mountain route details"
```

6. **推送分支**
```bash
git push origin feature/你的功能名稱
```

7. **建立 Pull Request**
   - 標題簡潔
   - 描述包含：改動內容、測試情況、相關 issue 號

## 編輯清單

### 新增登山路線

1. 在 `index.html` 中找到 `data` 物件
2. 在 `candidate` 陣列新增物件：
```javascript
{
  title: "路線名稱",
  location: "地點",
  desc: "簡短描述（1-2句）",
  img: "https://images.unsplash.com/...",
  tag: "候選",
  url: "filename.html"
}
```

3. 若需詳情頁，複製現有 HTML 檔案（如 `nanshijiao.html`），修改：
   - 頁面標題（`<title>`）
   - 路線名稱、難度、距離等
   - 高度圖表資料（若有）
   - 地圖座標（Leaflet）
   - 路線描述與貼士

### 更新已完成行程

1. 在 `index.html` 的 `data.completed` 陣列找到該行程
2. 新增屬性或修改現有資訊：
```javascript
{
  title: "行程名稱",
  date: "YYYY/MM/DD",
  location: "地點",
  desc: "簡短敘述",
  img: "https://...",
  isLatest: false,
  url: "filename.html"  // 指向詳情頁，若無則為 "#"
}
```

### 修改樣式

- 顏色、間距、字型調整位在各 HTML 檔案的 `<style>` 段落
- 全域樣式（導覽列、卡片等）在 `index.html` 或各詳情頁的 `<style>` 中
- **不建議大幅重構設計** — 先開 issue 討論

## 測試

在提交前，務必在多個環境測試：

### 本機測試
```bash
# 啟動本機伺服器
python -m http.server 8000
# 訪問 http://localhost:8000
```

### 檢查項目

- [ ] 桌面裝置（Chrome、Firefox、Safari）
- [ ] 平板與手機（響應式設計）
- [ ] 圖片正常載入
- [ ] 地圖與圖表能正常顯示
- [ ] 連結正確（無 404 或無效連結）
- [ ] 中文字型正確顯示

### 效能檢查

使用瀏覽器開發者工具：
- Network — 檢查載入時間與資源大小
- Console — 確認無 JavaScript 錯誤

## 代碼風格

### HTML
- 使用 4 格縮排（或 2 格，保持一致）
- 語意化標籤（`<section>`, `<article>`, `<nav>` 等）
- 完整的 `<head>` 段落（meta、title、charset）

### CSS
- 優先用 Tailwind 類別
- 避免內聯 `style` 屬性（用 `<style>` 標籤）
- 使用有意義的顏色變數名稱

### JavaScript
- 簡單明確的變數名稱
- 避免複雜邏輯（本專案偏好簡單實作）
- 必要時加上單行註解

## 常見編輯情境

### 情境 1：修正已完成行程的連結

**位置** — `index.html` 第 144-167 行

**步驟**：
1. 在 `completed` 陣列找到該行程
2. 若有對應 HTML 檔案，修改 `url` 字段：
```javascript
// 修改前
{ title: "...", url: "#" }

// 修改後
{ title: "...", url: "yourfile.html" }
```

### 情境 2：更新計畫行程日期

**位置** — `index.html` 第 127-137 行

**步驟**：修改 `date` 字段，同時更新對應詳情頁內容

### 情境 3：新增圖片

建議使用 Unsplash、Pexels 等免費圖庫，確保版權清晰

```javascript
img: "https://images.unsplash.com/photo-XXXXXXXXXX?auto=format&fit=crop&q=80&w=800"
```

## PR 審查期望

提交 PR 後，維護者會檢查：
1. 代碼風格與一致性
2. 功能正常運作
3. 無 JavaScript 錯誤
4. 響應式設計完整
5. 提交訊息清晰

## 問題協助

卡住或有疑問？

- 檢查現有 [issue 和 discussion](../../issues)
- 在 PR 中提出具體問題
- 參考相鄰的 HTML 檔案學習結構

## 行為準則

- 尊重他人意見
- 提供建設性反饋
- 保持對話友善與專業

---

感謝你的貢獻！🏔️
