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
    M["armor"], _ = nm(TAG + "armor", base_color=(0.028, 0.035, 0.043, 1.0),
                       roughness=0.27, metallic=0.32)
    M["armor_hi"], _ = nm(TAG + "armor_hi", base_color=(0.062, 0.074, 0.086, 1.0),
                          roughness=0.31, metallic=0.38)
    M["axe"], _ = nm(TAG + "axe_iron", base_color=(0.030, 0.037, 0.045, 1.0),
                     roughness=0.30, metallic=0.45)
    M["axe_edge"], _ = nm(TAG + "axe_edge", base_color=(0.190, 0.205, 0.220, 1.0),
                          roughness=0.18, metallic=0.80)
    M["steel"], _ = nm(TAG + "steel", base_color=(0.210, 0.222, 0.238, 1.0),
                       roughness=0.38, metallic=0.75)
    M["bone"], _ = nm(TAG + "bone", base_color=(0.545, 0.528, 0.470, 1.0),
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
    # the geometric half of the "evil aura": torn wisps peeling off him.
    # scene_main owns the volumetric half, so nothing here is a light.
    M["wisp"], _ = nm(TAG + "wisp", base_color=(0.013, 0.030, 0.034, 1.0),
                      roughness=0.88,
                      emission_color=(0.040, 0.300, 0.325, 1.0), emission_strength=0.30)

    # black-teal ichor: wet and very glossy, barely self-lit so it reads as
    # dark fluid catching a teal highlight, not as glowing paint.
    M["ichor"], _ = nm(TAG + "ichor", base_color=ICHOR, roughness=0.035, metallic=0.20,
                       emission_color=(0.016, 0.110, 0.120, 1.0), emission_strength=0.05)
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
# Built to measured numbers, floor = Y 0, total height 3.00 m:
#   floor -> hip            1.45      (long, heavy digitigrade legs)
#   hip -> shoulder line    0.85      (shoulders 2.25 - 2.33)
#   top of skull            2.62      (the HORNS are what reach 3.00)
#   horn tips               ~3.00, swept back behind the skull
#   shoulder width          ~1.25 overall
#   fingertips of the free arm hang to ~0.95 (knee height)
# The hunch is carried by the forward/raised LEFT shoulder (+X, the axe
# shoulder, the side the scene rotation turns toward camera) against the
# dropped and retracted RIGHT shoulder, plus a spine pitched ~19 deg forward
# and a head thrust forward on a visible neck.

SPINE = [
    ((0.00, 1.45, 0.00), (0.175, 0.225)),    # waist          t = 0.00
    ((0.01, 1.68, 0.09), (0.197, 0.258)),    # belly          t ~ 0.26
    ((0.02, 1.90, 0.19), (0.226, 0.326)),    # lower chest    t ~ 0.52
    ((0.04, 2.08, 0.27), (0.245, 0.376)),    # chest          t ~ 0.73
    ((0.05, 2.21, 0.29), (0.238, 0.390)),    # shoulder shelf t ~ 0.87
    ((0.05, 2.30, 0.26), (0.208, 0.330)),    # trapezius      t ~ 0.97
    ((0.04, 2.36, 0.21), (0.163, 0.215)),    # base of neck   t = 1.00
]

L_SH = Vector((0.385, 2.325, 0.395))    # LEFT shoulder: forward and raised
L_ELB = Vector((0.610, 1.846, 0.072))
L_WRI = Vector((0.550, 1.650, 0.550))   # gripping the haft in FRONT of the hip

R_SH = Vector((-0.375, 2.185, 0.160))   # RIGHT shoulder: dropped and back
R_ELB = Vector((-0.620, 1.630, 0.280))
R_WRI = Vector((-0.820, 1.420, 0.680))  # free arm, low and swung out

HEAD_C = Vector((0.05, 2.46, 0.56))

# ---- the axe -------------------------------------------------------------
# A 2.2 m haft running diagonally across the chest from a butt down by the
# forward knee up to a head sitting squarely ON the raised left shoulder.
# The bit spreads almost straight out along +X, which puts the blade's broad
# face within ~30 deg of the hero camera: a big flat axe silhouette, with the
# haft a clear unbroken diagonal line across the body.
AXE_T = Vector((0.440, 2.720, 0.140))                 # centre of the head
AXE_D = Vector((-0.110, 1.070, -0.410)).normalized()  # butt -> head
AXE_B = AXE_T - AXE_D * 2.20                          # butt, low and forward
AXE_O = Vector((0.9946, 0.0752, -0.0706)).normalized()  # the bit spreads out
AXE_N = AXE_O.cross(AXE_D).normalized()                 # broad face -> camera


def _splash(out_list, name, surf, t, a, rt, ra, mats, rng, drip=0.0):
    """A flat, wet, irregular ichor splash CONFORMING to the surface: two or
    three overlapping thin surface patches, not a sphere stuck on the skin."""
    for k in range(rng.randint(2, 3)):
        tt = t + rng.uniform(-rt, rt) * 0.5
        aa = a + rng.uniform(-ra, ra) * 0.5
        dt = rt * rng.uniform(0.45, 1.0)
        da = ra * rng.uniform(0.45, 1.0)
        o = _shell(f"{name}_{k}", surf, tt - dt, tt + dt, aa - da, aa + da,
                   gap0=0.004, gap1=0.004, thick=0.008, nt=2, na=3, bevel=0.0)
        _mat(o, mats["ichor"])
        out_list.append(o)
    if drip > 0.0:
        pts = [surf.at(t - k * drip * 0.42, a + k * 0.02, gap=0.010)[0] for k in range(3)]
        d = _tube(f"{name}_run", pts, [0.016, 0.012, 0.003], sides=6)
        _mat(d, mats["ichor"])
        _smooth(d, 1)
        out_list.append(d)


# ============================================================ body masses ===

def _build_body(parts, glow, mats, rng):
    skin = mats["skin"]

    torso = _tube(TAG + "torso", [p for p, _ in SPINE], [r for _, r in SPINE], sides=12)
    _mat(torso, skin)
    _smooth(torso, 2)
    parts.append(torso)
    torso_surf = _Surf([p for p, _ in SPINE], [r for _, r in SPINE])

    # rounded hunch across the shoulder blades
    hunch = _tube(TAG + "hunch",
                  [(-0.30, 2.02, 0.02), (-0.10, 2.22, -0.03), (0.14, 2.32, 0.00),
                   (0.36, 2.30, 0.12)],
                  [(0.120, 0.140), (0.175, 0.200), (0.190, 0.212), (0.150, 0.172)],
                  sides=8)
    _mat(hunch, skin)
    _smooth(hunch, 2)
    parts.append(hunch)

    for side, t_c, a_c, w in (("l", 0.74, 0.50, 0.40), ("r", 0.67, -0.48, 0.36)):
        p0, _ = torso_surf.at(t_c + 0.08, a_c - w * 0.5, gap=-0.055)
        p1, _ = torso_surf.at(t_c, a_c, gap=0.008)
        p2, _ = torso_surf.at(t_c - 0.09, a_c + w * 0.5, gap=-0.055)
        pec = _tube(TAG + "pec_" + side, [p0, p1, p2],
                    [(0.050, 0.080), (0.100, 0.130), (0.050, 0.076)], sides=8)
        _mat(pec, skin)
        _smooth(pec, 2)
        parts.append(pec)

    ab = [torso_surf.at(t, 0.0, gap=-0.065)[0] for t in (0.18, 0.34, 0.50)]
    abdo = _tube(TAG + "abs", ab,
                 [(0.070, 0.160), (0.085, 0.190), (0.085, 0.180)], sides=8)
    _mat(abdo, skin)
    _smooth(abdo, 2)
    parts.append(abdo)

    pelvis = _tube(TAG + "pelvis",
                   [(0.00, 1.21, -0.04), (0.00, 1.34, -0.01), (0.00, 1.49, 0.01)],
                   [(0.180, 0.255), (0.205, 0.300), (0.180, 0.245)], sides=12)
    _mat(pelvis, skin)
    _smooth(pelvis, 2)
    parts.append(pelvis)

    # ---- visible, thick neck carrying the head forward ------------------
    nk_pts = [(0.045, 2.25, 0.18), (0.050, 2.31, 0.33), (0.050, 2.345, 0.47)]
    nk_rad = [(0.150, 0.165), (0.140, 0.152), (0.126, 0.138)]
    neck = _tube(TAG + "neck", nk_pts, nk_rad, sides=8)
    _mat(neck, skin)
    _smooth(neck, 2)
    parts.append(neck)
    neck_surf = _Surf(nk_pts, nk_rad)

    # ---- head: top of skull lands at 2.62 -------------------------------
    sk_pts = [(0.05, 2.300, 0.455), (0.05, 2.390, 0.545), (0.05, 2.490, 0.575),
              (0.05, 2.575, 0.525), (0.05, 2.612, 0.435)]
    sk_rad = [(0.125, 0.120), (0.172, 0.160), (0.185, 0.168),
              (0.155, 0.135), (0.085, 0.070)]
    skull = _tube(TAG + "skull", sk_pts, sk_rad, sides=10)
    _mat(skull, skin)
    _smooth(skull, 2)
    parts.append(skull)
    skull_surf = _Surf(sk_pts, sk_rad)

    # a long demonic snout, well clear of the skull mass
    mz_pts = [(0.05, 2.470, 0.545), (0.05, 2.440, 0.700),
              (0.05, 2.412, 0.830), (0.05, 2.392, 0.935)]
    muzzle = _tube(TAG + "muzzle", mz_pts,
                   [(0.105, 0.132), (0.082, 0.108), (0.062, 0.084),
                    (0.040, 0.055)], sides=8)
    _mat(muzzle, skin)
    _smooth(muzzle, 2)
    parts.append(muzzle)
    muzzle_surf = _Surf(mz_pts, [(0.105, 0.132), (0.082, 0.108),
                                 (0.062, 0.084), (0.040, 0.055)])
    for sx in (-1, 1):
        nos = _blob(f"{TAG}nostril_{sx}", (0.05 + sx * 0.040, 2.408, 0.905),
                    (0.018, 0.015, 0.022), subdiv=2)
        _mat(nos, mats["mouth"])
        parts.append(nos)

    # the jaw hangs open a crack -- that gap is what makes the fangs read
    jaw = _tube(TAG + "jaw",
                [(0.05, 2.352, 0.490), (0.05, 2.312, 0.650),
                 (0.05, 2.292, 0.790), (0.05, 2.286, 0.890)],
                [(0.068, 0.124), (0.058, 0.108), (0.044, 0.082),
                 (0.030, 0.056)], sides=8)
    _mat(jaw, skin)
    _smooth(jaw, 2)
    parts.append(jaw)
    # a thin dark mouth line tilted UP on his left: the bored half-smile
    maw_slit = add_box(TAG + "maw_slit", (0.235, 0.030, 0.165), (0.055, 2.344, 0.800),
                       rotation=(0.22, 0.0, 0.17), bevel_width=0.006)
    _mat(maw_slit, mats["mouth"])
    parts.append(maw_slit)
    for sx in (-1, 1):
        cheek = _tube(f"{TAG}cheek_{sx}",
                      [(0.05 + sx * 0.120, 2.455, 0.560),
                       (0.05 + sx * 0.140, 2.405, 0.680),
                       (0.05 + sx * 0.120, 2.370, 0.780)],
                      [0.055, 0.044, 0.028], sides=6)
        _mat(cheek, skin)
        _smooth(cheek, 2)
        parts.append(cheek)

    for side, sx in (("l", 1.0), ("r", -1.0)):
        brow = add_box(TAG + "brow_" + side, (0.185, 0.058, 0.125),
                       (0.05 + sx * 0.112, 2.552, 0.700),
                       rotation=(0.24, 0.0, sx * -0.36), bevel_width=0.014, bevel_segments=2)
        _mat(brow, skin)
        parts.append(brow)
        socket = add_box(TAG + "socket_" + side, (0.175, 0.090, 0.050),
                         (0.05 + sx * 0.108, 2.487, 0.718),
                         rotation=(0.1, 0.0, sx * -0.32), bevel_width=0.008)
        _mat(socket, mats["mouth"])
        parts.append(socket)
        eye = _blob(TAG + "eye_" + side, (0.05 + sx * 0.106, 2.490, 0.730),
                    (0.074, 0.040, 0.046), rot=(0.0, 0.0, sx * -0.32), subdiv=3)
        _mat(eye, mats["eye"])
        glow.append(eye)

    # ---- bored half-smile: the mouth lifts on his LEFT (+X) only --------
    maw = add_box(TAG + "maw", (0.25, 0.026, 0.045), (0.055, 2.352, 0.790),
                  rotation=(0.0, 0.0, 0.18), bevel_width=0.005)
    _mat(maw, mats["mouth"])
    parts.append(maw)
    curl = add_box(TAG + "maw_curl", (0.095, 0.023, 0.038), (0.173, 2.385, 0.748),
                   rotation=(0.0, -0.45, 0.55), bevel_width=0.005)
    _mat(curl, mats["mouth"])
    parts.append(curl)

    # Tusk-like teeth.  The two big outer tusks stand clear of the lip and
    # are what make the mouth read at distance; the inner fangs fill it in.
    # Everything is lifted on his LEFT (+X) by the half-smile's tilt.
    for i, (lx, lz, ln, rr) in enumerate([(-0.112, 0.690, 0.105, 0.028),
                                          (-0.052, 0.770, 0.062, 0.019),
                                          (0.014, 0.812, 0.070, 0.020),
                                          (0.082, 0.800, 0.090, 0.022),
                                          (0.142, 0.740, 0.130, 0.030),
                                          (0.186, 0.660, 0.082, 0.021)]):
        x, y = 0.055 + lx, 2.302 + lx * 0.195
        t = _tube(f"{TAG}tooth_lo_{i}",
                  [(x, y - 0.015, lz), (x + lx * 0.10, y + ln * 0.55, lz + 0.004),
                   (x + lx * 0.18, y + ln, lz + 0.006)],
                  [rr, rr * 0.66, 0.002], sides=6)
        _mat(t, mats["bone"])
        _smooth(t, 1)
        parts.append(t)
    for i, (lx, lz, ln, rr) in enumerate([(-0.078, 0.745, 0.062, 0.021),
                                          (0.016, 0.812, 0.056, 0.018),
                                          (0.108, 0.775, 0.074, 0.023)]):
        x, y = 0.055 + lx, 2.396 + lx * 0.195
        t = _tube(f"{TAG}tooth_up_{i}",
                  [(x, y + 0.012, lz), (x, y - ln * 0.55, lz + 0.002),
                   (x, y - ln, lz + 0.004)],
                  [rr, rr * 0.62, 0.002], sides=6)
        _mat(t, mats["bone"])
        _smooth(t, 1)
        parts.append(t)

    # ---- the two long swept-back horns ----------------------------------
    # Base thick at the temple, tapering to a tip ~3.00 high and ~0.85 m
    # behind the skull: the primary silhouette element, read against sky.
    horn_surfs = []
    for side, sx, st in (("l", 1.0, 1.0), ("r", -1.0, 0.95)):
        pts = [
            (0.05 + sx * 0.150, 2.520, 0.420),
            (0.05 + sx * 0.215, 2.605, 0.245),
            (0.05 + sx * 0.265, 2.712, 0.040),
            (0.05 + sx * 0.300, 2.822, -0.165 * st),
            (0.05 + sx * 0.322, 2.915, -0.345 * st),
            (0.05 + sx * 0.335, 2.975, -0.510 * st),
            (0.05 + sx * 0.340, 3.000, -0.655 * st),
        ]
        rad = [0.128, 0.114, 0.096, 0.076, 0.054, 0.031, 0.008]
        horn = _tube(TAG + "horn_" + side, pts, rad, sides=8)
        _mat(horn, mats["horn"])
        _smooth(horn, 2)
        parts.append(horn)
        horn_surfs.append(_Surf(pts, rad))

    return torso_surf, horn_surfs, [skull_surf, muzzle_surf, neck_surf]


# ===================================================================== arms ===

def _arm_chain(sh, elb, wri, r_sh, r_elb, r_wri, bulge):
    """One continuous polyline shoulder -> elbow -> wrist, with points
    bracketing the elbow so subdivision keeps the joint instead of melting
    it, plus a biceps / forearm bulge."""
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
           (r_sh[0] * 0.84, r_sh[1] * 0.84),
           (r_elb[0] * 1.06, r_elb[1] * 1.04),
           r_elb,
           (r_elb[0] * 1.05, r_elb[1] * 1.03),
           (r_elb[0] * 0.96, r_elb[1] * 0.94),
           (r_wri[0] * 1.12, r_wri[1] * 1.10),
           r_wri]
    return pts, rad


