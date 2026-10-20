"""Elf Hero "Sylvara" -- Lunar Huntress / Moon-Druid (RACE_ELF).

Port of src/gfx/models3d/elf_hero.cpp, C++ numbers verbatim.

One recurring correction, applied here as it was in dire_hero.py: the tapered
ribbons (antlers, bow limbs) are emitted as a GL_QUADS run whose four vertices
go near-left, near-right, far-left, far-right. Fed to GL_QUADS in that order
the quad crosses itself; _ribbon() below takes the pairs as the source writes
them and emits the flat ribbon they describe.
"""

import math

from claude_studio.craftwar_gl import U, GLModel

EL_BODY = 0x3C5028   # fitted forest leather
EL_DARK = 0x0A140C   # near-black outline
EL_BARK = 0x506030   # leaf-mantle bark tone
EL_GLOW = 0x90E8A0   # moonlit heartwood glow
EL_MOON = 0xD0FFE0   # pale silver-moon highlight
EL_LEAF = 0x60A050   # leaf cluster green
EL_SKIN = 0xC8C0B0   # forest elf pale complexion
EL_WISP = 0x70C8FF   # sky-blue wisp color

WR = (3.5, 4.8, 2.8, 5.5, 3.9)            # wisp orbit radii (xU)
WS = (0.15, 0.09, 0.19, 0.07, 0.12)       # angular speeds
WY = (2 * U, 4 * U, 6 * U, 3 * U, 8 * U)  # hover heights
WP = (0, 1.25, 2.5, 3.75, 5.0)            # phase offsets

LBX = (3.5, -4.0, 2.0, -2.8, 5.0, -1.5, 4.2, -3.5)
LBZ = (-2.5, 3.0, -4.5, 2.0, -1.5, 4.0, -3.0, 1.8)
LPH = (0, 2.5, 5.3, 8.1, 10.7, 13.2, 16.0, 18.8)
LSP = (0.70, 0.90, 0.60, 0.80, 1.10, 0.70, 1.00, 0.85)


def _ribbon(m, n0, n1, f0, f1, col, mul):
    m.quad(n0, n1, f1, f0, col, mul)


