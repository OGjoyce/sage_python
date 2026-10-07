"""
undead_ai_animations.py -- five short action clips for the Undead AI
character, sharing one rig (claude_studio.rig) and one render harness.

    blender -b --python studio/scenes/undead_ai_animations.py -- \
        --anim attack --frames-dir /tmp/out --samples 32 --res 640 720

--anim one of: attack, walk, talk, taunt, ultimate

All five animate at the rigid-object level (see rig.py's docstring for
why: characters.py joins each sub-assembly into one mesh, so there is no
per-vertex skeleton to deform, only whole parts -- Torso, Head, LeftArm,
RightArm, HoverBase -- that can rotate/translate as rigid pieces around a
chosen pivot). That is enough for all five of these: none of them need a
part to bend partway along its own length, only to move and rotate as a
whole relative to its parent.
"""

import argparse
import colorsys
import math
import os
import sys

STUDIO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, STUDIO_DIR)

import bpy  # noqa: E402
import mathutils  # noqa: E402
import claude_studio as cs  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import undead_ai_scene as base_scene  # noqa: E402

from claude_studio.rig import keyframe_pose, bake_sword_to_hand, RIGHT_CLAW_LOCAL  # noqa: E402


# ------------------------------------------------------------- helpers ----

def hsv_rgba(h, s=1.0, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def keyframe_emission(bsdf, frame, color=None, strength=None, interpolation='LINEAR'):
    ecol = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
    estr = bsdf.inputs.get("Emission Strength")
    bpy.context.scene.frame_set(frame)
    if color is not None and ecol is not None:
        ecol.default_value = color
        ecol.keyframe_insert(data_path="default_value", frame=frame)
    if strength is not None and estr is not None:
        estr.default_value = strength
        estr.keyframe_insert(data_path="default_value", frame=frame)
    for sock in (ecol, estr):
        if sock is None or not sock.id_data.animation_data:
            continue
        for fc in sock.id_data.animation_data.action.fcurves:
            if fc.keyframe_points:
                kp = fc.keyframe_points[-1]
                if round(kp.co.x) == frame:
                    kp.interpolation = interpolation


def set_interp(obj, interpolation='BEZIER', easing='EASE_IN_OUT'):
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = interpolation
                kp.easing = easing


def add_burst(name, location, mat, radius=0.08, vertices=10):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=radius, location=location, subdivisions=1)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    obj.modifiers.new("Triangulate", "TRIANGULATE")
    return obj


# ------------------------------------------------------------ 1. attack ---

def pose_attack(parts, mats):
    torso, head = parts["Torso"], parts["Head"]
    left_arm, right_arm, hover = parts["LeftArm"], parts["RightArm"], parts["HoverBase"]
    sword = parts["GreatSword"]

    arm_keys = [
        (0, 0.0), (22, 92.0), (30, 98.0), (36, 98.0),
        (54, -62.0), (66, -62.0), (86, 98.0), (92, 98.0), (108, 0.0),
    ]
    for f, deg in arm_keys:
        keyframe_pose(right_arm, f, rotation_deg=(deg, 0, 0))

    # left arm counter-swings for balance, opposite phase to the right
    left_keys = [
        (0, 0.0), (22, -18.0), (36, -18.0), (54, 14.0), (66, 14.0), (86, -18.0), (108, 0.0),
    ]
    for f, deg in left_keys:
        keyframe_pose(left_arm, f, rotation_deg=(deg, 0, 0))

    # torso: windup twist away from the swing, snap through on impact,
    # with a forward lean (local X) at the moment of commitment
    torso_keys = [
        (0, (0.0, 0.0, 0.0)), (22, (0.0, -14.0, 0.0)), (36, (0.0, -14.0, 0.0)),
        (54, (8.0, 18.0, 0.0)), (66, (8.0, 18.0, 0.0)),
        (86, (0.0, -10.0, 0.0)), (108, (0.0, 0.0, 0.0)),
    ]
    for f, (rx, ry, rz) in torso_keys:
        keyframe_pose(torso, f, rotation_deg=(rx, ry, rz))

    head_keys = [(0, 0.0), (36, 8.0), (54, -6.0), (66, -6.0), (108, 0.0)]
    for f, deg in head_keys:
        keyframe_pose(head, f, rotation_deg=(0, deg, 0))

    hover_keys = [(0, 0.0), (22, -4.0), (54, 6.0), (66, 6.0), (108, 0.0)]
    for f, deg in hover_keys:
        keyframe_pose(hover, f, rotation_deg=(0, 0, deg))

    for obj in (torso, head, left_arm, right_arm, hover):
        set_interp(obj)

    bake_sword_to_hand(sword, right_arm, range(0, 109), grab_blend=26, grab_start=30,
                        sheathe_start=88, sheathe_blend=92)
    return 108


