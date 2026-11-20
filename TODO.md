# Project Roadmap

This document tracks the development of the GTA VI Translation Layer, from
initial research and technical investigation through implementation, testing, and
release.

Tasks will be updated as development progresses.

An item is checked only when the implementation is committed and its tests pass.
See [docs/build.md](docs/build.md) for building and running the test suite.

## Phase 1: Research & Feasibility

Understand the PS5 build's requirements and determine what the translation layer
must provide. See [docs/research/phase-1-research-report.md](docs/research/phase-1-research-report.md)
for the evidence standard and the report itself.

### Guest Architecture Research

- [ ] Identify the PS5 executable container and module format.
- [ ] Determine how the entry module is loaded and what the entry point expects.
- [ ] Enumerate imported libraries and symbols.
- [ ] Identify lazily loaded libraries that a static import table does not show.
- [ ] Research guest memory layout and allocation behaviour.
- [ ] Research threading, scheduling, and synchronisation behaviour.
- [ ] Research filesystem layout and mount-point semantics.
- [ ] Research graphics requirements (command buffers, shaders, synchronisation).
- [ ] Research audio output requirements.
- [ ] Research input device requirements.
- [ ] Research networking and online service dependencies.
- [ ] Investigate protection, encryption, and entitlement requirements.
- [ ] Identify potential compatibility obstacles.

### Host & Translation Research

- [ ] Map each imported library to a host implementation strategy.
- [ ] Review publicly documented behaviour of comparable translation projects for
      findings. Do not copy code unless its licence permits it.
- [ ] Identify behaviour that cannot be translated faithfully.
- [ ] Evaluate graphics translation targets (Vulkan, Direct3D 12).
- [ ] Evaluate Windows and Linux host capability differences.

### Technical Feasibility

- [ ] Determine the minimum library set required to reach a first frame.
- [ ] Establish whether loading is possible without prohibited material.
- [ ] Document technical limitations and risks.
- [ ] Produce the initial research report.

## Phase 2: Architecture & Design

Define the project's architecture before implementing the core components.

- [ ] Finalize the subsystem architecture.
- [ ] Define the loader interface and entry contract.
- [ ] Define the library dispatch interface.
- [ ] Design guest mount-point translation.
- [ ] Design the graphics translation subsystem.
- [ ] Design the audio subsystem.
- [ ] Design the input subsystem.
- [ ] Design the memory and threading compatibility layer.
- [x] Define error handling and logging standards. (`gtavi/error.h`, `gtavi/log.h`)
- [x] Establish cross-platform coding conventions. (`.clang-format`, `.editorconfig`)
- [x] Select supported C++ standard. (C++20)
- [x] Configure CMake build system.
- [x] Document architectural decisions. (ADR 0002, accepted)

## Phase 3: Development Environment

Prepare the development infrastructure.

- [x] Set up the CMake project structure.
- [x] Configure Windows development builds. (MSVC 19.51, verified locally)
- [x] Configure Linux development builds. (CI: GCC and Clang)
- [x] Set up automated compilation.
- [ ] Configure static analysis and formatting. (formatting configured; static analysis pending)
- [x] Integrate unit testing. (`tests/`, CTest, 53 cases)
- [x] Configure CI workflows. (`.github/workflows/ci.yml`)
- [x] Establish debugging and diagnostic tooling. (`gtavi-probe`)
- [x] Create development documentation. (`docs/build.md`)

## Phase 4: Core Implementation

Implement the foundational translation layer.

### Core Runtime

- [ ] Implement the loader.
- [ ] Implement import resolution and the dispatch table.
- [ ] Implement module initialization and shutdown.
- [ ] Implement configuration management.
- [x] Implement structured logging. (`gtavi/log.h`)
- [x] Implement error handling. (`gtavi/error.h`)
- [x] Implement runtime diagnostics. (`gtavi-probe`)

### Filesystem

- [ ] Implement the guest filesystem abstraction.
- [ ] Implement guest mount-point mapping (`/app0`, `/data`, `/user`, ...).
- [x] Implement host path translation. (`gtavi/path.h`, host-side only)
- [x] Handle host drive letters and mount points. (`DriveMap`, C: -> /mnt/c)
- [ ] Implement file access compatibility.
- [ ] Implement directory and metadata handling.
- [ ] Handle permissions and access control differences.
- [ ] Implement file operation testing.

### Memory & Processes

