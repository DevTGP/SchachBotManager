// Model of the viewer: messages, game record, session, navigation and texts.
#include "check.hpp"

void test_messages();
void test_game_record();
void test_session();
void test_navigation();
void test_texts();

int main() {
    test_messages();
    test_game_record();
    test_session();
    test_navigation();
    test_texts();
    return sbm_unit::report("sbm_viewer_model_tests");
}
