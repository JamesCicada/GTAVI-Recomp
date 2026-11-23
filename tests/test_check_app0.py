"""Exercise the app0 preflight with generated metadata and ELF headers."""

import json
from pathlib import Path
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_app0.py"


def executable(entry=0x400078, segment_end=121, kind=0xFE10):
    ident = b"\x7fELF\x02\x01\x01" + bytes(9)
    header = struct.pack("<16sHHIQQQIHHHHHH", ident, kind, 62, 1, entry, 64, 0, 0, 64, 56, 1, 0, 0, 0)
    load = struct.pack("<IIQQQQQQ", 1, 5, 0, 0x400000, 0, segment_end, segment_end, 4096)
    return header + load + b"\xc3"


class CheckApp0Tests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.app0 = Path(temp.name)
        (self.app0 / "sce_sys").mkdir()
        self.param = self.app0 / "sce_sys/param.json"
        self.param.write_text(json.dumps({"titleId": "PPSA99999", "contentVersion": "01.000.000"}), encoding="utf-8")
        self.eboot = self.app0 / "eboot.bin"
        self.eboot.write_bytes(executable())

    def probe(self, *args, status=0):
        result = subprocess.run([sys.executable, "-I", str(SCRIPT), str(self.app0), *args],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, status, result.stderr + result.stdout)
        return json.loads(result.stdout)

    def test_checks_both_inputs_and_preserves_them(self):
        before = (self.param.read_bytes(), self.eboot.read_bytes())
        report = self.probe("--title-id", "PPSA99999", "--content-version", "01.000.000")
        self.assertEqual(report["metadata"]["title_id"], "PPSA99999")
        self.assertEqual(report["executable"]["bytes"], len(before[1]))
        self.assertEqual(report["errors"], {})
        self.assertEqual((self.param.read_bytes(), self.eboot.read_bytes()), before)

    def test_metadata_is_reported_when_executable_is_missing(self):
        self.eboot.unlink()
        report = self.probe(status=2)
        self.assertEqual(report["metadata"]["content_version"], "01.000.000")
        self.assertIn("eboot.bin", report["errors"])

    def test_duplicate_title_fields_are_rejected(self):
        self.param.write_text('{"titleId":"PPSA99999","titleId":"PPSA99998","contentVersion":"01.000.000"}',
                              encoding="utf-8")
        report = self.probe(status=2)
        self.assertIn("duplicate metadata field", report["errors"]["sce_sys/param.json"])

    def test_wrong_expected_version_is_reported(self):
        report = self.probe("--content-version", "01.000.001", status=2)
        self.assertIn("expected 01.000.001", report["errors"]["sce_sys/param.json"])
        self.assertIsNotNone(report["executable"])

    def test_self_and_malformed_metadata_are_both_reported(self):
        self.eboot.write_bytes(b"\x54\x14\xf5\xee" + bytes(64))
        self.param.write_bytes(b"{")
        report = self.probe(status=2)
        self.assertIn("SELF container", report["errors"]["eboot.bin"])
        self.assertIn("sce_sys/param.json", report["errors"])

    def test_invalid_segments_and_entry_points_are_reported(self):
        for fixture, error in ((executable(segment_end=122), "invalid load segment"),
                               (executable(entry=0x500000), "entry point")):
            self.eboot.write_bytes(fixture)
            self.assertIn(error, self.probe(status=2)["errors"]["eboot.bin"])

    def test_reports_readable_and_missing_modules_without_an_eboot(self):
        self.eboot.unlink()
        (self.app0 / "sce_module").mkdir()
        module = executable(entry=0, kind=0xFE18)
        (self.app0 / "sce_module/present.prx").write_bytes(module)
        report = self.probe("--module", "present.prx", "--module", "missing.prx", status=2)
        self.assertEqual(report["modules"]["sce_module/present.prx"]["bytes"], len(module))
        self.assertIsNone(report["modules"]["sce_module/missing.prx"])
        self.assertEqual(set(report["errors"]), {"eboot.bin", "sce_module/missing.prx"})

    def test_rejects_executable_and_empty_module_inputs(self):
        (self.app0 / "sce_module").mkdir()
        (self.app0 / "sce_module/executable.prx").write_bytes(executable())
        (self.app0 / "sce_module/empty.prx").write_bytes(executable(entry=0, segment_end=0, kind=3))
        report = self.probe("--module", "executable.prx", "--module", "empty.prx", status=2)
        self.assertIn("expected an x86-64 ELF shared module", report["errors"]["sce_module/executable.prx"])
        self.assertIn("no file-backed load segment", report["errors"]["sce_module/empty.prx"])

    def test_module_option_requires_a_basename(self):
        for name in ("../outside.prx", r"..\outside.prx", "outside.bin"):
            with self.subTest(name=name):
                result = subprocess.run([sys.executable, "-I", str(SCRIPT), str(self.app0), "--module", name],
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 2)
                self.assertIn(".prx basename", result.stderr)


if __name__ == "__main__":
    unittest.main()
