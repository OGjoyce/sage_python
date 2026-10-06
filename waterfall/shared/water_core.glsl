// =============================================================================
// water_core.glsl — procedural waterfall + river, pure math, zero textures.
//
// This file has no `#version`, no `in`/`out`/`varying`, no `main()`. It is
// pasted verbatim into two thin wrappers:
//   - threejs/shaders/water.wrapper.js   (GLSL ES 1.00, WebGL)
//   - opengl/shaders/water.frag          (#version 330 core, native GL)
// so the exact same math drives both renderers. That's the point: if the two
// windows disagree, the bug is in a wrapper, never in the water itself.
//
// PHYSICS / MATH USED (see waterfall/README.md for the long version):
//   1. Stream-function flow field: v = curl(psi) = (d psi/dy, -d psi/dx).
//      Any vector field built this way is divergence-free by construction
//      (Bridson, "Curl-Noise for Procedural Fluid Flow", SIGGRAPH 2007) —
//      i.e. it never creates or destroys "water" the way a raw scrolling
//      UV or a naive gradient field would. psi mixes a uniform rightward
//      current with multi-octave fbm, so curl(psi) gives a turbulent but
//      incompressible river current.
//   2. Free-fall kinematics for the cascade: a parcel that left the lip at
//      time t0 has fallen y(t)=0.5*g*t^2, so we advect the fall texture by
//      a speed that *increases* with distance fallen, instead of a constant
//      scroll — streaks visibly accelerate on the way down.
//   3. Two-phase flow-mapped domain warp (GPU Gems "Rendering Water As a
//      Post Process" trick, also Unity's FlowMap shader): sample the same
//      noise twice at phases t and t+0.5, each advected along the local
//      flow direction, and cross-fade with a triangle wave. A single
//      infinitely-scrolling UV would show a hard reset every loop; this
//      hides it completely.
//   4. Foam is driven by an estimate of vorticity (how sheared the curl
//      field is locally) — this is where real whitewater actually forms,
//      not a hand-placed decal.
//   5. Rocks/cliff are smooth-min-blended implicit shapes (IQ's polynomial
//      smin) with normals taken from the field's own gradient, lit with a
//      simple Lambert + rim term, and moss-tinted by a slope test.
//   6. Final color passes through 4x4 Bayer ordered dithering + per-channel
//      posterization — the classic 16-bit-era trick for faking more
//      gradient steps than the palette has, which is what gives pixel art
//      its "hand-painted" banding instead of a smooth gradient.
// =============================================================================

