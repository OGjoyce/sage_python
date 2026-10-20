"""Horde Hero "Thrall" -- Orc Shaman (RACE_HORDE).

Port of src/gfx/models3d/horde_hero.cpp, C++ numbers verbatim. The curled ram
horns list their vertices near-left, near-right, far-right, far-left, which is
already proper ring order, so unlike the Dire horns and the Elf antlers they
are passed through unchanged.
"""

import math

from claude_studio.craftwar_gl import U, GLModel

HR_SKIN = 0x6E8A3A    # orc green hide
HR_DARK = 0x120F08    # near-black outline
HR_FUR = 0x4A5820     # hide/fur mantle
HR_BONE = 0xDCC8A0    # weathered bone (skull, necklace)
HR_GLOW = 0x40B0FF    # spirit-blue light in eye sockets
HR_ACCENT = 0xD09030  # amber horn rim-light
HR_TUSK = 0xF0F0E0    # ivory tusk

SKA = (0, 1.5708, 3.1416, 4.7124)
SPX = (2.5, -2.0, 4.5, -4.0, 0.8, -3.5)
SPZ = (-1.5, 3.0, -2.5, 1.8, 4.0, -0.5)
SPPH = (0, 3.8, 7.6, 11.4, 15.2, 18.5)
TBX = (-3.5, 0.5, 4.0)


