// =============================================================================
// water_core_3d.glsl — the same waterfall scene, now actual 3D geometry.
//
// water_core.glsl (the original) is a flat fragment-shader "painting": every
// pixel independently decides "am I rock/water/sky" from 2D masks, with
// fake normals bolted on for lighting. It works and it's cheap, but it is
// not 3D -- there is no camera position, no real depth, nothing to orbit
// around.
//
// This file is a genuine 3D scene instead, built with sphere-trace
// raymarching: a camera shoots one ray per pixel into a signed-distance-
// field (SDF) description of the cliff, boulders, water surface and
// waterfall slab, and marches each ray forward until it hits something (or
// gives up). It is still -- deliberately -- pure math with no mesh assets,
// no textures, no `#version`/`main()` of its own, so it can be pasted into
// a WebGL wrapper and a native-GL wrapper exactly like the 2D core, and
// the camera can really orbit because the geometry is really there.
//
// Reused from water_core.glsl: wf_hash12, wf_vnoise, wf_fbm, wf_fbm3,
// wf_fbmStreak, wf_smin, wf_voronoi, wf_bayer4, wf_posterizeDither. This
// file assumes those are already defined (both wrapper mains concatenate
// water_core.glsl before this file).
// =============================================================================

// ------------------------------------------------------------------ sdfs ---
float sd_sphere(vec3 p, vec3 c, float r) { return length(p - c) - r; }

