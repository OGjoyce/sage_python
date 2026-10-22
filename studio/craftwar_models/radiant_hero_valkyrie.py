"""Radiant Hero "Sun-King" -- VALKYRIE SKIN (cinematic).

Port of src/gfx/models3d/radiant_hero_valkyrie.cpp, C++ numbers verbatim.
Separate from radiant_hero.py: that is the gameplay model and is unchanged.

What translates and what does not. The figure is axis-aligned boxes, cubes,
triangles and a matrix stack, which is exactly the substitution table the
other models use, so it comes across one for one. The cold open's sky, cloud
volume, fog and lightning do NOT: those are camera-facing billboards and GL
render state, not geometry, and in Blender they belong in a world shader and
a volume rather than in a mesh.
"""

import math

from claude_studio.craftwar_gl import GLModel

VK_PLATE = 0x4A5870   # deep slate-blue lamellar
VK_DARK  = 0x202838   # near-black navy
VK_JADE  = 0x2E9E90   # jade ceremonial
VK_GLOW  = 0xFFD840   # solar gold glow
VK_GOLD  = 0xD4A828   # gold trim
VK_SKIN  = 0xC09050   # warm brown complexion
VK_HAIR  = 0x33210F
VK_CAPE  = 0x141A26
VK_LINE  = 0x5A2028   # cape lining
VK_WING  = 0xE8EEF6   # feather
VK_WINGD = 0x8FA3C0   # feather underside
VK_SHAFT = 0x6A5A42


def _feather(m, length, wide, thick, col, mul):
    """A thin tapered slab. glBegin(GL_QUADS) with four faces -> four quads."""
    tipw = wide * 0.35
    m.quad((-wide, 0, thick), (wide, 0, thick),
           (tipw, -length, thick), (-tipw, -length, thick), col, mul * 1.00)
    m.quad((wide, 0, -thick), (-wide, 0, -thick),
           (-tipw, -length, -thick), (tipw, -length, -thick), col, mul * 0.55)
    m.quad((wide, 0, thick), (wide, 0, -thick),
           (tipw, -length, -thick), (tipw, -length, thick), col, mul * 0.80)
    m.quad((-wide, 0, -thick), (-wide, 0, thick),
           (-tipw, -length, thick), (-tipw, -length, -thick), col, mul * 0.70)


def _wing(m, tickF, side, spread):
    """Three rows of feathers fanned along an arc, plus a gold leading edge."""
    flap = math.sin(tickF * 0.11)
    m.push()
    m.scale(side, 1, 1)                      # mirror for the far wing
    for i in range(16):
        u = i / 15.0
        ang = 3.0 + u * 34.0
        rad = 5.0 + u * spread
        m.push()
        m.rotate(ang + flap * 5.0, 0, 0, 1)
        m.translate(rad, 0, 0)
        m.box3d(-1.6, -0.9, -0.7, 1.6, 0.9, 0.7, VK_GOLD, 1.0)
        m.pop()
    ROW_LEN = (12.0, 20.0, 28.0)
    ROW_N = (22, 18, 14)
    for row in range(3):
        for i in range(ROW_N[row]):
            u = (i + row * 0.33) / float(ROW_N[row] - 1)
            if u > 1.0:
                continue
            ang = 5.0 + u * 33.0
            rad = 5.0 + u * spread
            taper = math.sin(3.14159 * (0.12 + 0.80 * u))
            length = ROW_LEN[row] * (0.45 + 0.75 * taper)
            m.push()
            m.rotate(ang + flap * (4.0 + row), 0, 0, 1)
            m.translate(rad, -row * 2.0, -0.6 - row * 1.5)
            m.rotate(14.0 + row * 9.0, 1, 0, 0)      # rows cup backwards
            _feather(m, length, 3.6 - row * 0.35, 0.5,
                     VK_WING if row == 0 else VK_WINGD, 1.05 - row * 0.13)
            m.pop()
    m.pop()


