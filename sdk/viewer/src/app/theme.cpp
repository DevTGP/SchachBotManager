#include "theme.hpp"

namespace sbm_viewer {

void apply_theme(float scale) {
    ImGui::StyleColorsDark();
    ImGuiStyle& style = ImGui::GetStyle();
    style.WindowRounding = 0.0f;
    style.FrameRounding = 3.0f;
    style.WindowPadding = ImVec2(10.0f, 10.0f);
    style.ItemSpacing = ImVec2(8.0f, 6.0f);
    style.ScaleAllSizes(scale);
    style.FontScaleDpi = scale;
}

} // namespace sbm_viewer
