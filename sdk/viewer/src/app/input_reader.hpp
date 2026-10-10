// Reads the SDK's lines from stdin on a thread of its own, so the window stays responsive.
#pragma once

#include <functional>
#include <memory>
#include <string>
#include <vector>

namespace sbm_viewer {

class InputReader {
public:
    // `wake` runs on the reading thread after new lines or the end of the input.
    explicit InputReader(std::function<void()> wake);
    ~InputReader();
    InputReader(const InputReader&) = delete;
    InputReader& operator=(const InputReader&) = delete;

    std::vector<std::string> take_lines();
    // True once stdin has ended: the bot program is gone.
    bool closed() const;

private:
    struct Shared;
    std::shared_ptr<Shared> shared_;
};

} // namespace sbm_viewer
