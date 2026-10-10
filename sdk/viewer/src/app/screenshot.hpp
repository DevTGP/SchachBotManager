// Saves the rendered frame, for the smoke test without a screen (SDL_VIDEO_DRIVER=offscreen).
#pragma once

#include <string>

struct SDL_Renderer;

namespace sbm_viewer {

bool save_bmp(SDL_Renderer* renderer, const std::string& path);

} // namespace sbm_viewer
