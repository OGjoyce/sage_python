"""ENVIRONMENT module for "Evening Breath" — the floating crystal gate
sanctuary: translucent island floor, the Underloom glowing hell below it,
the colossal inscribed archway, the flanking colonnade, and the sea of
clouds.

Conventions (see CONVENTIONS.md): Y is up, +Z is toward camera, 1 unit =
1 m, everything built at the origin with the sanctuary floor's TOP surface
at Y = 0. No lights / camera / world / render settings here — all "glow"
is emissive geometry.

Key numbers scene_main.py may care about:
  * floor top surface      Y = 0.0, slab bottom Y = -0.40
  * island radius          ~15 m toward +Z, growing to ~22 m toward -Z
  * archway                centered X = 0, Z = -12.0, total height 13.45 m,
                           clear opening 8.5 m wide x 9.6 m tall
  * Underloom dome         crown at Y = -9.5, rim at Y = -16,
                           emission UNDERLOOM @ 13 (hot pools @ 22)
  * cloud sea              Y = -34 deck, tops up to ~-15, radius 250 m
"""

import math
import os
import random
import sys

sys.path.insert(0, "/home/user/sage_python/studio")

import bmesh  # noqa: E402
import bpy  # noqa: E402
import claude_studio as cs  # noqa: E402
from claude_studio.characters import (  # noqa: E402
    add_box,
    add_cone,
    add_cylinder,
    assign_material,
    join_parts,
)

# ------------------------------------------------------------- palette ----
SUN_ORANGE = (1.000, 0.478, 0.180, 1.0)
GOLD_LAW = (1.000, 0.816, 0.290, 1.0)
CRYSTAL = (0.671, 0.788, 0.878, 1.0)
CRYSTAL_DEEP = (0.290, 0.400, 0.510, 1.0)
UNDERLOOM = (1.000, 0.250, 0.055, 1.0)

# ------------------------------------------------------------ geometry ----
FLOOR_TOP = 0.0
FLOOR_THICK = 0.40
ISLAND_R_FRONT = 15.0
ISLAND_R_BACK_EXTRA = 7.0

ARCH_Z = -12.0
ARCH_DEPTH = 3.0
OPENING_HALF = 4.25          # clear opening 8.5 m wide
LEG_BASE_Y = 0.95            # top of the stepped plinth
CORBEL_Y = 7.40              # springing: where the opening starts to close
N_COURSE = 5
COURSE_H = (CORBEL_Y - LEG_BASE_Y) / N_COURSE
N_CORBEL = 5
CORBEL_H = 0.70
CORBEL_STEP = 0.42           # how far each course cantilevers inward
CORBEL_TOP = CORBEL_Y + N_CORBEL * CORBEL_H          # 10.90
LINTEL_Y = CORBEL_TOP + 0.50                         # center of the lintel
ARCH_TOP = 13.9              # tip of the keystone spire


def _leg_course(y):
    """(width, depth, x_center_sign1, z_front_face) of the leg course that
    contains height `y` — shared by the masonry and the glyph layout so the
    runes always sit exactly on a face."""
    k = max(0, min(N_COURSE - 1, int((y - LEG_BASE_Y) / COURSE_H)))
    w = 2.95 - 0.13 * k
    d = ARCH_DEPTH - 0.09 * k
    return w, d, OPENING_HALF + w * 0.5, ARCH_Z + d * 0.5

UNDERLOOM_CROWN_Y = -9.5


