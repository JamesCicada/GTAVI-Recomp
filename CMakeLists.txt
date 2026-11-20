cmake_minimum_required(VERSION 3.21)

project(
  GTAVIRecomp
  VERSION 0.1.0
  DESCRIPTION "Cross-platform translation layer for GTA VI components"
  LANGUAGES CXX
)

# --- Global settings ---------------------------------------------------------

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Single-config generators default to Debug so that assertions stay enabled.
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS Debug Release RelWithDebInfo MinSizeRel)
endif()

option(GTAVI_BUILD_TOOLS "Build the diagnostic command-line tools" ON)
option(GTAVI_BUILD_TESTS "Build the unit test suite" ON)
option(GTAVI_WARNINGS_AS_ERRORS "Treat compiler warnings as errors" OFF)

include(cmake/CompilerWarnings.cmake)

# --- Generated headers -------------------------------------------------------

configure_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/include/gtavi/version.h.in
  ${CMAKE_CURRENT_BINARY_DIR}/generated/gtavi/version.h
  @ONLY
)

# --- Core library ------------------------------------------------------------
# Platform-specific sources are selected here and nowhere else. Everything
# outside src/platform/ must stay portable.

set(GTAVI_CORE_SOURCES
  src/error.cpp
  src/log.cpp
  src/path.cpp
  src/platform.cpp
)

if(WIN32)
  list(APPEND GTAVI_CORE_SOURCES src/platform/platform_windows.cpp)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  list(APPEND GTAVI_CORE_SOURCES src/platform/platform_linux.cpp)
else()
  list(APPEND GTAVI_CORE_SOURCES src/platform/platform_unsupported.cpp)
endif()

add_library(gtavi_core STATIC ${GTAVI_CORE_SOURCES})
add_library(gtavi::core ALIAS gtavi_core)

target_include_directories(
  gtavi_core
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
         $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}/generated>
)

target_compile_features(gtavi_core PUBLIC cxx_std_20)
target_link_libraries(gtavi_core PRIVATE gtavi_warnings)

# --- Tools and tests ---------------------------------------------------------

if(GTAVI_BUILD_TOOLS)
  add_subdirectory(tools)
endif()

if(GTAVI_BUILD_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif()
