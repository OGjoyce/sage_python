"""
characters.py — low-poly hard-surface character construction helpers, plus
build_undead_ai(): a mechanical "undead AI announcer" character built from
the numeric blueprint supplied for it (hover base / exposed spine / torso /
asymmetric arms / blocky head / oversized back-mounted sword), assembled
piece by piece into named sub-assemblies.

This is an ORIGINAL character built from the blueprint's own numbers and
hierarchy (dimensions, positions, materials, part list) -- a generic
undead-robot announcer archetype, not a reproduction of any existing
copyrighted character design.

Primitive choices follow the blueprint's own rules: beveled boxes for
armor plates (1-2 bevel segments, explicitly NOT 8-16 -- this is meant to
read as a low-poly hard-surface asset), low-sided cylinders (6-8 sides)
for mechanical discs/vertebrae, and curves-converted-to-mesh for cables
(a handful of bevel segments, not a smooth round tube).
"""

import math
import random
import bpy


# ============================================================ primitives ===

def add_box(name, dims, location, rotation=(0.0, 0.0, 0.0), bevel_width=0.0, bevel_segments=1):
    """A beveled rectangular block -- the basic unit of this character's
    "rectangular mechanical plates" visual language. `dims` is the FULL
    width/height/depth (matches how the blueprint specifies dimensions)."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = rotation
    obj.scale = (dims[0], dims[1], dims[2])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel_width > 0:
        bev = obj.modifiers.new("Bevel", "BEVEL")
        bev.width = bevel_width
        bev.segments = bevel_segments  # low-poly: 1-2, never 8-16
    obj.modifiers.new("Triangulate", "TRIANGULATE")
    return obj


def add_cylinder(name, radius, depth, location, rotation=(0.0, 0.0, 0.0), vertices=8, cap_fill="NGON"):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, depth=depth, vertices=vertices, location=location, end_fill_type=cap_fill
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = rotation
    obj.modifiers.new("Triangulate", "TRIANGULATE")
    return obj


def add_ring(name, outer_r, inner_r, depth, location, vertices=12):
    """A disc with a hole -- used for the hover base's rings. Built as a
    boolean (outer cylinder minus inner cylinder) rather than hand-modeled,
    since that's the low-poly-friendly way to get an exact annulus."""
    outer = add_cylinder(f"{name}_outer", outer_r, depth, location, vertices=vertices)
    inner = add_cylinder(f"{name}_inner", inner_r, depth * 2.2, location, vertices=vertices)
    boolmod = outer.modifiers.new("Hole", "BOOLEAN")
    boolmod.operation = "DIFFERENCE"
    boolmod.object = inner
    boolmod.solver = "EXACT"
    bpy.context.view_layer.objects.active = outer
    bpy.ops.object.modifier_apply(modifier="Hole")
    bpy.context.collection.objects.unlink(inner)
    outer.name = name
    return outer


