# Character Pipeline Guide: modeling, exporting, and animating

This is the practical guide to the character side of `claude_studio`:
turning reference images + a spec into a low-poly 3D character
(`claude_studio/characters.py`), exporting it (`gl_export.py`), and
animating it (`rig.py` + a scene script like
`scenes/undead_ai_animations.py`). It was written after building one
full character (the "Undead AI" announcer) end to end, including every
real bug hit along the way — this doc exists so the next character (or
the next agent) doesn't re-discover the same ones from scratch.

It's written for two readers at once: a person deciding what to ask for,
and an AI agent doing the building. Section 7 ("Pitfalls") is the single
highest-value section for an agent — read it before writing any rig or
animation code, not after something looks wrong.

---

## 1. What this pipeline actually is

Blender (`bpy`), scripted headlessly (`blender -b --python script.py`),
building **low-poly hard-surface models from primitives** (beveled
boxes, low-sided cylinders, cones, rings, bezier-curve cables) — not
sculpting, not photogrammetry, not an AI mesh generator. Every part is
code: a box here, a cylinder there, a material assigned, joined into a
named sub-assembly. This means two things worth knowing up front:

- **It's good at**: mechanical/robotic characters, hard-surface props,
  anything whose silhouette is built from flat plates, chamfered edges,
  and simple primitives — the "rectangular mechanical blocks" aesthetic.
- **It's bad at**: organic shapes, cloth simulation, anything that
  needs sculpted curvature a handful of beveled boxes can't fake.

Output feeds two renderers:
1. **Blender/Cycles** — the quality renderer, used for stills and
   animation preview frames (what you've been looking at in this
   project).
2. **A native OpenGL 3.3 viewer** (`opengl_viewer/`) — real-time,
   renders through an actual pixel-art pipeline (lit mesh → 256×256
   internal framebuffer → palette quantization → `GL_NEAREST` upscale),
   loads the custom `.uaig` binary mesh format exported by
   `gl_export.py`. This is the "game-ready" end of the pipeline.

---

## 2. Quick start

```sh
# Build + render a character turntable still
blender -b --python studio/scenes/undead_ai_scene.py -- --view three_quarter

# Build + export OBJ and the OpenGL binary (no render)
blender -b --python studio/scenes/undead_ai_scene.py -- \
    --no-render --export-obj studio/exports/x.obj --export-gl studio/exports/x.uaig

# Build the OpenGL viewer once
cd studio/opengl_viewer && mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release && make

# Run it (headless screenshot)
./uaig_viewer --mesh ../../exports/x.uaig --screenshot out.ppm --after 1.5

# Record a 4-second turntable (one process, ~2-3s for 96 frames)
./uaig_viewer --mesh ../../exports/x.uaig --turntable /tmp/frames 96 \
    --turntable-seconds 4.0 --turntable-el 0.3
ffmpeg -y -framerate 24 -i /tmp/frames/frame_%04d.ppm -c:v libx264 -crf 18 out.mp4

# Render one of the five rigged animations (see section 6)
blender -b --python studio/scenes/undead_ai_animations.py -- \
    --anim attack --frames-dir /tmp/attack_frames --samples 32 --res 640 720
ffmpeg -y -framerate 24 -i /tmp/attack_frames/f_%04d.png -c:v libx264 -crf 18 out.mp4
```

The bare `--` before script args is load-bearing: it tells Blender
"stop parsing args yourself, hand the rest to the script."

---

## 3. Inputs needed to build a new character

Two kinds of input get you a good result; one of them alone gets you a
mediocre one.

### 3a. Reference images (the thing that actually anchors accuracy)

What worked well in this project, roughly in order of how much it
helped:

1. **A "parts topology" sheet** — the individual pieces (head, torso,
   one arm, the base, a cable, a rivet) shown ISOLATED and reasonably
   large, each with its own triangle budget and dimensions. This is
   the single most useful reference type: it's the difference between
   guessing a part's shape from a full-body thumbnail and actually
   seeing it. If you only have one reference image to ask for, ask for
   this.
2. **A front/back/left/right/three-quarter turnaround** — catches
   silhouette and proportion mistakes a single angle hides. In this
   project, a real shape bug (the torso needed to taper from wide
   shoulders to a narrow waist, not read as a uniform box) only became
   obvious once it was compared directly against a reference that
   showed the taper clearly.