def _build_arms(parts, mats, rng):
    skin = mats["skin"]
    surfs = {}

    for side, sh, elb, wri, bulge in (
            ("l", L_SH, L_ELB, L_WRI, Vector((0.050, 0.0, 0.040))),
            ("r", R_SH, R_ELB, R_WRI, Vector((-0.050, 0.0, 0.040)))):
        rsh = (0.190, 0.200) if side == "l" else (0.180, 0.190)
        pts, rad = _arm_chain(sh, elb, wri, rsh, (0.124, 0.132), (0.082, 0.089), bulge)
        arm = _tube(TAG + "arm_" + side, pts, rad, sides=10)
        _mat(arm, skin)
        _smooth(arm, 2)
        parts.append(arm)
        surfs[side] = _Surf(pts, rad)

        inward = -0.15 if side == "l" else 0.15
        tie = _tube(TAG + "delt_" + side,
                    [sh + Vector((inward, 0.05, -0.05)),
                     sh + Vector((0.0, 0.025, 0.0)),
                     sh + Vector((-inward * 0.7, -0.09, 0.02))],
                    [(0.140, 0.122), (0.182, 0.172), (0.158, 0.150)], sides=8)
        _mat(tie, skin)
        _smooth(tie, 2)
        parts.append(tie)

    # ---- LEFT hand: fist closed around the haft -------------------------
    d, o, n = AXE_D, AXE_O, AXE_N
    gp = L_WRI
    palm = _tube(TAG + "hand_l", [gp - d * 0.095 - n * 0.015, gp, gp + d * 0.095 - n * 0.01],
                 [(0.072, 0.076), (0.098, 0.106), (0.072, 0.078)], sides=8)
    _mat(palm, skin)
    _smooth(palm, 2)
    parts.append(palm)
    for i in range(4):
        base = gp + d * (-0.072 + i * 0.050) - n * 0.072
        f = _tube(f"{TAG}fing_l_{i}",
                  [base, base + n * 0.078 + o * 0.078, base + n * 0.158 + o * 0.024],
                  [0.032, 0.027, 0.018], sides=6)
        _mat(f, skin)
        _smooth(f, 2)
        parts.append(f)
    thumb = _tube(TAG + "thumb_l",
                  [gp + d * 0.072 + n * 0.052, gp + d * 0.028 + n * 0.118,
                   gp - d * 0.028 + n * 0.136],
                  [0.036, 0.029, 0.018], sides=6)
    _mat(thumb, skin)
    _smooth(thumb, 2)
    parts.append(thumb)

    # ---- RIGHT hand: open, palm UP, lazy beckon -------------------------
    # Held out away from the body at waist height so it reads in profile.
    pc = Vector((-0.880, 1.408, 0.815))
    palm_r = _tube(TAG + "hand_r",
                   [pc - Vector((0.010, 0.0, 0.120)), pc - Vector((0.0, 0.006, 0.015)),
                    pc + Vector((0.014, 0.000, 0.098))],
                   [(0.090, 0.044), (0.150, 0.042), (0.158, 0.038)], sides=10,
                   ref=(0.0, 1.0, 0.0))
    _mat(palm_r, skin)
    _smooth(palm_r, 2)
    parts.append(palm_r)
    heel = _blob(TAG + "palmheel_r", tuple(pc - Vector((0.010, 0.018, 0.100))),
                 (0.124, 0.054, 0.086), subdiv=2)
    _mat(heel, skin)
    _smooth(heel, 1)
    parts.append(heel)

    for i in range(4):
        fx = -0.120 + i * 0.080
        spread = 0.064 * (i - 1.5) / 1.5
        b = pc + Vector((fx, 0.004, 0.100))
        m = b + Vector((spread * 0.8, 0.036, 0.138))
        t = m + Vector((spread * 1.0, 0.105, 0.078))
        f = _tube(f"{TAG}fing_r_{i}", [b, m, t],
                  [0.040 - 0.003 * abs(i - 1.5), 0.034, 0.021], sides=6)
        _mat(f, skin)
        _smooth(f, 2)
        parts.append(f)
        cl = _tube(f"{TAG}fclaw_r_{i}", [t, t + Vector((spread * 0.3, 0.056, 0.018))],
                   [0.017, 0.002], sides=6)
        _mat(cl, mats["horn"])
        _smooth(cl, 1)
        parts.append(cl)
    th = _tube(TAG + "thumb_r",
               [pc + Vector((0.126, -0.006, -0.044)), pc + Vector((0.222, 0.030, 0.034)),
                pc + Vector((0.268, 0.090, 0.096))],
               [0.045, 0.035, 0.021], sides=6)
    _mat(th, skin)
    _smooth(th, 2)
    parts.append(th)
    thc = _tube(TAG + "thumbclaw_r",
                [pc + Vector((0.268, 0.090, 0.096)), pc + Vector((0.294, 0.132, 0.118))],
                [0.018, 0.002], sides=6)
    _mat(thc, mats["horn"])
    _smooth(thc, 1)
    parts.append(thc)

    return surfs


