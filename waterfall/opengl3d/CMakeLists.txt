cmake_minimum_required(VERSION 3.10)
project(craftflow_waterfall_3d CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(PkgConfig REQUIRED)
pkg_check_modules(GLFW REQUIRED glfw3)
find_package(OpenGL REQUIRED)

add_executable(craftflow_waterfall_3d
  src/main.cpp
  ../opengl/src/gl_loader.c
)

target_include_directories(craftflow_waterfall_3d PRIVATE ../opengl/include ${GLFW_INCLUDE_DIRS})
target_link_libraries(craftflow_waterfall_3d PRIVATE ${GLFW_LIBRARIES} OpenGL::GL ${CMAKE_DL_LIBS})
target_link_directories(craftflow_waterfall_3d PRIVATE ${GLFW_LIBRARY_DIRS})

# Same idea as waterfall/opengl/CMakeLists.txt: bake in paths to the two
# shared GLSL files so the binary finds them regardless of launch directory.
target_compile_definitions(craftflow_waterfall_3d PRIVATE
  WATER_CORE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/../shared/water_core.glsl"
  WATER_CORE_3D_PATH="${CMAKE_CURRENT_SOURCE_DIR}/../shared/water_core_3d.glsl"
)
