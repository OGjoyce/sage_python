// CraftFlow -- native OpenGL twin of the Three.js waterfall.
//
// Same shared/water_core.glsl, same uniforms (uTime, uResolution), same
// "render small, upscale with nearest filtering" pixel-art pipeline. If
// this window and the browser window ever disagree, the bug lives in one
// of the two wrapper shaders below, not in the math.
#define GLFW_INCLUDE_NONE
#include <GLFW/glfw3.h>
#include "gl_loader.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>

#ifndef WATER_CORE_PATH
#define WATER_CORE_PATH "../shared/water_core.glsl"
#endif

static std::string readFile(const std::string& path) {
    std::ifstream f(path, std::ios::in | std::ios::binary);
    if (!f) {
        fprintf(stderr, "Failed to open \"%s\" (run from the opengl/ build dir, "
                         "or rebuild so WATER_CORE_PATH points at shared/water_core.glsl)\n",
                path.c_str());
        exit(1);
    }
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

static GLuint compileShader(GLenum type, const std::string& src) {
    GLuint sh = glCreateShader(type);
    const char* csrc = src.c_str();
    GLint len = (GLint)src.size();
    glShaderSource(sh, 1, &csrc, &len);
    glCompileShader(sh);
    GLint ok = 0;
    glGetShaderiv(sh, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[8192];
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
        char log[8192];
        GLsizei n = 0;
        glGetProgramInfoLog(prog, sizeof(log), &n, log);
        fprintf(stderr, "Program link error:\n%.*s\n", n, log);
        exit(1);
    }
    return prog;
}

// A fullscreen triangle generated purely from gl_VertexID -- no VBO, no
// vertex attributes. Core profile still requires *some* VAO bound for a
// draw call even when nothing is read from it, which is the only reason
// main() below creates one.
static const char* kVertexSrc =
    "#version 330 core\n"
    "out vec2 vUv;\n"
    "void main() {\n"
    "    vec2 pos[3] = vec2[3](vec2(-1.0, -1.0), vec2(3.0, -1.0), vec2(-1.0, 3.0));\n"
    "    vUv = (pos[gl_VertexID] + 1.0) * 0.5;\n"
    "    gl_Position = vec4(pos[gl_VertexID], 0.0, 1.0);\n"
    "}\n";

static std::string buildWaterFragmentSrc(const std::string& core) {
    std::ostringstream ss;
    ss << "#version 330 core\n"
          "in vec2 vUv;\n"
          "out vec4 FragColor;\n"
          "uniform float uTime;\n"
          "uniform vec2 uResolution;\n"
          "\n"
       << core
       << "\n"
          "void main() {\n"
          "    vec2 fragPx = vUv * uResolution;\n"
          "    vec3 col = wf_render(fragPx, uResolution, uTime);\n"
          "    FragColor = vec4(col, 1.0);\n"
          "}\n";
    return ss.str();
}

static const char* kPresentFragSrc =
    "#version 330 core\n"
    "in vec2 vUv;\n"
    "out vec4 FragColor;\n"
    "uniform sampler2D uTex;\n"
    "void main() { FragColor = texture(uTex, vUv); }\n";

struct Target {
    GLuint fbo = 0, tex = 0;
    int w = 0, h = 0;
};

static Target createTarget(int w, int h) {
    Target t;
    t.w = w;
    t.h = h;
    glGenTextures(1, &t.tex);
    glBindTexture(GL_TEXTURE_2D, t.tex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);

    glGenFramebuffers(1, &t.fbo);
    glBindFramebuffer(GL_FRAMEBUFFER, t.fbo);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, t.tex, 0);
    GLenum status = glCheckFramebufferStatus(GL_FRAMEBUFFER);
    if (status != GL_FRAMEBUFFER_COMPLETE) {
        fprintf(stderr, "Framebuffer incomplete: 0x%x\n", status);
        exit(1);
    }
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    return t;
}

static void destroyTarget(Target& t) {
    if (t.fbo) glDeleteFramebuffers(1, &t.fbo);
    if (t.tex) glDeleteTextures(1, &t.tex);
    t.fbo = t.tex = 0;
}

// Minimal binary PPM (P6) writer -- zero dependencies, and trivially
// converted to PNG with `convert shot.ppm shot.png` or Python/Pillow.
// This exists so the project can be smoke-tested in CI / headlessly
// (this is literally how the two renderers in this repo were visually
// diffed against each other during development) without pulling in a
// PNG-writing library for a debug feature.
static void writePPM(const std::string& path, int w, int h, const std::vector<uint8_t>& rgbTopDown) {
    std::ofstream f(path, std::ios::out | std::ios::binary);
    f << "P6\n" << w << " " << h << "\n255\n";
    f.write(reinterpret_cast<const char*>(rgbTopDown.data()), (std::streamsize)rgbTopDown.size());
}

