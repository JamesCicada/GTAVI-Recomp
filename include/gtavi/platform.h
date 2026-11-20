#pragma once

#include <string>
#include <string_view>

#include "gtavi/error.h"

namespace gtavi {

/// Host platforms the layer knows how to describe. "Unknown" builds compile but
/// every platform query reports ErrorCode::UnsupportedPlatform.
enum class Platform {
    Unknown = 0,
    Windows,
    Linux,
};

/// The platform this binary was compiled for.
constexpr Platform current_platform() noexcept {
#if defined(_WIN32)
    return Platform::Windows;
#elif defined(__linux__)
    return Platform::Linux;
#else
    return Platform::Unknown;
#endif
}

std::string_view to_string(Platform platform) noexcept;

/// Facts about the host, collected for diagnostics and bug reports.
struct PlatformInfo {
    Platform platform = Platform::Unknown;
    /// Windows: "10.0.26100". Linux: kernel release, for example "6.8.0-45-generic".
    std::string os_version;
    /// "x86_64", "arm64", "x86", or "unknown".
    std::string architecture;
};

/// Queries the running OS. Fails only when the platform is not supported.
Result<PlatformInfo> query_platform_info();

}  // namespace gtavi
