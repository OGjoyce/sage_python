"""Alliance 3D unit models.

Port of drawAllianceUnit3D in src/gfx/models3d/alliance_units.cpp, C++
numbers verbatim. Buildings from the same file are in alliance_bldg.py.

Units: Peasant(0) Footman(1) Rifleman(2) Knight(3) Sorceress(4) Priest(5)
       Cannon(6)
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

NAMES = ("Peasant", "Footman", "Rifleman", "Knight", "Sorceress", "Priest",
         "Cannon")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the unit, as unitIdx does in the C++."""
    m = GLModel(name or f"ALLIANCE_unit{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")

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
        # -- 0: PEASANT (Worker) ---------------------------------------------
        # Small civilian -- cloth tunic, boots, hammer tool
        lY1 = 3.5 * U
        gaitL = math.sin(walkP) * 20.0 if anim == 1 else 0.0
        gaitR = -gaitL
        # Legs (slim, cloth trousers)
        m.push()
        m.translate(-1.0, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(1.0, -lY1, 0)
        m.box3d(-1.8, 0, -0.9, -0.2, lY1, 0.9, AL_CLOTH)
        m.pop()
        m.push()
        m.translate(1.0, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-1.0, -lY1, 0)
        m.box3d(0.2, 0, -0.9, 1.8, lY1, 0.9, AL_CLOTH)
        m.pop()
        # Boots
        m.box3d(-2.1, 0, -1.1, -0.1, U * 0.65, 1.1, AL_NAVY)
        m.box3d(0.1, 0, -1.1, 2.1, U * 0.65, 1.1, AL_NAVY)
        # Torso (tunic)
        m.box3d(-2.5, lY1, -1.3, 2.5, lY1 + 3 * U, 1.3, AL_CLOTH)
        # Belt
        m.box3d(-2.6, lY1 + 0.1, -1.4, 2.6, lY1 + 0.65, 1.4, AL_NAVY)
        # Left arm (swings opposite to right)
        if anim == 1:
            armSwing = math.sin(walkP) * 18.0
        elif anim == 2:
            armSwing = -30.0 + math.sin(atkP) * 40.0
        else:
            armSwing = 0.0
        m.push()
        m.translate(-2.5, lY1 + 2.5 * U, 0)
        m.rotate(armSwing, 1, 0, 0)
        m.translate(2.5, -(lY1 + 2.5 * U), 0)
        m.box3d(-3.6, lY1 + 1.3 * U, -0.7, -2.4, lY1 + 2.7 * U, 0.7, AL_CLOTH)
        m.pop()
        # Right arm (holds hammer)
        m.push()
        m.translate(2.5, lY1 + 2.5 * U, 0)
        m.rotate(-armSwing, 1, 0, 0)
        m.translate(-2.5, -(lY1 + 2.5 * U), 0)
        m.box3d(2.4, lY1 + 1.3 * U, -0.7, 3.6, lY1 + 2.7 * U, 0.7, AL_CLOTH)
        m.box3d(3.3, lY1 + 0.4 * U, -0.25, 3.7, lY1 + 3.0 * U, 0.25, AL_NAVY)  # shaft
        m.box3d(2.8, lY1 + 2.8 * U, -0.75, 4.2, lY1 + 3.6 * U, 0.75, AL_STEEL)  # head
        m.pop()
        # Head (small, human)
        m.box3d(-1.5, lY1 + 3 * U, -1.0, 1.5, lY1 + 5 * U, 1.0, AL_CLOTH)
        # Brim hat
        m.box3d(-2.1, lY1 + 4.8 * U, -1.4, 2.1, lY1 + 5.2 * U, 1.4, AL_NAVY)
        m.box3d(-1.4, lY1 + 5.1 * U, -0.9, 1.4, lY1 + 5.9 * U, 0.9, AL_NAVY)

    elif idx == 1:
        # -- 1: FOOTMAN (Melee) ----------------------------------------------
        # Stocky armored soldier -- royal blue plate, kite shield, sword
        lY1 = 4 * U
        gaitL = math.sin(walkP) * 18.0 if anim == 1 else 0.0
        gaitR = -gaitL
        atkL = math.sin(atkP) * 10.0 if anim == 2 else 0.0
        # Legs (plate armored)
        m.push()
        m.translate(-1.5, lY1, 0)
        m.rotate(gaitL + atkL, 1, 0, 0)
        m.translate(1.5, -lY1, 0)
        m.box3d(-2.5, 0, -1.5, -0.5, lY1, 1.5, AL_BLUE)
        m.pop()
        m.push()
        m.translate(1.5, lY1, 0)
        m.rotate(gaitR + atkL, 1, 0, 0)
        m.translate(-1.5, -lY1, 0)
        m.box3d(0.5, 0, -1.5, 2.5, lY1, 1.5, AL_BLUE)
        m.pop()
        # Knee guards (gold)
        m.cube3(-1.5, lY1, 0, 0.6, AL_GOLD, 0.9)
        m.cube3(1.5, lY1, 0, 0.6, AL_GOLD, 0.9)
        # Greaves / boots
        m.box3d(-2.7, 0, -1.6, -0.4, U, 1.6, AL_NAVY)
        m.box3d(0.4, 0, -1.6, 2.7, U, 1.6, AL_NAVY)
        # Torso (wide plate chest)
        m.box3d(-3.5, lY1, -2.0, 3.5, lY1 + 4 * U, 2.0, AL_BLUE)
        # Chest cross crest
        m.box3d(-0.35, lY1 + 0.5 * U, 2.1, 0.35, lY1 + 3.5 * U, 2.5, AL_GOLD)  # vert
        m.box3d(-1.5, lY1 + 1.6 * U, 2.1, 1.5, lY1 + 2.3 * U, 2.5, AL_GOLD)    # horiz
        # Shoulder pads (broad navy)
        m.box3d(-6.0, lY1 + 2.5 * U, -1.8, -3.5, lY1 + 4 * U, 1.8, AL_NAVY)
        m.box3d(3.5, lY1 + 2.5 * U, -1.8, 6.0, lY1 + 4 * U, 1.8, AL_NAVY)
        # Head / Great Helm
        m.box3d(-2.2, lY1 + 4 * U, -1.8, 2.2, lY1 + 6 * U, 1.8, AL_NAVY)
        m.box3d(-1.5, lY1 + 4.3 * U, 1.8, 1.5, lY1 + 5.5 * U, 2.4, AL_STEEL, 0.4)
        # Gold helm plume
        m.box3d(-0.35, lY1 + 6 * U, -0.35, 0.35, lY1 + 7.2 * U, 0.35, AL_GOLD)
        # KITE SHIELD (left arm, rotates on attack)
        shieldAng = math.sin(atkP) * 12.0 if anim == 2 else 0.0
        m.push()
        m.translate(-4.5, lY1 + 2 * U, 0)
        m.rotate(shieldAng, 0, 1, 0)
        m.translate(4.5, -(lY1 + 2 * U), 0)
        m.box3d(-6.5, lY1 + 0.4 * U, -0.3, -4.0, lY1 + 4.0 * U, 0.3, AL_BLUE)
        m.box3d(-6.7, lY1 + 0.3 * U, -0.45, -3.9, lY1 + 4.1 * U, 0.45, AL_NAVY, 0.5)
        m.box3d(-5.7, lY1 + 0.9 * U, 0.32, -5.1, lY1 + 3.7 * U, 0.6, AL_GOLD)
        m.box3d(-6.4, lY1 + 1.9 * U, 0.32, -4.3, lY1 + 2.5 * U, 0.6, AL_GOLD)
        m.pop()
        # SWORD (right arm, swings on attack)
        if anim == 2:
            swordAng = -45.0 + math.sin(atkP) * 85.0
        elif anim == 1:
            swordAng = math.sin(walkP) * 10.0
        else:
            swordAng = 0.0
        m.push()
        m.translate(4.0, lY1 + 3 * U, 0)
        m.rotate(-swordAng, 0, 0, 1)
        m.translate(-4.0, -(lY1 + 3 * U), 0)
        m.box3d(3.5, lY1 + 1.5 * U, -0.6, 4.5, lY1 + 3 * U, 0.6, AL_BLUE)       # arm
        m.box3d(4.1, lY1 + 2.8 * U, -0.95, 4.8, lY1 + 3.3 * U, 0.95, AL_GOLD)   # guard
        m.box3d(4.35, lY1 + 3.3 * U, -0.3, 4.65, lY1 + 6.5 * U, 0.3, AL_STEEL)  # blade
        if anim == 2 and math.sin(atkP) > 0.5:
            m.cube3(4.5, lY1 + 6.5 * U, 0, 0.45, AL_GLOW, math.sin(atkP) * 0.6)
        m.pop()

    elif idx == 2:
        # -- 2: RIFLEMAN (Ranged) --------------------------------------------
        # Slim soldier, long rifle with scope, beret
        lY1 = 4 * U
        gaitL = math.sin(walkP) * 20.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-0.9, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(0.9, -lY1, 0)
        m.box3d(-1.5, 0, -0.9, -0.3, lY1, 0.9, AL_NAVY)
        m.pop()
        m.push()
        m.translate(0.9, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-0.9, -lY1, 0)
        m.box3d(0.3, 0, -0.9, 1.5, lY1, 0.9, AL_NAVY)
        m.pop()
        # Boots
        m.box3d(-1.8, 0, -1.0, -0.2, U * 0.7, 1.0, AL_DARK)
        m.box3d(0.2, 0, -1.0, 1.8, U * 0.7, 1.0, AL_DARK)
        # Torso (slim uniform)
        m.box3d(-2.0, lY1, -1.5, 2.0, lY1 + 4 * U, 1.5, AL_BLUE)
        # Epaulette (left shoulder, gold)
        m.box3d(-2.5, lY1 + 3 * U, -1.0, -1.5, lY1 + 4.2 * U, 1.0, AL_GOLD)
        # Head
        m.box3d(-1.5, lY1 + 4 * U, -1.2, 1.5, lY1 + 5.8 * U, 1.2, AL_CLOTH)
        # Beret (flat cap)
        m.box3d(-2.0, lY1 + 5.6 * U, -1.5, 2.0, lY1 + 6.1 * U, 1.5, AL_NAVY)
        m.box3d(-1.3, lY1 + 6.0 * U, -1.0, 1.3, lY1 + 6.5 * U, 1.0, AL_NAVY)
        # LONG RIFLE (right side, elevates)
        if anim == 2:
            rfElev = math.sin(atkP) * 12.0
        elif anim == 1:
            rfElev = math.sin(walkP) * 5.0
        else:
            rfElev = 0.0
        m.push()
        m.translate(2.5, lY1 + 2.5 * U, 0)
        m.rotate(-rfElev, 1, 0, 0)
        m.translate(-2.5, -(lY1 + 2.5 * U), 0)
        # Stock + housing
        m.box3d(2.0, lY1 + 1.5 * U, -0.45, 3.0, lY1 + 2.8 * U, 0.45, AL_NAVY)
        # Barrel (long -- 8*U)
        m.box3d(2.8, lY1 + 2.0 * U, -0.3, 2.8 + 8 * U, lY1 + 2.5 * U, 0.3, AL_STEEL)
        # Scope on top
        m.box3d(3.4, lY1 + 2.5 * U, -0.2, 3.4 + 3 * U, lY1 + 2.9 * U, 0.2, AL_DARK)
        m.cube3(3.4, lY1 + 2.7 * U, 0, 0.3, AL_GLOW, 0.45)      # scope lens
        # Bayonet tip
        m.box3d(2.8 + 7.8 * U, lY1 + 1.7 * U, -0.15, 2.8 + 9.2 * U, lY1 + 2.0 * U,
                0.15, AL_STEEL)
        # Muzzle flash
        if anim == 2 and math.sin(atkP) > 0.5:
            m.cube3(2.8 + 8 * U, lY1 + 2.25 * U, 0, 0.65, AL_GLOW, math.sin(atkP))
        m.pop()

    elif idx == 3:
        # -- 3: KNIGHT (Heavy) -----------------------------------------------
        # Full plate knight on armored warhorse -- 4 leg-posts, rider, lance
        horseH = 6 * U
        # Leg alternation (front-left+rear-right vs front-right+rear-left)
        legA = math.sin(walkP) * 2.5 if anim == 1 else 0.0
        legB = -legA
        # HORSE BODY (wide low platform)
        m.box3d(-4.0, 0, -6.0, 4.0, horseH, 6.0, 0xB09070)
        # 4 Leg posts at corners
        m.box3d(-3.5, legA, 3.0, -2.0, horseH * 0.65 + legA, 5.5, 0x907050)
        m.box3d(2.0, legB, 3.0, 3.5, horseH * 0.65 + legB, 5.5, 0x907050)
        m.box3d(-3.5, legB, -5.5, -2.0, horseH * 0.65 + legB, -3.0, 0x907050)
        m.box3d(2.0, legA, -5.5, 3.5, horseH * 0.65 + legA, -3.0, 0x907050)
        # Horse neck + head (front)
        m.box3d(-1.5, horseH - 2 * U, 5.0, 1.5, horseH + U, 8.0, 0x907050)
        m.box3d(-1.0, horseH - 3.5 * U, 7.5, 1.0, horseH - 1.5 * U, 9.5, 0x906050)
        # Mane
        m.box3d(-0.4, horseH, 1.0, 0.4, horseH + 1.8 * U, 6.0, AL_DARK)
        # Tail
        m.box3d(-0.5, horseH - 0.8 * U, -6.0, 0.5, horseH + 0.5 * U, -8.5, AL_DARK)
        # Blue caparison (horse armor cloth drape)
        m.box3d(-4.3, horseH * 0.3, -5.0, 4.3, horseH - U, 5.0, AL_BLUE, 0.65)
        # Gold trim on caparison
        m.box3d(-4.4, horseH * 0.3, -5.1, 4.4, horseH * 0.3 + 0.6, 5.1, AL_GOLD)
        # RIDER torso
        rY = horseH
        m.box3d(-2.5, rY, -1.5, 2.5, rY + 3.5 * U, 1.5, AL_BLUE)
        # Rider shoulder pads
        m.box3d(-4.0, rY + 2 * U, -1.0, -2.5, rY + 3.5 * U, 1.0, AL_NAVY)
        m.box3d(2.5, rY + 2 * U, -1.0, 4.0, rY + 3.5 * U, 1.0, AL_NAVY)
        # Rider head (great helm)
        m.box3d(-1.8, rY + 3.5 * U, -1.5, 1.8, rY + 5.5 * U, 1.5, AL_NAVY)
        m.box3d(-1.3, rY + 3.7 * U, 1.5, 1.3, rY + 4.8 * U, 2.2, AL_STEEL, 0.45)
        # Gold plume
        m.box3d(-0.3, rY + 5.5 * U, -0.3, 0.3, rY + 6.8 * U, 0.3, AL_GOLD)
        # LANCE (right arm, elevated -- pivots on attack)
        lanceElev = 20.0 + math.sin(atkP) * 30.0 if anim == 2 else 14.0
        m.push()
        m.translate(3.0, rY + 2.5 * U, 0)
        m.rotate(-lanceElev, 1, 0, 0)
        m.translate(-3.0, -(rY + 2.5 * U), 0)
        m.box3d(2.5, rY + 1.5 * U, -0.4, 4.0, rY + 3 * U, 0.4, AL_BLUE)         # arm
        m.box3d(3.2, rY + 2.5 * U, -0.3, 3.6, rY + 2.5 * U + 10 * U, 0.3, AL_CLOTH)
        m.box3d(3.0, rY + 2.5 * U + 9.5 * U, -0.5, 3.8, rY + 2.5 * U + 11 * U, 0.5,
                AL_STEEL)
        if anim == 2 and math.sin(atkP) > 0.4:
            m.cube3(3.4, rY + 2.5 * U + 11 * U, 0, 0.55, AL_GLOW, math.sin(atkP) * 0.7)
        m.pop()

    elif idx == 4:
        # -- 4: SORCERESS (Mage) ---------------------------------------------
        # Slim robed mage -- navy robe, glowing arcane staff, orb
        lY1 = 3 * U
        # Robe bottom (wide, flares out)
        m.box3d(-3.2, 0, -2.2, 3.2, lY1, 2.2, AL_NAVY)
        # Gold hem trim
        m.box3d(-3.3, 0, -2.3, 3.3, 0.6, 2.3, AL_GOLD)
        # Robe torso (tapers slightly)
        m.box3d(-2.5, lY1, -1.8, 2.5, lY1 + 3.5 * U, 1.8, AL_NAVY)
        # Gold belt / sash
        m.box3d(-2.6, lY1 + 0.1, -1.9, 2.6, lY1 + 0.7, 1.9, AL_GOLD)
        # Mantle / collar (cloth)
        m.box3d(-3.6, lY1 + 2.5 * U, -1.5, 3.6, lY1 + 3.6 * U, 1.5, AL_CLOTH)
        # Brooch on mantle
        m.cube3(0, lY1 + 3.0 * U, 1.6, 0.45, AL_GOLD, 0.9)
        # Head (face)
        m.box3d(-1.5, lY1 + 3.5 * U, -1.2, 1.5, lY1 + 5.3 * U, 1.2, AL_CLOTH)
        # Pointed hood
        m.box3d(-1.8, lY1 + 5.0 * U, -1.5, 1.8, lY1 + 5.5 * U, 1.5, AL_NAVY)
        m.box3d(-1.3, lY1 + 5.4 * U, -1.0, 1.3, lY1 + 6.0 * U, 1.0, AL_NAVY)
        m.box3d(-0.8, lY1 + 5.9 * U, -0.6, 0.8, lY1 + 6.5 * U, 0.6, AL_NAVY)
        # Right sleeve arm (gestures)
        if anim == 2:
            armAng = -20.0 + math.sin(atkP) * 35.0
        elif anim == 0:
            armAng = math.sin(idleP) * 8.0
        else:
            armAng = 0.0
        m.push()
        m.translate(2.5, lY1 + 2.5 * U, 0)
        m.rotate(-armAng, 0, 0, 1)
        m.translate(-2.5, -(lY1 + 2.5 * U), 0)
        m.box3d(2.0, lY1 + 0.8 * U, -0.8, 3.2, lY1 + 2.5 * U, 0.8, AL_NAVY)
        m.pop()
        # STAFF (left side -- tall)
        staffBob = math.sin(idleP) * 1.5
        m.box3d(-3.6, 0.5, -0.3, -3.0, lY1 + 5.5 * U + staffBob, 0.3, AL_CLOTH)
        # Orb at tip (pulsing glow)
        orbA = 0.7 + math.sin(tickF * 2.5) * 0.25
        m.cube3(-3.3, lY1 + 6.0 * U + staffBob, 0, 1.1, AL_GLOW, orbA)
        m.cube3(-3.3, lY1 + 6.0 * U + staffBob, 0, 2.0, AL_GLOW, orbA * 0.25)
        # Gold ring at staff top
        m.box3d(-3.7, lY1 + 5.0 * U, -0.4, -2.9, lY1 + 5.4 * U, 0.4, AL_GOLD)
        # Attack bolt (fires forward)
        if anim == 2 and math.sin(atkP) > 0.4:
            boltZ = 3.0 + math.sin(atkP) * 7.0
            m.cube3(0, lY1 + 3.5 * U, boltZ, 0.9, AL_GLOW, math.sin(atkP))

    elif idx == 5:
        # -- 5: PRIEST (Healer) ----------------------------------------------
        # Short robed figure -- holy cross on chest, shorter staff, gentle glow
        lY1 = 3 * U
        gaitL = math.sin(walkP) * 14.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-1.0, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(1.0, -lY1, 0)
        m.box3d(-1.6, 0, -0.9, -0.2, lY1, 0.9, AL_CLOTH)
        m.pop()
        m.push()
        m.translate(1.0, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-1.0, -lY1, 0)
        m.box3d(0.2, 0, -0.9, 1.6, lY1, 0.9, AL_CLOTH)
        m.pop()
        # Robe overlay (lower, cloth)
        m.box3d(-2.6, 0.1, -1.6, 2.6, lY1 * 0.9, 1.6, AL_CLOTH)
        # Torso robe
        m.box3d(-2.8, lY1, -1.7, 2.8, lY1 + 3 * U, 1.7, AL_CLOTH)
        # HOLY CROSS on chest (blue + gold trim)
        m.box3d(-0.3, lY1 + 0.5 * U, 1.8, 0.3, lY1 + 2.8 * U, 2.2, AL_BLUE)   # vert
        m.box3d(-1.3, lY1 + 1.4 * U, 1.8, 1.3, lY1 + 2.0 * U, 2.2, AL_BLUE)   # horiz
        m.box3d(-1.35, lY1 + 1.35 * U, 2.2, 1.35, lY1 + 2.05 * U, 2.4, AL_GOLD, 0.55)
        m.box3d(-0.35, lY1 + 0.45 * U, 2.2, 0.35, lY1 + 2.85 * U, 2.4, AL_GOLD, 0.55)
        # Shoulder drape
        m.box3d(-3.2, lY1 + 2.2 * U, -1.5, 3.2, lY1 + 3.1 * U, 1.5, AL_CLOTH)
        # Head
        m.box3d(-1.5, lY1 + 3 * U, -1.0, 1.5, lY1 + 4.8 * U, 1.0, AL_CLOTH)
        # Hood / coif
        m.box3d(-1.8, lY1 + 4.6 * U, -1.3, 1.8, lY1 + 5.0 * U, 1.3, AL_CLOTH)
        m.box3d(-1.0, lY1 + 4.9 * U, -0.8, 1.0, lY1 + 5.4 * U, 0.8, AL_CLOTH)
        # HOLY STAFF (right side, shorter -- swings on heal)
        if anim == 2:
            healSwing = -25.0 + math.sin(atkP) * 50.0
        elif anim == 0:
            healSwing = math.sin(idleP) * 6.0
        else:
            healSwing = 0.0
        m.push()
        m.translate(3.0, lY1 + 1.5 * U, 0)
        m.rotate(healSwing, 0, 0, 1)
        m.translate(-3.0, -(lY1 + 1.5 * U), 0)
        m.box3d(2.5, lY1 * 0.4, -0.3, 3.0, lY1 + 4.5 * U, 0.3, AL_CLOTH)   # shaft
        # Holy orb (warm silver-blue, pulsing)
        holyA = 0.6 + math.sin(tickF * 1.8) * 0.3
        m.cube3(2.75, lY1 + 5.0 * U, 0, 0.9, AL_GLOW, holyA)
        m.cube3(2.75, lY1 + 5.0 * U, 0, 1.7, AL_GLOW, holyA * 0.25)
        # Healing ray on cast
        if anim == 2 and math.sin(atkP) > 0.3:
            m.box3d(2.6, 0, -0.2, 2.9, lY1 + 5.0 * U, 0.2, AL_GLOW,
                    math.sin(atkP) * 0.5)
        m.pop()

    elif idx == 6:
        # -- 6: CANNON (Siege) -----------------------------------------------
        # Wheeled cannon -- dark wood carriage, 4 spoked wheels, round barrel
        m.box3d(-7.0, 0, -4.0, 7.0, 2.5 * U, 4.0, 0x5A3A1A)
        m.box3d(-7.6, 0.5, -3.5, 7.6, 2.0 * U, 3.5, 0x402810)   # undercarriage
        # Side frame rails
        m.box3d(-7.6, 2.0 * U, -0.5, 7.6, 2.8 * U, 0.5, 0x5A3A1A)
        # 4 WOODEN SPOKED WHEELS
        wheelA = walkP * 55.0 if anim == 1 else 0.0
        for wx in (-1, 1):
            for wz in (-1, 1):
                m.push()
                m.translate(wx * 5.5, 2.0, wz * 3.2)
                m.rotate(wheelA * float(wx), 0, 0, 1)
                # 4 cross spokes (2 + 2 diagonal)
                m.box3d(-0.3, -2.3, -1.0, 0.3, 2.3, 1.0, 0x5A3A1A)   # V spoke
                m.box3d(-2.3, -0.3, -1.0, 2.3, 0.3, 1.0, 0x5A3A1A)   # H spoke
                m.push()
                m.rotate(45.0, 0, 0, 1)
                m.box3d(-0.22, -2.2, -0.8, 0.22, 2.2, 0.8, 0x4A2A0A)
                m.pop()
                m.push()
                m.rotate(-45.0, 0, 0, 1)
                m.box3d(-0.22, -2.2, -0.8, 0.22, 2.2, 0.8, 0x4A2A0A)
                m.pop()
                # Rim blocks (8 segments around circle)
                for s in range(8):
                    a = s * 0.7854
                    m.box3d(math.cos(a) * 2.0 - 0.3, -1.0, math.sin(a) * 2.0 - 0.3,
                            math.cos(a) * 2.0 + 0.3, 1.0, math.sin(a) * 2.0 + 0.3,
                            0x3A2008)
                # Hub
                m.cube3(0, 0, 0, 0.75, AL_STEEL, 0.9)
                m.pop()
        # CANNON BARREL (elevates, blue-steel)
        if anim == 2:
            elev = 22.0 - math.sin(atkP) * 40.0
        elif anim == 0:
            elev = 14.0 + math.sin(idleP) * 3.0
        else:
            elev = 14.0
        m.push()
        m.translate(0, 2.5 * U, 0)
        m.rotate(-elev, 1, 0, 0)
        # Breech block (navy)
        m.box3d(-2.2, 0, -2.2, 2.2, 2.8 * U, 2.2, AL_NAVY)
        # Barrel body (tapers toward muzzle)
        m.box3d(-1.5, 2.8 * U, -1.5, 1.5, 2.8 * U + 5.5 * U, 1.5, AL_STEEL)
        # Muzzle (narrower)
        m.box3d(-1.0, 2.8 * U + 5.5 * U, -1.0, 1.0, 2.8 * U + 7.5 * U, 1.0, AL_STEEL)
        # Cooling bands
        for r in (1, 2, 3):
            m.box3d(-1.7, 2.8 * U + r * 1.6 * U, -1.7,
                    1.7, 2.8 * U + r * 1.6 * U + 0.35, 1.7, AL_NAVY)
        # Muzzle flash
        if anim == 2 and math.sin(atkP) > 0.2:
            m.cube3(0, 2.8 * U + 7.8 * U, 0, 1.0, AL_GLOW, math.sin(atkP))
        m.pop()
        # Recoil kick. As in the Radiant Trebuchet, this glTranslatef lands
        # after every draw in the case, so it moves nothing; kept verbatim.
        if anim == 2:
            m.translate(-abs(math.sin(atkP)) * 2.0, 0, 0)

    else:
        return None     # the C++ answers an unknown unitIdx with "return false"

    m.pop()
    return m.build(**bake)
