// 本環境的網路政策擋掉 CDN，故以最小樁件替代 Leaflet 與 Chart.js，
// 讓各頁腳本能跑完（否則 initMap() 一拋錯，renderTimeline() 就不會執行，
// 時間軸的幾何就量不到）。樁件只需支撐呼叫鏈，不需真的畫東西。
window.__stubbed = true;

const chain = () => {
  const o = {
    addTo: () => o, bindPopup: () => o, openPopup: () => o, closePopup: () => o,
    bindTooltip: () => o, openTooltip: () => o, unbindTooltip: () => o,
    setRadius: () => o, bringToFront: () => o, setOpacity: () => o,
    on: () => o, off: () => o, setStyle: () => o, setLatLng: () => o,
    getElement: () => document.createElement('div'), remove: () => o,
  };
  return o;
};

const mapObj = () => {
  const m = {
    setView: () => m, panTo: () => m, flyTo: () => m, fitBounds: () => m,
    addLayer: () => m, removeLayer: () => m, on: () => m, off: () => m,
    invalidateSize: () => m, getZoom: () => 14, setZoom: () => m,
    getBounds: () => ({ pad: () => ({}) }), scrollWheelZoom: { disable(){}, enable(){} },
    remove: () => m,
  };
  return m;
};

window.L = {
  map: () => mapObj(),
  tileLayer: () => chain(),
  polyline: () => chain(),
  circleMarker: () => chain(),
  marker: () => chain(),
  divIcon: () => ({}),
  icon: () => ({}),
  latLngBounds: () => ({ pad: () => ({}) }),
  control: { scale: () => chain() },
};

window.Chart = function Chart() {
  return { update(){}, destroy(){}, resize(){}, data: { datasets: [] } };
};
window.Chart.register = () => {};
window.Chart.defaults = { font: {}, plugins: {} };
