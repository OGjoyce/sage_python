#!/usr/bin/env python3
"""
request_scaffold.py -- turns one "model request" submitted through the
Model Request Builder web form into real files to read and run:

    studio/requests/<slug>/spec.json       the request, verbatim
    studio/requests/<slug>/reference.<ext> the uploaded reference image, if any
    studio/scenes/<slug>_scene.py          a scaffolded Blender scene script

This does not build a specific character -- characters.py does that, by
hand, for Undead AI. It writes a generic STARTING POINT any new model
request can run immediately: image-to-3D relief if a reference image was
given, otherwise a primitive-built placeholder block to fill in -- with
the triangle budget, materials, scene/light toggles, and exports already
wired to that request's own choices. It needs no Blender (`bpy`): run it
with plain system Python right after pulling a submission down from the
Model Request Builder artifact.

Usage:
    python3 studio/tools/request_scaffold.py path/to/spec.json \
        [--image path/to/reference.png] [--out studio]
"""

import argparse
import json
import os


def _slugify(name):
    s = "".join(c if c.isalnum() else "_" for c in name.strip().lower())
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_") or "model"


def _hex_to_rgb(hexstr):
    h = hexstr.lstrip("#")
    if len(h) != 6:
        return (0.5, 0.5, 0.5)
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _render_scene_script(slug, spec, image_rel):
    prompt = spec.get("prompt", "")
    colors = spec.get("colors") or ["#8a8a8a"]
    triangles = int(spec.get("triangleBudget", 4000))
    include_scene = bool(spec.get("includeScene"))
    include_lights = bool(spec.get("includeLights"))
    light_preset = spec.get("lightPreset", "studio")
    formats = spec.get("outputFormats") or ["obj"]
    class_name = "".join(w.capitalize() for w in slug.split("_")) or "Model"

    lines = []
    lines.append('"""')
    lines.append(f"{slug}_scene.py -- scaffolded from a Model Request Builder submission.")
    lines.append("")
    lines.append(f"Prompt: {prompt}")
    lines.append(f"Colors: {', '.join(colors)}")
    lines.append(f"Triangle budget: {triangles}")
    lines.append(f"Scene included: {include_scene}   Lights included: {include_lights} ({light_preset})")
    lines.append(f"Output formats requested: {', '.join(formats)}")
    lines.append("")
    lines.append("STARTING POINT, not a finished build -- fill in the geometry where")
    lines.append("marked below (characters.py's primitive helpers are the established")
    lines.append("pattern for hard-surface parts), then re-run. Triangle budget,")
    lines.append("materials, scene/light toggles, and exports below already match")
    lines.append("what this request asked for.")
    lines.append('"""')
    lines.append("")
    lines.append("import os")
    lines.append("import sys")
    lines.append("")
    lines.append("sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))")
    lines.append("import claude_studio as cs")
    lines.append("")
    lines.append("ROOT = os.path.join(os.path.dirname(__file__), '..')")
    lines.append("cs.scene.reset_scene()")
    lines.append("")

    if image_rel:
        posix_rel = image_rel.replace(os.sep, "/")
        lines.append("# Reference image provided -- image_to_3d gives a relief mesh for free.")
        lines.append("# Swap this block for hand-built primitives if the request needs real")
        lines.append("# hard-surface geometry instead of a height-relief.")
        lines.append(f"REFERENCE_IMAGE = os.path.join(ROOT, {posix_rel!r})")
        lines.append("model_obj, achieved = cs.image_to_3d.image_to_mesh(")
        lines.append(f"    REFERENCE_IMAGE, target_triangles={triangles}, name={class_name!r}")
        lines.append(")")
        lines.append(f"print('STUDIO: {slug} --', achieved, 'triangles (budget {triangles})')")
    else:
        lines.append("# No reference image -- build geometry by hand with claude_studio's")
        lines.append("# primitive helpers (see characters.py: add_box / add_tapered_box /")
        lines.append("# add_cylinder / add_cone / add_ring), then join the pieces and keep")
        lines.append(f"# the running triangle count under the {triangles}-triangle budget.")
        lines.append("parts = {}  # TODO: build the model's parts here, e.g. parts['Body'] = ...")
        lines.append("model_obj = None  # TODO: join the parts into one object once they exist")
    lines.append("")

    lines.append("# Materials, one per color this request specified:")
    for i, hx in enumerate(colors):
        r, g, b = _hex_to_rgb(hx)
        mat_name = f"MAT_{i}_{hx.lstrip('#')}"
        lines.append(
            f"mat_{i} = cs.materials.new_principled_material({mat_name!r}, "
            f"base_color=({r:.4f}, {g:.4f}, {b:.4f}, 1.0))"
        )
    lines.append("# TODO: obj.data.materials.append(mat_N) on whichever parts should use each color")
    lines.append("")

    if include_scene:
        lines.append("cs.scene.set_world_gradient()")
        lines.append("cs.scene.add_camera(location=(4, 2.2, 6), target=(0, 1, 0))")
    else:
        lines.append("cs.scene.add_camera(location=(3, 1.6, 4), target=(0, 0.8, 0))")
    lines.append("")

    if include_lights:
        if light_preset == "dramatic":
            lines.append("cs.scene.add_sun(location=(-4, 6, 2), target=(0, 0.8, 0), energy=4.5, angle=0.05)")
            lines.append("cs.scene.add_area_light((3, 3, -2), target=(0, 0.8, 0), energy=80, color=(0.4, 0.6, 1.0))")
        elif light_preset == "outdoor":
            lines.append("cs.scene.add_sun(location=(5, 8, 3), target=(0, 0.8, 0), energy=3.0, angle=0.3)")
        else:
            lines.append("cs.scene.add_sun(location=(3, 5, 4), target=(0, 0.8, 0), energy=2.5, angle=0.2)")
            lines.append("cs.scene.add_area_light((-3, 2.5, 2), target=(0, 0.8, 0), energy=150, size=3.0)")
    lines.append("")

    lines.append("os.makedirs(os.path.join(ROOT, 'renders'), exist_ok=True)")
    lines.append(f"cs.render.configure_render(filepath=os.path.join(ROOT, 'renders', {(slug + '.png')!r}))")
    lines.append("cs.render.render_still()")
    lines.append("")

    export_lines = []
    if "obj" in formats:
        export_lines.append("# OBJ + MTL -- the most portable \"edit this in another DCC\" deliverable")
        export_lines.append("if model_obj is not None:")
        export_lines.append(
            f"    cs.gl_export.export_obj_mtl({{'model': model_obj}}, "
            f"os.path.join(ROOT, 'exports', {(slug + '.obj')!r}))"
        )
    if "uaig" in formats:
        export_lines.append("# .uaig binary -- the OpenGL real-time viewer's own format")
        export_lines.append("if model_obj is not None:")
        export_lines.append(
            f"    cs.gl_export.export_gl_binary({{'model': model_obj}}, "
            f"os.path.join(ROOT, 'exports', {(slug + '.uaig')!r}))"
        )
    if export_lines:
        lines.append("os.makedirs(os.path.join(ROOT, 'exports'), exist_ok=True)")
        lines.extend(export_lines)
        lines.append("")

    if "turntable" in formats:
        lines.append("# Turntable animation frames: run this script, then feed the exported")
        lines.append("# model through the OpenGL viewer's recording mode, e.g.:")
        lines.append(f"#   ./viewer --turntable renders/{slug}_turntable 96 --turntable-seconds 4")
        lines.append(f"#   ffmpeg -y -framerate 24 -i renders/{slug}_turntable/f_%04d.png \\")
        lines.append("#       -vf \"format=yuv420p\" -c:v libx264 -crf 18 -pix_fmt yuv420p \\")
        lines.append(f"#       renders/{slug}_turntable.mp4")
        lines.append("")

    return "\n".join(lines) + "\n"


