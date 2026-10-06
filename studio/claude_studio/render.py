"""Render configuration + invocation.

Defaults to Cycles on CPU with denoising OFF. That's not the "best
quality" choice -- it's the choice that actually works in a headless
container with no GPU: the Ubuntu-packaged Blender used here is built
without OpenImageDenoise, so leaving denoising on makes render.render()
raise RuntimeError, and Cycles-on-CPU has no GPU driver dependency at all
(EEVEE technically works too, via surfaceless EGL + llvmpipe, but it's
slower here than Cycles-CPU at matching sample counts and depends on a
software GL stack being present, which Cycles-CPU doesn't need).
"""

import bpy


def configure_render(engine="CYCLES", samples=32, resolution=(960, 540), denoise=False, filepath=None, transparent=False, device="CPU", view_transform="Standard"):
    scene = bpy.context.scene
    scene.render.engine = engine
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = "PNG"
    # Blender 4.x defaults to the "AgX" view transform, a filmic-style
    # tone-mapper that noticeably desaturates and compresses bright/
    # saturated colors on its way to the final pixels -- exactly what a
    # material built from an exact hex spec (MAT_LIVE_GREEN #70FFB0,
    # MAT_BEACON #FF3030, the procedural rust orange, ...) doesn't want,
    # since the point was to hit those colors faithfully. "Standard" is a
    # straight linear-to-sRGB encode with no additional tone-mapping.
    scene.view_settings.view_transform = view_transform

    if engine == "CYCLES":
        scene.cycles.samples = samples
        scene.cycles.use_denoising = denoise
        scene.view_layers[0].cycles.use_denoising = denoise
        scene.cycles.device = device

    if filepath is not None:
        scene.render.filepath = filepath
    return scene


def render_still():
    bpy.ops.render.render(write_still=True)


def render_animation(start, end, filepath_prefix, fps=24):
    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    scene.render.fps = fps
    scene.render.filepath = filepath_prefix
    bpy.ops.render.render(animation=True)
