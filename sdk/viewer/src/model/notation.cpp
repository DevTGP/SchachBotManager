#include "notation.hpp"

#include <cstdio>
#include <cstdlib>

namespace sbm_viewer {

std::vector<MoveRow> move_rows(int ply_count, int first_number, bool black_starts) {
    std::vector<MoveRow> rows;
    int ply = 1;
    if (black_starts && ply_count > 0) {
        rows.push_back(MoveRow{first_number, 0, ply++});
        ++first_number;
    }
    for (int number = first_number; ply <= ply_count; ++number) {
        MoveRow row{number, ply++, 0};
        if (ply <= ply_count) {
            row.black_ply = ply++;
        }
        rows.push_back(row);
    }
    return rows;
}

std::string score_text(const SearchInfo& info) {
    char buffer[32];
    if (info.score_mate) {
        std::snprintf(buffer, sizeof buffer, "#%d", *info.score_mate);
        return buffer;
    }
    if (info.score_cp) {
        const int cp = *info.score_cp;
        std::snprintf(
            buffer, sizeof buffer, "%c%d.%02d", cp < 0 ? '-' : '+', std::abs(cp) / 100,
            std::abs(cp) % 100);
        return buffer;
    }
    return {};
}

std::string nodes_text(int64_t nodes) {
    char buffer[32];
    const double value = static_cast<double>(nodes);
    if (nodes < 10'000) {
        std::snprintf(buffer, sizeof buffer, "%lld", static_cast<long long>(nodes));
    } else if (nodes < 1'000'000) {
        std::snprintf(buffer, sizeof buffer, "%.1fk", value / 1e3);
    } else if (nodes < 1'000'000'000) {
        std::snprintf(buffer, sizeof buffer, "%.1fM", value / 1e6);
    } else {
        std::snprintf(buffer, sizeof buffer, "%.1fG", value / 1e9);
    }
    return buffer;
}

std::string pv_text(const Position& from, const std::vector<std::string>& pv) {
    Position position = from;
    std::string text;
    for (const std::string& uci : pv) {
        const auto san = position.san(uci);
        if (!san || !position.play(uci)) {
            break;
        }
        if (!text.empty()) {
            text += ' ';
        }
        text += *san;
    }
    return text;
}

} // namespace sbm_viewer
