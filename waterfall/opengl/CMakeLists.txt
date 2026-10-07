cmake_minimum_required(VERSION 3.10)
project(craftflow_waterfall CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(PkgConfig REQUIRED)
pkg_check_modules(GLFW REQUIRED glfw3)
find_package(OpenGL REQUIRED)

add_executable(craftflow_waterfall
  src/main.cpp
  src/gl_loader.c
)

target_include_directories(craftflow_waterfall PRIVATE include ${GLFW_INCLUDE_DIRS})
target_link_libraries(craftflow_waterfall PRIVATE ${GLFW_LIBRARIES} OpenGL::GL ${CMAKE_DL_LIBS})
target_link_directories(craftflow_waterfall PRIVATE ${GLFW_LIBRARY_DIRS})

# Baked-in path to the GLSL source of truth shared with the Three.js build,
# so the binary finds it regardless of which directory it's launched from.
target_compile_definitions(craftflow_waterfall PRIVATE
  WATER_CORE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/../shared/water_core.glsl"
)
