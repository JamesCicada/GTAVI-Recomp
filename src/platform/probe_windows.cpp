#include <windows.h>

#include <stdexcept>
#include <string>
#include <vector>

#include "probe.h"

namespace {

// wmain receives the original command line before conversion through the ANSI code page.
std::string utf8_argument(const wchar_t* argument) {
    const int size = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, argument, -1, nullptr, 0,
                                         nullptr, nullptr);
    if (size == 0) {
        throw std::invalid_argument("command-line argument contains invalid UTF-16");
    }
    std::string result(static_cast<std::size_t>(size), '\0');
    if (WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, argument, -1, result.data(), size,
                            nullptr, nullptr) != size) {
        throw std::runtime_error("could not convert command-line argument to UTF-8");
    }
    result.pop_back();  // The size includes the terminating NUL.
    return result;
}

void write_text(std::FILE* stream, std::string_view text) {
    const HANDLE handle = GetStdHandle(stream == stdout ? STD_OUTPUT_HANDLE : STD_ERROR_HANDLE);
    DWORD mode{};
    if (!GetConsoleMode(handle, &mode)) {
        if (std::fwrite(text.data(), 1, text.size(), stream) != text.size()) {
            throw std::runtime_error("could not write probe output");
        }
        return;
    }

    // Keep the ASCII banner and host facts ahead of direct console writes.
    std::fflush(stream);
    const int length = static_cast<int>(text.size());
    // A UTF-8 byte sequence occupies at most as many UTF-16 code units as bytes.
    std::wstring wide(text.size(), L'\0');
    const int size = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, text.data(), length,
                                         wide.data(), length);
    if (size == 0) {
        throw std::runtime_error("could not decode probe output");
    }
    wide.resize(static_cast<std::size_t>(size));
    // Mirror the CRT's text-mode line endings on the native console.
    std::wstring line;
    line.reserve(wide.size());
    for (const wchar_t ch : wide) {
        if (ch == L'\n') {
            line.push_back(L'\r');
        }
        line.push_back(ch);
    }
    std::wstring_view remaining{line};
    while (!remaining.empty()) {
        DWORD written{};
        if (!WriteConsoleW(handle, remaining.data(), static_cast<DWORD>(remaining.size()), &written,
                           nullptr) ||
            written == 0) {
            throw std::runtime_error("could not write probe output to the console");
        }
        remaining.remove_prefix(written);
    }
}

}  // namespace

int wmain(int argc, wchar_t* argv[]) {
    try {
        std::vector<std::string> arguments;
        for (int i = 1; i < argc; ++i) {
            arguments.push_back(utf8_argument(argv[i]));
        }
        return run_probe(arguments, write_text);
    } catch (const std::invalid_argument& error) {
        std::fprintf(stderr, "%s\n", error.what());
        return 2;
    } catch (const std::runtime_error& error) {
        std::fprintf(stderr, "%s\n", error.what());
        return 1;
    }
}
