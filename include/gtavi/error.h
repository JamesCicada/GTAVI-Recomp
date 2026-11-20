#pragma once

#include <optional>
#include <ostream>
#include <string>
#include <string_view>
#include <utility>

namespace gtavi {

/// Stable error identifiers. Values are part of the public interface and must
/// not be reordered; append new entries at the end.
enum class ErrorCode {
    Ok = 0,
    InvalidArgument,
    PathEmpty,
    PathInvalid,
    PathUnsupportedForm,
    PathUnmappedDrive,
    UnsupportedPlatform,
    Internal,
};

/// Returns a short, stable, lower_snake_case name for diagnostics and logs.
std::string_view to_string(ErrorCode code) noexcept;

/// Streams the same name that to_string() returns.
inline std::ostream& operator<<(std::ostream& stream, ErrorCode code) {
    return stream << to_string(code);
}

/// A recoverable failure. Success is represented by ErrorCode::Ok and is the
/// default state, so an `if (error)` check reads naturally.
class Error {
  public:
    Error() = default;

    Error(ErrorCode code, std::string message) : code_(code), message_(std::move(message)) {}

    ErrorCode code() const noexcept { return code_; }
    const std::string& message() const noexcept { return message_; }

    /// "path_empty: Windows path must not be empty"
    std::string describe() const;

    explicit operator bool() const noexcept { return code_ != ErrorCode::Ok; }

  private:
    ErrorCode code_ = ErrorCode::Ok;
    std::string message_;
};

/// Either a value or the Error that prevented producing one.
///
/// The project targets C++20, so this stands in for std::expected. Accessing
/// value() on a failed Result is a precondition violation; callers must check
/// ok() first.
template <typename T> class Result {
  public:
    // Implicit on purpose so functions can `return value;`.
    Result(T value) : value_(std::move(value)) {}  // NOLINT(google-explicit-constructor)
    Result(Error error) : error_(std::move(error)) {}

    bool ok() const noexcept { return value_.has_value(); }
    explicit operator bool() const noexcept { return ok(); }

    const T& value() const { return *value_; }
    T& value() { return *value_; }

    const Error& error() const noexcept { return error_; }

    /// Returns the value, or `fallback` when the Result holds an error.
    /// Returns by value so a temporary fallback is never dangled.
    T value_or(T fallback) const { return value_ ? *value_ : std::move(fallback); }

  private:
    std::optional<T> value_;
    Error error_;
};

}  // namespace gtavi
