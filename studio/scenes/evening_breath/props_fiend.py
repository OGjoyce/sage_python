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
        roughness=0.30,
        emission_color=(TEAL_CRACK[0] * 0.10, TEAL_CRACK[1] * 0.10, TEAL_CRACK[2] * 0.10, 1.0),
        emission_strength=0.38,
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
        roughness=0.34,
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
        emission_strength=9.0,
    )
    m["crack"], _ = cs.materials.new_principled_material(
        TAG + "crack",
        base_color=(0.018, 0.040, 0.048, 1.0),
        roughness=0.62,
        emission_color=(TEAL_CRACK[0] * 0.10, TEAL_CRACK[1] * 0.10, TEAL_CRACK[2] * 0.10, 1.0),
        emission_strength=0.9,
    )
    return m


# =========================================================== the fiend ====
# ~2.1 m tall if it were upright (noticeably smaller than the 3 m Chaos
# Lord). Headless and STILL WALKING: caught at the contact frame of a
# stride — right leg forward and just landed, left leg trailing and
# pushing off with the heel lifted, hips and shoulders counter-rotated,
# weight over the front leg, torso pitched slightly forward. The left arm
# (opposite the lead leg, as in a real gait) is stretched out ahead.
# The contact frame is used because it is the moment of a walk cycle whose
# silhouette is unmistakable: both legs at full spread, one heel down,
# one toe down.

P_HIP = (0.00, 0.92, 0.02)
P_BELLY = (0.03, 1.17, 0.13)
P_CHEST = (0.07, 1.45, 0.27)
# shoulders counter-rotate against the hips: lead-leg side pulled back
R_SH = (0.40, 1.38, 0.11)
L_SH = (-0.27, 1.41, 0.41)
STUMP_A = (0.07, 1.44, 0.27)
STUMP_B = (0.09, 1.61, 0.34)

# left arm stretched forward (contralateral to the lead leg)
L_EL = (-0.48, 1.39, 0.64)
L_WR = (-0.70, 1.355, 1.10)
L_HAND = (-0.77, 1.345, 1.26)
# right arm swung back behind the hip
R_EL = (0.44, 1.19, -0.18)
R_WR = (0.52, 0.99, -0.46)
R_HAND = (0.55, 0.92, -0.56)

# lead leg: forward, nearly straight, heel just down
RL_HIP = (0.17, 0.90, 0.11)
RL_KNEE = (0.21, 0.52, 0.43)
RL_ANK = (0.24, 0.135, 0.58)
# trailing leg: extended back, pushing off, heel lifted
LL_HIP = (-0.17, 0.92, -0.07)
LL_KNEE = (-0.22, 0.49, -0.36)
LL_ANK = (-0.26, 0.165, -0.64)

# how far the whole walking body is turned inside its own group
FIEND_GAIT_YAW = math.radians(60.0)

