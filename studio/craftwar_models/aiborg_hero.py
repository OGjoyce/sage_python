"""AI-Borg "Talos Reborn" -- Overmind Prime (RACE_AIBORG, skin 0).

Port of src/gfx/models3d/aiborg_hero.cpp, C++ numbers verbatim.

Local coord system: Y up, Z toward viewer, feet at y = 0 -- which is this
studio's convention too, so nothing is converted.

Layout (all in world units = sprite_units x U):
  Legs      y [0,    6U]   two 2U-wide boxes
  Torso     y [6U,  11U]   6U wide x 5U tall x 3U deep
  Head      y [11U, 13U]   4U wide x 2U tall
  Mast      y [13U, ~17U]  sensor shaft + pulsing beacon
  Pauldrons x [+-9, +-15], y [9U, 11U]   full torso depth
  Spear     x=17, base y=0.5, tip y~51.5 -- crossguard at mid-chest
  Cables    5 strands from center-back mount, fan 60 deg arc
  Rings     XZ plane at y=0.4, radii 7U / 9U / 11U (breathing)
"""

import math

from claude_studio.craftwar_gl import U, GLModel

AB_BODY = 0x2A2A38   # dark navy-charcoal armor
AB_SKULL = 0x505060  # gunmetal machine skull
AB_GLOW = 0xF0C040   # gold energy / endoskeleton (body only)
AB_DARK = 0x0C0C18   # deep shadow / plate recesses
AB_STEEL = 0x7090A8  # neutral steel (spear back edge)
AB_CABLE = 0x404055  # cable dreadlock strands
# Electrical storm palette (aura only -- body stays gold)
AB_ARC = 0x40C8FF    # electric blue arc / ring core
AB_SPARK = 0xD0F4FF  # white-blue spark tip / scan line

CAB_LEN = (18.0, 22.5, 27.0, 21.0, 15.0)
CAB_TX = (-16.0, -9.0, 0.0, 8.0, 14.0)
CAB_TZ = (-4.5, -2.5, -1.5, -2.0, -3.5)

NX = (0, 5, 7, 5, 0, -5, -7, -5)
NZ = (-7, -5, 0, 5, 7, 5, 0, -5)

# (tick bit, node index, brightness, use spark colour)
ARCS = ((1, 0, 0.90, False), (2, 1, 0.75, True), (4, 2, 0.85, False),
        (8, 3, 0.70, False), (1, 4, 0.80, False), (4, 5, 0.75, False),
        (2, 6, 0.88, False), (8, 7, 0.68, True))

BX = (0, 5.5, 7, 5.5, 0, -5.5, -7, -5.5)
BZ = (-7, -5.5, 0, 5.5, 7, 5.5, 0, -5.5)
J1X = (1.5, -1.2, 2.0, -1.5, 1.0, 1.8, -1.0, 2.2)
J1Z = (-1.0, 2.0, -1.5, 1.2, -2.0, 1.0, 1.5, -1.8)
J2X = (-0.8, 1.5, -0.5, 2.0, -1.2, -0.8, 1.5, -1.0)
J2Z = (1.5, -0.8, 2.0, -1.0, 0.5, -2.0, 1.0, 0.8)


