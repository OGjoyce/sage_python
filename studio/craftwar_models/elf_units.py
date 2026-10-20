"""Elf (Sentinel) 3D unit models.

Port of drawElfUnit3D in src/gfx/models3d/elf_units.cpp, C++ numbers verbatim.
Buildings from the same file are in elf_bldg.py.

Units: Wisp(0) Archer(1) Sentinel(2) Druid(3) Dryad(4) Keeper(5) Ballista(6)
"""

import math

from claude_studio.craftwar_gl import U, GLModel

EL_FERN = 0x3C5028
EL_DARK = 0x0A140C
EL_BARK = 0x506030
EL_GLOW = 0x90E8A0
EL_MOON = 0xD0FFE0
EL_WISP = 0x70C8FF
EL_SILVER = 0xC0D0C8
EL_LEAF = 0x60A840

NAMES = ("Wisp", "Archer", "Sentinel", "Druid", "Dryad", "Keeper", "Ballista")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the unit, as unitIdx does in the C++."""
    m = GLModel(name or f"ELF_unit{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")

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
        # -- 0: WISP (Worker -- floating orb) --------------------------------
        # Pure energy ball -- no legs, pure hover
        hY = 2.5 * U + math.sin(idleP) * 1.2 * U
        m.translate(0, hY, 0)
        # Core orb
        sz = 0.9 + 0.25 * math.sin(idleP * 2.0)
        m.cube3(0, 0, 0, sz * U, EL_WISP, 0.9)
        # Inner glow core
        m.cube3(0, 0, 0, sz * 0.55 * U, EL_MOON, 0.85)
        # Trailing wisps orbiting
        a1 = tickF * 2.5
        a2, a3 = a1 + 2.094, a1 + 4.189
        m.cube3(1.5 * U * math.cos(a1), 0.5 * U * math.sin(a1 * 0.7),
                1.5 * U * math.sin(a1), 0.3 * U, EL_GLOW, 0.7)
        m.cube3(1.5 * U * math.cos(a2), 0.5 * U * math.sin(a2 * 0.7),
                1.5 * U * math.sin(a2), 0.3 * U, EL_WISP, 0.65)
        m.cube3(1.5 * U * math.cos(a3), 0.5 * U * math.sin(a3 * 0.7),
                1.5 * U * math.sin(a3), 0.3 * U, EL_MOON, 0.6)
        # Tool aura on attack
        if anim == 2:
            ar = tickF * 5.0
            for p in range(4):
                pa = p * 1.57 + ar
                m.cube3(2.0 * U * math.cos(pa), 0, 2.0 * U * math.sin(pa),
                        0.25 * U, EL_GLOW, 0.75)

    elif idx == 1:
        # -- 1: ARCHER (Melee -- elf with twin blades) -----------------------
        lY1 = 3.5 * U
        gaitL = math.sin(walkP) * 20.0 if anim == 1 else 0.0
        gaitR = -gaitL
        # Slim elf legs (fitted leather)
        m.push()
        m.translate(-0.8, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(0.8, -lY1, 0)
        m.box3d(-1.8, 0, -0.8, -0.2, lY1, 0.8, EL_FERN)
        m.pop()
        m.push()
        m.translate(0.8, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-0.8, -lY1, 0)
        m.box3d(0.2, 0, -0.8, 1.8, lY1, 0.8, EL_FERN)
        m.pop()
        # Boots
        m.box3d(-2.1, 0, -1.0, -0.1, 0.6 * U, 1.0, EL_DARK)
        m.box3d(0.1, 0, -1.0, 2.1, 0.6 * U, 1.0, EL_DARK)
        # Slim torso with leather armour
        m.box3d(-2.5, lY1, -1.2, 2.5, lY1 + 3.2 * U, 1.2, EL_FERN)
        # Leaf-green mantle
        m.box3d(-3.0, lY1 + 2.0 * U, -1.0, 3.0, lY1 + 3.0 * U, 1.0, EL_LEAF)
        # Pointed elf ears from head
        m.box3d(-1.8, lY1 + 3.2 * U, -1.2, 1.8, lY1 + 4.6 * U, 1.2, EL_SILVER)
        m.box3d(-2.4, lY1 + 4.0 * U, -0.5, -1.6, lY1 + 4.9 * U, 0.5, EL_SILVER)  # left
        m.box3d(1.6, lY1 + 4.0 * U, -0.5, 2.4, lY1 + 4.9 * U, 0.5, EL_SILVER)    # right
        # Twin short blades at hips
        if anim == 1:
            swL, swR = math.sin(walkP) * 22.0, -math.sin(walkP) * 22.0
        elif anim == 2:
            swL = -45.0 + math.sin(atkP) * 70.0
            swR = 45.0 - math.sin(atkP) * 70.0
        else:
            swL = swR = 0.0
        m.push()
        m.translate(-2.5, lY1 + 2.2 * U, 0)
        m.rotate(swL, 1, 0, 0)
        m.box3d(-0.6, -1.5 * U, -0.5, 0.0, 0.0, 0.5, EL_FERN)       # left arm
        m.box3d(-0.9, -3.2 * U, -0.2, -0.3, -1.3 * U, 0.2, EL_MOON)  # blade
        m.pop()
        m.push()
        m.translate(2.5, lY1 + 2.2 * U, 0)
        m.rotate(swR, 1, 0, 0)
        m.box3d(0.0, -1.5 * U, -0.5, 0.6, 0.0, 0.5, EL_FERN)
        m.box3d(0.3, -3.2 * U, -0.2, 0.9, -1.3 * U, 0.2, EL_MOON)
        m.pop()

    elif idx == 2:
        # -- 2: SENTINEL (Ranged -- tall elf archer) -------------------------
        lY1 = 4.0 * U
        gaitL = math.sin(walkP) * 18.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-0.9, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(0.9, -lY1, 0)
        m.box3d(-2.0, 0, -0.9, -0.2, lY1, 0.9, EL_FERN)
        m.pop()
        m.push()
        m.translate(0.9, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-0.9, -lY1, 0)
        m.box3d(0.2, 0, -0.9, 2.0, lY1, 0.9, EL_FERN)
        m.pop()
        m.box3d(-2.3, 0, -1.1, -0.1, 0.7 * U, 1.1, EL_DARK)
        m.box3d(0.1, 0, -1.1, 2.3, 0.7 * U, 1.1, EL_DARK)
        # Taller slimmer torso + silver chest plate
        m.box3d(-2.6, lY1, -1.3, 2.6, lY1 + 3.5 * U, 1.3, EL_FERN)
        m.box3d(-2.5, lY1 + 0.8 * U, -1.4, 2.5, lY1 + 2.8 * U, 1.4, EL_SILVER)
        # Head with circlet
        m.box3d(-1.8, lY1 + 3.5 * U, -1.3, 1.8, lY1 + 5.0 * U, 1.3, EL_SILVER)
        m.box3d(-2.3, lY1 + 4.2 * U, -0.5, -1.6, lY1 + 4.9 * U, 0.5, EL_SILVER)
        m.box3d(1.6, lY1 + 4.2 * U, -0.5, 2.3, lY1 + 4.9 * U, 0.5, EL_SILVER)
        # Moon circlet
        m.box3d(-2.2, lY1 + 5.0 * U, -0.3, 2.2, lY1 + 5.3 * U, 0.3, EL_MOON)
        # Quiver on back
        m.box3d(-0.5, lY1 + 1.0 * U, 1.3, 0.5, lY1 + 3.2 * U, 2.0, EL_BARK)
        # Tall moonbow (held)
        bowRot = math.sin(atkP) * 25.0 if anim == 2 else 0.0
        m.push()
        m.translate(-2.6, lY1 + 2.5 * U, 0)
        m.rotate(-20.0 + gaitR, 1, 0, 0)
        m.box3d(-0.6, -1.8 * U, -0.5, 0.0, 0.0, 0.5, EL_FERN)    # left arm
        m.pop()
        m.push()
        m.translate(2.6, lY1 + 2.5 * U, 0)
        m.rotate(bowRot + gaitL, 1, 0, 0)
        m.box3d(0.0, -1.8 * U, -0.5, 0.6, 0.0, 0.5, EL_FERN)     # right arm holds bow
        m.box3d(0.2, -4.5 * U, -0.2, 0.5, 0.0, 0.2, EL_MOON)     # bow limb lower
        m.box3d(0.2, 0, -0.2, 0.5, 3.5 * U, 0.2, EL_MOON)        # bow limb upper
        m.box3d(0.3, -4.3 * U, -0.15, 0.4, 3.3 * U, 0.15, EL_GLOW, 0.8)   # bowstring
        m.pop()

    elif idx == 3:
        # -- 3: DRUID (Heavy -- panther mount) -------------------------------
        pairA = abs(math.sin(walkP * 2.0)) * U * 0.6 if anim == 1 else 0.0
        pairB = abs(math.sin(walkP * 2.0 + 1.57)) * U * 0.6 if anim == 1 else 0.0
        # Panther body hull
        m.box3d(-5.0, 0, -4.0, 5.0, 3.0 * U, 4.0, EL_DARK)
        # Four panther legs
        m.push()
        m.translate(0, pairA, 0)
        m.box3d(-4.5, -pairA, -3.5, -2.0, 3.0 * U, -1.5, EL_DARK)
        m.box3d(2.0, -pairA, -3.5, 4.5, 3.0 * U, -1.5, EL_DARK)
        m.pop()
        m.push()
        m.translate(0, pairB, 0)
        m.box3d(-4.5, -pairB, 1.5, -2.0, 3.0 * U, 3.5, EL_DARK)
        m.box3d(2.0, -pairB, 1.5, 4.5, 3.0 * U, 3.5, EL_DARK)
        m.pop()
        # Panther head (front)
        m.box3d(-2.0, 2.5 * U, -6.0, 2.0, 4.5 * U, -3.5, EL_DARK)
        m.box3d(-1.5, 2.0 * U, -7.5, 1.5, 3.0 * U, -5.5, EL_DARK)    # snout
        # Panther tail (back)
        m.box3d(-0.4, 3.5 * U, 4.0, 0.4, 4.5 * U, 6.0, EL_DARK)
        # Spotted pattern (leaf spots)
        m.cube3(-3.0, 3.2 * U, 0.0, 0.4, EL_FERN, 1.0)
        m.cube3(3.0, 3.2 * U, 0.0, 0.4, EL_FERN, 1.0)
        m.cube3(0, 3.2 * U, -2.5, 0.4, EL_FERN, 1.0)
        # Druid rider on top
        m.box3d(-2.0, 3.0 * U, -3.0, 2.0, 7.0 * U, -0.5, EL_BARK)
        m.box3d(-2.5, 5.5 * U, -1.8, 2.5, 7.5 * U, 1.8, EL_FERN)     # mantle
        # Head with antler crown
        m.box3d(-1.5, 7.0 * U, -2.0, 1.5, 8.5 * U, -0.5, EL_SILVER)
        m.push()
        m.rotate(-25.0, 0, 0, 1)
        m.box3d(-5.0, 7.5 * U, -0.4, -2.0, 9.0 * U, 0.4, EL_BARK)
        m.pop()
        m.push()
        m.rotate(25.0, 0, 0, 1)
        m.box3d(2.0, 7.5 * U, -0.4, 5.0, 9.0 * U, 0.4, EL_BARK)
        m.pop()
        # Attack -- nature staff
        atkSwing = math.sin(atkP) * 40.0 if anim == 2 else 0.0
        m.push()
        m.translate(2.5, 6.5 * U, 0)
        m.rotate(atkSwing, 1, 0, 0)
        m.box3d(0.0, -3.0 * U, -0.3, 0.6, 0.0, 0.3, EL_BARK)
        m.cube3(0.3, -3.5 * U, 0.0, 0.5 + 0.2 * math.sin(tickF * 2.0), EL_GLOW, 0.75)
        m.pop()

    elif idx == 4:
        # -- 4: DRYAD (Mage -- plant hybrid) ---------------------------------
        lY1 = 2.5 * U
        # Root/vine lower body (no legs, plant base)
        for r in range(5):
            ra = r * 1.257 + tickF * 0.3
            rx, rz = 2.0 * math.cos(ra), 2.0 * math.sin(ra)
            m.box3d(rx - 0.5, 0, rz - 0.5, rx + 0.5, lY1, rz + 0.5, EL_BARK, 0.9)
        # Thorn-vine coil at waist
        m.box3d(-2.8, lY1, -1.3, 2.8, lY1 + 0.4 * U, 1.3, EL_LEAF)
        # Plant-humanoid upper torso
        m.box3d(-2.4, lY1, -1.3, 2.4, lY1 + 3.0 * U, 1.3, EL_FERN)
        # Leaf mantle on shoulders
        for lf in range(6):
            la = lf * 1.047
            lx, lz = 3.2 * math.cos(la), 3.2 * math.sin(la)
            m.cube3(lx, lY1 + 2.8 * U, lz, 0.5, EL_LEAF, 0.85)
        # Leaf crown / head
        m.box3d(-1.8, lY1 + 3.0 * U, -1.2, 1.8, lY1 + 4.5 * U, 1.2, EL_SILVER)
        m.box3d(-2.5, lY1 + 4.2 * U, -0.7, 2.5, lY1 + 4.7 * U, 0.7, EL_LEAF)  # crown
        # Vine tendrils for arms
        atkSw = math.sin(atkP) * 40.0 if anim == 2 else math.sin(idleP) * 8.0
        m.push()
        m.translate(-2.4, lY1 + 2.0 * U, 0)
        m.rotate(-atkSw * 0.5, 1, 0, 0)
        m.box3d(-1.5, -1.5 * U, -0.5, 0.0, 0.0, 0.5, EL_BARK)
        m.cube3(-0.8, -1.8 * U, 0, 0.5, EL_LEAF, 0.85)     # leaf cluster at hand
        m.pop()
        m.push()
        m.translate(2.4, lY1 + 2.0 * U, 0)
        m.rotate(atkSw, 1, 0, 0)
        m.box3d(0.0, -1.5 * U, -0.5, 1.5, 0.0, 0.5, EL_BARK)
        m.cube3(0.8, -1.8 * U, 0, 0.5, EL_LEAF, 0.85)
        # Spell bloom on attack
        if anim == 2:
            sg = 0.6 + 0.4 * math.sin(atkP * 2.0)
            m.cube3(0.8, -2.5 * U, -1.5, sg, EL_GLOW, 0.7)
        m.pop()

    elif idx == 5:
        # -- 5: KEEPER (Healer -- ancient nature spirit) ---------------------
        lY1 = 3.0 * U
        gaitL = math.sin(walkP) * 14.0 if anim == 1 else 0.0
        gaitR = -gaitL
        # Ancient, root-tangled legs
        m.push()
        m.translate(-0.9, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(0.9, -lY1, 0)
        m.box3d(-2.3, 0, -1.2, -0.2, lY1, 1.2, EL_BARK)
        m.pop()
        m.push()
        m.translate(0.9, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-0.9, -lY1, 0)
        m.box3d(0.2, 0, -1.2, 2.3, lY1, 1.2, EL_BARK)
        m.pop()
        # Root tangle at feet
        for r in range(4):
            ra = r * 0.785
            rx, rz = 2.0 * math.cos(ra), 2.0 * math.sin(ra)
            m.box3d(rx - 0.3, 0, rz - 0.3, rx + 0.3, 0.8 * U, rz + 0.3, EL_BARK)
        # Ancient wide torso
        m.box3d(-3.0, lY1, -1.5, 3.0, lY1 + 4.0 * U, 1.5, EL_BARK)
        # Moon-silver chest glyph
        m.box3d(-0.2, lY1 + 1.5 * U, -1.6, 0.2, lY1 + 3.0 * U, -1.4, EL_MOON)
        m.box3d(-1.2, lY1 + 2.0 * U, -1.6, 1.2, lY1 + 2.3 * U, -1.4, EL_MOON)
        # Ancient face with wooden features
        m.box3d(-2.0, lY1 + 4.0 * U, -1.5, 2.0, lY1 + 5.5 * U, 1.5, EL_BARK)
        # Leaf horns / crown
        m.box3d(-3.0, lY1 + 5.0 * U, -0.5, -2.0, lY1 + 6.5 * U, 0.5, EL_LEAF)
        m.box3d(2.0, lY1 + 5.0 * U, -0.5, 3.0, lY1 + 6.5 * U, 0.5, EL_LEAF)
        m.box3d(-0.5, lY1 + 5.5 * U, -0.5, 0.5, lY1 + 7.0 * U, 0.5, EL_GLOW)
        # Staff with moon orb
        if anim == 2:
            staffRot = math.sin(atkP) * 30.0
        elif anim == 0:
            staffRot = math.sin(idleP) * 6.0
        else:
            staffRot = 0.0
        m.push()
        m.translate(-3.0, lY1 + 3.0 * U, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.box3d(-0.7, -1.5 * U, -0.7, 0.0, 0.0, 0.7, EL_BARK)
        m.pop()
        m.push()
        m.translate(3.0, lY1 + 3.0 * U, 0)
        m.rotate(staffRot, 1, 0, 0)
        m.box3d(0.0, -1.5 * U, -0.7, 0.7, 0.0, 0.7, EL_BARK)
        m.box3d(0.25, -5.0 * U, -0.25, 0.55, 0.0, 0.25, EL_BARK)   # staff shaft
        m.cube3(0.4, -5.5 * U, 0, 0.7 + 0.25 * math.sin(tickF * 1.8), EL_MOON, 0.85)
        # Healing ring
        if anim == 2:
            hr = tickF * 3.0
            for p in range(5):
                pa = p * 1.257 + hr
                m.cube3(2.5 * math.cos(pa), 0.5 * U, 2.5 * math.sin(pa),
                        0.35, EL_GLOW, 0.7)
        m.pop()

    elif idx == 6:
        # -- 6: BALLISTA (Siege) ---------------------------------------------
        # Elegant wooden frame
        m.box3d(-5.0, 0, -3.5, 5.0, 1.5 * U, 3.5, EL_BARK)
        # Two large wooden wheels
        wRot = tickF * 100.0 if anim == 1 else 0.0
        for s in (-1, 1):
            wx = s * 5.5
            for wz in (2.0, -2.0):
                m.push()
                m.translate(wx, 2.5 * U, wz)
                m.rotate(wRot, 0, 1, 0)
                m.box3d(-0.8, -2.5 * U, -2.5, 0.8, 2.5 * U, 2.5, EL_DARK)
                m.box3d(-1.0, -0.25, -2.7, 1.0, 0.25, 2.7, EL_BARK)
                m.box3d(-1.0, -2.7, -0.25, 1.0, 2.7, 0.25, EL_BARK)
                m.pop()
        # Curved ballista arms
        atkAng = math.sin(atkP) * 55.0 if anim == 2 else 0.0
        m.push()
        m.translate(-5.0, 2.0 * U, 0)
        m.rotate(-35.0 + atkAng, 0, 0, 1)
        m.box3d(-3.0, -0.4, -0.4, 0.0, 0.4, 0.4, EL_FERN)
        m.pop()
        m.push()
        m.translate(5.0, 2.0 * U, 0)
        m.rotate(35.0 - atkAng, 0, 0, 1)
        m.box3d(0.0, -0.4, -0.4, 3.0, 0.4, 0.4, EL_FERN)
        m.pop()
        # Torsion string
        m.box3d(-5.5, 2.0 * U, -0.2, -4.0, 2.0 * U, 0.2, EL_MOON, 0.9)
        m.box3d(4.0, 2.0 * U, -0.2, 5.5, 2.0 * U, 0.2, EL_MOON, 0.9)
        # Long moonsilver bolt
        m.box3d(-0.25, 2.5 * U, -5.5, 0.25, 2.5 * U + 0.3, 0.0, EL_MOON)
        m.box3d(-0.15, 2.5 * U, -0.5, 0.15, 2.5 * U + 0.3, 1.5, EL_GLOW)  # fletching
        # Moon-carved ornament on frame
        m.box3d(-0.4, 1.5 * U, -0.4, 0.4, 3.5 * U, 0.4, EL_BARK)          # center post
        m.cube3(0, 3.5 * U, 0, 0.6, EL_MOON, 0.8)

    else:
        return None     # the C++ answers an unknown unitIdx with "return false"

    m.pop()
    return m.build(**bake)
