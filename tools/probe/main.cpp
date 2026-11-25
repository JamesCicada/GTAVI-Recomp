// gtavi-probe: diagnostic front end for the translation layer.
//
// Prints host facts and exercises the path translation rules so that behaviour
// can be compared between Windows and Linux builds.

#include "gtavi/log.h"
#include "gtavi/path.h"
#include "gtavi/platform.h"
#include "gtavi/version.h"

#include <cstdio>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "probe.h"

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
        "  -h, --help           show this message\n"
        "\n"
        "Exit status: 0 on success, 2 on a usage error. When paths are given, 1 means\n"
        "a translation failed; a host the layer cannot describe only logs a warning.\n"
        "Without paths, 1 means the host query failed.\n",
        stderr);
}

std::string to_string(std::string_view text) {
    return std::string{text};
}

/// Prints host facts. A failed query is an error when host facts are what was
/// asked for, and only a warning when the probe was asked to translate paths,
/// so path translation stays usable on hosts the layer does not support.
int print_platform_info(gtavi::Logger& logger, bool host_facts_requested) {
    const auto info = gtavi::query_platform_info();
    if (!info) {
        const std::string message = "platform query failed: " + info.error().describe();
        if (host_facts_requested) {
            logger.error(message);
            return 1;
        }
        logger.warn(message);
        return 0;
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

int run_probe(std::span<const std::string> arguments, ProbeWriter write_text) {
    gtavi::Logger& logger = gtavi::Logger::default_logger();
    logger.add_sink([write_text](const gtavi::LogRecord& record) {
        std::ostringstream message;
        gtavi::make_stream_sink(message)(record);
        write_text(stderr, message.str());
        std::fflush(stderr);
    });

    std::printf("gtavi-probe %s\n", to_string(gtavi::version_string).c_str());

    if (arguments.empty()) {
        const int exit_code = print_platform_info(logger, /*host_facts_requested=*/true);
        std::fputs("\npass --to-posix or --to-windows with a path to test translation\n", stderr);
        return exit_code;
    }

    std::vector<gtavi::DriveMapping> mounts;
    std::vector<Translation> translations;
    for (std::size_t index = 0; index < arguments.size(); ++index) {
        const std::string_view option = arguments[index];

        if (option == "-h" || option == "--help") {
            const int exit_code = print_platform_info(logger, /*host_facts_requested=*/true);
            print_usage();
            return exit_code;
        }

        if (option != "--to-posix" && option != "--to-windows" && option != "--mount") {
            logger.error("unknown argument: " + to_string(option));
            print_usage();
            return 2;
        }

        if (index + 1 >= arguments.size()) {
            logger.error("missing path after " + to_string(option));
            return 2;
        }

        const std::string_view path = arguments[++index];
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

    // Host facts are informational here: only the translations set the exit
    // status, unless nothing was given to translate (just --mount).
    int exit_code = print_platform_info(logger, /*host_facts_requested=*/translations.empty());

    const auto defaults = gtavi::DriveMap::default_map();
    mounts.insert(mounts.end(), defaults.mappings().begin(), defaults.mappings().end());
    const auto map = gtavi::DriveMap::with_mappings(std::move(mounts));
    for (const auto& [to_posix, path] : translations) {
        const auto converted =
            to_posix ? gtavi::windows_to_posix(path, map) : gtavi::posix_to_windows(path, map);
        if (converted) {
            write_text(stdout, to_string(path) + " -> " + converted.value() + '\n');
        } else {
            logger.error(converted.error().describe());
            exit_code = 1;
        }
    }

    return exit_code;
}
