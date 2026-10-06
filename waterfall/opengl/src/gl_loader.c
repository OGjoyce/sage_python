#include "gl_loader.h"
#include <stddef.h>

PFNGLGENFRAMEBUFFERSPROC        glGenFramebuffers;
PFNGLBINDFRAMEBUFFERPROC        glBindFramebuffer;
PFNGLFRAMEBUFFERTEXTURE2DPROC   glFramebufferTexture2D;
PFNGLCHECKFRAMEBUFFERSTATUSPROC glCheckFramebufferStatus;
PFNGLDELETEFRAMEBUFFERSPROC     glDeleteFramebuffers;

PFNGLCREATESHADERPROC      glCreateShader;
PFNGLSHADERSOURCEPROC      glShaderSource;
PFNGLCOMPILESHADERPROC     glCompileShader;
PFNGLGETSHADERIVPROC       glGetShaderiv;
PFNGLGETSHADERINFOLOGPROC  glGetShaderInfoLog;
PFNGLDELETESHADERPROC      glDeleteShader;

PFNGLCREATEPROGRAMPROC     glCreateProgram;
PFNGLATTACHSHADERPROC      glAttachShader;
PFNGLLINKPROGRAMPROC       glLinkProgram;
PFNGLGETPROGRAMIVPROC      glGetProgramiv;
PFNGLGETPROGRAMINFOLOGPROC glGetProgramInfoLog;
PFNGLUSEPROGRAMPROC        glUseProgram;
PFNGLDELETEPROGRAMPROC     glDeleteProgram;

PFNGLGENVERTEXARRAYSPROC    glGenVertexArrays;
PFNGLBINDVERTEXARRAYPROC    glBindVertexArray;
PFNGLDELETEVERTEXARRAYSPROC glDeleteVertexArrays;

PFNGLGENBUFFERSPROC    glGenBuffers;
PFNGLBINDBUFFERPROC    glBindBuffer;
PFNGLBUFFERDATAPROC    glBufferData;
PFNGLDELETEBUFFERSPROC glDeleteBuffers;

PFNGLVERTEXATTRIBPOINTERPROC     glVertexAttribPointer;
PFNGLENABLEVERTEXATTRIBARRAYPROC glEnableVertexAttribArray;

PFNGLGETUNIFORMLOCATIONPROC glGetUniformLocation;
PFNGLUNIFORM1FPROC          glUniform1f;
PFNGLUNIFORM2FPROC          glUniform2f;
PFNGLUNIFORM1IPROC          glUniform1i;

#define WF_LOAD(name) \
    do { \
        *(void**)(&(name)) = loader(#name); \
        if (!(name)) ok = 0; \
    } while (0)

int wf_gl_load(wf_GLLoadFunc loader) {
    int ok = 1;

    WF_LOAD(glGenFramebuffers);
    WF_LOAD(glBindFramebuffer);
    WF_LOAD(glFramebufferTexture2D);
    WF_LOAD(glCheckFramebufferStatus);
    WF_LOAD(glDeleteFramebuffers);

    WF_LOAD(glCreateShader);
    WF_LOAD(glShaderSource);
    WF_LOAD(glCompileShader);
    WF_LOAD(glGetShaderiv);
    WF_LOAD(glGetShaderInfoLog);
    WF_LOAD(glDeleteShader);

    WF_LOAD(glCreateProgram);
    WF_LOAD(glAttachShader);
    WF_LOAD(glLinkProgram);
    WF_LOAD(glGetProgramiv);
    WF_LOAD(glGetProgramInfoLog);
    WF_LOAD(glUseProgram);
    WF_LOAD(glDeleteProgram);

    WF_LOAD(glGenVertexArrays);
    WF_LOAD(glBindVertexArray);
    WF_LOAD(glDeleteVertexArrays);

    WF_LOAD(glGenBuffers);
    WF_LOAD(glBindBuffer);
    WF_LOAD(glBufferData);
    WF_LOAD(glDeleteBuffers);

    WF_LOAD(glVertexAttribPointer);
    WF_LOAD(glEnableVertexAttribArray);

    WF_LOAD(glGetUniformLocation);
    WF_LOAD(glUniform1f);
    WF_LOAD(glUniform2f);
    WF_LOAD(glUniform1i);

    return ok;
}
