"""char_chaos.py -- the CHAOS LORD / AH PUCH, antagonist of "Evening Breath".

CraftWar's own data.h names DIRE's tier-1 hero "Chaos Lord", so this scene's
antagonist and that hero are one character: Ah Puch, the Maya lord of death.
Palette and design language are taken from the authoritative sources,
/home/user/craftwar/src/gfx/models3d/dire_hero.cpp and the 2D original
drawDireHeroBody() in src/gfx/pixel_anim.cpp -- gaunt starved ribcage, bone
rib bands, a hollow fel-core where the heart should be, a fanged bone
half-skull flush to the shoulders with deep hollow sockets, curved dark-red
horns, and the bone rattle on a cord that is Ah Puch's own iconography.

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
# DIRE hero constants, straight out of dire_hero.cpp, converted to 0..1.

DI_FLESH = (0.102, 0.063, 0.125, 1.0)   # 0x1A1020 fel-dark corrupted flesh
DI_DARK = (0.055, 0.031, 0.063, 1.0)    # 0x0E0810 deep shadow
DI_BONE = (0.847, 0.800, 0.643, 1.0)    # 0xD8CCA4 bone ivory
DI_GLOW = (0.502, 1.000, 0.188, 1.0)    # 0x80FF30 fel-green ember
DI_ACCENT = (0.188, 0.345, 0.345, 1.0)  # 0x305858 teal shoulder trim ONLY
DI_HORN = (0.251, 0.063, 0.063, 1.0)    # 0x401010 dark red horn
DI_HOT = (0.933, 1.000, 0.565, 1.0)     # 0xEEFF90 white-hot flame core
DI_MID = (0.659, 1.000, 0.220, 1.0)     # 0xA8FF38
DI_DIM = (0.118, 0.251, 0.031, 1.0)     # 0x1E4008
DI_CRUPT = (0.314, 0.094, 0.439, 1.0)   # 0x501870 corruption purple
DI_TIP = (0.353, 0.290, 0.314, 1.0)     # 0x5A4A50 horn-tip sheen

ICHOR = (0.027, 0.106, 0.110, 1.0)      # scene palette, now lit fel-green

TAG = "CHAOS_"


# ============================================================== materials ===

def _materials():
    nm = cs.materials.new_principled_material
    M = {}

    # fel-dark corrupted flesh, purple-black, kept glossy so the key light
    # behind still draws a hard specular edge along every starved muscle.
    mat, bsdf = nm(TAG + "flesh", base_color=DI_FLESH, roughness=0.26, metallic=0.10)
    cs.materials.add_noise_bump(mat, bsdf, scale=26.0, detail=6.0, strength=0.11)
    M["skin"] = mat

    M["horn"], _ = nm(TAG + "horn", base_color=DI_HORN, roughness=0.30, metallic=0.15)
    M["horn_tip"], _ = nm(TAG + "horn_tip", base_color=DI_TIP, roughness=0.26, metallic=0.30)
    M["armor"], _ = nm(TAG + "armor", base_color=DI_DARK, roughness=0.30, metallic=0.28)
    M["armor_hi"], _ = nm(TAG + "armor_hi", base_color=(0.086, 0.058, 0.102, 1.0),
                          roughness=0.33, metallic=0.34)
    M["accent"], _ = nm(TAG + "accent_trim", base_color=DI_ACCENT, roughness=0.26,
                        metallic=0.55, emission_color=DI_ACCENT, emission_strength=0.45)
    M["crupt"], _ = nm(TAG + "crack_corruption", base_color=DI_CRUPT, roughness=0.34,
                       metallic=0.20, emission_color=DI_CRUPT, emission_strength=2.2)
    M["crupt_dim"], _ = nm(TAG + "crack_corruption_dim", base_color=(0.150, 0.045, 0.210, 1.0),
                           roughness=0.40, emission_color=DI_CRUPT, emission_strength=1.0)
    M["mid"], _ = nm(TAG + "crack_mid", base_color=(0.240, 0.420, 0.080, 1.0),
                     roughness=0.30, emission_color=DI_MID, emission_strength=4.0)
    M["hot"], _ = nm(TAG + "crack_hotcore", base_color=(0.420, 0.500, 0.200, 1.0),
                     roughness=0.26, emission_color=DI_HOT, emission_strength=8.0)
    M["glow_soft"], _ = nm(TAG + "crack_glow_soft", base_color=(0.120, 0.230, 0.050, 1.0),
                           roughness=0.40, emission_color=DI_GLOW, emission_strength=1.6)
    M["axe"], _ = nm(TAG + "axe_iron", base_color=(0.034, 0.024, 0.042, 1.0),
                     roughness=0.32, metallic=0.42)
    M["axe_edge"], _ = nm(TAG + "axe_edge", base_color=(0.430, 0.408, 0.330, 1.0),
                          roughness=0.32, metallic=0.25)
    M["steel"], _ = nm(TAG + "steel", base_color=(0.210, 0.200, 0.172, 1.0),
                       roughness=0.40, metallic=0.55)
    bmat, bbsdf = nm(TAG + "bone", base_color=DI_BONE, roughness=0.50)
    cs.materials.add_noise_bump(bmat, bbsdf, scale=34.0, detail=5.0, strength=0.10)
    M["bone"] = bmat
    M["bone_dim"], _ = nm(TAG + "bone_dim", base_color=(0.470, 0.440, 0.350, 1.0),
                          roughness=0.52)
    M["cloth"], _ = nm(TAG + "cape_cloth", base_color=(0.026, 0.017, 0.032, 1.0),
                       roughness=0.56)
    M["mouth"], _ = nm(TAG + "maw", base_color=(0.018, 0.010, 0.018, 1.0), roughness=0.55)
    M["socket"], _ = nm(TAG + "socket_void", base_color=(0.012, 0.007, 0.013, 1.0),
                        roughness=0.70)

    # emissives
    # Every fissure is now FEL-GREEN.  Names are kept on the CHAOS_crack* /
    # CHAOS_eye* stems so scene_main's existing emission ceilings still match.
    M["crack"], _ = nm(TAG + "crack", base_color=(0.070, 0.140, 0.030, 1.0),
                       roughness=0.30, emission_color=DI_GLOW, emission_strength=5.0)
    M["crack_hot"], _ = nm(TAG + "crack_hot", base_color=(0.110, 0.180, 0.045, 1.0),
                           roughness=0.28, emission_color=DI_HOT, emission_strength=9.0)
    M["crack_dim"], _ = nm(TAG + "crack_dim", base_color=(0.045, 0.095, 0.022, 1.0),
                           roughness=0.34, emission_color=DI_DIM, emission_strength=2.6)
    M["crack_halo"], _ = nm(TAG + "crack_halo", base_color=(0.050, 0.100, 0.025, 1.0),
                            roughness=0.40, emission_color=DI_GLOW, emission_strength=2.0)
    M["filigree"], _ = nm(TAG + "filigree", base_color=(0.160, 0.300, 0.070, 1.0),
                          roughness=0.28, metallic=0.70,
                          emission_color=DI_MID, emission_strength=1.6)
    M["eye"], _ = nm(TAG + "eye_socket", base_color=(0.300, 0.600, 0.110, 1.0),
                     roughness=0.10, emission_color=DI_GLOW, emission_strength=14.0)
    M["core"], _ = nm(TAG + "eye_felcore", base_color=(0.380, 0.760, 0.140, 1.0),
                      roughness=0.10, emission_color=DI_MID, emission_strength=10.0)
    M["ember"], _ = nm(TAG + "ember", base_color=(0.120, 0.140, 0.040, 1.0),
                       roughness=0.6, emission_color=DI_HOT, emission_strength=3.0)
    # the geometric half of the "evil aura": torn wisps peeling off him.
    # scene_main owns the volumetric half, so nothing here is a light.
    M["wisp"], _ = nm(TAG + "wisp", base_color=(0.030, 0.050, 0.014, 1.0),
                      roughness=0.88,
                      emission_color=DI_DIM, emission_strength=0.45)

    # black-teal ichor: wet and very glossy, barely self-lit so it reads as
    # dark fluid catching a teal highlight, not as glowing paint.
    M["ichor"], _ = nm(TAG + "ichor", base_color=ICHOR, roughness=0.035, metallic=0.20,
                       emission_color=(0.090, 0.190, 0.035, 1.0), emission_strength=0.06)
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


def _annulus(name, radius, band, y, thick=0.014, segs=56):
    """A flat glowing ring lying on the ground -- the aura's ring3d() torii,
    built as a thin annulus rather than a fat donut so it reads as light on
    the floor the way the reference does."""
    r0, r1 = radius - band * 0.5, radius + band * 0.5
    bm = bmesh.new()
    rows = []
    for yy in (y + thick * 0.5, y - thick * 0.5):
        inner, outer = [], []
        for k in range(segs):
            a = 2.0 * math.pi * k / segs
            ca, sa = math.cos(a), math.sin(a)
            inner.append(bm.verts.new((ca * r0, yy, sa * r0)))
            outer.append(bm.verts.new((ca * r1, yy, sa * r1)))
        rows.append((inner, outer))
    (ti, to), (bi, bo) = rows
    for k in range(segs):
        j = (k + 1) % segs
        bm.faces.new([ti[k], to[k], to[j], ti[j]])
        bm.faces.new([bi[k], bi[j], bo[j], bo[k]])
        bm.faces.new([to[k], bo[k], bo[j], to[j]])
        bm.faces.new([ti[k], ti[j], bi[j], bi[k]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _link(name, bm)


def _carve(target, cutters):
    """Bake `target`'s modifiers, then boolean-subtract each cutter and
    delete it.  Used for the skull's eye sockets and nasal cavity: a real
    hole through the bone, so the socket reads as a hollow you can see into
    rather than a dark rectangle painted on a visor."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = target.evaluated_get(dg)
    baked = bpy.data.meshes.new_from_object(ev)
    old = target.data
    target.modifiers.clear()
    target.data = baked
    bpy.data.meshes.remove(old)
    for i, c in enumerate(cutters):
        m = target.modifiers.new(f"Carve{i}", "BOOLEAN")
        m.operation = "DIFFERENCE"
        m.object = c
        m.solver = "EXACT"
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    for i in range(len(cutters)):
        bpy.ops.object.modifier_apply(modifier=f"Carve{i}")
    for c in cutters:
        bpy.data.objects.remove(c, do_unlink=True)
    for poly in target.data.polygons:
        poly.use_smooth = True
    return target


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
# Proportions taken straight off dire_hero.cpp.  That model is 51 world units
# tall to the horn tips and gl3d_draw.h sets U = 3.0 world units per sprite
# unit, so one world unit = 3.00 / 51 = 0.058824 m here.  Everything below is
# that conversion, not a reinterpretation:
#
#   floor -> hip          18 u = 1.059      torso width      12 u = 0.706
#   hip -> shoulder       18 u = 1.059      torso depth       6 u = 0.353
#   skull block            6 u = 0.353      shoulder span    24 u = 1.412
#   horns above skull      9 u = 0.529      rib bands  21/24/27/30 u
#   eye sockets   36.75 - 39 u              jaw slab       34.5 u = 2.029
#   fel core              24 u = 1.412, standing 4 u = 0.235 proud of the chest
#
# Legs are only 35% of his height and the horns 18%: short-legged, long
# ribcage, horn-dominated -- the opposite of a broad warlord.

