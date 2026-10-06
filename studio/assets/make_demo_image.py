#!/usr/bin/env python3
"""
Generates studio/assets/demo_heightmap.png — a synthetic grayscale test
image for the image-to-3D pipeline (studio/scenes/image_to_3d_demo.py).

Run with plain system Python (needs numpy + Pillow), NOT Blender's bundled
Python -- this has nothing to do with bpy, it just needs to exist as a
file before image_to_3d_demo.py runs.

The pattern (a raised dome with concentric ripples, like a stone dropped
in a pond) was picked because it has both broad, low-frequency structure
(reads clearly even after heavy decimation to a low triangle count) and
fine high-frequency ripples (shows the benefit of a higher triangle
budget) -- useful for sanity-checking the N-triangle control.
"""
import numpy as np
from PIL import Image

W = H = 512
yy, xx = np.mgrid[0:H, 0:W]
cx, cy = W / 2, H / 2
r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (W / 2)

dome = np.clip(1.0 - r, 0.0, 1.0) ** 1.4
ripple = 0.5 + 0.5 * np.sin(r * 26.0 - 2.0) * np.exp(-r * 1.6)
height = np.clip(dome * 0.65 + ripple * 0.45, 0.0, 1.0)

img = (height * 255).astype(np.uint8)
Image.fromarray(img, mode="L").convert("RGB").save(
    __file__.rsplit("/", 1)[0] + "/demo_heightmap.png"
)
print("wrote demo_heightmap.png")