// ---------------------------------------------------------------- noise ----
float wf_hash12(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float wf_vnoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = wf_hash12(i);
    float b = wf_hash12(i + vec2(1.0, 0.0));
    float c = wf_hash12(i + vec2(0.0, 1.0));
    float d = wf_hash12(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float wf_fbm(vec2 p) {
    float v = 0.0;
    float amp = 0.5;
    mat2 m = mat2(1.6, 1.2, -1.2, 1.6);
    for (int i = 0; i < 5; i++) {
        v += amp * wf_vnoise(p);
        p = m * p;
        amp *= 0.5;
    }
    return v;
}

// a cheaper 3-octave fbm for things sampled many times per pixel
float wf_fbm3(vec2 p) {
    float v = 0.0;
    float amp = 0.5;
    mat2 m = mat2(1.6, 1.2, -1.2, 1.6);
    for (int i = 0; i < 3; i++) {
        v += amp * wf_vnoise(p);
        p = m * p;
        amp *= 0.5;
    }
    return v;
}

// --------------------------------------------------------- flow field ------
// Stream function: uniform rightward current + turbulent eddies.
float wf_streamFn(vec2 p, float t) {
    float U = 0.55; // psi = -U*y  =>  v = curl(psi) = (U, 0)
    float psi = -U * p.y;
    psi += 0.55 * wf_fbm3(p * 2.2 + vec2(t * 0.15, -t * 0.05));
    psi += 0.18 * wf_fbm3(p * 5.0 - vec2(t * 0.30, t * 0.10));
    return psi;
}

// v = curl(psi) = (d(psi)/dy, -d(psi)/dx) -- divergence-free by construction
vec2 wf_curl(vec2 p, float t) {
    float e = 0.015;
    float n1 = wf_streamFn(p + vec2(0.0, e), t);
    float n2 = wf_streamFn(p - vec2(0.0, e), t);
    float n3 = wf_streamFn(p + vec2(e, 0.0), t);
    float n4 = wf_streamFn(p - vec2(e, 0.0), t);
    float dPsiDy = (n1 - n2) / (2.0 * e);
    float dPsiDx = (n3 - n4) / (2.0 * e);
    return vec2(dPsiDy, -dPsiDx);
}

// ----------------------------------------------------------------- sdf -----
float wf_smin(float a, float b, float k) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    return mix(b, a, h) - k * h * (1.0 - h);
}

float wf_sdCircle(vec2 p, vec2 c, float r) {
    return length(p - c) - r;
}

// Worley/cellular noise: returns (F1, F2, cellRandom) -- distance to the
// nearest feature point, distance to the second-nearest, and a stable
// per-cell random value. F2-F1 is ~0 exactly on a cell boundary, which is
// what turns this into convincing cracked rock instead of soft blobs: a
// smooth noise field has no edges to speak of, but real stone is made of
// discrete facets with joints between them, and a Voronoi diagram *is*
// that structure for free.
vec3 wf_voronoi(vec2 p) {
    vec2 ip = floor(p);
    vec2 fp = fract(p);
    float f1 = 8.0;
    float f2 = 8.0;
    float cellVal = 0.0;
    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            vec2 neighbor = vec2(float(x), float(y));
            vec2 seed = neighbor + vec2(
                wf_hash12(ip + neighbor + vec2(11.0, 0.0)),
                wf_hash12(ip + neighbor + vec2(0.0, 37.0))
            );
            float d = length(seed - fp);
            if (d < f1) {
                f2 = f1;
                f1 = d;
                cellVal = wf_hash12(ip + neighbor + vec2(99.0, 13.0));
            } else if (d < f2) {
                f2 = d;
            }
        }
    }
    return vec3(f1, f2, cellVal);
}

// ------------------------------------------------------- dither/palette ----
// Written as a flat if/else (rather than an array literal + dynamic index)
// on purpose: GLSL ES 1.00 (WebGL1) allows neither `float[16](...)`
// constructors nor non-constant array indexing in a fragment shader, and
// this file is compiled unmodified under both WebGL and desktop GL.
float wf_bayer4(vec2 fragPx) {
    vec2 m = mod(fragPx, 4.0);
    int x = int(m.x);
    int y = int(m.y);
    if (y == 0) {
        if (x == 0) return 0.0 / 16.0;
        if (x == 1) return 8.0 / 16.0;
        if (x == 2) return 2.0 / 16.0;
        return 10.0 / 16.0;
    } else if (y == 1) {
        if (x == 0) return 12.0 / 16.0;
        if (x == 1) return 4.0 / 16.0;
        if (x == 2) return 14.0 / 16.0;
        return 6.0 / 16.0;
    } else if (y == 2) {
        if (x == 0) return 3.0 / 16.0;
        if (x == 1) return 11.0 / 16.0;
        if (x == 2) return 1.0 / 16.0;
        return 9.0 / 16.0;
    } else {
        if (x == 0) return 15.0 / 16.0;
        if (x == 1) return 7.0 / 16.0;
        if (x == 2) return 13.0 / 16.0;
        return 5.0 / 16.0;
    }
}

vec3 wf_posterizeDither(vec3 col, vec2 fragPx, float levels) {
    // kept deliberately subtle: a full-strength Bayer pattern reads as a
    // visible regular dot-grid on any large near-flat area (the canopy,
    // open pool) -- enough to fake extra gradient steps, not enough to
    // look like a halftone print.
    float d = (wf_bayer4(fragPx) - 0.5) / levels;
    vec3 c = col + d * 0.32;
    return floor(c * levels + 0.5) / levels;
}

