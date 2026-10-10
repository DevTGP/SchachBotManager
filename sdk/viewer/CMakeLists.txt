# Viewer: a window that shows the game of a bot live and lets the user step through it (E106).
# The SDKs start it and write viewer-v1 messages (spec/protocol/viewer-v1/) to its stdin.
cmake_minimum_required(VERSION 3.21)

project(sbm_viewer LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# The program runs on its own next to a bot of any language, so it carries the C++ runtime.
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
if(MINGW)
    add_link_options(-static-libgcc -static-libstdc++)
endif()

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

option(SBM_VIEWER_BUILD_TESTS "Build the viewer tests" ${PROJECT_IS_TOP_LEVEL})
option(SBM_VIEWER_BUILD_APP "Build the window program (fetches SDL3 and Dear ImGui)" ON)
set(SBM_VIEWER_INSTALL_DIR bin CACHE STRING "Install directory of the program")
set(SBM_VIEWER_LICENSE_DIR share/sbm-viewer/licenses CACHE STRING
    "Install directory of the third-party licenses")

# The rules come from the core, linked statically into the program.
set(SBM_BUILD_TESTS OFF)
set(SBM_SHARED OFF)
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../core ${CMAKE_CURRENT_BINARY_DIR}/core)

include(cmake/dependencies.cmake)
include(cmake/embed_file.cmake)

# Everything without a window: messages, game record, navigation, texts. Tested on its own.
add_library(sbm_viewer_model STATIC
    src/model/game_record.cpp
    src/model/messages.cpp
    src/model/navigation.cpp
    src/model/notation.cpp
    src/model/position.cpp
    src/model/session.cpp
    src/model/time_text.cpp
)
target_include_directories(sbm_viewer_model PUBLIC src)
target_link_libraries(sbm_viewer_model PUBLIC sbm PRIVATE nlohmann_json::nlohmann_json)
sbm_enable_warnings(sbm_viewer_model)

if(SBM_VIEWER_BUILD_APP)
    add_executable(sbm-viewer WIN32
        src/app/board_view.cpp
        src/app/controls.cpp
        src/app/details_view.cpp
        src/app/font.cpp
        src/app/frame.cpp
        src/app/game_bar.cpp
        src/app/input_reader.cpp
        src/app/log_view.cpp
        src/app/main.cpp
        src/app/move_list.cpp
        src/app/players_view.cpp
        src/app/screenshot.cpp
        src/app/theme.cpp
        src/app/window.cpp
    )
    sbm_viewer_embed_file(sbm-viewer ${CMAKE_CURRENT_SOURCE_DIR}/assets/DejaVuSans-viewer.ttf
        sbm_viewer_font)
    target_link_libraries(sbm-viewer PRIVATE sbm_viewer_model sbm_viewer_imgui)
    sbm_enable_warnings(sbm-viewer)

    install(TARGETS sbm-viewer RUNTIME DESTINATION ${SBM_VIEWER_INSTALL_DIR})
    install(FILES ${sdl3_SOURCE_DIR}/LICENSE.txt DESTINATION ${SBM_VIEWER_LICENSE_DIR}
        RENAME SDL3-LICENSE.txt)
    install(FILES ${imgui_SOURCE_DIR}/LICENSE.txt DESTINATION ${SBM_VIEWER_LICENSE_DIR}
        RENAME imgui-LICENSE.txt)
    install(FILES ${nlohmann_json_SOURCE_DIR}/LICENSE.MIT DESTINATION ${SBM_VIEWER_LICENSE_DIR}
        RENAME nlohmann-json-LICENSE.txt)
    install(FILES assets/DejaVu-LICENSE.txt DESTINATION ${SBM_VIEWER_LICENSE_DIR})
endif()

if(SBM_VIEWER_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
