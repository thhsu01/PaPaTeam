// detail.js 的執行期基準。用法：
//     node tools/regress/check.js               比對全站
//     node tools/regress/check.js hushan bishan  只比對這幾頁
//     node tools/regress/check.js --update       重寫 baseline.json
// 需要本機在 8099 埠提供靜態檔：python3 -m http.server 8099
//
// 為什麼要有這支：detail.js 是 22 頁共用的機制，介面只有 init(cfg)。改它的時候
// 沒有辦法「看一眼」就知道 22 頁有沒有變——2026-08 那輪重構靠的是三支臨時腳本，
// 每次改完把時間軸 DOM、地圖標記樣式、海拔圖設定逐欄比對，要求未改動的頁零變動。
// 那三支住在工作階段的暫存目錄，事後就不見了。這支是它們收進倉庫的版本。
//
// 量的是介面另一側的結果，不是實作：
//   timeline  #timeline-container 裡每個航點的 class、圓點的 inline style、文字與 HTML
//   markers   detail.js 交給 L.circleMarker 的樣式物件、popup、選取時的 setStyle
//   polyline  交給 L.polyline 的軌跡：點數、頭尾兩點、樣式
//   chart     detail.js 交給 new Chart() 的設定（函式除外）
//   card      逐一切換航點後，航點卡七個欄位的文字
//   trip      行程事實槽 [data-trip] 填進去的文字
// 所以測試只穿過 init(cfg)，跟頁面一樣。想測到介面「後面」去，多半是模組形狀不對。
//
// 基準是刻意的決定，不是快照的副產品：只有 --update 會寫，寫完 `git diff
// tools/regress/baseline.json` 就是審查面——改了什麼、改到哪幾頁，一眼看得到。

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const BASE = process.env.PAPA_BASE || 'http://127.0.0.1:8099';
const CHROME = process.env.PW_CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const BASELINE = path.join(__dirname, 'baseline.json');
const CDN = ['**://cdn.tailwindcss.com/**', '**://cdn.jsdelivr.net/**', '**://unpkg.com/**',
             '**://fonts.googleapis.com/**', '**://api.open-meteo.com/**',
             '**://generativelanguage.googleapis.com/**', '**://images.unsplash.com/**',
             '**://*.tile.openstreetmap.org/**'];

async function capture(browser, name) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const p = await ctx.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(String(e.message || e)));
  await p.addInitScript({ path: path.join(ROOT, 'tools/contrast/stubs.js') });
  await p.addInitScript({ path: path.join(__dirname, 'record.js') });
  for (const u of CDN) await p.route(u, r => r.fulfill({ body: '{}', contentType: 'application/javascript' }));
  await p.goto(`${BASE}/${name}.html`, { waitUntil: 'load' });
  await p.waitForTimeout(300);   // DOMContentLoaded 的 initMap/initChart/renderTimeline 已跑完

  const state = await p.evaluate(() => {
    const $ = id => document.getElementById(id);
    const text = id => ($(id) ? $(id).textContent.trim().replace(/\s+/g, ' ') : null);

    // 容器裡有一根靜態的 .timeline-line，不是航點，跳過
    const items = () => [...document.querySelectorAll('#timeline-container > div')]
      .filter(el => !el.classList.contains('timeline-line'));
    const timeline = items().map(el => {
      const dot = el.querySelector('[style*="background"]');
      return { cls: el.className,
               dot: dot ? { cls: dot.className, style: dot.getAttribute('style') } : null,
               text: el.textContent.trim().replace(/\s+/g, ' '),
               html: el.innerHTML.replace(/\s+/g, ' ').trim() };
    });

    // 逐一切換航點：航點卡的欄位、以及每個標記在「被選取／未選取」時拿到的樣式
    const n = (window.PaPaDetail && window.PaPaDetail.markers.length) || 0;
    const card = [];
    const total = n || items().length;
    for (let i = 0; i < total; i++) {
      if (typeof window.updateWaypointCard === 'function') window.updateWaypointCard(i);
      card.push(['wp-pos-label', 'wp-title', 'wp-time', 'wp-dist', 'wp-ele', 'wp-desc', 'wp-advice']
        .reduce((o, id) => { o[id] = text(id); return o; }, {}));
    }
    if (typeof window.updateWaypointCard === 'function' && total) window.updateWaypointCard(0);

    // 行程事實槽：detail.js 依 trip 填進 [data-trip] 的文字
    const trip = [...document.querySelectorAll('[data-trip]')]
      .map(el => ({ slot: el.getAttribute('data-trip'), text: el.textContent.trim() }));

    return { timeline: timeline, markers: window.__rec.markers, polyline: window.__rec.polyline,
             chart: window.__rec.chart, card: card, trip: trip };
  });
  await ctx.close();
  state.errors = errors;
  return state;
}

