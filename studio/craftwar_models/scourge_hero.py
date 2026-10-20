"""Scourge Hero "La Parca" -- The Grim Reaper (RACE_SCOURGE).

Port of src/gfx/models3d/scourge_hero.cpp, C++ numbers verbatim.

Note the nesting the source uses and this keeps: the scythe's own rotation
closes before the blood is drawn, so stains, drips and falling drops ride the
body bob but not the weapon swing; the ground pool is outside the bob entirely,
because a pool on the floor does not bob with the hero.
"""

import math

from claude_studio.craftwar_gl import U, GLModel

SC_ROBE = 0x1A1428   # near-black robe
SC_DARK = 0x06050A   # deepest shadow
SC_BONE = 0xEEE6CC   # bone ivory
SC_GLOW = 0x40FF80   # fel-green plague-core
SC_GOLD = 0xB08020   # pendant cross

BL_FRESH = 0xCC1010  # bright arterial red
BL_MID = 0x880808    # mid blood
BL_DARK = 0x520404   # dried crust
BL_POOL = 0x2A0202   # old pooled blood

BCLOT_DX = (-1.5, -3.0, -4.8, -6.5, -8.0, -9.8)
BCLOT_DY = (1.3, 1.6, 1.8, 2.0, 1.8, 1.5)
BCLOT_SZ = (0.55, 0.42, 0.50, 0.38, 0.48, 0.40)
BCLOT_BR = (0.85, 0.80, 0.88, 0.75, 0.82, 0.78)
BFSP_DX = (-1.0, -2.5, -5.5, -7.2, -9.2)
BFSP_DY = (0.7, 0.9, 1.2, 1.5, 1.7)
BFSP_SZ = (0.20, 0.18, 0.22, 0.16, 0.24)
BMST_DX = (-2.0, -4.0, -7.8)
BMST_DY = (2.2, 2.5, 2.3)
BDSP = (0.35, 0.35, 0.35, 0.28)   # drip speeds
BDPH = (0.00, 0.37, 0.71, 0.18)   # phase offsets

# Purple fire palette (aura only)
SC_PURP_HOT = 0xE060FF   # bright purple-white flame core
SC_PURP_MID = 0x9010C8   # deep purple mid-flame
SC_PURP_DIM = 0x280840   # near-black fading tip
SC_PEST = 0x30E050       # pestilence green drops

PFX = (0, 3.0, -2.5, 4.5, -4.0, 1.8, -1.2, 3.5)
PFZ = (0, -2.5, 3.5, -1.8, 2.0, 4.5, -3.5, 0.8)
PPH = (0, 2.8, 6.4, 10.5, 14.8, 1.5, 5.2, 8.9)
DPX = (2.0, -3.0, 0.5, -1.5, 4.0, -4.5)
DPZ = (-2.5, 1.5, 3.5, -3.0, 0.5, 2.0)
DPH = (0, 3.3, 6.8, 10.5, 14.2, 17.6)


