#include "check.hpp"
#include "model/navigation.hpp"

using namespace sbm_viewer;

namespace {

void follows_live_and_pins() {
    Navigation navigation;
    CHECK(navigation.live());
    CHECK(navigation.shown(5) == 5);

    navigation.step(-2, 5);
    CHECK(!navigation.live());
    CHECK(navigation.shown(5) == 3);
    CHECK(navigation.shown(9) == 3);

    navigation.first(9);
    CHECK(navigation.shown(9) == 0);
    navigation.step(-1, 9);
    CHECK(navigation.shown(9) == 0);

    navigation.go_to(9, 9);
    CHECK(navigation.live());
    navigation.go_to(2, 9);
    navigation.last();
    CHECK(navigation.live());
    CHECK(navigation.shown(12) == 12);
}

void selects_games() {
    Navigation navigation;
    navigation.games_changed(1);
    CHECK(navigation.game() == 0);
    navigation.games_changed(2);
    CHECK(navigation.game() == 1);

    navigation.select_game(0, 2);
    navigation.games_changed(3);
    CHECK(navigation.game() == 0);

    navigation.step(-1, 4);
    navigation.select_game(2, 3);
    CHECK(navigation.live());
    navigation.games_changed(4);
    CHECK(navigation.game() == 3);
}

} // namespace

void test_navigation() {
    follows_live_and_pins();
    selects_games();
}
