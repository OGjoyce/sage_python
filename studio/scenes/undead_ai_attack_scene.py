"""
undead_ai_attack_scene.py -- a short action clip: the damaged (right,
cabled) arm reaches back, draws the back-mounted Great Sword, swings an
attack, holds the pose, then sheathes the sword again.

The rig here is intentionally simple -- a single rigid RightArm object
(shoulder box through claw, as already built by characters.py) pivoting
only at the shoulder, not a multi-bone IK chain. characters.py joins
every arm part into one mesh per side, so there is no existing per-joint
skeleton to animate; building one (real bones, skin weights, a
deform rig) is a much larger undertaking than this clip calls for. A
shoulder-pivot swing reads clearly as "reach / draw / swing / sheathe"
without it.

The sword is NOT parented to the hand (animated Blender parenting can't
be keyframed mid-clip without constraint tricks). Instead its transform
is baked frame-by-frame: outside the "grabbed" window it holds the
static back-mounted (strap) transform; inside that window its location
and rotation are computed each frame from the RightArm object's
evaluated world matrix (via the depsgraph, so it already reflects
Blender's own interpolation of the arm's keyframes) plus a fixed local
grip offset, so the blade tracks the claw. Short blend windows at the
grab/sheathe boundaries slerp between the two so the sword doesn't pop.

Run with:
    blender -b --python studio/scenes/undead_ai_attack_scene.py -- \
        --frames-dir /tmp/attack_frames --samples 32 --res 640 720
"""

import argparse
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


# ---------------------------------------------------------------- pose ----
# (frame, shoulder X-rotation in degrees). Blender interpolates between
# these (default bezier) when the arm's rotation_euler is keyframed at
# just these frames.
ARM_POSE_KEYS = [
    (0,   0.0),    # rest, hanging at the side
    (22,  92.0),   # reach back/up toward the hilt
    (30,  98.0),   # at the hilt -- grab
    (36,  98.0),   # brief hold (grip confirmed)
    (54, -62.0),   # swing through and down -- attack impact
    (66, -62.0),   # hold the extended attack pose
    (86,  98.0),   # swing back up to the sheathe point
    (92,  98.0),   # hold at the sheathe point
    (108,  0.0),   # settle back to rest
]
TOTAL_FRAMES = ARM_POSE_KEYS[-1][0]

# sword "grabbed" window, with short blend ramps at each edge so the
# sword doesn't pop between its static strap transform and the
# hand-tracked one
GRAB_BLEND_START = 26
GRAB_START = 30
SHEATHE_START = 88
SHEATHE_BLEND_END = 92

SHOULDER_PIVOT = mathutils.Vector((1.04, 3.35, 0.0))
CLAW_LOCAL = mathutils.Vector((1.04 * 1.14 - 1.04, 1.68 - 3.35, 0.0))  # claw, relative to shoulder pivot
GRIP_LOCAL_ON_SWORD = mathutils.Vector((0.0, -0.45, 0.0))  # mid-handle, in the sword's own local space

SWORD_REST_LOC = mathutils.Vector((0.45, 2.85, -0.55))
SWORD_REST_ROT = mathutils.Euler((0.0, 0.0, math.radians(118)), 'XYZ')


def set_origin_to(obj, world_point):
    cursor = bpy.context.scene.cursor
    old_cursor = cursor.location.copy()
    cursor.location = world_point
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    cursor.location = old_cursor


def sword_held_transform(arm_obj, depsgraph):
    """World (location, rotation_euler) for the sword, tracking the claw
    at the arm's CURRENT evaluated pose."""
    eval_arm = arm_obj.evaluated_get(depsgraph)
    claw_world = eval_arm.matrix_world @ CLAW_LOCAL
    # the arm only ever rotates about local X (see ARM_POSE_KEYS), so its
    # own current X angle plus 180 degrees points the sword's local +Y
    # (blade) the same way the forearm points (continuing the arm's line,
    # blade out past the fist) -- see the module docstring's grip-offset
    # derivation.
    arm_x = arm_obj.rotation_euler.x
    sword_rot = mathutils.Euler((arm_x + math.pi, 0.0, 0.0), 'XYZ')
    sword_loc = claw_world - (sword_rot.to_matrix() @ GRIP_LOCAL_ON_SWORD)
    return sword_loc, sword_rot


