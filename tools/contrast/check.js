// 對比度實測（WCAG 2.1 AA）。用法：
//     node tools/contrast/check.js <頁名> [頁名...]        例：node tools/contrast/check.js hushan index
//     node tools/contrast/check.js --all
// 需要本機在 8099 埠提供靜態檔：python3 -m http.server 8099
//
// 這支工具踩過四個坑，每一個都曾產生整批假訊號，作法都寫在下面：
//
//  1. DOM 往上找 backgroundColor 會遺失 alpha。bg-red-500/30 疊在 bg-black/20 上會被
//     當成純紅。→ 改為實際截圖、取畫面上的眾數像素當底色。
//
//  2. 但字多的元素，眾數就是「字」本身。可能是它自己的字（量到 fg == bg、比值 1:1），
//     也可能是子元素的字（datongshan 的 <h1> 兩行不同色，量第一行時眾數是第二行的
//     玫瑰色，於是報 2.78:1，實際 12.6:1）。→ 只對第一輪不合格的元素做第二輪：
//     把整個子樹的文字都塗透明再截一次，此時眾數必然是真正的底色。
//     （先前版本靠人工記住哪些該忽略；直接量對比較不會出錯，也不會把真問題一起忽略掉。）
//
//  3. Tailwind 沒載到時整頁沒有樣式，text-white 會算成黑色，於是滿江紅。
//     2026-08-03 就這樣誤報了 15 頁共 31 處。→ 開頭先驗樣式有沒有生效，沒有就中止。
//
//  4. 祖先有 backdrop-filter 時，locator.screenshot() 只截到該元素自己那層，拿不到
//     底下已經合成的畫面。huoyianshan 的大峽谷面板因此量到淺色底、報 1.18:1，
//     實際是 6.81:1。→ 改用整頁截圖再裁切到元素範圍。
//
// 另外：skip link 在取得焦點前定位在畫面外，量它沒有意義——依位置略過，不是靠名單。

const { chromium } = require('playwright');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const BASE = process.env.PAPA_BASE || 'http://127.0.0.1:8099';
const CHROME = process.env.PW_CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const TMP = path.join(require('os').tmpdir(), '_ctr_' + process.pid + '.png');

const CDN = ['**://cdn.tailwindcss.com/**', '**://cdn.jsdelivr.net/**', '**://unpkg.com/**',
             '**://fonts.googleapis.com/**', '**://api.open-meteo.com/**',
             '**://generativelanguage.googleapis.com/**', '**://images.unsplash.com/**'];