def build(tickF=0.0, anim=0, name="SCOURGE_hero", **bake):
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
    m.translate(0, bodyBob, 0)   # body bob

    # bw=5, bh=6 -- tall, gaunt reaper stance
    lY0, lY1 = 0, 6 * U
    tX0, tX1 = -7.5, 7.5
    tY0, tY1 = 6 * U, 12 * U
    tZ0, tZ1 = -3.75, 3.75
    hoodBase = tY1     # hood base sits at torso top

    # LEGS -- robed, very dark
    m.box3d(-6, lY0, -3, 0, lY1, 3, SC_DARK)
    m.box3d(0, lY0, -3, 6, lY1, 3, SC_DARK)
    # plague mist: 3 glowing motes at ankle level, drifting
    drift = math.sin(tickF * 0.25) * 2.5
    m.cube3(tX0 - U + drift, lY1 - 0.8, 0, 0.7, SC_GLOW, 0.55)
    m.cube3(0, lY1, 0, 0.7, SC_GLOW, 0.40)
    m.cube3(tX1 + U - drift, lY1 - 0.8, 0, 0.7, SC_GLOW, 0.55)

    # TORSO -- solid dark robe body
    m.box3d(tX0, tY0, tZ0, tX1, tY1, tZ1, SC_ROBE)
    # ragged hem: alternating dark notches along the bottom edge
    seg = (tX1 - tX0) / 5.0
    for i in range(0, 5, 2):
        m.box3d(tX0 + i * seg, tY0, tZ1 - 0.2,
                tX0 + (i + 1) * seg, tY0 + U, tZ1 + 0.3, SC_DARK)

    # PENDANT CROSS AT COLLAR -- tiny gold cross hanging at the collar
    pendX, pendY = 0.0, tY1 - U
    m.box3d(pendX - 0.25, pendY - U, tZ1 + 0.2, pendX + 0.25, pendY + 0.1, tZ1 + 0.8,
            SC_GOLD, 0.90)   # V
    m.box3d(pendX - 0.8, pendY - 0.6, tZ1 + 0.3, pendX + 0.8, pendY - 0.3, tZ1 + 0.8,
            SC_GOLD, 0.90)   # H

    # EXPOSED RIBCAGE -- bone-white column in the center of the robe
    rbX0, rbX1 = -U * 0.9, U * 0.9
    m.box3d(rbX0, tY0 + U, tZ1, rbX1, tY1 - U, tZ1 + 0.6, SC_BONE, 0.85)
    # spine line down center
    m.box3d(-0.3, tY0 + U, tZ1 + 0.3, 0.3, tY1 - U, tZ1 + 0.9, SC_DARK, 0.60)
    # 3 rib bars across the bone column
    for i in range(3):
        ry = tY0 + 2 * U + i * U
        m.box3d(rbX0, ry, tZ1 + 0.1, rbX1, ry + 0.4, tZ1 + 0.7, SC_DARK, 0.65)

    # PLAGUE-CORE GLOW -- pulsing green sphere at the ribcage bottom
    coreY = tY0 + 4 * U
    cPulse = 1.1 + 0.65 * math.sin(tickF * 0.22)
    cSize = 1.5 + 0.35 * math.sin(tickF * 0.22)
    m.cube3(0, coreY, tZ1 + 1.2, cSize, SC_GLOW, cPulse)
    # outer halo ring
    m.ring3d(0, coreY, 0, 3 * U, 1.2, SC_GLOW, 0.25)

    # WIDE ROBED SLEEVES -- on both sides
    m.box3d(tX0 - 2 * U, tY1 - 4 * U, tZ0, tX0, tY1 - U, tZ1, SC_ROBE, 0.90)
    m.box3d(tX1, tY1 - 4 * U, tZ0, tX1 + 2 * U, tY1 - U, tZ1, SC_ROBE, 0.90)
    # dark outline on sleeves
    m.box3d(tX0 - 2 * U - 0.2, tY1 - 4 * U, tZ0, tX0 - 2 * U, tY1 - U, tZ1, SC_DARK)
    m.box3d(tX1 + 2 * U, tY1 - 4 * U, tZ0, tX1 + 2 * U + 0.2, tY1 - U, tZ1, SC_DARK)
    # skeletal hands at cuffs
    m.cube3(tX0 - 2 * U + U * 0.5, tY1 - 4 * U - U * 0.5, tZ1 + 0.2, 0.8, SC_BONE, 0.90)
    m.cube3(tX1 + 2 * U - U * 0.5, tY1 - 4 * U - U * 0.5, tZ1 + 0.2, 0.8, SC_BONE, 0.90)

    # HOOD -- dark dome cowl: 4 stacked boxes decreasing in size
    hoodR = 2 * U      # row 0: full width = 2*hoodR = 4U
    m.box3d(-hoodR, hoodBase, tZ0, hoodR, hoodBase + U, tZ1, SC_ROBE, 0.95)
    m.box3d(-hoodR * 0.9, hoodBase + U, tZ0, hoodR * 0.9, hoodBase + 2 * U, tZ1,
            SC_ROBE, 0.90)
    m.box3d(-hoodR * 0.65, hoodBase + 2 * U, tZ0, hoodR * 0.65, hoodBase + 3 * U, tZ1,
            SC_ROBE, 0.85)
    m.box3d(-hoodR * 0.3, hoodBase + 3 * U, tZ0, hoodR * 0.3, hoodBase + 4 * U, tZ1,
            SC_DARK, 0.80)
    # hood interior -- dark cavity
    m.box3d(-hoodR * 0.8, hoodBase + U * 0.3, tZ1 - 0.3,
            hoodR * 0.8, hoodBase + U * 1.8, tZ1 + 0.1, SC_DARK)
    # ember eyes deep inside the shadow
    eFlicker = 1.2 + 0.5 * (1.0 if (tick & 1) else -1.0) * 0.3
    m.cube3(-2.5, hoodBase + U * 0.8, tZ1 + 0.2, 0.9, SC_GLOW, eFlicker)
    m.cube3(2.5, hoodBase + U * 0.8, tZ1 + 0.2, 0.9, SC_GLOW, eFlicker)
    # hood peak pointing up
    m.tri((-U * 0.3, hoodBase + 4 * U, 0), (U * 0.3, hoodBase + 4 * U, 0),
          (0, hoodBase + 5.5 * U, 0), SC_DARK, 0.90)

    # SCYTHE -- long shaft + hooked crescent blade
    shX, shZ, shBY = 14.0, 1.5, 0.5
    shTY = shBY + 16 * U
    shGripY = tY0 + 1.5 * U
    if anim == 2:
        wepAng = -22.0 + math.sin(atkP) * 58.0
    elif anim == 1:
        wepAng = math.sin(walkP * 0.5) * 7.0
    else:
        wepAng = 0.0
    m.push()
    m.translate(shX, shGripY, shZ)
    m.rotate(wepAng, 0, 0, 1)
    m.translate(-shX, -shGripY, -shZ)
    m.box3d(shX - 0.6, shBY, shZ - 0.4, shX + 0.3, shTY, shZ + 0.4, 0x241C20)   # shaft
    m.box3d(shX - 0.3, shBY, shZ - 0.2, shX + 0.1, shTY, shZ + 0.2, 0x6A5058, 0.50)
    # curved blade sweeping left from the shaft top -- hook shape
    bY = shTY - U
    m.quad((shX - 0.5, bY, shZ + 0.4), (shX - 0.5, bY + U, shZ + 0.4),
           (shX - 10, bY + 2 * U, shZ + 0.3), (shX - 10, bY + U, shZ + 0.3),
           SC_GLOW, 1.10)     # inner glow edge
    m.quad((shX - 0.5, bY - U, shZ - 0.4), (shX - 0.5, bY, shZ - 0.4),
           (shX - 10, bY + U, shZ - 0.3), (shX - 10, bY, shZ - 0.3),
           0x888090, 0.70)    # blade back
    # blade tip hook curling back toward the shaft
    m.tri((shX - 10, bY + 2 * U, shZ), (shX - 12, bY + U, shZ), (shX - 10, bY, shZ),
          SC_GLOW, 1.30)
    m.cube3(shX - 10, bY + 2 * U, shZ, 0.9, SC_GLOW, 1.50)   # blade tip glow
    m.pop()   # end scythe rotation

    # -- BLOOD -- dried stains, pendant drips, falling drops, ground pool ----

    # 1. DRIED STAIN -- dark-red coating on the inner cutting face
    m.quad((shX - 0.5, bY, shZ + 0.52), (shX - 0.5, bY + U, shZ + 0.52),
           (shX - 10, bY + 2 * U, shZ + 0.42), (shX - 10, bY + U, shZ + 0.42),
           BL_DARK, 0.90)
    m.tri((shX - 10, bY + 2 * U, shZ + 0.06), (shX - 12, bY + U, shZ + 0.06),
          (shX - 10, bY, shZ + 0.06), BL_DARK, 0.80)

    # 2. BLOOD SPLATTER -- medium clots + fine spatter + tiny mist on the blade
    for i in range(6):
        m.cube3(shX + BCLOT_DX[i], bY + BCLOT_DY[i] * U, shZ + 0.53,
                BCLOT_SZ[i], BL_MID, BCLOT_BR[i])
    for i in range(5):
        m.cube3(shX + BFSP_DX[i], bY + BFSP_DY[i] * U, shZ + 0.54,
                BFSP_SZ[i], BL_FRESH, 0.70)
    # tiny mist dots (slow shimmer)
    for i in range(3):
        m.cube3(shX + BMST_DX[i], bY + BMST_DY[i] * U, shZ + 0.55, 0.13, BL_FRESH,
                0.55 + 0.22 * math.sin(tickF * 0.25 + i))

    # 3+4. PENDANT DRIPS + FALLING DROPS -- 4 streams (3 blade edge + 1 hook tip)
    BDOX = (shX - 3.0, shX - 6.0, shX - 9.5, shX - 12.0)
    BDOY = (bY + 0.9 * U, bY + 1.3 * U, bY + 1.8 * U, bY + U)
    for i in range(4):
        ox, oy = BDOX[i], BDOY[i]
        phase = math.fmod(tickF * BDSP[i] + BDPH[i], 1.0)
        if phase < 0.35:
            # PENDANT FORMING -- teardrop growing below the blade
            grow = phase / 0.35
            pLen = 0.4 + grow * 2.4      # elongates 0.4 -> 2.8
            pW = 0.20 + grow * 0.20      # widens  0.20 -> 0.40
            m.box3d(ox - pW, oy - pLen, shZ, ox + pW, oy, shZ + 0.12, BL_FRESH, 0.90)
            # rounded bulge at the bottom (the swelling drop head)
            bW = pW * (1.3 + grow * 0.4)
            m.box3d(ox - bW, oy - pLen - bW * 0.9, shZ - 0.02,
                    ox + bW, oy - pLen + bW * 0.5, shZ + 0.10, BL_FRESH, 0.75)
        else:
            # FALLING DROP -- accelerating teardrop in mid-air
            tFall = (phase - 0.35) / 0.65
            dropY = oy - tFall * (oy - 2.0)    # falls from blade to near ground
            elong = 0.55 + tFall * 3.2         # elongates with speed
            dW = 0.30 * (1.0 - tFall * 0.35)
            alpha = 1.0 - tFall * 0.28
            dCol = BL_FRESH if tFall < 0.45 else BL_MID
            # elongated body
            m.box3d(ox - dW, dropY - elong, shZ - 0.04, ox + dW, dropY, shZ + 0.04,
                    dCol, alpha)
            # rounded leading head (bottom of the falling drop)
            hW = dW * 1.35
            m.box3d(ox - hW, dropY - elong - hW * 0.8, shZ - 0.04,
                    ox + hW, dropY - elong + hW * 0.4, shZ + 0.04, dCol, alpha * 0.78)
            # speed-streak trail above the drop
            if tFall > 0.20:
                trailLen = elong * 0.7 * tFall
                m.line3d((ox, dropY, shZ), (ox, dropY + trailLen, shZ),
                         BL_MID, alpha * 0.50, px=1.0, col1=BL_MID, mul1=0.02)

    m.pop()   # end body bob

    # 5. BLOOD POOL -- irregular flat disc on the ground below the blade
    poolX, poolZ = shX - 7.5, shZ
    POOL_N, POOL_PI2, POOL_R = 18, 6.28318530, 4.5
    rim = []
    for i in range(POOL_N + 1):
        a = POOL_PI2 * i / POOL_N
        r = POOL_R * (0.72 + 0.28 * math.sin(a * 2.7 + 0.9))
        rim.append((poolX + math.cos(a) * r, 0.30, poolZ + math.sin(a) * r))
    m.fan((poolX, 0.30, poolZ), rim, BL_POOL, 0.62, 0.04)
    # fresher center -- slightly brighter, still wet
    rim2 = [(poolX + math.cos(POOL_PI2 * i / POOL_N) * (POOL_R * 0.38), 0.32,
             poolZ + math.sin(POOL_PI2 * i / POOL_N) * (POOL_R * 0.38))
            for i in range(POOL_N + 1)]
    m.fan((poolX, 0.32, poolZ), rim2, BL_MID, 0.26, 0.02, col_edge=BL_POOL)
    # smear trail from the shaft base to the pool
    m.box3d(shX - 7.5, 0.20, shZ - 0.8, shX - 1.0, 0.22, shZ + 0.6, BL_DARK, 0.27)

    # -- AURA -- DEATH PULSE / PURPLE HELLFIRE / PESTILENCE ------------------
    rY = 0.4

    # PLAGUE RINGS -- green-tinted, with a tight inner purple corruption ring
    ph0 = float(tick % 36)
    ex0 = (ph0 if ph0 < 18 else 36 - ph0) * 0.11
    ph1 = float(tick % 26)
    ex1 = (ph1 if ph1 < 13 else 26 - ph1) * 0.14
    m.ring3d(0, rY, 0, 3.5 * U, 1.8, 0x6010A0, 0.85)   # inner purple ring
    m.ring3d(0, rY, 0, 6 * U + ex0, 3.0, SC_GLOW, 0.55)
    m.ring3d(0, rY, 0, 8 * U + ex1, 2.4, SC_GLOW, 0.28)

    # PURPLE HELLFIRE -- 8 flame tongues rising with hot->dim gradient.
    # Same structure as Dire's fel-fire but in purple (death magic, not fel).
    maxPFH = 7 * U
    for i in range(8):
        phase = math.fmod(tickF * 0.75 + PPH[i], 20.0) / 20.0
        fh = phase * maxPFH
        fw = 0.4 + 0.18 * math.sin(tickF * 1.3 + i * 0.8)
        fx, fz = PFX[i] * U * 0.44, PFZ[i] * U * 0.44

        # outer tongue -- full height, dim purple rim
        m.line3d((fx + fw, rY, fz + fw), (fx + fw * 0.5, rY + fh, fz + fw * 0.5),
                 SC_PURP_MID, 0.40, px=2.0, col1=SC_PURP_DIM, mul1=0.04)
        # mid tongue -- 3/4 height, purple gradient
        m.line3d((fx, rY, fz), (fx, rY + fh * 0.75, fz),
                 SC_PURP_MID, 0.72, px=3.0, col1=SC_PURP_DIM, mul1=0.06)
        # core -- 1/2 height, white-purple hot -> purple fade
        m.line3d((fx - fw, rY, fz - fw),
                 (fx - fw * 0.3, rY + fh * 0.50, fz - fw * 0.3),
                 SC_PURP_HOT, 1.00, px=4.0, col1=SC_PURP_MID, mul1=0.15)
        # bright base ember
        m.cube3(fx, rY + 0.2, fz, 0.85, SC_PURP_HOT,
                1.05 + 0.25 * math.sin(tickF * 1.8 + i))

    # FALLING PESTILENCE DROPS -- 6 sickly green particles from above the hood,
    # falling to ground level and fading.
    dropStartH = 18 * U
    for i in range(6):
        period = 22.0
        phase = math.fmod(tickF * 0.8 + DPH[i], period) / period   # 0..1 fall
        dy = rY + dropStartH * (1.0 - phase)                       # high -> low
        drift2 = math.sin(tickF * 0.3 + DPH[i]) * 1.2
        dx, dz = DPX[i] * U * 0.5 + drift2, DPZ[i] * U * 0.5
        alpha = (1.0 - phase * 0.80) * 0.80    # bright at top -> dim at ground

        # a small splattering cube that flattens as it nears the ground
        dropSz = 0.9 + 0.3 * (1.0 - phase)
        m.cube3(dx, dy, dz, dropSz, SC_PEST, alpha * 1.20)
        # drip trail above the drop
        m.line3d((dx, dy, dz), (dx, dy + 2 * U, dz),
                 SC_PEST, alpha * 0.40, px=1.0, col1=SC_GLOW, mul1=0.02)

    return m.build(**bake)
