import bpy
import os
import sys
from math import radians
import bmesh
import mathutils

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import claude_studio as cs

# Reset the scene
cs.scene.reset_scene()

# Parameters
colors = {
    "pink": (0.9686, 0.6863, 0.7686, 1),  # #F7AFC4
    "red": (0.8784, 0.2824, 0.3529, 1),  # #E0485A
    "blue": (0.1804, 0.1922, 0.5725, 1),  # #2E3192
    "blush": (0.9569, 0.6039, 0.7569, 1)  # #F49AC1
}

# Create materials
pink_material, _ = cs.materials.new_principled_material(name="Pink", base_color=colors["pink"], roughness=0.7)
red_material, _ = cs.materials.new_principled_material(name="RedFeet", base_color=colors["red"], roughness=0.7)
blue_material, _ = cs.materials.new_principled_material(name="BlueEyes", base_color=colors["blue"], roughness=0.7)
blush_material, _ = cs.materials.new_principled_material(name="Blush", base_color=colors["blush"], roughness=0.7)

# Add Kirby's body
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1))
body = bpy.context.object
body.name = "KirbyBody"
body.data.materials.append(pink_material)

# Add Kirby's feet
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=(-0.5, -0.6, 0.4))
left_foot = bpy.context.object
left_foot.name = "LeftFoot"
left_foot.data.materials.append(red_material)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=(0.5, -0.6, 0.4))
right_foot = bpy.context.object
right_foot.name = "RightFoot"
right_foot.data.materials.append(red_material)

# Add Kirby's eyes
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.15, location=(-0.3, -0.95, 1.2))
left_eye = bpy.context.object
left_eye.name = "LeftEye"
left_eye.data.materials.append(blue_material)

bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.15, location=(0.3, -0.95, 1.2))
right_eye = bpy.context.object
right_eye.name = "RightEye"
right_eye.data.materials.append(blue_material)

# Add Kirby's blush
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.1, location=(-0.4, -0.95, 1.05))
left_blush = bpy.context.object
left_blush.name = "LeftBlush"
left_blush.data.materials.append(blush_material)

bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.1, location=(0.4, -0.95, 1.05))
right_blush = bpy.context.object
right_blush.name = "RightBlush"
right_blush.data.materials.append(blush_material)

# Combine all Kirby parts
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
left_foot.select_set(True)
right_foot.select_set(True)
left_eye.select_set(True)
right_eye.select_set(True)
left_blush.select_set(True)
right_blush.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()

# Add camera and a single sun light
cs.scene.add_camera(location=(0, -5, 2), target=(0, 0, 1))
cs.scene.add_sun(location=(5, -5, 10), target=(0, 0, 1), energy=2.0)

# Set the world background to mid-gray
cs.scene.set_world_gradient(top_color=(0.6, 0.6, 0.6, 1), bottom_color=(0.6, 0.6, 0.6, 1))

# Triangle count evaluation
# Due to complex operations, directly evaluate triangle count
mesh = body.data
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated_mesh = body.evaluated_get(depsgraph).to_mesh()
triangle_count = len(evaluated_mesh.polygons)
body.evaluated_get(depsgraph).to_mesh_clear()

# Export the model
ROOT = os.path.join(os.path.dirname(__file__), '..')
os.makedirs(os.path.join(ROOT, 'renders'), exist_ok=True)
os.makedirs(os.path.join(ROOT, 'exports'), exist_ok=True)
cs.gl_export.export_obj_mtl({"Kirby": body}, os.path.join(ROOT, 'exports', 'kirby.obj'))
cs.render.configure_render(filepath=os.path.join(ROOT, 'renders', 'kirby.png'), samples=32, resolution=(960, 540), denoise=False, view_transform="Standard")
cs.render.render_still()

print(f"STUDIO: Kirby model created with {triangle_count} triangles.")
