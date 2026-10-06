/* Board-independent move functions (spec/api/move.json).
 * The pure bit operations of Move (from_square, to_square, flags, promotion, is_capture, ...)
 * have no C function; each binding computes them from the encoding (E34). */
#ifndef SBM_MOVE_H
#define SBM_MOVE_H

#include <stdint.h>

#include "sbm/export.h"
#include "sbm/status.h"
#include "sbm/types.h"

SBM_BEGIN_DECLS

/* Move.parse: SBM_INVALID_UCI for anything but [a-h][1-8][a-h][1-8][nbrq]?. */
SBM_API sbm_status sbm_move_parse(const char* uci, sbm_move* out);

/* Move.uci: SBM_INVALID_ARGUMENT for NULL_MOVE, RESIGN and values with flags 6 or 7. */
SBM_API sbm_status sbm_move_uci(sbm_move move, char* buffer, uint32_t size);

SBM_END_DECLS

#endif