def scaffold_request(spec, image_bytes, image_ext, out_root):
    """spec: dict matching the Model Request Builder's submission shape --
    {name, prompt, colors: [hex, ...], triangleBudget, includeScene,
    includeLights, lightPreset, outputFormats: [...]}. image_bytes: raw
    bytes of the uploaded reference image, or None. out_root: the
    studio/ directory. Returns (slug, [file paths written])."""
    slug = _slugify(spec.get("name") or spec.get("prompt", "model")[:24])
    req_dir = os.path.join(out_root, "requests", slug)
    os.makedirs(req_dir, exist_ok=True)

    written = []

    spec_path = os.path.join(req_dir, "spec.json")
    with open(spec_path, "w") as f:
        json.dump(spec, f, indent=2)
    written.append(spec_path)

    image_rel = None
    if image_bytes:
        ext = (image_ext or "png").lstrip(".")
        image_path = os.path.join(req_dir, f"reference.{ext}")
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        written.append(image_path)
        image_rel = os.path.relpath(image_path, out_root)

    scenes_dir = os.path.join(out_root, "scenes")
    os.makedirs(scenes_dir, exist_ok=True)
    scene_path = os.path.join(scenes_dir, f"{slug}_scene.py")
    with open(scene_path, "w") as f:
        f.write(_render_scene_script(slug, spec, image_rel))
    written.append(scene_path)

    return slug, written


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec_json", help="path to the request's spec.json")
    ap.add_argument("--image", help="path to the uploaded reference image, if any")
    ap.add_argument("--out", default="studio", help="studio/ directory (default: studio)")
    args = ap.parse_args()

    with open(args.spec_json) as f:
        spec = json.load(f)

    image_bytes = None
    image_ext = None
    if args.image:
        with open(args.image, "rb") as f:
            image_bytes = f.read()
        image_ext = os.path.splitext(args.image)[1].lstrip(".") or "png"

    slug, written = scaffold_request(spec, image_bytes, image_ext, args.out)
    print(f"STUDIO: scaffolded '{slug}' --")
    for path in written:
        print(f"  {path}")
    print(f"Next: blender -b --python {os.path.join(args.out, 'scenes', slug + '_scene.py')}")


if __name__ == "__main__":
    main()
