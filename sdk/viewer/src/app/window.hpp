// The SDL window with its renderer and the Dear ImGui context on top.
#pragma once

#include <cstdint>
#include <string>

struct SDL_Window;
struct SDL_Renderer;
struct ImFont;

namespace sbm_viewer {

class Window {
public:
    Window() = default;
    ~Window();
    Window(const Window&) = delete;
    Window& operator=(const Window&) = delete;

    // Opens the window; false with a message in `error` if SDL cannot.
    bool open(std::string& error);
    void set_title(const std::string& title);

    // Event type the input thread posts to wake the loop.
    uint32_t wake_event() const {
        return wake_event_;
    }
    // Waits up to `timeout_ms` for events and handles them; false once the user closed the window.
    bool handle_events(int timeout_ms);

    void begin_frame();
    // Renders and shows the frame; with a path it also saves the frame as BMP (false on failure).
    bool end_frame(const std::string& screenshot = {});

    ImFont* font() const {
        return font_;
    }

private:
    SDL_Window* window_ = nullptr;
    SDL_Renderer* renderer_ = nullptr;
    ImFont* font_ = nullptr;
    uint32_t wake_event_ = 0;
    bool imgui_ready_ = false;
};

} // namespace sbm_viewer