# ===================================================================== legs ===
# Floor -> hip 1.45.  Knee ~0.95, digitigrade heel ~0.44, toes on the floor.

LEGS = {
    "l": ([(0.235, 1.470, 0.070), (0.265, 1.220, 0.160), (0.300, 0.970, 0.260),
           (0.310, 0.880, 0.250), (0.305, 0.740, 0.160), (0.295, 0.560, 0.020),
           (0.290, 0.440, -0.020), (0.293, 0.300, 0.060), (0.298, 0.180, 0.180),
           (0.302, 0.112, 0.280)],
          [(0.225, 0.238), (0.215, 0.224), (0.165, 0.172), (0.155, 0.160),
           (0.142, 0.148), (0.118, 0.124), (0.100, 0.108), (0.096, 0.106),
           (0.100, 0.115), (0.108, 0.122)],
          (0.302, 0.280, 1.0)),
    "r": ([(-0.245, 1.450, -0.010), (-0.300, 1.200, -0.010), (-0.355, 0.950, 0.000),
           (-0.368, 0.860, -0.030), (-0.372, 0.720, -0.120), (-0.378, 0.550, -0.270),
           (-0.382, 0.430, -0.370), (-0.378, 0.300, -0.310), (-0.372, 0.180, -0.200),
           (-0.368, 0.112, -0.110)],
          [(0.225, 0.238), (0.215, 0.224), (0.165, 0.172), (0.155, 0.160),
           (0.142, 0.148), (0.118, 0.124), (0.100, 0.108), (0.096, 0.106),
           (0.100, 0.115), (0.108, 0.122)],
          (-0.368, -0.110, -1.0)),
}


