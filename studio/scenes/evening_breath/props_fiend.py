"""props_fiend.py — "Evening Breath" story props.

Module tag: PROP_

Builds three separately-placeable groups:

  root   PROP_root          parent Empty for the whole module
  fiend  PROP_fiend_root    the beheaded background Fiend, mid-stagger,
                            with a fountain of black-teal ichor erupting
                            from the severed neck
  head   PROP_head_root     the severed head lying on its side, the ichor
                            pool spreading from it, and the spiderweb
                            cracks radiating in the crystal under it

Both sub-groups are built at the ORIGIN with their base at Y=0 and facing
+Z. scene_main.py does the final placement:

  fiend -> (-7.5, 0, -18.0) rot Y +15 deg
  head  -> ( 0.15, 0,  2.2)

Axis convention (see CONVENTIONS.md): Y is UP, +Z is toward the camera,
1 unit = 1 m. No lights, no camera, no reset_scene.
"""

import math
import os
import random
import sys

sys.path.insert(0, "/home/user/sage_python/studio")

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import claude_studio as cs  # noqa: E402
from claude_studio.characters import (  # noqa: E402
    add_box,
    add_cone,
    add_cylinder,
    add_tapered_box,
    assign_material,
)

# --------------------------------------------------------------- palette ---
TEAL_CRACK = (0.149, 0.898, 0.937, 1.0)
ICHOR = (0.027, 0.106, 0.110, 1.0)
FIEND_RED = (0.380, 0.180, 0.141, 1.0)

TAG = "PROP_"


# ------------------------------------------------------------- utilities ---

