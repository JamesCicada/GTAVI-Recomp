#include <vector>

#include "probe.h"

int main(int argc, char* argv[]) {
    std::vector<std::string> arguments;
    for (int i = 1; i < argc; ++i) {
        arguments.emplace_back(argv[i]);
    }
    return run_probe(arguments, [](std::FILE* stream, std::string_view text) {
        std::fwrite(text.data(), 1, text.size(), stream);
    });
}
