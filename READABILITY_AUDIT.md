# 可讀性與對比度審計

**日期**：2026-07-30
**標準**：WCAG 2.1 AA（一般文字 4.5:1、大文字 ≥18.66px 粗體或 ≥24px 為 3:1）

> **修訂說明**：本文件第一版的對比度數字是憑印象填寫的，其中兩項（`#7c9e52`、`#059669`）錯誤地標記為「通過 AA」。本版所有數值均以 WCAG 2.1 相對亮度公式實際計算，計算腳本見文末。

---

## 1. 對比度實測

### 內文色（白底）— 全部通過

| 類別 | Hex | 對比度 | AA |
|---|---|---|---|
| `text-slate-900` | `#0f172a` | 17.85:1 | ✅ |
| `text-stone-800` | `#292524` | 15.17:1 | ✅ |
| `text-slate-800` | `#1e293b` | 14.63:1 | ✅ |
| `text-stone-600` | `#57534e` | 7.63:1 | ✅ |

### 小字標籤色 × 各頁實際背景

詳情頁背景不是白色，而是米色系，因此需按各頁背景分別計算。

| 背景 | 使用頁面 | `stone-500` | `stone-600` |
|---|---|---|---|
| `#ffffff` | index 卡片 | 4.80:1 ✅ | 7.63:1 ✅ |
| `#fefaf6` | huoyianshan | 4.62:1 ✅ | 7.35:1 ✅ |
| `#fcfaf7` | bishan | 4.60:1 ✅ | 7.32:1 ✅ |
| `#f8fafc` | shiqiulinling | 4.59:1 ✅ | 7.29:1 ✅ |
| `#f8f7f4` | datunshan / dinghu / qixingshan / laojiujianshan / meihuashan / mochashan | **4.48:1 ❌** | 7.12:1 ✅ |
| `#f5f3ef` | nanshijiao | **4.33:1 ❌** | 6.88:1 ✅ |
| `#e7e5e4` | 部分卡片區塊 | **3.82:1 ❌** | 6.08:1 ✅ |

**已修正**：`text-stone-500` 在 7 種背景中有 3 種未達 4.5:1（影響 8 個檔案的 `text-xs` 小字標籤 —— 12px 屬一般文字，不適用 3:1 放寬）。已將 9 個 stone 家族詳情頁共 255 處全部改為 `text-stone-600`，所有背景現達 6.08:1 以上。

`text-slate-500`（index.html 6 處 4.67:1、shiqiulinling.html 18 處 4.55:1）**兩者均已通過**，故未改動 —— 避免無無障礙理由的視覺變更。

> 沿革：原先使用 `text-stone-400`（白底僅 2.52:1，明確不合格），commit `80ecb77` 改為 `stone-500` 方向正確但幅度不足（未考慮詳情頁是米色底而非白底），本次補足。

### 品牌色（白底）— 均未達一般文字標準

| 顏色 | Hex | 對比度 | 一般文字 4.5:1 | 大文字 3:1 |
|---|---|---|---|---|
| 翠綠 | `#059669` | 3.77:1 | ❌ | ✅ |
| 棕橙 | `#c77c3e` | 3.29:1 | ❌ | ✅ |
| 草綠 | `#7c9e52` | 3.06:1 | ❌ | ✅ |

**這三色僅可用於大標題或非文字元素**（色塊、圖表線條、邊框）。目前用於小字時不合格，例如 `.stamp`（`font-size: 11px`，`#c77c3e` 前景）。

**作為按鈕背景時同樣不合格**：對比度公式對稱，前後景互換不改變比值，因此白字配 `#c77c3e` 底仍是 3.29:1、白字配 `#7c9e52` 底仍是 3.06:1。導航按鈕（`text-sm`，14px）屬一般文字，未達 4.5:1。

---

## 2. 字級

| 用途 | 類別 | px | 評估 |
|---|---|---|---|
| 標題 | `text-2xl`–`text-6xl` | 24–60 | 階層清晰 |
| 卡片標題 | `text-xl`–`text-2xl` | 20–24 | 合適 |
| 內文 | `text-base` | 16 | 合適 |
| 小字標籤 | `text-xs` | 12 | 大量使用；因屬一般文字，對比度須 4.5:1（見上表） |

