"""char_chaos.py -- the CHAOS LORD, antagonist module of "Evening Breath".

A 3 m demon warlord in a hunched predator stance, left shoulder driven
forward, a huge two-handed axe resting on that shoulder, free (right) hand
open palm-up in a lazy beckoning gesture.  Bored, contemptuous, coiled.

Conventions (see CONVENTIONS.md): Y is UP, +Z is toward the camera, 1 unit =
1 metre, feet at Y=0, built at the origin facing +Z.  No lights, no camera,
no reset_scene().  Everything is prefixed CHAOS_ and parented to CHAOS_root.

Technique notes:
  * Every organic mass (torso, limbs, head, horns, cape) is a lofted QUAD
    tube / grid carrying a Subdivision Surface modifier + smooth shading.
    Each arm and each leg is ONE continuous tube running shoulder-elbow-
    wrist / hip-knee-ankle-toe, so subdivision blends the joints into a
    single muscular limb instead of a chain of separate robot segments.
  * Armour and the axe stay hard-surface with small bevels, and are placed
    against the measured front surface of the torso (_front_z / _half_w) so
    plate actually sits proud of the hide instead of sinking into it.
  * The glowing cyan "cold lava vein" cracks are several hundred thin
    emissive strips walked across the parametric surface of every limb,
    with branching -- a network, not a pattern.

HIS LEFT is +X: a figure facing +Z is mirrored relative to the viewer, so
its left hand lies toward +X.  scene_main rotates him -28 deg about Y, which
swings that left side -- pauldron, axe, open silhouette -- toward camera.
"""

import math
import random
import sys

sys.path.insert(0, "/home/user/sage_python/studio")

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import claude_studio as cs  # noqa: E402
from claude_studio.characters import add_box, join_parts  # noqa: E402


# ======================================================== shared palette ===

OBSIDIAN = (0.047, 0.059, 0.071, 1.0)
TEAL_CRACK = (0.149, 0.898, 0.937, 1.0)
ICHOR = (0.027, 0.106, 0.110, 1.0)
UNDERLOOM = (1.000, 0.250, 0.055, 1.0)

TAG = "CHAOS_"


# ============================================================== materials ===

def _materials():
    nm = cs.materials.new_principled_material
    M = {}

    # glossy obsidian-black hide with a teal undertone; very low roughness so
    # the key light behind draws a hard specular edge along every muscle.
    mat, bsdf = nm(TAG + "obsidian", base_color=OBSIDIAN, roughness=0.11, metallic=0.25)
    cs.materials.add_noise_bump(mat, bsdf, scale=26.0, detail=6.0, strength=0.08)
    M["skin"] = mat

    M["horn"], _ = nm(TAG + "horn", base_color=(0.026, 0.034, 0.042, 1.0),
                      roughness=0.19, metallic=0.25)
    M["armor"], _ = nm(TAG + "armor", base_color=(0.030, 0.037, 0.045, 1.0),
                       roughness=0.23, metallic=0.62)
    M["armor_hi"], _ = nm(TAG + "armor_hi", base_color=(0.068, 0.080, 0.092, 1.0),
                          roughness=0.30, metallic=0.68)
    M["axe"], _ = nm(TAG + "axe_iron", base_color=(0.021, 0.026, 0.032, 1.0),
                     roughness=0.26, metallic=0.76)
    M["steel"], _ = nm(TAG + "steel", base_color=(0.265, 0.277, 0.295, 1.0),
                       roughness=0.34, metallic=0.95)
    M["bone"], _ = nm(TAG + "bone", base_color=(0.430, 0.418, 0.372, 1.0),
                      roughness=0.44)
    M["cloth"], _ = nm(TAG + "cape_cloth", base_color=(0.018, 0.022, 0.026, 1.0),
                       roughness=0.56)
    M["mouth"], _ = nm(TAG + "maw", base_color=(0.006, 0.008, 0.010, 1.0), roughness=0.55)

    # emissives -- the practical light source for the final shot.
    M["crack"], _ = nm(TAG + "crack", base_color=(0.018, 0.055, 0.062, 1.0),
                       roughness=0.30, emission_color=TEAL_CRACK, emission_strength=5.0)
    M["crack_hot"], _ = nm(TAG + "crack_hot", base_color=(0.022, 0.070, 0.078, 1.0),
                           roughness=0.28, emission_color=TEAL_CRACK, emission_strength=9.0)
    M["crack_dim"], _ = nm(TAG + "crack_dim", base_color=(0.015, 0.045, 0.050, 1.0),
                           roughness=0.34, emission_color=TEAL_CRACK, emission_strength=2.6)
    M["filigree"], _ = nm(TAG + "filigree", base_color=(0.030, 0.180, 0.195, 1.0),
                          roughness=0.26, metallic=0.85,
                          emission_color=TEAL_CRACK, emission_strength=1.6)
    M["eye"], _ = nm(TAG + "eye", base_color=(0.120, 0.700, 0.740, 1.0),
                     roughness=0.10, emission_color=TEAL_CRACK, emission_strength=14.0)
    M["ember"], _ = nm(TAG + "ember", base_color=(0.080, 0.022, 0.008, 1.0),
                       roughness=0.6, emission_color=UNDERLOOM, emission_strength=3.0)

    # black-teal ichor: wet and very glossy, barely self-lit so it reads as
    # dark fluid catching a teal highlight rather than as glowing paint.
    M["ichor"], _ = nm(TAG + "ichor", base_color=ICHOR, roughness=0.035, metallic=0.20,
                       emission_color=(0.020, 0.150, 0.160, 1.0), emission_strength=0.14)
    return M


def _mat(obj, mat):
    obj.data.materials.append(mat)
    return obj


def _smooth(obj, levels=2):
    for poly in obj.data.polygons:
        poly.use_smooth = True
    sub = obj.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = levels
    sub.render_levels = levels
    return obj


# ============================================================= primitives ===

def _frames(pts, ref=None):
    """Parallel-transported orthonormal frames along a polyline, so a lofted
    tube does not twist.  `u` is kept near `ref` (default +Z): for a mostly
    vertical tube that makes u = depth (Z) and v = width (X)."""
    n = len(pts)
    tans = []
    for i in range(n):
        if i == 0:
            d = pts[1] - pts[0]
        elif i == n - 1:
            d = pts[-1] - pts[-2]
        else:
            d = pts[i + 1] - pts[i - 1]
        if d.length < 1e-9:
            d = Vector((0, 1, 0))
        tans.append(d.normalized())

    r = Vector(ref) if ref is not None else Vector((0.0, 0.0, 1.0))
    if abs(tans[0].dot(r)) > 0.95:
        r = Vector((1.0, 0.0, 0.0))
    u0 = (r - tans[0] * tans[0].dot(r)).normalized()
    us = [u0]
    for i in range(1, n):
        q = tans[i - 1].rotation_difference(tans[i])
        u = q @ us[-1]
        u = u - tans[i] * tans[i].dot(u)
        if u.length < 1e-6:
            alt = Vector((0, 0, 1))
            u = alt - tans[i] * tans[i].dot(alt)
        us.append(u.normalized())
    vs = [tans[i].cross(us[i]).normalized() for i in range(n)]
    return tans, us, vs


def _radpair(r):
    if isinstance(r, (tuple, list)):
        return (float(r[0]), float(r[1]))
    return (float(r), float(r))