def _build_legs(parts, mats, rng):
    skin = mats["skin"]
    surfs = {}

    for side, (pts, rad, (fx, fz, zd)) in LEGS.items():
        leg = _tube(TAG + "leg_" + side, pts, rad, sides=10)
        _mat(leg, skin)
        _smooth(leg, 2)
        parts.append(leg)
        surfs[side] = _Surf(pts, rad)

        foot = _tube(TAG + "foot_" + side,
                     [(fx, 0.110, fz), (fx, 0.088, fz + zd * 0.12),
                      (fx, 0.070, fz + zd * 0.22)],
                     [(0.108, 0.122), (0.086, 0.130), (0.064, 0.116)], sides=8)
        _mat(foot, skin)
        _smooth(foot, 2)
        parts.append(foot)

        for i, ox in enumerate((-0.098, 0.0, 0.098)):
            cl = _tube(f"{TAG}claw_{side}_{i}",
                       [(fx + ox, 0.074, fz + zd * 0.20),
                        (fx + ox * 1.25, 0.054, fz + zd * 0.33),
                        (fx + ox * 1.45, 0.022, fz + zd * 0.45)],
                       [0.050, 0.034, 0.004], sides=6)
            _mat(cl, mats["horn"])
            _smooth(cl, 2)
            parts.append(cl)
        sp = _tube(f"{TAG}spur_{side}",
                   [(fx, 0.150, fz - zd * 0.04), (fx, 0.098, fz - zd * 0.17),
                    (fx, 0.044, fz - zd * 0.28)],
                   [0.046, 0.029, 0.004], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 2)
        parts.append(sp)

    return surfs


