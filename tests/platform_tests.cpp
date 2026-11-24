#include "gtavi/platform.h"

#include <string>

#include "gtavi/version.h"
#include "test_framework.h"

GTAVI_TEST(current_platform_matches_build_target) {
#if defined(_WIN32)
    CHECK_TRUE(gtavi::current_platform() == gtavi::Platform::Windows);
#elif defined(__linux__)
    CHECK_TRUE(gtavi::current_platform() == gtavi::Platform::Linux);
#else
    CHECK_TRUE(gtavi::current_platform() == gtavi::Platform::Unknown);
#endif
}

GTAVI_TEST(platform_names_are_stable) {
    CHECK_EQ(gtavi::to_string(gtavi::Platform::Windows), std::string{"windows"});
    CHECK_EQ(gtavi::to_string(gtavi::Platform::Linux), std::string{"linux"});
    CHECK_EQ(gtavi::to_string(gtavi::Platform::Unknown), std::string{"unknown"});
}

GTAVI_TEST(platform_query_reports_host_facts) {
    const auto info = gtavi::query_platform_info();
    if (gtavi::current_platform() == gtavi::Platform::Unknown) {
        // Hosts the layer cannot describe (macOS, for example) must say so
        // rather than report made-up facts.
        CHECK_FALSE(info.ok());
        if (!info.ok()) {
            CHECK_EQ(info.error().code(), gtavi::ErrorCode::UnsupportedPlatform);
        }
        return;
    }
    CHECK_TRUE(info.ok());
    if (!info.ok()) {
        return;
    }
    CHECK_TRUE(info.value().platform == gtavi::current_platform());
    CHECK_FALSE(info.value().os_version.empty());
    CHECK_FALSE(info.value().architecture.empty());
}

GTAVI_TEST(version_constants_are_consistent) {
    CHECK_EQ(std::string{gtavi::version_string},
             std::to_string(gtavi::version_major) + "." + std::to_string(gtavi::version_minor) + "." +
                 std::to_string(gtavi::version_patch));
}
