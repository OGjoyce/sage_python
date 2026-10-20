"""Radiant 3D building models -- Maya solar warlord aesthetic.

Port of drawRadiantBldg3D in src/gfx/models3d/radiant_units.cpp, C++ numbers
verbatim. Units from the same file are in radiant_units.py.

Buildings: Grand Cathedral(0) Garrison(1) Granary(2) Sanctum(3) Foundry(4)
           Fountain(5) Gold Mine(6)
"""

import math

from claude_studio.craftwar_gl import U, GLModel

RD_PLATE = 0x4A5870   # deep slate-blue lamellar plate
RD_DARK = 0x202838    # near-black navy
RD_JADE = 0x2E9E90    # jade ceremonial
RD_GOLD = 0xFFD840    # solar gold glow
RD_TRIM = 0xD4A828    # gold trim
RD_SKIN = 0xC09050    # warm brown Mesoamerican complexion
RD_CLOTH = 0xB89060   # simple cloth / beige robe
RD_STONE = 0x808070   # stone masonry
RD_OBSID = 0x181820   # obsidian
RD_JAGUAR = 0xC07830  # jaguar tawny pelt

NAMES = ("GrandCathedral", "Garrison", "Granary", "Sanctum",
         "Foundry", "Fountain", "GoldMine")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the building, as bldgIdx does in the C++. anim is accepted
    and ignored -- buildings have no animation state."""
    m = GLModel(name or f"RADIANT_bldg{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")
    idleP = tickF * 0.9

    if idx == 0:
        # -- 0: GRAND CATHEDRAL (Town Hall) ----------------------------------
        # Stepped pyramid, temple sanctuary on top, sun disc, flanking obelisks
        m.box3d(-16.0, 0, -14.0, 16.0, U, 14.0, RD_STONE)            # foundation
        # Pyramid tier 1 (widest)
        m.box3d(-14.0, U, -12.0, 14.0, 3 * U, 12.0, RD_PLATE)
        m.box3d(-14.5, 1.8 * U, -12.5, 14.5, 2.2 * U, 12.5, RD_DARK)  # lamellar edge
        # Pyramid tier 2
        m.box3d(-11.0, 3 * U, -9.5, 11.0, 6 * U, 9.5, RD_PLATE)
        m.box3d(-11.5, 4.5 * U, -10.0, 11.5, 5.0 * U, 10.0, RD_DARK)
        # Pyramid tier 3
        m.box3d(-8.0, 6 * U, -7.0, 8.0, 9 * U, 7.0, RD_PLATE)
        m.box3d(-8.5, 7.5 * U, -7.5, 8.5, 7.9 * U, 7.5, RD_TRIM)      # gold stripe
        # Temple sanctuary on top
        m.box3d(-5.5, 9 * U, -4.5, 5.5, 14 * U, 4.5, RD_PLATE)
        m.box3d(-6.0, 9 * U, -5.0, 6.0, 9.5 * U, 5.0, RD_DARK)        # base ring
        # Temple stepped roof
        m.box3d(-6.5, 14 * U, -5.5, 6.5, 14.5 * U, 5.5, RD_STONE)
        m.box3d(-4.5, 14.5 * U, -3.5, 4.5, 15.0 * U, 3.5, RD_DARK)
        m.box3d(-2.5, 15.0 * U, -1.5, 2.5, 15.5 * U, 1.5, RD_STONE)
        # SUN DISC on front face (pulsing glow)
        sunPulse = 0.6 + math.sin(idleP * 2.2) * 0.3
        m.cube3(0.0, 11.5 * U, 5.0, 1.7, RD_GOLD, sunPulse)
        m.cube3(0.0, 11.5 * U, 5.0, 3.0, RD_GOLD, sunPulse * 0.22)
        # Cardinal sun rays
        for i in range(4):
            a = float(i) * 1.5708
            rx, ry = math.cos(a) * 3.8, math.sin(a) * 3.8
            m.box3d(rx - 0.25, 11.5 * U + ry - 0.2, 4.9,
                    rx + 0.25, 11.5 * U + ry + 0.2, 5.05, RD_TRIM)
        # FLANKING OBELISKS
        for side in (-1, 1):
            ox = float(side) * 12.5
            m.box3d(ox - 1.2, U, -1.2, ox + 1.2, 9 * U, 1.2, RD_DARK)      # shaft
            m.box3d(ox - 0.7, 9 * U, -0.7, ox + 0.7, 12 * U, 0.7, RD_DARK)  # taper
            m.box3d(ox - 0.4, 12 * U, -0.4, ox + 0.4, 13 * U, 0.4, RD_TRIM)  # gold cap
            m.cube3(ox, 13.4 * U, 0.0, 0.38, RD_GOLD,
                    0.7 + math.sin(idleP + float(side)) * 0.2)
            m.box3d(ox - 1.25, 5 * U, -1.25, ox + 1.25, 5.4 * U, 1.25, RD_JADE)
        # Entry arch
        m.box3d(-3.5, U, 12.0, -1.5, 5.5 * U, 14.0, RD_DARK)
        m.box3d(1.5, U, 12.0, 3.5, 5.5 * U, 14.0, RD_DARK)
        m.box3d(-3.5, 5.5 * U, 12.0, 3.5, 6.5 * U, 14.0, RD_DARK)
        m.box3d(-1.2, U + 0.1, 12.1, 1.2, 5.0 * U, 14.1, RD_GOLD, 0.1)  # door glow

    elif idx == 1:
        # -- 1: GARRISON (Barracks) ------------------------------------------
        # Stone longhouse, spear rack on wall, sun banner
        m.box3d(-13.0, 0, -10.0, 13.0, U, 10.0, RD_STONE)          # foundation
        m.box3d(-12.0, U, -9.0, 12.0, 7 * U, 9.0, RD_PLATE)        # main walls
        m.box3d(-12.5, 1.5 * U, -9.5, 12.5, 2.0 * U, 9.5, RD_DARK)  # mid band
        # Stepped roof
        m.box3d(-13.0, 7 * U, -10.0, 13.0, 8 * U, 10.0, RD_STONE)
        m.box3d(-10.0, 8 * U, -7.0, 10.0, 8.5 * U, 7.0, RD_DARK)
        # Front battlements
        for i in range(-4, 5):
            bx = float(i) * 2.8
            m.box3d(bx - 0.7, 8 * U, 9.5, bx + 0.7, 9.3 * U, 10.2, RD_STONE)
        # SPEAR RACK (3 spears leaning against the front wall)
        m.box3d(-2.0, U, 9.1, 2.0, U + 0.5, 9.5, RD_STONE)         # rack base
        for i in (-1, 0, 1):
            sx = float(i) * 1.5
            m.box3d(sx - 0.15, U + 0.5, 9.1, sx + 0.15, 6.5 * U, 9.5, RD_STONE)
            m.cube3(sx, 6.6 * U, 9.3, 0.3, RD_TRIM, 0.9)
        # SUN BANNER on roof pole
        m.box3d(9.0, 8 * U, -0.3, 9.4, 12.5 * U, 0.3, RD_STONE)
        flagWave = math.sin(tickF * 2.0) * 0.5
        m.box3d(9.4, 11.2 * U, -0.2 + flagWave, 13.0, 12.2 * U, 0.2 + flagWave, RD_GOLD)
        m.cube3(11.2, 11.7 * U, flagWave, 0.65, RD_DARK, 0.7)
        # Windows
        for i in (-1, 0, 1):
            wx = float(i) * 7.0
            m.box3d(wx - 1.0, 3.5 * U, 9.05, wx + 1.0, 5.5 * U, 9.2, RD_DARK, 0.9)
        # Rear entry door
        m.box3d(-2.5, U, -9.1, 2.5, 4.5 * U, -8.9, RD_DARK, 0.7)
        # Jade step-fret strips on corners
        m.box3d(-12.1, 3 * U, -9.1, -11.8, 6 * U, 9.1, RD_JADE, 0.5)
        m.box3d(11.8, 3 * U, -9.1, 12.1, 6 * U, 9.1, RD_JADE, 0.5)

    elif idx == 2:
        # -- 2: GRANARY (Farm) -----------------------------------------------
        # Stout rounded storehouse on a raised platform, clay jar decorations
        m.box3d(-10.0, 0, -9.0, 10.0, 2 * U, 9.0, RD_STONE)
        m.box3d(-9.5, 2 * U, -8.5, 9.5, 2.4 * U, 8.5, RD_DARK)     # platform edge
        # Main storehouse
        m.box3d(-9.0, 2.4 * U, -8.0, 9.0, 8 * U, 8.0, RD_PLATE, 0.85)
        m.box3d(-9.5, 4.0 * U, -8.5, 9.5, 4.5 * U, 8.5, RD_DARK)   # mid band
        # Rounded dome (stepped approximation)
        m.box3d(-8.5, 8 * U, -7.5, 8.5, 9.5 * U, 7.5, RD_STONE)
        m.box3d(-6.5, 9.5 * U, -5.5, 6.5, 10.5 * U, 5.5, RD_STONE)
        m.box3d(-4.0, 10.5 * U, -3.5, 4.0, 11.0 * U, 3.5, RD_PLATE)
        m.cube3(0.0, 11.3 * U, 0.0, 0.65, RD_GOLD,
                0.8 + math.sin(idleP) * 0.15)                      # apex ornament
        # Step-fret carved border on the front face
        for i in range(-4, 5):
            sx = float(i) * 2.2
            m.box3d(sx - 0.5, 6.5 * U, 8.05, sx + 0.5, 7.0 * U, 8.15, RD_JADE, 0.8)
        # CLAY JAR decorations (3 jars on the front platform)
        for i in (-1, 0, 1):
            jx = float(i) * 4.0
            m.box3d(jx - 0.9, 2.4 * U, 8.1, jx + 0.9, 4.5 * U, 9.0, 0xA07850)   # body
            m.box3d(jx - 0.6, 4.5 * U, 8.2, jx + 0.6, 5.2 * U, 8.9, 0xA07850)   # neck
            m.box3d(jx - 0.7, 5.2 * U, 8.15, jx + 0.7, 5.5 * U, 8.95, 0x906840)  # lid
            m.cube3(jx, 2.6 * U, 9.05, 0.15, RD_JADE, 0.7)                      # bead
        # Ventilation slits on the sides
        m.box3d(9.1, 4.0 * U, -1.5, 9.3, 6.0 * U, 1.5, RD_DARK, 0.7)
        m.box3d(-9.3, 4.0 * U, -1.5, -9.1, 6.0 * U, 1.5, RD_DARK, 0.7)

    elif idx == 3:
        # -- 3: SANCTUM OF LIGHT (Mage Tower) --------------------------------
        # Tall obelisk, golden apex sun, glowing step-fret seams
        m.box3d(-7.0, 0, -7.0, 7.0, 2 * U, 7.0, RD_STONE)
        m.box3d(-6.5, 2 * U, -6.5, 6.5, 2.5 * U, 6.5, RD_DARK)
        # Step tier 1
        m.box3d(-5.0, 2.5 * U, -5.0, 5.0, 5 * U, 5.0, RD_PLATE)
        m.box3d(-5.5, 3.5 * U, -5.5, 5.5, 4.0 * U, 5.5, RD_JADE)   # jade band
        # Step tier 2 (taller)
        m.box3d(-3.0, 5 * U, -3.0, 3.0, 10 * U, 3.0, RD_PLATE, 0.85)
        m.box3d(-3.5, 5 * U, -3.5, 3.5, 5.5 * U, 3.5, RD_DARK)
        # Glowing step-fret seams (pulsing)
        sfPulse = 0.4 + math.sin(idleP * 1.5) * 0.3
        for h in (1, 2, 3):
            hy = 5.0 * U + float(h) * 1.5 * U
            m.box3d(-3.1, hy, -3.1, 3.1, hy + 0.3, 3.1, RD_JADE, sfPulse)
        # Upper obelisk spire
        m.box3d(-2.0, 10 * U, -2.0, 2.0, 15 * U, 2.0, RD_DARK)
        m.box3d(-1.5, 10 * U, -1.5, 1.5, 15 * U, 1.5, RD_PLATE, 0.9)
        m.box3d(-0.8, 15 * U, -0.8, 0.8, 18 * U, 0.8, RD_STONE)    # needle
        # GOLDEN APEX SUN
        apexPulse = 0.65 + math.sin(idleP * 2.8) * 0.3
        m.cube3(0.0, 18.5 * U, 0.0, 1.1, RD_GOLD, apexPulse)
        m.cube3(0.0, 18.5 * U, 0.0, 2.2, RD_GOLD, apexPulse * 0.22)
        for i in range(4):
            a = float(i) * 1.5708
            rx, rz = math.cos(a) * 2.7, math.sin(a) * 2.7
            m.box3d(rx - 0.25, 18.5 * U - 0.15, rz - 0.25,
                    rx + 0.25, 18.5 * U + 0.15, rz + 0.25, RD_TRIM)
        # Front carved sun disc at mid spire
        m.cube3(0.0, 12.0 * U, 3.15, 1.0, RD_GOLD, 0.5 + math.sin(idleP) * 0.2)
        # Side jade carved strips
        m.box3d(-3.15, 6.0 * U, -1.0, -3.0, 9.0 * U, 1.0, RD_JADE, 0.6)
        m.box3d(3.0, 6.0 * U, -1.0, 3.15, 9.0 * U, 1.0, RD_JADE, 0.6)

    elif idx == 4:
        # -- 4: FOUNDRY (Workshop) -------------------------------------------
        # Forge hall, glowing smelter, stepped roof, jade corner accents
        m.box3d(-12.0, 0, -10.0, 12.0, U, 10.0, RD_STONE)            # foundation
        m.box3d(-11.0, U, -9.0, 11.0, 7 * U, 9.0, RD_PLATE, 0.8)     # walls
        m.box3d(-11.5, 1.5 * U, -9.5, 11.5, 2.0 * U, 9.5, RD_DARK)   # mid band
        # Stepped roof (3 tiers)
        m.box3d(-11.5, 7 * U, -9.5, 11.5, 8 * U, 9.5, RD_STONE)
        m.box3d(-9.0, 8 * U, -7.0, 9.0, 9 * U, 7.0, RD_DARK)
        m.box3d(-6.0, 9 * U, -4.0, 6.0, 9.5 * U, 4.0, RD_STONE)
        # SMELTER (center, glowing)
        smeltPulse = 0.6 + math.sin(idleP * 2.5) * 0.35
        m.box3d(-3.0, U, -3.0, 3.0, 5 * U, 3.0, 0x402820)                  # housing
        m.cube3(0.0, 3.0 * U, 3.1, 1.2, 0xFF6020, smeltPulse)              # orange fire
        m.cube3(0.0, 3.0 * U, 0.0, 2.0, 0xFF4010, smeltPulse * 0.28)       # interior
        # Chimney + smoke
        m.box3d(-1.5, 5 * U, -1.5, 1.5, 11.5 * U, 1.5, RD_DARK)
        smokeY = math.sin(tickF * 1.5) * 1.5
        m.cube3(0.0, 11.8 * U + smokeY, 0.0, 0.8, 0x604858, 0.3)
        m.cube3(0.0, 12.8 * U + smokeY * 1.4, 0.0, 0.6, 0x504050, 0.18)
        # Gold trim strip on the front
        m.box3d(-11.0, 4.5 * U, 8.6, 11.0, 5.0 * U, 9.0, RD_TRIM)
        # Work benches / anvil blocks
        m.box3d(-10.0, U, -2.0, -4.0, 3 * U, 2.0, RD_STONE)
        m.box3d(4.0, U, -2.0, 10.0, 3 * U, 2.0, RD_STONE)
        # Molten gold sheen on the benches
        m.cube3(-7.0, 3.15 * U, 0.0, 0.65, RD_GOLD, smeltPulse * 0.7)
        m.cube3(7.0, 3.15 * U, 0.0, 0.65, RD_GOLD, smeltPulse * 0.65)
        # Jade corner accents
        m.box3d(-11.1, U, -9.1, -10.8, 7 * U, 9.1, RD_JADE, 0.6)
        m.box3d(10.8, U, -9.1, 11.1, 7 * U, 9.1, RD_JADE, 0.6)

    elif idx == 5:
        # -- 5: FOUNTAIN (Hero Spawn) ----------------------------------------
        # Jade and gold circular basin, solar column, orbiting golden orb
        m.box3d(-7.0, 0, -7.0, 7.0, 0.8, 7.0, RD_STONE)
        m.box3d(-6.5, 0, -6.5, 6.5, 0.5, 6.5, RD_JADE, 0.45)     # jade inlay
        # 8 basin rim pillars
        for i in range(8):
            a = float(i) * 0.7854
            rx, rz = math.cos(a) * 6.0, math.sin(a) * 6.0
            m.box3d(rx - 0.8, 0, rz - 0.8, rx + 0.8, 3.0 * U, rz + 0.8, RD_STONE)
            m.cube3(rx, 3.2 * U, rz, 0.5, RD_JADE, 0.8)          # jade cap
        # Pulsing jade bead ring inside the basin
        for i in range(8):
            a = float(i) * 0.7854 + idleP * 0.3
            m.cube3(math.cos(a) * 4.0, 0.6, math.sin(a) * 4.0, 0.35, RD_JADE,
                    0.4 + math.sin(idleP + float(i)) * 0.2)
        # SOLAR COLUMN (center)
        m.box3d(-U, 0, -U, U, 7 * U, U, RD_DARK)
        m.box3d(-0.7, 0, -0.7, 0.7, 7 * U, 0.7, RD_PLATE, 0.9)
        # Step-fret carvings on the column
        for h in (1, 2, 3, 4):
            hy = float(h) * 1.5 * U
            m.box3d(-1.1, hy, -1.1, 1.1, hy + 0.25, 1.1, RD_JADE, 0.7)
        # GOLDEN ORB (hero spawn, floating + pulsing)
        orbY = 7.5 * U + math.sin(idleP) * 0.9 * U
        orbPulse = 0.65 + math.sin(tickF * 2.5) * 0.25
        m.cube3(0.0, orbY, 0.0, 1.2, RD_GOLD, orbPulse)
        m.cube3(0.0, orbY, 0.0, 2.6, RD_GOLD, orbPulse * 0.18)
        # Two orbiting rings (jade + gold)
        for r in (0, 1):
            m.push()
            m.translate(0.0, orbY, 0.0)
            spinR = tickF * (55.0 if r == 0 else -40.0)
            if r == 0:
                m.rotate(spinR, 0, 1, 0)
            else:
                m.rotate(20.0, 1, 0, 0)
                m.rotate(spinR, 0, 1, 0)
            for i in range(6):
                a = float(i) * 1.047
                m.cube3(math.cos(a) * 4.0, 0.0, math.sin(a) * 4.0, 0.35,
                        RD_JADE if r == 0 else RD_GOLD, 0.55)
            m.pop()

    elif idx == 6:
        # -- 6: GOLD MINE (neutral resource) ---------------------------------
        # Rock mound, jade-trimmed mine entrance, scaffolding, gold vein shimmer
        m.box3d(-13.0, 0, -11.0, 13.0, 4 * U, 11.0, RD_DARK)
        m.box3d(-9.0, 4 * U, -7.0, 9.0, 8 * U, 7.0, 0x404030)
        m.box3d(-5.0, 8 * U, -4.0, 5.0, 11 * U, 4.0, 0x504840)
        # Mine entrance arch (front)
        m.box3d(-4.0, 0, 9.5, -2.0, 5 * U, 11.0, 0x404030)
        m.box3d(2.0, 0, 9.5, 4.0, 5 * U, 11.0, 0x404030)
        m.box3d(-4.0, 5 * U, 9.5, 4.0, 6 * U, 11.0, 0x404030)
        # Jade carved lintel
        m.box3d(-3.8, 5.3 * U, 9.5, 3.8, 5.6 * U, 11.1, RD_JADE, 0.6)
        # Gold vein shimmer inside
        goldPulse = 0.45 + math.sin(idleP * 1.8) * 0.3
        m.cube3(0.0, 2.5 * U, 10.0, 1.2, RD_GOLD, goldPulse)
        m.cube3(0.0, 2.5 * U, 10.0, 2.0, RD_TRIM, goldPulse * 0.28)
        # Cart tracks (two rails)
        m.box3d(-0.8, 0, 3.0, -0.4, 0.5, 9.5, 0x705030)
        m.box3d(0.4, 0, 3.0, 0.8, 0.5, 9.5, 0x705030)
        # Scaffolding uprights + cross beams
        m.box3d(-4.0, 5 * U, -2.0, -2.8, 10 * U, 2.0, 0x706050)
        m.box3d(2.8, 5 * U, -2.0, 4.0, 10 * U, 2.0, 0x706050)
        m.box3d(-4.0, 9.5 * U, -1.0, 4.0, 10.0 * U, 1.0, 0x706050)
        m.box3d(-4.0, 7.0 * U, -1.0, 4.0, 7.5 * U, 1.0, 0x706050)
        # Step-pyramid motif on the mound face (decorative)
        m.box3d(-6.0, 0, 10.5, 6.0, U, 11.0, RD_PLATE, 0.5)
        m.box3d(-4.0, U, 10.5, 4.0, 2 * U, 11.0, RD_PLATE, 0.4)

    else:
        return None     # the C++ answers an unknown bldgIdx with "return false"

    return m.build(**bake)
