#pragma once

#include <string>
#include <string_view>
#include <vector>

#include "gtavi/error.h"

namespace gtavi {

/// Associates a Windows drive letter with a native mount point.
struct DriveMapping {
    /// Uppercase ASCII letter in 'A'..'Z'.
    char drive = '\0';
    /// Absolute POSIX path without a trailing separator, for example "/mnt/c".
    std::string mount_point;
};

/// Bidirectional mapping between Windows drive letters and POSIX mount points.
///
/// These utilities translate **host** paths — the PC the layer runs on — and are
/// used when the host filesystem differs from what a subsystem expects. Guest
/// mount points such as `/app0` are a separate subsystem and are not handled
/// here; see ADR 0002.
///
/// Lookup is case-insensitive for drive letters. When several mount points
/// could match a POSIX path, the longest matching prefix wins.
class DriveMap {
  public:
    /// Maps every drive letter to /mnt/<lowercase letter>, matching common WSL
    /// and Wine layouts. Callers may replace individual entries.
    static DriveMap default_map();

    /// Builds a map from explicit mappings. Drive letters are uppercased and
    /// trailing separators are stripped from mount points. Entries with an
    /// invalid drive letter or a non-absolute mount point are dropped.
    static DriveMap with_mappings(std::vector<DriveMapping> mappings);

    /// Returns the mount point for `drive`, or ErrorCode::PathUnmappedDrive.
    Result<std::string> mount_point_for(char drive) const;

    /// Returns the drive whose mount point is the longest prefix of
    /// `posix_path` at a path boundary, or ErrorCode::PathUnmappedDrive.
    Result<char> drive_for(std::string_view posix_path) const;

    const std::vector<DriveMapping>& mappings() const noexcept { return mappings_; }

  private:
    std::vector<DriveMapping> mappings_;
};

/// True if `windows_path` starts with a drive designator such as "C:".
bool has_drive_designator(std::string_view windows_path) noexcept;

/// Converts a Windows path to a POSIX path.
///
///   "C:\\Games\\GTA VI\\data" -> "/mnt/c/Games/GTA VI/data"
///   "C:\\"                    -> "/mnt/c"
///   "data\\common.rpf"        -> "data/common.rpf"
///
/// Separators are normalised, repeated separators are collapsed, and a trailing
/// separator is dropped. "." and ".." components are preserved, not resolved.
/// The output never ends with a separator except for the POSIX root "/".
///
/// Rejected forms: empty paths, embedded NUL bytes, UNC and device paths
/// ("\\\\server\\share", "\\\\?\\C:"), and drive-relative paths ("C:Games").
Result<std::string> windows_to_posix(std::string_view windows_path, const DriveMap& map);

/// Converts a POSIX path to a Windows path using `map`.
///
///   "/mnt/c/Games" -> "C:\\Games"
///   "/mnt/c"       -> "C:\\"
///
/// The input must be absolute and must fall under a configured mount point.
Result<std::string> posix_to_windows(std::string_view posix_path, const DriveMap& map);

}  // namespace gtavi