# ================================================================== armour ===

def _build_armor(parts, glow, mats, rng, torso, arms, legs):
    """Woven black obsidian plate with teal filigree, ONE big spiked left
    pauldron, and a belt with a metal skull clasp.  Every plate is a _shell
    lofted off the body's own parametric surface, so it curves with the form
    and sits 1.5-3 cm proud of the hide.  On the torso a = 0 is dead centre
    front, a = +pi/2 is his left.  Small spikes are deliberately scarce: a
    few large ones read as menace, dozens read as noise."""
    A, AH, F = mats["armor"], mats["armor_hi"], mats["filigree"]

    def shell(name, surf, t0, t1, a0, a1, m=None, **kw):
        o = _shell(TAG + name, surf, t0, t1, a0, a1, **kw)
        _mat(o, m if m else A)
        parts.append(o)
        return o

    def fil(name, surf, ta, gap, w=0.011):
        _band(glow, TAG + name, surf, ta, w, 0.008, gap, F)

    # ---- cuirass ---------------------------------------------------------
    shell("cuir_sternum", torso, 0.545, 0.875, -0.34, 0.34,
          gap0=0.014, gap1=0.020, thick=0.034, nt=7, na=7, m=AH)
    shell("cuir_pec_l", torso, 0.570, 0.865, 0.37, 1.02,
          gap0=0.012, gap1=0.018, thick=0.032, nt=6, na=6)
    shell("cuir_pec_r", torso, 0.540, 0.840, -1.02, -0.37,
          gap0=0.012, gap1=0.018, thick=0.032, nt=6, na=6)
    # NOTHING on the flanks, the back, the collarbone or the belly: bare
    # glossy obsidian hide, so the cracks have skin to run across.

    # ---- "woven" obsidian straps crossing the midriff -------------------
    for i in range(2):
        off = -0.10 + i * 0.20
        _band(parts, f"{TAG}weave_a{i}", torso,
              [(0.16 + k * 0.055, -0.80 + off + k * 0.40) for k in range(5)],
              0.052, 0.016, 0.008, A)
        _band(parts, f"{TAG}weave_b{i}", torso,
              [(0.16 + k * 0.055, 0.80 + off - k * 0.40) for k in range(5)],
              0.048, 0.014, 0.018, AH)

    # ---- filigree tracery ------------------------------------------------
    # one spine line down the sternum plus two sweeping arcs -- a crest,
    # not a grid of tally marks.
    fil("fil_spine", torso, [(0.56 + k * 0.075, 0.02) for k in range(5)], gap=0.050)
    for sgn in (1, -1):
        fil(f"fil_arc{sgn}", torso,
            [(0.86 - k * 0.055, sgn * (0.06 + 0.075 * k)) for k in range(5)],
            gap=0.050, w=0.009)
    for i in range(2):
        fil(f"fil_back{i}", torso, [(0.61 + k * 0.075, 2.85 + i * 0.55) for k in range(5)],
            gap=0.048, w=0.009)

    # ---- low collar across the back of the shoulders --------------------
    c0, c1 = Vector((0.04, 2.16, 0.06)), Vector((0.04, 2.40, -0.14))
    nr, nc = 3, 11
    bmc = bmesh.new()
    rows_i, rows_o = [], []
    for ri in range(nr + 1):
        f = ri / nr
        c = c0.lerp(c1, f)
        rad = 0.255 + 0.105 * f
        ii, oo = [], []
        for ci in range(nc + 1):
            a = 2.20 + (4.30 - 2.20) * (ci / nc)
            dv = Vector((math.sin(a), 0.0, math.cos(a)))
            ii.append(bmc.verts.new(c + dv * rad))
            oo.append(bmc.verts.new(c + dv * (rad + 0.045)))
        rows_i.append(ii)
        rows_o.append(oo)
    for ri in range(nr):
        for ci in range(nc):
            bmc.faces.new([rows_o[ri][ci], rows_o[ri][ci + 1],
                           rows_o[ri + 1][ci + 1], rows_o[ri + 1][ci]])
            bmc.faces.new([rows_i[ri][ci], rows_i[ri + 1][ci],
                           rows_i[ri + 1][ci + 1], rows_i[ri][ci + 1]])
        bmc.faces.new([rows_o[ri][0], rows_o[ri + 1][0], rows_i[ri + 1][0], rows_i[ri][0]])
        bmc.faces.new([rows_o[ri][nc], rows_i[ri][nc], rows_i[ri + 1][nc], rows_o[ri + 1][nc]])
    for ci in range(nc):
        bmc.faces.new([rows_o[0][ci], rows_i[0][ci], rows_i[0][ci + 1], rows_o[0][ci + 1]])
        bmc.faces.new([rows_o[nr][ci], rows_o[nr][ci + 1], rows_i[nr][ci + 1], rows_i[nr][ci]])
    bmesh.ops.recalc_face_normals(bmc, faces=bmc.faces[:])
    collar = _link(TAG + "collar", bmc)
    _mat(collar, AH)
    bvc = collar.modifiers.new("Bevel", "BEVEL")
    bvc.width = 0.007
    bvc.segments = 2
    parts.append(collar)

    # ---- the spiked LEFT pauldron: four big spikes, nothing else --------
    la = arms["l"]
    shell("paul_l0", la, 0.000, 0.145, -math.pi, math.pi,
          gap0=0.034, gap1=0.046, thick=0.042, nt=3, na=14, m=AH, bevel=0.010)
    shell("paul_l1", la, 0.115, 0.270, -2.70, 0.70,
          gap0=0.056, gap1=0.068, thick=0.042, nt=4, na=10, bevel=0.012)
    shell("paul_l2", la, 0.245, 0.395, -2.50, 0.55,
          gap0=0.072, gap1=0.080, thick=0.040, nt=4, na=10, m=AH, bevel=0.012)
    for i, (t, a, ln, lift) in enumerate([(0.04, -2.30, 0.44, 0.55),
                                          (0.07, -1.75, 0.52, 0.42),
                                          (0.11, -1.20, 0.46, 0.26),
                                          (0.24, -1.90, 0.34, 0.45)]):
        base, n = la.at(t, a, gap=0.056)
        d = (n + Vector((0.0, lift, 0.0))).normalized()
        sp = _tube(f"{TAG}paulspike_{i}",
                   [base, base + d * ln * 0.40, base + d * ln * 0.74, base + d * ln],
                   [0.072, 0.049, 0.027, 0.004], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 2)
        parts.append(sp)
    for i in range(3):
        fil(f"fil_paul{i}", la, [(0.02 + k * 0.09, -2.3 + i * 0.85)
                                 for k in range(4)], gap=0.100, w=0.012)

    # ---- plain strapped RIGHT shoulder plate (asymmetry) ----------------
    ra = arms["r"]
    shell("paul_r0", ra, 0.000, 0.135, -math.pi, math.pi,
          gap0=0.024, gap1=0.032, thick=0.036, nt=3, na=12)
    shell("paul_r1", ra, 0.105, 0.240, 0.45, 3.30,
          gap0=0.042, gap1=0.050, thick=0.036, nt=4, na=9, m=AH)

    # ---- short bracers only; upper arms and most of the forearms bare ---
    for side in ("l", "r"):
        s = arms[side]
        shell(f"bracer_{side}", s, 0.760, 0.920, -math.pi, math.pi,
              gap0=0.020, gap1=0.016, thick=0.032, nt=3, na=12)
        fil(f"fil_brac_{side}", s,
            [(0.78 + k * 0.045, -0.8) for k in range(4)], gap=0.054, w=0.010)

    # The legs wear NO plate at all -- bare demon hide from hip to claw,
    # which is where most of the crack network lives.

    # ---- belt + metal skull clasp ---------------------------------------
    belt = _tube(TAG + "belt",
                 [(0.0, 1.400, -0.025), (0.0, 1.465, 0.000), (0.0, 1.530, 0.010)],
                 [(0.190, 0.262), (0.208, 0.288), (0.192, 0.268)], sides=14)
    _mat(belt, A)
    belt.modifiers.new("Bevel", "BEVEL").width = 0.008
    parts.append(belt)
    for i in range(7):
        a = -1.25 + i * 0.42
        o = add_box(f"{TAG}beltstud{i}", (0.062, 0.066, 0.042),
                    (math.sin(a) * 0.288, 1.468, math.cos(a) * 0.214 + 0.000),
                    rotation=(0.0, -a, 0.0), bevel_width=0.006, bevel_segments=2)
        _mat(o, AH)
        parts.append(o)

    sk = Vector((0.02, 1.468, 0.232))
    cr = _blob(TAG + "skull_cranium", tuple(sk + Vector((0, 0.030, -0.010))),
               (0.122, 0.114, 0.094), subdiv=2)
    _mat(cr, mats["steel"])
    _smooth(cr, 1)
    parts.append(cr)
    jw = _blob(TAG + "skull_jaw", tuple(sk + Vector((0, -0.052, 0.015))),
               (0.096, 0.058, 0.080), subdiv=2)
    _mat(jw, mats["steel"])
    _smooth(jw, 1)
    parts.append(jw)
    for sx in (-1, 1):
        soc = _blob(f"{TAG}skull_socket_{sx}", tuple(sk + Vector((sx * 0.042, 0.035, 0.060))),
                    (0.029, 0.025, 0.018), subdiv=2)
        _mat(soc, mats["crack_dim"])
        glow.append(soc)
        base = sk + Vector((sx * 0.080, 0.055, 0.006))
        hs = _tube(f"{TAG}skull_horn_{sx}",
                   [base, base + Vector((sx * 0.050, 0.054, -0.028)),
                    base + Vector((sx * 0.075, 0.096, -0.065))],
                   [0.025, 0.015, 0.003], sides=6)
        _mat(hs, mats["steel"])
        _smooth(hs, 1)
        parts.append(hs)

    # ---- tassets hanging off the belt -----------------------------------
    for i, (a, ln) in enumerate([(-1.05, 0.30), (-0.62, 0.40), (-0.20, 0.44),
                                 (0.22, 0.42), (0.64, 0.34)]):
        bx = math.sin(a) * 0.292
        bz = math.cos(a) * 0.222
        o = add_box(f"{TAG}tasset{i}", (0.20, ln, 0.055),
                    (bx * 1.05, 1.392 - ln * 0.5, bz * 1.05),
                    rotation=(0.14, -a, 0.03), bevel_width=0.009, bevel_segments=2)
        _mat(o, AH if i % 2 else A)
        parts.append(o)


