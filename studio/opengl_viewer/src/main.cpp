// uaig_viewer -- native OpenGL renderer for the .uaig binary mesh format
// (see claude_studio/gl_export.py: export_gl_binary) implementing the
// exact pipeline the Undead AI spec asked for:
//
//     MODEL -> OPENGL -> LIGHTING -> 256x256 FRAMEBUFFER
//           -> PALETTE QUANTIZATION -> NEAREST NEIGHBOR UPSCALE -> SCREEN
//
// The geometry is real, lit 3D the whole way through (a vertex/fragment
// rasterizer, not a raymarched SDF like waterfall/opengl3d) -- "pixel
// art" only happens in the LAST step, where the lit 256x256 render gets
// posterized and blown up with GL_NEAREST (never GL_LINEAR, per spec).
#define GLFW_INCLUDE_NONE
#include <GLFW/glfw3.h>
#include "gl_loader.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <cmath>
#include <string>
#include <vector>
#include <fstream>

// ------------------------------------------------------------- mini-mat4 --
// No glm dependency in this sandbox; a handful of 4x4 float functions is
// all a single orbiting camera + one model matrix needs. Column-major,
// matching OpenGL's own convention (and glUniformMatrix4fv's default).
struct Mat4 {
    float m[16];
};

static Mat4 mat4_identity() {
    Mat4 r{};
    r.m[0] = r.m[5] = r.m[10] = r.m[15] = 1.0f;
    return r;
}

static Mat4 mat4_mul(const Mat4& a, const Mat4& b) {
    Mat4 r{};
    for (int c = 0; c < 4; c++) {
        for (int row = 0; row < 4; row++) {
            float sum = 0.0f;
            for (int k = 0; k < 4; k++) sum += a.m[k * 4 + row] * b.m[c * 4 + k];
            r.m[c * 4 + row] = sum;
        }
    }
    return r;
}

static Mat4 mat4_perspective(float fovy_rad, float aspect, float znear, float zfar) {
    Mat4 r{};
    float f = 1.0f / tanf(fovy_rad * 0.5f);
    r.m[0] = f / aspect;
    r.m[5] = f;
    r.m[10] = (zfar + znear) / (znear - zfar);
    r.m[11] = -1.0f;
    r.m[14] = (2.0f * zfar * znear) / (znear - zfar);
    return r;
}

struct Vec3 { float x, y, z; };
static Vec3 v3sub(Vec3 a, Vec3 b) { return {a.x - b.x, a.y - b.y, a.z - b.z}; }
static Vec3 v3cross(Vec3 a, Vec3 b) { return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x}; }
static float v3len(Vec3 a) { return sqrtf(a.x * a.x + a.y * a.y + a.z * a.z); }
static Vec3 v3norm(Vec3 a) { float l = v3len(a); return l > 1e-8f ? Vec3{a.x / l, a.y / l, a.z / l} : Vec3{0, 0, 1}; }

static Mat4 mat4_lookat(Vec3 eye, Vec3 center, Vec3 up) {
    Vec3 f = v3norm(v3sub(center, eye));
    Vec3 s = v3norm(v3cross(f, up));
    Vec3 u = v3cross(s, f);
    Mat4 r = mat4_identity();
    r.m[0] = s.x; r.m[4] = s.y; r.m[8] = s.z;
    r.m[1] = u.x; r.m[5] = u.y; r.m[9] = u.z;
    r.m[2] = -f.x; r.m[6] = -f.y; r.m[10] = -f.z;
    r.m[12] = -(s.x * eye.x + s.y * eye.y + s.z * eye.z);
    r.m[13] = -(u.x * eye.x + u.y * eye.y + u.z * eye.z);
    r.m[14] = (f.x * eye.x + f.y * eye.y + f.z * eye.z);
    return r;
}