def bake_sword_keyframes(sword_obj, arm_obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rest_quat = SWORD_REST_ROT.to_quaternion()
    for f in range(0, TOTAL_FRAMES + 1):
        bpy.context.scene.frame_set(f)
        depsgraph.update()

        if f <= GRAB_BLEND_START or f >= SHEATHE_BLEND_END:
            loc, rot = SWORD_REST_LOC, SWORD_REST_ROT
        elif GRAB_BLEND_START < f < GRAB_START:
            t = (f - GRAB_BLEND_START) / (GRAB_START - GRAB_BLEND_START)
            held_loc, held_rot = sword_held_transform(arm_obj, depsgraph)
            loc = SWORD_REST_LOC.lerp(held_loc, t)
            rot = rest_quat.slerp(held_rot.to_quaternion(), t).to_euler('XYZ')
        elif SHEATHE_START < f < SHEATHE_BLEND_END:
            t = (f - SHEATHE_START) / (SHEATHE_BLEND_END - SHEATHE_START)
            held_loc, held_rot = sword_held_transform(arm_obj, depsgraph)
            loc = held_loc.lerp(SWORD_REST_LOC, t)
            rot = held_rot.to_quaternion().slerp(rest_quat, t).to_euler('XYZ')
        else:
            loc, rot = sword_held_transform(arm_obj, depsgraph)

        sword_obj.location = loc
        sword_obj.rotation_euler = rot
        sword_obj.keyframe_insert(data_path="location", frame=f)
        sword_obj.keyframe_insert(data_path="rotation_euler", frame=f)


def build_rig_and_animation(parts):
    arm_obj = parts["RightArm"]
    sword_obj = parts["GreatSword"]

    set_origin_to(arm_obj, SHOULDER_PIVOT)

    arm_obj.rotation_mode = 'XYZ'
    for frame, deg in ARM_POSE_KEYS:
        bpy.context.scene.frame_set(frame)
        arm_obj.rotation_euler = (math.radians(deg), 0.0, 0.0)
        arm_obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    for fc in arm_obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'EASE_IN_OUT'

    sword_obj.rotation_mode = 'XYZ'
    bake_sword_keyframes(sword_obj, arm_obj)
    for fc in sword_obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

    bpy.context.scene.frame_set(0)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--frames-dir", required=True)
    p.add_argument("--samples", type=int, default=32)
    p.add_argument("--res", type=int, nargs=2, default=(640, 720))
    p.add_argument("--fps", type=int, default=24)
    return p.parse_args(argv)


def main():
    args = parse_args()
    cs.scene.reset_scene()

    root, parts, tri_count = cs.characters.build_undead_ai(cs.materials)
    base_scene.build_presentation_lighting()
    base_scene.setup_glare_compositor()

    build_rig_and_animation(parts)

    cs.scene.add_camera(location=(5.6, 2.8, 5.4), target=(0.3, 2.5, -0.3), lens=38)

    scene = bpy.context.scene
    scene.frame_start = 0
    scene.frame_end = TOTAL_FRAMES
    scene.render.fps = args.fps

    os.makedirs(args.frames_dir, exist_ok=True)
    cs.render.configure_render(
        engine="CYCLES", samples=args.samples, resolution=tuple(args.res), denoise=False,
        filepath=os.path.join(args.frames_dir, "f_"), view_transform="Standard",
    )
    scene.render.image_settings.file_format = "PNG"

    bpy.ops.render.render(animation=True)
    print(f"STUDIO: rendered {TOTAL_FRAMES + 1} frames to {args.frames_dir}")


if __name__ == "__main__":
    main()
