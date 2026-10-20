"""Alliance 3D building models.

Port of drawAllianceBldg3D in src/gfx/models3d/alliance_units.cpp, C++
numbers verbatim. Units from the same file are in alliance_units.py.

Buildings: Keep(0) Barracks(1) Farm(2) ArcaneSanctum(3) Workshop(4)
           Fountain(5) GoldMine(6)
"""

import math

from claude_studio.craftwar_gl import U, GLModel

AL_BLUE = 0x3070E8   # royal blue (primary armor)
AL_NAVY = 0x1A3E80   # deep navy (trim / shadow)
AL_GLOW = 0x80C0FF   # silver-blue holy light
AL_GOLD = 0xD4A828   # gold accents
AL_CLOTH = 0xE8E4D8  # cloth / ivory
AL_STEEL = 0xA8B8C8  # polished steel
AL_STONE = 0x8090A0  # dressed stone
AL_DARK = 0x283048   # shadow / dark base

NAMES = ("Keep", "Barracks", "Farm", "ArcaneSanctum", "Workshop",
         "Fountain", "GoldMine")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the building, as bldgIdx does in the C++."""
    m = GLModel(name or f"ALLIANCE_bldg{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")
    idleP = tickF * 0.9

    if idx == 0:
        # -- 0: KEEP (Town Hall) ---------------------------------------------
        # Large stone keep -- 3x3 tile footprint, battlements, banners, portcullis
        m.box3d(-15.0, -0.5, -15.0, 15.0, 0, 15.0, AL_DARK)            # foundation
        m.box3d(-13.0, 0, -12.0, 13.0, 10 * U, 12.0, AL_STONE)         # main body
        m.box3d(-7.0, 10 * U, -7.0, 7.0, 15 * U, 7.0, AL_STONE)        # inner keep
        # 4 corner towers
        for cx in (-1, 1):
            for cz in (-1, 1):
                tx, tz = cx * 11.0, cz * 10.0
                m.box3d(tx - 2.5, 0, tz - 2.5, tx + 2.5, 12 * U, tz + 2.5, AL_STONE)
                # Tower battlements (merlons)
                for mi in (-1, 0, 1):
                    m.box3d(tx - 0.6 + mi * 1.8, 12 * U, tz - 2.7,
                            tx + 0.6 + mi * 1.8, 13.3 * U, tz + 2.7, AL_STONE)
        # Main wall battlements (front face)
        for i in range(-4, 5):
            bx = i * 2.8
            m.box3d(bx - 0.7, 10 * U, -13.1, bx + 0.7, 11.5 * U, 13.1, AL_STONE)
        # Portcullis gate (front)
        m.box3d(-4.5, 0, 11.0, -2.5, 5 * U, 13.5, AL_STONE)        # left jamb
        m.box3d(2.5, 0, 11.0, 4.5, 5 * U, 13.5, AL_STONE)          # right jamb
        m.box3d(-4.5, 5 * U, 11.0, 4.5, 6.5 * U, 13.5, AL_STONE)   # arch lintel
        m.box3d(-2.2, 0.2, 11.0, 2.2, 4.8 * U, 13.6, AL_DARK, 0.5)  # gate void
        # Portcullis bars
        for b in range(-2, 3):
            m.box3d(b * 0.8 - 0.12, 0.3, 11.0, b * 0.8 + 0.12, 4.8 * U, 13.7, AL_NAVY)
        # Banners on front towers
        for cx in (-1, 1):
            tx = cx * 11.0
            m.box3d(tx - 0.15, 12.3 * U, -0.3, tx + 0.15, 15.5 * U, 0.3, AL_CLOTH)
            m.box3d(tx + 0.15, 13.8 * U, -0.3, tx + 3.0, 15.2 * U, 0.3, AL_BLUE)
            # Cross on banner
            m.box3d(tx + 0.9, 14.0 * U, -0.25, tx + 1.3, 15.0 * U, 0.25, AL_GOLD)
            m.box3d(tx + 0.2, 14.4 * U, -0.25, tx + 2.0, 14.7 * U, 0.25, AL_GOLD)
        # Keep peak flag
        m.box3d(-0.2, 15 * U, -0.2, 0.2, 18 * U, 0.2, AL_CLOTH)
        m.box3d(0.2, 17.0 * U, -0.2, 3.8, 18.0 * U, 0.2, AL_BLUE)

    elif idx == 1:
        # -- 1: BARRACKS -----------------------------------------------------
        # Rectangular stone building, 2 front corner towers, archway entrance
        m.box3d(-13.0, 0, -10.0, 13.0, 7 * U, 10.0, AL_STONE)        # main hall
        m.box3d(-13.5, 7 * U, -10.5, 13.5, 8 * U, 10.5, AL_NAVY)     # roof cap
        # 2 front corner towers (taller)
        for cx in (-1, 1):
            tx = cx * 11.0
            m.box3d(tx - 2.5, 0, 8.5, tx + 2.5, 9.5 * U, 13.0, AL_STONE)
            m.box3d(tx - 2.7, 9.5 * U, 8.3, tx + 2.7, 10.5 * U, 13.2, AL_STONE)
            # Merlons on tower top
            for mi in (-1, 0, 1):
                mz = 10.0 + mi * 1.5
                m.box3d(tx - 2.8, 10.5 * U, mz - 0.45, tx + 2.8, 11.8 * U, mz + 0.45,
                        AL_STONE)
        # Archway entrance (front center)
        m.box3d(-4.0, 0, 9.5, -2.0, 4.5 * U, 11.5, AL_STONE)       # left post
        m.box3d(2.0, 0, 9.5, 4.0, 4.5 * U, 11.5, AL_STONE)         # right post
        m.box3d(-4.0, 4.5 * U, 9.5, 4.0, 5.8 * U, 11.5, AL_STONE)  # arch lintel
        m.box3d(-1.8, 0.2, 9.5, 1.8, 4.3 * U, 11.6, AL_DARK, 0.4)  # arch opening
        # Banner over entrance
        m.box3d(-2.2, 5.8 * U, 9.6, 2.2, 6.9 * U, 10.1, AL_BLUE)
        m.box3d(-0.5, 6.0 * U, 9.7, 0.5, 6.7 * U, 10.2, AL_GOLD)
        # Arrow slits (sides)
        for s in (-1, 1):
            sz = s * 4.5
            m.box3d(-0.3, 2.5 * U, sz - 0.15, 0.3, 5.5 * U, sz + 0.15, AL_GLOW, 0.3)
        # Wall torch brackets
        for cx in (-1, 1):
            tx = cx * 7.0
            m.box3d(tx - 0.2, 5.5 * U, 10.1, tx + 0.2, 6.3 * U, 10.5, AL_GOLD)
            m.cube3(tx, 6.5 * U, 10.3, 0.35, 0xFFA030,
                    0.5 + math.sin(tickF * 3.0 + tx) * 0.35)

    elif idx == 2:
        # -- 2: FARM ---------------------------------------------------------
        # Low 2x2 building, peaked roof, silo, wheat symbol on front
        m.box3d(-8.0, 0, -7.0, 8.0, 5 * U, 7.0, 0x8B5A2B)        # main barn (wood)
        # Peaked roof (stepped pyramid approximation)
        for r in range(5):
            sh = r * 1.4
            m.box3d(-8.0 + sh, 5 * U + r * 0.95, -7.0 + sh,
                    8.0 - sh, 5 * U + r * 0.95 + 0.95, 7.0 - sh, 0x6B4010)
        # Roof ridge
        m.box3d(-1.8, 5 * U + 4.75, -5.0, 1.8, 7.5 * U, 5.0, 0x5A3008)
        # Wheat cross symbol on front face
        m.box3d(-0.45, 1.5 * U, 7.1, 0.45, 4.3 * U, 7.5, AL_GOLD)   # vert stem
        m.box3d(-2.5, 3.0 * U, 7.1, 2.5, 3.6 * U, 7.5, AL_GOLD)     # crossbar
        # Grain bundles at top of stem
        for i in (-1, 0, 1):
            m.cube3(i * 1.3, 4.5 * U, 7.3, 0.55, AL_GOLD, 0.75)
        # SILO (right side -- circular approximated by box)
        m.box3d(8.0, 0, -3.5, 12.5, 8 * U, 3.5, 0xA87050)
        # Silo dome (stepped top)
        for d in range(4):
            ds = d * 0.55
            m.box3d(8.0 + ds, 8 * U + d * 0.65, -3.5 + ds,
                    12.5 - ds, 8 * U + d * 0.65 + 0.65, 3.5 - ds, 0x886030)
        # Fence posts (front of farm)
        for f in range(-3, 4):
            fx = f * 2.3
            m.box3d(fx - 0.2, 0, 7.5, fx + 0.2, 2.5, 8.0, 0x8B5A2B)
        m.box3d(-7.0, 1.5, 7.5, 7.0, 2.0, 8.0, 0x8B5A2B)           # rail

    elif idx == 3:
        # -- 3: ARCANE SANCTUM (Mage Tower) ----------------------------------
        # Tall slim tower, glowing window, spinning orb on peak
        m.box3d(-6.0, 0, -6.0, 6.0, 2 * U, 6.0, AL_STONE)          # base platform
        # 4 corner buttresses
        for cx in (-1, 1):
            for cz in (-1, 1):
                m.box3d(cx * 4.0 - 1.0, 0, cz * 4.0 - 1.0,
                        cx * 4.0 + 1.0, 5 * U, cz * 4.0 + 1.0, AL_NAVY)
        m.box3d(-3.5, 2 * U, -3.5, 3.5, 14 * U, 3.5, AL_STONE)     # main shaft
        m.box3d(-2.5, 14 * U, -2.5, 2.5, 18 * U, 2.5, AL_NAVY)     # upper tower
        m.box3d(-1.0, 18 * U, -1.0, 1.0, 21.5 * U, 1.0, AL_STEEL)  # spire
        m.box3d(-4.6, 10 * U, -4.6, 4.6, 10.6 * U, 4.6, AL_STONE)  # balcony ring
        # ARCANE WINDOW (front, mid-height -- glowing blue)
        m.box3d(-1.9, 7 * U, 3.6, 1.9, 11 * U, 4.0, AL_GLOW,
                0.65 + math.sin(idleP) * 0.25)
        # Window cross runes
        m.box3d(-0.3, 7.5 * U, 4.0, 0.3, 10.5 * U, 4.2, AL_BLUE)
        m.box3d(-1.6, 8.9 * U, 4.0, 1.6, 9.5 * U, 4.2, AL_BLUE)
        # Orbiting arcane particles around peak
        spinAng = tickF * 38.0
        m.push()
        m.translate(0, 20 * U, 0)
        m.rotate(spinAng, 0, 1, 0)
        for i in range(5):
            a = i * 1.2566
            m.cube3(math.cos(a) * 3.2, 0, math.sin(a) * 3.2, 0.4, AL_GLOW, 0.55)
        m.pop()
        # Peak orb
        peakA = 0.55 + math.sin(tickF * 2.8) * 0.35
        m.cube3(0, 22.0 * U, 0, 1.1, AL_GLOW, peakA)
        m.cube3(0, 22.0 * U, 0, 2.2, AL_GLOW, peakA * 0.2)

    elif idx == 4:
        # -- 4: WORKSHOP -----------------------------------------------------
        # Wide stone hall, chimney with smoke, wooden scaffolding, forge glow
        m.box3d(-14.0, 0, -10.0, 14.0, 5.5 * U, 10.0, AL_STONE)        # main hall
        m.box3d(-14.0, 5.5 * U, -10.5, 14.0, 7 * U, 10.5, AL_NAVY)     # roof deck
        m.box3d(-14.5, 7 * U, -10.5, 14.5, 8.5 * U, 10.5, AL_STONE)    # front gable
        # CHIMNEY (left rear)
        m.box3d(-11.0, 5.5 * U, -2.0, -8.5, 14.5 * U, 2.0, AL_STONE)
        # Smoke puff (animated)
        puffY = math.sin(tickF * 1.6) * 2.0
        m.cube3(-9.75, 15.0 * U + puffY, 0, 0.85, AL_STONE, 0.25)
        m.cube3(-9.75, 16.2 * U + puffY * 1.3, 0, 0.6, AL_STONE, 0.14)
        # SCAFFOLDING (right side, wooden)
        m.box3d(11.5, 0, 8.0, 12.0, 10 * U, 8.6, 0x8B5A2B)    # left post
        m.box3d(13.2, 0, 8.0, 13.7, 10 * U, 8.6, 0x8B5A2B)    # right post
        for r in range(4):
            ry = 2.0 * U + r * 2.2 * U
            m.box3d(11.5, ry, 8.0, 13.7, ry + 0.5, 8.6, 0x8B5A2B)   # planks
        # Diagonal brace
        m.box3d(11.6, 0, 8.1, 13.6, 8 * U, 8.5, 0x5A3A1A, 0.5)
        # Forge glow (front window, orange)
        m.box3d(-2.5, 1.5 * U, 10.1, 2.5, 4.5 * U, 10.5, 0xFF8030,
                0.3 + math.sin(tickF * 2.0) * 0.1)
        # Tool silhouettes on front wall
        for t in range(-2, 3):
            tx = t * 3.2
            m.box3d(tx - 0.2, 5.8 * U, 10.1, tx + 0.2, 7.0 * U, 10.5, AL_STEEL)

    elif idx == 5:
        # -- 5: FOUNTAIN (Hero Spawn) ----------------------------------------
        # Circular stone basin, holy column with cross, spinning golden rings
        m.box3d(-7.5, 0, -7.5, 7.5, 1.0, 7.5, AL_STONE)          # basin floor
        # Water surface (blue, translucent)
        m.box3d(-6.5, 0.9, -6.5, 6.5, 1.3, 6.5, AL_GLOW, 0.25 + math.sin(idleP) * 0.1)
        # Basin rim pillars (8 around circle)
        for i in range(8):
            a = i * 0.7854
            rx, rz = math.cos(a) * 6.5, math.sin(a) * 6.5
            m.box3d(rx - 0.8, 0, rz - 0.8, rx + 0.8, 3.5 * U, rz + 0.8, AL_STONE)
        # Rim capstone band
        for i in range(8):
            a = i * 0.7854 + 0.3927
            rx, rz = math.cos(a) * 6.5, math.sin(a) * 6.5
            m.box3d(rx - 0.6, 3.3 * U, rz - 0.6, rx + 0.6, 3.9 * U, rz + 0.6, AL_STONE)
        # HOLY COLUMN (center)
        m.box3d(-1.3, 0, -1.3, 1.3, 7.5 * U, 1.3, AL_STONE)
        m.box3d(-2.2, 7.2 * U, -2.2, 2.2, 8 * U, 2.2, AL_STONE)   # column capital
        # Holy cross on front face of column
        m.box3d(-0.28, 1 * U, 1.35, 0.28, 6.5 * U, 1.6, AL_GOLD)   # vert
        m.box3d(-1.8, 3.8 * U, 1.35, 1.8, 4.5 * U, 1.6, AL_GOLD)   # horiz
        # FLOATING ORB (holy light)
        orbY = 8.5 * U + math.sin(idleP) * 1.1 * U
        orbA = 0.7 + math.sin(tickF * 2.0) * 0.2
        m.cube3(0, orbY, 0, 1.3, AL_GLOW, orbA)
        m.cube3(0, orbY, 0, 2.8, AL_GLOW, orbA * 0.18)
        # Spinning ring of golden beads
        m.push()
        m.translate(0, orbY, 0)
        m.rotate(tickF * 50.0, 0, 1, 0)
        for i in range(6):
            a = i * 1.0472
            m.cube3(math.cos(a) * 4.0, 0, math.sin(a) * 4.0, 0.35, AL_GOLD, 0.65)
        m.pop()
        # Second ring (tilted, opposite spin)
        m.push()
        m.translate(0, orbY, 0)
        m.rotate(18.0, 1, 0, 0)
        m.rotate(tickF * (-35.0), 0, 1, 0)
        for i in range(4):
            a = i * 1.5708
            m.cube3(math.cos(a) * 3.5, 0, math.sin(a) * 3.5, 0.3, AL_GLOW, 0.5)
        m.pop()

    elif idx == 6:
        # -- 6: GOLD MINE (neutral resource) ---------------------------------
        # Rock mound, timber-framed mine entrance, ore cart, scaffolding
        m.box3d(-13.0, 0, -11.0, 13.0, 5 * U, 11.0, 0x504840)
        m.box3d(-8.0, 5 * U, -7.0, 8.0, 9 * U, 7.0, 0x605040)
        m.box3d(-5.0, 9 * U, -4.0, 5.0, 11 * U, 4.0, 0x706050)
        # Mine entrance arch (stone)
        m.box3d(-4.5, 0, 9.0, -2.5, 4.5 * U, 11.0, 0x504840)      # left post
        m.box3d(2.5, 0, 9.0, 4.5, 4.5 * U, 11.0, 0x504840)        # right post
        m.box3d(-4.5, 4.5 * U, 9.0, 4.5, 5.5 * U, 11.0, 0x504840)  # lintel
        # Timber frame on entrance
        m.box3d(-4.8, 0, 9.0, -4.3, 5.5 * U, 11.2, 0x8B5A2B)
        m.box3d(4.3, 0, 9.0, 4.8, 5.5 * U, 11.2, 0x8B5A2B)
        m.box3d(-4.8, 5.5 * U, 9.0, 4.8, 6.1 * U, 11.2, 0x8B5A2B)
        # Gold vein shimmer inside
        m.cube3(0, 2.5 * U, 10.5, 1.1, AL_GOLD, 0.45 + math.sin(idleP) * 0.3)
        # Cart tracks (two rails)
        m.box3d(-0.9, 0, 2.0, -0.5, 0.5, 9.0, 0x705030)
        m.box3d(0.5, 0, 2.0, 0.9, 0.5, 9.0, 0x705030)
        # Ore cart (rolling on tracks)
        cartZ = 3.0 + abs(math.sin(tickF * 0.3)) * 5.0
        m.box3d(-1.5, 0.5, cartZ, 1.5, 2 * U, cartZ + 2.5, 0x6B4010)
        m.cube3(0, 1.3 * U, cartZ + 1.25, 0.7, AL_GOLD, 0.5)      # ore inside cart
        # Cart wheels
        m.cube3(-1.6, 0.5, cartZ + 0.5, 0.45, AL_DARK, 0.9)
        m.cube3(-1.6, 0.5, cartZ + 2.0, 0.45, AL_DARK, 0.9)
        m.cube3(1.6, 0.5, cartZ + 0.5, 0.45, AL_DARK, 0.9)
        m.cube3(1.6, 0.5, cartZ + 2.0, 0.45, AL_DARK, 0.9)
        # Scaffolding (two uprights + cross beam)
        m.box3d(-4.5, 5.5 * U, -3.0, -3.5, 9.5 * U, 3.0, 0x706050)
        m.box3d(3.5, 5.5 * U, -3.0, 4.5, 9.5 * U, 3.0, 0x706050)
        m.box3d(-4.5, 9.5 * U, -1.0, 4.5, 10.0 * U, 1.0, 0x706050)

    else:
        return None     # the C++ answers an unknown bldgIdx with "return false"

    return m.build(**bake)
