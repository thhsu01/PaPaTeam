# ADR-0001：Chart.js 藏在接縫後面，各頁不直接設定它

- **狀態**：已採納
- **日期**：2026-08-04
- **相關**：`assets/detail.js` 的 `initChart()`、`CONTEXT.md`「海拔軸地板」

## 脈絡

`/improve-codebase-architecture` 量測後發現 `PaPaDetail.init` 是**淺介面**：
18 頁供 **1033 行設定**，才驅動 `assets/detail.js` 的 **329 行機制**——比例 **3.1×**。
模組要深是「介面小、實作大」，這裡反過來了。

各頁的 `chart:` 區塊都在寫 Chart.js 的設定樹（`scales`、`plugins.tooltip.callbacks`、
`dataset`），平均約 35 行。表面上看是「每頁客製自己的圖表」，但實際量下來：

- `fillAlpha`：16/18 頁是 0.1，其中 7 頁寫成 `0.10`、9 頁寫成 `0.1`——**同一個值的兩種寫法**
- `tooltip.callbacks`：7 頁逐字相同
- `chart.options` 骨架：7 頁相同，只差 `y.max` 一個數字
- `dataset` 線寬／點徑：12 頁是 2.5／5
- `onHover`（滑過圖表選取航點）：4 頁一字不差，另 14 頁沒有

也就是說，「客製」多半不是決定，是**抄來的差異**。

## 決策

**`assets/detail.js` 完整擁有 Chart.js。各頁只給領域旋鈕，不寫 Chart.js 設定。**

```javascript
chart: { elevationFloor: 450, lineColor: '--accent-deep', palette: PAL }
```

現行旋鈕：`elevationFloor`、`elevationMax`、`lineColor`、`fillColor`、`fillAlpha`、
`palette`，以及逃生口 `advanced`（深合併進最終設定）。

`tooltip`、`legend`、`onHover`、格線、x 軸旋轉角、航點短名規則全部收進機制。

## 後果

**好的**：換掉 Chart.js 只需改 `initChart()` 一個函式，不是 18 個檔案——這是本決策的
主要目的。18 頁的 `chart:` 從約 35 行縮成一行。`0.1` 與 `0.10` 這種「假差異」不可能再發生。

**代價**：想調 Chart.js 的細節要先在 `detail.js` 加旋鈕，比直接改頁面多一步。
這是刻意的摩擦——它逼人回答「這真的是這一頁的決定嗎」。

**逃生口的風險**：`advanced` 一旦被濫用，就退化成「各頁自己寫 Chart.js」，本決策等於失效。
目前 18 頁都沒用到它。**若哪天多數頁面都在傳 `advanced`，那是本 ADR 該被重開的訊號**，
不是該再加旋鈕的訊號。

## 為什麼記成 ADR

因為反方向的建議看起來很合理：「讓各頁能直接調 Chart.js 比較靈活」。
沒有這份紀錄，下一次架構檢視很可能就這樣建議，而量測結果會再被發現一次。

判準寫在這裡：**在提議把 Chart.js 設定放回各頁之前，先量一次各頁到底有多少是真差異。**
2026-08-04 量出來的答案是——真正因頁而異的只有兩個維度（海拔軸地板、線色深淺），
兩個都已經是旋鈕。
