"""Build a Blender mesh from a .cwmesh captured out of the C++ models.

    blender -b --python tools/import_capture.py -- --in model.cwmesh \
            [--name Foo] [--lit] [--blend out.blend] [--glb out.glb]

craftwar_models/*.py are hand ports: someone reads the C++ and rewrites it in
Python. They are fast to run (about 20 ms for a hero) but they are a second
source of truth, so every edit to the C++ has to be mirrored by hand and goes
stale the moment it is not. A .cwmesh is produced by compiling the model's own
TU against tools/glcapture in craftwar, so it is not a port -- it is the
geometry the engine actually draws, and it cannot disagree with the engine.

The file carries the face brightness the game's own table produced, as vertex
colour, which is the same thing GLModel.build() wires up. --lit swaps the flat
emission material for the Principled one used when dropping a model into a
Cycles scene.
"""

import os
import struct
import sys

sys.path.insert(0, "/home/user/sage_python/studio")

import bpy  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def _srgb_to_linear(c):
    """The capture stores what glColor3f received, which is the game's own
    sRGB value scaled to 0..1. Blender's FLOAT_COLOR attribute is linear, so
    handing it sRGB directly renders everything washed-out and bright --
    which is exactly how the first captured import differed from the hand
    port. craftwar_gl._col does this same conversion.
    """
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def load_cwmesh(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"CWMESH01":
        raise ValueError("%s is not a CWMESH01 file" % path)
    nv, nt = struct.unpack_from("<II", data, 8)
    off = 16
    # 9 floats per vertex: position, colour, normal
    vals = struct.unpack_from("<%df" % (nv * 9), data, off)
    off += nv * 9 * 4
    idx = struct.unpack_from("<%dI" % (nt * 3), data, off)
    verts = [(vals[i * 9 + 0], vals[i * 9 + 1], vals[i * 9 + 2]) for i in range(nv)]
    cols = [(_srgb_to_linear(vals[i * 9 + 3]),
             _srgb_to_linear(vals[i * 9 + 4]),
             _srgb_to_linear(vals[i * 9 + 5]), 1.0) for i in range(nv)]
    tris = [(idx[i * 3], idx[i * 3 + 1], idx[i * 3 + 2]) for i in range(nt)]
    return verts, cols, tris


def build_mesh(verts, cols, tris, name, lit=False):
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], tris)
    mesh.update()

    attr = mesh.color_attributes.new(name="GLCol", type="FLOAT_COLOR", domain="CORNER")
    # Each captured vertex is unshared and carries its own colour, so the loop
    # colour is simply the colour of the vertex that loop points at.
    data = attr.data
    for poly in mesh.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices):
            data[li].color = cols[vi]

    mat = bpy.data.materials.new(name + "_mat")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    cattr = nt.nodes.new("ShaderNodeVertexColor")
    cattr.layer_name = "GLCol"
    if lit:
        sh = nt.nodes.new("ShaderNodeBsdfPrincipled")
        sh.inputs["Roughness"].default_value = 0.55
        sh.inputs["Metallic"].default_value = 0.0
        nt.links.new(cattr.outputs["Color"], sh.inputs["Base Color"])
    else:
        sh = nt.nodes.new("ShaderNodeEmission")
        sh.inputs["Strength"].default_value = 1.0
        nt.links.new(cattr.outputs["Color"], sh.inputs["Color"])
    nt.links.new(sh.outputs[0], out.inputs["Surface"])
    mesh.materials.append(mat)

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def main():
    src = arg("--in")
    if not src:
        raise SystemExit("--in model.cwmesh is required")
    name = arg("--name") or os.path.splitext(os.path.basename(src))[0]
    lit = "--lit" in argv

    bpy.ops.wm.read_factory_settings(use_empty=True)
    verts, cols, tris = load_cwmesh(src)
    build_mesh(verts, cols, tris, name, lit)
    print("IMPORTED %s  verts=%d tris=%d" % (name, len(verts), len(tris)))

    blend = arg("--blend")
    if blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
        print("BLEND %s" % os.path.abspath(blend))
    glb = arg("--glb")
    if glb:
        bpy.ops.export_scene.gltf(filepath=os.path.abspath(glb), export_format="GLB")
        print("GLB %s" % os.path.abspath(glb))


# Guarded so the loader can also be imported as a module -- the comparison
# harness builds both the hand port and the capture in one process, and an
# unguarded main() kills it with SystemExit on import.
if __name__ == "__main__":
    main()
