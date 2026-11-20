#include "gtavi/error.h"

namespace gtavi {

std::string_view to_string(ErrorCode code) noexcept {
    switch (code) {
        case ErrorCode::Ok:
            return "ok";
        case ErrorCode::InvalidArgument:
            return "invalid_argument";
        case ErrorCode::PathEmpty:
            return "path_empty";
        case ErrorCode::PathInvalid:
            return "path_invalid";
        case ErrorCode::PathUnsupportedForm:
            return "path_unsupported_form";
        case ErrorCode::PathUnmappedDrive:
            return "path_unmapped_drive";
        case ErrorCode::UnsupportedPlatform:
            return "unsupported_platform";
        case ErrorCode::Internal:
            return "internal";
    }
    return "unknown";
}

std::string Error::describe() const {
    std::string out{to_string(code_)};
    if (!message_.empty()) {
        out += ": ";
        out += message_;
    }
    return out;
}

}  // namespace gtavi
