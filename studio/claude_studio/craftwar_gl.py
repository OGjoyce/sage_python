"""Translate CraftWar's C++/OpenGL model code into Blender geometry.

CraftWar's 3D models are not assets -- they are immediate-mode OpenGL draw
calls in src/gfx/models3d/*.cpp, built on the primitives in
src/platform/native/gl3d_draw.h. That file is WinAPI-bound, so the models
only run in the native Windows build.

This module reimplements those primitives against Blender, so a model can be
ported almost line-for-line from C++ to Python and then rendered, orbited and
exported anywhere. Port rule: keep the C++ numbers EXACTLY as written; this
shim handles the rest.

Faithfulness notes, all taken from gl3d_draw.h rather than guessed:

- U = 3.0 world units per sprite unit.
- Axes match this studio already: +Y is up, +Z is front. No conversion.
- `cube3(cx,cy,cz,s,...)` takes s as a HALF-size, since it expands to
  box3d(c-s ... c+s).
- The game uses NO OpenGL lighting. All shading is the per-face brightness
  table baked into box3d:
      front +Z x1.00   back -Z x0.30   top +Y x1.20
      bottom -Y x0.40  right +X x0.85  left -X x0.65
  so these meshes are given an UNLIT emission material driven by a per-face
  colour attribute. That reproduces the in-game look exactly and makes the
  result independent of whatever lights the surrounding scene has.
- setCol clamps each channel to 1.0 after multiplying, so `mul` above 1.0
  saturates rather than overflowing -- replicated here.
- Colours in the C++ are sRGB bytes (0xRRGGBB). Blender shades in linear, so
  they are converted; with view_transform="Standard" the final encode returns
  the original value.
"""

import math

import bmesh
import bpy
import mathutils

U = 3.0   # world units per 2D sprite unit (gl3d_draw.h:12)

# gl3d_draw.h box3d() face brightness table
FACE_FRONT, FACE_BACK = 1.00, 0.30
FACE_TOP, FACE_BOTTOM = 1.20, 0.40
FACE_RIGHT, FACE_LEFT = 0.85, 0.65

# glLineWidth is in PIXELS, which a raytracer has no equivalent for. The models
# are drawn ~60 world units tall filling ~600px of frame in gl3d.cpp's viewer,
# so one pixel is about 0.1 world units. line3d() takes the C++ glLineWidth
# value and scales it by this, which reproduces the on-screen weight.
PX = 0.12

# OpenGL resolves two faces drawn in the same plane with the depth buffer, and
# the models lean on that constantly: rib slabs sit flush on the torso front,
# the brow rim sits flush on the skull top. A raytracer has no tie-break, so
# those faces come out as speckled noise. Each quad is nudged out along its own
# normal by a hair, with a small per-call step so later draws land in front --
# the same ordering the C++ intends. At model scale (tens of units) this is far
# below a pixel.
# The nudge grows monotonically with draw order across the whole model, so a
# face drawn later always lands in front of one drawn earlier -- which is the
# layering the C++ means when it slaps a rib slab onto a torso. It is applied
# in build(), once the total draw count is known, to keep the range bounded.
BIAS_NEAR = 0.004
BIAS_FAR = 0.030


def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _col(rgb, f):
    """setCol(): sRGB bytes * f, clamped at 1.0, then taken to linear."""
    r = min(((rgb >> 16) & 0xFF) * f / 255.0, 1.0)
    g = min(((rgb >> 8) & 0xFF) * f / 255.0, 1.0)
    b = min((rgb & 0xFF) * f / 255.0, 1.0)
    return (_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), 1.0)


def _lerp_rgb(a, b, t):
    """Blend two 0xRRGGBB values, for GL's per-vertex smooth shading."""
    out = 0
    for sh in (16, 8, 0):
        ca, cb = (a >> sh) & 0xFF, (b >> sh) & 0xFF
        out |= int(round(ca + (cb - ca) * t)) << sh
    return out


