// 神奈川沖浪裏 — 一枚の絵を、マスクで決めた範囲ごとにわずかに歪ませて動かす。
//
// 動きはすべて「位相 p(0〜2π)の整数倍」だけで書くので、LOOP_SECONDS で
// ぴったり一周し、つなぎ目が出ない。
//
// 隠しオプション(画面には何も出さない。調整用):
//   ?debug=mask   マスクを色で重ねて表示(赤=大波, 緑=波の先, 青=海面)
//   ?speed=4      再生速度を上げる(一周の確認用)
//   ?amp=2        揺れ幅を何倍かにする
//   #mask / #fast  上の debug=mask / 早送り と同じ(? が使えない場所用)

(() => {
  'use strict';

  const LOOP_SECONDS = 30;
  const IMAGE_URL = 'assets/great-wave.jpg';
  const MASK_URL = 'assets/masks.png';

  const params = new URLSearchParams(location.search);
  // 確認ページ(アーティファクト)では ?… が使えないので、#mask / #fast でも切り替えられる。
  const hash = location.hash.slice(1);
  const DEBUG_MASK = params.get('debug') === 'mask' || hash === 'mask';
  const SPEED = parseFloat(params.get('speed')) || (hash === 'fast' ? 6 : 1);
  const AMP = parseFloat(params.get('amp')) || 1;

  const canvas = document.getElementById('c');
  const glOpts = { antialias: false, alpha: false, premultipliedAlpha: false, powerPreference: 'low-power' };
  const gl = canvas.getContext('webgl2', glOpts) || canvas.getContext('webgl', glOpts);
  if (!gl) return;
  const isGL2 = typeof WebGL2RenderingContext !== 'undefined' && gl instanceof WebGL2RenderingContext;

  const VERT = `
    attribute vec2 aPos;
    uniform vec2 uFit;      // 画面に「収める」ための縮尺
    varying vec2 vUv;
    // 絵の外周をほんの少しだけ隠す(縁の 1 画素のにじみ対策)。
    // 左端の落款にかかるので、これ以上は大きくしない。
    const float CROP = 0.004;
    void main() {
      vUv = CROP + (1.0 - 2.0 * CROP) * vec2(aPos.x * 0.5 + 0.5, 0.5 - aPos.y * 0.5);
      gl_Position = vec4(aPos * uFit, 0.0, 1.0);
    }
  `;

  const FRAG = `
    precision highp float;
    uniform sampler2D uImg;
    uniform sampler2D uMask;
    uniform float uPhase;   // 0..2π で一周
    uniform float uAmp;
    uniform float uAspect;  // 絵の 横/縦
    uniform float uDebug;
    varying vec2 vUv;

    const float TAU = 6.28318530718;

    // 大波のうねり。
    // 主役は「根元を支点に、波頭がのめり込んでは起き上がる」回転。回転は絵を
    // ひとかたまりのまま動かすので、大きく動かしても線が伸び縮みしにくい。
    // そこに少しの伸び上がりと、左下から波頭へ伝わる長い波長のずれを重ねる。
    const vec2 PIVOT = vec2(0.45, 0.80);   // 波の根元(縦横比をそろえた座標)
    vec2 swell(vec2 q, float p) {
      vec2 r = q - PIVOT;
      float ang = 0.050 * sin(p + 0.6);    // 最大およそ 3 度
      float c = cos(ang), s = sin(ang);
      vec2 rot = vec2(c * r.x + s * r.y, -s * r.x + c * r.y);
      vec2 d = r - rot;
      d += r * 0.020 * sin(p - 0.9);        // 伸び上がっては縮む
      vec2 w;
      w.x = sin(TAU * (0.55 * q.x - 0.45 * q.y) - p);
      w.y = sin(TAU * (0.40 * q.x - 0.60 * q.y) - p + 1.2);
      return d + w * 0.020;
    }

    // 波の先(爪):うねりの倍の速さで、上乗せして揺らす。
    // 波長を短くすると爪の一本一本が別々に伸び縮みして線が崩れるので、長めにとる。
    vec2 claws(vec2 q, float p) {
      vec2 d;
      d.x = sin(TAU * (0.7 * q.x + 0.5 * q.y) - 2.0 * p)
          + 0.5 * sin(TAU * (0.9 * q.y - 0.3 * q.x) - p + 0.8);
      d.y = sin(TAU * (0.5 * q.x - 0.7 * q.y) - 2.0 * p + 2.1)
          + 0.5 * sin(TAU * (0.8 * q.x + 0.4 * q.y) - p + 2.9);
      return d * 0.018;
    }

    void main() {
      vec2 uv = vUv;
      vec3 m = texture2D(uMask, uv).rgb;   // r=大波, g=波の先, b=海面

      // 縦横比をそろえた座標で計算し、最後に uv に戻す(ずれが円く出るように)。
      vec2 q = vec2(uv.x * uAspect, uv.y);
      vec2 d = m.r * swell(q, uPhase) + m.g * claws(q, uPhase);
      d *= uAmp;
      d.x /= uAspect;
      // 絵の縁に近いほど動きを弱める。ずれの最大(およそ 0.08)より縁からの距離が
      // 常に大きくなるので、絵の外を引き込むことはない。
      vec2 e = smoothstep(0.0, 0.10, uv) * smoothstep(0.0, 0.10, 1.0 - uv);
      d *= e.x * e.y;

      vec3 col = texture2D(uImg, uv - d).rgb;

      if (uDebug > 0.5) {
        col = mix(col, vec3(1.0, 0.15, 0.1), m.r * 0.45);
        col = mix(col, vec3(0.1, 1.0, 0.2), m.g * 0.55);
        col = mix(col, vec3(0.1, 0.3, 1.0), m.b * 0.45);
      }
      gl_FragColor = vec4(col, 1.0);
    }
  `;

  function compile(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }
  const prog = gl.createProgram();
  gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT));
  gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG));
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
  gl.useProgram(prog);

  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const aPos = gl.getAttribLocation(prog, 'aPos');
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

  const u = {};
  for (const n of ['uImg', 'uMask', 'uPhase', 'uAmp', 'uAspect', 'uDebug', 'uFit']) u[n] = gl.getUniformLocation(prog, n);
  gl.uniform1i(u.uImg, 0);
  gl.uniform1i(u.uMask, 1);
  gl.uniform1f(u.uAmp, AMP);
  gl.uniform1f(u.uDebug, DEBUG_MASK ? 1 : 0);

  function loadImage(url) {
    return new Promise((res, rej) => {
      const im = new Image();
      im.onload = () => res(im);
      im.onerror = () => rej(new Error('load failed: ' + url));
      im.src = url;
    });
  }

  function makeTexture(unit, img, mip) {
    const t = gl.createTexture();
    gl.activeTexture(gl.TEXTURE0 + unit);
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    // 絵は画面より大きく持つので、縮小時のちらつきを防ぐためにミップマップを使う(WebGL2 のみ)。
    if (mip && isGL2) {
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    } else {
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    }
    return t;
  }

  let imgAspect = 1;

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    const w = Math.round(canvas.clientWidth * dpr);
    const h = Math.round(canvas.clientHeight * dpr);
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    gl.viewport(0, 0, w, h);
    // 絵の全体が必ず見えるように収める(余白は黒)。
    const screenAspect = w / h;
    const fit = screenAspect > imgAspect ? [imgAspect / screenAspect, 1] : [1, screenAspect / imgAspect];
    gl.uniform2f(u.uFit, fit[0], fit[1]);
  }

  function frame(now) {
    resize();
    const t = ((now / 1000) * SPEED) % LOOP_SECONDS;
    gl.uniform1f(u.uPhase, (t / LOOP_SECONDS) * Math.PI * 2);
    gl.clearColor(0, 0, 0, 1);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    requestAnimationFrame(frame);
  }

  Promise.all([loadImage(IMAGE_URL), loadImage(MASK_URL)]).then(([img, mask]) => {
    imgAspect = img.naturalWidth / img.naturalHeight;
    gl.uniform1f(u.uAspect, imgAspect);
    makeTexture(0, img, true);
    makeTexture(1, mask, false);
    requestAnimationFrame(frame);
  });

  // ---- 画面を自動で消さない ----
  // Screen Wake Lock API(iOS Safari 16.4 以降)。ブラウザによっては
  // 画面に触れたあとでないと取れないので、最初のタップでも取り直す。
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
  keepAwake();
  document.addEventListener('visibilitychange', keepAwake);
  window.addEventListener('pointerdown', keepAwake);
  window.addEventListener('touchend', keepAwake);
})();
