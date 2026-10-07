"""
waterfall_scene.py — the Claude 3D Scene Studio's flagship demo.

Builds the same composition as waterfall/shared/water_core_3d.glsl (cliff
wall with a notch cut out, a falling sheet of water in the gap, a handful
of boulders, a river/pool surface) but as *real* Blender geometry and
shader node materials instead of a raymarched signed-distance field --
the "studio" (mesh + modifier + node-based) way of building the same
scene, for comparison against the "shader" way.

Run with:
    blender -b --python studio/scenes/waterfall_scene.py

Renders a still to studio/renders/waterfall_studio.png by default. Pass
`-- --animate` (note the extra `--` that tells Blender "everything after
this is for the script, not for me") to also render a short turntable
animation of PNG frames to studio/renders/anim/.
"""

import math
import os
import sys

STUDIO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, STUDIO_DIR)

import bpy  # noqa: E402
import claude_studio as cs  # noqa: E402

RENDERS_DIR = os.path.join(STUDIO_DIR, "renders")
os.makedirs(RENDERS_DIR, exist_ok=True)

# -- layout constants, chosen to roughly match water_core_3d.glsl's scene --
CLIFF_TOP = 2.35
CLIFF_X0, CLIFF_X1 = -4.3, 2.3
CLIFF_THICKNESS = 0.8
GAP_X0, GAP_X1 = -1.35, -0.25
WATER_LEVEL = 0.0


def legacy_texture(name, tex_type, **props):
    """Displace modifiers read from the old bpy.data.textures system
    (distinct from the shader-node textures materials use) -- this just
    creates one and sets whatever properties were passed."""
    tex = bpy.data.textures.new(name, type=tex_type)
    for k, v in props.items():
        setattr(tex, k, v)
    return tex


def add_flow_empty(name, axis_index, speed):
    """An Empty whose position drifts over time, used as the coordinate
    source for a Displace modifier so the displacement pattern appears to
    scroll/flow across the surface instead of sitting static."""
    empty = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(empty)
    fcurve = empty.driver_add("location", axis_index)
    drv = fcurve.driver
    drv.type = "SCRIPTED"
    var = drv.variables.new()
    var.name = "frame"
    var.type = "SINGLE_PROP"
    var.targets[0].id_type = "SCENE"
    var.targets[0].id = bpy.context.scene
    var.targets[0].data_path = "frame_current"
    drv.expression = f"frame * {speed}"
    return empty