# ichor fountain ballistics (used for both the arc and the droplets)
FOUNT_V = Vector((0.72, 2.95, 0.34))
FOUNT_G = 2.85
FOUNT_T = 2.46


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
    gore = []        # ichor-material parts that belong to the body
    hot = []         # the few brighter spots

    # ---- torso: pelvis -> belly -> chest, pitched slightly forward ----
    parts_skin.append(_seg(TAG + "fiend_pelvis", (0.0, 0.78, -0.03), P_HIP, 0.175, 0.160, 0.80))
    parts_skin.append(_seg(TAG + "fiend_abdomen", P_HIP, P_BELLY, 0.160, 0.150, 0.82))
    parts_skin.append(_seg(TAG + "fiend_chest", P_BELLY, P_CHEST, 0.155, 0.200, 0.78))
    parts_skin.append(_sphere(TAG + "fiend_ribs", 0.195, (0.05, 1.36, 0.20)))
    parts_skin[-1].scale = (1.05, 0.80, 0.88)
    parts_skin.append(_sphere(TAG + "fiend_backhump", 0.140, (0.03, 1.38, 0.06)))
    # shoulder yoke, carrying the counter-rotation
    parts_skin.append(_seg(TAG + "fiend_clavicle", L_SH, R_SH, 0.135, 0.145, 0.85, levels=1))
    # trapezius slabs: they flatten and widen the top of the silhouette, so
    # that at 150 px the eye reads "shoulders, and nothing above them"
    for i, (c, sc) in enumerate([((0.20, 1.40, 0.19), (1.5, 0.55, 1.0)),
                                 ((-0.12, 1.42, 0.33), (1.5, 0.55, 1.0))]):
        tr = _sphere(TAG + f"fiend_trap_{i}", 0.145, c, subdivisions=2)
        tr.scale = sc
        parts_skin.append(tr)

    # ======================= the torn neck stump =======================
    rng = random.Random(7)
    up = (Vector(STUMP_B) - Vector(STUMP_A)).normalized()
    side = Vector((1.0, 0.0, 0.0)).cross(up).normalized()
    side2 = up.cross(side).normalized()
    parts_skin.append(_seg(TAG + "fiend_neck", STUMP_A, STUMP_B, 0.105, 0.090, 1.0))

    # torn muscle inside the stump, and the open wound bowl
    cav = _sphere(TAG + "fiend_stump_cavity", 0.084, tuple(Vector(STUMP_B) - up * 0.010))
    cav.scale = (1.0, 0.5, 1.0)
    parts_other.append((cav, mats["flesh"]))
    for i in range(7):
        a = i / 7.0 * math.tau + 0.3
        radial = side * math.cos(a) + side2 * math.sin(a)
        b0 = Vector(STUMP_B) + radial * rng.uniform(0.025, 0.055) - up * 0.02
        b1 = b0 + up * rng.uniform(0.02, 0.05) + radial * rng.uniform(-0.01, 0.015)
        parts_other.append((_seg(TAG + f"fiend_muscle_{i}", tuple(b0), tuple(b1),
                                 rng.uniform(0.016, 0.026), 0.008, 1.0, levels=1),
                            mats["flesh"]))
    # stump of spine standing proud of the wound
    sp0 = Vector(STUMP_B) - up * 0.02
    parts_other.append((_seg(TAG + "fiend_spine_stump", tuple(sp0), tuple(sp0 + up * 0.085),
                             0.028, 0.020, 1.0, levels=1), mats["bone"]))
    parts_other.append((_sphere(TAG + "fiend_vert_1", 0.030, tuple(sp0 + up * 0.090),
                                subdivisions=2), mats["bone"]))
    # flaps of skin peeled back and hanging off the rim
    for i in range(7):
        a = i / 7.0 * math.tau + 0.9
        radial = (side * math.cos(a) + side2 * math.sin(a)).normalized()
        b0 = Vector(STUMP_B) + radial * 0.085 - up * 0.01
        mid = b0 + radial * 0.045 - up * rng.uniform(0.03, 0.07)
        tip = mid + radial * rng.uniform(0.01, 0.03) - up * rng.uniform(0.05, 0.12)
        flap = _ribbon(TAG + f"fiend_flap_{i}", [b0, mid, tip],
                       [rng.uniform(0.028, 0.040), 0.022, 0.006],
                       bevel_resolution=1, resolution_u=3)
        flap.scale = (1.0, 1.0, 0.45)
        parts_other.append((flap, mats["flesh"]))
    # tendons and sinew strands trailing out of the wound
    for i in range(6):
        a = rng.uniform(0, math.tau)
        radial = (side * math.cos(a) + side2 * math.sin(a)).normalized()
        b0 = Vector(STUMP_B) + radial * rng.uniform(0.02, 0.07)
        mid = b0 + up * rng.uniform(0.04, 0.10) + radial * rng.uniform(0.02, 0.06)
        tip = mid + radial * rng.uniform(0.03, 0.09) - up * rng.uniform(0.02, 0.10)
        parts_other.append((_ribbon(TAG + f"fiend_tendon_{i}", [b0, mid, tip],
                                    [0.012, 0.008, 0.003],
                                    bevel_resolution=1, resolution_u=3), mats["flesh"]))
    # ragged torn skin around the rim
    for i in range(10):
        a = i / 10.0 * math.tau
        radial = side * math.cos(a) + side2 * math.sin(a)
        rad = 0.086 + rng.uniform(-0.008, 0.014)
        base = Vector(STUMP_B) + radial * rad
        tip = base + up * rng.uniform(0.03, 0.09) + radial * rng.uniform(0.01, 0.05)
        parts_other.append((_seg(TAG + f"fiend_stump_rag_{i}", tuple(base), tuple(tip),
                                 0.024, 0.006, 1.0, levels=1), mats["flesh"]))

    # ---- arms: left stretched out ahead, right swung back ----
    parts_skin.append(_sphere(TAG + "fiend_delt_l", 0.115, L_SH))
    parts_skin.append(_seg(TAG + "fiend_uarm_l", L_SH, L_EL, 0.098, 0.076))
    parts_skin.append(_sphere(TAG + "fiend_elbow_l", 0.072, L_EL, subdivisions=1))
    parts_skin.append(_seg(TAG + "fiend_farm_l", L_EL, L_WR, 0.078, 0.052))
    parts_skin.append(_seg(TAG + "fiend_hand_l", L_WR, L_HAND, 0.056, 0.042, 0.65))
    hdir = (Vector(L_HAND) - Vector(L_WR)).normalized()
    for i in range(4):
        base = Vector(L_HAND) + Vector((-0.040 + i * 0.028, -0.010 + 0.012 * (i % 2), 0.0))
        tip = base + hdir * 0.115 + Vector((0.01 * (i - 1.5), -0.030, 0.0))
        parts_other.append((_seg(TAG + f"fiend_claw_l_{i}", tuple(base), tuple(tip),
                                 0.020, 0.004, 1.0, levels=1), mats["horn"]))

    parts_skin.append(_sphere(TAG + "fiend_delt_r", 0.112, R_SH))
    parts_skin.append(_seg(TAG + "fiend_uarm_r", R_SH, R_EL, 0.096, 0.072))
    parts_skin.append(_sphere(TAG + "fiend_elbow_r", 0.068, R_EL, subdivisions=1))
    parts_skin.append(_seg(TAG + "fiend_farm_r", R_EL, R_WR, 0.074, 0.050))
    parts_skin.append(_seg(TAG + "fiend_hand_r", R_WR, R_HAND, 0.054, 0.040, 0.65))
    hdir = (Vector(R_HAND) - Vector(R_WR)).normalized()
    for i in range(4):
        base = Vector(R_HAND) + Vector((-0.030 + i * 0.022, 0.0, 0.012 * (i % 2)))
        tip = base + hdir * 0.10 + Vector((0.01 * (i - 1.5), -0.02, 0.0))
        parts_other.append((_seg(TAG + f"fiend_claw_r_{i}", tuple(base), tuple(tip),
                                 0.018, 0.004, 1.0, levels=1), mats["horn"]))

    # ---- legs ----
    # lead leg, heel just down and the sole rolling flat
    parts_skin.append(_seg(TAG + "fiend_thigh_r", RL_HIP, RL_KNEE, 0.145, 0.098))
    parts_skin.append(_sphere(TAG + "fiend_knee_r", 0.090, RL_KNEE, subdivisions=1))
    parts_skin.append(_seg(TAG + "fiend_calf_r", RL_KNEE, RL_ANK, 0.110, 0.062))
    parts_skin.append(_sphere(TAG + "fiend_ankle_r", 0.078, RL_ANK, subdivisions=2))
    foot_r = add_box(TAG + "fiend_foot_r", (0.155, 0.135, 0.34), (0.250, 0.078, 0.665),
                     rotation=(-0.12, 0.0, 0.0))
    _organic(foot_r, levels=2)
    parts_skin.append(foot_r)
    for i in range(3):
        base = Vector((0.195 + i * 0.055, 0.045, 0.815))
        tip = base + Vector((0.01, -0.004, 0.085))
        parts_other.append((_seg(TAG + f"fiend_toe_r_{i}", tuple(base), tuple(tip),
                                 0.024, 0.008, 1.0, levels=1), mats["horn"]))

    # trailing leg, heel lifted, driving off the ball of the foot
    parts_skin.append(_seg(TAG + "fiend_thigh_l", LL_HIP, LL_KNEE, 0.142, 0.096))
    parts_skin.append(_sphere(TAG + "fiend_knee_l", 0.088, LL_KNEE, subdivisions=1))
    parts_skin.append(_seg(TAG + "fiend_calf_l", LL_KNEE, LL_ANK, 0.108, 0.060))
    parts_skin.append(_sphere(TAG + "fiend_ankle_l", 0.078, LL_ANK, subdivisions=2))
    foot_l = add_box(TAG + "fiend_foot_l", (0.155, 0.125, 0.34), (-0.272, 0.135, -0.735),
                     rotation=(0.62, 0.0, 0.0))
    _organic(foot_l, levels=2)
    parts_skin.append(foot_l)
    for i in range(3):
        base = Vector((-0.33 + i * 0.055, 0.030, -0.600))
        tip = base + Vector((-0.01, -0.010, 0.080))
        parts_other.append((_seg(TAG + f"fiend_toe_l_{i}", tuple(base), tuple(tip),
                                 0.024, 0.008, 1.0, levels=1), mats["horn"]))

    # back spines along the hunched spine
    for i in range(5):
        t = i / 4.0
        a = Vector(P_HIP).lerp(Vector(P_CHEST), t)
        a = a + Vector((-0.02, 0.01, -0.150 - 0.02 * math.sin(t * 3.0)))
        b = a + Vector((-0.01, 0.055 - 0.02 * t, -0.085 - 0.03 * t))
        parts_other.append((_seg(TAG + f"fiend_spine_{i}", tuple(a), tuple(b),
                                 0.030 - 0.004 * i, 0.006, 1.0, levels=1), mats["horn"]))

    # ============ the ichor fountain: pulsed, ragged, arterial ===========
    arc_objs = []

    def pulsed(i, n, base, taper=0.85, amp=0.42, freq=3.1, phase=0.0):
        """Radius along a jet: a taper with a pulse beat on top, so the
        stream looks pumped rather than extruded."""
        f = i / float(n)
        return base * (1.0 - f) ** taper * (1.0 + amp * math.sin(f * freq * math.tau + phase)) + 0.012

    # the main jet: solid only while it is under pressure, then it tears
    # into separate ribbons and finally into pure droplets
    SOLID = 0.34          # fraction of the arc that is still a stream
    n = 11
    pts, radii = [], []
    for i in range(n + 1):
        f = i / n
        pts.append(_fount_point(FOUNT_T * SOLID * f))
        radii.append(pulsed(i, n, 0.130, taper=0.75, amp=0.46, freq=3.4))
    pts.insert(0, Vector(STUMP_B) - up * 0.04)
    radii.insert(0, 0.140)
    arc_objs.append(_ribbon(TAG + "fiend_spray_main", pts, radii, resolution_u=3))

    rngc = random.Random(5)
    for i in range(6):
        t = FOUNT_T * SOLID * (0.18 + 0.82 * i / 5.0)
        p = _fount_point(t) + Vector((rngc.uniform(-0.04, 0.04), 0.0,
                                      rngc.uniform(-0.04, 0.04)))
        cl = _sphere(TAG + f"fiend_clot_{i}", rngc.uniform(0.045, 0.085), tuple(p),
                     subdivisions=2)
        cl.scale = (1.0, rngc.uniform(1.1, 1.9), 1.0)
        arc_objs.append(cl)

    # torn ribbons shearing off the stream for the rest of the arc
    rngs = random.Random(33)
    for k in range(10):
        t0 = FOUNT_T * (SOLID + (1.0 - SOLID) * (k / 10.0)) - rngs.uniform(0.0, 0.04)
        span = FOUNT_T * (1.0 - SOLID) / 10.0 * rngs.uniform(0.45, 0.95)
        jitter = Vector((rngs.uniform(-0.12, 0.12), rngs.uniform(-0.08, 0.08),
                         rngs.uniform(-0.12, 0.12))) * (0.5 + k * 0.20)
        rp, rr = [], []
        for j in range(4):
            tt = t0 + span * j / 3.0
            rp.append(_fount_point(tt) + jitter * (j / 3.0))
            rr.append(max(0.006, (0.046 - 0.0032 * k) * (1.0 - 0.55 * j / 3.0)))
        arc_objs.append(_ribbon(TAG + f"fiend_spray_frag_{k}", rp, rr,
                                bevel_resolution=1, resolution_u=3))

    # secondary jets off the stump at their own angles — a severed artery
    # does not spit in one direction only
    jets = [
        (Vector((-1.05, 0.55, -0.35)), 0.46, 0.026, 3.0),
        (Vector((0.80, 0.42, 0.70)), 0.38, 0.021, 3.0),
    ]
    for j, (v, span, r0, g) in enumerate(jets):
        rp, rr = [], []
        for i in range(9):
            t = span * i / 8.0
            p = Vector(STUMP_B) + v * t - Vector((0.0, 0.5 * g * t * t, 0.0))
            rp.append(p)
            rr.append(pulsed(i, 8, r0, taper=0.7, amp=0.45, freq=2.2, phase=j * 1.7))
        arc_objs.append(_ribbon(TAG + f"fiend_spray_jet_{j}", rp, rr,
                                bevel_resolution=1, resolution_u=3))

    # ichor sheeting down the chest, shoulders and back
    dribbles = [
        [Vector((0.06, 1.54, 0.40)), Vector((0.05, 1.36, 0.36)),
         Vector((0.04, 1.14, 0.28)), Vector((0.02, 0.96, 0.20))],
        [Vector((0.16, 1.52, 0.30)), Vector((0.22, 1.36, 0.26)),
         Vector((0.26, 1.18, 0.20)), Vector((0.28, 1.02, 0.14))],
        [Vector((0.02, 1.52, 0.22)), Vector((-0.04, 1.34, 0.12)),
         Vector((-0.08, 1.16, 0.04)), Vector((-0.10, 0.98, -0.02))],
        [Vector((-0.08, 1.50, 0.34)), Vector((-0.16, 1.40, 0.36)),
         Vector((-0.22, 1.30, 0.34))],
        [Vector((0.14, 1.50, 0.36)), Vector((0.26, 1.42, 0.26)),
         Vector((0.33, 1.34, 0.16))],
        [Vector((0.05, 1.50, 0.14)), Vector((0.02, 1.30, 0.06)),
         Vector((0.00, 1.10, 0.00)), Vector((-0.02, 0.92, -0.04))],
    ]
    for i, dp in enumerate(dribbles):
        rr = [0.046 - 0.009 * j for j in range(len(dp))]
        d = _ribbon(TAG + f"fiend_dribble_{i}", dp, rr, bevel_resolution=1, resolution_u=3)
        d.scale = (1.0, 1.0, 0.55)
        gore.append(d)
    # sheets of it clinging to the shoulders and the small of the back
    for i, (c, sc) in enumerate([((0.07, 1.34, 0.31), (1.5, 1.5, 0.35)),
                                 ((-0.16, 1.33, 0.33), (1.0, 1.3, 0.32)),
                                 ((0.27, 1.30, 0.19), (0.9, 1.4, 0.32)),
                                 ((0.01, 1.22, 0.00), (1.4, 1.6, 0.30))]):
        sh = _sphere(TAG + f"fiend_sheet_{i}", 0.095, c, subdivisions=2)
        sh.scale = sc
        gore.append(sh)
    # spatter running down the legs
    rngl = random.Random(91)
    for i in range(14):
        lead = i % 2 == 0
        hip, knee, ank = ((RL_HIP, RL_KNEE, RL_ANK) if lead else (LL_HIP, LL_KNEE, LL_ANK))
        t = rngl.uniform(0.0, 1.0)
        a = Vector(hip).lerp(Vector(knee), min(1.0, t * 2.0)) if t < 0.5 else \
            Vector(knee).lerp(Vector(ank), (t - 0.5) * 2.0)
        off = Vector((rngl.uniform(-0.09, 0.09), 0.0, rngl.uniform(-0.09, 0.09)))
        sp = _sphere(TAG + f"fiend_legspat_{i}", rngl.uniform(0.016, 0.040),
                     tuple(a + off), subdivisions=1)
        sp.scale = (1.0, rngl.uniform(1.4, 3.0), 0.5)
        gore.append(sp)

    _mat_all(arc_objs, mats["ichor"])
    _mat_all(gore, mats["ichor"])

    # droplets torn off the arc — stretched along their flight direction
    rng = random.Random(21)
    drops = []
    for i in range(62):
        t = rng.uniform(FOUNT_T * 0.22, 2.95)
        p = _fount_point(t)
        spread = 0.06 + 0.17 * t
        p = p + Vector((rng.uniform(-spread, spread),
                        rng.uniform(-spread * 0.7, spread * 0.7),
                        rng.uniform(-spread * 0.8, spread * 0.8)))
        # keep stretched droplets clear of the floor plane
        if p.y < 0.12:
            p.y = rng.uniform(0.12, 0.30)
        r = rng.uniform(0.013, 0.048)
        d = _sphere(TAG + f"fiend_drop_{i}", r, tuple(p), subdivisions=2)
        tang = (FOUNT_V - Vector((0.0, FOUNT_G * t, 0.0))).normalized()
        d.rotation_euler = Vector((0.0, 1.0, 0.0)).rotation_difference(tang).to_euler()
        d.scale = (1.0, rng.uniform(1.4, 2.8), 1.0)
        (hot if i % 6 == 0 else drops).append(d)

    # splash where the arc lands
    land = _fount_point(FOUNT_T)
    for i in range(7):
        a = rng.uniform(0, math.tau)
        rr2 = rng.uniform(0.05, 0.42)
        sp = add_cylinder(TAG + f"fiend_splat_{i}",
                          rng.uniform(0.05, 0.17), 0.010,
                          (land.x + math.cos(a) * rr2, 0.006, land.z + math.sin(a) * rr2),
                          rotation=(math.pi / 2, rng.uniform(0.0, 3.0), 0.0), vertices=12)
        sp.scale = (1.0, rng.uniform(0.6, 1.5), 1.0)
        drops.append(sp)

    # ---- the trail it has already walked: spatter behind the body ----
    rngt = random.Random(57)
    for i in range(34):
        z = -0.9 - 2.9 * (i / 34.0) ** 0.85
        x = 0.15 * math.sin(z * 1.1) + rngt.uniform(-0.42, 0.42)
        r = rngt.uniform(0.020, 0.105) * (1.0 - 0.45 * (i / 34.0))
        sp = add_cylinder(TAG + f"fiend_trail_{i}", r, 0.009, (x, 0.006, z),
                          rotation=(math.pi / 2, rngt.uniform(0.0, 3.0), 0.0), vertices=10)
        sp.scale = (rngt.uniform(0.8, 2.1), rngt.uniform(0.7, 1.3), 1.0)
        drops.append(sp)
    # bigger pooled footfalls along that trail, where it stood a moment
    for i in range(6):
        z = -1.0 - 0.52 * i
        x = (-0.28 if i % 2 else 0.24) + rngt.uniform(-0.08, 0.08)
        sp = add_cylinder(TAG + f"fiend_step_{i}", rngt.uniform(0.10, 0.17), 0.010,
                          (x, 0.006, z), rotation=(math.pi / 2, rngt.uniform(0, 3.0), 0.0),
                          vertices=12)
        sp.scale = (1.0, rngt.uniform(1.2, 1.8), 1.0)
        drops.append(sp)
    # a few droplets still in the air behind, flicked off by the stride
    for i in range(10):
        z = -0.8 - rngt.uniform(0.0, 2.4)
        d = _sphere(TAG + f"fiend_trailair_{i}", rngt.uniform(0.012, 0.030),
                    (rngt.uniform(-0.5, 0.5), rngt.uniform(0.05, 0.55), z), subdivisions=1)
        d.scale = (1.0, rngt.uniform(1.2, 2.0), 1.0)
        drops.append(d)

    _mat_all(drops, mats["ichor"])
    _mat_all(hot, mats["ichor_hot"])

    # ---- materials + parenting ----
    _mat_all(parts_skin, mats["skin"])
    for obj, mat in parts_other:
        assign_material(obj, mat)
    everything = (parts_skin + [o for o, _ in parts_other] + arc_objs
                  + gore + drops + hot)
    _parent_to(everything, parent)
    return everything


