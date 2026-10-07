"""
rig.py -- turns the flat parts dict from characters.build_undead_ai()
(every part parented directly to one root empty, nothing parented to
anything else) into a real hierarchy suitable for keyframe animation,
plus the shared "sword tracks the gripping hand" bake used by any
animation where the Great Sword is drawn (attack, ultimate, ...).

characters.py joins every sub-assembly's own parts into one mesh per
assembly (TorsoMain + chest panel + rivets + ... all become one "Torso"
object, etc.) -- there is no per-vertex skeleton, no bone weights. This
module animates at the RIGID-OBJECT level: each named part (Torso, Head,
LeftArm, RightArm, ...) is one rigid piece that rotates/translates as a
whole around a chosen pivot. That's enough for the kind of broad,
readable motion a low-poly action-game character needs (reach, swing,
lean, nod, spin) -- it will never bend a torso or curl a spine. A true
deforming rig (armature + vertex groups) would need re-building every
part as a single skinned mesh instead of many joined rigid pieces, which
is a much larger change than animating what's already here.
"""

import math

import bpy
import mathutils


# ----------------------------------------------------------- hierarchy ----
# (child, parent, pivot_world) -- pivot_world is where that child's local
# origin is moved to (via the 3D cursor technique) before parenting, so
# rotating it swings around the right joint instead of its mesh's
# geometric bounding-box center.
HOVER_BASE_PIVOT = mathutils.Vector((0.0, 0.10, 0.0))
TORSO_PIVOT = mathutils.Vector((0.0, 1.70, 0.0))          # waist, where it meets the spine
HEAD_PIVOT = mathutils.Vector((0.0, 4.05, 0.0))           # neck base
LEFT_SHOULDER_PIVOT = mathutils.Vector((-1.04, 3.35, 0.0))
RIGHT_SHOULDER_PIVOT = mathutils.Vector((1.04, 3.35, 0.0))

RIGHT_CLAW_LOCAL = mathutils.Vector((1.04 * 1.14 - 1.04, 1.68 - 3.35, 0.0))
LEFT_PALM_LOCAL = mathutils.Vector((-(1.04 * 1.16 - 1.04), 1.76 - 3.35, 0.0))

SWORD_REST_LOC = mathutils.Vector((0.45, 2.85, -0.55))
SWORD_REST_ROT = mathutils.Euler((0.0, 0.0, math.radians(118)), 'XYZ')
SWORD_GRIP_LOCAL = mathutils.Vector((0.0, -0.45, 0.0))  # mid-handle, in the sword's own local space


def _set_origin(obj, world_point):
    cursor = bpy.context.scene.cursor
    old = cursor.location.copy()
    cursor.location = world_point
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    cursor.location = old


def _normalize_rotation(obj):
    """Bakes any existing object-level rotation into the mesh data and
    resets rotation_euler to identity, keeping the exact same world
    appearance.

    characters.py's join_parts() keeps parts[0]'s own object-level
    rotation on the combined object (joining copies the OTHER parts'
    geometry into parts[0]'s mesh, accounting for their relative
    rotation, but never touches parts[0]'s own transform) -- and
    HoverBase's first part is a tier built with rotation=(90, 0, 0), so
    HoverBase's rotation_euler is secretly (90, 0, 0) at "rest", not
    (0, 0, 0). Every animation in this module assumes rotation_euler=0
    means the rest pose; keyframing a pose like (0, 0, tilt_deg) would
    silently replace that load-bearing 90-degree rotation instead of
    adding to it, scrambling the whole part's orientation the moment it
    got its first keyframe. Run for all five pivoted parts, defensively,
    not just HoverBase -- any future change to which part ends up first
    in a join_parts() call could introduce the same trap elsewhere."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)


def _parent_keep_transform(child, parent):
    bpy.ops.object.select_all(action="DESELECT")
    child.select_set(True)
    parent.select_set(True)
    bpy.context.view_layer.objects.active = parent
    bpy.ops.object.parent_set(type="OBJECT", keep_transform=True)


def build_character_rig(parts):
    """Re-parents the flat parts dict into:

        root
         |- HoverBase (pivot: own center)
             |- LowerSpine
             |- Torso (pivot: waist)
                 |- Neck
                 |- Head (pivot: neck base)
                 |- LeftArm (pivot: left shoulder)
                 |- RightArm (pivot: right shoulder)
                 |- GreatSword, StrapTop/Bottom, StrapBuckleTop/Bottom

    Every part keeps its current world-space position/rotation (parented
    with keep_transform=True), so calling this right after
    build_undead_ai() changes nothing about how the character looks --
    only what moves what. Returns the same pivot points used, in case a
    caller wants to rotate something around the same joint by hand.
    """
    hover = parts["HoverBase"]
    torso = parts["Torso"]
    head = parts["Head"]
    left_arm = parts["LeftArm"]
    right_arm = parts["RightArm"]

    _set_origin(hover, HOVER_BASE_PIVOT)
    _set_origin(torso, TORSO_PIVOT)
    _set_origin(head, HEAD_PIVOT)
    _set_origin(left_arm, LEFT_SHOULDER_PIVOT)
    _set_origin(right_arm, RIGHT_SHOULDER_PIVOT)

    for obj in (hover, torso, head, left_arm, right_arm):
        _normalize_rotation(obj)

    _parent_keep_transform(parts["LowerSpine"], hover)
    _parent_keep_transform(torso, hover)
    _parent_keep_transform(parts["Neck"], torso)
    _parent_keep_transform(head, torso)
    _parent_keep_transform(left_arm, torso)
    _parent_keep_transform(right_arm, torso)
    for key in ("GreatSword", "StrapTop", "StrapBottom", "StrapBuckleTop", "StrapBuckleBottom"):
        _parent_keep_transform(parts[key], torso)

    for obj in (hover, torso, head, left_arm, right_arm):
        obj.rotation_mode = 'XYZ'

    return {
        "hover_base": HOVER_BASE_PIVOT, "torso": TORSO_PIVOT, "head": HEAD_PIVOT,
        "left_shoulder": LEFT_SHOULDER_PIVOT, "right_shoulder": RIGHT_SHOULDER_PIVOT,
    }


# -------------------------------------------------- sword hand-tracking ----

def sword_grip_transform(arm_obj, claw_local, depsgraph):
    """World (location, rotation_euler) for the sword gripped in
    `arm_obj`'s hand, using the arm's full evaluated world matrix (not
    just one local axis) -- correct even when the arm's parent (the
    torso) is itself rotating, which a single-axis shortcut isn't."""
    eval_arm = arm_obj.evaluated_get(depsgraph)
    world_matrix = eval_arm.matrix_world
    claw_world = world_matrix @ claw_local

    # the sword's local +Y (blade) should point the same way the arm's
    # own local -Y does (continuing the forearm's line, blade out past
    # the fist) -- that's the arm's world rotation composed with a
    # 180-degree flip around local X (maps local -Y -> +Y, -Z -> +Z).
    flip = mathutils.Matrix.Rotation(math.pi, 3, 'X')
    sword_rot_mat = world_matrix.to_3x3() @ flip
    sword_rot = sword_rot_mat.to_euler('XYZ')
    sword_loc = claw_world - (sword_rot_mat @ SWORD_GRIP_LOCAL)
    return sword_loc, sword_rot