UU = 3.00 / 51.0          # metres per dire_hero world unit
HIP_Y = 18 * UU           # 1.059
SHOULDER_Y = 36 * UU      # 2.118
SKULL_TOP = 42 * UU       # 2.471
TOR_HW = 6 * UU           # 0.353  half torso width
TOR_HD = 3 * UU           # 0.177  half torso depth
PLATE_X = 12 * UU         # 0.706  outer edge of the shoulder plates

SPINE = [
    ((0.00, HIP_Y, -0.03), (0.130, 0.235)),          # cinched starved waist
    ((0.00, 1.200, 0.02), (0.160, 0.300)),
    ((0.01, 1.400, 0.08), (0.175, 0.345)),
    ((0.02, 1.650, 0.14), (TOR_HD, TOR_HW)),
    ((0.03, 1.900, 0.18), (0.176, 0.350)),
    ((0.03, SHOULDER_Y, 0.19), (0.168, 0.340)),
]

L_SH = Vector((0.430, 2.100, 0.250))    # LEFT shoulder: forward and raised
L_ELB = Vector((0.615, 1.700, 0.110))
L_WRI = Vector((0.611, 1.483, 0.434))   # on the haft, in front of the ribs

R_SH = Vector((-0.420, 2.010, 0.100))   # RIGHT shoulder: dropped and back
R_ELB = Vector((-0.580, 1.610, 0.200))
R_WRI = Vector((-0.700, 1.330, 0.520))  # free arm, open palm-up beckon

AXE_T = Vector((0.520, 2.460, 0.060))                 # head, on the shoulder
AXE_D = Vector((-0.100, 1.070, -0.410)).normalized()  # butt -> head
AXE_B = AXE_T - AXE_D * 2.20
AXE_O = Vector((0.9946, 0.0752, -0.0706)).normalized()
AXE_N = AXE_O.cross(AXE_D).normalized()

RING_Y = 0.4 * UU         # 0.024 -- the aura sits just off the crystal floor


