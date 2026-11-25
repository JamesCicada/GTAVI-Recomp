#pragma once

#include <cstdio>
#include <span>
#include <string>
#include <string_view>

// write_text handles translations and diagnostic records that may contain host paths.
using ProbeWriter = void (*)(std::FILE*, std::string_view);

int run_probe(std::span<const std::string> arguments, ProbeWriter write_text);
