# Phase 1 Research Report

- **Status:** In progress — filled from public sources and AnyPS5; GTA VI-specific findings blocked
- **Owner:** unassigned
- **Last updated:** 2026-11-26

This document is the deliverable for Phase 1 of `TODO.md`. It records what has
been *observed* about the PS5 build and the host platforms, not what is assumed.

Every section is filled in the same way. Delete the guidance lines as sections
are completed; do not delete a section because it is empty — an empty section is
an honest statement that nothing is known yet.

## How to use this document

1. Copy the finding block for each item you investigate.
2. Record the evidence *before* the interpretation.
3. Mark confidence honestly. "Unverified" is a valid and useful result.
4. If something could not be investigated, say so and why.

## Evidence standard

| Label | Meaning |
| --- | --- |
| **Confirmed** | Observed directly, with reproduction steps and a source. |
| **Reported** | Found in a credible external source, not reproduced locally. |
| **Hypothesis** | A reasoned inference from confirmed findings. Not evidence. |
| **Unverified** | Mentioned or assumed, but nothing supports it yet. |
| **Blocked** | Cannot be investigated with the resources available. |

A claim may only move to **Confirmed** when another contributor can reproduce it.
Per `TODO.md` principle 7, no compatibility claim is made from anything less.

### Finding block

```text
Finding:      <one sentence>
Evidence:     <commands, tool output, document section, or file hash>
Reproduction: <exact steps, or "n/a" for external sources>
Confidence:   Confirmed | Reported | Hypothesis | Unverified | Blocked
Implication:  <what this means for the translation layer>
```

## Legal and ethical constraints

- Do not include game files, assets, PS5 system files, decryption keys, or
  decompiled code in this repository or in this report.
- Do not include material from leaks. If a finding can only be supported by
  leaked material, record it as **Blocked** and stop.
- Do not document or implement ways to bypass encryption, entitlement checks, or
  DRM. Record only *whether* a mechanism exists and what it requires.
- Record *behaviour* and *interface facts*, not copyrighted content.
- Reverse engineering must comply with applicable law; see `CONTRIBUTE.md`.

## Background — reported, not verified

The following is commonly stated about the PS5 platform. None of it has been
verified by this project, and each item must be promoted to **Confirmed** or
demoted before it is relied on. It is listed only to give the research a shape.

| Claim | Confidence | Verify by |
| --- | --- | --- |
| CPU is x86-64 (AMD Zen 2 class) | Reported | Public specifications |
| OS is FreeBSD-derived ("Orbis OS") | Reported | Public documentation, observed behaviour |
| Executables are ELF-derived, loaded from an app container | Reported | Inspecting a legitimately obtained sample |
| Main module is commonly named `eboot.bin` | Reported | Same |
| System libraries use a `libSce*` naming convention | Reported | Import table of a sample |
| Graphics is a low-level command-buffer API (GNM/AGC family) | Reported | Public documentation, samples |
| Guest mount points include `/app0`, `/data`, `/user` | Reported | Observed file access |
| Saved data is managed by a dedicated system service | Reported | Public documentation |

---