def _mats():
    """Every material this module uses, ENV_-prefixed."""
    m = {}
    m["floor"] = cs.materials.new_principled_material(
        "ENV_crystal_floor", base_color=CRYSTAL, roughness=0.05,
        transmission=0.92, ior=1.48)[0]
    m["floor_rim"] = cs.materials.new_principled_material(
        "ENV_crystal_rim", base_color=(0.46, 0.58, 0.69, 1.0), roughness=0.22,
        transmission=0.55, ior=1.5)[0]
    m["arch"] = cs.materials.new_principled_material(
        "ENV_crystal_arch", base_color=(0.56, 0.68, 0.78, 1.0), roughness=0.11,
        transmission=0.62, ior=1.52)[0]
    m["arch_deep"] = cs.materials.new_principled_material(
        "ENV_crystal_arch_deep", base_color=CRYSTAL_DEEP, roughness=0.18,
        transmission=0.45, ior=1.52)[0]
    m["shard"] = cs.materials.new_principled_material(
        "ENV_crystal_shard", base_color=CRYSTAL, roughness=0.08,
        transmission=0.88, ior=1.5)[0]
    m["pillar"] = cs.materials.new_principled_material(
        "ENV_crystal_pillar", base_color=(0.60, 0.71, 0.80, 1.0), roughness=0.14,
        transmission=0.58, ior=1.5)[0]
    # NOTE on emission levels: scene_main renders with view_transform
    # "Standard", i.e. no tone-mapping, so anything above ~1.2 clips to
    # white. UNDERLOOM at 4.0 reads as (4.0, 1.0, 0.22) -- the red channel
    # blows out while green/blue stay in range, which is exactly the
    # saturated molten orange-red we want. Pushed to 10+ every channel
    # clips and the hell below turns into a flat white lightbox. These are
    # still the brightest things in the scene and the shot's warm uplight.
    m["underloom"] = cs.materials.new_principled_material(
        "ENV_underloom", base_color=(0.02, 0.01, 0.01, 1.0), roughness=1.0,
        emission_color=UNDERLOOM, emission_strength=4.0)[0]
    m["underloom_hot"] = cs.materials.new_principled_material(
        "ENV_underloom_hot", base_color=(0.02, 0.01, 0.01, 1.0), roughness=1.0,
        emission_color=(1.0, 0.38, 0.10, 1.0), emission_strength=7.0)[0]
    m["underloom_dark"] = cs.materials.new_principled_material(
        "ENV_underloom_dark", base_color=(0.03, 0.01, 0.01, 1.0), roughness=1.0,
        emission_color=(0.55, 0.09, 0.02, 1.0), emission_strength=1.6)[0]
    m["crack"] = cs.materials.new_principled_material(
        "ENV_floor_crack", base_color=(0.05, 0.01, 0.0, 1.0), roughness=0.9,
        emission_color=(1.0, 0.30, 0.06, 1.0), emission_strength=4.5)[0]
    m["crust"] = cs.materials.new_principled_material(
        "ENV_underloom_crust", base_color=(0.045, 0.022, 0.016, 1.0), roughness=0.96)[0]
    m["glyph"] = cs.materials.new_principled_material(
        "ENV_glyph_gold", base_color=GOLD_LAW, roughness=0.3,
        emission_color=GOLD_LAW, emission_strength=5.5)[0]
    m["glyph_hot"] = cs.materials.new_principled_material(
        "ENV_glyph_gold_hot", base_color=GOLD_LAW, roughness=0.3,
        emission_color=(1.0, 0.88, 0.45, 1.0), emission_strength=7.5)[0]
    m["glyph_dim"] = cs.materials.new_principled_material(
        "ENV_glyph_gold_dim", base_color=GOLD_LAW, roughness=0.35,
        emission_color=GOLD_LAW, emission_strength=2.2)[0]
    m["shimmer"] = cs.materials.new_principled_material(
        "ENV_gate_shimmer", base_color=(0.80, 0.88, 0.95, 1.0), roughness=0.10,
        transmission=0.96, ior=1.04,
        emission_color=(1.0, 0.72, 0.42, 1.0), emission_strength=0.22)[0]
    m["cloud"] = cs.materials.new_principled_material(
        "ENV_cloud", base_color=(0.93, 0.87, 0.82, 1.0), roughness=0.92,
        emission_color=(1.0, 0.62, 0.34, 1.0), emission_strength=0.18)[0]
    m["cloud_deck"] = cs.materials.new_principled_material(
        "ENV_cloud_deck", base_color=(0.80, 0.70, 0.64, 1.0), roughness=0.95,
        emission_color=(1.0, 0.50, 0.26, 1.0), emission_strength=0.30)[0]
    return m


# ------------------------------------------------------ small helpers ----

def _island_radius(angle, rng_jitter=0.0):
    """Island plan radius at a given plan angle (x = cos, z = sin).

    Bigger toward -Z so the colonnade has room to recede behind the arch,
    which also keeps the silhouette from reading as a disc."""
    back = max(0.0, -math.sin(angle)) ** 1.3
    return ISLAND_R_FRONT + ISLAND_R_BACK_EXTRA * back + rng_jitter


def _dims(u, su, v, sv, n, sn):
    """Full (w, h, d) for a plate lying in the u/v plane with thickness sn
    along n. Axes are unit world-axis tuples."""
    return tuple(abs(u[i]) * su + abs(v[i]) * sv + abs(n[i]) * sn for i in range(3))


def _pt(origin, u, du, v, dv, n, dn):
    return tuple(origin[i] + u[i] * du + v[i] * dv + n[i] * dn for i in range(3))


# An invented sacred script: each glyph is 2-4 axis-aligned strokes laid
# out in a unit cell as (offset_u, offset_v, len_u, len_v).
_STROKES = [
    (0.00, 0.00, 0.11, 0.86),   # tall stem
    (0.00, 0.26, 0.64, 0.11),   # upper bar
    (0.00, -0.26, 0.52, 0.11),  # lower bar
    (0.00, 0.40, 0.44, 0.10),   # crown bar
    (-0.26, 0.08, 0.11, 0.46),  # left stem
    (0.26, 0.08, 0.11, 0.46),   # right stem
    (-0.22, -0.34, 0.26, 0.10), # left foot
    (0.24, -0.34, 0.26, 0.10),  # right foot
    (0.00, 0.00, 0.34, 0.12),   # mid tick
    (0.30, 0.30, 0.14, 0.14),   # dot
    (-0.30, -0.08, 0.16, 0.16), # dot
]


