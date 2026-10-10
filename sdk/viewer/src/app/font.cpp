#include "font.hpp"

#include <cstddef>

#include <imgui.h>

extern const unsigned char sbm_viewer_font[];
extern const std::size_t sbm_viewer_font_size;

namespace sbm_viewer {

ImFont* load_font() {
    ImFontConfig config;
    config.FontDataOwnedByAtlas = false;
    ImGuiIO& io = ImGui::GetIO();
    // ImGui only reads the data; the cast is for its non-const parameter.
    ImFont* font = io.Fonts->AddFontFromMemoryTTF(
        const_cast<unsigned char*>(sbm_viewer_font), static_cast<int>(sbm_viewer_font_size), 16.0f,
        &config);
    io.FontDefault = font;
    return font;
}

} // namespace sbm_viewer
