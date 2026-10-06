"""Scene-level helpers: clearing the default scene, cameras, lights, world."""

import math
import bpy
import mathutils


def reset_scene():
    """Wipe the default cube/camera/light and start from an empty scene."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def look_at(obj, target):
    """Point obj's local -Z axis at `target`, local +Y up (the convention
    Blender cameras and spot/sun lights use for their forward direction).

    Built from explicit basis vectors (forward/right/up via cross
    products) rather than Vector.to_track_quat('-Z','Y'), which this
    function used originally: for at least one direction that is exactly
    horizontal (zero world-Y component) but not axis-aligned -- e.g.
    target-location = (-6, 0, -8), as opposed to (0, 0, -10.5), which
    worked fine -- to_track_quat returned a quaternion with a genuine 90
    degree roll baked in (verified by dumping rotation_euler), rendering
    the entire scene sideways with no error of any kind. The explicit
    basis-vector construction is the same technique used for the raymarch
    camera in water_core_3d.glsl, and has no such edge case."""
    pos = mathutils.Vector(obj.location)
    tgt = mathutils.Vector(target)
    forward = (tgt - pos)
    if forward.length < 1e-9:
        return obj  # target == position, nothing to orient toward
    forward.normalize()

    world_up = mathutils.Vector((0.0, 1.0, 0.0))
    if abs(forward.dot(world_up)) > 0.999:
        world_up = mathutils.Vector((0.0, 0.0, 1.0))  # looking ~straight up/down: avoid a degenerate cross product

    right = forward.cross(world_up).normalized()
    up = right.cross(forward).normalized()

    rot_mat = mathutils.Matrix((
        (right.x, up.x, -forward.x),
        (right.y, up.y, -forward.y),
        (right.z, up.z, -forward.z),
    ))
    obj.rotation_euler = rot_mat.to_euler()
    return obj


def add_camera(location, target=None, rotation_euler=None, lens=35.0, name="StudioCamera"):
    """Add a camera and make it the active scene camera. Either pass
    `target` (a point to aim at, via look_at) or `rotation_euler` directly."""
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens
    cam_obj = bpy.data.objects.new(name, cam_data)
    cam_obj.location = location
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    if target is not None:
        look_at(cam_obj, target)
    elif rotation_euler is not None:
        cam_obj.rotation_euler = rotation_euler
    return cam_obj


def add_sun(location=(0, 0, 10), target=(0, 0, 0), energy=3.0, angle=0.2, name="Sun"):
    """A SUN light (parallel rays, like real sunlight) aimed at `target`."""
    light_data = bpy.data.lights.new(name, type="SUN")
    light_data.energy = energy
    light_data.angle = angle  # angular diameter -> softness of shadows
    light_obj = bpy.data.objects.new(name, light_data)
    light_obj.location = location
    bpy.context.collection.objects.link(light_obj)
    look_at(light_obj, target)
    return light_obj


def add_area_light(location, target=None, energy=200.0, size=4.0, color=(1, 1, 1), name="Fill"):
    """A soft AREA light, typically used as a dim fill/bounce stand-in."""
    light_data = bpy.data.lights.new(name, type="AREA")
    light_data.energy = energy
    light_data.size = size
    light_data.color = color
    light_obj = bpy.data.objects.new(name, light_data)
    light_obj.location = location
    bpy.context.collection.objects.link(light_obj)
    if target is not None:
        look_at(light_obj, target)
    return light_obj


def set_world_gradient(top_color=(0.05, 0.12, 0.10, 1.0), bottom_color=(0.12, 0.28, 0.22, 1.0), strength=1.0):
    """A simple vertical-gradient sky via the World shader -- cheap, no HDRI
    asset needed, and enough to put reflections/fill light into the scene."""
    world = bpy.data.worlds.new("StudioWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = bottom_color
    ramp.color_ramp.elements[1].color = top_color
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "LINEAR"
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value = (0, math.radians(90), 0)
    texcoord = nt.nodes.new("ShaderNodeTexCoord")

    nt.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return world


def drive_with_frame(input_socket, channel_index, expression):
    """Animate a node-tree input (e.g. a Mapping node's Location.Z) with a
    driver expression in terms of the current frame, instead of hand-
    keyframing. `expression` is a Python expression string that uses the
    variable `frame`, e.g. "frame * 0.05". This is what makes water/
    waterfall textures actually move across a rendered animation."""
    fcurve = input_socket.driver_add("default_value", channel_index)
    drv = fcurve.driver
    drv.type = "SCRIPTED"
    var = drv.variables.new()
    var.name = "frame"
    var.type = "SINGLE_PROP"
    var.targets[0].id_type = "SCENE"
    var.targets[0].id = bpy.context.scene
    var.targets[0].data_path = "frame_current"
    drv.expression = expression
    return fcurve
