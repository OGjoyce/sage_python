/**
 * Record a flythrough of the WebGL viewer to a PNG sequence.
 *
 *   node record.js [--frames 780] [--w 1600] [--h 900] [--out DIR] [--port 8711]
 *
 * Frames are captured by DRIVING the camera to an exact normalised t and
 * rendering one frame per screenshot, rather than letting the page animate on
 * wall-clock time. Headless Chromium does not pace requestAnimationFrame at
 * real time under load, so a timing-based capture would produce a juddering,
 * non-uniform move; stepping t deterministically makes every frame exactly
 * 1/N of the path regardless of how long each screenshot actually took.
 */
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };

const FRAMES = parseInt(opt('--frames', '780'), 10);
const W = parseInt(opt('--w', '1600'), 10);
const H = parseInt(opt('--h', '900'), 10);
const PORT = parseInt(opt('--port', '8711'), 10);
const OUT = opt('--out', '/tmp/claude-0/eb_frames');
const ROOT = __dirname;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.glb': 'model/gltf-binary',
  '.wasm': 'application/wasm',
  '.json': 'application/json',
  '.png': 'image/png',
};

function serve() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html';
      const file = path.join(ROOT, rel);
      if (!file.startsWith(ROOT)) { res.writeHead(403).end(); return; }
      fs.readFile(file, (err, buf) => {
        if (err) { res.writeHead(404).end('not found: ' + rel); return; }
        res.writeHead(200, {
          'Content-Type': MIME[path.extname(file)] || 'application/octet-stream',
          'Content-Length': buf.length,
        });
        res.end(buf);
      });
    });
    server.listen(PORT, '127.0.0.1', () => resolve(server));
  });
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  for (const f of fs.readdirSync(OUT)) if (f.endsWith('.png')) fs.unlinkSync(path.join(OUT, f));

  const server = await serve();
  console.log(`REC: serving ${ROOT} on :${PORT}`);

  const browser = await chromium.launch({
    args: [
      '--use-gl=angle',
      '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader',
      '--ignore-gpu-blocklist',
      '--hide-scrollbars',
    ],
  });
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  page.on('console', (m) => { if (m.type() === 'error') console.log('PAGE ERR:', m.text()); });
  page.on('pageerror', (e) => console.log('PAGE EXC:', e.message));

  await page.goto(`http://127.0.0.1:${PORT}/index.html?fast=1`, { waitUntil: 'load', timeout: 120000 });

  // WebGL must actually be alive before we judge the load
  const gl = await page.evaluate(() => {
    const c = document.createElement('canvas');
    const g = c.getContext('webgl2') || c.getContext('webgl');
    return g ? g.getParameter(g.VERSION) + ' | ' + g.getParameter(g.RENDERER) : 'NO WEBGL';
  });
  console.log('REC: webgl =', gl);

  try {
    await page.waitForFunction(() => window.__ready === true || window.__error, null, { timeout: 300000 });
  } catch (e) {
    console.log('REC: timed out waiting for scene');
  }
  const err = await page.evaluate(() => window.__error || null);
  if (err) { console.log('REC: scene load error:', err); await browser.close(); server.close(); process.exit(1); }
  console.log('REC: scene ready');

  await page.waitForTimeout(1500);   // let shadow maps and bloom settle

  const t0 = Date.now();
  for (let i = 0; i < FRAMES; i++) {
    const t = FRAMES === 1 ? 0 : i / (FRAMES - 1);
    await page.evaluate((tt) => window.__cine.setT(tt), t);
    await page.screenshot({
      path: path.join(OUT, `f_${String(i).padStart(5, '0')}.png`),
      animations: 'disabled',
      timeout: 180000,
    });
    if (i % 60 === 0 || i === FRAMES - 1) {
      const el = (Date.now() - t0) / 1000;
      console.log(`REC: frame ${i + 1}/${FRAMES}  ${el.toFixed(0)}s elapsed`);
    }
  }

  await browser.close();
  server.close();
  console.log(`REC: wrote ${FRAMES} frames to ${OUT}`);
})().catch((e) => { console.error('REC FAILED:', e); process.exit(1); });
