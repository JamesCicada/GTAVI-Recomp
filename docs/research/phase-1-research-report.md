# Phase 1 Research Report

- **Status:** Template — no findings recorded yet
- **Owner:** unassigned
- **Last updated:** 2026-11-20

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

## 1. Executable container and module loading

**Question:** What container holds the executable, how is it loaded, and what
does the entry point expect?

| Field | Value |
| --- | --- |
| Container format | _unknown_ |
| Module format | _unknown_ |
| Architecture | _unknown_ |
| Encryption / signing | _unknown_ |
| Loader entry contract | _unknown_ |

Findings: none recorded.

Open questions:

- Does loading require entitlements or keys the project cannot legitimately
  obtain? If so, this is **Blocked** and must be stated plainly.
- Are there secondary modules loaded at runtime, or is everything in one image?

## 2. Imported library surface

**Question:** Which libraries and symbols does the guest import?

This is the single most important table in the project: it defines the work.

| Library | Symbols imported | Subsystem | Priority | Evidence |
| --- | --- | --- | --- | --- |
| _none recorded_ | | | | |

Open questions:

- Which imports are optional (loaded lazily by name) and therefore invisible in a
  static import table?
- Which imports are only used by features we can initially omit?

## 3. Guest OS behaviour

**Question:** Which OS behaviours does the guest depend on that a PC host does not
provide identically?

| Behaviour | Guest expectation | Host difference | Impact |
| --- | --- | --- | --- |
| Virtual memory layout | _unknown_ | _unknown_ | |
| Executable memory permissions | _unknown_ | _unknown_ | |
| Thread priorities and affinity | _unknown_ | _unknown_ | |
| Timing and clocks | _unknown_ | _unknown_ | |
| Synchronisation primitives | _unknown_ | _unknown_ | |
| Signal / exception handling | _unknown_ | _unknown_ | |

## 4. Filesystem and mount points

**Question:** Which mount points does the guest use, and what semantics does it
expect from them?

| Mount point | Purpose | Read/write | Host mapping candidate |
| --- | --- | --- | --- |
| `/app0` | _unknown_ | _unknown_ | Game install directory |
| `/data` | _unknown_ | _unknown_ | _unknown_ |
| `/user` | _unknown_ | _unknown_ | User profile directory |
| _others_ | | | |

Note: `DriveMap` / `windows_to_posix` in `src/path.cpp` handle **host** paths
only. Guest mount-point translation is a separate subsystem and is not
implemented.

Open questions:

- Does the guest rely on case-insensitive lookups, or on exact names?
- Does it expect POSIX permissions, ownership, or read-only mounts to behave in a
  particular way?

## 5. Graphics

**Question:** What graphics interface does the guest use, and what is the
translation target?

| Field | Value |
| --- | --- |
| API family | _unknown_ |
| Command buffer format | _unknown_ |
| Shader format | _unknown_ |
| Synchronisation model | _unknown_ |
| Translation target | Vulkan or D3D12 (undecided) |

Findings: none recorded.

Open questions:

- Is a command-stream translation layer sufficient, or is a higher-level
  interception point available?
- What is the cost of translating shaders ahead of time versus at load?

## 6. Audio

| Field | Value |
| --- | --- |
| Output API | _unknown_ |
| Channel / format expectations | _unknown_ |
| 3D audio usage | _unknown_ |
| Host backends | WASAPI (Windows), PipeWire/ALSA (Linux) — candidates |

## 7. Input

| Field | Value |
| --- | --- |
| Input API | _unknown_ |
| Device features used (haptics, adaptive triggers) | _unknown_ |
| Host backends | XInput / Raw Input (Windows), evdev (Linux) — candidates |

## 8. Networking and online services

**Question:** Does the guest require network services, and are they in scope?

Findings: none recorded. Note that online services may be out of scope by design;
record that decision here if so.

## 9. Protection and entitlements

**Question:** Which protection mechanisms exist, and do they block translation?

Record only whether a mechanism exists and what it requires. Do not document
bypass techniques, and do not include keys or entitlement data.

## 10. Compatibility obstacles

| Obstacle | Category | Severity | Blocking | Evidence |
| --- | --- | --- | --- | --- |
| _none recorded_ | | | | |

## 11. Library-to-host mapping

One row per library, filled in as designs are decided.

| Guest library | Host implementation | Fidelity | Notes |
| --- | --- | --- | --- |
| _none recorded_ | | | |

## 12. Feasibility conclusions

- What is the minimum library set for a first frame? _unknown_
- Is command-stream graphics translation viable? _unknown_
- Can guest memory and threading be delegated to the host? _unknown_
- Which parts must be reimplemented rather than delegated? _unknown_
- Is the project blocked by entitlements or encryption? _unknown_

## Risk register

| Risk | Likelihood | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- |
| No legitimate research material available | High | High | Keep work scoped to portable code; mark rest **Blocked** | Open |
| Encryption or entitlements block loading | Unknown | High | Establish early; do not bypass | Open |
| Graphics translation is infeasible or too slow | Medium | High | Prototype the command stream early | Open |
| Undocumented behaviour is misread, causing subtle bugs | High | Medium | Require reproducible evidence; test per library | Open |
| Legal exposure from research inputs | Medium | High | Enforce the DMCA-avoidance policy in `CONTRIBUTE.md` | Open |

## Open questions

1. _none recorded_

## Changelog

| Date | Change | Author |
| --- | --- | --- |
| 2026-11-20 | Template created | — |
| 2026-11-20 | Reworked for PS5-to-PC library translation (ADR 0002) | — |
