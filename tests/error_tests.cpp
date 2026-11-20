#include "gtavi/error.h"

#include <string>

#include "test_framework.h"

using gtavi::Error;
using gtavi::ErrorCode;
using gtavi::Result;

GTAVI_TEST(default_error_is_success) {
    const Error error;
    CHECK_FALSE(error);
    CHECK_TRUE(error.code() == ErrorCode::Ok);
}

GTAVI_TEST(error_with_code_is_truthy) {
    const Error error{ErrorCode::PathEmpty, "empty"};
    CHECK_TRUE(error);
    CHECK_EQ(static_cast<int>(error.code()), static_cast<int>(ErrorCode::PathEmpty));
    CHECK_EQ(error.message(), std::string{"empty"});
}

GTAVI_TEST(describe_includes_code_and_message) {
    const Error error{ErrorCode::PathInvalid, "bad path"};
    CHECK_EQ(error.describe(), std::string{"path_invalid: bad path"});
}

GTAVI_TEST(describe_without_message_is_just_the_code) {
    const Error error{ErrorCode::Internal, ""};
    CHECK_EQ(error.describe(), std::string{"internal"});
}

GTAVI_TEST(result_holds_value) {
    const Result<std::string> result{std::string{"value"}};
    CHECK_TRUE(result.ok());
    CHECK_TRUE(static_cast<bool>(result));
    CHECK_EQ(result.value(), std::string{"value"});
    CHECK_EQ(result.value_or("fallback"), std::string{"value"});
}

GTAVI_TEST(result_holds_error) {
    const Result<std::string> result{Error{ErrorCode::PathEmpty, "empty"}};
    CHECK_FALSE(result.ok());
    CHECK_EQ(result.error().code(), ErrorCode::PathEmpty);
    CHECK_EQ(result.value_or("fallback"), std::string{"fallback"});
}

GTAVI_TEST(error_code_names_are_stable) {
    CHECK_EQ(gtavi::to_string(ErrorCode::Ok), std::string{"ok"});
    CHECK_EQ(gtavi::to_string(ErrorCode::PathEmpty), std::string{"path_empty"});
    CHECK_EQ(gtavi::to_string(ErrorCode::PathInvalid), std::string{"path_invalid"});
    CHECK_EQ(gtavi::to_string(ErrorCode::PathUnsupportedForm),
             std::string{"path_unsupported_form"});
    CHECK_EQ(gtavi::to_string(ErrorCode::PathUnmappedDrive), std::string{"path_unmapped_drive"});
    CHECK_EQ(gtavi::to_string(ErrorCode::UnsupportedPlatform), std::string{"unsupported_platform"});
}
