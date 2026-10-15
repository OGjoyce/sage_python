"""Commander Lys — hero character module for "Evening Breath".

Tall athletic woman, 1.85 m, standing calm and grounded, feet at Y=0,
facing +Z (toward camera).  Ivory-and-gold ceremonial plate, stepped
tiered pauldrons, large engraved solar-disc pectoral, crystal diadem,
black low braid, short wind-blown pale cloak with a gold hem, a slim
emissive white-gold blade held low in her right hand (tip to the floor)
and a glowing recording shard cupped in her left.

Axis convention per CONVENTIONS.md: Y up, +Z toward camera, 1 unit = 1 m.
Her right hand is on -X (she faces the camera), her left hand on +X.

No lights, no camera, no scene reset.  Everything is prefixed `LYS_` and
parented to the `LYS_root` Empty.
"""

import math
import os
import sys

sys.path.insert(0, "/home/user/sage_python/studio")

import bpy  # noqa: E402
import bmesh  # noqa: E402
import mathutils  # noqa: E402
import claude_studio as cs  # noqa: E402
from claude_studio.characters import (  # noqa: E402
    add_box,
    add_cylinder,
    add_cone,
    add_ring,
    assign_material,
)

V = mathutils.Vector

# ----------------------------------------------------------------- palette
IVORY = (0.941, 0.925, 0.871, 1.0)
GOLD_LAW = (1.000, 0.816, 0.290, 1.0)
PALE_CLOAK = (0.878, 0.855, 0.804, 1.0)
CRYSTAL = (0.671, 0.788, 0.878, 1.0)
CRYSTAL_DEEP = (0.290, 0.400, 0.510, 1.0)
ICHOR = (0.027, 0.106, 0.110, 1.0)
SKIN_LYS = (0.714, 0.510, 0.361, 1.0)
WHITE_GOLD = (1.000, 0.945, 0.780, 1.0)
AMBER = (0.420, 0.180, 0.030, 1.0)

# ------------------------------------------------------------- body ladder
# (every Y landmark in one place so proportions can be tuned coherently)
HEIGHT = 1.85
Y_ANKLE = 0.095
Y_KNEE = 0.495
Y_CROTCH = 0.905
Y_HIP = 1.015
Y_WAIST = 1.145
Y_CHEST = 1.345
Y_SHOULDER = 1.455
Y_NECK = 1.520
Y_CHIN = 1.600
Y_EYE = 1.755          # skull's widest ring
Y_BROW = 1.782         # hairline reference
F_EYE = 1.737          # eye line (mid-head)
F_BROW = 1.766
F_NOSE = 1.708
F_MOUTH = 1.660
Y_TOP = 1.850

SH_X = 0.205          # shoulder joint X
HIP_X = 0.105         # hip joint X
FOOT_X = 0.128        # stance width (half)


# ============================================================== helpers ===

