#include "gtavi/path.h"

#include <cstddef>
#include <utility>

namespace gtavi {
namespace {

bool is_separator(char c) noexcept {
    return c == '\\' || c == '/';
}

char to_upper_ascii(char c) noexcept {
    return (c >= 'a' && c <= 'z') ? static_cast<char>(c - 'a' + 'A') : c;
}

bool is_drive_letter(char c) noexcept {
    const char upper = to_upper_ascii(c);
    return upper >= 'A' && upper <= 'Z';
}

bool contains_nul(std::string_view text) noexcept {
    return text.find('\0') != std::string_view::npos;
}

std::string quoted(std::string_view text) {
    std::string out;
    out.reserve(text.size() + 2);
    out.push_back('\'');
    out += text;
    out.push_back('\'');
    return out;
}

/// Converts separators to '/', collapses runs of separators, and drops a
/// trailing separator. A leading separator is preserved.
std::string normalize_separators(std::string_view path) {
    std::string out;
    out.reserve(path.size());
    bool previous_was_separator = false;
    for (const char c : path) {
        if (is_separator(c)) {
            if (!previous_was_separator) {
                out.push_back('/');
                previous_was_separator = true;
            }
        } else {
            out.push_back(c);
            previous_was_separator = false;
        }
    }
    if (out.size() > 1 && out.back() == '/') {
        out.pop_back();
    }
    return out;
}

}  // namespace

bool has_drive_designator(std::string_view windows_path) noexcept {
    return windows_path.size() >= 2 && windows_path[1] == ':' && is_drive_letter(windows_path[0]);
}

DriveMap DriveMap::default_map() {
    std::vector<DriveMapping> mappings;
    mappings.reserve(26);
    for (char letter = 'A'; letter <= 'Z'; ++letter) {
        std::string mount_point = "/mnt/";
        mount_point.push_back(static_cast<char>(letter - 'A' + 'a'));
        mappings.push_back(DriveMapping{letter, std::move(mount_point)});
    }
    return with_mappings(std::move(mappings));
}

DriveMap DriveMap::with_mappings(std::vector<DriveMapping> mappings) {
    DriveMap map;
    for (auto& mapping : mappings) {
        if (!is_drive_letter(mapping.drive)) {
            continue;
        }
        if (mapping.mount_point.empty() || mapping.mount_point.front() != '/') {
            continue;
        }
        mapping.drive = to_upper_ascii(mapping.drive);
        while (mapping.mount_point.size() > 1 && mapping.mount_point.back() == '/') {
            mapping.mount_point.pop_back();
        }
        map.mappings_.push_back(std::move(mapping));
    }
    return map;
}

Result<std::string> DriveMap::mount_point_for(char drive) const {
    if (!is_drive_letter(drive)) {
        return Error{ErrorCode::PathInvalid, "invalid drive letter"};
    }

    const char wanted = to_upper_ascii(drive);
    for (const auto& mapping : mappings_) {
        if (mapping.drive == wanted) {
            return mapping.mount_point;
        }
    }

    std::string label(1, wanted);
    return Error{ErrorCode::PathUnmappedDrive,
                 "no mount point configured for drive '" + label + "'"};
}

Result<char> DriveMap::drive_for(std::string_view posix_path) const {
    if (posix_path.empty() || posix_path.front() != '/') {
        return Error{ErrorCode::PathInvalid, "POSIX path must be absolute"};
    }

    const DriveMapping* best = nullptr;
    for (const auto& mapping : mappings_) {
        if (posix_path.size() < mapping.mount_point.size()) {
            continue;
        }
        if (posix_path.compare(0, mapping.mount_point.size(), mapping.mount_point) != 0) {
            continue;
        }

        const bool at_boundary =
            mapping.mount_point == "/" || posix_path.size() == mapping.mount_point.size() ||
            posix_path[mapping.mount_point.size()] == '/';
        if (!at_boundary) {
            continue;
        }

        if (best == nullptr || mapping.mount_point.size() > best->mount_point.size()) {
            best = &mapping;
        }
    }

    if (best == nullptr) {
        return Error{ErrorCode::PathUnmappedDrive, "no mount point matches " + quoted(posix_path)};
    }
    return best->drive;
}

Result<std::string> windows_to_posix(std::string_view windows_path, const DriveMap& map) {
    if (windows_path.empty()) {
        return Error{ErrorCode::PathEmpty, "Windows path must not be empty"};
    }
    if (contains_nul(windows_path)) {
        return Error{ErrorCode::PathInvalid, "Windows path must not contain a NUL byte"};
    }
    if (windows_path.size() >= 2 && is_separator(windows_path[0]) && is_separator(windows_path[1])) {
        return Error{ErrorCode::PathUnsupportedForm,
                     "UNC and device paths are not supported: " + quoted(windows_path)};
    }
    if (is_separator(windows_path.front())) {
        return Error{ErrorCode::PathUnsupportedForm,
                     "root-relative paths are not supported: " + quoted(windows_path)};
    }

    if (windows_path.size() >= 2 && windows_path[1] == ':') {
        if (!is_drive_letter(windows_path[0])) {
            return Error{ErrorCode::PathInvalid, "invalid drive letter in " + quoted(windows_path)};
        }

        const std::string_view remainder = windows_path.substr(2);
        if (remainder.empty() || !is_separator(remainder.front())) {
            return Error{ErrorCode::PathUnsupportedForm,
                         "drive-relative paths are not supported: " + quoted(windows_path)};
        }

        auto mount_point = map.mount_point_for(windows_path[0]);
        if (!mount_point) {
            return mount_point.error();
        }

        std::string out = mount_point.value();
        while (!out.empty() && out.back() == '/') {
            out.pop_back();
        }
        if (out.empty()) {
            out = "/";
        }

        const std::string normalized = normalize_separators(remainder);
        if (normalized != "/") {
            if (out == "/") {
                out = normalized;
            } else {
                out += normalized;
            }
        }
        return out;
    }

    return normalize_separators(windows_path);
}

Result<std::string> posix_to_windows(std::string_view posix_path, const DriveMap& map) {
    if (posix_path.empty()) {
        return Error{ErrorCode::PathEmpty, "POSIX path must not be empty"};
    }
    if (contains_nul(posix_path)) {
        return Error{ErrorCode::PathInvalid, "POSIX path must not contain a NUL byte"};
    }
    if (posix_path.front() != '/') {
        return Error{ErrorCode::PathInvalid, "POSIX path must be absolute: " + quoted(posix_path)};
    }

    auto drive = map.drive_for(posix_path);
    if (!drive) {
        return drive.error();
    }

    auto mount_point = map.mount_point_for(drive.value());
    if (!mount_point) {
        return mount_point.error();
    }

    const std::string& mount = mount_point.value();
    const std::string_view remainder = posix_path.substr(mount.size());

    std::string out;
    out.reserve(remainder.size() + 2);
    out.push_back(drive.value());
    out.push_back(':');

    if (remainder.empty() || remainder == "/") {
        out += "\\";
        return out;
    }

    if (mount == "/") {
        out += "\\";
    }
    for (const char c : remainder) {
        out.push_back(c == '/' ? '\\' : c);
    }
    return out;
}

}  // namespace gtavi
