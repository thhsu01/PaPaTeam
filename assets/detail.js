/* ============================================================
   爬爬小隊 — 行程詳情頁共用腳本
   ------------------------------------------------------------
   十個詳情頁各自帶著 92–287 行幾乎相同的 inline JS：地圖、圖表、
   航點卡、天氣、時間軸。同一段邏輯抄十遍的代價是實際發生過的——
   天氣代碼對照表寫了五份、五份都不完整，使用者因此看到「天氣代碼96」。

   本檔收「機制」，各頁只描述「差異」：
     schedule / TRIP_DATE  ── 行程資料
     PaPaDetail.init({...}) ── 本頁的設定與少量小回呼

   刻意不收進本檔：時間軸卡片的 HTML 樣板。2026-08-04 量測後修正這句話的理由——
   結構其實只有兩種家族、圓點規則已收進 palette()，真正因頁而異的只有「顯示哪些欄位」。
   還沒收是因為它應該以「欄位清單」為介面，不是把樣板字串搬個位置；那是下一輪的事。

   海拔圖則已經收了：各頁只給領域旋鈕，Chart.js 藏在接縫後面（見 docs/adr/0001）。

   載入順序：site.js → detail.js → 各頁 inline script。
   兩支共用檔都不可加 defer，否則各頁 inline script 會先跑。
   ============================================================ */

