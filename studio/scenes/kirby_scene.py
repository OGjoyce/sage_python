"""
kirby_scene.py — a "greybox" test object: a simple round character (body,
two feet, two arms, two eye-bumps), built entirely from icosphere
primitives (triangles by construction -- an icosphere is subdivided
triangles all the way, unlike a UV sphere's quads+poles) and a single flat
gray material, no color/texture detail at all. This is deliberately a
geometry/topology test, not a finished character: one uniform gray
material everywhere is a classic game-dev "greybox" prototyping move, used
specifically to judge shape and proportion without material work
distracting from it.

Placed standing on the tallest boulder in the waterfall scene (reusing
waterfall_scene's builders) so the two studio demos share one render.

Run with:
    blender -b --python studio/scenes/kirby_scene.py
    -> studio/renders/kirby_scene.png
"""

import os
import sys

STUDIO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, STUDIO_DIR)
sys.path.insert(0, os.path.join(STUDIO_DIR, "scenes"))

import bpy  # noqa: E402
import claude_studio as cs  # noqa: E402
import waterfall_scene as wf  # noqa: E402

RENDERS_DIR = os.path.join(STUDIO_DIR, "renders")


def add_tri_icosphere(name, radius, location, scale=(1.0, 1.0, 1.0), subdivisions=3):
    """An icosphere -- not a UV sphere -- specifically because its surface
    is 100% triangles by construction (20 * 4^subdivisions of them, no
    quads, no poles). Adding a Triangulate modifier on top is redundant
    here but kept anyway so the intent ("this part is triangles, provably,
    not just incidentally") is explicit in the modifier stack, not just
    true by choice of primitive."""
    bpy.ops.mesh.primitive_ico_sphere_add(radius=radius, subdivisions=subdivisions, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.modifiers.new("Triangulate", "TRIANGULATE")
    return obj


def build_kirby(base_location=(0.0, 0.0, 0.0), body_radius=0.42, name="KirbyClone"):
    """All parts positioned relative to `base_location`, which is where
    the feet touch the ground. Returns the single joined mesh object.

    Proportions are worked out so each nub part's center sits roughly ON
    the body sphere's surface (distance from body center ~= body_radius):
    that's what makes a small sphere read as "attached to and poking out
    of" the big one, instead of either floating disconnected (center too
    far out) or fully swallowed and invisible (center too far in) -- the
    first version of this had the feet's center so close to the body's
    own center that they ended up entirely inside it."""
    bx, by, bz = base_location
    R = body_radius
    parts = []

    body_z = bz + R * 0.92  # squashed scale.z=0.92, so this puts the bottom exactly at bz
    body = add_tri_icosphere(
        f"{name}_Body", R, (bx, by, body_z),
        scale=(1.0, 0.96, 0.92), subdivisions=3,
    )
    parts.append(body)

    foot_r = R * 0.32
    for side, dx in (("L", -0.38), ("R", 0.38)):
        foot = add_tri_icosphere(
            f"{name}_Foot{side}", foot_r,
            (bx + dx * R, by - 0.42 * R, bz + 0.07 * R),
            scale=(1.0, 1.3, 0.55), subdivisions=2,
        )
        parts.append(foot)

    arm_r = R * 0.27
    for side, dx in (("L", -1.0), ("R", 1.0)):
        arm = add_tri_icosphere(
            f"{name}_Arm{side}", arm_r,
            (bx + dx * R, by, body_z),
            scale=(1.0, 0.9, 1.1), subdivisions=2,
        )
        parts.append(arm)

    eye_r = R * 0.11
    eye_z = body_z + 0.20 * R
    for side, dx in (("L", -0.30), ("R", 0.30)):
        eye = add_tri_icosphere(
            f"{name}_Eye{side}", eye_r,
            (bx + dx * R, by - 0.95 * R, eye_z),
            scale=(0.85, 0.5, 1.35), subdivisions=1,
        )
        parts.append(eye)

    mat, bsdf = cs.materials.new_principled_material(
        f"{name}_GrayClay", base_color=(0.62, 0.62, 0.63, 1.0), roughness=0.55, metallic=0.0,
    )
    cs.materials.add_noise_bump(mat, bsdf, scale=22.0, strength=0.04)
    for p in parts:
        p.data.materials.append(mat)

    # NOTE: bpy.ops.object.join() merges base mesh *data* from every
    # selected object into the active one, but drops the non-active
    # objects' modifiers in the process -- so each part's Triangulate
    # modifier doesn't survive the join. That's harmless here specifically
    # because an icosphere's base geometry is already 100% triangles (see
    # add_tri_icosphere's docstring); the modifier was a belt-and-braces
    # guarantee, not the thing actually doing the work.
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.name = name
    return body


def main():
    cs.scene.reset_scene()

    wf.build_cliff()
    wf.build_boulders()
    wf.build_water()
    wf.build_waterfall()

    # Stand Kirby on the furthest-downstream boulder (x=2.85, past the
    # cliff's right edge at x=2.3), not the biggest one at (1.55, 0.65) --
    # that one sits right against the cliff face, and any shot tight
    # enough to make a 0.3-unit character legible has the adjacent
    # 6.6-unit wall looming across the whole frame. Boulder center sits at
    # z = radius*0.55 (see build_boulders), so its top is roughly
    # center + radius.
    boulder_xy = (2.85, 0.95)
    boulder_r = 0.20
    boulder_top_z = boulder_r * 0.55 + boulder_r
    kirby = build_kirby(base_location=(boulder_xy[0], boulder_xy[1], boulder_top_z), body_radius=0.22)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_kirby = kirby.evaluated_get(depsgraph)
    mesh = eval_kirby.to_mesh()
    tri_count = len(mesh.polygons)
    eval_kirby.to_mesh_clear()
    print(f"STUDIO: {kirby.name} built from {tri_count} triangles")

    wf.build_lighting_and_world()
    # Framed tight on the boulder Kirby's standing on (not the whole
    # cliff) -- the first pass used the wide waterfall_scene establishing
    # shot framing, which made a 0.3-radius character indistinguishable
    # from a 0.29-radius rock at that distance. The *second* pass then put
    # the camera itself a little too close and on the wrong side of the
    # (thin, 0.8-unit) cliff slab, so its view ray grazed through solid
    # rock instead of around it -- this offset is the same cliff-clearing
    # (dx, dy, dz) direction waterfall_scene's own working camera uses,
    # just scaled down for a tighter shot on one boulder instead of the
    # whole establishing shot.
    kirby_target = (boulder_xy[0], boulder_xy[1], boulder_top_z + 0.20)
    cs.scene.add_camera(
        location=(kirby_target[0] + 2.2, kirby_target[1] - 2.6, kirby_target[2] + 0.9),
        target=kirby_target,
        lens=40,
    )

    cs.render.configure_render(
        engine="CYCLES", samples=64, resolution=(960, 540), denoise=False,
        filepath=os.path.join(RENDERS_DIR, "kirby_scene.png"),
    )
    cs.render.render_still()
    print("STUDIO: rendered to", os.path.join(RENDERS_DIR, "kirby_scene.png"))


if __name__ == "__main__":
    main()