/** 深比對，回傳 [ '路徑: 前 → 後' ]。 */
function diff(a, b, p, out) {
  if (JSON.stringify(a) === JSON.stringify(b)) return out;
  const isObj = v => v && typeof v === 'object';
  if (isObj(a) && isObj(b)) {
    for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) diff(a[k], b[k], p + (Array.isArray(a) ? `[${k}]` : `.${k}`), out);
  } else {
    // 長字串（timeline 的 html）從第一個不同的字附近摘，不然兩邊印出來的開頭都一樣
    let sa = a === undefined ? '（無）' : JSON.stringify(a);
    let sb = b === undefined ? '（無）' : JSON.stringify(b);
    if (sa.length > 80 || sb.length > 80) {
      let i = 0;
      while (i < sa.length && i < sb.length && sa[i] === sb[i]) i++;
      const from = Math.max(0, i - 20);
      sa = (from ? '…' : '') + sa.slice(from, from + 70);
      sb = (from ? '…' : '') + sb.slice(from, from + 70);
    }
    out.push(`${p}: ${sa} → ${sb}`);
  }
  return out;
}

(async () => {
  const args = process.argv.slice(2);
  const update = args.includes('--update');
  let names = args.filter(a => !a.startsWith('--'));
  if (!names.length) {
    names = fs.readdirSync(ROOT).filter(f => f.endsWith('.html') && f !== 'index.html').map(f => f.slice(0, -5)).sort();
  }
  const base = fs.existsSync(BASELINE) ? JSON.parse(fs.readFileSync(BASELINE, 'utf8')) : {};
  const browser = await chromium.launch({ executablePath: CHROME });
  let bad = 0;
  const next = Object.assign({}, base);
  for (const n of names) {
    const s = await capture(browser, n);
    next[n] = s;
    const errs = s.errors.length ? `  ⚠ JS 錯誤：${s.errors.join(' | ')}` : '';
    if (update) {
      console.log(`${n.padEnd(16)} 已記錄  ${s.timeline.length} 航點 ${s.markers.length} 標記${errs}`);
      continue;
    }
    if (!base[n]) { console.log(`${n.padEnd(16)} ✗ 基準裡沒有這頁——跑 --update 收進去${errs}`); bad++; continue; }
    const d = diff(base[n], s, n, []);
    if (d.length || s.errors.length) {
      bad++;
      console.log(`${n.padEnd(16)} ✗ ${d.length} 處變動${errs}`);
      d.slice(0, 12).forEach(x => console.log('   ' + x));
      if (d.length > 12) console.log(`   … 另 ${d.length - 12} 處`);
    } else {
      console.log(`${n.padEnd(16)} ✓ 零變動`);
    }
  }
  await browser.close();
  if (update) {
    fs.writeFileSync(BASELINE, JSON.stringify(next, null, 1) + '\n');
    console.log(`\n已寫入 ${path.relative(ROOT, BASELINE)}（${names.length} 頁）。git diff 它，確認每一處變動都是你要的。`);
    return;
  }
  console.log(`\n${names.length} 頁，有變動 ${bad} 頁`);
  process.exit(bad ? 1 : 0);
})();
