"""Dire Hero "Ah Puch" -- Maya Lord of Death (RACE_DIRE).

Port of src/gfx/models3d/dire_hero.cpp. The C++ numbers are kept exactly as
written; everything structural is a mechanical substitution:

    glPushMatrix/glPopMatrix   -> m.push() / m.pop()
    glTranslatef / glRotatef   -> m.translate() / m.rotate()
    box3d / cube3 / ring3d     -> m.box3d() / m.cube3() / m.ring3d()
    glBegin(GL_LINES) pairs    -> m.line3d(), carrying both vertex colours
    glBegin(GL_QUADS) runs     -> m.quad()

Two places where GL has no raytracer equivalent, both handled in craftwar_gl:
glLineWidth is in pixels (converted through PX), and GL_LINES have no
thickness (drawn as thin bars).
"""

import math

from claude_studio.craftwar_gl import U, GLModel

DI_FLESH = 0x1A1020   # fel-dark corrupted flesh
DI_DARK = 0x0E0810    # deep shadow
DI_BONE = 0xD8CCA4    # literal bone ivory
DI_GLOW = 0x80FF30    # fel-green ember
DI_ACCENT = 0x305858  # teal shoulder trim
DI_HORN = 0x401010    # dark red horn
# Fire gradient palette (aura only)
DI_HOT = 0xEEFF90     # near-white hot flame core (base)
DI_MID = 0xA8FF38     # mid-flame bright fel-green
DI_DIM = 0x1E4008     # cooled outer tongue (tip)
DI_CRUPT = 0x501870   # inner corruption ring purple

FX = (0, 2.5, -2.0, 4.0, -3.5, 1.5, -1.0, 3.0, -4.0, 0.5)
FZ = (0, -2.0, 3.0, -1.5, 2.5, 4.0, -3.0, 0.5, -1.0, -4.0)
FPH = (0, 3.5, 7.2, 11.0, 15.3, 1.8, 5.5, 9.0, 13.7, 17.1)