def _glyph(parts, mat, name, center, u, v, n, cell, rng, relief=0.075):
    """One rune-like mark, extruded `relief` proud of a face."""
    pool = list(range(len(_STROKES)))
    rng.shuffle(pool)
    count = rng.choice((2, 3, 3, 4))
    for k in pool[:count]:
        ou, ov, lu, lv = _STROKES[k]
        jitter = rng.uniform(0.86, 1.14)
        loc = _pt(center, u, ou * cell, v, ov * cell, n, relief * 0.5)
        dims = _dims(u, max(0.055, lu * cell * jitter),
                     v, max(0.055, lv * cell * jitter), n, relief)
        b = add_box(f"{name}_{k}", dims, loc)
        assign_material(b, mat)
        parts.append(b)


# ------------------------------------------------------------- floor -----

def _build_island(mats, rng):
    """One closed, broken-edged crystal slab: jittered n-gon top, slightly
    undercut bottom. Kept a clean slab in the middle so the Underloom can
    actually refract through it."""
    bm = bmesh.new()
    n_seg = 40
    top, bot = [], []
    for i in range(n_seg):
        a = 2.0 * math.pi * i / n_seg
        r = _island_radius(a, rng.uniform(-1.7, 1.2))
        if rng.random() < 0.18:
            r -= rng.uniform(1.4, 3.2)          # bitten-out notch
        top.append(bm.verts.new((math.cos(a) * r, FLOOR_TOP, math.sin(a) * r)))
        r2 = r - rng.uniform(0.15, 0.95)
        bot.append(bm.verts.new((math.cos(a) * r2, FLOOR_TOP - FLOOR_THICK,
                                 math.sin(a) * r2)))
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    for i in range(n_seg):
        j = (i + 1) % n_seg
        bm.faces.new([top[i], top[j], bot[j], bot[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("ENV_floor_mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("ENV_floor", mesh)
    bpy.context.collection.objects.link(obj)
    assign_material(obj, mats["floor"])
    return obj


def _build_island_keel(mats, rng):
    """Jagged crystal roots hanging off the rim — the "torn off a mountain"
    read, without blocking the slab's middle."""
    parts = []
    for i in range(34):
        a = 2.0 * math.pi * (i + rng.uniform(-0.3, 0.3)) / 34
        r = _island_radius(a) - rng.uniform(0.6, 3.4)
        length = rng.uniform(1.1, 4.6) * (1.0 + 0.35 * max(0.0, -math.sin(a)))
        rad = rng.uniform(0.6, 1.9)
        c = add_cone(f"ENV_keel_{i}", rad, rad * rng.uniform(0.0, 0.25), length,
                     (math.cos(a) * r, -FLOOR_THICK - length * 0.5 + 0.1,
                      math.sin(a) * r),
                     rotation=(rng.uniform(-0.28, 0.28), rng.uniform(0, 3.0),
                               rng.uniform(-0.28, 0.28)),
                     vertices=rng.choice((5, 6, 7)))
        c.rotation_euler[0] += math.pi      # cones point down
        assign_material(c, mats["floor_rim"])
        parts.append(c)
    # a few chunky broken wedges biting into the rim profile
    for i in range(12):
        a = 2.0 * math.pi * i / 12 + rng.uniform(-0.2, 0.2)
        r = _island_radius(a) - rng.uniform(0.8, 2.6)
        b = add_box(f"ENV_rimchunk_{i}",
                    (rng.uniform(1.4, 3.4), rng.uniform(0.5, 1.4), rng.uniform(1.4, 3.0)),
                    (math.cos(a) * r, -FLOOR_THICK - rng.uniform(0.0, 0.5), math.sin(a) * r),
                    rotation=(rng.uniform(-0.3, 0.3), rng.uniform(0, 3.0), rng.uniform(-0.3, 0.3)),
                    bevel_width=0.03, bevel_segments=1)
        assign_material(b, mats["floor_rim"])
        parts.append(b)
    return join_parts(parts, "ENV_island_keel")


def _build_shards(mats, rng):
    """Smaller crystal shards floating just off the island edge."""
    parts = []
    for i in range(14):
        a = rng.uniform(0, 2 * math.pi)
        r = _island_radius(a) + rng.uniform(1.6, 7.0)
        y = rng.uniform(-3.2, 1.4)
        s = rng.uniform(0.45, 1.5)
        c = add_cone(f"ENV_shard_{i}", s, s * rng.uniform(0.0, 0.3),
                     s * rng.uniform(2.0, 4.2),
                     (math.cos(a) * r, y, math.sin(a) * r),
                     rotation=(rng.uniform(-1.4, 1.4), rng.uniform(0, 3.0),
                               rng.uniform(-1.4, 1.4)),
                     vertices=rng.choice((5, 6)))
        assign_material(c, mats["shard"])
        parts.append(c)
        if rng.random() < 0.5:
            b = add_box(f"ENV_shardchip_{i}",
                        (s * rng.uniform(0.6, 1.6), s * rng.uniform(0.4, 1.0),
                         s * rng.uniform(0.6, 1.4)),
                        (math.cos(a) * (r + rng.uniform(-1.2, 1.2)),
                         y + rng.uniform(-1.6, 1.6),
                         math.sin(a) * (r + rng.uniform(-1.2, 1.2))),
                        rotation=(rng.uniform(-1.2, 1.2), rng.uniform(0, 3.0),
                                  rng.uniform(-1.2, 1.2)),
                        bevel_width=0.02)
            assign_material(b, mats["shard"])
            parts.append(b)
    # a handful hanging higher and further out, so they float in the sky
    # inside the gate's opening rather than only below the rim
    for i in range(9):
        a = rng.uniform(-math.pi * 0.95, -math.pi * 0.05)   # behind the gate
        r = rng.uniform(26.0, 60.0)
        s = rng.uniform(0.7, 2.1)
        c = add_cone(f"ENV_shard_high_{i}", s, s * rng.uniform(0.0, 0.25),
                     s * rng.uniform(2.2, 4.6),
                     (math.cos(a) * r, rng.uniform(1.0, 9.0), math.sin(a) * r),
                     rotation=(rng.uniform(-1.5, 1.5), rng.uniform(0, 3.0),
                               rng.uniform(-1.5, 1.5)),
                     vertices=rng.choice((5, 6)))
        assign_material(c, mats["shard"])
        parts.append(c)
    return join_parts(parts, "ENV_shards")


def _build_cracks(mats, rng):
    """Branching molten veins sunk just under the floor's top surface, so
    the underglow reads uneven and alive rather than as a flat wash."""
    parts = []
    idx = 0
    for seed_i in range(16):
        a0 = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(1.0, 13.0)
        x, z = math.cos(a0) * r0, math.sin(a0) * r0
        heading = rng.uniform(0, 2 * math.pi)
        for _ in range(rng.randint(3, 6)):
            length = rng.uniform(1.2, 4.0)
            heading += rng.uniform(-0.9, 0.9)
            cx = x + math.cos(heading) * length * 0.5
            cz = z + math.sin(heading) * length * 0.5
            if math.hypot(cx, cz) > _island_radius(math.atan2(cz, cx)) - 1.5:
                break
            b = add_box(f"ENV_crack_{idx}",
                        (length, 0.09, rng.uniform(0.07, 0.26)),
                        (cx, FLOOR_TOP - 0.10, cz),
                        rotation=(0.0, -heading, 0.0))
            assign_material(b, mats["crack"])
            parts.append(b)
            idx += 1
            x += math.cos(heading) * length
            z += math.sin(heading) * length
    # molten veining pressed against the slab underside: long thin slivers,
    # not slabs, so the glow under the glass stays filamentary
    for i in range(54):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.5, 16.0)
        b = add_box(f"ENV_pool_{i}",
                    (rng.uniform(0.9, 4.5), 0.04, rng.uniform(0.07, 0.5)),
                    (math.cos(a) * r, FLOOR_TOP - FLOOR_THICK + 0.06, math.sin(a) * r),
                    rotation=(0.0, rng.uniform(0, 3.0), 0.0))
        assign_material(b, mats["underloom_hot" if i % 5 == 0 else "crack"])
        parts.append(b)
    return join_parts(parts, "ENV_floor_cracks")


# --------------------------------------------------------- underloom -----

def _build_underloom(mats, rng):
    """The hell below: a wide, shallow emissive dome crowning up toward the
    island, plus hotter pools floating above it. This is the shot's warm
    uplight source, so it is genuinely bright (13 / 22)."""
    bm = bmesh.new()
    rings_r = [0.0, 10.0, 21.0, 33.0, 46.0]
    rings_y = [UNDERLOOM_CROWN_Y, UNDERLOOM_CROWN_Y - 0.8,
               UNDERLOOM_CROWN_Y - 2.4, UNDERLOOM_CROWN_Y - 4.3,
               UNDERLOOM_CROWN_Y - 6.5]
    n_seg = 22
    rings = []
    for ri, (r, y) in enumerate(zip(rings_r, rings_y)):
        if ri == 0:
            rings.append([bm.verts.new((0.0, y, 0.0))])
            continue
        row = []
        for i in range(n_seg):
            a = 2.0 * math.pi * i / n_seg
            jr = r * rng.uniform(0.94, 1.06)
            row.append(bm.verts.new((math.cos(a) * jr, y + rng.uniform(-0.5, 0.5),
                                     math.sin(a) * jr)))
        rings.append(row)
    for i in range(n_seg):
        j = (i + 1) % n_seg
        bm.faces.new([rings[0][0], rings[1][i], rings[1][j]])
    for ri in range(1, len(rings) - 1):
        for i in range(n_seg):
            j = (i + 1) % n_seg
            bm.faces.new([rings[ri][i], rings[ri][j],
                          rings[ri + 1][j], rings[ri + 1][i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("ENV_underloom_mesh")
    bm.to_mesh(mesh)
    bm.free()
    dome = bpy.data.objects.new("ENV_underloom_dome", mesh)
    bpy.context.collection.objects.link(dome)
    assign_material(dome, mats["underloom"])

    parts = [dome]
    for i in range(20):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.0, 32.0)
        b = add_box(f"ENV_underloom_pool_{i}",
                    (rng.uniform(2.0, 7.0), 0.12, rng.uniform(2.0, 6.0)),
                    (math.cos(a) * r, UNDERLOOM_CROWN_Y + rng.uniform(0.5, 3.0),
                     math.sin(a) * r),
                    rotation=(rng.uniform(-0.15, 0.15), rng.uniform(0, 3.0),
                              rng.uniform(-0.15, 0.15)))
        assign_material(b, mats["underloom_hot" if i % 2 else "underloom"])
        parts.append(b)
    # dark crust floating over the molten floor: silhouetted slag that makes
    # the Underloom read as broken and moving, not as a lightbox
    for i in range(26):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(2.0, 44.0)
        b = add_box(f"ENV_underloom_crust_{i}",
                    (rng.uniform(3.0, 13.0), rng.uniform(0.3, 1.1), rng.uniform(3.0, 11.0)),
                    (math.cos(a) * r,
                     UNDERLOOM_CROWN_Y + rng.uniform(1.0, 5.5) - 0.07 * r,
                     math.sin(a) * r),
                    rotation=(rng.uniform(-0.18, 0.18), rng.uniform(0, 3.0),
                              rng.uniform(-0.18, 0.18)))
        assign_material(b, mats["crust"])
        parts.append(b)
    return join_parts(parts, "ENV_underloom")


# ------------------------------------------------------------- arch ------

def _arch_blocks(parts, mats, rng):
    """Heavy stepped crystal masonry: plinths, tapering legs, a corbelled
    head, lintel, crown, and a protruding keystone."""
    for s in (-1, 1):
        tag = "R" if s > 0 else "L"
        # stepped plinth
        for k, (w, h, d) in enumerate(((4.0, 0.50, 4.2), (3.5, 0.45, 3.7))):
            y = 0.25 if k == 0 else 0.725
            b = add_box(f"ENV_arch_plinth_{tag}{k}", (w, h, d),
                        (s * (OPENING_HALF + 1.15), y, ARCH_Z),
                        bevel_width=0.04, bevel_segments=2)
            assign_material(b, mats["arch_deep"])
            parts.append(b)
        # tapering leg, five stacked courses, inner face held at OPENING_HALF
        for k in range(N_COURSE):
            w = 2.95 - 0.13 * k
            d = ARCH_DEPTH - 0.09 * k
            y = LEG_BASE_Y + COURSE_H * (k + 0.5)
            b = add_box(f"ENV_arch_leg_{tag}{k}", (w, COURSE_H * 0.99, d),
                        (s * (OPENING_HALF + w * 0.5), y, ARCH_Z),
                        bevel_width=0.035, bevel_segments=2)
            assign_material(b, mats["arch"])
            parts.append(b)
            # a course line proud of the camera-facing face
            pb = add_box(f"ENV_arch_band_{tag}{k}", (w * 0.92, 0.10, d * 0.06),
                         (s * (OPENING_HALF + w * 0.5), y + COURSE_H * 0.5 - 0.06,
                          ARCH_Z + d * 0.5),
                         bevel_width=0.012)
            assign_material(pb, mats["arch_deep"])
            parts.append(pb)
            # inner-face reveal: a shallow pilaster facing the opening
            ib = add_box(f"ENV_arch_reveal_{tag}{k}", (0.18, COURSE_H * 0.86, d * 0.52),
                         (s * (OPENING_HALF - 0.05), y, ARCH_Z),
                         bevel_width=0.02)
            assign_material(ib, mats["arch_deep"])
            parts.append(ib)
        # corbelled head: blocks cantilever inward to close the arch
        for k in range(N_CORBEL):
            inner = OPENING_HALF - CORBEL_STEP * (k + 1)
            outer = 6.75 - 0.13 * k
            w = outer - inner
            y = CORBEL_Y + CORBEL_H * (k + 0.5)
            b = add_box(f"ENV_arch_corbel_{tag}{k}", (w, CORBEL_H * 0.99, ARCH_DEPTH - 0.18 - 0.08 * k),
                        (s * (inner + w * 0.5), y, ARCH_Z),
                        bevel_width=0.035, bevel_segments=2)
            assign_material(b, mats["arch"])
            parts.append(b)
            # a bracket nose under each cantilever, catching the underlight
            nb = add_box(f"ENV_arch_bracket_{tag}{k}", (0.5, 0.16, ARCH_DEPTH * 0.55),
                         (s * (inner + 0.25), y - CORBEL_H * 0.5 + 0.08, ARCH_Z),
                         bevel_width=0.02)
            assign_material(nb, mats["arch_deep"])
            parts.append(nb)
        # buttress wedge on the outside of each leg
        b = add_box(f"ENV_arch_buttress_{tag}", (1.15, 4.6, 1.8),
                    (s * 7.3, 2.6, ARCH_Z), bevel_width=0.04, bevel_segments=2)
        assign_material(b, mats["arch_deep"])
        parts.append(b)
        b = add_cone(f"ENV_arch_butt_top_{tag}", 0.88, 0.2, 1.8,
                     (s * 7.3, 5.75, ARCH_Z), vertices=6)
        assign_material(b, mats["arch_deep"])
        parts.append(b)

    # lintel + crown spanning the whole gate
    b = add_box("ENV_arch_lintel", (13.9, 1.0, ARCH_DEPTH + 0.15),
                (0.0, LINTEL_Y, ARCH_Z), bevel_width=0.05, bevel_segments=2)
    assign_material(b, mats["arch"])
    parts.append(b)
    b = add_box("ENV_arch_crown", (12.4, 0.5, ARCH_DEPTH - 0.35),
                (0.0, LINTEL_Y + 0.75, ARCH_Z), bevel_width=0.04, bevel_segments=2)
    assign_material(b, mats["arch_deep"])
    parts.append(b)
    for i in range(9):
        x = -5.6 + 1.4 * i
        b = add_cone(f"ENV_arch_merlon_{i}", 0.42, 0.10, 1.0,
                     (x, LINTEL_Y + 1.45, ARCH_Z), vertices=5)
        assign_material(b, mats["arch_deep"])
        parts.append(b)

    # keystone: steps forward toward the camera, the glyph focus
    b = add_box("ENV_arch_keystone", (3.2, 2.8, ARCH_DEPTH + 0.9),
                (0.0, LINTEL_Y - 0.55, ARCH_Z + 0.25), bevel_width=0.05, bevel_segments=2)
    assign_material(b, mats["arch"])
    parts.append(b)
    b = add_box("ENV_arch_keystone_cap", (3.9, 0.45, ARCH_DEPTH + 1.2),
                (0.0, LINTEL_Y + 1.05, ARCH_Z + 0.25), bevel_width=0.04, bevel_segments=2)
    assign_material(b, mats["arch_deep"])
    parts.append(b)
    b = add_cone("ENV_arch_keystone_spire", 1.05, 0.0, 2.4,
                 (0.0, LINTEL_Y + 2.45, ARCH_Z + 0.25), vertices=6)
    assign_material(b, mats["arch_deep"])
    parts.append(b)
    return parts


def _build_arch(mats, rng):
    parts = _arch_blocks([], mats, rng)
    return join_parts(parts, "ENV_arch")


def _build_glyphs(mats, rng):
    """Dozens of golden law-glyphs: columns running up both legs on the
    camera-facing and inner faces, plus a band across lintel and keystone."""
    parts = []
    gi = 0
    PZ = (0.0, 0.0, 1.0)
    PY = (0.0, 1.0, 0.0)
    PX = (1.0, 0.0, 0.0)

    for s in (-1, 1):
        # two columns of runes climbing the camera-facing face of each leg
        y = LEG_BASE_Y + 0.42
        while y < CORBEL_Y - 0.25:
            w, d, xc, z_face = _leg_course(y)
            for col in (-0.46, 0.46):
                c = (s * xc + col * w * 0.48, y, z_face)
                mat = mats["glyph_hot"] if (gi % 6 == 0) else mats["glyph"]
                _glyph(parts, mat, f"ENV_glyph_f{gi}", c, PX, PY, PZ, 0.60, rng)
                gi += 1
            # one column on the inner face, glowing into the opening
            c = (s * OPENING_HALF, y, ARCH_Z + rng.uniform(-0.55, 0.55))
            _glyph(parts, mats["glyph"], f"ENV_glyph_i{gi}", c, PZ, PY,
                   (s, 0.0, 0.0), 0.55, rng)
            gi += 1
            y += 0.72
        # glyphs on the corbel faces, following the opening inward
        for k in range(N_CORBEL):
            inner = OPENING_HALF - CORBEL_STEP * (k + 1)
            outer = 6.75 - 0.13 * k
            z_face = ARCH_Z + (ARCH_DEPTH - 0.18 - 0.08 * k) * 0.5
            for col in (0.3, 0.68):
                c = (s * (inner + (outer - inner) * col),
                     CORBEL_Y + CORBEL_H * (k + 0.5), z_face)
                _glyph(parts, mats["glyph"], f"ENV_glyph_c{gi}", c, PX, PY, PZ, 0.55, rng)
                gi += 1

    # lintel band
    for i in range(13):
        x = -6.0 + 1.0 * i
        if abs(x) < 2.1:
            continue
        c = (x, LINTEL_Y, ARCH_Z + (ARCH_DEPTH + 0.15) * 0.5)
        mat = mats["glyph_hot"] if i % 5 == 0 else mats["glyph"]
        _glyph(parts, mat, f"ENV_glyph_l{gi}", c, PX, PY, PZ, 0.55, rng)
        gi += 1
    # keystone face: a dense 3x3 sigil cluster
    for ix in range(3):
        for iy in range(3):
            c = (-0.9 + 0.9 * ix, LINTEL_Y - 1.45 + 0.9 * iy,
                 ARCH_Z + (ARCH_DEPTH + 0.9) * 0.5 + 0.25)
            _glyph(parts, mats["glyph_hot"], f"ENV_glyph_k{gi}", c, PX, PY, PZ, 0.62, rng)
            gi += 1
    # a low inscribed threshold line across the gate's footprint
    for i in range(16):
        x = -7.5 + i
        b = add_box(f"ENV_glyph_thresh_{i}", (0.55, 0.03, 0.16),
                    (x, FLOOR_TOP + 0.015, ARCH_Z + ARCH_DEPTH * 0.5 + 0.55))
        assign_material(b, mats["glyph_dim"])
        parts.append(b)
    # the sanctuary's inlaid law-circle, flush with the floor
    for ri, (radius, n_dash, dash) in enumerate(((7.60, 72, 0.44), (8.15, 48, 0.22))):
        for i in range(n_dash):
            a = 2.0 * math.pi * (i + 0.2 * ri) / n_dash
            b = add_box(f"ENV_glyph_circle{ri}_{i}", (dash, 0.025, 0.11),
                        (math.cos(a) * radius, FLOOR_TOP + 0.012, math.sin(a) * radius),
                        rotation=(0.0, -a + math.pi / 2.0, 0.0))
            assign_material(b, mats["glyph_dim"])
            parts.append(b)
    print(f"ENV: {gi} law-glyphs")
    return join_parts(parts, "ENV_glyphs")


def _build_shimmer(mats):
    """A barely-there membrane across the opening — heat-haze / portal
    shimmer, not a wall."""
    h = CORBEL_Y + 0.55
    b = add_box("ENV_gate_shimmer", (OPENING_HALF * 2.0 - 0.05, h, 0.02),
                (0.0, h * 0.5, ARCH_Z))
    assign_material(b, mats["shimmer"])
    return b


# ---------------------------------------------------------- colonnade ----

# (|x|, z, height, broken). Kept outside +-4.5 m on X anywhere in front of
# Z = -4 so the two foreground figures are never blocked, and clear of both
# the gate footprint and the background fiend's mark at (-7.5, 0, -18).
PILLARS = [
    (6.90, 2.2, 8.2, False),
    (7.85, -2.8, 9.0, False),
    (8.75, -7.6, 9.8, True),
    (9.20, -12.6, 10.4, False),
    (10.10, -17.4, 8.6, True),
]


def _build_pillars(mats, rng):
    parts = []
    for pi, (ax, z, h, broken) in enumerate(PILLARS):
        for s in (-1, 1):
            x = s * ax
            tag = f"{pi}{'R' if s > 0 else 'L'}"
            base = add_box(f"ENV_pil_base_{tag}", (2.20, 0.36, 2.20),
                           (x, 0.18, z), bevel_width=0.03, bevel_segments=2)
            assign_material(base, mats["arch_deep"])
            parts.append(base)
            base2 = add_box(f"ENV_pil_base2_{tag}", (1.85, 0.26, 1.85),
                            (x, 0.48, z), bevel_width=0.03, bevel_segments=2)
            assign_material(base2, mats["arch_deep"])
            parts.append(base2)
            shaft_h = h - 1.3
            shaft = add_cylinder(f"ENV_pil_shaft_{tag}", 0.72, shaft_h,
                                 (x, 0.6 + shaft_h * 0.5, z), vertices=10)
            shaft.rotation_euler = (math.pi / 2.0, 0.0, 0.0)  # cylinder is +Z long
            assign_material(shaft, mats["pillar"])
            parts.append(shaft)
            if broken:
                # snapped top: an angled shear cap, no capital
                cap = add_cone(f"ENV_pil_snap_{tag}", 0.78, 0.30, 1.1,
                               (x + rng.uniform(-0.12, 0.12), 0.6 + shaft_h + 0.4, z),
                               rotation=(rng.uniform(-0.3, 0.3), 0.0,
                                         rng.uniform(-0.3, 0.3)), vertices=7)
                assign_material(cap, mats["pillar"])
                parts.append(cap)
            else:
                nk = add_box(f"ENV_pil_neck_{tag}", (1.62, 0.24, 1.62),
                             (x, 0.6 + shaft_h + 0.12, z), bevel_width=0.02)
                assign_material(nk, mats["arch_deep"])
                parts.append(nk)
                cap = add_box(f"ENV_pil_cap_{tag}", (2.0, 0.55, 2.0),
                              (x, 0.6 + shaft_h + 0.52, z),
                              bevel_width=0.04, bevel_segments=2)
                assign_material(cap, mats["pillar"])
                parts.append(cap)
                top = add_box(f"ENV_pil_abacus_{tag}", (1.7, 0.32, 1.7),
                              (x, 0.6 + shaft_h + 0.96, z), bevel_width=0.03)
                assign_material(top, mats["arch_deep"])
                parts.append(top)
                # a single glyph stud on the camera-facing side of the capital
                g = add_box(f"ENV_pil_glyph_{tag}", (0.34, 0.34, 0.08),
                            (x, 0.6 + shaft_h + 0.52, z + 1.02))
                assign_material(g, mats["glyph"])
                parts.append(g)
    return join_parts(parts, "ENV_pillars")


# ------------------------------------------------------------ clouds -----

def _build_clouds(mats, rng):
    """Cheap sea of cloud tops: one warm deck disc plus many squashed
    low-poly blobs, dense near the island and sprawling to 250 m."""
    bm = bmesh.new()
    n_seg = 32
    center = bm.verts.new((0.0, -34.0, 0.0))
    ring = []
    for i in range(n_seg):
        a = 2.0 * math.pi * i / n_seg
        ring.append(bm.verts.new((math.cos(a) * 620.0, -38.0, math.sin(a) * 620.0)))
    for i in range(n_seg):
        bm.faces.new([center, ring[i], ring[(i + 1) % n_seg]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("ENV_cloud_deck_mesh")
    bm.to_mesh(mesh)
    bm.free()
    deck = bpy.data.objects.new("ENV_cloud_deck", mesh)
    bpy.context.collection.objects.link(deck)
    assign_material(deck, mats["cloud_deck"])

    parts = [deck]
    bands = ((36.0, 85.0, 70, 6.0, 15.0), (85.0, 170.0, 60, 12.0, 30.0),
             (170.0, 320.0, 48, 22.0, 50.0), (320.0, 600.0, 42, 34.0, 80.0))
    for bi, (r0, r1, count, s0, s1) in enumerate(bands):
        for i in range(count):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(r0, r1)
            sx = rng.uniform(s0, s1)
            bpy.ops.mesh.primitive_ico_sphere_add(
                subdivisions=2, radius=1.0,
                location=(math.cos(a) * r,
                          rng.uniform(-33.0, -21.0) + (bi * -1.5),
                          math.sin(a) * r))
            o = bpy.context.active_object
            o.name = f"ENV_cloud_{bi}_{i}"
            o.scale = (sx, sx * rng.uniform(0.16, 0.34), sx * rng.uniform(0.7, 1.4))
            o.rotation_euler = (0.0, rng.uniform(0, 3.0), 0.0)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            bpy.ops.object.shade_smooth()
            assign_material(o, mats["cloud"])
            parts.append(o)
    # Distant cumulus towers. From the final camera (y = 1.15, near level)
    # every sight-line steeper than about -2 degrees lands on the island
    # itself, so a cloud sea that lives only at y = -30 would be invisible.
    # These towers are rooted down in the deck but pile up to roughly the
    # island's own height, so the horizon reads as a sea of cloud tops.
    for i in range(46):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(110.0, 560.0)
        s = rng.uniform(22.0, 70.0) * (0.6 + r / 560.0)
        top = rng.uniform(-9.0, 2.0)
        for j in range(rng.randint(2, 4)):
            bs = s * rng.uniform(0.45, 1.0)
            bpy.ops.mesh.primitive_ico_sphere_add(
                subdivisions=2, radius=1.0,
                location=(math.cos(a) * r + rng.uniform(-s, s),
                          top - j * bs * 0.30 - rng.uniform(0.0, 4.0),
                          math.sin(a) * r + rng.uniform(-s, s)))
            o = bpy.context.active_object
            o.name = f"ENV_cloud_tower_{i}_{j}"
            o.scale = (bs, bs * rng.uniform(0.22, 0.45), bs * rng.uniform(0.7, 1.3))
            o.rotation_euler = (0.0, rng.uniform(0, 3.0), 0.0)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            bpy.ops.object.shade_smooth()
            assign_material(o, mats["cloud"])
            parts.append(o)
    # cloud tops lapping close around the island, read just below the rim
    for i in range(34):
        a = rng.uniform(0, 2 * math.pi)
        r = _island_radius(a) + rng.uniform(3.0, 24.0)
        s = rng.uniform(4.0, 11.0)
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2, radius=1.0,
            location=(math.cos(a) * r, rng.uniform(-21.0, -13.5), math.sin(a) * r))
        o = bpy.context.active_object
        o.name = f"ENV_cloud_near_{i}"
        o.scale = (s, s * rng.uniform(0.2, 0.4), s * rng.uniform(0.7, 1.3))
        o.rotation_euler = (0.0, rng.uniform(0, 3.0), 0.0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        bpy.ops.object.shade_smooth()
        assign_material(o, mats["cloud"])
        parts.append(o)
    return join_parts(parts, "ENV_clouds")


# ------------------------------------------------------------- build -----

def build():
    """Build the environment. Returns the named top-level objects; every
    one is parented to the single ENV_root Empty."""
    rng = random.Random(20251015)
    mats = _mats()

    root = bpy.data.objects.new("ENV_root", None)
    bpy.context.collection.objects.link(root)

    out = {"root": root}
    out["floor"] = _build_island(mats, rng)
    out["keel"] = _build_island_keel(mats, rng)
    out["shards"] = _build_shards(mats, rng)
    out["cracks"] = _build_cracks(mats, rng)
    out["underloom"] = _build_underloom(mats, rng)
    out["arch"] = _build_arch(mats, rng)
    out["glyphs"] = _build_glyphs(mats, rng)
    out["shimmer"] = _build_shimmer(mats)
    out["pillars"] = _build_pillars(mats, rng)
    out["clouds"] = _build_clouds(mats, rng)

    for key, obj in out.items():
        if key == "root":
            continue
        obj.parent = root

    depsgraph = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for key, obj in out.items():
        if obj.type != "MESH":
            continue
        ev = obj.evaluated_get(depsgraph)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        n = len(me.loop_triangles)
        tris += n
        ev.to_mesh_clear()
        print(f"ENV: {key:10s} {n:7d} tris")
    print(f"ENV: total {tris} triangles")
    return out


if __name__ == "__main__":
    build()