---

## 3. 已完成的無障礙改動

- `<img>` 的 `alt`：index.html 3 個圖片全部補齊。**其餘 10 個詳情頁沒有 `<img>` 標籤**，無需處理（先前版本誤稱涵蓋 11 個檔案）。
- 返回鍵、導覽鍵、航點前後鍵、地圖導航鍵：補 `aria-label`。
- `<nav>`：補 `aria-label`。
- 圖表與地圖容器：補 `role="region"` + `aria-label`。
- 觸控目標放大至 44×44px。
- **skip link**：11 頁均加入「跳至主要內容」，預設移出畫面、鍵盤聚焦時滑入；`<main>` 補 `id="main-content"` 作為跳轉目標。
- **鍵盤焦點指示**：新增 `:focus-visible` 雙環樣式（深色 outline + 白色 halo），同時涵蓋淺色頁面與 index.html 的深色頁腳。此前 Tailwind preflight 移除了預設 outline 而全站無替代樣式。
- **減少動態**：`@media (prefers-reduced-motion: reduce)` 關閉轉場與動畫；因 `scrollIntoView({behavior:'smooth'})` 依規範會覆蓋 CSS，另以 `assets/site.js` 在該偏好啟用時改寫為 `auto`。

### 共用檔的取捨

新增 `assets/site.css` 與 `assets/site.js`，但**只收上述三項全新規則**，未收各頁既有 CSS。原因是這些頁面實為兩套模板世代，class 詞彙與數值本就不一致：

- 6 個檔案用 `.nav-link` / `.info-glass` / `.card-hover` / `#realMap`
- 4 個檔案用 `.nav-btn` / `#map` / `#elevation-chart` / `.waypoint-card`
- 連唯一三個共通選擇器的值也不同（`.timeline-line` 有 `left:20px` vs `24px`、漸層 vs 純色；`.chart-container` 有 `max-width:800px` vs `100%`）

因此「抽出共用 CSS」實質上是**統一各頁現有差異**，會改動多頁視覺呈現，須另案評估。本次只加入原本一條都不存在的規則，確保不影響既有外觀。

### 已撤回的錯誤改動

| 改動 | 撤回原因 |
|---|---|
| `role="article"` 加在 `<a href>` | ARIA role 覆蓋原生語意，螢幕閱讀器不再將卡片播報為連結 |
| `role="navigation"` 加在 `<nav>` 內的 div | 巢狀 landmark，重複播報 |
| `min-width: 500px` 於圖表 canvas | Chart.js 本已自適應；反而在手機產生多餘橫向滾動 |
| `bindPopup(..., {'aria-label': ...})` | 非 Leaflet 選項，會被忽略 |
| `querySelector('button:has-text(...)')` | `:has-text()` 是 Playwright 語法非 CSS，每次點擊拋 SyntaxError |

---

## 4. 尚未處理的缺口

1. **品牌色用於小字仍不合格** —— `.stamp`（`font-size: 11px`，前景 `#c77c3e`）為 3.29:1；導航按鈕白字配 `#c77c3e` 底（`text-sm`，14px）同為 3.29:1。須加深色值或放大字級至大文字門檻。未一併處理是因為調整品牌色會影響全站視覺識別，屬設計決策。
2. **各頁 CSS 統一** —— 見上節「共用檔的取捨」。屬較大重構，會改動多頁視覺。
3. **天氣 API 日期寫死** —— `nanshijiao.html` 的 `start_date=2026-08-02`，過期後將永久顯示舊資料。

---

## 5. 未執行的驗證

以下項目本次**未實際執行**，不應視為已通過：

- Lighthouse 無障礙評分
- 螢幕閱讀器（NVDA / VoiceOver）實測
- 實機測試（本環境無瀏覽器可驅動）
- 超小螢幕（280–375px）實際渲染

---

## 附錄：對比度計算腳本

```python
def lum(h):
    r, g, b = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def ratio(fg, bg):
    a, b = lum(fg), lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)

print(ratio('78716c', 'f5f3ef'))   # stone-500 on nanshijiao bg -> 4.33
```

參考：[WCAG 2.1 相對亮度定義](https://www.w3.org/TR/WCAG21/#dfn-relative-luminance)
