# Related projects

- **Last reviewed:** 2026-11-23
- **Related:** [ADR 0003](../adr/0003-build-on-anyps5-relinker.md),
  [limitations-and-risks.md](limitations-and-risks.md), [CONTRIBUTE.md](../../CONTRIBUTE.md)

Other projects working on the same platform or the same game, and what this
project may take from each. This repository is **GPL-2.0-only**, so the licence
decides what can be reused.

## Rules for every entry

1. **Facts, not code.** A documented format, interface or measured behaviour
   can be learned from and implemented independently, in our own words and
   code, with the source cited. Code, comments and tables are copied only when
   the project's licence is compatible with GPL-2.0-only, and its copyright and
   licence notices are kept.
2. **GPLv3 code is incompatible.** Code under GPL-3.0 (only or "or later")
   cannot be combined into a GPL-2.0-only project. There is no exception for a
   single file or a small function.
3. **No licence means no permission.** A repository without a licence keeps all
   rights with its authors; read it, but do not copy from it.
4. **No game-derived material.** This project does not work from game files
   ([README](../../README.md), ADR 0003). Some projects below do. Their findings
   about **GTA VI itself** (its imports, shaders, archives, assets or content)
   were measured from game files and are not used here unless the maintainer
   decides otherwise. Their findings about public formats or hardware may be
   used under rule 1, verified against a public source where possible.
5. **Keep a clear separation.** Do not link to game-derived material, generated
   assets or converted builds from this repository or its Discord.

## Summary

| Project | Target | Licence | Code reuse here | Status (as reviewed) |
| --- | --- | --- | --- | --- |
| [AnyPS5](https://github.com/boykopovar/AnyPS5) | Any PS5 title | GPL-2.0-only | **Yes**: the foundation, as a submodule | Relinker, 413 libraries, shader recompiler; one title playable |
| [americas-recomp](https://github.com/realdody/americas-recomp) | GTA VI, Xbox Series | GPL-2.0 (see below) | Possibly, after confirming the licence | AnyPS5 fork with an `xbox-series` branch |
| [Leonida](https://github.com/ItsNotRexed/Leonida) | GTA VI, Xbox Series | GPL-3.0-or-later | **No** | Does not boot; shader, asset and loader tooling |

## AnyPS5

<https://github.com/boykopovar/AnyPS5>

The project this one builds on (ADR 0003). It converts a PS5 executable into a
native Windows or Linux program, links it against its own implementations of
the PS5 system libraries, and recompiles PS5 GPU shaders to SPIR-V for Vulkan.

- **Licence:** GPL-2.0-only, the same as this project. Its code is used
  directly, through the submodule in `third_party/AnyPS5`.
- **Relationship:** work that any PS5 title could use goes upstream to AnyPS5;
  this repository keeps what is specific to GTA VI.
- **Progress:** measured by its own tool and shown on the
  [progress page](https://jamescicada.github.io/GTAVI-Recomp/).

## americas-recomp

<https://github.com/realdody/americas-recomp>

A fork of AnyPS5 working on the **Xbox Series** build of GTA VI, on its
`xbox-series` branch. According to Leonida's related-projects page, it
recompiles the Xbox Series shaders and has run the game package's DLLs against
a PC Direct3D 12 device behind an Xbox interface layer.

- **Licence:** GitHub reports GPL-2.0, and Leonida describes it as
  GPL-2.0-only, inherited from AnyPS5. If that holds, its code is compatible
  with this project. Confirm the licence of the specific files before reusing
  anything.
- **Caveat:** it works from the Xbox game package, so rule 4 applies to its
  findings about the game.
- **Why it matters:** if this project ever reconsiders the Xbox build, this is
  the closest licence-compatible starting point. It also exercises AnyPS5's
  shader recompiler on GTA VI-scale shaders, so fixes made there may be worth
  following upstream.

## Leonida

<https://github.com/ItsNotRexed/Leonida>

A project to run the **Xbox Series** build of GTA VI on Windows. Despite calling
itself a recompilation, it works like AnyPS5: the game's x86-64 code is loaded
and run directly, Xbox system libraries are replaced by its own implementations,
and Xbox Direct3D 12 and RDNA2 shaders are translated to Vulkan and SPIR-V.

- **Licence:** GPL-3.0-or-later. **No code may be copied into this project**
  (rule 2). Its own documentation draws the same line in the other direction for
  GPL-2.0-only code.
- **Status, from its README:** the game does not boot, because the executable is
  missing from the package its developers have. It reports translating every
  shader in the Xbox package to SPIR-V, exporting models, textures and audio,
  a loader with Xbox system-library replacements that runs a stand-in
  executable, and Direct3D 12 → Vulkan and ray-tracing work in progress.
- **Caveat:** it works directly from the game package and documents the game's
  archives and content, so rule 4 applies to its findings about the game. It is
  very visible, uses a GTA VI icon as its logo, and is an obvious takedown
  target; keep this project separate from it (rule 5).
- **Possibly relevant to the PS5 build (Hypothesis):** both consoles use AMD
  RDNA2-family GPUs, and Leonida reports that most of GTA VI's Xbox shaders run
  in AMD's 64-lane wave mode (wave64). If the PS5 build is similar, AnyPS5's
  shader recompiler will need solid wave64 support, including emulation on
  NVIDIA and Intel GPUs, which run 32-lane groups. This is an inference about
  hardware behaviour, not a measurement of the PS5 build, and it rests on a
  game-derived count (rule 4), so treat it as a question to check in AnyPS5,
  not as a fact.

## Other prior art

- **bbport** (Bloodborne on PC): the model this project follows, a runtime for a
  single game built on a general project (shadPS4). Its licence has not been
  reviewed here.
- **shadPS4** (PS4 emulator): GPL-licensed; its exact licence version has not
  been reviewed here, so check it before relying on rule 1 or 2 for it.

## Keeping this page current

Add a project when it becomes relevant, with its licence as GitHub reports it
and as its own files state, and re-review entries when their licence or status
changes. Statuses here are as reviewed on the date at the top and come from each
project's own documentation, not from running it.
