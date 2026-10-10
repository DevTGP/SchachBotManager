# Tests of the viewer model; the window itself is checked by the screenshot smoke test in CI.
add_executable(sbm_viewer_model_tests
    game_record_test.cpp
    main.cpp
    messages_test.cpp
    navigation_test.cpp
    session_test.cpp
    text_test.cpp
)
target_include_directories(sbm_viewer_model_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../../core/tests/unit)
target_link_libraries(sbm_viewer_model_tests PRIVATE sbm_viewer_model)
sbm_enable_warnings(sbm_viewer_model_tests)
add_test(NAME viewer_model COMMAND sbm_viewer_model_tests)
