"""The canonical DIRE hero, dropped into the Evening Breath shot.

This is not a re-interpretation: it is CraftWar's own src/gfx/models3d/
dire_hero.cpp, translated draw-call for draw-call into Blender by
claude_studio.craftwar_gl and ported in craftwar_models/dire_hero.py. What
stands in the shot is the model the game draws, at the pose the game would
draw on this tick.

Two shot-level decisions, both here rather than in the port so the port stays
a faithful copy:

- Lit mode. The game shades entirely through its own per-face brightness
  table and uses no lights at all. Those face colours still drive base colour
  here, so the game's read survives, but the surface also takes this shot's
  key, rim and fill -- otherwise a flat emissive cut-out would sit in a
  volumetrically lit scene and look pasted on. The parts the game authored
  bright (socket embers, fel-fire, the heart core) still emit.
- Scale. The model is authored in sprite units, 51.7 of them from sole to
  horn tip. The Chaos Lord it replaces stood 3.015 m, which is the height
  the camera, the arch and Lys were all framed against, so it is matched
  exactly rather than eyeballed.
"""

import math
import sys

import bpy

sys.path.insert(0, "/home/user/sage_python/studio")

from craftwar_models import dire_hero  # noqa: E402

MODEL_TOP = 51.7     # sole (y=0) to horn-tip sheen, in the port's own units
TARGET_H = 3.015     # metres -- the height this shot was framed against
TICK = 7.0           # flame tongues mid-rise, heart core near the top of its pulse
ANIM = 0             # idle


def build():
    # unlit=False: see the module docstring. Threshold 0.42 keeps the fel-dark
    # flesh (0x1A1020) and the deep shadow matte, while the fel-green, the
    # white-hot flame bases and the bone emit light of their own.
    obj = dire_hero.build(tickF=TICK, anim=ANIM, name="DIRE_hero",
                          unlit=False, emit_strength=5.0, emit_threshold=0.42)

    scaler = bpy.data.objects.new("DIRE_scale", None)
    bpy.context.collection.objects.link(scaler)
    s = TARGET_H / MODEL_TOP
    scaler.scale = (s, s, s)
    obj.parent = scaler

    root = bpy.data.objects.new("DIRE_root", None)
    bpy.context.collection.objects.link(root)
    scaler.parent = root

    bpy.context.view_layer.update()
    print(f"DIRE: {len(obj.data.polygons)} faces, scale {s:.5f} -> {TARGET_H} m")
    return {"root": root, "body": obj}
