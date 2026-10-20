# CraftWar's 3D models, translated into Blender

CraftWar's 3D models are not assets. They are immediate-mode OpenGL draw calls
in `src/gfx/models3d/*.cpp`, built on the primitives in
`src/platform/native/gl3d_draw.h`, which is WinAPI-bound — so they only ever
ran in the native Windows build.

Every module here is a near line-for-line port of one of those C++ functions,
built on `claude_studio.craftwar_gl`. The C++ numbers are kept exactly as
written; the shim handles the rest. They render, orbit and export anywhere
Blender runs.

## Using them

```python
from craftwar_models import dire_hero
obj = dire_hero.build(tickF=7.0, anim=0)            # faithful, unlit
obj = dire_hero.build(tickF=7.0, anim=0,
                      unlit=False, emit_strength=1.8)  # for a lit scene
```

`tickF` and `anim` mean exactly what they mean in the C++ (anim: 0 idle,
1 walk, 2 attack), so a pose can be reproduced frame-for-frame against the
game. Unit and building modules also take `idx`, as `unitIdx` / `bldgIdx`.
An index the C++ answers with `return false` returns `None` here.

Render one:

```
blender -b --python tools/render_model.py -- --model dire_hero --views 4
blender -b --python tools/render_model.py -- --model dire_units --idx 3 --az0 180
python3 tools/roster.py dire_units 7
```

## Coverage

| Race | Hero | Units | Buildings |
|---|---|---|---|
| Alliance | `alliance_hero` | `alliance_units` 0-6 | `alliance_bldg` 0-6 |
| Horde | `horde_hero` | `horde_units` 0-6 | `horde_bldg` 0-6 |
| Scourge | `scourge_hero` | `scourge_units` 0-6 | `scourge_bldg` 0-6 |
| Elf | `elf_hero` | `elf_units` 0-6 | `elf_bldg` 0-6 |
| Radiant | `radiant_hero` | `radiant_units` 0-6 | `radiant_bldg` 0-6 |
| Dire | `dire_hero` | `dire_units` 0-6 | `dire_bldg` 0-6 |
| AI-Borg | `aiborg_hero` | `aiborg_units` 0 only | `aiborg_bldg` 0-6 |
| Mayan | `mayan_hero` | — | `mayan_bldg` 0 only |

101 models. The gaps are gaps in the C++ too: AI-Borg units 1-6 and every
Mayan unit `return false` ("Coming Soon"), as do Mayan buildings 1-6.

Not here, deliberately: **undead_ai**. Its shell is already authored in Blender
by `tools/build_undead_ai.py` and loaded from `assets/models/*.obj`, so it has
a path off Windows already; re-deriving it from the C++ primitive fallback
would be a step backwards.

## What the translation is faithful to, and where it cannot be

Taken from `gl3d_draw.h` rather than guessed:

- `U = 3.0` world units per sprite unit.
- Axes already match this studio: +Y up, +Z front. Nothing is converted.
- `cube3(cx,cy,cz,s,...)` takes `s` as a **half**-size.
- The game uses **no OpenGL lighting at all**. Every bit of shading is the
  per-face brightness table baked into `box3d` (front ×1.00, back ×0.30, top
  ×1.20, bottom ×0.40, right ×0.85, left ×0.65), so these meshes get an unlit
  emission material driven by a per-face colour attribute. That reproduces the
  in-game look exactly and keeps the result independent of scene lighting.
- `setCol` clamps each channel at 1.0, so `mul` above 1.0 saturates.

Three places where GL has no raytracer equivalent, all handled in the shim:

- **`glLineWidth` is in pixels.** Converted through a pixels-to-world constant
  chosen from how large the models are drawn on screen in the game's viewer.
- **GL_LINES have no thickness.** Drawn as thin square-section bars, split into
  segments when the source sets a colour per vertex (a flame tongue that goes
  white-hot at the base and fades out at the tip).
- **`wisp3` is a camera-facing billboard.** A raytraced frame has no single
  camera-right and nothing reorients per view, so it becomes nested octahedra
  at the fans' own radii and brightnesses — which also survives an orbit, where
  a flat billboard baked into the mesh would turn edge-on and vanish. This is
  the one visible difference: wisps read as faceted orbs rather than soft ones.

And one correction the shim makes on purpose: OpenGL resolves two faces drawn
in the same plane with the depth buffer, and the models lean on that constantly
(rib slabs flush on a torso, a brow rim flush on a skull). A raytracer has no
tie-break, so each quad is nudged out along its own normal by an amount that
grows with draw order — later draws land in front, which is the layering the
C++ means. Far below a pixel at model scale.

## Things the port turned up in the C++

- **Tapered ribbons wind into a bowtie.** The Dire hero's horns and the Elf
  hero's antlers and bow limbs emit their four vertices as near-left,
  near-right, far-left, far-right. `GL_QUADS` draws that as a self-crossing
  quad. The Horde hero's ram horns use proper ring order, so it is not a
  house convention — it is a slip in two files. Corrected in the ports.
- **The Dire units face −Z.** Their glowing eyes sit just outside the −Z face,
  while the Radiant units, the AI-Borg units and every hero put facial detail
  on +Z. Rendered from +Z the whole Dire roster is the backs of their heads,
  lit by the ×0.30 back-face multiplier. Ported as written; `--az0 180` exists
  to look at them.
- **A dead recoil kick.** The Radiant Trebuchet and the Alliance Cannon both
  end their case with a `glTranslatef` that lands after every draw and before
  the matrix is popped, so it moves nothing. Kept verbatim.
- **`aiborg_units.cpp` did not compile.** `drawAiborgBldg3D` uses seven colour
  constants that the Drone rewrite deleted from the file. Fixed in the craftwar
  repo (branch `3d-asset-studio`, commit 6287a55).
