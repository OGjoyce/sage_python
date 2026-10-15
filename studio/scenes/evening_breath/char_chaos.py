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
  * Armour is SURFACE-CONFORMAL.  Every plate, strap and filigree line is
    lofted off the same parametric surface (`_Surf`) the body tube was built
    from -- `_shell()` samples (t, a) across that surface and offsets each
    sample along its own normal, so a plate curves with the chest and sits a
    measured 2-4 cm proud of the hide.  Nothing is a floating box.
  * The glowing cyan "cold lava vein" cracks are chains of thin emissive
    strips walked across those same surfaces, with branching -- an irregular
    network, kept sparse enough that it decorates the form rather than
    flattening it.
  * Emission strengths here are authored for this module's own test rig;
    scene_main applies the shot-level emission grade.

HIS LEFT is +X: a figure facing +Z is mirrored relative to the viewer, so
its left hand lies toward +X.  scene_main rotates him about -30 deg about Y,
which swings that left side -- pauldron, axe, open chest -- toward camera.
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
    M["armor_hi"], _ = nm(TAG + "armor_hi", base_color=(0.072, 0.085, 0.098, 1.0),
                          roughness=0.30, metallic=0.68)
    M["axe"], _ = nm(TAG + "axe_iron", base_color=(0.034, 0.041, 0.049, 1.0),
                     roughness=0.25, metallic=0.80)
    M["axe_edge"], _ = nm(TAG + "axe_edge", base_color=(0.145, 0.158, 0.172, 1.0),
                          roughness=0.16, metallic=0.95)
    M["steel"], _ = nm(TAG + "steel", base_color=(0.265, 0.277, 0.295, 1.0),
                       roughness=0.34, metallic=0.95)
    M["bone"], _ = nm(TAG + "bone", base_color=(0.430, 0.418, 0.372, 1.0),
                      roughness=0.44)
    M["cloth"], _ = nm(TAG + "cape_cloth", base_color=(0.018, 0.022, 0.026, 1.0),
                       roughness=0.56)
    M["mouth"], _ = nm(TAG + "maw", base_color=(0.006, 0.008, 0.010, 1.0), roughness=0.55)

    # emissives
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
    # dark fluid catching a teal highlight, not as glowing paint.
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


def _link(name, bm):
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


# ============================================================= primitives ===

def _frames(pts, ref=None):
    """Parallel-transported orthonormal frames along a polyline, so a lofted
    tube does not twist.  `u` is kept near `ref` (default +Z): for a mostly
    vertical tube that makes u = depth (Z, i.e. the FRONT at angle 0) and
    v = width (X, his left at angle +pi/2)."""
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
    return _link(name, bm)


def _strip(name, p0, p1, nrm, width, thick):
    """A thin flat slab lying in a surface -- the unit a glowing crack, a
    woven strap and a filigree line are all made of."""
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
    return _link(name, bm)


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
    """Parametric surface of a lofted tube: at(t, a) -> (point on the hide,
    outward normal).  Cracks, straps and armour plates are all placed with
    this, which is what guarantees they follow the body."""

    def __init__(self, pts, radii, ref=None):
        self.pts = [Vector(p) for p in pts]
        self.rr = [_radpair(r) for r in radii]
        _, self.us, self.vs = _frames(self.pts, ref)
        self.cum = [0.0]
        for i in range(len(self.pts) - 1):
            self.cum.append(self.cum[-1] + (self.pts[i + 1] - self.pts[i]).length)
        self.length = max(self.cum[-1], 1e-6)

    def at(self, t, a, out=1.0, gap=0.0):
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
        p = c + u * (ca * ru * out) + v * (sa * rv * out) + nrm * gap
        return p, nrm


