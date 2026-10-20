"""Mayan Town Hall -- "Tikal Pyramid" (RACE_MAYAN, bldgIdx 0).

Port of drawMayanBldg3D in src/gfx/models3d/mayan_hero.cpp, C++ numbers
verbatim. The first building ported, and it exercises the same primitives as
the heroes -- box3d, cube3, wisp3 -- so the translator needed nothing new.

Stepped Maya temple-pyramid: 5 tapering limestone tiers streaked with jade
moss, a twin balustrade stairway up the front (+Z) face, and a roof-comb
shrine at the summit with a glowing jade capstone.
"""

import math

from claude_studio.craftwar_gl import U, GLModel

STONE = 0xD08858      # red-ochre plaster
STONE_D = 0x582410    # deep shadow riser
STAIR = 0xEDE0C0      # pale limestone stairway ramp
MOSS = 0x1E5A28       # jade moss streaking
COMB = 0x703018       # roof-comb / shrine stone
GOLD = 0xE8A820       # bright copper-gold shrine trim
JADE_LT = 0x30E0A0    # glowing jade capstone


def build(tickF=0.0, anim=0, name="MAYAN_bldg", **bake):
    """anim is accepted and ignored, as in the C++ -- buildings have no
    animation state. **bake is forwarded to GLModel.build()."""
    idleP = tickF * 0.9
    m = GLModel(name)

    # Sun-baked red-ochre plaster, not bare grey stone -- real Maya temples
    # were painted, and the colour pop reads far better against jungle green
    # at map-decor scale.
    #
    # No Y-rotation: the compositing camera uses a fixed -33 deg X tilt and no
    # Y spin, so a Y-rotated model would show the front stairway as an oblique
    # sliver instead of facing the viewer head-on.
    TIERS = 5
    w0, tierH, riser = 15.0, 3.4 * U, 0.6
    y = 0.0
    for t in range(TIERS):
        w = w0 - t * 2.6
        m.box3d(-w, y, -w, w, y + tierH, w, STONE, 1.0 - t * 0.05)
        # Dark riser band at the foot of each tier -- box3d's own face shading
        # alone was too subtle at this scale to read as "stepped".
        m.box3d(-w, y, -w, w, y + riser, w, STONE_D, 0.9)
        mossA = 0.42 - t * 0.06
        if mossA > 0.0:
            m.box3d(-w * 0.75, y, w - 0.1, -w * 0.4, y + tierH * 0.75, w + 0.3,
                    MOSS, mossA)
            m.box3d(w * 0.4, y, w - 0.1, w * 0.75, y + tierH * 0.75, w + 0.3,
                    MOSS, mossA)
        y += tierH

    # Single continuous stairway ramp up the front (+Z) face -- pale limestone
    # against the red body, dark rails either side.
    stairHalfW, stairY = 3.6, 0.0
    for t in range(TIERS):
        w = w0 - t * 2.6
        m.box3d(-stairHalfW - 0.9, stairY, w - 0.2, -stairHalfW, stairY + tierH,
                w + 1.2, STONE_D, 0.85)      # left rail
        m.box3d(stairHalfW, stairY, w - 0.2, stairHalfW + 0.9, stairY + tierH,
                w + 1.2, STONE_D, 0.85)      # right rail
        m.box3d(-stairHalfW, stairY, w + 0.1, stairHalfW, stairY + tierH,
                w + 1.0, STAIR, 0.95)        # ramp tread
        stairY += tierH

    # Shrine / roof comb at the summit
    sw = w0 - (TIERS - 1) * 2.6
    m.box3d(-sw * 0.75, y, -sw * 0.75, sw * 0.75, y + 3.6 * U, sw * 0.75, COMB, 1.0)
    m.box3d(-sw * 0.2, y + 3.6 * U, -1.2, sw * 0.2, y + 7.0 * U, 1.2, COMB, 1.1)
    m.box3d(-sw * 0.6, y + 0.4 * U, sw * 0.75, sw * 0.6, y + 2.6 * U,
            sw * 0.75 + 0.3, GOLD, 0.55)     # doorway glow trim
    capPulse = 0.7 + 0.35 * math.sin(idleP)
    m.cube3(0.0, y + 7.4 * U, 0.0, 1.0, JADE_LT, capPulse)          # jade capstone
    m.wisp3(0.0, y + 7.6 * U, 0.0, 3.0, JADE_LT, 0.35 * capPulse)   # soft glow halo

    return m.build(**bake)