// ------------------------------------------------------- .uaig loading ----
struct GLMaterial {
    std::string name;
    float baseColor[3];
    float emission[3];
};
struct GLSubmesh {
    std::string name;
    uint32_t materialIndex;
    uint32_t indexOffset;
    uint32_t indexCount;
};
struct Vertex {
    float px, py, pz;
    float nx, ny, nz;
    float u, v;
};
struct UaigMesh {
    std::vector<GLMaterial> materials;
    std::vector<GLSubmesh> submeshes;
    std::vector<Vertex> vertices;
    std::vector<uint32_t> indices;
};

static std::string readName(std::ifstream& f) {
    uint32_t len = 0;
    f.read(reinterpret_cast<char*>(&len), sizeof(len));
    std::string s(len, '\0');
    f.read(s.data(), len);
    return s;
}

static UaigMesh loadUaig(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) {
        fprintf(stderr, "Failed to open %s\n", path.c_str());
        exit(1);
    }
    char magic[4];
    f.read(magic, 4);
    if (memcmp(magic, "UAIG", 4) != 0) {
        fprintf(stderr, "Not a UAIG file: %s\n", path.c_str());
        exit(1);
    }
    uint32_t version, nMat, nSub, nVert, nIdx;
    f.read(reinterpret_cast<char*>(&version), 4);
    f.read(reinterpret_cast<char*>(&nMat), 4);
    f.read(reinterpret_cast<char*>(&nSub), 4);
    f.read(reinterpret_cast<char*>(&nVert), 4);
    f.read(reinterpret_cast<char*>(&nIdx), 4);

    UaigMesh mesh;
    mesh.materials.reserve(nMat);
    for (uint32_t i = 0; i < nMat; i++) {
        GLMaterial m;
        m.name = readName(f);
        f.read(reinterpret_cast<char*>(m.baseColor), sizeof(float) * 3);
        f.read(reinterpret_cast<char*>(m.emission), sizeof(float) * 3);
        mesh.materials.push_back(m);
    }
    mesh.submeshes.reserve(nSub);
    for (uint32_t i = 0; i < nSub; i++) {
        GLSubmesh s;
        s.name = readName(f);
        f.read(reinterpret_cast<char*>(&s.materialIndex), 4);
        f.read(reinterpret_cast<char*>(&s.indexOffset), 4);
        f.read(reinterpret_cast<char*>(&s.indexCount), 4);
        mesh.submeshes.push_back(s);
    }
    mesh.vertices.resize(nVert);
    f.read(reinterpret_cast<char*>(mesh.vertices.data()), sizeof(Vertex) * nVert);
    mesh.indices.resize(nIdx);
    f.read(reinterpret_cast<char*>(mesh.indices.data()), sizeof(uint32_t) * nIdx);

    printf("Loaded %s: %u vertices, %u indices, %u submeshes, %u materials\n",
           path.c_str(), nVert, nIdx, nSub, nMat);
    return mesh;
}

// ------------------------------------------------------------- shaders ----
static const char* kVertexSrc =
    "#version 330 core\n"
    "layout(location = 0) in vec3 aPos;\n"
    "layout(location = 1) in vec3 aNormal;\n"
    "layout(location = 2) in vec2 aUV;\n"
    "uniform mat4 uMVP;\n"
    "out vec3 vNormal;\n"
    "void main() {\n"
    "    vNormal = aNormal;\n"
    "    gl_Position = uMVP * vec4(aPos, 1.0);\n"
    "}\n";

