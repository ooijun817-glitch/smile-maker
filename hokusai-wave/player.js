// AI で動かした「神奈川沖浪裏」の動画を、全画面でくり返し流すだけ。
// 動画は最初と最後のコマが元の絵と同じなので、そのまま loop すればつながる。
(() => {
  'use strict';
  const video = document.getElementById('v');

  // iPhone の低電力モードなどで自動再生が止められたときは、最初のタップで再生する。
  function play() {
    const p = video.play();
    if (p && p.catch) p.catch(() => {});
  }
  play();

  // ---- 画面を自動で消さない ----
  let lock = null;
  async function keepAwake() {
    if (!('wakeLock' in navigator) || document.visibilityState !== 'visible') return;
    if (lock && !lock.released) return;
    try {
      lock = await navigator.wakeLock.request('screen');
    } catch (e) {
      lock = null;
    }
  }
  function onTouch() {
    play();
    keepAwake();
  }
  keepAwake();
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') play();
    keepAwake();
  });
  window.addEventListener('pointerdown', onTouch);
  window.addEventListener('touchend', onTouch);
})();
