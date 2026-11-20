// Linux implementation of the platform queries.

#include "gtavi/platform.h"

#include <sys/utsname.h>

#include <string>

#include "gtavi/error.h"

namespace gtavi::detail {

Result<std::string> query_os_version() {
    utsname info{};
    if (::uname(&info) != 0) {
        return Error{ErrorCode::Internal, "uname() failed"};
    }
    // The kernel release is the most useful identifier for compatibility
    // reports; the distribution is recorded separately once we need it.
    return std::string{info.release};
}

}  // namespace gtavi::detail