def build(tickF=0.0, anim=0, name="HORDE_hero", **bake):
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
    if anim == 2:
        wepAng = math.sin(atkP) * (-50.0)
    elif anim == 1:
        wepAng = math.sin(walkP * 0.5) * 6.0
    else:
        wepAng = 0.0

    m.push()
    m.translate(0, bodyBob, 0)   # body bob

    # bw=6, bh=5 -- same hulking footprint as AI-Borg
    lY0, lY1 = 0, 6 * U
    tX0, tX1 = -9, 9
    tY0, tY1 = 6 * U, 11 * U
    tZ0, tZ1 = -4.5, 4.5
    hY0, hY1 = tY1, tY1 + 2 * U

    # LEGS -- hulking 2-cell, hide-wrapped (not plated)
    m.box3d(-6, lY0, -3, 0, lY1, 3, HR_FUR)
    m.box3d(0, lY0, -3, 6, lY1, 3, HR_FUR)
    m.box3d(-5.5, lY1 - 1.0, -2.5, -0.5, lY1 + 0.8, 2.5, HR_SKIN)
    m.box3d(0.5, lY1 - 1.0, -2.5, 5.5, lY1 + 0.8, 2.5, HR_SKIN)

    # TORSO -- bare orc hide
    m.box3d(tX0, tY0, tZ0, tX1, tY1, tZ1, HR_SKIN)

    # FUR/HIDE MANTLE -- covers top 2 rows of torso only (bh/5*2 = 40%)
    mantleY = tY1 - 2 * U
    m.box3d(tX0 - U, mantleY, tZ0, tX1 + U, tY1, tZ1, HR_FUR)
    m.box3d(tX0 - U, mantleY, tZ0, tX1 + U, tY1, tZ1, HR_FUR)
    # ragged fringe: 4 shaggy tufts hanging below mantle hem
    m.box3d(tX0 - U, mantleY - U, tZ0 + 0.5, tX0, mantleY, tZ1, 0x3A4818, 0.70)
    m.box3d(tX0, mantleY - U, tZ0 + 0.5, tX0 + U, mantleY, tZ1, 0x3A4818, 0.55)
    m.box3d(tX1 - U, mantleY - U, tZ0 + 0.5, tX1, mantleY, tZ1, 0x3A4818, 0.55)
    m.box3d(tX1, mantleY - U, tZ0 + 0.5, tX1 + U, mantleY, tZ1, 0x3A4818, 0.70)

    # BONE/TOOTH NECKLACE -- horizontal strip at mantle hem
    m.box3d(tX0 + U, mantleY - 0.6, tZ1, tX1 - U, mantleY + 0.4, tZ1 + 0.8, HR_BONE, 0.75)
    # two pendant teeth hanging below necklace line
    m.box3d(-3.5, mantleY - U, tZ1 + 0.2, -2.5, mantleY, tZ1 + 0.8, HR_BONE, 0.80)
    m.box3d(2.5, mantleY - U, tZ1 + 0.2, 3.5, mantleY, tZ1 + 0.8, HR_BONE, 0.80)

    # TRIBAL WARPAINT -- 2 dark geometric bands across the bare chest
    tb1, tb2 = tY0 + 3 * U, tY0 + 2 * U
    m.box3d(tX0 + U, tb1, tZ1, tX1 - U, tb1 + 0.6, tZ1 + 0.6, HR_DARK)
    m.box3d(tX0 + 2 * U, tb1 + 0.6, tZ1, tX0 + 3 * U, tb1 + 1.2, tZ1 + 0.5, HR_DARK)
    m.box3d(tX1 - 3 * U, tb1 - 0.5, tZ1, tX1 - 2 * U, tb1 + 0.2, tZ1 + 0.5, HR_DARK)
    m.box3d(tX0 + U, tb2, tZ1, tX1 - U, tb2 + 0.6, tZ1 + 0.6, HR_DARK)

    # THICK BARE FOREARMS -- orc green, outside torso, hide-wrapped at the wrist
    m.box3d(tX0 - 2 * U, tY0 + U, tZ0 + 0.5, tX0, tY0 + 3 * U, tZ1 - 0.5, HR_SKIN)
    m.box3d(tX1, tY0 + U, tZ0 + 0.5, tX1 + 2 * U, tY0 + 3 * U, tZ1 - 0.5, HR_SKIN)
    m.box3d(tX0 - 2 * U, tY0 + U, tZ0 + 0.5, tX0, tY0 + 1.5 * U, tZ1 - 0.5, HR_FUR, 0.75)
    m.box3d(tX1, tY0 + U, tZ0 + 0.5, tX1 + 2 * U, tY0 + 1.5 * U, tZ1 - 0.5, HR_FUR, 0.75)

    # RAM-SKULL MASK -- bone-white, worn over the upper face
    m.box3d(-2 * U, hY0, tZ0, 2 * U, hY1, tZ1, HR_BONE)
    m.box3d(-2 * U, hY0, tZ0, 2 * U, hY1, tZ1, HR_BONE)   # solid mask face
    # deep eye socket recesses (dark cavity, spirit glow at the back)
    m.box3d(-5.8, hY0 + U * 0.4, tZ1 - 0.1, -1.5, hY0 + U, tZ1 + 2.2, 0x1A1008)
    m.box3d(1.5, hY0 + U * 0.4, tZ1 - 0.1, 5.8, hY0 + U, tZ1 + 2.2, 0x1A1008)
    # spirit-light blazing at the back of the sockets
    sGlow = 1.2 + 0.6 * math.sin(tickF * 0.18)
    m.cube3(-4.0, hY0 + U * 0.7, tZ1 + 1.8, 1.3, HR_GLOW, sGlow)
    m.cube3(4.0, hY0 + U * 0.7, tZ1 + 1.8, 1.3, HR_GLOW, sGlow)
    # nasal cavity slot
    m.box3d(-0.8, hY0 + U * 0.3, tZ1 + 0.2, 0.8, hY0 + U, tZ1 + 1.5, 0x1A1008)

    # CURLED RAM HORNS -- double-stroked, sweeping down and inward (3 segments)
    for sx in (-1, 1):
        m.quad((sx * 6, hY1, 0), (sx * 7, hY1, -1),
               (sx * 9, hY0 + U * 0.5, -1), (sx * 8, hY0 + U * 0.5, 0), HR_BONE, 0.85)
        m.quad((sx * 9, hY0 + U * 0.5, -1), (sx * 8, hY0 + U * 0.5, 0),
               (sx * 7, hY0 - U, 0), (sx * 8, hY0 - U, -1), HR_BONE, 0.75)
        m.quad((sx * 7, hY0 - U, 0), (sx * 8, hY0 - U, -1),
               (sx * 5, hY0 - 1.8 * U, -0.5), (sx * 4, hY0 - 1.8 * U, 0), HR_BONE, 0.65)
    # Horn rim-light accent nodes
    m.cube3(-9, hY0 + U * 0.5, -0.5, 0.8, HR_ACCENT, 0.80)
    m.cube3(9, hY0 + U * 0.5, -0.5, 0.8, HR_ACCENT, 0.80)

    # ORC JAW + TUSKS -- visible below the mask's snout
    m.box3d(-2 * U, hY0 - U, tZ0, 2 * U, hY0, tZ1, HR_SKIN, 0.90)
    m.box3d(-U, hY0 - U, tZ1 + 0.2, U, hY0, tZ1 + 0.9, 0x1A1008)   # open mouth cavity
    m.cube3(-5.5, hY0 - U * 0.5, tZ1 + 0.5, 0.8, HR_TUSK, 0.95)    # left tusk
    m.cube3(5.5, hY0 - U * 0.5, tZ1 + 0.5, 0.8, HR_TUSK, 0.95)     # right tusk

    # TOTEM STAFF -- carved wood haft, skull-and-feather crown
    stX, stZ, stBY = 14.0, 1.5, 0.5
    stTY = stBY + 17 * U
    stGripY = tY0 + 1.5 * U
    m.push()
    m.translate(stX, stGripY, stZ)
    m.rotate(wepAng, 1, 0, 0)
    m.translate(-stX, -stGripY, -stZ)
    m.box3d(stX - 0.7, stBY, stZ - 0.4, stX + 0.3, stTY, stZ + 0.4, 0x6A4020, 0.85)
    m.box3d(stX - 0.4, stBY, stZ - 0.2, stX + 0.1, stTY, stZ + 0.2, 0x8A5828, 0.55)
    # grip wrap at hand height
    m.box3d(stX - 1.1, tY0 + U, stZ - 0.8, stX + 0.6, tY0 + 2 * U, stZ + 0.8, 0x3A2010)
    # skull-and-feather crown at the staff head
    skY = stTY - U
    m.box3d(stX - 3, skY - U, stZ - 1.5, stX + 2, skY + U, stZ + 1.5, HR_BONE)  # skull box
    m.cube3(stX - 2, skY, stZ + 1.2, 0.9, HR_GLOW, 1.20)   # left eye socket glow
    m.cube3(stX + 1, skY, stZ + 1.2, 0.9, HR_GLOW, 1.20)   # right eye socket glow
    # spirit-glow halo around the skull
    m.ring3d(stX - 0.5, skY, 0, 4.5, 1.8, HR_GLOW, 0.55)
    # two feathers trailing behind the skull
    m.tri((stX - 3, skY, stZ), (stX - 7, skY + 4, stZ - 1), (stX - 3, skY - U, stZ),
          0xE8E8E8, 0.85)
    m.tri((stX - 3, skY, stZ), (stX - 5, skY + 3, stZ + 1), (stX - 3, skY - U, stZ),
          0xE8E8E8, 0.70)
    # orbiting spirit wisps around the staff head (2 positions, tick-alternated)
    orb = 3.0 if (tick & 1) else -3.0
    m.cube3(stX - 0.5 + orb, skY + orb * 0.5, 0, 0.7, HR_GLOW, 0.80)
    m.cube3(stX - 0.5 - orb, skY - orb * 0.5, 0, 0.7, HR_GLOW, 0.55)
    m.pop()   # end staff rotation

    m.pop()   # end body bob

    # -- AURA -- VOODOO DRUMS / SHAMAN THUNDERSTORM -------------------------
    rY = 0.4

    # EARTH TREMOR GROUND CRACKS -- 3 hlines at ground level, orange crack veins
    m.line3d((-7 * U, rY, 0), (-2 * U, rY, 0), 0x6A3010, 0.65, px=2.5)
    m.line3d((-1 * U, rY, 0), (1 * U, rY, 0), HR_ACCENT, 0.80, px=2.5)   # hot gap
    m.line3d((2 * U, rY, 0), (7 * U, rY, 0), 0x6A3010, 0.65, px=2.5)
    # offshoots
    m.line3d((-4 * U, rY, 0), (-5 * U, rY, -2 * U), HR_ACCENT, 0.45, px=2.5)
    m.line3d((4 * U, rY, 0), (5 * U, rY, 2 * U), HR_ACCENT, 0.45, px=2.5)

    # VOODOO SIGIL -- large bone-glyph circle + cross burned into the earth
    m.ring3d(0, rY, 0, 3.2 * U, 1.2, HR_BONE, 0.40)   # sigil circle
    m.line3d((-3.2 * U, rY, 0), (3.2 * U, rY, 0), HR_BONE, 0.30, px=1.0)   # H arm
    m.line3d((0, rY, -3.2 * U), (0, rY, 3.2 * U), HR_BONE, 0.30, px=1.0)   # V arm

    # DRUM-BEAT PULSE RINGS -- spirit rings that throb on a 4/8-tick beat.
    # They expand outward on even beats and contract on odd beats.
    beat4, beat8 = tick % 8, tick % 16
    beatEx0 = (beat4 if beat4 < 4 else 8 - beat4) * 0.25
    beatEx1 = (beat8 if beat8 < 8 else 16 - beat8) * 0.18
    ph0 = float(tick % 28)
    ex0 = (ph0 if ph0 < 14 else 28 - ph0) * 0.12
    ph1 = float(tick % 36)
    ex1 = (ph1 if ph1 < 18 else 36 - ph1) * 0.10
    m.ring3d(0, rY, 0, 5 * U + beatEx0 * U, 2.8, HR_GLOW, 0.70)        # inner pulse
    m.ring3d(0, rY, 0, 7 * U + ex0 + beatEx1 * U, 3.2, HR_GLOW, 0.50)  # mid
    m.ring3d(0, rY, 0, 9 * U + ex1, 2.5, HR_ACCENT, 0.30)              # outer amber ghost

    # SPIRIT SKULL ICONS at 4 cardinal positions at mid-ring
    skR = 7 * U
    for i in range(4):
        if not (tick & (1 << i)):
            continue    # each flickers independently
        sx, sz = math.cos(SKA[i]) * skR, math.sin(SKA[i]) * skR
        m.cube3(sx, rY + 0.6, sz, 1.5, HR_BONE, 0.85)   # skull body
        m.cube3(sx, rY + 1.4, sz, 0.8, HR_GLOW, 1.20)   # spirit eye glow

    # RISING SMOKE / SPIRIT PLUMES -- 6 ascending particles in amber + blue
    maxSPH = 10 * U
    for i in range(6):
        phase = math.fmod(tickF * 0.7 + SPPH[i], 20.0) / 20.0
        phy = rY + phase * maxSPH
        pdrift = math.sin(tickF * 0.5 + SPPH[i]) * 1.5
        px_, pz = SPX[i] * U * 0.45 + pdrift, SPZ[i] * U * 0.45
        pcol = HR_ACCENT if i % 3 == 0 else HR_GLOW
        palpha = (1.0 - phase * 0.80) * 0.65
        # ascending particle (gets smaller and dimmer as it rises)
        psz = 1.2 * (1.0 - phase * 0.6)
        m.cube3(px_, phy, pz, psz, pcol, palpha * 1.30)
        # trail below
        m.line3d((px_, phy, pz), (px_, phy - 2 * U, pz),
                 pcol, palpha * 0.35, px=1.0, col1=pcol, mul1=0.02)

    # THUNDER LIGHTNING -- 3 bolts from above, appear on even ticks
    if not (tick & 1):      # fast flicker (even ticks only)
        for i in range(3):
            col = 0xFFFFFF if i == 0 else HR_GLOW
            bTop, bBot = 16 * U, 7 * U
            m.line3d((TBX[i] * U, rY + bTop, 0),
                     (TBX[i] * U + i * U * 0.3, rY + bBot, 0),
                     col, 0.90, px=2.0, col1=col, mul1=0.20)

    return m.build(**bake)
