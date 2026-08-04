#!/usr/bin/env bash
# 重建 tools/contrast/tw.css —— 對比度量測用的 Tailwind。
#
# 為什麼需要這支：站上是靠 cdn.tailwindcss.com 即時產生 utility 的，但量測環境連不到
# CDN（網路政策），所以改用本地建置的 CSS。Tailwind 是掃 HTML 才知道要產生哪些 class，
# 因此**新頁面或新用到的 utility 沒重建就不存在**，量測會拿到一個缺樣式的假版面。
#
# 2026-08-04 就是這樣：tw.css 建於 caolingguidao / henglingguidao 兩頁誕生之前，
# 缺 from-blue-50 與 from-lime-50，那兩頁的 hero 漸層一直是在錯的底色上量的。
#
# check.js 會在每次量測前比對，缺 utility 就直接中止並要你跑這支——不會再無聲量錯。
#
# 掃描範圍含 assets/*.js：時間軸與航點卡的 class 是由 detail.js 在執行時產生的，
# 只掃 HTML 會漏掉它們。站上走 CDN 的 JIT 會觀察 DOM 變動所以沒事，本地建置不會。
#
# 用法：bash tools/contrast/build-css.sh
set -euo pipefail

cd "$(dirname "$0")/../.."
OUT="tools/contrast/tw.css"

# 站上用的是 Tailwind 3（cdn.tailwindcss.com 目前提供 v3），版本要跟著它走，
# 不然量測用的 utility 語意會與實際頁面不同。
npx --yes tailwindcss@3 \
  --input <(printf '@tailwind base;\n@tailwind components;\n@tailwind utilities;\n') \
  --content './*.html,./assets/*.js' \
  --minify \
  --output "$OUT"

echo "已重建 $OUT（$(wc -c < "$OUT") bytes）"
echo "接著跑：node tools/contrast/check.js --all"