def build(tickF=0.0, anim=0, name="ELF_hero", **bake):
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

    # bw=3, bh=6 -- THE SLIMMEST HERO. Deliberate opposite of the 6-wide hulks.
    lY0, lY1 = 0, 6 * U
    tX0, tX1 = -4.5, 4.5         # 3 sprite units = 9 world units total
    tY0, tY1 = 6 * U, 12 * U     # 6 sprite units tall
    tZ0, tZ1 = -2.0, 2.0         # shallow depth -- willowy, not thick
    hY0, hY1 = tY1, tY1 + 3 * U  # head: 3 units tall (slim elongated face)

    # LEGS -- single-cell stance, reed-slim (agility over armor)
    m.box3d(tX0, lY0, -1.2, tX0 + 2.5, lY1, 1.2, EL_DARK)       # left
    m.box3d(tX1 - 2.5, lY0, -1.2, tX1, lY1, 1.2, EL_DARK)       # right

    # TORSO -- slim fitted leather cuirass
    m.box3d(tX0, tY0, tZ0, tX1, tY1, tZ1, EL_BODY)
    # full-width horizontal wraps: underbust + waist belt
    w1y, w2y = tY0 + (tY1 - tY0) / 3.0, tY0 + 2 * (tY1 - tY0) / 3.0
    m.box3d(tX0, w1y, tZ1, tX1, w1y + 0.5, tZ1 + 0.6, EL_DARK)
    m.box3d(tX0, w2y, tZ1, tX1, w2y + 0.5, tZ1 + 0.6, EL_DARK)
    # near-black outline rim (green-on-green legibility, as in 2D)
    m.box3d(tX0, tY0, tZ0, tX0 + 0.3, tY1, tZ1, EL_DARK, 0.60)
    m.box3d(tX1 - 0.3, tY0, tZ0, tX1, tY1, tZ1, EL_DARK, 0.60)

    # HEARTWOOD GLOW VEIN -- bioluminescent down the sternum
    vGlow = 1.0 + 0.45 * math.sin(tickF * 0.22)
    m.box3d(-0.5, tY0 + U * 0.5, tZ1, 0.5, tY1 - U * 0.5, tZ1 + 0.8, EL_GLOW, vGlow)
    # attack: vein flares wider -- moon-goddess rage
    m.box3d(-1.0, tY0 + U, tZ1, 1.0, tY1 - U, tZ1 + 0.5, EL_GLOW, vGlow * 0.45)

    # MOONLIT RIM-LIGHT -- left edge (leading-edge sheen, Artemis idiom)
    m.box3d(tX0 - 0.3, tY0 + U * 0.5, tZ0, tX0, tY1 - U * 0.5, tZ1, EL_MOON, 0.50)

    # CRESCENT-MOON CLASP -- off-center at LEFT shoulder collar
    m.cube3(tX0 + U * 0.5, tY1 - U * 0.6, tZ1 + 1.0, 1.3, EL_GLOW, 1.15)
    m.cube3(tX0 + U * 0.5 + 1.4, tY1 - U * 0.6, tZ1 + 1.5, 1.1, EL_BODY, 1.00)

    # ASYMMETRIC LEAF-MANTLE -- right shoulder ONLY, 3 layered clusters
    mX, mY = tX1 + 0.5, tY1 - U * 1.5
    m.box3d(mX, mY, tZ0, mX + 3.5 * U, mY + 2.5 * U, tZ1, EL_BARK, 0.75)
    m.box3d(mX + U * 0.5, mY - U, tZ0 + 0.3, mX + 3.0 * U, mY + U, tZ1 + 0.5, EL_LEAF, 0.90)
    m.box3d(mX, mY + U * 1.2, tZ1, mX + 2.0 * U, mY + 2.5 * U, tZ1 + 1.0, 0x98E8A8, 1.00)
    # trailing tendril downward
    m.box3d(mX + U * 0.5, tY0 + 2 * U, tZ0 + 0.5, mX + 2.0 * U, tY1 - 2.5 * U, tZ1 - 0.3,
            EL_BARK, 0.55)

    # SLIM ARMS -- thin single-cell reach, pendulum on walk
    armSwSpd = 2.8 if anim == 1 else 0.3
    armSwAmt = 4.5 if anim == 1 else (2.0 if anim == 2 else 1.5)
    armSwL = math.sin(tickF * armSwSpd) * armSwAmt
    armSwR = -armSwL
    m.box3d(tX0 - 2.5, tY0 + 0.5 * U + armSwL, tZ0, tX0, tY0 + 2.5 * U + armSwL, tZ1,
            EL_DARK, 0.80)
    m.box3d(tX1, tY0 + 0.5 * U + armSwR, tZ0, tX1 + 2.5, tY0 + 2.5 * U + armSwR, tZ1,
            EL_DARK, 0.80)

    # HEAD -- narrow, elongated
    fW = 2.5 * U     # slightly wider than 2*U for readability
    m.box3d(-fW * 0.5, hY0, tZ0, fW * 0.5, hY1, tZ1, EL_SKIN)
    m.box3d(-fW * 0.5, hY0, tZ1 - 0.1, fW * 0.5, hY0 + 0.5, tZ1 + 0.4, EL_DARK)  # jaw line
    # moonlit glowing eyes -- they GLOW, not flat dots
    eGlow = 1.0 + 0.55 * math.sin(tickF * 0.28)
    m.cube3(-fW * 0.25, hY0 + U * 1.0, tZ1 + 1.1, 1.0, EL_GLOW, eGlow)
    m.cube3(fW * 0.25, hY0 + U * 1.0, tZ1 + 1.1, 1.0, EL_GLOW, eGlow)

    # BROW CRESCENT CIRCLET -- crescent of moonlight on the brow
    m.cube3(0, hY1 - 0.5, tZ1 + 0.8, 1.4, EL_GLOW, 1.25)
    m.cube3(1.5, hY1 - 0.5, tZ1 + 1.3, 1.1, EL_SKIN, 1.00)   # bites out right

    # ANTLERS + POINTED CROWN -- sweep upward-back, leaf clusters at the tips
    _ribbon(m, (-fW * 0.45, hY1, -0.5), (-fW * 0.45, hY1, 0.5),
            (-fW * 0.45 - 2.5 * U, hY1 + 3.5 * U, -0.8),
            (-fW * 0.45 - 2.5 * U, hY1 + 3.5 * U, 0.3), 0xA09060, 0.85)
    _ribbon(m, (fW * 0.45, hY1, -0.5), (fW * 0.45, hY1, 0.5),
            (fW * 0.45 + 2.5 * U, hY1 + 3.5 * U, -0.8),
            (fW * 0.45 + 2.5 * U, hY1 + 3.5 * U, 0.3), 0xA09060, 0.85)
    # Center crown spike -- tall central point (already a proper trapezoid)
    m.quad((-U * 0.5, hY1, -0.4), (U * 0.5, hY1, -0.4),
           (U * 0.3, hY1 + 4.5 * U, -0.2), (-U * 0.3, hY1 + 4.5 * U, -0.2), EL_MOON, 0.90)
    # Leaf clusters at antler tips
    m.cube3(-fW * 0.45 - 2.5 * U, hY1 + 3.5 * U, -0.3, 2.0, EL_BARK, 1.00)
    m.cube3(fW * 0.45 + 2.5 * U, hY1 + 3.5 * U, -0.3, 2.0, EL_BARK, 1.00)
    m.cube3(-fW * 0.45 - 2.5 * U, hY1 + 3.5 * U, 0.2, 1.4, EL_LEAF, 1.10)
    m.cube3(fW * 0.45 + 2.5 * U, hY1 + 3.5 * U, 0.2, 1.4, EL_LEAF, 1.10)
    # crown tip glint
    m.cube3(0, hY1 + 4.5 * U, -0.2, 1.0, EL_MOON, 1.30)

    # MOONBOW -- curved bow of living bark, held left
    bwX, bwZ, bwMY = -14.0, 1.0, tY0 + 3 * U
    if anim == 2:
        bowAng = math.sin(atkP) * 30.0
    elif anim == 1:
        bowAng = math.sin(walkP * 0.5) * 5.0
    else:
        bowAng = 0.0
    m.push()
    m.translate(bwX, bwMY, bwZ)
    m.rotate(bowAng, 1, 0, 0)
    m.translate(-bwX, -bwMY, -bwZ)
    bwH = 7 * U
    # grip -- wrapped in dark leather
    m.box3d(bwX - 0.4, bwMY - U, bwZ - 0.2, bwX + 0.4, bwMY + U, bwZ + 0.2, 0x604030, 0.95)
    # Upper limb
    _ribbon(m, (bwX - 0.4, bwMY + U, bwZ - 0.3), (bwX + 0.3, bwMY + U, bwZ + 0.2),
            (bwX - 2.5, bwMY + bwH, bwZ - 0.4), (bwX + 0.2, bwMY + bwH, bwZ + 0.1),
            EL_BODY, 0.90)
    # Lower limb
    _ribbon(m, (bwX - 0.4, bwMY - U, bwZ - 0.3), (bwX + 0.3, bwMY - U, bwZ + 0.2),
            (bwX - 2.5, bwMY - bwH, bwZ - 0.4), (bwX + 0.2, bwMY - bwH, bwZ + 0.1),
            EL_BODY, 0.80)
    # Bowstring -- glow moon-light
    m.box3d(bwX - 0.1, bwMY - bwH, bwZ + 0.5, bwX + 0.1, bwMY + bwH, bwZ + 0.7, EL_MOON, 0.55)
    # Nocked arrow -- glowing moonlit shaft
    m.box3d(bwX + 0.0, bwMY, bwZ + 0.6, bwX + 11 * U, bwMY + 0.25, bwZ + 0.8, EL_MOON, 0.85)
    m.cube3(bwX + 11 * U, bwMY + 0.12, bwZ + 0.7, 1.0, EL_GLOW, 1.50)   # arrowhead glow
    m.pop()   # end bow rotation

    m.pop()   # end body bob

    # -- AURA -- LUNAR MOONBEAM STORM ---------------------------------------
    rY = 0.3

    # SILVER-MOON RINGS -- radial gradient: inner bright -> outer ghost
    ph0 = float(tick % 38)
    ex0 = (ph0 if ph0 < 19 else 38 - ph0) * 0.12
    ph1 = float(tick % 26)
    ex1 = (ph1 if ph1 < 13 else 26 - ph1) * 0.15
    m.ring3d(0, rY, 0, 3.2 * U, 1.8, EL_MOON, 0.92)      # tight core
    m.ring3d(0, rY, 0, 5 * U + ex0, 2.8, EL_MOON, 0.62)
    m.ring3d(0, rY, 0, 7 * U + ex1, 2.2, EL_GLOW, 0.32)

    # WISPS -- 5 glowing orbs orbiting at varying radii and heights
    for i in range(5):
        ang = tickF * WS[i] + WP[i]
        wx, wz = math.cos(ang) * WR[i] * U, math.sin(ang) * WR[i] * U
        pulse = 0.65 + 0.35 * math.sin(tickF * 0.25 + i)
        m.wisp3(wx, rY + WY[i], wz, 4.5, EL_WISP, pulse)
        # trailing tail in orbit direction
        tailAng = ang - 0.28
        tx, tz = math.cos(tailAng) * WR[i] * U, math.sin(tailAng) * WR[i] * U
        m.line3d((wx, rY + WY[i], wz), (tx, rY + WY[i] + 0.4, tz),
                 EL_GLOW, pulse * 0.50, px=1.5, col1=EL_GLOW, mul1=0.02)

    # FALLING LEAVES -- 8 leaves drifting down from crown height, fading out.
    # Flat diamond using GL_TRIANGLES; independent fall speed and phase each.
    leafH = 12 * U
    for i in range(8):
        period = 20.0
        phase = math.fmod(tickF * LSP[i] + LPH[i], period) / period   # 0..1 fall
        ly = rY + leafH * (1.0 - phase)                               # top -> ground
        drift = math.sin(tickF * 0.4 + LPH[i]) * 1.8                  # lateral drift
        lx, lz = LBX[i] * U * 0.5 + drift, LBZ[i] * U * 0.5 + drift * 0.5
        alpha = 1.0 - phase * 0.88                                    # bright -> gone
        sz = 0.85 + 0.40 * math.sin(LPH[i])                           # size variety

        m.tri((lx - sz, ly, lz), (lx, ly, lz - sz), (lx + sz, ly, lz), EL_LEAF, alpha * 0.90)
        m.tri((lx - sz, ly, lz), (lx, ly, lz + sz), (lx + sz, ly, lz), EL_GLOW, alpha * 0.50)
        # underside slightly darker
        m.tri((lx - sz, ly - 0.3, lz), (lx, ly - 0.3, lz - sz), (lx + sz, ly - 0.3, lz),
              EL_BARK, alpha * 0.35)

    return m.build(**bake)
