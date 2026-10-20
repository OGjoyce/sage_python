"""CraftWar's 3D models, translated from C++/OpenGL into Blender geometry.

Each module here is a near line-for-line port of the matching
src/gfx/models3d/*.cpp, built on claude_studio.craftwar_gl. Every module
exposes:

    build(tickF=0.0, anim=0) -> bpy.types.Object

tickF and anim mean exactly what they mean in the C++ (anim: 0 idle, 1 walk,
2 attack), so a pose can be reproduced frame-for-frame against the game.
"""
