"""Scourge 3D unit models.

Port of drawScourgeUnit3D in src/gfx/models3d/scourge_units.cpp, C++ numbers
verbatim. Buildings from the same file are in scourge_bldg.py.

Units: Acolyte(0) Ghoul(1) CryptFiend(2) Abomination(3) Lich(4) Banshee(5)
       MeatWagon(6)
"""

import math

from claude_studio.craftwar_gl import U, GLModel

SC_VOID = 0x1A1428
SC_SHADOW = 0x06050A
SC_BONE = 0xEEE6CC
SC_PLAGUE = 0x40FF80
SC_GOLD = 0xB08020
SC_ROBE = 0x281C40
SC_ROT = 0x304830
SC_RUST = 0x503828

NAMES = ("Acolyte", "Ghoul", "CryptFiend", "Abomination", "Lich", "Banshee",
         "MeatWagon")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the unit, as unitIdx does in the C++."""
    m = GLModel(name or f"SCOURGE_unit{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")

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
        # -- 0: ACOLYTE (Worker) ---------------------------------------------
        lY1 = 3.0 * U
        gaitL = math.sin(walkP) * 16.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-0.7, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(0.7, -lY1, 0)
        m.box3d(-1.8, 0, -0.9, -0.2, lY1, 0.9, SC_SHADOW)
        m.pop()
        m.push()
        m.translate(0.7, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-0.7, -lY1, 0)
        m.box3d(0.2, 0, -0.9, 1.8, lY1, 0.9, SC_SHADOW)
        m.pop()
        m.box3d(-2.3, lY1, -1.2, 2.3, lY1 + 3.2 * U, 1.2, SC_ROBE)
        m.box3d(-2.5, lY1, -1.3, 2.5, lY1 + 0.3 * U, 1.3, SC_GOLD)
        m.box3d(-1.6, lY1 + 3.2 * U, -1.2, 1.6, lY1 + 4.7 * U, 1.2, SC_BONE)
        m.box3d(-2.0, lY1 + 3.5 * U, -1.4, 2.0, lY1 + 4.2 * U, 1.4, SC_ROBE)
        if anim == 1:
            armSw = math.sin(walkP) * 18.0
        elif anim == 2:
            armSw = -35.0 + math.sin(atkP) * 45.0
        else:
            armSw = 0.0
        m.push()
        m.translate(-2.3, lY1 + 2.2 * U, 0)
        m.rotate(-armSw * 0.5, 1, 0, 0)
        m.box3d(-0.7, -1.2 * U, -0.5, 0.0, 0.0, 0.5, SC_BONE)
        m.pop()
        m.push()
        m.translate(2.3, lY1 + 2.2 * U, 0)
        m.rotate(armSw, 1, 0, 0)
        m.box3d(0.0, -1.2 * U, -0.5, 0.7, 0.0, 0.5, SC_BONE)
        m.box3d(0.3, -2.0 * U, -0.2, 0.6, 0.0, 0.2, SC_BONE)
        m.box3d(0.4, -2.3 * U, -0.7, 1.2, -2.0 * U, -0.1, SC_BONE)
        m.pop()

    elif idx == 1:
        # -- 1: GHOUL (Melee) ------------------------------------------------
        lY1 = 2.5 * U
        gaitL = math.sin(walkP) * 25.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-1.2, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(1.2, -lY1, 0)
        m.box3d(-3.0, 0, -1.5, -0.2, lY1, 1.5, SC_ROT)
        m.pop()
        m.push()
        m.translate(1.2, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-1.2, -lY1, 0)
        m.box3d(0.2, 0, -1.5, 3.0, lY1, 1.5, SC_ROT)
        m.pop()
        m.box3d(-4.5, lY1, -2.2, 4.5, lY1 + 2.5 * U, 2.2, SC_ROT)
        for r in range(3):
            ry = lY1 + 0.5 * U + r * 0.7 * U
            m.box3d(-4.6, ry, -2.0, -3.8, ry + 0.25 * U, 2.0, SC_BONE)
            m.box3d(3.8, ry, -2.0, 4.6, ry + 0.25 * U, 2.0, SC_BONE)
        m.box3d(-2.5, lY1 + 2.5 * U, -2.0, 2.5, lY1 + 3.8 * U, 2.0, SC_BONE)
        m.box3d(-2.2, lY1 + 2.2 * U, -2.5, 2.2, lY1 + 2.8 * U, 2.5, SC_BONE)
        if anim == 1:
            clawSwL = math.sin(walkP) * 20.0
            clawSwR = -math.sin(walkP) * 20.0
        elif anim == 2:
            clawSwL = -50.0 + math.sin(atkP) * 80.0
            clawSwR = 50.0 - math.sin(atkP) * 80.0
        else:
            clawSwL = clawSwR = 0.0
        m.push()
        m.translate(-4.5, lY1 + 2.0 * U, 0)
        m.rotate(clawSwL, 1, 0, 0)
        m.box3d(-1.5, -2.0 * U, -1.0, 0.0, 0.0, 1.0, SC_ROT)
        m.box3d(-2.5, -3.5 * U, -0.2, -0.5, -1.8 * U, 0.2, SC_BONE)
        m.box3d(-2.5, -3.5 * U, -0.9, -0.5, -1.8 * U, -0.5, SC_BONE)
        m.box3d(-2.5, -3.5 * U, 0.5, -0.5, -1.8 * U, 0.9, SC_BONE)
        m.pop()
        m.push()
        m.translate(4.5, lY1 + 2.0 * U, 0)
        m.rotate(clawSwR, 1, 0, 0)
        m.box3d(0.0, -2.0 * U, -1.0, 1.5, 0.0, 1.0, SC_ROT)
        m.box3d(0.5, -3.5 * U, -0.2, 2.5, -1.8 * U, 0.2, SC_BONE)
        m.box3d(0.5, -3.5 * U, -0.9, 2.5, -1.8 * U, -0.5, SC_BONE)
        m.box3d(0.5, -3.5 * U, 0.5, 2.5, -1.8 * U, 0.9, SC_BONE)
        m.pop()

    elif idx == 2:
        # -- 2: CRYPT FIEND (Ranged -- spider form) --------------------------
        legL1 = math.sin(walkP * 2.0) * 15.0 if anim == 1 else 0.0
        legL2 = -legL1
        m.box3d(-3.0, 2.5 * U, -3.0, 3.0, 4.5 * U, 3.0, SC_VOID)
        m.box3d(-2.0, 2.0 * U, -5.5, 2.0, 4.0 * U, -2.5, SC_VOID)
        for sx, sz, ang, x0, x1 in ((-3.0, 2.0, -30.0 + legL1, -3.5, 0.0),
                                    (-3.0, -2.0, -30.0 + legL2, -3.5, 0.0),
                                    (3.0, 2.0, 30.0 + legL1, 0.0, 3.5),
                                    (3.0, -2.0, 30.0 + legL2, 0.0, 3.5)):
            m.push()
            m.translate(sx, 3.0 * U, sz)
            m.rotate(ang, 0, 0, 1)
            m.box3d(x0, -0.5, -0.6, x1, 0.5, 0.6, SC_BONE)
            m.pop()
        m.box3d(-2.0, 4.0 * U, -5.0, 2.0, 7.5 * U, -2.5, SC_VOID)
        m.box3d(-1.7, 7.5 * U, -5.2, 1.7, 9.0 * U, -3.0, SC_BONE)
        m.box3d(-2.5, 7.5 * U, -6.5, -1.5, 8.0 * U, -5.0, SC_BONE)
        m.box3d(1.5, 7.5 * U, -6.5, 2.5, 8.0 * U, -5.0, SC_BONE)
        webRot = math.sin(atkP) * 40.0 if anim == 2 else 0.0
        m.push()
        m.translate(2.0, 6.0 * U, -3.5)
        m.rotate(webRot, 1, 0, 0)
        m.box3d(0.0, -1.5 * U, -0.7, 0.7, 0.0, 0.7, SC_VOID)
        if anim == 2:
            m.cube3(0.4, -1.8 * U, -2.5, 0.4 + 0.2 * math.sin(atkP * 2.0), SC_PLAGUE, 0.75)
        m.pop()

    elif idx == 3:
        # -- 3: ABOMINATION (Heavy -- flesh golem) ---------------------------
        lY1 = 4.0 * U
        gaitL = math.sin(walkP) * 14.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-2.0, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(2.0, -lY1, 0)
        m.box3d(-4.0, 0, -2.0, -0.2, lY1, 2.0, SC_ROT)
        m.pop()
        m.push()
        m.translate(2.0, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-2.0, -lY1, 0)
        m.box3d(0.2, 0, -2.0, 4.0, lY1, 2.0, SC_ROT)
        m.pop()
        m.box3d(-6.0, lY1, -3.0, 6.0, lY1 + 5.0 * U, 3.0, SC_ROT)
        for s in range(4):
            sy = lY1 + s * 1.2 * U
            m.box3d(-6.2, sy, -0.3, 6.2, sy + 0.2, 0.3, SC_BONE)
        atkS = math.sin(atkP) * 50.0 if anim == 2 else 0.0
        m.push()
        m.translate(-6.0, lY1 + 4.0 * U, 0)
        m.rotate(-15.0 + atkS, 1, 0, 0)
        m.box3d(-2.0, -3.0 * U, -1.2, 0.0, 0.0, 1.2, SC_ROT)
        m.box3d(-3.5, -3.5 * U, -1.8, -0.5, -3.0 * U, 1.8, SC_BONE)
        m.pop()
        m.push()
        m.translate(6.0, lY1 + 4.0 * U, 0)
        m.rotate(-15.0 - atkS, 1, 0, 0)
        m.box3d(0.0, -3.0 * U, -1.2, 2.0, 0.0, 1.2, SC_ROT)
        m.box3d(0.5, -3.5 * U, -1.8, 3.5, -3.0 * U, 1.8, SC_BONE)
        m.pop()
        m.push()
        m.translate(6.0, lY1 + 1.5 * U, 0)
        m.box3d(0.0, -1.5 * U, -0.8, 1.5, 0.0, 0.8, SC_ROT)
        m.pop()
        m.box3d(-3.5, lY1 + 5.0 * U, -2.8, 3.5, lY1 + 7.0 * U, 2.8, SC_ROT)
        m.box3d(-3.0, lY1 + 4.5 * U, -3.2, 3.0, lY1 + 5.3 * U, 3.2, SC_BONE)
        m.cube3(-4.0, lY1 + 2.0 * U, -3.75, 0.4, SC_BONE, 0.85)

    elif idx == 4:
        # -- 4: LICH (Mage -- hovering) --------------------------------------
        hoverY = 3.0 * U + math.sin(idleP) * 0.8 * U
        m.translate(0, hoverY, 0)
        for r in range(4):
            ra = r * 1.57 + tickF * 0.5
            rx, rz = 1.2 * math.cos(ra), 1.2 * math.sin(ra)
            m.box3d(rx - 0.6, -1.5 * U, rz - 0.6, rx + 0.6, 0.0, rz + 0.6, SC_ROBE, 0.75)
        m.box3d(-2.0, 0.0, -1.5, 2.0, 1.5 * U, 1.5, SC_BONE, 0.9)
        m.box3d(-0.5, 0.0, -0.5, 0.5, 5.0 * U, 0.5, SC_BONE)
        m.box3d(-2.5, 1.5 * U, -1.8, 2.5, 4.5 * U, 1.8, SC_ROBE)
        m.box3d(-2.8, 2.0 * U, -2.0, 2.8, 4.0 * U, 2.0, SC_VOID, 0.7)
        m.box3d(-4.0, 4.0 * U, -1.5, -2.5, 5.0 * U, 1.5, SC_VOID)
        m.box3d(2.5, 4.0 * U, -1.5, 4.0, 5.0 * U, 1.5, SC_VOID)
        m.push()
        m.translate(-3.5, 4.5 * U, 0)
        m.rotate(-20.0 + (math.sin(idleP) * 12.0 if anim == 0 else 0.0), 1, 0, 0)
        m.box3d(-0.5, -2.0 * U, -0.5, 0.5, 0.0, 0.5, SC_BONE)
        m.pop()
        atkR = math.sin(atkP) * 40.0 if anim == 2 else 0.0
        m.push()
        m.translate(3.5, 4.5 * U, 0)
        m.rotate(-20.0 + atkR, 1, 0, 0)
        m.box3d(-0.5, -2.0 * U, -0.5, 0.5, 0.0, 0.5, SC_BONE)
        m.cube3(0.0, -2.3 * U, 0.0,
                0.7 + 0.3 * math.sin(atkP * 1.5 + tickF), SC_PLAGUE, 0.75)
        m.pop()
        m.box3d(-2.0, 4.5 * U, -2.0, 2.0, 6.2 * U, 2.0, SC_BONE)
        m.box3d(-1.8, 4.0 * U, -2.3, 1.8, 4.7 * U, 2.3, SC_BONE)
        for c in range(5):
            ca = c * 1.257
            cx, cz = 1.5 * math.cos(ca), 1.5 * math.sin(ca)
            m.box3d(cx - 0.3, 6.2 * U, cz - 0.3, cx + 0.3, 7.0 * U, cz + 0.3, 0xA0E0FF)

    elif idx == 5:
        # -- 5: BANSHEE (Healer -- ghostly hover) ----------------------------
        hoverY = 2.5 * U + math.sin(idleP * 1.2) * U
        m.translate(0, hoverY, 0)
        m.box3d(-2.0, 0.0, -1.3, 2.0, 3.5 * U, 1.3, SC_VOID, 0.65)
        for w in range(4):
            wa = w * 1.57 + tickF * 0.8
            wx, wz = 1.0 * math.cos(wa), 1.0 * math.sin(wa)
            m.box3d(wx - 0.5, -2.0 * U, wz - 0.5, wx + 0.5, 0.0, wz + 0.5, SC_VOID, 0.45)
        wailAng = math.sin(idleP) * 15.0 if anim == 0 else 0.0
        m.push()
        m.translate(-2.0, 2.5 * U, 0)
        m.rotate(-60.0 + wailAng, 0, 0, 1)
        m.box3d(-3.0, -0.4, -0.4, 0.0, 0.4, 0.4, SC_VOID, 0.7)
        m.pop()
        m.push()
        m.translate(2.0, 2.5 * U, 0)
        m.rotate(60.0 - wailAng, 0, 0, 1)
        m.box3d(0.0, -0.4, -0.4, 3.0, 0.4, 0.4, SC_VOID, 0.7)
        m.pop()
        m.box3d(-1.5, 3.5 * U, -1.3, 1.5, 4.8 * U, 1.3, SC_BONE, 0.75)
        m.box3d(-1.0, 3.0 * U, -1.5, 1.0, 3.6 * U, 1.5, SC_BONE, 0.7)
        m.cube3(-0.7, 4.0 * U, -1.5, 0.35, SC_PLAGUE, 0.8)
        m.cube3(0.7, 4.0 * U, -1.5, 0.35, SC_PLAGUE, 0.8)
        if anim == 2:
            ar = tickF * 3.5
            for p in range(6):
                pa = p * 1.047 + ar
                m.cube3(2.5 * math.cos(pa), 0.5 * U, 2.5 * math.sin(pa),
                        0.3, SC_PLAGUE, 0.7)

    elif idx == 6:
        # -- 6: MEAT WAGON (Siege) -------------------------------------------
        m.box3d(-5.5, 0, -4.0, 5.5, 2.5 * U, 4.0, SC_VOID)
        for sp in range(-4, 5, 2):
            m.box3d(sp - 0.35, 2.5 * U, -4.5, sp + 0.35, 3.5 * U, -3.8, SC_BONE)
            m.box3d(sp - 0.35, 2.5 * U, 3.8, sp + 0.35, 3.5 * U, 4.5, SC_BONE)
        wRot = tickF * 110.0 if anim == 1 else 0.0
        for s in (-1, 1):
            wx = s * 6.5
            for wz in (2.5, -2.5):
                m.push()
                m.translate(wx, 2.8 * U, wz)
                m.rotate(wRot, 0, 1, 0)
                m.box3d(-0.9, -2.8 * U, -2.8, 0.9, 2.8 * U, 2.8, SC_SHADOW)
                m.box3d(-1.1, -0.3, -3.0, 1.1, 0.3, 3.0, SC_BONE)
                m.box3d(-1.1, -3.0, -0.3, 1.1, 3.0, 0.3, SC_BONE)
                m.pop()
        armAng = -60.0 + math.sin(atkP) * 85.0 if anim == 2 else -20.0
        m.push()
        m.translate(0, 3.0 * U, 0)
        m.rotate(armAng, 0, 0, 1)
        m.box3d(-0.5, 0, -0.5, 0.5, 6.0 * U, 0.5, SC_RUST)
        m.box3d(-1.5, 5.5 * U, -1.5, 1.5, 6.5 * U, 1.5, SC_SHADOW)
        m.cube3(0, 6.0 * U, 0, 0.6 + 0.3 * math.sin(tickF * 4.0), SC_PLAGUE, 0.65)
        m.pop()
        m.push()
        m.translate(0, 3.0 * U, 0)
        m.rotate(armAng + 180.0, 0, 0, 1)
        m.box3d(-1.0, 0.5 * U, -1.0, 1.0, 2.5 * U, 1.0, SC_BONE)
        m.pop()

    else:
        return None     # the C++ answers an unknown unitIdx with "return false"

    m.pop()
    return m.build(**bake)