def _tube(name, pts, radii, sides=8, cap=True, ref=None):
    """A lofted quad tube.  `radii` entries are a scalar or (half_u, half_v);
    for a vertical limb that is (half-depth, half-width)."""
    pts = [Vector(p) for p in pts]
    rr = [_radpair(r) for r in radii]
    _, us, vs = _frames(pts, ref)

    bm = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        ring = []
        for k in range(sides):
            a = 2.0 * math.pi * k / sides
            off = us[i] * (math.cos(a) * rr[i][0]) + vs[i] * (math.sin(a) * rr[i][1])
            ring.append(bm.verts.new(p + off))
        rings.append(ring)
    for i in range(len(pts) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            bm.faces.new([rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]])
    if cap:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def _strip(name, p0, p1, nrm, width, thick):
    """A thin flat slab lying in a surface -- the unit a glowing crack and a
    filigree line are made of."""
    p0, p1, nrm = Vector(p0), Vector(p1), Vector(nrm).normalized()
    d = p1 - p0
    if d.length < 1e-7:
        d = Vector((0, 1, 0))
    d.normalize()
    s = nrm.cross(d)
    if s.length < 1e-6:
        s = d.cross(Vector((0, 0, 1)))
    s.normalize()
    nn = d.cross(s).normalized()

    bm = bmesh.new()
    ends = []
    for p in (p0, p1):
        quad = [p + s * (width * 0.5) + nn * (thick * 0.5),
                p - s * (width * 0.5) + nn * (thick * 0.5),
                p - s * (width * 0.5) - nn * (thick * 0.5),
                p + s * (width * 0.5) - nn * (thick * 0.5)]
        ends.append([bm.verts.new(c) for c in quad])
    bm.faces.new(ends[0])
    bm.faces.new(list(reversed(ends[1])))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([ends[0][i], ends[0][j], ends[1][j], ends[1][i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def _blob(name, loc, scale, rot=(0, 0, 0), subdiv=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler = rot
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


class _Surf:
    """Parametric surface of a lofted tube: at(t, a) -> (point just outside
    the hide, outward normal).  Cracks are walked across this."""

    def __init__(self, pts, radii, ref=None):
        self.pts = [Vector(p) for p in pts]
        self.rr = [_radpair(r) for r in radii]
        _, self.us, self.vs = _frames(self.pts, ref)
        self.cum = [0.0]
        for i in range(len(self.pts) - 1):
            self.cum.append(self.cum[-1] + (self.pts[i + 1] - self.pts[i]).length)
        self.length = max(self.cum[-1], 1e-6)

    def at(self, t, a, out=1.006):
        t = min(max(t, 0.0), 1.0)
        target = t * self.length
        i = 0
        while i < len(self.cum) - 2 and self.cum[i + 1] < target:
            i += 1
        seg = max(self.cum[i + 1] - self.cum[i], 1e-6)
        f = min(max((target - self.cum[i]) / seg, 0.0), 1.0)
        c = self.pts[i].lerp(self.pts[i + 1], f)
        u = (self.us[i] * (1 - f) + self.us[i + 1] * f).normalized()
        v = (self.vs[i] * (1 - f) + self.vs[i + 1] * f).normalized()
        ru = self.rr[i][0] * (1 - f) + self.rr[i + 1][0] * f
        rv = self.rr[i][1] * (1 - f) + self.rr[i + 1][1] * f
        ca, sa = math.cos(a), math.sin(a)
        nrm = (u * (ca * rv) + v * (sa * ru)).normalized()
        p = c + u * (ca * ru * out) + v * (sa * rv * out)
        return p, nrm


def _veins(out, name, surf, rng, mats, count, nseg=(4, 8), seg_len=0.095,
           width=(0.010, 0.026), t_range=(0.05, 0.95), hot=0.18, branch_p=0.5):
    """Walk `count` irregular, branching crack veins across a _Surf.  Each is
    a chain of thin emissive strips; together they read as a fine network of
    cold lava veins rather than a decal."""

    def walk(tag, t, a, nsegs, w, depth):
        dt = rng.uniform(0.35, 1.0) * rng.choice((-1.0, 1.0)) * (seg_len / surf.length)
        da = rng.uniform(-1.0, 1.0) * 0.85
        p, n = surf.at(t, a)
        for k in range(nsegs):
            t2 = t + dt * rng.uniform(0.6, 1.4)
            a2 = a + da * rng.uniform(0.5, 1.5)
            if not (t_range[0] - 0.05 <= t2 <= t_range[1] + 0.05):
                dt = -dt
                t2 = t + dt
            p2, n2 = surf.at(t2, a2)
            ww = w * (1.0 - 0.62 * k / max(nsegs - 1, 1))
            m = mats["crack_hot"] if rng.random() < hot else mats["crack"]
            s = _strip(f"{TAG}crk_{tag}_{depth}_{k}", p, p2, (n + n2) * 0.5, ww, 0.010)
            _mat(s, m)
            out.append(s)
            if depth < 2 and k in (1, 2) and rng.random() < branch_p:
                walk(tag + "b", t2, a2, max(2, nsegs - 2), ww * 0.7, depth + 1)
            t, a, p, n = t2, a2, p2, n2
            dt *= rng.uniform(0.85, 1.15)
            da += rng.uniform(-0.5, 0.5)

    for i in range(count):
        walk(f"{name}{i}", rng.uniform(*t_range), rng.uniform(0.0, 2.0 * math.pi),
             rng.randint(*nseg), rng.uniform(*width), 0)


# ================================================================ skeleton ===
# Hunched predator.  The spine pitches ~30 deg forward out of a low pelvis,
# the LEFT (+X) shoulder is shoved forward and high under the axe, the RIGHT
# shoulder is dropped and pulled back, the head is thrust forward and sits
# level with the shoulder tops.  Nothing here is mirrored.

SPINE = [
    ((0.00, 1.44, -0.03), (0.235, 0.315)),   # waist
    ((0.01, 1.67, 0.10), (0.262, 0.355)),    # belly
    ((0.03, 1.89, 0.24), (0.300, 0.460)),    # lower chest
    ((0.05, 2.07, 0.34), (0.330, 0.580)),    # chest
    ((0.06, 2.20, 0.36), (0.320, 0.615)),    # shoulder shelf
    ((0.06, 2.30, 0.32), (0.285, 0.540)),    # trapezius
    ((0.05, 2.37, 0.26), (0.225, 0.355)),    # base of neck
]

L_SH = Vector((0.635, 2.300, 0.300))    # LEFT shoulder: forward and high
L_ELB = Vector((1.060, 1.760, 0.020))   # elbow kicked out and back
L_WRI = Vector((0.800, 1.620, 0.720))   # hand up on the haft

R_SH = Vector((-0.580, 2.125, 0.060))   # RIGHT shoulder: dropped and back
R_ELB = Vector((-0.880, 1.520, 0.220))
R_WRI = Vector((-0.640, 1.260, 0.860))  # low, forward: open palm-up beckon

HEAD_C = Vector((0.06, 2.52, 0.62))

# ---- axe frame: grip, haft direction, blade spread, blade face normal ----
AXE_G = Vector((0.800, 1.620, 0.720))
AXE_D = Vector((-0.10, 0.90, -0.62)).normalized()
AXE_T = AXE_G + AXE_D * 1.33
AXE_O = Vector((0.96, -0.12, -0.33)).normalized()
AXE_N = AXE_O.cross(AXE_D).normalized()


def _front_z(y):
    """Z of the torso's front surface at height y -- armour, filigree and
    ichor are placed against this so they sit proud of the hide."""
    ys = [p[1] for p, _ in SPINE]
    zs = [p[2] + r[0] for p, r in SPINE]
    if y <= ys[0]:
        return zs[0]
    for i in range(len(ys) - 1):
        if y <= ys[i + 1]:
            f = (y - ys[i]) / (ys[i + 1] - ys[i])
            return zs[i] * (1 - f) + zs[i + 1] * f
    return zs[-1]


def _half_w(y):
    ys = [p[1] for p, _ in SPINE]
    ws = [r[1] for _, r in SPINE]
    if y <= ys[0]:
        return ws[0]
    for i in range(len(ys) - 1):
        if y <= ys[i + 1]:
            f = (y - ys[i]) / (ys[i + 1] - ys[i])
            return ws[i] * (1 - f) + ws[i + 1] * f
    return ws[-1]


# ============================================================ body masses ===

def _build_body(parts, glow, mats, rng):
    skin = mats["skin"]

    torso = _tube(TAG + "torso", [p for p, _ in SPINE], [r for _, r in SPINE], sides=12)
    _mat(torso, skin)
    _smooth(torso, 2)
    parts.append(torso)
    torso_surf = _Surf([p for p, _ in SPINE], [r for _, r in SPINE])

    # rounded hunch across the shoulder blades: the coiled back
    hunch = _tube(TAG + "hunch",
                  [(-0.40, 2.02, 0.03), (-0.14, 2.24, -0.04), (0.18, 2.33, -0.02),
                   (0.50, 2.28, 0.08)],
                  [(0.16, 0.19), (0.24, 0.27), (0.26, 0.29), (0.20, 0.23)], sides=8)
    _mat(hunch, skin)
    _smooth(hunch, 2)
    parts.append(hunch)

    # pectoral slabs (left one driven forward with the shoulder)
    for side, (cx, cy, cz, w) in (("l", (0.30, 2.07, 0.0, 0.27)),
                                  ("r", (-0.27, 1.99, 0.0, 0.24))):
        fz = _front_z(cy) - 0.10
        pec = _tube(TAG + "pec_" + side,
                    [(cx - w, cy + 0.11, fz - 0.14), (cx, cy + 0.02, fz),
                     (cx + w, cy - 0.07, fz - 0.12)],
                    [(0.075, 0.115), (0.145, 0.185), (0.075, 0.110)], sides=8)
        _mat(pec, skin)
        _smooth(pec, 2)
        parts.append(pec)

    # abdominal wall
    abdo = _tube(TAG + "abs",
                 [(0.01, 1.54, _front_z(1.54) - 0.11), (0.02, 1.72, _front_z(1.72) - 0.10),
                  (0.04, 1.89, _front_z(1.89) - 0.11)],
                 [(0.10, 0.23), (0.12, 0.265), (0.12, 0.25)], sides=8)
    _mat(abdo, skin)
    _smooth(abdo, 2)
    parts.append(abdo)

    pelvis = _tube(TAG + "pelvis",
                   [(0.00, 1.22, -0.07), (0.00, 1.38, -0.02), (0.00, 1.52, 0.00)],
                   [(0.235, 0.355), (0.285, 0.430), (0.250, 0.350)], sides=12)
    _mat(pelvis, skin)
    _smooth(pelvis, 2)
    parts.append(pelvis)

    # ---- thick neck + head, thrust forward ------------------------------
    neck = _tube(TAG + "neck",
                 [(0.05, 2.28, 0.21), (0.055, 2.37, 0.37), (0.06, 2.44, 0.52)],
                 [(0.205, 0.225), (0.190, 0.205), (0.165, 0.180)], sides=8)
    _mat(neck, skin)
    _smooth(neck, 2)
    parts.append(neck)

    skull = _tube(TAG + "skull",
                  [(0.06, 2.36, 0.46), (0.06, 2.46, 0.57), (0.06, 2.58, 0.615),
                   (0.06, 2.68, 0.555), (0.06, 2.735, 0.435)],
                  [(0.170, 0.165), (0.235, 0.215), (0.255, 0.225),
                   (0.215, 0.185), (0.125, 0.100)], sides=10)
    _mat(skull, skin)
    _smooth(skull, 2)
    parts.append(skull)

    muzzle = _tube(TAG + "muzzle",
                   [(0.06, 2.545, 0.600), (0.06, 2.495, 0.760), (0.06, 2.455, 0.880)],
                   [(0.135, 0.170), (0.105, 0.145), (0.070, 0.100)], sides=8)
    _mat(muzzle, skin)
    _smooth(muzzle, 2)
    parts.append(muzzle)

    jaw = _tube(TAG + "jaw",
                [(0.06, 2.440, 0.540), (0.06, 2.400, 0.720), (0.06, 2.385, 0.860)],
                [(0.085, 0.160), (0.070, 0.135), (0.048, 0.092)], sides=8)
    _mat(jaw, skin)
    _smooth(jaw, 2)
    parts.append(jaw)

    # heavy brow ridges, slanted down toward the nose: contemptuous
    for side, sx in (("l", 1.0), ("r", -1.0)):
        brow = add_box(TAG + "brow_" + side, (0.23, 0.065, 0.16),
                       (0.06 + sx * 0.150, 2.635, 0.760),
                       rotation=(0.24, 0.0, sx * -0.34), bevel_width=0.015, bevel_segments=2)
        _mat(brow, skin)
        parts.append(brow)

    # solid pupil-less glowing cyan eyes
    for side, sx in (("l", 1.0), ("r", -1.0)):
        eye = _blob(TAG + "eye_" + side, (0.06 + sx * 0.142, 2.565, 0.800),
                    (0.092, 0.050, 0.058), rot=(0.0, 0.0, sx * -0.30), subdiv=3)
        _mat(eye, mats["eye"])
        glow.append(eye)
        socket = add_box(TAG + "socket_" + side, (0.22, 0.10, 0.06),
                         (0.06 + sx * 0.145, 2.560, 0.790),
                         rotation=(0.1, 0.0, sx * -0.30), bevel_width=0.010)
        _mat(socket, mats["mouth"])
        parts.append(socket)

    # ---- bored half-smile: the mouth line lifts on his LEFT only --------
    maw = add_box(TAG + "maw", (0.34, 0.034, 0.060), (0.065, 2.408, 0.872),
                  rotation=(0.0, 0.0, 0.18), bevel_width=0.006)
    _mat(maw, mats["mouth"])
    parts.append(maw)
    curl = add_box(TAG + "maw_curl", (0.13, 0.030, 0.052), (0.235, 2.452, 0.818),
                   rotation=(0.0, -0.45, 0.55), bevel_width=0.006)
    _mat(curl, mats["mouth"])
    parts.append(curl)

    # small tusk-like teeth; longer on the smirking side
    for i, (lx, ln) in enumerate([(-0.115, 0.050), (-0.045, 0.058), (0.030, 0.066),
                                  (0.105, 0.084), (0.175, 0.100), (0.235, 0.074)]):
        x, y = 0.065 + lx, 2.400 + lx * 0.180
        t = _tube(f"{TAG}tooth_lo_{i}",
                  [(x, y - 0.014, 0.870), (x, y + ln * 0.6, 0.866), (x, y + ln, 0.858)],
                  [0.019, 0.013, 0.003], sides=6)
        _mat(t, mats["bone"])
        _smooth(t, 1)
        parts.append(t)
    for i, (lx, ln) in enumerate([(-0.070, 0.046), (0.055, 0.052), (0.150, 0.060)]):
        x, y = 0.065 + lx, 2.420 + lx * 0.180
        t = _tube(f"{TAG}tooth_up_{i}",
                  [(x, y + 0.014, 0.864), (x, y - ln * 0.6, 0.860), (x, y - ln, 0.852)],
                  [0.016, 0.011, 0.002], sides=6)
        _mat(t, mats["bone"])
        _smooth(t, 1)
        parts.append(t)

    # cheek spurs
    for i, (sx, px, py, pz, ln) in enumerate([(1, 0.215, 2.510, 0.700, 0.13),
                                              (-1, -0.100, 2.495, 0.690, 0.11),
                                              (1, 0.200, 2.420, 0.610, 0.10),
                                              (-1, -0.090, 2.410, 0.600, 0.09)]):
        sp = _tube(f"{TAG}cheekspur_{i}",
                   [(px, py, pz),
                    (px + sx * ln * 0.55, py + ln * 0.45, pz - ln * 0.55),
                    (px + sx * ln, py + ln * 0.85, pz - ln * 1.1)],
                   [0.034, 0.020, 0.003], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 1)
        parts.append(sp)

    # ---- long swept-back horns: the major silhouette element ------------
    horn_surfs = []
    for side, sx, st in (("l", 1.0, 1.0), ("r", -1.0, 0.93)):
        pts = [
            (0.06 + sx * 0.190, 2.620, 0.520),
            (0.06 + sx * 0.290, 2.790, 0.360),
            (0.06 + sx * 0.360, 2.912, 0.095),
            (0.06 + sx * 0.405, 2.988, -0.205 * st),
            (0.06 + sx * 0.425, 2.972, -0.525 * st),
            (0.06 + sx * 0.405, 2.878, -0.820 * st),
            (0.06 + sx * 0.365, 2.735, -1.070 * st),
        ]
        rad = [0.158, 0.146, 0.126, 0.102, 0.074, 0.044, 0.010]
        horn = _tube(TAG + "horn_" + side, pts, rad, sides=8)
        _mat(horn, mats["horn"])
        _smooth(horn, 2)
        parts.append(horn)
        hs = _Surf(pts, rad)
        horn_surfs.append(hs)

        # growth ridges -- texture that survives in silhouette
        for k in range(6):
            tt = 0.10 + k * 0.105
            c, _ = hs.at(tt, 0.0, out=0.0)
            r = 0.155 - 0.019 * k
            ring = _tube(f"{TAG}hornring_{side}_{k}",
                         [c + Vector((0, 0.016, 0.014)), c - Vector((0, 0.016, 0.014))],
                         [r, r], sides=8)
            _mat(ring, mats["horn"])
            parts.append(ring)

        bh = _tube(f"{TAG}browhorn_{side}",
                   [(0.06 + sx * 0.095, 2.665, 0.650),
                    (0.06 + sx * 0.130, 2.750, 0.545),
                    (0.06 + sx * 0.150, 2.812, 0.420)],
                   [0.046, 0.027, 0.004], sides=6)
        _mat(bh, mats["horn"])
        _smooth(bh, 1)
        parts.append(bh)

    return torso_surf, horn_surfs


# ===================================================================== arms ===

def _arm_chain(sh, elb, wri, r_sh, r_elb, r_wri, bulge):
    """One continuous polyline shoulder -> elbow -> wrist, with extra points
    bracketing the elbow so subdivision keeps the joint instead of melting
    it, and a biceps/forearm bulge between them."""
    d1 = (elb - sh)
    d2 = (wri - elb)
    pts = [sh,
           sh + d1 * 0.30 + bulge * 0.55,
           sh + d1 * 0.62 + bulge * 0.35,
           sh + d1 * 0.88,
           elb,
           elb + d2 * 0.16,
           elb + d2 * 0.42 + bulge * 0.30,
           elb + d2 * 0.74,
           wri]
    rad = [r_sh,
           (r_sh[0] * 1.00, r_sh[1] * 0.98),
           (r_sh[0] * 0.88, r_sh[1] * 0.88),
           (r_elb[0] * 1.06, r_elb[1] * 1.04),
           r_elb,
           (r_elb[0] * 1.05, r_elb[1] * 1.03),
           (r_elb[0] * 0.98, r_elb[1] * 0.96),
           (r_wri[0] * 1.10, r_wri[1] * 1.08),
           r_wri]
    return pts, rad


def _build_arms(parts, mats, rng):
    skin = mats["skin"]
    surfs = []

    for side, sh, elb, wri, bulge in (
            ("l", L_SH, L_ELB, L_WRI, Vector((0.055, 0.0, 0.045))),
            ("r", R_SH, R_ELB, R_WRI, Vector((-0.055, 0.0, 0.045)))):
        rsh = (0.255, 0.280) if side == "l" else (0.240, 0.262)
        pts, rad = _arm_chain(sh, elb, wri, rsh, (0.160, 0.170), (0.108, 0.116), bulge)
        arm = _tube(TAG + "arm_" + side, pts, rad, sides=10)
        _mat(arm, skin)
        _smooth(arm, 2)
        parts.append(arm)
        surfs.append(_Surf(pts, rad))

        # trapezius/deltoid wedge tying the arm into the torso
        tie = _tube(TAG + "delt_" + side,
                    [sh + Vector((-0.20 if side == "l" else 0.20, 0.06, -0.02)),
                     sh + Vector((0.0, 0.03, 0.0)),
                     sh + Vector((0.14 if side == "l" else -0.14, -0.10, 0.02))],
                    [(0.195, 0.165), (0.250, 0.235), (0.215, 0.205)], sides=8)
        _mat(tie, skin)
        _smooth(tie, 2)
        parts.append(tie)

    # ---- LEFT hand: fist wrapped around the axe haft --------------------
    d, o, n = AXE_D, AXE_O, AXE_N
    gp = AXE_G
    palm = _tube(TAG + "hand_l",
                 [gp - d * 0.115 - n * 0.02, gp, gp + d * 0.115 - n * 0.01],
                 [(0.090, 0.095), (0.125, 0.135), (0.090, 0.098)], sides=8)
    _mat(palm, skin)
    _smooth(palm, 2)
    parts.append(palm)
    for i in range(4):
        s = -0.090 + i * 0.062
        base = gp + d * s - n * 0.090
        knuck = base + n * 0.095 + o * 0.095
        tip = base + n * 0.195 + o * 0.030
        f = _tube(f"{TAG}fing_l_{i}", [base, knuck, tip], [0.039, 0.033, 0.022], sides=6)
        _mat(f, skin)
        _smooth(f, 2)
        parts.append(f)
    thumb = _tube(TAG + "thumb_l",
                  [gp + d * 0.090 + n * 0.065, gp + d * 0.035 + n * 0.145,
                   gp - d * 0.035 + n * 0.168],
                  [0.045, 0.036, 0.023], sides=6)
    _mat(thumb, skin)
    _smooth(thumb, 2)
    parts.append(thumb)

    # ---- RIGHT hand: wide, open, palm up, lazy beckon -------------------
    pc = Vector((-0.620, 1.248, 0.990))
    palm_r = _tube(TAG + "hand_r",
                   [pc - Vector((0.0, 0.0, 0.140)), pc - Vector((0.0, 0.006, 0.020)),
                    pc + Vector((0.012, 0.000, 0.110))],
                   [(0.105, 0.052), (0.170, 0.050), (0.180, 0.044)], sides=10,
                   ref=(0.0, 1.0, 0.0))
    _mat(palm_r, skin)
    _smooth(palm_r, 2)
    parts.append(palm_r)
    heel = _blob(TAG + "palmheel_r", tuple(pc - Vector((0.0, 0.020, 0.115))),
                 (0.140, 0.062, 0.100), subdiv=2)
    _mat(heel, skin)
    _smooth(heel, 1)
    parts.append(heel)

    # four fingers fanned, flat then softly curling up: "come on, then"
    for i in range(4):
        fx = -0.135 + i * 0.090
        spread = 0.070 * (i - 1.5) / 1.5
        b = pc + Vector((fx, 0.000, 0.112))
        m = b + Vector((spread * 0.8, 0.012, 0.145))
        t = m + Vector((spread * 1.0, 0.062, 0.115))
        f = _tube(f"{TAG}fing_r_{i}", [b, m, t],
                  [0.044 - 0.004 * abs(i - 1.5), 0.037, 0.024], sides=6)
        _mat(f, skin)
        _smooth(f, 2)
        parts.append(f)
        cl = _tube(f"{TAG}fclaw_r_{i}", [t, t + Vector((spread * 0.3, 0.045, 0.040))],
                   [0.019, 0.002], sides=6)
        _mat(cl, mats["horn"])
        _smooth(cl, 1)
        parts.append(cl)
    th = _tube(TAG + "thumb_r",
               [pc + Vector((0.140, -0.010, -0.050)), pc + Vector((0.240, 0.010, 0.040)),
                pc + Vector((0.290, 0.045, 0.115))],
               [0.050, 0.039, 0.024], sides=6)
    _mat(th, skin)
    _smooth(th, 2)
    parts.append(th)
    thc = _tube(TAG + "thumbclaw_r",
                [pc + Vector((0.290, 0.045, 0.115)), pc + Vector((0.322, 0.080, 0.155))],
                [0.020, 0.002], sides=6)
    _mat(thc, mats["horn"])
    _smooth(thc, 1)
    parts.append(thc)

    return surfs


# ===================================================================== legs ===

def _build_legs(parts, mats, rng):
    """Massive digitigrade legs, one planted forward and one braced back."""
    skin = mats["skin"]
    surfs = []

    legs = {
        "l": ([(0.310, 1.520, 0.100), (0.360, 1.280, 0.200), (0.420, 1.040, 0.305),
               (0.452, 0.925, 0.340), (0.455, 0.835, 0.295), (0.440, 0.660, 0.150),
               (0.418, 0.510, 0.010), (0.425, 0.390, 0.080), (0.435, 0.245, 0.215),
               (0.445, 0.148, 0.320)],
              [(0.300, 0.315), (0.292, 0.300), (0.230, 0.235), (0.218, 0.222),
               (0.198, 0.202), (0.180, 0.185), (0.142, 0.150), (0.126, 0.138),
               (0.130, 0.150), (0.142, 0.158)],
              (0.445, 0.320, 1.0)),
        "r": ([(-0.330, 1.500, 0.010), (-0.415, 1.265, 0.025), (-0.510, 1.030, 0.030),
               (-0.545, 0.915, 0.010), (-0.552, 0.825, -0.055), (-0.560, 0.650, -0.215),
               (-0.568, 0.505, -0.370), (-0.562, 0.388, -0.305), (-0.550, 0.245, -0.175),
               (-0.542, 0.148, -0.075)],
              [(0.300, 0.315), (0.292, 0.300), (0.230, 0.235), (0.218, 0.222),
               (0.198, 0.202), (0.180, 0.185), (0.142, 0.150), (0.126, 0.138),
               (0.130, 0.150), (0.142, 0.158)],
              (-0.542, -0.075, -1.0)),
    }
    for side, (pts, rad, (fx, fz, zd)) in legs.items():
        leg = _tube(TAG + "leg_" + side, pts, rad, sides=10)
        _mat(leg, skin)
        _smooth(leg, 2)
        parts.append(leg)
        surfs.append(_Surf(pts, rad))

        foot = _tube(TAG + "foot_" + side,
                     [(fx, 0.145, fz), (fx, 0.110, fz + zd * 0.14),
                      (fx, 0.086, fz + zd * 0.26)],
                     [(0.142, 0.158), (0.112, 0.168), (0.082, 0.150)], sides=8)
        _mat(foot, skin)
        _smooth(foot, 2)
        parts.append(foot)

        for i, ox in enumerate((-0.125, 0.0, 0.125)):
            b = Vector((fx + ox, 0.090, fz + zd * 0.24))
            m = Vector((fx + ox * 1.25, 0.066, fz + zd * 0.39))
            t = Vector((fx + ox * 1.45, 0.028, fz + zd * 0.53))
            cl = _tube(f"{TAG}claw_{side}_{i}", [b, m, t], [0.062, 0.042, 0.004], sides=6)
            _mat(cl, mats["horn"])
            _smooth(cl, 2)
            parts.append(cl)
        sp = _tube(f"{TAG}spur_{side}",
                   [(fx, 0.195, fz - zd * 0.05), (fx, 0.125, fz - zd * 0.21),
                    (fx, 0.055, fz - zd * 0.35)],
                   [0.058, 0.036, 0.004], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 2)
        parts.append(sp)

    return surfs


# ================================================================== armour ===

def _build_armor(parts, glow, mats, rng):
    """Woven black obsidian plate with teal filigree, a big spiked LEFT
    pauldron, a belt with a metal skull clasp."""
    A, AH, F = mats["armor"], mats["armor_hi"], mats["filigree"]

    def plate(name, dims, loc, rot=(0, 0, 0), m=None, bev=0.012):
        o = add_box(TAG + name, dims, loc, rotation=rot, bevel_width=bev, bevel_segments=2)
        _mat(o, m if m else A)
        parts.append(o)
        return o

    def fil(name, p0, p1, nrm, w=0.014):
        s = _strip(TAG + name, Vector(p0), Vector(p1), Vector(nrm), w, 0.010)
        _mat(s, F)
        glow.append(s)
        return s

    # ---- chest cuirass, sitting proud of the measured torso front -------
    plate("cuir_mid", (0.58, 0.44, 0.13), (0.06, 2.07, _front_z(2.07) + 0.03),
          rot=(0.40, 0.0, 0.03), m=AH)
    plate("cuir_up", (0.80, 0.19, 0.12), (0.06, 2.255, _front_z(2.255) + 0.02),
          rot=(0.55, 0.0, 0.04), m=AH)
    plate("cuir_l", (0.32, 0.42, 0.12), (0.43, 2.06, _front_z(2.06) - 0.09),
          rot=(0.38, -0.46, 0.06))
    plate("cuir_r", (0.30, 0.38, 0.11), (-0.38, 1.98, _front_z(1.98) - 0.10),
          rot=(0.36, 0.48, -0.05))

    # "woven": narrow straps crossing diagonally over the ribs/abdomen
    for i in range(6):
        y = 1.60 + i * 0.072
        z = _front_z(y) + 0.015
        plate(f"weave_a{i}", (0.52 + 0.05 * i, 0.046, 0.065), (0.03, y, z),
              rot=(0.48, 0.0, 0.26 - 0.03 * i), bev=0.008)
        plate(f"weave_b{i}", (0.50 + 0.05 * i, 0.040, 0.055), (0.03, y + 0.028, z + 0.012),
              rot=(0.48, 0.0, -0.22 + 0.03 * i), bev=0.008, m=AH)

    # filigree tracery over the cuirass
    for i in range(7):
        x = -0.24 + i * 0.085
        fil(f"fil_ch{i}", (0.06 + x, 1.96, _front_z(1.96) + 0.085 - abs(x) * 0.30),
            (0.06 + x * 0.5, 2.26, _front_z(2.26) + 0.075 - abs(x) * 0.18),
            (0.0, 0.35, 0.94))
    for i in range(4):
        y = 1.99 + i * 0.080
        fil(f"fil_chh{i}", (-0.20, y, _front_z(y) + 0.080),
            (0.32, y + 0.02, _front_z(y) + 0.080), (0.0, 0.3, 0.95), w=0.011)

    # ---- high collar behind the head: sells the hunch -------------------
    for i, a in enumerate((-1.45, -0.95, -0.45, 0.05, 0.55, 1.05, 1.45)):
        cx = 0.06 + math.sin(a) * 0.44
        cz = 0.20 - math.cos(a) * 0.38
        plate(f"collar{i}", (0.22, 0.40, 0.08), (cx, 2.46 + 0.035 * abs(a), cz),
              rot=(-0.34, -a, 0.0), m=AH if i % 2 else A)

    # ---- spiked LEFT pauldron -------------------------------------------
    pl = Vector((0.670, 2.330, 0.210))
    plate("paul_l0", (0.60, 0.24, 0.62), tuple(pl), rot=(0.08, 0.0, -0.32), m=AH, bev=0.020)
    plate("paul_l1", (0.54, 0.20, 0.54), tuple(pl - Vector((0.035, 0.195, -0.015))),
          rot=(0.06, 0.0, -0.24), bev=0.018)
    plate("paul_l2", (0.46, 0.17, 0.44), tuple(pl - Vector((0.060, 0.370, -0.030))),
          rot=(0.05, 0.0, -0.17), bev=0.016, m=AH)
    spikes = [(0.30, 0.19, 0.52, 1.25, 0.20, 0.60),
              (0.36, 0.15, 0.14, 1.05, -0.08, 0.68),
              (0.34, 0.09, -0.28, 0.95, -0.46, 0.58),
              (0.20, 0.27, -0.14, 1.45, -0.30, 0.48),
              (0.06, 0.33, 0.24, 1.62, 0.26, 0.40),
              (0.26, -0.06, 0.40, 0.75, 0.55, 0.36)]
    for i, (ox, oy, oz, pitch, yaw, ln) in enumerate(spikes):
        base = pl + Vector((ox, oy, oz))
        d = Vector((math.sin(pitch) * math.cos(yaw), math.cos(pitch),
                    -math.sin(pitch) * math.sin(yaw))).normalized()
        sp = _tube(f"{TAG}paulspike_{i}",
                   [base, base + d * ln * 0.40, base + d * ln * 0.74, base + d * ln],
                   [0.090, 0.062, 0.034, 0.004], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 2)
        parts.append(sp)
    for i in range(4):
        fil(f"fil_paul{i}", tuple(pl + Vector((-0.24 + i * 0.14, 0.095, 0.29))),
            tuple(pl + Vector((-0.22 + i * 0.14, 0.015, -0.29))), (0.1, 0.95, 0.0))

    # ---- smaller strapped RIGHT shoulder plate (asymmetry) --------------
    pr = Vector((-0.610, 2.175, 0.040))
    plate("paul_r0", (0.44, 0.18, 0.44), tuple(pr), rot=(0.05, 0.0, 0.36))
    plate("paul_r1", (0.36, 0.14, 0.35), tuple(pr + Vector((0.025, -0.155, 0.0))),
          rot=(0.04, 0.0, 0.28), m=AH)
    for i, (ox, oy, oz, ln) in enumerate([(-0.21, 0.10, 0.06, 0.26), (-0.18, 0.03, -0.17, 0.22)]):
        base = pr + Vector((ox, oy, oz))
        d = Vector((-0.74, 0.52, -0.42)).normalized()
        sp = _tube(f"{TAG}paulspike_r{i}", [base, base + d * ln * 0.6, base + d * ln],
                   [0.060, 0.033, 0.004], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 1)
        parts.append(sp)

    # ---- bracers ---------------------------------------------------------
    for side, elb, wri in (("l", L_ELB, L_WRI), ("r", R_ELB, R_WRI)):
        d = (wri - elb).normalized()
        c = elb.lerp(wri, 0.50)
        br = _tube(TAG + "bracer_" + side,
                   [c - d * 0.23, c - d * 0.02, c + d * 0.20],
                   [(0.182, 0.192), (0.172, 0.178), (0.148, 0.154)], sides=10)
        _mat(br, A)
        br.modifiers.new("Bevel", "BEVEL").width = 0.008
        parts.append(br)
        n = d.cross(Vector((0, 0, 1)))
        if n.length < 0.1:
            n = d.cross(Vector((1, 0, 0)))
        n.normalize()
        for i in range(3):
            off = n * (0.175 * math.cos(i * 1.9)) + n.cross(d) * (0.175 * math.sin(i * 1.9))
            fil(f"fil_brac_{side}{i}", tuple(c - d * 0.19 + off), tuple(c + d * 0.17 + off),
                tuple(off.normalized()), w=0.011)
        for i in range(2):
            base = c + d * (0.04 + 0.14 * i) + n * 0.175
            sp = _tube(f"{TAG}bracspike_{side}{i}",
                       [base, base + n * 0.08 - d * 0.05, base + n * 0.16 - d * 0.12],
                       [0.044, 0.026, 0.003], sides=6)
            _mat(sp, mats["horn"])
            _smooth(sp, 1)
            parts.append(sp)

    # ---- belt + metal skull clasp ---------------------------------------
    belt = _tube(TAG + "belt",
                 [(0.0, 1.400, -0.045), (0.0, 1.475, -0.010), (0.0, 1.550, 0.000)],
                 [(0.265, 0.370), (0.290, 0.405), (0.270, 0.380)], sides=14)
    _mat(belt, A)
    belt.modifiers.new("Bevel", "BEVEL").width = 0.009
    parts.append(belt)
    for i in range(9):
        a = -1.40 + i * 0.35
        plate(f"beltstud{i}", (0.08, 0.085, 0.055),
              (math.sin(a) * 0.40, 1.478, math.cos(a) * 0.295 - 0.01),
              rot=(0.0, -a, 0.0), m=AH, bev=0.008)

    sk = Vector((0.03, 1.478, 0.300))
    cr = _blob(TAG + "skull_cranium", tuple(sk + Vector((0, 0.035, -0.012))),
               (0.118, 0.110, 0.090), subdiv=2)
    _mat(cr, mats["steel"])
    _smooth(cr, 1)
    parts.append(cr)
    jw = _blob(TAG + "skull_jaw", tuple(sk + Vector((0, -0.062, 0.018))),
               (0.092, 0.056, 0.076), subdiv=2)
    _mat(jw, mats["steel"])
    _smooth(jw, 1)
    parts.append(jw)
    for sx in (-1, 1):
        soc = _blob(f"{TAG}skull_socket_{sx}", tuple(sk + Vector((sx * 0.050, 0.042, 0.070))),
                    (0.034, 0.029, 0.022), subdiv=2)
        _mat(soc, mats["crack_dim"])
        glow.append(soc)
        base = sk + Vector((sx * 0.095, 0.066, 0.008))
        hs = _tube(f"{TAG}skull_horn_{sx}",
                   [base, base + Vector((sx * 0.060, 0.065, -0.034)),
                    base + Vector((sx * 0.090, 0.115, -0.078))],
                   [0.030, 0.018, 0.003], sides=6)
        _mat(hs, mats["steel"])
        _smooth(hs, 1)
        parts.append(hs)
    for i in range(4):
        plate(f"skull_teeth{i}", (0.024, 0.038, 0.022),
              (sk.x - 0.038 + i * 0.026, 1.432, sk.z + 0.058), m=mats["steel"], bev=0.004)

    # ---- tassets hanging off the belt -----------------------------------
    for i, (a, ln) in enumerate([(-1.15, 0.36), (-0.70, 0.46), (-0.25, 0.52),
                                 (0.22, 0.50), (0.68, 0.42), (1.12, 0.32)]):
        bx = math.sin(a) * 0.38
        bz = math.cos(a) * 0.285 - 0.015
        plate(f"tasset{i}", (0.25, ln, 0.07), (bx * 1.08, 1.395 - ln * 0.5, bz * 1.08),
              rot=(0.14, -a, 0.03), m=AH if i % 2 else A, bev=0.010)

    # ---- thigh / knee plating -------------------------------------------
    for side, kx, ky, kz, yaw in (("l", 0.452, 0.945, 0.345, -0.22), ("r", -0.545, 0.930, 0.010, 0.26)):
        plate(f"knee_{side}", (0.34, 0.30, 0.16), (kx, ky, kz), rot=(0.22, yaw, 0.0), m=AH)
        base = Vector((kx, ky + 0.06, kz + 0.07))
        d = Vector((0.0, 0.28, 1.0)).normalized()
        sp = _tube(f"{TAG}kneespike_{side}", [base, base + d * 0.12, base + d * 0.24],
                   [0.062, 0.036, 0.004], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 1)
        parts.append(sp)
        plate(f"thigh_{side}", (0.30, 0.34, 0.16), (kx * 0.88, ky + 0.34, kz * 0.82),
              rot=(0.30, yaw, 0.0))
        fil(f"fil_knee_{side}", (kx - 0.13, ky + 0.02, kz + 0.09),
            (kx + 0.13, ky + 0.02, kz + 0.09), (0.0, 0.2, 1.0), w=0.011)


# ==================================================================== cape ===

def _build_cape(mats, rng):
    """Torn, smouldering black cape: a shoulder-anchored grid swept back by
    wind, with whole columns cut short so the hem tears into strips and real
    gaps open between them.  Returns (object, torn-edge points for embers)."""
    nu, nv = 26, 18
    y_top = 2.42
    R = 0.58
    a0, a1 = math.radians(58.0), math.radians(302.0)
    Lmax = 2.40

    lengths = []
    for i in range(nu + 1):
        u = i / nu
        base = 0.78 + 0.13 * math.sin(u * 7.3 + 1.1) + 0.10 * math.sin(u * 15.1)
        roll = rng.random()
        if roll < 0.24:
            base *= rng.uniform(0.40, 0.62)                 # deep tear
        elif roll < 0.42:
            base = min(1.0, base * rng.uniform(1.10, 1.24))  # long tongue
        lengths.append(max(0.22, min(1.0, base)))

    def vert(i, j):
        u = i / nu
        a = a0 + (a1 - a0) * u
        v = j / nv
        x0, z0 = math.sin(a) * R, math.cos(a) * R
        y = y_top - v * Lmax * 0.93
        flare = 1.0 + 0.95 * v
        x = x0 * flare + 0.30 * v * v + 0.11 * math.sin(a * 2.1 + v * 3.4) * v
        z = z0 * (1.0 + 0.35 * v) - 0.78 * v * v + 0.10 * math.sin(a * 3.3 + v * 2.0) * v
        y += 0.07 * math.sin(a * 2.7) * v
        return Vector((x, y, z))

    bm = bmesh.new()
    grid = [[bm.verts.new(vert(i, j)) for j in range(nv + 1)] for i in range(nu + 1)]
    edge_pts = []
    for i in range(nu):
        jmax = 0
        for j in range(nv):
            frac = (j + 1) / nv
            if frac <= lengths[i] and frac <= lengths[i + 1]:
                bm.faces.new([grid[i][j], grid[i + 1][j],
                              grid[i + 1][j + 1], grid[i][j + 1]])
                jmax = j + 1
        if jmax:
            edge_pts.append(vert(i, jmax))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)

    mesh = bpy.data.meshes.new(TAG + "cape_mesh")
    bm.to_mesh(mesh)
    bm.free()
    cape = bpy.data.objects.new(TAG + "cape", mesh)
    bpy.context.collection.objects.link(cape)
    _mat(cape, mats["cloth"])
    for poly in cape.data.polygons:
        poly.use_smooth = True
    sub = cape.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 1
    sol = cape.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.018
    sol.offset = 0.0
    return cape, edge_pts


# ===================================================================== axe ===

def _build_axe(parts, glow, ichor, mats, rng):
    """A huge, crude two-handed axe resting on the forward left shoulder,
    broad blade face angled toward camera, black-teal ichor running off it."""
    d, o, n, T = AXE_D, AXE_O, AXE_N, AXE_T
    butt = AXE_G - d * 0.38

    haft = _tube(TAG + "axe_haft",
                 [butt, butt + d * 0.40, AXE_G, AXE_G.lerp(T, 0.55), T, T + d * 0.14],
                 [0.054, 0.064, 0.070, 0.066, 0.062, 0.054], sides=10)
    _mat(haft, mats["axe"])
    haft.modifiers.new("Bevel", "BEVEL").width = 0.006
    for poly in haft.data.polygons:
        poly.use_smooth = True
    parts.append(haft)
    cap = _tube(TAG + "axe_buttcap", [butt - d * 0.05, butt + d * 0.06], [0.078, 0.082], sides=10)
    _mat(cap, mats["steel"])
    parts.append(cap)
    for i in range(7):
        p = AXE_G + d * (-0.30 + i * 0.10)
        bind = _tube(f"{TAG}axe_bind{i}", [p - d * 0.024, p + d * 0.024], [0.079, 0.079], sides=10)
        _mat(bind, mats["armor"])
        parts.append(bind)

    # ---- massive bearded blade ------------------------------------------
    outline = [(0.36, 0.00), (0.40, 0.14), (0.34, 0.34), (0.20, 0.50),
               (-0.02, 0.60), (-0.30, 0.62), (-0.52, 0.50), (-0.58, 0.27),
               (-0.49, 0.09), (-0.34, 0.00)]
    th0, tmax = 0.070, 0.62
    bm = bmesh.new()
    front, back = [], []
    for (s, t) in outline:
        th = th0 * max(0.055, 1.0 - (t / tmax) * 0.945)
        p = T + d * s + o * t
        front.append(bm.verts.new(p + n * th))
        back.append(bm.verts.new(p - n * th))
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        bm.faces.new([front[i], front[j], back[j], back[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(TAG + "axe_blade_mesh")
    bm.to_mesh(mesh)
    bm.free()
    blade = bpy.data.objects.new(TAG + "axe_blade", mesh)
    bpy.context.collection.objects.link(blade)
    _mat(blade, mats["axe"])
    bv = blade.modifiers.new("Bevel", "BEVEL")
    bv.width = 0.012
    bv.segments = 2
    parts.append(blade)

    bspike = _tube(TAG + "axe_backspike",
                   [T - o * 0.02, T - o * 0.26 + d * 0.06, T - o * 0.46 + d * 0.12],
                   [(0.175, 0.060), (0.120, 0.042), (0.012, 0.010)], sides=6)
    _mat(bspike, mats["axe"])
    parts.append(bspike)
    for i, s in enumerate((-0.36, 0.34)):
        col = _tube(f"{TAG}axe_collar{i}", [T + d * s - o * 0.05, T + d * s + o * 0.13],
                    [0.092, 0.080], sides=8)
        _mat(col, mats["steel"])
        col.modifiers.new("Bevel", "BEVEL").width = 0.006
        parts.append(col)
    fin = _tube(TAG + "axe_finial", [T + d * 0.14, T + d * 0.22, T + d * 0.30],
                [0.056, 0.034, 0.004], sides=6)
    _mat(fin, mats["horn"])
    _smooth(fin, 1)
    parts.append(fin)

    # filigree etched into the blade face
    for i in range(5):
        s = -0.36 + i * 0.18
        f = _strip(f"{TAG}axe_fil{i}", T + d * s + o * 0.07 + n * (th0 * 0.92),
                   T + d * (s * 0.5) + o * 0.42 + n * (th0 * 0.30), n, 0.017, 0.010)
        _mat(f, mats["filigree"])
        glow.append(f)
    for sgn in (1, -1):
        f = _strip(f"{TAG}axe_filspine{sgn}",
                   T + d * (-0.34) + o * 0.11 + n * sgn * (th0 * 0.88),
                   T + d * 0.32 + o * 0.11 + n * sgn * (th0 * 0.88), n * sgn, 0.022, 0.010)
        _mat(f, mats["filigree"])
        glow.append(f)

    # ---- ichor running off the cutting edge, dripping to the crystal ----
    for i, (s, t) in enumerate([(0.26, 0.46), (0.00, 0.58), (-0.26, 0.60),
                                (-0.48, 0.50), (-0.56, 0.30)]):
        base = T + d * s + o * t
        ln = rng.uniform(0.18, 0.38)
        dr = _tube(f"{TAG}axe_drip{i}",
                   [base, base + Vector((0.0, -ln * 0.35, 0.008)),
                    base + Vector((0.008, -ln * 0.72, 0.012)),
                    base + Vector((0.008, -ln, 0.010))],
                   [0.028, 0.042, 0.030, 0.004], sides=6)
        _mat(dr, mats["ichor"])
        _smooth(dr, 2)
        ichor.append(dr)
        if i in (1, 3):
            dp = _blob(f"{TAG}axe_droplet{i}",
                       tuple(base + Vector((0.008, -ln - rng.uniform(0.22, 0.55), 0.01))),
                       (0.026, 0.042, 0.026), subdiv=2)
            _mat(dp, mats["ichor"])
            _smooth(dp, 1)
            ichor.append(dp)
    for i in range(4):
        s0 = 0.30 - i * 0.26
        sm = _strip(f"{TAG}axe_edgeichor{i}",
                    T + d * s0 + o * (0.52 - abs(s0) * 0.12),
                    T + d * (s0 - 0.24) + o * (0.52 - abs(s0 - 0.24) * 0.12),
                    n, 0.080, 0.028)
        _mat(sm, mats["ichor"])
        ichor.append(sm)


# ========================================================= ichor / embers ===

def _build_ichor_splashes(ichor, mats, rng, horn_surfs):
    """Black-teal ichor splashed across the chest and horns, thrown off the
    axe that rests there."""
    for i in range(14):
        y = rng.uniform(1.72, 2.30)
        x = 0.06 + rng.uniform(-0.34, 0.42)
        z = _front_z(y) + 0.085 - abs(x - 0.06) * 0.30
        s = rng.uniform(0.045, 0.100)
        sp = _blob(f"{TAG}ichor_chest{i}", (x, y, z),
                   (s * rng.uniform(0.7, 1.5), s * rng.uniform(0.9, 1.9), 0.020),
                   rot=(0.3, 0.0, rng.uniform(-0.8, 0.8)), subdiv=2)
        _mat(sp, mats["ichor"])
        ichor.append(sp)
    for i in range(5):
        x = 0.06 + rng.uniform(-0.28, 0.36)
        y0 = rng.uniform(2.06, 2.26)
        ln = rng.uniform(0.18, 0.42)
        z = _front_z(y0) + 0.082 - abs(x - 0.06) * 0.26
        run = _tube(f"{TAG}ichor_run{i}",
                    [(x, y0, z), (x + 0.008, y0 - ln * 0.5, z + 0.004),
                     (x + 0.012, y0 - ln, z)],
                    [0.022, 0.017, 0.005], sides=6)
        _mat(run, mats["ichor"])
        _smooth(run, 1)
        ichor.append(run)

    for hi, surf in enumerate(horn_surfs):
        for i in range(6):
            p, _ = surf.at(rng.uniform(0.04, 0.55), rng.uniform(0, 2 * math.pi), out=1.0)
            s = rng.uniform(0.040, 0.085)
            sp = _blob(f"{TAG}ichor_horn{hi}_{i}", tuple(p),
                       (s * 1.4, s * rng.uniform(1.0, 2.0), s),
                       rot=(rng.uniform(0, 1.0), rng.uniform(0, 3.1), 0.0), subdiv=2)
            _mat(sp, mats["ichor"])
            ichor.append(sp)
        p, _ = surf.at(rng.uniform(0.22, 0.42), -math.pi / 2, out=1.0)
        dr = _tube(f"{TAG}ichor_horndrip{hi}",
                   [p, p + Vector((0, -0.11, 0)), p + Vector((0, -0.20, 0.006))],
                   [0.024, 0.030, 0.004], sides=6)
        _mat(dr, mats["ichor"])
        _smooth(dr, 1)
        ichor.append(dr)


def _build_embers(glow, mats, rng, edge_pts):
    """Smouldering embers along the cape's torn hem."""
    picks = edge_pts[:]
    rng.shuffle(picks)
    for i, p in enumerate(picks[:16]):
        s = rng.uniform(0.010, 0.023)
        e = _blob(f"{TAG}ember{i}",
                  (p.x + rng.uniform(-0.02, 0.02), p.y + rng.uniform(-0.04, 0.01),
                   p.z + rng.uniform(-0.02, 0.02)),
                  (s, s * rng.uniform(0.8, 1.7), s), subdiv=1)
        _mat(e, mats["ember"])
        glow.append(e)


# =================================================================== build ===

def build():
    """Creates the Chaos Lord.  Returns the named top-level objects; all of
    them are parented to CHAOS_root."""
    rng = random.Random(20261015)
    mats = _materials()

    body, glow, armor, ichor, axe = [], [], [], [], []

    torso_surf, horn_surfs = _build_body(body, glow, mats, rng)
    arm_surfs = _build_arms(body, mats, rng)
    leg_surfs = _build_legs(body, mats, rng)
    _build_armor(armor, glow, mats, rng)
    cape, edge_pts = _build_cape(mats, rng)
    _build_axe(axe, glow, ichor, mats, rng)
    _build_ichor_splashes(ichor, mats, rng, horn_surfs)
    _build_embers(glow, mats, rng, edge_pts)

    # ---- the signature: fine glowing cyan cracks across the hide --------
    cracks = []
    _veins(cracks, "torso", torso_surf, rng, mats, 22, nseg=(4, 8), seg_len=0.105,
           width=(0.010, 0.028), hot=0.22)
    for i, s in enumerate(arm_surfs):
        _veins(cracks, f"arm{i}", s, rng, mats, 11, nseg=(4, 8), seg_len=0.095,
               width=(0.009, 0.022), hot=0.16)
    for i, s in enumerate(leg_surfs):
        _veins(cracks, f"leg{i}", s, rng, mats, 11, nseg=(4, 8), seg_len=0.105,
               width=(0.009, 0.024), hot=0.14)
    for i, s in enumerate(horn_surfs):
        _veins(cracks, f"horn{i}", s, rng, mats, 4, nseg=(3, 6), seg_len=0.120,
               width=(0.007, 0.016), t_range=(0.04, 0.68), hot=0.30, branch_p=0.30)

    out = {
        "body": join_parts(body, TAG + "body"),
        "armor": join_parts(armor, TAG + "armor"),
        "cracks": join_parts(cracks + glow, TAG + "glow"),
        "axe": join_parts(axe, TAG + "axe"),
        "ichor": join_parts(ichor, TAG + "ichor"),
        "cape": cape,
    }

    root = bpy.data.objects.new(TAG + "root", None)
    bpy.context.collection.objects.link(root)
    root.location = (0.0, 0.0, 0.0)
    for obj in out.values():
        obj.parent = root
    out["root"] = root
    return out


if __name__ == "__main__":
    build()