3. **Close-up crops of specific details** (an eye, the mouth grille, a
   hand) — worth asking for when a general-purpose render still looks
   "off" after the first two; a tight crop settles arguments a full-body
   shot can't.

What did NOT help: asking for more detail without a specific gap to
close. Every real improvement in this project came from a concrete,
specific mismatch against a reference image ("the antenna isn't
visible," "the torso doesn't taper," "the cables blend into the
background") — not from a vague "make it better."

### 3b. The spec / blueprint (numbers, not vibes)

A numeric spec, even an informal one, is what turns "a robot" into a
buildable part list. At minimum:

- **Hierarchy**: named sub-assemblies (Head, Torso, LeftArm, ...) and
  their rough parent/child relationship.
- **Dimensions**: approximate size per part, and an overall scale
  reference (this project used Blender units with +Y up, origin at the
  character's base).
- **Materials**: a short palette, ideally as hex colors with a name per
  swatch (`#56685A Metal`, `#70FFB0 Live Green`, ...) and which parts
  use which. Emissive materials should say so explicitly (and roughly
  how strong — "glowing," "faint," "blinding").
- **A triangle budget**: a target range and a hard max. Without this,
  there's no way to know when "add more detail" has gone too far (see
  the join_parts pitfall in section 7 — triangle counts in this
  pipeline can balloon in ways that aren't obvious from the code alone,
  so a stated budget is also a sanity-check mechanism, not just an
  art-direction choice).
- **Topology rules**, if the look matters: this project's rule was
  "beveled boxes, 1-2 bevel segments, never 8-16; low-sided cylinders
  (6-10 sides); curves-to-mesh for cables, not smooth round tubes" —
  i.e. genuinely low-poly, not "high-poly pretending to be low-poly."

### 3c. For an AI agent building from these inputs

Don't try to match a reference in one shot. The pattern that worked
here, repeatedly:

1. Build a first pass from the spec.
2. Render it — **both** the full character (context) **and** an
   isolated, brightly-lit render of just the part in question (no mood
   lighting, no shadows hiding problems — see section 7's lighting
   pitfall). `cs.scene.set_world_gradient(top_color=(0.35,0.35,0.38,1),
   bottom_color=(0.35,0.35,0.38,1))` with two plain suns is the pattern
   used throughout this project for "just show me the shape."
3. Compare the isolated render against the reference crop for that
   part, specifically. Not "does the whole character look right" —
   that question is too diffuse to act on.
4. Fix exactly the mismatch found, re-render, repeat.

### 3d. Collecting these inputs through the Poly Forge intake page

Typing a spec by hand every time is optional now. **Poly Forge** is a
small web form (a Claude Artifact) for submitting exactly the inputs
3a/3b describe -- a reference image, a free-text prompt, a color
palette, a triangle budget, and toggles for whether the model needs its
own scene/lighting and which output formats it needs -- without opening
an editor. Each submission is stored in the page's own queue (readable
by whoever has the link, backed by the Artifact `db`/`assets`
capabilities), not as files in this repo.

Turning a submission into actual files an agent can run is a separate,
deliberate step: read the queue with the `ArtifactData` tool (`action:
"list"`, `collection: "requests"`) against the page's URL, download the
reference image (if any) from its `imageAssetId` via the `Artifact`
tool's `read` action with that id as `path`, write the spec to a local
JSON file, and run:

```sh
python3 studio/tools/request_scaffold.py path/to/spec.json \
    [--image path/to/reference.<ext>] --out studio
```

This needs no `bpy` -- it's plain Python -- and writes:

- `studio/requests/<slug>/spec.json` and `.../reference.<ext>` (gitignored; regenerate on demand)
- `studio/scenes/<slug>_scene.py` -- a runnable starting-point scene
  script, pre-wired to the submission's triangle budget, one material
  per chosen color, scene/light toggles, and export calls for every
  output format requested (OBJ+MTL, `.uaig`, a rendered PNG still, and a
  turntable-animation comment block). If a reference image was
  submitted it drives `image_to_3d.image_to_mesh()` for an immediate
  relief mesh; otherwise it leaves a `parts = {}` block marked `TODO`
  for hand-built primitives, per sections 3a-4.

Run the scaffolded script (`blender -b --python studio/scenes/<slug>_scene.py`),
then keep iterating on it exactly as section 3c describes -- the
scaffold is a starting point, not a finished model.

