"""Composite the per-view PNGs of a model onto one labelled contact sheet."""
import sys, glob, os
from PIL import Image, ImageDraw

model = sys.argv[1]
src = sys.argv[2] if len(sys.argv) > 2 else "/home/user/sage_python/studio/renders/craftwar_models"
files = sorted(glob.glob(os.path.join(src, f"{model}_*_v*.png")))
if not files:
    sys.exit("no views for " + model)
ims = [Image.open(f).convert("RGBA") for f in files]
w, h = ims[0].size
cols = len(ims)
sheet = Image.new("RGB", (w * cols, h + 26), (14, 12, 18))
for i, im in enumerate(ims):
    sheet.paste(im, (i * w, 26), im)
d = ImageDraw.Draw(sheet)
d.text((8, 7), f"{model}  --  CraftWar C++/OpenGL model translated to Blender", fill=(200, 230, 170))
for i, f in enumerate(files):
    d.text((i * w + 8, h + 8), os.path.basename(f), fill=(120, 130, 120))
out = os.path.join(src, f"{model}_sheet.png")
sheet.save(out)
print(out, sheet.size)
