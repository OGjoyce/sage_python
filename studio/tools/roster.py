"""Tile one view of every index in a *_units / *_bldg module into one sheet.

    python3 tools/roster.py dire_units 7 [cols]

Expects tools/render_model.py to have already written <module><idx>_a0_v0.png
into renders/craftwar_models/roster/. Missing indices are skipped, which is
what an unimplemented unit looks like (the C++ returns false for those).
"""
import os
import sys

from PIL import Image, ImageDraw

SRC = "/home/user/sage_python/studio/renders/craftwar_models/roster"

module = sys.argv[1]
count = int(sys.argv[2])
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4

# The module cannot be imported here: it imports bpy, which only exists inside
# Blender. Read its NAMES tuple out of the source text instead.
names = [str(i) for i in range(count)]
try:
    src = open(f"/home/user/sage_python/studio/craftwar_models/{module}.py").read()
    body = src.split("NAMES = (", 1)[1].split(")", 1)[0]
    names = [t.strip().strip('"\'') for t in body.split(",") if t.strip()]
except Exception:
    pass

tiles = []
for i in range(count):
    f = os.path.join(SRC, f"{module}{i}_a0_v0.png")
    if os.path.exists(f):
        tiles.append((i, Image.open(f).convert("RGBA")))

if not tiles:
    sys.exit("no renders for " + module)

w, h = tiles[0][1].size
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (w * cols, 26 + rows * (h + 20)), (14, 12, 18))
d = ImageDraw.Draw(sheet)
d.text((8, 7), f"{module}  --  CraftWar C++/OpenGL models translated to Blender",
       fill=(200, 230, 170))
for n, (i, im) in enumerate(tiles):
    cx, cy = (n % cols) * w, 26 + (n // cols) * (h + 20)
    sheet.paste(im, (cx, cy), im)
    label = names[i] if i < len(names) else str(i)
    d.text((cx + 8, cy + h + 4), f"{i}  {label}", fill=(150, 165, 150))

out = os.path.join(SRC, f"{module}_roster.png")
sheet.save(out)
print(out, sheet.size)