---

## 4. Building the model

### 4.1 Primitives (`claude_studio/characters.py`)

| Function | Use for |
|---|---|
| `add_box(name, dims, location, rotation=(0,0,0), bevel_width=0, bevel_segments=1)` | Flat armor plates — the default building block |
| `add_tapered_box(name, bottom_dims, top_dims, height, location, bevel_width=0, bevel_segments=1)` | A frustum — anything that needs to taper (e.g. shoulders-wide-to-waist-narrow). A plain `add_box` CANNOT taper; its scale stretches both ends equally. Built via `bmesh` with `recalc_face_normals` so you never have to hand-derive face winding. |
| `add_cylinder(name, radius, depth, location, rotation=(0,0,0), vertices=8, cap_fill="NGON")` | Discs, pivots, limb segments, hover-base tiers |
| `add_cone(name, radius1, radius2, depth, location, rotation=(0,0,0), vertices=6)` | Tapered details — flame licks, pommel caps (radius2=0 for a true cone) |
| `add_ring(name, outer_r, inner_r, depth, location, vertices=12)` | An annulus (outer cylinder minus inner, via boolean) — glowing collar rings, base rims |
| `add_cable(name, points, radius=0.018, bevel_resolution=1)` | Wires/cables — a bezier curve through `points`, bevelled and converted to mesh. Low `bevel_resolution` (0-1) keeps it low-poly; it will NOT look like a smooth round tube, by design. |
| `scatter_patches(parts, mats, mat_key, name_prefix, center, spread, count, size_range=(0.07,0.16), seed=0)` | Deterministic (seeded) random small decal boxes — moss, grime, weathering |
| `assign_material(obj, mat)` | One-liner: `obj.data.materials.append(mat)` |
| `join_parts(parts, name)` | Merges a list of built objects into one named mesh object. **Read section 7.1 before using this if you plan to animate the result.** |

**Cylinder axis convention** (this bit a lot of parts in this project):
`add_cylinder`/`add_cone`'s default axis is local **Z**. A part meant to
be seen face-on (a rivet, a flat vertebra disc, an eye) wants the
default — it reads as a flat circle from the front. A part that needs
to look like a round 3D form from EVERY angle (a vertical limb segment,
a hover-base tier, a joint collar) needs `rotation=(math.radians(90),
0, 0)` to swing the axis from Z to **Y** (this project's vertical
axis). Getting this wrong doesn't error — it just looks like a flat
rectangle from the side and only resolves into a circle from the front,
which is easy to miss until you render a three-quarter or side view.

### 4.2 Materials (`claude_studio/materials.py`)

```python
mat, bsdf = cs.materials.new_principled_material(
    "MAT_NAME", base_color=_hex(0x70FFB0), roughness=0.2,
    emission_color=_hex(0x70FFB0), emission_strength=6.0,
)
```

`_hex(h)` (in `characters.py`) converts an sRGB hex int to the linear
RGBA tuple Blender's Base Color/Emission Color inputs actually expect —
use it for every hex value from a spec, or colors will look washed out
relative to the spec's swatches.

For a non-uniform material (rust spreading across metal, cracked rock,
etc.), build a small node tree directly — see `MAT_RUST` in
`characters.py` for the pattern (Noise texture → ColorRamp → Mix
Shader between two Principled BSDFs, plus a Bump node off the same
noise for free micro-surface detail).

### 4.3 Assembling and checking the triangle budget

Each sub-assembly is its own function (`build_torso(mats)`,
`build_head(mats)`, ...) that builds a list of parts and ends with
`return join_parts(parts, "Torso")`. `build_undead_ai()` calls each of
these, positions them, and returns `(root, parts_dict, total_triangle_count)`.

**Check the triangle budget as you go, not just at the end** — a
profiling script that builds the character and prints per-assembly
triangle counts (sorted, descending) is the fastest way to find out
which part is eating the budget:

```python
import bpy, claude_studio as cs
cs.scene.reset_scene()
root, parts, tri_count = cs.characters.build_undead_ai(cs.materials)
dg = bpy.context.evaluated_depsgraph_get()
rows = []
for name, obj in parts.items():
    mesh = obj.evaluated_get(dg).to_mesh()
    rows.append((len(mesh.polygons), name))
    obj.evaluated_get(dg).to_mesh_clear()
for t, n in sorted(rows, reverse=True):
    print(f"{t:6d}  {n}")
```

