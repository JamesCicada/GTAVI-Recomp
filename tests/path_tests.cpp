#include "gtavi/path.h"

#include <string>
#include <vector>

#include "test_framework.h"

using gtavi::DriveMap;
using gtavi::DriveMapping;
using gtavi::ErrorCode;
using gtavi::posix_to_windows;
using gtavi::windows_to_posix;

namespace {

std::string to_posix(const std::string& path) {
    const auto result = windows_to_posix(path, DriveMap::default_map());
    CHECK_TRUE(result.ok());
    return result.ok() ? result.value() : std::string{"<error>"};
}

std::string to_windows(const std::string& path) {
    const auto result = posix_to_windows(path, DriveMap::default_map());
    CHECK_TRUE(result.ok());
    return result.ok() ? result.value() : std::string{"<error>"};
}

ErrorCode to_posix_error(const std::string& path) {
    const auto result = windows_to_posix(path, DriveMap::default_map());
    CHECK_FALSE(result.ok());
    return result.error().code();
}

}  // namespace

// --- windows_to_posix: accepted forms ---------------------------------------

GTAVI_TEST(drive_root_maps_to_mount_point) {
    CHECK_EQ(to_posix("C:\\"), std::string{"/mnt/c"});
}

GTAVI_TEST(nested_path_preserves_components) {
    CHECK_EQ(to_posix("C:\\Games\\GTA VI\\data\\common.rpf"),
             std::string{"/mnt/c/Games/GTA VI/data/common.rpf"});
}

GTAVI_TEST(forward_slashes_are_accepted) {
    CHECK_EQ(to_posix("C:/Games/x"), std::string{"/mnt/c/Games/x"});
}

GTAVI_TEST(trailing_separator_is_dropped) {
    CHECK_EQ(to_posix("C:\\Games\\"), std::string{"/mnt/c/Games"});
}

GTAVI_TEST(repeated_separators_are_collapsed) {
    CHECK_EQ(to_posix("C:\\\\Games\\\\x"), std::string{"/mnt/c/Games/x"});
}

GTAVI_TEST(drive_letter_is_case_insensitive) {
    CHECK_EQ(to_posix("c:\\games"), std::string{"/mnt/c/games"});
}

GTAVI_TEST(relative_paths_keep_only_separator_changes) {
    CHECK_EQ(to_posix("data\\common.rpf"), std::string{"data/common.rpf"});
}

GTAVI_TEST(spaces_and_dots_are_preserved) {
    CHECK_EQ(to_posix("C:\\Program Files\\..\\GTA VI\\"),
             std::string{"/mnt/c/Program Files/../GTA VI"});
}

GTAVI_TEST(has_drive_designator_detects_prefix) {
    CHECK_TRUE(gtavi::has_drive_designator("C:\\x"));
    CHECK_TRUE(gtavi::has_drive_designator("z:"));
    CHECK_FALSE(gtavi::has_drive_designator("\\x"));
    CHECK_FALSE(gtavi::has_drive_designator("data"));
    CHECK_FALSE(gtavi::has_drive_designator("1:\\x"));
}

// --- windows_to_posix: rejected forms ---------------------------------------

GTAVI_TEST(empty_windows_path_is_rejected) {
    CHECK_EQ(to_posix_error(""), ErrorCode::PathEmpty);
}

GTAVI_TEST(nul_byte_in_windows_path_is_rejected) {
    const std::string path{"C:\\a\0b", 6};
    CHECK_EQ(to_posix_error(path), ErrorCode::PathInvalid);
}

GTAVI_TEST(unc_path_is_rejected) {
    CHECK_EQ(to_posix_error("\\\\server\\share\\x"), ErrorCode::PathUnsupportedForm);
}

GTAVI_TEST(device_path_is_rejected) {
    CHECK_EQ(to_posix_error("\\\\?\\C:\\x"), ErrorCode::PathUnsupportedForm);
}

GTAVI_TEST(root_relative_path_is_rejected) {
    CHECK_EQ(to_posix_error("\\Windows\\System32"), ErrorCode::PathUnsupportedForm);
}

GTAVI_TEST(bare_drive_is_rejected) {
    CHECK_EQ(to_posix_error("C:"), ErrorCode::PathUnsupportedForm);
}

