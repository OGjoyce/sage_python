"""
image_to_3d_demo.py — proves out claude_studio.image_to_3d end to end:
load an image, build a heightfield mesh from it, decimate to a target
triangle count N, color it with the source image, and render it.

Run with:
    blender -b --python studio/scenes/image_to_3d_demo.py -- \\
        --image studio/assets/demo_heightmap.png --triangles 4000

(The bare `--` tells Blender "everything after this is for the script" --
without it, Blender tries to parse --image/--triangles itself.) All flags
are optional; it defaults to the bundled demo_heightmap.png.

To use your own photo: same command with --image pointing at it. Expect a
relief/lithophane effect (brightness -> height), not a recovered 3D
object -- see the module docstring in claude_studio/image_to_3d.py for
why, and when that's the right or wrong tool for a given image.
"""

import argparse
import os
import sys

STUDIO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, STUDIO_DIR)

import bpy  # noqa: E402
import claude_studio as cs  # noqa: E402


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--image", default=os.path.join(STUDIO_DIR, "assets", "demo_heightmap.png"))
    p.add_argument("--triangles", type=int, default=4000, help="target triangle count N")
    p.add_argument("--height", type=float, default=1.1, help="max relief height")
    p.add_argument("--grid-res", type=int, default=220, help="source grid resolution (must stay well above --triangles)")
    p.add_argument("--size", type=float, default=4.0, help="mesh footprint, world units")
    p.add_argument("--out", default=os.path.join(STUDIO_DIR, "renders", "image_to_3d.png"))
    p.add_argument("--export", default=None, help="also export the mesh, e.g. --export model.glb")
    return p.parse_args(argv)


def main():
    args = parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    cs.scene.reset_scene()

    obj, achieved = cs.image_to_3d.image_to_mesh(
        args.image,
        target_triangles=args.triangles,
        grid_res=args.grid_res,
        size=args.size,
        height_scale=args.height,
        name="ImageModel",
    )
    print(f"STUDIO: image_to_mesh('{args.image}') -> {achieved} triangles (target was {args.triangles})")

    if args.export:
        cs.image_to_3d.export_mesh(obj, args.export)
        print("STUDIO: exported mesh to", args.export)

    cs.scene.set_world_gradient(top_color=(0.04, 0.05, 0.07, 1.0), bottom_color=(0.10, 0.12, 0.16, 1.0))
    cs.scene.add_sun(location=(4, -6, 6), target=(0, 0, args.height * 0.3), energy=3.0, angle=0.3)
    cs.scene.add_area_light(location=(-3, -3, 3), target=(0, 0, args.height * 0.3), energy=80, size=3)
    cam_dist = args.size * 0.95
    cs.scene.add_camera(
        location=(cam_dist, -cam_dist * 1.05, cam_dist * 0.72),
        target=(0, 0, args.height * 0.3),
        lens=38,
    )

    cs.render.configure_render(engine="CYCLES", samples=48, resolution=(960, 540), filepath=args.out)
    cs.render.render_still()
    print("STUDIO: rendered to", args.out)


if __name__ == "__main__":
    main()