- [ ] Research and implement required memory compatibility mechanisms.
- [ ] Investigate virtual memory behaviour differences.
- [ ] Implement process and thread management interfaces.
- [ ] Handle thread creation and synchronisation.
- [ ] Implement required runtime compatibility mechanisms.

### Translated Libraries

- [ ] Implement the library module template and registration.
- [ ] Implement the highest-priority libraries from the import table.
- [ ] Add per-library tests.

## Phase 5: Host Platform Compatibility

Implement host-specific integrations and the dispatch mechanism.

### Windows

- [x] Implement Windows platform detection. (`gtavi/platform.h`)
- [ ] Implement Windows-specific host interfaces.
- [x] Establish Windows build and testing pipeline. (CI: MSVC)
- [ ] Verify behaviour against native Windows APIs.

### Linux

- [x] Implement Linux platform detection. (`gtavi/platform.h`)
- [ ] Implement POSIX host interfaces.
- [ ] Implement Linux-specific system integrations.
- [x] Establish Linux build and testing pipeline. (CI: GCC, Clang)
- [ ] Verify behaviour against native Linux interfaces.

### Library Dispatch

- [ ] Implement symbol resolution with clear errors for missing imports.
- [ ] Implement stub reporting for unimplemented symbols.
- [ ] Test dispatch against a table-driven harness.

## Phase 6: Graphics, Audio & Input

Implement the guest's major subsystems.

### Graphics

- [ ] Identify the command buffer and shader formats.
- [ ] Prototype command-stream translation.
- [ ] Evaluate translation targets (Vulkan, Direct3D 12).
- [ ] Implement the graphics interface.
- [ ] Test rendering correctness.
- [ ] Investigate performance overhead.

### Audio

- [ ] Identify audio output requirements.
- [ ] Implement audio output for Windows and Linux hosts.
- [ ] Test device handling and format conversion.

### Input

- [ ] Implement controller input.
- [ ] Implement haptics and adaptive triggers where feasible.
- [ ] Test input behaviour.

## Phase 7: Integration & Compatibility

Bring the individual components together.

- [ ] Integrate the translation subsystems.
- [ ] Implement runtime initialization.
- [ ] Implement dependency detection.
- [ ] Establish a game installation detection mechanism.
- [ ] Implement diagnostic reporting.
- [ ] Test individual subsystems against the guest.
- [ ] Test game startup.
- [ ] Investigate and resolve compatibility failures.
- [ ] Document known limitations.

## Phase 8: Testing & Optimization

Ensure correctness, stability, and acceptable performance.

- [ ] Expand unit test coverage.
- [ ] Add integration tests.
- [ ] Add regression tests.
- [ ] Test supported Windows versions.
- [ ] Test supported Linux distributions.
- [ ] Investigate memory leaks.
- [ ] Profile CPU and memory usage.
- [ ] Profile translation overhead.
- [ ] Optimize performance bottlenecks.
- [ ] Test long-running stability.
- [ ] Document hardware and software requirements.

## Phase 9: Documentation & Release Preparation

Prepare the project for public use.

- [ ] Write installation documentation.
- [ ] Write configuration documentation.
- [ ] Document supported platforms.
- [ ] Document known limitations.
- [ ] Publish build instructions.
- [ ] Finalize contribution guidelines.
- [ ] Finalize licensing.
- [ ] Prepare release binaries where appropriate.
- [ ] Establish versioning conventions.
- [ ] Create release notes.
- [ ] Prepare the first public release.

## Phase 10: Post-Release Development

Continue improving compatibility and supporting contributors.

- [ ] Collect community bug reports.
- [ ] Investigate compatibility reports.
- [ ] Expand library coverage.
- [ ] Improve hardware compatibility.
- [ ] Address performance issues.
- [ ] Expand automated testing.
- [ ] Maintain compatibility documentation.
- [ ] Review and prioritize community contributions.

---

## Development Principles

1. Research before implementing undocumented behavior.
2. Prioritize correctness and stability over premature optimization.
3. Keep platform-specific code isolated.
4. Avoid unnecessary dependencies.
5. Prefer existing, well-tested compatibility technologies where appropriate.
6. Document technical decisions and implementation limitations.
7. Never claim compatibility without reproducible testing.
8. Never bypass protection mechanisms. If running the guest requires material the
   project cannot legitimately obtain, document the limitation instead.

**Note:** This roadmap is a development plan, not a statement that every listed capability is currently feasible or implemented. Tasks may be revised as research reveals the actual requirements.
