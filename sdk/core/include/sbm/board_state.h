/* End conditions (spec/api/board_state.json). */
#ifndef SBM_BOARD_STATE_H
#define SBM_BOARD_STATE_H

#include <stdint.h>

#include "sbm/board.h"
#include "sbm/export.h"
#include "sbm/status.h"
#include "sbm/types.h"

SBM_BEGIN_DECLS

SBM_API sbm_status sbm_board_is_check(const sbm_board* board, sbm_bool* out);
SBM_API sbm_status sbm_board_is_checkmate(const sbm_board* board, sbm_bool* out);
SBM_API sbm_status sbm_board_is_stalemate(const sbm_board* board, sbm_bool* out);
SBM_API sbm_status sbm_board_is_repetition(const sbm_board* board, int32_t count, sbm_bool* out);
SBM_API sbm_status sbm_board_is_fifty_move_rule(const sbm_board* board, sbm_bool* out);
SBM_API sbm_status sbm_board_is_insufficient_material(const sbm_board* board, sbm_bool* out);
SBM_API sbm_status
sbm_board_has_insufficient_material(const sbm_board* board, sbm_color color, sbm_bool* out);
SBM_API sbm_status sbm_board_is_draw(const sbm_board* board, sbm_bool* out);
SBM_API sbm_status sbm_board_is_game_over(const sbm_board* board, sbm_bool* out);

SBM_END_DECLS

#endif
