#include "attacks.hpp"

#include <array>

namespace sbm {

namespace {

// Directions as file and rank steps. The first four increase the square index, so the nearest
// blocker on them is the lowest set bit; on the last four it is the highest.
struct Direction {
    int file;
    int rank;
};

constexpr int kDirectionCount = 8;
constexpr std::array<Direction, kDirectionCount> kDirections{{
    {0, 1},   // north
    {1, 1},   // north-east
    {1, 0},   // east
    {-1, 1},  // north-west
    {0, -1},  // south
    {-1, -1}, // south-west
    {-1, 0},  // west
    {1, -1},  // south-east
}};
constexpr int kOpposite = 4;
constexpr std::array<int, 4> kRookDirections{0, 2, 4, 6};
constexpr std::array<int, 4> kBishopDirections{1, 3, 5, 7};

using SquareTable = std::array<Bitboard, kSquareCount>;

constexpr bool increases_square(int direction) {
    return direction < kOpposite;
}

constexpr Bitboard steps(int square, const Direction* offsets, int count) {
    Bitboard result = 0;
    for (int i = 0; i < count; ++i) {
        const int file = file_of(square) + offsets[i].file;
        const int rank = rank_of(square) + offsets[i].rank;
        if (on_board(file, rank)) {
            result |= square_bb(make_square(file, rank));
        }
    }
    return result;
}

constexpr Bitboard ray(int square, Direction direction) {
    Bitboard result = 0;
    int file = file_of(square) + direction.file;
    int rank = rank_of(square) + direction.rank;
    while (on_board(file, rank)) {
        result |= square_bb(make_square(file, rank));
        file += direction.file;
        rank += direction.rank;
    }
    return result;
}

constexpr std::array<SquareTable, kDirectionCount> make_rays() {
    std::array<SquareTable, kDirectionCount> rays{};
    for (int direction = 0; direction < kDirectionCount; ++direction) {
        for (int square = 0; square < kSquareCount; ++square) {
            rays[direction][square] = ray(square, kDirections[direction]);
        }
    }
    return rays;
}

constexpr SquareTable make_steps(const Direction* offsets, int count) {
    SquareTable table{};
    for (int square = 0; square < kSquareCount; ++square) {
        table[square] = steps(square, offsets, count);
    }
    return table;
}

constexpr Direction kKnightSteps[] = {{1, 2},   {2, 1},   {2, -1}, {1, -2},
                                      {-1, -2}, {-2, -1}, {-2, 1}, {-1, 2}};
constexpr Direction kWhitePawnSteps[] = {{-1, 1}, {1, 1}};
constexpr Direction kBlackPawnSteps[] = {{-1, -1}, {1, -1}};

constexpr auto kRays = make_rays();
constexpr auto kKnightAttacks = make_steps(kKnightSteps, 8);
constexpr auto kKingAttacks = make_steps(kDirections.data(), kDirectionCount);
constexpr std::array<SquareTable, kColorCount> kPawnAttacks{
    make_steps(kWhitePawnSteps, 2), make_steps(kBlackPawnSteps, 2)};

Bitboard slide(int square, int direction, Bitboard occupied) {
    Bitboard attacks = kRays[direction][square];
    const Bitboard blockers = attacks & occupied;
    if (blockers != 0) {
        const int blocker = increases_square(direction) ? lsb(blockers) : msb(blockers);
        attacks ^= kRays[direction][blocker];
    }
    return attacks;
}

Bitboard slide_all(int square, const std::array<int, 4>& directions, Bitboard occupied) {
    Bitboard attacks = 0;
    for (const int direction : directions) {
        attacks |= slide(square, direction, occupied);
    }
    return attacks;
}

int sign(int value) {
    return (value > 0) - (value < 0);
}

// Direction from a to b if both share a rank, file or diagonal, otherwise -1.
int direction_between(int a, int b) {
    const int file_step = file_of(b) - file_of(a);
    const int rank_step = rank_of(b) - rank_of(a);
    if (a == b ||
        (file_step != 0 && rank_step != 0 && file_step != rank_step && file_step != -rank_step)) {
        return -1;
    }
    for (int direction = 0; direction < kDirectionCount; ++direction) {
        if (kDirections[direction].file == sign(file_step) &&
            kDirections[direction].rank == sign(rank_step)) {
            return direction;
        }
    }
    return -1;
}

int opposite_direction(int direction) {
    return (direction + kOpposite) % kDirectionCount;
}

} // namespace

Bitboard pawn_attacks(Color color, int square) {
    return kPawnAttacks[color][square];
}

Bitboard knight_attacks(int square) {
    return kKnightAttacks[square];
}

Bitboard king_attacks(int square) {
    return kKingAttacks[square];
}

Bitboard bishop_attacks(int square, Bitboard occupied) {
    return slide_all(square, kBishopDirections, occupied);
}

Bitboard rook_attacks(int square, Bitboard occupied) {
    return slide_all(square, kRookDirections, occupied);
}

Bitboard queen_attacks(int square, Bitboard occupied) {
    return bishop_attacks(square, occupied) | rook_attacks(square, occupied);
}

Bitboard piece_attacks(PieceType type, Color color, int square, Bitboard occupied) {
    switch (type) {
        case kPawn:
            return pawn_attacks(color, square);
        case kKnight:
            return knight_attacks(square);
        case kBishop:
            return bishop_attacks(square, occupied);
        case kRook:
            return rook_attacks(square, occupied);
        case kQueen:
            return queen_attacks(square, occupied);
        case kKing:
            return king_attacks(square);
        default:
            return 0;
    }
}

Bitboard between(int a, int b) {
    const int direction = direction_between(a, b);
    if (direction < 0) {
        return 0;
    }
    return kRays[direction][a] & kRays[opposite_direction(direction)][b];
}

Bitboard line_through(int a, int b) {
    const int direction = direction_between(a, b);
    if (direction < 0) {
        return 0;
    }
    return kRays[direction][a] | kRays[opposite_direction(direction)][a] | square_bb(a);
}

} // namespace sbm
