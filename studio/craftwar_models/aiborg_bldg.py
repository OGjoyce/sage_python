"""AI-Borg 3D building models.

Port of drawAiborgBldg3D in src/gfx/models3d/aiborg_units.cpp, C++ numbers
verbatim. Units from the same file are in aiborg_units.py.

Buildings: Mainframe(0) Fabricator(1) PowerNode(2) DataSpire(3)
           AssemblyYard(4) NeuralNexus(5) GoldMine(6)

Palette note: this half of the C++ file uses AB_BODY, AB_EXOSK, AB_GLOW,
AB_DARK, AB_STEEL, AB_CABLE and AB_ARC, which the file itself no longer
declares -- the Drone rewrite replaced the palette block with a unit-only one
and left these behind, so the file does not compile as it stands. The values
below are the ones the file defined before that rewrite (git 79e3d56).
"""

import math

from claude_studio.craftwar_gl import U, GLModel

AB_BODY = 0x2A2A38
AB_EXOSK = 0x505060
AB_GLOW = 0xF0C040
AB_DARK = 0x0C0C18
AB_STEEL = 0x7090A8
AB_CABLE = 0x404055
AB_ARC = 0x40C8FF

NAMES = ("Mainframe", "Fabricator", "PowerNode", "DataSpire",
         "AssemblyYard", "NeuralNexus", "GoldMine")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the building, as bldgIdx does in the C++."""
    m = GLModel(name or f"AIBORG_bldg{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")
    idleP = tickF * 0.9

    if idx == 0:
        # -- 0: MAINFRAME (Town Hall) ----------------------------------------
        # Server-cluster command center -- 3x3 tile footprint
        m.box3d(-15.0, -0.5, -15.0, 15.0, 0, 15.0, AB_DARK)          # foundation
        m.box3d(-13.0, 0, -12.0, 13.0, 10 * U, 12.0, AB_BODY)        # main hall
        # 5 server rack columns visible from front
        for i in range(-2, 3):
            rx = i * 4.5
            m.box3d(rx - 0.9, 0, -10.0, rx + 0.9, 8 * U, 10.0, AB_EXOSK)
            # Port glow lights per rack
            for j in range(5):
                ry = j * 1.4 * U + U
                m.cube3(rx, ry, 10.1, 0.25, AB_GLOW if j % 2 == 0 else AB_ARC, 0.7)
        # Roof mast + rotating scanner
        m.box3d(-1.0, 10 * U, -1.0, 1.0, 14 * U, 1.0, AB_STEEL)
        scanAng = tickF * 40.0
        m.push()
        m.translate(0, 14 * U, 0)
        m.rotate(scanAng, 0, 1, 0)
        m.box3d(-3.5, -0.2, -0.25, 3.5, 0.25, 0.25, AB_ARC)
        m.pop()
        m.cube3(0, 14.5 * U, 0, 0.65, AB_GLOW, 0.5 + math.sin(idleP) * 0.25)
        # Entry arch
        m.box3d(-4.0, 0, 12.0, -2.0, 4.5 * U, 14.0, AB_EXOSK)
        m.box3d(2.0, 0, 12.0, 4.0, 4.5 * U, 14.0, AB_EXOSK)
        m.box3d(-4.0, 4.5 * U, 12.0, 4.0, 5.5 * U, 14.0, AB_EXOSK)
        # Door glow
        m.box3d(-1.5, 0.1, 12.0, 1.5, 4.0, 14.1, AB_ARC, 0.15)

    elif idx == 1:
        # -- 1: FABRICATOR (Barracks) ----------------------------------------
        # Manufacturing plant -- 3 production bays, exhaust stack, assembly arm
        m.box3d(-13.0, 0, -10.0, 13.0, 6 * U, 10.0, AB_BODY)      # main hall
        # Three bay sections with raised roof
        for b in range(3):
            bx = -8.0 + b * 8.0
            m.box3d(bx - 3.0, 6 * U, -8.0, bx + 3.0, 8.5 * U, 8.0, AB_EXOSK)
        # Exhaust chimney
        m.box3d(-10.5, 6 * U, -2.0, -8.5, 13 * U, 2.0, AB_STEEL)
        puffY = math.sin(tickF * 1.8) * 1.5
        m.cube3(-9.5, 13.5 * U + puffY, 0, 0.7, AB_EXOSK, 0.3)
        m.cube3(-9.5, 14.5 * U + puffY * 1.3, 0, 0.5, AB_EXOSK, 0.18)
        # Rotating assembly arm (right side exterior)
        armYaw = math.sin(tickF * 0.4) * 25.0
        m.push()
        m.translate(13.0, 5.5 * U, 0)
        m.rotate(armYaw, 0, 1, 0)
        m.box3d(0, 0, -0.6, 6.0, U, 0.6, AB_EXOSK)           # arm span
        m.cube3(6.0, 0.5 * U, 0, 0.5, AB_GLOW, 0.6)          # mag end-effector
        m.pop()
        # Status LEDs on front wall
        for i in range(5):
            m.cube3(-8.0 + i * 4.0, 5.8 * U, 10.1, 0.35, AB_GLOW,
                    0.4 + math.sin(tickF + i) * 0.35)

    elif idx == 2:
        # -- 2: POWER NODE (Farm) --------------------------------------------
        # Energy tower -- 2x2 tile, tall, pulsing plasma rings
        m.box3d(-6.0, 0, -6.0, 6.0, 2 * U, 6.0, AB_BODY)          # base pad
        m.box3d(-3.0, 2 * U, -3.0, 3.0, 10 * U, 3.0, AB_EXOSK)    # column
        m.box3d(-2.0, 10 * U, -2.0, 2.0, 14 * U, 2.0, AB_BODY)
        # 3 pulsing plasma rings at different heights + phases
        for r in range(3):
            rY = 4.0 * U + r * 2.8 * U
            rPhase = idleP + r * 2.094        # 120 deg offset
            rS = 0.85 + math.sin(rPhase) * 0.15
            m.push()
            m.translate(0, rY, 0)
            m.scale(rS, 1.0, rS)
            for i in range(8):
                a = i * 0.7854
                rx, rz = math.cos(a) * 5.5, math.sin(a) * 5.5
                col = AB_GLOW if r == 0 else (AB_ARC if r == 1 else AB_STEEL)
                m.box3d(rx - 0.35, -0.2, rz - 0.35, rx + 0.35, 0.2, rz + 0.35,
                        col, 0.45 + math.sin(rPhase) * 0.3)
            m.pop()
        # Apex glow cluster
        aG = 0.55 + math.sin(tickF * 2.1) * 0.3
        m.cube3(0, 14.5 * U, 0, 1.1, AB_GLOW, aG)
        m.cube3(0, 14.5 * U, 0, 2.2, AB_ARC, aG * 0.35)

    elif idx == 3:
        # -- 3: DATA SPIRE (Mage Tower) --------------------------------------
        # Tall antenna spire -- 3 directional dishes, scanning apex
        m.box3d(-5.0, 0, -5.0, 5.0, 2 * U, 5.0, AB_BODY)              # base
        m.box3d(-3.0, 2 * U, -3.0, 3.0, 7 * U, 3.0, AB_EXOSK)         # mid section
        m.box3d(-2.0, 7 * U, -2.0, 2.0, 14 * U, 2.0, AB_BODY)         # upper
        m.box3d(-0.7, 14 * U, -0.7, 0.7, 18 * U, 0.7, AB_STEEL)       # spire tip
        # 3 rotating dish arrays at mid-height
        dishSpin = tickF * 0.1
        for i in range(3):
            a = i * 2.094 + dishSpin
            dx, dz = math.cos(a) * 4.0, math.sin(a) * 4.0
            m.box3d(dx - 0.3, 5.5 * U, dz - 0.3, dx + 0.3, 7 * U, dz + 0.3,
                    AB_STEEL)                                          # post
            m.box3d(dx - 1.6, 6 * U, dz - 1.6, dx + 1.6, 6.6 * U, dz + 1.6,
                    AB_EXOSK)                                          # dish
        # Data ring at mid
        for i in range(8):
            a = i * 0.7854 + tickF * 0.15
            m.cube3(math.cos(a) * 2.5, 10 * U, math.sin(a) * 2.5, 0.3, AB_ARC, 0.4)
        # Apex pulsing
        m.cube3(0, 18.5 * U, 0, 0.75, AB_GLOW,
                0.45 + math.sin(tickF * 3.0) * 0.45)

    elif idx == 4:
        # -- 4: ASSEMBLY YARD (Workshop) -------------------------------------
        # Factory complex -- wide floor, crane, active conveyor status
        m.box3d(-14.0, 0, -10.0, 14.0, 4 * U, 10.0, AB_BODY)
        m.box3d(-12.0, 4 * U, -8.0, 12.0, 6 * U, 8.0, AB_EXOSK)    # roof deck
        # Crane mast
        m.box3d(9.5, 0, -0.8, 11.0, 7 * U, 0.8, AB_STEEL)
        # Crane arm (slow horizontal sweep)
        craneYaw = math.sin(tickF * 0.35) * 35.0
        m.push()
        m.translate(10.0, 7 * U, 0)
        m.rotate(craneYaw, 0, 1, 0)
        m.box3d(0, -0.4, -0.5, 8.0, 0.4, 0.5, AB_STEEL)            # arm
        m.box3d(7.5, -4.5 * U, -0.4, 8.5, 0, 0.4, AB_CABLE)        # cable
        m.cube3(8.0, -5 * U, 0, 0.55, AB_GLOW, 0.55)               # magnetic clamp
        m.pop()
        # Corner indicators
        m.cube3(-12.5, 6.5 * U, 0, 0.45, AB_ARC, 0.5 + math.sin(tickF) * 0.3)
        m.cube3(12.5, 6.5 * U, 0, 0.45, AB_GLOW, 0.5 + math.sin(tickF + 1.0) * 0.3)

    elif idx == 5:
        # -- 5: NEURAL NEXUS (Fountain / Hero spawn) -------------------------
        # Circular basin, central column, floating orb with orbiting rings
        for i in range(8):
            a = i * 0.7854
            rx, rz = math.cos(a) * 6.5, math.sin(a) * 6.5
            m.box3d(rx - 0.7, 0, rz - 0.7, rx + 0.7, 2.5 * U, rz + 0.7, AB_EXOSK)
        m.box3d(-6.0, 0, -6.0, 6.0, 0.6, 6.0, AB_DARK)        # basin floor
        m.box3d(-U, 0, -U, U, 5.5 * U, U, AB_BODY)            # central column
        # Floating orb (hero spawn effect)
        orbY = 5.5 * U + math.sin(idleP) * 0.8 * U
        m.cube3(0, orbY, 0, 1.1, AB_GLOW, 0.65 + math.sin(tickF * 2.2) * 0.2)
        m.cube3(0, orbY, 0, 2.4, AB_ARC, 0.2 + math.sin(tickF * 1.6) * 0.1)
        # Two orbiting rings (one vertical, one tilted)
        for r in (0, 1):
            m.push()
            m.translate(0, orbY, 0)
            spinR = tickF * (50.0 if r == 0 else -35.0)
            if r == 0:
                m.rotate(spinR, 0, 1, 0)
            else:
                m.rotate(15.0, 1, 0, 0)
                m.rotate(spinR, 0, 1, 0)
            for i in range(6):
                a = i * 1.047
                m.cube3(math.cos(a) * 3.5, 0, math.sin(a) * 3.5, 0.3,
                        AB_GLOW if r == 0 else AB_ARC, 0.5)
            m.pop()

    elif idx == 6:
        # -- 6: GOLD MINE (neutral resource) ---------------------------------
        # Rock mound with mine entrance, cart tracks, scaffolding
        m.box3d(-13.0, 0, -11.0, 13.0, 5 * U, 11.0, AB_DARK)
        m.box3d(-8.0, 5 * U, -7.0, 8.0, 9 * U, 7.0, 0x403830)     # rock
        m.box3d(-5.0, 9 * U, -4.0, 5.0, 11 * U, 4.0, 0x504840)    # peak
        # Mine entrance arch
        m.box3d(-3.7, 0, 9.5, -1.7, 4.5 * U, 11.0, 0x403830)      # left post
        m.box3d(1.7, 0, 9.5, 3.7, 4.5 * U, 11.0, 0x403830)        # right post
        m.box3d(-3.7, 4.5 * U, 9.5, 3.7, 5.5 * U, 11.0, 0x403830)  # lintel
        # Gold vein shimmer inside
        m.cube3(0, 2.5 * U, 10.0, 1.0, 0xF0D030, 0.45 + math.sin(idleP) * 0.3)
        # Cart tracks (two rails)
        m.box3d(-0.8, 0, 2.0, -0.4, 0.5, 9.5, 0x705030)
        m.box3d(0.4, 0, 2.0, 0.8, 0.5, 9.5, 0x705030)
        # Scaffolding (two vertical supports)
        m.box3d(-3.0, 4.5 * U, -2.0, -2.0, 8.5 * U, 2.0, 0x706050)
        m.box3d(2.0, 4.5 * U, -2.0, 3.0, 8.5 * U, 2.0, 0x706050)
        m.box3d(-3.0, 8.5 * U, -1.0, 3.0, 9.0 * U, 1.0, 0x706050)  # cross beam

    else:
        return None     # the C++ answers an unknown bldgIdx with "return false"

    return m.build(**bake)