def _splash(out_list, name, surf, t, a, rt, ra, mats, rng, drip=0.0):
    """Flat, wet, irregular ichor CONFORMING to the surface."""
    for k in range(rng.randint(2, 3)):
        tt = t + rng.uniform(-rt, rt) * 0.5
        aa = a + rng.uniform(-ra, ra) * 0.5
        dt = rt * rng.uniform(0.45, 1.0)
        da = ra * rng.uniform(0.45, 1.0)
        o = _shell(f"{name}_{k}", surf, tt - dt, tt + dt, aa - da, aa + da,
                   gap0=0.004, gap1=0.004, thick=0.007, nt=2, na=3, bevel=0.0)
        _mat(o, mats["ichor"])
        out_list.append(o)
    if drip > 0.0:
        pts = [surf.at(t - k * drip * 0.42, a + k * 0.02, gap=0.009)[0] for k in range(3)]
        d = _tube(f"{name}_run", pts, [0.013, 0.010, 0.003], sides=6)
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

    for sx in (-1, 1):
        sc = _tube(f"{TAG}scapula_{sx}",
                   [(sx * 0.070, 2.05, 0.02), (sx * 0.190, 1.96, -0.02),
                    (sx * 0.235, 1.82, 0.01)],
                   [(0.050, 0.044), (0.074, 0.066), (0.052, 0.048)], sides=6)
        _mat(sc, skin)
        _smooth(sc, 2)
        parts.append(sc)

    pelvis = _tube(TAG + "pelvis",
                   [(0.00, 0.930, -0.06), (0.00, 1.020, -0.04), (0.00, 1.120, -0.02)],
                   [(0.118, 0.172), (0.138, 0.205), (0.120, 0.180)], sides=10)
    _mat(pelvis, skin)
    _smooth(pelvis, 2)
    parts.append(pelvis)

    # ---- BONE HALF-SKULL: full torso width, flush, no neck gap ----------
    sk_pts = [(0.03, 2.125, 0.185), (0.03, 2.215, 0.200), (0.03, 2.330, 0.195),
              (0.03, 2.430, 0.170), (0.03, SKULL_TOP, 0.130)]
    sk_rad = [(0.165, 0.330), (0.172, 0.342), (0.170, 0.338),
              (0.142, 0.285), (0.085, 0.175)]
    skull = _tube(TAG + "skull", sk_pts, sk_rad, sides=12)
    _mat(skull, mats["bone"])
    _smooth(skull, 2)
    cutters = []
    for sx in (-1.0, 1.0):
        cutters.append(add_box(TAG + "cut_socket", (0.176, 0.150, 0.34),
                               (0.03 + sx * 0.250, 2.228, 0.330),
                               rotation=(0.06, 0.0, sx * -0.10)))
    cutters.append(add_box(TAG + "cut_nasal", (0.094, 0.110, 0.30),
                           (0.035, 2.185, 0.330), rotation=(0.08, 0.0, 0.0)))
    _carve(skull, cutters)
    parts.append(skull)
    skull_surf = _Surf(sk_pts, sk_rad)

    # brow-ridge rim light -- the one place DI_ACCENT teal touches the bone
    brow = add_box(TAG + "brow_rim", (0.62, 0.022, 0.10), (0.03, 2.455, 0.240),
                   rotation=(0.40, 0.0, 0.0), bevel_width=0.006, bevel_segments=2)
    _mat(brow, mats["accent"])
    parts.append(brow)
    for i, (ty, rr) in enumerate([(2.160, (0.168, 0.334)), (2.300, (0.172, 0.340))]):
        band = _tube(f"{TAG}skullband{i}",
                     [(0.03, ty - 0.010, 0.190), (0.03, ty + 0.010, 0.192)],
                     [rr, rr], sides=12)
        _mat(band, mats["bone_dim"])
        parts.append(band)

    # hollow sockets: a dark wall set deep inside the carved hole, with the
    # ember burning at the BOTTOM of it -- light looking up from inside.
    for side, sx in (("l", 1.0), ("r", -1.0)):
        fill = add_box(TAG + "socketvoid_" + side, (0.168, 0.144, 0.26),
                       (0.03 + sx * 0.250, 2.228, 0.165),
                       rotation=(0.06, 0.0, sx * -0.10))
        _mat(fill, mats["socket"])
        parts.append(fill)
        ember = _blob(TAG + "eye_" + side, (0.03 + sx * 0.248, 2.176, 0.300),
                      (0.060, 0.026, 0.028), subdiv=3)
        _mat(ember, mats["eye"])
        glow.append(ember)
        spill = _blob(TAG + "eye_spill_" + side, (0.03 + sx * 0.248, 2.190, 0.252),
                      (0.068, 0.050, 0.034), subdiv=2)
        _mat(spill, mats["crack_dim"])
        glow.append(spill)
    nasalfill = add_box(TAG + "nasalvoid", (0.088, 0.104, 0.24),
                        (0.035, 2.185, 0.170), rotation=(0.08, 0.0, 0.0))
    _mat(nasalfill, mats["socket"])
    parts.append(nasalfill)

    # ---- JAW slab, hung below the cranium with a visible hinge gap -----
    jw_pts = [(0.045, 2.029, 0.150), (0.045, 2.012, 0.290), (0.045, 2.004, 0.400)]
    jw_rad = [(0.072, 0.182), (0.064, 0.168), (0.050, 0.130)]
    jaw = _tube(TAG + "jaw", jw_pts, jw_rad, sides=8)
    jaw.rotation_euler = (0.0, 0.0, 0.09)
    _mat(jaw, mats["bone"])
    _smooth(jaw, 2)
    parts.append(jaw)
    jaw_surf = _Surf(jw_pts, jw_rad)
    for sx in (-1, 1):
        ram = _tube(f"{TAG}jaw_ramus_{sx}",
                    [(0.045 + sx * 0.160, 2.118, 0.175),
                     (0.045 + sx * 0.150, 2.060, 0.180)],
                    [0.038, 0.034], sides=6)
        _mat(ram, mats["bone_dim"])
        _smooth(ram, 1)
        parts.append(ram)

    # two fangs below the jaw (longer on his lifted left: the half-smile)
    for i, (lx, ln, rr) in enumerate([(-0.105, 0.078, 0.025), (0.105, 0.108, 0.029)]):
        x, y = 0.045 + lx, 1.996 + lx * 0.110
        t = _tube(f"{TAG}fang_{i}",
                  [(x, y, 0.350), (x, y - ln * 0.55, 0.346), (x, y - ln, 0.338)],
                  [rr, rr * 0.62, 0.002], sides=6)
        _mat(t, mats["bone"])
        _smooth(t, 1)
        parts.append(t)
    for i, (lx, ln) in enumerate([(-0.040, 0.050), (0.046, 0.058)]):
        t = _tube(f"{TAG}fang_up_{i}",
                  [(0.045 + lx, 2.060, 0.330), (0.045 + lx, 2.060 - ln, 0.326)],
                  [0.020, 0.002], sides=6)
        _mat(t, mats["bone"])
        _smooth(t, 1)
        parts.append(t)

    # ---- CURVED DARK-RED HORNS: up-and-out, then turning back in -------
    horn_surfs = []
    for side, sx, st in (("l", 1.0, 1.0), ("r", -1.0, 0.96)):
        pts = [
            (0.03 + sx * 0.330, 2.440, 0.090),
            (0.03 + sx * 0.432, 2.572, 0.070),
            (0.03 + sx * 0.529, 2.735, 0.020 * st),   # end of segment 1
            (0.03 + sx * 0.487, 2.868, -0.060 * st),  # segment 2 turns back in
            (0.03 + sx * 0.368, 2.962, -0.110 * st),
            (0.03 + sx * 0.265, 3.000, -0.130 * st),
        ]
        rad = [0.088, 0.076, 0.060, 0.043, 0.026, 0.007]
        horn = _tube(TAG + "horn_" + side, pts, rad, sides=8)
        _mat(horn, mats["horn"])
        _smooth(horn, 2)
        parts.append(horn)
        horn_surfs.append(_Surf(pts, rad))
        tip = _blob(f"{TAG}horntip_{side}", pts[-1], (0.019, 0.022, 0.019), subdiv=2)
        _mat(tip, mats["horn_tip"])
        _smooth(tip, 1)
        parts.append(tip)

    return torso_surf, horn_surfs, [skull_surf, jaw_surf]


# ===================================================================== arms ===

def _arm_chain(sh, elb, wri, r_sh, r_elb, r_wri, bulge):
    d1, d2 = (elb - sh), (wri - elb)
    pts = [sh, sh + d1 * 0.30 + bulge * 0.55, sh + d1 * 0.62 + bulge * 0.35,
           sh + d1 * 0.88, elb, elb + d2 * 0.16, elb + d2 * 0.42 + bulge * 0.30,
           elb + d2 * 0.74, wri]
    rad = [r_sh, (r_sh[0] * 0.92, r_sh[1] * 0.90), (r_sh[0] * 0.76, r_sh[1] * 0.76),
           (r_elb[0] * 1.08, r_elb[1] * 1.06), r_elb,
           (r_elb[0] * 1.06, r_elb[1] * 1.04), (r_elb[0] * 0.92, r_elb[1] * 0.90),
           (r_wri[0] * 1.14, r_wri[1] * 1.12), r_wri]
    return pts, rad