# -------------------------------------------------------------- 2. walk ---

def pose_walk(parts, mats, root):
    hover = parts["HoverBase"]
    legs = [
        (0, (0, 0, 0), 0.0),
        (28, (0, 0, 2.2), -10.0),     # drift forward (+Z), lean back (away from travel)
        (40, (0, 0, 2.2), -10.0),
        (56, (0, 0, 0.0), 0.0),
        (70, (0, 0, -2.0), 9.0),      # drift back (-Z), lean forward
        (82, (0, 0, -2.0), 9.0),
        (96, (0, 0, 0.0), 0.0),
        (110, (2.0, 0, 0), 0.0),      # strafe +X, lean away (-Z tilt around local Z axis -> roll)
        (122, (2.0, 0, 0), 0.0),
        (136, (0, 0, 0), 0.0),
    ]
    # root carries translation; hover_base carries the lean (rotation) and
    # a continuous small bob so it reads as floating, not sliding
    for f, loc, lean_x in legs:
        keyframe_pose(root, f, location=loc)
    for f, loc, lean_x in legs:
        bpy.context.scene.frame_set(f)
        hover.rotation_euler = (math.radians(lean_x), 0, 0)
        hover.keyframe_insert(data_path="rotation_euler", frame=f)
    # roll lean for the strafe segment (110-122): lean away from travel
    # direction (+X) means tilting around local Z
    bpy.context.scene.frame_set(110)
    hover.rotation_euler = (0, 0, math.radians(-8.0))
    hover.keyframe_insert(data_path="rotation_euler", frame=110)
    bpy.context.scene.frame_set(122)
    hover.rotation_euler = (0, 0, math.radians(-8.0))
    hover.keyframe_insert(data_path="rotation_euler", frame=122)

    set_interp(root)
    set_interp(hover)

    # gentle continuous float bob on top of the lean, baked every frame so
    # it layers on regardless of the lean keys above
    total = legs[-1][0]
    base_y = hover.location.y
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for f in range(0, total + 1):
        bpy.context.scene.frame_set(f)
        depsgraph.update()
        bob = 0.06 * math.sin(f * 0.35)
        hover.location = (hover.location.x, base_y + bob, hover.location.z)
        hover.keyframe_insert(data_path="location", frame=f)
    set_interp(hover, interpolation='LINEAR', easing='AUTO')
    return total


# -------------------------------------------------------------- 3. talk ---

def pose_talk(parts, mats):
    head = parts["Head"]
    mouth_bsdf = mats["DARK_GREEN"].node_tree.nodes.get("Principled BSDF")
    base_strength = 3.0

    nod_keys = [(0, 0.0), (10, 3.0), (20, -1.5), (30, 2.0), (40, 0.0),
                (50, 2.5), (60, -1.0), (70, 1.5), (80, 0.0)]
    for f, deg in nod_keys:
        keyframe_pose(head, f, rotation_deg=(deg, 0, 0))
    set_interp(head)

    # mouth glow "talks" -- rapid irregular pulses, like a VU meter, not a
    # clean sine (two mismatched periods summed, same trick as the
    # OpenGL viewer's real-time flicker shader)
    total = 80
    for f in range(0, total + 1):
        t = f / 24.0
        pulse = 0.5 + 0.5 * math.sin(t * 14.0) * math.sin(t * 5.3 + 1.0)
        keyframe_emission(mouth_bsdf, f, strength=base_strength * (0.3 + 0.9 * max(pulse, 0)))
    return total


# ------------------------------------------------------------- 4. taunt ---