# ====================================================== the severed head ==
# After the roll+yaw below the neck stump points roughly toward +X and a
# little -Z; the pool and the crack web are laid out along that direction.
HEAD_YAW = math.radians(-78.0)
# Deliberately oversized: at true anatomical scale the head disappeared
# against the floor in the assembled frame, so it is built ~40% larger
# and reads as a foreground story beat. Skull ends up ~0.72 m long.
HEAD_SCALE = 1.57
# the local direction the neck stump points before the head is rolled
STUMP_DIR_LOCAL = Vector((0.0, -0.60, -0.80)).normalized()


def _rot_xz(x, z, ang):
    c, s = math.cos(ang), math.sin(ang)
    return x * c - z * s, x * s + z * c


# Built upright in a local frame (face +Z, up +Y) under PROP_head_pivot,
# which is then rolled onto its cheek and dropped so it rests on the floor.

def _build_head_mesh(mats, pivot):
    skin = []
    other = []

    # ---- skull: one continuous lofted shell, cranium through muzzle ----
    # (cx, cy, cz, half_width, half_height) — +Z is the muzzle direction
    skull_rings = [
        (0.0, 0.040, -0.175, 0.050, 0.055),
        (0.0, 0.045, -0.140, 0.100, 0.100),
        (0.0, 0.048, -0.075, 0.128, 0.124),
        (0.0, 0.046, -0.010, 0.128, 0.126),
        (0.0, 0.038, 0.050, 0.118, 0.118),
        (0.0, 0.020, 0.100, 0.100, 0.100),   # brow / eye line
        (0.0, -0.006, 0.150, 0.066, 0.076),  # muzzle narrows sharply here
        (0.0, -0.020, 0.205, 0.052, 0.064),
        (0.0, -0.030, 0.255, 0.040, 0.048),
        (0.0, -0.038, 0.290, 0.024, 0.030),  # snout tip
    ]
    skin.append(_loft(TAG + "head_skull", skull_rings, levels=3))

    # heavy brow ridge sitting over the sockets
    brow = add_box(TAG + "head_brow", (0.205, 0.048, 0.095), (0.0, 0.080, 0.068),
                   rotation=(0.26, 0.0, 0.0), bevel_width=0.006, bevel_segments=2)
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
        (0.0, -0.030, -0.080, 0.062, 0.046),
        (0.0, -0.048, -0.010, 0.082, 0.054),
        (0.0, -0.058, 0.070, 0.080, 0.050),
        (0.0, -0.062, 0.140, 0.064, 0.044),
        (0.0, -0.060, 0.205, 0.044, 0.034),
        (0.0, -0.056, 0.255, 0.024, 0.022),
    ], levels=3)
    jaw.rotation_euler = (0.42, 0.0, 0.0)   # hinged slack open
    jaw.location = (0.0, 0.005, -0.020)
    skin.append(jaw)

    # ---- teeth: a few prominent tusks plus a smaller row ----
    for s in (-1, 1):
        tusk = _ribbon(TAG + f"head_tusk_u_{s}",
                       [Vector((s * 0.055, -0.048, 0.112)),
                        Vector((s * 0.060, -0.078, 0.124)),
                        Vector((s * 0.062, -0.102, 0.134))],
                       [0.020, 0.012, 0.002], bevel_resolution=1, resolution_u=3)
        other.append((tusk, mats["bone"]))
        tusk2 = _ribbon(TAG + f"head_tusk_l_{s}",
                        [Vector((s * 0.050, -0.040, 0.098)),
                         Vector((s * 0.054, -0.012, 0.108)),
                         Vector((s * 0.056, 0.008, 0.114))],
                        [0.018, 0.011, 0.002], bevel_resolution=1, resolution_u=3)
        other.append((tusk2, mats["bone"]))
        for i in range(4):
            f = i / 3.0
            t = add_cone(TAG + f"head_tooth_u_{i}_{s}", 0.0090, 0.0015, 0.026,
                         (s * (0.046 - 0.014 * f), -0.054 - 0.004 * f, 0.165 + 0.042 * f),
                         rotation=(math.pi + 0.15, 0.0, 0.0), vertices=6)
            other.append((t, mats["bone"]))
        for i in range(3):
            f = i / 2.0
            t = add_cone(TAG + f"head_tooth_l_{i}_{s}", 0.0080, 0.0015, 0.022,
                         (s * (0.040 - 0.010 * f), -0.036 - 0.020 * f, 0.105 + 0.048 * f),
                         rotation=(-0.30, 0.0, 0.0), vertices=6)
            other.append((t, mats["bone"]))

    # ---- horns: continuous tapering sweeps back off the skull ----
    for s in (-1, 1):
        horn = _ribbon(TAG + f"head_horn_{s}", [
            Vector((s * 0.090, 0.112, -0.022)),
            Vector((s * 0.102, 0.212, -0.080)),
            Vector((s * 0.110, 0.300, -0.205)),
            Vector((s * 0.108, 0.348, -0.350)),
            Vector((s * 0.100, 0.352, -0.480)),
        ], [0.054, 0.044, 0.032, 0.019, 0.006])
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
        c = Vector((s * 0.072, 0.042, 0.096))
        eb = _sphere(TAG + f"head_eye_{s}", 0.040, tuple(c), subdivisions=3)
        other.append((eb, mats["eye"]))
        # the iris has rolled up and back — only a sliver of it still shows
        gdir = Vector((s * 0.86, 0.38, 0.34)).normalized()
        gl = _sphere(TAG + f"head_flicker_{s}", 0.0260, tuple(c + gdir * 0.032),
                     subdivisions=2)
        gl.scale = (1.3, 0.75, 1.3)
        other.append((gl, mats["eye_flicker"]))
        # slack lower lid
        lid = _seg(TAG + f"head_lid_{s}", (s * 0.040, 0.004, 0.124),
                   (s * 0.098, 0.012, 0.082), 0.020, 0.016, 0.60, levels=2)
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
        tip = base + ndir * rng.uniform(0.012, 0.038) + (
            nside * math.cos(a) + nside2 * math.sin(a)) * rng.uniform(0.002, 0.016)
        rag = _seg(TAG + f"head_rag_{i}", tuple(base), tuple(tip), 0.020, 0.004, 0.42, levels=1)
        other.append((rag, mats["flesh"]))

    _mat_all(skin, mats["skin_head"])
    for obj, mat in other:
        assign_material(obj, mat)
    objs = skin + [o for o, _ in other]
    _parent_to(objs, pivot)
    return objs


