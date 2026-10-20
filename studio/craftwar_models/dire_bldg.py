"""Dire (Legion of Chaos) 3D building models.

Port of drawDireBldg3D in src/gfx/models3d/dire_units.cpp, C++ numbers
verbatim. Units from the same file are in dire_units.py.

Buildings: DemonGate(0) BloodPit(1) SoulFarm(2) FelSanctum(3)
           InfernalForge(4) Fountain(5) GoldMine(6)
"""

import math

from claude_studio.craftwar_gl import U, GLModel

DR_TEAL = 0x20B0A8
DR_DEEP = 0x0E5450
DR_GLOW = 0x60F0F0
DR_BONE = 0xD8CCA4
DR_FLESH = 0x1A1020
DR_HORN = 0x401010
DR_STONE = 0x484050
DR_FEL = 0x30F060

NAMES = ("DemonGate", "BloodPit", "SoulFarm", "FelSanctum",
         "InfernalForge", "Fountain", "GoldMine")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the building, as bldgIdx does in the C++. anim is accepted
    and ignored, as in the C++ -- buildings have no animation state."""
    m = GLModel(name or f"DIRE_bldg{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")
    idleP = tickF * 0.6

    if idx == 0:
        # -- 0: DEMON GATE (Town Hall) ---------------------------------------
        # Two massive obelisk pillars
        m.box3d(-10.0, 0, -3.0, -6.0, 14.0 * U, 3.0, DR_STONE)
        m.box3d(6.0, 0, -3.0, 10.0, 14.0 * U, 3.0, DR_STONE)
        # Spike accents on pillars
        for s in range(5):
            sy = 3.0 * U + s * 2.0 * U
            m.box3d(-11.0, sy, -1.0, -10.0, sy + U, 1.0, DR_TEAL)
            m.box3d(10.0, sy, -1.0, 11.0, sy + U, 1.0, DR_TEAL)
        # Arch at top connecting pillars
        m.box3d(-6.0, 14.0 * U, -3.0, 6.0, 15.5 * U, 3.0, DR_STONE)
        m.box3d(-6.0, 15.5 * U, -2.0, 6.0, 17.0 * U, 2.0, DR_TEAL)
        # Glowing fel portal between pillars
        portalPulse = 1.5 + 0.5 * math.sin(idleP * 2.0)
        m.box3d(-5.5, 0, -2.0, 5.5, 14.0 * U, 2.0, DR_GLOW, 0.35 * portalPulse)
        m.box3d(-4.0, 2.0 * U, -2.5, 4.0, 12.0 * U, 2.5, DR_FEL, 0.25)
        # Skull totem at top
        m.cube3(0, 15.0 * U, -2.5, 1.2, DR_BONE, 1.0)

    elif idx == 1:
        # -- 1: BLOOD PIT (Barracks) -----------------------------------------
        # Sunken arena rim
        m.box3d(-9.0, 0, -9.0, 9.0, 1.5 * U, 9.0, DR_STONE)
        m.box3d(-8.0, 0, -8.0, 8.0, 0.0, 8.0, 0x200010)      # pit floor
        # Bone spike rim
        for sp in range(8):
            spa = sp * 0.785
            spx, spz = 9.0 * math.cos(spa), 9.0 * math.sin(spa)
            m.box3d(spx - 0.6, 1.5 * U, spz - 0.6, spx + 0.6, 3.5 * U, spz + 0.6, DR_BONE)
        # Glow from inside pit
        m.cube3(0, 0.5 * U, 0, 2.5 + 0.8 * math.sin(idleP), DR_GLOW, 0.4)
        m.cube3(0, 0.5 * U, 0, 3.0 + math.sin(idleP * 1.7), 0xFF0040, 0.2)
        # Iron gate at entrance
        m.box3d(-3.5, 0, -9.5, 3.5, 4.0 * U, -8.5, DR_STONE)
        for g in range(-2, 3):
            m.box3d(g - 0.25, 0.5 * U, -9.6, g + 0.25, 3.5 * U, -8.4, DR_TEAL)

    elif idx == 2:
        # -- 2: SOUL FARM (Farm) ---------------------------------------------
        # Twisted dark building
        m.box3d(-7.0, 0, -6.0, 7.0, 0.8 * U, 6.0, DR_STONE)
        m.box3d(-6.0, 0.8 * U, -5.0, 6.0, 5.0 * U, 5.0, DR_FLESH)
        # Jagged roof
        m.box3d(-7.0, 5.0 * U, -6.0, 7.0, 6.0 * U, 6.0, DR_DEEP)
        for jp in range(-6, 7, 3):
            m.box3d(jp - 0.5, 6.0 * U, -0.5, jp + 0.5, 7.5 * U, 0.5, DR_BONE)
        # Soul cages hanging on sides
        for c in range(-5, 6, 5):
            m.box3d(c - 0.15, 4.0 * U, 6.35, c + 0.15, 6.0 * U, 6.65, DR_TEAL)
            m.cube3(c, 3.5 * U, 6.5, 0.6, DR_BONE, 0.8)
            m.cube3(c, 3.5 * U, 6.5, 0.35, DR_GLOW, 0.7)    # soul inside
        # Fel glow inside
        m.cube3(0, 3.0 * U, 0, 1.2 + 0.5 * math.sin(idleP * 2.0), DR_GLOW, 0.4)

    elif idx == 3:
        # -- 3: FEL SANCTUM (Mage Tower) -------------------------------------
        # Jagged fel spire -- asymmetric chaos geometry
        m.box3d(-3.0, 0, -3.0, 3.0, 14.0 * U, 3.0, DR_STONE)
        # Extra jutting shards
        m.push()
        m.rotate(15.0, 0, 0, 1)
        m.box3d(-1.0, 8.0 * U, -8.0, 1.0, 10.0 * U, 0.0, DR_TEAL, 0.9)
        m.pop()
        m.push()
        m.rotate(-20.0, 0, 1, 0)
        m.box3d(-8.0, 6.0 * U, -1.0, 0.0, 8.0 * U, 1.0, DR_STONE)
        m.pop()
        # Glowing seams
        for s in range(4):
            sa = s * 1.57
            sx, sz = 3.0 * math.cos(sa), 3.0 * math.sin(sa)
            m.box3d(sx - 0.25, 0, sz - 0.25, sx + 0.25, 14.0 * U, sz + 0.25, DR_GLOW, 0.6)
        # Apex fel orb
        ag = 1.4 + 0.5 * math.sin(idleP)
        m.cube3(0, 15.5 * U, 0, ag, DR_GLOW, 0.75)
        m.cube3(0, 15.5 * U, 0, ag * 0.5, DR_FEL, 0.7)
        # Orbiting shards
        oa = tickF * 2.0
        m.cube3(5.0 * math.cos(oa), 15.5 * U, 5.0 * math.sin(oa), 0.5, DR_TEAL, 0.65)
        m.cube3(5.0 * math.cos(oa + 3.14), 15.5 * U, 5.0 * math.sin(oa + 3.14),
                0.5, DR_GLOW, 0.65)

    elif idx == 4:
        # -- 4: INFERNAL FORGE (Workshop) ------------------------------------
        m.box3d(-8.5, 0, -7.5, 8.5, 0.8 * U, 7.5, DR_STONE)
        m.box3d(-8.5, 0, -8.0, 8.5, 6.0 * U, -7.0, DR_STONE)
        m.box3d(-9.0, 0, -7.5, -8.0, 6.0 * U, 7.5, DR_STONE)
        m.box3d(8.0, 0, -7.5, 9.0, 6.0 * U, 7.5, DR_STONE)
        m.box3d(-9.0, 6.0 * U, -8.0, 9.0, 7.0 * U, 8.0, DR_DEEP)
        # Fel forge at back -- glowing magma
        m.box3d(-5.0, 0.8 * U, -7.0, 5.0, 4.5 * U, -5.5, DR_STONE)
        m.cube3(0, 3.5 * U, -6.0, 1.3 + 0.5 * math.sin(idleP * 3.0), DR_GLOW, 0.7)
        m.cube3(0, 3.5 * U, -6.0, 0.7 + 0.3 * math.sin(idleP * 3.0), 0xFF6000, 0.6)
        # Chains hanging
        for c in range(-6, 7, 4):
            m.box3d(c - 0.15, 4.0 * U, -0.15, c + 0.15, 7.0 * U, 0.15, DR_BONE)
            m.cube3(c, 3.8 * U, 0, 0.45, DR_TEAL, 0.85)
        # Anvil of fel steel
        m.box3d(-2.5, 0.8 * U, -2.5, 2.5, 3.0 * U, 2.5, DR_DEEP)
        m.box3d(-2.0, 3.0 * U, -3.0, 2.0, 3.8 * U, 3.0, DR_TEAL)

    elif idx == 5:
        # -- 5: FOUNTAIN (Hero spawn -- fel) ---------------------------------
        m.box3d(-5.5, 0, -5.5, 5.5, 1.8 * U, 5.5, DR_STONE)
        m.box3d(-4.5, 1.8 * U, -4.5, 4.5, 2.3 * U, 4.5, DR_DEEP)
        # Bone rim spikes
        for sk in range(6):
            sa = sk * 1.047
            m.cube3(5.3 * math.cos(sa), 2.1 * U, 5.3 * math.sin(sa), 0.6, DR_BONE, 1.0)
        # Fel teal energy column
        fh = 3.0 + math.sin(idleP) * 1.3
        m.box3d(-0.8, 2.3 * U, -0.8, 0.8, 2.3 * U + fh * U, 0.8, DR_GLOW, 0.7)
        m.cube3(0, 2.3 * U + fh * U * 0.5, 0,
                0.7 + 0.3 * math.sin(idleP * 2.0), DR_GLOW, 0.65)
        m.cube3(0, 2.3 * U + fh * U * 0.5, 0,
                0.4 + 0.15 * math.sin(idleP * 2.0), DR_FEL, 0.6)

    elif idx == 6:
        # -- 6: GOLD MINE (neutral) ------------------------------------------
        m.box3d(-6.5, 0, -6.5, 6.5, 4.5 * U, 6.5, 0x706050)
        m.box3d(-4.5, 4.5 * U, -4.5, 4.5, 6.5 * U, 4.5, 0x706050)
        m.box3d(-2.5, 6.5 * U, -2.5, 2.5, 7.8 * U, 2.5, 0x706050)
        m.box3d(-3.2, 0, -8.0, 3.2, 5.5 * U, -6.0, DR_STONE)
        m.box3d(-3.8, 5.5 * U, -8.5, 3.8, 6.5 * U, -5.5, DR_DEEP)
        m.cube3(0, 3.5 * U, 0, 0.9 + 0.4 * math.sin(idleP * 3.0), 0xFFD040, 0.7)
        m.box3d(-0.6, 0, -8.5, -0.1, 0.3, -5.5, 0x604030)
        m.box3d(0.1, 0, -8.5, 0.6, 0.3, -5.5, 0x604030)
        m.box3d(-4.5, 0, 5.0, -4.0, 7.5 * U, 5.5, DR_STONE)
        m.box3d(4.0, 0, 5.0, 4.5, 7.5 * U, 5.5, DR_STONE)
        m.box3d(-4.5, 7.0 * U, 5.0, 4.5, 7.5 * U, 5.5, DR_STONE)

    else:
        return None     # the C++ answers an unknown bldgIdx with `return false`

    return m.build(**bake)
