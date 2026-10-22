"""Save a translated CraftWar model as a .blend (and optionally .glb).

    blender -b --python tools/export_model.py -- --model radiant_hero_valkyrie \
            [--anim 0] [--tick 0] [--glb]

render_model.py answers "what does it look like"; this answers "give me the
file". The .blend lands in exports/ and opens by double-click, with the model
as real mesh data carrying its vertex-colour material -- so it can be lit,
re-shaded, posed or dropped into a Cycles scene like any other asset.
"""

import importlib
import inspect
import os
import sys

sys.path.insert(0, "/home/user/sage_python/studio")

import bpy  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


model = arg("--model", "radiant_hero_valkyrie")
anim = int(arg("--anim", 0))
tick = float(arg("--tick", 0))
want_glb = "--glb" in argv

# Empty scene: whatever build() makes is the whole file.
bpy.ops.wm.read_factory_settings(use_empty=True)

mod = importlib.import_module("craftwar_models." + model)
kw = {}
sig = inspect.signature(mod.build)
if "tickF" in sig.parameters:
    kw["tickF"] = tick
if "anim" in sig.parameters:
    kw["anim"] = anim
obj = mod.build(**kw)

out_dir = "/home/user/sage_python/studio/exports"
os.makedirs(out_dir, exist_ok=True)
blend = os.path.join(out_dir, "%s.blend" % model)
bpy.ops.wm.save_as_mainfile(filepath=blend)
print("BLEND %s" % blend)

if want_glb:
    glb = os.path.join(out_dir, "%s.glb" % model)
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB")
    print("GLB %s" % glb)

name = getattr(obj, "name", model)
mesh = getattr(obj, "data", None)
if mesh is not None:
    print("MESH %s  verts=%d  tris=%d  materials=%d"
          % (name, len(mesh.vertices), len(mesh.loop_triangles) or len(mesh.polygons),
             len(mesh.materials)))