float sd_box(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

// ----------------------------------------------------------- scene layout --
// World space, y up. The cliff is a wall roughly in the x/y plane (small
// z-thickness) with a notch cut out of it; the waterfall fills that notch;
// everything below the (wavy) water level is "water"; a handful of
// boulders sit in the river downstream (+x) of the pool.
const float WF_CLIFF_TOP = 2.35;
const float WF_GAP_X0 = -1.35;
const float WF_GAP_X1 = -0.25;
const float WF_WATER_BASE = 0.0;

float wf_cliffTopJag3d(float x) {
    return WF_CLIFF_TOP + 0.22 * (wf_fbm(vec2(x * 1.1, 4.0)) - 0.5);
}

// the cliff wall, with its gap already subtracted
float wf_sdCliff3d(vec3 p) {
    float topJag = wf_cliffTopJag3d(p.x);
    vec3 q = p;
    q.y -= topJag - WF_CLIFF_TOP; // shift so the jagged top sits at the right height
    float wall = sd_box(q - vec3(-1.0, WF_CLIFF_TOP * 0.5, 0.0), vec3(3.3, WF_CLIFF_TOP * 0.5 + 0.3, 0.42));
    float gapCx = (WF_GAP_X0 + WF_GAP_X1) * 0.5;
    float gapHw = (WF_GAP_X1 - WF_GAP_X0) * 0.5;
    float gap = sd_box(q - vec3(gapCx, WF_CLIFF_TOP * 0.55, 0.0), vec3(gapHw, WF_CLIFF_TOP * 0.6, 0.6));
    return max(wall, -gap);
}

// river-bed height (dry-land reference, used only to decide where boulders
// sit) -- a gentle downstream slope plus broad undulation
float wf_bedHeight3d(vec2 xz) {
    return -0.22 - 0.035 * xz.x + 0.05 * wf_fbm3(xz * 0.3);
}

// true water SURFACE height: the 3D analogue of wf_waterHeight, periodic
// traveling waves (so it needs no seam trick) plus a slow swell, now
// literally the geometry rays bounce off instead of a color trick
float wf_waterSurface3d(vec2 xz, float t) {
    float h = WF_WATER_BASE - 0.015 * max(xz.x, 0.0); // gentle downstream drop
    h += 0.05 * sin(xz.x * 1.7 - t * 2.1);
    h += 0.025 * sin(xz.x * 3.6 + xz.y * 1.6 - t * 3.2 + 1.7);
    h += 0.016 * sin(xz.y * 4.4 - t * 1.6 + 4.0);
    h += 0.03 * wf_fbm3(xz * 0.5 - vec2(t * 0.35, 0.0));
    // a plunge-pool dip right under the falls
    float poolMask = 1.0 - smoothstep(0.0, 1.6, length(xz - vec2(-0.75, 0.55)));
    h -= 0.10 * poolMask;
    return h;
}

// water as a solid half-space below its surface -- correct SDF for "the
// region below this height field", which is exactly what a body of water is
float wf_sdWater3d(vec3 p, float t) {
    return p.y - wf_waterSurface3d(p.xz, t);
}

// the falling sheet: a thin slab sitting in the cliff's notch, bulged by
// the same kind of turbulence the 2D version used for its color, except
// here it's an actual surface displacement
float wf_sdFall3d(vec3 p, float t) {
    float gapCx = (WF_GAP_X0 + WF_GAP_X1) * 0.5;
    float halfW = (WF_GAP_X1 - WF_GAP_X0) * 0.5 - 0.06;
    vec3 q = p - vec3(gapCx, WF_CLIFF_TOP * 0.56, 0.0);
    float fallSpeed = 1.6 + 2.6 * clamp(1.0 - p.y / WF_CLIFF_TOP, 0.0, 1.0);
    float bulge = 0.035 * wf_fbmStreak(vec2(p.x * 24.0, p.y * 3.0 - t * fallSpeed * 3.2));
    q.z -= bulge;
    return sd_box(q, vec3(halfW, WF_CLIFF_TOP * 0.58, 0.035));
}

float wf_sdBoulders3d(vec3 p) {
    float d = 1.0e9;
    d = wf_smin(d, sd_sphere(p, vec3(0.35, -0.08, 0.95), 0.24), 0.14);
    d = wf_smin(d, sd_sphere(p, vec3(0.95, -0.12, -0.55), 0.20), 0.14);
    d = wf_smin(d, sd_sphere(p, vec3(1.55, -0.07, 0.65), 0.27), 0.14);
    d = wf_smin(d, sd_sphere(p, vec3(1.15, -0.15, 1.55), 0.17), 0.14);
    d = wf_smin(d, sd_sphere(p, vec3(2.35, -0.10, -0.25), 0.23), 0.14);
    d = wf_smin(d, sd_sphere(p, vec3(2.85, -0.14, 0.95), 0.18), 0.14);
    d = wf_smin(d, sd_sphere(p, vec3(0.55, -0.16, -0.85), 0.15), 0.14);
    return d;
}

// material ids
#define WF_MAT_CLIFF 1.0
#define WF_MAT_BOULDER 2.0
#define WF_MAT_WATER 3.0
#define WF_MAT_FALL 4.0

vec2 wf_map(vec3 p, float t) {
    float best = wf_sdCliff3d(p);
    float mat = WF_MAT_CLIFF;

    float dB = wf_sdBoulders3d(p);
    if (dB < best) { best = dB; mat = WF_MAT_BOULDER; }

    float dF = wf_sdFall3d(p, t);
    if (dF < best) { best = dF; mat = WF_MAT_FALL; }

    float dW = wf_sdWater3d(p, t);
    if (dW < best) { best = dW; mat = WF_MAT_WATER; }

    return vec2(best, mat);
}

// ------------------------------------------------------------ raymarching --
vec3 wf_normal(vec3 p, float t) {
    vec2 e = vec2(0.0025, 0.0);
    float c = wf_map(p, t).x;
    return normalize(vec3(
        wf_map(p + e.xyy, t).x - c,
        wf_map(p + e.yxy, t).x - c,
        wf_map(p + e.yyx, t).x - c
    ));
}

// soft shadow: march toward the light, tracking the narrowest angle the
// ray ever squeezed through (the classic IQ soft-shadow trick)
float wf_softShadow(vec3 ro, vec3 rd, float maxDist, float t) {
    float res = 1.0;
    float dist = 0.03;
    for (int i = 0; i < 24; i++) {
        float h = wf_map(ro + rd * dist, t).x;
        res = min(res, 10.0 * h / dist);
        dist += clamp(h, 0.02, 0.3);
        if (res < 0.02 || dist > maxDist) break;
    }
    return clamp(res, 0.0, 1.0);
}

// cheap ambient occlusion: how much free space is there near the surface
float wf_ao(vec3 p, vec3 n, float t) {
    float occ = 0.0;
    float scale = 1.0;
    for (int i = 1; i <= 5; i++) {
        float h = 0.03 * float(i);
        float d = wf_map(p + n * h, t).x;
        occ += (h - d) * scale;
        scale *= 0.6;
    }
    return clamp(1.0 - occ * 1.5, 0.0, 1.0);
}

// =============================================================================
// shading
// =============================================================================

vec3 wf_shadeCliff(vec3 p, vec3 n, float t) {
    vec3 rockD = vec3(0.060, 0.068, 0.078);
    vec3 rockL = vec3(0.280, 0.272, 0.252);
    vec3 mossC = vec3(0.235, 0.420, 0.165);

    // Triplanar projection: the cliff is a box, so a single p.xy Voronoi
    // sample is fine on the front face but stretches into horizontal
    // banding on the side faces (y barely changes while z sweeps the
    // whole depth there). Blend three axis-aligned samples weighted by
    // how much the normal faces each axis -- the standard fix for texturing
    // a box-like SDF without UVs.
    vec3 w = n * n;
    w /= (w.x + w.y + w.z + 1e-5);
    vec3 vrX = wf_voronoi(p.yz * 7.5);
    vec3 vrY = wf_voronoi(p.xz * 7.5 + 50.0);
    vec3 vrZ = wf_voronoi(p.xy * 7.5 + 100.0);
    vec3 vr = vrX * w.x + vrY * w.y + vrZ * w.z;

    float facetTone = floor(vr.z * 4.0) / 4.0;
    vec3 col = mix(rockD, rockL, 0.15 + 0.85 * facetTone);
    float crackEdge = smoothstep(0.0, 0.05, vr.y - vr.x);
    col = mix(rockD * 0.25, col, crackEdge);
    float mossMask = smoothstep(0.4, 0.75, n.y) * smoothstep(0.55, 0.85, wf_fbm3(p.xz * 3.0 + 3.0));
    col = mix(col, mossC, mossMask * 0.4);
    return col;
}

vec3 wf_shadeBoulder(vec3 p, vec3 n, float t) {
    vec3 rockD = vec3(0.065, 0.072, 0.080);
    vec3 rockL = vec3(0.300, 0.290, 0.265);
    vec3 mossC = vec3(0.235, 0.420, 0.165);
    vec3 vr = wf_voronoi(p.xz * 14.0 + p.y * 3.0);
    float facetTone = floor(vr.z * 3.0) / 3.0;
    vec3 col = mix(rockD, rockL, 0.2 + 0.7 * facetTone);
    float crackEdge = smoothstep(0.0, 0.07, vr.y - vr.x);
    col = mix(col * 0.6, col, crackEdge);
    float mossMask = smoothstep(0.3, 0.8, n.y);
    col = mix(col, mossC, mossMask * 0.35);
    return col;
}

vec3 wf_shadeFall(vec3 p, vec3 n, float t) {
    vec3 waterDeep = vec3(0.010, 0.130, 0.185);
    vec3 waterMid  = vec3(0.050, 0.360, 0.430);
    vec3 waterLite = vec3(0.260, 0.620, 0.660);
    vec3 foamC     = vec3(0.960, 0.985, 1.000);

    float fallDrop = clamp(1.0 - p.y / WF_CLIFF_TOP, 0.0, 1.0);
    float fallSpeed = 1.6 + 3.8 * fallDrop;
    float fallPhase = t * fallSpeed;

    float gapCx = (WF_GAP_X0 + WF_GAP_X1) * 0.5;
    float gapHalfW = (WF_GAP_X1 - WF_GAP_X0) * 0.5;
    float localX = clamp((p.x - gapCx) / max(gapHalfW, 0.001), -1.0, 1.0); // -1..1 across the fall

    float nStrands = 14.0;
    float strandPos = (localX * 0.5 + 0.5) * nStrands;
    float strandId = floor(strandPos);
    float strandFrac = fract(strandPos) - 0.5;
    float strandHalfWidth = 0.22 + 0.22 * wf_hash12(vec2(strandId, 3.0));
    float strandBright = 0.55 + 0.6 * wf_hash12(vec2(strandId, 7.0));
    float strandMask = 1.0 - smoothstep(strandHalfWidth, strandHalfWidth + 0.22, abs(strandFrac));

    vec2 streakUV = vec2(p.x * 46.0, p.y * 2.6 - fallPhase * 3.4);
    float turb = wf_fbmStreak(streakUV) * 0.7 + wf_fbmStreak(streakUV * 2.4 + 11.0) * 0.3;
    float coreStreaks = smoothstep(0.38, 0.66, turb);
    float streaks = clamp(coreStreaks * strandMask, 0.0, 1.0);

    vec3 col = mix(waterDeep * 0.85, waterMid, clamp(turb * 1.25, 0.0, 1.0));
    col = mix(col, waterLite, streaks * (0.55 + 0.3 * strandBright));
    col = mix(col, vec3(1.0), pow(streaks, 2.2) * 0.4);
    col *= mix(0.55, 1.0, strandMask);

    float spray = smoothstep(0.5, 1.0, fallDrop) * streaks;
    col = mix(col, foamC, spray * 0.7);
    return col;
}

vec3 wf_shadeWater(vec3 p, vec3 n, vec3 rd, float t) {
    vec3 waterDeep = vec3(0.010, 0.130, 0.185);
    vec3 waterMid  = vec3(0.050, 0.360, 0.430);
    vec3 waterLite = vec3(0.260, 0.620, 0.660);
    vec3 foamC     = vec3(0.960, 0.985, 1.000);
    vec3 skyCol    = vec3(0.35, 0.55, 0.52);

    float wave = wf_waterSurface3d(p.xz, t) - (WF_WATER_BASE - 0.015 * max(p.x, 0.0));
    float waveTone = smoothstep(-0.04, 0.05, wave);
    vec3 col = mix(waterMid, waterLite, waveTone);

    // Fresnel-ish rim: grazing angles reflect more sky, head-on angles show
    // more of the water body color -- real 3D normals make this free
    float fresnel = pow(1.0 - clamp(dot(n, -rd), 0.0, 1.0), 4.0);
    col = mix(col, skyCol, fresnel * 0.5);

    // foam near the base of the falls and around boulders
    float distToFall = length(p.xz - vec2((WF_GAP_X0 + WF_GAP_X1) * 0.5, 0.55));
    float churn = (1.0 - smoothstep(0.0, 1.1, distToFall))
                * smoothstep(0.35, 0.85, wf_fbm3(p.xz * 3.0 - vec2(0.0, t * 1.4)));
    float nearBoulder = 1.0 - smoothstep(0.0, 0.25, wf_sdBoulders3d(vec3(p.x, p.y, p.z)));
    float foamNoise = smoothstep(0.4, 0.8, wf_fbm3(p.xz * 6.0 - vec2(0.0, t * 1.2)));
    col = mix(col, foamC, clamp(churn * 0.6 + nearBoulder * 0.35 * foamNoise, 0.0, 1.0));

    return col;
}

// =============================================================================
// entry point: trace one camera ray, return a shaded pixel
// =============================================================================
vec3 wf_render3d(vec2 fragPx, vec2 res, float time, vec3 camPos, vec3 camTarget) {
    vec2 uv = (fragPx - 0.5 * res) / res.y;

    vec3 fwd = normalize(camTarget - camPos);
    vec3 right = normalize(cross(fwd, vec3(0.0, 1.0, 0.0)));
    vec3 up = cross(right, fwd);
    float focal = 1.6;
    vec3 rd = normalize(fwd * focal + right * uv.x + up * uv.y);
    vec3 ro = camPos;

    vec3 lightDir = normalize(vec3(-0.45, 0.62, 0.55));
    vec3 skyTop = vec3(0.035, 0.11, 0.095);
    vec3 skyBot = vec3(0.11, 0.26, 0.21);
    vec3 bg = mix(skyBot, skyTop, clamp(rd.y * 0.6 + 0.35, 0.0, 1.0));

    float dist = 0.0;
    float mat = 0.0;
    bool hit = false;
    for (int i = 0; i < 110; i++) {
        vec3 p = ro + rd * dist;
        vec2 m = wf_map(p, time);
        if (m.x < 0.0015) { mat = m.y; hit = true; break; }
        dist += m.x * 0.9;
        if (dist > 40.0) break;
    }

    vec3 col = bg;
    if (hit) {
        vec3 p = ro + rd * dist;
        vec3 n = wf_normal(p, time);

        vec3 base;
        if (mat == WF_MAT_CLIFF) base = wf_shadeCliff(p, n, time);
        else if (mat == WF_MAT_BOULDER) base = wf_shadeBoulder(p, n, time);
        else if (mat == WF_MAT_FALL) base = wf_shadeFall(p, n, time);
        else base = wf_shadeWater(p, n, rd, time);

        float ao = wf_ao(p, n, time);
        float shadow = (mat == WF_MAT_FALL) ? 1.0 : wf_softShadow(p + n * 0.01, lightDir, 5.0, time);
        float lambert = clamp(dot(n, lightDir), 0.0, 1.0);
        float ambient = 0.30;
        float lighting = ambient * ao + (1.0 - ambient) * lambert * mix(0.35, 1.0, shadow);

        vec3 halfVec = normalize(lightDir - rd);
        float specPow = (mat == WF_MAT_WATER) ? 180.0 : 24.0;
        float specAmt = (mat == WF_MAT_WATER) ? 0.6 : 0.12;
        float spec = pow(clamp(dot(n, halfVec), 0.0, 1.0), specPow) * shadow;

        col = base * lighting + vec3(1.0) * spec * specAmt;

        // distance fog ties the scene into the background gracefully
        float fog = 1.0 - exp(-dist * 0.045);
        col = mix(col, bg, clamp(fog, 0.0, 1.0));
    }

    // gentle vignette
    vec2 c = uv;
    col *= 1.0 - 0.20 * dot(c, c);

    col = clamp(col, 0.0, 1.0);
    col = pow(col, vec3(1.0 / 2.2));
    col = wf_posterizeDither(col, fragPx, 34.0);
    return clamp(col, 0.0, 1.0);
}
