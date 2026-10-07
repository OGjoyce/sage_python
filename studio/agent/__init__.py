"""
studio/agent -- a standalone, OpenAI-backed coding agent for the 3D model
pipeline, with real sessions (plain JSON/files on disk, no hosted page).

This is a separate thing from the claude_studio package: claude_studio is
a bpy toolkit imported BY scene scripts; this package is the harness that
writes those scene scripts in the first place, by running an OpenAI model
in a tool-calling loop against claude_studio's own API, with Blender
itself as the execution sandbox (write a script -> run it -> read back
stdout/stderr and the render -> let the model react -> repeat).

No bpy import here -- everything in this package runs as plain system
Python; only the scene scripts it writes run inside `blender -b`.
"""