def _smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def _subsurf(obj, levels=2):
    m = obj.modifiers.new("Subsurf", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    return m


def _bevel(obj, width, segments=2):
    if width <= 0:
        return None
    m = obj.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(35)
    return m


def _frames(pts):
    """Parallel-transported orthonormal frames along a polyline."""
    n = len(pts)
    tans = []
    for i in range(n):
        if i == 0:
            t = V(pts[1]) - V(pts[0])
        elif i == n - 1:
            t = V(pts[-1]) - V(pts[-2])
        else:
            t = V(pts[i + 1]) - V(pts[i - 1])
        tans.append(t.normalized())
    ref = V((0.0, 0.0, 1.0)) if abs(tans[0].dot(V((0, 1, 0)))) > 0.8 else V((0.0, 1.0, 0.0))
    u = ref.cross(tans[0]).normalized()
    frames = []
    for i, t in enumerate(tans):
        # re-orthogonalize the carried u against the new tangent
        u = (u - t * u.dot(t))
        if u.length < 1e-6:
            u = V((1.0, 0.0, 0.0))
        u.normalize()
        v = t.cross(u).normalized()
        frames.append((u, v))
    return frames


def _tube(name, pts, radii, mat, sides=8, subdiv=2, smooth=True, caps=True,
          thickness=None, bevel=0.0):
    """Lofted tube with rings perpendicular to the centreline.

    `radii` is one (half_u, half_v) per point.  With subdiv=2 + smooth this
    is the organic workhorse: limbs, torso, neck, head, braid cores.
    """
    frames = _frames(pts)
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        u, v = frames[i]
        hu, hv = radii[i]
        ring = []
        for k in range(sides):
            a = 2.0 * math.pi * k / sides
            off = u * (hu * math.cos(a)) + v * (hv * math.sin(a))
            ring.append(bm.verts.new((p[0] + off.x, p[1] + off.y, p[2] + off.z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(sides):
            j = (k + 1) % sides
            bm.faces.new([rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]])
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if thickness:
        s = obj.modifiers.new("Solidify", "SOLIDIFY")
        s.thickness = thickness
        s.offset = 0.0
    _bevel(obj, bevel)
    if subdiv:
        _subsurf(obj, subdiv)
    if smooth:
        _smooth(obj)
    assign_material(obj, mat)
    return obj


def _plate(name, dims, loc, mat, rot=(0, 0, 0), bevel=0.008, seg=2):
    obj = add_box(name, dims, loc, rotation=rot)
    obj.modifiers.clear()
    _bevel(obj, bevel, seg)
    obj.modifiers.new("Triangulate", "TRIANGULATE")
    assign_material(obj, mat)
    return obj


def _organic_box(name, dims, loc, mat, rot=(0, 0, 0), levels=2):
    obj = add_box(name, dims, loc, rotation=rot)
    obj.modifiers.clear()
    _subsurf(obj, levels)
    _smooth(obj)
    assign_material(obj, mat)
    return obj


# =============================================================== cloak ====

def _build_cloak(mat_cloth, mat_gold):
    """Short pale cloak, wind-swept to her left (+X) and billowing back.

    Built as a parametric grid (theta around the body x v down the cloth),
    solidified for thickness and subdivided so it reads as cloth.  The last
    two V-rows get material slot 1 -> a distinct gold hem band.
    """
    NU, NV = 30, 15
    HEM_ROWS = 1
    bm = bmesh.new()
    grid = []
    for iv in range(NV):
        v = iv / (NV - 1.0)
        row = []
        for iu in range(NU):
            t = iu / (NU - 1.0)
            theta = math.radians(-142.0 + 284.0 * t)      # 0 = straight behind
            # base shell around the torso, flaring as it falls
            r = 0.190 + 0.215 * (v ** 1.2)
            r += 0.042 * math.sin(4.0 * theta) * (0.25 + v)   # vertical folds
            y = (Y_NECK + 0.030) - 0.680 * v
            x = r * math.sin(theta)
            z = -r * math.cos(theta) - 0.030
            # wind: sweep toward her left (+X), billow backward, hem curls up
            lift = 0.5 * (1.0 + math.sin(theta))          # 1 on her left side
            x += 0.235 * (v ** 1.9) * (0.35 + 0.65 * lift)
            z -= 0.150 * (v ** 1.8) * (0.4 + 0.6 * lift)
            y += 0.185 * (v ** 2.4) * lift                # trailing edge flies up
            y -= 0.035 * (v ** 2.0) * (1.0 - lift)
            z += 0.070 * (v ** 2.2) * math.cos(2.6 * theta)   # curl
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for iv in range(NV - 1):
        for iu in range(NU - 1):
            f = bm.faces.new([grid[iv][iu], grid[iv][iu + 1],
                              grid[iv + 1][iu + 1], grid[iv + 1][iu]])
            f.material_index = 1 if iv >= NV - 1 - HEM_ROWS else 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("LYS_cloak_mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("LYS_cloak", mesh)
    bpy.context.collection.objects.link(obj)
    s = obj.modifiers.new("Solidify", "SOLIDIFY")
    s.thickness = 0.016
    s.offset = 0.0
    s.material_offset = 0
    s.material_offset_rim = 0
    _subsurf(obj, 2)
    _smooth(obj)
    assign_material(obj, mat_cloth)
    assign_material(obj, mat_gold)
    return obj


# =============================================================== build ====

def build():
    M = {}
    M["skin"], _ = cs.materials.new_principled_material(
        "LYS_skin", base_color=SKIN_LYS, roughness=0.52, metallic=0.0)
    M["skin_dark"], _ = cs.materials.new_principled_material(
        "LYS_skin_dark", base_color=(0.430, 0.280, 0.190, 1.0), roughness=0.55)
    # quilted under-armour: what shows between the plates (never bare skin)
    M["under"], _ = cs.materials.new_principled_material(
        "LYS_underarmour", base_color=(0.098, 0.092, 0.105, 1.0), roughness=0.72)
    M["ivory"], _ = cs.materials.new_principled_material(
        "LYS_ivory", base_color=IVORY, roughness=0.34, metallic=0.25)
    M["ivory_dim"], _ = cs.materials.new_principled_material(
        "LYS_ivory_dim", base_color=(0.780, 0.765, 0.715, 1.0), roughness=0.42, metallic=0.2)
    M["gold"], _ = cs.materials.new_principled_material(
        "LYS_gold", base_color=GOLD_LAW, roughness=0.22, metallic=1.0)
    M["gold_deep"], _ = cs.materials.new_principled_material(
        "LYS_gold_deep", base_color=(0.760, 0.560, 0.160, 1.0), roughness=0.33, metallic=1.0)
    M["cloth"], _ = cs.materials.new_principled_material(
        "LYS_cloth", base_color=PALE_CLOAK, roughness=0.78, metallic=0.0)
    M["dark"], _ = cs.materials.new_principled_material(
        "LYS_dark", base_color=(0.065, 0.062, 0.068, 1.0), roughness=0.58)
    M["hair"], _ = cs.materials.new_principled_material(
        "LYS_hair", base_color=(0.030, 0.026, 0.030, 1.0), roughness=0.40)
    M["crystal"], _ = cs.materials.new_principled_material(
        "LYS_crystal", base_color=CRYSTAL, roughness=0.08, metallic=0.0,
        transmission=0.62, ior=1.52,
        emission_color=(0.420, 0.620, 0.780, 1.0), emission_strength=1.1)
    M["blade"], _ = cs.materials.new_principled_material(
        "LYS_blade_light", base_color=WHITE_GOLD, roughness=0.15,
        emission_color=(1.000, 0.905, 0.640, 1.0), emission_strength=9.0)
    M["blade_core"], _ = cs.materials.new_principled_material(
        "LYS_blade_core", base_color=(1.0, 1.0, 0.95, 1.0), roughness=0.1,
        emission_color=(1.000, 0.960, 0.830, 1.0), emission_strength=14.0)
    M["shard"], _ = cs.materials.new_principled_material(
        "LYS_shard_light", base_color=(1.0, 0.97, 0.86, 1.0), roughness=0.1,
        transmission=0.3, emission_color=(1.000, 0.930, 0.720, 1.0),
        emission_strength=13.0)
    M["eye"], _ = cs.materials.new_principled_material(
        "LYS_eye", base_color=AMBER, roughness=0.18,
        emission_color=(0.780, 0.380, 0.070, 1.0), emission_strength=1.1)
    M["scar"], _ = cs.materials.new_principled_material(
        "LYS_scar_tone", base_color=(0.330, 0.200, 0.140, 1.0), roughness=0.45)
    M["ichor"], _ = cs.materials.new_principled_material(
        "LYS_ichor", base_color=ICHOR, roughness=0.18,
        emission_color=(0.040, 0.240, 0.250, 1.0), emission_strength=0.5)

    parts = []

    def P(obj):
        parts.append(obj)
        return obj

    # ------------------------------------------------------------- legs ---
    for side, sx in (("R", -1.0), ("L", 1.0)):
        hx = sx * HIP_X
        kx = sx * (FOOT_X - 0.012)
        ax = sx * FOOT_X
        # organic leg: hip -> knee -> ankle, athletic taper
        P(_tube(
            f"LYS_thigh_{side}",
            [(hx, Y_CROTCH + 0.115, 0.012), (hx * 1.05, Y_CROTCH - 0.09, 0.016),
             (hx * 1.15 + sx * 0.012, Y_KNEE + 0.10, 0.012), (kx, Y_KNEE, 0.004)],
            [(0.092, 0.101), (0.086, 0.095), (0.070, 0.077), (0.060, 0.065)],
            M["under"]))
        P(_tube(
            f"LYS_shin_{side}",
            [(kx, Y_KNEE + 0.01, 0.004), (kx, Y_KNEE - 0.14, 0.014),
             (ax, Y_ANKLE + 0.09, -0.006), (ax, Y_ANKLE, -0.014)],
            [(0.064, 0.069), (0.064, 0.072), (0.040, 0.045), (0.034, 0.038)],
            M["under"]))
        # armoured foot (sabaton) + toe cap
        P(_plate(f"LYS_sabaton_{side}", (0.104, 0.076, 0.228),
                 (ax, 0.040, 0.038), M["ivory"], rot=(0, sx * math.radians(11), 0),
                 bevel=0.012))
        P(_plate(f"LYS_toecap_{side}", (0.090, 0.044, 0.066),
                 (ax + sx * 0.010, 0.026, 0.148), M["gold_deep"],
                 rot=(math.radians(-10), sx * math.radians(11), 0), bevel=0.010))
        # greave: ivory shin plate + gold centre strip
        P(_tube(
            f"LYS_greave_{side}",
            [(ax, Y_ANKLE + 0.02, 0.0), (kx, Y_KNEE - 0.17, 0.010), (kx, Y_KNEE - 0.015, 0.004)],
            [(0.050, 0.055), (0.078, 0.087), (0.080, 0.088)],
            M["ivory"], subdiv=0, smooth=False, bevel=0.009))
        P(_plate(f"LYS_greave_trim_{side}", (0.024, 0.33, 0.020),
                 (ax + sx * 0.004, 0.295, 0.058), M["gold"], bevel=0.005))
        # knee poleyn
        P(_plate(f"LYS_poleyn_{side}", (0.098, 0.096, 0.072),
                 (kx, Y_KNEE + 0.012, 0.042), M["ivory"],
                 rot=(0, 0, 0), bevel=0.020, seg=3))
        P(_plate(f"LYS_poleyn_rim_{side}", (0.108, 0.020, 0.058),
                 (kx, Y_KNEE - 0.044, 0.042), M["gold"], bevel=0.005))
        # cuisse: ivory plate down the front/outer thigh
        P(_tube(
            f"LYS_cuisse_{side}",
            [(sx * 0.108, 0.880, 0.026), (sx * 0.116, 0.730, 0.028),
             (kx, Y_KNEE + 0.085, 0.020)],
            [(0.100, 0.109), (0.088, 0.096), (0.076, 0.082)],
            M["ivory_dim"], subdiv=0, smooth=False, caps=False, thickness=0.016, bevel=0.009))
        # tasset over the outer hip
        P(_plate(f"LYS_tasset_{side}", (0.058, 0.165, 0.170),
                 (sx * 0.170, 0.885, 0.018), M["ivory"],
                 rot=(0, 0, sx * math.radians(9)), bevel=0.014))

    # ------------------------------------------------------------ torso ---
    P(_tube(
        "LYS_torso",
        [(0.0, Y_CROTCH - 0.02, 0.0), (0.0, Y_HIP, 0.004), (0.0, Y_WAIST, 0.004),
         (0.0, 1.265, 0.010), (0.0, Y_CHEST, 0.012), (0.0, Y_SHOULDER, 0.006),
         (0.0, Y_NECK, -0.002)],
        [(0.150, 0.108), (0.158, 0.112), (0.112, 0.086), (0.148, 0.106),
         (0.168, 0.112), (0.192, 0.104), (0.148, 0.090)],
        M["under"]))
    # hips / seat volume
    P(_organic_box("LYS_pelvis", (0.30, 0.21, 0.245), (0.0, Y_HIP - 0.035, -0.012),
                   M["under"]))

    # ---- cuirass: ivory plate shell over the torso, hard surface + bevel
    P(_tube(
        "LYS_cuirass",
        [(0.0, Y_HIP - 0.015, 0.004), (0.0, Y_WAIST + 0.005, 0.006),
         (0.0, 1.270, 0.012), (0.0, Y_CHEST + 0.010, 0.014),
         (0.0, Y_SHOULDER + 0.015, 0.006)],
        [(0.162, 0.118), (0.124, 0.094), (0.168, 0.120), (0.196, 0.130), (0.208, 0.117)],
        M["ivory"], subdiv=0, smooth=False, bevel=0.010))
    # breastplate keel + feminine chest shaping
    P(_plate("LYS_keel", (0.052, 0.300, 0.060), (0.0, 1.300, 0.126),
             M["gold"], bevel=0.008))
    for side, sx in (("R", -1.0), ("L", 1.0)):
        P(_plate(f"LYS_chest_curve_{side}", (0.150, 0.130, 0.080),
                 (sx * 0.085, 1.330, 0.098), M["ivory"],
                 rot=(0, 0, sx * math.radians(-6)), bevel=0.028, seg=4))
    # gold trim bands: collar flange, waist, fauld edges
    P(_tube("LYS_cuirass_trim_top",
            [(0.0, Y_SHOULDER + 0.004, 0.006), (0.0, Y_SHOULDER + 0.030, 0.004)],
            [(0.212, 0.122), (0.206, 0.117)],
            M["gold"], subdiv=0, smooth=False, caps=False, thickness=0.013, bevel=0.004))
    P(_tube("LYS_belt",
            [(0.0, Y_WAIST - 0.028, 0.006), (0.0, Y_WAIST + 0.030, 0.006)],
            [(0.134, 0.102), (0.134, 0.102)],
            M["gold_deep"], subdiv=0, smooth=False, caps=False, thickness=0.016, bevel=0.004))
    P(_plate("LYS_belt_buckle", (0.085, 0.075, 0.035), (0.0, Y_WAIST, 0.112),
             M["gold"], bevel=0.010))

    # ---- faulds: two stepped skirt tiers under the cuirass
    P(_tube("LYS_fauld_1",
            [(0.0, Y_HIP + 0.012, 0.004), (0.0, Y_HIP - 0.075, 0.002)],
            [(0.172, 0.126), (0.192, 0.140)],
            M["ivory"], subdiv=0, smooth=False, caps=False, thickness=0.018, bevel=0.007))
    P(_tube("LYS_fauld_1_hem",
            [(0.0, Y_HIP - 0.080, 0.002), (0.0, Y_HIP - 0.100, 0.002)],
            [(0.193, 0.141), (0.199, 0.145)],
            M["gold"], subdiv=0, smooth=False, caps=False, thickness=0.015, bevel=0.004))
    P(_tube("LYS_fauld_2",
            [(0.0, Y_HIP - 0.085, 0.002), (0.0, 0.858, 0.0)],
            [(0.186, 0.136), (0.208, 0.151)],
            M["ivory_dim"], subdiv=0, smooth=False, caps=False, thickness=0.018, bevel=0.007))
    P(_tube("LYS_fauld_2_hem",
            [(0.0, 0.856, 0.0), (0.0, 0.834, 0.0)],
            [(0.209, 0.152), (0.215, 0.156)],
            M["gold"], subdiv=0, smooth=False, caps=False, thickness=0.015, bevel=0.004))

    # ---- gorget / collar
    P(_tube("LYS_gorget",
            [(0.0, Y_NECK - 0.020, 0.0), (0.0, Y_NECK + 0.068, -0.004)],
            [(0.130, 0.106), (0.106, 0.090)],
            M["ivory"], subdiv=0, smooth=False, caps=False, thickness=0.020, bevel=0.008))
    P(_tube("LYS_gorget_trim",
            [(0.0, Y_NECK + 0.066, -0.004), (0.0, Y_NECK + 0.086, -0.004)],
            [(0.106, 0.090), (0.102, 0.087)],
            M["gold"], subdiv=0, smooth=False, caps=False, thickness=0.014, bevel=0.004))

    # ----------------------------------------- solar-disc pectoral (hero) --
    DX, DY, DZ = 0.0, 1.302, 0.138
    back = add_cylinder("LYS_disc_back", 0.150, 0.030, (DX, DY, DZ - 0.010), vertices=24)
    back.modifiers.clear()
    _bevel(back, 0.008, 2)
    back.modifiers.new("Triangulate", "TRIANGULATE")
    assign_material(back, M["gold_deep"])
    P(back)
    disc = add_cylinder("LYS_solar_disc", 0.132, 0.034, (DX, DY, DZ + 0.012), vertices=32)
    disc.modifiers.clear()
    _bevel(disc, 0.006, 2)
    disc.modifiers.new("Triangulate", "TRIANGULATE")
    assign_material(disc, M["gold"])
    P(disc)
    rim = add_ring("LYS_solar_rim", 0.146, 0.126, 0.040, (DX, DY, DZ + 0.014), vertices=32)
    rim.modifiers.clear()
    _bevel(rim, 0.004, 2)
    rim.modifiers.new("Triangulate", "TRIANGULATE")
    assign_material(rim, M["gold"])
    P(rim)
    # engraved radiating rays
    for i in range(16):
        a = 2.0 * math.pi * i / 16.0
        rr = 0.090
        P(_plate(f"LYS_solar_ray_{i}", (0.068, 0.017, 0.016),
                 (DX + rr * math.cos(a), DY + rr * math.sin(a), DZ + 0.030),
                 M["gold"], rot=(0, 0, a), bevel=0.004))
    inner = add_cylinder("LYS_solar_boss", 0.054, 0.040, (DX, DY, DZ + 0.030), vertices=24)
    inner.modifiers.clear()
    _bevel(inner, 0.008, 2)
    inner.modifiers.new("Triangulate", "TRIANGULATE")
    assign_material(inner, M["gold"])
    P(inner)
    core = add_cylinder("LYS_solar_core", 0.026, 0.046, (DX, DY, DZ + 0.034), vertices=16)
    core.modifiers.clear()
    core.modifiers.new("Triangulate", "TRIANGULATE")
    assign_material(core, M["crystal"])
    P(core)

    # -------------------------------------------- stepped tiered pauldrons --
    for side, sx in (("R", -1.0), ("L", 1.0)):
        tiers = (
            (0.168, 0.086, 0.250, 0.210, 1.504, 14.0),
            (0.182, 0.086, 0.268, 0.250, 1.422, 32.0),
            (0.178, 0.084, 0.246, 0.276, 1.330, 52.0),
        )
        for i, (w, h, d, cx, cy, deg) in enumerate(tiers):
            rz = -sx * math.radians(deg)
            P(_plate(f"LYS_pauldron_{side}{i}", (w, h, d), (sx * cx, cy, 0.004),
                     M["ivory"], rot=(0, 0, rz), bevel=0.034, seg=4))
            # gold lip on the outer-lower edge of each step
            P(_plate(f"LYS_pauldron_lip_{side}{i}", (w * 1.04, 0.020, d * 1.03),
                     (sx * (cx + 0.004), cy - h * 0.52 - 0.006, 0.004),
                     M["gold"], rot=(0, 0, rz), bevel=0.005))
        # shoulder cap connecting to the gorget
        P(_plate(f"LYS_shoulder_cap_{side}", (0.150, 0.100, 0.215),
                 (sx * 0.155, 1.494, 0.004), M["ivory"],
                 rot=(0, 0, -sx * math.radians(6)), bevel=0.028, seg=3))
        # cloak clasp
        P(_plate(f"LYS_clasp_{side}", (0.055, 0.055, 0.040),
                 (sx * 0.150, 1.505, -0.070), M["gold"], bevel=0.010))

    # ------------------------------------------------------------- arms ---
    # right arm (her right = -X) hangs low, holding the blade
    r_sh = (-SH_X, Y_SHOULDER - 0.015, 0.004)
    r_el = (-0.262, 1.118, 0.012)
    r_wr = (-0.292, 0.912, 0.104)
    r_hand = (-0.305, 0.845, 0.152)
    P(_tube("LYS_upperarm_R",
            [r_sh, (-0.232, 1.290, 0.008), r_el],
            [(0.060, 0.064), (0.052, 0.055), (0.043, 0.045)], M["under"]))
    P(_tube("LYS_forearm_R",
            [r_el, (-0.262, 1.010, 0.052), r_wr],
            [(0.044, 0.046), (0.038, 0.040), (0.031, 0.033)], M["under"]))
    # left arm (her left = +X) bent forward, cupping the shard
    l_sh = (SH_X, Y_SHOULDER - 0.015, 0.004)
    l_el = (0.254, 1.170, 0.008)
    l_wr = (0.236, 1.072, 0.188)
    l_hand = (0.222, 1.048, 0.258)
    P(_tube("LYS_upperarm_L",
            [l_sh, (0.230, 1.292, 0.010), l_el],
            [(0.060, 0.064), (0.052, 0.055), (0.043, 0.045)], M["under"]))
    P(_tube("LYS_forearm_L",
            [l_el, (0.248, 1.108, 0.098), l_wr],
            [(0.044, 0.046), (0.038, 0.040), (0.031, 0.033)], M["under"]))

    for side, sh, el, wr, hand, sx in (("R", r_sh, r_el, r_wr, r_hand, -1.0),
                                       ("L", l_sh, l_el, l_wr, l_hand, 1.0)):
        # rerebrace (upper arm plate)
        P(_tube(f"LYS_rerebrace_{side}",
                [(sh[0] + sx * 0.012, sh[1] - 0.045, sh[2]), (el[0], el[1] + 0.085, el[2])],
                [(0.062, 0.066), (0.049, 0.052)],
                M["ivory_dim"], subdiv=0, smooth=False, caps=False, thickness=0.016, bevel=0.008))
        # couter (elbow)
        P(_plate(f"LYS_couter_{side}", (0.078, 0.078, 0.084), (el[0], el[1], el[2]),
                 M["ivory"], bevel=0.022, seg=3))
        # vambrace + gold edge
        P(_tube(f"LYS_vambrace_{side}",
                [(el[0], el[1] - 0.030, el[2] + 0.012), (wr[0], wr[1] + 0.030, wr[2] - 0.010)],
                [(0.049, 0.053), (0.037, 0.041)],
                M["ivory"], subdiv=0, smooth=False, caps=False, thickness=0.016, bevel=0.008))
        P(_tube(f"LYS_vambrace_trim_{side}",
                [(wr[0], wr[1] + 0.034, wr[2] - 0.010), (wr[0], wr[1] + 0.012, wr[2] - 0.002)],
                [(0.039, 0.043), (0.040, 0.044)],
                M["gold"], subdiv=0, smooth=False, caps=False, thickness=0.013, bevel=0.004))
        # gauntlet: closed hand
        P(_organic_box(f"LYS_hand_{side}", (0.082, 0.112, 0.092), hand, M["ivory"]))
        P(_plate(f"LYS_gauntlet_cuff_{side}", (0.090, 0.055, 0.095),
                 (hand[0], hand[1] + 0.068, hand[2] - 0.022), M["gold_deep"], bevel=0.010))

    # knuckle plates (reads as a fist, not a mitten)
    for i in range(3):
        P(_plate(f"LYS_knuckle_R{i}", (0.022, 0.030, 0.070),
                 (r_hand[0] - 0.026 + i * 0.026, r_hand[1] - 0.038, r_hand[2] + 0.018),
                 M["ivory"], bevel=0.007))

    # ---------------------------------- blade of white-gold light (right) --
    # local space: blade runs along -Y from the grip at the origin.
    blade_rot = (math.radians(-27.0), 0.0, math.radians(-11.0))
    BL = 0.96

    def _blade_mesh():
        bm = bmesh.new()
        prof = [(0.0, 0.034, 0.011), (0.10, 0.038, 0.012), (0.42, 0.031, 0.0095),
                (0.74, 0.022, 0.007), (0.92, 0.012, 0.004)]
        rings = []
        for t, hw, hd in prof:
            y = -t * BL
            rings.append([bm.verts.new(p) for p in
                          ((-hw, y, -hd), (hw, y, -hd), (hw, y, hd), (-hw, y, hd))])
        for i in range(len(rings) - 1):
            for k in range(4):
                j = (k + 1) % 4
                bm.faces.new([rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]])
        bm.faces.new(list(reversed(rings[0])))
        tip = bm.verts.new((0.0, -BL, 0.0))
        for k in range(4):
            j = (k + 1) % 4
            bm.faces.new([rings[-1][k], rings[-1][j], tip])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        mesh = bpy.data.meshes.new("LYS_blade_mesh")
        bm.to_mesh(mesh)
        bm.free()
        o = bpy.data.objects.new("LYS_blade", mesh)
        bpy.context.collection.objects.link(o)
        return o

    blade = _blade_mesh()
    blade.location = (r_hand[0], r_hand[1] + 0.02, r_hand[2])
    blade.rotation_euler = blade_rot
    assign_material(blade, M["blade"])
    P(blade)
    # hotter inner core line
    core_b = add_box("LYS_blade_core", (0.013, BL * 0.93, 0.016),
                     (0.0, -BL * 0.47, 0.0))
    core_b.modifiers.clear()
    core_b.parent = blade
    assign_material(core_b, M["blade_core"])
    P(core_b)
    grip = add_box("LYS_blade_grip", (0.034, 0.165, 0.040), (0.0, 0.028, 0.0))
    grip.modifiers.clear()
    _bevel(grip, 0.008, 2)
    grip.parent = blade
    assign_material(grip, M["dark"])
    P(grip)
    guard = add_box("LYS_blade_guard", (0.185, 0.030, 0.052), (0.0, -0.040, 0.0))
    guard.modifiers.clear()
    _bevel(guard, 0.008, 2)
    guard.parent = blade
    assign_material(guard, M["gold"])
    P(guard)
    pommel = add_box("LYS_blade_pommel", (0.046, 0.050, 0.046), (0.0, 0.122, 0.0))
    pommel.modifiers.clear()
    _bevel(pommel, 0.014, 3)
    pommel.parent = blade
    assign_material(pommel, M["gold"])
    P(pommel)

    # ------------------------------------- recording shard (left hand) ----
    sh_loc = (l_hand[0] + 0.012, l_hand[1] + 0.012, l_hand[2] + 0.030)
    shard = add_cone("LYS_shard", 0.050, 0.016, 0.120, sh_loc,
                     rotation=(math.radians(28), 0, math.radians(-18)), vertices=6)
    shard.modifiers.clear()
    assign_material(shard, M["shard"])
    P(shard)
    shard2 = add_cone("LYS_shard_b", 0.036, 0.010, 0.090,
                      (sh_loc[0] - 0.022, sh_loc[1] - 0.004, sh_loc[2] + 0.004),
                      rotation=(math.radians(16), 0, math.radians(26)), vertices=6)
    shard2.modifiers.clear()
    assign_material(shard2, M["shard"])
    P(shard2)
    # fingers closed over it, with gaps for the light to leak through
    for i in range(4):
        P(_plate(f"LYS_finger_L{i}", (0.017, 0.030, 0.082),
                 (l_hand[0] - 0.030 + i * 0.024, l_hand[1] - 0.022,
                  l_hand[2] + 0.028 - i * 0.004),
                 M["ivory"], rot=(math.radians(-22), 0, 0), bevel=0.006))
    P(_plate("LYS_thumb_L", (0.026, 0.070, 0.026),
             (l_hand[0] + 0.042, l_hand[1] + 0.006, l_hand[2] + 0.034),
             M["ivory"], rot=(math.radians(-18), 0, math.radians(32)), bevel=0.007))

    # ichor smear on the LEFT gauntlet (dark teal, thin)
    for i, (dx, dy, dz, w, h) in enumerate((
            (-0.016, 0.030, 0.040, 0.036, 0.020),
            (0.018, 0.016, 0.044, 0.024, 0.015),
            (-0.032, 0.002, 0.030, 0.020, 0.028))):
        P(_plate(f"LYS_ichor_{i}", (w, h, 0.012),
                 (l_hand[0] + dx, l_hand[1] + dy, l_hand[2] + dz),
                 M["ichor"], rot=(0, 0, math.radians(18 * i - 14)), bevel=0.004))
    P(_plate("LYS_ichor_3", (0.022, 0.042, 0.014),
             (l_wr[0] + 0.030, l_wr[1] - 0.010, l_wr[2] + 0.030),
             M["ichor"], rot=(math.radians(14), 0, math.radians(26)), bevel=0.004))

    # ------------------------------------------------------- neck + head --
    P(_tube("LYS_neck",
            [(0.0, Y_NECK - 0.040, -0.004), (0.0, Y_CHIN - 0.020, 0.000)],
            [(0.062, 0.060), (0.054, 0.054)], M["skin"]))
    P(_tube(
        "LYS_head",
        [(0.0, Y_CHIN - 0.006, 0.014), (0.0, 1.632, 0.010), (0.0, 1.678, 0.004),
         (0.0, Y_EYE - 0.030, 0.0), (0.0, Y_EYE, 0.0), (0.0, Y_BROW + 0.018, -0.002),
         (0.0, 1.820, -0.008), (0.0, Y_TOP - 0.012, -0.014)],
        [(0.044, 0.052), (0.064, 0.078), (0.076, 0.090), (0.082, 0.098),
         (0.084, 0.100), (0.082, 0.098), (0.074, 0.088), (0.052, 0.062)],
        M["skin"]))
    # jaw / chin definition
    P(_organic_box("LYS_jaw", (0.112, 0.064, 0.108), (0.0, 1.642, 0.022), M["skin"]))
    # nose
    P(_organic_box("LYS_nose", (0.026, 0.058, 0.044), (0.0, F_NOSE + 0.014, 0.078), M["skin"]))
    # eyes (dark amber, steady) in shallow sockets
    for side, sx in (("R", -1.0), ("L", 1.0)):
        P(_plate(f"LYS_socket_{side}", (0.046, 0.019, 0.014),
                 (sx * 0.040, F_EYE, 0.060), M["skin_dark"], bevel=0.005))
        eye = add_cylinder(f"LYS_eye_{side}", 0.0105, 0.014,
                           (sx * 0.040, F_EYE + 0.001, 0.070),
                           rotation=(math.radians(90), 0, 0), vertices=12)
        eye.modifiers.clear()
        assign_material(eye, M["eye"])
        P(eye)
        # brow ridge
        P(_plate(f"LYS_brow_{side}", (0.048, 0.008, 0.014),
                 (sx * 0.041, F_BROW, 0.068), M["hair"],
                 rot=(0, 0, -sx * math.radians(8)), bevel=0.002))
        # upper lash line keeps the eyes from reading as beads
        P(_plate(f"LYS_lash_{side}", (0.042, 0.006, 0.012),
                 (sx * 0.040, F_EYE + 0.010, 0.071), M["dark"], bevel=0.002))
    # mouth: calm, closed, level
    P(_plate("LYS_mouth", (0.040, 0.008, 0.014), (0.0, F_MOUTH, 0.070),
             M["skin_dark"], bevel=0.003))
    # scar through her LEFT eyebrow (+X), a thin dark inset bar
    P(_plate("LYS_scar", (0.0080, 0.054, 0.012), (0.047, F_BROW + 0.004, 0.063),
             M["scar"], rot=(0, 0, math.radians(-14)), bevel=0.002))
    # ears
    for side, sx in (("R", -1.0), ("L", 1.0)):
        P(_organic_box(f"LYS_ear_{side}", (0.015, 0.042, 0.026),
                       (sx * 0.082, 1.722, -0.010), M["skin"], levels=1))

    # ------------------------------------------------ hair + tight braid --
    P(_tube("LYS_hair_cap",
            [(0.0, Y_BROW + 0.006, -0.004), (0.0, 1.806, -0.010),
             (0.0, 1.832, -0.016), (0.0, Y_TOP - 0.006, -0.024)],
            [(0.096, 0.108), (0.096, 0.110), (0.084, 0.096), (0.050, 0.060)],
            M["hair"]))
    P(_tube("LYS_hair_back",
            [(0.0, 1.830, -0.028), (0.0, 1.766, -0.048), (0.0, 1.700, -0.062),
             (0.0, 1.640, -0.072), (0.0, 1.604, -0.076)],
            [(0.086, 0.070), (0.092, 0.072), (0.088, 0.066), (0.072, 0.052),
             (0.054, 0.040)],
            M["hair"]))
    # tight low braid: segmented tapered plait down her back, drifting to
    # her right (-X) so it clears the wind-swept cloak and breaks the
    # silhouette edge.
    braid_pts = [(0.000, 1.616, -0.084), (-0.058, 1.610, -0.062),
                 (-0.098, 1.598, -0.020), (-0.124, 1.572, 0.038),
                 (-0.148, 1.508, 0.096), (-0.170, 1.420, 0.126),
                 (-0.182, 1.328, 0.132), (-0.188, 1.236, 0.126),
                 (-0.188, 1.168, 0.112)]
    P(_tube("LYS_braid_core", braid_pts,
            [(0.042, 0.040), (0.042, 0.040), (0.041, 0.039), (0.039, 0.037),
             (0.036, 0.034), (0.032, 0.030), (0.027, 0.025), (0.021, 0.019),
             (0.014, 0.013)],
            M["hair"], sides=6))
    # plait knuckles: alternating lobes along the braid
    for i in range(13):
        t = i / 12.0
        seg = t * (len(braid_pts) - 1)
        i0 = min(int(seg), len(braid_pts) - 2)
        f = seg - i0
        px = braid_pts[i0][0] + (braid_pts[i0 + 1][0] - braid_pts[i0][0]) * f
        py = braid_pts[i0][1] + (braid_pts[i0 + 1][1] - braid_pts[i0][1]) * f
        pz = braid_pts[i0][2] + (braid_pts[i0 + 1][2] - braid_pts[i0][2]) * f
        s = 1.0 - 0.52 * t
        side = 1.0 if i % 2 == 0 else -1.0
        P(_organic_box(f"LYS_braid_lobe_{i}",
                       (0.094 * s, 0.046 * s, 0.084 * s),
                       (px + side * 0.016 * s, py, pz + side * 0.006 * s),
                       M["hair"], rot=(0, 0, side * math.radians(30)), levels=2))
    P(_plate("LYS_braid_tie", (0.050, 0.022, 0.046),
             (braid_pts[0][0], braid_pts[0][1] - 0.018, braid_pts[0][2] - 0.004),
             M["gold_deep"], bevel=0.005))
    P(_plate("LYS_braid_tie_end", (0.030, 0.016, 0.028),
             (braid_pts[-1][0] + 0.004, braid_pts[-1][1] + 0.020, braid_pts[-1][2]),
             M["gold_deep"], bevel=0.004))

    # ------------------------------------------------- crystal diadem -----
    DIA_Y = Y_BROW + 0.018
    for i in range(9):
        t = i / 8.0
        a = math.radians(-66.0 + 132.0 * t)
        rr = 0.090
        x = rr * math.sin(a)
        z = rr * math.cos(a) - 0.006
        hs = 0.030 - 0.011 * abs(t - 0.5) * 2.0
        P(_plate(f"LYS_diadem_{i}", (0.024, hs, 0.014),
                 (x, DIA_Y, z), M["crystal"],
                 rot=(0, a, 0), bevel=0.003))
    P(_tube("LYS_diadem_band",
            [(0.0, DIA_Y - 0.010, -0.004), (0.0, DIA_Y + 0.008, -0.004)],
            [(0.089, 0.100), (0.088, 0.099)],
            M["gold"], subdiv=0, smooth=False, caps=False, thickness=0.009, bevel=0.003))
    spire = add_cone("LYS_diadem_crystal", 0.019, 0.0, 0.046,
                     (0.0, DIA_Y + 0.024, 0.074), rotation=(math.radians(14), 0, 0),
                     vertices=6)
    spire.modifiers.clear()
    assign_material(spire, M["crystal"])
    P(spire)

    # ------------------------------------------------------------ cloak ---
    cloak = _build_cloak(M["cloth"], M["gold"])
    P(cloak)

    # ------------------------------------------------------------- root ---
    root = bpy.data.objects.new("LYS_root", None)
    bpy.context.collection.objects.link(root)
    for obj in parts:
        if obj.parent is None:
            obj.parent = root

    return {
        "root": root,
        "cloak": cloak,
        "blade": blade,
        "shard": shard,
        "head": bpy.data.objects["LYS_head"],
        "solar_disc": disc,
    }


if __name__ == "__main__":
    build()
