"""Standalone module preview harness.

    blender -b --python _test_module.py -- <module_name> [--az 35] [--el 12]

Imports <module_name>.build(), frames whatever it built with a neutral
3-point rig, and writes _test_<module_name>.png next to this file. Use it to
check silhouette and proportion before wiring a module into scene_main.py.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/user/sage_python/studio")
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import mathutils  # noqa: E402
import claude_studio as cs  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not argv:
    raise SystemExit("usage: blender -b --python _test_module.py -- <module_name>")
module_name = argv[0].replace(".py", "")
az = float(argv[argv.index("--az") + 1]) if "--az" in argv else 35.0
el = float(argv[argv.index("--el") + 1]) if "--el" in argv else 12.0

cs.scene.reset_scene()

mod = __import__(module_name)
built = mod.build()
print(f"TEST: {module_name}.build() returned keys: {sorted(built)}")

# ---- measure what was built (world-space bounds over all mesh objects) ----
depsgraph = bpy.context.evaluated_depsgraph_get()
lo = mathutils.Vector((1e9, 1e9, 1e9))
hi = mathutils.Vector((-1e9, -1e9, -1e9))
tris = 0
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    tris += len(me.loop_triangles)
    for corner in obj.bound_box:
        world = obj.matrix_world @ mathutils.Vector(corner)
        lo = mathutils.Vector((min(lo[i], world[i]) for i in range(3)))
        hi = mathutils.Vector((max(hi[i], world[i]) for i in range(3)))
    ev.to_mesh_clear()

if lo.x > 1e8:
    raise SystemExit("TEST FAILED: build() produced no mesh geometry")

center = (lo + hi) / 2.0
size = hi - lo
radius = max(size.x, size.y, size.z) / 2.0
print(f"TEST: bounds min={tuple(round(v,3) for v in lo)} max={tuple(round(v,3) for v in hi)}")
print(f"TEST: size={tuple(round(v,3) for v in size)}  triangles={tris}")

# ---- neutral 3-point rig: enough to read shape, not the final scene look ----
cs.scene.set_world_gradient(top_color=(0.18, 0.19, 0.22, 1), bottom_color=(0.10, 0.10, 0.12, 1))
dist = radius * 3.4 + 1.0
a, e = math.radians(az), math.radians(el)
cam_pos = (center.x + dist * math.sin(a) * math.cos(e),
           center.y + dist * math.sin(e) + radius * 0.15,
           center.z + dist * math.cos(a) * math.cos(e))
cs.scene.add_camera(location=cam_pos, target=tuple(center), lens=50)
cs.scene.add_sun(location=(center.x + dist, center.y + dist, center.z + dist * 0.6),
                 target=tuple(center), energy=3.0, angle=0.15)
cs.scene.add_area_light((center.x - dist * 0.8, center.y + dist * 0.4, center.z + dist * 0.5),
                        target=tuple(center), energy=radius * radius * 260, size=radius * 2)
cs.scene.add_area_light((center.x, center.y + radius * 0.4, center.z - dist * 0.9),
                        target=tuple(center), energy=radius * radius * 200, size=radius * 2)

out = os.path.join(HERE, f"_test_{module_name}.png")
cs.render.configure_render(filepath=out, samples=24, resolution=(900, 1100),
                           denoise=False, view_transform="Standard")
cs.render.render_still()
print(f"TEST: wrote {out}")
