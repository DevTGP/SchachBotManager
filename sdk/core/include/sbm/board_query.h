/* Single properties of the position (spec/api/board_query.json). */
#ifndef SBM_BOARD_QUERY_H
#define SBM_BOARD_QUERY_H

#include <stdint.h>

#include "sbm/board.h"
#include "sbm/export.h"
#include "sbm/status.h"
#include "sbm/types.h"

SBM_BEGIN_DECLS

SBM_API sbm_status sbm_board_piece_at(const sbm_board* board, sbm_square square, sbm_piece* out);

/* Board.pieces: square and piece of each match in squares[i] and pieces[i], ordered by square,
 * never more than SBM_SQUARE_COUNT. SBM_NO_COLOR and SBM_NO_PIECE_TYPE match everything (E188).
 * Buffer rule as for move lists (E51): squares and pieces may be NULL only with capacity 0. */
SBM_API sbm_status sbm_board_pieces(
    const sbm_board* board, sbm_color color, sbm_piece_type piece_type, sbm_square* squares,
    sbm_piece* pieces, uint32_t capacity, uint32_t* count);
SBM_API sbm_status sbm_board_side_to_move(const sbm_board* board, sbm_color* out);
SBM_API sbm_status sbm_board_castling_rights(const sbm_board* board, sbm_castling* out);
SBM_API sbm_status sbm_board_en_passant_square(const sbm_board* board, sbm_square* out);
SBM_API sbm_status sbm_board_halfmove_clock(const sbm_board* board, int32_t* out);
SBM_API sbm_status sbm_board_fullmove_number(const sbm_board* board, int32_t* out);
SBM_API sbm_status sbm_board_king_square(const sbm_board* board, sbm_color color, sbm_square* out);

SBM_END_DECLS

#endif