def add_cable(name, points, radius=0.018, bevel_resolution=1):
    """A hand-placed curve, bevelled into a low-poly tube and converted to
    real mesh -- the blueprint explicitly asks for curves-to-geometry
    rather than a straight extruded box, and a *low* bevel_resolution
    (few sides) to keep it in the "low-poly" register, not a smooth round
    cable."""
    curve_data = bpy.data.curves.new(f"{name}_curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = bevel_resolution
    curve_data.resolution_u = 2
    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for i, p in enumerate(points):
        bp = spline.bezier_points[i]
        bp.co = p
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj.modifiers.new("Triangulate", "TRIANGULATE")
    return obj


def scatter_patches(parts, mats, mat_key, name_prefix, center, spread, count, size_range=(0.07, 0.16), seed=0):
    """Scatters small flat decal boxes around `center` -- used for the
    moss/grime blotches the reference sheet shows mottled across the
    plating. Deterministic (local seeded RNG) so rebuilds are repeatable."""
    rng = random.Random(seed)
    for i in range(count):
        dx = rng.uniform(-spread[0], spread[0])
        dy = rng.uniform(-spread[1], spread[1])
        s = rng.uniform(*size_range)
        loc = (center[0] + dx, center[1] + dy, center[2])
        patch = add_box(f"{name_prefix}_{i}", (s, s * rng.uniform(0.6, 1.3), 0.018), loc,
                         rotation=(0, 0, rng.uniform(-0.6, 0.6)), bevel_width=0.008)
        assign_material(patch, mats[mat_key])
        parts.append(patch)


def join_parts(parts, name):
    """Joins every part into one mesh object.

    bpy.ops.object.join() keeps only the ACTIVE object's modifiers --
    every other part's Bevel/Triangulate modifiers are silently dropped,
    and whatever modifier parts[0] happens to carry (e.g. a torso plate's
    wide 0.10 bevel) then gets re-evaluated against the WHOLE merged mesh,
    sweeping every joined-in rivet/LED/decal edge with that same oversized
    bevel width instead of its own. That inflated triangle counts
    unpredictably as more small parts were added. Baking (applying) each
    part's own modifiers onto its own mesh data *before* joining fixes it:
    every part keeps its own correctly-scaled bevel, and nothing is left
    over to run a second, wrong pass on the combined mesh."""
    if not parts:
        raise ValueError(f"join_parts({name!r}): no parts given")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for p in parts:
        if not p.modifiers:
            continue
        eval_obj = p.evaluated_get(depsgraph)
        baked_mesh = bpy.data.meshes.new_from_object(eval_obj)
        old_mesh = p.data
        p.modifiers.clear()
        p.data = baked_mesh
        bpy.data.meshes.remove(old_mesh)
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    parts[0].name = name
    return parts[0]


def assign_material(obj, mat):
    obj.data.materials.append(mat)
    return obj


# ============================================================= materials ===

def build_undead_ai_materials(cs_materials):
    """Returns a dict of {name: (material, bsdf)}. `cs_materials` is the
    claude_studio.materials module (passed in rather than imported, so
    this file has no import-order dependency on the package __init__)."""
    mats = {}

    mats["METAL"], _ = cs_materials.new_principled_material(
        "MAT_METAL", base_color=_hex(0x56685A), roughness=0.55, metallic=0.6,
    )
    mats["LIGHT_METAL"], _ = cs_materials.new_principled_material(
        "MAT_LIGHT_METAL", base_color=_hex(0x7C927E), roughness=0.45, metallic=0.6,
    )
    mats["DARK_METAL"], _ = cs_materials.new_principled_material(
        "MAT_DARK_METAL", base_color=_hex(0x2E3A2C), roughness=0.65, metallic=0.5,
    )
    mats["CAVITY"], _ = cs_materials.new_principled_material(
        "MAT_CAVITY", base_color=_hex(0x12160F), roughness=0.9, metallic=0.0,
    )
    mats["TEETH"], _ = cs_materials.new_principled_material(
        "MAT_TEETH", base_color=_hex(0xC8D0B8), roughness=0.4, metallic=0.3,
    )
    mats["LIVE_GREEN"], _ = cs_materials.new_principled_material(
        "MAT_LIVE_GREEN", base_color=_hex(0x70FFB0), roughness=0.2,
        emission_color=_hex(0x70FFB0), emission_strength=6.0,
    )
    mats["DARK_GREEN"], _ = cs_materials.new_principled_material(
        "MAT_DARK_GREEN", base_color=_hex(0x44E088), roughness=0.3,
        emission_color=_hex(0x44E088), emission_strength=3.0,
    )
    mats["BEACON"], _ = cs_materials.new_principled_material(
        "MAT_BEACON", base_color=_hex(0xFF3030), roughness=0.2,
        emission_color=(1.0, 0.19, 0.19, 1.0), emission_strength=8.0,
    )

    # MAT_RUST: the user asked explicitly for *rusty oxidized* metal (the
    # blueprint's own MAT_CORROSION is an olive/verdigris green, which
    # reads as oxidized copper, not rust) -- built as a procedural blend
    # between dark metal and an iron-oxide orange, driven by noise, so it
    # reads as patchy rust spreading across metal rather than a flat
    # orange paint job.
    rust = bpy.data.materials.new("MAT_RUST")
    rust.use_nodes = True
    nt = rust.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix_shader = nt.nodes.new("ShaderNodeMixShader")

    metal_bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    metal_bsdf.inputs["Base Color"].default_value = _hex(0x3A3630)
    metal_bsdf.inputs["Roughness"].default_value = 0.5
    metal_bsdf.inputs["Metallic"].default_value = 0.7

    rust_bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    rust_bsdf.inputs["Base Color"].default_value = (0.42, 0.18, 0.06, 1.0)  # iron-oxide orange-brown
    rust_bsdf.inputs["Roughness"].default_value = 0.95
    rust_bsdf.inputs["Metallic"].default_value = 0.0

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 9.0
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.75
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.70
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25

    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mix_shader.inputs["Fac"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], metal_bsdf.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], rust_bsdf.inputs["Normal"])
    nt.links.new(metal_bsdf.outputs["BSDF"], mix_shader.inputs[1])
    nt.links.new(rust_bsdf.outputs["BSDF"], mix_shader.inputs[2])
    nt.links.new(mix_shader.outputs["Shader"], out.inputs["Surface"])
    mats["RUST"] = rust

    # MAT_MOSS: blotchy olive-green growth/grime patches scattered across
    # the armor plating (distinct from MAT_CORROSION/MAT_RUST -- this is a
    # matte biological growth reading, not oxidized metal), matching the
    # reference sheet's mottled green patina across the plates.
    mats["MOSS"], _ = cs_materials.new_principled_material(
        "MAT_MOSS", base_color=_hex(0x3A4A28), roughness=0.95, metallic=0.0,
    )
    # MAT_CLOTH: the frayed strap/ribbon material -- dark worn fabric, used
    # for the antenna's tattered hanging cord and as a strap accent.
    mats["CLOTH"], _ = cs_materials.new_principled_material(
        "MAT_CLOTH", base_color=_hex(0x4A2020), roughness=1.0, metallic=0.0,
    )

    return mats


