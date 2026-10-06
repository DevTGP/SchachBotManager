// Attack tables and lines against a square-by-square walk on random occupancies.
#include <cstdint>
#include <cstdlib>
#include <utility>
#include <vector>

#include "attacks.hpp"
#include "check.hpp"

using sbm::Bitboard;

namespace {

using Step = std::pair<int, int>; // file and rank offset

const std::vector<Step> kRookSteps{{0, 1}, {1, 0}, {0, -1}, {-1, 0}};
const std::vector<Step> kBishopSteps{{1, 1}, {1, -1}, {-1, -1}, {-1, 1}};
const std::vector<Step> kKnightSteps{{1, 2},   {2, 1},   {2, -1}, {1, -2},
                                     {-1, -2}, {-2, -1}, {-2, 1}, {-1, 2}};
const std::vector<Step> kKingSteps{{0, 1},  {1, 1},   {1, 0},  {1, -1},
                                   {0, -1}, {-1, -1}, {-1, 0}, {-1, 1}};

// Squares reached by each step, repeated up to the first occupied square if sliding.
Bitboard walk(int square, const std::vector<Step>& steps, Bitboard occupied, bool sliding) {
    Bitboard result = 0;
    for (const auto& [df, dr] : steps) {
        int file = sbm::file_of(square) + df;
        int rank = sbm::rank_of(square) + dr;
        while (sbm::on_board(file, rank)) {
            const Bitboard target = sbm::square_bb(sbm::make_square(file, rank));
            result |= target;
            if (!sliding || (occupied & target) != 0) {
                break;
            }
            file += df;
            rank += dr;
        }
    }
    return result;
}

// Deterministic pseudo-random occupancies (xorshift64).
std::uint64_t next_random(std::uint64_t& state) {
    state ^= state << 13;
    state ^= state >> 7;
    state ^= state << 17;
    return state;
}

void test_leapers() {
    for (int square = 0; square < 64; ++square) {
        CHECK(sbm::knight_attacks(square) == walk(square, kKnightSteps, 0, false));
        CHECK(sbm::king_attacks(square) == walk(square, kKingSteps, 0, false));
        CHECK(sbm::pawn_attacks(sbm::kWhite, square) == walk(square, {{-1, 1}, {1, 1}}, 0, false));
        CHECK(
            sbm::pawn_attacks(sbm::kBlack, square) == walk(square, {{-1, -1}, {1, -1}}, 0, false));
    }
}

void test_sliders() {
    std::uint64_t state = 0x9E3779B97F4A7C15ULL;
    for (int round = 0; round < 200; ++round) {
        const Bitboard occupied = next_random(state) & next_random(state);
        for (int square = 0; square < 64; ++square) {
            const Bitboard rook = walk(square, kRookSteps, occupied, true);
            const Bitboard bishop = walk(square, kBishopSteps, occupied, true);
            CHECK(sbm::rook_attacks(square, occupied) == rook);
            CHECK(sbm::bishop_attacks(square, occupied) == bishop);
            CHECK(sbm::queen_attacks(square, occupied) == (rook | bishop));
        }
    }
}

void test_lines() {
    for (int a = 0; a < 64; ++a) {
        for (int b = 0; b < 64; ++b) {
            const Bitboard others = sbm::square_bb(a) | sbm::square_bb(b);
            Bitboard between = 0;
            Bitboard line = 0;
            for (const auto& steps : {kRookSteps, kBishopSteps}) {
                for (const Step& step : steps) {
                    const Bitboard ray = walk(a, {step}, sbm::square_bb(b), true);
                    if ((ray & sbm::square_bb(b)) != 0) {
                        between = ray & ~others;
                        const Step back{-step.first, -step.second};
                        line =
                            walk(a, {step}, 0, true) | walk(a, {back}, 0, true) | sbm::square_bb(a);
                    }
                }
            }
            CHECK(sbm::between(a, b) == between);
            CHECK(sbm::line_through(a, b) == (a == b ? 0 : line));
        }
    }
}

} // namespace

void test_attacks() {
    test_leapers();
    test_sliders();
    test_lines();
}
