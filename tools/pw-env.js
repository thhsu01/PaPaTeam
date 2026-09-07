// 兩支 Playwright 工具（contrast/check.js、regress/check.js）共用的環境：伺服器位址、
// Chromium 位置、要擋掉的外部網址。2026-09 的審查抓到這三樣在兩支各抄一份，
// 而且已經漂了——一份多擋 open-meteo 與地圖磚，另一份還留著沒人用的 Gemini 網址。
const fs = require('fs');

module.exports = {
  // 本機 python3 -m http.server 8099；CI 同一個埠
  BASE: process.env.PAPA_BASE || 'http://127.0.0.1:8099',

  // 本機沙箱的 Chromium 在 /opt/pw-browsers；CI 用 npx playwright install 裝的那份。
  // 路徑不存在就不指定 executablePath，讓 Playwright 用自己的——先前寫死本機路徑，
  // CI 上會找不到執行檔（該 workflow 當時只掛 PR，所以沒被觸發過）。
  LAUNCH: (() => {
    const def = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
    const chrome = process.env.PW_CHROME || (fs.existsSync(def) ? def : null);
    return chrome ? { executablePath: chrome } : {};
  })(),

  // 頁面會去拿的外部資源，量測時一律以空回應擋掉：量的是自己的 HTML／CSS／JS，
  // 不是 CDN 有沒有通。Leaflet 與 Chart.js 由 contrast/stubs.js 補樁。
  CDN: ['**://cdn.tailwindcss.com/**', '**://cdn.jsdelivr.net/**', '**://unpkg.com/**',
        '**://fonts.googleapis.com/**', '**://api.open-meteo.com/**',
        '**://images.unsplash.com/**', '**://*.tile.openstreetmap.org/**'],
};