def _hex(h):
    """RRGGBB int -> linear-space RGBA tuple (alpha=1.0). The blueprint's
    hex codes are sRGB display values; Blender's Base Color/Emission Color
    inputs expect linear, hence the gamma conversion."""
    r = ((h >> 16) & 0xFF) / 255.0
    g = ((h >> 8) & 0xFF) / 255.0
    b = (h & 0xFF) / 255.0

    def to_linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return (to_linear(r), to_linear(g), to_linear(b), 1.0)


# ================================================================ pieces ===
# Dimensions/positions below follow the supplied blueprint (+Y up, +Z
# front, origin at hover-base center) fairly closely, simplified to the
# subset that reads clearly at this scope: hover base, exposed spine,
# torso + chest lights, neck vertebrae, head (eyes/mouth/antenna), one
# clean arm, one damaged/rusty arm with cables, and the back-mounted
# oversized sword with straps.

def build_hover_base(mats):
    """A tapered bell/skirt the character floats on, with a glowing rim at
    the very bottom.

    Earlier version: every tier was a default (unrotated) cylinder, whose
    circular caps face along local Z. That reads fine for a flat decal
    (a rivet, a vertebra disc) meant to be seen face-on from the front,
    but it's wrong for a part that has to read as a round 3D form from
    every camera angle -- from the front each tier appeared as a flat
    circle as intended, but the upper ring (y=0.35) and the core (y=0.0)
    were never actually concentric (they're stacked at different heights,
    not overlapping), so the ring's hole showed straight through to the
    background: a solid disc sitting on top of a visibly separate donut,
    not a continuous flared base. Rotating 90 degrees about X swings each
    cylinder's axis from Z to Y (vertical) instead, so every tier wraps
    around the same central vertical axis like actual stacked cone
    segments, and reads correctly from front/back/side/three-quarter."""
    parts = []
    tiers = [
        ("BaseNeck",  0.22, 0.30, 0.55, mats["METAL"]),
        ("BaseUpper", 0.34, 0.22, 0.34, mats["LIGHT_METAL"]),
        ("BaseMid",   0.46, 0.20, 0.15, mats["METAL"]),
        ("BaseLower", 0.56, 0.18, -0.04, mats["DARK_METAL"]),
    ]
    for name, radius, height, y, mat in tiers:
        tier = add_cylinder(name, radius, height, (0, y, 0), rotation=(math.radians(90), 0, 0), vertices=10)
        assign_material(tier, mat)
        parts.append(tier)

    glow_ring = add_ring("BaseGlowRing", outer_r=0.56, inner_r=0.42, depth=0.05, location=(0, -0.16, 0), vertices=12)
    glow_ring.rotation_euler = (math.radians(90), 0, 0)
    assign_material(glow_ring, mats["DARK_GREEN"])
    parts.append(glow_ring)

    glow_core = add_cylinder("BaseGlowCore", 0.40, 0.03, (0, -0.18, 0),
                              rotation=(math.radians(90), 0, 0), vertices=10)
    assign_material(glow_core, mats["LIVE_GREEN"])
    parts.append(glow_core)

    return join_parts(parts, "HoverBase")


def build_vertebra_stack(mats, name, count, start_y, spacing, radius, height, sides=8):
    parts = []
    for i in range(count):
        mat = mats["LIGHT_METAL"] if i % 2 == 0 else mats["DARK_METAL"]
        v = add_cylinder(f"{name}_{i:02d}", radius, height, (0, start_y + i * spacing, 0), vertices=sides)
        assign_material(v, mat)
        parts.append(v)
    return join_parts(parts, name)


