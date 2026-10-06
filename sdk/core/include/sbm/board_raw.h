/* Raw access as bitboards and arrays (spec/api/board_raw.json). */
#ifndef SBM_BOARD_RAW_H
#define SBM_BOARD_RAW_H

#include <stdint.h>

#include "sbm/board.h"
#include "sbm/export.h"
#include "sbm/status.h"
#include "sbm/types.h"

SBM_BEGIN_DECLS

SBM_API sbm_status sbm_board_bitboard(
    const sbm_board* board, sbm_color color, sbm_piece_type piece_type, sbm_bitboard* out);

/* Board.bitboards: out has SBM_PIECE_COUNT entries, indexed by piece. */
SBM_API sbm_status sbm_board_bitboards(const sbm_board* board, sbm_bitboard* out);

/* Board.squares: out has SBM_SQUARE_COUNT entries, indexed by square. */
SBM_API sbm_status sbm_board_squares(const sbm_board* board, sbm_piece* out);

SBM_API sbm_status sbm_board_occupied(const sbm_board* board, sbm_bitboard* out);
SBM_API sbm_status sbm_board_occupied_by(const sbm_board* board, sbm_color color, sbm_bitboard* out);
SBM_API sbm_status sbm_board_piece_count(
    const sbm_board* board, sbm_color color, sbm_piece_type piece_type, int32_t* out);
SBM_API sbm_status sbm_board_attacks_from(
    const sbm_board* board, sbm_square square, sbm_bitboard* out);
SBM_API sbm_status sbm_board_attackers_of(
    const sbm_board* board, sbm_square square, sbm_color color, sbm_bitboard* out);
SBM_API sbm_status sbm_board_is_attacked(
    const sbm_board* board, sbm_square square, sbm_color color, sbm_bool* out);
SBM_API sbm_status sbm_board_checkers(const sbm_board* board, sbm_bitboard* out);
SBM_API sbm_status sbm_board_pinned(const sbm_board* board, sbm_color color, sbm_bitboard* out);

SBM_END_DECLS

#endif
