# Native module sbm._core: the chess core linked statically into a nanobind extension.
cmake_minimum_required(VERSION 3.21)

project(sbm_python LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# CPython for Windows is built with MSVC; a MinGW module would need a foreign C++ runtime.
if(WIN32 AND NOT MSVC)
    message(FATAL_ERROR "Build the Python module with MSVC, e.g. CMAKE_GENERATOR=\"Visual Studio 17 2022\"")
endif()

find_package(Python 3.11 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(nanobind CONFIG REQUIRED)

# The core is built from source next to this package; wheels therefore come from the repository.
set(SBM_BUILD_TESTS OFF)
set(SBM_SHARED OFF)
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../core ${CMAKE_CURRENT_BINARY_DIR}/core)

nanobind_add_module(_core NB_STATIC
    src/native/module.cpp
    src/native/status.cpp
    src/native/move.cpp
    src/native/board.cpp
    src/native/board_moves.cpp
    src/native/board_query.cpp
    src/native/board_raw.cpp
    src/native/board_state.cpp
)
target_link_libraries(_core PRIVATE sbm)
if(MSVC)
    target_compile_options(_core PRIVATE /W4 /permissive- /utf-8)
else()
    target_compile_options(_core PRIVATE -Wall -Wextra)
endif()

# Type stubs, so editors complete the native classes.
nanobind_add_stub(_core_stub
    MODULE _core
    OUTPUT _core.pyi
    PYTHON_PATH $<TARGET_FILE_DIR:_core>
    MARKER_FILE py.typed
    DEPENDS _core
)

install(TARGETS _core LIBRARY DESTINATION sbm)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/_core.pyi ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    DESTINATION sbm
)
