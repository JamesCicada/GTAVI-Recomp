// Minimal test framework.
//
// The project avoids external dependencies, so this header provides just enough
// to register test cases and report failures. Tests are discovered through
// static registration in each translation unit and run by tests/main.cpp.

#pragma once

#include <functional>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace testing {

struct TestCase {
    std::string name;
    std::function<void()> body;
};

std::vector<TestCase>& registry();
int& failure_count();

struct Registrar {
    Registrar(std::string name, std::function<void()> body) {
        registry().push_back(TestCase{std::move(name), std::move(body)});
    }
};

inline void report_failure(const char* file, int line, const std::string& message) {
    ++failure_count();
    std::cerr << file << ':' << line << ": failure: " << message << '\n';
}

}  // namespace testing

/// Defines a test case. The body follows the macro in braces.
#define GTAVI_TEST(name)                                                                          \
    static void name();                                                                           \
    static const ::testing::Registrar registrar_##name{#name, name};                              \
    static void name()

#define CHECK_TRUE(expression)                                                                    \
    do {                                                                                          \
        if (!(expression)) {                                                                      \
            ::testing::report_failure(__FILE__, __LINE__, #expression);                           \
        }                                                                                         \
    } while (false)

#define CHECK_FALSE(expression) CHECK_TRUE(!(expression))

#define CHECK_EQ(actual, expected)                                                                \
    do {                                                                                          \
        const auto& gtavi_actual = (actual);                                                      \
        const auto& gtavi_expected = (expected);                                                  \
        if (!(gtavi_actual == gtavi_expected)) {                                                  \
            std::ostringstream gtavi_stream;                                                      \
            gtavi_stream << "expected [" << gtavi_expected << "], got [" << gtavi_actual << "]";  \
            ::testing::report_failure(__FILE__, __LINE__, gtavi_stream.str());                    \
        }                                                                                         \
    } while (false)