# ==================================================================== cape ===

def _build_cape(mats, rng):
    """Torn, smouldering black cape: a shoulder-anchored grid swept back by
    wind, with whole columns cut short so the hem tears into strips and real
    gaps open between them.  Returns (object, torn-edge points for embers)."""
    nu, nv = 30, 22
    y_top = 2.30
    R = 0.40
    a0, a1 = math.radians(74.0), math.radians(286.0)
    Lmax = 2.30

    lengths = []
    for i in range(nu + 1):
        u = i / nu
        base = 0.72 + 0.15 * math.sin(u * 7.3 + 1.1) + 0.11 * math.sin(u * 15.1)
        roll = rng.random()
        if roll < 0.30:
            base *= rng.uniform(0.30, 0.55)                   # deep tear
        elif roll < 0.46:
            base = min(1.0, base * rng.uniform(1.18, 1.38))   # long tongue
        lengths.append(max(0.16, min(1.0, base)))

    def vert(i, j):
        u = i / nu
        a = a0 + (a1 - a0) * u
        v = j / nv
        rx, rz = math.sin(a), math.cos(a)
        fold = 0.125 * math.sin(u * math.pi * 9.0) * (v ** 0.6)
        rad = R * (1.0 + 0.72 * v) + fold
        y = y_top - v * Lmax * 0.94
        x = rx * rad + 0.22 * v * v
        z = rz * rad - 0.72 * v ** 1.7
        y += 0.08 * math.sin(a * 2.7 + 0.8) * v
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
    sol.thickness = 0.014
    sol.offset = 0.0
    return cape, edge_pts


# ===================================================================== axe ===

