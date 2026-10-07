"""
gl_export.py — the "last mile" from a built character to something an
OpenGL engine can actually load: scene organization (collections), UV
coordinates, debug statistics, and a binary vertex/index buffer export
matching the spec:

    struct Vertex { glm::vec3 position; glm::vec3 normal; glm::vec2 uv; };
    index buffer: uint32_t

plus a small per-material table (base color + emission), so a renderer
can draw each sub-mesh with the right material without re-deriving colors
from Blender.
"""

import json
import struct

import bpy


# ========================================================= collections ====

def organize_collections(root_name, parts, lights=None):
    """Creates the collection hierarchy the blueprint asks for and moves
    objects into it. Mapped onto this build's actual granularity (10
    joined sub-assemblies, not ~40 standing individual objects -- see
    characters.py's build_undead_ai docstring for why): GEOMETRY holds the
    body, SWORD its own pieces, LIGHTS the actual light objects. DETAILS
    and CABLES exist as empty collections with a comment, since at this
    LOD those parts are merged into their parent sub-assembly rather than
    kept standalone -- declared rather than silently dropped, so the gap
    between "spec asks for this collection" and "this build's LOD doesn't
    split it out" is visible in the scene itself, not just in a comment."""
    def get_or_create(name):
        if name in bpy.data.collections:
            return bpy.data.collections[name]
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        return c

    root_col = get_or_create(f"{root_name}")
    geometry_col = get_or_create(f"{root_name}_GEOMETRY")
    sword_col = get_or_create(f"{root_name}_SWORD")
    lights_col = get_or_create(f"{root_name}_LIGHTS")
    get_or_create(f"{root_name}_DETAILS")   # reserved: not split out at this LOD
    get_or_create(f"{root_name}_CABLES")    # reserved: cables are merged into RightArm
    get_or_create(f"{root_name}_DEBUG")
    for c in (geometry_col, sword_col, lights_col):
        if c.name not in [ch.name for ch in root_col.children]:
            try:
                root_col.children.link(c)
            except RuntimeError:
                pass  # already linked

    def move_to(obj, collection):
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)

    sword_names = {"GreatSword", "StrapTop", "StrapBottom"}
    for name, obj in parts.items():
        move_to(obj, sword_col if name in sword_names else geometry_col)

    if lights:
        for light_obj in lights:
            move_to(light_obj, lights_col)

    return {
        "root": root_col, "geometry": geometry_col, "sword": sword_col, "lights": lights_col,
    }


# =========================================================== uv unwrap ====

def unwrap_parts(parts, margin=0.02):
    """Smart UV Project on each joined sub-assembly -- robust and fully
    automatic for a pile of mostly-axis-aligned boxes/cylinders, which is
    exactly this character's geometry, without needing hand-placed seams."""
    for obj in parts.values():
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=margin)
        bpy.ops.object.mode_set(mode="OBJECT")


# =========================================================== statistics ===

