"""Radiant Hero "Sun-King" -- Maya Solar Warlord (RACE_RADIANT).

Port of src/gfx/models3d/radiant_hero.cpp, C++ numbers verbatim. See
dire_hero.py for the substitution table; this one adds GL_TRIANGLES (the
feathered headdress) via m.tri().
"""

import math

from claude_studio.craftwar_gl import U, GLModel

RA_PLATE = 0x4A5870
RA_DARK = 0x202838
RA_JADE = 0x2E9E90
RA_GLOW = 0xFFD840
RA_GOLD = 0xD4A828
RA_SKIN = 0xC09050

RAY_ANG = (0, 0.7854, 1.5708, 2.3562, 3.1416, 3.9270, 4.7124, 5.4978)


def build(tickF=0.0, anim=0, name="RADIANT_hero", **bake):
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
    m.translate(0, bodyBob, 0)                     # body bob
    if anim == 2:
        m.rotate(math.sin(atkP) * 10.0, 0, 0, 1)   # attack: body lean

    # bw=6, bh=5 -- heavy footprint, same as Alliance/AI-Borg
    lY0, lY1 = 0, 6 * U
    tX0, tX1 = -9, 9
    tY0, tY1 = 6 * U, 11 * U
    tZ0, tZ1 = -4.5, 4.5
    hY0, hY1 = tY1, tY1 + 2 * U

    # LEGS -- heavy armored stance
    m.box3d(-6, lY0, -3, 0, lY1, 3, RA_DARK)
    m.box3d(0, lY0, -3, 6, lY1, 3, RA_DARK)
    m.box3d(-5.5, lY1 - 1.0, -2.5, -0.5, lY1 + 0.8, 2.5, RA_PLATE)
    m.box3d(0.5, lY1 - 1.0, -2.5, 5.5, lY1 + 0.8, 2.5, RA_PLATE)
    if tick & 1:
        m.cube3(-3, lY1, 0, 0.5, RA_GLOW, 0.30)
    if not (tick & 1):
        m.cube3(3, lY1, 0, 0.5, RA_GLOW, 0.30)

    # TORSO -- lamellar plate with step-fret seams (Maya greca ornament)
    m.box3d(tX0, tY0, tZ0, tX1, tY1, tZ1, RA_PLATE)
    # Step-fret seams: jagged alternating teeth across two horizontal lines
    seg = (tX1 - tX0) / 6.0          # 6 segments = 1 sprite unit each
    for i in range(6):
        sx0 = tX0 + i * seg
        seamY1 = tY0 + (tY1 - tY0) / 3.0 + (U if (i & 2) else 0)
        seamY2 = tY0 + 2 * (tY1 - tY0) / 3.0 + (U if (i & 2) else 0)
        m.box3d(sx0, seamY1, tZ1, sx0 + seg, seamY1 + 0.5, tZ1 + 0.5, RA_DARK)
        m.box3d(sx0, seamY2, tZ1, sx0 + seg, seamY2 + 0.5, tZ1 + 0.5, RA_DARK)

    # STEPPED-PYRAMID PAULDRONS -- 2 tiers per shoulder
    # Outer (wide, lower): extends 2U beyond torso at shoulder level
    m.box3d(tX0 - 6, tY1 - 2 * U, tZ0, tX0, tY1 - U, tZ1, RA_DARK, 0.95)
    m.box3d(tX1, tY1 - 2 * U, tZ0, tX1 + 6, tY1 - U, tZ1, RA_DARK, 0.95)
    # Inner (narrow, upper): 1U wide, sits above outer step
    m.box3d(tX0 - 3, tY1 - U, tZ0, tX0, tY1, tZ1, RA_DARK, 0.95)
    m.box3d(tX1, tY1 - U, tZ0, tX1 + 3, tY1, tZ1, RA_DARK, 0.95)
    # Gold accent rims on each tier
    m.box3d(tX0 - 7, tY1 - 2 * U - 0.5, tZ0, tX0 - 5.4, tY1 - U + 0.5, tZ1, RA_GOLD, 0.70)
    m.box3d(tX1 + 5.4, tY1 - 2 * U - 0.5, tZ0, tX1 + 7, tY1 - U + 0.5, tZ1, RA_GOLD, 0.70)
    m.box3d(tX0 - 3.8, tY1 - U - 0.4, tZ0, tX0 - 2.5, tY1 + 0.4, tZ1, RA_JADE, 0.70)
    m.box3d(tX1 + 2.5, tY1 - U - 0.4, tZ0, tX1 + 3.8, tY1 + 0.4, tZ1, RA_JADE, 0.70)

    # SUN-DISC BREASTPLATE -- k'in glyph: circle + 8 rays (4 cardinal + 4 diagonal)
    ecx, ecy, ecz = 0, tY0 + (tY1 - tY0) * 0.4, tZ1
    m.cube3(ecx, ecy, ecz + 1.4, 2.2, RA_GLOW, 1.25)      # solar disc core
    # cardinal rays (H + V)
    m.box3d(-6.0, ecy - 0.5, ecz, 6.0, ecy + 0.5, ecz + 0.8, RA_GLOW, 0.75)
    m.box3d(-0.5, ecy - 6.0, ecz, 0.5, ecy + 6.0, ecz + 0.8, RA_GLOW, 0.75)
    # diagonal rays (4 short angled slabs)
    dr = 4.0
    for i in range(4):
        ang = 0.7854 + i * 1.5708            # 45, 135, 225, 315 deg
        dx, dy = math.cos(ang) * dr, math.sin(ang) * dr
        m.box3d(dx - 0.5, ecy + dy - 0.5, ecz,
                dx + 0.5, ecy + dy + 0.5, ecz + 0.7, RA_GLOW, 0.60)
    # solar pulse
    sPulse = 1.1 + 0.55 * math.sin(tickF * 0.22)
    m.cube3(ecx, ecy, ecz + 2.0, 1.5, RA_GLOW, sPulse)

    # JADE SASH -- ceremonial belt strip with dangling celt pendants
    sashY = tY0 + 0.5
    m.box3d(tX0 + U, sashY, tZ1, tX1 - U, sashY + U, tZ1 + 0.8, RA_JADE, 0.80)
    # 3 hanging jade celts below sash
    celtSwing = math.sin(tickF * 0.30) * 0.8
    m.cube3(-5.0, sashY - 1.5 + celtSwing * 0.5, tZ1 + 0.4, 0.7, RA_JADE, 0.90)
    m.cube3(0.0, sashY - 2.0 + celtSwing, tZ1 + 0.4, 0.7, RA_JADE, 0.75)
    m.cube3(5.0, sashY - 1.5 - celtSwing * 0.5, tZ1 + 0.4, 0.7, RA_JADE, 0.90)

    # HEAD -- real human face with squared eyes + jade nose ornament
    m.box3d(-2 * U, hY0, tZ0, 2 * U, hY1, tZ1, RA_SKIN)
    m.box3d(-2 * U, hY0, tZ1 - 0.2, 2 * U, hY0 + 0.4, tZ1 + 0.4, RA_DARK)  # jawline
    # squared eyes (Maya portrait convention -- not round)
    m.box3d(-5.5, hY0 + U * 0.4, tZ1, -2.0, hY0 + U, tZ1 + 1.2, 0x201810)
    m.box3d(2.0, hY0 + U * 0.4, tZ1, 5.5, hY0 + U, tZ1 + 1.2, 0x201810)
    # jade nose ornament (royal nose-bead)
    m.cube3(0, hY0 + U * 0.55, tZ1 + 1.4, 0.8, RA_JADE, 1.00)

    # GOLD DIADEM BAND + jade studs
    m.box3d(-2 * U - U, hY1 - 0.6, tZ0, 2 * U + U, hY1, tZ1, RA_GOLD, 0.80)
    m.cube3(-(2 * U + U), hY1 - 0.4, 0, 0.9, RA_JADE, 0.85)   # left stud
    m.cube3((2 * U + U), hY1 - 0.4, 0, 0.9, RA_JADE, 0.85)    # right stud

    # FEATHERED HEADDRESS -- 3 plumes: outer jade + tall center gold
    # left outer jade plume
    m.tri((-2 * U, hY1, 0), (-4 * U, hY1 + 6 * U, 0), (-2 * U, hY1, 1.5), RA_JADE, 0.80)
    m.tri((-2 * U, hY1, 0), (-4 * U, hY1 + 6 * U, 0), (-2 * U, hY1, -1.5), RA_JADE, 0.60)
    # center tall gold plume
    m.tri((-U, hY1, 0), (0, hY1 + 8 * U, 0), (U, hY1, 0), RA_GLOW, 1.00)
    m.tri((-U, hY1, 1.5), (0, hY1 + 8 * U, 0), (-U, hY1, -1.5), RA_GLOW, 0.75)
    # right outer jade plume
    m.tri((2 * U, hY1, 0), (4 * U, hY1 + 6 * U, 0), (2 * U, hY1, 1.5), RA_JADE, 0.80)
    m.tri((2 * U, hY1, 0), (4 * U, hY1 + 6 * U, 0), (2 * U, hY1, -1.5), RA_JADE, 0.60)
    # feather-tip glints
    m.cube3(-4 * U, hY1 + 6 * U, 0, 1.0, RA_JADE, 1.10)
    m.cube3(0, hY1 + 8 * U, 0, 1.2, RA_GLOW, 1.40)
    m.cube3(4 * U, hY1 + 6 * U, 0, 1.0, RA_JADE, 1.10)

    m.pop()   # end body bob

    # -- AURA -- SOLAR RADIANCE BURST ---------------------------------------
    rY = 0.4

    # GROUND SUN-FIRE DISC -- expanding circle that resets each 16 ticks
    # Two concentric fills: inner warm gold + outer white-gold rim
    discPhase = float(tick % 16) / 16.0
    discR = discPhase * 5 * U
    m.ring3d(0, rY, 0, discR, 1.5, RA_GLOW, 0.75 * (1.0 - discPhase * 0.5))
    m.ring3d(0, rY, 0, discR + 1.5, 1.0, 0xFFFFC0, 0.55 * (1.0 - discPhase))

    # SOLAR RINGS -- radial gradient: inner bright -> outer ghostly
    ph0 = float(tick % 32)
    ex0 = (ph0 if ph0 < 16 else 32 - ph0) * 0.12
    ph1 = float(tick % 24)
    ex1 = (ph1 if ph1 < 12 else 24 - ph1) * 0.15
    ph2 = float(tick % 16)
    ex2 = (ph2 if ph2 < 8 else 16 - ph2) * 0.18
    Rinner = 4 * U + ex2        # inner solar pulse (fast independent breath)
    R0, R1 = 7 * U + ex0, 9 * U + ex1
    m.ring3d(0, rY, 0, Rinner, 2.2, RA_GLOW, 0.90)   # inner pulse
    m.ring3d(0, rY, 0, R0, 3.5, RA_GLOW, 0.65)       # mid
    m.ring3d(0, rY, 0, R1, 2.8, RA_JADE, 0.38)       # outer jade ghost

    # 8 PERMANENT RADIANT RAYS -- all 8 compass positions
    # Each ray: inner segment (Rinner -> R1) always on + pulsing tip beyond R1
    tipPulse = 1.0 + float(tick % 2) * 0.6   # tip alternates each tick (spec)
    for r in range(8):
        ca, sa = math.cos(RAY_ANG[r]), math.sin(RAY_ANG[r])
        isDiag = r & 1
        col = RA_JADE if isDiag else RA_GLOW
        brightness = 0.60 if isDiag else 0.90
        # inner segment: Rinner -> R1 (always present, bright)
        m.line3d((ca * Rinner, rY, sa * Rinner), (ca * R1, rY, sa * R1),
                 col, brightness, px=2.5, col1=col, mul1=brightness * 0.3)
        # outer pulsing tip extension beyond R1
        tipR = R1 + 2.5 * U * tipPulse
        m.line3d((ca * R1, rY, sa * R1), (ca * tipR, rY, sa * tipR),
                 col, brightness * 0.5 * tipPulse, px=2.5, col1=col, mul1=0.02)

    # RAY TIP SPARKS -- bright flares at the outermost tip (cardinal, alternating)
    for r in range(0, 8, 2):
        ca, sa = math.cos(RAY_ANG[r]), math.sin(RAY_ANG[r])
        tipR = R1 + 2.0 * U * tipPulse
        if tick & (1 << (r // 2)):
            m.cube3(ca * tipR, rY + 0.6, sa * tipR, 1.3, 0xFFFFC0, 1.50)

    # SOLAR WIND PARTICLES -- 8 motes spiraling outward, fading at the outer ring
    for i in range(8):
        ang = tickF * 0.10 + i * (3.14159 * 2.0 / 8.0)
        spiralR = math.fmod(tickF * 0.5 + i * 1.2, R1 / U) * U   # 0 -> R1, repeats
        mx, mz = math.cos(ang) * spiralR, math.sin(ang) * spiralR
        fade = 1.0 - spiralR / R1
        m.cube3(mx, rY + 0.4, mz, 1.1, RA_GLOW, fade * 1.20 + 0.10)

    return m.build(**bake)
