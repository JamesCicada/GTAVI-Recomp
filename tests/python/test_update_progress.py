#!/usr/bin/env python3
"""Tests for scripts/update_progress.py.

The progress report is what the project shows the world, and CI fails when it
is stale. Nothing tested the generator itself, so a parsing or rendering
regression would change the published numbers without any error. These tests
cover the pure parts of the script (TODO.md parsing, percent formatting, the
README splice, SVG rendering) and the --site builder's destructive-target
guards.

Run with: python3 -m unittest discover -s tests/python -v
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "update_progress", REPO / "scripts" / "update_progress.py"
)
assert SPEC and SPEC.loader
progress = importlib.util.module_from_spec(SPEC)
# Dataclasses resolve their annotations through sys.modules, so the module has
# to be registered before it is executed.
sys.modules[SPEC.name] = progress
SPEC.loader.exec_module(progress)


def parse(text: str) -> list:
    return progress.parse_todo(text)


class TestMeasureAnyPS5(unittest.TestCase):
    def test_only_committed_tool_and_sources_are_measured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            def git(*args):
                return subprocess.check_output(["git", "-C", tmp, *args], text=True).strip()

            git("init", "--quiet")
            (repo / "tools").mkdir()
            tool = repo / "tools/progress.py"
            tool.write_text(
                "import json\nfrom pathlib import Path\n"
                "print(json.dumps({p.name: p.read_text() for p in Path('.').glob('*.txt')}))\n",
                encoding="utf-8",
            )
            data = repo / "input.txt"
            data.write_text("committed", encoding="utf-8")
            git("add", ".")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                "-c", "commit.gpgSign=false", "commit", "--quiet", "-m", "fixture")
            commit = git("rev-parse", "HEAD")
            data.write_text("staged", encoding="utf-8")
            git("add", "input.txt")
            tool.write_text("raise AssertionError('ran the working copy')", encoding="utf-8")
            (repo / "extra.txt").write_text("untracked", encoding="utf-8")
            before = git("status", "--porcelain")
            with mock.patch.object(progress, "ANYPS5", repo):
                self.assertEqual(progress.measure_anyps5(commit), {"input.txt": "committed"})
            self.assertEqual(git("status", "--porcelain"), before)
            self.assertEqual(git("show", ":input.txt"), "staged")


class TestParseTodo(unittest.TestCase):
    def test_counts_done_open_and_blocked(self) -> None:
        phases = parse(
            "## Phase 1: Research\n"
            "- [x] done\n"
            "- [ ] open\n"
            "- [ ] blocked *(needs game files)*\n"
        )
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0].done, 1)
        self.assertEqual(phases[0].open, 1)
        self.assertEqual(phases[0].blocked, 1)
        self.assertEqual(phases[0].total, 3)

    def test_checked_item_with_blocked_marker_is_done(self) -> None:
        phases = parse(
            "## Phase 1: Research\n"
            "- [x] finished anyway *(needs game files)*\n"
        )
        self.assertEqual(phases[0].done, 1)
        self.assertEqual(phases[0].blocked, 0)

    def test_capital_x_counts_as_done(self) -> None:
        phases = parse("## Phase 1: Research\n- [X] done\n")
        self.assertEqual(phases[0].done, 1)

    def test_marker_in_wrapped_continuation_counts_as_blocked(self) -> None:
        phases = parse(
            "## Phase 1: Research\n"
            "- [ ] an item whose text wraps onto\n"
            "      needs game files before it can start\n"
        )
        self.assertEqual(phases[0].blocked, 1)
        self.assertEqual(phases[0].open, 0)
        self.assertEqual(phases[0].total, 1)

    def test_multiple_phases_keep_their_numbers_and_titles(self) -> None:
        phases = parse(
            "## Phase 2: Architecture\n"
            "- [x] a\n"
            "## Phase 3: Environment\n"
            "- [ ] b\n"
            "- [x] c\n"
        )
        self.assertEqual([p.number for p in phases], [2, 3])
        self.assertEqual([p.title for p in phases], ["Architecture", "Environment"])
        self.assertEqual([p.done for p in phases], [1, 1])
        self.assertEqual([p.open for p in phases], [0, 1])

    def test_items_outside_a_phase_are_ignored(self) -> None:
        phases = parse(
            "## Phase 1: Research\n"
            "- [x] counted\n"
            "## Development Principles\n"
            "- [ ] not counted\n"
        )
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0].total, 1)

    def test_missing_phase_heading_is_an_error(self) -> None:
        with self.assertRaises(SystemExit):
            parse("- [x] item without a phase\n")

    def test_real_todo_parses_into_numbered_phases(self) -> None:
        phases = parse(progress.TODO.read_text(encoding="utf-8"))
        numbers = [p.number for p in phases]
        self.assertTrue(numbers)
        self.assertEqual(numbers, sorted(set(numbers)))
        self.assertTrue(all(p.total > 0 for p in phases))


class TestFormatting(unittest.TestCase):
    def test_percent_of_empty_total_is_zero(self) -> None:
        self.assertEqual(progress.percent(0, 0), 0)
        self.assertEqual(progress.percent(5, 0), 0)

    def test_percent_rounds_to_nearest_integer(self) -> None:
        self.assertEqual(progress.percent(1, 3), 33)
        self.assertEqual(progress.percent(2, 3), 67)
        self.assertEqual(progress.percent(138, 138), 100)

    def test_number_uses_thousands_separators(self) -> None:
        self.assertEqual(progress.number(1234), "1,234")
        self.assertEqual(progress.number(7), "7")


class TestSvg(unittest.TestCase):
    def test_bar_keeps_a_tiny_done_count_visible(self) -> None:
        bar = progress.svg_bar(10, done=1, total=1000)
        self.assertIn('width="3.0"', bar)

    def test_bar_never_shows_unfinished_work_as_full(self) -> None:
        bar = progress.svg_bar(10, done=999, total=1000)
        self.assertIn('width="337.0"', bar)
        self.assertNotIn('width="340.0"', bar)

    def test_bar_with_zero_total_does_not_divide_by_zero(self) -> None:
        bar = progress.svg_bar(10, done=0, total=0)
        self.assertIn("<clipPath", bar)

    def test_chart_escapes_labels_and_title(self) -> None:
        rows = [progress.ChartRow("<b>label</b>", 1, 2)]
        svg = progress.svg_chart("<title>", rows, "light")
        self.assertNotIn("<b>label</b>", svg)
        self.assertIn("&lt;b&gt;label&lt;/b&gt;", svg)
        self.assertIn("&lt;title&gt;", svg)

    def test_chart_renders_percentage_and_counts(self) -> None:
        rows = [progress.ChartRow("Row", 3, 4)]
        svg = progress.svg_chart("title", rows, "dark")
        self.assertIn("75%", svg)
        self.assertIn("3 / 4", svg)


class TestSplice(unittest.TestCase):
    def test_replaces_only_the_marked_block(self) -> None:
        readme = f"before\n{progress.START}\nold\n{progress.END}\nafter\n"
        result = progress.splice(readme, f"{progress.START}\nnew\n{progress.END}")
        self.assertTrue(result.startswith("before\n"))
        self.assertTrue(result.endswith("\nafter\n"))
        self.assertIn("new", result)
        self.assertNotIn("old", result)

    def test_missing_marker_is_an_error(self) -> None:
        with self.assertRaises(SystemExit):
            progress.splice(f"no markers here\n", "block")

    def test_end_before_start_is_an_error(self) -> None:
        readme = f"{progress.END}\n{progress.START}\n"
        with self.assertRaises(SystemExit):
            progress.splice(readme, "block")


def sample_snapshot() -> dict:
    return {
        "commit": "15826135019b8c7de27f42661a850a1dd9750932",
        "source": "https://github.com/boykopovar/AnyPS5/tree/15826135019b",
        "libraries": {"done": 17999, "total": 39306},
        "library_count": 413,
        "shaders": {
            "rdna2": {"isa": "RDNA 2", "total": 1460, "decoded": 1460, "translated": 1460},
            "gfx1013": {"isa": "gfx1013", "total": 1560, "decoded": 1484, "translated": 1484},
            "unsupported_throws": 127,
        },
        "core_libraries": [
            {"name": "libScePad", "role": "Controller", "done": 56, "total": 222}
        ],
    }


class TestRenderReadme(unittest.TestCase):
    def test_block_is_delimited_and_states_the_blocker(self) -> None:
        phases = parse(
            "## Phase 1: Research\n- [x] done\n- [ ] blocked *(needs game files)*\n"
        )
        block = progress.render_readme(phases, sample_snapshot())
        self.assertTrue(block.startswith(progress.START))
        self.assertTrue(block.endswith(progress.END))
        self.assertIn("Game research is blocked", block)
        self.assertIn("1 of 2 roadmap tasks", block)
        self.assertIn("1582613", block)
        self.assertIn("progress/anyps5-light.svg", block)


class TestBuildSite(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.data = {"roadmap": {"done": 1}, "anyps5": {}}

    def test_builds_into_a_new_directory(self) -> None:
        target = self.tmp / "out"
        progress.build_site(target, self.data)
        self.assertTrue((target / "index.html").is_file())
        report = (target / "progress.json").read_bytes()
        self.assertNotIn(b"\r\n", report)
        self.assertEqual(json.loads(report.decode("utf-8")), self.data)

    def test_rebuilds_a_previous_build(self) -> None:
        target = self.tmp / "out"
        progress.build_site(target, self.data)
        (target / "stale.txt").write_text("old", encoding="utf-8")
        progress.build_site(target, self.data)
        self.assertFalse((target / "stale.txt").exists())

    def test_refuses_the_repository_root(self) -> None:
        with self.assertRaises(SystemExit):
            progress.build_site(progress.ROOT, self.data)
        self.assertTrue(progress.TODO.is_file())

    def test_refuses_an_ancestor_of_the_repository(self) -> None:
        with self.assertRaises(SystemExit):
            progress.build_site(progress.ROOT.parent, self.data)

    def test_refuses_the_site_source(self) -> None:
        with self.assertRaises(SystemExit):
            progress.build_site(progress.SITE_SOURCE, self.data)
        self.assertTrue((progress.SITE_SOURCE / "index.html").is_file())

    def test_refuses_a_directory_inside_the_site_source(self) -> None:
        with self.assertRaises(SystemExit):
            progress.build_site(progress.SITE_SOURCE / "out", self.data)

    def test_refuses_an_unrelated_non_empty_directory(self) -> None:
        target = self.tmp / "notes"
        target.mkdir()
        (target / "keep.txt").write_text("do not delete", encoding="utf-8")
        with self.assertRaises(SystemExit):
            progress.build_site(target, self.data)
        self.assertTrue((target / "keep.txt").is_file())

    def test_force_allows_an_unrelated_directory(self) -> None:
        target = self.tmp / "notes"
        target.mkdir()
        (target / "keep.txt").write_text("replaced", encoding="utf-8")
        progress.build_site(target, self.data, force=True)
        self.assertFalse((target / "keep.txt").exists())
        self.assertTrue((target / "index.html").is_file())

    def test_refuses_a_file_target(self) -> None:
        target = self.tmp / "file"
        target.write_text("x", encoding="utf-8")
        with self.assertRaises(SystemExit):
            progress.build_site(target, self.data)
        self.assertTrue(target.is_file())


if __name__ == "__main__":
    unittest.main()
