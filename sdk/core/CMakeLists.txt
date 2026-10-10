# Chess core: rules engine with the flat C interface of include/sbm/ (E50).
cmake_minimum_required(VERSION 3.21)

project(sbm_core VERSION 0.2.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# The library and the test programs land in one directory, so Windows finds the DLL.
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

option(SBM_BUILD_TESTS "Build the core tests" ${PROJECT_IS_TOP_LEVEL})
option(SBM_SHARED "Build sbm as a shared library; OFF links it statically into a binding" ON)

include(cmake/warnings.cmake)

# MinGW: link the C++ runtime statically, so the DLL does not pick up another libstdc++ on PATH.
if(MINGW)
    add_link_options(-static-libgcc -static-libstdc++)
endif()

# Rules engine without the C interface; linked into the library and the unit tests.
add_library(sbm_engine STATIC
    src/attacks.cpp
    src/en_passant.cpp
    src/end_conditions.cpp
    src/fen_parse.cpp
    src/fen_write.cpp
    src/game.cpp
    src/hash.cpp
    src/material.cpp
    src/movegen.cpp
    src/play.cpp
    src/polyglot_keys.cpp
    src/position.cpp
    src/repetition.cpp
    src/san.cpp
    src/text.cpp
    src/threats.cpp
    src/uci.cpp
)
target_include_directories(sbm_engine PUBLIC src)
set_target_properties(sbm_engine PROPERTIES
    POSITION_INDEPENDENT_CODE ON
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN ON
)
sbm_enable_warnings(sbm_engine)

# The library the bindings load (shared) or link into their native module (static).
if(SBM_SHARED)
    set(SBM_LIBRARY_TYPE SHARED)
else()
    set(SBM_LIBRARY_TYPE STATIC)
endif()
add_library(sbm ${SBM_LIBRARY_TYPE}
    src/capi/board.cpp
    src/capi/board_moves.cpp
    src/capi/board_query.cpp
    src/capi/board_raw.cpp
    src/capi/board_state.cpp
    src/capi/move.cpp
    src/capi/output.cpp
    src/capi/status.cpp
    src/capi/version.cpp
)
target_include_directories(sbm PUBLIC include)
target_link_libraries(sbm PRIVATE sbm_engine)
target_compile_definitions(sbm
    PRIVATE SBM_BUILD SBM_VERSION_STRING="${PROJECT_VERSION}"
)
set_target_properties(sbm PROPERTIES
    POSITION_INDEPENDENT_CODE ON
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN ON
)
if(NOT SBM_SHARED)
    target_compile_definitions(sbm PUBLIC SBM_STATIC)
endif()
sbm_enable_warnings(sbm)

if(SBM_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
