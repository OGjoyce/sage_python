"""Mayan Hero "Tecun Uman" -- K'iche' Warrior King (RACE_MAYAN = 7).

Port of drawMayanHero3D in src/gfx/models3d/mayan_hero.cpp, C++ numbers
verbatim. The Tikal Pyramid from the same file is in mayan_bldg.py.

This is the model that leans hardest on wisp3 -- the pyrite mirror disc, the
spear flare, the quetzal nahualli's body and six orbiting spirit wisps are all
camera-facing billboards in the game. See craftwar_gl.wisp3 for how they are
reproduced without a camera to face.
"""

import math

from claude_studio.craftwar_gl import U, GLModel

TU_SKIN = 0xBB7840     # tawny Mayan brown (face / arms)
TU_BODY = 0x28B050     # bright jade-green cuirass
TU_JADE = 0x1E9070     # deep jade (inlays, knee guards, sash, pauldrons)
TU_JADE_LT = 0x2FBB90  # bright jade highlight (inlay vlines, studs, pendants)
TU_DARK = 0x141C18     # near-obsidian dark (legs, plate seams)
TU_QUETZAL = 0x1A9030  # quetzal feather emerald (outer plumes, bird body)
TU_QLIGHT = 0x30CC60   # bright quetzal shimmer (center plumes, glow bead)
TU_GOLD = 0xD4921A     # copper-gold (headband, disc, pauldron rims)
TU_OBSID = 0x181618    # obsidian black (spear tip, outline strips)
TU_OBS_LT = 0x9878D0   # obsidian glint (spear tip highlight)
TU_RED = 0xCC2020      # scarlet (quetzal breast, war paint)
TU_WOOD = 0x5A3818     # dark brown wood (spear shaft)

SWEEP_BASE = (0.7854, 2.3562, 3.9270, 5.4978)


