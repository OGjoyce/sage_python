import * as THREE from 'three';

const hud = {
  resVal: document.getElementById('resVal'),
  fpsVal: document.getElementById('fpsVal'),
};
const errEl = document.getElementById('err');

function showError(e) {
  console.error(e);
  errEl.style.display = 'flex';
  errEl.textContent = 'Shader/WebGL error:\n\n' + (e && e.message ? e.message : String(e));
}

async function main() {
  // Same idea as the 2D build: fetch the shared math as plain text and
  // splice it into this platform's fragment shader wrapper. Here two
  // files get concatenated -- water_core.glsl for the shared noise/sdf/
  // dither helpers, then water_core_3d.glsl (which assumes those exist)
  // for the actual raymarched scene.
  const [coreSrc, core3dSrc] = await Promise.all([
    fetch('../shared/water_core.glsl').then(r => r.text()),
    fetch('../shared/water_core_3d.glsl').then(r => r.text()),
  ]);

  const fragmentShader = `
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform vec2 uResolution;
uniform vec3 uCamPos;
uniform vec3 uCamTarget;

${coreSrc}

${core3dSrc}

void main() {
  vec2 fragPx = vUv * uResolution;
  vec3 col = wf_render3d(fragPx, uResolution, uTime, uCamPos, uCamTarget);
  gl_FragColor = vec4(col, 1.0);
}
`;

  const vertexShader = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

  const renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1);
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace; // see water_core.glsl's gamma-encode note
  document.body.appendChild(renderer.domElement);

  const pixelSize = 2;

  const lowScene = new THREE.Scene();
  const lowCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10);
  lowCam.position.z = 1;

  const camTarget = new THREE.Vector3(0.3, 1.1, 0.5);
  const orbit = { az: 0.55, el: 0.34, dist: 6.2, autorotate: true };

  const uniforms = {
    uTime: { value: 0 },
    uResolution: { value: new THREE.Vector2(1, 1) },
    uCamPos: { value: new THREE.Vector3() },
    uCamTarget: { value: camTarget },
  };

  const waterMat = new THREE.ShaderMaterial({ vertexShader, fragmentShader, uniforms });
  const waterQuad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), waterMat);
  lowScene.add(waterQuad);

  let rt = null;
  const presentScene = new THREE.Scene();
  const presentCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10);
  presentCam.position.z = 1;
  const presentMat = new THREE.MeshBasicMaterial({ map: null });
  const presentQuad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), presentMat);
  presentScene.add(presentQuad);

  function resize() {
    const w = window.innerWidth, h = window.innerHeight;
    const lowW = Math.max(2, Math.floor(w / pixelSize));
    const lowH = Math.max(2, Math.floor(h / pixelSize));
    renderer.setSize(lowW * pixelSize, lowH * pixelSize, true);
    if (rt) rt.dispose();
    rt = new THREE.WebGLRenderTarget(lowW, lowH, {
      minFilter: THREE.NearestFilter,
      magFilter: THREE.NearestFilter,
      format: THREE.RGBAFormat,
      type: THREE.UnsignedByteType,
    });
    uniforms.uResolution.value.set(lowW, lowH);
    presentMat.map = rt.texture;
    presentMat.needsUpdate = true;
    hud.resVal.textContent = `${lowW}×${lowH}`;
  }
  window.addEventListener('resize', resize);
  resize();

  // ---- orbit controls: drag to look around, wheel to zoom ---------------
  const canvas = renderer.domElement;
  let dragging = false;
  let lastX = 0, lastY = 0;
  let idleTimer = null;

  function stopAutorotateFor(ms) {
    orbit.autorotate = false;
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => { orbit.autorotate = true; }, ms);
  }

  canvas.addEventListener('pointerdown', (e) => {
    dragging = true;
    lastX = e.clientX; lastY = e.clientY;
    canvas.setPointerCapture(e.pointerId);
    stopAutorotateFor(4000);
  });
  canvas.addEventListener('pointermove', (e) => {
    if (!dragging) return;
    const dx = e.clientX - lastX, dy = e.clientY - lastY;
    lastX = e.clientX; lastY = e.clientY;
    orbit.az -= dx * 0.006;
    orbit.el = Math.max(-0.15, Math.min(1.35, orbit.el + dy * 0.006));
  });
  window.addEventListener('pointerup', () => { dragging = false; });
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    orbit.dist = Math.max(2.2, Math.min(14.0, orbit.dist + e.deltaY * 0.0045));
    stopAutorotateFor(2500);
  }, { passive: false });

  const clock = new THREE.Clock();
  let frames = 0, fpsTimer = 0;

  function animate() {
    requestAnimationFrame(animate);
    const dt = Math.min(clock.getDelta(), 0.05);
    uniforms.uTime.value += dt;

    if (orbit.autorotate) orbit.az += dt * 0.09;

    const camPos = uniforms.uCamPos.value;
    camPos.set(
      camTarget.x + orbit.dist * Math.cos(orbit.el) * Math.sin(orbit.az),
      camTarget.y + orbit.dist * Math.sin(orbit.el),
      camTarget.z + orbit.dist * Math.cos(orbit.el) * Math.cos(orbit.az)
    );

    renderer.setRenderTarget(rt);
    renderer.render(lowScene, lowCam);
    renderer.setRenderTarget(null);
    renderer.render(presentScene, presentCam);

    frames++; fpsTimer += dt;
    if (fpsTimer >= 0.5) {
      hud.fpsVal.textContent = (frames / fpsTimer).toFixed(0);
      frames = 0; fpsTimer = 0;
    }
  }
  animate();
}

main().catch(showError);
