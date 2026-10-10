// The embedded DejaVu Sans subset: text and chess pieces in one font (assets/README.md).
#pragma once

struct ImFont;

namespace sbm_viewer {

// Adds the font to the ImGui atlas and makes it the default.
ImFont* load_font();

} // namespace sbm_viewer
