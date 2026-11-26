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

## Guest clocks

The guest POSIX and Sce kernel interfaces each returned 1,000 consecutive
nondecreasing monotonic readings. The fixture also checks that libc++
`system_clock` and `steady_clock` readings fall between the corresponding
guest clock reads on either side of the call. In the resolution fixture,
both interfaces report 81 ns for realtime and monotonic, 1 ms for the
virtual and profiling clocks, and 1 s for `CLOCK_SECOND`.
[Clock readings](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/tests/GuestKernelClock.cpp)
and [resolution checks](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/tests/GuestFreebsdClocks.cpp).

```console
cmake --build build/a5 --parallel 4 --target guest_kernel_clock_tests guest_freebsd_clocks_tests
ctest --test-dir build/a5 --output-on-failure --no-tests=error -R "^(guest_kernel_clock|guest_freebsd_clocks)$"
```

## Thread cancellation

A cancellation request interrupts a blocked guest POSIX `nanosleep` and runs
one cleanup handler. With cancellation disabled, the sleep returns normally
and the worker handles the pending request after re-enabling cancellation.
For `sceKernelNanosleep`, the fixture checks that the requested one-second
interval elapses before cancellation unwinds the call.
[Sleep fixture](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/tests/GuestSleepCancel.cpp)

The pthread fixture selects asynchronous mode while cancellation is disabled.
The worker receives a pending request and joins as cancelled when it re-enables
cancellation. Delivery during uninterrupted computation remains unverified.
[Pthread fixture](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/tests/GuestPthreadCancel.cpp)

```console
cmake --build build/a5 --parallel 4 --target guest_pthread_cancel_tests guest_sleep_cancel_tests
ctest --test-dir build/a5 --output-on-failure --no-tests=error -R "^(guest_pthread_cancel|guest_sleep_cancel_(nanosleep_(blocked|disabled)|sce_nanosleep_deferred))$"
```

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

### Guest filename case

