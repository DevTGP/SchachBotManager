// Board: owns one board handle of the core, freed together with the Python object (E22).
#pragma once

#include <memory>

#include <nanobind/nanobind.h>

#include "sbm/board.h"

namespace sbm_py {

struct BoardFree {
    void operator()(sbm_board* board) const noexcept {
        sbm_board_free(board);
    }
};

class Board {
public:
    explicit Board(sbm_board* handle) noexcept : handle_(handle) {}

    sbm_board* get() const noexcept {
        return handle_.get();
    }

private:
    std::unique_ptr<sbm_board, BoardFree> handle_;
};

using BoardClass = nanobind::class_<Board>;

// One function per module of spec/api/ that adds its Board functions.
void bind_board(BoardClass& cls);
void bind_board_moves(BoardClass& cls);
void bind_board_query(BoardClass& cls);
void bind_board_raw(BoardClass& cls);
void bind_board_state(BoardClass& cls);

} // namespace sbm_py