def _build_pool(mats, parent, pool_dir):
    """Flat irregular ichor pool spreading from the stump (which, after the
    head is rolled onto its cheek, points toward +X), plus satellite
    splatters and thin runnels. Sits at Y=0.004 to clear the floor."""
    rng = random.Random(5)
    objs = []
    y = 0.006          # clear of the floor plane, no z-fighting

    # main mass: overlapping flat ellipses -> one irregular organic outline
    blobs = [
        (0.08, 0.00, 0.30, 1.0, 1.0),
        (0.26, 0.04, 0.27, 1.25, 0.95),
        (0.44, -0.08, 0.22, 1.15, 1.0),
        (0.58, 0.10, 0.17, 1.3, 0.85),
        (0.20, -0.22, 0.17, 0.95, 1.15),
        (0.16, 0.24, 0.16, 1.0, 1.1),
        (0.70, -0.04, 0.13, 1.0, 1.0),
        (-0.14, 0.08, 0.22, 1.0, 1.1),
        (-0.32, -0.04, 0.17, 1.1, 0.95),
        (-0.46, 0.12, 0.12, 1.0, 0.9),
        (-0.10, -0.20, 0.15, 1.0, 1.0),
        (0.40, 0.26, 0.13, 1.15, 0.9),
        (0.50, -0.26, 0.12, 1.1, 0.95),
        (-0.06, -0.26, 0.12, 1.0, 0.9),
        (0.86, 0.06, 0.09, 1.2, 0.8),
    ]
    S = 0.92   # overall spread of the pool, in metres of radius scale
    blobs = [_rot_xz(x * S, z * S, pool_dir) + (r * S, sx, sz)
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
        sx_, sz_ = _rot_xz(0.25 * S + math.cos(a) * rr, math.sin(a) * rr * 0.75, pool_dir)
        b = add_cylinder(TAG + f"splat_{i}", r, 0.008, (sx_, y, sz_),
                         rotation=(math.pi / 2, rng.uniform(0, 3.0), 0.0), vertices=10)
        b.scale = (rng.uniform(0.7, 1.9), rng.uniform(0.6, 1.2), 1.0)
        objs.append(b)

    # thin runnels creeping out of the pool
    for i in range(7):
        a = rng.uniform(-1.0, 1.6)
        x0, z0 = _rot_xz((0.30 + math.cos(a) * 0.38) * S, math.sin(a) * 0.30 * S, pool_dir)
        a = a - pool_dir
        L = rng.uniform(0.20, 0.52) * S
        run = add_box(TAG + f"runnel_{i}", (0.026 + rng.uniform(0, 0.018), 0.008, L),
                      (x0 + math.cos(a) * L * 0.5, y, z0 + math.sin(a) * L * 0.5),
                      rotation=(0.0, -a + math.pi / 2, 0.0))
        objs.append(run)

    _mat_all(objs, mats["ichor_pool"])
    _parent_to(objs, parent)
    return objs


def _build_cracks(mats, parent, pool_dir):
    """Spiderweb fracture radiating in the crystal under the head."""
    rng = random.Random(3)
    objs = []
    y = 0.0016            # all but flush with the floor plane
    idx = 0

    def bar(x0, z0, ang, length, width):
        nonlocal idx
        b = add_box(TAG + f"crack_{idx}", (width, 0.0020, length),
                    (x0 + math.sin(ang) * length * 0.5, y, z0 + math.cos(ang) * length * 0.5),
                    rotation=(0.0, ang, 0.0))
        idx += 1
        objs.append(b)

    for i in range(17):
        a = i / 17.0 * math.tau + rng.uniform(-0.09, 0.09)
        x, z = _rot_xz(math.cos(a) * 0.05, math.sin(a) * 0.05, pool_dir)
        ang = math.pi / 2 - a
        total = rng.uniform(0.34, 0.80)
        walked = 0.0
        w = 0.014
        while walked < total:
            L = min(rng.uniform(0.12, 0.26), total - walked)
            bar(x, z, ang, L, w)
            x += math.sin(ang) * L
            z += math.cos(ang) * L
            walked += L
            ang += rng.uniform(-0.34, 0.34)
            w = max(0.005, w * 0.80)
            # branch
            if rng.random() < 0.45 and walked < total * 0.8:
                ba = ang + rng.choice((-1, 1)) * rng.uniform(0.5, 1.0)
                bar(x, z, ba, rng.uniform(0.10, 0.26), max(0.004, w * 0.8))

    # a few concentric chordal cracks tying the web together
    for i in range(9):
        a = rng.uniform(0, math.tau)
        rr = rng.uniform(0.18, 0.62)
        bar(math.cos(a) * rr, math.sin(a) * rr,
            math.pi / 2 - a + math.pi / 2 + rng.uniform(-0.3, 0.3),
            rng.uniform(0.14, 0.38), rng.uniform(0.005, 0.010))

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

    # The walk only reads at an angle: a stride along the view axis is
    # invisible. The body therefore sits on its own Empty, yawed inside
    # the group, so scene_main's own rotation lands it three-quarter on.
    body = bpy.data.objects.new(TAG + "fiend_body", None)
    bpy.context.collection.objects.link(body)
    body.parent = fiend_root
    body.rotation_euler = (0.0, FIEND_GAIT_YAW, 0.0)
    _build_fiend(mats, body)

    # the head itself hangs off a pivot that rolls it onto its cheek
    pivot = bpy.data.objects.new(TAG + "head_pivot", None)
    bpy.context.collection.objects.link(pivot)
    pivot.parent = head_root
    # ZYX order so the roll happens FIRST, about the head's own face axis
    # (tipping it onto its left cheek, face still horizontal), and only
    # then the yaw turns it. In the default XYZ order the roll is applied
    # about the world axis after the yaw, which faceplants the head.
    pivot.rotation_mode = "ZYX"
    pivot.rotation_euler = (math.radians(-9.0), HEAD_YAW, math.radians(62.0))
    pivot.scale = (HEAD_SCALE, HEAD_SCALE, HEAD_SCALE)
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

    # spread the pool along the direction the stump actually ends up facing
    sd = pivot.matrix_world.to_3x3() @ STUMP_DIR_LOCAL
    pool_dir = math.atan2(sd.z, sd.x)
    _build_pool(mats, head_root, pool_dir)
    _build_cracks(mats, head_root, pool_dir)

    return {"root": root, "fiend": fiend_root, "head": head_root}


if __name__ == "__main__":
    build()
