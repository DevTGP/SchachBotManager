# Pinned third-party sources, fetched at build time and checked against their hashes (E106).
include(FetchContent)

FetchContent_Declare(nlohmann_json
    URL https://github.com/nlohmann/json/releases/download/v3.12.0/json.tar.xz
    URL_HASH SHA256=42f6e95cad6ec532fd372391373363b62a14af6d771056dbfc86160e6dfff7aa
    DOWNLOAD_EXTRACT_TIMESTAMP ON
)
set(JSON_Install OFF CACHE INTERNAL "")
FetchContent_MakeAvailable(nlohmann_json)

if(NOT SBM_VIEWER_BUILD_APP)
    return()
endif()

# Without the X11 headers SDL would quietly build without a window system; fail early instead.
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    find_package(X11 REQUIRED)
    if(NOT X11_Xext_FOUND)
        message(FATAL_ERROR "The viewer needs the headers of libX11 and libXext")
    endif()
endif()

# SDL3 as a static library with video and rendering only. On Linux the window goes through X11
# (also under Wayland via XWayland); SDL loads libX11 at runtime, so the program runs without it.
foreach(subsystem AUDIO GPU CAMERA JOYSTICK HAPTIC HIDAPI POWER SENSOR DIALOG TRAY)
    set(SDL_${subsystem} OFF CACHE BOOL "" FORCE)
endforeach()
foreach(feature VULKAN WAYLAND KMSDRM DBUS IBUS LIBURING LIBUDEV PIPEWIRE OPENGLES)
    set(SDL_${feature} OFF CACHE BOOL "" FORCE)
endforeach()
set(SDL_SHARED OFF CACHE BOOL "" FORCE)
set(SDL_STATIC ON CACHE BOOL "" FORCE)
set(SDL_TEST_LIBRARY OFF CACHE BOOL "" FORCE)
set(SDL_TESTS OFF CACHE BOOL "" FORCE)
set(SDL_EXAMPLES OFF CACHE BOOL "" FORCE)
set(SDL_INSTALL OFF CACHE BOOL "" FORCE)
FetchContent_Declare(SDL3
    URL https://github.com/libsdl-org/SDL/releases/download/release-3.4.16/SDL3-3.4.16.tar.gz
    URL_HASH SHA256=7322236cd12090c3eb40b9728be4d49c76f66ad17d04369584d4ecad5cf77c68
    DOWNLOAD_EXTRACT_TIMESTAMP ON
)
FetchContent_MakeAvailable(SDL3)

# Dear ImGui has no build of its own; the viewer compiles the core and the SDL3 backends.
FetchContent_Declare(imgui
    URL https://github.com/ocornut/imgui/archive/refs/tags/v1.92.9b.tar.gz
    URL_HASH SHA256=21d8a0a565e85dce943e375db00812c2f3f0ab21f3f0f7964e364a63422d7f99
    DOWNLOAD_EXTRACT_TIMESTAMP ON
)
FetchContent_MakeAvailable(imgui)

add_library(sbm_viewer_imgui STATIC
    ${imgui_SOURCE_DIR}/imgui.cpp
    ${imgui_SOURCE_DIR}/imgui_draw.cpp
    ${imgui_SOURCE_DIR}/imgui_tables.cpp
    ${imgui_SOURCE_DIR}/imgui_widgets.cpp
    ${imgui_SOURCE_DIR}/backends/imgui_impl_sdl3.cpp
    ${imgui_SOURCE_DIR}/backends/imgui_impl_sdlrenderer3.cpp
)
target_include_directories(sbm_viewer_imgui PUBLIC ${imgui_SOURCE_DIR} ${imgui_SOURCE_DIR}/backends)
target_compile_definitions(sbm_viewer_imgui PUBLIC IMGUI_DISABLE_DEMO_WINDOWS)
target_link_libraries(sbm_viewer_imgui PUBLIC SDL3::SDL3-static)