def build_torso(mats):
    parts = []
    main = add_box("TorsoMain", (1.65, 2.05, 0.75), (0, 2.65, 0), bevel_width=0.10, bevel_segments=2)
    assign_material(main, mats["METAL"])
    parts.append(main)

    panel = add_box("TorsoFrontPanel", (0.78, 0.55, 0.08), (0, 2.85, 0.45), bevel_width=0.02, bevel_segments=1)
    assign_material(panel, mats["CAVITY"])
    parts.append(panel)

    indicator_mats = [mats["LIVE_GREEN"], mats["DARK_METAL"], mats["CAVITY"]]
    for i, (dx, mat) in enumerate(zip((-0.22, 0.0, 0.22), indicator_mats)):
        ind = add_box(f"ChestIndicator{i}", (0.12, 0.12, 0.03), (dx, 2.85, 0.50))
        assign_material(ind, mat)
        parts.append(ind)

    for i in range(4):
        strip = add_box(f"ChestStrip{i}", (0.09, 0.045, 0.025), (-0.19 + i * 0.13, 2.65, 0.50))
        assign_material(strip, mats["DARK_GREEN"] if i < 2 else mats["DARK_METAL"])
        parts.append(strip)

    # a row of small terminal-readout LEDs under the chest screen, per the
    # reference sheet's "ChestLights" strip -- the 3 big indicators above
    # read as status lamps, this reads as a data/activity readout
    led_states = [mats["LIVE_GREEN"], mats["DARK_GREEN"], mats["CAVITY"], mats["LIVE_GREEN"],
                  mats["CAVITY"], mats["DARK_GREEN"], mats["CAVITY"]]
    for i, mat in enumerate(led_states):
        led = add_box(f"ChestLed{i}", (0.06, 0.06, 0.02), (-0.33 + i * 0.11, 2.73, 0.50))
        assign_material(led, mat)
        parts.append(led)

    # corner rivets plus a few extra along the top/bottom edges -- the
    # first pass only had the 4 corners, which reads as sparse up close
    for dx in (-0.73, 0.73):
        for dy in (0.90, -0.90):
            rivet = add_cylinder(f"TorsoRivet_{dx:.2f}_{dy:.2f}", 0.035, 0.05,
                                  (dx, 2.65 + dy, 0.40), rotation=(math.radians(90), 0, 0), vertices=6)
            assign_material(rivet, mats["DARK_METAL"])
            parts.append(rivet)
    for dx in (-0.40, 0.0, 0.40):
        for dy in (0.95, -0.95):
            rivet = add_cylinder(f"TorsoRivetEdge_{dx:.2f}_{dy:.2f}", 0.03, 0.045,
                                  (dx, 2.65 + dy, 0.40), rotation=(math.radians(90), 0, 0), vertices=6)
            assign_material(rivet, mats["DARK_METAL"])
            parts.append(rivet)

    # side vent plates -- raised armor detailing on the flanks, giving the
    # silhouette more than one flat slab reads from the side views
    for dx in (-0.80, 0.80):
        vent_frame = add_box(f"TorsoVentFrame_{dx:.2f}", (0.10, 0.65, 0.42), (dx, 2.70, 0.0),
                              bevel_width=0.02, bevel_segments=1)
        assign_material(vent_frame, mats["LIGHT_METAL"] if dx < 0 else mats["DARK_METAL"])
        parts.append(vent_frame)
        for i in range(3):
            louver = add_box(f"TorsoVentLouver_{dx:.2f}_{i}", (0.055, 0.10, 0.44), (dx, 2.45 + i * 0.22, 0.0))
            assign_material(louver, mats["CAVITY"])
            parts.append(louver)

    # a secondary raised shoulder collar plate, following the panel's own
    # beveled-box language rather than a new primitive type
    collar = add_box("TorsoCollar", (1.20, 0.16, 0.78), (0, 3.62, 0.0), bevel_width=0.03, bevel_segments=2)
    assign_material(collar, mats["LIGHT_METAL"])
    parts.append(collar)

    # asymmetric damage per the blueprint: left side clean, right side
    # corroded -- the rusty material carries that asymmetry
    corrosion_r = add_box("TorsoCorrosionR", (0.45, 0.85, 0.035), (0.45, 2.55, 0.40), bevel_width=0.015)
    assign_material(corrosion_r, mats["RUST"])
    parts.append(corrosion_r)
    corrosion_l = add_box("TorsoCorrosionL", (0.18, 0.40, 0.03), (-0.60, 2.95, 0.40), bevel_width=0.01)
    assign_material(corrosion_l, mats["RUST"])
    parts.append(corrosion_l)

    # moss/grime blotches mottled across the plating -- heavier on the
    # damaged (+X) side, light scatter on the clean side, matching the
    # reference sheet's weathered-patina look rather than flat clean metal
    scatter_patches(parts, mats, "MOSS", "TorsoMossR", center=(0.55, 2.55, 0.40),
                     spread=(0.35, 0.55), count=10, size_range=(0.06, 0.15), seed=11)
    scatter_patches(parts, mats, "MOSS", "TorsoMossL", center=(-0.45, 2.70, 0.40),
                     spread=(0.25, 0.45), count=5, size_range=(0.05, 0.11), seed=12)

    return join_parts(parts, "Torso")


