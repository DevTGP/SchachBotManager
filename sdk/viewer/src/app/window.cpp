#include "window.hpp"

#include <SDL3/SDL.h>
#include <imgui.h>
#include <imgui_impl_sdl3.h>
#include <imgui_impl_sdlrenderer3.h>

#include "font.hpp"
#include "screenshot.hpp"
#include "theme.hpp"

namespace sbm_viewer {

Window::~Window() {
    if (imgui_ready_) {
        ImGui_ImplSDLRenderer3_Shutdown();
        ImGui_ImplSDL3_Shutdown();
        ImGui::DestroyContext();
    }
    if (renderer_ != nullptr) {
        SDL_DestroyRenderer(renderer_);
    }
    if (window_ != nullptr) {
        SDL_DestroyWindow(window_);
    }
    SDL_Quit();
}

bool Window::open(std::string& error) {
    if (!SDL_Init(SDL_INIT_VIDEO)) {
        error = SDL_GetError();
        return false;
    }
    wake_event_ = SDL_RegisterEvents(1);

    float scale = SDL_GetDisplayContentScale(SDL_GetPrimaryDisplay());
    if (scale <= 0.0f) {
        scale = 1.0f;
    }
    const SDL_WindowFlags flags =
        SDL_WINDOW_RESIZABLE | SDL_WINDOW_HIDDEN | SDL_WINDOW_HIGH_PIXEL_DENSITY;
    window_ = SDL_CreateWindow(
        "SchachBotManager Viewer", static_cast<int>(1180 * scale), static_cast<int>(760 * scale),
        flags);
    if (window_ == nullptr) {
        error = SDL_GetError();
        return false;
    }
    SDL_SetWindowMinimumSize(window_, static_cast<int>(640 * scale), static_cast<int>(420 * scale));
    renderer_ = SDL_CreateRenderer(window_, nullptr);
    if (renderer_ == nullptr) {
        error = SDL_GetError();
        return false;
    }
    SDL_SetRenderVSync(renderer_, 1);
    SDL_SetWindowPosition(window_, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED);
    SDL_ShowWindow(window_);

    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = nullptr;
    io.LogFilename = nullptr;
    apply_theme(scale);
    font_ = load_font();
    ImGui_ImplSDL3_InitForSDLRenderer(window_, renderer_);
    ImGui_ImplSDLRenderer3_Init(renderer_);
    imgui_ready_ = true;
    return true;
}

void Window::set_title(const std::string& title) {
    SDL_SetWindowTitle(window_, title.c_str());
}

bool Window::handle_events(int timeout_ms) {
    SDL_Event event;
    if (!SDL_WaitEventTimeout(&event, timeout_ms)) {
        return true;
    }
    bool open = true;
    do {
        ImGui_ImplSDL3_ProcessEvent(&event);
        if (event.type == SDL_EVENT_QUIT || (event.type == SDL_EVENT_WINDOW_CLOSE_REQUESTED &&
                                             event.window.windowID == SDL_GetWindowID(window_))) {
            open = false;
        }
    } while (SDL_PollEvent(&event));
    return open;
}

void Window::begin_frame() {
    ImGui_ImplSDLRenderer3_NewFrame();
    ImGui_ImplSDL3_NewFrame();
    ImGui::NewFrame();
}

bool Window::end_frame(const std::string& screenshot) {
    ImGui::Render();
    const ImGuiIO& io = ImGui::GetIO();
    SDL_SetRenderScale(renderer_, io.DisplayFramebufferScale.x, io.DisplayFramebufferScale.y);
    SDL_SetRenderDrawColor(renderer_, 30, 30, 30, 255);
    SDL_RenderClear(renderer_);
    ImGui_ImplSDLRenderer3_RenderDrawData(ImGui::GetDrawData(), renderer_);
    const bool saved = screenshot.empty() || save_bmp(renderer_, screenshot);
    SDL_RenderPresent(renderer_);
    return saved;
}

} // namespace sbm_viewer
