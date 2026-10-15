"""Export the assembled "Evening Breath" scene to a .glb for the web viewer.

    blender -b --python export_gltf.py -- [--out PATH] [--quality preview]

Builds the real scene by importing scene_main with --no-render (so placement,
the gate refit, the emission grade and every light come from the one source of
truth rather than being duplicated here), then strips the parts that cannot
survive the trip to glTF and writes a single self-contained .glb.

What does NOT export, and why:

- The volumetric fog domain and the Chaos Lord's aura are Principled Volume
  materials with nothing connected to Surface. glTF has no volumetric
  scattering, so they would arrive as two enormous black boxes swallowing the
  camera. They are deleted here and re-created in the viewer as exponential
  height fog plus a glow sprite, which is the closest WebGL equivalent.
- Cycles-only shading (transmission depth through the crystal floor, the
  Underloom read through it) degrades to glTF transmission, which the viewer
  approximates.

Blender's glTF exporter maps Principled BSDF emission onto KHR_materials_emissive_strength,
so the graded glyphs, cracks and eyes carry over with their shot-level values.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/user/sage_python/studio")
sys.path.insert(0, HERE)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(HERE, "evening_breath.glb")
QUALITY = argv[argv.index("--quality") + 1] if "--quality" in argv else "preview"

# Hand scene_main the flags it parses, then import it: module-level code
# builds the whole shot and stops short of rendering.
sys.argv = ["blender", "--", "--" + QUALITY, "--no-render"]

import bpy  # noqa: E402
import scene_main  # noqa: E402,F401  (import *is* the build)

print("EXPORT: scene built, preparing for glTF")

# ---- strip what glTF cannot carry -----------------------------------------
STRIP = ("ATMO_fog_domain", "ATMO_chaos_aura", "ATMO_mote_src")
for name in STRIP:
    obj = bpy.data.objects.get(name)
    if obj is not None:
        bpy.data.objects.remove(obj, do_unlink=True)
        print(f"EXPORT: stripped {name}")

# Cameras and lights are re-authored in the viewer (three.js needs its own
# tone mapping and shadow setup), so leave them out of the payload.
for obj in list(bpy.data.objects):
    if obj.type in {"CAMERA", "LIGHT"}:
        bpy.data.objects.remove(obj, do_unlink=True)

bpy.context.view_layer.update()

meshes = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render]
tris = 0
dg = bpy.context.evaluated_depsgraph_get()
for o in meshes:
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    tris += len(me.loop_triangles)
    ev.to_mesh_clear()
print(f"EXPORT: {len(meshes)} mesh objects, {tris} triangles")

# ---- export ---------------------------------------------------------------
for o in bpy.data.objects:
    o.hide_set(False)
    o.hide_viewport = False

bpy.ops.object.select_all(action="SELECT")

kwargs = dict(
    filepath=OUT,
    export_format="GLB",
    export_apply=True,          # bake modifiers (subsurf!) into the mesh
    # CRITICAL: must be False. The exporter's "yup" conversion assumes the
    # Blender scene is Blender-native Z-up and rotates it -90 degrees about X
    # to reach glTF's Y-up. This scene is ALREADY authored Y-up inside a Z-up
    # Blender (CONVENTIONS.md rule 1), so that conversion maps my up-axis Y
    # onto glTF -Z and the whole scene arrives lying on its back -- the
    # viewer's camera path then runs through the inside of the geometry.
    # False exports Blender coordinates verbatim, which for a Y-up scene is
    # already correct glTF.
    export_yup=False,
    export_materials="EXPORT",
    export_cameras=False,
    export_lights=False,
    use_selection=False,
)
try:
    kwargs["export_draco_mesh_compression_enable"] = True
    kwargs["export_draco_mesh_compression_level"] = 6
    bpy.ops.export_scene.gltf(**kwargs)
    print("EXPORT: wrote with Draco compression")
except (TypeError, RuntimeError) as exc:
    print(f"EXPORT: Draco unavailable ({exc}); exporting uncompressed")
    kwargs.pop("export_draco_mesh_compression_enable", None)
    kwargs.pop("export_draco_mesh_compression_level", None)
    bpy.ops.export_scene.gltf(**kwargs)

size = os.path.getsize(OUT) / 1e6
print(f"EXPORT: wrote {OUT} ({size:.1f} MB)")