def report_statistics(root_name, parts):
    """Matches the blueprint's requested debug output shape:

        UNDEAD AI STATISTICS
        Objects: 42
        Meshes: 18
        Vertices: XXXX
        Triangles: XXXX
        Materials: 11
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    total_verts = 0
    total_tris = 0
    mesh_count = 0
    material_names = set()

    for obj in parts.values():
        mesh_count += 1
        for slot in obj.material_slots:
            if slot.material:
                material_names.add(slot.material.name)
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        total_verts += len(mesh.vertices)
        total_tris += len(mesh.polygons)
        eval_obj.to_mesh_clear()

    lines = [
        f"{root_name.upper()} STATISTICS",
        "",
        f"Objects: {len(parts)}",
        f"Meshes: {mesh_count}",
        f"Vertices: {total_verts}",
        f"Triangles: {total_tris}",
        f"Materials: {len(material_names)}",
    ]
    report = "\n".join(lines)
    print(report)
    return {
        "objects": len(parts), "meshes": mesh_count, "vertices": total_verts,
        "triangles": total_tris, "materials": len(material_names),
        "material_names": sorted(material_names),
    }


# ================================================================ export ===

def export_obj_mtl(parts, filepath):
    """Multi-object OBJ+MTL export -- Blender's own exporter keeps each
    part as its own `o`/`g` group and writes real per-face material
    assignments, which is the most portable "edit this in another DCC"
    deliverable."""
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts.values():
        obj.select_set(True)
    bpy.context.view_layer.objects.active = next(iter(parts.values()))
    bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True, export_materials=True)


def _material_gl_table(parts):
    """One entry per unique material actually used, in a stable order, so
    the exported per-vertex material index is reproducible across runs."""
    seen = {}
    order = []
    for obj in parts.values():
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None or mat.name in seen:
                continue
            bsdf = None
            if mat.use_nodes:
                bsdf = mat.node_tree.nodes.get("Principled BSDF")
            base_color = list(bsdf.inputs["Base Color"].default_value) if bsdf else [0.5, 0.5, 0.5, 1.0]
            emission = [0.0, 0.0, 0.0]
            emission_strength = 0.0
            if bsdf is not None:
                ecol = bsdf.inputs.get("Emission Color")
                estr = bsdf.inputs.get("Emission Strength")
                if ecol is not None:
                    emission = list(ecol.default_value)[:3]
                if estr is not None:
                    emission_strength = estr.default_value
            seen[mat.name] = len(order)
            order.append({
                "name": mat.name,
                "base_color": base_color[:3],
                "emission": [c * emission_strength for c in emission],
            })
    return seen, order


def export_gl_binary(parts, filepath):
    """Writes a compact custom binary mesh format an OpenGL (or any)
    engine can memory-map / fread straight into GPU buffers:

        MAGIC    "UAIG" (4 bytes)
        VERSION  uint32 = 1
        n_materials  uint32
        n_submeshes  uint32
        n_vertices   uint32
        n_indices    uint32
        materials: n_materials * (name_len:uint32, name:bytes,
                                   base_color: 3*float32, emission: 3*float32)
        submeshes: n_submeshes * (name_len:uint32, name:bytes,
                                   material_index:uint32,
                                   index_offset:uint32, index_count:uint32)
        vertices: n_vertices * (px,py,pz, nx,ny,nz, u,v : 8*float32)
        indices:  n_indices * uint32

    Also writes `<filepath>.json` with the same material/submesh metadata
    in a human-readable form, since hand-debugging a pure binary blob is
    miserable and the JSON costs nothing extra to produce.
    """
    mat_index, mat_table = _material_gl_table(parts)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    all_positions = []
    all_normals = []
    all_uvs = []
    all_indices = []
    submeshes = []

    vertex_cursor = 0
    index_cursor = 0

    for name, obj in parts.items():
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        mesh.calc_loop_triangles()
        if mesh.uv_layers.active is None:
            mesh.uv_layers.new(name="UVMap")
        uv_layer = mesh.uv_layers.active.data

        mat_slot_names = [s.material.name if s.material else None for s in obj.material_slots]
        wm = obj.matrix_world
        normal_mat = wm.inverted().transposed().to_3x3()

        # group this object's triangles by material slot, one submesh per
        # (object, material) pair -- usually one submesh per object here,
        # since each part is built with a single assigned material already
        tris_by_mat = {}
        for tri in mesh.loop_triangles:
            tris_by_mat.setdefault(tri.material_index, []).append(tri)

        for slot_idx, tris in tris_by_mat.items():
            mat_name = mat_slot_names[slot_idx] if slot_idx < len(mat_slot_names) else None
            gl_mat_idx = mat_index.get(mat_name, 0)

            local_verts = {}
            local_indices = []
            for tri in tris:
                for li in range(3):
                    vi = tri.vertices[li]
                    loop_i = tri.loops[li]
                    v = mesh.vertices[vi]
                    pos = wm @ v.co
                    nrm = (normal_mat @ v.normal).normalized()
                    uv = uv_layer[loop_i].uv
                    key = (vi, round(uv.x, 6), round(uv.y, 6))
                    if key not in local_verts:
                        local_verts[key] = vertex_cursor + len(local_verts)
                        all_positions.append((pos.x, pos.y, pos.z))
                        all_normals.append((nrm.x, nrm.y, nrm.z))
                        all_uvs.append((uv.x, uv.y))
                    local_indices.append(local_verts[key])

            submeshes.append({
                "name": f"{name}_mat{slot_idx}",
                "material_index": gl_mat_idx,
                "index_offset": index_cursor,
                "index_count": len(local_indices),
            })
            all_indices.extend(local_indices)
            index_cursor += len(local_indices)
            vertex_cursor += len(local_verts)

        eval_obj.to_mesh_clear()

    with open(filepath, "wb") as f:
        f.write(b"UAIG")
        f.write(struct.pack("<IIIII", 1, len(mat_table), len(submeshes), len(all_positions), len(all_indices)))
        for m in mat_table:
            name_bytes = m["name"].encode("utf-8")
            f.write(struct.pack("<I", len(name_bytes)))
            f.write(name_bytes)
            f.write(struct.pack("<3f", *m["base_color"]))
            f.write(struct.pack("<3f", *m["emission"]))
        for sm in submeshes:
            name_bytes = sm["name"].encode("utf-8")
            f.write(struct.pack("<I", len(name_bytes)))
            f.write(name_bytes)
            f.write(struct.pack("<III", sm["material_index"], sm["index_offset"], sm["index_count"]))
        for p, n, uv in zip(all_positions, all_normals, all_uvs):
            f.write(struct.pack("<8f", p[0], p[1], p[2], n[0], n[1], n[2], uv[0], uv[1]))
        for idx in all_indices:
            f.write(struct.pack("<I", idx))

    meta_path = filepath + ".json"
    with open(meta_path, "w") as f:
        json.dump({
            "vertex_count": len(all_positions), "index_count": len(all_indices),
            "materials": mat_table, "submeshes": submeshes,
        }, f, indent=2)

    print(f"STUDIO: wrote {filepath} ({len(all_positions)} vertices, {len(all_indices)} indices, "
          f"{len(submeshes)} submeshes, {len(mat_table)} materials)")
    print(f"STUDIO: wrote {meta_path}")
    return {
        "vertex_count": len(all_positions), "index_count": len(all_indices),
        "submesh_count": len(submeshes), "material_count": len(mat_table),
    }
