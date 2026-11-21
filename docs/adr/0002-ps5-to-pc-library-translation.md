# ADR 0002: PS5-to-PC library translation

- **Status:** Superseded by [ADR 0003](0003-build-on-anyps5-relinker.md)
- **Date:** 2026-11-20
- **Deciders:** project maintainer
- **Supersedes:** [ADR 0001](0001-project-scope.md)
- **Related:** `README.md`, `TODO.md`, `docs/research/phase-1-research-report.md`

## Context

The project targets the **PlayStation 5 build** of Grand Theft Auto VI running
natively on PC.

The maintainer's stated approach is **library-level translation**, in the manner
of AnyPS5: the game's own executable is loaded and run, and the calls it makes
into the PS5 platform are served by native implementations on the host. The game
is not recompiled, and instructions are not emulated individually.

ADR 0001 assumed the input was a Windows build and the output a Linux port. That
premise was incorrect, so this ADR replaces it.

Terminology used below:

- **Guest** — the PS5 build: the executable, its data, and the platform it
  expects.
- **Host** — the PC running the layer: Windows or Linux.
- **Translated library** — one PS5 system library (commonly named `libSce*`),
  implemented by this project for the host.

## Decision

1. The guest is the PS5 build. The host is a PC running Windows or Linux.
2. The technique is library translation: imported libraries and symbols are
   intercepted and resolved against this project's implementations.
3. The shipped executable runs unmodified wherever a faithful library
   implementation is possible. Patching the game is a fallback, not the design.
4. Portable code is shared; host-specific code is isolated to `src/platform/`
   and to per-subsystem host backends.
5. The repository never contains Sony code, SDK material, system files,
   decryption keys, entitlements, game content, or extracted assets.

## What this implies

- **Loader.** Something must parse the executable container, map its segments,
  resolve its imports, apply relocations, and transfer control to the entry
  point.
- **Dispatch.** A mapping from (library, symbol) to a native function pointer is
  the core mechanism. It must be table-driven and testable without the game.
- **Per-library modules.** Each translated library is an independent module with
  its own tests, so contributors can work in parallel.
- **Host abstraction.** Filesystem, memory, threads, timing, graphics, audio, and
  input each need a host-facing interface with Windows and Linux backends.
- **Two kinds of path translation.** Host paths (already implemented as
  `DriveMap` / `windows_to_posix`) are *not* the main problem. Guest mount points
  such as `/app0`, `/data`, and `/user` must be mapped onto host directories, and
  that is a separate, unimplemented subsystem.

## Consequences

**Positive**

- Work is incremental and testable per library; no single milestone blocks
  everything.
- Host-native APIs are used directly, so there is no per-instruction translation
  cost.
- No derived binaries or Sony material need to be distributed.

**Negative**

- Correctness depends on undocumented platform behaviour, which must be
  researched and verified before implementation.
- Graphics translation is the highest-risk subsystem and may dominate the
  schedule.
- Performance under translation is unknown until measured.
- Research inputs are constrained by the DMCA-avoidance policy, which may stall
  Phase 1.

**Neutral**

- The existing scaffolding (build system, `Error`/`Result`, logging, host path
  translation, `gtavi-probe`) remains valid and is a usable first slice.

## Open questions

1. What is the executable container format, and does loading it require
   entitlements or keys the project cannot legitimately obtain?
2. Which graphics path is viable: translating the low-level command stream, or
   targeting a higher-level interface?
3. Which host comes first — Windows, Linux, or both in parallel?
4. How much guest OS behaviour (memory layout, thread priorities, timing) can be
   delegated to the host, and how much must be emulated in the layer?
5. What is the minimum set of libraries required to reach a first frame?

## Follow-ups

- [ ] Enumerate the guest's imports once research material is available.
- [ ] Define the loader interface (`src/loader/`, planned).
- [ ] Define the dispatch interface (`src/libraries/`, planned).
- [ ] Design guest mount-point translation.
- [ ] Record the answers to the open questions above as they are resolved.
