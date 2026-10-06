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
SBM_API sbm_status sbm_board_side_to_move(const sbm_board* board, sbm_color* out);
SBM_API sbm_status sbm_board_castling_rights(const sbm_board* board, sbm_castling* out);
SBM_API sbm_status sbm_board_en_passant_square(const sbm_board* board, sbm_square* out);
SBM_API sbm_status sbm_board_halfmove_clock(const sbm_board* board, int32_t* out);
SBM_API sbm_status sbm_board_fullmove_number(const sbm_board* board, int32_t* out);
SBM_API sbm_status sbm_board_king_square(const sbm_board* board, sbm_color color, sbm_square* out);

SBM_END_DECLS

#endif