def _build_arms(parts, mats, rng):
    """Starved arms: thin shafts with the joints standing out as bone knobs."""
    skin = mats["skin"]
    surfs = {}

    for side, sh, elb, wri, bulge in (
            ("l", L_SH, L_ELB, L_WRI, Vector((0.026, 0.0, 0.022))),
            ("r", R_SH, R_ELB, R_WRI, Vector((-0.026, 0.0, 0.022)))):
        rsh = (0.098, 0.104) if side == "l" else (0.092, 0.098)
        pts, rad = _arm_chain(sh, elb, wri, rsh, (0.064, 0.069), (0.045, 0.049), bulge)
        arm = _tube(TAG + "arm_" + side, pts, rad, sides=10)
        _mat(arm, skin)
        _smooth(arm, 2)
        parts.append(arm)
        surfs[side] = _Surf(pts, rad)
        knob = _blob(f"{TAG}elbowknob_{side}", tuple(elb), (0.046, 0.043, 0.044), subdiv=2)
        _mat(knob, mats["bone_dim"])
        _smooth(knob, 1)
        parts.append(knob)

    # ---- LEFT hand: fist closed around the haft -------------------------
    d, o, n = AXE_D, AXE_O, AXE_N
    gp = L_WRI
    palm = _tube(TAG + "hand_l", [gp - d * 0.066 - n * 0.010, gp, gp + d * 0.066 - n * 0.007],
                 [(0.045, 0.049), (0.063, 0.068), (0.045, 0.050)], sides=8)
    _mat(palm, skin)
    _smooth(palm, 2)
    parts.append(palm)
    for i in range(4):
        base = gp + d * (-0.049 + i * 0.033) - n * 0.047
        f = _tube(f"{TAG}fing_l_{i}",
                  [base, base + n * 0.052 + o * 0.052, base + n * 0.106 + o * 0.016],
                  [0.020, 0.017, 0.011], sides=6)
        _mat(f, skin)
        _smooth(f, 2)
        parts.append(f)
    thumb = _tube(TAG + "thumb_l",
                  [gp + d * 0.049 + n * 0.035, gp + d * 0.019 + n * 0.078,
                   gp - d * 0.019 + n * 0.090],
                  [0.023, 0.018, 0.011], sides=6)
    _mat(thumb, skin)
    _smooth(thumb, 2)
    parts.append(thumb)

    # ---- RIGHT hand: open, palm UP, lazy beckon -------------------------
    pc = Vector((-0.735, 1.318, 0.620))
    palm_r = _tube(TAG + "hand_r",
                   [pc - Vector((0.007, 0.0, 0.084)), pc - Vector((0.0, 0.004, 0.010)),
                    pc + Vector((0.010, 0.000, 0.068))],
                   [(0.063, 0.030), (0.105, 0.028), (0.110, 0.025)], sides=10,
                   ref=(0.0, 1.0, 0.0))
    _mat(palm_r, skin)
    _smooth(palm_r, 2)
    parts.append(palm_r)
    heel = _blob(TAG + "palmheel_r", tuple(pc - Vector((0.007, 0.012, 0.070))),
                 (0.088, 0.037, 0.060), subdiv=2)
    _mat(heel, skin)
    _smooth(heel, 1)
    parts.append(heel)
    for i in range(4):
        fx = -0.084 + i * 0.056
        spread = 0.046 * (i - 1.5) / 1.5
        b = pc + Vector((fx, 0.003, 0.070))
        m = b + Vector((spread * 0.8, 0.025, 0.096))
        t = m + Vector((spread * 1.0, 0.073, 0.054))
        f = _tube(f"{TAG}fing_r_{i}", [b, m, t],
                  [0.026 - 0.002 * abs(i - 1.5), 0.021, 0.013], sides=6)
        _mat(f, skin)
        _smooth(f, 2)
        parts.append(f)
        cl = _tube(f"{TAG}fclaw_r_{i}", [t, t + Vector((spread * 0.3, 0.040, 0.012))],
                   [0.011, 0.002], sides=6)
        _mat(cl, mats["bone_dim"])
        _smooth(cl, 1)
        parts.append(cl)
    th = _tube(TAG + "thumb_r",
               [pc + Vector((0.088, -0.004, -0.032)), pc + Vector((0.156, 0.021, 0.024)),
                pc + Vector((0.188, 0.063, 0.067))],
               [0.029, 0.022, 0.013], sides=6)
    _mat(th, skin)
    _smooth(th, 2)
    parts.append(th)
    thc = _tube(TAG + "thumbclaw_r",
                [pc + Vector((0.188, 0.063, 0.067)), pc + Vector((0.206, 0.093, 0.083))],
                [0.011, 0.002], sides=6)
    _mat(thc, mats["bone_dim"])
    _smooth(thc, 1)
    parts.append(thc)
    return surfs


# ===================================================================== legs ===
# Gaunt SINGLE-width legs (3 world units = 0.176 m across), floor -> hip 1.059.

LEGS = {
    "l": ([(0.172, 1.075, 0.040), (0.180, 0.880, 0.105), (0.190, 0.690, 0.160),
           (0.190, 0.600, 0.140), (0.186, 0.470, 0.075), (0.182, 0.330, -0.010),
           (0.183, 0.220, 0.035), (0.186, 0.120, 0.120), (0.188, 0.072, 0.190)],
          [(0.092, 0.096), (0.088, 0.092), (0.072, 0.076), (0.068, 0.072),
           (0.062, 0.066), (0.054, 0.058), (0.050, 0.054), (0.052, 0.058),
           (0.056, 0.062)],
          (0.188, 0.190, 1.0), 2),
    "r": ([(-0.180, 1.065, -0.020), (-0.196, 0.875, -0.025), (-0.214, 0.685, -0.030),
           (-0.216, 0.595, -0.060), (-0.218, 0.465, -0.145), (-0.220, 0.325, -0.250),
           (-0.219, 0.218, -0.205), (-0.216, 0.118, -0.120), (-0.214, 0.072, -0.055)],
          [(0.092, 0.096), (0.088, 0.092), (0.072, 0.076), (0.068, 0.072),
           (0.062, 0.066), (0.054, 0.058), (0.050, 0.054), (0.052, 0.058),
           (0.056, 0.062)],
          (-0.214, -0.055, -1.0), 2),
}