The fixture creates `Data/Settings.ini` and reads its contents through
`dAtA/SETTINGS.INI`. Mixed-case lookup also works through a guest mount
alias. On the case-sensitive Ubuntu test filesystem, `Settings.ini` and
`SETTINGS.INI` held different bytes. Each exact spelling read its own file,
and looking up `settings.ini` raised an ambiguity error.
[Pinned path fixture](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/tests/GuestPathCase.cpp)
and [Ubuntu filesystem check and test results](https://github.com/RavenCurseBurg/GTAVI-Recomp/actions/runs/45791835529/job/139812542754).

```console
cmake --build build/a5 --parallel 4 --target guest_path_case_tests
ctest --test-dir build/a5 --output-on-failure --no-tests=error -R "^guest_path_case$"
```

### Ordinary file permissions

The fixture creates one ordinary file and changes its mode first by path
(`sceKernelChmod`) and then by open descriptor (`sceKernelFchmod`). Both
calls returned success for each mode and gave the same host observations.

| Requested mode (octal) | Ubuntu 24.04 `stat` permissions | Windows x64 read-only attribute |
| --- | --- | --- |
| `0640` | `0640` | Clear |
| `0604` | `0604` | Clear |
| `0400` | `0400` | Set |
| `0600` | `0600` | Clear |

On Windows the read-only attribute was set only when the requested mode
omitted owner-write permission. Effective access for another user and Windows
ACLs remain unmeasured.
[Fixture source](https://github.com/RavenCurseBurg/GTAVI-Recomp/blob/b85666e31c4d3bf57c1f9dc55cfe63cde5704614/verification/regular_file_mode.cpp)
and [Ubuntu build and results](https://github.com/RavenCurseBurg/GTAVI-Recomp/actions/runs/45775900448/job/139759363578).

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

## Vulkan barrier batching

This CPU-only test exercises the Vulkan recorder's barrier decisions. In one
case, the barrier at the end of a render pass already covers the stages and
accesses needed for a subsequent label write. Other cases require the recorder
to keep a barrier when an image changes layout, ownership moves between queue
families, or the destination includes the host stage for a read. The fixture
checks these decisions using stage and access masks.
[Barrier cases](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/prx/libSceAgcDriver/tests/BarrierBatch.cpp)
and [recorder implementation](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/prx/libSceAgcDriver/Graphics/src/Recorder.cpp#L2604-L2612).

```console
cmake --build build/a5 --parallel 4 --target agc_barrier_batch_tests
ctest --test-dir build/a5 --output-on-failure --no-tests=error -R "^agc_barrier_batch$"
```

## Display status on Linux

Two VideoOut fixtures open a display using synthetic application metadata.
The resolution fixture registers a 1920×1080 buffer, checks the reported full
and pane sizes, and compares the refresh-rate codes returned by the resolution
and output status APIs. The current-output-mode fixture checks that the pinned
implementation returns `NO_DEVICE` on an open handle and preserves the
caller's output buffer.

With the full build configured as above, build both fixtures. On Ubuntu a
virtual X display can run them using Xvfb, xauth and Mesa's lavapipe driver
from the `mesa-vulkan-drivers` package.

```bash
cmake --build build/a5 --parallel 4 --target guest_video_out_resolution_status_tests guest_video_out_current_output_mode_tests
icd=$(dpkg -L mesa-vulkan-drivers | grep -E '/lvp_icd(\.x86_64)?\.json$')
VK_DRIVER_FILES="$icd" SDL_VIDEODRIVER=x11 ANYPS5_REQUIRE_DISPLAY=1 \
  xvfb-run -a -s '-screen 0 1920x1080x24' ctest --test-dir build/a5 \
  --no-tests=error --output-on-failure -R '^guest_video_out_(resolution_status|current_output_mode)$'
```

`ANYPS5_REQUIRE_DISPLAY=1` makes a display-open failure fail the test. Without
it the fixtures can return CTest's skip code, 77. On Ubuntu 24.04 x86-64,
both tests ran and passed with Xvfb and Mesa 25.2.8 llvmpipe
(`GALLIUM_OVERRIDE_CPU_CAPS=avx` on the runner).
[Display status test log](https://github.com/RavenCurseBurg/GTAVI-Recomp/actions/runs/45767909873/job/139733209089)

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

### PCM formats and channel layouts

The legacy output test sends 512 frames of eight-channel, 48 kHz float PCM
through `sceAudioOutOutput`. It checks the frame count returned and compares
all 16,384 queued bytes against the input. The AudioOut2 test uses SDL's disk
driver to capture stereo output. It checks each left and right sample for
mono, stereo, 7.1 and 7.1.4 inputs in both float and signed 16-bit PCM.
[Legacy output fixture](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/prx/libSceAudioOut/tests/AudioOutBufferSize.cpp)
and [AudioOut2 layout fixture](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/prx/libSceAudioOut/tests/AudioOut2PortLayouts.cpp).

```console
cmake --build build/a5 --parallel 4 --target audio_out_buffer_size_tests audio_out2_port_layouts_tests
ctest --test-dir build/a5 --output-on-failure --no-tests=error -R "^(audio_out_buffer_size_pass_through|audio_out2_port_layouts)$"
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

### Keyboard and mouse mapping

The pinned runtime reads `anyps5-input.ini` beside the generated executable.
Set `ANYPS5_INPUT_CONFIG` to select a different file. The mapping fixture
loads these settings together and checks the F key binding for the Cross
button, the two stick dead zones (percent) and mouse sensitivity.

```ini
Cross = KEY:F
LeftStickDeadzone = 12
RightStickDeadzone = 5
MouseSensitivity = 2.5
```

A separate fixture feeds SDL events to the default mapping. Pressing W
moves the left stick fully up, and releasing the direction keys returns it
to center. With mouse mode enabled, a stationary mouse leaves both right-stick
axes at 128 at polling intervals of 1, 8 and 33 ms.
[Configuration fixture](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/prx/libSceVideoOut/tests/InputMapping.cpp),
[SDL event fixture](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/core/libs/prx/libSceVideoOut/tests/KeyboardMouse.cpp)
and [upstream input guide](https://github.com/boykopovar/AnyPS5/blob/15826135019b8c7de27f42661a850a1dd9750932/docs/user/INPUT_MAPPING.md).

```console
cmake --build build/a5 --parallel 4 --target pad_input_mapping_tests pad_keyboard_mouse_tests
ctest --test-dir build/a5 --output-on-failure --no-tests=error -R "^(pad_input_mapping|pad_keyboard_mouse)$"
```
