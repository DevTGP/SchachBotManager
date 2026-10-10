// sbm-viewer: shows the games of a bot program live (E106). The SDK starts it and writes
// viewer-v1 lines to its stdin; the window stays open until the user closes it. Once stdin ends
// (the bot program is gone), the viewer ends too.
#include <cstdio>
#include <string>
#include <string_view>

#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>

#include "frame.hpp"
#include "input_reader.hpp"
#include "model/session.hpp"
#include "view_state.hpp"
#include "window.hpp"

namespace {

// After the input ended, a few frames let the layout settle before the screenshot.
constexpr int screenshot_frames = 3;

std::string window_title(const sbm_viewer::Session& session) {
    const std::string name = "SchachBotManager Viewer";
    if (session.games().empty()) {
        return name;
    }
    const auto& start = session.games().back().start();
    const bool bot_white = start.color == "white";
    const std::string& white = bot_white ? start.bot : start.opponent;
    const std::string& black = bot_white ? start.opponent : start.bot;
    return white + " vs " + black + " – " + name;
}

} // namespace

int main(int argc, char** argv) {
    // --screenshot FILE: draws everything read until stdin ends, saves it as BMP and exits.
    // Used by the tests with the offscreen video driver.
    std::string screenshot;
    for (int i = 1; i < argc; ++i) {
        if (std::string_view(argv[i]) == "--screenshot" && i + 1 < argc) {
            screenshot = argv[++i];
        }
    }

    sbm_viewer::Window window;
    std::string error;
    if (!window.open(error)) {
        std::fprintf(stderr, "sbm-viewer: cannot open a window: %s\n", error.c_str());
        return 1;
    }

    const uint32_t wake_event = window.wake_event();
    sbm_viewer::InputReader reader([wake_event] {
        SDL_Event event{};
        event.type = wake_event;
        SDL_PushEvent(&event);
    });

    sbm_viewer::Session session;
    sbm_viewer::ViewState state;
    size_t known_games = 0;
    int known_plies = 0;
    int frames_after_end = 0;
    std::string title;

    while (true) {
        // Checked before taking the lines, so no line that came before the end is missed.
        const bool closed = reader.closed();
        for (const std::string& line : reader.take_lines()) {
            session.apply_line(line);
        }
        const auto& games = session.games();
        const int plies = games.empty() ? 0 : games.back().ply_count();
        if (games.size() != known_games || plies != known_plies) {
            known_games = games.size();
            known_plies = plies;
            state.changed_at_ms = SDL_GetTicks();
        }
        state.navigation.games_changed(static_cast<int>(games.size()));
        if (closed && !state.input_closed) {
            state.input_closed = true;
        }
        if (closed && screenshot.empty()) {
            break;
        }

        const std::string new_title = window_title(session);
        if (new_title != title) {
            title = new_title;
            window.set_title(title);
        }

        window.begin_frame();
        sbm_viewer::draw_frame(session, state, window.font(), SDL_GetTicks());
        if (closed && ++frames_after_end > screenshot_frames) {
            return window.end_frame(screenshot) ? 0 : 1;
        }
        window.end_frame();

        const bool running = !games.empty() && !games.back().result() && !closed;
        if (!window.handle_events(closed ? 0 : running ? 100 : 500)) {
            break;
        }
    }
    return 0;
}
