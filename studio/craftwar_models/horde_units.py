"""Horde 3D unit models.

Port of drawHordeUnit3D in src/gfx/models3d/horde_units.cpp, C++ numbers
verbatim. Buildings from the same file are in horde_bldg.py.

Units: Peon(0) Grunt(1) Headhunter(2) Tauren(3) Shaman(4) WitchDoctor(5)
       WarMachine(6)
"""

import math

from claude_studio.craftwar_gl import U, GLModel

HR_GREEN = 0x6E8A3A
HR_DARK = 0x3A4E1E
HR_BONE = 0xDCC8A0
HR_GLOW = 0xFF8040
HR_IRON = 0x5A5840
HR_RUST = 0x805030
HR_TUSK = 0xF0E0B0
HR_CLOTH = 0x806040

NAMES = ("Peon", "Grunt", "Headhunter", "Tauren", "Shaman", "WitchDoctor",
         "WarMachine")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the unit, as unitIdx does in the C++."""
    m = GLModel(name or f"HORDE_unit{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")

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
        # -- 0: PEON (Worker) ------------------------------------------------
        lY1 = 3.0 * U
        gaitL = math.sin(walkP) * 18.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-0.9, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(0.9, -lY1, 0)
        m.box3d(-2.1, 0, -1.0, -0.2, lY1, 1.0, HR_GREEN)
        m.pop()
        m.push()
        m.translate(0.9, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-0.9, -lY1, 0)
        m.box3d(0.2, 0, -1.0, 2.1, lY1, 1.0, HR_GREEN)
        m.pop()
        m.box3d(-2.5, 0, -1.4, -0.1, 0.65 * U, 1.4, HR_DARK)
        m.box3d(0.1, 0, -1.4, 2.5, 0.65 * U, 1.4, HR_DARK)
        m.box3d(-3.0, lY1, -1.5, 3.0, lY1 + 2.8 * U, 1.5, HR_GREEN)
        m.box3d(-0.5, lY1 + 0.5 * U, -1.6, 0.5, lY1 + 2.8 * U, 1.6, HR_RUST)
        m.box3d(-1.9, lY1 + 3.0 * U, -1.4, 1.9, lY1 + 4.6 * U, 1.4, HR_GREEN)
        m.box3d(-1.6, lY1 + 2.7 * U, -1.8, 1.6, lY1 + 3.3 * U, 1.8, HR_GREEN)
        m.box3d(-1.3, lY1 + 2.6 * U, -2.2, -0.5, lY1 + 2.9 * U, -1.4, HR_TUSK)
        m.box3d(0.5, lY1 + 2.6 * U, -2.2, 1.3, lY1 + 2.9 * U, -1.4, HR_TUSK)
        armSwL = math.sin(walkP) * 20.0 if anim == 1 else 0.0
        if anim == 1:
            armSwR = -math.sin(walkP) * 20.0
        elif anim == 2:
            armSwR = -40.0 + math.sin(atkP) * 50.0
        else:
            armSwR = 0.0
        m.push()
        m.translate(-3.0, lY1 + 2.0 * U, 0)
        m.rotate(armSwL, 1, 0, 0)
        m.box3d(-1.0, -1.5 * U, -0.8, 0.0, 0.0, 0.8, HR_GREEN)
        m.pop()
        m.push()
        m.translate(3.0, lY1 + 2.0 * U, 0)
        m.rotate(armSwR, 1, 0, 0)
        m.box3d(0.0, -1.5 * U, -0.8, 1.0, 0.0, 0.8, HR_GREEN)
        m.box3d(0.35, -3.8 * U, -0.25, 0.7, 0.0, 0.25, HR_BONE)
        m.box3d(-0.5, -4.2 * U, -0.5, 1.5, -3.6 * U, 0.5, HR_IRON)
        m.pop()

    elif idx == 1:
        # -- 1: GRUNT (Melee) ------------------------------------------------
        lY1 = 3.5 * U
        gaitL = math.sin(walkP) * 22.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-1.2, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(1.2, -lY1, 0)
        m.box3d(-3.0, 0, -1.5, -0.2, lY1, 1.5, HR_GREEN)
        m.pop()
        m.push()
        m.translate(1.2, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-1.2, -lY1, 0)
        m.box3d(0.2, 0, -1.5, 3.0, lY1, 1.5, HR_GREEN)
        m.pop()
        m.box3d(-3.3, 0, -1.8, 0.0, 0.9 * U, 1.8, HR_IRON)
        m.box3d(0.0, 0, -1.8, 3.3, 0.9 * U, 1.8, HR_IRON)
        m.box3d(-4.8, lY1, -2.0, 4.8, lY1 + 3.8 * U, 2.0, HR_GREEN)
        m.box3d(-4.7, lY1 + 0.5 * U, -2.2, 4.7, lY1 + 2.8 * U, 2.2, HR_IRON)
        m.box3d(-6.0, lY1 + 2.5 * U, -1.0, -4.2, lY1 + 4.2 * U, 1.0, HR_IRON)
        m.box3d(4.2, lY1 + 2.5 * U, -1.0, 6.0, lY1 + 4.2 * U, 1.0, HR_IRON)
        m.box3d(-2.5, lY1 + 3.8 * U, -2.0, 2.5, lY1 + 5.4 * U, 2.0, HR_GREEN)
        m.box3d(-2.8, lY1 + 5.0 * U, -2.2, 2.8, lY1 + 5.8 * U, 2.2, HR_IRON)
        m.box3d(-2.0, lY1 + 3.4 * U, -2.5, 2.0, lY1 + 4.0 * U, 2.5, HR_GREEN)
        m.box3d(-1.8, lY1 + 3.0 * U, -2.8, -0.6, lY1 + 3.5 * U, -1.5, HR_TUSK)
        m.box3d(0.6, lY1 + 3.0 * U, -2.8, 1.8, lY1 + 3.5 * U, -1.5, HR_TUSK)
        swL = math.sin(walkP) * 18.0 if anim == 1 else 0.0
        atkRot = math.sin(atkP) * 55.0 - 20.0 if anim == 2 else 0.0
        m.push()
        m.translate(-4.8, lY1 + 2.5 * U, 0)
        m.rotate(-swL, 1, 0, 0)
        m.box3d(-0.9, -2.2 * U, -0.9, 0.0, 0.0, 0.9, HR_GREEN)
        m.pop()
        m.push()
        m.translate(4.8, lY1 + 2.5 * U, 0)
        m.rotate(atkRot, 1, 0, 0)
        m.box3d(0.0, -2.2 * U, -0.9, 0.9, 0.0, 0.9, HR_GREEN)
        m.box3d(0.35, -4.0 * U, -0.3, 0.8, 0.0, 0.3, HR_BONE)
        m.box3d(-0.6, -4.3 * U, -1.8, 1.8, -3.7 * U, 1.8, HR_IRON)
        m.box3d(-0.6, -1.1 * U, -1.8, 1.8, -0.5 * U, 1.8, HR_IRON)
        m.pop()

    elif idx == 2:
        # -- 2: HEADHUNTER (Ranged) ------------------------------------------
        lY1 = 3.2 * U
        gaitL = math.sin(walkP) * 22.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-0.8, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(0.8, -lY1, 0)
        m.box3d(-2.1, 0, -1.0, -0.2, lY1, 1.0, HR_GREEN)
        m.pop()
        m.push()
        m.translate(0.8, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-0.8, -lY1, 0)
        m.box3d(0.2, 0, -1.0, 2.1, lY1, 1.0, HR_GREEN)
        m.pop()
        m.box3d(-2.4, 0, -1.3, 0.0, 0.65 * U, 1.3, HR_DARK)
        m.box3d(0.0, 0, -1.3, 2.4, 0.65 * U, 1.3, HR_DARK)
        m.box3d(-3.0, lY1, -1.4, 3.0, lY1 + 3.2 * U, 1.4, HR_GREEN)
        m.box3d(-3.1, lY1 + 0.7 * U, -1.5, 3.1, lY1 + 1.2 * U, 1.5, HR_BONE)
        m.box3d(-2.0, lY1 + 3.2 * U, -1.5, 2.0, lY1 + 4.8 * U, 1.5, HR_GREEN)
        m.box3d(-1.7, lY1 + 2.8 * U, -1.9, 1.7, lY1 + 3.4 * U, 1.9, HR_GREEN)
        m.box3d(-0.5, lY1 + 4.8 * U, -0.35, 0.5, lY1 + 6.3 * U, 0.35, HR_DARK)
        m.box3d(-0.3, lY1 + 4.7 * U, -0.8, 0.3, lY1 + 5.9 * U, 0.0, HR_DARK)
        m.box3d(-0.3, lY1 + 4.7 * U, 0.0, 0.3, lY1 + 5.9 * U, 0.8, HR_DARK)
        atkRot = math.sin(atkP) * 60.0 if anim == 2 else 0.0
        swL = math.sin(walkP) * 20.0 if anim == 1 else 0.0
        m.push()
        m.translate(-3.0, lY1 + 2.0 * U, 0)
        m.rotate(-swL + atkRot, 1, 0, 0)
        m.box3d(-1.0, -1.8 * U, -0.6, 0.0, 0.0, 0.6, HR_GREEN)
        m.box3d(-2.3, -0.9 * U, -1.1, 0.3, -0.4 * U, 1.1, HR_IRON)
        m.pop()
        m.push()
        m.translate(3.0, lY1 + 2.0 * U, 0)
        m.rotate(swL + atkRot, 1, 0, 0)
        m.box3d(0.0, -1.8 * U, -0.6, 1.0, 0.0, 0.6, HR_GREEN)
        m.box3d(-0.3, -0.9 * U, -1.1, 2.3, -0.4 * U, 1.1, HR_IRON)
        m.pop()

    elif idx == 3:
        # -- 3: TAUREN (Heavy -- bull centaur) -------------------------------
        pairA = abs(math.sin(walkP * 2.0)) * U * 0.7 if anim == 1 else 0.0
        pairB = abs(math.sin(walkP * 2.0 + 1.57)) * U * 0.7 if anim == 1 else 0.0
        m.box3d(-6.0, 0, -5.5, 6.0, 3.5 * U, 5.5, HR_DARK)
        m.push()
        m.translate(0, pairA, 0)
        m.box3d(-5.0, -pairA, -4.5, -2.5, 3.5 * U, -2.0, HR_GREEN)
        m.box3d(2.5, -pairA, -4.5, 5.0, 3.5 * U, -2.0, HR_GREEN)
        m.pop()
        m.push()
        m.translate(0, pairB, 0)
        m.box3d(-5.0, -pairB, 2.0, -2.5, 3.5 * U, 4.5, HR_GREEN)
        m.box3d(2.5, -pairB, 2.0, 5.0, 3.5 * U, 4.5, HR_GREEN)
        m.pop()
        m.box3d(-4.0, 3.5 * U, 0.0, 4.0, 5.5 * U, 4.5, HR_GREEN)
        m.box3d(-4.0, 3.5 * U, -5.5, 4.0, 9.5 * U, -0.5, HR_GREEN)
        m.box3d(-4.5, 5.0 * U, -6.0, 4.5, 8.0 * U, -0.3, HR_IRON)
        m.box3d(-7.0, 8.0 * U, -3.0, -4.0, 10.0 * U, 3.0, HR_IRON)
        m.box3d(4.0, 8.0 * U, -3.0, 7.0, 10.0 * U, 3.0, HR_IRON)
        m.box3d(-3.0, 9.5 * U, -3.0, 3.0, 11.5 * U, 3.0, HR_GREEN)
        m.box3d(-2.5, 9.0 * U, -4.0, 2.5, 10.2 * U, 4.0, HR_GREEN)
        m.push()
        m.rotate(-35.0, 0, 0, 1)
        m.box3d(-8.5, 9.0 * U, -0.6, -4.5, 10.5 * U, 0.6, HR_BONE)
        m.pop()
        m.push()
        m.rotate(35.0, 0, 0, 1)
        m.box3d(4.5, 9.0 * U, -0.6, 8.5, 10.5 * U, 0.6, HR_BONE)
        m.pop()
        atkSwing = math.sin(atkP) * 45.0 - 25.0 if anim == 2 else 0.0
        m.push()
        m.translate(-6.0, 8.5 * U, 0)
        m.rotate(-20.0 + atkSwing, 1, 0, 0)
        m.box3d(-0.8, -3.0 * U, -0.8, 0.0, 0.0, 0.8, HR_BONE)
        m.box3d(-1.5, -3.6 * U, -1.8, 0.8, -3.0 * U, 1.8, HR_IRON)
        m.pop()
        m.push()
        m.translate(6.0, 8.5 * U, 0)
        m.rotate(-20.0 - atkSwing, 1, 0, 0)
        m.box3d(0.0, -3.0 * U, -0.8, 0.8, 0.0, 0.8, HR_BONE)
        m.box3d(-0.8, -3.6 * U, -1.8, 1.5, -3.0 * U, 1.8, HR_IRON)
        m.pop()

    elif idx == 4:
        # -- 4: SHAMAN (Mage) ------------------------------------------------
        lY1 = 3.2 * U
        gaitL = math.sin(walkP) * 16.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-0.8, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(0.8, -lY1, 0)
        m.box3d(-2.1, 0, -1.0, -0.2, lY1, 1.0, HR_DARK)
        m.pop()
        m.push()
        m.translate(0.8, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-0.8, -lY1, 0)
        m.box3d(0.2, 0, -1.0, 2.1, lY1, 1.0, HR_DARK)
        m.pop()
        m.box3d(-3.2, lY1, -1.6, 3.2, lY1 + 3.6 * U, 1.6, HR_DARK)
        m.box3d(-3.4, lY1 + 0.8 * U, -0.4, -2.7, lY1 + 2.6 * U, 0.4, HR_BONE)
        m.box3d(2.7, lY1 + 0.8 * U, -0.4, 3.4, lY1 + 2.6 * U, 0.4, HR_BONE)
        m.box3d(-2.1, lY1 + 3.6 * U, -1.6, 2.1, lY1 + 5.2 * U, 1.6, HR_GREEN)
        m.box3d(-1.8, lY1 + 3.2 * U, -2.0, 1.8, lY1 + 3.8 * U, 2.0, HR_GREEN)
        m.box3d(-1.6, lY1 + 5.2 * U, -0.4, -0.6, lY1 + 6.8 * U, 0.4, HR_BONE)
        m.box3d(-0.4, lY1 + 5.2 * U, -0.4, 0.4, lY1 + 7.2 * U, 0.4, HR_GLOW)
        m.box3d(0.6, lY1 + 5.2 * U, -0.4, 1.6, lY1 + 6.8 * U, 0.4, HR_BONE)
        if anim == 2:
            staffRot = math.sin(atkP) * 35.0
        elif anim == 0:
            staffRot = math.sin(idleP) * 8.0
        else:
            staffRot = 0.0
        m.push()
        m.translate(-3.2, lY1 + 2.4 * U, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.box3d(-0.8, -1.4 * U, -0.8, 0.0, 0.0, 0.8, HR_GREEN)
        m.pop()
        m.push()
        m.translate(3.2, lY1 + 2.4 * U, 0)
        m.rotate(staffRot, 1, 0, 0)
        m.box3d(0.0, -1.4 * U, -0.8, 0.8, 0.0, 0.8, HR_GREEN)
        m.box3d(0.3, -4.8 * U, -0.3, 0.7, 0.0, 0.3, HR_BONE)
        m.box3d(-0.5, -5.5 * U, -0.5, 1.5, -4.9 * U, 0.5, HR_BONE)
        sa = tickF * 2.0
        m.cube3(0.5 + 1.8 * math.cos(sa), -5.2 * U, 1.8 * math.sin(sa),
                0.35, HR_GLOW, 0.8)
        m.cube3(0.5 + 1.8 * math.cos(sa + 2.1), -5.2 * U, 1.8 * math.sin(sa + 2.1),
                0.35, HR_GLOW, 0.75)
        m.pop()

    elif idx == 5:
        # -- 5: WITCH DOCTOR (Healer) ----------------------------------------
        lY1 = 2.8 * U
        gaitL = math.sin(walkP) * 16.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-0.7, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(0.7, -lY1, 0)
        m.box3d(-1.6, 0, -0.9, -0.2, lY1, 0.9, HR_DARK)
        m.pop()
        m.push()
        m.translate(0.7, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-0.7, -lY1, 0)
        m.box3d(0.2, 0, -0.9, 1.6, lY1, 0.9, HR_DARK)
        m.pop()
        m.box3d(-2.6, lY1, -1.4, 2.6, lY1 + 3.2 * U, 1.4, HR_RUST)
        for i in range(3):
            ry = lY1 + (0.5 + i * 0.85) * U
            m.box3d(-2.7, ry, -1.5, 2.7, ry + 0.25 * U, 1.5, HR_BONE)
        m.box3d(-1.9, lY1 + 3.2 * U, -1.4, 1.9, lY1 + 4.7 * U, 1.4, HR_GREEN)
        m.box3d(-2.1, lY1 + 3.4 * U, -1.9, 2.1, lY1 + 4.4 * U, -1.3, HR_BONE)
        m.box3d(-0.9, lY1 + 3.7 * U, -2.1, -0.3, lY1 + 4.1 * U, -1.8, HR_DARK)
        m.box3d(0.3, lY1 + 3.7 * U, -2.1, 0.9, lY1 + 4.1 * U, -1.8, HR_DARK)
        m.box3d(-2.6, lY1 + 4.7 * U, -0.5, -1.6, lY1 + 6.7 * U, 0.5, HR_GLOW)
        m.box3d(-0.9, lY1 + 4.7 * U, -0.5, 0.0, lY1 + 7.2 * U, 0.5, HR_BONE)
        m.box3d(0.0, lY1 + 4.7 * U, -0.5, 0.9, lY1 + 7.2 * U, 0.5, HR_DARK)
        m.box3d(1.6, lY1 + 4.7 * U, -0.5, 2.6, lY1 + 6.7 * U, 0.5, HR_GLOW)
        if anim == 2:
            hexRot = math.sin(atkP) * 40.0
        elif anim == 0:
            hexRot = math.sin(idleP) * 10.0
        else:
            hexRot = 0.0
        m.push()
        m.translate(-2.6, lY1 + 2.0 * U, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.box3d(-0.8, -1.4 * U, -0.7, 0.0, 0.0, 0.7, HR_GREEN)
        m.pop()
        m.push()
        m.translate(2.6, lY1 + 2.0 * U, 0)
        m.rotate(hexRot, 1, 0, 0)
        m.box3d(0.0, -1.4 * U, -0.7, 0.8, 0.0, 0.7, HR_GREEN)
        m.box3d(0.25, -4.2 * U, -0.2, 0.65, 0.0, 0.2, HR_BONE)
        m.box3d(-0.5, -4.9 * U, -0.5, 1.3, -4.2 * U, 0.5, HR_CLOTH)
        if anim == 2:
            m.cube3(0.4, -4.5 * U, 0.0, 0.5 + 0.35 * math.sin(atkP * 2.0), HR_GLOW, 0.7)
        m.pop()

    elif idx == 6:
        # -- 6: WAR MACHINE (Siege catapult) ---------------------------------
        m.box3d(-5.5, 0, -4.5, 5.5, 2.8 * U, 4.5, HR_IRON)
        for s in (-1, 0, 1):
            sx = s * 3.0
            m.box3d(sx - 0.7, 1.5 * U, -6.0, sx + 0.7, 2.3 * U, -4.4, HR_BONE)
        wRot = tickF * 130.0 if anim == 1 else 0.0
        for wx in (-6.0, 6.0):
            for wz in (-3.5, 3.5):
                m.push()
                m.translate(wx, 2.8 * U, wz)
                m.rotate(wRot, 0, 1, 0)
                m.box3d(-1.0, -2.8 * U, -2.8, 1.0, 2.8 * U, 2.8, HR_DARK)
                m.box3d(-1.2, -0.3, -3.0, 1.2, 0.3, 3.0, HR_IRON)
                m.box3d(-1.2, -3.0, -0.3, 1.2, 3.0, 0.3, HR_IRON)
                m.pop()
        armAng = -55.0 + math.sin(atkP) * 80.0 if anim == 2 else -25.0
        m.push()
        m.translate(0, 3.2 * U, 0)
        m.rotate(armAng, 0, 0, 1)
        m.box3d(-0.6, 0, -0.6, 0.6, 6.5 * U, 0.6, HR_RUST)
        m.box3d(-1.8, -2.5 * U, -1.8, 1.8, 0.0, 1.8, HR_IRON)
        m.box3d(-1.5, 5.8 * U, -1.5, 1.5, 6.8 * U, 1.5, HR_DARK)
        if anim != 2:
            m.cube3(0, 6.4 * U, 0, 0.9, HR_BONE, 1.0)
        m.pop()
        m.box3d(-5.0, 2.8 * U, -1.0, 5.0, 3.8 * U, 1.0, HR_RUST)

    else:
        return None     # the C++ answers an unknown unitIdx with "return false"

    m.pop()
    return m.build(**bake)
