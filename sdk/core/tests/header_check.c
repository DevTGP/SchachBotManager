/* Compiles the public headers as C11 and checks the codes fixed by E34, E35 and E45. */
#include "sbm/sbm.h"

_Static_assert(sizeof(sbm_move) == 2, "move is 16 bits");
_Static_assert(sizeof(sbm_bitboard) == 8, "bitboard is 64 bits");
_Static_assert(sizeof(sbm_bool) == 4, "bool is a 32-bit integer");
_Static_assert(sizeof(sbm_status) == 4, "status is a 32-bit integer");

_Static_assert(SBM_BLACK == 1, "colors");
_Static_assert(SBM_KING == 5 && SBM_NO_PIECE_TYPE == 6, "piece types");
_Static_assert(SBM_NO_PIECE == 12 && SBM_PIECE_COUNT == 12, "pieces");
_Static_assert(SBM_NO_SQUARE == 64 && SBM_SQUARE_COUNT == 64, "squares");
_Static_assert(SBM_BLACK_QUEENSIDE == 8, "castling");
_Static_assert(SBM_FLAG_PROMOTION_CAPTURE == 12, "flags");
_Static_assert(SBM_NULL_MOVE == 0 && SBM_RESIGN == 0xFFFF, "special moves");
_Static_assert(SBM_INTERNAL_ERROR == 8, "status codes");
_Static_assert(SBM_ABI_VERSION == 1, "abi version");

int main(void) {
    return SBM_OK;
}
