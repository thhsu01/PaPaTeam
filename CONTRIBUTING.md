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

> **動任何頁面前先讀 `ARCHITECTURE.md`。** 它是規範權威，規定了詳情頁只能有五個段落、
> id 與順序固定、色彩一律走 `--accent` token。片段速查見 `SNIPPETS.md`。

### 新增登山路線

1. 在 `index.html` 底部的 `data` 物件，於 `candidate` 陣列新增：
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

2. 若需詳情頁，**複製 `nanshijiao.html`**（不要複製其他頁），照
   `ARCHITECTURE.md` §建立新詳情頁 的步驟改。重點：
   - `<title>`、`<h1>`、`<meta name="description">`
   - 底部的 `schedule` 陣列（座標、時間、里程、海拔、`pos`、描述）
   - `:root` 的 `--accent` 那一段（換主色只改這裡）
   - `PaPaDetail.init()` 的 `nav`、`weather`、`map.setView`

   **不要自己寫地圖或圖表**——Leaflet 與 Chart.js 都在 `assets/detail.js` 裡，
   各頁只提供 `schedule` 與設定。

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
  isLatest: false,        // 只有最新那筆為 true
  url: "filename.html"    // 指向詳情頁，若無則為 "#"
}
```

行程編號（`#1`–`#21` 徽章）**不要寫進資料**，`renderUI()` 依日期推導；
補登舊行程時後面的編號會自動遞補。

### 里程與建議：缺就留空

`dist` 與 `advice` 是實走才知道的東西。**不得為了填滿欄位而編造**——
沒有 `advice` 時建議框會自動整塊收起來，不會留一個空框。
座標對不上時同樣如實留著疑點，等走過的人確認，不要挑一個看起來合理的數字改掉。

### 修改樣式

- 詳情頁共用樣式在 `assets/detail.css`，全站共用在 `assets/site.css`
- 各頁 `<style>` 只放該頁的 `:root` 變數與少數專屬規則
- **改顏色前必讀 `READABILITY_AUDIT.md`**，尤其小字：`text-stone-500` 只在白底安全，
  頁底 `#f5f3ef` 上只有 4.33:1，小字一律 `text-stone-600` 起跳
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
- [ ] 地圖與圖表能正常顯示
- [ ] 上／下一個航點鍵可切換，地圖標記同步
- [ ] 連結正確（無 404 或無效連結）
- [ ] 中文字型正確顯示

詳情頁另有一份規格檢查清單，見 `ARCHITECTURE.md` §快速檢查清單。

**若要量對比度**：本環境的網路政策擋掉 `cdn.tailwindcss.com`，必須 stub 掉 CDN 並
注入本地建置的 Tailwind，且**改完 HTML 要重建**。量之前先確認 `text-white` 的
computed color 真的是白的——不是就代表樣式沒生效，量到的會是一個沒有樣式的假版面。
細節與踩過的坑見 `READABILITY_AUDIT.md` §量測方法的三個坑。

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

> 以下不寫行號——行號會飄。用搜尋找 `data.completed`、`data.planned` 等關鍵字。

### 情境 1：修正已完成行程的連結

在 `index.html` 的 `data.completed` 陣列找到該行程，修改 `url`：
```javascript
// 修改前
{ title: "...", url: "#" }

// 修改後
{ title: "...", url: "yourfile.html" }
```

### 情境 2：更新計畫行程日期

改 `data.planned` 的 `date`，同時更新對應詳情頁的 `TRIP_DATE`。
**詳情頁的日期只在 `TRIP_DATE` 出現一次**，其餘都由它推導，不要另外寫死。

### 情境 3：把計畫行程歸檔為已完成

1. 把該筆從 `data.planned` 搬到 `data.completed`，補上 `date`（`YYYY/MM/DD`）
2. `isLatest: true` 移到這一筆，舊的那筆改成 `false`
3. 若有 GPS 紀錄，把簡化後的軌跡存成 `assets/tracks/<頁名>-<YYYY-MM-DD>.js`，
   詳情頁載入它並把 `map.track.points` 傳給 `PaPaDetail`
4. 依實走紀錄更新 `schedule` 的 `time` 與 `dist`；原本的預估時刻搬進 `plan` 欄位

### 情境 4：新增圖片

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
