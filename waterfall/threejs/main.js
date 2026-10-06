import * as THREE from 'three';

const hud = {
  pixelSize: document.getElementById('pixelSize'),
  pixelSizeVal: document.getElementById('pixelSizeVal'),
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
  // The only math in this file is plumbing (render targets, uniforms).
  // The actual waterfall lives in shared/water_core.glsl, fetched here as
  // plain text and spliced into this platform's fragment shader wrapper.
  const coreSrc = await (await fetch('../shared/water_core.glsl')).text();

  const fragmentShader = `
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform vec2 uResolution;

${coreSrc}

void main() {
  vec2 fragPx = vUv * uResolution;
  vec3 col = wf_render(fragPx, uResolution, uTime);
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
  // water_core.glsl does its own gamma encode as its very last step (see
  // the comment there) specifically so both renderers show the same
  // brightness. Three.js's default is to re-encode linear->sRGB on output,
  // which would gamma-correct an already-gamma-corrected image; turning
  // that off makes this a raw passthrough, matching native GL's default
  // framebuffer behavior exactly.
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
  document.body.appendChild(renderer.domElement);

  let pixelSize = parseInt(hud.pixelSize.value, 10);

  // ---- low-res pass: the water shader renders into a small target -------
  const lowScene = new THREE.Scene();
  const lowCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10);
  lowCam.position.z = 1;

  const waterUniforms = {
    uTime: { value: 0 },
    uResolution: { value: new THREE.Vector2(1, 1) },
  };

  const waterMat = new THREE.ShaderMaterial({ vertexShader, fragmentShader, uniforms: waterUniforms });
  const waterQuad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), waterMat);
  lowScene.add(waterQuad);

  let rt = null;

  // ---- present pass: nearest-filtered upscale to the real canvas --------
  // This, not the shader, is what makes it "pixel per pixel": the geometry
  // is computed once per low-res texel, then blown up with zero filtering,
  // so a window resize costs nothing extra on the expensive shader.
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
    // Size the real canvas to an EXACT integer multiple of the low-res
    // target (lowW*pixelSize, not the raw window size). Nearest-neighbor
    // upscaling by a non-integer ratio (e.g. 1280 -> 426 -> 1280 is a
    // 3.0047x stretch, not 3x) duplicates source columns unevenly and
    // shows up as moire/dot artifacts -- this keeps every art-pixel a
    // clean NxN block, letterboxed and centered by the CSS above.
    renderer.setSize(lowW * pixelSize, lowH * pixelSize, true);
    if (rt) rt.dispose();
    rt = new THREE.WebGLRenderTarget(lowW, lowH, {
      minFilter: THREE.NearestFilter,
      magFilter: THREE.NearestFilter,
      format: THREE.RGBAFormat,
      type: THREE.UnsignedByteType,
    });
    waterUniforms.uResolution.value.set(lowW, lowH);
    presentMat.map = rt.texture;
    presentMat.needsUpdate = true;
    hud.resVal.textContent = `${lowW}×${lowH}`;
  }

  window.addEventListener('resize', resize);
  hud.pixelSize.addEventListener('input', () => {
    pixelSize = parseInt(hud.pixelSize.value, 10);
    hud.pixelSizeVal.textContent = String(pixelSize);
    resize();
  });

  resize();

  const clock = new THREE.Clock();
  let frames = 0, fpsTimer = 0;

  function animate() {
    requestAnimationFrame(animate);
    const dt = Math.min(clock.getDelta(), 0.05);
    waterUniforms.uTime.value += dt;

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