def _build_axe(parts, glow, ichor, mats, rng):
    """A huge two-handed axe: a 2.2 m haft lying diagonally across the back
    with the head resting above the forward left shoulder.  The head is a
    bearded crescent ~0.80 m across with a bright honed bit, so the
    silhouette reads unmistakably as an axe."""
    d, o, n, T, B = AXE_D, AXE_O, AXE_N, AXE_T, AXE_B

    haft = _tube(TAG + "axe_haft",
                 [B, B.lerp(T, 0.28), B.lerp(T, 0.58), B.lerp(T, 0.84), T, T + d * 0.22],
                 [0.044, 0.052, 0.057, 0.057, 0.054, 0.046], sides=10)
    _mat(haft, mats["axe"])
    haft.modifiers.new("Bevel", "BEVEL").width = 0.005
    for poly in haft.data.polygons:
        poly.use_smooth = True
    parts.append(haft)
    cap = _tube(TAG + "axe_buttcap", [B - d * 0.05, B + d * 0.06], [0.064, 0.070], sides=10)
    _mat(cap, mats["steel"])
    parts.append(cap)
    for i in range(5):
        p = L_WRI + d * (-0.22 + i * 0.11)
        bind = _tube(f"{TAG}axe_bind{i}", [p - d * 0.022, p + d * 0.022], [0.064, 0.064], sides=10)
        _mat(bind, mats["axe"])
        parts.append(bind)

    # ---- bearded blade: (s along the haft, t outward from it) -----------
    outline = [(0.32, 0.00), (0.34, 0.16), (0.30, 0.38), (0.19, 0.56),
               (-0.02, 0.66), (-0.28, 0.67), (-0.50, 0.55), (-0.62, 0.33),
               (-0.54, 0.12), (-0.36, 0.00)]
    th0, tmax = 0.070, 0.67
    bm = bmesh.new()
    front, back = [], []
    for (sp, tp) in outline:
        th = th0 * max(0.05, 1.0 - (tp / tmax) * 0.95)
        p = T + d * sp + o * tp
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
    bv.width = 0.011
    bv.segments = 2
    parts.append(blade)

    # the honed bit: a bright steel welt that draws the cutting arc
    arc = [(0.19, 0.56), (0.09, 0.625), (-0.02, 0.66), (-0.15, 0.672),
           (-0.28, 0.67), (-0.40, 0.625), (-0.50, 0.55), (-0.57, 0.45)]
    for i in range(len(arc) - 1):
        p0 = T + d * arc[i][0] + o * arc[i][1]
        p1 = T + d * arc[i + 1][0] + o * arc[i + 1][1]
        e = _strip(f"{TAG}axe_welt{i}", p0, p1, o, 0.034, 0.022)
        _mat(e, mats["axe_edge"])
        parts.append(e)

    bspike = _tube(TAG + "axe_backspike",
                   [T - o * 0.02, T - o * 0.24 + d * 0.06, T - o * 0.42 + d * 0.12],
                   [(0.150, 0.054), (0.100, 0.036), (0.010, 0.008)], sides=6)
    _mat(bspike, mats["axe"])
    parts.append(bspike)
    for i, sp in enumerate((-0.36, 0.28)):
        col = _tube(f"{TAG}axe_collar{i}", [T + d * sp - o * 0.05, T + d * sp + o * 0.12],
                    [0.082, 0.070], sides=8)
        _mat(col, mats["steel"])
        col.modifiers.new("Bevel", "BEVEL").width = 0.005
        parts.append(col)
    fin = _tube(TAG + "axe_finial", [T + d * 0.22, T + d * 0.29, T + d * 0.36],
                [0.048, 0.029, 0.004], sides=6)
    _mat(fin, mats["horn"])
    _smooth(fin, 1)
    parts.append(fin)

    for i in range(4):
        sp = -0.30 + i * 0.19
        f = _strip(f"{TAG}axe_fil{i}", T + d * sp + o * 0.07 + n * (th0 * 0.92),
                   T + d * (sp * 0.5) + o * 0.42 + n * (th0 * 0.28), n, 0.016, 0.009)
        _mat(f, mats["filigree"])
        glow.append(f)
    for sgn in (1, -1):
        f = _strip(f"{TAG}axe_filspine{sgn}",
                   T + d * (-0.32) + o * 0.10 + n * sgn * (th0 * 0.88),
                   T + d * 0.30 + o * 0.10 + n * sgn * (th0 * 0.88), n * sgn, 0.020, 0.009)
        _mat(f, mats["filigree"])
        glow.append(f)

    # ---- ichor: runnels down the blade face, then drops falling free ----
    for i, (s0, t0) in enumerate([(0.14, 0.12), (-0.06, 0.16), (-0.30, 0.14),
                                  (-0.44, 0.10)]):
        pts = [T + d * s0 + o * t0 + n * (th0 * 0.80)]
        for k in range(1, 4):
            pts.append(T + d * (s0 - 0.05 * k) + o * (t0 + 0.145 * k)
                       + n * (th0 * (0.80 - 0.18 * k)))
        run = _tube(f"{TAG}axe_runnel{i}", pts,
                    [0.018, 0.026, 0.021, 0.012], sides=6)
        _mat(run, mats["ichor"])
        _smooth(run, 2)
        ichor.append(run)

    for i, (sp, tp) in enumerate([(0.12, 0.60), (-0.04, 0.66), (-0.28, 0.67),
                                  (-0.46, 0.57), (-0.58, 0.40)]):
        base = T + d * sp + o * tp
        ln = rng.uniform(0.26, 0.52)
        dr = _tube(f"{TAG}axe_drip{i}",
                   [base, base + Vector((0.0, -ln * 0.32, 0.006)),
                    base + Vector((0.008, -ln * 0.70, 0.010)),
                    base + Vector((0.008, -ln, 0.008))],
                   [0.028, 0.044, 0.030, 0.004], sides=6)
        _mat(dr, mats["ichor"])
        _smooth(dr, 2)
        ichor.append(dr)
        # free-falling drops on their way to the crystal floor
        for k, fall in enumerate((0.36, 0.78)):
            if (i + k) % 2:
                continue
            dp = _blob(f"{TAG}axe_droplet{i}_{k}",
                       tuple(base + Vector((0.010, -ln - fall, 0.012))),
                       (0.024, 0.040, 0.024), subdiv=2)
            _mat(dp, mats["ichor"])
            _smooth(dp, 1)
            ichor.append(dp)
    for i in range(0, len(arc) - 1, 2):
        p0 = T + d * arc[i][0] + o * arc[i][1]
        p1 = T + d * arc[i + 1][0] + o * arc[i + 1][1]
        sm = _strip(f"{TAG}axe_edgeichor{i}", p0, p1, n, 0.050, 0.026)
        _mat(sm, mats["ichor"])
        ichor.append(sm)