function lum(c) {
  const s = c.map(v => v / 255).map(v => v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  return 0.2126 * s[0] + 0.7152 * s[1] + 0.0722 * s[2];
}
function ratio(a, b) {
  const la = lum(a), lb = lum(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}
const near = (a, b) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) + Math.abs(a[2] - b[2]) <= 12;

/** 截一個元素，回傳畫面上最常見的像素（RGB 陣列）。 */
function modePixel(buf) {
  fs.writeFileSync(TMP, buf);
  return JSON.parse(execSync(
    `python3 -c "
from PIL import Image
from collections import Counter
im=Image.open('${TMP}').convert('RGB');w,h=im.size;px=im.load()
print(list(Counter(px[x,y] for x in range(w) for y in range(h)).most_common(1)[0][0]))"`
  ).toString());
}

async function checkPage(browser, name) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const p = await ctx.newPage();
  await p.addInitScript({ path: path.join(__dirname, 'stubs.js') });
  for (const u of CDN) await p.route(u, r => r.fulfill({ body: '{}', contentType: 'application/javascript' }));
  await p.goto(`${BASE}/${name}.html`, { waitUntil: 'load' });
  await p.addStyleTag({ path: path.join(__dirname, 'tw.css') });
  await p.waitForTimeout(700);

  // 坑 3：確認 Tailwind 真的生效，否則整輪結果沒有意義
  const styled = await p.evaluate(() => {
    const d = document.createElement('div');
    d.className = 'text-white'; document.body.appendChild(d);
    const c = getComputedStyle(d).color; d.remove();
    return c.replace(/\s/g, '') === 'rgb(255,255,255)';
  });
  if (!styled) {
    await ctx.close();
    throw new Error(`${name}：Tailwind 未生效，中止（見本檔開頭第 3 點）`);
  }

  const cands = await p.evaluate(() => {
    const parse = s => (s.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
    const out = [];
    document.querySelectorAll('*').forEach((el, i) => {
      const t = [...el.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim())
                                  .map(n => n.textContent.trim()).join('');
      if (!t) return;
      const st = getComputedStyle(el);
      if (st.display === 'none' || st.visibility === 'hidden' || el.closest('.hidden')) return;
      const r = el.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) return;
      // skip link 之類在取得焦點前定位到畫面外的元素：量了沒有意義
      if (r.right <= 0 || r.bottom <= 0 || r.left >= document.documentElement.scrollWidth) return;
      // 底圖載不出來時，量到的底色是佔位灰，不是實際會看到的顏色。
      // 只認 url()——CSS 漸層同樣算 background-image，但它一定畫得出來，不該被排除。
      let bgImg = false;
      for (let n = el; n && n !== document.documentElement; n = n.parentElement)
        if (/url\(/.test(getComputedStyle(n).backgroundImage)) { bgImg = true; break; }
      el.setAttribute('data-ctr', i);
      const px = parseFloat(st.fontSize), w = parseInt(st.fontWeight) || 400;
      out.push({ i, t: t.slice(0, 26), fg: parse(st.color), px, w, bgImg,
                 need: (px >= 24 || (px >= 18.66 && w >= 700)) ? 3 : 4.5 });
    });
    return out;
  });

  // 坑 4：祖先有 backdrop-filter 時，locator.screenshot() 拿不到底下已合成的畫面
  // （huoyianshan 的大峽谷面板因此量到淺色底、報 1.18:1，實際是 6.81:1）。
  // 改用「整頁截圖 + 裁切到元素範圍」，合成結果就跟人眼看到的一致。
  const shoot = async (loc) => {
    const box = await loc.boundingBox({ timeout: 4000 });
    if (!box || box.width < 4 || box.height < 4) return null;
    return p.screenshot({ clip: box, timeout: 4000 });
  };

  const bad = [], unsure = [];
  for (const c of cands) {
    const loc = p.locator(`[data-ctr="${c.i}"]`);
    let buf;
    try { buf = await shoot(loc); } catch { continue; }
    if (!buf) continue;
    let bg = modePixel(buf);
    if (ratio(c.fg, bg) >= c.need - 0.005) continue;   // 過了就不必再量

    // 坑 2：第一輪不合格時，眾數很可能根本不是底色，而是字——可能是這個元素自己的字
    // （字太多、佔滿整格），也可能是子元素的字（datongshan 的 <h1> 兩行不同色，
    // 量第一行時眾數是第二行的玫瑰色）。把整個子樹的文字都塗透明再量一次，
    // 這時眾數必然是真正的底色。只對不合格者做，所以只多花幾張截圖。
    try {
      await loc.evaluate(el => {
        el.dataset._ctrHide = '1';
        el.querySelectorAll('*').forEach(n => n.style.setProperty('color', 'transparent', 'important'));
        el.style.setProperty('color', 'transparent', 'important');
      });
      const b2 = await shoot(loc);
      await loc.evaluate(el => {
        el.querySelectorAll('*').forEach(n => n.style.removeProperty('color'));
        el.style.removeProperty('color');
        delete el.dataset._ctrHide;
      });
      if (!b2) continue;
      bg = modePixel(b2);
    } catch { continue; }

    const r = ratio(c.fg, bg);
    if (r >= c.need - 0.005) continue;
    (c.bgImg ? unsure : bad).push({ ...c, bg, r: +r.toFixed(2) });
  }

  await ctx.close();
  return { cands: cands.length, bad, unsure };
}

(async () => {
  let names = process.argv.slice(2);
  if (names[0] === '--all' || !names.length) {
    names = fs.readdirSync(ROOT).filter(f => f.endsWith('.html')).map(f => f.slice(0, -5)).sort();
  }
  const b = await chromium.launch({ executablePath: CHROME });
  let fails = 0;
  for (const n of names) {
    let r;
    try { r = await checkPage(b, n); }
    catch (e) { console.log(`${n.padEnd(16)} ⚠ ${e.message}`); fails++; continue; }
    const tag = r.bad.length ? `✗ ${r.bad.length} 處不合格` : '✓ 通過';
    console.log(`${n.padEnd(16)} ${tag}（候選 ${r.cands}${r.unsure.length ? `，另 ${r.unsure.length} 處疊在圖片上、無法確定` : ''}）`);
    r.bad.forEach(x => console.log(`   ✗ ${x.t}  ${x.r}:1（需 ${x.need}）  ${x.px}px/${x.w}  rgb(${x.fg}) on rgb(${x.bg})`));
    r.unsure.forEach(x => console.log(`   ? ${x.t}  ${x.r}:1（需 ${x.need}）  疊在背景圖上，本環境載不到圖，實際底色可能不同`));
    fails += r.bad.length;
  }
  await b.close();
  try { fs.unlinkSync(TMP); } catch {}
  console.log(`\n${names.length} 頁，不合格 ${fails} 處`);
  process.exit(fails ? 1 : 0);
})();
