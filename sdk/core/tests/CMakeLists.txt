# Core tests: the vectors of spec/testvectors/ through the C interface, plus unit tests.
include(FetchContent)

# Test-only dependency; never part of the shipped library.
FetchContent_Declare(nlohmann_json
    URL https://github.com/nlohmann/json/releases/download/v3.12.0/json.tar.xz
    URL_HASH SHA256=42f6e95cad6ec532fd372391373363b62a14af6d771056dbfc86160e6dfff7aa
    DOWNLOAD_EXTRACT_TIMESTAMP ON
)
set(JSON_Install OFF CACHE INTERNAL "")
FetchContent_MakeAvailable(nlohmann_json)

option(SBM_SLOW_TESTS "Also run the perft vectors marked slow" OFF)
set(SBM_TESTVECTORS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../../../spec/testvectors
    CACHE PATH "Directory of the test vectors")

add_executable(sbm_vector_tests
    vectors/board_setup.cpp
    vectors/calls_board.cpp
    vectors/calls_board_moves.cpp
    vectors/calls_board_query.cpp
    vectors/calls_board_raw.cpp
    vectors/calls_board_state.cpp
    vectors/calls_move.cpp
    vectors/json_values.cpp
    vectors/main.cpp
    vectors/perft.cpp
    vectors/run_calls.cpp
)
target_link_libraries(sbm_vector_tests PRIVATE sbm nlohmann_json::nlohmann_json)
sbm_enable_warnings(sbm_vector_tests)

if(SBM_SLOW_TESTS)
    add_test(NAME vectors COMMAND sbm_vector_tests --slow ${SBM_TESTVECTORS_DIR})
else()
    add_test(NAME vectors COMMAND sbm_vector_tests ${SBM_TESTVECTORS_DIR})
endif()

# Internal modules against simple reference implementations.
add_executable(sbm_engine_tests
    unit/attacks_test.cpp
    unit/engine_main.cpp
)
target_link_libraries(sbm_engine_tests PRIVATE sbm_engine)
sbm_enable_warnings(sbm_engine_tests)
add_test(NAME engine COMMAND sbm_engine_tests)

# Rules of the C interface that the vectors do not cover: pointers, buffers, versions.
add_executable(sbm_capi_tests
    unit/capi_buffers_test.cpp
    unit/capi_handles_test.cpp
    unit/capi_main.cpp
)
target_link_libraries(sbm_capi_tests PRIVATE sbm)
target_compile_definitions(sbm_capi_tests PRIVATE SBM_EXPECTED_VERSION="${PROJECT_VERSION}")
sbm_enable_warnings(sbm_capi_tests)
add_test(NAME capi COMMAND sbm_capi_tests)