If a count looks implausibly high for what you added, it's very
possibly the `join_parts` modifier-order bug — see 7.1 before spending
time tuning bevel widths down.

---

## 5. Exporting (`claude_studio/gl_export.py`)

```python
cs.gl_export.organize_collections("ROOT_NAME", parts, lights=lights)   # tidy Blender outliner
cs.gl_export.unwrap_parts(parts)                                        # Smart UV Project, only needed for export
stats = cs.gl_export.report_statistics("ROOT_NAME", parts)              # prints Objects/Verts/Tris/Materials
cs.gl_export.export_obj_mtl(parts, "out.obj")                            # standard OBJ+MTL
cs.gl_export.export_gl_binary(parts, "out.uaig")                         # custom binary (below) + out.uaig.json
```

### The `.uaig` binary format

```
magic "UAIG", version:u32
counts: nMaterials, nSubmeshes, nVertices, nIndices (u32 each)
materials[nMaterials]:  name (len-prefixed string), base_color (3×f32), emission (3×f32)
submeshes[nSubmeshes]:  name (len-prefixed string), material_index:u32, index_offset:u32, index_count:u32
vertices[nVertices]:    position (3×f32), normal (3×f32), uv (2×f32)   -- interleaved
indices[nIndices]:      u32
```

Materials are flat-color + emission only (no texture sampling) — matches
this project's "flat-shaded hard-surface plates" look. If a future
character needs textures, that's a real extension to both the export
format and the OpenGL shaders, not a config flag.

---

## 6. Animating a model

### 6.1 The one thing to understand before writing any animation code

**There is no per-vertex skeleton.** `join_parts()` merges every
sub-assembly's pieces into ONE mesh object (e.g. "Torso" is a single
mesh containing the main box, the chest panel, every rivet, every moss
decal...). There is no armature, no bone weights, no per-vertex
skinning anywhere in this pipeline. Animation here means **rigid-object
animation**: whole named parts (Torso, Head, LeftArm, RightArm,
HoverBase) rotate/translate as a single stiff piece around a chosen
pivot. This is enough for broad, readable game-character motion (reach,
swing, lean, nod, spin) — it will never bend a torso or curl a spine
partway along its own length. If a future character needs that, it
needs to be built as a differently-structured, skinned mesh from the
start — that's a bigger redesign, not a rig.py extension.

### 6.2 `claude_studio/rig.py`: turning the flat parts dict into a rig

`build_undead_ai()` parents every part directly to one root empty —
flat, nothing parented to anything else. `cs.rig.build_character_rig(parts)`
re-parents that into a real hierarchy:

```
root
 └─ HoverBase (pivot: own center)
     ├─ LowerSpine
     └─ Torso (pivot: waist)
         ├─ Neck
         ├─ Head (pivot: neck base)
         ├─ LeftArm (pivot: left shoulder)
         ├─ RightArm (pivot: right shoulder)
         └─ GreatSword, StrapTop/Bottom, StrapBuckleTop/Bottom
```

Call it once, right after `build_undead_ai()`, before any posing. It's
safe to call on a static (non-animated) character too — it's been
verified (via a render diff) to not change the resting appearance at
all, only what moves what.

Each pivot is set via a 3D-cursor `origin_set(type='ORIGIN_CURSOR')`
trick (`rig._set_origin`) — moves an object's local origin to a world
point without moving its geometry, so rotating the object afterward
swings around that point instead of its mesh's bounding-box center.
**Read 7.2 before customizing pivot points or adding a new pivoted
part** — there's a specific, non-obvious trap here.

### 6.3 Posing: `keyframe_pose`

```python
from claude_studio.rig import keyframe_pose

keyframe_pose(torso, frame=22, rotation_deg=(0, -14, 0))
keyframe_pose(root, frame=28, location=(0, 0, 2.2))
```

Sets rotation (degrees, XYZ Euler tuple) and/or location at a frame and
inserts keyframes, tagging them with the given interpolation/easing
(default: Bezier, ease-in-out). **The order inside this function is
load-bearing — see 7.3 if writing a similar helper from scratch.**

### 6.4 Making one object track another: the sword-in-hand pattern

