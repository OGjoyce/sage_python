"""Radiant 3D unit models -- Maya solar warlord aesthetic.

Port of drawRadiantUnit3D in src/gfx/models3d/radiant_units.cpp, C++ numbers
verbatim. Buildings from the same file are in radiant_bldg.py.

Units: Acolyte(0) Vanguard(1) Marksman(2) Templar(3) Oracle(4) Cleric(5)
       Trebuchet(6)
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
RD_OBSID = 0x181820   # obsidian (macahuitl blades)
RD_JAGUAR = 0xC07830  # jaguar tawny pelt

NAMES = ("Acolyte", "Vanguard", "Marksman", "Templar", "Oracle", "Cleric", "Trebuchet")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the unit, as unitIdx does in the C++."""
    m = GLModel(name or f"RADIANT_unit{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")

    idleP = tickF * 0.9
    walkP = tickF * 2.8
    atkP = tickF * 3.2
    if anim == 1:
        bob = abs(math.sin(walkP)) * 1.5
    elif anim == 0:
        bob = math.sin(idleP) * 0.4
    else:
        bob = 0.0

    m.push()
    m.translate(0, bob, 0)

    if idx == 0:
        # -- 0: ACOLYTE (Worker) ---------------------------------------------
        # Brown-skinned figure in simple cloth robe, pick tool + clay pot
        lY1 = 3.5 * U
        gaitL = math.sin(walkP) * 16.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-0.9, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(0.9, -lY1, 0)
        m.box3d(-1.6, 0, -0.9, -0.2, lY1, 0.9, RD_CLOTH)
        m.pop()
        m.push()
        m.translate(0.9, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-0.9, -lY1, 0)
        m.box3d(0.2, 0, -0.9, 1.6, lY1, 0.9, RD_CLOTH)
        m.pop()
        # Robe torso
        m.box3d(-2.0, lY1, -1.2, 2.0, lY1 + 3.5 * U, 1.2, RD_CLOTH)
        m.box3d(-1.8, lY1 + 3.4 * U, -1.25, 1.8, lY1 + 3.7 * U, 1.25, RD_TRIM)  # collar
        # Neck + head
        m.box3d(-0.7, lY1 + 3.7 * U, -0.6, 0.7, lY1 + 4.0 * U, 0.6, RD_SKIN)
        m.box3d(-1.2, lY1 + 4.0 * U, -1.0, 1.2, lY1 + 5.6 * U, 1.0, RD_SKIN)
        m.box3d(-1.25, lY1 + 4.9 * U, -1.05, 1.25, lY1 + 5.1 * U, 1.05, RD_TRIM)  # headband
        # Left arm holding clay pot
        m.box3d(-3.5, lY1 + 1.0 * U, -0.6, -2.0, lY1 + 2.8 * U, 0.6, RD_SKIN)
        potBob = math.sin(idleP) * 0.6 if anim == 0 else 0.0
        m.cube3(-3.8, lY1 + 0.9 * U + potBob, 0.0, 0.65, 0xA07850, 0.9)   # clay pot
        m.cube3(-3.8, lY1 + 1.6 * U + potBob, 0.0, 0.4, 0x906840, 0.7)    # pot rim
        # Right arm swinging pick on attack
        if anim == 2:
            swingAng = -30.0 + math.sin(atkP) * 80.0
        elif anim == 1:
            swingAng = math.sin(walkP) * 12.0
        else:
            swingAng = 0.0
        m.push()
        m.translate(2.0, lY1 + 2.0 * U, 0)
        m.rotate(swingAng, 1, 0, 0)
        m.translate(-2.0, -(lY1 + 2.0 * U), 0)
        m.box3d(2.0, lY1 + 0.8 * U, -0.6, 3.5, lY1 + 2.5 * U, 0.6, RD_SKIN)     # arm
        m.box3d(3.0, lY1 - 0.8 * U, -0.3, 3.6, lY1 + 1.0 * U, 0.3, RD_STONE)    # handle
        m.box3d(2.9, lY1 - 1.0 * U, -0.55, 4.2, lY1 - 0.1 * U, 0.55, RD_DARK)   # pick head
        m.pop()

    elif idx == 1:
        # -- 1: VANGUARD (Melee) ---------------------------------------------
        # Heavy lamellar plate, macahuitl obsidian club, sun-disc shield
        lY1 = 4.0 * U
        gaitL = math.sin(walkP) * 18.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-1.5, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(1.5, -lY1, 0)
        m.box3d(-2.8, 0, -1.6, -0.2, lY1, 1.6, RD_PLATE)
        m.box3d(-2.9, lY1 * 0.45, -1.7, -0.1, lY1 * 0.65, 1.7, RD_DARK)   # knee guard
        m.pop()
        m.push()
        m.translate(1.5, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-1.5, -lY1, 0)
        m.box3d(0.2, 0, -1.6, 2.8, lY1, 1.6, RD_PLATE)
        m.box3d(0.1, lY1 * 0.45, -1.7, 2.9, lY1 * 0.65, 1.7, RD_DARK)
        m.pop()
        # Heavy torso cuirass
        m.box3d(-4.0, lY1, -2.0, 4.0, lY1 + 4.5 * U, 2.0, RD_PLATE)
        m.box3d(-4.1, lY1 + 1.5 * U, -2.1, 4.1, lY1 + 2.0 * U, 2.1, RD_DARK)  # lamellar
        m.cube3(0.0, lY1 + 2.2 * U, 2.1, 0.9, RD_GOLD, 0.85)            # chest sun-disc
        # Large pauldrons
        m.box3d(-6.5, lY1 + 2.5 * U, -1.8, -4.0, lY1 + 4.5 * U, 1.8, RD_DARK)
        m.box3d(4.0, lY1 + 2.5 * U, -1.8, 6.5, lY1 + 4.5 * U, 1.8, RD_DARK)
        m.box3d(-6.6, lY1 + 3.5 * U, -0.5, -4.0, lY1 + 3.8 * U, 0.5, RD_JADE)
        m.box3d(4.0, lY1 + 3.5 * U, -0.5, 6.6, lY1 + 3.8 * U, 0.5, RD_JADE)
        # Helm + solar crest
        m.box3d(-2.0, lY1 + 4.5 * U, -1.5, 2.0, lY1 + 6.5 * U, 1.5, RD_PLATE)
        m.box3d(-1.5, lY1 + 4.7 * U, 1.5, 1.5, lY1 + 5.7 * U, 1.9, RD_DARK, 0.7)  # visor
        m.box3d(-0.4, lY1 + 6.5 * U, -0.3, 0.4, lY1 + 7.5 * U, 0.3, RD_GOLD)  # sun crest
        # SHIELD (left side -- rectangular, gold sun symbol)
        if anim == 2:
            shieldAng = math.sin(atkP) * 15.0
        elif anim == 1:
            shieldAng = math.sin(walkP) * 5.0
        else:
            shieldAng = 0.0
        m.push()
        m.translate(-5.5, lY1 + 2.0 * U, 0)
        m.rotate(-shieldAng, 0, 1, 0)
        m.box3d(-0.4, -1.5 * U, -2.2, 0.4, 2.5 * U, 2.2, RD_PLATE)     # shield body
        m.box3d(-0.45, -0.9 * U, -0.9, 0.0, 0.9 * U, 0.9, RD_GOLD)     # sun symbol
        m.pop()
        # MACAHUITL (obsidian club, right arm)
        if anim == 2:
            swingA = -40.0 + math.sin(atkP) * 90.0
        elif anim == 1:
            swingA = math.sin(walkP) * 10.0
        else:
            swingA = 0.0
        m.push()
        m.translate(5.0, lY1 + 2.5 * U, 0)
        m.rotate(swingA, 1, 0, 0)
        m.translate(-5.0, -(lY1 + 2.5 * U), 0)
        m.box3d(4.0, lY1 + 0.5 * U, -0.6, 6.5, lY1 + 2.5 * U, 0.6, RD_SKIN)      # arm
        m.box3d(5.5, lY1 - 3.5 * U, -0.55, 6.5, lY1 + 0.8 * U, 0.55, RD_STONE)   # handle
        m.box3d(5.0, lY1 - 3.7 * U, -1.0, 7.0, lY1 + 0.5 * U, 1.0, RD_DARK)      # body
        # Obsidian blade studs along both edges
        for i in range(4):
            oy = lY1 - 3.2 * U + i * 0.8 * U
            m.box3d(4.8, oy, -1.15, 5.2, oy + 0.4, -1.0, RD_OBSID)
            m.box3d(6.8, oy, -1.15, 7.2, oy + 0.4, -1.0, RD_OBSID)
        m.pop()

    elif idx == 2:
        # -- 2: MARKSMAN (Ranged) --------------------------------------------
        # Lighter armor, atlatl dart-thrower, feathered quiver, plume helm
        lY1 = 3.8 * U
        gaitL = math.sin(walkP) * 20.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-1.0, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(1.0, -lY1, 0)
        m.box3d(-1.8, 0, -1.1, -0.2, lY1, 1.1, RD_CLOTH)
        m.pop()
        m.push()
        m.translate(1.0, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-1.0, -lY1, 0)
        m.box3d(0.2, 0, -1.1, 1.8, lY1, 1.1, RD_CLOTH)
        m.pop()
        # Lighter torso -- partial plate + cloth
        m.box3d(-2.5, lY1, -1.4, 2.5, lY1 + 3.8 * U, 1.4, RD_PLATE, 0.8)
        m.box3d(-2.0, lY1 + 3.4 * U, -1.3, 2.0, lY1 + 3.8 * U, 1.3, RD_JADE)   # collar
        # Head + plume helm
        m.box3d(-1.5, lY1 + 3.8 * U, -1.0, 1.5, lY1 + 5.5 * U, 1.0, RD_PLATE)
        m.box3d(-0.3, lY1 + 5.5 * U, -0.2, 0.3, lY1 + 7.3 * U, 0.2, RD_JADE)   # plume stem
        m.box3d(-0.55, lY1 + 6.2 * U, -0.15, 0.55, lY1 + 7.8 * U, 0.15,
                RD_GOLD, 0.7)                                                  # gold tip
        # QUIVER on back (tube with 3 dart feather ends)
        m.box3d(1.5, lY1 + 1.5 * U, -1.65, 2.2, lY1 + 3.8 * U, -1.25, RD_STONE)
        for i in range(3):
            qx = 1.6 + i * 0.2
            m.box3d(qx, lY1 + 3.6 * U, -1.68, qx + 0.12, lY1 + 4.3 * U, -1.22,
                    RD_JADE, 0.8)
        # ATLATL (dart-thrower, left arm, elevates on attack)
        if anim == 2:
            atkElev = -25.0 - math.sin(atkP) * 40.0
        elif anim == 1:
            atkElev = math.sin(walkP) * 5.0
        else:
            atkElev = 0.0
        m.push()
        m.translate(-2.5, lY1 + 2.5 * U, 0)
        m.rotate(atkElev, 1, 0, 0)
        m.translate(2.5, -(lY1 + 2.5 * U), 0)
        m.box3d(-4.0, lY1 + 1.5 * U, -0.5, -2.5, lY1 + 2.5 * U, 0.5, RD_SKIN)   # arm
        m.box3d(-4.5, lY1 + 1.5 * U, -0.3, -2.5, lY1 + 2.0 * U, 0.3, RD_STONE)  # board
        m.box3d(-9.0, lY1 + 1.85 * U, -0.15, -4.5, lY1 + 2.1 * U, 0.15,
                RD_STONE)                                                       # dart shaft
        m.cube3(-9.1, lY1 + 1.97 * U, 0.0, 0.2, RD_GOLD, 0.9)                   # dart tip
        if anim == 2 and math.sin(atkP) > 0.5:
            m.cube3(-9.2, lY1 + 1.97 * U, 0.0, 0.5, RD_GOLD, math.sin(atkP))
        m.pop()

    elif idx == 3:
        # -- 3: TEMPLAR (Heavy -- armored jaguar mount) ----------------------
        # Wide quad-leg jaguar body + plate rider, great spear
        legBobFR = math.sin(walkP) * 2.5 if anim == 1 else 0.0
        legBobRL = -legBobFR
        # Front legs
        m.box3d(-5.0, legBobFR, -5.5, -1.5, 3.5 * U, -1.0, RD_JAGUAR)
        m.box3d(1.5, -legBobFR, -5.5, 5.0, 3.5 * U, -1.0, RD_JAGUAR)
        # Rear legs
        m.box3d(-5.0, legBobRL, 1.0, -1.5, 3.5 * U, 5.5, RD_JAGUAR)
        m.box3d(1.5, -legBobRL, 1.0, 5.0, 3.5 * U, 5.5, RD_JAGUAR)
        # Jaguar main body hull
        m.box3d(-5.5, 3.5 * U, -5.0, 5.5, 6.5 * U, 5.0, RD_JAGUAR)
        # Armored barding plates
        m.box3d(-6.0, 4.0 * U, -4.5, -5.5, 6.0 * U, 4.5, RD_PLATE)
        m.box3d(5.5, 4.0 * U, -4.5, 6.0, 6.0 * U, 4.5, RD_PLATE)
        m.box3d(-5.5, 6.5 * U, -4.5, 5.5, 7.0 * U, 4.5, RD_PLATE)   # back plate
        # Dark jaguar spot pattern
        for i in (-1, 0, 1):
            sx = i * 2.8
            m.cube3(sx, 5.5 * U, 0.5, 0.6, RD_DARK, 0.9)
            m.cube3(sx + 1.4, 4.5 * U, 4.0, 0.5, RD_DARK, 0.8)
        # Ceremonial jade+gold collar
        m.box3d(-5.5, 6.2 * U, -0.9, 5.5, 6.8 * U, 0.9, RD_JADE)
        m.box3d(-5.5, 6.4 * U, -0.95, 5.5, 6.6 * U, 0.95, RD_GOLD, 0.6)
        # Rider torso (heavy plate cuirass)
        m.box3d(-3.0, 7.0 * U, -2.0, 3.0, 11.0 * U, 2.0, RD_PLATE)
        m.box3d(-4.0, 8.5 * U, -1.8, -3.0, 11.0 * U, 1.8, RD_DARK)  # left pauldron
        m.box3d(3.0, 8.5 * U, -1.8, 4.0, 11.0 * U, 1.8, RD_DARK)    # right pauldron
        m.cube3(0.0, 9.0 * U, 2.1, 0.8, RD_GOLD, 0.8)               # chest sun-disc
        # Great helm
        m.box3d(-2.2, 11.0 * U, -1.5, 2.2, 13.0 * U, 1.5, RD_PLATE)
        m.box3d(-0.4, 13.0 * U, -0.3, 0.4, 14.0 * U, 0.3, RD_GOLD)  # crest spike
        # GREAT SPEAR (elevates on attack)
        if anim == 2:
            spearElev = 30.0 - math.sin(atkP) * 55.0
        elif anim == 0:
            spearElev = 15.0 + math.sin(idleP) * 3.0
        else:
            spearElev = 15.0
        m.push()
        m.translate(3.0, 10.0 * U, 0)
        m.rotate(-spearElev, 1, 0, 0)
        m.translate(-3.0, -10.0 * U, 0)
        m.box3d(2.5, 10.0 * U - 0.4, -0.4, 4.0, 10.0 * U + 0.4, 0.4, RD_PLATE)  # guard
        m.box3d(3.5, 10.0 * U - 0.3, -0.3, 3.5 + 9.0 * U, 10.0 * U + 0.3, 0.3,
                RD_STONE)                                                        # shaft
        m.cube3(3.5 + 9.0 * U, 10.0 * U, 0.0, 0.5, RD_GOLD, 0.9)                 # tip
        if anim == 2 and math.sin(atkP) > 0.4:
            m.cube3(3.5 + 9.0 * U, 10.0 * U, 0.0, 0.9, RD_GOLD, math.sin(atkP))
        m.pop()

    elif idx == 4:
        # -- 4: ORACLE (Mage) ------------------------------------------------
        # Robed seer, tall feathered headdress, sun-disc staff, orbiting pendant
        lY1 = 3.5 * U
        gaitL = math.sin(walkP) * 12.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-0.9, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(0.9, -lY1, 0)
        m.box3d(-1.5, 0, -1.0, -0.3, lY1, 1.0, RD_CLOTH, 0.75)
        m.pop()
        m.push()
        m.translate(0.9, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-0.9, -lY1, 0)
        m.box3d(0.3, 0, -1.0, 1.5, lY1, 1.0, RD_CLOTH, 0.75)
        m.pop()
        # Wide ceremonial robe
        m.box3d(-3.0, lY1, -1.5, 3.0, lY1 + 4.0 * U, 1.5, RD_CLOTH)
        m.box3d(-3.1, lY1 + 3.7 * U, -1.6, 3.1, lY1 + 4.0 * U, 1.6, RD_TRIM)  # collar
        m.box3d(-3.1, lY1, -1.6, 3.1, lY1 + 0.4 * U, 1.6, RD_TRIM)            # hem
        # Jade chest pendant
        m.cube3(0.0, lY1 + 2.5 * U, 1.6, 0.45, RD_JADE, 0.9)
        # Neck + head
        m.box3d(-0.8, lY1 + 4.0 * U, -0.7, 0.8, lY1 + 4.3 * U, 0.7, RD_SKIN)
        m.box3d(-1.5, lY1 + 4.3 * U, -1.2, 1.5, lY1 + 5.8 * U, 1.2, RD_SKIN)
        # FEATHERED HEADDRESS (large, iconic -- 5 feathers)
        m.box3d(-2.5, lY1 + 5.8 * U, -0.4, 2.5, lY1 + 6.3 * U, 0.4, RD_JADE)  # base band
        for i in range(-2, 3):
            fx = i * 1.1
            fh = 2.5 * U - abs(float(i)) * 0.3 * U
            fc = RD_JADE if i % 2 == 0 else RD_GOLD
            m.box3d(fx - 0.25, lY1 + 6.3 * U, -0.2, fx + 0.25, lY1 + 6.3 * U + fh, 0.2,
                    fc, 0.9)
        # SUN-DISC STAFF (left side, vertical -- disc at top, above headdress)
        staffPulse = 0.6 + math.sin(idleP * 2.0) * 0.3
        m.box3d(-4.0, 0.0, -0.3, -3.6, lY1 + 2.8 * U, 0.3, RD_STONE)      # lower shaft
        m.box3d(-4.0, lY1 + 1.0 * U, -0.55, -2.8, lY1 + 2.8 * U, 0.55, RD_SKIN)  # arm
        m.box3d(-4.0, lY1 + 2.8 * U, -0.3, -3.6, lY1 + 8.5 * U, 0.3, RD_STONE)  # upper
        # Sun disc at top
        m.cube3(-3.8, lY1 + 8.6 * U, 0.0, 1.1, RD_GOLD, staffPulse)
        m.cube3(-3.8, lY1 + 8.6 * U, 0.0, 2.0, RD_GOLD, staffPulse * 0.25)
        # Attack glow blast
        if anim == 2 and math.sin(atkP) > 0.3:
            m.cube3(-3.8, lY1 + 8.6 * U, 3.0, 0.8, RD_GOLD, math.sin(atkP))
        # ORBITING JADE PENDANT (slowly rotates around the figure)
        m.push()
        m.translate(0.0, lY1 + 2.0 * U, 0.0)
        m.rotate(tickF * 60.0, 0, 1, 0)
        m.cube3(5.0, 0.0, 0.0, 0.5, RD_JADE, 0.85)
        m.pop()

    elif idx == 5:
        # -- 5: CLERIC (Healer) ----------------------------------------------
        # Ceremonial robes, sun-cross on chest, healing stave with golden orb
        lY1 = 3.5 * U
        gaitL = math.sin(walkP) * 14.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-1.0, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(1.0, -lY1, 0)
        m.box3d(-1.7, 0, -1.1, -0.3, lY1, 1.1, RD_PLATE, 0.7)
        m.pop()
        m.push()
        m.translate(1.0, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-1.0, -lY1, 0)
        m.box3d(0.3, 0, -1.1, 1.7, lY1, 1.1, RD_PLATE, 0.7)
        m.pop()
        # Ceremonial cream robe
        m.box3d(-2.8, lY1, -1.4, 2.8, lY1 + 4.0 * U, 1.4, 0xE8D8A0)
        m.box3d(-2.9, lY1 + 3.8 * U, -1.5, 2.9, lY1 + 4.2 * U, 1.5, RD_JADE)  # collar
        m.box3d(-0.3, lY1 + 0.5 * U, -1.5, 0.3, lY1 + 3.8 * U, 1.5, RD_TRIM)  # stripe
        # SUN-CROSS on chest (gold)
        m.box3d(-0.25, lY1 + 1.5 * U, 1.5, 0.25, lY1 + 3.0 * U, 1.9, RD_GOLD)  # vertical
        m.box3d(-1.1, lY1 + 2.0 * U, 1.5, 1.1, lY1 + 2.5 * U, 1.9, RD_GOLD)    # horizontal
        # Head + ceremonial cap
        m.box3d(-1.5, lY1 + 4.2 * U, -1.1, 1.5, lY1 + 5.8 * U, 1.1, RD_SKIN)
        m.box3d(-1.6, lY1 + 5.4 * U, -1.2, 1.6, lY1 + 5.9 * U, 1.2, RD_PLATE)
        m.cube3(0.0, lY1 + 6.0 * U, 0.0, 0.35, RD_GOLD, 0.85)
        # HEALING STAVE (right arm -- elevates and pulses)
        if anim == 2:
            healAng = -30.0 + math.sin(atkP) * 60.0
        elif anim == 0:
            healAng = math.sin(idleP) * 6.0
        else:
            healAng = 0.0
        healPulse = 0.5 + math.sin(idleP * 3.0) * 0.35
        m.push()
        m.translate(3.0, lY1 + 1.5 * U, 0)
        m.rotate(healAng, 0, 0, 1)
        m.translate(-3.0, -(lY1 + 1.5 * U), 0)
        m.box3d(2.5, lY1 + 0.8 * U, -0.55, 3.5, lY1 + 2.5 * U, 0.55, RD_SKIN)    # arm
        m.box3d(2.8, lY1 + 2.4 * U, -0.35, 3.2, lY1 + 5.8 * U, 0.35, RD_STONE)   # shaft
        m.cube3(3.0, lY1 + 5.9 * U, 0.0, 0.75, RD_GOLD, healPulse)               # orb
        m.cube3(3.0, lY1 + 5.9 * U, 0.0, 1.4, RD_GOLD, healPulse * 0.25)         # glow
        # Healing beam on attack
        if anim == 2 and math.sin(atkP) > 0.3:
            m.cube3(3.0, lY1 + 5.9 * U, 4.0, 0.4, RD_JADE, math.sin(atkP) * 0.9)
        m.pop()

    elif idx == 6:
        # -- 6: TREBUCHET (Siege) --------------------------------------------
        # Stone masonry platform, step-fret frame, counterweight arm, 4 wheels
        m.box3d(-8.0, 0, -5.0, 8.0, 2 * U, 5.0, RD_STONE)
        # Step-fret front decoration
        m.box3d(-8.0, U, -5.15, 8.0, 1.5 * U, -5.0, RD_DARK)
        for i in range(-3, 4):
            bx = float(i) * 2.0
            m.box3d(bx - 0.5, 1.3 * U, -5.2, bx + 0.5, 1.8 * U, -5.05, RD_TRIM)
        # 4 thick stone wheels
        wheelA = walkP * 50.0 if anim == 1 else 0.0
        for wx in (-1, 1):
            for wz in (-1, 1):
                m.push()
                m.translate(float(wx) * 5.0, 2.2, float(wz) * 4.0)
                m.rotate(wheelA * float(wx), 0, 0, 1)
                m.box3d(-0.55, -2.6, -1.4, 0.55, 2.6, 1.4, RD_STONE)   # vert spoke
                m.box3d(-2.6, -0.55, -1.4, 2.6, 0.55, 1.4, RD_STONE)   # horiz spoke
                m.cube3(0.0, 0.0, 0.0, 0.8, RD_DARK, 0.9)              # hub
                m.pop()
        # A-frame uprights
        m.box3d(-5.0, 2 * U, -1.5, -3.5, 9 * U, 1.5, RD_STONE)
        m.box3d(3.5, 2 * U, -1.5, 5.0, 9 * U, 1.5, RD_STONE)
        m.box3d(-3.5, 8.3 * U, -1.2, 3.5, 9.0 * U, 1.2, RD_STONE)   # crossbar
        # Jade accent bands on frame
        m.box3d(-5.1, 5.5 * U, -1.6, 5.1, 6.0 * U, 1.6, RD_JADE, 0.6)
        m.cube3(0.0, 9.0 * U, 0.0, 0.9, RD_DARK, 0.9)               # pivot hub
        # COUNTERWEIGHT ARM (elevates on attack)
        if anim == 2:
            armElev = 50.0 + math.sin(atkP) * 70.0
        elif anim == 0:
            armElev = 30.0 + math.sin(idleP) * 5.0
        else:
            armElev = 30.0
        m.push()
        m.translate(0.0, 9.0 * U, 0.0)
        m.rotate(-armElev, 1, 0, 0)
        # Long throwing arm
        m.box3d(-0.8, 0, -0.8, 0.8, 8 * U, 0.8, RD_STONE)
        # Gold ring ornaments along arm
        for r in (1, 2, 3):
            m.box3d(-1.0, float(r) * 2.0 * U, -1.0, 1.0, float(r) * 2.0 * U + 0.4, 1.0,
                    RD_TRIM)
        # Sling payload end
        m.cube3(0.0, 8.0 * U, 0.0, 0.9, RD_DARK, 0.9)
        # Counterweight (short arm, heavy stone)
        m.box3d(-0.6, -2 * U, -0.6, 0.6, 0.0, 0.6, RD_STONE, 1.1)
        m.cube3(0.0, -2.6 * U, 0.0, 1.3, RD_STONE, 1.2)
        m.cube3(0.0, -2.6 * U, 0.0, 1.5, RD_DARK, 0.4)
        # Launch boulder flash
        if anim == 2 and math.sin(atkP) > 0.4:
            m.cube3(0.0, 9.0 * U, 0.0, 1.0, RD_GOLD, math.sin(atkP) * 0.8)
        m.pop()
        # Recoil kick on fire. In the C++ this glTranslatef lands after every
        # draw in the case and before the matrix is popped, so it moves nothing
        # -- kept here so the port stays line-for-line rather than silently
        # "fixing" it; if it is meant to shift the machine it has to come first.
        if anim == 2:
            m.translate(-abs(math.sin(atkP)) * 1.5, 0.0, 0.0)

    else:
        return None     # the C++ answers an unknown unitIdx with "return false"

    m.pop()
    return m.build(**bake)
