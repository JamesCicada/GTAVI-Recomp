// Fallback for platforms without a dedicated implementation.
//
// The core library still builds so that portable code can be compiled and
// tested, but every platform query reports ErrorCode::UnsupportedPlatform.

#include "gtavi/platform.h"

#include <string>

#include "gtavi/error.h"

namespace gtavi::detail {

Result<std::string> query_os_version() {
    return Error{ErrorCode::UnsupportedPlatform, "the host platform is not supported"};
}

}  // namespace gtavi::detail
