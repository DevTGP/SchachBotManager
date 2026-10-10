#include "screenshot.hpp"

#include <SDL3/SDL.h>

namespace sbm_viewer {

bool save_bmp(SDL_Renderer* renderer, const std::string& path) {
    SDL_Surface* surface = SDL_RenderReadPixels(renderer, nullptr);
    if (surface == nullptr) {
        return false;
    }
    const bool saved = SDL_SaveBMP(surface, path.c_str());
    SDL_DestroySurface(surface);
    return saved;
}

} // namespace sbm_viewer
