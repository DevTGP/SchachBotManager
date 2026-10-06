// Runs every vector below spec/testvectors/ against the C interface of the core.
// Usage: sbm_vector_tests [--slow] <testvectors directory>
#include <algorithm>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>

#include <nlohmann/json.hpp>

#include "call.hpp"
#include "perft.hpp"
#include "run_calls.hpp"
#include "summary.hpp"

namespace fs = std::filesystem;
using namespace sbm_test;

namespace {

bool ends_with(std::string_view text, std::string_view suffix) {
    return text.size() >= suffix.size() && text.substr(text.size() - suffix.size()) == suffix;
}

// Vector files in a fixed order; schema files are left out.
std::vector<fs::path> vector_files(const fs::path& directory) {
    std::vector<fs::path> files;
    for (const auto& entry : fs::recursive_directory_iterator(directory)) {
        const auto name = entry.path().filename().string();
        if (entry.is_regular_file() && ends_with(name, ".json") &&
            !ends_with(name, ".schema.json")) {
            files.push_back(entry.path());
        }
    }
    std::sort(files.begin(), files.end());
    return files;
}

Registry make_registry() {
    Registry registry;
    add_board_calls(registry);
    add_board_moves_calls(registry);
    add_board_query_calls(registry);
    add_board_raw_calls(registry);
    add_board_state_calls(registry);
    add_move_calls(registry);
    return registry;
}

void run_file(const fs::path& path, const Registry& registry, bool slow, Summary& summary) {
    std::ifstream stream(path, std::ios::binary);
    const auto file = nlohmann::json::parse(stream);
    const auto schema = file.at("$schema").get<std::string>();
    if (ends_with(schema, "perft.schema.json")) {
        run_perft_vectors(file, slow, summary);
    } else if (ends_with(schema, "calls.schema.json")) {
        run_call_vectors(file, registry, summary);
    } else {
        summary.fail(path.string(), "unknown schema " + schema);
    }
}

} // namespace

int main(int argc, char** argv) {
    bool slow = false;
    fs::path directory;
    for (int i = 1; i < argc; ++i) {
        const std::string_view arg = argv[i];
        if (arg == "--slow") {
            slow = true;
        } else {
            directory = arg;
        }
    }
    if (directory.empty()) {
        std::cerr << "usage: sbm_vector_tests [--slow] <testvectors directory>\n";
        return 2;
    }
    const Registry registry = make_registry();
    Summary summary;
    try {
        for (const auto& path : vector_files(directory)) {
            run_file(path, registry, slow, summary);
        }
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 2;
    }
    std::cout << summary.passed << " passed, " << summary.failed << " failed, " << summary.skipped
              << " skipped\n";
    return summary.failed == 0 && summary.passed > 0 ? 0 : 1;
}