def build_head(mats):
    parts = []
    head = add_box("HeadMain", (1.25, 1.10, 0.80), (0, 4.55, 0), bevel_width=0.08, bevel_segments=2)
    assign_material(head, mats["LIGHT_METAL"])
    parts.append(head)

    # left eye: alive, emissive green
    socket_l = add_box("LeftEyeSocket", (0.27, 0.28, 0.05), (-0.28, 4.63, 0.415), bevel_width=0.015)
    assign_material(socket_l, mats["CAVITY"])
    parts.append(socket_l)
    live_l = add_box("LeftEyeLive", (0.17, 0.17, 0.02), (-0.28, 4.63, 0.45))
    assign_material(live_l, mats["LIVE_GREEN"])
    parts.append(live_l)

    # right eye: dead, dark socket with an X
    socket_r = add_box("RightEyeSocket", (0.27, 0.28, 0.05), (0.28, 4.63, 0.415), bevel_width=0.015)
    assign_material(socket_r, mats["CAVITY"])
    parts.append(socket_r)
    for sign in (1, -1):
        bar = add_box(f"DeadEyeX_{sign}", (0.04, 0.24, 0.015), (0.28, 4.63, 0.45),
                       rotation=(0, 0, sign * math.radians(45)))
        assign_material(bar, mats["DARK_METAL"])
        parts.append(bar)

    # mouth: recessed speaker grille + broken teeth
    mouth_cavity = add_box("MouthCavity", (0.75, 0.35, 0.06), (0, 4.28, 0.415), bevel_width=0.015)
    assign_material(mouth_cavity, mats["CAVITY"])
    parts.append(mouth_cavity)

    # an emissive backlight sitting just behind the grille bars -- the
    # reference sheet shows the mouth glowing green through the slats
    # rather than just dark bars over a dark cavity
    mouth_glow = add_box("MouthGlow", (0.64, 0.26, 0.02), (0, 4.28, 0.435))
    assign_material(mouth_glow, mats["DARK_GREEN"])
    parts.append(mouth_glow)

    for i in range(7):
        bar_h = 0.26 + 0.05 * ((i * 37) % 5) / 5.0  # deterministic slight irregularity, no randomness import needed
        bar = add_box(f"MouthBar{i}", (0.045, bar_h, 0.03), (-0.27 + i * 0.09, 4.28, 0.46))
        assign_material(bar, mats["DARK_METAL"])
        parts.append(bar)
    tooth_positions = (-0.30, -0.15, 0.0, 0.15, 0.30)  # center (index 2) intentionally skipped below
    for i, dx in enumerate(tooth_positions):
        if i == 2:
            continue  # one missing tooth, per spec
        tooth_h = 0.10 + 0.03 * (i % 2)
        tooth = add_box(f"Tooth{i}", (0.09, tooth_h, 0.05), (dx, 4.44, 0.46))
        assign_material(tooth, mats["TEETH"])
        parts.append(tooth)

    # 4 corner rivets
    for dx in (-0.55, 0.55):
        for dy in (0.42, -0.42):
            rivet = add_cylinder(f"HeadRivet_{dx:.2f}_{dy:.2f}", 0.035, 0.05,
                                  (dx, 4.55 + dy, 0.40), rotation=(math.radians(90), 0, 0), vertices=6)
            assign_material(rivet, mats["DARK_METAL"])
            parts.append(rivet)

    head_corrosion = add_box("HeadCorrosion", (0.30, 0.45, 0.025), (-0.40, 4.70, 0.42), bevel_width=0.01)
    assign_material(head_corrosion, mats["RUST"])
    parts.append(head_corrosion)

    # antenna + beacon
    stem = add_cylinder("AntennaStem", 0.045, 0.30, (0, 5.08, 0), vertices=6)
    assign_material(stem, mats["DARK_METAL"])
    parts.append(stem)
    for dx, dz in ((-0.05, 0.02), (0.05, -0.015)):
        wire = add_cable(f"AntennaWire_{dx:.2f}", [(dx * 0.4, 4.98, 0), (dx, 5.10, dz), (dx * 0.6, 5.22, 0)], radius=0.009)
        assign_material(wire, mats["DARK_METAL"])
        parts.append(wire)
    beacon = add_box("Beacon", (0.16, 0.10, 0.12), (0, 5.28, 0), bevel_width=0.025, bevel_segments=1)
    assign_material(beacon, mats["BEACON"])
    parts.append(beacon)

    # a frayed cloth/wire ribbon hanging loose off the beacon, drooping
    # down past the antenna stem -- the reference sheet's tattered-flag
    # detail on the antenna
    ribbon = add_cable("AntennaRibbon",
                        [(0.03, 5.22, 0.03), (0.09, 5.00, 0.05), (0.04, 4.75, 0.02), (0.08, 4.58, -0.02)],
                        radius=0.012, bevel_resolution=1)
    assign_material(ribbon, mats["CLOTH"])
    parts.append(ribbon)

    # moss/grime blotches on the head plating -- lighter than the torso's,
    # concentrated toward the damaged (+X, dead-eye) side
    scatter_patches(parts, mats, "MOSS", "HeadMoss", center=(0.50, 4.78, 0.40),
                     spread=(0.08, 0.22), count=4, size_range=(0.05, 0.09), seed=21)

    return join_parts(parts, "Head")