def _shell(name, surf, t0, t1, a0, a1, gap0=0.020, gap1=None, thick=0.045,
           nt=6, na=8, bevel=0.008):
    """An armour plate lofted directly off `surf`: a (t, a) patch of the body
    surface, pushed out along its own normals by `gap` and given `thick`ness.
    The result curves with the chest instead of floating in front of it."""
    if gap1 is None:
        gap1 = gap0
    bm = bmesh.new()
    outer, inner = [], []
    for i in range(nt + 1):
        fi = i / nt
        t = t0 + (t1 - t0) * fi
        g = gap0 + (gap1 - gap0) * fi
        ro, ri = [], []
        for j in range(na + 1):
            a = a0 + (a1 - a0) * (j / na)
            p, n = surf.at(t, a)
            ri.append(bm.verts.new(p + n * g))
            ro.append(bm.verts.new(p + n * (g + thick)))
        outer.append(ro)
        inner.append(ri)
    for i in range(nt):
        for j in range(na):
            bm.faces.new([outer[i][j], outer[i][j + 1], outer[i + 1][j + 1], outer[i + 1][j]])
            bm.faces.new([inner[i][j], inner[i + 1][j], inner[i + 1][j + 1], inner[i][j + 1]])
    for i in range(nt):
        bm.faces.new([outer[i][0], outer[i + 1][0], inner[i + 1][0], inner[i][0]])
        bm.faces.new([outer[i][na], inner[i][na], inner[i + 1][na], outer[i + 1][na]])
    for j in range(na):
        bm.faces.new([outer[0][j], inner[0][j], inner[0][j + 1], outer[0][j + 1]])
        bm.faces.new([outer[nt][j], outer[nt][j + 1], inner[nt][j + 1], inner[nt][j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    obj = _link(name, bm)
    if bevel > 0:
        bv = obj.modifiers.new("Bevel", "BEVEL")
        bv.width = bevel
        bv.segments = 2
        bv.limit_method = "ANGLE"
    return obj


def _band(out_list, name, surf, ta_points, width, thick, gap, mat, smooth_n=True):
    """A strap / filigree line that follows the body surface through a list
    of (t, a) parameter points."""
    prev = None
    for k, (t, a) in enumerate(ta_points):
        p, n = surf.at(t, a, gap=gap)
        if prev is not None:
            s = _strip(f"{name}_{k}", prev[0], p,
                       (prev[1] + n) * 0.5 if smooth_n else n, width, thick)
            _mat(s, mat)
            out_list.append(s)
        prev = (p, n)


def _veins(out, name, surf, rng, mats, count, nseg=(4, 7), seg_len=0.10,
           width=(0.009, 0.022), t_range=(0.05, 0.95), hot=0.18, branch_p=0.42,
           gap=0.006):
    """Walk `count` irregular, branching crack veins across a _Surf.  Kept
    deliberately sparse: the veins should decorate the muscle, not net it."""

    def walk(tag, t, a, nsegs, w, depth):
        dt = rng.uniform(0.35, 1.0) * rng.choice((-1.0, 1.0)) * (seg_len / surf.length)
        da = rng.uniform(-1.0, 1.0) * 0.85
        p, n = surf.at(t, a, gap=gap)
        for k in range(nsegs):
            t2 = t + dt * rng.uniform(0.6, 1.4)
            a2 = a + da * rng.uniform(0.5, 1.5)
            if not (t_range[0] - 0.05 <= t2 <= t_range[1] + 0.05):
                dt = -dt
                t2 = t + dt
            p2, n2 = surf.at(t2, a2, gap=gap)
            ww = w * (1.0 - 0.62 * k / max(nsegs - 1, 1))
            m = mats["crack_hot"] if rng.random() < hot else mats["crack"]
            s = _strip(f"{TAG}crk_{tag}_{depth}_{k}", p, p2, (n + n2) * 0.5, ww, 0.009)
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
# shoulder is dropped and pulled back, and the head is thrust forward so it
# sits level with the shoulder tops.  Nothing here is mirrored.

SPINE = [
    ((0.00, 1.44, -0.03), (0.235, 0.315)),   # waist           t = 0.00
    ((0.01, 1.67, 0.10), (0.262, 0.355)),    # belly           t ~ 0.25
    ((0.03, 1.89, 0.24), (0.300, 0.460)),    # lower chest     t ~ 0.49
    ((0.05, 2.07, 0.34), (0.330, 0.580)),    # chest           t ~ 0.69
    ((0.06, 2.20, 0.36), (0.320, 0.615)),    # shoulder shelf  t ~ 0.81
    ((0.06, 2.30, 0.32), (0.285, 0.540)),    # trapezius       t ~ 0.91
    ((0.05, 2.37, 0.26), (0.225, 0.355)),    # base of neck    t = 1.00
]

L_SH = Vector((0.645, 2.325, 0.395))    # LEFT shoulder: forward and high
L_ELB = Vector((1.075, 1.780, 0.060))   # elbow kicked out and back
L_WRI = Vector((0.800, 1.620, 0.720))   # hand up on the haft

R_SH = Vector((-0.585, 2.090, -0.055))  # RIGHT shoulder: dropped and back
R_ELB = Vector((-0.890, 1.500, 0.195))
R_WRI = Vector((-0.640, 1.250, 0.860))  # low and forward: open palm-up beckon

# ---- axe frame: grip, haft direction, blade spread, blade face normal ----
AXE_G = Vector((0.800, 1.620, 0.720))
AXE_D = Vector((-0.10, 0.90, -0.62)).normalized()
AXE_T = AXE_G + AXE_D * 1.26
AXE_O = Vector((0.96, -0.12, -0.33)).normalized()
AXE_N = AXE_O.cross(AXE_D).normalized()


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
                  [(-0.42, 2.00, 0.00), (-0.14, 2.24, -0.06), (0.20, 2.35, -0.02),
                   (0.54, 2.30, 0.14)],
                  [(0.16, 0.19), (0.25, 0.28), (0.27, 0.30), (0.21, 0.24)], sides=8)
    _mat(hunch, skin)
    _smooth(hunch, 2)
    parts.append(hunch)

    # pectoral slabs, placed on the real chest surface (left one driven
    # forward with the shoulder)
    for side, t_c, a_c, w in (("l", 0.68, 0.52, 0.42), ("r", 0.62, -0.50, 0.38)):
        p0, _ = torso_surf.at(t_c + 0.09, a_c - w * 0.5, gap=-0.07)
        p1, _ = torso_surf.at(t_c, a_c, gap=0.01)
        p2, _ = torso_surf.at(t_c - 0.10, a_c + w * 0.5, gap=-0.07)
        pec = _tube(TAG + "pec_" + side, [p0, p1, p2],
                    [(0.070, 0.110), (0.140, 0.180), (0.070, 0.105)], sides=8)
        _mat(pec, skin)
        _smooth(pec, 2)
        parts.append(pec)

    # abdominal wall
    ab = [torso_surf.at(t, 0.0, gap=-0.09)[0] for t in (0.20, 0.34, 0.48)]
    abdo = _tube(TAG + "abs", ab,
                 [(0.100, 0.225), (0.120, 0.265), (0.120, 0.250)], sides=8)
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
                 [(0.05, 2.26, 0.20), (0.055, 2.36, 0.38), (0.06, 2.44, 0.55)],
                 [(0.215, 0.235), (0.195, 0.212), (0.168, 0.184)], sides=8)
    _mat(neck, skin)
    _smooth(neck, 2)
    parts.append(neck)

    skull = _tube(TAG + "skull",
                  [(0.06, 2.355, 0.490), (0.06, 2.455, 0.600), (0.06, 2.575, 0.645),
                   (0.06, 2.675, 0.585), (0.06, 2.730, 0.465)],
                  [(0.170, 0.165), (0.235, 0.215), (0.255, 0.225),
                   (0.215, 0.185), (0.125, 0.100)], sides=10)
    _mat(skull, skin)
    _smooth(skull, 2)
    parts.append(skull)

    muzzle = _tube(TAG + "muzzle",
                   [(0.06, 2.540, 0.630), (0.06, 2.490, 0.790), (0.06, 2.448, 0.910)],
                   [(0.135, 0.170), (0.105, 0.145), (0.070, 0.100)], sides=8)
    _mat(muzzle, skin)
    _smooth(muzzle, 2)
    parts.append(muzzle)

    jaw = _tube(TAG + "jaw",
                [(0.06, 2.435, 0.570), (0.06, 2.395, 0.750), (0.06, 2.380, 0.890)],
                [(0.085, 0.160), (0.070, 0.135), (0.048, 0.092)], sides=8)
    _mat(jaw, skin)
    _smooth(jaw, 2)
    parts.append(jaw)

    # heavy brow ridges, slanted down toward the nose: contemptuous
    for side, sx in (("l", 1.0), ("r", -1.0)):
        brow = add_box(TAG + "brow_" + side, (0.23, 0.065, 0.16),
                       (0.06 + sx * 0.150, 2.632, 0.790),
                       rotation=(0.24, 0.0, sx * -0.34), bevel_width=0.015, bevel_segments=2)
        _mat(brow, skin)
        parts.append(brow)

    # solid pupil-less glowing cyan eyes
    for side, sx in (("l", 1.0), ("r", -1.0)):
        socket = add_box(TAG + "socket_" + side, (0.23, 0.11, 0.06),
                         (0.06 + sx * 0.145, 2.558, 0.820),
                         rotation=(0.1, 0.0, sx * -0.30), bevel_width=0.010)
        _mat(socket, mats["mouth"])
        parts.append(socket)
        eye = _blob(TAG + "eye_" + side, (0.06 + sx * 0.142, 2.562, 0.830),
                    (0.092, 0.050, 0.058), rot=(0.0, 0.0, sx * -0.30), subdiv=3)
        _mat(eye, mats["eye"])
        glow.append(eye)

    # ---- bored half-smile: the mouth line lifts on his LEFT only --------
    maw = add_box(TAG + "maw", (0.34, 0.034, 0.060), (0.065, 2.403, 0.902),
                  rotation=(0.0, 0.0, 0.18), bevel_width=0.006)
    _mat(maw, mats["mouth"])
    parts.append(maw)
    curl = add_box(TAG + "maw_curl", (0.13, 0.030, 0.052), (0.235, 2.447, 0.848),
                   rotation=(0.0, -0.45, 0.55), bevel_width=0.006)
    _mat(curl, mats["mouth"])
    parts.append(curl)

    for i, (lx, ln) in enumerate([(-0.115, 0.050), (-0.045, 0.058), (0.030, 0.066),
                                  (0.105, 0.084), (0.175, 0.100), (0.235, 0.074)]):
        x, y = 0.065 + lx, 2.395 + lx * 0.180
        t = _tube(f"{TAG}tooth_lo_{i}",
                  [(x, y - 0.014, 0.900), (x, y + ln * 0.6, 0.896), (x, y + ln, 0.888)],
                  [0.019, 0.013, 0.003], sides=6)
        _mat(t, mats["bone"])
        _smooth(t, 1)
        parts.append(t)
    for i, (lx, ln) in enumerate([(-0.070, 0.046), (0.055, 0.052), (0.150, 0.060)]):
        x, y = 0.065 + lx, 2.415 + lx * 0.180
        t = _tube(f"{TAG}tooth_up_{i}",
                  [(x, y + 0.014, 0.894), (x, y - ln * 0.6, 0.890), (x, y - ln, 0.882)],
                  [0.016, 0.011, 0.002], sides=6)
        _mat(t, mats["bone"])
        _smooth(t, 1)
        parts.append(t)

    for i, (sx, px, py, pz, ln) in enumerate([(1, 0.215, 2.505, 0.730, 0.13),
                                              (-1, -0.100, 2.490, 0.720, 0.11),
                                              (1, 0.200, 2.415, 0.640, 0.10),
                                              (-1, -0.090, 2.405, 0.630, 0.09)]):
        sp = _tube(f"{TAG}cheekspur_{i}",
                   [(px, py, pz),
                    (px + sx * ln * 0.55, py + ln * 0.45, pz - ln * 0.55),
                    (px + sx * ln, py + ln * 0.85, pz - ln * 1.1)],
                   [0.034, 0.020, 0.003], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 1)
        parts.append(sp)

    # ---- long swept-back horns: the major silhouette element ------------
    # They clear the shoulder line (top ~2.55) and peak at ~2.99.
    horn_surfs = []
    for side, sx, st in (("l", 1.0, 1.0), ("r", -1.0, 0.93)):
        pts = [
            (0.06 + sx * 0.190, 2.615, 0.550),
            (0.06 + sx * 0.295, 2.790, 0.380),
            (0.06 + sx * 0.370, 2.915, 0.105),
            (0.06 + sx * 0.420, 2.992, -0.210 * st),
            (0.06 + sx * 0.440, 2.975, -0.540 * st),
            (0.06 + sx * 0.420, 2.878, -0.845 * st),
            (0.06 + sx * 0.375, 2.730, -1.100 * st),
        ]
        rad = [0.165, 0.152, 0.131, 0.106, 0.077, 0.046, 0.010]
        horn = _tube(TAG + "horn_" + side, pts, rad, sides=8)
        _mat(horn, mats["horn"])
        _smooth(horn, 2)
        parts.append(horn)
        hs = _Surf(pts, rad)
        horn_surfs.append(hs)

        for k in range(6):
            c, _ = hs.at(0.10 + k * 0.105, 0.0)
            r = 0.160 - 0.020 * k
            ring = _tube(f"{TAG}hornring_{side}_{k}",
                         [c + Vector((0, 0.016, 0.014)), c - Vector((0, 0.016, 0.014))],
                         [r, r], sides=8)
            _mat(ring, mats["horn"])
            parts.append(ring)

        bh = _tube(f"{TAG}browhorn_{side}",
                   [(0.06 + sx * 0.095, 2.662, 0.680),
                    (0.06 + sx * 0.130, 2.748, 0.575),
                    (0.06 + sx * 0.150, 2.810, 0.450)],
                   [0.046, 0.027, 0.004], sides=6)
        _mat(bh, mats["horn"])
        _smooth(bh, 1)
        parts.append(bh)

    return torso_surf, horn_surfs


# ===================================================================== arms ===

def _arm_chain(sh, elb, wri, r_sh, r_elb, r_wri, bulge):
    """One continuous polyline shoulder -> elbow -> wrist, with extra points
    bracketing the elbow so subdivision keeps the joint instead of melting
    it, plus a biceps / forearm bulge between them."""
    d1, d2 = (elb - sh), (wri - elb)
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
    surfs = {}

    for side, sh, elb, wri, bulge in (
            ("l", L_SH, L_ELB, L_WRI, Vector((0.055, 0.0, 0.045))),
            ("r", R_SH, R_ELB, R_WRI, Vector((-0.055, 0.0, 0.045)))):
        rsh = (0.258, 0.284) if side == "l" else (0.240, 0.262)
        pts, rad = _arm_chain(sh, elb, wri, rsh, (0.160, 0.170), (0.108, 0.116), bulge)
        arm = _tube(TAG + "arm_" + side, pts, rad, sides=10)
        _mat(arm, skin)
        _smooth(arm, 2)
        parts.append(arm)
        surfs[side] = _Surf(pts, rad)

        # trapezius / deltoid wedge tying the arm into the torso
        inward = -0.20 if side == "l" else 0.20
        tie = _tube(TAG + "delt_" + side,
                    [sh + Vector((inward, 0.06, -0.06)),
                     sh + Vector((0.0, 0.03, 0.0)),
                     sh + Vector((-inward * 0.7, -0.10, 0.02))],
                    [(0.195, 0.165), (0.252, 0.238), (0.218, 0.208)], sides=8)
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
        base = gp + d * (-0.090 + i * 0.062) - n * 0.090
        f = _tube(f"{TAG}fing_l_{i}",
                  [base, base + n * 0.095 + o * 0.095, base + n * 0.195 + o * 0.030],
                  [0.039, 0.033, 0.022], sides=6)
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
    pc = Vector((-0.620, 1.238, 0.995))
    palm_r = _tube(TAG + "hand_r",
                   [pc - Vector((0.0, 0.0, 0.140)), pc - Vector((0.0, 0.006, 0.020)),
                    pc + Vector((0.012, 0.000, 0.110))],
                   [(0.105, 0.052), (0.172, 0.050), (0.182, 0.044)], sides=10,
                   ref=(0.0, 1.0, 0.0))
    _mat(palm_r, skin)
    _smooth(palm_r, 2)
    parts.append(palm_r)
    heel = _blob(TAG + "palmheel_r", tuple(pc - Vector((0.0, 0.020, 0.115))),
                 (0.142, 0.062, 0.100), subdiv=2)
    _mat(heel, skin)
    _smooth(heel, 1)
    parts.append(heel)

    for i in range(4):
        fx = -0.138 + i * 0.092
        spread = 0.072 * (i - 1.5) / 1.5
        b = pc + Vector((fx, 0.000, 0.112))
        m = b + Vector((spread * 0.8, 0.012, 0.148))
        t = m + Vector((spread * 1.0, 0.064, 0.118))
        f = _tube(f"{TAG}fing_r_{i}", [b, m, t],
                  [0.045 - 0.004 * abs(i - 1.5), 0.038, 0.024], sides=6)
        _mat(f, skin)
        _smooth(f, 2)
        parts.append(f)
        cl = _tube(f"{TAG}fclaw_r_{i}", [t, t + Vector((spread * 0.3, 0.046, 0.042))],
                   [0.019, 0.002], sides=6)
        _mat(cl, mats["horn"])
        _smooth(cl, 1)
        parts.append(cl)
    th = _tube(TAG + "thumb_r",
               [pc + Vector((0.142, -0.010, -0.050)), pc + Vector((0.244, 0.010, 0.040)),
                pc + Vector((0.294, 0.046, 0.118))],
               [0.050, 0.039, 0.024], sides=6)
    _mat(th, skin)
    _smooth(th, 2)
    parts.append(th)
    thc = _tube(TAG + "thumbclaw_r",
                [pc + Vector((0.294, 0.046, 0.118)), pc + Vector((0.326, 0.082, 0.158))],
                [0.020, 0.002], sides=6)
    _mat(thc, mats["horn"])
    _smooth(thc, 1)
    parts.append(thc)

    return surfs


# ===================================================================== legs ===

LEGS = {
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


def _build_legs(parts, mats, rng):
    """Massive digitigrade legs, one planted forward and one braced back."""
    skin = mats["skin"]
    surfs = {}

    for side, (pts, rad, (fx, fz, zd)) in LEGS.items():
        leg = _tube(TAG + "leg_" + side, pts, rad, sides=10)
        _mat(leg, skin)
        _smooth(leg, 2)
        parts.append(leg)
        surfs[side] = _Surf(pts, rad)

        foot = _tube(TAG + "foot_" + side,
                     [(fx, 0.145, fz), (fx, 0.110, fz + zd * 0.14),
                      (fx, 0.086, fz + zd * 0.26)],
                     [(0.142, 0.158), (0.112, 0.168), (0.082, 0.150)], sides=8)
        _mat(foot, skin)
        _smooth(foot, 2)
        parts.append(foot)

        for i, ox in enumerate((-0.125, 0.0, 0.125)):
            cl = _tube(f"{TAG}claw_{side}_{i}",
                       [(fx + ox, 0.090, fz + zd * 0.24),
                        (fx + ox * 1.25, 0.066, fz + zd * 0.39),
                        (fx + ox * 1.45, 0.028, fz + zd * 0.53)],
                       [0.062, 0.042, 0.004], sides=6)
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

def _build_armor(parts, glow, mats, rng, torso, arms, legs):
    """Woven black obsidian plate with teal filigree, a big spiked LEFT
    pauldron, and a belt with a metal skull clasp.

    Every plate is a `_shell` lofted off the body's own parametric surface,
    so it curves with the chest and sits 2-4 cm proud of the hide.  On the
    torso, a = 0 is dead centre front and a = +pi/2 is his left side."""
    A, AH, F = mats["armor"], mats["armor_hi"], mats["filigree"]

    def shell(name, surf, t0, t1, a0, a1, m=None, **kw):
        o = _shell(TAG + name, surf, t0, t1, a0, a1, **kw)
        _mat(o, m if m else A)
        parts.append(o)
        return o

    def fil(name, surf, ta, gap, w=0.013):
        _band(glow, TAG + name, surf, ta, w, 0.009, gap, F)

    # ---- cuirass: many small curved plates, not two big slabs -----------
    shell("cuir_sternum", torso, 0.505, 0.815, -0.36, 0.36,
          gap0=0.018, gap1=0.024, thick=0.042, nt=7, na=7, m=AH)
    shell("cuir_pec_l", torso, 0.530, 0.805, 0.39, 1.06,
          gap0=0.016, gap1=0.022, thick=0.040, nt=6, na=6)
    shell("cuir_pec_r", torso, 0.500, 0.780, -1.06, -0.39,
          gap0=0.016, gap1=0.022, thick=0.040, nt=6, na=6)
    shell("cuir_clav", torso, 0.815, 0.920, -1.18, 1.18,
          gap0=0.026, gap1=0.040, thick=0.044, nt=4, na=10, m=AH)
    shell("cuir_flank_l", torso, 0.430, 0.740, 1.10, 1.72,
          gap0=0.014, thick=0.034, nt=6, na=5)
    shell("cuir_flank_r", torso, 0.410, 0.715, -1.72, -1.10,
          gap0=0.014, thick=0.034, nt=6, na=5)
    shell("cuir_back", torso, 0.520, 0.900, 2.45, 3.84,
          gap0=0.016, thick=0.040, nt=7, na=8)
    shell("girdle", torso, 0.430, 0.520, -1.60, 1.60,
          gap0=0.018, thick=0.038, nt=3, na=12, m=AH)

    # ---- "woven" obsidian: narrow straps crossing over the midriff ------
    for i in range(5):
        off = -0.26 + i * 0.13
        _band(parts, f"{TAG}weave_a{i}", torso,
              [(0.16 + k * 0.055, -0.95 + off + k * 0.48) for k in range(5)],
              0.070, 0.022, 0.010, A)
        _band(parts, f"{TAG}weave_b{i}", torso,
              [(0.16 + k * 0.055, 0.95 + off - k * 0.48) for k in range(5)],
              0.062, 0.020, 0.024, AH)

    # ---- filigree tracery over the cuirass ------------------------------
    for i in range(5):
        a = -0.27 + i * 0.135
        fil(f"fil_ch{i}", torso, [(0.52 + k * 0.072, a * (1.0 - k * 0.12))
                                  for k in range(5)], gap=0.064)
    for i in range(3):
        t = 0.56 + i * 0.100
        fil(f"fil_chh{i}", torso, [(t, -0.34 + k * 0.17) for k in range(5)],
            gap=0.064, w=0.011)
    for i in range(3):
        fil(f"fil_back{i}", torso, [(0.56 + k * 0.08, 2.70 + i * 0.42) for k in range(5)],
            gap=0.060, w=0.012)

    # ---- high collar behind the head: sells the hunch -------------------
    shell("collar", torso, 0.880, 1.000, 1.85, 4.45,
          gap0=0.045, gap1=0.300, thick=0.050, nt=4, na=14, m=AH)
    for i in range(7):
        a = 2.05 + i * 0.39
        base, n = torso.at(0.995, a, gap=0.30)
        sp = _tube(f"{TAG}collarspike_{i}",
                   [base, base + n * 0.10 + Vector((0, 0.09, 0)),
                    base + n * 0.17 + Vector((0, 0.20, 0))],
                   [0.050, 0.030, 0.004], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 1)
        parts.append(sp)

    # ---- spiked LEFT pauldron, lofted off the deltoid -------------------
    la = arms["l"]
    shell("paul_l0", la, 0.000, 0.135, -math.pi, math.pi,
          gap0=0.045, gap1=0.060, thick=0.050, nt=3, na=14, m=AH, bevel=0.010)
    shell("paul_l1", la, 0.105, 0.255, -2.75, 0.75,
          gap0=0.075, gap1=0.090, thick=0.050, nt=4, na=10, bevel=0.012)
    shell("paul_l2", la, 0.230, 0.385, -2.55, 0.60,
          gap0=0.095, gap1=0.105, thick=0.048, nt=4, na=10, m=AH, bevel=0.012)
    for i, (t, a, ln, lift) in enumerate([(0.05, -2.45, 0.62, 0.55),
                                          (0.07, -1.95, 0.72, 0.45),
                                          (0.09, -1.45, 0.70, 0.30),
                                          (0.12, -0.95, 0.58, 0.18),
                                          (0.20, -2.20, 0.52, 0.35),
                                          (0.20, -1.25, 0.48, 0.15)]):
        base, n = la.at(t, a, gap=0.075)
        d = (n + Vector((0.0, lift, 0.0))).normalized()
        sp = _tube(f"{TAG}paulspike_{i}",
                   [base, base + d * ln * 0.40, base + d * ln * 0.74, base + d * ln],
                   [0.088, 0.060, 0.033, 0.004], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 2)
        parts.append(sp)
    for i in range(4):
        fil(f"fil_paul{i}", la, [(0.02 + k * 0.08, -2.5 + i * 0.75)
                                 for k in range(4)], gap=0.130, w=0.014)

    # ---- smaller strapped RIGHT shoulder plate (asymmetry) --------------
    ra = arms["r"]
    shell("paul_r0", ra, 0.000, 0.130, -math.pi, math.pi,
          gap0=0.030, gap1=0.040, thick=0.042, nt=3, na=12)
    shell("paul_r1", ra, 0.100, 0.235, 0.45, 3.30,
          gap0=0.052, gap1=0.062, thick=0.044, nt=4, na=9, m=AH)
    for i, (t, a, ln) in enumerate([(0.06, 1.70, 0.28), (0.14, 2.25, 0.24)]):
        base, n = ra.at(t, a, gap=0.055)
        d = (n + Vector((0.0, 0.5, 0.0))).normalized()
        sp = _tube(f"{TAG}paulspike_r{i}", [base, base + d * ln * 0.6, base + d * ln],
                   [0.058, 0.032, 0.004], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 1)
        parts.append(sp)

    # ---- bracers, lofted straight onto the forearms ---------------------
    for side in ("l", "r"):
        s = arms[side]
        shell(f"bracer_{side}", s, 0.640, 0.900, -math.pi, math.pi,
              gap0=0.028, gap1=0.024, thick=0.042, nt=4, na=12)
        for i in range(3):
            fil(f"fil_brac_{side}{i}", s,
                [(0.66 + k * 0.07, -1.0 + i * 1.0) for k in range(4)], gap=0.074, w=0.012)
        for i in range(2):
            base, n = s.at(0.70 + i * 0.10, -1.55 if side == "l" else 1.55, gap=0.070)
            sp = _tube(f"{TAG}bracspike_{side}{i}",
                       [base, base + n * 0.09, base + n * 0.18],
                       [0.046, 0.027, 0.003], sides=6)
            _mat(sp, mats["horn"])
            _smooth(sp, 1)
            parts.append(sp)

    # ---- thigh / knee plating, lofted onto the legs ---------------------
    for side in ("l", "r"):
        s = legs[side]
        shell(f"thigh_{side}", s, 0.060, 0.260, -1.15, 1.15,
              gap0=0.022, thick=0.042, nt=4, na=8, m=AH)
        shell(f"knee_{side}", s, 0.285, 0.420, -1.35, 1.35,
              gap0=0.028, thick=0.046, nt=3, na=9)
        base, n = s.at(0.345, 0.0, gap=0.070)
        sp = _tube(f"{TAG}kneespike_{side}", [base, base + n * 0.12, base + n * 0.24],
                   [0.064, 0.037, 0.004], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 1)
        parts.append(sp)
        fil(f"fil_knee_{side}", s, [(0.32, -0.9 + k * 0.6) for k in range(4)],
            gap=0.080, w=0.012)
        shell(f"greave_{side}", s, 0.560, 0.720, -1.5, 1.5,
              gap0=0.022, thick=0.038, nt=3, na=9)

    # ---- belt + metal skull clasp ---------------------------------------
    belt = _tube(TAG + "belt",
                 [(0.0, 1.400, -0.045), (0.0, 1.475, -0.010), (0.0, 1.550, 0.000)],
                 [(0.268, 0.374), (0.293, 0.409), (0.273, 0.384)], sides=14)
    _mat(belt, A)
    belt.modifiers.new("Bevel", "BEVEL").width = 0.009
    parts.append(belt)
    for i in range(9):
        a = -1.40 + i * 0.35
        o = add_box(f"{TAG}beltstud{i}", (0.08, 0.085, 0.055),
                    (math.sin(a) * 0.405, 1.478, math.cos(a) * 0.300 - 0.010),
                    rotation=(0.0, -a, 0.0), bevel_width=0.008, bevel_segments=2)
        _mat(o, AH)
        parts.append(o)

    sk = Vector((0.03, 1.478, 0.310))
    cr = _blob(TAG + "skull_cranium", tuple(sk + Vector((0, 0.035, -0.012))),
               (0.120, 0.112, 0.092), subdiv=2)
    _mat(cr, mats["steel"])
    _smooth(cr, 1)
    parts.append(cr)
    jw = _blob(TAG + "skull_jaw", tuple(sk + Vector((0, -0.062, 0.018))),
               (0.094, 0.057, 0.078), subdiv=2)
    _mat(jw, mats["steel"])
    _smooth(jw, 1)
    parts.append(jw)
    for sx in (-1, 1):
        soc = _blob(f"{TAG}skull_socket_{sx}", tuple(sk + Vector((sx * 0.051, 0.042, 0.072))),
                    (0.035, 0.030, 0.022), subdiv=2)
        _mat(soc, mats["crack_dim"])
        glow.append(soc)
        base = sk + Vector((sx * 0.097, 0.066, 0.008))
        hs = _tube(f"{TAG}skull_horn_{sx}",
                   [base, base + Vector((sx * 0.060, 0.065, -0.034)),
                    base + Vector((sx * 0.090, 0.115, -0.078))],
                   [0.030, 0.018, 0.003], sides=6)
        _mat(hs, mats["steel"])
        _smooth(hs, 1)
        parts.append(hs)
    for i in range(4):
        o = add_box(f"{TAG}skull_teeth{i}", (0.024, 0.038, 0.022),
                    (sk.x - 0.038 + i * 0.026, 1.432, sk.z + 0.058), bevel_width=0.004)
        _mat(o, mats["steel"])
        parts.append(o)

    # ---- tassets hanging off the belt -----------------------------------
    for i, (a, ln) in enumerate([(-1.15, 0.36), (-0.70, 0.46), (-0.25, 0.52),
                                 (0.22, 0.50), (0.68, 0.42), (1.12, 0.32)]):
        bx = math.sin(a) * 0.41
        bz = math.cos(a) * 0.305 - 0.015
        o = add_box(f"{TAG}tasset{i}", (0.25, ln, 0.07),
                    (bx * 1.06, 1.395 - ln * 0.5, bz * 1.06),
                    rotation=(0.14, -a, 0.03), bevel_width=0.010, bevel_segments=2)
        _mat(o, AH if i % 2 else A)
        parts.append(o)


# ==================================================================== cape ===

def _build_cape(mats, rng):
    """Torn, smouldering black cape: a shoulder-anchored grid swept back by
    wind, with whole columns cut short so the hem tears into strips and real
    gaps open between them.  Returns (object, torn-edge points for embers)."""
    nu, nv = 26, 18
    y_top = 2.44
    R = 0.60
    a0, a1 = math.radians(56.0), math.radians(304.0)
    Lmax = 2.45

    lengths = []
    for i in range(nu + 1):
        u = i / nu
        base = 0.78 + 0.13 * math.sin(u * 7.3 + 1.1) + 0.10 * math.sin(u * 15.1)
        roll = rng.random()
        if roll < 0.24:
            base *= rng.uniform(0.40, 0.62)                   # deep tear
        elif roll < 0.42:
            base = min(1.0, base * rng.uniform(1.10, 1.24))   # long tongue
        lengths.append(max(0.22, min(1.0, base)))

    def vert(i, j):
        u = i / nu
        a = a0 + (a1 - a0) * u
        v = j / nv
        x0, z0 = math.sin(a) * R, math.cos(a) * R
        y = y_top - v * Lmax * 0.93
        flare = 1.0 + 1.00 * v
        x = x0 * flare + 0.32 * v * v + 0.12 * math.sin(a * 2.1 + v * 3.4) * v
        z = z0 * (1.0 + 0.38 * v) - 0.82 * v * v + 0.11 * math.sin(a * 3.3 + v * 2.0) * v
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

    cape = _link(TAG + "cape", bm)
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
    """A huge, crude two-handed axe resting on the forward left shoulder.
    The head is a proper bearded crescent -- straight top shoulder, wide
    cutting arc, long hooked beard -- with a bright honed edge so it reads
    as an axe and not as a dark angular mass."""
    d, o, n, T = AXE_D, AXE_O, AXE_N, AXE_T
    butt = AXE_G - d * 0.42

    haft = _tube(TAG + "axe_haft",
                 [butt, butt + d * 0.42, AXE_G, AXE_G.lerp(T, 0.55), T, T + d * 0.16],
                 [0.058, 0.068, 0.074, 0.070, 0.066, 0.058], sides=10)
    _mat(haft, mats["axe"])
    haft.modifiers.new("Bevel", "BEVEL").width = 0.006
    for poly in haft.data.polygons:
        poly.use_smooth = True
    parts.append(haft)
    cap = _tube(TAG + "axe_buttcap", [butt - d * 0.06, butt + d * 0.07], [0.082, 0.088], sides=10)
    _mat(cap, mats["steel"])
    parts.append(cap)
    for i in range(7):
        p = AXE_G + d * (-0.32 + i * 0.105)
        bind = _tube(f"{TAG}axe_bind{i}", [p - d * 0.026, p + d * 0.026], [0.084, 0.084], sides=10)
        _mat(bind, mats["armor"])
        parts.append(bind)

    # ---- bearded blade ---------------------------------------------------
    # (s along the haft, t outward).  Outer arc = the cutting edge.
    outline = [(0.44, 0.00), (0.46, 0.17), (0.40, 0.39), (0.26, 0.57),
               (0.00, 0.69), (-0.30, 0.70), (-0.56, 0.57), (-0.70, 0.35),
               (-0.62, 0.13), (-0.44, 0.00)]
    th0, tmax = 0.075, 0.70
    bm = bmesh.new()
    front, back = [], []
    for (s, t) in outline:
        th = th0 * max(0.05, 1.0 - (t / tmax) * 0.95)
        p = T + d * s + o * t
        front.append(bm.verts.new(p + n * th))
        back.append(bm.verts.new(p - n * th))
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        bm.faces.new([front[i], front[j], back[j], back[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    blade = _link(TAG + "axe_blade", bm)
    _mat(blade, mats["axe"])
    bv = blade.modifiers.new("Bevel", "BEVEL")
    bv.width = 0.013
    bv.segments = 2
    parts.append(blade)

    # honed cutting edge: a bright steel welt along the outer arc
    arc = [(0.26, 0.57), (0.13, 0.645), (0.00, 0.69), (-0.15, 0.705),
           (-0.30, 0.70), (-0.44, 0.645), (-0.56, 0.57), (-0.65, 0.46)]
    for i in range(len(arc) - 1):
        p0 = T + d * arc[i][0] + o * arc[i][1]
        p1 = T + d * arc[i + 1][0] + o * arc[i + 1][1]
        e = _strip(f"{TAG}axe_welt{i}", p0, p1, o, 0.030, 0.018)
        _mat(e, mats["axe_edge"])
        parts.append(e)

    bspike = _tube(TAG + "axe_backspike",
                   [T - o * 0.02, T - o * 0.28 + d * 0.07, T - o * 0.50 + d * 0.14],
                   [(0.185, 0.064), (0.125, 0.044), (0.012, 0.010)], sides=6)
    _mat(bspike, mats["axe"])
    parts.append(bspike)
    for i, s in enumerate((-0.42, 0.40)):
        col = _tube(f"{TAG}axe_collar{i}", [T + d * s - o * 0.05, T + d * s + o * 0.14],
                    [0.098, 0.084], sides=8)
        _mat(col, mats["steel"])
        col.modifiers.new("Bevel", "BEVEL").width = 0.006
        parts.append(col)
    fin = _tube(TAG + "axe_finial", [T + d * 0.16, T + d * 0.24, T + d * 0.33],
                [0.058, 0.035, 0.004], sides=6)
    _mat(fin, mats["horn"])
    _smooth(fin, 1)
    parts.append(fin)

    for i in range(5):
        s = -0.38 + i * 0.19
        f = _strip(f"{TAG}axe_fil{i}", T + d * s + o * 0.08 + n * (th0 * 0.92),
                   T + d * (s * 0.5) + o * 0.46 + n * (th0 * 0.28), n, 0.018, 0.010)
        _mat(f, mats["filigree"])
        glow.append(f)
    for sgn in (1, -1):
        f = _strip(f"{TAG}axe_filspine{sgn}",
                   T + d * (-0.38) + o * 0.12 + n * sgn * (th0 * 0.88),
                   T + d * 0.36 + o * 0.12 + n * sgn * (th0 * 0.88), n * sgn, 0.024, 0.010)
        _mat(f, mats["filigree"])
        glow.append(f)

    # ---- ichor running off the cutting edge, dripping to the crystal ----
    for i, (s, t) in enumerate([(0.22, 0.60), (0.00, 0.69), (-0.26, 0.70),
                                (-0.50, 0.60), (-0.66, 0.34)]):
        base = T + d * s + o * t
        ln = rng.uniform(0.20, 0.42)
        dr = _tube(f"{TAG}axe_drip{i}",
                   [base, base + Vector((0.0, -ln * 0.35, 0.008)),
                    base + Vector((0.008, -ln * 0.72, 0.012)),
                    base + Vector((0.008, -ln, 0.010))],
                   [0.028, 0.044, 0.030, 0.004], sides=6)
        _mat(dr, mats["ichor"])
        _smooth(dr, 2)
        ichor.append(dr)
        if i in (1, 3):
            dp = _blob(f"{TAG}axe_droplet{i}",
                       tuple(base + Vector((0.008, -ln - rng.uniform(0.25, 0.60), 0.01))),
                       (0.026, 0.042, 0.026), subdiv=2)
            _mat(dp, mats["ichor"])
            _smooth(dp, 1)
            ichor.append(dp)
    for i in range(len(arc) - 1):
        p0 = T + d * arc[i][0] + o * arc[i][1]
        p1 = T + d * arc[i + 1][0] + o * arc[i + 1][1]
        if i % 2 == 0:
            sm = _strip(f"{TAG}axe_edgeichor{i}", p0, p1, n, 0.085, 0.034)
            _mat(sm, mats["ichor"])
            ichor.append(sm)


# ========================================================= ichor / embers ===

def _build_ichor_splashes(ichor, mats, rng, torso, horn_surfs):
    """Black-teal ichor splashed across the chest and horns, thrown off the
    axe that rests there.  Placed on the real body surface."""
    for i in range(16):
        t = rng.uniform(0.42, 0.95)
        a = rng.uniform(-1.05, 1.15)
        p, _ = torso.at(t, a, gap=0.072 if abs(a) < 1.05 else 0.030)
        s = rng.uniform(0.045, 0.100)
        sp = _blob(f"{TAG}ichor_chest{i}", tuple(p),
                   (s * rng.uniform(0.7, 1.5), s * rng.uniform(0.9, 1.9), 0.022),
                   rot=(0.3, 0.0, rng.uniform(-0.8, 0.8)), subdiv=2)
        _mat(sp, mats["ichor"])
        ichor.append(sp)
    for i in range(5):
        a = rng.uniform(-0.70, 0.80)
        t0 = rng.uniform(0.70, 0.90)
        pts = [torso.at(t0 - k * 0.075, a + k * 0.03, gap=0.072)[0] for k in range(3)]
        run = _tube(f"{TAG}ichor_run{i}", pts, [0.022, 0.017, 0.005], sides=6)
        _mat(run, mats["ichor"])
        _smooth(run, 1)
        ichor.append(run)

    for hi, surf in enumerate(horn_surfs):
        for i in range(5):
            p, _ = surf.at(rng.uniform(0.04, 0.55), rng.uniform(0, 2 * math.pi))
            s = rng.uniform(0.040, 0.085)
            sp = _blob(f"{TAG}ichor_horn{hi}_{i}", tuple(p),
                       (s * 1.4, s * rng.uniform(1.0, 2.0), s),
                       rot=(rng.uniform(0, 1.0), rng.uniform(0, 3.1), 0.0), subdiv=2)
            _mat(sp, mats["ichor"])
            ichor.append(sp)
        p, _ = surf.at(rng.uniform(0.22, 0.42), -math.pi / 2)
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
    _build_armor(armor, glow, mats, rng, torso_surf, arm_surfs, leg_surfs)
    cape, edge_pts = _build_cape(mats, rng)
    _build_axe(axe, glow, ichor, mats, rng)
    _build_ichor_splashes(ichor, mats, rng, torso_surf, horn_surfs)
    _build_embers(glow, mats, rng, edge_pts)

    # ---- the signature: fine glowing cyan cracks across the hide --------
    # Sparse on purpose: a branching network over the exposed muscle, not a
    # net over every surface (that flattens the form).
    cracks = []
    _veins(cracks, "torso", torso_surf, rng, mats, 9, nseg=(4, 7), seg_len=0.11,
           width=(0.009, 0.024), t_range=(0.10, 0.92), hot=0.20)
    for side, s in arm_surfs.items():
        _veins(cracks, f"arm{side}", s, rng, mats, 6, nseg=(4, 7), seg_len=0.10,
               width=(0.008, 0.019), t_range=(0.28, 0.95), hot=0.16)
    for side, s in leg_surfs.items():
        _veins(cracks, f"leg{side}", s, rng, mats, 6, nseg=(4, 7), seg_len=0.11,
               width=(0.008, 0.020), t_range=(0.38, 0.95), hot=0.14)
    for i, s in enumerate(horn_surfs):
        _veins(cracks, f"horn{i}", s, rng, mats, 3, nseg=(3, 5), seg_len=0.13,
               width=(0.006, 0.014), t_range=(0.05, 0.62), hot=0.28, branch_p=0.25)

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
