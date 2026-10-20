"""Render a translated CraftWar model from craftwar_models/ as a contact sheet.

    blender -b --python tools/render_model.py -- --model dire_hero \
            [--anim 0] [--tick 0] [--views 4] [--res 700] [--samples 24]

The models carry their own shading in a vertex-colour emission material (see
claude_studio.craftwar_gl), so the scene needs no lights at all -- what comes
out is what the game's own face-brightness table produces. The camera is framed
from the model's measured bounding box, so this works unchanged for any of the
108 models as they get ported.
"""

import inspect
import math
import os
import sys

sys.path.insert(0, "/home/user/sage_python/studio")

import bpy       # noqa: E402
import mathutils  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(k, d):
    return argv[argv.index(k) + 1] if k in argv else d


MODEL = opt("--model", "dire_hero")
ANIM = int(opt("--anim", "0"))
TICK = float(opt("--tick", "0"))
VIEWS = int(opt("--views", "4"))
RES = int(opt("--res", "700"))
SAMPLES = int(opt("--samples", "24"))
ZOOM = float(opt("--zoom", "1.0"))   # <1 tightens the frame onto the figure
AIMY = float(opt("--aimy", "0.0"))   # lifts the aim point, in bbox heights
AZ0 = float(opt("--az0", "0"))     # starting azimuth. The hero models face +Z,
                                   # but the unit models put their eyes outside
                                   # the -Z face -- they face AWAY from the
                                   # heroes' front, so a roster of units wants
                                   # --az0 180 to be looking at their faces.
IDX = int(opt("--idx", "0"))       # unit/building index, for the *_units and *_bldg modules
OUTDIR = opt("--out", "/home/user/sage_python/studio/renders/craftwar_models")

# ---- empty scene -----------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = False      # this build has no OpenImageDenoise
scene.view_settings.view_transform = "Standard"   # emission == authored sRGB
scene.render.resolution_x = RES
scene.render.resolution_y = RES
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"

# ---- build the model -------------------------------------------------------
mod = __import__("craftwar_models." + MODEL, fromlist=["build"])
# The unit and building modules take an index, as drawXUnit3D/drawXBldg3D do
# in the C++; the hero modules do not. Ask the function rather than keeping a
# list here that would drift as more are ported.
kwargs = dict(tickF=TICK, anim=ANIM)
if "idx" in inspect.signature(mod.build).parameters:
    kwargs["idx"] = IDX
obj = mod.build(**kwargs)
if obj is None:
    print(f"MODEL {MODEL}: index {IDX} is not implemented (the C++ returns false)")
    sys.exit(0)
print(f"MODEL {MODEL}: {len(obj.data.polygons)} faces, {len(obj.data.vertices)} verts")

bpy.context.view_layer.update()
corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
lo = mathutils.Vector((min(c[i] for c in corners) for i in range(3)))
hi = mathutils.Vector((max(c[i] for c in corners) for i in range(3)))
ctr = (lo + hi) * 0.5
span = max((hi - lo).x, (hi - lo).y, (hi - lo).z)
print(f"BOUNDS lo={tuple(round(v,2) for v in lo)} hi={tuple(round(v,2) for v in hi)}")

# ---- camera ----------------------------------------------------------------
cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 50.0
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

ctr.y += (hi - lo).y * AIMY
dist = span * 1.45 * ZOOM
elev = math.radians(16.0)
os.makedirs(OUTDIR, exist_ok=True)
paths = []

for v in range(VIEWS):
    az = math.radians(AZ0 + 360.0 * v / VIEWS)
    # Y-up: azimuth sweeps XZ, elevation lifts Y. View 0 looks at the front (+Z).
    cam.location = (
        ctr.x + dist * math.cos(elev) * math.sin(az),
        ctr.y + dist * math.sin(elev),
        ctr.z + dist * math.cos(elev) * math.cos(az),
    )
    d = ctr - cam.location
    # Blender cameras look down their own -Z with +Y up; build that basis by hand
    # rather than using track_axis, which assumes a Z-up world.
    fwd = -d.normalized()
    up = mathutils.Vector((0, 1, 0))
    right = up.cross(fwd).normalized()
    up2 = fwd.cross(right).normalized()
    cam.matrix_world = mathutils.Matrix((
        (right.x, up2.x, fwd.x, cam.location.x),
        (right.y, up2.y, fwd.y, cam.location.y),
        (right.z, up2.z, fwd.z, cam.location.z),
        (0, 0, 0, 1),
    ))
    p = os.path.join(OUTDIR, f"{MODEL}{IDX}_a{ANIM}_v{v}.png")
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    paths.append(p)
    print(f"VIEW {v} az={int(math.degrees(az))} -> {p}")

print("DONE " + " ".join(paths))