Generalizable beyond swords: whenever a rigid object needs to visually
"attach" to a moving part for part of a clip (a held weapon, a thrown
object, anything that isn't permanently parented), bake its transform
frame-by-frame instead of trying to keyframe a changing parent:

```python
from claude_studio.rig import bake_sword_to_hand, RIGHT_CLAW_LOCAL

bake_sword_to_hand(
    sword_obj, right_arm_obj, frame_range=range(0, 109),
    grab_blend=26, grab_start=30, sheathe_start=88, sheathe_blend=92,
    claw_local=RIGHT_CLAW_LOCAL,
)
```

What it does, per frame: outside `[grab_blend, sheathe_blend]`, holds
the object's static rest transform. Inside `[grab_start, sheathe_start]`,
computes the gripping arm's FULL evaluated world matrix (not just one
local rotation axis — correct even when the arm's parent, e.g. the
torso, is itself rotating) via `sword_grip_transform()`, derives the
grip point's world position, and places the object there with a fixed
local grip offset. The short `[grab_blend, grab_start]` and
`[sheathe_start, sheathe_blend]` windows quaternion-slerp between the
static and tracked transforms so the object doesn't pop.

To adapt this for a different "track an object" need: copy
`sword_grip_transform`'s approach (full world matrix of the source
object, a chosen local attach point on it, a chosen local grip point on
the tracked object, matrix composition — not a single-axis shortcut).

### 6.5 Animating materials (color/emission over time)

Material node socket values keyframe like any other property:

```python
bsdf = mats["LIVE_GREEN"].node_tree.nodes.get("Principled BSDF")
ecol = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
estr = bsdf.inputs.get("Emission Strength")

scene.frame_set(frame)          # frame_set FIRST -- see 7.3, same trap applies here
ecol.default_value = (r, g, b, 1.0)
ecol.keyframe_insert(data_path="default_value", frame=frame)
estr.default_value = 40.0
estr.keyframe_insert(data_path="default_value", frame=frame)
```

Remember materials are usually **shared** across many parts (the same
`MAT_LIVE_GREEN` material might be used by the eyes, chest LEDs, and
every arm joint ring) — animating a shared material's color affects
every part using it simultaneously. That's sometimes exactly what you
want (a whole-body flash for a taunt) and sometimes not (isolating just
one indicator needs its own dedicated material, not a shared one).

### 6.6 The five animation templates (`scenes/undead_ai_animations.py`)

One script, `--anim {attack,walk,talk,taunt,ultimate}`, sharing rig
setup / camera / render boilerplate. Use these as starting templates
for a new character's animations — the techniques generalize even
though the specific pivot angles won't:

- **attack**: full-body — a right-arm reach/grab/swing/sheathe arc
  (`bake_sword_to_hand`) layered with a torso windup-twist-and-lean, a
  counter-swinging opposite arm, a head reaction, and a hover-base
  weight-shift tilt. The "full body" part is specifically the torso/
  head/other-arm layering on top of the weapon arm — a single-limb
  swing reads as stiff without it.
- **walk**: for a legless/hovering character, "walking" is translating
  the root while leaning the base counter to the direction of travel
  (inertia read) plus a continuous float bob, with the arms left
  untouched in their rest pose. Demonstrates multiple directions by
  sequencing translate-lean segments (forward, back, strafe) in one
  clip.
- **talk**: a small irregular head nod (not a metronome) plus a
  material Emission Strength keyframed on an uneven double-sine
  (`0.5 + 0.5*sin(t*14)*sin(t*5.3+1)`) for a "talking"/VU-meter pulse
  rather than a clean on/off blink.
- **taunt**: a full continuous rotation (e.g. 360° head spin, linear
  interpolation for constant speed) combined with a material hue cycle
  via `colorsys.hsv_to_rgb` sampled at each of several keyframes,
  written to Emission Color.
- **ultimate**: reach/draw (reusing `bake_sword_to_hand`), raise
  overhead, a "charge" phase (rising emission strength on
  power/corruption materials + a small rapid rotational jitter), then
  a burst — small emissive ico-spheres spawned at a world point derived
  from the held object's evaluated matrix (e.g. the blade tip),
  scaling 0 → peak → 0 over a handful of frames.

### 6.7 Rendering and encoding a clip

