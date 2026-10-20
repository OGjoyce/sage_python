"""Scourge 3D building models.

Port of drawScourgeBldg3D in src/gfx/models3d/scourge_units.cpp, C++ numbers
verbatim. Units from the same file are in scourge_units.py.

Buildings: Necropolis(0) Crypt(1) Ziggurat(2) TempleOfDamned(3)
           Slaughterhouse(4) Fountain(5) GoldMine(6)
"""

import math

from claude_studio.craftwar_gl import U, GLModel

SC_VOID = 0x1A1428
SC_SHADOW = 0x06050A
SC_BONE = 0xEEE6CC
SC_PLAGUE = 0x40FF80
SC_GOLD = 0xB08020
SC_ROBE = 0x281C40
SC_ROT = 0x304830
SC_RUST = 0x503828

NAMES = ("Necropolis", "Crypt", "Ziggurat", "TempleOfDamned",
         "Slaughterhouse", "Fountain", "GoldMine")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the building, as bldgIdx does in the C++."""
    m = GLModel(name or f"SCOURGE_bldg{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")
    idleP = tickF * 0.6

    if idx == 0:
        # -- 0: NECROPOLIS (Town Hall) ---------------------------------------
        m.box3d(-9.0, 0, -9.0, 9.0, U, 9.0, SC_SHADOW)
        m.box3d(-7.5, U, -7.5, 7.5, 3.0 * U, 7.5, SC_VOID)
        m.box3d(-5.5, 3.0 * U, -5.5, 5.5, 6.0 * U, 5.5, SC_VOID)
        m.box3d(-3.0, 6.0 * U, -3.0, 3.0, 10.0 * U, 3.0, SC_VOID)
        m.box3d(-1.0, 10.0 * U, -1.0, 1.0, 13.0 * U, 1.0, SC_SHADOW)
        m.cube3(-8.0, U, -8.0, 0.9, SC_BONE, 1.0)
        m.cube3(8.0, U, -8.0, 0.9, SC_BONE, 1.0)
        m.cube3(-8.0, U, 8.0, 0.9, SC_BONE, 1.0)
        m.cube3(8.0, U, 8.0, 0.9, SC_BONE, 1.0)
        colH = 4.0 + math.sin(idleP) * 2.0
        m.box3d(-0.5, 0, -0.5, 0.5, colH * U, 0.5, SC_PLAGUE, 0.7)
        m.cube3(0, colH * U, 0, 1.2 + 0.5 * math.sin(idleP * 2.0), SC_PLAGUE, 0.6)
        m.box3d(-3.5, 0, -10.0, 3.5, 5.5 * U, -8.5, SC_VOID)
        m.box3d(-4.0, 5.5 * U, -10.5, 4.0, 7.0 * U, -8.0, SC_BONE)

    elif idx == 1:
        # -- 1: CRYPT (Barracks) ---------------------------------------------
        m.box3d(-8.0, 0, -6.0, 8.0, 0.8 * U, 6.0, SC_SHADOW)
        m.box3d(-7.0, 0.8 * U, -5.0, 7.0, 4.5 * U, 5.0, SC_VOID)
        m.box3d(-8.0, 4.5 * U, -6.5, 8.0, 5.5 * U, 6.5, SC_SHADOW)
        m.box3d(-0.4, 1.5 * U, -5.2, 0.4, 4.0 * U, -4.8, SC_BONE)
        m.box3d(-1.5, 2.5 * U, -5.2, 1.5, 3.0 * U, -4.8, SC_BONE)
        for s in range(-6, 7, 4):
            m.box3d(s - 1.0, 0, -5.5, s + 1.0, 3.5 * U, -4.8, SC_SHADOW)
            m.box3d(s - 1.0, 0, 4.8, s + 1.0, 3.5 * U, 5.5, SC_SHADOW)
        m.box3d(-2.5, 0.8 * U, -5.5, 2.5, 3.5 * U, -4.0, SC_SHADOW)
        m.cube3(0, 3.0 * U, -5.0, 0.6 + 0.3 * math.sin(idleP * 2.0), SC_PLAGUE, 0.5)

    elif idx == 2:
        # -- 2: ZIGGURAT (Farm -- step pyramid) ------------------------------
        m.box3d(-8.0, 0, -8.0, 8.0, 2.0 * U, 8.0, SC_VOID)
        m.box3d(-5.5, 2.0 * U, -5.5, 5.5, 4.0 * U, 5.5, SC_SHADOW)
        m.box3d(-3.0, 4.0 * U, -3.0, 3.0, 6.0 * U, 3.0, SC_VOID)
        m.box3d(-8.5, 2.0 * U, -8.5, 8.5, 2.3 * U, 8.5, SC_BONE, 0.8)
        m.box3d(-6.0, 4.0 * U, -6.0, 6.0, 4.3 * U, 6.0, SC_BONE, 0.8)
        m.cube3(0, 7.0 * U, 0, 0.9 + 0.4 * math.sin(idleP), SC_PLAGUE, 0.7)
        m.cube3(-8.0, 0.2 * U, -8.0, 0.8, SC_BONE, 1.0)
        m.cube3(8.0, 0.2 * U, -8.0, 0.8, SC_BONE, 1.0)
        m.cube3(-8.0, 0.2 * U, 8.0, 0.8, SC_BONE, 1.0)
        m.cube3(8.0, 0.2 * U, 8.0, 0.8, SC_BONE, 1.0)

    elif idx == 3:
        # -- 3: TEMPLE OF THE DAMNED (Mage Tower) ----------------------------
        m.box3d(-4.0, 0, -4.0, 4.0, 15.0 * U, 4.0, SC_VOID)
        for sp in range(4):
            sa = sp * 1.57
            sx, sz = 3.5 * math.cos(sa), 3.5 * math.sin(sa)
            m.box3d(sx - 0.5, 12.0 * U, sz - 0.5, sx + 0.5, 18.0 * U, sz + 0.5, SC_BONE)
        m.box3d(-4.2, 4.0 * U, -0.8, -3.8, 6.0 * U, 0.8, SC_PLAGUE, 0.7)
        m.box3d(-4.2, 8.0 * U, -0.8, -3.8, 10.0 * U, 0.8, SC_PLAGUE, 0.7)
        m.box3d(3.8, 4.0 * U, -0.8, 4.2, 6.0 * U, 0.8, SC_PLAGUE, 0.7)
        m.box3d(3.8, 8.0 * U, -0.8, 4.2, 10.0 * U, 0.8, SC_PLAGUE, 0.7)
        for b in range(4):
            ba = b * 1.57 + 0.785
            bx, bz = 5.0 * math.cos(ba), 5.0 * math.sin(ba)
            m.box3d(bx - 0.7, 0, bz - 0.7, bx + 0.7, 8.0 * U, bz + 0.7, SC_BONE, 0.8)
        m.cube3(0, 16.0 * U, 0, 1.3 + 0.5 * math.sin(idleP), SC_PLAGUE, 0.7)

    elif idx == 4:
        # -- 4: SLAUGHTERHOUSE (Workshop) ------------------------------------
        m.box3d(-8.0, 0, -7.0, 8.0, 0.8 * U, 7.0, SC_SHADOW)
        m.box3d(-8.0, 0, -7.5, 8.0, 6.0 * U, -6.5, SC_VOID)
        m.box3d(-8.5, 0, -7.0, -7.5, 6.0 * U, 7.0, SC_VOID)
        m.box3d(7.5, 0, -7.0, 8.5, 6.0 * U, 7.0, SC_VOID)
        m.box3d(-8.5, 6.0 * U, -7.5, 8.5, 7.0 * U, 7.5, SC_SHADOW)
        for h in range(-6, 7, 3):
            m.box3d(h - 0.15, 4.5 * U, -0.15, h + 0.15, 7.0 * U, 0.15, SC_BONE)
            m.cube3(h, 4.3 * U, 0, 0.4, SC_RUST, 0.9)
        m.box3d(-4.0, 0.8 * U, -6.5, 4.0, 4.0 * U, -5.5, SC_VOID)
        m.cube3(0, 3.5 * U, -6.0, 1.0 + 0.4 * math.sin(idleP * 2.5), SC_PLAGUE, 0.6)

    elif idx == 5:
        # -- 5: FOUNTAIN (Hero spawn) ----------------------------------------
        m.box3d(-5.0, 0, -5.0, 5.0, 1.5 * U, 5.0, SC_VOID)
        m.box3d(-4.0, 1.5 * U, -4.0, 4.0, 2.0 * U, 4.0, SC_SHADOW)
        for b in range(8):
            ba = b * 0.785
            m.cube3(4.8 * math.cos(ba), 1.7 * U, 4.8 * math.sin(ba), 0.7, SC_BONE, 1.0)
        fh = 3.0 + math.sin(idleP) * 1.2
        m.box3d(-0.8, 2.0 * U, -0.8, 0.8, 2.0 * U + fh * U, 0.8, SC_PLAGUE, 0.7)
        m.cube3(0, 2.0 * U + fh * U * 0.5, 0,
                0.7 + 0.3 * math.sin(idleP * 2.0), SC_PLAGUE, 0.6)

    elif idx == 6:
        # -- 6: GOLD MINE (neutral) ------------------------------------------
        m.box3d(-6.5, 0, -6.5, 6.5, 4.5 * U, 6.5, 0x706050)
        m.box3d(-4.5, 4.5 * U, -4.5, 4.5, 6.5 * U, 4.5, 0x706050)
        m.box3d(-2.5, 6.5 * U, -2.5, 2.5, 7.8 * U, 2.5, 0x706050)
        m.box3d(-3.2, 0, -8.0, 3.2, 5.5 * U, -6.0, SC_SHADOW)
        m.box3d(-3.8, 5.5 * U, -8.5, 3.8, 6.5 * U, -5.5, SC_VOID)
        m.cube3(0, 3.5 * U, 0, 0.9 + 0.4 * math.sin(idleP * 3.0), 0xFFD040, 0.7)
        m.box3d(-0.6, 0, -8.5, -0.1, 0.3, -5.5, 0x604030)
        m.box3d(0.1, 0, -8.5, 0.6, 0.3, -5.5, 0x604030)
        m.box3d(-4.5, 0, 5.0, -4.0, 7.5 * U, 5.5, SC_RUST)
        m.box3d(4.0, 0, 5.0, 4.5, 7.5 * U, 5.5, SC_RUST)
        m.box3d(-4.5, 7.0 * U, 5.0, 4.5, 7.5 * U, 5.5, SC_RUST)

    else:
        return None     # the C++ answers an unknown bldgIdx with "return false"

    return m.build(**bake)