def pose_taunt(parts, mats):
    head = parts["Head"]
    live_bsdf = mats["LIVE_GREEN"].node_tree.nodes.get("Principled BSDF")
    dark_bsdf = mats["DARK_GREEN"].node_tree.nodes.get("Principled BSDF")

    total = 96
    # full 360 head spin, linear for constant speed
    keyframe_pose(head, 0, rotation_deg=(0, 0, 0))
    keyframe_pose(head, total, rotation_deg=(0, 360, 0))
    set_interp(head, interpolation='LINEAR', easing='AUTO')

    # a little chest-puff bob so the taunt doesn't read as just a head spin
    torso = parts["Torso"]
    for f, dz in ((0, 0.0), (24, 4.0), (48, 0.0), (72, -3.0), (96, 0.0)):
        keyframe_pose(torso, f, rotation_deg=(0, 0, dz))
    set_interp(torso)

    # RGB cycle on the two LED materials (LIVE_GREEN/DARK_GREEN are
    # shared across chest LEDs, eyes, and joint rings, so the whole body
    # flashes through the cycle -- a bold, deliberately over-the-top taunt
    # read rather than isolating just the chest row)
    n_steps = 16
    for i in range(n_steps + 1):
        f = int(i * total / n_steps)
        hue = (i / n_steps) % 1.0
        keyframe_emission(live_bsdf, f, color=hsv_rgba(hue, 0.85, 1.0), strength=6.0)
        keyframe_emission(dark_bsdf, f, color=hsv_rgba((hue + 0.5) % 1.0, 0.85, 1.0), strength=3.0)
    return total


# ---------------------------------------------------------- 5. ultimate ---

def pose_ultimate(parts, mats):
    torso, head = parts["Torso"], parts["Head"]
    right_arm, hover = parts["RightArm"], parts["HoverBase"]
    sword = parts["GreatSword"]
    corrupt_bsdf = mats["CORRUPT"].node_tree.nodes.get("Principled BSDF")
    beacon_bsdf = mats["BEACON"].node_tree.nodes.get("Principled BSDF")

    GRAB_BLEND, GRAB, RAISE, CHARGE_START, CHARGE_END, BURST, SETTLE_START, TOTAL = \
        20, 24, 44, 46, 86, 90, 96, 116

    # reach back, grab, then raise straight overhead (shoulder rotation
    # past vertical) and hold through the charge
    arm_keys = [
        (0, 0.0), (GRAB, 98.0), (RAISE, 178.0), (CHARGE_END, 178.0),
        (BURST, 170.0), (SETTLE_START, 98.0), (TOTAL, 0.0),
    ]
    for f, deg in arm_keys:
        keyframe_pose(right_arm, f, rotation_deg=(deg, 0, 0))
    set_interp(right_arm)

    # torso leans back under the raised sword, straining through the charge
    torso_keys = [
        (0, 0.0), (RAISE, -14.0), (CHARGE_END, -16.0), (BURST, -10.0),
        (SETTLE_START, -4.0), (TOTAL, 0.0),
    ]
    for f, rx in torso_keys:
        keyframe_pose(torso, f, rotation_deg=(rx, 0, 0))
    set_interp(torso)

    head_keys = [(0, 0.0), (RAISE, -10.0), (CHARGE_END, -10.0), (TOTAL, 0.0)]
    for f, rx in head_keys:
        keyframe_pose(head, f, rotation_deg=(rx, 0, 0))
    set_interp(head)

    bake_sword_to_hand(sword, right_arm, range(0, TOTAL + 1), grab_blend=GRAB_BLEND, grab_start=GRAB,
                        sheathe_start=SETTLE_START, sheathe_blend=SETTLE_START + 6)

    # charge: a jittery jittered jitter? -- small rapid shake on the hover
    # base (the only thing not already carrying the arm's own motion),
    # plus the corrupt aura and beacon intensifying
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for f in range(RAISE, CHARGE_END + 1):
        bpy.context.scene.frame_set(f)
        depsgraph.update()
        jitter = 0.035 * math.sin(f * 2.7) * math.sin(f * 0.9)
        hover.rotation_euler = (0, 0, jitter)
        hover.keyframe_insert(data_path="rotation_euler", frame=f)
        t = (f - RAISE) / max(1, (CHARGE_END - RAISE))
        keyframe_emission(corrupt_bsdf, f, strength=14.0 + 50.0 * t)
        keyframe_emission(beacon_bsdf, f, strength=8.0 + 18.0 * t)
    keyframe_pose(hover, 0, rotation_deg=(0, 0, 0))
    keyframe_pose(hover, SETTLE_START, rotation_deg=(0, 0, 0))
    keyframe_pose(hover, TOTAL, rotation_deg=(0, 0, 0))
    set_interp(hover)
    keyframe_emission(corrupt_bsdf, 0, strength=14.0)
    keyframe_emission(beacon_bsdf, 0, strength=8.0)
    keyframe_emission(corrupt_bsdf, SETTLE_START, strength=14.0)
    keyframe_emission(beacon_bsdf, SETTLE_START, strength=8.0)
    keyframe_emission(corrupt_bsdf, TOTAL, strength=14.0)
    keyframe_emission(beacon_bsdf, TOTAL, strength=8.0)

    # the burst itself: a small cluster of ico-spheres at the sword tip,
    # scaling from nothing to a bright flash and back down over ~10 frames
    depsgraph.update()
    eval_sword = sword.evaluated_get(depsgraph)
    tip_world = eval_sword.matrix_world @ mathutils.Vector((0.0, 2.5, 0.0))
    burst_objs = []
    for i in range(5):
        ang = i / 5 * 2 * math.pi
        off = mathutils.Vector((0.18 * math.cos(ang), 0.05 * i, 0.18 * math.sin(ang)))
        b = add_burst(f"Burst_{i}", tip_world + off, mats["CORRUPT"], radius=0.05 + 0.02 * i)
        burst_objs.append(b)
    for b in burst_objs:
        for f, scale in ((0, 0.0), (BURST, 0.0), (BURST + 3, 1.0), (BURST + 6, 1.6), (BURST + 14, 0.0)):
            bpy.context.scene.frame_set(f)
            b.scale = (scale, scale, scale)
            b.keyframe_insert(data_path="scale", frame=f)
        set_interp(b, interpolation='LINEAR', easing='AUTO')

    return TOTAL


