/* Board handle: creating, copying, freeing and printing (spec/api/board.json). */
#ifndef SBM_BOARD_H
#define SBM_BOARD_H

#include <stdint.h>

#include "sbm/export.h"
#include "sbm/status.h"
#include "sbm/types.h"

typedef struct sbm_board sbm_board;

SBM_BEGIN_DECLS

/* Board.create: standard start position. */
SBM_API sbm_status sbm_board_new(sbm_board** out);

SBM_API sbm_status sbm_board_from_fen(const char* fen, sbm_board** out);

/* Board.copy: independent board including the move history. */
SBM_API sbm_status sbm_board_copy(const sbm_board* board, sbm_board** out);

/* Frees a board created by sbm_board_new, sbm_board_from_fen or sbm_board_copy.
 * NULL is ignored. */
SBM_API void sbm_board_free(sbm_board* board);

/* Board.fen: needs SBM_FEN_BUFFER_SIZE bytes at most. */
SBM_API sbm_status sbm_board_fen(const sbm_board* board, char* buffer, uint32_t size);

/* Board.hash: Polyglot key (E46). */
SBM_API sbm_status sbm_board_hash(const sbm_board* board, uint64_t* out);

/* Board.move_history: has no fixed maximum; with capacity 0 (out may then be NULL) the call
 * returns SBM_BUFFER_TOO_SMALL and the required count. */
SBM_API sbm_status
sbm_board_move_history(const sbm_board* board, sbm_move* out, uint32_t capacity, uint32_t* count);

/* Board.to_text: needs SBM_TEXT_BUFFER_SIZE bytes at most. */
SBM_API sbm_status sbm_board_to_text(const sbm_board* board, char* buffer, uint32_t size);

SBM_END_DECLS

#endif