Most findings below come from AnyPS5's source and documentation at commit
[`1582613`](https://github.com/boykopovar/AnyPS5/tree/15826135019b8c7de27f42661a850a1dd9750932),
pinned in `third_party/AnyPS5`. They are **Reported**: AnyPS5 states them and its
code implements them, but this project has not reproduced them on a console or
with GTA VI. Paths in the Evidence column are relative to `third_party/AnyPS5`.
Risks and gaps are collected in [limitations-and-risks.md](limitations-and-risks.md).

## 1. Executable container and module loading

**Question:** What container holds the executable, how is it loaded, and what
does the entry point expect?

| Field | Value | Confidence | Evidence |
| --- | --- | --- | --- |
| Container format | SELF/fSELF containers wrapping ELF images | Reported | `docs/user/USAGE.md`, `tools/unwrap_self.py` |
| Module format | x86-64 ELF; bundled modules are `.prx` ELF files in `sce_module/` | Reported | `docs/user/USAGE.md` |
| Main module name | `eboot.bin`, under `/app0` | Reported | `core/libs/prx/libkernel/AppMetadata/src/AppMetadata.cpp` |
| Architecture | x86-64 (AMD Zen 2 class) | Reported | Public specifications; AnyPS5 runs guest code natively on x86-64 |
| Encryption / signing | Executables are encrypted; AnyPS5 needs them decrypted | Reported | `docs/user/USAGE.md` ("does not extract or decrypt package files") |
| Import binding | Imports are named by NID, a hash of the symbol name | Reported | `docs/dev/ARCHITECTURE.md` |
| Loader entry contract | Host entry stubs documented; console register state not measured | Reported | `docs/dev/ARCHITECTURE.md` ("Main-module entry registers", AnyPS5 #9048) |

```text
Finding:      Loading requires a decrypted executable, which the project cannot
              legitimately obtain.
Evidence:     third_party/AnyPS5/docs/user/USAGE.md, "Input and conversion"
Reproduction: n/a (external documentation)
Confidence:   Reported
Implication:  Running GTA VI depends on users supplying their own decrypted copy.
              The project does not provide or explain decryption (ADR 0003).
```

Answers to the earlier open questions:

- **Do entitlements or keys block loading?** Yes, for the project itself: see the
  finding above.
- **Are secondary modules loaded at run time?** Yes. A title can ship its own
  modules in `sce_module/` and load some later with `sceKernelLoadStartModule`;
  AnyPS5 defers starting those until the title asks (`docs/user/USAGE.md`,
  "Module start-up"). Which modules GTA VI ships is unknown. **Blocked.**

## 2. Imported library surface

**Question:** Which libraries and symbols does the guest import?

This is the single most important table in the project: it defines the work.

| Library | Symbols imported | Subsystem | Priority | Evidence |
| --- | --- | --- | --- | --- |
| _none recorded_ | | | | **Blocked**: needs GTA VI's executable |

Until this is known, work targets the libraries nearly every PS5 title imports;
see section 11 and [limitations-and-risks.md](limitations-and-risks.md#3-gaps-in-the-core-libraries).
AnyPS5's `tools/import_audit.py` can produce this table once an executable can be
examined lawfully.

Open questions:

- Which imports are optional (loaded lazily by name) and therefore invisible in a
  static import table? **Blocked.**
- Which imports are only used by features we can initially omit? **Blocked.**

## 3. Guest OS behaviour

**Question:** Which OS behaviours does the guest depend on that a PC host does not
provide identically?

| Behaviour | Guest expectation | Host handling in AnyPS5 | Confidence |
| --- | --- | --- | --- |
| Virtual memory layout | Direct memory mapped by the title | Separate Windows and macOS/Linux allocators (`docs/dev/ARCHITECTURE.md`, `libkernel/DirectMemory`) | Reported |
| Executable memory permissions | _unknown_ | _not reviewed_ | Unverified |
| Thread priorities and affinity | `scePthread*` API | `libkernel/Pthread` on host threads | Reported |
| Timing and clocks | GTA VI's timing requirements are unknown | The realtime and monotonic clocks report 81 ns resolution. The separate CPU mode query (`sceKernelGetCpumode`) returns 0 at the pin. | [Confirmed for the clock fixtures](../testing-anyps5.md#guest-clocks) |
| Synchronisation primitives | Mutexes, semaphores, condition variables | `libkernel`; some attributes accepted and ignored (debt: silent stubs) | Reported |
| Thread cancellation | Deferred and asynchronous cancellation | Deferred requests handled; asynchronous cases unverified (`docs/dev/ARCHITECTURE.md`) | Reported |

## 4. Filesystem and mount points

**Question:** Which mount points does the guest use, and what semantics does it
expect from them?

| Mount point | Purpose | Read/write | Host mapping | Confidence |
| --- | --- | --- | --- | --- |
| `/app0` | The game's install: `eboot.bin`, modules, `sce_sys/param.json` | Read | Converted program's `app0/` directory (`libkernel/File`) | Reported |
| `/data`, `/user`, `/savedata0`, ... | _unknown for GTA VI_ | _unknown_ | _not reviewed_ | Blocked |

Note: `DriveMap` / `windows_to_posix` in `src/path.cpp` handle **host** paths
only and are not used by AnyPS5.

Open questions:

- Which other mount points does GTA VI use? **Blocked.**
- Does the guest rely on case-insensitive lookups, or on exact names? _Not reviewed._

## 5. Graphics

**Question:** What graphics interface does the guest use, and what is the
translation target?

| Field | Value | Confidence | Evidence |
| --- | --- | --- | --- |
| API family | AGC (`libSceAgc`, `libSceAgcDriver`) | Reported | `core/libs/prx/libSceAgc*` |
| Command buffer format | APR and AMM command buffers | Reported | `docs/dev/ARCHITECTURE.md`, "APR and AMM command buffers" |
| Shader format | AMD RDNA-family GPU machine code; AnyPS5 tracks RDNA 2 and gfx1013 references | Reported | `docs/dev/PROGRESS.md` |
| Synchronisation model | _not reviewed_ | Unverified | |
| Translation target | Vulkan; shaders recompiled to SPIR-V | Reported | `libSceAgcDriver/Execution/src/VulkanDevice.cpp`, `core/shader/recompiler` |

Answers to the earlier open questions:

- **Is command-stream translation sufficient?** It is the approach AnyPS5 takes,
  and it has run at least one title. Whether it holds up for GTA VI is unknown.
- **Cost of translating shaders ahead of time versus at load?** AnyPS5 has a
  shader disk cache (`core/shader/recompiler/ShaderDiskCache.cpp`). Cost for
  GTA VI is unknown. **Blocked.**

## 6. Audio

| Field | Value | Confidence | Evidence |
| --- | --- | --- | --- |
| Output API | `libSceAudioOut` (78 / 219 functions implemented) | Reported | AnyPS5 progress scan |
| Channel / format expectations | At the pin, legacy AudioOut queues eight-channel float PCM unchanged. AudioOut2 produces the expected stereo samples for mono, stereo, 7.1 and 7.1.4 float and signed 16-bit PCM inputs. GTA VI's input formats remain unknown. | Confirmed for the runtime fixtures | [PCM formats and channel layouts](../testing-anyps5.md#pcm-formats-and-channel-layouts) |
| 3D audio usage | `libSceAudio3d` exists in AnyPS5 (32 functions); GTA VI's use unknown | Reported / Blocked | AnyPS5 progress scan |
| Host backend | SDL2 audio | Reported | `libSceAudioOut/src/AudioOut.cpp` |

## 7. Input

| Field | Value | Confidence | Evidence |
| --- | --- | --- | --- |
| Input API | `libScePad` (56 / 222 functions implemented) | Reported | AnyPS5 progress scan |
| Adaptive-trigger commands | Guest L2 and R2 requests produce separate effect blocks. The fixture checks zone strengths and the effect restored after re-enabling triggers. | Confirmed | [Guest pad trigger fixture](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/tests/GuestPadTriggerEffects.cpp) |
| Bluetooth DualSense haptic audio | The haptics buffer converts generated PCM to 3 kHz samples. The fixture checks the report bytes, checksum and scheduled intervals between reports. | Confirmed | [DualSense haptics fixture](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/prx/libSceVideoOut/tests/DualSenseHaptics.cpp) |
| Host backend | SDL2 game controllers, plus keyboard and mouse mapping | Reported | `docs/user/INPUT_MAPPING.md` |

At the pinned revision `1582613`, the host sends adaptive triggers through SDL
for PS5 controllers. Alongside motor rumble, it has a separate Bluetooth HID
output path for DualSense haptic audio. [Trigger and rumble dispatch](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/prx/libSceVideoOut/src/PadInput.cpp#L329-L398) · [Bluetooth haptics output](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/prx/libSceVideoOut/src/PadInput.cpp#L225-L269)

From the GTAVI-Recomp root, configure `third_party/AnyPS5` in `build/a5` with
`BUILD_TESTING=ON`, then build and run the two fixtures. [Pinned build requirements](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/docs/dev/BUILD.md#requirements)

```console
cmake --build build/a5 --parallel 4 --target guest_pad_trigger_effects_tests dualsense_haptics_tests
ctest --test-dir build/a5 --no-tests=error --output-on-failure -R "^(guest_pad_trigger_effects|dualsense_haptics)$"
```

Both fixtures passed on Windows x64 and Ubuntu 24.04 x64 using in-memory data.
Physical trigger resistance, vibration fidelity and GTA VI's use of either
feature remain unverified by this project. [Ubuntu fixture output](https://github.com/RavenCurseBurg/GTAVI-Recomp/actions/runs/45725866198/job/139595455924)

## 8. Networking and online services

GTA VI has no online mode released, so online services are out of scope for now.
The game may still call PSN functions at startup, for example to check account
state. AnyPS5 makes unsupported PSN account queries throw rather than return a
fake answer (`sceUserServiceIsUserStorageAccountBound`), so any such call would
stop the game until it is handled. Which calls GTA VI makes is unknown.
**Blocked.**

## 9. Protection and entitlements

Executables are encrypted, and AnyPS5 needs them decrypted (section 1). Whether
GTA VI performs entitlement checks at run time is unknown. **Blocked.** As
required above, this report records only that the mechanism exists.

## 10. Compatibility obstacles

| Obstacle | Category | Severity | Blocking | Evidence |
| --- | --- | --- | --- | --- |
| Decrypted executable cannot be obtained by the project | Access | Critical | Yes | Section 1 |
| Unimplemented functions throw and end the process | Libraries | High | Per function | `TechnicalDebt.md` |
| Graphics driver behaviour gaps (312 debt entries) | Graphics | High | Unknown | `debt/libSceAgcDriver.md` |
| 76 gfx1013 shader forms and 126 unsupported recompiler paths | Graphics | Medium | Unknown | Progress scan |
| User and system services largely unimplemented | Libraries | Medium | Unknown | Progress scan |

Details in [limitations-and-risks.md](limitations-and-risks.md).

## 11. Library-to-host mapping

The libraries nearly every PS5 title imports, and AnyPS5's implementation of
each. GTA VI's own list is **Blocked** (section 2).

| Guest library | Host implementation | Fidelity | Notes |
| --- | --- | --- | --- |
| `libkernel` | AnyPS5 `libkernel` | 719 / 758 functions | Memory, threads, files, modules |
| `libSceLibcInternal` | AnyPS5 `libSceLibcInternal` | 664 / 1,124 | C runtime |
| `libSceAgc`, `libSceAgcDriver` | AnyPS5, on Vulkan | 239 / 242, 97 / 167 | Graphics |
| `libSceVideoOut` | AnyPS5 `libSceVideoOut` | 78 / 290 | Display output |
| `libSceAudioOut` | AnyPS5, on SDL2 | 78 / 219 | Audio output |
| `libScePad` | AnyPS5, on SDL2 | 56 / 222 | Controller |
| `libSceUserService` | AnyPS5 `libSceUserService` | 44 / 695 | User accounts |
| `libSceSystemService` | AnyPS5 `libSceSystemService` | 144 / 617 | System service |
| `libSceSaveData.native` | AnyPS5 `libSceSaveData.native` | 58 / 119 | Save data |

Counts are implemented / declared functions from AnyPS5's own progress tool;
current figures are on the [progress page](https://jamescicada.github.io/GTAVI-Recomp/).

## 12. Feasibility conclusions

- **What is the minimum library set for a first frame?** Unknown. **Blocked** on
  GTA VI's import list.
- **Is command-stream graphics translation viable?** Yes in general: AnyPS5 does
  it. Viable for GTA VI: unknown.
- **Can guest memory and threading be delegated to the host?** Largely, as
  AnyPS5's `libkernel` does, with the unmeasured areas listed in section 3.
- **Which parts must be reimplemented rather than delegated?** The system
  libraries themselves, which AnyPS5 implements on host APIs.
- **Is the project blocked by entitlements or encryption?** Yes, for the
  project's own research: it cannot lawfully obtain a decrypted executable.

## Risk register

| Risk | Likelihood | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- |
| No legitimate research material available | High | High | Work from AnyPS5 and public sources; mark the rest **Blocked** | Open |
| Encryption blocks loading | Certain | High | Users supply their own copy; the project never bypasses it | Accepted |
| Graphics translation is incomplete or too slow for GTA VI | Medium | High | Contribute to AnyPS5's graphics driver and recompiler | Open |
| Undocumented behaviour is misread, causing subtle bugs | High | Medium | Require reproducible evidence; test per library | Open |
| Legal exposure from research inputs | Medium | High | Enforce the DMCA-avoidance policy in `CONTRIBUTE.md` | Open |
| Upstream AnyPS5 does not accept or prioritise GTA VI needs | Medium | Medium | Follow AnyPS5's conventions; keep GTA VI-only work here | Open |

## Open questions

1. Which libraries, functions and mount points does GTA VI use? **Blocked.**
2. Does GTA VI make PSN or entitlement calls at startup without an online mode?
   **Blocked.**
3. What is the console's register state at the main-module entry point? Needs a
   console, not the game (AnyPS5 #9048).

## Changelog

| Date | Change | Author |
| --- | --- | --- |
| 2026-11-20 | Template created | — |
| 2026-11-20 | Reworked for PS5-to-PC library translation (ADR 0002) | — |
| 2026-11-21 | Filled sections from AnyPS5's documentation and code (ADR 0003) | — |