def build(tickF=0.0, anim=0, name="AIBORG_hero", **bake):
    """**bake is forwarded to GLModel.build() -- unlit/emit_strength/
    emit_threshold, for dropping the model into a lit scene."""
    tick = int(tickF)
    m = GLModel(name)

    idleP, walkP, atkP = tickF * 0.9, tickF * 2.8, tickF * 3.2
    if anim == 1:
        bodyBob = abs(math.sin(walkP)) * 2.5
    elif anim == 0:
        bodyBob = math.sin(idleP) * 0.7
    else:
        bodyBob = 0.0
    m.push()
    m.translate(0, bodyBob, 0)

    # -- layout constants ----------------------------------------------------
    lY0, lY1 = 0, 6 * U
    tX0, tX1 = -9, 9
    tY0, tY1 = 6 * U, 11 * U
    tZ0, tZ1 = -4.5, 4.5
    hY0, hY1 = tY1, tY1 + 2 * U
    mY0 = hY1

    # -- LEGS -- walk stride -------------------------------------------------
    walkSwing = math.sin(walkP) * 28.0 if anim == 1 else 0.0
    # Left leg: pivot at hip (-3, lY1, 0), swings forward when right leg is back
    m.push()
    m.translate(-3, lY1, 0)
    m.rotate(-walkSwing, 1, 0, 0)
    m.translate(3, -lY1, 0)
    m.box3d(-6, lY0, -3, 0, lY1, 3, AB_BODY)
    m.box3d(-5.5, lY1 - 1.2, -2.5, -0.5, lY1 + 0.8, 2.5, AB_BODY)
    m.pop()
    # Right leg: opposite phase
    m.push()
    m.translate(3, lY1, 0)
    m.rotate(walkSwing, 1, 0, 0)
    m.translate(-3, -lY1, 0)
    m.box3d(0, lY0, -3, 6, lY1, 3, AB_BODY)
    m.box3d(0.5, lY1 - 1.2, -2.5, 5.5, lY1 + 0.8, 2.5, AB_BODY)
    m.pop()
    # Knee piston sparks alternate each tick
    spk = 0.7
    if tick & 1:
        m.cube3(-3, lY1 + 0.5, 0, spk, AB_GLOW, 0.55)
    if not (tick & 1):
        m.cube3(3, lY1 + 0.5, 0, spk, AB_GLOW, 0.55)

    # -- TORSO ---------------------------------------------------------------
    m.box3d(tX0, tY0, tZ0, tX1, tY1, tZ1, AB_BODY)
    # Lamellar seams -- 2 horizontal (1/3, 2/3 up torso)
    s1y, s2y = tY0 + (tY1 - tY0) / 3.0, tY0 + 2 * (tY1 - tY0) / 3.0
    m.box3d(tX0 + 1, s1y, tZ1, tX1 - 1, s1y + 0.5, tZ1 + 0.5, AB_DARK)
    m.box3d(tX0 + 1, s2y, tZ1, tX1 - 1, s2y + 0.5, tZ1 + 0.5, AB_DARK)
    # 2 vertical column seams
    for col in (1, 2):
        vx = tX0 + col * (tX1 - tX0) / 3.0
        m.box3d(vx, tY0 + 1, tZ1, vx + 0.4, tY1 - 1, tZ1 + 0.5, AB_DARK)
    # Center chest slot -- exposes mechanical gold spine
    m.box3d(-0.8, tY0 + 2.5, tZ1, 0.8, tY1 - 2.5, tZ1 + 1.3, AB_GLOW, 1.00)
    # Forge-mark sunburst (chest reactor) -- overloads during attack
    ecx, ecy, ecz = 0, (tY0 + tY1) * 0.5, tZ1
    reactorPulse = 1.25 + abs(math.sin(atkP)) * 0.8 if anim == 2 else 1.25
    rayExt = 5.5 + abs(math.sin(atkP)) * 4.0 if anim == 2 else 5.5
    m.cube3(ecx, ecy, ecz + 0.9, 1.6, AB_GLOW, reactorPulse)
    m.box3d(-rayExt, ecy - 0.55, ecz, rayExt, ecy + 0.55, ecz + 0.8, AB_GLOW, 0.80)  # H
    m.box3d(-0.55, ecy - rayExt, ecz, 0.55, ecy + rayExt, ecz + 0.8, AB_GLOW, 0.80)  # V

    # -- PAULDRONS -----------------------------------------------------------
    # Full torso depth -- extend forward and backward equally
    m.box3d(tX0 - 6, tY1 - 2 * U, tZ0, tX0, tY1, tZ1, AB_BODY, 0.90)
    m.box3d(tX1, tY1 - 2 * U, tZ0, tX1 + 6, tY1, tZ1, AB_BODY, 0.90)
    # Gold accent rims
    m.box3d(tX0 - 7.0, tY1 - 2 * U - 0.6, tZ0, tX0 - 5.4, tY1 + 0.6, tZ1, AB_GLOW, 0.75)
    m.box3d(tX1 + 5.4, tY1 - 2 * U - 0.6, tZ0, tX1 + 7.0, tY1 + 0.6, tZ1, AB_GLOW, 0.75)

    # -- HEAD -- machine skull -----------------------------------------------
    m.box3d(-2 * U, hY0, tZ0, 2 * U, hY1, tZ1, AB_SKULL)
    m.box3d(-2 * U, hY0, tZ1 - 0.3, 2 * U, hY0 + 0.5, tZ1 + 0.5, AB_DARK)   # jaw line
    # Eye socket recesses -- dark frame wider than glow for a visible rim
    eT, eB = hY0 + U * 0.35, hY0 + U * 1.25
    m.box3d(-6.2, eT - 0.3, tZ1 + 0.2, -1.0, eB + 0.3, tZ1 + 1.8, AB_DARK)  # L frame
    m.box3d(1.0, eT - 0.3, tZ1 + 0.2, 6.2, eB + 0.3, tZ1 + 1.8, AB_DARK)    # R frame
    eyeBright = 2.4 + abs(math.sin(atkP)) * 0.9 if anim == 2 else 1.50
    m.box3d(-5.5, eT, tZ1 + 0.5, -1.7, eB, tZ1 + 2.1, AB_GLOW, eyeBright)   # L iris
    m.box3d(1.7, eT, tZ1 + 0.5, 5.5, eB, tZ1 + 2.1, AB_GLOW, eyeBright)     # R iris

    # -- SENSOR MAST + BEACON ------------------------------------------------
    m.box3d(-0.7, mY0, -0.7, 0.7, mY0 + 4.0 * U, 0.7, AB_SKULL)
    bPulse = 1.05 + 0.60 * math.sin(tickF * 0.2513)    # 1-sec cycle
    bSize = 1.3 + 0.18 * math.sin(tickF * 0.2513)
    m.cube3(0, mY0 + 4.5 * U, 0, bSize, AB_GLOW, bPulse)

    # -- ENERGY SPEAR --------------------------------------------------------
    # Planted to the right; crossguard at mid-chest height; tip far above mast.
    spX, spZ, spBY = 17.0, 1.5, 0.5
    spXY = tY0 + (tY1 - tY0) * 0.50    # crossguard ~ 25.5
    spHY = spBY + 15.5 * U             # spearhead base ~ 47
    spTY = spBY + 17.0 * U             # tip ~ 51.5
    gY = tY0 + (tY1 - tY0) * 0.30      # grip height
    if anim == 2:
        wepAng = -15.0 + math.sin(atkP) * 50.0
    elif anim == 1:
        wepAng = math.sin(walkP * 0.5) * 6.0
    else:
        wepAng = 0.0
    m.push()
    m.translate(spX, gY, spZ)
    m.rotate(wepAng, 1, 0, 0)
    m.translate(-spX, -gY, -spZ)
    # Shaft -- continuous floor to spearhead base
    m.box3d(spX - 1.0, spBY, spZ - 0.6, spX - 0.1, spHY, spZ + 0.6, AB_STEEL)
    m.box3d(spX - 0.1, spBY, spZ - 0.8, spX + 0.9, spHY, spZ + 0.8, 0x9090A0)
    # Grip band at hand height
    m.box3d(spX - 1.6, gY - 1.0, spZ - 1.1, spX + 1.5, gY + 1.0, spZ + 1.1, 0x444450)
    # Crossguard -- gold bar at mid-chest
    m.box3d(spX - 4.2, spXY - 0.8, spZ - 1.0, spX + 4.0, spXY + 0.8, spZ + 1.0, AB_GLOW)
    # Spearhead triangles
    m.tri((spX - 3.5, spHY, spZ + 0.9), (spX + 3.3, spHY, spZ + 0.9),
          (spX - 0.1, spTY, spZ), AB_GLOW, 1.30)
    m.tri((spX + 3.3, spHY, spZ - 0.9), (spX - 3.5, spHY, spZ - 0.9),
          (spX - 0.1, spTY, spZ), AB_GLOW, 0.85)
    m.tri((spX - 3.5, spHY, spZ + 0.9), (spX - 0.1, spTY, spZ),
          (spX - 3.5, spHY, spZ - 0.9), AB_GLOW, 1.10)
    m.tri((spX + 3.3, spHY, spZ + 0.9), (spX + 3.3, spHY, spZ - 0.9),
          (spX - 0.1, spTY, spZ), AB_GLOW, 1.00)
    m.cube3(spX - 0.1, spTY, spZ, 1.1, AB_GLOW, 1.65)    # tip flare
    m.pop()   # end spear rotation

    # -- CABLE DREADLOCKS ----------------------------------------------------
    # All 5 strands emerge from one shared mount point between the shoulder blades.
    cabY0, cabMZ = tY1 - 2 * U, tZ0 - 1.5
    m.box3d(-1.8, cabY0 - 1.8, tZ0 - 0.6, 1.8, cabY0 + 0.3, tZ0, AB_STEEL, 0.55)  # bracket
    for i in range(5):
        cy1, cz1 = cabY0 - CAB_LEN[i], cabMZ + CAB_TZ[i]
        tipCol = AB_GLOW if (i & 1) else 0x707080
        t = 0.65
        m.quad((-t, cabY0, cabMZ), (t, cabY0, cabMZ),
               (CAB_TX[i] + t, cy1, cz1), (CAB_TX[i] - t, cy1, cz1), AB_CABLE, 0.70)
        m.cube3(CAB_TX[i], cy1, cz1, t, tipCol, 1.25)

    m.pop()   # end body bob

    # -- AURA -- ELECTRICAL STORM / SCAN FIELD -------------------------------
    rY = 0.4

    # Breathing ring radii (independent periods)
    ph0 = float(tick % 32)
    ex0 = (ph0 if ph0 < 16 else 32 - ph0) * 0.12
    ph1 = float(tick % 40)
    ex1 = (ph1 if ph1 < 20 else 40 - ph1) * 0.12
    ph2 = float(tick % 28)
    ex2 = (ph2 if ph2 < 14 else 28 - ph2) * 0.12
    R0, R1, R2 = 7 * U + ex0, 9 * U + ex1, 11 * U + ex2

    # GROUND POWER-DRAIN LINES -- 4 faint hlines radiating from the feet
    m.line3d((-R2, rY, 0), (R2, rY, 0), AB_ARC, 0.12, px=1.0)
    m.line3d((0, rY, -R2), (0, rY, R2), AB_ARC, 0.12, px=1.0)
    m.line3d((-R2, rY, -R2 * 0.7), (R2, rY, R2 * 0.7), AB_ARC, 0.08, px=1.0)
    m.line3d((-R2, rY, R2 * 0.7), (R2, rY, -R2 * 0.7), AB_ARC, 0.08, px=1.0)

    # AURA RINGS -- electric blue, radial gradient (innermost = brightest)
    m.ring3d(0, rY, 0, 4.5 * U, 2.0, AB_SPARK, 0.95)   # tight core glow
    m.ring3d(0, rY, 0, R0, 3.5, AB_ARC, 0.78)          # inner ring
    m.ring3d(0, rY, 0, R1, 3.0, AB_ARC, 0.50)          # mid ring
    m.ring3d(0, rY, 0, R2, 2.5, AB_ARC, 0.28)          # outer ghost ring

    # CIRCUIT-NODE SQUARES at 8 compass positions on the inner ring.
    # Each flickers on a different tick bit -- 8 blink patterns.
    for i in range(8):
        bit = 1 << (i & 3)
        if not (tick & bit):
            continue
        nx, nz = NX[i] * R0 / 7.0, NZ[i] * R0 / 7.0
        nm = 1.30 if (i & 1) else 0.90
        m.cube3(nx, rY + 0.4, nz, 1.4, AB_SPARK if (i & 1) else AB_ARC, nm)

    # SCAN SWEEP LINES -- 3 horizontal planes sweeping upward across the field.
    # Different speeds (x1, x2, x3 of tick mod period) -- holographic scanner read.
    for s in range(3):
        period = 30.0 + s * 8.0
        phase = math.fmod(tickF * (s + 1) * 0.5, period) / period    # 0..1
        sweepY = rY + phase * 14 * U
        alpha = 0.25 * (1.0 - phase * 0.8)    # dimmer as it rises
        m.line3d((-R2, sweepY, 0), (R2, sweepY, 0), AB_ARC, alpha, px=1.0)
        m.line3d((0, sweepY, -R2), (0, sweepY, R2), AB_SPARK, alpha * 0.6, px=1.0)

    # HORIZONTAL STORM ARCS -- 8 async electric arcs on the ring plane
    for bit, i, mul, spark in ARCS:
        if not (tick & bit):
            continue
        bx, bz = NX[i] * R0 / 7.0, NZ[i] * R0 / 7.0
        ni = (i + 1) % 8
        tx = NX[i] * (R1 + 1.5 * U) / 7.0 + NX[ni] * U * 0.6
        tz = NZ[i] * (R1 + 1.5 * U) / 7.0 + NZ[ni] * U * 0.6
        m.line3d((bx, rY, bz), (tx, rY + U * 0.4, tz),
                 AB_SPARK if spark else AB_ARC, mul, px=2.0)

    # LIGHTNING COLUMNS -- jagged 3-segment bolts rising from the ring surface.
    # Gated by different tick bits so they fire asynchronously.
    # Gradient: dim at base, brightest at the crackling tip.
    boltH = 8 * U      # lightning reaches 8 sprite-units above the ring plane
    for i in range(8):
        if not (tick & (1 << (i & 3))):
            continue
        ox, oz = BX[i] * R0 / 7.0, BZ[i] * R0 / 7.0
        # three segments: base->mid1, mid1->mid2, mid2->tip
        m1x, m1z, m1y = ox + J1X[i] * 1.8, oz + J1Z[i] * 1.8, rY + boltH * 0.38
        m2x, m2z, m2y = ox + J2X[i] * 1.2, oz + J2Z[i] * 1.2, rY + boltH * 0.70
        tx, tz, ty = ox + J2X[i] * 0.5, oz + J2Z[i] * 0.5, rY + boltH
        col = AB_SPARK if (i & 1) else AB_ARC
        m.line3d((ox, rY, oz), (m1x, m1y, m1z), col, 0.45, px=2.5)
        m.line3d((m1x, m1y, m1z), (m2x, m2y, m2z), col, 0.70, px=2.5)
        m.line3d((m2x, m2y, m2z), (tx, ty, tz), col, 1.00, px=2.5)

    # SPARK TIPS -- bright cube at the top of each active bolt
    for i in range(8):
        if not (tick & (1 << (i & 3))):
            continue
        ox, oz = BX[i] * R0 / 7.0, BZ[i] * R0 / 7.0
        tx, tz = ox + J2X[i] * 0.5, oz + J2Z[i] * 0.5
        m.cube3(tx, rY + boltH + 0.5, tz, 1.1, AB_SPARK, 1.50)

    return m.build(**bake)