def build(tickF=0.0, anim=0, name="MAYAN_hero", **bake):
    """**bake is forwarded to GLModel.build() -- unlit/emit_strength/
    emit_threshold, for dropping the model into a lit scene."""
    tick = int(tickF)
    m = GLModel(name)

    idleP = tickF * 0.8
    walkP = tickF * 2.6
    atkP = tickF * 3.0
    if anim == 1:
        bodyBob = abs(math.sin(walkP)) * 2.5
    elif anim == 0:
        bodyBob = math.sin(idleP) * 0.6
    else:
        bodyBob = 0.0

    m.push()
    m.translate(0.0, bodyBob, 0.0)
    if anim == 2:
        m.rotate(math.sin(atkP) * 8.0, 0.0, 0.0, 1.0)

    # Body geometry constants -- match 2D: bw=5, bh=6, lean/agile
    lY0, lY1 = 0, 5.0 * U                   # legs (lean = slightly shorter)
    tX0, tX1 = -7.0, 7.0                    # torso: ~5 wide
    tY0, tY1 = lY1, lY0 + 10.0 * U          # torso: ~6 tall
    tZ0, tZ1 = -4.0, 4.0
    hY0, hY1 = tY1, tY1 + 2.2 * U           # head

    # -- SANDAL SOLES --------------------------------------------------------
    m.box3d(-6.5, 0.0, -3.5, 0.0, 0.8, 3.5, TU_DARK, 0.55)
    m.box3d(0.0, 0.0, -3.5, 6.5, 0.8, 3.5, TU_DARK, 0.55)

    # -- LEGS -- lean dark warrior (agile, not titan) ------------------------
    lW = 2.5
    m.box3d(-6.5, lY0, -3.0, -6.5 + lW * 2, lY1, 3.0, TU_DARK, 0.88)       # left
    m.box3d(6.5 - lW * 2, lY0, -3.0, 6.5, lY1, 3.0, TU_DARK, 0.88)         # right
    # Jade knee guards (2D has these explicitly)
    m.box3d(-6.5, lY1 - U, -3.0, -6.5 + lW * 2, lY1 + 0.5 * U, 3.0, TU_JADE, 0.95)
    m.box3d(6.5 - lW * 2, lY1 - U, -3.0, 6.5, lY1 + 0.5 * U, 3.0, TU_JADE, 0.95)

    # -- TORSO -- jade-green cuirass matching 2D ----------------------------
    m.box3d(tX0, tY0, tZ0, tX1, tY1, tZ1, TU_BODY)
    # Obsidian outline strips on the front face
    m.box3d(tX0 - 0.5, tY0, tZ1, tX0, tY1, tZ1 + 0.6, TU_OBSID, 0.72)      # left
    m.box3d(tX1, tY0, tZ1, tX1 + 0.5, tY1, tZ1 + 0.6, TU_OBSID, 0.72)      # right
    m.box3d(tX0, tY0 - 0.4, tZ1, tX1, tY0, tZ1 + 0.5, TU_OBSID, 0.60)      # bottom
    m.box3d(tX0, tY1, tZ1, tX1, tY1 + 0.4, tZ1 + 0.5, TU_OBSID, 0.60)      # top

    # Two jade inlay vlines (1/5 and 4/5 of width)
    inLX = tX0 + (tX1 - tX0) / 5.0
    inRX = tX1 - (tX1 - tX0) / 5.0
    m.box3d(inLX - 0.45, tY0 + U, tZ1, inLX + 0.45, tY1 - U, tZ1 + 0.75, TU_JADE_LT, 0.92)
    m.box3d(inRX - 0.45, tY0 + U, tZ1, inRX + 0.45, tY1 - U, tZ1 + 0.75, TU_JADE_LT, 0.92)

    # Two horizontal obsidian plate seams
    seamY1 = tY0 + (tY1 - tY0) / 3.0
    seamY2 = tY0 + (tY1 - tY0) * 2.0 / 3.0
    m.box3d(inLX, seamY1 - 0.32, tZ1, inRX, seamY1 + 0.32, tZ1 + 0.65, TU_OBSID, 0.68)
    m.box3d(inLX, seamY2 - 0.32, tZ1, inRX, seamY2 + 0.32, tZ1 + 0.65, TU_OBSID, 0.68)

    # PYRITE MIRROR DISC on chest -- royal regalia
    discY = tY0 + (tY1 - tY0) * 0.38
    m.ring3d(0.0, discY, tZ1 + 1.2, 3.3, 1.0, TU_OBSID, 0.88)   # obsidian ring border
    m.wisp3(0.0, discY, tZ1 + 1.6, 3.0, TU_GOLD, 0.80)          # pyrite gold fill
    if anim == 2:   # attack -- flares outward
        m.ring3d(0.0, discY, tZ1 + 1.2, 4.8, 0.8, TU_GOLD, 0.50)

    # STEPPED-PYRAMID PAULDRONS -- 2 tiers, jade
    m.box3d(tX0 - 5.0, tY1 - 2 * U, tZ0, tX0, tY1 - U, tZ1, TU_JADE, 0.84)
    m.box3d(tX1, tY1 - 2 * U, tZ0, tX1 + 5.0, tY1 - U, tZ1, TU_JADE, 0.84)
    m.box3d(tX0 - 3.0, tY1 - U, tZ0, tX0, tY1, tZ1, TU_JADE, 0.84)
    m.box3d(tX1, tY1 - U, tZ0, tX1 + 3.0, tY1, tZ1, TU_JADE, 0.84)
    # gold accent rims on the outer edges of each tier
    m.box3d(tX0 - 5.6, tY1 - 2 * U - 0.4, tZ0, tX0 - 4.2, tY1 - U + 0.4, tZ1, TU_GOLD, 0.68)
    m.box3d(tX1 + 4.2, tY1 - 2 * U - 0.4, tZ0, tX1 + 5.6, tY1 - U + 0.4, tZ1, TU_GOLD, 0.68)

    # JADE BEAD SASH at waist + 2 swinging pendants + glow bead
    sashY = tY0 + 0.6 * U
    m.box3d(tX0 + U, sashY, tZ0, tX1 - U, sashY + 0.55 * U, tZ1 + 0.4, TU_JADE, 0.88)
    pendSwing = math.sin(tickF * 0.28) * 1.8
    m.cube3(tX0 + 3.2 + pendSwing, sashY - 2.0, tZ1 + 0.2, 1.1, TU_JADE_LT, 0.96)
    m.cube3(tX1 - 3.2 - pendSwing, sashY - 2.0, tZ1 + 0.2, 1.1, TU_JADE_LT, 0.96)
    glowBead = 0.85 + 0.38 * math.sin(tickF * 0.35)
    m.cube3(0.0, sashY - 3.0, tZ1 + 0.2, 1.1, TU_QLIGHT, glowBead)

    # -- ARMS -- pendulum swing ---------------------------------------------
    aSpd = 2.6 if anim == 1 else 0.3
    aAmt = 4.0 if anim == 1 else (2.0 if anim == 2 else 1.2)
    aSwL = math.sin(tickF * aSpd) * aAmt
    aSwR = -aSwL
    rZ1 = tZ1 + 2.0 if anim == 2 else tZ1
    m.box3d(tX0 - 4.5, tY0 + 0.5 * U + aSwL, tZ0, tX0 - 0.5, tY0 + 2.5 * U + aSwL, tZ1,
            TU_SKIN, 0.90)
    m.box3d(tX1 + 0.5, tY0 + 0.5 * U + aSwR, tZ0, tX1 + 4.5, tY0 + 2.5 * U + aSwR, rZ1,
            TU_SKIN, 0.90)
    # jade wristbands
    m.box3d(tX0 - 5.0, tY0 + 1.2 * U + aSwL - 0.5, tZ0, tX0,
            tY0 + 1.2 * U + aSwL + 0.5, tZ1, TU_JADE, 0.80)
    m.box3d(tX1, tY0 + 1.2 * U + aSwR - 0.5, tZ0, tX1 + 5.0,
            tY0 + 1.2 * U + aSwR + 0.5, rZ1, TU_JADE, 0.80)

    # -- OBSIDIAN-TIPPED SPEAR -- vertical shaft held upright ---------------
    spX = tX1 + 3.0
    spBY = lY0 - 2.5              # base below feet
    spTY = hY1 + 5.0 * U          # tip above headdress level
    spZ = tZ1 + 0.9
    if anim == 2:                 # thrust on attack
        spX += math.sin(atkP) * 3.0
        spZ += 2.0
    # wooden shaft
    m.box3d(spX - 0.55, spBY, spZ - 0.55, spX + 0.55, spTY - 1.8 * U, spZ + 0.55,
            TU_WOOD, 0.82)
    # obsidian blade tip -- tapers upward
    m.box3d(spX - 1.0, spTY - 1.8 * U, spZ - 1.0, spX + 1.0, spTY - 0.8 * U, spZ + 1.0,
            TU_OBSID, 0.92)
    m.box3d(spX - 0.6, spTY - 0.8 * U, spZ - 0.6, spX + 0.6, spTY, spZ + 0.6,
            TU_OBSID, 0.98)
    m.cube3(spX, spTY, spZ, 0.9, TU_OBS_LT, 1.12)    # glint at tip
    if anim == 2:    # attack: tip flares
        sp = 1.1 + 0.9 * abs(math.sin(tickF * 5.0))
        m.cube3(spX, spTY, spZ, 1.3, TU_OBS_LT, sp)
        m.wisp3(spX, spTY + 1.5, spZ, 2.5, TU_OBS_LT, 0.65 * sp)

    # -- HEAD -- warm skin face ---------------------------------------------
    m.box3d(-2 * U, hY0, tZ0, 2 * U, hY1, tZ1, TU_SKIN)
    m.box3d(-2 * U, hY0, tZ1 - 0.2, 2 * U, hY0 + 0.4, tZ1 + 0.4, TU_OBSID, 0.60)  # jawline
    # Eyes at outer corners
    m.box3d(-5.5, hY0 + U * 0.45, tZ1, -2.2, hY0 + U, tZ1 + 1.2, 0x201810)
    m.box3d(2.2, hY0 + U * 0.45, tZ1, 5.5, hY0 + U, tZ1 + 1.2, 0x201810)
    # Jade nose ornament -- center of face (royal mark)
    m.cube3(0.0, hY0 + U * 0.55, tZ1 + 1.5, 0.88, TU_JADE_LT, 1.12)
    # Jade ear flares -- large royal discs
    earY = hY0 + 0.7 * U
    m.ring3d(-2 * U - 3.5, earY, 0.0, 2.4, 0.7, TU_JADE, 0.88)
    m.cube3(-2 * U - 3.5, earY, 0.0, 0.9, TU_JADE_LT, 1.05)
    m.ring3d(2 * U + 3.5, earY, 0.0, 2.4, 0.7, TU_JADE, 0.88)
    m.cube3(2 * U + 3.5, earY, 0.0, 0.9, TU_JADE_LT, 1.05)

    # -- HEADDRESS ----------------------------------------------------------
    # Gold warrior headband at brow with jade studs at each end
    m.box3d(-2 * U - U, hY1 - 0.85, tZ0, 2 * U + U, hY1, tZ1, TU_GOLD, 0.88)
    m.cube3(-(2 * U + U), hY1 - 0.45, 0.0, 0.88, TU_JADE, 0.92)   # left jade stud
    m.cube3((2 * U + U), hY1 - 0.45, 0.0, 0.88, TU_JADE, 0.92)    # right jade stud

    # Quetzal feather plume fan -- 6 plumes matching the 2D fan exactly:
    #   Outer pair: angle outward to ~6s height (jade)
    #   Fill/flanking: shorter at ~5s, darker jade
    #   Center pair: straight up to ~7s, tallest, bright glow-green
    ps = math.sin(tickF * 0.15) * 0.8    # gentle idle sway

    # Outer plumes -- angle outward
    m.tri((-2.5 * U + ps, hY1, 0.5), (-6.5 * U + ps * 0.3, hY1 + 8.0 * U, 0.0),
          (-2.5 * U + ps, hY1, -0.5), TU_QUETZAL, 0.75)
    m.tri((-2.5 * U + ps, hY1, 1.3), (-6.5 * U + ps * 0.3, hY1 + 8.0 * U, 0.0),
          (-2.5 * U + ps, hY1, -1.3), TU_QUETZAL, 0.48)
    m.tri((2.5 * U - ps, hY1, 0.5), (6.5 * U - ps * 0.3, hY1 + 8.0 * U, 0.0),
          (2.5 * U - ps, hY1, -0.5), TU_QUETZAL, 0.75)
    m.tri((2.5 * U - ps, hY1, 1.3), (6.5 * U - ps * 0.3, hY1 + 8.0 * U, 0.0),
          (2.5 * U - ps, hY1, -1.3), TU_QUETZAL, 0.48)

    # Shorter fill/flanking plumes
    m.tri((-1.5 * U + ps * 0.6, hY1, 0.9), (-4.5 * U + ps * 0.4, hY1 + 6.0 * U, 0.0),
          (-1.5 * U + ps * 0.6, hY1, -0.9), TU_JADE, 0.52)
    m.tri((1.5 * U - ps * 0.6, hY1, 0.9), (4.5 * U - ps * 0.4, hY1 + 6.0 * U, 0.0),
          (1.5 * U - ps * 0.6, hY1, -0.9), TU_JADE, 0.52)

    # Center pair -- tallest, straight up
    m.tri((-1.2 * U + ps * 0.15, hY1 + 0.8 * U, 0.8),
          (-0.6 * U + ps * 0.08, hY1 + 10.5 * U, 0.0),
          (-1.2 * U + ps * 0.15, hY1 + 0.8 * U, -0.8), TU_QLIGHT, 0.96)
    m.tri((-1.5 * U, hY1 + 0.8 * U, 1.6),
          (-0.6 * U + ps * 0.08, hY1 + 10.5 * U, 0.0),
          (-1.5 * U, hY1 + 0.8 * U, -1.6), TU_QLIGHT, 0.60)
    m.tri((1.2 * U - ps * 0.15, hY1 + 0.8 * U, 0.8),
          (0.6 * U - ps * 0.08, hY1 + 10.5 * U, 0.0),
          (1.2 * U - ps * 0.15, hY1 + 0.8 * U, -0.8), TU_QLIGHT, 0.96)
    m.tri((1.5 * U, hY1 + 0.8 * U, 1.6),
          (0.6 * U - ps * 0.08, hY1 + 10.5 * U, 0.0),
          (1.5 * U, hY1 + 0.8 * U, -1.6), TU_QLIGHT, 0.60)

    # Plume tip glints
    m.cube3(-6.5 * U + ps * 0.3, hY1 + 8.0 * U, 0.0, 0.9, TU_QUETZAL, 1.00)
    m.cube3(6.5 * U - ps * 0.3, hY1 + 8.0 * U, 0.0, 0.9, TU_QUETZAL, 1.00)
    cPulse = 1.10 + 0.42 * math.sin(tickF * 0.30)
    m.cube3(-0.6 * U + ps * 0.08, hY1 + 10.5 * U, 0.0, 1.2, TU_QLIGHT, cPulse)  # tallest
    m.cube3(0.6 * U - ps * 0.08, hY1 + 10.5 * U, 0.0, 1.2, TU_QLIGHT, cPulse)   # tallest
    m.wisp3(0.0, hY1 + 12.0 * U, 0.0, 3.2, TU_QLIGHT, 0.58 * cPulse)            # glow crown

    m.pop()   # end body bob

    # -- QUETZAL NAHUALLI -- spirit companion bird at shoulder --------------
    # Bobs independently of the hero bob (so it reads as floating, not attached).
    birdBob = math.sin(tickF * 0.22 + 1.57) * 1.8
    birdX = -(tX1 + 9.5)                 # left shoulder side
    birdY = tY1 - 0.5 * U + birdBob      # shoulder height
    birdZ = 0.0                          # center depth -- visible from the front

    # Jade-green body
    m.ring3d(birdX, birdY, birdZ, 2.8, 0.65, TU_QUETZAL, 0.82)
    m.wisp3(birdX, birdY, birdZ, 2.4, TU_QUETZAL, 0.70)
    # Scarlet breast
    m.cube3(birdX + 0.5, birdY - 0.5, birdZ + 0.6, 0.85, TU_RED, 0.88)

    # Long trailing tail plumes going down-toward-hero
    m.line3d((birdX, birdY - 1.5, birdZ), (birdX + 7.0, birdY - 9.0, birdZ),
             TU_QLIGHT, 0.88, px=1.0)
    m.line3d((birdX + 0.6, birdY - 1.5, birdZ), (birdX + 9.0, birdY - 11.0, birdZ),
             TU_JADE, 0.52, px=1.0)

    # Wing spread on attack (the nahualli mirrors the warrior's ferocity)
    if anim == 2:
        m.tri((birdX, birdY, birdZ), (birdX - 5.0, birdY + 4.0, birdZ),
              (birdX + 3.0, birdY + 3.0, birdZ), TU_QLIGHT, 0.72)
        m.tri((birdX, birdY, birdZ), (birdX - 4.0, birdY + 3.5, birdZ + 1.8),
              (birdX + 2.0, birdY + 3.0, birdZ + 1.8), TU_JADE, 0.48)

    # -- AURA -- QUETZAL SPIRIT ---------------------------------------------
    rY = 0.4

    # GROUND EMERALD DISC -- expanding wave, 20-tick cycle
    discPhase = float(tick % 20) / 20.0
    discR = discPhase * 5.0 * U
    m.ring3d(0.0, rY, 0.0, discR, 1.5, TU_QLIGHT, 0.85 * (1.0 - discPhase * 0.5))
    m.ring3d(0.0, rY, 0.0, discR + 1.4, 0.9, TU_JADE, 0.55 * (1.0 - discPhase))

    # JADE ORBIT RINGS -- 3 concentric, independent breathing periods
    ph0 = float(tick % 24)
    ex0 = (ph0 if ph0 < 12 else 24 - ph0) * 0.14
    ph1 = float(tick % 32)
    ex1 = (ph1 if ph1 < 16 else 32 - ph1) * 0.12
    ph2 = float(tick % 16)
    ex2 = (ph2 if ph2 < 8 else 16 - ph2) * 0.18
    Rin = 3.5 * U + ex2
    R0 = 6.5 * U + ex0
    R1 = 8.5 * U + ex1
    m.ring3d(0.0, rY, 0.0, Rin, 2.0, TU_JADE_LT, 0.95)
    m.ring3d(0.0, rY, 0.0, R0, 3.2, TU_JADE, 0.65)
    m.ring3d(0.0, rY, 0.0, R1, 2.5, TU_QUETZAL, 0.38)

    # LOGARITHMIC-SPIRAL FEATHER SWEEPS -- 4 arcs at the cardinal diagonals
    featherPulse = 1.0 + 0.45 * math.sin(tickF * 0.18 + 1.5)
    logRatio = math.log(R1 / Rin)
    for s in range(4):
        baseAng = SWEEP_BASE[s] + math.sin(tickF * 0.10 + s * 0.8) * 0.06
        for seg in range(8):
            t0 = seg / 8.0
            t1 = (seg + 1) / 8.0
            r0 = Rin * math.exp(t0 * logRatio)
            r1 = Rin * math.exp(t1 * logRatio)
            a0 = baseAng + t0 * 0.38
            a1 = baseAng + t1 * 0.38
            fade = 1.0 - t0 * 0.7
            col = TU_QLIGHT if seg < 4 else TU_JADE
            m.line3d((math.cos(a0) * r0, rY, math.sin(a0) * r0),
                     (math.cos(a1) * r1, rY, math.sin(a1) * r1),
                     col, fade * 0.85 * featherPulse, px=2.2,
                     col1=col, mul1=fade * 0.18)

    # ORBITING JADE WISPS -- 6 wisps circling in a sinusoidal orbit
    for i in range(6):
        ang = tickF * 0.08 + i * (3.14159 * 2.0 / 6.0)
        wR = R0 * 0.60 + math.sin(tickF * 0.20 + i * 1.1) * U
        wX = math.cos(ang) * wR
        wZ = math.sin(ang) * wR
        wY = rY + math.sin(tickF * 0.25 + i * 0.85) * 1.5
        wFd = 0.55 + 0.45 * math.sin(tickF * 0.30 + i * 0.7)
        wCol = TU_JADE_LT if i % 2 == 0 else TU_QLIGHT
        m.wisp3(wX, wY, wZ, 2.6, wCol, wFd)

    return m.build(**bake)
