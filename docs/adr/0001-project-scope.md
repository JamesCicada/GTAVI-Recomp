# ADR 0001: Project scope — translation layer or recompilation?

- **Status:** Superseded by [ADR 0002](0002-ps5-to-pc-library-translation.md)
- **Date:** 2026-11-20
- **Deciders:** project maintainer
- **Related:** `README.md`, `TODO.md`

> **Superseded.** This ADR framed the problem as "a Windows build running on
> Linux" and did not consider that the input is the **PS5 build**. The maintainer
> confirmed the target is PS5-to-PC library translation, so the premise below is
> wrong. The record is kept for context; ADR 0002 is authoritative.

## Context

The repository is named `GTAVI-Recomp`, while `README.md` and `TODO.md` describe a
*runtime translation layer* in the style of Wine or Proton. These are different
techniques with different costs, and Phase 2 (Architecture & Design) cannot
proceed until one is chosen.

Two broad approaches exist for running Windows software on Linux:

1. **Runtime translation.** Intercept the game's calls to the operating system
   and reimplement them on the host: filesystem access, threading, memory
   management, graphics (DirectX → Vulkan), audio, input. The Windows binary is
   loaded and executed largely as shipped.
2. **Static recompilation.** Convert the shipped machine code into source or
   intermediate representation, then compile it for the target platform. The
   result is a native binary that no longer contains the original executable.

They are not mutually exclusive. A hybrid runs recompiled code on top of a
translation layer for the parts that are not recompiled.

## Options

| | A. Runtime translation | B. Static recompilation | C. Hybrid |
| --- | --- | --- | --- |
| Primary artefact | Loader + API shims | Generated native binary | Recompiled code + shims |
| Reuses Wine/Proton work | Yes | No | Partly |
| Incremental delivery | Yes, subsystem by subsystem | No, needs broad coverage first | Partly |
| Legal surface | Does not distribute derived binaries | Distributes derived binaries | Distributes derived binaries |
| Key risk | API coverage and performance | Correctness of generated code | Both |
| Effort to first runnable result | High | Very high | Very high |

## Decision

**Proposed:** adopt **A (runtime translation)** as the primary architecture, and
keep **B** as a Phase 1 research question rather than an implementation target.

Rationale:

- It matches what `README.md` and `TODO.md` already describe.
- Development principle 5 asks us to prefer existing, well-tested compatibility
  technology; A can build on Wine/Proton and DXVK/VKD3D instead of replacing them.
- A can be delivered incrementally and tested per subsystem, which suits a
  community project with no confirmed schedule.
- B distributes artefacts derived from the game executable, which is a legal and
  practical burden the project has not agreed to carry.

This is a proposal, not a decision. Per `CONTRIBUTE.md`, changes that affect
project-wide interfaces should be discussed before implementation, and the
architecture is such a change.

## Consequences

**Positive**

- Phase 2 can proceed with concrete subsystem boundaries.
- The existing scaffolding (`gtavi_core`, path translation, diagnostics) is a
  first slice of the runtime layer and stays relevant.
- Contributors can work on independent subsystems without a full pipeline.

**Negative**

- The repository name suggests B. If A is adopted, the name either needs to
  change or `README.md` must state the intent explicitly to avoid misleading
  contributors.
- Runtime translation inherits the limitations of Wine/Proton, including
  anti-cheat and DRM interactions we cannot resolve.

**Neutral**

- Research into the binary format is still required under either option, so
  Phase 1 is not wasted work.

## Open questions

1. Is the target "run the Windows build on Linux", or "produce a native Linux
   build"? The answer changes how much of the layer is translation versus
   reimplementation.
2. Does the project intend to distribute binaries, or only source and
   instructions?
3. Is Windows support a compatibility target (the game already runs there) or
   only a reference platform for testing Linux behaviour?

## Follow-ups

- [ ] Maintainer decision recorded here.
- [ ] `README.md` updated to state the chosen approach in the first paragraph.
- [ ] If A: rename the repository or add an explicit note about the name.
- [ ] If B: replace this ADR with a recompilation-focused one and revise
      `TODO.md` Phases 4–6.
