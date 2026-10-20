"""Alliance Hero "Uther" -- Paladin of the Holy Order (RACE_ALLIANCE).

Port of src/gfx/models3d/alliance_hero.cpp, C++ numbers verbatim. The cape
and sword-tip quads here already list their vertices in ring order, so unlike
the antlers and horns they need no reordering.
"""

import math

from claude_studio.craftwar_gl import U, GLModel

AL_PLATE = 0xC8D0D8
AL_DARK = 0x28303C
AL_GOLD = 0xD4A828
AL_CLOTH = 0xE8E4D8
AL_GLOW = 0xF8F0A0

CX = (1, 0, -1, 0)
CZ = (0, 1, 0, -1)
PWX = (7 * U, 0, -7 * U, 0)
PWZ = (0, 7 * U, 0, -7 * U)


def build(tickF=0.0, anim=0, name="ALLIANCE_hero", **bake):
    """**bake is forwarded to GLModel.build() -- unlit/emit_strength/
    emit_threshold, for dropping the model into a lit scene."""
    tick = int(tickF)
    m = GLModel(name)

    # -- animation parameters ------------------------------------------------
    idleP, walkP, atkP = tickF * 0.9, tickF * 2.8, tickF * 3.2
    if anim == 1:
        bodyBob = abs(math.sin(walkP)) * 2.5
    elif anim == 0:
        bodyBob = math.sin(idleP) * 0.7
    else:
        bodyBob = 0.0
    # Greatsword swings in a Z-axis arc (horizontal slash); sways on walk
    swGripX, swGripY, swGripZ = 17.0, 0.5 + 2.5 * U, 1.5
    if anim == 2:
        wepAng = -22.0 + math.sin(atkP) * 58.0
    elif anim == 1:
        wepAng = math.sin(walkP * 0.5) * 7.0
    else:
        wepAng = 0.0

    m.push()
    m.translate(0, bodyBob, 0)   # body bob

    # bw=6, bh=5 -- same heavy footprint as AI-Borg
    lY0, lY1 = 0, 6 * U
    tX0, tX1 = -9, 9
    tY0, tY1 = 6 * U, 11 * U
    tZ0, tZ1 = -4.5, 4.5
    hY0, hY1 = tY1, tY1 + 2 * U

    # LEGS -- heavy armored
    m.box3d(-6, lY0, -3, 0, lY1, 3, AL_DARK)
    m.box3d(0, lY0, -3, 6, lY1, 3, AL_DARK)
    m.box3d(-5.5, lY1 - 1.0, -2.5, -0.5, lY1 + 0.8, 2.5, AL_PLATE)
    m.box3d(0.5, lY1 - 1.0, -2.5, 5.5, lY1 + 0.8, 2.5, AL_PLATE)
    if tick & 1:
        m.cube3(-3, lY1, 0, 0.55, AL_GLOW, 0.35)
    if not (tick & 1):
        m.cube3(3, lY1, 0, 0.55, AL_GLOW, 0.35)

    # TORSO -- sealed plate with seams
    m.box3d(tX0, tY0, tZ0, tX1, tY1, tZ1, AL_PLATE)
    s1y, s2y = tY0 + (tY1 - tY0) / 3.0, tY0 + 2 * (tY1 - tY0) / 3.0
    m.box3d(tX0 + 1, s1y, tZ1, tX1 - 1, s1y + 0.4, tZ1 + 0.5, AL_DARK)
    m.box3d(tX0 + 1, s2y, tZ1, tX1 - 1, s2y + 0.4, tZ1 + 0.5, AL_DARK)
    m.box3d(-3.5, tY0 + 1, tZ1, -3.0, tY1 - 1, tZ1 + 0.4, AL_DARK)
    m.box3d(3.0, tY0 + 1, tZ1, 3.5, tY1 - 1, tZ1 + 0.4, AL_DARK)

    # HOLY TABARD -- ivory cloth panel + gold double-stroked cross + holy glow
    m.box3d(-4.5, tY0 + 1, tZ1, 4.5, tY1 - 1, tZ1 + 0.8, AL_CLOTH)
    crossY = tY0 + (tY1 - tY0) * 0.5
    m.box3d(-0.7, tY0 + 2, tZ1 + 0.3, 0.7, tY1 - 2, tZ1 + 1.4, AL_GOLD, 0.90)
    m.box3d(-4.0, crossY - 0.7, tZ1 + 0.3, 4.0, crossY + 0.7, tZ1 + 1.4, AL_GOLD, 0.90)
    gPulse = 1.05 + 0.50 * math.sin(tickF * 0.20)
    m.cube3(0, crossY, tZ1 + 2.0, 1.5, AL_GLOW, gPulse)

    # WINGED PAULDRONS -- plate + gold rim + ivory feather tips
    m.box3d(tX0 - 6, tY1 - 2 * U, tZ0, tX0, tY1, tZ1, AL_DARK, 0.92)
    m.box3d(tX1, tY1 - 2 * U, tZ0, tX1 + 6, tY1, tZ1, AL_DARK, 0.92)
    m.box3d(tX0 - 7.2, tY1 - 2 * U - 0.5, tZ0, tX0 - 5.5, tY1 + 0.5, tZ1, AL_GOLD, 0.70)
    m.box3d(tX1 + 5.5, tY1 - 2 * U - 0.5, tZ0, tX1 + 7.2, tY1 + 0.5, tZ1, AL_GOLD, 0.70)
    m.tri((tX0 - 6, tY1, tZ1), (tX0 - 10, tY1 + 4, tZ1 - 1), (tX0 - 6, tY1 - 2, tZ1),
          AL_CLOTH, 0.88)
    m.tri((tX0 - 6, tY1 - U, tZ1), (tX0 - 8, tY1 + 1.5, tZ1 - 1),
          (tX0 - 6, tY1 - 2 * U, tZ1), AL_CLOTH, 0.70)
    m.tri((tX1 + 6, tY1, tZ1), (tX1 + 10, tY1 + 4, tZ1 - 1), (tX1 + 6, tY1 - 2, tZ1),
          AL_CLOTH, 0.88)
    m.tri((tX1 + 6, tY1 - U, tZ1), (tX1 + 8, tY1 + 1.5, tZ1 - 1),
          (tX1 + 6, tY1 - 2 * U, tZ1), AL_CLOTH, 0.70)

    # CAPE -- 3 panels behind torso
    m.quad((-2, tY1 - U, tZ0 - 0.5), (2, tY1 - U, tZ0 - 0.5),
           (1, tY0 - 2 * U, tZ0 - 5.0), (-1, tY0 - 2 * U, tZ0 - 5.0), AL_DARK, 0.42)
    m.quad((-9, tY1 - U, tZ0), (-2, tY1 - U, tZ0 - 0.5),
           (-1, tY0 - 3 * U, tZ0 - 5.5), (-6, tY0 - 2 * U, tZ0 - 3.5), AL_DARK, 0.33)
    m.quad((2, tY1 - U, tZ0 - 0.5), (9, tY1 - U, tZ0),
           (6, tY0 - 2 * U, tZ0 - 3.5), (1, tY0 - 3 * U, tZ0 - 5.5), AL_DARK, 0.33)

    # HELM -- fully enclosed, T-visor glow slit
    m.box3d(-2 * U, hY0, tZ0, 2 * U, hY1, tZ1, AL_PLATE)
    m.box3d(-2 * U, hY0, tZ1 - 0.2, 2 * U, hY0 + 0.4, tZ1 + 0.4, AL_DARK)
    vY = hY0 + U * 0.35
    m.box3d(-5.5, vY, tZ1, 5.5, vY + 0.5, tZ1 + 0.9, AL_GLOW, 1.30)
    m.box3d(-0.35, vY, tZ1, 0.35, hY0 + U * 0.85, tZ1 + 0.9, AL_GLOW, 1.10)

    # PLUMED CREST -- gold post + ivory fan
    m.box3d(-0.7, hY1, -0.7, 0.7, hY1 + 4 * U, 0.7, AL_GOLD)
    m.box3d(-4.0, hY1 + 3 * U, -1.2, 4.0, hY1 + 3.5 * U, 1.2, AL_CLOTH, 1.00)
    m.box3d(-5.0, hY1 + 3.5 * U, -0.9, 5.0, hY1 + 4.5 * U, 0.9, AL_CLOTH, 0.90)
    m.box3d(-3.0, hY1 + 4.5 * U, -0.7, 3.0, hY1 + 5.5 * U, 0.7, AL_CLOTH, 0.80)
    m.cube3(-5.5, hY1 + 2.5 * U, 0, 0.8, AL_GOLD, 0.70)
    m.cube3(5.5, hY1 + 2.5 * U, 0, 0.8, AL_GOLD, 0.70)

    # HOLY GREATSWORD -- planted right (Z-axis horizontal slash)
    m.push()
    m.translate(swGripX, swGripY, swGripZ)
    m.rotate(wepAng, 0, 0, 1)
    m.translate(-swGripX, -swGripY, -swGripZ)
    swX, swZ, swBY = 17.0, 1.5, 0.5
    swTY = swBY + 15.5 * U
    m.box3d(swX - 0.5, swBY, swZ - 0.3, swX + 0.3, swTY, swZ + 0.3, 0xD8E0E8)
    m.box3d(swX - 0.9, swBY, swZ - 0.7, swX + 0.7, swBY + 2 * U, swZ + 0.7, 0x806020)
    m.box3d(swX - 4.5, swBY + 2.5 * U, swZ - 0.9, swX + 4.3, swBY + 3.0 * U, swZ + 0.9,
            AL_GOLD)
    m.tri((swX - 2, swTY, swZ + 0.4), (swX + 2, swTY, swZ + 0.4),
          (swX, swTY + 2 * U, swZ), AL_CLOTH, 1.20)
    m.tri((swX + 2, swTY, swZ - 0.4), (swX - 2, swTY, swZ - 0.4),
          (swX, swTY + 2 * U, swZ), AL_CLOTH, 0.90)
    m.cube3(swX, swTY + 2 * U, swZ, 1.3, AL_GLOW, 1.55)
    m.pop()   # end sword rotation

    # KITE SHIELD -- off-hand left (static with body, not part of sword rotation)
    shX, shZ = -17.0, 2.0
    m.box3d(shX - 3, crossY - 5, shZ - 0.3, shX + 3, crossY + 7, shZ + 0.8, AL_GOLD, 0.85)
    m.box3d(shX - 2.5, crossY - 4.5, shZ + 0.3, shX + 2.5, crossY + 6.5, shZ + 1.0,
            AL_DARK, 0.80)
    m.box3d(shX - 0.5, crossY - 4, shZ + 0.8, shX + 0.5, crossY + 6, shZ + 1.3, AL_CLOTH)
    m.box3d(shX - 2.8, crossY, shZ + 0.8, shX + 2.8, crossY + 1, shZ + 1.3, AL_CLOTH)

    m.pop()   # end body bob

    # -- AURA -- HOLY CONSECRATION FIELD / DIVINE DEFENSE --------------------
    rY = 0.4

    # GROUND CONSECRATION DISC -- gold circle at the feet, breathing white ring
    discPh = float(tick % 16) / 16.0
    discR = 2.5 * U + discPh * 2 * U        # expands then resets
    m.ring3d(0, rY, 0, discR, 1.5, AL_GLOW, 0.80 * (1.0 - discPh * 0.4))
    m.ring3d(0, rY, 0, discR + 1.5, 1.0, 0xFFFFFF, 0.55 * (1.0 - discPh))

    # CONSECRATION RINGS -- warm gold gradient
    ph0 = float(tick % 30)
    ex0 = (ph0 if ph0 < 15 else 30 - ph0) * 0.11
    ph1 = float(tick % 44)
    ex1 = (ph1 if ph1 < 22 else 44 - ph1) * 0.09
    m.ring3d(0, rY, 0, 4.5 * U, 2.0, AL_GLOW, 0.90)     # tight inner core
    m.ring3d(0, rY, 0, 6 * U + ex0, 3.2, AL_GLOW, 0.58)
    m.ring3d(0, rY, 0, 8 * U + ex1, 2.5, AL_GLOW, 0.30)

    # HOLY CROSS RAYS -- 4 cardinal rays pulsing outward from the inner ring
    R0, R1 = 6 * U + ex0, 8 * U + ex1
    rayLen = R1 + (2.5 * U if (tick & 1) else 1.0 * U)   # pulses each tick
    for i in range(4):
        m.line3d((CX[i] * R0, rY, CZ[i] * R0), (CX[i] * rayLen, rY, CZ[i] * rayLen),
                 AL_GLOW, 0.85, px=3.0, col1=AL_GLOW, mul1=0.05)

    # RAY TIP FLARES -- bright holy sparks at the ray ends (alternating frames)
    for i in range(4):
        if tick & (1 << i):
            m.cube3(CX[i] * rayLen, rY + 0.5, CZ[i] * rayLen, 1.5, 0xFFFFFF, 1.60)

    # SHIELD-WALL PILLARS at 4 cardinal positions -- divine barrier.
    # These read as holy fortress walls: thick, radiant, immovable.
    for i in range(4):
        pilH = 6 * U            # pillar height
        pw, pd = 1.8, 0.8
        # pillar body -- silvered plate
        m.box3d(PWX[i] - pw, rY, PWZ[i] - pd, PWX[i] + pw, rY + pilH, PWZ[i] + pd,
                AL_PLATE, 0.55)
        # glowing gold rim along the pillar edge
        m.box3d(PWX[i] - pw - 0.3, rY, PWZ[i] - pd - 0.2, PWX[i] - pw, rY + pilH,
                PWZ[i] + pd + 0.2, AL_GLOW, 0.45)
        # top capstone glow
        m.cube3(PWX[i], rY + pilH, PWZ[i], 2.0, 0xFFFFFF, 0.60 + 0.30 * (tick & 1))

    # HEAVEN-BEAMS -- 3 columns of holy light descending from above.
    # Central wide beam + 2 flanking thinner beams (spec exactly).
    beamTop, beamBot = 18 * U, tY0   # from above head down to torso
    m.line3d((0, rY + beamTop, 0), (0, rY + beamBot, 0),
             0xFFFFFF, 0.35, px=4.0, col1=0xFFFFFF, mul1=0.02)
    m.line3d((-3 * U, rY + beamTop - 2 * U, 0), (-3 * U, rY + beamBot, 0),
             AL_GLOW, 0.22, px=2.5, col1=AL_GLOW, mul1=0.02)
    m.line3d((3 * U, rY + beamTop - 2 * U, 0), (3 * U, rY + beamBot, 0),
             AL_GLOW, 0.22, px=2.5, col1=AL_GLOW, mul1=0.02)
    m.line3d((-5.5 * U, rY + beamTop - 4 * U, 0), (-5.5 * U, rY + beamBot, 0),
             AL_GLOW, 0.12, px=1.5, col1=AL_GLOW, mul1=0.01)
    m.line3d((5.5 * U, rY + beamTop - 4 * U, 0), (5.5 * U, rY + beamBot, 0),
             AL_GLOW, 0.12, px=1.5, col1=AL_GLOW, mul1=0.01)

    # 8 HOLY SPARKS -- 4 gold clockwise inner + 4 white counter-clockwise outer
    for i in range(4):
        angCW = tickF * 0.12 + i * (3.14159 * 2.0 / 4.0)
        angCCW = -tickF * 0.08 + i * (3.14159 * 2.0 / 4.0)
        m.cube3(math.cos(angCW) * R0, rY + 0.5, math.sin(angCW) * R0, 1.1, AL_GLOW, 0.90)
        m.cube3(math.cos(angCCW) * R1, rY + 0.5, math.sin(angCCW) * R1, 1.0, 0xFFFFFF, 0.65)

    return m.build(**bake)
