# Technical limitations and risks

- **Status:** Living document
- **Last updated:** 2026-11-21
- **AnyPS5 commit reviewed:** [`1582613`](https://github.com/boykopovar/AnyPS5/tree/15826135019b8c7de27f42661a850a1dd9750932)
- **Related:** [ADR 0003](../adr/0003-build-on-anyps5-relinker.md),
  [Phase 1 research report](phase-1-research-report.md), [TODO.md](../../TODO.md)

What stands between this project and GTA VI running on a PC, ordered from the
hardest blocker down. Everything here comes from public sources and from
AnyPS5's own code and documentation; nothing comes from the game. Where a
finding rests on AnyPS5's documentation rather than our own reproduction, it is
labelled **Reported**, following the
[evidence standard](phase-1-research-report.md#evidence-standard).

## 1. Access to the game (blocker)

**The project cannot lawfully obtain what AnyPS5 needs as input.** AnyPS5's
relinker needs an extracted, decrypted executable and its modules
(`third_party/AnyPS5/docs/user/USAGE.md`). PS5 executables are encrypted, and
decrypting them means circumventing an access control, which DMCA §1201
prohibits in the US even for a copy you own. The project will not do that, link
to tools that do, or accept material obtained that way. *(Reported: AnyPS5
usage docs; legal position is the project's policy, not legal advice.)*

Consequences:

- GTA VI's import list, and with it the exact set of libraries and functions it
  needs, is unknown. 15 roadmap tasks wait on it.
- No behaviour of the game can be tested or reproduced by the project.
- The library work below is chosen by what nearly every PS5 game uses, not by
  what GTA VI is known to use.

**Distribution risk.** A relinked executable is derived from the game. It must
never be shared, and the project never publishes one
([ADR 0003](../adr/0003-build-on-anyps5-relinker.md), decision 5). Take-Two,
which owns Rockstar Games, has taken down GTA reverse-engineering projects
before; a project named after GTA VI should expect scrutiny.

## 2. Unimplemented functions end the game

AnyPS5's rule is that every function "either does exactly what it's supposed to
or throws an exception" (`third_party/AnyPS5/docs/dev/TechnicalDebt.md`). An
uncaught exception prints a message and ends the process. So the first
unimplemented function GTA VI calls stops it, rather than returning a fake
success that might let it continue. *(Reported.)*

This makes failures easy to find and fix, but it means every function on GTA VI's
startup path must be implemented before the game gets far. With 17,749 of 39,253
declared functions implemented across 413 libraries, gaps on that path are
likely.

## 3. Gaps in the core libraries

Libraries nearly every PS5 game imports, with AnyPS5's implemented counts and the
entries in its technical-debt file for each
(`third_party/AnyPS5/docs/dev/debt/<library>.md`):

| Library | Role | Implemented | Silent stubs | Unknown signatures | Behaviour gaps |
| --- | --- | ---: | ---: | ---: | ---: |
| `libkernel` | Kernel | 719 / 758 | 18 | 125 | 291 |
| `libSceLibcInternal` | C runtime | 664 / 1,124 | — | 26 | 54 |
| `libSceAgc` | Graphics | 239 / 242 | — | 46 | 12 |
| `libSceAgcDriver` | Graphics driver | 97 / 167 | 5 | 97 | 312 |
| `libSceVideoOut` | Display output | 78 / 290 | 6 | 37 | 23 |
| `libSceAudioOut` | Audio output | 78 / 219 | 4 | 130 | 14 |
| `libScePad` | Controller | 56 / 222 | 4 | 57 | 12 |
| `libSceUserService` | User service | 44 / 695 | — | 520 | 6 |
| `libSceSystemService` | System service | 144 / 617 | 10 | 110 | 49 |
| `libSceSaveData.native` | Save data | 58 / 119 | 4 | 14 | 23 |
| `libSceSysmodule` | Module loading | 12 / 21 | 2 | 6 | 4 |
| `libSceAppContent` | App content | 30 / 39 | 1 | 6 | 16 |
| `libSceNpTrophy2` | Trophies | 18 / 61 | 4 | 2 | 8 |

How to read the columns, per AnyPS5's debt conventions:

- **Silent stubs** are the exceptions to the throw rule: functions that return
  without doing the work. A game that relies on their result may misbehave
  without any error.
- **Unknown signatures** are exports whose parameters are assumed or unknown,
  usually because they were added from a title's import list without
  documentation. Many of the unimplemented functions are in this group, which is
  why user service (520 entries) and audio output (130) look so incomplete.
- **Behaviour gaps** are approximations or unverified behaviour in implemented
  functions.

Counts are entry counts from the debt files at the reviewed commit, made with a
read-only script; one entry can cover several functions. *(Confirmed:
reproducible from the submodule.)*

Most relevant to a large open-world game:

- **Graphics driver.** 312 behaviour-gap entries make `libSceAgcDriver` the
  largest risk. GTA VI will lean on the GPU far harder than the titles AnyPS5
  has been tested with.
- **Shaders.** The recompiler handles every RDNA 2 reference instruction form
  but 1,484 of 1,560 gfx1013 reference forms, and has 126 code paths that report
  an unsupported case. A translated instruction is counted from source code; it
  has not been verified against GTA VI's shaders.
- **Kernel.** 18 silent stubs in `libkernel`, including semaphore attributes
  accepted and ignored and some mutex protocol settings. Timing and threading
  differences tend to show up only in large, heavily threaded games.
- **User and system services.** Most of these libraries are declared but not
  implemented. PSN-linked account state is explicitly unsupported and throws
  (`sceUserServiceIsUserStorageAccountBound`, for example), which matters if
  GTA VI checks account state at startup even without an online mode.

## 4. Behaviour not measured on a console

AnyPS5 documents several areas as unmeasured against real hardware. *(Reported.)*

- The register state at the main-module entry point
  (`docs/dev/ARCHITECTURE.md`, AnyPS5 issue #9048).
- Thread cancellation beyond deferred requests.
- Controller rumble derived from haptic audio, and rumble pausing on focus loss:
  approximations, not tested on real controllers.
- `--to-intel` trampolines, which adapt AMD-only instructions for Intel
  processors, are covered only by a synthetic test.

Problems in these areas may only appear with a real, large title.

## 5. Toolchain and dependency risks

- **Windows toolchain.** AnyPS5 needs x86-64 MinGW-w64 GCC with POSIX threads
  and SEH or DWARF exceptions. Built libraries need `libgcc_s_seh-1.dll`,
  `libstdc++-6.dll` and `libwinpthread-1.dll` beside them; a different
  `libstdc++-6.dll` earlier on `PATH` (Git's, for example) causes "Entry Point
  Not Found". *(Reported: AnyPS5 `TechnicalDebt.md`.)*
- **Upstream dependency.** Fixes GTA VI needs land on AnyPS5's schedule and
  review. The submodule pins one commit, so upstream changes reach this project
  only when it is bumped on purpose.
- **Licence.** GPL-2.0-only rules out code from projects under incompatible
  licences, including GPLv3-only code.

## 6. Performance

Unknown. Native execution avoids the cost of emulating instructions, but
graphics translation and shader recompilation have overhead that can only be
measured with the game. AnyPS5 has profiling tools (`tools/performance_*.py`)
for when that is possible.

## What can be done now

- Fill gaps upstream in the core libraries above, starting with silent stubs and
  functions with known signatures.
- Build AnyPS5 locally and in CI so library changes can be tested.
- Keep this document current when the submodule is bumped.