window.PaPaDetail = (function () {
  'use strict';

  var cfg = null;
  var map = null, chart = null, markers = [];
  var current = 0;

  // ── 工具 ──────────────────────────────────────────────────
  function $(id) { return document.getElementById(id); }

  function setText(id, value) {
    var el = $(id);
    if (el && value != null) el.textContent = value;
  }

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  // ── 航點卡 ────────────────────────────────────────────────
  function updateWaypointCard(i) {
    current = i;
    var wp = cfg.schedule[i];
    var card = cfg.card || {};

    setText('wp-pos-label', wp.pos);
    setText('wp-title', wp.loc);
    setText('wp-time', wp.time);
    setText('wp-ele', wp.ele);
    if (wp.dist != null) setText('wp-dist', wp.dist.toFixed(2));
    setText('wp-desc', wp.desc);

    // 每個航點都必須有 advice（見 ARCHITECTURE.md）。這裡刻意不隱藏空的
    // 建議框——漏寫時就該在畫面上看得見，而不是被靜靜藏起來。
    var advice = $('wp-advice');
    if (advice) advice.textContent = wp.advice || '';

    if (map && markers.length) {
      if (cfg.map && cfg.map.selected) {
        markers.forEach(function (m, j) {
          m.setStyle(cfg.map.selected(cfg.schedule[j], j, cfg.schedule.length, j === i));
        });
      }
      if (card.follow === 'pan') map.panTo([wp.lat, wp.lng]);
      else if (card.follow === 'popup' && markers[i]) markers[i].openPopup();
    }

    // 選取時卡片閃一下，讓使用者知道右側/下方內容換了
    if (card.flash) {
      var el = $('wp-card');
      if (el) {
        el.classList.add.apply(el.classList, card.flash);
        setTimeout(function () {
          el.classList.remove.apply(el.classList, card.flash);
        }, 500);
      }
    }

    if (card.onUpdate) card.onUpdate(wp, i);
  }

  function step(delta) {
    var n = cfg.schedule.length;
    var next = current + delta;
    // 兩種原有行為：家族 A 循環、家族 B 到頭就停。維持各頁原樣。
    if ((cfg.card && cfg.card.wrap) === 'cycle') next = (next + n) % n;
    else if (next < 0 || next >= n) return;
    updateWaypointCard(next);
  }

  // ── 地圖 ──────────────────────────────────────────────────
  function initMap() {
    var m = cfg.map;
    if (!m || !$('map') || typeof L === 'undefined') return;

    var opts = { preferCanvas: !!m.preferCanvas };
    if (m.center) { opts.center = m.center; opts.zoom = m.zoom; }
    map = L.map('map', opts);
    if (!m.center) map.setView(m.setView[0], m.setView[1]);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                m.attribution ? { attribution: m.attribution } : {}).addTo(map);

    // 候選／計畫行程只有航點，軌跡就是航點連成的直線；已走過的行程若留下
    // GPS 紀錄，就改畫實際軌跡——那條線會繞過航點之間看不出來的髮夾彎。
    var track = m.track || {};
    var pts = track.points ||
              (track.slice ? cfg.schedule.slice(track.slice[0], track.slice[1]) : cfg.schedule)
                .map(function (w) { return [w.lat, w.lng]; });
    var line = { color: track.color || cssVar('--accent'), weight: track.weight || 4,
                 opacity: track.opacity == null ? 0.85 : track.opacity };
    if (track.dashArray) line.dashArray = track.dashArray;
    L.polyline(pts, line).addTo(map);

    cfg.schedule.forEach(function (wp, i) {
      var style = m.marker(wp, i, cfg.schedule.length);
      style.color = style.color || '#fff';
      style.weight = style.weight == null ? 2 : style.weight;
      var mk = L.circleMarker([wp.lat, wp.lng], style).addTo(map);
      if (m.popup) {
        mk.bindPopup('<strong>' + wp.loc + '</strong><br>⏱ ' + wp.time +
                     (wp.dist != null ? '<br>📏 ' + wp.dist + ' km' : '') + '<br>⛰ ' + wp.ele + ' m');
      }
      mk.on('click', function () { updateWaypointCard(i); });
      markers.push(mk);
    });
  }

  // ── 海拔剖面圖 ────────────────────────────────────────────
  /** 航點短名：海拔圖 x 軸上的顯示名稱。預設剝掉標高註記「(H643m)」，
      剝不乾淨的航點在 schedule 裡直接給 short——例外用資料表達，不是每頁一個格式化函式。 */
  function shortName(wp) {
    return wp.short || wp.loc
      // 標高註記有三種寫法：(H643m)、(H1,092m) 逗號、(標高 65m)
      .replace(/\s*[（(]\s*(?:[Hh]|標高)?\s*[\d.,]+\s*(?:m|M|公尺)?\s*[)）]/g, '')
      // 狀態註記：同一個地點在去回程各出現一次時用來區分，x 軸上是雜訊
      .replace(/\s*[（(](?:起點|終點|回程|去程|接駁|抵達|出發)[)）]/g, '')
      .trim();
  }

  /** 深合併：逃生口 advanced 用。陣列與非物件直接覆蓋，物件才往下併。 */
  function merge(base, extra) {
    if (!extra) return base;
    Object.keys(extra).forEach(function (k) {
      var a = base[k], b = extra[k];
      base[k] = (a && b && typeof a === 'object' && typeof b === 'object' &&
                 !Array.isArray(a) && !Array.isArray(b)) ? merge(a, b) : b;
    });
    return base;
  }

  // 海拔圖。各頁只給領域旋鈕，Chart.js 的設定樹完全由這裡組出來——
  // 換圖表庫只要改這一個函式，不是改 18 頁。理由見 docs/adr/0001。
  //
  //   elevationFloor  y 軸起點。市郊路線從 0 起讀得出爬升感；高山路線從 0 起
  //                   會浪費半張圖，所以設地板。這是編輯判斷，不可推導。預設 0。
  //   elevationMax    y 軸上限。不給就讓 Chart.js 自己算——它的刻度演算法挑的
  //                   數字（1092→1100、155→160）不是固定百分比，推導反而會改掉畫面。
  //   lineColor       剖面線的顏色。預設 --accent；四頁改用較深的 --accent-deep、
  //                   一頁改用較淺的 --accent-light。刻意不自動採用 --accent-deep：
  //                   bishan 與 mochashan 有定義它卻沒拿來當線色，自動套用會改到它們。
  //   fillAlpha       線下填色的濃度。預設 0.1，兩頁用 0.05。
  //   fillColor       線下填色的顏色。預設 --accent（與 lineColor 分開——
  //                   四頁的線較深但填色仍是主色）。只有 shiqiulinling 兩者同色。
  //   palette         航點配色，與地圖標記、時間軸圓點共用同一個決定。
  //   advanced        逃生口，深合併進最終的 Chart.js 設定。
  function initChart() {
    var c = cfg.chart || {};
    if (!$('elevation-chart') || typeof Chart === 'undefined') return;

    var accent = cssVar('--accent');

    var line = c.lineColor ? (cssVar(c.lineColor) || c.lineColor) : accent;
    // 填色與線色是兩件事：四頁的線用較深的 --accent-deep，填色卻仍是 --accent。
    // 所以填色預設走 accent，只有 shiqiulinling 兩者刻意同色，用 fillColor 指定。
    var fillC = c.fillColor ? (cssVar(c.fillColor) || c.fillColor) : accent;
    var y = { title: { display: true, text: '海拔 (m)' },
              grid: { color: '#f0ede8' },
              min: c.elevationFloor == null ? 0 : c.elevationFloor };
    if (c.elevationMax != null) y.max = c.elevationMax;

    var opts = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: {
          label: function (ctx) { return '海拔: ' + ctx.parsed.y + ' m'; },
          title: function (ctx) { return ctx[0].label; }
        } }
      },
      scales: { y: y, x: { ticks: { maxRotation: 35, font: { size: 10 } }, grid: { display: false } } },
      // 滑過圖表即選取該航點。原本只有四頁有（且四頁一字不差），2026-08-04 起全站預設。
      onHover: function (e, el) { if (el.length > 0) updateWaypointCard(el[0].index); }
    };

    chart = new Chart($('elevation-chart').getContext('2d'), {
      type: 'line',
      data: {
        labels: cfg.schedule.map(shortName),
        datasets: [{
          label: '海拔 (m)',
          data: cfg.schedule.map(function (w) { return w.ele; }),
          borderColor: line,
          borderWidth: 2.5,
          pointRadius: 5,
          // 資料點顏色與地圖標記、時間軸圓點是同一個決定，走同一個 palette。
          // 沒給就用本頁主色建一個預設的。
          pointBackgroundColor: (function () {
            var pal = c.palette || cfg.palette || palette({ accent: accent });
            var n = cfg.schedule.length;
            return cfg.schedule.map(function (w, i) { return pal.color(w, i, n); });
          })(),
          fill: true,
          backgroundColor: alpha(fillC, c.fillAlpha == null ? 0.1 : c.fillAlpha),
          tension: 0.35
        }]
      },
      options: merge(opts, c.advanced)
    });
  }

  function alpha(hex, a) {
    var h = hex.replace('#', '');
    return 'rgba(' + parseInt(h.slice(0, 2), 16) + ', ' + parseInt(h.slice(2, 4), 16) +
           ', ' + parseInt(h.slice(4, 6), 16) + ', ' + a + ')';
  }

  // ── 時間軸 ────────────────────────────────────────────────
  // 卡片樣板由各頁提供（那是版面設計）；此處只負責走訪、掛上點擊行為。
  function renderTimeline() {
    var t = cfg.timeline;
    var container = $('timeline-container');
    if (!t || !container) return;

    cfg.schedule.forEach(function (wp, i) {
      var div = document.createElement('div');
      div.className = t.className;
      div.innerHTML = t.item(wp, i, cfg.schedule.length);
      div.onclick = function () {
        updateWaypointCard(i);
        var target = $('map-section');
        if (target) target.scrollIntoView({ behavior: 'smooth' });
      };
      container.appendChild(div);
    });
  }

  // ── 天氣 ──────────────────────────────────────────────────
  // 兩種情境：有行程日的查該日預報，沒日期的候選行程顯示今日天氣。
  function markTripPast(todayISO) {
    if (cfg.tripDate && todayISO && cfg.tripDate < todayISO) {
      var el = $('trip-past-notice');
      if (el) el.classList.remove('hidden');
    }
  }

  function tripMD() {
    var p = cfg.tripDate.split('-');
    return (+p[1]) + '/' + (+p[2]);
  }

  function val(arr, i) {
    if (!arr) return null;
    var v = arr[i];
    return (v == null || (typeof v === 'number' && isNaN(v))) ? null : v;
  }

  async function fetchWeather() {
    var w = cfg.weather;
    if (!w) return;
    var main = $(w.mainId || 'weather-main');
    var sub = $(w.subId || 'weather-sub');
    var label = $('weather-label');
    if (!main) return;

    var days = cfg.tripDate ? 16 : 1;

    // 只給經緯度時，Open-Meteo 用它自己地形網格的高度，山區常常差很多。
    // 傳實際海拔可讓它做高度降尺度，拿到的才是那個高度的預報。
    // 預設取行程最高點——那是最冷、風最大的地方，對行前判斷是保守的一側。
    var elev = w.elevation;
    if (elev == null && cfg.schedule) {
      elev = Math.max.apply(null, cfg.schedule.map(function (x) { return x.ele; }));
    }

    var url = 'https://api.open-meteo.com/v1/forecast?latitude=' + w.lat + '&longitude=' + w.lng +
              (elev != null ? '&elevation=' + elev : '') +
              '&daily=weathercode,temperature_2m_max,temperature_2m_min' +
              ',apparent_temperature_max,apparent_temperature_min,precipitation_probability_max' +
              '&timezone=Asia/Taipei&forecast_days=' + days;
    try {
      var data = await (await fetch(url)).json();
      var idx = 0, subText = w.subText || '', labelText = null;

      if (cfg.tripDate) {
        var found = data.daily.time.indexOf(cfg.tripDate);
        markTripPast(data.daily.time[0]);   // 視窗第一天即今日
        if (found !== -1) {
          idx = found;
          labelText = tripMD() + ' 天氣預報';
          subText = tripMD() + ' 行程日預報';
        } else {
          labelText = '今日天氣';
          // 行程日已過卻說「尚遠」是先前實際出現過的錯誤文案
          subText = cfg.tripDate < data.daily.time[0]
                    ? '行程日已過，顯示今日天氣' : '行程日尚遠，顯示今日天氣';
        }
      }

      var text = window.PaPaWeather.text(data.daily.weathercode[idx]);
      var lo = Math.round(data.daily.temperature_2m_min[idx]);
      var hi = Math.round(data.daily.temperature_2m_max[idx]);
      main.textContent = text + ' ' + lo + (w.sep || '°–') + hi + (w.unit || '°');

      // 體感與降雨機率是附加資訊，接在副標後面。
      // 實測 16 天視窗內兩者都有值，但仍逐項確認才顯示——欄位若因模型或
      // 參數組合而缺席，寧可整項不出現，也不要讓 null 變成畫面上的 NaN。
      var extra = [];
      var fl = val(data.daily.apparent_temperature_min, idx);
      var fh = val(data.daily.apparent_temperature_max, idx);
      if (fl != null && fh != null) {
        extra.push('體感 ' + Math.round(fl) + (w.sep || '°–') + Math.round(fh) + (w.unit || '°'));
      }
      var pop = val(data.daily.precipitation_probability_max, idx);
      if (pop != null) extra.push('降雨 ' + Math.round(pop) + '%');

      if (sub) {
        var line = [subText].concat(extra).filter(Boolean).join(' · ');
        if (line) sub.textContent = line;
      }
      if (label && labelText) label.textContent = labelText;
      main.classList.remove('loading-pulse', 'weather-pulse');
    } catch (e) {
      // 天氣取不到時仍要判斷行程是否已過，故以本地日期作為後備
      markTripPast(new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Taipei' }));
      main.textContent = w.errorMain || '天氣資料暫無法取得';
      if (sub) sub.textContent = '請稍後再試';
      main.classList.remove('loading-pulse', 'weather-pulse');
    }
  }

  // ── 航點配色 ──────────────────────────────────────────────
  // 「這個航點該是什麼顏色」原本在每頁寫三次：地圖標記、圖表資料點、時間軸圓點。
  // 寫三次就會漂——2026-08-04 發現 caolingguidao 加了「集合地點」之後只更新了
  // 地圖那份，同一個航點在地圖上是端點色、在圖表上卻是一般色。
  //
  // 這裡只收「規則」，顏色與判準仍由各頁給：哪個 pos 算山頂各頁不同
  // （最高點／觀機平台／瞭望台），端點預設看索引但也可覆寫。
  function palette(opt) {
    var peak   = opt.peak  || '#7c9e52';   // 全站語意色：山頂（見 manifest 的 semantic_colors）
    var stone  = opt.stone || '#a09080';   // 一般航點
    var accent = opt.accent;               // 本頁主色，用於起訖點
    var isPeak = opt.isPeak || function (wp) { return wp.pos === '最高點'; };
    var isEnd  = opt.isEnd  || function (wp, i, n) { return i === 0 || i === n - 1; };
    // 有些路線有第三種值得標的東西——datongshan 的展望台、nanshijiao 的信仰地標。
    // 以 { pos: 顏色 } 表達，優先序在山頂之後、起訖點之前。刻意只開一層：
    // 再多下去就變回「每頁一套配色」，那正是要收掉的東西。
    var extra = opt.extra || null;
    function colorOf(wp, i, n) {
      if (isPeak(wp)) return peak;
      if (extra && Object.prototype.hasOwnProperty.call(extra, wp.pos)) return extra[wp.pos];
      return isEnd(wp, i, n) ? accent : stone;
    }
    return {
      peak: peak, stone: stone, accent: accent, isPeak: isPeak, isEnd: isEnd, extra: extra,
      color:  colorOf,
      radius: function (wp, i, n) { return isEnd(wp, i, n) ? 9 : isPeak(wp) ? 8 : 6; }
    };
  }

  // ── 對外介面 ──────────────────────────────────────────────
  return {
    palette: palette,
    init: function (options) {
      cfg = options;

      window.prevWaypoint = function () { step(-1); };
      window.nextWaypoint = function () { step(1); };
      window.updateWaypointCard = updateWaypointCard;
      // 並非每頁都有導航鍵（shiqiulinling 就沒有），沒設 nav 就不掛
      if (cfg.nav) {
        window.openNavigation = function () {
          window.open('https://www.google.com/maps/dir/?api=1&destination=' +
                      cfg.nav[0] + ',' + cfg.nav[1], '_blank');
        };
      }

      if (cfg.weather) fetchWeather();

      window.addEventListener('DOMContentLoaded', function () {
        initMap();
        initChart();
        renderTimeline();
        updateWaypointCard(0);
      });
    },
    get map() { return map; },
    get chart() { return chart; },
    get markers() { return markers; }
  };
})();