def _build_legs(parts, mats, rng):
    skin = mats["skin"]
    surfs = {}
    for side, (pts, rad, (fx, fz, zd), ki) in LEGS.items():
        leg = _tube(TAG + "leg_" + side, pts, rad, sides=10)
        _mat(leg, skin)
        _smooth(leg, 2)
        parts.append(leg)
        surfs[side] = _Surf(pts, rad)

        kx, ky, kz = pts[ki]
        knob = _blob(f"{TAG}kneeknob_{side}", (kx, ky, kz + 0.040),
                     (0.068, 0.060, 0.058), subdiv=2)
        _mat(knob, mats["bone"])
        _smooth(knob, 1)
        parts.append(knob)
        hx, hy, hz = pts[5]
        hock = _blob(f"{TAG}hock_{side}", (hx, hy, hz - zd * 0.038),
                     (0.048, 0.050, 0.044), subdiv=2)
        _mat(hock, mats["bone_dim"])
        _smooth(hock, 1)
        parts.append(hock)
        # bone iliac knob at the hip, the model's upper leg-cube bone node
        px_, py_, pz_ = pts[0]
        ili = _blob(f"{TAG}iliac_{side}", (px_, py_ + 0.010, pz_ + 0.030),
                    (0.058, 0.050, 0.050), subdiv=2)
        _mat(ili, mats["bone_dim"])
        _smooth(ili, 1)
        parts.append(ili)

        foot = _tube(TAG + "foot_" + side,
                     [(fx, 0.058, fz), (fx, 0.046, fz + zd * 0.075),
                      (fx, 0.036, fz + zd * 0.140)],
                     [(0.060, 0.038), (0.066, 0.032), (0.060, 0.026)], sides=8)
        _mat(foot, skin)
        _smooth(foot, 2)
        parts.append(foot)
        for i, ox in enumerate((-0.050, 0.0, 0.050)):
            cl = _tube(f"{TAG}claw_{side}_{i}",
                       [(fx + ox, 0.038, fz + zd * 0.125),
                        (fx + ox * 1.25, 0.024, fz + zd * 0.210),
                        (fx + ox * 1.45, 0.006, fz + zd * 0.295)],
                       [0.027, 0.018, 0.003], sides=6)
            _mat(cl, mats["bone_dim"])
            _smooth(cl, 2)
            parts.append(cl)
        sp = _tube(f"{TAG}spur_{side}",
                   [(fx, 0.082, fz - zd * 0.028), (fx, 0.050, fz - zd * 0.110),
                    (fx, 0.018, fz - zd * 0.182)],
                   [0.026, 0.017, 0.003], sides=6)
        _mat(sp, mats["bone_dim"])
        _smooth(sp, 2)
        parts.append(sp)
    return surfs


# ============================================= bone, shoulder plate, rattle ===

def _build_armor(parts, glow, mats, rng, torso, arms, legs):
    """Four bone RIB BANDS, the hollow fel-core and its halo, the bone rattle
    on its cord, and dark shoulder plates edged in DI_ACCENT teal.  There is
    deliberately almost no other plate: the flesh has rotted off the bone and
    that is what the silhouette should say."""
    A, AH = mats["armor"], mats["armor_hi"]

    def shell(name, surf, t0, t1, a0, a1, m=None, **kw):
        o = _shell(TAG + name, surf, t0, t1, a0, a1, **kw)
        _mat(o, m if m else A)
        parts.append(o)
        return o

    # ---- FOUR BONE RIB BANDS at 21, 24, 27, 30 world units --------------
    for i, t in enumerate((0.171, 0.341, 0.508, 0.674)):
        shell(f"rib{i}", torso, t - 0.030, t + 0.030, -1.32, 1.32,
              gap0=0.010, thick=0.026, nt=2, na=11, m=mats["bone"], bevel=0.006)
    shell("sternum", torso, 0.150, 0.700, -0.080, 0.080,
          gap0=0.013, thick=0.022, nt=7, na=2, m=mats["bone_dim"], bevel=0.005)
    for i, t in enumerate((0.770, 0.855)):
        shell(f"ribup{i}", torso, t - 0.024, t + 0.024, -1.00, 1.00,
              gap0=0.009, thick=0.021, nt=2, na=9, m=mats["bone_dim"], bevel=0.005)

    # ---- HOLLOW FEL-CORE: the pulsing orb where a heart should be -------
    cp, cn = torso.at(0.341, 0.0)
    cavity = _shell(TAG + "core_cavity", torso, 0.285, 0.400, -0.30, 0.30,
                    gap0=-0.050, gap1=-0.050, thick=0.028, nt=3, na=5, bevel=0.0)
    _mat(cavity, mats["socket"])
    parts.append(cavity)
    core_c = cp + cn * (4 * UU)          # standing 4 u = 0.235 m proud
    core = _blob(TAG + "felcore", tuple(core_c), (0.062, 0.068, 0.062), subdiv=3)
    _mat(core, mats["core"])
    glow.append(core)
    for k, (rr, m) in enumerate(((0.098, mats["mid"]), (0.132, mats["crack_dim"]))):
        sh_ = _blob(f"{TAG}core_shell{k}", tuple(core_c - cn * 0.03),
                    (rr, rr * 1.05, rr * 0.45), subdiv=2)
        _mat(sh_, m)
        glow.append(sh_)
    # the dim halo ring, radius 9 u = 0.529 m, standing round the core
    halo = _annulus(TAG + "crack_corehalo", 9 * UU, 0.026, 0.0, thick=0.018, segs=48)
    halo.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    halo.location = (core_c.x, core_c.y, core_c.z - 0.185)
    _mat(halo, mats["crack_dim"])
    glow.append(halo)
    for i, a in enumerate((-0.16, 0.05, 0.22)):
        _band(glow, f"{TAG}core_seep{i}", torso,
              [(0.33 - k * 0.055, a + k * 0.02) for k in range(4)],
              0.015, 0.009, 0.028, mats["crack_dim"])

    # ---- BONE RATTLE ON A CORD -- Ah Puch's own iconography -------------
    ctop, _ = torso.at(0.020, 0.00, gap=0.020)
    cbot = Vector((ctop.x + 0.010, 15 * UU + 0.055, ctop.z + 0.045))
    cord = _tube(TAG + "rattle_cord", [ctop, ctop.lerp(cbot, 0.55), cbot],
                 [0.008, 0.007, 0.006], sides=6)
    _mat(cord, mats["bone_dim"])
    _smooth(cord, 1)
    parts.append(cord)
    for i, ox in enumerate((-0.052, 0.0, 0.052)):
        bead = _blob(f"{TAG}rattle_bead{i}",
                     (cbot.x + ox, cbot.y - 0.028 - abs(ox) * 0.12, cbot.z + 0.004),
                     (0.025, 0.031, 0.023), subdiv=2)
        _mat(bead, mats["bone"])
        _smooth(bead, 1)
        parts.append(bead)
    lit = _blob(TAG + "rattle_felbead", (cbot.x, cbot.y - 0.028, cbot.z + 0.020),
                (0.016, 0.019, 0.014), subdiv=2)
    _mat(lit, mats["core"])
    glow.append(lit)

    # ---- SHOULDER PLATES: 2 u thick slabs out to 12 u, teal-trimmed -----
    for side, sx in (("l", 1.0), ("r", -1.0)):
        cxp = sx * (TOR_HW + PLATE_X) * 0.5
        yp = (SHOULDER_Y + (SHOULDER_Y - 6 * UU)) * 0.5
        lean = 0.10 if side == "l" else -0.06
        pl = add_box(TAG + "paul_" + side, (PLATE_X - TOR_HW, 6 * UU, 2 * TOR_HD * 1.05),
                     (cxp, yp + (0.03 if side == "l" else -0.02), 0.175),
                     rotation=(0.05, 0.0, sx * -0.34 + lean * 0.0),
                     bevel_width=0.022, bevel_segments=3)
        _mat(pl, AH if side == "l" else A)
        parts.append(pl)
        cap = add_box(TAG + "paulcap_" + side, (PLATE_X - TOR_HW + 0.05, 0.070, 2 * TOR_HD * 1.12),
                      (cxp - sx * 0.015, yp + 6 * UU * 0.5 + 0.030
                       + (0.03 if side == "l" else -0.02), 0.175),
                      rotation=(0.05, 0.0, sx * -0.34), bevel_width=0.016, bevel_segments=3)
        _mat(cap, A)
        parts.append(cap)
        trim = add_box(TAG + "trim_" + side, (0.030, 6 * UU + 0.10, 2 * TOR_HD * 1.12),
                       (sx * PLATE_X, yp - 0.030 + (0.03 if side == "l" else -0.02), 0.175),
                       rotation=(0.05, 0.0, sx * -0.34), bevel_width=0.006)
        _mat(trim, mats["accent"])
        glow.append(trim)
        trim2 = add_box(TAG + "trimtop_" + side, (PLATE_X - TOR_HW + 0.04, 0.026, 0.040),
                        (cxp, yp + 6 * UU * 0.5 + 0.055 + (0.03 if side == "l" else -0.02),
                         0.175 + TOR_HD * 1.05),
                        rotation=(0.05, 0.0, sx * -0.34), bevel_width=0.005)
        _mat(trim2, mats["accent"])
        glow.append(trim2)

    # three big spikes, only on his spiked left pauldron
    for i, (oy, oz, ln, lift) in enumerate([(0.10, 0.14, 0.34, 1.60),
                                            (0.00, -0.02, 0.40, 1.25),
                                            (-0.12, -0.15, 0.28, 0.95)]):
        base = Vector((PLATE_X - 0.02, 1.95 + oy, 0.175 + oz))
        d = Vector((0.75, lift, -0.30)).normalized()
        sp = _tube(f"{TAG}paulspike_{i}",
                   [base, base + d * ln * 0.40, base + d * ln * 0.74, base + d * ln],
                   [0.048, 0.033, 0.018, 0.003], sides=6)
        _mat(sp, mats["horn"])
        _smooth(sp, 2)
        parts.append(sp)

    # ---- thin wrist cuffs; the rest of the arm stays bare ---------------
    for side in ("l", "r"):
        s = arms[side]
        shell(f"cuff_{side}", s, 0.860, 0.930, -math.pi, math.pi,
              gap0=0.014, gap1=0.012, thick=0.022, nt=2, na=12)
        _band(glow, f"{TAG}cufftrim_{side}", s,
              [(0.895, -3.14 + k * 1.05) for k in range(7)],
              0.011, 0.007, 0.040, mats["accent"])

    # ---- a narrow belt over the cinched waist ---------------------------
    belt = _tube(TAG + "belt",
                 [(0.0, HIP_Y - 0.010, -0.030), (0.0, HIP_Y + 0.045, -0.012),
                  (0.0, HIP_Y + 0.100, 0.005)],
                 [(0.132, 0.238), (0.142, 0.252), (0.132, 0.240)], sides=12)
    _mat(belt, A)
    belt.modifiers.new("Bevel", "BEVEL").width = 0.006
    parts.append(belt)
    for i, (a, ln) in enumerate([(-0.72, 0.26), (-0.24, 0.32), (0.24, 0.30), (0.72, 0.22)]):
        o = add_box(f"{TAG}tasset{i}", (0.115, ln, 0.036),
                    (math.sin(a) * 0.230, HIP_Y - 0.030 - ln * 0.5,
                     math.cos(a) * 0.150 - 0.020),
                    rotation=(0.12, -a, 0.03), bevel_width=0.006, bevel_segments=2)
        _mat(o, AH if i % 2 else A)
        parts.append(o)


