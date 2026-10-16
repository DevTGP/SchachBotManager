# Native addon sbm.node: the chess core linked statically into a Node-API module (E221).
# scripts/build-native.mjs configures it with the paths of node-api-headers and node-addon-api.
cmake_minimum_required(VERSION 3.21)

project(sbm_javascript LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
# The static runtime keeps the addon free of a separate Visual C++ redistributable.
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

set(NODE_API_HEADERS_DIR "" CACHE PATH "Directory include/ of node-api-headers")
set(NODE_API_DEF "" CACHE FILEPATH "node_api.def of node-api-headers (Windows only)")
set(NODE_ADDON_API_DIR "" CACHE PATH "Directory of node-addon-api with napi.h")
set(SBM_JS_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/out" CACHE PATH "Directory for sbm.node")
foreach(required NODE_API_HEADERS_DIR NODE_ADDON_API_DIR)
    if(NOT ${required})
        message(FATAL_ERROR "${required} is not set; build with scripts/build-native.mjs")
    endif()
endforeach()

# The core is built from source next to this package, like for the Python SDK.
set(SBM_BUILD_TESTS OFF)
set(SBM_SHARED OFF)
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../core ${CMAKE_CURRENT_BINARY_DIR}/core)

add_library(sbm_node MODULE
    src/native/module.cpp
    src/native/status.cpp
    src/native/move.cpp
    src/native/board.cpp
    src/native/board_moves.cpp
    src/native/board_query.cpp
    src/native/board_raw.cpp
    src/native/board_state.cpp
)
# SYSTEM keeps the warnings of the foreign headers out of the build log.
target_include_directories(sbm_node SYSTEM PRIVATE ${NODE_API_HEADERS_DIR} ${NODE_ADDON_API_DIR})
target_compile_definitions(sbm_node PRIVATE
    NAPI_VERSION=8
    NAPI_CPP_EXCEPTIONS
    NODE_ADDON_API_DISABLE_DEPRECATED
    BUILDING_NODE_EXTENSION
)
target_link_libraries(sbm_node PRIVATE sbm)
# $<0:> keeps multi-config generators from adding a Release/ or Debug/ subdirectory.
set_target_properties(sbm_node PROPERTIES
    OUTPUT_NAME sbm
    PREFIX ""
    SUFFIX ".node"
    LIBRARY_OUTPUT_DIRECTORY "${SBM_JS_OUTPUT_DIR}$<0:>"
    CXX_VISIBILITY_PRESET hidden
)

if(MSVC)
    target_compile_options(sbm_node PRIVATE /W4 /permissive- /utf-8 /EHsc)
    # Node exports Node-API from node.exe; the import library comes from the .def file.
    if(NOT NODE_API_DEF)
        message(FATAL_ERROR "NODE_API_DEF is not set; build with scripts/build-native.mjs")
    endif()
    if(CMAKE_CXX_COMPILER_ARCHITECTURE_ID STREQUAL "ARM64")
        set(node_machine ARM64)
    else()
        set(node_machine X64)
    endif()
    set(node_lib ${CMAKE_CURRENT_BINARY_DIR}/node.lib)
    add_custom_command(
        OUTPUT ${node_lib}
        COMMAND ${CMAKE_AR} /nologo /def:${NODE_API_DEF} /out:${node_lib} /machine:${node_machine}
        DEPENDS ${NODE_API_DEF}
        VERBATIM
    )
    add_custom_target(sbm_node_lib DEPENDS ${node_lib})
    add_dependencies(sbm_node sbm_node_lib)
    target_link_libraries(sbm_node PRIVATE ${node_lib})
else()
    target_compile_options(sbm_node PRIVATE -Wall -Wextra)
    if(APPLE)
        # The symbols of Node-API come from the node process at load time.
        target_link_options(sbm_node PRIVATE -undefined dynamic_lookup)
    else()
        # One addon for every Linux with a glibc that is new enough, whatever its libstdc++.
        target_link_options(sbm_node PRIVATE -static-libstdc++ -static-libgcc)
    endif()
endif()