def _add_joint_ring(parts, mats, name, mat_key, location, outer_r=0.16, inner_r=0.115, depth=0.05, vertices=10):
    """A thin ring encircling a vertical limb (rotated so its hole axis
    runs along +Y, the character's "up"), rather than a flat coin stuck to
    the front face -- the reference sheet's glowing collar at each pivot."""
    ring = add_ring(name, outer_r=outer_r, inner_r=inner_r, depth=depth, location=location, vertices=vertices)
    ring.rotation_euler = (math.radians(90), 0, 0)
    assign_material(ring, mats[mat_key])
    parts.append(ring)
    return ring


def _build_arm(mats, side, alive):
    """side: 'L' or 'R'. alive controls material/geometry per the
    blueprint's "left clean, right damaged" asymmetry rule."""
    # bug (now fixed): this compared against the single letter "L", but
    # build_undead_ai() passes side="Left"/"Right" (so this object's own
    # names read "LeftShoulder" etc, not "LShoulder") -- "Left" == "L" is
    # always False, so both arms silently got sign=+1 and were built
    # stacked exactly on top of each other at the same position. Only one
    # arm (whichever one happened to render on top) was ever visible.
    sign = -1 if side == "Left" else 1
    parts = []
    # pushed out a bit further than the torso's own edge (0.825 half-width)
    # so the arm reads as a clearly separate silhouette instead of
    # visually fusing with the torso -- the alive arm's LIGHT_METAL plates
    # share a hue family with the torso's own METAL/LIGHT_METAL, so without
    # a real gap it was disappearing into the body outline
    base_x = sign * 1.04
    metal_mat = mats["LIGHT_METAL"] if alive else mats["RUST"]

    shoulder = add_box(f"{side}Shoulder", (0.42, 0.44, 0.46), (base_x, 3.35, 0), bevel_width=0.04, bevel_segments=2)
    assign_material(shoulder, metal_mat)
    parts.append(shoulder)

    if alive:
        # clean, intact limb: boxy plates with a glowing collar ring
        # wrapped around every pivot (shoulder/elbow/wrist), reading as a
        # powered, functioning joint at each break in the armor
        _add_joint_ring(parts, mats, f"{side}ShoulderRing", "LIVE_GREEN",
                         (base_x * 1.05, 3.10, 0), outer_r=0.19, inner_r=0.145)

        upper = add_box(f"{side}UpperArm", (0.32, 0.56, 0.32), (base_x * 1.16, 2.90, 0), bevel_width=0.035, bevel_segments=2)
        assign_material(upper, metal_mat)
        parts.append(upper)

        elbow = add_cylinder(f"{side}Elbow", 0.12, 0.22, (base_x * 1.16, 2.58, 0),
                              rotation=(math.radians(90), 0, 0), vertices=8)
        assign_material(elbow, mats["DARK_METAL"])
        parts.append(elbow)
        _add_joint_ring(parts, mats, f"{side}ElbowRing", "LIVE_GREEN",
                         (base_x * 1.16, 2.58, 0), outer_r=0.165, inner_r=0.125)

        forearm = add_box(f"{side}Forearm", (0.30, 0.58, 0.30), (base_x * 1.16, 2.22, 0), bevel_width=0.03, bevel_segments=2)
        assign_material(forearm, metal_mat)
        parts.append(forearm)

        _add_joint_ring(parts, mats, f"{side}WristRing", "DARK_GREEN",
                         (base_x * 1.16, 1.95, 0), outer_r=0.145, inner_r=0.105, depth=0.035, vertices=8)

        hand = add_box(f"{side}HandPalm", (0.30, 0.30, 0.22), (base_x * 1.16, 1.76, 0), bevel_width=0.03, bevel_segments=2)
        assign_material(hand, metal_mat)
        parts.append(hand)
        palm_light = add_box(f"{side}PalmLight", (0.08, 0.08, 0.02), (base_x * 1.16, 1.76, 0.12))
        assign_material(palm_light, mats["LIVE_GREEN"])
        parts.append(palm_light)
        # three fingers plus an opposed thumb -- a gripper claw read
        # rather than a flat mitt
        for i, fx in enumerate((-0.11, 0.0, 0.11)):
            finger = add_box(f"{side}Finger{i}", (0.085, 0.27, 0.085), (base_x * 1.16 + fx, 1.49, 0))
            assign_material(finger, metal_mat)
            parts.append(finger)
        thumb = add_box(f"{side}Thumb", (0.09, 0.19, 0.09), (base_x * 1.16 - sign * 0.145, 1.62, 0.10),
                         rotation=(0, 0, sign * math.radians(35)))
        assign_material(thumb, metal_mat)
        parts.append(thumb)
    else:
        # damaged: a visibly thinner skeletal limb -- an exposed dark
        # structural spine runs the whole arm's length with only partial,
        # offset rust-plate armor left covering it, trailing cables the
        # entire way down (not just at the shoulder) ending in a longer,
        # spindlier claw than the alive hand
        spine = add_cylinder(f"{side}ArmSpine", 0.095, 1.55, (base_x * 1.14, 2.45, -0.02), vertices=6)
        assign_material(spine, mats["DARK_METAL"])
        parts.append(spine)

        upper_plate = add_box(f"{side}UpperArmPlate", (0.24, 0.32, 0.24), (base_x * 1.18, 2.95, 0.03),
                               bevel_width=0.025, bevel_segments=1)
        assign_material(upper_plate, mats["RUST"])
        parts.append(upper_plate)

        elbow = add_cylinder(f"{side}Elbow", 0.10, 0.18, (base_x * 1.16, 2.58, 0),
                              rotation=(math.radians(90), 0, 0), vertices=8)
        assign_material(elbow, mats["DARK_METAL"])
        parts.append(elbow)
        joint = add_cylinder(f"{side}DeadJoint", 0.06, 0.018, (base_x * 1.16, 2.58, 0.11), vertices=8)
        assign_material(joint, mats["DARK_METAL"])
        parts.append(joint)
        # one surviving flicker of red circuitry -- a small cracked
        # emissive shard, the only spark of "still half-alive" on this arm
        spark = add_box(f"{side}Spark", (0.05, 0.05, 0.015), (base_x * 1.18, 2.70, 0.14))
        assign_material(spark, mats["BEACON"])
        parts.append(spark)

        forearm_plate = add_box(f"{side}ForearmPlate", (0.24, 0.26, 0.24), (base_x * 1.16, 2.30, -0.05),
                                 bevel_width=0.02, bevel_segments=1)
        assign_material(forearm_plate, mats["RUST"])
        parts.append(forearm_plate)

        claw = add_box(f"{side}ClawPalm", (0.20, 0.22, 0.16), (base_x * 1.14, 1.68, 0), bevel_width=0.018, bevel_segments=2)
        assign_material(claw, mats["DARK_METAL"])
        parts.append(claw)
        for i, (fx, flen) in enumerate(((-0.13, 0.32), (-0.045, 0.37), (0.045, 0.35), (0.13, 0.29))):
            finger = add_box(f"{side}ClawFinger{i}", (0.05, flen, 0.05), (base_x * 1.14 + fx, 1.47 - flen * 0.18, 0.015),
                              rotation=(math.radians(-14 + i * 7), 0, 0))
            assign_material(finger, mats["DARK_METAL"])
            parts.append(finger)

        # cables trail the full length of the arm -- a "dreadlock" bundle
        # from the shoulder, plus a second cluster off the elbow, rather
        # than one batch all starting from the same anchor
        for i in range(5):
            y0 = 3.05 - i * 0.22
            points = [
                (base_x * 1.28, y0, -0.10),
                (base_x * 1.40 + 0.05 * (i % 2), y0 - 0.22, -0.17 - 0.03 * (i % 3)),
                (base_x * 1.22, y0 - 0.46, -0.08),
            ]
            cable = add_cable(f"{side}ShoulderCable{i}", points, radius=0.014)
            assign_material(cable, mats["DARK_METAL"] if i % 2 == 0 else mats["RUST"])
            parts.append(cable)
        for i in range(3):
            y0 = 2.45 - i * 0.30
            points = [
                (base_x * 1.22, y0, -0.08),
                (base_x * 1.32, y0 - 0.20, -0.13),
                (base_x * 1.16, y0 - 0.42, -0.05),
            ]
            cable = add_cable(f"{side}ElbowCable{i}", points, radius=0.012)
            assign_material(cable, mats["RUST"])
            parts.append(cable)

    return join_parts(parts, f"{side}Arm")


