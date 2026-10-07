# Claude 3D Scene Studio

A Blender-based toolkit for building and rendering 3D scenes headlessly in
this container — `bpy` scripts run via `blender -b`, no display needed
(verified on Mesa `llvmpipe`, i.e. no GPU either). Two things live here:

1. **`claude_studio/`** — a small reusable Python package on top of `bpy`
   (scene/camera/light helpers, material helpers, render config, and an
   image-to-3D pipeline) meant to be imported by scene scripts instead of
   re-deriving the same node-tree/modifier plumbing every time.
2. **`scenes/`** — runnable scene scripts built with that toolkit. Two so
   far: a from-scratch 3D waterfall (the mesh/material counterpart to
   `waterfall/shared/water_core_3d.glsl`'s raymarched version), and a
   generic image→3D-relief pipeline with a triangle-count budget.

**Building or animating a low-poly character?** See
[`docs/CHARACTER_PIPELINE_GUIDE.md`](docs/CHARACTER_PIPELINE_GUIDE.md) --
what reference images/spec to start from, the primitive/material/export
API, the rigid-body animation rig in `claude_studio/rig.py`, and (in its
Pitfalls section) every real bug hit building the one character this
pipeline has shipped so far, written down so the next character doesn't
re-discover them.

```
studio/
  claude_studio/
    scene.py        <- reset_scene, camera, lights, world, frame-driven animation
    materials.py     <- Principled BSDF shortcuts, Voronoi cracked-rock, water
    render.py         <- Cycles/EEVEE config, still + animation rendering
    image_to_3d.py      <- image -> heightfield mesh -> N-triangle decimation
  scenes/
    waterfall_scene.py   <- the flagship demo: cliff/falls/boulders/river, real geometry
    image_to_3d_demo.py   <- image -> 3D relief model, CLI-configurable
  assets/
    make_demo_image.py     <- generates demo_heightmap.png (system python, not bpy)
    demo_heightmap.png
  renders/                   <- script output (gitignored; regenerate on demand)
```

## Setup

```sh
sudo apt-get install blender   # installs Blender 4.0.2 + its dependencies
blender --version               # sanity check
```

That's everything — `bpy` is Blender's bundled Python module, there is no
separate pip install. Two things about *this* container specifically,
worth knowing before you hit them yourself:

- The Ubuntu-packaged Blender is **built without OpenImageDenoise**.
  Leaving Cycles' default denoising on makes `render.render()` raise
  `RuntimeError: Build without OpenImageDenoiser`. `claude_studio.render`
  turns denoising off by default for exactly this reason.
- **Cycles on CPU, not EEVEE**, is the default engine here. Both work
  headlessly (EEVEE falls back to "surfaceless EGL" + llvmpipe software
  rendering and produces a real image), but in this container EEVEE is
  markedly slower than Cycles-CPU at matching quality and depends on a
  software GL stack Cycles doesn't need at all. If you have an actual GPU
  available, flip `device="CPU"` to `"GPU"` in `configure_render()` and
  Cycles will use it.

## Run the demos

```sh
cd /home/user/sage_python   # repo root
blender -b --python studio/scenes/waterfall_scene.py
# -> studio/renders/waterfall_studio.png  (~15s on CPU)

blender -b --python studio/scenes/waterfall_scene.py -- --animate
# -> studio/renders/anim/frame_0001.png .. frame_0048.png (a turntable-ish clip;
#    the water/falls textures are frame-driven, see "animation" below)

blender -b --python studio/scenes/image_to_3d_demo.py -- --triangles 4000
# -> studio/renders/image_to_3d.png

blender -b --python studio/scenes/image_to_3d_demo.py -- \
    --image /path/to/your/photo.png --triangles 8000 --height 1.3 \
    --export /path/to/output.glb
```

(The bare `--` before script flags is load-bearing: it tells Blender
"stop parsing args yourself, hand the rest to the script.")

## The image→3D pipeline, and what "N triangles" actually means here

`claude_studio.image_to_3d.image_to_mesh(image_path, target_triangles=N, ...)`
does, in order:

1. **Heightfield**: a subdivided Grid mesh, UV-displaced along Z by the
   image's luminance (`Displace` modifier, `mid_level=0.0` so black = 0
   height and white = `height_scale`). This is a **relief / lithophane**
   technique — the same idea 3D-printed photo lithophanes use — not
   photogrammetry or a learned depth model. It needs no model weights, no
   internet access, and no GPU, which is why it's what's here; it also
   means a brighter pixel always reads as "more height," never as "closer
   to the camera," so it will not recover the actual 3D shape of an
   object from one photo the way a real depth model or multi-view capture
   would. Good fit: terrain from a grayscale elevation map, coins/
   medallions, "turn this image into relief art." Bad fit: "give me a 3D
   model of the chair in this photo."
2. **Color**: the same source image is UV-mapped onto the mesh's Base
   Color, so it still reads as the original picture, just extruded.
3. **Triangulate**, then **measure** the actual evaluated triangle count
   (through the full modifier stack, not the base grid's raw face count).
4. **Decimate** (Collapse mode) to `target_triangles`. Blender's `ratio`
   parameter is an estimate, not an exact dial, so this does a measure →
   adjust → re-measure correction pass by default — tested here at N=300,
   4000, and 6000 and landed within 0–1 triangles of target every time.
   Collapse decimation is **adaptive**: it spends triangle budget on
   high-curvature regions and strips it from flat ones, so a photo with
   hard black outlines (cartoon line art, high-contrast line drawings)
   will concentrate detail — and look visually spiky/chaotic — right at
   those edges, while smooth photos or grayscale height/elevation maps
   decimate cleanly. This was not a bug I had to fix; it's genuinely what
   quadric-error decimation is supposed to do, and it's worth knowing
   before you feed it a comic panel and wonder why the result looks like
   a sea urchin.
5. **Bake** (`apply_modifiers=True` by default) the modifier stack into
   real mesh data, so what you export or inspect afterward actually has
   the reported triangle count as real geometry, not a live modifier
   stack that only resolves inside this `.blend` session.

`grid_res` (source grid resolution) has to stay comfortably above
`target_triangles` — Decimate only removes detail, it can't invent
detail a lower-resolution source grid never had.

## Animation: how things move without hand-keyframing

`claude_studio.scene.drive_with_frame(socket, channel, "frame * 0.05")`
(and the `add_flow_empty` helper in `waterfall_scene.py` built on the same
idea) attaches a **driver** — an expression evaluated from the current
frame — directly to a node input or object property, instead of placing
keyframes. `waterfall_scene.py` uses this to move the coordinate source
an animated Displace modifier reads from, which is what makes the river's
ripples and the waterfall's turbulence actually flow across a rendered
animation rather than sit static.

## Why a separate studio from the GLSL waterfall project

`waterfall/` (the shader-based 2D and raymarched-3D scenes) and this
studio solve the same "make a waterfall" brief with deliberately different
constraints: the GLSL side is pure math with no mesh/texture assets at
all, runs identically in a browser and a native binary, and renders in
real time. This studio uses Blender's actual geometry/modifier/shading
pipeline — real triangle meshes, Cycles path-traced lighting with true
soft shadows, and (via `image_to_3d.py`) a way to pull a mesh out of an
arbitrary image, none of which a raymarched fragment shader gives you for
free. Different tool, different tradeoffs, same waterfall as the shared
reference scene so the two are easy to compare.
