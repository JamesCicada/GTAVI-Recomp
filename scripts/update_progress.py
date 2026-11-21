#!/usr/bin/env python3
"""Generate the project's progress report: the README section and the Pages data.

Usage:
    python3 scripts/update_progress.py                  # rewrite README.md in place
    python3 scripts/update_progress.py --check          # exit 1 if anything is stale
    python3 scripts/update_progress.py --site _site     # also build the Pages site
    python3 scripts/update_progress.py --refresh-anyps5 # re-measure the AnyPS5 submodule

Two sources feed the report:

* TODO.md. Each "## Phase N: Title" heading is one row. A "- [x]" item is done,
  a "- [ ]" item is open, and an open item whose text contains BLOCKED_MARKER
  is counted as blocked until the game files can be researched.
* progress/anyps5.json, a snapshot of AnyPS5's own measurements (shader
  recompiler and system libraries) taken at the pinned submodule commit by
  AnyPS5's tools/progress.py. --refresh-anyps5 rewrites it and needs the
  submodule checked out; nothing else does, so CI can run without it.

Standard library only, so it runs anywhere Python 3.8+ does.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODO = ROOT / "TODO.md"
README = ROOT / "README.md"
SITE_SOURCE = ROOT / "site"
SNAPSHOT = ROOT / "progress" / "anyps5.json"
ANYPS5 = ROOT / "third_party" / "AnyPS5"
ANYPS5_PATH = "third_party/AnyPS5"
ANYPS5_URL = "https://github.com/boykopovar/AnyPS5"
SITE_URL = "https://jamescicada.github.io/GTAVI-Recomp/"

BLOCKED_MARKER = "needs game files"
START = "<!-- progress:start -->"
END = "<!-- progress:end -->"
BAR_WIDTH = 20

# System libraries that nearly every PS5 title imports. GTA VI's real import
# list is unknown until its files can be researched, so this is the expected
# core, not a measured one. Order is the order shown.
CORE_LIBRARIES = (
    ("libScePad", "Controller"),
    ("libSceVideoOut", "Display output"),
    ("libSceAgc", "Graphics (AGC)"),
    ("libSceAgcDriver", "Graphics driver"),
    ("libSceAudioOut", "Audio output"),
    ("libkernel", "Kernel"),
    ("libSceLibcInternal", "C runtime"),
    ("libSceSysmodule", "Module loading"),
    ("libSceSystemService", "System service"),
    ("libSceUserService", "User service"),
    ("libSceSaveData", "Save data"),
    ("libSceAppContent", "App content"),
    ("libSceNpTrophy2", "Trophies"),
)

PHASE_RE = re.compile(r"^## Phase (\d+): (.+?)\s*$")
ITEM_RE = re.compile(r"^- \[([ xX])\] ")


# --------------------------------------------------------------------------
# TODO.md


@dataclass
class Phase:
    number: int
    title: str
    done: int = 0
    open: int = 0
    blocked: int = 0

    @property
    def total(self) -> int:
        return self.done + self.open + self.blocked


def parse_todo(text: str) -> list[Phase]:
    phases: list[Phase] = []
    current: Phase | None = None
    # (phase, checked, text) for the item being read; items may wrap lines.
    item: tuple[Phase, bool, str] | None = None

    def finish_item() -> None:
        nonlocal item
        if item is None:
            return
        phase, checked, body = item
        if checked:
            phase.done += 1
        elif BLOCKED_MARKER in body:
            phase.blocked += 1
        else:
            phase.open += 1
        item = None

    for line in text.splitlines():
        heading = PHASE_RE.match(line)
        if heading:
            finish_item()
            current = Phase(int(heading.group(1)), heading.group(2))
            phases.append(current)
            continue
        if line.startswith("## "):
            # A non-phase section (for example "Development Principles").
            finish_item()
            current = None
            continue
        match = ITEM_RE.match(line)
        if match and current is not None:
            finish_item()
            item = (current, match.group(1) != " ", line)
            continue
        if item is not None:
            if line.strip() and line.startswith(" "):
                phase, checked, body = item
                item = (phase, checked, body + " " + line.strip())
            else:
                finish_item()
    finish_item()

    if not phases:
        raise SystemExit("update_progress: no '## Phase N:' headings found in TODO.md")
    return phases


# --------------------------------------------------------------------------
# AnyPS5 snapshot


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def pinned_anyps5_commit() -> str | None:
    """The submodule commit recorded in the index, without needing a checkout."""
    try:
        entry = git("ls-files", "--stage", "--", ANYPS5_PATH)
    except (OSError, subprocess.CalledProcessError):
        return None
    # "160000 <sha> 0\tthird_party/AnyPS5"
    parts = entry.split()
    return parts[1] if len(parts) >= 2 and parts[0] == "160000" else None


def counts(done: int, total: int) -> dict:
    return {"done": done, "total": total}


def refresh_snapshot() -> None:
    tool = ANYPS5 / "tools" / "progress.py"
    if not tool.is_file():
        raise SystemExit(
            "update_progress: AnyPS5 is not checked out. "
            "Run: git submodule update --init third_party/AnyPS5"
        )
    commit = git("-C", ANYPS5_PATH, "rev-parse", "HEAD")
    pinned = pinned_anyps5_commit()
    if pinned and pinned != commit:
        raise SystemExit(
            f"update_progress: the AnyPS5 checkout is at {commit[:7]} but the repository "
            f"pins {pinned[:7]}. Stage the submodule change or check out the pinned commit."
        )

    print("Measuring AnyPS5 with its tools/progress.py (this takes a few seconds)...")
    result = subprocess.run(
        [sys.executable, "-I", str(tool), "--json", "--require-shader-source"],
        cwd=ANYPS5,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    data = json.loads(result.stdout)

    groups = {g["name"]: g for g in data["libraries"]["groups"]}
    core = []
    for name, role in CORE_LIBRARIES:
        group = groups.get(name)
        if group is None:
            raise SystemExit(f"update_progress: AnyPS5 has no library named {name}")
        core.append(
            {"name": name, "role": role, **counts(group["done"], group["done"] + group["todo"])}
        )

    source = data["shader_source"]
    gfx1013 = source["profiles"]["gfx1013"]
    snapshot = {
        "_comment": "Generated by scripts/update_progress.py --refresh-anyps5. Do not edit by hand.",
        "commit": commit,
        "source": f"{ANYPS5_URL}/tree/{commit}",
        "libraries": counts(data["libraries"]["done"], data["libraries"]["total"]),
        "library_count": len(groups),
        "shaders": {
            "rdna2": {
                "isa": source["isa"],
                "total": source["instructions"]["total"],
                "decoded": source["instructions"]["decoded"],
                "translated": source["instructions"]["translated"],
            },
            "gfx1013": {
                "isa": gfx1013["isa"],
                "total": gfx1013["instructions"]["total"],
                "decoded": gfx1013["instructions"]["decoded"],
                "translated": gfx1013["instructions"]["translated"],
            },
            "unsupported_throws": source["unsupported_throws"],
        },
        "core_libraries": core,
    }
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {SNAPSHOT.relative_to(ROOT).as_posix()} for AnyPS5 {commit[:7]}.")


def load_snapshot() -> dict:
    if not SNAPSHOT.is_file():
        raise SystemExit(
            "update_progress: progress/anyps5.json is missing. "
            "Run: python3 scripts/update_progress.py --refresh-anyps5"
        )
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Rendering


def percent(part: int, whole: int) -> int:
    return round(100 * part / whole) if whole else 0


def bar(done: int, total: int, blocked: int = 0) -> str:
    """Done cells, then open cells, then blocked cells, BAR_WIDTH wide."""
    if total == 0:
        return "`" + "░" * BAR_WIDTH + "`"
    done_cells = round(BAR_WIDTH * done / total)
    blocked_cells = round(BAR_WIDTH * blocked / total)
    # Never hide a non-zero count behind rounding, nor round an unfinished
    # count up to a full bar.
    if done and not done_cells:
        done_cells = 1
    if done < total and done_cells == BAR_WIDTH:
        done_cells = BAR_WIDTH - 1
    if blocked and not blocked_cells:
        blocked_cells = 1
    blocked_cells = min(blocked_cells, BAR_WIDTH - done_cells)
    open_cells = BAR_WIDTH - done_cells - blocked_cells
    return "`" + "█" * done_cells + "░" * open_cells + "▒" * blocked_cells + "`"


def number(value: int) -> str:
    return f"{value:,}"


def site_data(phases: list[Phase], snapshot: dict) -> dict:
    return {
        "roadmap": {
            "done": sum(p.done for p in phases),
            "open": sum(p.open for p in phases),
            "blocked": sum(p.blocked for p in phases),
            "phases": [
                {
                    "number": p.number,
                    "title": p.title,
                    "done": p.done,
                    "open": p.open,
                    "blocked": p.blocked,
                }
                for p in phases
            ],
        },
        "anyps5": {k: v for k, v in snapshot.items() if k != "_comment"},
    }


def render_readme(phases: list[Phase], snapshot: dict) -> str:
    done = sum(p.done for p in phases)
    blocked = sum(p.blocked for p in phases)
    total = sum(p.total for p in phases)
    commit = snapshot["commit"]
    shaders = snapshot["shaders"]
    rdna2, gfx1013 = shaders["rdna2"], shaders["gfx1013"]
    libs = snapshot["libraries"]

    lines = [
        START,
        "<!-- Generated by scripts/update_progress.py. Do not edit by hand. -->",
        "",
        "> [!WARNING]",
        "> **Game research is blocked.** No GTA VI files can be researched lawfully yet,",
        f"> so {blocked} of {total} roadmap tasks ({percent(blocked, total)}%) cannot start.",
        "> Until that changes, the project works from public research and builds on",
        f"> [AnyPS5]({ANYPS5_URL}) to move faster.",
        "",
        f"**[View the progress page]({SITE_URL})**",
        "",
        "### Roadmap",
        "",
        "| Phase | Progress | Done | Blocked on game files |",
        "| --- | --- | ---: | ---: |",
    ]
    for p in phases:
        lines.append(
            f"| {p.number}. {p.title} | {bar(p.done, p.total, p.blocked)} "
            f"{percent(p.done, p.total)}% | {p.done}/{p.total} | {p.blocked or '—'} |"
        )
    lines += [
        f"| **Overall** | {bar(done, total, blocked)} {percent(done, total)}% "
        f"| **{done}/{total}** | **{blocked}** |",
        "",
        "`█` done · `░` open, can be worked on now · `▒` blocked until the game files"
        " can be researched. Details in [TODO.md](TODO.md).",
        "",
        "### Foundation from AnyPS5",
        "",
        f"Measured by AnyPS5's own `tools/progress.py` at the pinned commit "
        f"[`{commit[:7]}`]({snapshot['source']}).",
        "",
        "| Component | Progress | Count |",
        "| --- | --- | ---: |",
        f"| Shaders: {rdna2['isa']} reference, translated | "
        f"{bar(rdna2['translated'], rdna2['total'])} {percent(rdna2['translated'], rdna2['total'])}% "
        f"| {number(rdna2['translated'])}/{number(rdna2['total'])} |",
        f"| Shaders: {gfx1013['isa']}, translated | "
        f"{bar(gfx1013['translated'], gfx1013['total'])} "
        f"{percent(gfx1013['translated'], gfx1013['total'])}% "
        f"| {number(gfx1013['translated'])}/{number(gfx1013['total'])} |",
        f"| System library functions ({snapshot['library_count']} libraries) | "
        f"{bar(libs['done'], libs['total'])} {percent(libs['done'], libs['total'])}% "
        f"| {number(libs['done'])}/{number(libs['total'])} |",
    ]
    for lib in snapshot["core_libraries"]:
        lines.append(
            f"| {lib['role']} (`{lib['name']}`) | {bar(lib['done'], lib['total'])} "
            f"{percent(lib['done'], lib['total'])}% | {number(lib['done'])}/{number(lib['total'])} |"
        )
    lines += [
        "",
        "The libraries listed are ones nearly every PS5 game imports; GTA VI's actual",
        "list is unknown until its files can be researched. A translated shader",
        "instruction or implemented function is counted from source code and does not",
        f"show that a game runs. The recompiler still has {shaders['unsupported_throws']}",
        "code paths that report an unsupported case.",
        END,
    ]
    return "\n".join(lines)


def splice(readme: str, block: str) -> str:
    start = readme.find(START)
    end = readme.find(END)
    if start == -1 or end == -1 or end < start:
        raise SystemExit(
            f"update_progress: README.md must contain '{START}' followed by '{END}'"
        )
    return readme[:start] + block + readme[end + len(END):]


def build_site(output: Path, data: dict) -> None:
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(SITE_SOURCE, output)
    (output / "progress.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Built the progress site in {output}.")


# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="exit 1 if README.md or the snapshot is stale"
    )
    parser.add_argument("--site", type=Path, metavar="DIR", help="build the Pages site into DIR")
    parser.add_argument(
        "--refresh-anyps5",
        action="store_true",
        help="re-measure the AnyPS5 submodule into progress/anyps5.json",
    )
    args = parser.parse_args()

    if args.refresh_anyps5:
        if args.check:
            parser.error("--refresh-anyps5 does not combine with --check")
        refresh_snapshot()

    phases = parse_todo(TODO.read_text(encoding="utf-8"))
    snapshot = load_snapshot()
    current = README.read_text(encoding="utf-8")
    updated = splice(current, render_readme(phases, snapshot))

    if args.check:
        stale = False
        pinned = pinned_anyps5_commit()
        if pinned and pinned != snapshot["commit"]:
            print(
                f"progress/anyps5.json measures AnyPS5 {snapshot['commit'][:7]}, but the "
                f"repository pins {pinned[:7]}. Run: python3 scripts/update_progress.py "
                "--refresh-anyps5",
                file=sys.stderr,
            )
            stale = True
        if updated != current:
            print(
                "README.md progress section is out of date. "
                "Run: python3 scripts/update_progress.py",
                file=sys.stderr,
            )
            stale = True
        if stale:
            return 1
        print("Progress report is up to date.")
    elif updated != current:
        README.write_text(updated, encoding="utf-8", newline="\n")
        print("Updated README.md progress section.")
    else:
        print("README.md progress section already up to date.")

    if args.site:
        build_site(args.site, site_data(phases, snapshot))
    return 0


if __name__ == "__main__":
    sys.exit(main())