def build(tickF=0.0, anim=0, name="RADIANT_hero_valkyrie", **bake):
    """**bake is forwarded to GLModel.build() -- unlit/emit_strength/
    emit_threshold, for dropping the model into a lit scene."""
    m = GLModel(name)
    S = 39.0 / 57.0              # crown lands at the canonical hero's 13U
    idleP = tickF * 0.9
    bob = abs(math.sin(tickF * 2.8)) * 2.5 if anim == 1 else math.sin(idleP) * 0.8
    sway = math.sin(idleP * 0.9) * 1.5
    gust = math.sin(tickF * 1.35) * 1.8

    m.push()
    m.scale(S, S, S)
    m.translate(0, bob, 0)

    # Wings, behind everything
    m.push()
    m.translate(0, 44.0, -5.0)
    for side in (-1, 1):
        _wing(m, tickF, side, 48.0)
    m.pop()

    # Cape: lining a shade wider than the outer, so it reads as a lining
    m.push()
    m.translate(0, 0, -4.6)
    m.rotate(sway * 0.8, 0, 0, 1)
    m.quad((-8.2, 46.5, 0.2), (8.2, 46.5, 0.2),
           (13.2 + sway, -5.0, -2.2), (-13.2 + sway, -5.0, -2.2), VK_LINE, 1.00)
    m.quad((-7.6, 46.0, 0.5), (7.6, 46.0, 0.5),
           (12.4 + sway, -4.0, -1.9), (-12.4 + sway, -4.0, -1.9), VK_CAPE, 1.00)
    m.pop()

    # Spear
    m.box3d(14.8, -9.0, -0.8, 16.4, 62.0, 0.8, VK_SHAFT, 1.0)
    m.box3d(14.4, 40.0, -1.0, 16.8, 42.4, 1.0, VK_JADE, 1.0)      # grip wrap
    m.tri((13.4, 62.0, 0), (17.8, 62.0, 0), (15.6, 71.0, 0), VK_GLOW, 1.05)
    m.tri((15.6, 62.0, 1.1), (15.6, 62.0, -1.1), (15.6, 71.0, 0), VK_GOLD, 0.75)

    # Legs: boot, greave, knee cop, thigh
    for side in (-1, 1):
        lx = side * 5.0
        m.box3d(lx - 3.4, 17.0, -3.0, lx + 3.4, 28.0, 3.0, VK_DARK, 1.30)
        m.box3d(lx - 2.7, 5.5, -2.7, lx + 2.7, 16.0, 2.7, VK_PLATE, 1.00)
        m.box3d(lx - 3.3, 15.0, -3.2, lx + 3.3, 18.6, 3.2, VK_PLATE, 1.14)
        m.box3d(lx - 0.9, 15.6, 3.0, lx + 0.9, 17.8, 3.6, VK_GLOW, 1.00)
        m.box3d(lx - 3.6, 0.0, -3.4, lx + 3.6, 5.5, 4.2, VK_DARK, 1.10)
        m.box3d(lx - 3.7, 4.6, -3.5, lx + 3.7, 5.9, 4.3, VK_GOLD, 1.00)

    # Faulds: three flaring lames
    for lam in range(3):
        y0 = 26.4 + lam * 1.7
        hw = 5.9 + lam * 0.8
        m.box3d(-hw, y0, -3.6, hw, y0 + 2.4, 3.6, VK_PLATE, 1.02 - lam * 0.04)
        m.box3d(-hw, y0, 3.5, hw, y0 + 0.5, 3.9, VK_DARK, 1.00)

    # Waist, jade sash, hanging celts
    m.box3d(-5.2, 31.0, -3.4, 5.2, 35.4, 3.4, VK_PLATE, 0.92)
    m.box3d(-5.5, 31.2, -3.6, 5.5, 34.4, 3.7, VK_JADE, 1.00)
    m.box3d(-1.1, 32.0, 3.6, 1.1, 33.8, 4.2, VK_GLOW, 1.05)
    sw = math.sin(tickF * 0.30) * 0.8
    m.cube3(-3.6, 29.5 + sw * 0.5, 3.4, 0.9, VK_JADE, 0.95)
    m.cube3(0.0, 29.1 + sw, 3.4, 0.9, VK_JADE, 0.85)
    m.cube3(3.6, 29.5 - sw * 0.5, 3.4, 0.9, VK_JADE, 0.80)

    # Chest: narrow at the waist, broad at the shoulders
    m.box3d(-9.0, 35.0, -4.0, 9.0, 46.0, 4.0, VK_PLATE, 1.00)
    m.box3d(-5.3, 34.0, -3.6, 5.3, 36.0, 3.6, VK_PLATE, 0.94)
    # Step-fret greca, two courses, teeth offset on alternate pairs
    for i in range(6):
        sx0 = -7.4 + i * 2.5
        o = 1.6 if (i & 2) else 0.0
        m.box3d(sx0, 37.2 + o, 3.9, sx0 + 2.5, 38.1 + o, 4.4, VK_DARK, 1.00)
        m.box3d(sx0, 42.0 + o, 3.9, sx0 + 2.5, 42.9 + o, 4.4, VK_DARK, 1.00)

    # The k'in sun-disc: eight rays and a burning core
    ey, ez = 40.2, 4.0
    m.box3d(-6.2, ey - 0.55, ez, 6.2, ey + 0.55, ez + 0.8, VK_GLOW, 0.85)
    m.box3d(-0.55, ey - 6.2, ez, 0.55, ey + 6.2, ez + 0.8, VK_GLOW, 0.85)
    for i in range(4):
        ang = 0.7854 + i * 1.5708
        dx, dy = math.cos(ang) * 4.3, math.sin(ang) * 4.3
        m.box3d(dx - 0.75, ey + dy - 0.75, ez,
                dx + 0.75, ey + dy + 0.75, ez + 0.7, VK_GLOW, 0.74)
    m.cube3(0, ey, ez + 1.6, 2.4, VK_GOLD, 1.05)
    m.cube3(0, ey, ez + 2.2, 1.5, VK_GLOW, 1.1 + 0.5 * math.sin(tickF * 0.22))

    # Gorget
    m.box3d(-6.0, 45.6, -3.8, 6.0, 47.4, 3.8, VK_DARK, 1.15)
    m.box3d(-6.0, 46.8, 3.6, 6.0, 47.6, 4.1, VK_GOLD, 1.00)

    # Arms
    for side in (-1, 1):
        mu = 1.05 if side < 0 else 0.88
        ux = side * 11.4
        m.box3d(ux - 2.8, 33.0, -2.6, ux + 2.8, 44.0, 2.6, VK_PLATE, mu)
        m.box3d(ux - 3.1, 31.6, -2.9, ux + 3.1, 34.0, 2.9, VK_PLATE, mu * 1.14)
        if side > 0:
            m.box3d(12.4, 26.0, -2.2, 17.2, 33.0, 2.2, VK_PLATE, mu * 0.95)
            m.box3d(14.0, 25.2, -2.4, 18.2, 28.4, 2.4, VK_SKIN, mu * 0.95)
        else:
            m.box3d(-17.0, 28.0, -2.3, -10.2, 33.0, 2.3, VK_PLATE, mu * 0.95)

    # Solar shield on the off arm -- two upright fans in the shield's own
    # XY plane (ring3d lays its ring on the ground plane, which turned it
    # into an ellipse lying on her hip)
    m.push()
    m.translate(-15.5, 29.6, 4.6)
    m.rotate(-16.0, 0, 1, 0)
    for face_r, face_z, face_col, face_mul in ((8.0, 0.0, VK_GOLD, 0.95),
                                               (6.9, 0.45, VK_PLATE, 1.08)):
        for i in range(24):
            a0 = i * 6.2832 / 24.0
            a1 = (i + 1) * 6.2832 / 24.0
            m.tri((0, 0, face_z),
                  (math.cos(a0) * face_r, math.sin(a0) * face_r, face_z),
                  (math.cos(a1) * face_r, math.sin(a1) * face_r, face_z),
                  face_col, face_mul)
    for i in range(8):
        a = i * 0.7854
        m.cube3(math.cos(a) * 4.6, math.sin(a) * 4.6, 0.6, 0.9, VK_GLOW, 0.90)
    m.cube3(0, 0, 0.9, 2.3, VK_GLOW, 1.15)
    m.pop()

    # Neck, head, face
    m.box3d(-2.0, 46.4, -2.0, 2.0, 49.8, 2.0, VK_SKIN, 0.80)
    m.box3d(-5.2, 49.0, -3.5, 5.2, 57.0, 3.5, VK_SKIN, 1.00)
    m.box3d(-5.2, 49.0, -3.5, 5.2, 49.8, 3.6, VK_DARK, 1.00)        # jawline
    m.box3d(-5.2, 54.0, 3.4, 5.2, 55.0, 3.9, 0x8A6638, 1.00)        # brow
    m.box3d(-4.7, 52.2, 3.5, -1.6, 53.8, 4.0, 0x201810, 1.00)       # squared eyes
    m.box3d(1.6, 52.2, 3.5, 4.7, 53.8, 4.0, 0x201810, 1.00)
    m.cube3(0, 52.1, 4.1, 0.8, VK_JADE, 1.10)                       # nose bead
    m.box3d(-1.7, 50.2, 3.5, 1.7, 50.7, 3.8, 0x7A4F28, 1.00)        # mouth
    m.box3d(-4.8, 51.4, 3.5, -2.7, 51.9, 3.9, VK_JADE, 0.95)        # war paint
    m.box3d(2.7, 51.4, 3.5, 4.8, 51.9, 3.9, VK_JADE, 0.80)
    m.box3d(-5.6, 49.6, -3.6, -4.6, 55.4, 3.6, VK_HAIR, 1.30)       # temple hair
    m.box3d(4.6, 49.6, -3.6, 5.6, 55.4, 3.6, VK_HAIR, 1.10)
    m.box3d(-5.3, 49.0, -4.0, 5.3, 56.0, -3.3, VK_HAIR, 1.00)       # back of head

    # Gold diadem with jade studs
    m.box3d(-5.8, 56.2, -3.7, 5.8, 57.8, 3.7, VK_GOLD, 1.06)
    m.cube3(-6.1, 56.8, 0, 1.0, VK_JADE, 1.05)
    m.cube3(6.1, 56.8, 0, 1.0, VK_JADE, 0.88)

    # Winged helm: stepped gold wings off the temples
    for side in (-1, 1):
        for k in range(4):
            x0 = side * (5.4 + k * 2.0)
            x1 = x0 + side * 2.1
            yb = 55.8 + k * 1.3
            hg = 2.6 - k * 0.35
            lo, hi = (x1, x0) if side < 0 else (x0, x1)
            m.box3d(lo, yb, -1.4, hi, yb + hg, 1.4,
                    VK_GLOW if k == 3 else VK_GOLD, 1.0 + k * 0.04)

    # Three-plume headdress
    m.tri((-5.0, 57.8, 0), (-2.2, 57.8, 0), (-9.5 - gust, 71.0, 0), VK_JADE, 1.00)
    m.tri((-4.6, 57.8, 1.4), (-4.6, 57.8, -1.4), (-9.5 - gust, 71.0, 0), VK_JADE, 0.66)
    m.tri((-2.3, 57.8, 0), (2.3, 57.8, 0), (gust * 0.4, 76.0, 0), VK_GLOW, 1.00)
    m.tri((0, 57.8, 1.5), (0, 57.8, -1.5), (gust * 0.4, 76.0, 0), VK_GOLD, 0.78)
    m.tri((2.2, 57.8, 0), (5.0, 57.8, 0), (9.5 + gust, 71.0, 0), VK_JADE, 0.84)
    m.tri((4.6, 57.8, 1.4), (4.6, 57.8, -1.4), (9.5 + gust, 71.0, 0), VK_JADE, 0.56)
    m.cube3(gust * 0.4, 76.0, 0, 1.3, VK_GLOW, 1.40)
    m.cube3(-9.5 - gust, 71.0, 0, 1.0, VK_JADE, 1.15)
    m.cube3(9.5 + gust, 71.0, 0, 1.0, VK_JADE, 1.00)

    # Stepped-pyramid pauldrons, last: they overlap everything
    for side in (-1, 1):
        mu = 1.10 if side < 0 else 0.86
        i0, i1, o1 = side * 8.6, side * 12.8, side * 16.4
        a0, a1 = (i1, i0) if side < 0 else (i0, i1)
        b0, b1 = (o1, i1) if side < 0 else (i1, o1)
        m.box3d(a0, 43.2, -4.4, a1, 47.0, 4.4, VK_DARK, mu * 1.15)
        m.box3d(b0, 40.0, -4.6, b1, 44.0, 4.6, VK_DARK, mu * 1.00)
        g0 = o1 - side * 1.6 if side < 0 else o1
        g1 = o1 if side < 0 else o1 + side * 1.6
        m.box3d(g0, 39.6, -4.7, g1, 44.4, 4.7, VK_GOLD, mu)
        j0 = i1 - side * 1.3 if side < 0 else i1
        j1 = i1 if side < 0 else i1 + side * 1.3
        m.box3d(j0, 43.0, -4.5, j1, 47.2, 4.5, VK_JADE, mu)

    # Braid, over the shoulder
    for i in range(6):
        u = i / 5.0
        bx = 4.6 + u * 9.5 + gust * (0.25 + u * 0.9)
        by = 54.0 - u * 14.0
        w = 2.5 - u * 1.2
        m.box3d(bx - w, by - w, -4.4 - u, bx + w, by + w, -1.0 - u * 0.6,
                VK_HAIR, 1.05 + u * 0.20)
    m.cube3(13.0 + gust * 1.15, 39.7, -3.4, 1.3, VK_GOLD, 1.00)

    m.pop()
    return m.build(**bake)