// ------------------------------------------------------ boulder field ------
// A handful of smooth-min-blended circles. Written as a real function (not
// inlined into wf_render) so we can also call it 3x with a tiny offset to
// get a central-difference "fake normal" for lighting -- the gradient of a
// signed distance field is a unit normal almost everywhere, for free.
float wf_bouldersSDF(vec2 p, float AR) {
    float d = 1.0e9;
    d = wf_smin(d, wf_sdCircle(p, vec2(0.470, 0.205) * vec2(AR, 1.0), 0.042 + 0.006 * wf_fbm3(p * 9.0 + 0.0)), 0.025);
    d = wf_smin(d, wf_sdCircle(p, vec2(0.565, 0.150) * vec2(AR, 1.0), 0.030 + 0.006 * wf_fbm3(p * 9.0 + 11.0)), 0.025);
    d = wf_smin(d, wf_sdCircle(p, vec2(0.690, 0.200) * vec2(AR, 1.0), 0.046 + 0.006 * wf_fbm3(p * 9.0 + 22.0)), 0.025);
    d = wf_smin(d, wf_sdCircle(p, vec2(0.615, 0.098) * vec2(AR, 1.0), 0.026 + 0.006 * wf_fbm3(p * 9.0 + 33.0)), 0.025);
    d = wf_smin(d, wf_sdCircle(p, vec2(0.800, 0.165) * vec2(AR, 1.0), 0.038 + 0.006 * wf_fbm3(p * 9.0 + 44.0)), 0.025);
    d = wf_smin(d, wf_sdCircle(p, vec2(0.885, 0.105) * vec2(AR, 1.0), 0.028 + 0.006 * wf_fbm3(p * 9.0 + 55.0)), 0.025);
    d = wf_smin(d, wf_sdCircle(p, vec2(0.955, 0.175) * vec2(AR, 1.0), 0.034 + 0.006 * wf_fbm3(p * 9.0 + 66.0)), 0.025);
    return d;
}

// Which single boulder (center, radius) is closest to p -- used to shade
// each stone as its own little hemisphere (see wf_render) instead of
// reading the blended SDF's in-plane gradient as a normal. That earlier
// approach had no component pointing toward the camera, so the "light"
// traced a flat radial wedge across each disc (it looked like a cone/party
// hat, not a rock) -- a real round-highlight needs the normal to curve
// away from the camera at the silhouette, which requires knowing which
// single sphere we're actually standing on.
vec3 wf_nearestBoulder(vec2 p, float AR) {
    vec3 best = vec3(0.0, 0.0, 0.03);
    float bestD = 1.0e9;
    vec2 c; float r; float d;
    c = vec2(0.470, 0.205) * vec2(AR, 1.0); r = 0.042; d = length(p - c) - r; if (d < bestD) { bestD = d; best = vec3(c, r); }
    c = vec2(0.565, 0.150) * vec2(AR, 1.0); r = 0.030; d = length(p - c) - r; if (d < bestD) { bestD = d; best = vec3(c, r); }
    c = vec2(0.690, 0.200) * vec2(AR, 1.0); r = 0.046; d = length(p - c) - r; if (d < bestD) { bestD = d; best = vec3(c, r); }
    c = vec2(0.615, 0.098) * vec2(AR, 1.0); r = 0.026; d = length(p - c) - r; if (d < bestD) { bestD = d; best = vec3(c, r); }
    c = vec2(0.800, 0.165) * vec2(AR, 1.0); r = 0.038; d = length(p - c) - r; if (d < bestD) { bestD = d; best = vec3(c, r); }
    c = vec2(0.885, 0.105) * vec2(AR, 1.0); r = 0.028; d = length(p - c) - r; if (d < bestD) { bestD = d; best = vec3(c, r); }
    c = vec2(0.955, 0.175) * vec2(AR, 1.0); r = 0.034; d = length(p - c) - r; if (d < bestD) { bestD = d; best = vec3(c, r); }
    return best;
}

