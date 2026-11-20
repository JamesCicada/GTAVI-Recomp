#include <iostream>

#include "test_framework.h"

namespace testing {

std::vector<TestCase>& registry() {
    static std::vector<TestCase> tests;
    return tests;
}

int& failure_count() {
    static int count = 0;
    return count;
}

}  // namespace testing

int main() {
    int failed_tests = 0;
    for (const auto& test : testing::registry()) {
        const int before = testing::failure_count();
        test.body();
        if (testing::failure_count() != before) {
            ++failed_tests;
            std::cerr << "[FAILED] " << test.name << '\n';
        }
    }

    const auto total = static_cast<int>(testing::registry().size());
    std::cout << (total - failed_tests) << '/' << total << " tests passed\n";
    if (failed_tests != 0) {
        std::cout << failed_tests << " test(s) failed\n";
        return 1;
    }
    return 0;
}