int main(int argc, char** argv) {
    int pixelSize = 2;
    std::string screenshotPath;
    double screenshotAfter = 2.0;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--pixel-size") && i + 1 < argc) {
            pixelSize = atoi(argv[++i]);
        } else if (!strcmp(argv[i], "--screenshot") && i + 1 < argc) {
            screenshotPath = argv[++i];
        } else if (!strcmp(argv[i], "--after") && i + 1 < argc) {
            screenshotAfter = atof(argv[++i]);
        }
    }
    if (pixelSize < 1) pixelSize = 1;

    if (!glfwInit()) {
        fprintf(stderr, "glfwInit failed\n");
        return 1;
    }
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
#ifdef __APPLE__
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
#endif

    int winW = 1280, winH = 720;
    GLFWwindow* window = glfwCreateWindow(winW, winH, "CraftFlow -- Waterfall (native OpenGL)", nullptr, nullptr);
    if (!window) {
        fprintf(stderr, "glfwCreateWindow failed\n");
        glfwTerminate();
        return 1;
    }
    glfwMakeContextCurrent(window);
    glfwSwapInterval(1);

    if (!wf_gl_load((wf_GLLoadFunc)glfwGetProcAddress)) {
        fprintf(stderr, "Failed to resolve one or more required OpenGL 3.3 entry points\n");
        return 1;
    }

    printf("GL_VERSION:  %s\n", glGetString(GL_VERSION));
    printf("GL_RENDERER: %s\n", glGetString(GL_RENDERER));

    std::string coreSrc = readFile(WATER_CORE_PATH);
    std::string waterFragSrc = buildWaterFragmentSrc(coreSrc);

    GLuint vs = compileShader(GL_VERTEX_SHADER, kVertexSrc);
    GLuint waterFs = compileShader(GL_FRAGMENT_SHADER, waterFragSrc);
    GLuint waterProg = linkProgram(vs, waterFs);

    GLuint presentFs = compileShader(GL_FRAGMENT_SHADER, kPresentFragSrc);
    GLuint presentProg = linkProgram(vs, presentFs);

    GLuint vao;
    glGenVertexArrays(1, &vao);

    GLint uTimeLoc = glGetUniformLocation(waterProg, "uTime");
    GLint uResLoc  = glGetUniformLocation(waterProg, "uResolution");
    GLint uTexLoc  = glGetUniformLocation(presentProg, "uTex");

    Target target{};
    int lastW = -1, lastH = -1;

    auto rebuildTarget = [&](int ww, int wh) {
        int lowW = ww / pixelSize; if (lowW < 2) lowW = 2;
        int lowH = wh / pixelSize; if (lowH < 2) lowH = 2;
        if (target.fbo) destroyTarget(target);
        target = createTarget(lowW, lowH);
        printf("internal resolution: %dx%d (pixel size %d)\n", lowW, lowH, pixelSize);
    };

    double t0 = glfwGetTime();
    bool shotTaken = screenshotPath.empty();

    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();

        if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS)
            glfwSetWindowShouldClose(window, GLFW_TRUE);

        static bool lbHeld = false, rbHeld = false;
        bool lbNow = glfwGetKey(window, GLFW_KEY_LEFT_BRACKET) == GLFW_PRESS;
        bool rbNow = glfwGetKey(window, GLFW_KEY_RIGHT_BRACKET) == GLFW_PRESS;

        int curW, curH;
        glfwGetFramebufferSize(window, &curW, &curH);

        if (lbNow && !lbHeld && pixelSize < 12) { pixelSize++; rebuildTarget(curW, curH); }
        if (rbNow && !rbHeld && pixelSize > 1)  { pixelSize--; rebuildTarget(curW, curH); }
        lbHeld = lbNow;
        rbHeld = rbNow;

        if (curW != lastW || curH != lastH) {
            rebuildTarget(curW, curH);
            lastW = curW;
            lastH = curH;
        }

        double t = glfwGetTime() - t0;

        // ---- pass 1: render the water shader into the low-res target ----
        glBindFramebuffer(GL_FRAMEBUFFER, target.fbo);
        glViewport(0, 0, target.w, target.h);
        glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);
        glUseProgram(waterProg);
        glUniform1f(uTimeLoc, (float)t);
        glUniform2f(uResLoc, (float)target.w, (float)target.h);
        glBindVertexArray(vao);
        glDrawArrays(GL_TRIANGLES, 0, 3);

        // ---- pass 2: nearest-upscale, integer-scaled and letterboxed ----
        // (same reasoning as threejs/main.js: a non-integer stretch factor
        // duplicates source columns unevenly under GL_NEAREST and shows up
        // as moire, so we size the blit to an exact multiple and center it)
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glViewport(0, 0, curW, curH);
        glClearColor(0.008f, 0.016f, 0.012f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);
        int presentW = target.w * pixelSize;
        int presentH = target.h * pixelSize;
        int offX = (curW - presentW) / 2;
        int offY = (curH - presentH) / 2;
        glViewport(offX, offY, presentW, presentH);
        glUseProgram(presentProg);
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, target.tex);
        glUniform1i(uTexLoc, 0);
        glBindVertexArray(vao);
        glDrawArrays(GL_TRIANGLES, 0, 3);

        if (!shotTaken && t >= screenshotAfter) {
            std::vector<uint8_t> pixels((size_t)curW * curH * 3);
            glPixelStorei(GL_PACK_ALIGNMENT, 1);
            glReadPixels(0, 0, curW, curH, GL_RGB, GL_UNSIGNED_BYTE, pixels.data());
            // glReadPixels is bottom-up; flip to top-down for a normal PPM
            std::vector<uint8_t> flipped((size_t)curW * curH * 3);
            for (int y = 0; y < curH; y++) {
                memcpy(&flipped[(size_t)y * curW * 3],
                       &pixels[(size_t)(curH - 1 - y) * curW * 3],
                       (size_t)curW * 3);
            }
            writePPM(screenshotPath, curW, curH, flipped);
            printf("wrote screenshot: %s (%dx%d)\n", screenshotPath.c_str(), curW, curH);
            shotTaken = true;
            glfwSetWindowShouldClose(window, GLFW_TRUE);
        }

        glfwSwapBuffers(window);
    }

    destroyTarget(target);
    glfwTerminate();
    return 0;
}