# ===================================================================== aura ===
# Everything after dire_hero.cpp's "AURA -- FEL-FIRE COLUMN / GROUND FISSURE"
# comment, rebuilt as emissive GEOMETRY (scene_main owns all lights).

def _build_aura(aura, mats, rng):
    u = UU
    y = RING_Y

    def crack(name, p0, p1, m, w0, w1=None):
        """A ground fissure segment: a flat tapered sliver of light lying in
        the crystal, drawn as two strips so it narrows along its length."""
        p0, p1 = Vector(p0), Vector(p1)
        w1 = w0 * 0.45 if w1 is None else w1
        mid = p0.lerp(p1, 0.5)
        for k, (a, b, wa) in enumerate(((p0, mid, w0), (mid, p1, (w0 + w1) * 0.5))):
            st = _strip(f"{TAG}{name}_{k}", a, b, Vector((0, 1, 0)), wa, 0.016)
            _mat(st, m)
            aura.append(st)

    # ---- GROUND FISSURE -------------------------------------------------
    crack("fiss_xl", (-18 * u, y, 0), (-6 * u, y, 0), mats["crack"], 0.075, 0.030)
    crack("fiss_xc", (-3 * u, y, 0), (3 * u, y, 0), mats["hot"], 0.105, 0.105)
    crack("fiss_xr", (6 * u, y, 0), (18 * u, y, 0), mats["crack"], 0.030, 0.075)
    crack("fiss_zb", (0, y, -15 * u), (0, y, -4.5 * u), mats["crack"], 0.062, 0.026)
    crack("fiss_zc", (0, y, -1.5 * u), (0, y, 1.5 * u), mats["hot"], 0.088, 0.088)
    crack("fiss_zf", (0, y, 4.5 * u), (0, y, 15 * u), mats["crack"], 0.026, 0.062)
    crack("fiss_d0", (-9 * u, y, 6 * u), (-3 * u, y, 12 * u), mats["mid"], 0.046, 0.016)
    crack("fiss_d1", (9 * u, y, -6 * u), (3 * u, y, -12 * u), mats["mid"], 0.046, 0.016)

    # ---- INNER CORRUPTION RINGS, then the OUTER FEL RINGS ---------------
    for i, (rad, band, m) in enumerate((
            (12 * u, 2.2 * u, mats["crupt"]),      # 4*U -> 0.706 m
            (18 * u, 1.8 * u, mats["crupt_dim"]),  # 6*U -> 1.059 m
            (24 * u, 3.2 * u, mats["crack"]),      # 8*U -> 1.412 m
            (30 * u, 2.6 * u, mats["glow_soft"]))):  # 10*U -> 1.765 m
        r = _annulus(f"{TAG}aura_ring{i}", rad, band, y, thick=0.016, segs=64)
        _mat(r, m)
        aura.append(r)

    # ---- 6 DARK-MATTER CHAOS MOTES on a tight inner orbit ---------------
    for i in range(6):
        ang = i * (math.pi * 2.0 / 6.0) + 0.4
        mx, mz = math.cos(ang) * 13.5 * u, math.sin(ang) * 13.5 * u
        hot = (i % 3 == 0)
        c = _blob(f"{TAG}aura_mote{i}", (mx, y + 0.024 + (0.03 if hot else 0.0), mz),
                  (0.042 if hot else 0.030,) * 3, subdiv=2)
        _mat(c, mats["hot"] if hot else mats["crack"])
        aura.append(c)

    # ---- 4 OUTER SHADOW TENDRILS, rising and leaning inward -------------
    for i in range(4):
        ang = i * (math.pi * 2.0 / 4.0) + 0.25
        tx, tz = math.cos(ang) * 30 * u, math.sin(ang) * 30 * u
        top = Vector((tx * 0.7, y + 6 * u, tz * 0.7))
        base = Vector((tx, y, tz))
        low = _tube(f"{TAG}aura_tendril_lo{i}",
                    [base, base.lerp(top, 0.30), base.lerp(top, 0.55)],
                    [0.062, 0.045, 0.030], sides=6)
        _mat(low, mats["crack"])
        _smooth(low, 1)
        aura.append(low)
        hi = _tube(f"{TAG}aura_tendril_hi{i}",
                   [base.lerp(top, 0.52), base.lerp(top, 0.78), top],
                   [0.031, 0.018, 0.003], sides=6)
        _mat(hi, mats["crupt"])
        _smooth(hi, 1)
        aura.append(hi)
        foot = _blob(f"{TAG}aura_tendrilfoot{i}", (tx, y + 0.020, tz),
                     (0.040, 0.034, 0.040), subdiv=2)
        _mat(foot, mats["crupt"])
        aura.append(foot)

    # ---- DENSE FEL-FIRE COLUMN: 10 staggered flame tongues --------------
    FX = (0.0, 2.5, -2.0, 4.0, -3.5, 1.5, -1.0, 3.0, -4.0, 0.5)
    FZ = (0.0, -2.0, 3.0, -1.5, 2.5, 4.0, -3.0, 0.5, -1.0, -4.0)
    FPH = (0.0, 3.5, 7.2, 11.0, 15.3, 1.8, 5.5, 9.0, 13.7, 17.1)
    max_fh = 27 * u
    for i in range(10):
        phase = ((FPH[i] + 2.0) % 20.0) / 20.0       # staggered, never zero
        fh = phase * max_fh
        fx, fz = FX[i] * 1.26 * u, FZ[i] * 1.26 * u
        fw = 0.026 + 0.011 * math.sin(i * 0.7) + 0.006 * ((i * 7) % 5)

        def tongue(nm, height, w, m, lean, segs=6):
            pts, rad = [], []
            for k in range(segs):
                f = k / (segs - 1.0)
                sway = math.sin(f * 3.4 + i * 1.3) * 0.085 * height
                pts.append((fx + sway * lean, y + height * f, fz + sway * 0.55 * lean))
                rad.append(w * (1.0 - f) ** 2.1 + 0.0015)
            o = _tube(nm, pts, rad, sides=6)
            _mat(o, m)
            _smooth(o, 1)
            aura.append(o)

        tongue(f"{TAG}aura_flame_out{i}", fh, fw * 1.30, mats["crack_dim"], 1.0)
        tongue(f"{TAG}aura_flame_mid{i}", fh * 0.75, fw * 0.92, mats["mid"], 0.8)
        tongue(f"{TAG}aura_flame_core{i}", fh * 0.50, fw * 0.58, mats["hot"], 0.6)
        em = _blob(f"{TAG}aura_flamefoot{i}", (fx, y + 0.016, fz),
                   (0.024, 0.017, 0.024), subdiv=2)
        _mat(em, mats["hot"])
        aura.append(em)


