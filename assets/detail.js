/* ============================================================
   爬爬小隊 — 行程詳情頁共用腳本
   ------------------------------------------------------------
   十個詳情頁各自帶著 92–287 行幾乎相同的 inline JS：地圖、圖表、
   航點卡、天氣、時間軸。同一段邏輯抄十遍的代價是實際發生過的——
   天氣代碼對照表寫了五份、五份都不完整，使用者因此看到「天氣代碼96」。

   本檔收「機制」，各頁只描述「差異」：
     schedule / TRIP_DATE  ── 行程資料
     PaPaDetail.init({...}) ── 本頁的設定與少量小回呼

   刻意不收進本檔：時間軸卡片的 HTML 樣板。那是各頁的版面設計
   （欄位、結構、圓點規則都不同），塞進設定只會把樣板字串搬個位置。

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
    setText('wp-time', wp[card.timeField || 'time']);
    setText('wp-ele', wp.ele);
    if (wp.dist != null) setText('wp-dist', wp.dist.toFixed(2));
    setText('wp-desc', wp.desc);

    // 沒有建議內容時整塊收起來，而不是留一個空欄位
    var advice = $('wp-advice');
    if (advice) {
      advice.textContent = wp.advice || '';
      if (card.hideEmptyAdvice) {
        advice.parentElement.classList.toggle('hidden', !wp.advice);
      }
    }

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

    var track = m.track || {};
    var pts = (track.slice ? cfg.schedule.slice(track.slice[0], track.slice[1]) : cfg.schedule)
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
        mk.bindPopup('<strong>' + wp.loc + '</strong><br>⏱ ' + wp[(cfg.card || {}).timeField || 'time'] +
                     (wp.dist != null ? '<br>📏 ' + wp.dist + ' km' : '') + '<br>⛰ ' + wp.ele + ' m');
      }
      mk.on('click', function () { updateWaypointCard(i); });
      markers.push(mk);
    });
  }

  // ── 海拔剖面圖 ────────────────────────────────────────────
  function initChart() {
    var c = cfg.chart;
    if (!c || !$('elevation-chart') || typeof Chart === 'undefined') return;

    var accent = cssVar('--accent');
    var ctx = $('elevation-chart').getContext('2d');
    var dataset = Object.assign({
      label: '海拔 (m)',
      data: cfg.schedule.map(function (w) { return w.ele; }),
      borderColor: accent,
      borderWidth: 3,
      pointRadius: 4,
      fill: true,
      backgroundColor: c.fillAlpha === false ? undefined : alpha(accent, c.fillAlpha || 0.05),
      tension: 0.35
    }, c.dataset || {});

    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: cfg.schedule.map(c.label || function (w) { return w.loc; }),
        datasets: [dataset]
      },
      options: Object.assign({
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }, c.options || {})
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

  async function fetchWeather() {
    var w = cfg.weather;
    if (!w) return;
    var main = $(w.mainId || 'weather-main');
    var sub = $(w.subId || 'weather-sub');
    var label = $('weather-label');
    if (!main) return;

    var days = cfg.tripDate ? 16 : 1;
    var url = 'https://api.open-meteo.com/v1/forecast?latitude=' + w.lat + '&longitude=' + w.lng +
              '&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia/Taipei' +
              '&forecast_days=' + days;
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
      if (sub && subText) sub.textContent = subText;
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

  // ── 對外介面 ──────────────────────────────────────────────
  return {
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
