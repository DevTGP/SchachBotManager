# Turns a file into a C++ source with a byte array, so the program carries it (the font).
function(sbm_viewer_embed_file target input symbol)
    file(READ ${input} content HEX)
    string(REGEX REPLACE "([0-9a-f][0-9a-f])" "0x\\1," bytes "${content}")
    string(REGEX REPLACE "(0x..,0x..,0x..,0x..,0x..,0x..,0x..,0x..,0x..,0x..,0x..,0x..,)" "\\1\n"
        bytes "${bytes}")
    set(output ${CMAKE_CURRENT_BINARY_DIR}/embedded/${symbol}.cpp)
    file(CONFIGURE OUTPUT ${output} CONTENT
"// Generated from ${input}; do not edit.
#include <cstddef>

extern const unsigned char ${symbol}[] = {
${bytes}
};
extern const std::size_t ${symbol}_size = sizeof(${symbol});
")
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${input})
    target_sources(${target} PRIVATE ${output})
endfunction()