# ========================================================= ichor / embers ===

def _build_ichor_splashes(ichor, mats, rng, torso, horn_surfs):
    """Flat, wet, irregular ichor splashes conforming to the chest and horns
    -- thrown off the axe resting on the shoulder."""
    for i in range(7):
        _splash(ichor, f"{TAG}ichor_chest{i}", torso,
                rng.uniform(0.52, 0.95), rng.uniform(-0.85, 0.95),
                rng.uniform(0.030, 0.065), rng.uniform(0.14, 0.34), mats, rng,
                drip=0.09 if i % 3 == 0 else 0.0)
    for hi, surf in enumerate(horn_surfs):
        for i in range(2):
            _splash(ichor, f"{TAG}ichor_horn{hi}_{i}", surf,
                    rng.uniform(0.06, 0.45), rng.uniform(0.0, 6.28),
                    rng.uniform(0.035, 0.070), rng.uniform(0.5, 1.1), mats, rng)
        p, _ = surf.at(rng.uniform(0.18, 0.38), -math.pi / 2)
        dr = _tube(f"{TAG}ichor_horndrip{hi}",
                   [p, p + Vector((0, -0.09, 0)), p + Vector((0, -0.17, 0.005))],
                   [0.020, 0.025, 0.003], sides=6)
        _mat(dr, mats["ichor"])
        _smooth(dr, 1)
        ichor.append(dr)


def _build_wisps(glow, mats, rng, edge_pts):
    """The geometry half of the evil aura: a few big torn ribbons of dark
    teal vapour peeling off the shoulders, the horns and the burning hem of
    the cape.  Deliberately few and large so they read at distance."""
    seeds = [
        (Vector((0.44, 2.50, 0.14)), Vector((0.30, 1.0, -0.95)), 0.78, 0.042),
        (Vector((-0.38, 2.32, 0.00)), Vector((-0.26, 1.0, -1.00)), 0.66, 0.036),
        (Vector((0.08, 2.38, -0.22)), Vector((0.04, 1.0, -1.15)), 0.84, 0.045),
    ]
    picks = edge_pts[:]
    rng.shuffle(picks)
    for p in picks[:2]:
        seeds.append((Vector(p) + Vector((0, 0.04, 0)),
                      Vector((rng.uniform(-0.3, 0.3), 1.0, rng.uniform(-0.7, -0.2))),
                      rng.uniform(0.42, 0.68), rng.uniform(0.026, 0.038)))

    for i, (base, up, ln, wd) in enumerate(seeds):
        up = up.normalized()
        side = up.cross(Vector((0.0, 0.0, 1.0)))
        if side.length < 0.2:
            side = up.cross(Vector((1.0, 0.0, 0.0)))
        side.normalize()
        pts, rad = [], []
        for k in range(5):
            f = k / 4.0
            sway = math.sin(f * 3.4 + i) * 0.16 * ln
            pts.append(base + up * (ln * f) + side * sway)
            # flat ribbon: thin through, wide across, tapering to nothing
            rad.append((wd * 0.14 * (1.0 - f * 0.70),
                        wd * (1.0 - f * 0.92) + 0.002))
        w = _tube(f"{TAG}wisp{i}", pts, rad, sides=6)
        _mat(w, mats["wisp"])
        _smooth(w, 2)
        glow.append(w)


def _build_embers(glow, mats, rng, edge_pts):
    """Smouldering embers along the cape's torn hem."""
    picks = edge_pts[:]
    rng.shuffle(picks)
    for i, p in enumerate(picks[:14]):
        s = rng.uniform(0.012, 0.026)
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

    torso_surf, horn_surfs, skin_surfs = _build_body(body, glow, mats, rng)
    arm_surfs = _build_arms(body, mats, rng)
    leg_surfs = _build_legs(body, mats, rng)
    _build_armor(armor, glow, mats, rng, torso_surf, arm_surfs, leg_surfs)
    cape, edge_pts = _build_cape(mats, rng)
    _build_axe(axe, glow, ichor, mats, rng)
    _build_ichor_splashes(ichor, mats, rng, torso_surf, horn_surfs)
    _build_embers(glow, mats, rng, edge_pts)
    _build_wisps(glow, mats, rng, edge_pts)

    # ---- fine glowing cyan cracks ---------------------------------------
    # Few, long and branching rather than a dense net: the obsidian has to
    # read as obsidian between them.
    cracks = []
    _veins(cracks, "torso", torso_surf, rng, mats, 6, nseg=(6, 10), seg_len=0.145,
           width=(0.009, 0.021), t_range=(0.10, 0.95), hot=0.18, branch_p=0.55)
    for side, s in arm_surfs.items():
        _veins(cracks, f"arm{side}", s, rng, mats, 3, nseg=(5, 9), seg_len=0.135,
               width=(0.007, 0.016), t_range=(0.26, 0.95), hot=0.14, branch_p=0.45)
    for side, s in leg_surfs.items():
        _veins(cracks, f"leg{side}", s, rng, mats, 3, nseg=(6, 10), seg_len=0.150,
               width=(0.007, 0.017), t_range=(0.36, 0.95), hot=0.12, branch_p=0.45)
    for i, s in enumerate(horn_surfs):
        _veins(cracks, f"horn{i}", s, rng, mats, 2, nseg=(4, 6), seg_len=0.150,
               width=(0.005, 0.012), t_range=(0.05, 0.60), hot=0.25, branch_p=0.20)
    # cracks on the bare hide of the FACE, snout and neck -- this is what
    # separates a creature with glowing fissures from a machine with lit seams
    skull_s, muzzle_s, neck_s = skin_surfs
    _veins(cracks, "face", skull_s, rng, mats, 5, nseg=(3, 6), seg_len=0.085,
           width=(0.005, 0.013), t_range=(0.15, 0.92), hot=0.34, branch_p=0.45)
    _veins(cracks, "snout", muzzle_s, rng, mats, 3, nseg=(3, 5), seg_len=0.070,
           width=(0.004, 0.011), t_range=(0.10, 0.90), hot=0.30, branch_p=0.35)
    _veins(cracks, "neck", neck_s, rng, mats, 4, nseg=(3, 6), seg_len=0.080,
           width=(0.006, 0.015), t_range=(0.08, 0.92), hot=0.26, branch_p=0.45)

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