def bake_sword_to_hand(sword_obj, arm_obj, frame_range, grab_blend, grab_start, sheathe_start, sheathe_blend,
                        claw_local=RIGHT_CLAW_LOCAL):
    """Keyframes the sword every frame in `frame_range` (an iterable of
    ints): the static SWORD_REST transform outside [grab_blend,
    sheathe_blend], a quaternion-slerped blend in the short ramps, and
    the hand-tracked transform (via sword_grip_transform) in between."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rest_quat = SWORD_REST_ROT.to_quaternion()
    sword_obj.rotation_mode = 'XYZ'
    for f in frame_range:
        bpy.context.scene.frame_set(f)
        depsgraph.update()

        if f <= grab_blend or f >= sheathe_blend:
            loc, rot = SWORD_REST_LOC, SWORD_REST_ROT
        elif grab_blend < f < grab_start:
            t = (f - grab_blend) / (grab_start - grab_blend)
            held_loc, held_rot = sword_grip_transform(arm_obj, claw_local, depsgraph)
            loc = SWORD_REST_LOC.lerp(held_loc, t)
            rot = rest_quat.slerp(held_rot.to_quaternion(), t).to_euler('XYZ')
        elif sheathe_start < f < sheathe_blend:
            t = (f - sheathe_start) / (sheathe_blend - sheathe_start)
            held_loc, held_rot = sword_grip_transform(arm_obj, claw_local, depsgraph)
            loc = held_loc.lerp(SWORD_REST_LOC, t)
            rot = held_rot.to_quaternion().slerp(rest_quat, t).to_euler('XYZ')
        else:
            loc, rot = sword_grip_transform(arm_obj, claw_local, depsgraph)

        sword_obj.location = loc
        sword_obj.rotation_euler = rot
        sword_obj.keyframe_insert(data_path="location", frame=f)
        sword_obj.keyframe_insert(data_path="rotation_euler", frame=f)


def keyframe_pose(obj, frame, rotation_deg=None, location=None, interpolation='BEZIER', easing='EASE_IN_OUT'):
    """Sets obj's rotation_euler (degrees, XYZ tuple) and/or local
    location at `frame` and inserts keyframes, tagging the newly-added
    keys with the given interpolation/easing (defaults match Blender's
    own default curve, just explicit).

    Order matters here: the scene frame must move FIRST, before the new
    value is written. Once an object has even one existing keyframe,
    frame_set() re-evaluates its f-curves and writes the interpolated
    result back into the object's real properties (not just an evaluated
    depsgraph copy) -- setting the property first and only then calling
    frame_set() throws that value away and keyframes whatever the
    existing curve already held at that frame instead, silently
    collapsing every pose after the first to the same value."""
    bpy.context.scene.frame_set(frame)
    if rotation_deg is not None:
        obj.rotation_euler = tuple(math.radians(d) for d in rotation_deg)
    if location is not None:
        obj.location = location
    if rotation_deg is not None:
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    if location is not None:
        obj.keyframe_insert(data_path="location", frame=frame)
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            kp = fc.keyframe_points[-1] if fc.keyframe_points else None
            if kp is not None and round(kp.co.x) == frame:
                kp.interpolation = interpolation
                kp.easing = easing
