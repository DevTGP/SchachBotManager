/* Generating, checking, making and taking back moves (spec/api/board_moves.json). */
#ifndef SBM_BOARD_MOVES_H
#define SBM_BOARD_MOVES_H

#include <stdint.h>

#include "sbm/board.h"
#include "sbm/export.h"
#include "sbm/status.h"
#include "sbm/types.h"

SBM_BEGIN_DECLS

/* Board.legal_moves and Board.legal_captures: never more than SBM_MAX_MOVES. */
SBM_API sbm_status sbm_board_legal_moves(
    const sbm_board* board, sbm_move* out, uint32_t capacity, uint32_t* count);
SBM_API sbm_status sbm_board_legal_captures(
    const sbm_board* board, sbm_move* out, uint32_t capacity, uint32_t* count);

/* Board.is_legal: malformed move values give false, not an error. */
SBM_API sbm_status sbm_board_is_legal(const sbm_board* board, sbm_move move, sbm_bool* out);

SBM_API sbm_status sbm_board_parse_move(const sbm_board* board, const char* uci, sbm_move* out);

/* Board.san: needs SBM_SAN_BUFFER_SIZE bytes at most. */
SBM_API sbm_status sbm_board_san(
    const sbm_board* board, sbm_move move, char* buffer, uint32_t size);

SBM_API sbm_status sbm_board_make_move(sbm_board* board, sbm_move move);
SBM_API sbm_status sbm_board_undo_move(sbm_board* board);
SBM_API sbm_status sbm_board_make_null_move(sbm_board* board);
SBM_API sbm_status sbm_board_undo_null_move(sbm_board* board);

SBM_END_DECLS

#endif