```python
scene.frame_start, scene.frame_end = 0, total_frames
cs.render.configure_render(engine="CYCLES", samples=32, resolution=(640, 720),
                            denoise=False, filepath=frames_dir + "/f_",
                            view_transform="Standard")
bpy.ops.render.render(animation=True)
```

32 samples / 640×720 rendered in roughly 5-8s/frame in this container
on CPU-only Cycles — budget accordingly (100 frames ≈ 10-15 minutes).
Run it as a background task; it doesn't need supervision. Then:

```sh
ffmpeg -y -framerate 24 -i frames_dir/f_%04d.png \
    -vf "format=yuv420p" -c:v libx264 -crf 18 -pix_fmt yuv420p out.mp4
```

**Verify the pose logic BEFORE rendering**, every time — build the
character, apply the rig, call the pose function, then `frame_set()` to
a few key frames and print the rotations/locations you expect. This is
minutes of work and would have caught both bugs in section 7 before
burning a 10-minute render on a broken result (which is exactly how
both were actually found in this project).

---

## 7. Pitfalls (read this before writing rig/animation code)

### 7.1 `join_parts` silently applies the WRONG part's modifiers to everything

`bpy.ops.object.join()` keeps only the **active** object's modifiers;
every other joined object's modifiers are discarded. Since
`join_parts(parts, name)` uses `parts[0]` as the active/surviving
object, if `parts[0]` has a Bevel modifier (e.g. a torso's main plate
with a wide 0.10 bevel), that modifier gets re-evaluated against the
**entire merged mesh** after joining — sweeping every other joined-in
rivet, LED, and decal with that same, wrong bevel width instead of
each part's own. This made triangle counts balloon unpredictably: a
handful of small decals could cost thousands of triangles, with no
visible code reason why.

**Fix, already in `join_parts`**: bake (apply) each part's own
modifiers onto its own mesh data before joining, so nothing is left
over to run a second, wrong pass on the combined mesh. If you ever
write a different join helper, carry this forward — it's not
`join_parts`-specific, it's inherent to how `bpy.ops.object.join()`
works.

### 7.2 A joined part's "rest rotation" can be secretly non-zero

Following directly from 7.1's mechanism: `join_parts` keeps `parts[0]`'s
own **object-level transform**, including its `rotation_euler`, on the
resulting combined object. If `parts[0]` happens to have been built
with a non-zero rotation (e.g. a cylinder built with
`rotation=(math.radians(90), 0, 0)` per the axis convention in 4.1),
the resulting joined object's "rest" `rotation_euler` is secretly that
rotation, not `(0, 0, 0)` — even though it looks visually correct at
rest (the geometry was built consistently with that baked-in rotation).

This becomes a real bug the moment anything **keyframes** that object's
rotation, because animation code naturally assumes `rotation_euler=0`
means "rest pose" and writes poses like `(0, 0, tilt_degrees)` — which
**replaces** the hidden rest rotation instead of adding to it, scrambling
the part (and everything parented above it) into a wrong orientation
the instant it gets its first keyframe. In this project, `HoverBase`'s
first part was a tier built with a 90° rotation; animating a simple
6° lean on `HoverBase` turned the whole character sideways.

**Fix, in `rig.build_character_rig`**: `_normalize_rotation(obj)` bakes
each pivoted part's current rotation into its mesh data and resets
`rotation_euler` to identity (`bpy.ops.object.transform_apply(rotation=True)`),
keeping the exact same world appearance but making `rotation_euler=0`
actually mean rest going forward. This runs defensively on every
pivoted part, not just the one that happened to hit it — any future
reordering of which part ends up first in a `join_parts()` call could
introduce the same trap on a different part.

**How to catch this class of bug if it recurs on a new character**:
after building the rig, print each pivoted object's `matrix_basis` (not
`rotation_euler` — that would read 0 correctly even when broken; it's
`matrix_basis`, the actual matrix built from location/rotation/scale,
that reveals a hidden baked rotation as an off-identity 3×3 block)
before trusting any of them to animate correctly.

### 7.3 Keyframing order: move the frame BEFORE writing the value

```python
# WRONG -- looks reasonable, silently keyframes the wrong value after the first key
obj.rotation_euler = new_value
scene.frame_set(frame)
obj.keyframe_insert(data_path="rotation_euler", frame=frame)

# RIGHT
scene.frame_set(frame)
obj.rotation_euler = new_value
obj.keyframe_insert(data_path="rotation_euler", frame=frame)
```

