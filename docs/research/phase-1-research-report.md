# Phase 1 Research Report

- **Status:** Template — no findings recorded yet
- **Owner:** unassigned
- **Last updated:** 2026-11-20

This document is the deliverable for Phase 1 of `TODO.md`. It records what has
been *observed* about GTA VI and the host platforms, not what is assumed.

Every section is filled in the same way. Delete the guidance lines as sections
are completed; do not delete a section because it is empty — an empty section
is an honest statement that nothing is known yet.

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

A claim may only move to **Confirmed** when another contributor can reproduce
it. Per `TODO.md` principle 7, no compatibility claim is made from anything less.

### Finding block

```text
Finding:      <one sentence>
Evidence:     <commands, tool output, document section, or file hash>
Reproduction: <exact steps, or "n/a" for external sources>
Confidence:   Confirmed | Reported | Hypothesis | Unverified | Blocked
Implication:  <what this means for the translation layer>
```

## Legal and ethical constraints

- Do not include game files, assets, or decompiled code in this repository or in
  this report.
- Do not include material from leaks. If a finding can only be supported by
  leaked material, record it as **Blocked** and stop.
- Record *behaviour* and *interface facts*, not copyrighted content.
- Reverse engineering must comply with applicable law; see `CONTRIBUTE.md`.

---

## 1. Executable format and binary structure

**Question:** What format is the game executable, what is its architecture, and
how is it loaded?

| Field | Value |
| --- | --- |
| Format | _unknown_ |
| Architecture | _unknown_ |
| Loader | _unknown_ |
| Observed with | _nothing yet_ |

Findings: none recorded.

Open questions:

- Is the executable packed or protected in a way that prevents inspection?
- Does it rely on a launcher process, or is it self-contained?

## 2. Dependencies and runtime requirements

**Question:** Which libraries and runtime components must exist for the game to
start?

| Dependency | Kind | Required at startup | Evidence |
| --- | --- | --- | --- |
| _none recorded_ | | | |

## 3. Windows-specific APIs and system interactions

**Question:** Which Windows interfaces does the game actually call?

Record the category and observed usage. Do not paste disassembly.

| Category | Examples | Observed | Notes |
| --- | --- | --- | --- |
| Filesystem | `CreateFileW`, `ReadFile` | _unknown_ | |
| Memory | `VirtualAlloc`, `VirtualProtect` | _unknown_ | |
| Threading | `CreateThread`, `WaitForSingleObject` | _unknown_ | |
| Synchronisation | `CreateEventW`, `CRITICAL_SECTION` | _unknown_ | |
| Registry | `RegOpenKeyExW` | _unknown_ | |
| Networking | `WSAStartup`, sockets | _unknown_ | |
| Graphics | D3D12, DXGI | _unknown_ | |
| Audio | XAudio2, WASAPI | _unknown_ | |
| Input | Raw Input, XInput | _unknown_ | |

## 4. Filesystem access patterns and file formats

**Question:** How does the game address its data, and in what formats?

| Field | Value |
| --- | --- |
| Container formats | _unknown_ |
| Path conventions | _unknown_ |
| Case sensitivity expectations | _unknown_ |
| Long path handling | _unknown_ |

Note: the translation layer's `windows_to_posix` currently assumes drive-letter
paths and rejects UNC, device, and root-relative paths. Any confirmed use of
those forms is a direct requirement on `src/path.cpp`.

## 5. Memory management and process behaviour

**Question:** What memory model does the game assume, and which behaviours
differ between Windows and Linux?

| Behaviour | Windows assumption | Linux difference | Impact |
| --- | --- | --- | --- |
| Address space layout | _unknown_ | _unknown_ | |
| Executable memory | _unknown_ | _unknown_ | |
| Large pages | _unknown_ | _unknown_ | |
| Process creation | _unknown_ | _unknown_ | |

## 6. Windows services and runtime components

**Question:** Does the game depend on services, COM components, or redistributables?

Findings: none recorded.

## 7. Graphics, audio, input, and networking

**Question:** Which APIs and versions are used, and what are the existing
translation options?

| Subsystem | API and version | Translation candidate | Evidence |
| --- | --- | --- | --- |
| Graphics | _unknown_ | DXVK / VKD3D-Proton (candidate) | |
| Audio | _unknown_ | _unknown_ | |
| Input | _unknown_ | _unknown_ | |
| Networking | _unknown_ | _unknown_ | |

## 8. DRM, launcher, and anti-cheat

**Question:** Which protection mechanisms exist, and do they block translation?

Findings: none recorded. Record only whether a mechanism exists and what it
requires; do not document bypass techniques.

## 9. Compatibility obstacles

| Obstacle | Category | Severity | Blocking | Evidence |
| --- | --- | --- | --- | --- |
| _none recorded_ | | | | |

## 10. Windows-to-Linux mapping

| Windows facility | Linux equivalent | Fidelity | Notes |
| --- | --- | --- | --- |
| Drive letters | mount points | Partial | Implemented in `DriveMap` |
| Path separators | `/` | Full | Implemented |
| UNC paths | _undecided_ | None | Rejected by `windows_to_posix` |
| Case-insensitive names | case-sensitive | Low | Requires lookup or overlay |

## 11. Feasibility conclusions

- Is file translation alone sufficient for any component? _unknown_
- Is API translation required? _unknown_
- Is a standalone runtime feasible? _unknown_
- Which parts must delegate to existing compatibility technology? _unknown_

## Risk register

| Risk | Likelihood | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- |
| No access to a legitimate installation for inspection | High | High | Keep research scoped to public information; mark rest **Blocked** | Open |
| Anti-cheat or DRM blocks translation | Unknown | High | Identify early, document, do not bypass | Open |
| Graphics translation performance is unacceptable | Medium | Medium | Measure before committing to an architecture | Open |

## Open questions

1. _none recorded_

## Changelog

| Date | Change | Author |
| --- | --- | --- |
| 2026-11-20 | Template created | — |
