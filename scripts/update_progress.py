#!/usr/bin/env python3
"""Generate the project's progress report: the README section and the Pages data.

Usage:
    python3 scripts/update_progress.py                  # rewrite README.md in place
    python3 scripts/update_progress.py --check          # exit 1 if anything is stale
    python3 scripts/update_progress.py --site _site     # also build the Pages site
    python3 scripts/update_progress.py --refresh-anyps5 # re-measure the AnyPS5 submodule

Two sources feed the report:

Outputs: the README section, which embeds the progress/roadmap-*.svg and
progress/anyps5-*.svg charts (light and dark variants, rendered by GitHub as
images), and with --site the Pages data.

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
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODO = ROOT / "TODO.md"
README = ROOT / "README.md"
SITE_SOURCE = ROOT / "site"
SNAPSHOT = ROOT / "progress" / "anyps5.json"
PROGRESS_DIR = ROOT / "progress"
ANYPS5 = ROOT / "third_party" / "AnyPS5"
ANYPS5_PATH = "third_party/AnyPS5"
ANYPS5_URL = "https://github.com/boykopovar/AnyPS5"
SITE_URL = "https://jamescicada.github.io/GTAVI-Recomp/"

BLOCKED_MARKER = "needs game files"
START = "<!-- progress:start -->"
END = "<!-- progress:end -->"

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


# SVG charts. GitHub renders SVG files referenced from Markdown as images, so
# the README gets graphical bars. Each chart is written in a light and a dark
# variant: the README picks one with <picture> and prefers-color-scheme, which
# GitHub matches to the viewer's GitHub theme (an image's own media queries
# would follow the OS theme instead). Colours follow GitHub's palette.

SVG_WIDTH = 820
LABEL_X = 0
BAR_X = 330
BAR_W = 340
PCT_X = BAR_X + BAR_W + 44  # right-aligned
COUNT_X = SVG_WIDTH  # right-aligned
ROW_H = 30
BAR_H = 10
GROUP_H = 34

THEMES = {
    "light": {"text": "#1f2328", "sub": "#59636e", "track": "#d1d9e0", "done": "#1f883d", "blocked": "#cf222e"},
    "dark": {"text": "#f0f6fc", "sub": "#9198a1", "track": "#3d444d", "done": "#2ea043", "blocked": "#f85149"},
}


def svg_head(theme: str) -> str:
    c = THEMES[theme]
    return f"""<style>
  text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif; font-size: 13px; fill: {c['text']}; }}
  .sub {{ fill: {c['sub']}; font-size: 12px; }}
  .num {{ font-variant-numeric: tabular-nums; }}
  .strong {{ font-weight: 600; }}
  .group {{ font-size: 12px; font-weight: 600; fill: {c['sub']}; letter-spacing: 0.06em; }}
  .track {{ fill: {c['track']}; }}
  .done {{ fill: {c['done']}; }}
  .rule {{ stroke: {c['track']}; }}
</style>
<defs>
  <pattern id="blocked" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="6" height="6" fill="{c['blocked']}" opacity="0.35"/>
    <rect width="3" height="6" fill="{c['blocked']}"/>
  </pattern>
