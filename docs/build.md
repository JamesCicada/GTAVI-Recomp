# Building and testing

## Requirements

- CMake 3.21 or newer
- A C++20 compiler: MSVC 19.3x+, GCC 11+, or Clang 14+
- Ninja (recommended; used by the presets) or any generator CMake supports

No third-party libraries are required. The core library and the test suite use
only the C++ standard library.

## Windows

The quickest path is the helper script. It finds `vcvars64.bat` with `vswhere`,
so it works with any Visual Studio edition or the Build Tools, from any shell:

```bat
scripts\build-windows.bat              :: Release
scripts\build-windows.bat Debug        :: Debug
scripts\build-windows.bat Debug --clean
```

It configures with `-DGTAVI_WARNINGS_AS_ERRORS=ON`, so warnings fail locally the
same way they do in CI. It leaves the caller's environment unchanged.

To build with Ninja manually, open the [x64 Native Tools Command Prompt for VS](https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line#developer_command_prompt_shortcuts)
from the Start menu. To use PowerShell, start `powershell` from that prompt so it
inherits the MSVC compiler and SDK environment. In either shell, change to the
repository root and run the following commands.

```powershell
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build --output-on-failure
```

From a plain PowerShell session, CMake can select the installed Visual Studio
generator. Use a separate build directory so CMake can keep both generators'
settings.

```powershell
cmake -S . -B build/vs -A x64
cmake --build build/vs --config Debug
ctest --test-dir build/vs -C Debug --output-on-failure
```

### Building the pinned AnyPS5 runtime on Windows

AnyPS5 uses its own CMake project and an x86-64 MinGW-w64 GCC toolchain. Start
from a short checkout path such as `C:\g`, with WinLibs GCC 15.2.0 (POSIX
threads, UCRT, r7), Ninja, CMake and Python on `PATH`. For toolchain setup and
the FFmpeg package used during configuration, see the [pinned AnyPS5 build
guide](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/docs/dev/BUILD.md#windows-setup-and-troubleshooting).

Run these commands from the GTAVI-Recomp root in PowerShell.

```powershell
git submodule update --init --recursive third_party/AnyPS5
cmake -S third_party/AnyPS5 -B build/a5 -G Ninja -DCMAKE_BUILD_TYPE=Release `
  -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DBUILD_TESTING=ON
cmake --build build/a5 --parallel 6
cmake --build build/a5 --target libs --parallel 6
$tests = '^(input_magic|file_identity|guest_filesystem|guest_file_timestamps|guest_file_vector)$'
ctest --test-dir build/a5 -R $tests --no-tests=error --output-on-failure
```

At AnyPS5 commit `1582613`, a Release build on Windows x64 (NT 10.0.26100)
with that toolchain, CMake 4.3.1, Ninja 1.13.2 and Python 3.14.3 produced
413 patched `.prx` files in `build/a5/core/libs/libs`. All five selected tests
passed using relinker and filesystem fixtures. Game compatibility remains
untested.

## Linux

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build --output-on-failure
```

## Presets

`CMakePresets.json` defines `debug`, `release`, and `ci`:

```bash
cmake --preset debug
cmake --build --preset debug
ctest --preset debug
```

The `ci` preset enables `-DGTAVI_WARNINGS_AS_ERRORS=ON`, matching the workflow in
`.github/workflows/ci.yml`. Builds must be warning-free with that setting.

## Static analysis

The Linux Clang job runs clang-tidy while compiling the core library, probe and
tests. Enabled checks detect errors such as dangling string views and uses of
moved-from objects. Diagnostics fail the build. See [`.clang-tidy`](../.clang-tidy).

With Clang, clang-tidy and Ninja installed, run the same checks on Linux with
these commands.

```bash
CXX=clang++ cmake --preset ci -B build/tidy -DCMAKE_CXX_CLANG_TIDY=clang-tidy
cmake --build build/tidy
ctest --test-dir build/tidy --output-on-failure
```

After changing only `.clang-tidy`, use `cmake --build build/tidy --clean-first`
to recheck every source file.

## Options

| Option | Default | Purpose |
| --- | --- | --- |
| `GTAVI_BUILD_TESTS` | `ON` | Build the unit test suite |
| `GTAVI_BUILD_TOOLS` | `ON` | Build `gtavi-probe` |
| `GTAVI_WARNINGS_AS_ERRORS` | `OFF` | Treat warnings as errors |

## Running the diagnostic tool

`gtavi-probe` prints host information and exercises path translation. After the
manual Ninja build, run `./build/tools/gtavi_probe` from the repository root
in Bash or PowerShell. With the Visual Studio Debug build, use
`.\build\vs\tools\Debug\gtavi_probe.exe`. For a preset or the Windows helper,
look under its build directory (for example, `build/ci` or `build/windows`).
Ninja places the executable in `tools/` and Visual Studio in
`tools/<configuration>/`.

```console
$ ./build/tools/gtavi_probe --to-posix "C:\Games\GTA VI\data" --to-windows /mnt/c/Games
gtavi-probe 0.1.0
platform:     windows
os version:   10.0.26200
architecture: x86_64
C:\Games\GTA VI\data -> /mnt/c/Games/GTA VI/data
/mnt/c/Games -> C:\Games
```

Use the repeatable `--mount` option to override a drive's default mount point.
The first override for each drive applies to every translation in the command.

```console
./build/tools/gtavi_probe --mount D:/games --to-posix "D:\PS5\app0" --to-windows /games/PS5/app0
```

Include its output when reporting platform-specific bugs.

## Checking a PS5 application directory

Python 3.11 or newer can check the readable input files before you run the relinker:

```console
python scripts/check_app0.py /path/to/app0 --title-id PPSA99999 --content-version 01.000.000
```

Use the application's own `sce_sys/param.json` and a readable ELF at `eboot.bin`.
Identity flags are optional. Use `--content-id` to distinguish packages that
share a title ID and version. Repeat `--module example.prx` to check explicitly named
shared modules under `sce_module/` in the same application directory. The JSON
report includes file hashes for valid inputs
and reports separate errors for missing or malformed files. The tool reads the
files in place. Passing the check confirms their structure and any requested
identity fields. Relinking and execution require further verification.

Run the generated-fixture tests with `python -I tests/test_check_app0.py`.

## Layout

```text
include/gtavi/      public headers
src/                portable implementation
src/platform/       per-OS implementation, selected by CMake only
tools/probe/        gtavi-probe diagnostic front end
tests/              unit tests and the minimal test framework
scripts/            helper build scripts
docs/               build notes, ADRs, research
cmake/              shared build configuration
```

Only `src/platform/` may contain OS-specific code. Everything else must compile
on both Windows and Linux, which the CI matrix enforces.

## Adding a test

Tests use a small in-repo framework, so no dependency is needed:

```cpp
#include "test_framework.h"

GTAVI_TEST(descriptive_name) {
    CHECK_TRUE(some_condition);
    CHECK_EQ(actual, expected);
}
```

Add the file to `tests/CMakeLists.txt`; registration is automatic.
