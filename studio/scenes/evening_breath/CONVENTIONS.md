# "Evening Breath" — shared build contract

Every module in this folder is built independently and assembled by
`scene_main.py`. These rules are what make the separate parts fit together.
Read this fully before writing any geometry.

## Scene summary

Sacred sunset on a floating crystal gate sanctuary above an infinite sea of
clouds. Through the translucent crystal floor, a hellish orange-red glow of
the Underloom far below. Two figures face off in the foreground; a beheaded
demon staggers in the background. Solemn, tense, the silence before the first
move.

## Hard rules

1. **Axis: Y is UP.** This matches `claude_studio`'s own convention
   (`cs.scene.look_at` uses world-up `(0,1,0)`; `characters.py` places heads at
   +Y). X is right, **+Z is toward the camera** (the camera lives at positive Z
   looking toward -Z).
2. **Scale: 1 Blender unit = 1 meter.** Commander Lys is 1.85 m tall. The
   Chaos Lord is 3.0 m tall. Do not deviate.
3. **Build at the origin.** Every module builds its content centered at
   `X=0, Z=0` with its **feet / base at `Y=0`**, **facing +Z** (toward camera).
   `scene_main.py` does all final placement and rotation. Do NOT pre-position
   anything for the final composition.
4. **No cameras, no lights, no world/background, no render settings** in any
   module. `scene_main.py` owns all of those. A module that adds a light will
   break the lighting design.
5. **Do not call `cs.scene.reset_scene()`** inside a module — it wipes
   everything the other modules built. Only `scene_main.py` may reset.

## Module interface

Each file exposes exactly one entry point:

```python
def build():
    """Creates this module's objects. Returns a dict of the named top-level
    objects, e.g. {"gate": obj, "floor": obj}. All objects must be parented
    to a single top-level Empty so scene_main can move the whole group."""
```

Return a dict that always includes a `"root"` key holding that Empty:

```python
root = bpy.data.objects.new("LYS_root", None)   # module-prefixed name
bpy.context.collection.objects.link(root)
# ... parent every object you create to `root` ...
return {"root": root, ...}
```

## Naming — avoid collisions

Prefix **every** object and material name with your module tag:

| Module | file | tag |
|---|---|---|
| Environment / gate / floor / clouds | `env_gate.py` | `ENV_` |
| Commander Lys | `char_lys.py` | `LYS_` |
| Chaos Lord | `char_chaos.py` | `CHAOS_` |
| Fiend + severed head + ichor | `props_fiend.py` | `PROP_` |

Materials too: `cs.materials.new_principled_material("LYS_gold", ...)`.

## Shared palette (use these exact values)

```python
# warm / sacred
SUN_ORANGE   = (1.000, 0.478, 0.180, 1.0)   # #FF7A2E  sunset key
GOLD_LAW     = (1.000, 0.816, 0.290, 1.0)   # #FFD04A  glyphs, gold trim
IVORY        = (0.941, 0.925, 0.871, 1.0)   # #F0ECDE  Lys plate
PALE_CLOAK   = (0.878, 0.855, 0.804, 1.0)   # #E0DACD
# crystal / sanctuary
CRYSTAL      = (0.671, 0.788, 0.878, 1.0)   # #ABC9E0  floor/arch glass
CRYSTAL_DEEP = (0.290, 0.400, 0.510, 1.0)   # #4A6682
# hell below
UNDERLOOM    = (1.000, 0.250, 0.055, 1.0)   # #FF400E  orange-red underglow
# demon
OBSIDIAN     = (0.047, 0.059, 0.071, 1.0)   # #0C0F12  Chaos Lord skin
TEAL_CRACK   = (0.149, 0.898, 0.937, 1.0)   # #26E5EF  glowing cyan cracks
ICHOR        = (0.027, 0.106, 0.110, 1.0)   # #071B1C  black-teal blood
FIEND_RED    = (0.380, 0.180, 0.141, 1.0)   # #612E24  background fiend
SKIN_LYS     = (0.714, 0.510, 0.361, 1.0)   # #B6825C  tan-bronze
```

Emissive parts (glyphs, cracks, eyes, Underloom) must use
`emission_color=` + `emission_strength=` on `new_principled_material`, since
`scene_main.py` renders with `view_transform="Standard"` — emission values
land close to their literal color.

## Geometry approach

`claude_studio.characters` gives you `add_box`, `add_tapered_box`,
`add_cylinder`, `add_cone`, `add_ring`, `join_parts`. Import them directly:

```python
import sys, os
sys.path.insert(0, "/home/user/sage_python/studio")
import claude_studio as cs
from claude_studio.characters import add_box, add_tapered_box, add_cylinder, add_cone
```

`add_box(name, dims, location, rotation=(0,0,0), bevel_width=0, bevel_segments=1)`
— `dims` is the **full** (width, height, depth); `location` is the **center**.

**This is a cinematic, not a game asset** — you have a far bigger polygon
budget than the usual low-poly rules. Use it:

- **Armor / hard surface**: beveled boxes and tapered boxes. `bevel_width`
  of 0.005–0.02 catches rim light and is what makes plate read as metal.
- **Organic forms** (limbs, demon musculature, cloth): build a blocky base,
  then add a **Subdivision Surface** modifier (`levels=2`) plus
  `bpy.ops.object.shade_smooth()` to round it off. This is the single biggest
  quality lever you have — a subdivided, smooth-shaded tapered box reads as a
  limb; a raw box reads as a crate.
- Budget: aim ≤ 120k triangles per character module. Check with
  `len(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh().polygons)`.

Silhouette matters more than surface detail here: the camera is low and the
key light is behind, so shapes read mostly as rim-lit outlines. Spend effort
on **pose, proportion, and silhouette**, not on tiny greebles.

## Final placement (done by scene_main — for your awareness only)

| Element | position (X, Y, Z) | rotation Y |
|---|---|---|
| Gate + floor | (0, 0, 0) | 0° |
| Commander Lys | (-1.75, 0, 2.6) | +22° (angled toward the Chaos Lord) |
| Chaos Lord | (2.25, 0, 1.9) | -28° |
| Severed head | (0.15, 0, 2.2) | — |
| Background fiend | (-7.5, 0, -18.0) | +15° |

Camera: 35 mm, f/2.8, at roughly (0.0, 1.15, 7.2) looking at (0.1, 1.45, 2.2) —
a low angle, focused on the two foreground figures. Anything you build above
~4 m or outside ±12 m on X will likely be out of frame except the gate.

## Testing your module

Render your own module standalone before reporting done:

```sh
blender -b --python /home/user/sage_python/studio/scenes/evening_breath/_test_module.py -- <module_name>
```

`_test_module.py` imports your `build()`, adds a neutral 3-point rig and a
camera framing whatever you built, and writes
`/home/user/sage_python/studio/scenes/evening_breath/_test_<module>.png`.
**Look at that PNG** (read the image file) and iterate until the silhouette
and proportions are right. A module that was never visually checked is not
done.

Keep `samples=24` for test renders — they are only a shape check.
