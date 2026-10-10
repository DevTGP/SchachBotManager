// Times as the window shows them.
#pragma once

#include <cstdint>
#include <string>

namespace sbm_viewer {

// Remaining time: "1:05:00", "4:59", and with tenths below ten seconds "0:09.3".
std::string clock_text(int64_t ms);
// Thinking time of one move: "850 ms", "12.4 s", "2:05".
std::string duration_text(int64_t ms);

} // namespace sbm_viewer