def build_cliff():
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    cliff = bpy.context.active_object
    cliff.name = "Cliff"
    cx = (CLIFF_X0 + CLIFF_X1) * 0.5
    cliff.location = (cx, 0.0, CLIFF_TOP * 0.5)
    cliff.scale = ((CLIFF_X1 - CLIFF_X0) * 0.5, CLIFF_THICKNESS * 0.5, CLIFF_TOP * 0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # cut the waterfall notch
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    cutter = bpy.context.active_object
    cutter.name = "GapCutter"
    gcx = (GAP_X0 + GAP_X1) * 0.5
    cutter.location = (gcx, 0.0, CLIFF_TOP * 0.55)
    cutter.scale = ((GAP_X1 - GAP_X0) * 0.5, CLIFF_THICKNESS, CLIFF_TOP * 0.65)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    boolmod = cliff.modifiers.new("Notch", "BOOLEAN")
    boolmod.operation = "DIFFERENCE"
    boolmod.object = cutter
    boolmod.solver = "EXACT"

    sub = cliff.modifiers.new("Facet", "SUBSURF")
    sub.subdivision_type = "SIMPLE"
    sub.levels = 3
    sub.render_levels = 3

    rock_tex = legacy_texture("CliffRockTex", "VORONOI", noise_scale=0.55)
    disp = cliff.modifiers.new("Jagged", "DISPLACE")
    disp.texture = rock_tex
    disp.strength = 0.18
    disp.mid_level = 0.5

    mat, bsdf = cs.materials.new_principled_material("CliffRock", roughness=0.85)
    cs.materials.add_voronoi_cracked_rock(mat, bsdf, scale=3.0)
    cs.materials.add_noise_bump(mat, bsdf, scale=14.0, strength=0.08)
    cliff.data.materials.append(mat)

    # IMPORTANT: the Boolean modifier keeps a *live* reference to `cutter`
    # and re-evaluates it at render time -- deleting the object here (as an
    # earlier version of this script did) leaves the modifier pointing at
    # nothing, which fails silently (no error, the cliff just renders as
    # an uncut solid block). Unlinking from the collection hides it from
    # the render as its own object while keeping the datablock alive for
    # the modifier to still reference.
    bpy.context.collection.objects.unlink(cutter)
    return cliff


def build_boulders():
    specs = [
        ((0.35, 0.95, -0.10), 0.26),
        ((0.95, -0.55, -0.14), 0.22),
        ((1.55, 0.65, -0.09), 0.29),
        ((1.15, 1.55, -0.17), 0.19),
        ((2.35, -0.25, -0.12), 0.25),
        ((2.85, 0.95, -0.16), 0.20),
        ((0.55, -0.85, -0.18), 0.17),
    ]
    boulders = []
    rock_tex = legacy_texture("BoulderRockTex", "VORONOI", noise_scale=0.9)
    mat, bsdf = cs.materials.new_principled_material("BoulderRock", roughness=0.8)
    cs.materials.add_voronoi_cracked_rock(mat, bsdf, scale=9.0, edge_width=0.1)

    for i, (pos, r) in enumerate(specs):
        bpy.ops.mesh.primitive_ico_sphere_add(radius=r, subdivisions=3, location=(pos[1], pos[2], WATER_LEVEL + pos[0] * 0 + r * 0.55))
        b = bpy.context.active_object
        # NOTE: world axes here are (x=downstream, y=across-river, z=up);
        # the ico_sphere_add location call above packs (x,y,z) from specs
        # as (across, depth-offset, height) -- rewritten explicitly below
        # for clarity rather than relying on the call above.
        b.location = (pos[0], pos[1], r * 0.55)
        b.name = f"Boulder_{i}"
        disp = b.modifiers.new("Facet", "DISPLACE")
        disp.texture = rock_tex
        disp.strength = 0.07
        disp.mid_level = 0.5
        b.data.materials.append(mat)
        boulders.append(b)
    return boulders


def build_water():
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=140, y_subdivisions=100, size=1.0)
    water = bpy.context.active_object
    water.name = "River"
    water.location = (2.2, 0.0, WATER_LEVEL)
    water.scale = (7.0, 4.5, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    flow = add_flow_empty("WaterFlowEmpty", 0, 0.045)
    wave_tex = legacy_texture("WaterWaveTex", "WOOD", wood_type="RINGS", noise_scale=0.6, turbulence=4.0)
    disp = water.modifiers.new("Ripples", "DISPLACE")
    disp.texture = wave_tex
    disp.texture_coords = "OBJECT"
    disp.texture_coords_object = flow
    disp.strength = 0.045
    disp.mid_level = 0.5

    mat, bsdf = cs.materials.new_water_material("RiverWater")
    cs.materials.add_noise_bump(mat, bsdf, scale=18.0, strength=0.05)
    water.data.materials.append(mat)
    return water


def build_waterfall():
    gcx = (GAP_X0 + GAP_X1) * 0.5
    gap_w = GAP_X1 - GAP_X0
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=18, y_subdivisions=120, size=1.0)
    fall = bpy.context.active_object
    fall.name = "Waterfall"
    fall.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    fall.location = (gcx, 0.0, CLIFF_TOP * 0.5)
    # The grid primitive spans -0.5..0.5 locally (size=1.0), so `scale` is
    # the FULL resulting width/height, not a half-width -- the first pass
    # of this used 0.46x the gap width here, meant as a half-width
    # multiplier, and ended up under half the gap's actual width, rendering
    # as a near-invisible sliver instead of filling the notch.
    fall.scale = (gap_w * 0.92, CLIFF_TOP * 1.04, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    fall.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    flow = add_flow_empty("FallFlowEmpty", 2, 0.4)
    turb_tex = legacy_texture("FallTurbulenceTex", "CLOUDS", noise_scale=0.25, noise_depth=4)
    disp = fall.modifiers.new("Turbulence", "DISPLACE")
    disp.texture = turb_tex
    disp.texture_coords = "OBJECT"
    disp.texture_coords_object = flow
    disp.strength = 0.04
    disp.mid_level = 0.5

    mat, bsdf = cs.materials.new_principled_material(
        "FallWater", base_color=(0.10, 0.55, 0.65, 1.0), roughness=0.12, transmission=0.2, ior=1.33,
        emission_color=(0.75, 0.92, 0.98, 1.0), emission_strength=0.25,
    )
    fall.data.materials.append(mat)
    return fall


def build_lighting_and_world():
    cs.scene.set_world_gradient()
    cs.scene.add_sun(location=(-6, -8, 10), target=(0, 0, 1), energy=3.2, angle=0.25)
    cs.scene.add_area_light(location=(4, -2, 4), target=(0, 0, 1), energy=120, size=3, color=(0.8, 0.95, 1.0))


def build_camera():
    return cs.scene.add_camera(location=(7.2, -6.8, 3.6), target=(0.3, 0.6, 1.1), lens=32)


def main():
    animate = "--animate" in sys.argv

    cs.scene.reset_scene()
    build_cliff()
    build_boulders()
    build_water()
    build_waterfall()
    build_lighting_and_world()
    build_camera()

    cs.render.configure_render(
        engine="CYCLES",
        samples=48,
        resolution=(960, 540),
        denoise=False,
        filepath=os.path.join(RENDERS_DIR, "waterfall_studio.png"),
    )

    if animate:
        anim_dir = os.path.join(RENDERS_DIR, "anim")
        os.makedirs(anim_dir, exist_ok=True)
        cs.render.render_animation(1, 48, os.path.join(anim_dir, "frame_"), fps=24)
        print("STUDIO: animation rendered to", anim_dir)
    else:
        cs.render.render_still()
        print("STUDIO: still rendered to", os.path.join(RENDERS_DIR, "waterfall_studio.png"))


if __name__ == "__main__":
    # Guarded (rather than a bare top-level call) so this stays importable
    # -- e.g. `import waterfall_scene` from another script to reuse
    # build_cliff()/build_boulders()/etc. -- without rendering as a
    # side effect of the import.
    main()
