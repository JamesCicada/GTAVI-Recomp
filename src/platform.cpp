#include "gtavi/platform.h"

#include <string>

namespace gtavi {

namespace detail {
/// Implemented once per supported platform in src/platform/.
Result<std::string> query_os_version();
}  // namespace detail

namespace {

constexpr std::string_view architecture_string() noexcept {
#if defined(_M_X64) || defined(__x86_64__)
    return "x86_64";
#elif defined(_M_ARM64) || defined(__aarch64__)
    return "arm64";
#elif defined(_M_IX86) || defined(__i386__)
    return "x86";
#else
    return "unknown";
#endif
}

}  // namespace

std::string_view to_string(Platform platform) noexcept {
    switch (platform) {
        case Platform::Unknown:
            return "unknown";
        case Platform::Windows:
            return "windows";
        case Platform::Linux:
            return "linux";
    }
    return "unknown";
}

Result<PlatformInfo> query_platform_info() {
    PlatformInfo info;
    info.platform = current_platform();
    info.architecture = std::string{architecture_string()};

    auto version = detail::query_os_version();
    if (!version) {
        return version.error();
    }
    info.os_version = version.value();
    return info;
}

}  // namespace gtavi
