"""
claude_studio — a small, reusable toolkit on top of Blender's `bpy` for
building and rendering 3D scenes headlessly.

This exists so building a scene is "import claude_studio, call a few
helpers" instead of re-deriving the same twenty lines of node-tree
plumbing every time. It is not a Blender add-on (no registration, no UI) --
it is a plain Python package meant to be run via:

    blender -b --python some_scene_script.py

where some_scene_script.py does `import claude_studio as cs` (after adding
this directory's parent to sys.path -- see scenes/waterfall_scene.py for
the two-line pattern) and calls into `cs.scene`, `cs.materials`, `cs.render`.
"""

from . import scene
from . import materials
from . import render
from . import image_to_3d

__all__ = ["scene", "materials", "render", "image_to_3d"]