// Flat per-submesh base color + emission (no texture lookup -- these
// parts are flat-material hard-surface plates, matching the "flat
// shading, hard-surface" instruction from the spec), lit with a simple
// two-light Lambert + ambient term.
// Emissive parts (beacon, eyes, chest lights, the sword's corrupt arcs,
// the base's fire/electric aura) flicker in real time instead of holding
// a flat brightness -- two mismatched sine waves (an irregular beat, not
// a clean pulse) combined with a per-submesh phase offset so every glow
// on the model crackles out of sync with the others rather than in
// lockstep.
static const char* kFragSrc =
    "#version 330 core\n"
    "in vec3 vNormal;\n"
    "out vec4 FragColor;\n"
    "uniform vec3 uBaseColor;\n"
    "uniform vec3 uEmission;\n"
    "uniform vec3 uLightDir1;\n"
    "uniform vec3 uLightDir2;\n"
    "uniform float uTime;\n"
    "uniform float uFlickerSeed;\n"
    "void main() {\n"
    "    vec3 n = normalize(vNormal);\n"
    "    float l1 = max(dot(n, uLightDir1), 0.0);\n"
    "    float l2 = max(dot(n, uLightDir2), 0.0) * 0.4;\n"
    "    float ambient = 0.38;\n"
    "    vec3 lit = uBaseColor * (ambient + (1.0 - ambient) * (l1 + l2));\n"
    "    float ph = uFlickerSeed * 6.2831853;\n"
    "    float flicker = 0.78 + 0.34 * sin(uTime * 7.3 + ph) * sin(uTime * 2.6 + ph * 1.7);\n"
    "    FragColor = vec4(lit + uEmission * flicker, 1.0);\n"
    "}\n";

static const char* kPresentVertSrc =
    "#version 330 core\n"
    "out vec2 vUv;\n"
    "void main() {\n"
    "    vec2 pos[3] = vec2[3](vec2(-1.0, -1.0), vec2(3.0, -1.0), vec2(-1.0, 3.0));\n"
    "    vUv = (pos[gl_VertexID] + 1.0) * 0.5;\n"
    "    gl_Position = vec4(pos[gl_VertexID], 0.0, 1.0);\n"
    "}\n";

// The "PALETTE QUANTIZATION" step: posterize each channel to a fixed
// number of levels before the nearest-upscale, same idea as
// water_core.glsl's wf_posterizeDither but without the Bayer dither (a
// clean hard quantize reads more like a limited hardware palette, which
// is the brief here, vs. water_core.glsl's deliberately softer "painted"
// look).
static const char* kPresentFragSrc =
    "#version 330 core\n"
    "in vec2 vUv;\n"
    "out vec4 FragColor;\n"
    "uniform sampler2D uTex;\n"
    "uniform float uLevels;\n"
    "void main() {\n"
    "    vec3 c = texture(uTex, vUv).rgb;\n"
    "    c = floor(c * uLevels + 0.5) / uLevels;\n"
    "    FragColor = vec4(c, 1.0);\n"
    "}\n";

static GLuint compileShader(GLenum type, const char* src) {
    GLuint sh = glCreateShader(type);
    glShaderSource(sh, 1, &src, nullptr);
    glCompileShader(sh);
    GLint ok = 0;
    glGetShaderiv(sh, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[4096];
        GLsizei n = 0;
        glGetShaderInfoLog(sh, sizeof(log), &n, log);
        fprintf(stderr, "Shader compile error:\n%.*s\n", n, log);
        exit(1);
    }
    return sh;
}

static GLuint linkProgram(GLuint vs, GLuint fs) {
    GLuint prog = glCreateProgram();
    glAttachShader(prog, vs);
    glAttachShader(prog, fs);
    glLinkProgram(prog);
    GLint ok = 0;
    glGetProgramiv(prog, GL_LINK_STATUS, &ok);
    if (!ok) {
        char log[4096];
        GLsizei n = 0;
        glGetProgramInfoLog(prog, sizeof(log), &n, log);
        fprintf(stderr, "Program link error:\n%.*s\n", n, log);
        exit(1);
    }
    return prog;
}

// ---------------------------------------------------------- orbit camera --
static double g_orbitAz = 0.6, g_orbitEl = 0.25, g_orbitDist = 7.3;
static bool g_autorotate = true;
static double g_idleUntil = 0.0;

static void scrollCallback(GLFWwindow*, double, double dy) {
    g_orbitDist -= dy * 0.4;
    if (g_orbitDist < 2.5) g_orbitDist = 2.5;
    if (g_orbitDist > 25.0) g_orbitDist = 25.0;
    g_autorotate = false;
    g_idleUntil = glfwGetTime() + 2.5;
}

