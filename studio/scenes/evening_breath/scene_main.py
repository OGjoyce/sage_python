"""'Evening Breath' -- assembly, camera, lighting, atmosphere, final render.

    blender -b --python scene_main.py -- [--draft|--preview|--final] [--out PATH]
                                         [--placeholders] [--only env,lys,...]

This file owns everything the per-element modules are forbidden to touch:
scene reset, final placement, the camera and its depth of field, every
light, the world, the volumetric fog and god rays, the floating motes, and
the render settings. See CONVENTIONS.md for the contract the modules build
against.

Quality tiers exist because this renders on 4 CPU cores with no GPU and the
scene is volumetric -- a full-size pass is minutes, not seconds. Iterate on
--draft, confirm on --preview, deliver --final.
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/user/sage_python/studio")
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import mathutils  # noqa: E402
import claude_studio as cs  # noqa: E402
from claude_studio.characters import add_box  # noqa: E402

# --------------------------------------------------------------------------
# args
# --------------------------------------------------------------------------
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def _flag(name):
    return name in argv


def _opt(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


QUALITY = "preview"
for tier in ("draft", "preview", "final"):
    if _flag("--" + tier):
        QUALITY = tier

TIERS = {
    #            resolution     samples  volume step rate  motes
    "draft":   ((720, 405),      24,      4.0,             70),
    "preview": ((1280, 720),     80,      1.5,             160),
    # Sized to what this machine can actually deliver. Measured throughput is
    # ~34k pixel-samples/sec on 4 CPU cores with no GPU, and this Blender is
    # built WITHOUT OpenImageDenoise (verified: the denoiser enum is empty and
    # enabling it raises "Build without OpenImageDenoiser"), so noise has to be
    # bought with samples rather than cleaned up afterwards.
    #
    # The original 2560x1440 at 400 samples works out to ~1.47 billion
    # pixel-samples, i.e. about 12 hours. 1920x1080 at 160 with adaptive
    # sampling lands in roughly 1.5 hours for a far better noise/time trade.
    "final":   ((1920, 1080),    160,     0.8,             260),
}
RESOLUTION, SAMPLES, VOL_STEP, MOTE_COUNT = TIERS[QUALITY]

OUT = _opt("--out", os.path.join(HERE, f"evening_breath_{QUALITY}.png"))
PLACEHOLDERS = _flag("--placeholders")
ONLY = set(_opt("--only", "env,lys,chaos,props").split(","))

# --------------------------------------------------------------------------
# palette (mirrors CONVENTIONS.md -- scene_main needs it for lights/fog)
# --------------------------------------------------------------------------
SUN_ORANGE = (1.000, 0.478, 0.180)
GOLD_LAW = (1.000, 0.816, 0.290)
UNDERLOOM = (1.000, 0.250, 0.055)
TEAL_CRACK = (0.149, 0.898, 0.937)
CRYSTAL = (0.671, 0.788, 0.878)

# --------------------------------------------------------------------------
# placement -- the table from CONVENTIONS.md, in one place
# --------------------------------------------------------------------------
PLACEMENT = {
    "env":   {"module": "env_gate",    "loc": (0.00, 0.0,   0.0), "rot_y": 0.0},
    # Pulled in from the left edge and turned further toward the Chaos Lord:
    # at x=-1.90 her blade ran off the bottom-left of frame and she read as
    # facing the camera rather than facing him, which killed the standoff.
    # +45 deg turns her torso toward him while keeping her face readable.
    "lys":   {"module": "char_lys",    "loc": (-1.40, 0.0,  3.3), "rot_y": 45.0},
    "chaos": {"module": "char_chaos",  "loc": (2.20, 0.0,   1.5), "rot_y": -30.0},
    "props": {"module": "props_fiend", "loc": (0.00, 0.0,   0.0), "rot_y": 0.0},
}
# props_fiend returns two sub-roots that are placed independently
PROP_SUBROOTS = {
    # The head group is now built at true scale in props_fiend (0.505 m
    # skull, ~1.0 m ichor pool), so no shot-level correction is needed; it
    # was briefly scaled here while the module built it several times too
    # large and it read as a crouching animal rather than a severed head.
    "head":  {"loc": (0.10, 0.0, 2.95), "rot_y": -12.0},
    # Moved further left than the (-7.5, -18) in CONVENTIONS.md: from the
    # camera, that line of sight passes through the left arch leg at x=-4.9
    # and the fiend was completely occluded. -11 clears the leg's outer edge
    # while staying inside the island's 22 m back radius.
    # Placed in the clear gap OUTSIDE the left arch leg rather than behind it.
    # The sightline from the camera to this point crosses the arch plane
    # (z=-8.6) at x=-6.5, past the leg's -5.5 outer edge, so it is not
    # occluded; and at 19 m it still sits ~2.8 m inside the left frame edge
    # instead of being clipped by it, which is what killed the two previous
    # placements.
    # Position chosen by ray-casting from the camera to the fiend's legs,
    # torso and shoulder stump against the real assembled geometry, after
    # three hand-estimated placements were all silently occluded. The
    # blocker was never the pillars -- it was the ARCH, whose legs span
    # x +/-8.1 (+/-6.9 after the shot refit), not the +/-3.4 the opening
    # half-width suggested. Every earlier guess sat inside that.
    #
    # This one measures CLEAR at all three heights, sits 2.2 m inside the
    # left frame edge, and lands 24.7 m from the lens -- which is also the
    # "~25 m away" the original art direction asked for.
    #
    # props_fiend yaws the body 60 deg on its own PROP_fiend_body Empty
    # inside the group, because a stride along the view axis is invisible.
    # This rotation ADDS to that, for an effective 75 deg: a three-quarter
    # profile reading both the stride and the nothing-above-the-shoulders
    # silhouette.
    "fiend": {"loc": (-2.80, 0.0, -11.5), "rot_y": 15.0},
}

# Pulled back from the 7.2 m in CONVENTIONS.md: at 35 mm the Chaos Lord's
# 3 m silhouette at x=+2.25 ran off the right edge. 8.8 m gives a 7.2 m-wide
# frame at the figures' depth -- both heroes inside it with air around them,
# and the demon's horns still reaching the top of frame from a low angle.
CAM_POS = (-0.10, 0.95, 8.80)
CAM_TARGET = (0.20, 1.70, 2.10)
LENS = 35.0
FSTOP = 2.8

cs.scene.reset_scene()


# --------------------------------------------------------------------------
# module loading
# --------------------------------------------------------------------------
def _place(root, loc, rot_y, scale=1.0):
    root.location = loc
    root.rotation_euler = (0.0, math.radians(rot_y), 0.0)
    if scale != 1.0:
        root.scale = (scale, scale, scale)


def _placeholder(key, dims, loc, rot_y, color):
    """A featureless proxy block so the shot can be lit and framed before a
    module exists. Same footprint and height as the real element."""
    obj = add_box(f"PLACEHOLDER_{key}", dims, (0, dims[1] / 2.0, 0))
    mat, _ = cs.materials.new_principled_material(
        f"PLACEHOLDER_{key}_mat", base_color=(*color, 1.0), roughness=0.5)
    obj.data.materials.append(mat)
    root = bpy.data.objects.new(f"PLACEHOLDER_{key}_root", None)
    bpy.context.collection.objects.link(root)
    obj.parent = root
    _place(root, loc, rot_y)
    return root


# Gate fit. env_gate builds the arch at its own honest scale -- crown at
# 13.9 m, an 8.5 m opening, standing at z=-12. That does not fit a 35 mm
# frame that also has to hold a 1.85 m woman: to get the crown in shot the
# camera would have to sit ~45 m back, by which point the heroes are specks.
# So the arch group is refit here, as a shot decision rather than a change
# to the module -- slightly squatter and wider than built, pulled forward,
# which keeps it reading as colossal (4x Lys's height) with the crown just
# inside the top of frame and both heroes framed inside the opening.
#
# Applied via a parent Empty at the world origin, NOT by scaling the meshes
# directly: these are joined objects whose origins sit wherever join_parts
# left them, so scaling in place would translate them unpredictably.
GATE_FIT_SCALE = (0.85, 0.52, 0.72)
GATE_FIT_PARTS = ("arch", "glyphs", "shimmer")


def _fit_gate(built):
    pivot = bpy.data.objects.new("ENV_gate_fit", None)
    bpy.context.collection.objects.link(pivot)
    pivot.parent = built["root"]
    for name in GATE_FIT_PARTS:
        obj = built.get(name)
        if obj is None:
            print(f"SCENE: WARNING gate fit: no '{name}' in env_gate output")
            continue
        obj.parent = pivot
    pivot.scale = GATE_FIT_SCALE
    bpy.context.view_layer.update()
    print(f"SCENE: gate refit {GATE_FIT_SCALE} on {GATE_FIT_PARTS}")
    return pivot


PLACEHOLDER_PROXIES = {
    "env":   ((26.0, 0.3, 26.0), CRYSTAL),
    "lys":   ((0.7, 1.85, 0.5), (0.9, 0.88, 0.82)),
    "chaos": ((1.5, 3.00, 1.0), (0.08, 0.09, 0.10)),
}

loaded = {}
missing = []
for key, spec in PLACEMENT.items():
    if key not in ONLY:
        continue
    try:
        if PLACEHOLDERS:
            raise ImportError("placeholders forced")
        mod = __import__(spec["module"])
        built = mod.build()
    except ImportError as exc:
        missing.append((key, str(exc)))
        if key in PLACEHOLDER_PROXIES:
            dims, color = PLACEHOLDER_PROXIES[key]
            loaded[key] = {"root": _placeholder(key, dims, spec["loc"], spec["rot_y"], color)}
        continue

    loaded[key] = built
    if key == "props":
        # the fiend and the severed head live in completely different places
        for sub, sub_spec in PROP_SUBROOTS.items():
            if sub in built:
                _place(built[sub], sub_spec["loc"], sub_spec["rot_y"],
                       sub_spec.get("scale", 1.0))
            else:
                print(f"SCENE: WARNING props_fiend returned no '{sub}' sub-root")
        if not any(s in built for s in PROP_SUBROOTS):
            _place(built["root"], spec["loc"], spec["rot_y"])
    else:
        _place(built["root"], spec["loc"], spec["rot_y"])

    if key == "env":
        _fit_gate(built)

    print(f"SCENE: loaded {spec['module']} -> {sorted(built)}")

for key, why in missing:
    print(f"SCENE: WARNING no module for '{key}' ({why}) -- using proxy/skipping")

bpy.context.view_layer.update()


# --------------------------------------------------------------------------
# world -- the sunset sky the sea of clouds sits in
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# emission grade
#
# The modules author emission at "looks right under a neutral test rig"
# levels -- glyphs at strength 5.5, the Underloom at 13. Under this shot's
# view_transform="Standard" there is no highlight rolloff at all: anything
# over 1.0 clips flat to white. That is why the gold law-glyphs rendered as
# white rectangles rather than gold ones.
#
# Rather than edit four modules (and break their standalone test renders),
# scene_main grades emission down here, the way a colorist would. Values
# just above 1.0 still read as "glowing" because the fog scatters them.
# --------------------------------------------------------------------------
EMISSION_GRADE = 0.26
EMISSION_CEILING = {        # material-name prefix -> max strength after grade
    "ENV_glyph": 1.75,      # gold must stay gold, not clip to white
    "ENV_under": 3.20,      # the Underloom is allowed to be a hot core
    "ENV_shimmer": 0.55,
    "PROP_eye": 2.40,       # the head's last cyan flicker
    "CHAOS_crack": 1.30,    # cold lava veins
    "CHAOS_eye": 2.20,      # authored at 14 -- would clip to flat white
    "CHAOS_filigree": 1.10,
}
# Materials the grade must NOT touch. The aura wisps and embers are authored
# faint on purpose (wisp 0.30); multiplying those by 0.26 puts them at 0.08
# and they disappear from the frame entirely, taking the evil aura's
# geometry component with them.
EMISSION_EXEMPT = ("CHAOS_wisp", "CHAOS_ember")
MODULE_TAGS = ("ENV_", "LYS_", "CHAOS_", "PROP_")


def grade_emission():
    touched = 0
    for mat in bpy.data.materials:
        if not mat.name.startswith(MODULE_TAGS) or not mat.use_nodes:
            continue
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is None or "Emission Strength" not in bsdf.inputs:
            continue
        sock = bsdf.inputs["Emission Strength"]
        if sock.is_linked or sock.default_value <= 0.0:
            continue
        if mat.name.startswith(EMISSION_EXEMPT):
            continue
        val = sock.default_value * EMISSION_GRADE
        for prefix, ceiling in EMISSION_CEILING.items():
            if mat.name.startswith(prefix):
                val = min(val, ceiling)
                break
        sock.default_value = val
        touched += 1
    print(f"SCENE: graded emission on {touched} module materials (x{EMISSION_GRADE})")


def build_sky():
    """A sunset gradient that runs along WORLD Y.

    `cs.scene.set_world_gradient` cannot be used here: it rotates its
    gradient 90 degrees about Y, i.e. it assumes Blender's native Z-up. This
    scene is Y-up (CONVENTIONS.md rule 1), so that helper paints the sky
    front-to-back instead of top-to-bottom -- a flat orange wall behind the
    subjects with no horizon anywhere. This builds the ramp off the view
    ray's Y component instead.
    """
    world = bpy.data.worlds.new("ENV_sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.0

    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    # Range tuned to the 35 mm frame's actual elevation span (~-13 to +19
    # degrees, i.e. Incoming.Y about -0.22..0.33) so the whole ramp is used
    # inside the shot instead of sitting mostly off-frame.
    mr.inputs["From Min"].default_value = -0.22
    mr.inputs["From Max"].default_value = 0.30
    mr.clamp = True

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.620, 0.340, 0.220, 1.0)   # cloud sea in shadow
    cr.elements[1].position = 0.33
    cr.elements[1].color = (1.000, 0.520, 0.190, 1.0)   # the sunset band itself
    e = cr.elements.new(0.46); e.color = (0.880, 0.420, 0.300, 1.0)
    e = cr.elements.new(0.62); e.color = (0.420, 0.270, 0.390, 1.0)  # dusk transition
    e = cr.elements.new(1.00); e.color = (0.055, 0.075, 0.185, 1.0)  # deep blue zenith

    nt.links.new(geo.outputs["Incoming"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return world


grade_emission()
build_sky()


# --------------------------------------------------------------------------
# lighting
#
#   key   : golden rim sun from BEHIND-LEFT -- the heroes read as rim-lit
#           silhouettes, which is the whole look
#   uplight: warm orange from below, bounced up through the crystal floor
#            by the Underloom
#   accents: cyan from the Chaos Lord's side, gold from the gate's glyphs
#   god rays: spots aimed forward through the pillar line, visible only
#            because of the fog below
# --------------------------------------------------------------------------
def _warm(c, mult=1.0):
    return tuple(min(1.0, v * mult) for v in c)


# key: low behind-left, raking across both figures toward camera
key = cs.scene.add_sun(
    location=(-16.0, 5.5, -13.0), target=(0.0, 1.6, 2.2),
    energy=3.2, angle=0.035, name="KEY_sun_gold")
key.data.color = _warm((1.00, 0.70, 0.36))

# a second, tighter warm sun just clipping the top edges -- sharpens the rim
rim = cs.scene.add_sun(
    location=(-9.0, 9.0, -8.0), target=(0.2, 2.1, 2.2),
    energy=2.0, angle=0.012, name="KEY_rim_hot")
rim.data.color = (1.00, 0.84, 0.55)

# Underloom uplight: a wide area light UNDER the floor, facing up. The floor
# is translucent, so this both glows through the glass and uplights the
# figures' undersides.
under = cs.scene.add_area_light(
    (0.0, -8.5, 1.0), target=(0.0, 1.0, 1.5),
    energy=140.0, size=22.0, color=UNDERLOOM, name="UNDERLOOM_uplight")
under.data.shape = "RECTANGLE"
under.data.size = 26.0
under.data.size_y = 26.0

# gate glyph spill -- gold bounce from the archway onto the backs of the heroes
cs.scene.add_area_light(
    (0.0, 3.4, -1.6), target=(0.2, 1.7, 2.3),
    energy=120.0, size=6.0, color=GOLD_LAW, name="GATE_glyph_spill")

# cyan accent from the Chaos Lord's cracks -- motivated practical fill
cs.scene.add_area_light(
    (3.6, 1.7, 2.6), target=(1.6, 1.8, 2.0),
    energy=70.0, size=2.2, color=TEAL_CRACK, name="CHAOS_crack_fill")

# cold fill from camera-right-high so the ivory plate does not go to black
cs.scene.add_area_light(
    (4.5, 4.2, 6.5), target=(-1.2, 1.5, 2.6),
    energy=42.0, size=7.0, color=(0.76, 0.80, 0.93), name="FILL_sky")

# Lys kicker. The key is behind-left by design, so her camera-facing side is
# in shadow -- correct for a rim-lit silhouette, but it left the ivory plate
# and the solar-disc pectoral reading as flat mud. This is a small warm
# source just off the camera axis, low, standing in for sunset bounce off
# the crystal floor in front of her: enough to find the gold engraving
# without killing the rim.
cs.scene.add_area_light(
    (-3.20, 0.85, 6.40), target=(-1.90, 1.25, 3.60),
    energy=300.0, size=2.6, color=(1.00, 0.76, 0.50), name="LYS_kicker")

# Underloom read through the glass: a second, tighter hot source directly
# beneath the two figures, so the orange-red hell-glow actually shows in the
# floor between them instead of washing the whole island evenly.
cs.scene.add_area_light(
    (0.40, -3.20, 2.60), target=(0.40, 0.0, 2.60),
    energy=260.0, size=7.0, color=(1.00, 0.30, 0.10), name="UNDERLOOM_core")

# Lys separation. Her ivory plate was sitting on a warm sky of almost the
# same value, so her silhouette dissolved into the background. A tight warm
# backlight placed behind and above her, aimed back toward the camera,
# draws a hot gold edge down her helmet, pauldron and cloak.
cs.scene.add_area_light(
    (-4.60, 3.10, 0.40), target=(-1.40, 1.30, 3.30),
    energy=240.0, size=2.0, color=(1.00, 0.80, 0.50), name="LYS_backlight")

# The beheaded fiend is the scene's narrative beat and was invisible: dark
# geometry at 16 m against a dark pillar. This rims it from behind-left so
# it reads as a semi-silhouette with a lit edge, per the brief.
cs.scene.add_area_light(
    (-11.00, 4.40, -17.50), target=(-2.80, 1.40, -11.50),
    energy=2600.0, size=4.0, color=(1.00, 0.72, 0.42), name="FIEND_rim")

# A semi-silhouette still has to be legible. Backdrop probing put the fiend
# against bright cloud, but the body itself was reading as an unidentifiable
# dark smudge at 21 m. This is a soft frontal fill, deliberately weak enough
# that the rim above still defines the edge, just strong enough that the
# stride and the missing head are readable.
cs.scene.add_area_light(
    (-6.50, 2.60, -3.00), target=(-2.80, 1.30, -11.50),
    energy=520.0, size=5.0, color=(1.00, 0.80, 0.62), name="FIEND_fill")

# Cold accent on the severed head, so the cyan death-flicker separates it
# from a floor that is lit warm orange from below. Small and close, kept
# under the head's eye level so it grazes rather than floods.
cs.scene.add_area_light(
    (0.10, 0.55, 4.00), target=(0.10, 0.18, 2.95),
    energy=14.0, size=0.7, color=TEAL_CRACK, name="HEAD_flicker_fill")

# god-ray spots: narrow cones from behind the pillar line, pointed at camera.
# These are what the fog turns into visible shafts.
# These sit BEHIND the arch (which, after the shot-level refit, stands at
# about z=-8.6) rather than in front of it. That is the whole trick: a spot
# with nothing between it and the camera lights fog evenly and produces no
# shaft at all, which is why the first placement at z=-9 gave none. From
# back here the arch legs, the keystone mass and the flanking pillars chop
# each cone into distinct beams on their way to the lens.
for i, (sx, sy, sz) in enumerate([(-9.0, 7.5, -17.0), (-3.5, 9.0, -19.0),
                                  (3.5, 8.5, -18.0), (9.0, 7.0, -16.0)]):
    ld = bpy.data.lights.new(f"GODRAY_spot_{i}", type="SPOT")
    ld.energy = 900.0
    ld.color = (1.00, 0.76, 0.42)
    ld.spot_size = math.radians(26.0)
    ld.spot_blend = 0.55
    ld.shadow_soft_size = 0.35
    lo = bpy.data.objects.new(f"GODRAY_spot_{i}", ld)
    lo.location = (sx, sy, sz)
    bpy.context.collection.objects.link(lo)
    cs.scene.look_at(lo, (sx * 0.22, 0.8, 7.0))


# --------------------------------------------------------------------------
# volumetric fog -- a bounded domain, not a world volume. A world volume
# would fog the infinite sky too and cost far more on CPU; a box lets the
# density sit low and thick around the sanctuary floor, which is where the
# god rays and the "sea of clouds" haze need to read.
# --------------------------------------------------------------------------
def build_fog():
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 3.0, -6.0))
    dom = bpy.context.active_object
    dom.name = "ATMO_fog_domain"
    dom.scale = (70.0, 18.0, 70.0)   # y spans -6 .. 12
    dom.display_type = "WIRE"
    dom.visible_shadow = False

    mat = bpy.data.materials.new("ATMO_fog")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")

    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (1.000, 0.640, 0.420, 1.0)
    vol.inputs["Anisotropy"].default_value = 0.42   # forward-scatters into the lens
    vol.inputs["Emission Strength"].default_value = 0.0

    # Density falls off with height: thick haze at floor level, clear above.
    # This MUST read WORLD position (Geometry > Position), not Tex Coord >
    # Object: object coordinates for a scaled cube are still only -0.5..0.5,
    # so a world-scale Map Range on them clamps to one value and the whole
    # domain becomes a flat opaque wash.
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = -1.5
    ramp.inputs["From Max"].default_value = 9.0
    ramp.inputs["To Min"].default_value = 0.0078
    ramp.inputs["To Max"].default_value = 0.0007
    ramp.clamp = True

    # Break the gradient up so the haze is not a flat wash.
    #
    # This is a Math/MULTIPLY, deliberately NOT a ShaderNodeMix: a Mix node
    # with data_type="FLOAT" silently ignores blend_type and always lerps,
    # so "MULTIPLY" there computed lerp(0.009, noise, 0.55) ~= 0.28 -- thirty
    # times the intended density, which renders as a solid orange wall.
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.22
    noise.inputs["Detail"].default_value = 3.0

    noise_gain = nt.nodes.new("ShaderNodeMapRange")   # Fac 0..1 -> 0.55..1.45
    noise_gain.inputs["From Min"].default_value = 0.0
    noise_gain.inputs["From Max"].default_value = 1.0
    noise_gain.inputs["To Min"].default_value = 0.55
    noise_gain.inputs["To Max"].default_value = 1.45
    noise_gain.clamp = True

    dens = nt.nodes.new("ShaderNodeMath")
    dens.operation = "MULTIPLY"

    nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Y"], ramp.inputs["Value"])
    nt.links.new(noise.outputs["Fac"], noise_gain.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], dens.inputs[0])
    nt.links.new(noise_gain.outputs["Result"], dens.inputs[1])
    nt.links.new(dens.outputs["Value"], vol.inputs["Density"])
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])

    dom.data.materials.append(mat)
    return dom


def build_chaos_aura():
    """An "aura maligna" around the Chaos Lord: a dark teal volume clinging
    to his body, densest at his feet and thinning upward, so he looks like
    he is standing in something rather than lit by something.

    Deliberately a separate, bounded volume rather than more scene fog --
    density is ~8x the ambient haze and it has to stop at his silhouette,
    which a global volume cannot do. Density falls off with distance from
    the ellipsoid centre, computed in OBJECT space (-0.5..0.5 across the
    cube regardless of its world scale), which is exactly the coordinate
    space the main fog could NOT use for a world-height gradient but is the
    right one for a normalised radial falloff.
    """
    cx, cz = PLACEMENT["chaos"]["loc"][0], PLACEMENT["chaos"]["loc"][2]
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, 1.45, cz))
    dom = bpy.context.active_object
    dom.name = "ATMO_chaos_aura"
    dom.scale = (3.40, 4.20, 3.40)
    dom.display_type = "WIRE"
    dom.visible_shadow = False

    mat = bpy.data.materials.new("ATMO_chaos_aura")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")

    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.055, 0.180, 0.195, 1.0)
    vol.inputs["Anisotropy"].default_value = 0.25
    vol.inputs["Emission Color"].default_value = (0.047, 0.420, 0.450, 1.0)
    vol.inputs["Emission Strength"].default_value = 0.045

    tex = nt.nodes.new("ShaderNodeTexCoord")
    dist = nt.nodes.new("ShaderNodeVectorMath")
    dist.operation = "LENGTH"
    fall = nt.nodes.new("ShaderNodeMapRange")
    fall.inputs["From Min"].default_value = 0.08
    fall.inputs["From Max"].default_value = 0.50
    fall.inputs["To Min"].default_value = 0.034
    fall.inputs["To Max"].default_value = 0.0
    fall.clamp = True

    # creeping, uneven -- a clean radial gradient reads as a lit sphere
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.4
    noise.inputs["Detail"].default_value = 5.0
    gain = nt.nodes.new("ShaderNodeMapRange")
    gain.inputs["To Min"].default_value = 0.35
    gain.inputs["To Max"].default_value = 1.65
    gain.clamp = True
    dens = nt.nodes.new("ShaderNodeMath")
    dens.operation = "MULTIPLY"

    nt.links.new(tex.outputs["Object"], dist.inputs[0])
    nt.links.new(dist.outputs["Value"], fall.inputs["Value"])
    nt.links.new(noise.outputs["Fac"], gain.inputs["Value"])
    nt.links.new(fall.outputs["Result"], dens.inputs[0])
    nt.links.new(gain.outputs["Result"], dens.inputs[1])
    nt.links.new(dens.outputs["Value"], vol.inputs["Density"])
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    dom.data.materials.append(mat)

    # a low cold source inside the aura so it is lit from within
    cs.scene.add_area_light(
        (cx, 0.55, cz + 0.9), target=(cx, 2.10, cz),
        energy=55.0, size=1.8, color=TEAL_CRACK, name="CHAOS_aura_core")
    return dom


if not _flag("--nofog"):
    build_fog()
    if "chaos" in loaded:
        build_chaos_aura()


# --------------------------------------------------------------------------
# floating light motes -- tiny emissive specks caught in the key light.
# Instanced off one source sphere so 260 of them cost one mesh.
# --------------------------------------------------------------------------
def build_motes(count):
    rng = random.Random(20251015)

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(0, 0, 0))
    src = bpy.context.active_object
    src.name = "ATMO_mote_src"
    bpy.ops.object.shade_smooth()
    mat, _ = cs.materials.new_principled_material(
        "ATMO_mote", base_color=(1.0, 0.85, 0.55, 1.0), roughness=0.4,
        emission_color=(1.0, 0.86, 0.58, 1.0), emission_strength=9.0)
    src.data.materials.append(mat)
    src.hide_render = True

    root = bpy.data.objects.new("ATMO_motes_root", None)
    bpy.context.collection.objects.link(root)

    for i in range(count):
        # Biased toward the lit wedge in front of the gate and kept out of
        # the near-camera metres, where f/2.8 blows a mote into a huge
        # out-of-focus disc that reads as a lens smudge, not an ember.
        x = rng.uniform(-8.0, 8.0)
        y = rng.uniform(0.20, 5.0)
        z = rng.uniform(-11.0, 4.5)
        r = rng.uniform(0.004, 0.016)
        m = bpy.data.objects.new(f"ATMO_mote_{i:03d}", src.data)
        m.location = (x, y, z)
        m.scale = (r, r, r)
        m.parent = root
        bpy.context.collection.objects.link(m)
    return root


build_motes(MOTE_COUNT)


# --------------------------------------------------------------------------
# camera -- 35 mm, f/2.8, low angle, focused between the two heroes
# --------------------------------------------------------------------------
cam = cs.scene.add_camera(location=CAM_POS, target=CAM_TARGET, lens=LENS, name="CAM_main")
focus = mathutils.Vector((0.25, 1.35, 2.25)) - mathutils.Vector(CAM_POS)
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = focus.length
cam.data.dof.aperture_fstop = FSTOP
cam.data.dof.aperture_blades = 7
cam.data.clip_end = 400.0
print(f"SCENE: camera {LENS}mm f/{FSTOP} focus_distance={focus.length:.3f}m")


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------
scene = cs.render.configure_render(
    filepath=OUT, samples=SAMPLES, resolution=RESOLUTION,
    denoise=False, view_transform="Standard")

# volumetrics: step rate trades noise for time, and this is a CPU render
scene.cycles.volume_step_rate = VOL_STEP
scene.cycles.volume_preview_step_rate = VOL_STEP
scene.cycles.volume_max_steps = 256 if QUALITY == "final" else 96
scene.cycles.max_bounces = 8 if QUALITY == "final" else 4
scene.cycles.volume_bounces = 1
scene.cycles.transmission_bounces = 8 if QUALITY == "final" else 4
scene.cycles.use_fast_gi = QUALITY != "final"
scene.cycles.film_exposure = 0.55

# Adaptive sampling concentrates samples on the noisy regions (volumetrics,
# the glossy floor) and stops early on the clean ones. With no denoiser
# available this is the only lever that buys quality without paying linearly
# in time.
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.010 if QUALITY == "final" else 0.025
scene.cycles.adaptive_min_samples = 0          # 0 = let Cycles choose
scene.cycles.use_light_tree = True             # ~14 lights in this shot

# a touch of bloom-substitute: Cycles has no glare node, so the emissive
# glyphs/cracks carry the glow on their own strength values.
scene.render.filter_size = 1.6 if QUALITY == "final" else 1.2

tri = 0
depsgraph = bpy.context.evaluated_depsgraph_get()
for obj in bpy.data.objects:
    if obj.type != "MESH" or obj.hide_render:
        continue
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    tri += len(me.loop_triangles)
    ev.to_mesh_clear()
print(f"SCENE: quality={QUALITY} res={RESOLUTION} samples={SAMPLES} triangles={tri}")
print(f"SCENE: rendering -> {OUT}")

cs.render.render_still()
print(f"SCENE: wrote {OUT}")
