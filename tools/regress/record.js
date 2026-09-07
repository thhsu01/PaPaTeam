// 執行期基準的錄音機。接在 tools/contrast/stubs.js 之後注入：樁件讓各頁腳本跑得完，
// 這一支則把 detail.js 交給 Leaflet 與 Chart.js 的東西原樣記下來——
// 那正是接縫上流過的資料（見 docs/adr/0001），比截圖精確，也不受字型與抗鋸齒影響。
window.__rec = { markers: [], chart: null };

(function () {
  const L = window.L;
  const circleMarker = L.circleMarker;
  L.circleMarker = function (latlng, options) {
    const o = circleMarker(latlng, options);
    const rec = { latlng: latlng, options: options, last: null, popup: null };
    const setStyle = o.setStyle, bindPopup = o.bindPopup;
    o.setStyle = function (s) { rec.last = s; return setStyle(s); };
    o.bindPopup = function (html) { rec.popup = html; return bindPopup(html); };
    window.__rec.markers.push(rec);
    return o;
  };

  const Chart = window.Chart;
  window.Chart = function (ctx, config) {
    // 函式（tooltip 回呼、onHover）丟掉，其餘照收：labels、datasets、scales、plugins
    window.__rec.chart = JSON.parse(JSON.stringify(config));
    return Chart(ctx, config);
  };
  window.Chart.register = Chart.register;
  window.Chart.defaults = Chart.defaults;
})();
