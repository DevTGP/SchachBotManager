// The opaque board handle of the C interface: a game with its move history.
#pragma once

#include "game.hpp"
#include "sbm/board.h"

struct sbm_board {
    sbm::Game game;
};