def build_sword(mats):
    """A real extruded profile for the blade (not a cube): a 2D polygon
    swept slightly in depth, per the blueprint's explicit instruction not
    to just box-extrude it. Built in its own local space with the blade
    pointing +Y, then rotated/positioned onto the back as a whole."""
    parts = []

    # blade profile: a tapered body with an aggressive angled tip, as a
    # flat polygon extruded a small thickness -- 10 profile points
    profile = [
        (-0.24, 0.0), (0.24, 0.0),          # base
        (0.24, 2.05), (0.10, 2.30),         # right edge up to tip shoulder
        (0.02, 2.50),                       # tip
        (-0.10, 2.30), (-0.24, 2.05),       # left edge back down
    ]
    mesh = bpy.data.meshes.new("Blade_mesh")
    bm_verts_bottom = [(x, y, -0.05) for x, y in profile]
    bm_verts_top = [(x, y, 0.05) for x, y in profile]
    verts = bm_verts_bottom + bm_verts_top
    n = len(profile)
    faces = []
    faces.append(list(range(n)))                          # bottom cap
    faces.append([n + i for i in reversed(range(n))])      # top cap
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])                  # side quad
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    blade = bpy.data.objects.new("Blade", mesh)
    bpy.context.collection.objects.link(blade)
    bev = blade.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.015
    bev.segments = 1
    bev.limit_method = "ANGLE"
    blade.modifiers.new("Triangulate", "TRIANGULATE")
    assign_material(blade, mats["DARK_METAL"])
    parts.append(blade)

    edge = add_box("BladeEdge", (0.07, 2.25, 0.025), (0, 1.15, 0.065), bevel_width=0.008)
    assign_material(edge, mats["LIGHT_METAL"])
    parts.append(edge)

    rust_patch = add_box("BladeRust", (0.20, 0.5, 0.012), (0.0, 0.55, 0.062), bevel_width=0.005)
    assign_material(rust_patch, mats["RUST"])
    parts.append(rust_patch)

    guard = add_box("Guard", (0.75, 0.18, 0.16), (0, 0.0, 0), bevel_width=0.025, bevel_segments=2)
    assign_material(guard, mats["DARK_METAL"])
    parts.append(guard)

    handle = add_cylinder("Handle", 0.10, 0.75, (0, -0.45, 0), vertices=10)
    assign_material(handle, mats["RUST"])
    parts.append(handle)
    for ry in (-0.15, 0.0, 0.15):
        ring = add_cylinder(f"HandleRing_{ry:.2f}", 0.12, 0.04, (0, -0.45 + ry, 0), vertices=10)
        assign_material(ring, mats["DARK_METAL"])
        parts.append(ring)

    pommel = add_box("Pommel", (0.28, 0.18, 0.28), (0, -0.87, 0), bevel_width=0.03, bevel_segments=2)
    assign_material(pommel, mats["DARK_METAL"])
    parts.append(pommel)

    return join_parts(parts, "GreatSword")


