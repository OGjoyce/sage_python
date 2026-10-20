"""AI-Borg 3D unit models.

Port of drawAiborgUnit3D in src/gfx/models3d/aiborg_units.cpp, C++ numbers
verbatim. Buildings from the same file are in aiborg_bldg.py.

Only the Worker ("Drone") exists; units 1-6 (Sentrybot, Railgunner,
Juggernaut, Synthmind, Nanite Medic, Railcannon) return false in the C++ and
return None here, which is what "Coming Soon" means in the viewer.
"""

import math

from claude_studio.craftwar_gl import U, GLModel  # noqa: F401  (U kept for parity)

AB_TORSO = 0x16161A  # RACE_INFO.color -- the true body tint
AB_HEAD = 0x2A2A30   # raceStyle().skin -- slightly lighter than torso
AB_GOLD = 0xF0C040   # raceStyle().eye == RACE_INFO.glowColor -- the ONE accent
AB_FOOT = 0x505866   # metallic foot-plate color (drawRaceBody form 6)
AB_RED = 0xFF4444    # fault-indicator status light

NAMES = ("Drone", "Sentrybot", "Railgunner", "Juggernaut", "Synthmind",
         "NaniteMedic", "Railcannon")


def _drone(m, tickF, anim):
    """Blocky bipedal chassis (NOT a quadruped -- that was an earlier mistake).

    Body: square torso with 2 panel seams, a pulsing gold chest-reactor disc,
    a gold waist light-strip, gold shoulder-joint lights, metallic foot plates.
    Head: smaller square block, lighter tone, with a gold visor band (an
    animated scan-line sweeps across it), a short antenna with a gold tip, and
    a gold+red status-light pair. Worker prop: a jointed robotic mining arm.
    """
    idleP = tickF * 1.0
    reactorPulse = 0.85 + 0.5 * math.sin(tickF * 0.28)   # matches 2D pulseGlow
    if anim == 1:
        hover = abs(math.sin(tickF * 3.0)) * 1.0
    else:
        hover = math.sin(idleP) * 0.4 + 0.4

    m.push()
    m.translate(0, hover, 0)

    br, hr = 7.5, 4.5      # torso / head half-sizes (world units)

    # Feet -- metallic plates attached straight to the torso base (the 2D
    # source has no separate articulated legs for this icon-style body).
    footY0, footY1 = 0.0, 4.8
    m.box3d(-br * 0.85, footY0, -2.0, -1.0, footY1, 2.0, AB_FOOT, 0.9)
    m.box3d(1.0, footY0, -2.0, br * 0.85, footY1, 2.0, AB_FOOT, 0.9)

    # Torso -- blocky square chassis.
    tX0, tX1 = -br, br
    tY0, tY1 = footY1, footY1 + br * 2
    tZ0, tZ1 = -br * 0.75, br * 0.75
    m.box3d(tX0, tY0, tZ0, tX1, tY1, tZ1, AB_TORSO)

    # Panel seams (upper/lower third).
    seam1Y = tY0 + (tY1 - tY0) / 3.0
    seam2Y = tY0 + (tY1 - tY0) * 2.0 / 3.0
    m.box3d(tX0 + 0.3, seam1Y, tZ1, tX1 - 0.3, seam1Y + 0.3, tZ1 + 0.25, AB_HEAD, 0.85)
    m.box3d(tX0 + 0.3, seam2Y, tZ1, tX1 - 0.3, seam2Y + 0.3, tZ1 + 0.25, AB_HEAD, 0.85)

    # Chest reactor core -- pulsing gold disc.
    reactorY = tY0 + (tY1 - tY0) * 0.55
    m.cube3(0, reactorY, tZ1 + 0.3, br * 0.22, AB_GOLD, reactorPulse)

    # Waist light-strip -- full-width gold bar near the torso base.
    m.box3d(tX0 + 0.2, tY0 + 0.6, tZ1 + 0.15, tX1 - 0.2, tY0 + 1.3, tZ1 + 0.4,
            AB_GOLD, 1.0)

    # Shoulder joint lights.
    m.cube3(tX0 - 0.3, tY1 - 1.2, 0, 0.45, AB_GOLD, 1.0)
    m.cube3(tX1 + 0.3, tY1 - 1.2, 0, 0.45, AB_GOLD, 1.0)

    # Head -- blocky unit, lighter tone than the torso.
    hX0, hX1 = -hr, hr
    hY0, hY1 = tY1, tY1 + hr * 2
    hZ1 = hr * 0.8
    m.box3d(hX0, hY0, -hZ1, hX1, hY1, hZ1, AB_HEAD)

    # Visor band -- horizontal gold rectangle, with an animated scan-line
    # sweep across it (2D source: scanX drifts across the visor each tick).
    visorY = hY0 + (hY1 - hY0) * 0.45
    m.box3d(hX0 + 0.3, visorY - 0.35, hZ1 + 0.15, hX1 - 0.3, visorY + 0.35, hZ1 + 0.4,
            AB_GOLD, 0.8)
    scanX = hX0 + 0.3 + math.fmod(tickF * 0.6, (hX1 - hX0 - 0.6))
    m.box3d(scanX, visorY - 0.4, hZ1 + 0.4, scanX + 0.4, visorY + 0.4, hZ1 + 0.6,
            AB_GOLD, 1.6)

    # Status lights below the visor: gold + a red fault indicator.
    m.cube3(hX0 + 0.6, visorY - 1.1, hZ1 + 0.3, 0.2, AB_GOLD, 1.0)
    m.cube3(hX1 - 0.6, visorY - 1.1, hZ1 + 0.3, 0.2, AB_RED, 0.9)

    # Antenna: short shaft + gold tip.
    m.box3d(-0.18, hY1, -0.18, 0.18, hY1 + 1.5, 0.18, AB_FOOT, 0.9)
    m.cube3(0, hY1 + 1.7, 0, 0.35, AB_GOLD, 1.0)

    # Helicopter-style spinning rotor on top of the antenna.
    rotorY = hY1 + 1.7 + 0.8
    m.push()
    m.translate(0, rotorY, 0)
    m.rotate(math.fmod(tickF * 14.0, 360.0), 0, 1, 0)
    m.box3d(-4.2, -0.15, -0.5, 4.2, 0.15, 0.5, AB_HEAD, 1.1)
    m.box3d(-0.5, -0.15, -4.2, 0.5, 0.15, 4.2, AB_HEAD, 1.1)
    m.cube3(0, 0, 0, 0.6, AB_GOLD, 1.0)
    m.pop()

    # Worker's jointed robotic mining arm: upper arm -> gold elbow servo ->
    # forearm -> pulsing gold drill head.
    armBaseY = tY1 - 1.0
    elbowX, elbowY, elbowZ = tX0 - br * 0.7, armBaseY - br * 0.4, 2.0
    tipX, tipY, tipZ = tX0 - br * 1.1, armBaseY - br * 1.1, 3.0
    m.box3d(tX0 - 0.3, armBaseY - 0.4, 1.7, elbowX + 0.3, armBaseY + 0.4, 2.3,
            AB_FOOT, 0.9)
    m.cube3(elbowX, elbowY, elbowZ, 0.5, AB_GOLD, 1.0)
    m.box3d(min(elbowX, tipX) - 0.3, min(elbowY, tipY), min(elbowZ, tipZ) - 0.3,
            max(elbowX, tipX) + 0.3, max(elbowY, tipY), max(elbowZ, tipZ) + 0.3,
            AB_FOOT, 0.9)
    m.cube3(tipX, tipY, tipZ, 0.7, AB_GOLD, reactorPulse)

    m.pop()


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the unit, as unitIdx does in the C++."""
    if idx != 0:
        return None     # units 1-6 are "Coming Soon" -- the C++ returns false
    m = GLModel(name or f"AIBORG_unit{idx}_{NAMES[idx]}")
    _drone(m, tickF, anim)
    return m.build(**bake)
