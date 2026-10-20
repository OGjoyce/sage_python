"""Elf (Sentinel) 3D building models.

Port of drawElfBldg3D in src/gfx/models3d/elf_units.cpp, C++ numbers verbatim.
Units from the same file are in elf_units.py.

Buildings: TreeOfLife(0) HuntersHall(1) MoonWell(2) AncientOfWonders(3)
           WoodWorkshop(4) Fountain(5) GoldMine(6)
"""

import math

from claude_studio.craftwar_gl import U, GLModel

EL_FERN = 0x3C5028
EL_DARK = 0x0A140C
EL_BARK = 0x506030
EL_GLOW = 0x90E8A0
EL_MOON = 0xD0FFE0
EL_WISP = 0x70C8FF
EL_SILVER = 0xC0D0C8
EL_LEAF = 0x60A840

NAMES = ("TreeOfLife", "HuntersHall", "MoonWell", "AncientOfWonders",
         "WoodWorkshop", "Fountain", "GoldMine")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the building, as bldgIdx does in the C++."""
    m = GLModel(name or f"ELF_bldg{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")
    idleP = tickF * 0.6

    if idx == 0:
        # -- 0: TREE OF LIFE (Town Hall) -------------------------------------
        # Massive ancient trunk
        m.box3d(-5.0, 0, -5.0, 5.0, 10.0 * U, 5.0, EL_BARK)
        m.box3d(-3.0, 10.0 * U, -3.0, 3.0, 14.0 * U, 3.0, EL_BARK)
        # Buttress roots
        for r in range(4):
            ra = r * 1.57 + 0.785
            rx, rz = 6.5 * math.cos(ra), 6.5 * math.sin(ra)
            m.box3d(rx - 1.0, 0, rz - 1.0, rx + 1.0, 5.0 * U, rz + 1.0, EL_BARK)
        # Leaf clusters in branches
        for b in range(6):
            ba = b * 1.047
            bx, bz = 5.0 * math.cos(ba), 5.0 * math.sin(ba)
            m.box3d(bx - 1.5, 10.0 * U, bz - 1.5, bx + 1.5, 13.0 * U, bz + 1.5,
                    EL_LEAF, 0.9)
        m.box3d(-4.0, 12.0 * U, -4.0, 4.0, 16.0 * U, 4.0, EL_LEAF, 0.85)
        # Glowing heartwood core
        glow = 1.0 + 0.4 * math.sin(idleP)
        m.cube3(0, 8.0 * U, 0, glow, EL_GLOW, 0.55)
        # Canopy tip glow
        m.cube3(0, 16.5 * U, 0, 1.2 + 0.5 * math.sin(idleP * 1.5), EL_MOON, 0.7)

    elif idx == 1:
        # -- 1: HUNTER'S HALL (Barracks) -------------------------------------
        # Long wooden longhouse
        m.box3d(-8.0, 0, -5.0, 8.0, 5.0 * U, 5.0, EL_BARK)
        # Log pillars
        for p in range(-6, 7, 4):
            m.box3d(p - 0.5, 0, -5.5, p + 0.5, 6.5 * U, 5.5, EL_DARK)
        # Peaked leaf-thatched roof
        m.box3d(-8.5, 5.0 * U, -5.5, 8.5, 7.5 * U, 5.5, EL_LEAF)
        m.box3d(-8.0, 7.5 * U, -4.5, 8.0, 9.0 * U, 4.5, EL_FERN)
        m.box3d(-7.0, 9.0 * U, -3.0, 7.0, 10.0 * U, 3.0, EL_BARK)
        # Antler trophy above entrance
        m.box3d(-0.4, 5.0 * U, -5.8, 0.4, 6.5 * U, -5.0, EL_BARK)
        m.push()
        m.rotate(-30.0, 0, 0, 1)
        m.box3d(-4.0, 5.5 * U, -5.5, -1.5, 6.0 * U, -5.0, EL_BARK)
        m.pop()
        m.push()
        m.rotate(30.0, 0, 0, 1)
        m.box3d(1.5, 5.5 * U, -5.5, 4.0, 6.0 * U, -5.0, EL_BARK)
        m.pop()
        # Bow rack on side
        m.box3d(-9.5, 0.5 * U, -4.0, -8.5, 5.0 * U, 4.0, EL_DARK)
        for b in range(-3, 4, 2):
            m.box3d(-9.8, 1.5 * U, b - 0.15, -8.2, 5.0 * U, b + 0.15, EL_MOON)

    elif idx == 2:
        # -- 2: MOON WELL (Farm) ---------------------------------------------
        # Circular stone well surround
        for p in range(8):
            pa = p * 0.785
            px, pz = 5.5 * math.cos(pa), 5.5 * math.sin(pa)
            m.box3d(px - 1.0, 0, pz - 1.0, px + 1.0, 3.0 * U, pz + 1.0, EL_SILVER)
        m.box3d(-5.0, 0, -5.0, 5.0, 1.5 * U, 5.0, EL_BARK)
        # Glowing water pool
        m.box3d(-4.0, 1.5 * U, -4.0, 4.0, 2.2 * U, 4.0, EL_GLOW, 0.7)
        m.cube3(0, 2.0 * U, 0, 1.5 + 0.5 * math.sin(idleP), EL_MOON, 0.6)
        # Willow tendrils hanging
        for t in range(4):
            ta = t * 1.57
            tx, tz = 4.5 * math.cos(ta), 4.5 * math.sin(ta)
            m.box3d(tx - 0.3, 3.0 * U, tz - 0.3, tx + 0.3, 7.5 * U, tz + 0.3,
                    EL_FERN, 0.8)
        # Moon arch above well
        m.box3d(-0.5, 0, -0.5, 0.5, 9.0 * U, 0.5, EL_SILVER)
        m.cube3(0, 9.5 * U, 0, 0.9 + 0.3 * math.sin(idleP * 2.0), EL_MOON, 0.75)

    elif idx == 3:
        # -- 3: ANCIENT OF WONDERS (Mage Tower) ------------------------------
        # Gnarled ancient tree trunk
        m.box3d(-4.5, 0, -4.5, 4.5, 11.0 * U, 4.5, EL_DARK)
        # Twisted branch arm (animating)
        branchSway = math.sin(idleP * 0.7) * 5.0
        m.push()
        m.translate(4.5, 9.0 * U, 0)
        m.rotate(30.0 + branchSway, 0, 0, 1)
        m.box3d(0.0, -0.8, -0.8, 5.0, 0.8, 0.8, EL_BARK)
        m.pop()
        m.push()
        m.translate(-4.5, 9.0 * U, 0)
        m.rotate(-30.0 - branchSway, 0, 0, 1)
        m.box3d(-5.0, -0.8, -0.8, 0.0, 0.8, 0.8, EL_BARK)
        m.pop()
        # Glowing ancient eyes
        m.cube3(-1.5, 7.0 * U, -4.6, 0.5, EL_GLOW, 0.85)
        m.cube3(1.5, 7.0 * U, -4.6, 0.5, EL_GLOW, 0.85)
        # Magical orbs in branches
        oa = tickF * 1.2
        m.cube3(5.5 * math.cos(oa), 10.0 * U, 5.5 * math.sin(oa), 0.6, EL_MOON, 0.7)
        m.cube3(5.5 * math.cos(oa + 2.094), 10.0 * U, 5.5 * math.sin(oa + 2.094),
                0.6, EL_GLOW, 0.7)
        m.cube3(5.5 * math.cos(oa + 4.189), 10.0 * U, 5.5 * math.sin(oa + 4.189),
                0.6, EL_WISP, 0.65)
        # Leaf cluster crown
        m.box3d(-5.0, 11.0 * U, -5.0, 5.0, 14.0 * U, 5.0, EL_LEAF, 0.85)
        m.box3d(-3.0, 14.0 * U, -3.0, 3.0, 16.5 * U, 3.0, EL_FERN, 0.9)

    elif idx == 4:
        # -- 4: WOOD WORKSHOP ------------------------------------------------
        # Treehouse platform
        for p in range(4):
            pa = p * 1.57
            px = 6.0 * math.cos(pa + 0.785)
            pz = 6.0 * math.sin(pa + 0.785)
            m.box3d(px - 0.7, 0, pz - 0.7, px + 0.7, 5.0 * U, pz + 0.7, EL_DARK)
        m.box3d(-7.0, 5.0 * U, -6.0, 7.0, 6.0 * U, 6.0, EL_BARK)      # platform floor
        m.box3d(-6.0, 6.0 * U, -5.0, 6.0, 9.5 * U, 5.0, EL_BARK)      # workshop walls
        m.box3d(-6.5, 9.5 * U, -5.5, 6.5, 11.0 * U, 5.5, EL_LEAF)     # leaf roof
        # Tools hanging
        for t in range(-4, 5, 4):
            m.box3d(t - 0.15, 8.5 * U, -0.15, t + 0.15, 11.0 * U, 0.15, EL_SILVER)
        # Workbench
        m.box3d(-3.0, 6.0 * U, -3.0, 3.0, 7.5 * U, 3.0, EL_BARK)
        # Wood shavings glow (heartwood in use)
        m.cube3(0, 7.5 * U, -2.0, 0.5 + 0.3 * math.sin(idleP * 2.0), EL_GLOW, 0.6)

    elif idx == 5:
        # -- 5: FOUNTAIN (Hero spawn -- moonlit) -----------------------------
        m.box3d(-5.5, 0, -5.5, 5.5, 1.5 * U, 5.5, EL_SILVER)
        m.box3d(-4.5, 1.5 * U, -4.5, 4.5, 2.0 * U, 4.5, EL_BARK)
        # Moon column
        m.box3d(-0.5, 2.0 * U, -0.5, 0.5, 6.0 * U, 0.5, EL_SILVER)
        # Crescent moon orb on top
        fh = 2.5 + math.sin(idleP) * 0.8
        m.cube3(0, 6.0 * U, 0, fh * 0.4, EL_MOON, 0.8)
        # Leaf vines on pillar
        for lf in range(4):
            la = lf * 1.57 + tickF * 0.5
            m.cube3(0.8 * math.cos(la), (2.0 + lf) * U, 0.8 * math.sin(la),
                    0.4, EL_LEAF, 0.8)
        # Pool glow
        m.box3d(-4.0, 1.5 * U, -4.0, 4.0, 2.0 * U, 4.0, EL_GLOW, 0.5)

    elif idx == 6:
        # -- 6: GOLD MINE (neutral) ------------------------------------------
        m.box3d(-6.5, 0, -6.5, 6.5, 4.5 * U, 6.5, 0x706050)
        m.box3d(-4.5, 4.5 * U, -4.5, 4.5, 6.5 * U, 4.5, 0x706050)
        m.box3d(-2.5, 6.5 * U, -2.5, 2.5, 7.8 * U, 2.5, 0x706050)
        m.box3d(-3.2, 0, -8.0, 3.2, 5.5 * U, -6.0, EL_DARK)
        m.box3d(-3.8, 5.5 * U, -8.5, 3.8, 6.5 * U, -5.5, EL_BARK)
        m.cube3(0, 3.5 * U, 0, 0.9 + 0.4 * math.sin(idleP * 3.0), 0xFFD040, 0.7)
        m.box3d(-0.6, 0, -8.5, -0.1, 0.3, -5.5, 0x604030)
        m.box3d(0.1, 0, -8.5, 0.6, 0.3, -5.5, 0x604030)
        m.box3d(-4.5, 0, 5.0, -4.0, 7.5 * U, 5.5, EL_BARK)
        m.box3d(4.0, 0, 5.0, 4.5, 7.5 * U, 5.5, EL_BARK)
        m.box3d(-4.5, 7.0 * U, 5.0, 4.5, 7.5 * U, 5.5, EL_BARK)

    else:
        return None     # the C++ answers an unknown bldgIdx with "return false"

    return m.build(**bake)
