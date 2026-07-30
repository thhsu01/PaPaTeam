/* ============================================================
   爬爬小隊 — 全站共用無障礙腳本
   ------------------------------------------------------------
   目前只做一件事：讓程式化捲動遵守 prefers-reduced-motion。
   ============================================================ */

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
