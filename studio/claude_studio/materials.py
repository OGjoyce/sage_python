"""Material helpers: Principled BSDF shortcuts + a couple of procedural
node-tree patterns (cracked rock, bump noise) used by more than one scene.

These build real Blender shader node trees -- nothing here is baked or
image-based, matching the same "pure math, no texture assets" spirit as
the GLSL side of this project.
"""

import bpy


def _get_input(bsdf, *names):
    """Principled BSDF's socket names changed between Blender versions
    (4.0 renamed "Transmission" to "Transmission Weight", etc.) -- try each
    candidate name and use whichever exists on this build."""
    for n in names:
        if n in bsdf.inputs:
            return bsdf.inputs[n]
    return None


def new_principled_material(
    name,
    base_color=(0.5, 0.5, 0.5, 1.0),
    roughness=0.6,
    metallic=0.0,
    transmission=0.0,
    ior=1.45,
    emission_color=None,
    emission_strength=0.0,
):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")

    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    trans = _get_input(bsdf, "Transmission Weight", "Transmission")
    if trans is not None:
        trans.default_value = transmission
    ior_in = _get_input(bsdf, "IOR")
    if ior_in is not None:
        ior_in.default_value = ior
    if emission_color is not None:
        ecol = _get_input(bsdf, "Emission Color", "Emission")
        estr = _get_input(bsdf, "Emission Strength")
        if ecol is not None:
            ecol.default_value = emission_color
        if estr is not None:
            estr.default_value = emission_strength

    return mat, bsdf


def add_noise_bump(mat, bsdf, scale=8.0, detail=6.0, roughness=0.6, strength=0.15):
    """Micro-surface roughness via a Noise texture piped through a Bump
    node into the BSDF's Normal input -- cheap detail with zero extra
    geometry."""
    nt = mat.node_tree
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = roughness
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return noise, bump


def add_voronoi_cracked_rock(mat, bsdf, scale=6.0, dark=(0.07, 0.07, 0.08, 1), light=(0.30, 0.29, 0.26, 1), edge_width=0.06):
    """The Blender-node equivalent of wf_voronoi's crack trick in the GLSL
    shaders: Voronoi 'Distance To Edge' is ~0 exactly on a cell boundary,
    so a tight ColorRamp on it draws dark cracks between randomly-toned
    facets -- same idea as water_core.glsl, different language."""
    nt = mat.node_tree
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.voronoi_dimensions = "3D"
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = scale

    edge_ramp = nt.nodes.new("ShaderNodeValToRGB")
    edge_ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    edge_ramp.color_ramp.elements[0].position = 0.0
    edge_ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    edge_ramp.color_ramp.elements[1].position = edge_width

    vor_cell = nt.nodes.new("ShaderNodeTexVoronoi")
    vor_cell.voronoi_dimensions = "3D"
    vor_cell.feature = "F1"
    vor_cell.inputs["Scale"].default_value = scale
    tone_ramp = nt.nodes.new("ShaderNodeValToRGB")
    tone_ramp.color_ramp.elements[0].color = dark
    tone_ramp.color_ramp.elements[1].color = light

    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 1.0

    nt.links.new(vor.outputs["Distance"], edge_ramp.inputs["Fac"])
    nt.links.new(vor_cell.outputs["Color"], tone_ramp.inputs["Fac"])
    nt.links.new(edge_ramp.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(tone_ramp.outputs["Color"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    return vor, vor_cell, mix


def new_water_material(name, base_color=(0.05, 0.30, 0.38, 1.0), roughness=0.08, transmission=0.85, ior=1.33):
    """Principled BSDF tuned for water: low roughness (sharp reflections),
    high transmission, IOR 1.33 (real water)."""
    return new_principled_material(
        name,
        base_color=base_color,
        roughness=roughness,
        metallic=0.0,
        transmission=transmission,
        ior=ior,
    )