int main(int argc, char** argv) {
    std::string meshPath = "../../exports/undead_ai.uaig";
    int internalRes = 256;      // per spec: 256x256 internal framebuffer
    float paletteLevels = 20.0f;
    std::string screenshotPath;
    double screenshotAfter = 1.5;
    std::string turntableDir;
    int turntableFrames = 0;
    double turntableSeconds = 4.0;
    double turntableEl = 0.30;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--mesh") && i + 1 < argc) meshPath = argv[++i];
        else if (!strcmp(argv[i], "--res") && i + 1 < argc) internalRes = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--levels") && i + 1 < argc) paletteLevels = (float)atof(argv[++i]);
        else if (!strcmp(argv[i], "--screenshot") && i + 1 < argc) screenshotPath = argv[++i];
        else if (!strcmp(argv[i], "--after") && i + 1 < argc) screenshotAfter = atof(argv[++i]);
        else if (!strcmp(argv[i], "--orbit") && i + 2 < argc) {
            g_orbitAz = atof(argv[++i]);
            g_orbitEl = atof(argv[++i]);
            g_autorotate = false;
        }
        else if (!strcmp(argv[i], "--turntable") && i + 2 < argc) {
            turntableDir = argv[++i];
            turntableFrames = atoi(argv[++i]);
        }
        else if (!strcmp(argv[i], "--turntable-seconds") && i + 1 < argc) turntableSeconds = atof(argv[++i]);
        else if (!strcmp(argv[i], "--turntable-el") && i + 1 < argc) turntableEl = atof(argv[++i]);
    }

    UaigMesh mesh = loadUaig(meshPath);

    if (!glfwInit()) { fprintf(stderr, "glfwInit failed\n"); return 1; }
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
#ifdef __APPLE__
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
#endif

    int winW = 960, winH = 960;
    GLFWwindow* window = glfwCreateWindow(winW, winH, "UAIG Viewer -- Undead AI (pixel-art pipeline)", nullptr, nullptr);
    if (!window) { fprintf(stderr, "glfwCreateWindow failed\n"); glfwTerminate(); return 1; }
    glfwMakeContextCurrent(window);
    glfwSwapInterval(1);
    glfwSetScrollCallback(window, scrollCallback);

    if (!wf_gl_load((wf_GLLoadFunc)glfwGetProcAddress)) {
        fprintf(stderr, "Failed to resolve required OpenGL 3.3 entry points\n");
        return 1;
    }
    printf("GL_VERSION:  %s\n", glGetString(GL_VERSION));
    printf("GL_RENDERER: %s\n", glGetString(GL_RENDERER));

    GLuint vs = compileShader(GL_VERTEX_SHADER, kVertexSrc);
    GLuint fs = compileShader(GL_FRAGMENT_SHADER, kFragSrc);
    GLuint meshProg = linkProgram(vs, fs);
    GLint uMVP = glGetUniformLocation(meshProg, "uMVP");
    GLint uBaseColor = glGetUniformLocation(meshProg, "uBaseColor");
    GLint uEmission = glGetUniformLocation(meshProg, "uEmission");
    GLint uLightDir1 = glGetUniformLocation(meshProg, "uLightDir1");
    GLint uLightDir2 = glGetUniformLocation(meshProg, "uLightDir2");
    GLint uTime = glGetUniformLocation(meshProg, "uTime");
    GLint uFlickerSeed = glGetUniformLocation(meshProg, "uFlickerSeed");

    GLuint pvs = compileShader(GL_VERTEX_SHADER, kPresentVertSrc);
    GLuint pfs = compileShader(GL_FRAGMENT_SHADER, kPresentFragSrc);
    GLuint presentProg = linkProgram(pvs, pfs);
    GLint uTex = glGetUniformLocation(presentProg, "uTex");
    GLint uLevels = glGetUniformLocation(presentProg, "uLevels");

    // ---- mesh VAO/VBO/EBO ----
    GLuint vao, vbo, ebo;
    glGenVertexArrays(1, &vao);
    glBindVertexArray(vao);
    glGenBuffers(1, &vbo);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, mesh.vertices.size() * sizeof(Vertex), mesh.vertices.data(), GL_STATIC_DRAW);
    glGenBuffers(1, &ebo);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, mesh.indices.size() * sizeof(uint32_t), mesh.indices.data(), GL_STATIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)offsetof(Vertex, px));
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)offsetof(Vertex, nx));
    glEnableVertexAttribArray(2);
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)offsetof(Vertex, u));

    GLuint presentVao;
    glGenVertexArrays(1, &presentVao);

    // ---- 256x256 internal framebuffer ----
    GLuint fbo, colorTex, depthRbo;
    glGenFramebuffers(1, &fbo);
    glBindFramebuffer(GL_FRAMEBUFFER, fbo);
    glGenTextures(1, &colorTex);
    glBindTexture(GL_TEXTURE_2D, colorTex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, internalRes, internalRes, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST); // spec: never GL_LINEAR
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, colorTex, 0);

    PFNGLGENRENDERBUFFERSPROC glGenRenderbuffers = (PFNGLGENRENDERBUFFERSPROC)glfwGetProcAddress("glGenRenderbuffers");
    PFNGLBINDRENDERBUFFERPROC glBindRenderbuffer = (PFNGLBINDRENDERBUFFERPROC)glfwGetProcAddress("glBindRenderbuffer");
    PFNGLRENDERBUFFERSTORAGEPROC glRenderbufferStorage = (PFNGLRENDERBUFFERSTORAGEPROC)glfwGetProcAddress("glRenderbufferStorage");
    PFNGLFRAMEBUFFERRENDERBUFFERPROC glFramebufferRenderbuffer = (PFNGLFRAMEBUFFERRENDERBUFFERPROC)glfwGetProcAddress("glFramebufferRenderbuffer");
    glGenRenderbuffers(1, &depthRbo);
    glBindRenderbuffer(GL_RENDERBUFFER, depthRbo);
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, internalRes, internalRes);
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depthRbo);

    if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) {
        fprintf(stderr, "Framebuffer incomplete\n");
        return 1;
    }
    glBindFramebuffer(GL_FRAMEBUFFER, 0);

    // bounding-box center, for an orbit target that works for any loaded mesh
    float minX = 1e9f, maxX = -1e9f, minY = 1e9f, maxY = -1e9f, minZ = 1e9f, maxZ = -1e9f;
    for (auto& v : mesh.vertices) {
        minX = fminf(minX, v.px); maxX = fmaxf(maxX, v.px);
        minY = fminf(minY, v.py); maxY = fmaxf(maxY, v.py);
        minZ = fminf(minZ, v.pz); maxZ = fmaxf(maxZ, v.pz);
    }
    Vec3 target = {(minX + maxX) * 0.5f, (minY + maxY) * 0.5f, (minZ + maxZ) * 0.5f};

    // ---- turntable mode: render N frames of a full rotation to disk and
    // exit, instead of opening the interactive window loop. One process,
    // one GL context/shader-compile, N cheap re-renders -- much faster
    // than spawning the whole app per frame the way a single --screenshot
    // capture does. ----
    if (!turntableDir.empty() && turntableFrames > 0) {
        for (int fi = 0; fi < turntableFrames; fi++) {
            double frameT = (double)fi / (double)turntableFrames * turntableSeconds;
            g_orbitAz = (double)fi / (double)turntableFrames * 2.0 * M_PI;
            g_orbitEl = turntableEl;

            Vec3 eye = {
                target.x + (float)(g_orbitDist * cos(g_orbitEl) * sin(g_orbitAz)),
                target.y + (float)(g_orbitDist * sin(g_orbitEl)),
                target.z + (float)(g_orbitDist * cos(g_orbitEl) * cos(g_orbitAz)),
            };
            Mat4 view = mat4_lookat(eye, target, Vec3{0, 1, 0});
            Mat4 proj = mat4_perspective(50.0f * (float)M_PI / 180.0f, 1.0f, 0.1f, 100.0f);
            Mat4 vp = mat4_mul(proj, view);

            glBindFramebuffer(GL_FRAMEBUFFER, fbo);
            glViewport(0, 0, internalRes, internalRes);
            glClearColor(0.03f, 0.035f, 0.045f, 1.0f);
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
            glEnable(GL_DEPTH_TEST);
            glUseProgram(meshProg);
            glUniformMatrix4fv(uMVP, 1, GL_FALSE, vp.m);
            glUniform3f(uLightDir1, -0.45f, 0.70f, 0.55f);
            glUniform3f(uLightDir2, 0.6f, 0.3f, -0.4f);
            glUniform1f(uTime, (float)frameT);
            glBindVertexArray(vao);
            for (size_t smi = 0; smi < mesh.submeshes.size(); smi++) {
                auto& sm = mesh.submeshes[smi];
                const GLMaterial& mat = mesh.materials[sm.materialIndex];
                glUniform3f(uBaseColor, mat.baseColor[0], mat.baseColor[1], mat.baseColor[2]);
                glUniform3f(uEmission, mat.emission[0], mat.emission[1], mat.emission[2]);
                float seed = fmodf((float)smi * 0.6180339887f, 1.0f);
                glUniform1f(uFlickerSeed, seed);
                glDrawElements(GL_TRIANGLES, sm.indexCount, GL_UNSIGNED_INT,
                                (void*)(uintptr_t)(sm.indexOffset * sizeof(uint32_t)));
            }

            glBindFramebuffer(GL_FRAMEBUFFER, 0);
            int fbW, fbH;
            glfwGetFramebufferSize(window, &fbW, &fbH);
            glViewport(0, 0, fbW, fbH);
            glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
            glClear(GL_COLOR_BUFFER_BIT);
            glDisable(GL_DEPTH_TEST);
            glUseProgram(presentProg);
            glActiveTexture(GL_TEXTURE0);
            glBindTexture(GL_TEXTURE_2D, colorTex);
            glUniform1i(uTex, 0);
            glUniform1f(uLevels, paletteLevels);
            glBindVertexArray(presentVao);
            glDrawArrays(GL_TRIANGLES, 0, 3);

            std::vector<uint8_t> pixels((size_t)fbW * fbH * 3);
            glPixelStorei(GL_PACK_ALIGNMENT, 1);
            glReadPixels(0, 0, fbW, fbH, GL_RGB, GL_UNSIGNED_BYTE, pixels.data());
            std::vector<uint8_t> flipped((size_t)fbW * fbH * 3);
            for (int y = 0; y < fbH; y++)
                memcpy(&flipped[(size_t)y * fbW * 3], &pixels[(size_t)(fbH - 1 - y) * fbW * 3], (size_t)fbW * 3);
            char outPath[1024];
            snprintf(outPath, sizeof(outPath), "%s/frame_%04d.ppm", turntableDir.c_str(), fi);
            std::ofstream out(outPath, std::ios::binary);
            out << "P6\n" << fbW << " " << fbH << "\n255\n";
            out.write(reinterpret_cast<char*>(flipped.data()), flipped.size());
            glfwSwapBuffers(window);
            glfwPollEvents();
        }
        printf("turntable: wrote %d frames to %s\n", turntableFrames, turntableDir.c_str());
        glfwTerminate();
        return 0;
    }

    double t0 = glfwGetTime();
    bool shotTaken = screenshotPath.empty();
    double lastMouseX = 0, lastMouseY = 0;
    bool haveLastMouse = false;

    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();
        if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS) glfwSetWindowShouldClose(window, GLFW_TRUE);

        double mx, my;
        glfwGetCursorPos(window, &mx, &my);
        bool dragging = glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_LEFT) == GLFW_PRESS;
        if (dragging) {
            if (haveLastMouse) {
                g_orbitAz -= (mx - lastMouseX) * 0.006;
                g_orbitEl += (my - lastMouseY) * 0.006;
                if (g_orbitEl < -1.4) g_orbitEl = -1.4;
                if (g_orbitEl > 1.4) g_orbitEl = 1.4;
            }
            g_autorotate = false;
            g_idleUntil = glfwGetTime() + 4.0;
        }
        lastMouseX = mx; lastMouseY = my; haveLastMouse = true;
        if (!g_autorotate && glfwGetTime() > g_idleUntil) g_autorotate = true;

        double t = glfwGetTime() - t0;
        if (g_autorotate) g_orbitAz += (1.0 / 60.0) * 0.12;

        Vec3 eye = {
            target.x + (float)(g_orbitDist * cos(g_orbitEl) * sin(g_orbitAz)),
            target.y + (float)(g_orbitDist * sin(g_orbitEl)),
            target.z + (float)(g_orbitDist * cos(g_orbitEl) * cos(g_orbitAz)),
        };
        Mat4 view = mat4_lookat(eye, target, Vec3{0, 1, 0});
        Mat4 proj = mat4_perspective(50.0f * (float)M_PI / 180.0f, 1.0f, 0.1f, 100.0f);
        Mat4 vp = mat4_mul(proj, view);

        // ---- pass 1: render the lit mesh into the 256x256 target ----
        glBindFramebuffer(GL_FRAMEBUFFER, fbo);
        glViewport(0, 0, internalRes, internalRes);
        glClearColor(0.03f, 0.035f, 0.045f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        glEnable(GL_DEPTH_TEST);
        glUseProgram(meshProg);
        glUniformMatrix4fv(uMVP, 1, GL_FALSE, vp.m);
        glUniform3f(uLightDir1, -0.45f, 0.70f, 0.55f);
        glUniform3f(uLightDir2, 0.6f, 0.3f, -0.4f);
        glUniform1f(uTime, (float)glfwGetTime());
        glBindVertexArray(vao);
        for (size_t smi = 0; smi < mesh.submeshes.size(); smi++) {
            auto& sm = mesh.submeshes[smi];
            const GLMaterial& mat = mesh.materials[sm.materialIndex];
            glUniform3f(uBaseColor, mat.baseColor[0], mat.baseColor[1], mat.baseColor[2]);
            glUniform3f(uEmission, mat.emission[0], mat.emission[1], mat.emission[2]);
            // a cheap deterministic per-submesh hash in [0,1) so every
            // glowing part flickers on its own, out-of-sync phase
            float seed = fmodf((float)smi * 0.6180339887f, 1.0f);
            glUniform1f(uFlickerSeed, seed);
            glDrawElements(GL_TRIANGLES, sm.indexCount, GL_UNSIGNED_INT,
                            (void*)(uintptr_t)(sm.indexOffset * sizeof(uint32_t)));
        }

        // ---- pass 2: palette quantize + nearest-upscale to the window ----
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        int fbW, fbH;
        glfwGetFramebufferSize(window, &fbW, &fbH);
        glViewport(0, 0, fbW, fbH);
        glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);
        glDisable(GL_DEPTH_TEST);
        glUseProgram(presentProg);
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, colorTex);
        glUniform1i(uTex, 0);
        glUniform1f(uLevels, paletteLevels);
        glBindVertexArray(presentVao);
        glDrawArrays(GL_TRIANGLES, 0, 3);

        if (!shotTaken && t >= screenshotAfter) {
            std::vector<uint8_t> pixels((size_t)fbW * fbH * 3);
            glPixelStorei(GL_PACK_ALIGNMENT, 1);
            glReadPixels(0, 0, fbW, fbH, GL_RGB, GL_UNSIGNED_BYTE, pixels.data());
            std::vector<uint8_t> flipped((size_t)fbW * fbH * 3);
            for (int y = 0; y < fbH; y++)
                memcpy(&flipped[(size_t)y * fbW * 3], &pixels[(size_t)(fbH - 1 - y) * fbW * 3], (size_t)fbW * 3);
            std::ofstream out(screenshotPath, std::ios::binary);
            out << "P6\n" << fbW << " " << fbH << "\n255\n";
            out.write(reinterpret_cast<char*>(flipped.data()), flipped.size());
            printf("wrote screenshot: %s (%dx%d)\n", screenshotPath.c_str(), fbW, fbH);
            shotTaken = true;
            glfwSetWindowShouldClose(window, GLFW_TRUE);
        }

        glfwSwapBuffers(window);
    }

    glfwTerminate();
    return 0;
}
