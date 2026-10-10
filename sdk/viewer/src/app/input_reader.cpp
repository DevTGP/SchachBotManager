#include "input_reader.hpp"

#include <atomic>
#include <mutex>
#include <thread>
#include <utility>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#else
#include <cerrno>
#include <unistd.h>
#endif

namespace sbm_viewer {

namespace {

// Longer lines are dropped; no message of the protocol comes near this.
constexpr size_t max_line = 1 << 20;

// Reads from stdin without the C runtime, whose stream locks could block the exit of the
// program while this thread waits for input. Returns 0 at the end of the input.
size_t read_stdin(char* buffer, size_t size) {
#ifdef _WIN32
    DWORD count = 0;
    const HANDLE input = GetStdHandle(STD_INPUT_HANDLE);
    if (input == nullptr || input == INVALID_HANDLE_VALUE ||
        !ReadFile(input, buffer, static_cast<DWORD>(size), &count, nullptr)) {
        return 0;
    }
    return count;
#else
    for (;;) {
        const ssize_t count = read(STDIN_FILENO, buffer, size);
        if (count >= 0) {
            return static_cast<size_t>(count);
        }
        if (errno != EINTR) {
            return 0;
        }
    }
#endif
}

} // namespace

struct InputReader::Shared {
    std::mutex mutex;
    std::vector<std::string> lines;
    std::function<void()> wake;
    std::atomic<bool> closed{false};

    void deliver(std::vector<std::string>& ready, bool end) {
        std::function<void()> callback;
        {
            std::lock_guard lock(mutex);
            for (std::string& line : ready) {
                lines.push_back(std::move(line));
            }
            if (end) {
                closed = true;
            }
            callback = wake;
        }
        ready.clear();
        if (callback) {
            callback();
        }
    }

    static void run(std::shared_ptr<Shared> shared) {
        std::string pending;
        bool skipping = false;
        std::vector<std::string> ready;
        char buffer[8192];
        for (;;) {
            const size_t count = read_stdin(buffer, sizeof buffer);
            if (count == 0) {
                if (!skipping && !pending.empty()) {
                    ready.push_back(std::move(pending));
                }
                shared->deliver(ready, true);
                return;
            }
            for (size_t index = 0; index < count; ++index) {
                const char c = buffer[index];
                if (c == '\n') {
                    if (!skipping) {
                        if (!pending.empty() && pending.back() == '\r') {
                            pending.pop_back();
                        }
                        ready.push_back(std::move(pending));
                    }
                    pending.clear();
                    skipping = false;
                } else if (!skipping) {
                    pending.push_back(c);
                    if (pending.size() > max_line) {
                        pending.clear();
                        skipping = true;
                    }
                }
            }
            if (!ready.empty()) {
                shared->deliver(ready, false);
            }
        }
    }
};

InputReader::InputReader(std::function<void()> wake) : shared_(std::make_shared<Shared>()) {
    shared_->wake = std::move(wake);
    std::thread(Shared::run, shared_).detach();
}

InputReader::~InputReader() {
    // The thread may still wait for input; it keeps the shared state alive but wakes no one.
    std::lock_guard lock(shared_->mutex);
    shared_->wake = nullptr;
}

std::vector<std::string> InputReader::take_lines() {
    std::lock_guard lock(shared_->mutex);
    return std::exchange(shared_->lines, {});
}

bool InputReader::closed() const {
    return shared_->closed;
}

} // namespace sbm_viewer
