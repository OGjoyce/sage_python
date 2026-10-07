// gl_loader.h — a deliberately tiny OpenGL 3.3 core function loader.
//
// GL 1.1 entry points (glViewport, glClear, glGenTextures, ...) are taken
// straight from <GL/gl.h> and linked normally against -lGL / -lopengl32:
// on Windows, wglGetProcAddress is explicitly unreliable for anything at
// or below GL 1.1 (MSDN says so outright), so those must come from the
// system library, not a loader. Everything newer (shaders, VAOs/VBOs,
// FBOs, glActiveTexture) genuinely has to be resolved at runtime via
// glfwGetProcAddress, which is what this file does -- the same handful
// of functions GLAD/GLEW would hand you, just spelled out instead of
// generated, since this project only needs a few dozen of them.
#ifndef WF_GL_LOADER_H
#define WF_GL_LOADER_H

#include <GL/gl.h>
#include <GL/glext.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void* (*wf_GLLoadFunc)(const char* name);

// returns 1 on success, 0 if any required entry point was not found
int wf_gl_load(wf_GLLoadFunc loader);

extern PFNGLGENFRAMEBUFFERSPROC        glGenFramebuffers;
extern PFNGLBINDFRAMEBUFFERPROC        glBindFramebuffer;
extern PFNGLFRAMEBUFFERTEXTURE2DPROC   glFramebufferTexture2D;
extern PFNGLCHECKFRAMEBUFFERSTATUSPROC glCheckFramebufferStatus;
extern PFNGLDELETEFRAMEBUFFERSPROC     glDeleteFramebuffers;

extern PFNGLCREATESHADERPROC      glCreateShader;
extern PFNGLSHADERSOURCEPROC      glShaderSource;
extern PFNGLCOMPILESHADERPROC     glCompileShader;
extern PFNGLGETSHADERIVPROC       glGetShaderiv;
extern PFNGLGETSHADERINFOLOGPROC  glGetShaderInfoLog;
extern PFNGLDELETESHADERPROC      glDeleteShader;

extern PFNGLCREATEPROGRAMPROC     glCreateProgram;
extern PFNGLATTACHSHADERPROC      glAttachShader;
extern PFNGLLINKPROGRAMPROC       glLinkProgram;
extern PFNGLGETPROGRAMIVPROC      glGetProgramiv;
extern PFNGLGETPROGRAMINFOLOGPROC glGetProgramInfoLog;
extern PFNGLUSEPROGRAMPROC        glUseProgram;
extern PFNGLDELETEPROGRAMPROC     glDeleteProgram;

extern PFNGLGENVERTEXARRAYSPROC    glGenVertexArrays;
extern PFNGLBINDVERTEXARRAYPROC    glBindVertexArray;
extern PFNGLDELETEVERTEXARRAYSPROC glDeleteVertexArrays;

extern PFNGLGENBUFFERSPROC    glGenBuffers;
extern PFNGLBINDBUFFERPROC    glBindBuffer;
extern PFNGLBUFFERDATAPROC    glBufferData;
extern PFNGLDELETEBUFFERSPROC glDeleteBuffers;

extern PFNGLVERTEXATTRIBPOINTERPROC     glVertexAttribPointer;
extern PFNGLENABLEVERTEXATTRIBARRAYPROC glEnableVertexAttribArray;

extern PFNGLGETUNIFORMLOCATIONPROC glGetUniformLocation;
extern PFNGLUNIFORM1FPROC          glUniform1f;
extern PFNGLUNIFORM2FPROC          glUniform2f;
extern PFNGLUNIFORM3FPROC          glUniform3f;
extern PFNGLUNIFORM1IPROC          glUniform1i;
extern PFNGLUNIFORMMATRIX4FVPROC   glUniformMatrix4fv;
// NOTE: glActiveTexture is intentionally NOT loaded here. It's GL 1.3, so
// in principle it needs the same runtime loading as everything else below
// GL 1.2+, but this system's <GL/gl.h> (common on Linux/Mesa, unlike
// Windows' opengl32.h) already declares and exports it directly, and
// declaring it again as a function-pointer variable of the same name is a
// hard conflict ("redeclared as different kind of entity"). It's linked
// straight from -lGL instead; see main.cpp.

#ifdef __cplusplus
}
#endif

#endif // WF_GL_LOADER_H