# ------------------------------------------------------------------ main --

ANIM_TABLE = {
    "attack": lambda parts, mats, root: pose_attack(parts, mats),
    "walk": lambda parts, mats, root: pose_walk(parts, mats, root),
    "talk": lambda parts, mats, root: pose_talk(parts, mats),
    "taunt": lambda parts, mats, root: pose_taunt(parts, mats),
    "ultimate": lambda parts, mats, root: pose_ultimate(parts, mats),
}

CAMERAS = {
    "attack": dict(location=(5.6, 2.8, 5.4), target=(0.3, 2.5, -0.3), lens=38),
    "walk": dict(location=(0.5, 2.9, 9.5), target=(0.5, 2.4, 0.0), lens=32),
    "talk": dict(location=(0.0, 4.9, 3.6), target=(0.0, 4.3, 0.0), lens=42),
    "taunt": dict(location=(0.0, 3.2, 7.2), target=(0.0, 3.0, 0.0), lens=36),
    "ultimate": dict(location=(4.8, 3.0, 6.4), target=(0.0, 3.4, 0.0), lens=34),
}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--anim", required=True, choices=list(ANIM_TABLE.keys()))
    p.add_argument("--frames-dir", required=True)
    p.add_argument("--samples", type=int, default=32)
    p.add_argument("--res", type=int, nargs=2, default=(640, 720))
    p.add_argument("--fps", type=int, default=24)
    return p.parse_args(argv)


def main():
    args = parse_args()
    cs.scene.reset_scene()

    root, parts, tri_count = cs.characters.build_undead_ai(cs.materials)
    cs.rig.build_character_rig(parts)

    base_scene.build_presentation_lighting()
    base_scene.setup_glare_compositor()
    cam = CAMERAS[args.anim]
    cs.scene.add_camera(location=cam["location"], target=cam["target"], lens=cam["lens"])

    # the materials dict isn't returned by build_undead_ai, but every
    # material it creates is still in bpy.data.materials by name
    mats = {
        "LIVE_GREEN": bpy.data.materials["MAT_LIVE_GREEN"],
        "DARK_GREEN": bpy.data.materials["MAT_DARK_GREEN"],
        "CORRUPT": bpy.data.materials["MAT_CORRUPT"],
        "BEACON": bpy.data.materials["MAT_BEACON"],
    }

    total_frames = ANIM_TABLE[args.anim](parts, mats, root)

    scene = bpy.context.scene
    scene.frame_start = 0
    scene.frame_end = total_frames
    scene.render.fps = args.fps
    bpy.context.scene.frame_set(0)

    os.makedirs(args.frames_dir, exist_ok=True)
    cs.render.configure_render(
        engine="CYCLES", samples=args.samples, resolution=tuple(args.res), denoise=False,
        filepath=os.path.join(args.frames_dir, "f_"), view_transform="Standard",
    )
    scene.render.image_settings.file_format = "PNG"

    bpy.ops.render.render(animation=True)
    print(f"STUDIO: rendered {total_frames + 1} frames ({args.anim}) to {args.frames_dir}")


if __name__ == "__main__":
    main()
