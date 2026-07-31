/* ============================================================
   爬爬小隊 — 全站共用腳本
   ------------------------------------------------------------
   1. 讓程式化捲動遵守 prefers-reduced-motion
   2. 天氣代碼對照表（WMO，Open-Meteo 使用）
   ============================================================ */

/* ── 天氣代碼 ──────────────────────────────────────────────
   Open-Meteo 的 weathercode 採 WMO 4677 的子集，共 28 種。
   先前五個頁面各自手寫一份，每份都只涵蓋 10–17 種，
   遇到沒列到的代碼就顯示「天氣代碼96」這種原始值給使用者看
   （96 是雷雨伴冰雹，實際發生過）。此處收成唯一一份完整表。

   本檔不可加 defer。各頁的 fetchWeather() 在 await 網路回應之後查表，
   一度以為「網路往返一定比 defer 晚」所以安全——實測推翻了這個推論：
   回應夠快（快取命中或本地測試）時，續行會在 defer 腳本執行前就跑完，
   PaPaWeather 還不存在，整段掉進 catch 顯示「天氣資料暫無法取得」。
   本檔不碰 DOM，放在 head 直接執行沒有副作用。 */
window.PaPaWeather = (function () {
  'use strict';

  var TEXT = {
    0: '☀️ 晴天',      1: '🌤 大致晴',    2: '⛅ 部分多雲',  3: '☁️ 陰天',
    45: '🌫 霧',        48: '🌫 霧淞',
    51: '🌦 小毛毛雨',  53: '🌦 毛毛雨',   55: '🌦 濃毛毛雨',
    56: '🌧 凍毛毛雨',  57: '🌧 強凍毛毛雨',
    61: '🌧 小雨',      63: '🌧 中雨',     65: '🌧 大雨',
    66: '🌧 凍雨',      67: '🌧 強凍雨',
    71: '🌨 小雪',      73: '🌨 中雪',     75: '🌨 大雪',     77: '🌨 冰珠',
    80: '🌦 小陣雨',    81: '🌧 陣雨',     82: '⛈ 強陣雨',
    85: '🌨 陣雪',      86: '🌨 強陣雪',
    95: '⛈ 雷雨',      96: '⛈ 雷雨伴冰雹', 99: '⛈ 強雷雨伴冰雹'
  };

  return {
    // 查不到時據實說不知道，不要猜一個天氣填上去——
    // 原本 laojiujianshan 的後備值是「多雲」，那是在對使用者謊報。
    text: function (code) {
      return TEXT[code] || '🌡 天氣代碼 ' + code + '（未知）';
    }
  };
})();

(function () {
  'use strict';

  // 依規範，scrollIntoView({behavior:'smooth'}) 會覆蓋 CSS 的
  // scroll-behavior，因此 @media (prefers-reduced-motion) 攔不到它。
  //
  // 各詳情頁的導覽鍵都是 inline onclick 直接呼叫 scrollIntoView（約 50 處），
  // 逐一改寫風險高且易漏，故在此集中改寫 behavior。
  // 僅在使用者確實要求減少動態時才介入，其餘情況完全不改變行為。
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  if (!reduceMotion.matches) return;

  var native = Element.prototype.scrollIntoView;

  Element.prototype.scrollIntoView = function (options) {
    if (options && typeof options === 'object' && options.behavior === 'smooth') {
      var patched = {};
      for (var key in options) {
        if (Object.prototype.hasOwnProperty.call(options, key)) {
          patched[key] = options[key];
        }
      }
      patched.behavior = 'auto';
      return native.call(this, patched);
    }
    return native.call(this, options);
  };
})();
