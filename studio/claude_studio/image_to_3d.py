"""
image_to_3d.py — turn a single 2D image into a 3D mesh with a controllable
triangle budget.

The technique is a **heightfield relief** (a.k.a. a lithophane / bump-to-
geometry conversion), not photogrammetry or a learned single-image depth
model: image luminance becomes Z-height on a subdivided grid, the image's
color is kept as the mesh's own material (so it still looks like the
source photo, just extruded into relief), and a Decimate modifier brings
the final triangle count down to a requested target N. This is a real,
long-standing technique (the same idea 3D-printed "photo lithophanes" use)
and -- unlike a neural depth/mesh model -- needs no model weights, no
internet access, and no GPU, which matters a lot in a headless container
that may have none of those. It will not recover actual depth/occlusion
the way a multi-view or learned method could; a brighter pixel always
means "more height," not "closer to the camera." Good for relief art,
terrain-from-a-grayscale-map, and coins/medallions; not a general-purpose
photogrammetry replacement.

Pipeline: load image -> build a displaced grid (height = luminance) ->
triangulate -> measure actual triangle count -> Decimate (collapse) to hit
the requested target -> optionally color the mesh with the source image
-> optionally bake the modifier stack down to real mesh data.
"""

import bpy


def load_image_texture(image_path, name=None):
    img = bpy.data.images.load(image_path)
    tex = bpy.data.textures.new(name or (img.name + "_tex"), type="IMAGE")
    tex.image = img
    return img, tex


def heightfield_from_image(image_path, grid_res=200, size=4.0, height_scale=1.0, name="ImageHeightfield"):
    """A Grid mesh, UV-displaced along Z by the image's luminance (Displace
    modifier, mid_level=0.0 so black=0 height and white=`height_scale`),
    then triangulated. `grid_res` is vertices per side -- keep this
    comfortably above whatever `target_triangles` you plan to decimate
    down to, since Decimate only removes detail, it cannot invent it."""
    img, tex = load_image_texture(image_path, name=name + "_HeightTex")

    bpy.ops.mesh.primitive_grid_add(x_subdivisions=grid_res, y_subdivisions=grid_res, size=size)
    obj = bpy.context.active_object
    obj.name = name

    disp = obj.modifiers.new("ImageHeight", "DISPLACE")
    disp.texture = tex
    disp.texture_coords = "UV"
    disp.direction = "Z"
    disp.mid_level = 0.0
    disp.strength = height_scale

    obj.modifiers.new("Triangulate", "TRIANGULATE")
    return obj, img, tex


def current_triangle_count(obj):
    """Evaluate the object through its full modifier stack (as it would
    render) and count the resulting triangles -- not the base mesh's
    edit-time face count, which Decimate's `ratio` needs to be computed
    against the *post*-Displace/Triangulate geometry to be meaningful."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    count = len(mesh.polygons)
    eval_obj.to_mesh_clear()
    return count


def retopologize_to_triangle_count(obj, target_triangles, correction_pass=True):
    """Add/adjust a Decimate (Collapse) modifier so the evaluated mesh has
    approximately `target_triangles` triangles. `ratio` is approximate (it
    is Blender's own estimate of how much to collapse, not an exact
    count), so by default this does one measure -> adjust -> re-measure
    correction pass, which gets it close. Returns the achieved count."""
    current = current_triangle_count(obj)
    if current == 0:
        raise ValueError(f"'{obj.name}' evaluates to 0 triangles -- nothing to decimate")
    if target_triangles >= current:
        # Decimate only removes detail; asking for more triangles than the
        # base grid has is a no-op, not an error, but worth flagging.
        print(f"STUDIO: requested {target_triangles} triangles >= current {current}; "
              f"raise grid_res in heightfield_from_image() to actually hit that count.")
        return current

    ratio = max(0.0, min(1.0, target_triangles / current))
    dec = obj.modifiers.get("Decimate") or obj.modifiers.new("Decimate", "DECIMATE")
    dec.decimate_type = "COLLAPSE"
    dec.ratio = ratio

    if correction_pass:
        achieved = current_triangle_count(obj)
        if achieved > 0:
            dec.ratio = max(0.0, min(1.0, dec.ratio * (target_triangles / achieved)))

    return current_triangle_count(obj)


def apply_all_modifiers(obj):
    """Bake the modifier stack into real mesh data -- needed if you want
    to export a fixed-topology file (OBJ/glTF/etc.) that other tools will
    read with exactly the decimated triangle count, rather than a
    modifier stack that only resolves inside this .blend."""
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def add_image_color_material(obj, image, name="ImagePhotoMaterial", roughness=0.75):
    """Paint the mesh with the same image that shaped it -- UV-mapped
    straight onto Base Color, so a decimated relief still reads as the
    original picture, just extruded."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = roughness
    tex_node = nt.nodes.new("ShaderNodeTexImage")
    tex_node.image = image
    nt.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    obj.data.materials.append(mat)
    return mat


def image_to_mesh(
    image_path,
    target_triangles=5000,
    grid_res=200,
    size=4.0,
    height_scale=1.0,
    name="ImageModel",
    apply_modifiers=True,
    color_from_image=True,
):
    """The full pipeline in one call: image -> heightfield grid -> colored
    with the source image -> decimated to ~target_triangles -> (optionally)
    baked to real mesh data. Returns (object, achieved_triangle_count)."""
    obj, img, tex = heightfield_from_image(
        image_path, grid_res=grid_res, size=size, height_scale=height_scale, name=name
    )
    if color_from_image:
        add_image_color_material(obj, img)

    achieved = retopologize_to_triangle_count(obj, target_triangles)

    if apply_modifiers:
        apply_all_modifiers(obj)
        achieved = len(obj.data.polygons)  # exact, now that it's real mesh data

    return obj, achieved


def export_mesh(obj, filepath):
    """Export a single object to OBJ or glTF (format chosen by extension)
    -- apply_all_modifiers() first if you haven't, so the exported file's
    topology matches what retopologize_to_triangle_count() reported."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    ext = filepath.rsplit(".", 1)[-1].lower()
    if ext == "obj":
        bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True)
    elif ext in ("glb", "gltf"):
        bpy.ops.export_scene.gltf(filepath=filepath, use_selection=True)
    else:
        raise ValueError(f"unsupported export extension: .{ext} (use .obj, .glb, or .gltf)")