# ================================================================== build ==

def build_undead_ai(cs_materials, root_location=(0.0, 0.0, 0.0), name="UndeadAI"):
    """Builds every sub-assembly, positions the sword on the back at its
    blueprint angle with two straps, and returns (root_empty, parts_dict,
    triangle_count). Each sub-assembly stays its own joined object (not
    merged into one giant mesh) so the logical hierarchy the blueprint
    asks for survives as real Blender parenting, inspectable after the
    fact -- "piece by piece, then assembled," not one monolithic blob."""
    mats = build_undead_ai_materials(cs_materials)

    root = bpy.data.objects.new(name + "_ROOT", None)
    bpy.context.collection.objects.link(root)
    root.location = root_location

    hover = build_hover_base(mats)
    spine = build_vertebra_stack(mats, "LowerSpine", count=3, start_y=0.75, spacing=0.28, radius=0.22, height=0.14)
    torso = build_torso(mats)
    neck = build_vertebra_stack(mats, "Neck", count=3, start_y=3.58, spacing=0.20, radius=0.22, height=0.13)
    head = build_head(mats)
    left_arm = _build_arm(mats, "Left", alive=True)
    right_arm = _build_arm(mats, "Right", alive=False)

    sword = build_sword(mats)
    # mount on the back: rotated to the blueprint's ~25 degree diagonal,
    # positioned behind the torso (negative Z), tip extending above the
    # shoulder and the lower blade below the torso
    sword.rotation_euler = (0, 0, math.radians(-25))
    sword.location = (0.35, 2.70, -0.60)

    strap_top = add_box("StrapTop", (0.10, 0.60, 0.04), (0.35, 3.30, -0.50), rotation=(0, 0, math.radians(-15)))
    assign_material(strap_top, mats["CLOTH"])
    strap_bottom = add_box("StrapBottom", (0.10, 0.60, 0.04), (0.15, 2.15, -0.50), rotation=(0, 0, math.radians(-15)))
    assign_material(strap_bottom, mats["CLOTH"])

    buckle_top = add_box("StrapBuckleTop", (0.15, 0.15, 0.05), (0.43, 3.45, -0.48), bevel_width=0.015, bevel_segments=1)
    assign_material(buckle_top, mats["DARK_METAL"])
    buckle_bottom = add_box("StrapBuckleBottom", (0.14, 0.14, 0.05), (0.08, 1.98, -0.48), bevel_width=0.015, bevel_segments=1)
    assign_material(buckle_bottom, mats["DARK_METAL"])

    parts = {
        "HoverBase": hover, "LowerSpine": spine, "Torso": torso, "Neck": neck,
        "Head": head, "LeftArm": left_arm, "RightArm": right_arm,
        "GreatSword": sword, "StrapTop": strap_top, "StrapBottom": strap_bottom,
        "StrapBuckleTop": buckle_top, "StrapBuckleBottom": buckle_bottom,
    }
    for obj in parts.values():
        obj.parent = root

    # triangle count across every sub-assembly, evaluated through modifiers
    depsgraph = bpy.context.evaluated_depsgraph_get()
    total_tris = 0
    for obj in parts.values():
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        total_tris += len(mesh.polygons)
        eval_obj.to_mesh_clear()

    return root, parts, total_tris