# ==================================================================== cape ===

def _build_cape(mats, rng):
    """Torn, smouldering cape, re-fitted to the gaunt Ah Puch frame."""
    nu, nv = 30, 22
    y_top = SHOULDER_Y - 0.02
    R = 0.300
    a0, a1 = math.radians(76.0), math.radians(284.0)
    Lmax = 1.95

    lengths = []
    for i in range(nu + 1):
        uu = i / nu
        base = 0.72 + 0.15 * math.sin(uu * 7.3 + 1.1) + 0.11 * math.sin(uu * 15.1)
        roll = rng.random()
        if roll < 0.30:
            base *= rng.uniform(0.30, 0.55)
        elif roll < 0.46:
            base = min(1.0, base * rng.uniform(1.18, 1.38))
        lengths.append(max(0.16, min(1.0, base)))

    def vert(i, j):
        uu = i / nu
        a = a0 + (a1 - a0) * uu
        v = j / nv
        rx, rz = math.sin(a), math.cos(a)
        fold = 0.110 * math.sin(uu * math.pi * 9.0) * (v ** 0.6)
        rad = R * (1.0 + 1.05 * v) + fold
        yy = y_top - v * Lmax * 0.94
        x = rx * rad + 0.18 * v * v
        z = rz * rad - 0.58 * v ** 1.7
        yy += 0.07 * math.sin(a * 2.7 + 0.8) * v
        return Vector((x, yy, z))

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
    sol.thickness = 0.012
    sol.offset = 0.0
    return cape, edge_pts


# ===================================================================== axe ===

def _build_axe(parts, glow, ichor, mats, rng):
    """The scene's two-handed axe, restyled for Ah Puch: bone-bound haft, a
    dark bearded head with a bone-pale honed bit and fel-green etching."""
    d, o, n, T, B = AXE_D, AXE_O, AXE_N, AXE_T, AXE_B

    haft = _tube(TAG + "axe_haft",
                 [B, B.lerp(T, 0.28), B.lerp(T, 0.58), B.lerp(T, 0.84), T, T + d * 0.20],
                 [0.034, 0.040, 0.044, 0.044, 0.041, 0.035], sides=10)
    _mat(haft, mats["axe"])
    haft.modifiers.new("Bevel", "BEVEL").width = 0.005
    for poly in haft.data.polygons:
        poly.use_smooth = True
    parts.append(haft)
    cap = _tube(TAG + "axe_buttcap", [B - d * 0.045, B + d * 0.055], [0.049, 0.054], sides=10)
    _mat(cap, mats["bone"])
    parts.append(cap)
    for i in range(5):
        p = L_WRI + d * (-0.17 + i * 0.085)
        bind = _tube(f"{TAG}axe_bind{i}", [p - d * 0.017, p + d * 0.017], [0.049, 0.049], sides=10)
        _mat(bind, mats["bone_dim"])
        parts.append(bind)

    outline = [(0.31, 0.00), (0.31, 0.27), (0.25, 0.47), (0.11, 0.60),
               (-0.09, 0.635), (-0.27, 0.60), (-0.42, 0.47), (-0.47, 0.27),
               (-0.40, 0.09), (-0.24, 0.00)]
    th0, tmax = 0.056, 0.635
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
    bv.width = 0.009
    bv.segments = 2
    parts.append(blade)

    arc = [(0.25, 0.47), (0.18, 0.545), (0.11, 0.60), (0.01, 0.628),
           (-0.09, 0.635), (-0.19, 0.622), (-0.27, 0.60), (-0.35, 0.535),
           (-0.42, 0.47)]
    for i in range(len(arc) - 1):
        p0 = T + d * arc[i][0] + o * arc[i][1]
        p1 = T + d * arc[i + 1][0] + o * arc[i + 1][1]
        e = _strip(f"{TAG}axe_welt{i}", p0, p1, o, 0.036, 0.022)
        _mat(e, mats["axe_edge"])
        parts.append(e)

    bspike = _tube(TAG + "axe_backspike",
                   [T - o * 0.02, T - o * 0.22 + d * 0.05, T - o * 0.38 + d * 0.11],
                   [(0.126, 0.045), (0.085, 0.031), (0.009, 0.007)], sides=6)
    _mat(bspike, mats["axe"])
    parts.append(bspike)
    for i, sp in enumerate((-0.30, 0.24)):
        col = _tube(f"{TAG}axe_collar{i}", [T + d * sp - o * 0.045, T + d * sp + o * 0.11],
                    [0.066, 0.056], sides=8)
        _mat(col, mats["bone_dim"])
        col.modifiers.new("Bevel", "BEVEL").width = 0.005
        parts.append(col)
    fin = _tube(TAG + "axe_finial", [T + d * 0.20, T + d * 0.26, T + d * 0.32],
                [0.038, 0.023, 0.004], sides=6)
    _mat(fin, mats["horn"])
    _smooth(fin, 1)
    parts.append(fin)

    for i in range(4):
        sp = -0.25 + i * 0.155
        f = _strip(f"{TAG}axe_fil{i}", T + d * sp + o * 0.065 + n * (th0 * 0.92),
                   T + d * (sp * 0.5) + o * 0.36 + n * (th0 * 0.28), n, 0.014, 0.008)
        _mat(f, mats["filigree"])
        glow.append(f)
    for sgn in (1, -1):
        f = _strip(f"{TAG}axe_filspine{sgn}",
                   T + d * (-0.27) + o * 0.09 + n * sgn * (th0 * 0.88),
                   T + d * 0.25 + o * 0.09 + n * sgn * (th0 * 0.88), n * sgn, 0.018, 0.008)
        _mat(f, mats["filigree"])
        glow.append(f)

    for i, (s0, t0) in enumerate([(0.12, 0.11), (-0.05, 0.145), (-0.27, 0.125),
                                  (-0.40, 0.09)]):
        pts = [T + d * s0 + o * t0 + n * (th0 * 0.80)]
        for k in range(1, 4):
            pts.append(T + d * (s0 - 0.045 * k) + o * (t0 + 0.130 * k)
                       + n * (th0 * (0.80 - 0.18 * k)))
        run = _tube(f"{TAG}axe_runnel{i}", pts, [0.013, 0.020, 0.016, 0.009], sides=6)
        _mat(run, mats["ichor"])
        _smooth(run, 2)
        ichor.append(run)

    for i, (sp, tp) in enumerate([(0.12, 0.58), (-0.03, 0.635), (-0.22, 0.618),
                                  (-0.36, 0.53), (-0.45, 0.40)]):
        base = T + d * sp + o * tp
        ln = rng.uniform(0.24, 0.48)
        dr = _tube(f"{TAG}axe_drip{i}",
                   [base, base + Vector((0.0, -ln * 0.32, 0.006)),
                    base + Vector((0.007, -ln * 0.70, 0.009)),
                    base + Vector((0.007, -ln, 0.007))],
                   [0.021, 0.034, 0.023, 0.004], sides=6)
        _mat(dr, mats["ichor"])
        _smooth(dr, 2)
        ichor.append(dr)
        for k, fall in enumerate((0.34, 0.74)):
            if (i + k) % 2:
                continue
            dp = _blob(f"{TAG}axe_droplet{i}_{k}",
                       tuple(base + Vector((0.009, -ln - fall, 0.011))),
                       (0.019, 0.032, 0.019), subdiv=2)
            _mat(dp, mats["ichor"])
            _smooth(dp, 1)
            ichor.append(dp)
    for i in range(0, len(arc) - 1, 2):
        p0 = T + d * arc[i][0] + o * arc[i][1]
        p1 = T + d * arc[i + 1][0] + o * arc[i + 1][1]
        sm = _strip(f"{TAG}axe_edgeichor{i}", p0, p1, n, 0.042, 0.022)
        _mat(sm, mats["ichor"])
        ichor.append(sm)


