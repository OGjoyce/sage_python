"""Dire (Legion of Chaos) 3D unit models.

Port of drawDireUnit3D in src/gfx/models3d/dire_units.cpp, C++ numbers
verbatim. Buildings from the same file are in dire_bldg.py.

Units: Imp(0) Fiend(1) Hellcaster(2) DoomGuard(3) Warlock(4) SoulEater(5)
       Infernal(6)

Note the palette: these are the race-table teals (DR_TEAL / DR_GLOW), not the
fel-green the DIRE hero model uses. dire_hero.cpp overrides the race style,
which is why the hero reads green and his own units read teal -- the model
that draws the thing wins over the race table.
"""

import math

from claude_studio.craftwar_gl import U, GLModel

DR_TEAL = 0x20B0A8
DR_DEEP = 0x0E5450
DR_GLOW = 0x60F0F0
DR_BONE = 0xD8CCA4
DR_FLESH = 0x1A1020
DR_HORN = 0x401010
DR_STONE = 0x484050
DR_FEL = 0x30F060

NAMES = ("Imp", "Fiend", "Hellcaster", "DoomGuard", "Warlock", "SoulEater", "Infernal")


def build(tickF=0.0, anim=0, idx=0, name=None, **bake):
    """idx selects the unit, as unitIdx does in the C++. Returns None for an
    index the C++ answers with `return false`."""
    m = GLModel(name or f"DIRE_unit{idx}_{NAMES[idx] if idx < len(NAMES) else 'none'}")

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
        # -- 0: IMP (Worker -- tiny hovering demon) --------------------------
        hY = 1.5 * U + math.sin(idleP) * 0.6 * U
        m.translate(0, hY, 0)
        # Tiny body -- 0.6x scale
        m.box3d(-1.2, 0, -0.8, 1.2, 1.8 * U, 0.8, DR_TEAL)
        # Small head
        m.box3d(-1.0, 1.8 * U, -0.9, 1.0, 2.9 * U, 0.9, DR_DEEP)
        # Tiny horns
        m.push()
        m.rotate(-20.0, 0, 0, 1)
        m.box3d(-2.0, 2.4 * U, -0.25, -0.8, 3.2 * U, 0.25, DR_HORN)
        m.pop()
        m.push()
        m.rotate(20.0, 0, 0, 1)
        m.box3d(0.8, 2.4 * U, -0.25, 2.0, 3.2 * U, 0.25, DR_HORN)
        m.pop()
        # Glowing eyes
        m.cube3(-0.55, 2.2 * U, -1.0, 0.2, DR_GLOW, 0.9)
        m.cube3(0.55, 2.2 * U, -1.0, 0.2, DR_GLOW, 0.9)
        # Bat wings (folded back)
        if anim == 1:
            wingFlap = math.sin(walkP * 4.0) * 20.0
        else:
            wingFlap = math.sin(idleP * 2.0) * 8.0
        m.push()
        m.translate(-1.2, 1.5 * U, 0)
        m.rotate(-40.0 + wingFlap, 0, 0, 1)
        m.box3d(-2.5, -0.3, -0.2, 0.0, 0.3, 0.2, DR_FLESH)          # wing
        m.box3d(-2.5, -0.3, -0.2, 0.0, 0.3, 0.2, DR_DEEP, 0.7)
        m.pop()
        m.push()
        m.translate(1.2, 1.5 * U, 0)
        m.rotate(40.0 - wingFlap, 0, 0, 1)
        m.box3d(0.0, -0.3, -0.2, 2.5, 0.3, 0.2, DR_FLESH)
        m.box3d(0.0, -0.3, -0.2, 2.5, 0.3, 0.2, DR_DEEP, 0.7)
        m.pop()
        # Spindly arms
        armSw = math.sin(atkP) * 45.0 if anim == 2 else 0.0
        m.push()
        m.translate(-1.2, 1.2 * U, 0)
        m.rotate(-armSw, 1, 0, 0)
        m.box3d(-0.8, -1.4 * U, -0.3, 0.0, 0.0, 0.3, DR_TEAL)
        m.pop()
        m.push()
        m.translate(1.2, 1.2 * U, 0)
        m.rotate(armSw, 1, 0, 0)
        m.box3d(0.0, -1.4 * U, -0.3, 0.8, 0.0, 0.3, DR_TEAL)
        if anim == 2:
            m.cube3(0.4, -1.8 * U, -0.5, 0.3 + 0.15 * math.sin(atkP * 2.0), DR_GLOW, 0.8)
        m.pop()
        # Long tail
        m.box3d(-0.2, -0.5 * U, -0.2, 0.2, 0.0, 0.2, DR_FLESH)
        m.box3d(-0.2, -1.2 * U, 0.5, 0.2, -0.4 * U, 1.0, DR_FLESH)

    elif idx == 1:
        # -- 1: FIEND (Melee -- angular bone-armoured demon) -----------------
        lY1 = 3.5 * U
        gaitL = math.sin(walkP) * 20.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-1.0, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(1.0, -lY1, 0)
        m.box3d(-2.5, 0, -1.2, -0.2, lY1, 1.2, DR_FLESH)
        m.pop()
        m.push()
        m.translate(1.0, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-1.0, -lY1, 0)
        m.box3d(0.2, 0, -1.2, 2.5, lY1, 1.2, DR_FLESH)
        m.pop()
        # Armoured hooves
        m.box3d(-2.8, 0, -1.5, -0.1, 0.8 * U, 1.5, DR_BONE)
        m.box3d(0.1, 0, -1.5, 2.8, 0.8 * U, 1.5, DR_BONE)
        # Chest with angular bone-shard armour
        m.box3d(-3.5, lY1, -1.7, 3.5, lY1 + 3.5 * U, 1.7, DR_FLESH)
        m.box3d(-3.8, lY1 + 0.5 * U, -1.9, 3.8, lY1 + 2.5 * U, 1.9, DR_BONE, 0.9)
        # Angular shoulder spikes
        m.box3d(-5.0, lY1 + 2.8 * U, -0.8, -3.0, lY1 + 4.5 * U, 0.8, DR_TEAL)
        m.box3d(3.0, lY1 + 2.8 * U, -0.8, 5.0, lY1 + 4.5 * U, 0.8, DR_TEAL)
        # Head with fel horns
        m.box3d(-2.2, lY1 + 3.5 * U, -1.8, 2.2, lY1 + 5.0 * U, 1.8, DR_FLESH)
        m.push()
        m.rotate(-25.0, 0, 0, 1)
        m.box3d(-5.0, lY1 + 4.5 * U, -0.5, -2.0, lY1 + 6.0 * U, 0.5, DR_TEAL)
        m.pop()
        m.push()
        m.rotate(25.0, 0, 0, 1)
        m.box3d(2.0, lY1 + 4.5 * U, -0.5, 5.0, lY1 + 6.0 * U, 0.5, DR_TEAL)
        m.pop()
        # Fel eyes
        m.cube3(-1.0, lY1 + 4.2 * U, -1.9, 0.3, DR_GLOW, 0.9)
        m.cube3(1.0, lY1 + 4.2 * U, -1.9, 0.3, DR_GLOW, 0.9)
        # Bone-shard sword arm
        swL = math.sin(walkP) * 18.0 if anim == 1 else 0.0
        atkRot = math.sin(atkP) * 55.0 - 15.0 if anim == 2 else 0.0
        m.push()
        m.translate(-3.5, lY1 + 2.5 * U, 0)
        m.rotate(-swL, 1, 0, 0)
        m.box3d(-0.8, -2.0 * U, -0.8, 0.0, 0.0, 0.8, DR_FLESH)
        m.pop()
        m.push()
        m.translate(3.5, lY1 + 2.5 * U, 0)
        m.rotate(atkRot, 1, 0, 0)
        m.box3d(0.0, -2.0 * U, -0.8, 0.8, 0.0, 0.8, DR_FLESH)
        m.box3d(0.3, -4.0 * U, -0.3, 0.7, 0.0, 0.3, DR_BONE)          # handle
        m.box3d(-0.2, -4.3 * U, -1.2, 1.2, -3.7 * U, 1.2, DR_TEAL)    # blade
        m.pop()

    elif idx == 2:
        # -- 2: HELLCASTER (Ranged -- hovering caster) -----------------------
        hY = 2.5 * U + math.sin(idleP) * 0.7 * U
        m.translate(0, hY, 0)
        # Hovering imp-like body (larger than Imp)
        m.box3d(-2.0, 0, -1.3, 2.0, 2.8 * U, 1.3, DR_TEAL)
        # Fel-burning eyes
        m.cube3(-0.9, 1.8 * U, -1.4, 0.4, DR_GLOW, 0.9)
        m.cube3(0.9, 1.8 * U, -1.4, 0.4, DR_GLOW, 0.9)
        # Head with swept-back horns
        m.box3d(-1.7, 2.8 * U, -1.4, 1.7, 4.2 * U, 1.4, DR_DEEP)
        m.push()
        m.rotate(-15.0, 0, 0, 1)
        m.box3d(-3.5, 3.5 * U, -0.4, -1.0, 4.5 * U, 0.4, DR_HORN)
        m.pop()
        m.push()
        m.rotate(15.0, 0, 0, 1)
        m.box3d(1.0, 3.5 * U, -0.4, 3.5, 4.5 * U, 0.4, DR_HORN)
        m.pop()
        # Bat wings (spread)
        if anim == 0:
            wingF = math.sin(idleP * 2.0) * 10.0
        elif anim == 1:
            wingF = math.sin(walkP * 3.0) * 25.0
        else:
            wingF = 0.0
        m.push()
        m.translate(-2.0, 2.0 * U, 0)
        m.rotate(-25.0 + wingF, 0, 0, 1)
        m.box3d(-4.0, -0.4, -0.3, 0.0, 0.4, 0.3, DR_FLESH, 0.8)
        m.pop()
        m.push()
        m.translate(2.0, 2.0 * U, 0)
        m.rotate(25.0 - wingF, 0, 0, 1)
        m.box3d(0.0, -0.4, -0.3, 4.0, 0.4, 0.3, DR_FLESH, 0.8)
        m.pop()
        # Arms -- large casting hands
        if anim == 2:
            castR = math.sin(atkP) * 40.0
        elif anim == 0:
            castR = math.sin(idleP) * 10.0
        else:
            castR = 0.0
        m.push()
        m.translate(-2.0, 1.5 * U, 0)
        m.rotate(-castR * 0.5, 1, 0, 0)
        m.box3d(-1.5, -1.5 * U, -0.8, 0.0, 0.0, 0.8, DR_TEAL)
        m.pop()
        m.push()
        m.translate(2.0, 1.5 * U, 0)
        m.rotate(castR, 1, 0, 0)
        m.box3d(0.0, -1.5 * U, -0.8, 1.5, 0.0, 0.8, DR_TEAL)
        # Fel orb in right hand
        orbSz = 0.7 + 0.35 * math.sin(atkP * 1.5 + tickF * 2.0)
        m.cube3(0.75, -2.0 * U, 0, orbSz, DR_GLOW, 0.75)
        if anim == 2:
            m.cube3(0.75, -2.0 * U, -2.5, 0.4 + 0.25 * math.sin(atkP * 3.0), DR_GLOW, 0.7)
        m.pop()

    elif idx == 3:
        # -- 3: DOOM GUARD (Heavy -- massive winged demon) -------------------
        lY1 = 4.5 * U
        gaitL = math.sin(walkP) * 15.0 if anim == 1 else 0.0
        gaitR = -gaitL
        # Enormous legs
        m.push()
        m.translate(-2.0, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(2.0, -lY1, 0)
        m.box3d(-4.5, 0, -2.5, -0.2, lY1, 2.5, DR_FLESH)
        m.pop()
        m.push()
        m.translate(2.0, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-2.0, -lY1, 0)
        m.box3d(0.2, 0, -2.5, 4.5, lY1, 2.5, DR_FLESH)
        m.pop()
        m.box3d(-5.0, 0, -3.0, -0.1, 1.0 * U, 3.0, DR_BONE)    # hooves
        m.box3d(0.1, 0, -3.0, 5.0, 1.0 * U, 3.0, DR_BONE)
        # Massive torso
        m.box3d(-7.0, lY1, -3.5, 7.0, lY1 + 5.5 * U, 3.5, DR_FLESH)
        # Teal armour plates across chest
        m.box3d(-7.2, lY1 + 1.0 * U, -4.0, 7.2, lY1 + 4.0 * U, 4.0, DR_TEAL, 0.9)
        # Giant bat wings from upper back
        if anim == 0:
            wingFl = math.sin(idleP) * 8.0
        elif anim == 1:
            wingFl = math.sin(walkP * 2.0) * 20.0
        else:
            wingFl = 0.0
        m.push()
        m.translate(-7.0, lY1 + 4.5 * U, 0)
        m.rotate(-50.0 + wingFl, 0, 0, 1)
        m.box3d(-9.0, -1.0, -1.2, 0.0, 1.0, 1.2, DR_FLESH, 0.85)
        m.box3d(-12.0, -1.0, -0.8, -7.0, 1.0, 0.8, DR_DEEP, 0.75)
        m.pop()
        m.push()
        m.translate(7.0, lY1 + 4.5 * U, 0)
        m.rotate(50.0 - wingFl, 0, 0, 1)
        m.box3d(0.0, -1.0, -1.2, 9.0, 1.0, 1.2, DR_FLESH, 0.85)
        m.box3d(7.0, -1.0, -0.8, 12.0, 1.0, 0.8, DR_DEEP, 0.75)
        m.pop()
        # Massive bull horns on head
        m.box3d(-3.5, lY1 + 5.5 * U, -3.0, 3.5, lY1 + 7.5 * U, 3.0, DR_FLESH)
        m.push()
        m.rotate(-40.0, 0, 0, 1)
        m.box3d(-10.0, lY1 + 6.5 * U, -0.8, -3.0, lY1 + 8.5 * U, 0.8, DR_HORN)
        m.pop()
        m.push()
        m.rotate(40.0, 0, 0, 1)
        m.box3d(3.0, lY1 + 6.5 * U, -0.8, 10.0, lY1 + 8.5 * U, 0.8, DR_HORN)
        m.pop()
        # Fel eyes
        m.cube3(-2.0, lY1 + 6.5 * U, -3.2, 0.5, DR_GLOW, 0.9)
        m.cube3(2.0, lY1 + 6.5 * U, -3.2, 0.5, DR_GLOW, 0.9)
        # Dual huge axes
        atkS = math.sin(atkP) * 55.0 - 25.0 if anim == 2 else 0.0
        m.push()
        m.translate(-7.0, lY1 + 4.0 * U, 0)
        m.rotate(-15.0 + atkS, 1, 0, 0)
        m.box3d(-1.5, -3.5 * U, -1.5, 0.0, 0.0, 1.5, DR_FLESH)
        m.box3d(-3.0, -4.2 * U, -2.5, 1.5, -3.5 * U, 2.5, DR_TEAL)
        m.pop()
        m.push()
        m.translate(7.0, lY1 + 4.0 * U, 0)
        m.rotate(-15.0 - atkS, 1, 0, 0)
        m.box3d(0.0, -3.5 * U, -1.5, 1.5, 0.0, 1.5, DR_FLESH)
        m.box3d(-1.5, -4.2 * U, -2.5, 3.0, -3.5 * U, 2.5, DR_TEAL)
        m.pop()

    elif idx == 4:
        # -- 4: WARLOCK (Mage -- tall humanoid demon caster) -----------------
        lY1 = 3.8 * U
        gaitL = math.sin(walkP) * 16.0 if anim == 1 else 0.0
        gaitR = -gaitL
        m.push()
        m.translate(-0.9, lY1, 0)
        m.rotate(gaitL, 1, 0, 0)
        m.translate(0.9, -lY1, 0)
        m.box3d(-2.2, 0, -1.0, -0.2, lY1, 1.0, DR_FLESH)
        m.pop()
        m.push()
        m.translate(0.9, lY1, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.translate(-0.9, -lY1, 0)
        m.box3d(0.2, 0, -1.0, 2.2, lY1, 1.0, DR_FLESH)
        m.pop()
        m.box3d(-2.5, 0, -1.3, -0.1, 0.8 * U, 1.3, DR_BONE)
        m.box3d(0.1, 0, -1.3, 2.5, 0.8 * U, 1.3, DR_BONE)
        # Tall flowing robe
        m.box3d(-3.0, lY1, -1.5, 3.0, lY1 + 4.0 * U, 1.5, DR_DEEP)
        # Teal fel trim
        m.box3d(-3.2, lY1, -1.6, 3.2, lY1 + 0.4 * U, 1.6, DR_TEAL)
        m.box3d(-3.2, lY1 + 3.6 * U, -1.6, 3.2, lY1 + 4.0 * U, 1.6, DR_TEAL)
        # Wide-shoulder mantle
        m.box3d(-4.5, lY1 + 3.2 * U, -1.2, 4.5, lY1 + 4.0 * U, 1.2, DR_DEEP)
        # Tall head with swept horns
        m.box3d(-2.0, lY1 + 4.0 * U, -1.7, 2.0, lY1 + 5.8 * U, 1.7, DR_FLESH)
        m.push()
        m.rotate(-20.0, 0, 0, 1)
        m.box3d(-5.0, lY1 + 5.0 * U, -0.5, -1.5, lY1 + 7.0 * U, 0.5, DR_TEAL)
        m.pop()
        m.push()
        m.rotate(20.0, 0, 0, 1)
        m.box3d(1.5, lY1 + 5.0 * U, -0.5, 5.0, lY1 + 7.0 * U, 0.5, DR_TEAL)
        m.pop()
        m.cube3(-1.0, lY1 + 5.0 * U, -1.8, 0.35, DR_GLOW, 0.9)
        m.cube3(1.0, lY1 + 5.0 * U, -1.8, 0.35, DR_GLOW, 0.9)
        # Chaos staff (right arm)
        if anim == 2:
            staffRot = math.sin(atkP) * 40.0
        elif anim == 0:
            staffRot = math.sin(idleP) * 8.0
        else:
            staffRot = 0.0
        m.push()
        m.translate(-3.0, lY1 + 3.0 * U, 0)
        m.rotate(gaitR, 1, 0, 0)
        m.box3d(-0.8, -1.5 * U, -0.8, 0.0, 0.0, 0.8, DR_FLESH)
        m.pop()
        m.push()
        m.translate(3.0, lY1 + 3.0 * U, 0)
        m.rotate(staffRot, 1, 0, 0)
        m.box3d(0.0, -1.5 * U, -0.8, 0.8, 0.0, 0.8, DR_FLESH)
        m.box3d(0.3, -5.0 * U, -0.3, 0.7, 0.0, 0.3, DR_BONE)     # staff
        # Chaotic orb at top -- double-pulsing
        orbSz = 0.8 + 0.35 * math.sin(tickF * 2.1)
        m.cube3(0.5, -5.6 * U, 0, orbSz, DR_GLOW, 0.75)
        m.cube3(0.5, -5.6 * U, 0, orbSz * 0.55, DR_FEL, 0.7)
        # Chaos orbiting shards
        ca = tickF * 2.5
        m.cube3(0.5 + 1.5 * math.cos(ca), -5.6 * U, 1.5 * math.sin(ca), 0.25, DR_TEAL, 0.8)
        m.cube3(0.5 + 1.5 * math.cos(ca + 2.1), -5.6 * U, 1.5 * math.sin(ca + 2.1),
                0.25, DR_GLOW, 0.75)
        m.pop()

    elif idx == 5:
        # -- 5: SOUL EATER (Healer -- spectral ghost) ------------------------
        hY = 2.0 * U + math.sin(idleP * 1.1) * 0.8 * U
        m.translate(0, hY, 0)
        # Translucent spectral mass
        m.box3d(-3.0, 0, -2.0, 3.0, 4.5 * U, 2.0, DR_TEAL, 0.55)
        # Tendrils hanging below (soul-eating mode)
        for t in range(5):
            ta = t * 1.257 + tickF * 0.6
            tx, tz = 2.5 * math.cos(ta), 2.5 * math.sin(ta)
            tl = 1.5 + 0.8 * math.sin(ta + tickF * 1.2)
            m.box3d(tx - 0.4, -tl * U, tz - 0.4, tx + 0.4, 0.0, tz + 0.4, DR_DEEP, 0.6)
        # Gaping mouth-like opening (soul suction)
        m.box3d(-2.5, 1.5 * U, -2.2, 2.5, 3.0 * U, -1.8, DR_GLOW, 0.5)
        # Soul wisps being absorbed
        sa = tickF * 3.0
        m.cube3(3.0 * math.cos(sa), 2.5 * U, 3.0 * math.sin(sa), 0.35, DR_GLOW, 0.65)
        m.cube3(3.0 * math.cos(sa + 2.094), 2.5 * U, 3.0 * math.sin(sa + 2.094),
                0.35, DR_BONE, 0.6)
        m.cube3(3.0 * math.cos(sa + 4.189), 2.5 * U, 3.0 * math.sin(sa + 4.189),
                0.35, DR_FEL, 0.6)
        # Healing aura ring
        if anim == 2:
            hr = tickF * 2.5
            for p in range(6):
                pa = p * 1.047 + hr
                m.cube3(3.5 * math.cos(pa), 0.0, 3.5 * math.sin(pa), 0.3, DR_GLOW, 0.7)
        # Spine ridge (structural)
        m.box3d(-0.4, 0, -0.4, 0.4, 4.8 * U, 0.4, DR_BONE, 0.7)

    elif idx == 6:
        # -- 6: INFERNAL (Siege -- walking rock golem) -----------------------
        # Four massive stone legs (slow stomper -- no wheels)
        pairA = abs(math.sin(walkP * 1.2)) * U * 0.9 if anim == 1 else 0.0
        pairB = abs(math.sin(walkP * 1.2 + 1.57)) * U * 0.9 if anim == 1 else 0.0
        m.push()
        m.translate(0, pairA, 0)
        m.box3d(-6.0, -pairA, -4.5, -3.0, 4.0 * U, -2.0, DR_STONE)
        m.box3d(3.0, -pairA, -4.5, 6.0, 4.0 * U, -2.0, DR_STONE)
        m.pop()
        m.push()
        m.translate(0, pairB, 0)
        m.box3d(-6.0, -pairB, 2.0, -3.0, 4.0 * U, 4.5, DR_STONE)
        m.box3d(3.0, -pairB, 2.0, 6.0, 4.0 * U, 4.5, DR_STONE)
        m.pop()
        # Massive meteor-like rocky body
        m.box3d(-7.0, 4.0 * U, -6.0, 7.0, 10.0 * U, 6.0, DR_STONE)
        m.box3d(-5.5, 10.0 * U, -5.0, 5.5, 13.0 * U, 5.0, DR_STONE)
        m.box3d(-3.5, 13.0 * U, -3.5, 3.5, 15.0 * U, 3.5, DR_STONE)
        # Fel core glowing through cracks
        felGlow = 1.5 + 0.6 * math.sin(idleP * 2.0)
        m.cube3(0, 7.0 * U, 0, felGlow, DR_GLOW, 0.65)
        m.cube3(0, 7.0 * U, 0, felGlow * 0.6, DR_FEL, 0.6)
        # Crack lines (glowing seams)
        for c in range(4):
            ca = c * 1.57 + 0.785
            cx, cz = 5.0 * math.cos(ca), 5.0 * math.sin(ca)
            m.cube3((cx + cx * 0.4) * 0.5, 6.5 * U, (cz + cz * 0.4) * 0.5,
                    0.4, DR_GLOW, 0.7)
        # Rock fist arms
        if anim == 2:
            atkSwing = math.sin(atkP) * 50.0 - 20.0
        else:
            atkSwing = math.sin(idleP) * 5.0
        m.push()
        m.translate(-7.0, 8.0 * U, 0)
        m.rotate(-20.0 + atkSwing, 1, 0, 0)
        m.box3d(-2.5, -3.0 * U, -2.0, 0.0, 0.0, 2.0, DR_STONE)
        m.box3d(-3.0, -3.5 * U, -2.5, 0.5, -2.8 * U, 2.5, DR_STONE)   # fist
        m.pop()
        m.push()
        m.translate(7.0, 8.0 * U, 0)
        m.rotate(-20.0 - atkSwing, 1, 0, 0)
        m.box3d(0.0, -3.0 * U, -2.0, 2.5, 0.0, 2.0, DR_STONE)
        m.box3d(-0.5, -3.5 * U, -2.5, 3.0, -2.8 * U, 2.5, DR_STONE)
        m.pop()

    else:
        return None     # the C++ answers an unknown unitIdx with `return false`

    m.pop()
    return m.build(**bake)