class GLModel:
    """Accumulates translated geometry, then bakes it into one Blender object.

    Mirrors the GL matrix stack, because the model sources use
    glPushMatrix/glTranslatef/glRotatef to place spinning and hinged parts.
    """

    def __init__(self, name):
        self.name = name
        self.verts = []          # [(x, y, z), ...]
        self.faces = []          # [(i0, i1, i2, i3), ...]
        self.face_cols = []      # one RGBA per face
        self.face_norms = []     # world-space normal per face, for the depth bias
        self._stack = [mathutils.Matrix.Identity(4)]

    # ---- matrix stack -------------------------------------------------
    @property
    def _m(self):
        return self._stack[-1]

    def push(self):
        self._stack.append(self._m.copy())

    def pop(self):
        if len(self._stack) > 1:
            self._stack.pop()

    def translate(self, x, y, z):
        self._stack[-1] = self._m @ mathutils.Matrix.Translation((x, y, z))

    def rotate(self, deg, ax, ay, az):
        axis = mathutils.Vector((ax, ay, az))
        if axis.length < 1e-9:
            return
        self._stack[-1] = self._m @ mathutils.Matrix.Rotation(
            math.radians(deg), 4, axis.normalized())

    def scale(self, sx, sy, sz):
        self._stack[-1] = self._m @ mathutils.Matrix.Diagonal(
            (sx, sy, sz, 1.0)).to_4x4()

    # ---- raw emission -------------------------------------------------
    def quad(self, p0, p1, p2, p3, rgb, mul):
        """One flat quad, the GL_QUADS workhorse. Points are model-space."""
        base = len(self.verts)
        pts = [self._m @ mathutils.Vector(p) for p in (p0, p1, p2, p3)]
        for p in pts:
            self.verts.append(tuple(p))
        self.faces.append((base, base + 1, base + 2, base + 3))
        self.face_cols.append(_col(rgb, mul))
        n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        self.face_norms.append(
            n.normalized() if n.length > 1e-9 else mathutils.Vector((0, 0, 0)))

    def tri(self, p0, p1, p2, rgb, mul):
        """One flat triangle, for the GL_TRIANGLES runs (feathers, plumes)."""
        base = len(self.verts)
        pts = [self._m @ mathutils.Vector(p) for p in (p0, p1, p2)]
        for p in pts:
            self.verts.append(tuple(p))
        self.faces.append((base, base + 1, base + 2))
        self.face_cols.append(_col(rgb, mul))
        n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        self.face_norms.append(
            n.normalized() if n.length > 1e-9 else mathutils.Vector((0, 0, 0)))

    def fan(self, center, rim, col, mul_center, mul_edge, col_edge=None, rings=4):
        """A GL_TRIANGLE_FAN with a bright centre fading out to its rim.

        GL shades a fan smoothly from the centre vertex's colour to the rim
        vertices', which one flat triangle per wedge cannot reproduce. The
        wedge is split into `rings` concentric bands instead, each carrying the
        colour at its own radius -- the same falloff, in flat faces.
        """
        c = mathutils.Vector(center)
        pts = [mathutils.Vector(p) for p in rim]
        if col_edge is None:
            col_edge = col
        for k in range(rings):
            t0, t1 = k / rings, (k + 1) / rings
            tm = (t0 + t1) * 0.5
            cm = _lerp_rgb(col, col_edge, tm)
            mm = mul_center + (mul_edge - mul_center) * tm
            for i in range(len(pts) - 1):
                a0 = c.lerp(pts[i], t0)
                a1 = c.lerp(pts[i + 1], t0)
                b0 = c.lerp(pts[i], t1)
                b1 = c.lerp(pts[i + 1], t1)
                if t0 == 0.0:
                    self.tri(tuple(a0), tuple(b0), tuple(b1), cm, mm)
                else:
                    self.quad(tuple(a0), tuple(a1), tuple(b1), tuple(b0), cm, mm)

    # ---- gl3d_draw.h primitives ---------------------------------------
    def box3d(self, x0, y0, z0, x1, y1, z1, col, mul=1.0):
        """Axis-aligned box with the 6-face directional shading table."""
        self.quad((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), col, mul * FACE_FRONT)
        self.quad((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0), col, mul * FACE_BACK)
        self.quad((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0), col, mul * FACE_TOP)
        self.quad((x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), col, mul * FACE_BOTTOM)
        self.quad((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), col, mul * FACE_RIGHT)
        self.quad((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0), col, mul * FACE_LEFT)

    def cube3(self, cx, cy, cz, s, col, mul=1.0):
        """Centred cube. NOTE: s is a HALF-size, as in the C++."""
        self.box3d(cx - s, cy - s, cz - s, cx + s, cy + s, cz + s, col, mul)

    def ring3d(self, cx, cy, cz, big_r, tube_r, col, mul=1.0, rs=32, ts=10):
        """Torus in the XZ plane, with ring3d's own per-tube shading."""
        p2 = math.tau
        for i in range(rs):
            a0, a1 = p2 * i / rs, p2 * (i + 1) / rs
            for j in range(ts):
                b0, b1 = p2 * j / ts, p2 * (j + 1) / ts

                def pt(a, b):
                    return (cx + (big_r + tube_r * math.cos(b)) * math.cos(a),
                            cy + tube_r * math.sin(b),
                            cz + (big_r + tube_r * math.cos(b)) * math.sin(a))

                self.quad(pt(a0, b0), pt(a1, b0), pt(a1, b1), pt(a0, b1),
                          col, mul * (0.65 + 0.55 * math.sin(b0)))

    def line3d(self, p0, p1, col, mul=1.0, px=2.0, col1=None, mul1=None, segs=8):
        """Stand-in for glBegin(GL_LINES) runs, which have no thickness in GL.

        Rendered as a square-section bar so it survives a raytracer. `px` is the
        C++ glLineWidth value, converted through PX above.

        The model sources set a colour per VERTEX on these lines (a flame tongue
        goes white-hot at the base and fades out at the tip), so col1/mul1 give
        the far end and the bar is split into `segs` pieces carrying the
        interpolated colour -- GL's own smooth shading, approximated.
        """
        a = mathutils.Vector(p0)
        b = mathutils.Vector(p1)
        d = b - a
        if d.length < 1e-9:
            return
        half = px * PX * 0.5
        d.normalize()
        up = mathutils.Vector((0, 1, 0))
        if abs(d.dot(up)) > 0.999:
            up = mathutils.Vector((1, 0, 0))
        r = d.cross(up).normalized() * half
        s = d.cross(r).normalized() * half
        n = segs if col1 is not None else 1
        if mul1 is None:
            mul1 = mul
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            q0 = a.lerp(b, t0)
            q1 = a.lerp(b, t1)
            tm = (t0 + t1) * 0.5
            if col1 is None:
                c, m = col, mul
            else:
                c, m = _lerp_rgb(col, col1, tm), mul + (mul1 - mul) * tm
            for o1, o2 in ((r, s), (s, -r), (-r, -s), (-s, r)):
                self.quad(tuple(q0 + o1), tuple(q1 + o1),
                          tuple(q1 + o2), tuple(q0 + o2), c, m)

    def wisp3(self, cx, cy, cz, r, col, mul=1.0):
        """wisp3 is a camera-facing additive billboard: four concentric fans at
        r, r*0.52, r*0.26 and r*0.10, each bright at the centre and fading to
        nothing at its edge, so the stack reads as a soft glowing orb.

        A raytraced frame has no single 'camera right' and nothing orbits with
        the lens, so the fans become nested octahedra at the same radii and the
        same brightnesses. Same glow, same place, view-independent -- and it
        still looks right from every angle an orbit passes through, which a
        single flat billboard baked into the mesh would not.

        The widest, faintest fan is included even though it is nearly invisible
        on its own: it is what fills the gap between the bright core and
        whatever ring the model draws around it. Dropping it left the Mayan
        hero's pyrite mirror disc as a dark obsidian ring with a hole in it.
        """
        for fr, cm in ((r, mul * 0.08),
                       (r * 0.52, mul * 0.32),
                       (r * 0.26, mul * 0.75),
                       (r * 0.10, mul * 1.00)):
            px = ((fr, 0, 0), (-fr, 0, 0))
            py = ((0, fr, 0), (0, -fr, 0))
            pz = ((0, 0, fr), (0, 0, -fr))
            for a in px:
                for b in py:
                    for c in pz:
                        self.tri((cx + a[0], cy + a[1], cz + a[2]),
                                 (cx + b[0], cy + b[1], cz + b[2]),
                                 (cx + c[0], cy + c[1], cz + c[2]), col, cm)

    # ---- bake ---------------------------------------------------------
    def build(self, unlit=True, emit_strength=4.0, emit_threshold=0.35):
        """Create the Blender object.

        unlit=True (default) is the faithful mode: the game does all its
        shading in the face table above, so adding scene lighting on top would
        double-shade it and stop matching.

        unlit=False is for dropping a model into a lit cinematic scene. The
        vertex colours still carry the game's face shading, and they drive
        Base Color; on top of that, the parts the game authored BRIGHT (a
        fel-green ember, a flame tongue, a solar disc) are the parts that are
        meant to glow, so luminance above emit_threshold is mapped onto
        emission strength. Dark flesh stays matte and takes the scene's light;
        the glow reads as glow.
        """
        verts = list(self.verts)
        total = max(len(self.faces) - 1, 1)
        for i, face in enumerate(self.faces):
            off = self.face_norms[i] * (
                BIAS_NEAR + (BIAS_FAR - BIAS_NEAR) * i / total)
            for vi in face:
                v = verts[vi]
                verts[vi] = (v[0] + off.x, v[1] + off.y, v[2] + off.z)

        mesh = bpy.data.meshes.new(self.name + "_mesh")
        mesh.from_pydata(verts, [], self.faces)
        mesh.update()

        attr = mesh.color_attributes.new(name="GLCol", type="FLOAT_COLOR", domain="CORNER")
        for poly in mesh.polygons:
            c = self.face_cols[poly.index]
            for li in poly.loop_indices:
                attr.data[li].color = c

        mat = bpy.data.materials.new(self.name + "_mat")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        cattr = nt.nodes.new("ShaderNodeVertexColor")
        cattr.layer_name = "GLCol"

        if unlit:
            shader = nt.nodes.new("ShaderNodeEmission")
            shader.inputs["Strength"].default_value = 1.0
            nt.links.new(cattr.outputs["Color"], shader.inputs["Color"])
        else:
            shader = nt.nodes.new("ShaderNodeBsdfPrincipled")
            shader.inputs["Roughness"].default_value = 0.55
            shader.inputs["Metallic"].default_value = 0.0
            nt.links.new(cattr.outputs["Color"], shader.inputs["Base Color"])
            nt.links.new(cattr.outputs["Color"], shader.inputs["Emission Color"])
            bw = nt.nodes.new("ShaderNodeRGBToBW")
            nt.links.new(cattr.outputs["Color"], bw.inputs["Color"])
            rng = nt.nodes.new("ShaderNodeMapRange")
            rng.clamp = True
            rng.inputs["From Min"].default_value = emit_threshold
            rng.inputs["From Max"].default_value = 1.0
            rng.inputs["To Min"].default_value = 0.0
            rng.inputs["To Max"].default_value = emit_strength
            nt.links.new(bw.outputs["Val"], rng.inputs["Value"])
            nt.links.new(rng.outputs["Result"], shader.inputs["Emission Strength"])

        nt.links.new(shader.outputs[0], out.inputs["Surface"])
        mesh.materials.append(mat)

        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(obj)
        return obj

    def stats(self):
        return {"verts": len(self.verts), "faces": len(self.faces)}
