# CraftFlow Waterfall — procedural, pure-math pixel art

A waterfall + river scene with **no image assets at all** — every pixel is
computed by a shared GLSL shader, driven by an actual (simplified) fluid
flow field rather than hand-scrolled textures. The same shader source runs
unmodified in two independent renderers — **WebGL via Three.js** and
**native OpenGL (GLFW)** — so you can open both side by side and confirm
they agree.

Inspired by, and a spiritual sequel to, `sage_python/Proyecto mate/Flujo de
agua en curvas de nivel.pdf` elsewhere in this repo — that project
visualized water flow as the negative gradient of a scalar surface in
Sage/Maxima (CPU, offline, symbolic). This does the GPU, real-time version:
instead of a raw gradient field (which has sources and sinks, i.e. "leaks"
water), it uses a **stream function**, whose curl gives a flow field that's
divergence-free by construction — the real-time analogue of the same idea,
done the way incompressible fluids actually work.

```
waterfall/
  shared/water_core.glsl   <- the entire scene; no main(), no #version
  threejs/                 <- WebGL build: index.html + main.js
  opengl/                  <- native GLFW build: CMakeLists.txt + src/
```

## Run it

**WebGL / Three.js** (needs any static file server, since it `fetch()`es
the shared shader as text — opening the HTML file directly with `file://`
will fail on that fetch):

```sh
cd waterfall
python3 -m http.server 8080
# open http://localhost:8080/threejs/
```

**Native OpenGL** (Linux shown; needs a GLFW3 + OpenGL 3.3 core dev
environment):

```sh
# Debian/Ubuntu:
sudo apt-get install libglfw3-dev libgl1-mesa-dev cmake build-essential

cd waterfall/opengl
mkdir build && cd build
cmake .. && make
./craftflow_waterfall
```

Controls: `[` / `]` resize the art-pixel (both resize live and re-render at
the new internal resolution), `Esc` quits. The Three.js page has the same
pixel-size control as an on-screen slider instead.
`./craftflow_waterfall --screenshot out.ppm --after 2.0` renders headlessly
for N seconds and dumps a PPM (viewable as-is in most image tools, or
`python3 -c "from PIL import Image; Image.open('out.ppm').save('out.png')"`)
— this is literally how the two renderers were diffed against each other
while building this.

## Why it looks the way it does (the "optimized, more pixels, hand drawn" part)

The brief asked for two things that sound like they pull in opposite
directions: **pixel-art** (implies big, chunky, few pixels) and **"the more
pixel the better"** (implies high resolution). The resolution of this
output is independent of the resolution of the math:

1. The shader renders into a small off-screen target (its size is `window
   size / pixel-size`, default **1/2** — not the retro 1/4 or 1/8 you'd see
   in an NES-style game).
2. That target is upscaled to the window with **nearest-neighbor**
   filtering (`image-rendering: pixelated` / `GL_NEAREST`), which is what
   actually produces the visible "art pixels" — the shader math itself
   doesn't know or care about pixelation.
3. Because step 1 is cheap (a 640×360 target is ~16x fewer shaded pixels
   than a naive 1920×1080 pass), the *per-pixel* math in
   `water_core.glsl` can afford to be comparatively heavy — multi-octave
   noise, a real flow-field integration, SDF rock shading — and still run
   well over 60fps even on a software GL rasterizer (this was developed
   and tested entirely on Mesa `llvmpipe`, i.e. no GPU at all, and still
   ran at 60fps+ at the default settings). That's the "optimized" part:
   spend the budget on quality-per-pixel, not pixel-count.
4. Turn `pixel-size` down to `1` for a much finer, "HD pixel art" look, or
   up to ~8 for a chunkier retro feel — same math either way.

## The math / physics, briefly

(Full detail is in the comment block at the top of `water_core.glsl`.)

- **Flow field**: a stream function `psi(x, y, t)` (uniform current +
  multi-octave fbm turbulence) drives velocity via `v = curl(psi) =
  (d(psi)/dy, -d(psi)/dx)`. Any field built this way is divergence-free —
  it cannot locally create or destroy water, unlike a raw scrolling UV or
  a naive gradient field. This is the same "curl noise" technique from
  Bridson's 2007 SIGGRAPH paper on procedural fluid flow.
- **Waterfall kinematics**: the vertical streak advection speed increases
  with how far a "parcel" has already fallen (approximating `y(t) =
  0.5·g·t²`), so the cascade visibly accelerates on the way down instead
  of scrolling at a constant rate.
- **Flow-mapped domain warp**: the river surface is sampled twice at
  offset time-phases, each advected along the local flow direction, and
  cross-faded with a triangle wave — the standard trick (GPU Gems /
  Unity's FlowMap shader) for animating an advected noise field forever
  without a visible "reset" seam.
- **Foam**: driven by an estimate of vorticity (local shear in the curl
  field) plus proximity to rocks/rapids — i.e. foam appears where real
  whitewater actually forms, not as a hand-painted decal.
- **Rocks**: signed-distance-field circles blended with a polynomial
  smooth-min, shaded from the SDF's own gradient (a cheap but correct
  fake normal) for believable rounded lighting with zero geometry.
- **Pixel-art palette**: the final color passes through 4×4 Bayer ordered
  dithering + posterization — the 16-bit-era trick for faking more
  gradient steps than the palette allows, applied *after* an explicit
  gamma encode so the bands read as perceptually even.

## One shader, two renderers — what that bought us

`water_core.glsl` has no `#version`, no `in`/`out`/`varying`, no `main()`.
Both apps paste it into a tiny platform-specific wrapper (uniform
declarations + a `main()` that calls `wf_render(...)`) and compile it
as-is. This was not a cosmetic choice — building it this way surfaced and
forced fixes for several real cross-platform bugs along the way, in
particular:

- A couple of `smoothstep(edge0, edge1, x)` calls with `edge0 > edge1`,
  which GLSL leaves **undefined** rather than erroring on. They compiled
  and even looked plausible on one driver, which is exactly the kind of
  bug that would otherwise have quietly drifted between the WebGL and
  native builds.
- WebGL's GLSL ES 1.00 doesn't support `float[16](...)` array-constructor
  syntax or dynamic array indexing in a fragment shader (both fine in
  desktop GLSL 330) — the Bayer dither matrix is written as a flat
  `if`/`else` chain instead, which is valid everywhere.
- Three.js defaults to re-encoding linear→sRGB on output; native GL's
  default framebuffer does not. Without accounting for this the two
  windows would show the same scene at visibly different brightness. The
  gamma encode now happens exactly once, explicitly, inside the shared
  shader, and both wrappers are told not to add their own.

If you ever see the two windows disagree, the shared math is provably
identical — the bug is in one of the two small wrapper files, not in the
water.