def build(tickF=0.0, anim=0, name="DIRE_hero"):
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
        m.rotate(math.sin(atkP) * 12.0, 0, 0, 1)   # attack: body lean

    # bw=4, bh=6 -- GAUNT and TALLER than the broad heroes
    lY0, lY1 = 0, 6 * U
    tX0, tX1 = -6.0, 6.0        # 4 sprite units wide = 12 world units (narrower!)
    tY0, tY1 = 6 * U, 12 * U    # 6 sprite units tall = 18 world units (taller!)
    tZ0, tZ1 = -3.0, 3.0
    hY0, hY1 = tY1, tY1 + 2 * U

    # LEGS -- gaunt SINGLE-cell width (not the 2-cell bulk of broad heroes)
    m.box3d(-4.5, lY0, -2, -1.5, lY1, 2, DI_FLESH)   # left -- 1 sprite unit wide
    m.box3d(1.5, lY0, -2, 4.5, lY1, 2, DI_FLESH)     # right
    # bony knee-knobs -- protruding bone cube
    m.cube3(-3, lY1, 0, 1.3, DI_BONE, 0.90)
    m.cube3(3, lY1, 0, 1.3, DI_BONE, 0.90)

    # TORSO -- gaunt ribcage, fel-dark flesh base
    m.box3d(tX0, tY0, tZ0, tX1, tY1, tZ1, DI_FLESH)

    # 4 BONE RIB BANDS -- bone-pale horizontal slabs through rotted flesh
    for i in range(4):
        ry = tY0 + (1 + i) * U
        m.box3d(tX0 + U, ry, tZ1, tX1 - U, ry + 0.5, tZ1 + 0.7, DI_BONE, 0.80)

    # CINCHED STARVED WAIST -- narrower at the very bottom
    m.box3d(tX0 + U, tY0, tZ0, tX1 - U, tY0 + U, tZ1, DI_DARK, 0.90)

    # SHOULDER PLATES WITH TEAL ACCENT TRIM
    m.box3d(tX0 - 2 * U, tY1 - 2 * U, tZ0, tX0, tY1, tZ1, DI_DARK, 0.95)
    m.box3d(tX1, tY1 - 2 * U, tZ0, tX1 + 2 * U, tY1, tZ1, DI_DARK, 0.95)
    m.box3d(tX0 - 2 * U - 0.5, tY1 - 2 * U - 0.4, tZ0,
            tX0 - 2 * U + 0.5, tY1 + 0.4, tZ1, DI_ACCENT, 0.70)
    m.box3d(tX1 + 2 * U - 0.5, tY1 - 2 * U - 0.4, tZ0,
            tX1 + 2 * U + 0.5, tY1 + 0.4, tZ1, DI_ACCENT, 0.70)

    # HOLLOW FEL-CORE -- glowing orb where the heart should be (between ribs)
    coreY, coreX = tY0 + 2 * U, 0.0
    cPulse = 1.15 + 0.70 * math.sin(tickF * 0.25)
    cSize = 1.6 + 0.40 * math.sin(tickF * 0.25)
    m.cube3(coreX, coreY, tZ1 + 1.0, cSize, DI_GLOW, cPulse)
    # outer dim halo
    m.ring3d(coreX, coreY, 0, 3 * U, 1.0, DI_GLOW, 0.20)

    # BONE RATTLE ON CORD -- hangs from torso bottom, swings with walk
    rattleSwing = math.sin(tickF * (2.8 if anim == 1 else 0.30)) * (4.0 if anim == 1 else 2.5)
    cordX, cordTopY, cordBotY = 0.0, tY0, tY0 - U
    m.box3d(cordX - 0.2, cordBotY, tZ1, cordX + 0.2, cordTopY, tZ1 + 0.3, DI_BONE, 0.60)
    # three-bead bone rattle (horizontal strip)
    rattleX, rattleY = rattleSwing, cordBotY - 0.5
    m.box3d(rattleX - U * 1.5, rattleY, tZ1 + 0.1,
            rattleX + U * 1.5, rattleY + U, tZ1 + 0.8, DI_BONE, 0.75)
    # center bead catches fel-light
    m.cube3(rattleX, rattleY + U * 0.5, tZ1 + 0.6, 0.7, DI_GLOW, 0.90)

    # HALF-SKULL HEAD -- bone-white, FULL TORSO WIDTH (flush to shoulders)
    m.box3d(tX0, hY0, tZ0, tX1, hY1, tZ1, DI_BONE)
    # brow-ridge rim light at top
    m.box3d(tX0, hY1 - 0.4, tZ0, tX1, hY1, tZ1 + 0.2, DI_ACCENT, 0.60)
    # deep hollow eye sockets: 2-cell dark cavity with ember at the bottom
    eT, eB = hY0 + U * 0.25, hY0 + U * 1.0
    m.box3d(tX0, eT, tZ1 - 0.2, tX0 + U, eB, tZ1 + 2.5, DI_DARK)    # left socket
    m.box3d(tX1 - U, eT, tZ1 - 0.2, tX1, eB, tZ1 + 2.5, DI_DARK)    # right socket
    # ember glowing at the BOTTOM of each socket (light-from-inside read)
    eFlicker = 1.3 + 0.6 * math.sin(tickF * 0.35)
    m.cube3(tX0 + U * 0.5, eT + U * 0.5, tZ1 + 2.0, 1.1, DI_GLOW, eFlicker)
    m.cube3(tX1 - U * 0.5, eT + U * 0.5, tZ1 + 2.0, 1.1, DI_GLOW, eFlicker)
    # nasal cavity -- no nose bridge, literal skull
    m.box3d(-0.8, eT + 0.2, tZ1 + 0.2, 0.8, eB - 0.5, tZ1 + 1.8, DI_DARK)

    # JAW -- set below the cranium with a gap (hinge read), fangs below
    jawY = hY0 - U * 0.5
    m.box3d(tX0 + U, jawY - U, tZ0, tX1 - U, jawY, tZ1, DI_BONE, 0.80)  # jaw slab
    # two fangs below the jaw
    m.cube3(tX0 + 1.5 * U, jawY - U * 1.2, tZ1 + 0.3, 0.9, DI_BONE, 0.85)
    m.cube3(tX1 - 1.5 * U, jawY - U * 1.2, tZ1 + 0.3, 0.9, DI_BONE, 0.85)

    # CURVED HORNS -- dark red, two segments sweeping up and slightly outward.
    # The C++ emits these as a GL_QUADS run whose vertex order (lo-z, hi-z,
    # lo-z, hi-z) draws a self-crossing bowtie; the pairs are reordered here
    # into the flat ribbon they were plainly meant to be.
    for sx in (-1, 1):
        x = tX0 if sx < 0 else tX1
        mid = x + sx * U
        tip = x - sx * U * 0.5
        m.quad((x, hY1, 0), (x, hY1, 1),
               (mid, hY1 + U * 1.5, 1.5), (mid, hY1 + U * 1.5, 0.5),
               DI_HORN, 0.85)
        m.quad((mid, hY1 + U * 1.5, 0.5), (mid, hY1 + U * 1.5, 1.5),
               (tip, hY1 + 3 * U, 0.5), (tip, hY1 + 3 * U, -0.5),
               DI_HORN, 0.70)
    # horn-tip sheen
    m.cube3(tX0 + U * 0.5, hY1 + 3 * U, 0, 0.7, 0x5A4A50, 0.80)
    m.cube3(tX1 - U * 0.5, hY1 + 3 * U, 0, 0.7, 0x5A4A50, 0.80)

    m.pop()   # end body bob

    # -- AURA -- FEL-FIRE COLUMN / GROUND FISSURE ---------------------------
    rY = 0.4

    # GROUND FISSURE -- cracked earth with fel light seeping through gaps
    # main horizontal crack -- bright gap in center, dimmer at edges
    m.line3d((-6 * U, rY, 0), (-2 * U, rY, 0), DI_GLOW, 0.65, px=2.5)
    m.line3d((-1 * U, rY, 0), (1 * U, rY, 0), DI_HOT, 0.95, px=2.5)
    m.line3d((2 * U, rY, 0), (6 * U, rY, 0), DI_GLOW, 0.65, px=2.5)
    # perpendicular crack (shorter)
    m.line3d((0, rY, -5 * U), (0, rY, -1.5 * U), DI_GLOW, 0.50, px=2.5)
    m.line3d((0, rY, -0.5 * U), (0, rY, 0.5 * U), DI_HOT, 0.80, px=2.5)
    m.line3d((0, rY, 1.5 * U), (0, rY, 5 * U), DI_GLOW, 0.50, px=2.5)
    # diagonal crack veins
    m.line3d((-3 * U, rY, 2 * U), (-U, rY, 4 * U), DI_MID, 0.35, px=2.5)
    m.line3d((3 * U, rY, -2 * U), (U, rY, -4 * U), DI_MID, 0.35, px=2.5)

    # INNER CORRUPTION RINGS -- 2 tight purple rings between body and outer
    ph_c0 = float(tick % 22)
    cx0 = (ph_c0 if ph_c0 < 11 else 22 - ph_c0) * 0.14
    ph_c1 = float(tick % 18)
    cx1 = (ph_c1 if ph_c1 < 9 else 18 - ph_c1) * 0.16
    m.ring3d(0, rY, 0, 4 * U + cx0, 2.2, DI_CRUPT, 0.80)
    m.ring3d(0, rY, 0, 6 * U + cx1, 1.8, DI_CRUPT, 0.50)

    # OUTER FEL RINGS -- radial gradient: inner bright -> outer ghostly
    ph0 = float(tick % 34)
    ex0 = (ph0 if ph0 < 17 else 34 - ph0) * 0.12
    ph1 = float(tick % 24)
    ex1 = (ph1 if ph1 < 12 else 24 - ph1) * 0.15
    m.ring3d(0, rY, 0, 8 * U + ex0, 3.2, DI_GLOW, 0.65)
    m.ring3d(0, rY, 0, 10 * U + ex1, 2.6, DI_GLOW, 0.28)

    # 6 DARK-MATTER CHAOS MOTES -- tight fast orbit at inner corruption ring
    orbitR = 4.5 * U
    for i in range(6):
        ang = tickF * 0.22 + i * (3.14159 * 2.0 / 6.0)
        mx, mz = math.cos(ang) * orbitR, math.sin(ang) * orbitR
        col = DI_HOT if i % 3 == 0 else DI_GLOW
        br = 1.35 if i % 3 == 0 else 0.85
        m.cube3(mx, rY + 0.4, mz, 1.0, col, br)

    # 4 OUTER SHADOW TENDRILS -- slow orbit at outer ring, trailing upward
    orbitR = 10 * U
    for i in range(4):
        ang = tickF * 0.06 + i * (3.14159 * 2.0 / 4.0)
        tx, tz = math.cos(ang) * orbitR, math.sin(ang) * orbitR
        m.line3d((tx, rY, tz), (tx * 0.7, rY + 2 * U, tz * 0.7),
                 DI_GLOW, 0.45, px=2.0, col1=DI_CRUPT, mul1=0.08)
        m.cube3(tx, rY + 0.2, tz, 1.3, DI_CRUPT, 0.70)

    # DENSE FEL-FIRE COLUMN -- 10 flame tongues at scattered hero-center
    # offsets. Each has its own tick phase so they never sync.
    # Per-tongue gradient: HOT at base -> MID fel-green mid -> DIM at tip.
    maxFH = 9 * U
    for i in range(10):
        phase = math.fmod(tickF * 0.8 + FPH[i], 20.0) / 20.0   # 0..1 rise cycle
        fh = phase * maxFH                                     # tongue height
        fw = 0.4 + 0.2 * math.sin(tickF * 1.4 + i * 0.7)       # width flicker
        fx, fz = FX[i] * U * 0.42, FZ[i] * U * 0.42

        # OUTER tongue -- full height, dim outer edge
        m.line3d((fx + fw, rY, fz + fw),
                 (fx + fw * 0.5, rY + fh, fz + fw * 0.5),
                 DI_GLOW, 0.45, px=2.0, col1=DI_DIM, mul1=0.05)
        # MID tongue -- 3/4 height, fel-green gradient
        m.line3d((fx, rY, fz), (fx, rY + fh * 0.75, fz),
                 DI_MID, 0.75, px=3.0, col1=DI_GLOW, mul1=0.08)
        # CORE tongue -- 1/2 height, white-hot base -> fel-green midpoint
        m.line3d((fx - fw, rY, fz - fw),
                 (fx - fw * 0.3, rY + fh * 0.50, fz - fw * 0.3),
                 DI_HOT, 1.00, px=4.0, col1=DI_GLOW, mul1=0.20)
        # bright base ember at foot of each tongue
        m.cube3(fx, rY + 0.2, fz, 0.9, DI_HOT,
                1.10 + 0.30 * math.sin(tickF * 2.0 + i))

    return m.build()