GTAVI_TEST(drive_relative_path_is_rejected) {
    CHECK_EQ(to_posix_error("C:Games"), ErrorCode::PathUnsupportedForm);
}

GTAVI_TEST(invalid_drive_letter_is_rejected) {
    CHECK_EQ(to_posix_error("1:\\Games"), ErrorCode::PathInvalid);
}

GTAVI_TEST(unmapped_drive_is_rejected) {
    const DriveMap empty = DriveMap::with_mappings({});
    const auto result = windows_to_posix("Z:\\Games", empty);
    CHECK_FALSE(result.ok());
    CHECK_EQ(result.error().code(), ErrorCode::PathUnmappedDrive);
}

// --- custom drive maps ------------------------------------------------------

GTAVI_TEST(default_map_has_a_mount_for_every_drive_letter) {
    const auto map = DriveMap::default_map();
    CHECK_EQ(map.mappings().size(), std::size_t{26});
    for (char drive = 'A'; drive <= 'Z'; ++drive) {
        const auto mount = map.mount_point_for(drive);
        CHECK_TRUE(mount.ok());
        if (mount.ok()) {
            CHECK_EQ(mount.value(), std::string{"/mnt/"} + static_cast<char>('a' + drive - 'A'));
        }
    }
}

GTAVI_TEST(custom_mapping_is_used) {
    const DriveMap map = DriveMap::with_mappings({DriveMapping{'D', "/games"}});
    const auto result = windows_to_posix("D:\\GTA", map);
    CHECK_TRUE(result.ok());
    CHECK_EQ(result.value(), std::string{"/games/GTA"});
}

GTAVI_TEST(mount_point_trailing_separator_is_normalised) {
    const DriveMap map = DriveMap::with_mappings({DriveMapping{'D', "/games/"}});
    const auto result = windows_to_posix("D:\\GTA", map);
    CHECK_TRUE(result.ok());
    CHECK_EQ(result.value(), std::string{"/games/GTA"});
}

GTAVI_TEST(custom_mount_points_use_normalized_posix_separators) {
    const DriveMap map = DriveMap::with_mappings({DriveMapping{'D', "/mnt//archive/"}});
    const auto posix = windows_to_posix("D:\\app0", map);
    CHECK_TRUE(posix.ok());
    CHECK_EQ(posix.value(), std::string{"/mnt/archive/app0"});
    const auto windows = posix_to_windows("/mnt/archive/app0", map);
    CHECK_TRUE(windows.ok());
    CHECK_EQ(windows.value(), std::string{"D:\\app0"});
}

GTAVI_TEST(invalid_mapping_entries_are_dropped) {
    const DriveMap map = DriveMap::with_mappings({
        DriveMapping{'1', "/bad-drive"},
        DriveMapping{'E', "relative/mount"},
        DriveMapping{'F', "/ok"},
    });
    CHECK_EQ(map.mappings().size(), std::size_t{1});
}

GTAVI_TEST(overrides_placed_before_defaults_replace_them) {
    std::vector<DriveMapping> mappings{DriveMapping{'D', "/data"}};
    const DriveMap defaults = DriveMap::default_map();
    for (const auto& mapping : defaults.mappings()) {
        mappings.push_back(mapping);
    }
    const DriveMap map = DriveMap::with_mappings(std::move(mappings));
    CHECK_EQ(map.mappings().size(), std::size_t{26});
    const auto mount = map.mount_point_for('d');
    CHECK_TRUE(mount.ok());
    CHECK_EQ(mount.value(), std::string{"/data"});
    const auto other = map.mount_point_for('C');
    CHECK_TRUE(other.ok());
    CHECK_EQ(other.value(), std::string{"/mnt/c"});
}

GTAVI_TEST(drive_for_collapses_repeated_separators) {
    const DriveMap map = DriveMap::default_map();
    const auto drive = map.drive_for("/mnt//d///Games");
    CHECK_TRUE(drive.ok());
    CHECK_EQ(drive.value(), 'D');
    const auto root = map.drive_for("/mnt/d/");
    CHECK_TRUE(root.ok());
    CHECK_EQ(root.value(), 'D');
}

GTAVI_TEST(drive_for_rejects_literal_backslash) {
    const auto drive = DriveMap::default_map().drive_for("/mnt/d/game\\content");
    CHECK_FALSE(drive.ok());
    CHECK_EQ(drive.error().code(), ErrorCode::PathUnsupportedForm);
}