def _activate(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def _organic(obj, levels=2):
    """Blocky base -> rounded organic volume. Clears the stock Triangulate
    (a subdivision after triangulation shatters the surface), subdivides,
    then smooth-shades. This is the main quality lever per CONVENTIONS."""
    obj.modifiers.clear()
    sub = obj.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = levels
    sub.render_levels = levels
    _activate(obj)
    bpy.ops.object.shade_smooth()
    return obj


def _sphere(name, radius, location, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(
        radius=radius, subdivisions=subdivisions, location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    _activate(obj)
    bpy.ops.object.shade_smooth()
    return obj


def _seg(name, p0, p1, r0, r1, depth_ratio=1.0, levels=2):
    """A tapered limb/muscle segment running from p0 to p1, radius r0 -> r1.
    Built as a tapered box oriented along the segment, then subdivided and
    smooth-shaded so it reads as flesh rather than as a crate."""
    a, b = Vector(p0), Vector(p1)
    d = b - a
    length = d.length
    obj = add_tapered_box(
        name,
        (2.0 * r0, 2.0 * r0 * depth_ratio),
        (2.0 * r1, 2.0 * r1 * depth_ratio),
        length * 1.06,
        (0.0, 0.0, 0.0),
    )
    obj.rotation_euler = Vector((0.0, 1.0, 0.0)).rotation_difference(
        d.normalized()
    ).to_euler()
    obj.location = (a + b) * 0.5
    _organic(obj, levels=levels)
    return obj


def _loft(name, rings, levels=2):
    """One continuous skinned form through a list of rectangular cross
    sections (cx, cy, cz, half_w, half_h), subdivided smooth. Separate
    overlapping blobs stay visibly separate under a Subsurf — a single
    lofted shell is what makes a skull read as a skull."""
    import bmesh

    bm = bmesh.new()
    loops = []
    for (cx, cy, cz, hw, hh) in rings:
        loops.append([
            bm.verts.new((cx - hw, cy - hh, cz)),
            bm.verts.new((cx + hw, cy - hh, cz)),
            bm.verts.new((cx + hw, cy + hh, cz)),
            bm.verts.new((cx - hw, cy + hh, cz)),
        ])
    for a, b in zip(loops, loops[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new([a[i], a[j], b[j], b[i]])
    bm.faces.new(loops[0])
    bm.faces.new(list(reversed(loops[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    _organic(obj, levels=levels)
    return obj


def _ribbon(name, points, radii, bevel_resolution=2, resolution_u=4):
    """One continuous tapering tube through `points` (per-point radius via
    the spline's own radius attribute). Used for the ichor jets: a chain of
    separate subdivided segments beads up at every joint, a single curve
    does not."""
    rmax = max(radii)
    curve = bpy.data.curves.new(name + "_curve", type="CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = rmax
    curve.bevel_resolution = bevel_resolution
    curve.resolution_u = resolution_u
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for i, p in enumerate(points):
        bp = spline.bezier_points[i]
        bp.co = tuple(p)
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
        bp.radius = max(radii[i] / rmax, 0.01)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    _activate(obj)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.active_object
    obj.name = name
    _activate(obj)
    bpy.ops.object.shade_smooth()
    return obj


def _mat_all(objs, mat):
    for o in objs:
        assign_material(o, mat)


def _parent_to(objs, parent):
    for o in objs:
        o.parent = parent


# ------------------------------------------------------------- materials ---

def _materials():
    m = {}
    m["skin"], bsdf = cs.materials.new_principled_material(
        TAG + "fiend_skin", base_color=FIEND_RED, roughness=0.62, metallic=0.0
    )
    cs.materials.add_noise_bump(m["skin"], bsdf, scale=14.0, detail=5.0, strength=0.22)

    m["skin_head"], bsdf = cs.materials.new_principled_material(
        TAG + "head_skin",
        base_color=(FIEND_RED[0] * 1.08, FIEND_RED[1] * 1.08, FIEND_RED[2] * 1.08, 1.0),
        roughness=0.55,
    )
    cs.materials.add_noise_bump(m["skin_head"], bsdf, scale=34.0, detail=6.0, strength=0.3)

    m["horn"], _ = cs.materials.new_principled_material(
        TAG + "horn", base_color=(0.105, 0.082, 0.075, 1.0), roughness=0.42
    )
    m["bone"], _ = cs.materials.new_principled_material(
        TAG + "bone", base_color=(0.760, 0.722, 0.620, 1.0), roughness=0.38
    )
    m["flesh"], _ = cs.materials.new_principled_material(
        TAG + "stump_flesh", base_color=(0.145, 0.045, 0.040, 1.0), roughness=0.45
    )
    # ichor: black-teal, wet, with a faint teal sheen so the spray still
    # catches light 25 m out in semi-silhouette.
    m["ichor"], _ = cs.materials.new_principled_material(
        TAG + "ichor",
        base_color=ICHOR,
        roughness=0.21,
        emission_color=(TEAL_CRACK[0] * 0.10, TEAL_CRACK[1] * 0.10, TEAL_CRACK[2] * 0.10, 1.0),
        emission_strength=1.0,
    )
    m["ichor_hot"], _ = cs.materials.new_principled_material(
        TAG + "ichor_hot",
        base_color=(0.035, 0.130, 0.140, 1.0),
        roughness=0.12,
        emission_color=(TEAL_CRACK[0] * 0.22, TEAL_CRACK[1] * 0.22, TEAL_CRACK[2] * 0.22, 1.0),
        emission_strength=2.0,
    )
    m["ichor_pool"], bsdf = cs.materials.new_principled_material(
        TAG + "ichor_pool",
        base_color=ICHOR,
        roughness=0.13,
        emission_color=(TEAL_CRACK[0] * 0.06, TEAL_CRACK[1] * 0.06, TEAL_CRACK[2] * 0.06, 1.0),
        emission_strength=0.5,
    )
    cs.materials.add_noise_bump(m["ichor_pool"], bsdf, scale=22.0, detail=4.0, strength=0.06)

    m["eye"], _ = cs.materials.new_principled_material(
        TAG + "eye_white", base_color=(0.895, 0.885, 0.845, 1.0), roughness=0.22
    )
    m["eye_flicker"], _ = cs.materials.new_principled_material(
        TAG + "eye_flicker",
        base_color=(0.30, 0.78, 0.82, 1.0),
        roughness=0.15,
        emission_color=TEAL_CRACK,
        emission_strength=2.0,
    )
    m["crack"], _ = cs.materials.new_principled_material(
        TAG + "crack",
        base_color=(0.022, 0.048, 0.056, 1.0),
        roughness=0.62,
        emission_color=(TEAL_CRACK[0] * 0.06, TEAL_CRACK[1] * 0.06, TEAL_CRACK[2] * 0.06, 1.0),
        emission_strength=0.5,
    )
    return m


# =========================================================== the fiend ====
# ~2.1 m tall if it were upright (noticeably smaller than the 3 m Chaos
# Lord). Headless, caught mid-stumble: torso pitched hard forward over a
# planted trailing leg, the other leg swinging through in the air, right
# arm flung out reaching, left arm flailing up and back.

P_HIP = (0.02, 0.90, 0.02)
P_BELLY = (0.10, 1.14, 0.26)
P_CHEST = (0.20, 1.39, 0.62)
R_SH = (0.47, 1.32, 0.57)
L_SH = (-0.07, 1.37, 0.60)
STUMP_A = (0.21, 1.37, 0.60)
STUMP_B = (0.27, 1.53, 0.72)

R_EL = (0.70, 1.18, 0.98)
R_WR = (0.86, 1.08, 1.42)
R_HAND = (0.915, 1.045, 1.555)
L_EL = (-0.54, 1.20, 0.22)
L_WR = (-0.80, 1.40, -0.16)
L_HAND = (-0.89, 1.50, -0.30)

RL_HIP = (0.19, 0.88, 0.04)
RL_KNEE = (0.44, 0.60, 0.50)
RL_ANK = (0.58, 0.40, 0.84)
LL_HIP = (-0.16, 0.88, 0.00)
LL_KNEE = (-0.34, 0.46, -0.22)
LL_ANK = (-0.42, 0.12, -0.58)

# ichor fountain ballistics (used for both the arc and the droplets)
FOUNT_V = Vector((0.62, 2.40, 0.30))
FOUNT_G = 2.60
FOUNT_T = 2.28


def _fount_point(t):
    o = Vector(STUMP_B)
    p = o + FOUNT_V * t
    p.y -= 0.5 * FOUNT_G * t * t
    # a little sideways wobble so the arc is not a flat textbook parabola
    p.x += 0.05 * math.sin(t * 2.2)
    p.z += 0.06 * math.sin(t * 1.5)
    return p


def _build_fiend(mats, parent):
    parts_skin = []
    parts_other = []

    # ---- torso: pelvis -> belly -> chest, pitched forward ----
    parts_skin.append(_seg(TAG + "fiend_pelvis", (0.0, 0.76, -0.04), P_HIP, 0.175, 0.160, 0.80))
    parts_skin.append(_seg(TAG + "fiend_abdomen", P_HIP, P_BELLY, 0.160, 0.150, 0.82))
    parts_skin.append(_seg(TAG + "fiend_chest", P_BELLY, P_CHEST, 0.155, 0.200, 0.78))
    # ribcage / back mass
    parts_skin.append(_sphere(TAG + "fiend_ribs", 0.195, (0.18, 1.30, 0.52)))
    parts_skin[-1].scale = (1.05, 0.78, 0.85)
    parts_skin.append(_sphere(TAG + "fiend_backhump", 0.140, (0.12, 1.32, 0.34)))
    # shoulder yoke across the top of the chest
    parts_skin.append(_seg(TAG + "fiend_clavicle", L_SH, R_SH, 0.115, 0.125, 0.85, levels=1))

    # ---- severed neck: a short ragged stub, no head ----
    parts_skin.append(_seg(TAG + "fiend_neck", STUMP_A, STUMP_B, 0.105, 0.088, 1.0))
    # open wound cavity
    rng = random.Random(7)
    up = (Vector(STUMP_B) - Vector(STUMP_A)).normalized()
    cav = _sphere(TAG + "fiend_stump_cavity", 0.080, tuple(Vector(STUMP_B) - up * 0.012))
    cav.scale = (1.0, 0.45, 1.0)
    parts_other.append((cav, mats["flesh"]))
    # ragged torn edge: spurs of flesh flicked outward around the rim
    side = Vector((1.0, 0.0, 0.0)).cross(up).normalized()
    side2 = up.cross(side).normalized()
    for i in range(9):
        a = i / 9.0 * math.tau
        rad = 0.082 + rng.uniform(-0.008, 0.012)
        base = Vector(STUMP_B) + (side * math.cos(a) + side2 * math.sin(a)) * rad
        tip = base + up * rng.uniform(0.035, 0.085) + (
            side * math.cos(a) + side2 * math.sin(a)
        ) * rng.uniform(0.01, 0.045)
        spur = _seg(TAG + f"fiend_stump_rag_{i}", base, tip, 0.024, 0.006, 1.0, levels=1)
        parts_other.append((spur, mats["flesh"]))

    # ---- arms: right flung forward reaching, left flailing back ----
    parts_skin.append(_sphere(TAG + "fiend_delt_r", 0.115, R_SH))
    parts_skin.append(_seg(TAG + "fiend_uarm_r", R_SH, R_EL, 0.098, 0.076))
    parts_skin.append(_sphere(TAG + "fiend_elbow_r", 0.072, R_EL, subdivisions=1))
    parts_skin.append(_seg(TAG + "fiend_farm_r", R_EL, R_WR, 0.078, 0.052))
    parts_skin.append(_seg(TAG + "fiend_hand_r", R_WR, R_HAND, 0.056, 0.042, 0.65))
    hdir = (Vector(R_HAND) - Vector(R_WR)).normalized()
    for i in range(4):
        off = Vector((-0.045 + i * 0.030, -0.012 + 0.012 * (i % 2), 0.0))
        base = Vector(R_HAND) + off
        tip = base + hdir * 0.115 + Vector((0.01 * (i - 1.5), -0.035, 0.0))
        claw = _seg(TAG + f"fiend_claw_r_{i}", base, tip, 0.020, 0.004, 1.0, levels=1)
        parts_other.append((claw, mats["horn"]))

    parts_skin.append(_sphere(TAG + "fiend_delt_l", 0.112, L_SH))
    parts_skin.append(_seg(TAG + "fiend_uarm_l", L_SH, L_EL, 0.096, 0.072))
    parts_skin.append(_sphere(TAG + "fiend_elbow_l", 0.068, L_EL, subdivisions=1))
    parts_skin.append(_seg(TAG + "fiend_farm_l", L_EL, L_WR, 0.074, 0.050))
    parts_skin.append(_seg(TAG + "fiend_hand_l", L_WR, L_HAND, 0.054, 0.040, 0.65))
    hdir = (Vector(L_HAND) - Vector(L_WR)).normalized()
    for i in range(4):
        base = Vector(L_HAND) + Vector((0.0, -0.030 + i * 0.022, 0.012 * (i % 2)))
        tip = base + hdir * 0.10 + Vector((0.0, 0.03 * (i - 1.5), 0.0))
        claw = _seg(TAG + f"fiend_claw_l_{i}", base, tip, 0.018, 0.004, 1.0, levels=1)
        parts_other.append((claw, mats["horn"]))

    # ---- legs: right swinging through in the air, left planted & trailing ---
    parts_skin.append(_seg(TAG + "fiend_thigh_r", RL_HIP, RL_KNEE, 0.145, 0.098))
    parts_skin.append(_sphere(TAG + "fiend_knee_r", 0.090, RL_KNEE, subdivisions=1))
    parts_skin.append(_seg(TAG + "fiend_calf_r", RL_KNEE, RL_ANK, 0.110, 0.062))
    foot_r = add_box(TAG + "fiend_foot_r", (0.155, 0.095, 0.30), (0.615, 0.355, 0.95),
                     rotation=(0.50, 0.0, 0.0))
    _organic(foot_r, levels=2)
    parts_skin.append(foot_r)
    for i in range(3):
        base = Vector((0.56 + i * 0.055, 0.305, 1.07))
        tip = base + Vector((0.01, -0.035, 0.085))
        toe = _seg(TAG + f"fiend_toe_r_{i}", base, tip, 0.024, 0.008, 1.0, levels=1)
        parts_other.append((toe, mats["horn"]))

    parts_skin.append(_seg(TAG + "fiend_thigh_l", LL_HIP, LL_KNEE, 0.142, 0.096))
    parts_skin.append(_sphere(TAG + "fiend_knee_l", 0.088, LL_KNEE, subdivisions=1))
    parts_skin.append(_seg(TAG + "fiend_calf_l", LL_KNEE, LL_ANK, 0.108, 0.060))
    foot_l = add_box(TAG + "fiend_foot_l", (0.155, 0.105, 0.34), (-0.445, 0.062, -0.695),
                     rotation=(-0.10, 0.0, 0.0))
    _organic(foot_l, levels=2)
    parts_skin.append(foot_l)
    for i in range(3):
        base = Vector((-0.50 + i * 0.055, 0.045, -0.84))
        tip = base + Vector((-0.01, -0.005, -0.085))
        toe = _seg(TAG + f"fiend_toe_l_{i}", base, tip, 0.024, 0.008, 1.0, levels=1)
        parts_other.append((toe, mats["horn"]))

    # back spines — cheap silhouette interest along the hunched spine
    for i in range(5):
        t = i / 4.0
        a = Vector(P_HIP).lerp(Vector(P_CHEST), t)
        a = a + Vector((-0.02, 0.01, -0.145 - 0.02 * math.sin(t * 3.0)))
        b = a + Vector((-0.01, 0.055 - 0.02 * t, -0.085 - 0.03 * t))
        sp = _seg(TAG + f"fiend_spine_{i}", a, b, 0.030 - 0.004 * i, 0.006, 1.0, levels=1)
        parts_other.append((sp, mats["horn"]))

    # ============ the ichor fountain: the key storytelling element ========
    arc_objs = []
    # main arc: one continuous tapering tube, fat and pressurised at the
    # wound, thinning and breaking up as it falls
    n = 13
    pts, radii = [], []
    for i in range(n + 1):
        f = i / n
        pts.append(_fount_point(FOUNT_T * f))
        radii.append(0.090 * (1.0 - f) ** 0.85 + 0.022)
    pts.insert(0, Vector(STUMP_B) - up * 0.04)
    radii.insert(0, 0.100)
    arc_objs.append(_ribbon(TAG + "fiend_spray_main", pts, radii))
    # secondary jet spitting the other way
    pts, radii = [], []
    v = Vector((-0.62, 1.60, -0.34))
    for i in range(9):
        t = 1.30 * i / 8.0
        p = Vector(STUMP_B) + v * t - Vector((0.0, 0.5 * 2.3 * t * t, 0.0))
        pts.append(p)
        radii.append(0.046 * (1.0 - i / 8.0) ** 0.8 + 0.011)
    arc_objs.append(_ribbon(TAG + "fiend_spray_second", pts, radii, bevel_resolution=1))
    # ichor sheeting down the chest and back from the open neck
    dribbles = [
        [Vector((0.24, 1.46, 0.74)), Vector((0.22, 1.28, 0.70)),
         Vector((0.20, 1.10, 0.60)), Vector((0.17, 0.95, 0.50))],
        [Vector((0.33, 1.47, 0.66)), Vector((0.37, 1.30, 0.60)),
         Vector((0.40, 1.16, 0.52))],
        [Vector((0.22, 1.46, 0.60)), Vector((0.16, 1.30, 0.44)),
         Vector((0.12, 1.12, 0.33)), Vector((0.09, 0.98, 0.26))],
    ]
    for i, pts in enumerate(dribbles):
        radii = [0.042 - 0.009 * j for j in range(len(pts))]
        arc_objs.append(_ribbon(TAG + f"fiend_dribble_{i}", pts, radii,
                                bevel_resolution=1, resolution_u=3))
    _mat_all(arc_objs, mats["ichor"])

    # droplets torn off the arc — stretched along their flight direction
    rng = random.Random(21)
    drops = []
    hot = []
    for i in range(40):
        t = rng.uniform(0.15, 2.75)
        p = _fount_point(t)
        spread = 0.07 + 0.14 * t
        p = p + Vector((rng.uniform(-spread, spread),
                        rng.uniform(-spread * 0.7, spread * 0.7),
                        rng.uniform(-spread * 0.8, spread * 0.8)))
        if p.y < 0.03:
            p.y = rng.uniform(0.03, 0.12)
        r = rng.uniform(0.013, 0.040)
        d = _sphere(TAG + f"fiend_drop_{i}", r, tuple(p), subdivisions=2)
        tang = (FOUNT_V - Vector((0.0, FOUNT_G * t, 0.0))).normalized()
        d.rotation_euler = Vector((0.0, 1.0, 0.0)).rotation_difference(tang).to_euler()
        d.scale = (1.0, rng.uniform(1.3, 2.4), 1.0)
        (hot if i % 5 == 0 else drops).append(d)
    # splash where the arc lands
    land = _fount_point(FOUNT_T)
    for i in range(6):
        a = rng.uniform(0, math.tau)
        rr = rng.uniform(0.05, 0.42)
        sp = add_cylinder(TAG + f"fiend_splat_{i}",
                          rng.uniform(0.05, 0.17), 0.010,
                          (land.x + math.cos(a) * rr, 0.006, land.z + math.sin(a) * rr),
                          rotation=(math.pi / 2, rng.uniform(0.0, 3.0), 0.0), vertices=12)
        sp.scale = (1.0, rng.uniform(0.6, 1.5), 1.0)
        drops.append(sp)
    _mat_all(drops, mats["ichor"])
    _mat_all(hot, mats["ichor_hot"])

    # ---- materials + parenting ----
    _mat_all(parts_skin, mats["skin"])
    for obj, mat in parts_other:
        assign_material(obj, mat)
    everything = parts_skin + [o for o, _ in parts_other] + arc_objs + drops + hot
    _parent_to(everything, parent)
    return everything


# ====================================================== the severed head ==
# After the roll+yaw below the neck stump points roughly toward +X and a
# little -Z; the pool and the crack web are laid out along that direction.
HEAD_YAW = math.radians(-32.0)
POOL_DIR = math.radians(-21.0)


def _pool_rot(x, z):
    c, s = math.cos(POOL_DIR), math.sin(POOL_DIR)
    return x * c + z * s, -x * s + z * c


# Built upright in a local frame (face +Z, up +Y) under PROP_head_pivot,
# which is then rolled onto its cheek and dropped so it rests on the floor.

def _build_head_mesh(mats, pivot):
    skin = []
    other = []

    # ---- skull: one continuous lofted shell, cranium through muzzle ----
    # (cx, cy, cz, half_width, half_height) — +Z is the muzzle direction
    skull_rings = [
        (0.0, 0.040, -0.175, 0.050, 0.055),
        (0.0, 0.045, -0.140, 0.098, 0.098),
        (0.0, 0.048, -0.075, 0.125, 0.120),
        (0.0, 0.048, -0.010, 0.128, 0.122),
        (0.0, 0.040, 0.045, 0.118, 0.112),
        (0.0, 0.022, 0.090, 0.098, 0.098),   # brow / eye line
        (0.0, -0.002, 0.140, 0.072, 0.080),  # muzzle
        (0.0, -0.016, 0.195, 0.052, 0.060),
        (0.0, -0.022, 0.235, 0.034, 0.040),  # snout tip
    ]
    skin.append(_loft(TAG + "head_skull", skull_rings, levels=3))

    # heavy brow ridge sitting over the sockets
    brow = add_box(TAG + "head_brow", (0.225, 0.052, 0.105), (0.0, 0.072, 0.072),
                   rotation=(0.20, 0.0, 0.0), bevel_width=0.006, bevel_segments=2)
    _organic(brow, levels=2)
    skin.append(brow)
    # occipital ridge running back over the crown
    skin.append(_loft(TAG + "head_crest", [
        (0.0, 0.120, 0.030, 0.022, 0.020),
        (0.0, 0.148, -0.040, 0.026, 0.030),
        (0.0, 0.140, -0.120, 0.022, 0.026),
        (0.0, 0.100, -0.180, 0.014, 0.014),
    ], levels=2))

    # slack lower jaw, hanging open — dead weight
    jaw = _loft(TAG + "head_jaw", [
        (0.0, -0.030, -0.075, 0.070, 0.050),
        (0.0, -0.045, -0.010, 0.098, 0.060),
        (0.0, -0.052, 0.060, 0.100, 0.058),
        (0.0, -0.056, 0.130, 0.080, 0.050),
        (0.0, -0.052, 0.190, 0.054, 0.038),
        (0.0, -0.048, 0.225, 0.030, 0.024),
    ], levels=3)
    jaw.rotation_euler = (0.28, 0.0, 0.0)   # hinged slack open
    jaw.location = (0.0, 0.005, -0.020)
    skin.append(jaw)

    # ---- teeth: a few prominent tusks plus a smaller row ----
    for s in (-1, 1):
        tusk = _ribbon(TAG + f"head_tusk_u_{s}",
                       [Vector((s * 0.055, -0.048, 0.112)),
                        Vector((s * 0.060, -0.078, 0.124)),
                        Vector((s * 0.062, -0.102, 0.134))],
                       [0.015, 0.009, 0.002], bevel_resolution=1, resolution_u=3)
        other.append((tusk, mats["bone"]))
        tusk2 = _ribbon(TAG + f"head_tusk_l_{s}",
                        [Vector((s * 0.050, -0.040, 0.098)),
                         Vector((s * 0.054, -0.012, 0.108)),
                         Vector((s * 0.056, 0.008, 0.114))],
                        [0.013, 0.008, 0.002], bevel_resolution=1, resolution_u=3)
        other.append((tusk2, mats["bone"]))
        for i in range(4):
            f = i / 3.0
            t = add_cone(TAG + f"head_tooth_u_{i}_{s}", 0.0090, 0.0015, 0.026,
                         (s * (0.046 - 0.014 * f), -0.052 - 0.003 * f, 0.145 + 0.045 * f),
                         rotation=(math.pi + 0.15, 0.0, 0.0), vertices=6)
            other.append((t, mats["bone"]))
        for i in range(3):
            f = i / 2.0
            t = add_cone(TAG + f"head_tooth_l_{i}_{s}", 0.0080, 0.0015, 0.022,
                         (s * (0.042 - 0.010 * f), -0.032 - 0.018 * f, 0.078 + 0.040 * f),
                         rotation=(-0.30, 0.0, 0.0), vertices=6)
            other.append((t, mats["bone"]))

    # ---- horns: continuous tapering sweeps back off the skull ----
    for s in (-1, 1):
        horn = _ribbon(TAG + f"head_horn_{s}", [
            Vector((s * 0.098, 0.118, -0.020)),
            Vector((s * 0.136, 0.186, -0.075)),
            Vector((s * 0.152, 0.222, -0.150)),
            Vector((s * 0.140, 0.212, -0.232)),
            Vector((s * 0.118, 0.178, -0.280)),
        ], [0.040, 0.030, 0.021, 0.012, 0.004])
        other.append((horn, mats["horn"]))
        # cheek spur and brow spike
        sp = _ribbon(TAG + f"head_spur_{s}",
                     [Vector((s * 0.098, 0.070, 0.050)),
                      Vector((s * 0.128, 0.098, 0.052)),
                      Vector((s * 0.142, 0.122, 0.040))],
                     [0.018, 0.011, 0.003], bevel_resolution=1, resolution_u=3)
        other.append((sp, mats["horn"]))
        sp2 = _ribbon(TAG + f"head_jawspur_{s}",
                      [Vector((s * 0.080, -0.050, -0.010)),
                       Vector((s * 0.108, -0.072, -0.060)),
                       Vector((s * 0.112, -0.078, -0.100))],
                      [0.015, 0.009, 0.003], bevel_resolution=1, resolution_u=3)
        other.append((sp2, mats["horn"]))
        # ear fin
        ear = add_box(TAG + f"head_ear_{s}", (0.014, 0.070, 0.095),
                      (s * 0.118, 0.040, -0.075), rotation=(0.0, s * -0.45, s * 0.40))
        _organic(ear, levels=2)
        skin.append(ear)

    # ---- eyes: rolled white, a last cyan flicker guttering out ----
    for s in (-1, 1):
        c = Vector((s * 0.066, 0.036, 0.086))
        eb = _sphere(TAG + f"head_eye_{s}", 0.032, tuple(c), subdivisions=3)
        other.append((eb, mats["eye"]))
        # the iris has rolled up and back — only a sliver of it still shows
        gdir = Vector((s * 0.35, 0.82, 0.45)).normalized()
        gl = _sphere(TAG + f"head_flicker_{s}", 0.0140, tuple(c + gdir * 0.025),
                     subdivisions=2)
        gl.scale = (1.3, 0.75, 1.3)
        other.append((gl, mats["eye_flicker"]))
        # slack lower lid
        lid = _seg(TAG + f"head_lid_{s}", (s * 0.044, 0.012, 0.110),
                   (s * 0.104, 0.018, 0.070), 0.020, 0.016, 0.60, levels=2)
        skin.append(lid)

    # ---- ragged neck stump: back-under the skull, cleanly severed ----
    n0 = Vector((0.0, -0.040, -0.110))
    n1 = Vector((0.0, -0.118, -0.212))
    skin.append(_seg(TAG + "head_neck", tuple(n0), tuple(n1), 0.094, 0.082, 1.0, levels=2))
    ndir = (n1 - n0).normalized()
    cav = _sphere(TAG + "head_stump_cavity", 0.074, tuple(n1 - ndir * 0.005), subdivisions=2)
    cav.scale = (1.0, 0.55, 0.45)
    cav.rotation_euler = Vector((0.0, 1.0, 0.0)).rotation_difference(ndir).to_euler()
    other.append((cav, mats["flesh"]))
    spine = add_cylinder(TAG + "head_vertebra", 0.022, 0.050, tuple(n1 + ndir * 0.012),
                         rotation=Vector((0.0, 0.0, 1.0)).rotation_difference(ndir).to_euler(),
                         vertices=10)
    other.append((spine, mats["bone"]))
    nside = ndir.cross(Vector((1.0, 0.0, 0.0))).normalized()
    nside2 = ndir.cross(nside).normalized()
    rng = random.Random(11)
    for i in range(10):
        a = i / 10.0 * math.tau
        rad = 0.078 + rng.uniform(-0.008, 0.010)
        base = n1 - ndir * 0.018 + (nside * math.cos(a) + nside2 * math.sin(a)) * rad
        tip = base + ndir * rng.uniform(0.02, 0.06) + (
            nside * math.cos(a) + nside2 * math.sin(a)) * rng.uniform(0.004, 0.028)
        rag = _seg(TAG + f"head_rag_{i}", tuple(base), tuple(tip), 0.021, 0.005, 1.0, levels=1)
        other.append((rag, mats["flesh"]))

    _mat_all(skin, mats["skin_head"])
    for obj, mat in other:
        assign_material(obj, mat)
    objs = skin + [o for o, _ in other]
    _parent_to(objs, pivot)
    return objs


def _build_pool(mats, parent):
    """Flat irregular ichor pool spreading from the stump (which, after the
    head is rolled onto its cheek, points toward +X), plus satellite
    splatters and thin runnels. Sits at Y=0.004 to clear the floor."""
    rng = random.Random(5)
    objs = []
    y = 0.004

    # main mass: overlapping flat ellipses -> one irregular organic outline
    blobs = [
        (0.08, 0.00, 0.30, 1.0, 1.0),
        (0.26, 0.04, 0.27, 1.25, 0.95),
        (0.44, -0.08, 0.22, 1.15, 1.0),
        (0.58, 0.10, 0.17, 1.3, 0.85),
        (0.20, -0.22, 0.17, 0.95, 1.15),
        (0.16, 0.24, 0.16, 1.0, 1.1),
        (0.70, -0.04, 0.13, 1.0, 1.0),
        (-0.14, 0.08, 0.20, 1.0, 1.1),
        (-0.30, -0.06, 0.14, 1.0, 0.9),
        (0.40, 0.26, 0.13, 1.15, 0.9),
        (0.50, -0.26, 0.12, 1.1, 0.95),
        (-0.06, -0.26, 0.12, 1.0, 0.9),
        (0.86, 0.06, 0.09, 1.2, 0.8),
    ]
    S = 0.72   # overall spread of the pool, in metres of radius scale
    blobs = [_pool_rot(x * S, z * S) + (r * S, sx, sz)
             for (x, z, r, sx, sz) in blobs]
    for i, (x, z, r, sx, sz) in enumerate(blobs):
        # NOTE euler XYZ applies X first, so the in-plane spin must go in the
        # Y slot — a Z term here would tilt the disc up out of the floor.
        b = add_cylinder(TAG + f"pool_{i}", r, 0.009, (x, y, z),
                         rotation=(math.pi / 2, rng.uniform(-0.8, 0.8), 0.0), vertices=18)
        b.scale = (sx, sz, 1.0)
        objs.append(b)

    # satellite splatters thrown further out
    for i in range(16):
        a = rng.uniform(-1.2, 1.9)
        rr = rng.uniform(0.55, 1.15) * S
        r = rng.uniform(0.022, 0.085) * S
        sx_, sz_ = _pool_rot(0.25 * S + math.cos(a) * rr, math.sin(a) * rr * 0.75)
        b = add_cylinder(TAG + f"splat_{i}", r, 0.008, (sx_, y, sz_),
                         rotation=(math.pi / 2, rng.uniform(0, 3.0), 0.0), vertices=10)
        b.scale = (rng.uniform(0.7, 1.9), rng.uniform(0.6, 1.2), 1.0)
        objs.append(b)

    # thin runnels creeping out of the pool
    for i in range(7):
        a = rng.uniform(-1.0, 1.6)
        x0, z0 = _pool_rot((0.30 + math.cos(a) * 0.38) * S, math.sin(a) * 0.30 * S)
        a = a + POOL_DIR
        L = rng.uniform(0.20, 0.52) * S
        run = add_box(TAG + f"runnel_{i}", (0.026 + rng.uniform(0, 0.018), 0.008, L),
                      (x0 + math.cos(a) * L * 0.5, y, z0 + math.sin(a) * L * 0.5),
                      rotation=(0.0, -a + math.pi / 2, 0.0))
        objs.append(run)

    _mat_all(objs, mats["ichor_pool"])
    _parent_to(objs, parent)
    return objs


def _build_cracks(mats, parent):
    """Spiderweb fracture radiating in the crystal under the head."""
    rng = random.Random(3)
    objs = []
    y = 0.002
    idx = 0

    def bar(x0, z0, ang, length, width):
        nonlocal idx
        b = add_box(TAG + f"crack_{idx}", (width, 0.0045, length),
                    (x0 + math.sin(ang) * length * 0.5, y, z0 + math.cos(ang) * length * 0.5),
                    rotation=(0.0, ang, 0.0))
        idx += 1
        objs.append(b)

    for i in range(17):
        a = i / 17.0 * math.tau + rng.uniform(-0.09, 0.09)
        x, z = math.cos(a) * 0.05, math.sin(a) * 0.05
        ang = math.pi / 2 - a
        total = rng.uniform(0.35, 0.80)
        walked = 0.0
        w = 0.013
        while walked < total:
            L = min(rng.uniform(0.12, 0.26), total - walked)
            bar(x, z, ang, L, w)
            x += math.sin(ang) * L
            z += math.cos(ang) * L
            walked += L
            ang += rng.uniform(-0.34, 0.34)
            w = max(0.005, w * 0.78)
            # branch
            if rng.random() < 0.45 and walked < total * 0.8:
                ba = ang + rng.choice((-1, 1)) * rng.uniform(0.5, 1.0)
                bar(x, z, ba, rng.uniform(0.10, 0.26), max(0.004, w * 0.8))

    # a few concentric chordal cracks tying the web together
    for i in range(9):
        a = rng.uniform(0, math.tau)
        rr = rng.uniform(0.15, 0.50)
        bar(math.cos(a) * rr, math.sin(a) * rr,
            math.pi / 2 - a + math.pi / 2 + rng.uniform(-0.3, 0.3),
            rng.uniform(0.10, 0.30), rng.uniform(0.005, 0.010))

    _mat_all(objs, mats["crack"])
    _parent_to(objs, parent)
    return objs


# ================================================================ build ===

def build():
    mats = _materials()

    root = bpy.data.objects.new(TAG + "root", None)
    bpy.context.collection.objects.link(root)

    fiend_root = bpy.data.objects.new(TAG + "fiend_root", None)
    bpy.context.collection.objects.link(fiend_root)
    fiend_root.parent = root

    head_root = bpy.data.objects.new(TAG + "head_root", None)
    bpy.context.collection.objects.link(head_root)
    head_root.parent = root

    _build_fiend(mats, fiend_root)

    # the head itself hangs off a pivot that rolls it onto its cheek
    pivot = bpy.data.objects.new(TAG + "head_pivot", None)
    bpy.context.collection.objects.link(pivot)
    pivot.parent = head_root
    # ZYX order so the roll happens FIRST, about the head's own face axis
    # (tipping it onto its left cheek, face still horizontal), and only
    # then the yaw turns it. In the default XYZ order the roll is applied
    # about the world axis after the yaw, which faceplants the head.
    pivot.rotation_mode = "ZYX"
    pivot.rotation_euler = (math.radians(-9.0), HEAD_YAW, math.radians(86.0))
    pivot.scale = (0.88, 0.88, 0.88)
    head_objs = _build_head_mesh(mats, pivot)

    # drop the rolled head so its lowest point just sinks into the pool
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    low = 1e9
    for o in head_objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        for v in me.vertices:
            low = min(low, (o.matrix_world @ v.co).y)
        ev.to_mesh_clear()
    pivot.location = (0.0, 0.012 - low, 0.0)
    bpy.context.view_layer.update()

    _build_pool(mats, head_root)
    _build_cracks(mats, head_root)

    return {"root": root, "fiend": fiend_root, "head": head_root}


if __name__ == "__main__":
    build()
