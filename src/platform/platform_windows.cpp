// Windows implementation of the platform queries.
//
// The version is obtained from ntdll's RtlGetVersion. GetVersionEx is avoided
// because it reports a compatibility-shimmed value unless the executable ships
// a version manifest.

#include "gtavi/platform.h"

#include <string>

#include "gtavi/error.h"

#if !defined(WIN32_LEAN_AND_MEAN)
#define WIN32_LEAN_AND_MEAN
#endif
#if !defined(NOMINMAX)
#define NOMINMAX
#endif

#include <windows.h>
#include <winternl.h>

#include <cstring>

namespace gtavi::detail {
namespace {

using RtlGetVersionFn = LONG(WINAPI*)(PRTL_OSVERSIONINFOW);

RtlGetVersionFn resolve_rtl_get_version() noexcept {
    const HMODULE ntdll = ::GetModuleHandleW(L"ntdll.dll");
    if (ntdll == nullptr) {
        return nullptr;
    }

    const FARPROC proc = ::GetProcAddress(ntdll, "RtlGetVersion");
    if (proc == nullptr) {
        return nullptr;
    }

    // Converting FARPROC (an object pointer type) to a function pointer is not
    // strictly legal C++, so copy the representation instead of casting.
    RtlGetVersionFn fn = nullptr;
    static_assert(sizeof(fn) == sizeof(proc), "function and data pointers must have equal size");
    std::memcpy(&fn, &proc, sizeof(fn));
    return fn;
}

}  // namespace

Result<std::string> query_os_version() {
    const RtlGetVersionFn get_version = resolve_rtl_get_version();
    if (get_version == nullptr) {
        return Error{ErrorCode::Internal, "RtlGetVersion is not available from ntdll.dll"};
    }

    RTL_OSVERSIONINFOW info{};
    info.dwOSVersionInfoSize = static_cast<DWORD>(sizeof(info));

    const LONG status = get_version(&info);
    if (status != 0) {
        return Error{ErrorCode::Internal, "RtlGetVersion failed with status " + std::to_string(status)};
    }

    return std::to_string(info.dwMajorVersion) + "." + std::to_string(info.dwMinorVersion) + "." +
           std::to_string(info.dwBuildNumber);
}

}  // namespace gtavi::detail
