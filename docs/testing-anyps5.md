# Testing pinned AnyPS5 libraries

The fixtures use generated files, draw commands, PCM samples and scripted
controller input. Each group can be built separately. The commands below were
verified at AnyPS5 `1582613` on Windows x64 (MinGW-w64 GCC 15.2) and Ubuntu
24.04 (GCC 14.2), with host-specific cases indicated below.

Start with the [AnyPS5 full-build prerequisites](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/docs/dev/BUILD.md#requirements).
On Windows, use a short checkout path with x86-64 MinGW-w64 GCC on `PATH`.
On Ubuntu 24.04, use `gcc-14` and `g++-14` for the two compiler settings below
to reproduce the tested build. Run the configuration from the GTAVI-Recomp root.

```console
git submodule update --init --recursive third_party/AnyPS5
cmake -S third_party/AnyPS5 -B build/a5 -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DBUILD_TESTING=ON
```

## Loading all runtime libraries

To check that the host can load the runtime libraries and their dependencies,
build the loader test. Its target also builds and patches all the system libraries.

```console
cmake --build build/a5 --parallel 4 --target patched_libraries_tests
ctest --test-dir build/a5 -R "^patched_libraries$" --no-tests=error --verbose
```

The test opens each `.prx` in `build/a5/core/libs/libs` using `LoadLibraryExW`
on Windows or `dlopen` with immediate symbol resolution on Linux. On Windows
x64 and Ubuntu 24.04 x64, the Release builds produced 413 files matching the
413 source directories in `core/libs/prx` at `1582613`. Both hosts reported
`413 patched libraries loaded, 0 failed`. [Ubuntu build and load test](https://github.com/RavenCurseBurg/GTAVI-Recomp/actions/runs/45692207079/job/139480310616)

## Filesystem

Three tests exercise file and directory operations, timestamps and vectored I/O.
Six more exercise download-data mounts using generated application directories.

```console
cmake --build build/a5 --parallel 4 --target guest_filesystem_tests guest_file_timestamp_tests guest_file_vector_tests download_data_mount_tests
ctest --test-dir build/a5 --output-on-failure --no-tests=error -R "^(guest_filesystem|guest_file_timestamps|guest_file_vector|download_data_mount_.*)$"
```

For a Linux leak check, add `-DANYPS5_ENABLE_ASAN=ON` when configuring
AnyPS5, rebuild the four targets above, and run the same CTest command with
`ASAN_OPTIONS=detect_leaks=1`. On glibc hosts, use a version that includes
the [`freopen` fix](https://github.com/bminor/glibc/commit/9c0d6f7a1046aba111e25e34ec07242853e859dc).
On Ubuntu 24.04 with glibc `2.39-0ubuntu8.12`, LeakSanitizer reported a
472-byte allocation in the directory-reopen case of `guest_filesystem`.

On Windows, seven additional file-lock cases cover contention between threads
and processes, among other modes.

```console
cmake --build build/a5 --parallel 4 --target guest_file_lock_tests
ctest --test-dir build/a5 --output-on-failure --no-tests=error -R "^guest_file_lock_"
```

## Offscreen rendering

Five CTests check rendered output from synthetic draws. The RGB565 test reads
back packed texels from linear and tiled targets. Three color write mask tests
check which channels change. The depth test checks pixel coverage before and
after remapping the depth range.

```console
cmake --build build/a5 --parallel 4 --target agc_driver_color565_target_tests agc_driver_color_write_mask_dynamic_tests agc_driver_depth_range_remap_draw_tests
cmake -E env ANYPS5_REQUIRE_VULKAN=1 ctest --test-dir build/a5 --no-tests=error --output-on-failure -R "^agc_driver_(color565_target|color_write_mask_dynamic(_in_pipeline|_unsuppressed)?|depth_range_remap_draw)$"
```

`ANYPS5_REQUIRE_VULKAN=1` makes a missing Vulkan device fail the test. All five
tests passed on Windows x64 with a GeForce RTX 4060 and on Ubuntu 24.04 x64
with Mesa 25.2.8's llvmpipe software driver. Each run checked 68 RGB565 draws
and 28 depth-remapping cases. [Ubuntu rendering test log](https://github.com/RavenCurseBurg/GTAVI-Recomp/actions/runs/45711008085/job/139545103758)

## Audio output

Ten cases exercise default-device discovery, disconnects and retries. Seven
use simulated controller audio endpoints. Six send signed 16-bit and float
samples through the vibration path using SDL's dummy audio driver.

```console
cmake --build build/a5 --parallel 4 --target audio_out_default_open_tests audio_out_vibration_device_tests audio_out_vibration_tests
ctest --test-dir build/a5 --output-on-failure --no-tests=error -R "^(audio_out_default_open_.*|audio_out_vibration_device_.*|audio_out_vibration_(s16|f32|batch_s16|batch_f32|mono_s16|mono_f32))$"
```

Linux also has a resampling test. It checks the stereo channels and impulse
response across buffer boundaries when converting 32 kHz and 44.1 kHz to 48 kHz.

```console
cmake --build build/a5 --parallel 4 --target audio_out_resampling_tests
ctest --test-dir build/a5 --output-on-failure --no-tests=error -R "^audio_out_resampling$"
```

## Controller input

These three fixtures exercise command-file input, timed button and stick events,
and recording and replay of controller state.

```console
cmake --build build/a5 --parallel 4 --target pad_command_file_tests pad_input_script_tests pad_recording_tests
ctest --test-dir build/a5 --output-on-failure --no-tests=error -R "^(pad_command_file|pad_input_script|pad_recording)$"
```

On Windows x64, `guest_pad_recording` was also verified through the guest API.
It reads a generated replay through `scePadReadState` and checks buttons, stick
axes and triggers.

```console
cmake --build build/a5 --parallel 4 --target guest_pad_recording_tests
ctest --test-dir build/a5 --output-on-failure --no-tests=error -R "^guest_pad_recording$"
```

For controller output, the [Phase 1 input findings](research/phase-1-research-report.md#7-input)
give the two tests for adaptive-trigger commands and Bluetooth DualSense haptic reports.