Once an object has even one existing keyframe, `frame_set()` re-evaluates
its f-curves and writes the interpolated result back into the object's
**real** properties (not just an evaluated depsgraph copy) — this is
exactly the mechanism that makes `bake_sword_to_hand` work (reading an
arm's current interpolated pose after moving the frame). But it also
means: if you set the new value FIRST and only THEN call `frame_set()`,
that call throws the new value away and overwrites it with whatever the
curve already held at that frame — so `keyframe_insert()` records the
**old** value again. Every pose after the first one silently collapses
to the same (wrong) value. This is easy to get backwards once (as
happened in this project's first version of `keyframe_pose`) and hard
to notice from the code alone — it only shows up as "the character
isn't moving" or "everything is stuck at the rest pose" once rendered.
**Verify with a numeric frame-dump before rendering** (see 6.7) — it
catches this in seconds instead of a wasted render.

### 7.4 Lighting: a dark, non-emissive part can be real but invisible

Thin or dark-materialed geometry (cables, an antenna stem) can be
completely correct and still read as "missing" in a render if it's
underlit against a dark presentation backdrop, especially at a real-time
renderer's lower resolution/sample count. Before concluding a part
needs to be rebuilt, check it in isolation under flat, bright, neutral
lighting (section 3c's pattern) to confirm the geometry itself is fine
— then fix VISIBILITY specifically: thicken the geometry, lighten/warm
the material (a mid-tone rust reads against black far better than a
near-black "grime" tone), add a dedicated fill light, or raise the
renderer's ambient term. Don't rebuild geometry to fix what's actually
a lighting/material-contrast problem, and don't assume a material
change fixes what's actually a geometry problem — isolate which one
it is first.

### 7.5 A few smaller ones worth knowing

- **View transform**: Blender 4.x defaults to the "AgX" view transform,
  which desaturates/tone-maps colors — a spec's exact hex colors will
  look washed out unless you set
  `scene.view_settings.view_transform = "Standard"`
  (`configure_render(..., view_transform="Standard")` does this).
- **Camera `look_at`**: `mathutils.Vector.to_track_quat('-Z', 'Y')` has
  a real edge-case bug — it can return a quaternion with an unwanted
  90° roll for certain non-axis-aligned horizontal look directions.
  `claude_studio.scene.look_at()` avoids it by building the rotation
  from explicit forward/right/up basis vectors instead; don't swap that
  back to `to_track_quat` for a "simpler" camera helper.
- **Denoising**: this container's Blender build has no OpenImageDenoise
  — leaving Cycles denoising on raises `RuntimeError: Build without
  OpenImageDenoiser`. `configure_render(denoise=False)` is the default
  for exactly this reason; don't flip it on.

---

## 8. Quick checklist for an AI agent asked to build or animate a new character

1. Ask for (or confirm you have) a parts-topology reference sheet, a
   turnaround, a hierarchy/dimensions/materials spec, and a triangle
   budget — section 3. If any are missing, build a reasonable first
   pass anyway and say explicitly what you're guessing at; don't block
   on having every input perfect.
2. Build sub-assemblies as `build_X(mats) -> join_parts(parts, "X")`
   functions, following the primitive table in 4.1. Respect the
   cylinder-axis convention for anything that needs to read as round
   from more than one angle.
3. Profile triangle count per assembly (4.3) before polishing — catch
   a 7.1-style blowup immediately, don't debug it after the fact by
   trimming bevel widths that were never the real cause.
4. Render the full character AND isolated, brightly-lit renders of
   whatever part you're actively working on. Compare against the
   specific reference crop for that part, not the whole sheet.
5. For animation: call `rig.build_character_rig(parts)` once, right
   after building. Before writing any pose, dump `matrix_basis` for
   every pivoted part (7.2) to rule out a hidden rest rotation.
6. Write poses with `keyframe_pose`/manual `frame_set-then-write-then-insert`
   (7.3) — never the reverse order.
7. For anything that needs to visually attach to a moving part for
   only part of a clip (a weapon, a thrown object), use the
   bake-per-frame pattern in 6.4, not Blender parenting.
8. Verify pose values numerically (6.7) before committing to a full
   render. Renders are background tasks — don't block the conversation
   waiting on one; launch it, keep working, encode+send when it
   completes.