</defs>"""


def svg_bar(y: float, done: int, total: int, blocked: int = 0) -> str:
    """A rounded track with done filled from the left and blocked from the right."""
    clip = f"bar{int(y)}"
    done_w = BAR_W * done / total if total else 0
    blocked_w = BAR_W * blocked / total if total else 0
    # Keep tiny non-zero values visible, and never show unfinished work as full.
    if done and done_w < 3:
        done_w = 3
    if done < total and done_w > BAR_W - 3:
        done_w = BAR_W - 3
    parts = [
        f'<clipPath id="{clip}"><rect x="{BAR_X}" y="{y}" width="{BAR_W}" '
        f'height="{BAR_H}" rx="{BAR_H / 2}"/></clipPath>',
        f'<g clip-path="url(#{clip})">',
        f'<rect class="track" x="{BAR_X}" y="{y}" width="{BAR_W}" height="{BAR_H}"/>',
    ]
    if done_w:
        parts.append(f'<rect class="done" x="{BAR_X}" y="{y}" width="{done_w:.1f}" height="{BAR_H}"/>')
    if blocked_w:
        parts.append(
            f'<rect fill="url(#blocked)" x="{BAR_X + BAR_W - blocked_w:.1f}" y="{y}" '
            f'width="{blocked_w:.1f}" height="{BAR_H}"/>'
        )
    parts.append("</g>")
    return "".join(parts)


@dataclass
class ChartRow:
    label: str
    done: int
    total: int
    blocked: int = 0
    sub: str = ""
    count: str = ""
    strong: bool = False
    rule_above: bool = False


def svg_chart(title: str, entries: list, theme: str, legend: bool = False) -> str:
    """entries: ChartRow, or a str for a group heading."""
    body: list[str] = []
    y = 4.0
    for entry in entries:
        if isinstance(entry, str):
            y += 8 if body else 0
            body.append(f'<text class="group" x="{LABEL_X}" y="{y + 16}">{escape(entry.upper())}</text>')
            y += GROUP_H - 8
            continue
        if entry.rule_above:
            body.append(f'<line class="rule" x1="0" x2="{SVG_WIDTH}" y1="{y + 0.5}" y2="{y + 0.5}"/>')
            y += 4
        mid = y + ROW_H / 2
        weight = " strong" if entry.strong else ""
        label = escape(entry.label)
        if entry.sub:
            label += f' <tspan class="sub">{escape(entry.sub)}</tspan>'
        body.append(f'<text class="{weight.strip()}" x="{LABEL_X}" y="{mid + 4.5}">{label}</text>')
        body.append(svg_bar(mid - BAR_H / 2, entry.done, entry.total, entry.blocked))
        body.append(
            f'<text class="num{weight}" x="{PCT_X}" y="{mid + 4.5}" text-anchor="end">'
            f"{percent(entry.done, entry.total)}%</text>"
        )
        count = entry.count or f"{number(entry.done)} / {number(entry.total)}"
        body.append(
            f'<text class="num sub" x="{COUNT_X}" y="{mid + 4.5}" text-anchor="end">{escape(count)}</text>'
        )
        y += ROW_H
    if legend:
        y += 10
        ly = y + 10
        body.append(
            f'<rect class="done" x="0" y="{ly - 9}" width="12" height="10" rx="2"/>'
            f'<text class="sub" x="18" y="{ly}">Done</text>'
            f'<rect class="track" x="70" y="{ly - 9}" width="12" height="10" rx="2"/>'
            f'<text class="sub" x="88" y="{ly}">Open, can be worked on now</text>'
            f'<rect fill="url(#blocked)" x="270" y="{ly - 9}" width="12" height="10" rx="2"/>'
            f'<text class="sub" x="288" y="{ly}">Blocked until the game files can be researched</text>'
        )
        y += 20
    height = int(y + 6)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{height}" '
        f'viewBox="0 0 {SVG_WIDTH} {height}" role="img" aria-label="{escape(title)}">\n'
        f"<title>{escape(title)}</title>\n{svg_head(theme)}\n"
        + "\n".join(body)
        + "\n</svg>\n"
    )


def roadmap_chart(phases: list[Phase], theme: str) -> str:
    done = sum(p.done for p in phases)
    blocked = sum(p.blocked for p in phases)
    total = sum(p.total for p in phases)
    rows = [
        ChartRow(
            f"{p.number}. {p.title}",
            p.done,
            p.total,
            p.blocked,
            count=f"{p.done} / {p.total}" + (f" · {p.blocked} blocked" if p.blocked else ""),
        )
        for p in phases
    ]
    rows.append(
        ChartRow(
            "Overall",
            done,
            total,
            blocked,
            count=f"{done} / {total} · {blocked} blocked",
            strong=True,
            rule_above=True,
        )
    )
    return svg_chart(
        f"Roadmap: {done} of {total} tasks done, {blocked} blocked on game files",
        rows,
        theme,
        legend=True,
    )


def anyps5_chart(snapshot: dict, theme: str) -> str:
    shaders = snapshot["shaders"]
    rdna2, gfx1013 = shaders["rdna2"], shaders["gfx1013"]
    libs = snapshot["libraries"]
    entries: list = [
        "Shader recompiler: instruction forms translated",
        ChartRow(f"{rdna2['isa']} reference", rdna2["translated"], rdna2["total"]),
        ChartRow(gfx1013["isa"], gfx1013["translated"], gfx1013["total"]),
        "System library functions",
        ChartRow(
            "All libraries",
            libs["done"],
            libs["total"],
            sub=f"{snapshot['library_count']} libraries",
            strong=True,
        ),
    ]
    for lib in snapshot["core_libraries"]:
        entries.append(ChartRow(lib["role"], lib["done"], lib["total"], sub=lib["name"]))
    return svg_chart(
        f"AnyPS5 at {snapshot['commit'][:7]}: shaders and system library functions",
        entries,
        theme,
    )


def chart_path(name: str, theme: str) -> Path:
    return PROGRESS_DIR / f"{name}-{theme}.svg"


def charts(phases: list[Phase], snapshot: dict) -> dict[Path, str]:
    out = {}
    for theme in THEMES:
        out[chart_path("roadmap", theme)] = roadmap_chart(phases, theme)
        out[chart_path("anyps5", theme)] = anyps5_chart(snapshot, theme)
    return out


def picture(name: str, alt: str) -> str:
    """GitHub swaps the <source> to match the viewer's GitHub theme."""
    def rel(theme: str) -> str:
        return chart_path(name, theme).relative_to(ROOT).as_posix()

    return (
        "<picture>\n"
        f'  <source media="(prefers-color-scheme: dark)" srcset="{rel("dark")}">\n'
        f'  <img src="{rel("light")}" width="820" alt="{escape(alt)}">\n'
        "</picture>"
    )


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
        picture(
            "roadmap",
            f"Roadmap progress: {done} of {total} tasks done ({percent(done, total)}%), "
            f"{blocked} blocked on game files",
        ),
        "",
        "Details in [TODO.md](TODO.md).",
        "",
        "### Foundation from AnyPS5",
        "",
        f"Measured by AnyPS5's own `tools/progress.py` at the pinned commit "
        f"[`{commit[:7]}`]({snapshot['source']}).",
        "",
        picture(
            "anyps5",
            f"AnyPS5: shaders translated {rdna2['translated']}/{rdna2['total']} (RDNA 2 "
            f"reference) and {gfx1013['translated']}/{gfx1013['total']} (gfx1013 reference); "
            f"system library functions {libs['done']}/{libs['total']}",
        ),
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

    svgs = charts(phases, snapshot)

    if args.check:
        stale = False
        for path, content in svgs.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                print(
                    f"{path.relative_to(ROOT).as_posix()} is out of date. "
                    "Run: python3 scripts/update_progress.py",
                    file=sys.stderr,
                )
                stale = True
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
    else:
        for path, content in svgs.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
                print(f"Updated {path.relative_to(ROOT).as_posix()}.")
        if updated != current:
            README.write_text(updated, encoding="utf-8", newline="\n")
            print("Updated README.md progress section.")
        else:
            print("README.md progress section already up to date.")

    if args.site:
        build_site(args.site, site_data(phases, snapshot))
    return 0


if __name__ == "__main__":
    sys.exit(main())