GTAVI_TEST(duplicate_drive_keeps_the_first_mapping_in_both_directions) {
    const DriveMap map = DriveMap::with_mappings({
        DriveMapping{'D', "/local/game"},
        DriveMapping{'d', "/archive"},
    });
    CHECK_EQ(map.mappings().size(), std::size_t{1});
    const auto windows = posix_to_windows("/local/game/app0", map);
    CHECK_TRUE(windows.ok());
    CHECK_EQ(windows.value(), std::string{"D:\\app0"});
    const auto posix = windows_to_posix("d:\\app0", map);
    CHECK_TRUE(posix.ok());
    CHECK_EQ(posix.value(), std::string{"/local/game/app0"});
    const auto discarded = posix_to_windows("/archive/app0", map);
    CHECK_FALSE(discarded.ok());
    CHECK_EQ(discarded.error().code(), ErrorCode::PathUnmappedDrive);
}

GTAVI_TEST(root_mount_point_is_supported) {
    const DriveMap map = DriveMap::with_mappings({DriveMapping{'R', "/"}});
    const auto result = windows_to_posix("R:\\Games", map);
    CHECK_TRUE(result.ok());
    CHECK_EQ(result.value(), std::string{"/Games"});
}

// --- posix_to_windows -------------------------------------------------------

GTAVI_TEST(mount_point_becomes_drive_root) {
    CHECK_EQ(to_windows("/mnt/c"), std::string{"C:\\"});
}

GTAVI_TEST(posix_root_with_trailing_separator_becomes_drive_root) {
    CHECK_EQ(to_windows("/mnt/c/"), std::string{"C:\\"});
}

GTAVI_TEST(repeated_posix_separators_are_collapsed_before_mount_lookup) {
    CHECK_EQ(to_windows("/mnt//d/Games///Title/"), std::string{"D:\\Games\\Title"});
    CHECK_EQ(to_windows("/mnt//d/"), std::string{"D:\\"});
}

GTAVI_TEST(literal_backslash_in_posix_name_is_rejected) {
    const auto result = posix_to_windows("/mnt/d/game\\content/file", DriveMap::default_map());
    CHECK_FALSE(result.ok());
    CHECK_EQ(result.error().code(), ErrorCode::PathUnsupportedForm);
}

GTAVI_TEST(nested_posix_path_becomes_windows_path) {
    CHECK_EQ(to_windows("/mnt/c/Games/GTA VI/data"), std::string{"C:\\Games\\GTA VI\\data"});
}

GTAVI_TEST(empty_posix_path_is_rejected) {
    const auto result = posix_to_windows("", DriveMap::default_map());
    CHECK_FALSE(result.ok());
    CHECK_EQ(result.error().code(), ErrorCode::PathEmpty);
}

GTAVI_TEST(relative_posix_path_is_rejected) {
    const auto result = posix_to_windows("mnt/c/Games", DriveMap::default_map());
    CHECK_FALSE(result.ok());
    CHECK_EQ(result.error().code(), ErrorCode::PathInvalid);
}

GTAVI_TEST(unmapped_posix_path_is_rejected) {
    const auto result = posix_to_windows("/home/user", DriveMap::default_map());
    CHECK_FALSE(result.ok());
    CHECK_EQ(result.error().code(), ErrorCode::PathUnmappedDrive);
}

GTAVI_TEST(prefix_match_requires_path_boundary) {
    const auto result = posix_to_windows("/mnt/cdrom/x", DriveMap::default_map());
    CHECK_FALSE(result.ok());
    CHECK_EQ(result.error().code(), ErrorCode::PathUnmappedDrive);
}

GTAVI_TEST(longest_mount_point_wins) {
    const DriveMap map =
        DriveMap::with_mappings({DriveMapping{'C', "/mnt/c"}, DriveMapping{'D', "/mnt/c/games"}});
    const auto result = posix_to_windows("/mnt/c/games/GTA", map);
    CHECK_TRUE(result.ok());
    CHECK_EQ(result.value(), std::string{"D:\\GTA"});
}

GTAVI_TEST(round_trip_preserves_normalised_path) {
    const std::string original = "C:\\Games\\GTA VI\\data\\common.rpf";
    const std::string posix = to_posix(original);
    CHECK_EQ(to_windows(posix), original);
}
