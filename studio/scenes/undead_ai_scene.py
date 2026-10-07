"""
undead_ai_scene.py — builds the Undead AI announcer character (see
claude_studio/characters.py: build_undead_ai) and renders it in a dark
presentation scene, piece by piece then assembled, with:

  - a procedural rust material (claude_studio.characters' MAT_RUST) on the
    damaged side -- the user's own "metal oxidado" request, distinct from
    the blueprint's olive-green MAT_CORROSION
  - emissive "plasma/LED" materials (live eye, chest lights, joint glow,
    beacon) pushed through a Glare compositor node for an actual bloom,
    so they read as glowing light sources, not just bright flat color

Run with:
    blender -b --python studio/scenes/undead_ai_scene.py -- --view front
    (--view: front | back | left | right | three_quarter)
"""

import argparse
import math
import os
import sys

STUDIO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, STUDIO_DIR)

import bpy  # noqa: E402
import claude_studio as cs  # noqa: E402

RENDERS_DIR = os.path.join(STUDIO_DIR, "renders")

CAMERAS = {
    "front": dict(location=(0.0, 2.6, 10.5), target=(0.0, 2.6, 0.0)),
    "back": dict(location=(0.3, 2.6, -10.8), target=(0.3, 2.6, 0.0)),
    "left": dict(location=(-10.5, 2.6, 0.0), target=(0.0, 2.6, 0.0)),
    "right": dict(location=(10.5, 2.6, 0.0), target=(0.0, 2.6, 0.0)),
    "three_quarter": dict(location=(6.0, 2.6, 8.0), target=(0.0, 2.6, 0.0)),
}


def setup_glare_compositor():
    """A real Glare (bloom) node so the emissive plasma/LED materials
    actually bleed light into the surrounding pixels, instead of just
    being bright flat squares -- this is what sells "glowing" rather than
    "painted bright green.\""""
    scene = bpy.context.scene
    scene.use_nodes = True
    nt = scene.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    glare = nt.nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.quality = "HIGH"
    glare.threshold = 0.9
    glare.size = 7
    comp = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(rl.outputs["Image"], glare.inputs["Image"])
    nt.links.new(glare.outputs["Image"], comp.inputs["Image"])


def build_presentation_lighting():
    # A dark, moody backdrop rather than the waterfall's green gradient --
    # this is a character turntable/presentation shot, not an environment
    # scene, and a near-black background makes the emissive plasma reads
    # pop instead of competing with a bright sky.
    #
    # Both arms sit close against the torso and share metal tones with it
    # (RUST on the right/dead arm is dark too), so against a near-black
    # backdrop either side goes near-invisible the moment its own light is
    # weaker than the other's. An earlier pass fixed the dead (+X) arm by
    # moving the rim+a dedicated fill there, but left the alive (-X) arm's
    # own fill at a much lower energy -- which then made IT disappear
    # instead. Both sides now get a matched front fill plus their own rim,
    # so neither arm depends on the key sun alone to read.
    cs.scene.set_world_gradient(top_color=(0.012, 0.014, 0.016, 1.0), bottom_color=(0.03, 0.035, 0.045, 1.0))
    cs.scene.add_sun(location=(-4, 6, 5), target=(0, 2.5, 0), energy=2.6, angle=0.2)
    # right side (+X, dead/rust arm): rim behind + front fill
    cs.scene.add_area_light(location=(4, 4, -3), target=(0, 2.5, 0), energy=190, size=3.5, color=(0.75, 0.8, 1.0))
    cs.scene.add_area_light(location=(3.5, 2.2, 3.5), target=(0.9, 2.3, 0), energy=120, size=3, color=(1.0, 0.95, 0.85))
    # left side (-X, alive/green arm): matching rim + front fill
    cs.scene.add_area_light(location=(-4, 4, -3), target=(0, 2.5, 0), energy=150, size=3.5, color=(0.7, 0.9, 0.85))
    cs.scene.add_area_light(location=(-3.5, 2.2, 3.5), target=(-0.9, 2.3, 0), energy=120, size=3, color=(0.85, 1.0, 0.95))


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--view", choices=list(CAMERAS.keys()), default="three_quarter")
    p.add_argument("--all-views", action="store_true", help="render every camera preset in one run")
    p.add_argument("--samples", type=int, default=96)
    p.add_argument("--no-render", action="store_true", help="build/export only, skip rendering")
    p.add_argument("--export-obj", default=None, help="export OBJ+MTL to this path")
    p.add_argument("--export-gl", default=None, help="export the custom OpenGL binary mesh (+ .json) to this path")
    return p.parse_args(argv)


def main():
    args = parse_args()
    cs.scene.reset_scene()

    root, parts, tri_count = cs.characters.build_undead_ai(cs.materials)
    stats = cs.gl_export.report_statistics("UndeadAI", parts)

    build_presentation_lighting()
    lights = [o for o in bpy.data.objects if o.type in ("LIGHT",)]
    cs.gl_export.organize_collections("UNDEAD_AI", parts, lights=lights)
    setup_glare_compositor()

    if args.export_obj or args.export_gl:
        # UV coordinates are only needed for export, not for the Cycles
        # preview renders (which shade from vertex color / flat material
        # color, not a texture lookup) -- skipped otherwise to keep plain
        # render iterations fast.
        cs.gl_export.unwrap_parts(parts)
        if args.export_obj:
            cs.gl_export.export_obj_mtl(parts, args.export_obj)
            print("STUDIO: exported OBJ+MTL to", args.export_obj)
        if args.export_gl:
            cs.gl_export.export_gl_binary(parts, args.export_gl)

    if args.no_render:
        return

    views = list(CAMERAS.keys()) if args.all_views else [args.view]
    for view in views:
        cam_spec = CAMERAS[view]
        for obj in list(bpy.data.objects):
            if obj.type == "CAMERA":
                bpy.data.objects.remove(obj, do_unlink=True)
        cs.scene.add_camera(location=cam_spec["location"], target=cam_spec["target"], lens=35)

        out_path = os.path.join(RENDERS_DIR, f"undead_ai_{view}.png")
        cs.render.configure_render(
            engine="CYCLES", samples=args.samples, resolution=(960, 1080), denoise=False, filepath=out_path,
        )
        cs.render.render_still()
        print(f"STUDIO: rendered {view} -> {out_path}")


if __name__ == "__main__":
    main()