# ========================================================= ichor / embers ===

def _build_ichor_splashes(ichor, mats, rng, torso, horn_surfs):
    for i in range(6):
        _splash(ichor, f"{TAG}ichor_chest{i}", torso,
                rng.uniform(0.18, 0.88), rng.uniform(-0.80, 0.90),
                rng.uniform(0.026, 0.055), rng.uniform(0.14, 0.32), mats, rng,
                drip=0.09 if i % 3 == 0 else 0.0)
    for hi, surf in enumerate(horn_surfs):
        _splash(ichor, f"{TAG}ichor_horn{hi}", surf,
                rng.uniform(0.10, 0.30), rng.uniform(0.0, 6.28),
                rng.uniform(0.022, 0.042), rng.uniform(0.30, 0.55), mats, rng)


def _build_wisps(glow, mats, rng, edge_pts):
    """Torn ribbons of fel vapour peeling off the shoulders and the hem."""
    seeds = [
        (Vector((0.56, 2.14, -0.06)), Vector((0.46, 1.0, -1.05)), 0.70, 0.034),
        (Vector((-0.54, 2.04, -0.10)), Vector((-0.42, 1.0, -1.05)), 0.60, 0.030),
        (Vector((0.03, 2.10, -0.22)), Vector((0.04, 1.0, -1.15)), 0.76, 0.038),
    ]
    picks = edge_pts[:]
    rng.shuffle(picks)
    for p in picks[:2]:
        seeds.append((Vector(p) + Vector((0, 0.04, 0)),
                      Vector((rng.uniform(-0.3, 0.3), 1.0, rng.uniform(-0.7, -0.2))),
                      rng.uniform(0.40, 0.62), rng.uniform(0.022, 0.033)))
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
            rad.append((wd * 0.14 * (1.0 - f * 0.70), wd * (1.0 - f * 0.92) + 0.002))
        w = _tube(f"{TAG}wisp{i}", pts, rad, sides=6)
        _mat(w, mats["wisp"])
        _smooth(w, 2)
        glow.append(w)


def _build_embers(glow, mats, rng, edge_pts):
    picks = edge_pts[:]
    rng.shuffle(picks)
    for i, p in enumerate(picks[:14]):
        s = rng.uniform(0.010, 0.022)
        e = _blob(f"{TAG}ember{i}",
                  (p.x + rng.uniform(-0.02, 0.02), p.y + rng.uniform(-0.04, 0.01),
                   p.z + rng.uniform(-0.02, 0.02)),
                  (s, s * rng.uniform(0.8, 1.7), s), subdiv=1)
        _mat(e, mats["ember"])
        glow.append(e)


# =================================================================== build ===

def build():
    """Creates the Chaos Lord / Ah Puch and his fel aura.  Returns the named
    top-level objects; all of them are parented to CHAOS_root."""
    rng = random.Random(20261015)
    mats = _materials()

    body, glow, armor, ichor, axe, aura = [], [], [], [], [], []

    torso_surf, horn_surfs, skin_surfs = _build_body(body, glow, mats, rng)
    arm_surfs = _build_arms(body, mats, rng)
    leg_surfs = _build_legs(body, mats, rng)
    _build_armor(armor, glow, mats, rng, torso_surf, arm_surfs, leg_surfs)
    cape, edge_pts = _build_cape(mats, rng)
    _build_axe(axe, glow, ichor, mats, rng)
    _build_ichor_splashes(ichor, mats, rng, torso_surf, horn_surfs)
    _build_embers(glow, mats, rng, edge_pts)
    _build_wisps(glow, mats, rng, edge_pts)
    _build_aura(aura, mats, rng)

    # ---- fel-green fissures over the bare corrupted flesh ---------------
    cracks = []
    _veins(cracks, "torso", torso_surf, rng, mats, 7, nseg=(6, 10), seg_len=0.110,
           width=(0.008, 0.018), t_range=(0.06, 0.95), hot=0.18, branch_p=0.55)
    for side, s in arm_surfs.items():
        _veins(cracks, f"arm{side}", s, rng, mats, 4, nseg=(5, 9), seg_len=0.100,
               width=(0.005, 0.012), t_range=(0.18, 0.95), hot=0.14, branch_p=0.45)
    for side, s in leg_surfs.items():
        _veins(cracks, f"leg{side}", s, rng, mats, 4, nseg=(6, 10), seg_len=0.110,
               width=(0.005, 0.013), t_range=(0.06, 0.95), hot=0.12, branch_p=0.45)
    for i, s in enumerate(horn_surfs):
        _veins(cracks, f"horn{i}", s, rng, mats, 1, nseg=(3, 5), seg_len=0.120,
               width=(0.004, 0.009), t_range=(0.05, 0.50), hot=0.0, branch_p=0.15)
    skull_s, jaw_s = skin_surfs
    _veins(cracks, "skull", skull_s, rng, mats, 4, nseg=(3, 6), seg_len=0.085,
           width=(0.004, 0.010), t_range=(0.12, 0.92), hot=0.34, branch_p=0.45)
    _veins(cracks, "jaw", jaw_s, rng, mats, 2, nseg=(3, 5), seg_len=0.070,
           width=(0.003, 0.008), t_range=(0.10, 0.90), hot=0.30, branch_p=0.35)

    out = {
        "body": join_parts(body, TAG + "body"),
        "armor": join_parts(armor, TAG + "armor"),
        "cracks": join_parts(cracks + glow, TAG + "glow"),
        "axe": join_parts(axe, TAG + "axe"),
        "ichor": join_parts(ichor, TAG + "ichor"),
        "aura": join_parts(aura, TAG + "aura"),
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