// =============================================================================
// Scene composition
// =============================================================================
//
// Layout (p is in "world" units, x in [0, aspect], y in [0,1], y UP):
//   - dense foliage canopy along the top
//   - a rock cliff band on the left two thirds, with a gap the water falls
//     through
//   - a plunge pool under the fall
//   - a river carrying the flow off to the right, scattered with boulders
//   - everything is lit from upper-left
//
// NOTE ON smoothstep(edge0, edge1, x): GLSL only defines the result when
// edge0 < edge1. Every mask below is written so the edges are in that
// order (using `1.0 - smoothstep(lo, hi, x)` for anything that should
// fall off as x increases) -- a reversed pair compiles fine but is
// undefined behaviour per spec, and will quietly drift between the WebGL
// and native GL builds of this same file, which defeats the entire point
// of sharing one source.

vec3 wf_render(vec2 fragPx, vec2 res, float time) {
    float aspect = res.x / res.y;
    vec2 uv = fragPx / res;
    vec2 p = uv;
    p.x *= aspect;
    float AR = aspect;

    // ---- palette --------------------------------------------------------
    vec3 skyDeep   = vec3(0.016, 0.055, 0.050);
    vec3 foliageD  = vec3(0.035, 0.145, 0.075);
    vec3 foliageL  = vec3(0.145, 0.360, 0.145);
    vec3 rockD     = vec3(0.060, 0.068, 0.078);
    vec3 rockL     = vec3(0.260, 0.252, 0.236);
    vec3 mossC     = vec3(0.235, 0.420, 0.165);
    vec3 waterDeep = vec3(0.010, 0.130, 0.185);
    vec3 waterMid  = vec3(0.050, 0.360, 0.430);
    vec3 waterLite = vec3(0.260, 0.620, 0.660);
    vec3 foamC     = vec3(0.960, 0.985, 1.000);

    // ---- geometry masks ---------------------------------------------------
    float cliffX1 = 0.62 * AR;                         // cliff runs from 0..cliffX1
    float fallX0  = 0.145 * AR;                         // waterfall gap
    float fallX1  = 0.360 * AR;
    float edgeJag = wf_fbm3(vec2(p.x * 3.3, 4.0)) - 0.5;
    float cliffTop = 0.840 + 0.035 * edgeJag;           // jagged skyline of the cliff

    float poolSurf = 0.300 + 0.012 * wf_fbm3(vec2(p.x * 1.6 + time * 0.05, 9.0));
    float riverSurf = mix(poolSurf, 0.205, smoothstep(fallX1, AR, p.x))
                     + 0.018 * wf_fbm3(vec2(p.x * 2.4 - time * 0.2, 22.0));

    // the rock doesn't cut a perfectly straight vertical gap -- jitter each
    // bank by height so the fall meets the cliff along a ragged edge
    float fallJag0 = 0.018 * (wf_fbm3(vec2(p.y * 5.0, 2.0)) - 0.5);
    float fallJag1 = 0.018 * (wf_fbm3(vec2(p.y * 5.0, 31.0)) - 0.5);
    float inFallX = smoothstep(fallX0 + fallJag0 - 0.018, fallX0 + fallJag0 + 0.018, p.x)
                   * (1.0 - smoothstep(fallX1 + fallJag1 - 0.018, fallX1 + fallJag1 + 0.018, p.x));

    // is this pixel on the cliff rock (not the gap, not the water, not the sky)?
    float rockBand = step(p.x, cliffX1) * (1.0 - inFallX) * step(p.y, cliffTop) * step(riverSurf, p.y);

    float boulders = wf_bouldersSDF(p, AR);
    float onBoulder = 1.0 - smoothstep(-0.004, 0.004, boulders); // decreasing in `boulders`

    // ---------------------------------------------------------------------
    // background: sky-less dense canopy, darker with height for depth
    // ---------------------------------------------------------------------
    vec3 col = mix(skyDeep, foliageD, smoothstep(0.55, 1.0, p.y));
    float leafNoise = wf_fbm(p * 5.0 + vec2(0.0, time * 0.01));
    col = mix(col, foliageL, smoothstep(0.45, 0.85, leafNoise) * smoothstep(0.50, 1.0, p.y));

    // ---------------------------------------------------------------------
    // cliff rock face: a Voronoi diagram stands in for discrete rock
    // facets (real stone is made of joined chunks, not a smooth gradient),
    // with dark cracks exactly on cell boundaries, plus ambient occlusion
    // darkening toward the base and a thin rim at the cliff's silhouette.
    // ---------------------------------------------------------------------
    float rockLarge = wf_fbm(p * vec2(2.0, 4.5)); // large-scale tonal variation
    vec3 rockVor = wf_voronoi(p * 10.0 + vec2(rockLarge * 1.5, 0.0));
    float facetTone = floor(rockVor.z * 4.0) / 4.0; // 4 discrete per-facet tones
    vec3 rockCol = mix(rockD, rockL, 0.15 + 0.85 * facetTone);
    rockCol *= 0.70 + 0.45 * rockLarge; // large-scale light/shadow patches
    float crackEdge = smoothstep(0.0, 0.055, rockVor.y - rockVor.x); // ~0 right on a cell boundary
    rockCol = mix(rockD * 0.25, rockCol, crackEdge);
    float mossMask = smoothstep(0.55, 0.85, wf_fbm3(p * 5.0 + 3.0)) * step(0.5, rockLarge);
    rockCol = mix(rockCol, mossC, mossMask * 0.45);
    // ambient occlusion: darker where the cliff meets the water
    float baseAO = smoothstep(riverSurf, riverSurf + 0.18, p.y);
    rockCol *= mix(0.5, 1.0, baseAO);
    float edgeDist = min(abs(p.y - cliffTop), min(abs(p.x - cliffX1), min(abs(p.x - fallX0), min(abs(p.x - fallX1), abs(p.y - riverSurf)))));
    float rockOutline = 1.0 - smoothstep(0.0, 0.009, edgeDist);
    rockCol = mix(rockCol, rockD * 0.4, rockOutline);
    col = mix(col, rockCol, rockBand);

    // boulders: each one shaded as its own little hemisphere. The normal
    // gets a synthetic z-component from how far p sits inside the sphere's
    // footprint (z = sqrt(1-d^2), the standard "fake sphere" trick), which
    // is what makes the highlight curve round instead of tracing a flat
    // radial wedge across the disc.
    if (onBoulder > 0.001) {
        vec3 binfo = wf_nearestBoulder(p, AR);
        vec2 center = binfo.xy;
        float radius = max(binfo.z, 0.001);
        vec2 d2 = (p - center) / radius;
        float distSq = dot(d2, d2);
        float zc = sqrt(max(1.0 - min(distSq, 1.0), 0.0));
        vec3 normal = normalize(vec3(d2, zc));
        vec3 lightDir3 = normalize(vec3(-0.45, 0.55, 0.70));
        float lambert = clamp(dot(normal, lightDir3), 0.0, 1.0);
        float ambient = 0.30;
        float shadeAmt = ambient + (1.0 - ambient) * lambert;
        vec3 vr = wf_voronoi(p * 24.0 + center * 6.0);
        float speckTone = floor(vr.z * 3.0) / 3.0;
        vec3 boulderCol = mix(rockD, rockL, clamp(shadeAmt, 0.0, 1.0));
        boulderCol *= 0.85 + 0.3 * speckTone;
        float crackEdge2 = smoothstep(0.0, 0.08, vr.y - vr.x);
        boulderCol = mix(boulderCol * 0.6, boulderCol, crackEdge2);
        // rim darkening at grazing angles -- this is what actually reads
        // as "round" (a flat disc has no silhouette falloff at all)
        float rim = 1.0 - smoothstep(0.0, 0.35, normal.z);
        boulderCol = mix(boulderCol, rockD * 0.35, rim * 0.6);
        float moss2 = smoothstep(0.5, 0.8, wf_fbm3(p * 7.0 + 9.0)) * smoothstep(0.1, 0.6, normal.y);
        boulderCol = mix(boulderCol, mossC, moss2 * 0.4);
        col = mix(col, boulderCol, onBoulder);
    }

    // ---------------------------------------------------------------------
    // the waterfall sheet: gravity-accelerated streaks falling through the gap
    // ---------------------------------------------------------------------
    float fallMask = inFallX * step(p.y, cliffTop) * step(poolSurf, p.y) * (1.0 - onBoulder);
    if (fallMask > 0.001) {
        // local "fallen distance" 0 at the lip, 1 at the pool
        float fallDrop = clamp((cliffTop - p.y) / max(cliffTop - poolSurf, 0.001), 0.0, 1.0);
        // y(t) = 0.5*g*t^2 -> the parcel's fall speed grows with how far it
        // has already dropped, so the streak-advection speed increases with
        // fallDrop instead of being a constant scroll.
        float fallSpeed = 1.5 + 3.2 * fallDrop;
        float fallPhase = time * fallSpeed;
        vec2 streakUV = vec2(p.x * 46.0, p.y * 5.0 - fallPhase * 3.0);
        // a slow-varying per-column term gives distinct bright/dark rivulets
        // instead of one uniform sheet of color
        float colBand = wf_fbm3(vec2(p.x * 9.0, 0.4));
        float turb = wf_fbm3(streakUV) * 0.65 + wf_fbm3(streakUV * 2.15 + 7.0) * 0.35;
        float streaks = clamp((turb - 0.30) * 2.6, 0.0, 1.0);
        streaks = mix(streaks, streaks * (0.5 + 0.9 * colBand), 0.6);
        vec3 sheet = mix(waterDeep, waterLite, streaks);
        sheet = mix(sheet, vec3(1.0), pow(streaks, 3.0) * 0.5); // bright highlight cores
        // turbulent spray increases near the bottom of the fall
        float spray = smoothstep(0.55, 1.0, fallDrop) * streaks;
        sheet = mix(sheet, foamC, spray * 0.85);
        col = mix(col, sheet, fallMask);
    }

    // ---------------------------------------------------------------------
    // pool + river surface, driven by the divergence-free curl-noise flow
    // ---------------------------------------------------------------------
    float waterMask = (1.0 - rockBand) * (1.0 - onBoulder) * (1.0 - fallMask)
                     * step(p.y, riverSurf + 0.004) * step(0.0, p.y);
    if (waterMask > 0.001) {
        vec2 vField = wf_curl(p * 1.3, time);
        // blend the turbulent curl field with a strong uniform rightward
        // current so the surface clearly reads as "flowing right", not
        // just boiling in place
        vec2 vDir = normalize(mix(vec2(1.0, 0.0), normalize(vField + 1e-4), 0.45));
        float vSpeed = length(vField) * 0.6 + 0.55;

        // two-phase flow-mapped domain warp: hides the seam of an
        // ever-scrolling advection by cross-fading two offset phases
        float cycle = 1.8;
        float phase1 = mod(time, cycle) / cycle;
        float phase2 = mod(time + cycle * 0.5, cycle) / cycle;
        float blend = abs(phase1 * 2.0 - 1.0); // triangle wave 0..1..0

        // Sample noise in a basis aligned to the flow direction, stretched
        // long along the flow and compressed across it, so features read
        // as elongated current streaks instead of isotropic blobs (an
        // isotropic fbm field, whatever its scale, always looks like
        // camouflage/ink blots -- it has no preferred direction, and
        // flowing water very much does).
        vec2 flowFwd = vDir;
        vec2 flowSide = vec2(-vDir.y, vDir.x);
        vec2 pf = vec2(dot(p, flowFwd), dot(p, flowSide));

        // two noise scales: a slow, large-scale swell for broad light/dark
        // bands (what the eye reads as "water"), and a finer streak
        // layered thinly on top -- using only the fine scale at full
        // contrast is what made this look like marbled soap/cell-outline
        // wallpaper instead of water.
        vec2 uv1 = pf * vec2(1.1, 3.2) - vec2(vSpeed * phase1 * cycle, 0.0);
        vec2 uv2 = pf * vec2(1.1, 3.2) - vec2(vSpeed * phase2 * cycle, 0.0);
        float swell = mix(wf_fbm3(uv1), wf_fbm3(uv2), blend);

        vec2 fuv1 = pf * vec2(2.6, 9.0) - vec2(vSpeed * phase1 * cycle * 1.6, 0.0);
        vec2 fuv2 = pf * vec2(2.6, 9.0) - vec2(vSpeed * phase2 * cycle * 1.6, 0.0);
        float fine = mix(wf_fbm3(fuv1), wf_fbm3(fuv2), blend);

        float ripple = clamp(swell * 0.7 + fine * 0.3, 0.0, 1.0);

        // depth shading: deeper (farther below its local surface) = darker
        float depth = clamp((riverSurf - p.y) * 7.0, 0.0, 1.0);
        vec3 wcol = mix(waterLite, waterMid, smoothstep(0.3, 0.7, ripple));
        wcol = mix(wcol, waterDeep, depth * 0.5);

        // specular glints: sparse, small highlights from the fine streak
        // field's own gradient (reusing fuv1 rather than a third sample) --
        // rare and bright, not a dense web of bright outlines
        float e = 0.015;
        float hL = wf_fbm3(fuv1 + vec2(-e, 0.0) * vec2(2.6, 9.0));
        float hR = wf_fbm3(fuv1 + vec2(e, 0.0) * vec2(2.6, 9.0));
        float slope = (hR - hL) / (2.0 * e);
        float glint = smoothstep(0.8, 1.0, abs(slope) * 0.5);
        wcol = mix(wcol, foamC, glint * 0.35);

        // vorticity-estimated foam: sample curl at a tiny offset and look
        // at how much it differs locally -> shear/vorticity proxy. This is
        // where real whitewater forms, so it's kept local to the falls'
        // immediate wake and around rocks, not smeared across the pool.
        vec2 vOff = wf_curl(p * 1.3 + vec2(0.02, 0.0), time);
        float vorticity = length(vField - vOff) * 10.0;
        float rapids = smoothstep(fallX1 - 0.05, fallX1 + 0.15, p.x)
                     * (1.0 - smoothstep(fallX1 + 0.35, fallX1 + 0.65, p.x));
        float nearBoulder = 1.0 - smoothstep(0.0, 0.10, boulders);
        float foamAmt = clamp(vorticity * 0.18 + rapids * 0.16 + nearBoulder * 0.42, 0.0, 1.0);
        float foamNoise = smoothstep(0.55, 0.85, wf_fbm3(p * 18.0 - vDir * time * 2.0));
        wcol = mix(wcol, foamC, foamAmt * foamNoise * 0.75);

        // base-of-falls churn: a tighter foam patch right under the cascade
        float distFromCenter = abs(p.x - (fallX0 + fallX1) * 0.5);
        float churn = (1.0 - smoothstep(0.0, 0.09, distFromCenter))
                    * smoothstep(poolSurf - 0.10, poolSurf + 0.02, p.y);
        float churnNoise = smoothstep(0.35, 0.78, wf_fbm3(p * 14.0 - vec2(0.0, time * 2.6)));
        wcol = mix(wcol, foamC, clamp(churn * churnNoise, 0.0, 1.0) * 0.8);

        col = mix(col, wcol, waterMask);
    }

    // mist near the base of the falls, drifting upward (buoyant spray) --
    // dense at the pool surface, thinning higher up.
    float mist = smoothstep(0.5, 1.0, wf_fbm3(p * 3.0 + vec2(0.0, -time * 0.25)));
    float mistMask = inFallX * (1.0 - smoothstep(poolSurf, poolSurf + 0.22, p.y)) * 0.22;
    col += foamC * mist * mistMask;

    // gentle vignette for depth
    vec2 c = uv - 0.5;
    col *= 1.0 - 0.25 * dot(c, c);

    // Explicit gamma encode, done once here rather than trusted to either
    // backend's default framebuffer/colorspace settings. WebGL and native
    // GL disagree on whether the default framebuffer is treated as sRGB,
    // and Three.js additionally applies its own output color-space
    // conversion unless told not to -- both wrapper mains below set that
    // up so this is genuinely the ONLY gamma step applied, and the two
    // renderers end up pixel-for-pixel comparable instead of one being a
    // washed-out or darkened copy of the other.
    col = clamp(col, 0.0, 1.0);
    col = pow(col, vec3(1.0 / 2.2));

    // pixel-art palette banding (dithered in this display-referred space,
    // same as real palette-constrained pixel art, so the bands read as
    // perceptually even rather than compressed in the shadows)
    col = wf_posterizeDither(col, fragPx, 34.0);

    return clamp(col, 0.0, 1.0);
}
