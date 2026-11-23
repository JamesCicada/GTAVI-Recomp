// gtavi-probe: diagnostic front end for the translation layer.
//
// Prints host facts and exercises the path translation rules so that behaviour
// can be compared between Windows and Linux builds.

#include <cstdio>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "gtavi/log.h"
#include "gtavi/path.h"
#include "gtavi/platform.h"
#include "gtavi/version.h"

namespace {

void print_usage() {
    std::fputs(
        "usage: gtavi-probe [--mount <drive:/root>] [--to-posix <windows-path>]\n"
        "                   [--to-windows <posix-path>]...\n"
        "\n"
        "Prints host information and translates the supplied paths using the\n"
        "default drive map (A: through Z: -> /mnt/a through /mnt/z).\n"
        "\n"
        "  --to-posix <path>    translate a Windows path to a POSIX path\n"
        "  --to-windows <path>  translate a POSIX path to a Windows path\n"
        "  --mount <drive:/root> override a drive's mount for all translations\n"
        "  -h, --help           show this message\n",
        stderr);
}

std::string to_string(std::string_view text) {
    return std::string{text};
}

int print_platform_info(gtavi::Logger& logger) {
    const auto info = gtavi::query_platform_info();
    if (!info) {
        logger.error("platform query failed: " + info.error().describe());
        return 1;
    }

    std::printf("platform:     %s\n", to_string(gtavi::to_string(info.value().platform)).c_str());
    std::printf("os version:   %s\n", info.value().os_version.c_str());
    std::printf("architecture: %s\n", info.value().architecture.c_str());
    return 0;
}

struct Translation {
    bool to_posix;
    std::string_view path;
};

}  // namespace

int main(int argc, char* argv[]) {
    gtavi::Logger& logger = gtavi::Logger::default_logger();
    logger.add_sink(gtavi::make_stderr_sink());

    std::printf("gtavi-probe %s\n", to_string(gtavi::version_string).c_str());

    int exit_code = print_platform_info(logger);

    if (argc == 1) {
        std::fputs("\npass --to-posix or --to-windows with a path to test translation\n", stderr);
        return exit_code;
    }

    std::vector<gtavi::DriveMapping> mounts;
    std::vector<Translation> translations;
    for (int index = 1; index < argc; ++index) {
        const std::string_view option = argv[index];

        if (option == "-h" || option == "--help") {
            print_usage();
            return exit_code;
        }

        if (option != "--to-posix" && option != "--to-windows" && option != "--mount") {
            logger.error("unknown argument: " + to_string(option));
            print_usage();
            return 2;
        }

        if (index + 1 >= argc) {
            logger.error("missing path after " + to_string(option));
            return 2;
        }

        const std::string_view path = argv[++index];
        if (option == "--mount") {
            if (!gtavi::has_drive_designator(path) || path.size() < 3 || path[2] != '/' ||
                path.find('\\') != std::string_view::npos) {
                logger.error("invalid mount: " + to_string(path) + " (expected drive:/absolute/posix/path)");
                return 2;
            }
            mounts.push_back({path.front(), to_string(path.substr(2))});
        } else {
            translations.push_back({option == "--to-posix", path});
        }
    }

    const auto defaults = gtavi::DriveMap::default_map();
    mounts.insert(mounts.end(), defaults.mappings().begin(), defaults.mappings().end());
    const auto map = gtavi::DriveMap::with_mappings(std::move(mounts));
    for (const auto& [to_posix, path] : translations) {
        if (to_posix) {
            const auto converted = gtavi::windows_to_posix(path, map);
            if (converted) {
                std::printf("%s -> %s\n", to_string(path).c_str(), converted.value().c_str());
            } else {
                logger.error(converted.error().describe());
                exit_code = 1;
            }
        } else {
            const auto converted = gtavi::posix_to_windows(path, map);
            if (converted) {
                std::printf("%s -> %s\n", to_string(path).c_str(), converted.value().c_str());
            } else {
                logger.error(converted.error().describe());
                exit_code = 1;
            }
        }
    }

    return exit_code;
}
