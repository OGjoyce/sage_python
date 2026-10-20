"""Horde 3D building models.

Port of drawHordeBldg3D in src/gfx/models3d/horde_units.cpp, C++ numbers
verbatim. Units from the same file are in horde_units.py.

Buildings: GreatHall(0) WarMill(1) Pigpen(2) SpiritLodge(3) SiegeWorks(4)
           Fountain(5) GoldMine(6)
"""

import math

from claude_studio.craftwar_gl import U, GLModel

HR_GREEN = 0x6E8A3A
HR_DARK = 0x3A4E1E
HR_BONE = 0xDCC8A0
HR_GLOW = 0xFF8040
HR_IRON = 0x5A5840
HR_RUST = 0x805030
HR_TUSK = 0xF0E0B0
HR_CLOTH = 0x806040

NAMES = ("GreatHall", "WarMill", "Pigpen", "SpiritLodge", "SiegeWorks",
         "Fountain", "GoldMine")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the building, as bldgIdx does in the C++."""
    m = GLModel(name or f"HORDE_bldg{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")
    idleP = tickF * 0.6

    if idx == 0:
        # -- 0: GREAT HALL (Town Hall) ---------------------------------------
        m.box3d(-8.5, 0, -8.5, 8.5, U, 8.5, HR_DARK)
        m.box3d(-7.5, U, -7.5, 7.5, 7.5 * U, 7.5, HR_IRON)
        for i in range(4):
            sy = U + i * 1.8 * U
            m.box3d(-7.7, sy, -7.7, 7.7, sy + 0.3, 7.7, HR_DARK)
        for s in (-1, 0, 1):
            m.cube3(s * 4.0, 8.0 * U, -7.5, 0.85, HR_BONE, 1.0)
        m.box3d(-10.0, 0, -2.5, -8.0, 10.0 * U, 2.5, HR_RUST)
        m.box3d(-10.5, 9.0 * U, -2.0, -7.5, 10.5 * U, 2.0, HR_BONE)
        m.box3d(8.0, 0, -2.5, 10.0, 10.0 * U, 2.5, HR_RUST)
        m.box3d(7.5, 9.0 * U, -2.0, 10.5, 10.5 * U, 2.0, HR_BONE)
        m.box3d(-3.2, U, -9.0, 3.2, 4.5 * U, -7.5, HR_DARK)
        m.box3d(-3.5, 4.5 * U, -9.5, 3.5, 5.5 * U, -7.0, HR_IRON)
        m.cube3(0, 4.5 * U, 0, 1.8 + 0.6 * math.sin(idleP), HR_GLOW, 0.5)

    elif idx == 1:
        # -- 1: WAR MILL (Barracks) ------------------------------------------
        m.box3d(-8.5, 0, -5.5, 8.5, 0.9 * U, 5.5, HR_DARK)
        m.box3d(-8.0, 0.9 * U, -5.0, 8.0, 6.5 * U, 5.0, HR_IRON)
        for b in range(-6, 7, 3):
            m.box3d(b - 0.4, 0, -5.6, b + 0.4, 7.0 * U, 5.6, HR_DARK)
        m.box3d(-8.6, 6.5 * U, -5.6, 8.6, 7.8 * U, 5.6, HR_DARK)
        for sp in range(-7, 8, 2):
            m.box3d(sp - 0.4, 7.8 * U, -0.4, sp + 0.4, 9.4 * U, 0.4, HR_BONE)
        for r in (-1, 1):
            rx = r * 9.2
            m.box3d(rx - 0.5, 0.9 * U, -4.0, rx + 0.5, 5.5 * U, 4.0, HR_RUST)
            for w in range(-3, 4, 2):
                m.box3d(rx - 0.3, 2.0 * U, w - 0.15, rx + 0.3, 6.0 * U, w + 0.15, HR_IRON)
        m.box3d(-0.4, 7.5 * U, -0.4, 0.4, 11.0 * U, 0.4, HR_BONE)
        m.box3d(-0.3, 8.5 * U, -3.0, 0.3, 11.0 * U, -0.3, HR_GLOW)

    elif idx == 2:
        # -- 2: PIGPEN (Farm) ------------------------------------------------
        m.box3d(-7.5, 0, -6.5, 7.5, 0.5 * U, 6.5, HR_RUST)
        for px in (-7.5, -3.7, 0.0, 3.7, 7.5):
            m.box3d(px - 0.4, 0, -7.0, px + 0.4, 2.8 * U, 7.0, HR_RUST)
        m.box3d(-8.0, 1.8 * U, -7.0, 8.0, 2.3 * U, -6.0, HR_RUST)
        m.box3d(-8.0, 1.8 * U, 6.0, 8.0, 2.3 * U, 7.0, HR_RUST)
        m.box3d(-5.5, 0, 3.5, 5.5, 4.5 * U, 7.0, HR_DARK)
        m.box3d(-6.0, 4.5 * U, 3.0, 6.0, 6.0 * U, 7.5, HR_RUST)
        m.box3d(-3.0, 0.5 * U, -4.5, 3.0, 1.8 * U, -2.5, HR_DARK)
        m.cube3(-2.5, 0.9 * U, 0.5, 0.9, HR_BONE, 1.0)
        m.cube3(2.0, 0.9 * U, -1.0, 0.9, HR_BONE, 1.0)

    elif idx == 3:
        # -- 3: SPIRIT LODGE (Mage Tower) ------------------------------------
        m.box3d(-4.5, 0, -4.5, 4.5, 13.0 * U, 4.5, HR_DARK)
        for t in range(3):
            ty = 2.0 * U + t * 3.6 * U
            m.box3d(-5.0, ty, -5.0, 5.0, ty + 2.2 * U, 5.0, HR_RUST)
            m.box3d(-5.5, ty + 1.0 * U, -1.5, -4.0, ty + 2.0 * U, 1.5, HR_BONE)
            m.box3d(4.0, ty + 1.0 * U, -1.5, 5.5, ty + 2.0 * U, 1.5, HR_BONE)
        m.box3d(-5.5, 13.0 * U, -5.5, 5.5, 14.5 * U, 5.5, HR_DARK)
        g = 1.6 + 0.5 * math.sin(idleP)
        m.cube3(0, 15.3 * U, 0, g, HR_GLOW, 0.7)
        oa = tickF * 1.5
        m.cube3(4.5 * math.cos(oa), 15.3 * U, 4.5 * math.sin(oa), 0.45, HR_GLOW, 0.6)
        m.cube3(4.5 * math.cos(oa + 2.1), 15.3 * U, 4.5 * math.sin(oa + 2.1),
                0.45, HR_GLOW, 0.55)
        m.cube3(4.5 * math.cos(oa - 2.1), 15.3 * U, 4.5 * math.sin(oa - 2.1),
                0.45, HR_GLOW, 0.55)

    elif idx == 4:
        # -- 4: SIEGE WORKS (Workshop) ---------------------------------------
        m.box3d(-8.5, 0, -7.5, 8.5, 0.9 * U, 7.5, HR_IRON)
        m.box3d(-8.5, 0, -8.0, 8.5, 5.5 * U, -7.0, HR_IRON)
        m.box3d(-9.0, 0, -7.5, -8.0, 5.5 * U, 7.5, HR_IRON)
        m.box3d(8.0, 0, -7.5, 9.0, 5.5 * U, 7.5, HR_IRON)
        m.box3d(-4.5, 0.9 * U, -7.0, 4.5, 4.5 * U, -5.5, HR_DARK)
        m.cube3(0, 3.5 * U, -6.0, 1.1 + 0.4 * math.sin(idleP * 3.0), HR_GLOW, 0.65)
        m.box3d(-2.0, 0.9 * U, -2.0, 2.0, 2.8 * U, 2.0, HR_IRON)
        m.box3d(-1.5, 2.8 * U, -3.2, 1.5, 3.5 * U, 3.2, HR_DARK)
        for c in range(-6, 7, 4):
            m.box3d(c - 0.15, 2.5 * U, -0.15, c + 0.15, 5.5 * U, 0.15, HR_IRON)
        m.box3d(-9.0, 5.5 * U, -8.0, 9.0, 6.5 * U, 8.0, HR_DARK)

    elif idx == 5:
        # -- 5: FOUNTAIN (Hero spawn) ----------------------------------------
        m.box3d(-5.5, 0, -5.5, 5.5, 1.8 * U, 5.5, HR_DARK)
        m.box3d(-4.5, 1.8 * U, -4.5, 4.5, 2.3 * U, 4.5, HR_RUST)
        fh = 3.2 + math.sin(idleP) * 1.5
        m.box3d(-0.9, 2.3 * U, -0.9, 0.9, 2.3 * U + fh * U, 0.9, HR_GLOW)
        m.cube3(0, 2.3 * U + fh * U * 0.5, 0,
                0.65 + 0.3 * math.sin(idleP * 2.0), HR_GLOW, 0.6)
        for sk in range(4):
            a = sk * 1.57
            m.cube3(5.0 * math.cos(a), 2.0 * U, 5.0 * math.sin(a), 0.75, HR_BONE, 1.0)

    elif idx == 6:
        # -- 6: GOLD MINE (neutral) ------------------------------------------
        m.box3d(-6.5, 0, -6.5, 6.5, 4.5 * U, 6.5, 0x706050)
        m.box3d(-4.5, 4.5 * U, -4.5, 4.5, 6.5 * U, 4.5, 0x706050)
        m.box3d(-2.5, 6.5 * U, -2.5, 2.5, 7.8 * U, 2.5, 0x706050)
        m.box3d(-3.2, 0, -8.0, 3.2, 5.5 * U, -6.0, HR_DARK)
        m.box3d(-3.8, 5.5 * U, -8.5, 3.8, 6.5 * U, -5.5, HR_DARK)
        m.cube3(0, 3.5 * U, 0, 0.9 + 0.4 * math.sin(idleP * 3.0), 0xFFD040, 0.7)
        m.box3d(-0.6, 0, -8.5, -0.1, 0.3, -5.5, 0x604030)
        m.box3d(0.1, 0, -8.5, 0.6, 0.3, -5.5, 0x604030)
        m.box3d(-4.5, 0, 5.0, -4.0, 7.5 * U, 5.5, HR_RUST)
        m.box3d(4.0, 0, 5.0, 4.5, 7.5 * U, 5.5, HR_RUST)
        m.box3d(-4.5, 7.0 * U, 5.0, 4.5, 7.5 * U, 5.5, HR_RUST)

    else:
        return None     # the C++ answers an unknown bldgIdx with "return false"

    return m.build(**bake)
