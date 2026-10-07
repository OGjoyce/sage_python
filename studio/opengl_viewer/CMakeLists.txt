cmake_minimum_required(VERSION 3.10)
project(uaig_viewer CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(PkgConfig REQUIRED)
pkg_check_modules(GLFW REQUIRED glfw3)
find_package(OpenGL REQUIRED)

add_executable(uaig_viewer
  src/main.cpp
  ../../waterfall/opengl/src/gl_loader.c
)

target_include_directories(uaig_viewer PRIVATE ../../waterfall/opengl/include ${GLFW_INCLUDE_DIRS})
target_link_libraries(uaig_viewer PRIVATE ${GLFW_LIBRARIES} OpenGL::GL ${CMAKE_DL_LIBS})
target_link_directories(uaig_viewer PRIVATE ${GLFW_LIBRARY_DIRS})
