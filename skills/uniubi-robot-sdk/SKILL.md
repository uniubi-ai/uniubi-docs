---
name: uniubi-robot-sdk
description: Develop, integrate, explain, and troubleshoot Uniubi Robot C++ or Python SDK applications, including High-level actions, Low-level joint control, observations, and MediaBus. Use for SDK API lookup, application changes, builds, and validation; ROS 2 application interfaces belong to uniubi-robot-ros2.
---

# Uniubi Robot SDK

Use the user's SDK delivery and firmware as the contract for the task. This skill supports API lookup and implementation; it does not authorize robot control, deployment, firmware changes, or policy execution.

## Establish the version and workspace

Locate the user's `uniubi_robot_sdk` and, for Python, `uniubi_robot_sdk_py` checkout or installed package. Follow applicable `AGENTS.md` instructions, including any remote workspace authority. Inspect branch/tag, full commit, working-tree changes, dependency locks, and runtime location before editing. Preserve unrelated changes. For installed Python, inspect `robot_motion_sdk.__file__` and binding/library provenance; a source checkout is not evidence that its binding is loaded.

Check the device's complete firmware version and the compatibility table in the matching README. A moving `main` is not a validated release bundle. Match public headers, bindings, runtime libraries, and companion dependencies; record hashes when diagnosing a delivery mismatch. Do not switch revisions, fetch a new release, or upgrade firmware merely to make an example work.

Locate `uniubi-docs` in the user's workspace if available. Otherwise consult the public repositories below, selecting the tag/commit matching the delivery where possible. These links are navigation entry points, not a promise that latest documentation matches installed software:

- [C++ SDK](https://github.com/uniubi-ai/uniubi_robot_sdk): `include/uniubi/robot_sdk/`, `examples/`, `CMakeLists.txt`, and README.
- [Python SDK](https://github.com/uniubi-ai/uniubi_robot_sdk_py): `src/MotionSdkPython.cpp`, `robot_motion_sdk/`, examples, README, and `dependencies.lock`.
- [Documentation](https://github.com/uniubi-ai/uniubi-docs): `docs/BUILD.md`, `docs/how-to/version-selection.md`, `docs/how-to/sdk-first-use.md`, and `docs/api-reference/{cpp,python}/`.

For an API question, trace the documented signature to the actual public header or binding and a maintained example. Cite the revision and source path. Do not invent a Python snake-case method by translating a C++ name; verify its binding.

## Select the integration path

| Need | Entry point and constraints |
|---|---|
| Built-in actions or read-only robot state | `MotionHighLevelClient`; external Linux hosts select their robot-facing NIC and target SN, while onboard use selects the local interface. An IP is not an SN. |
| Custom joint controller or policy | `MotionLowLevelClient`; real-hardware control runs on the robot brain with a local SHM data plane. ROS 2 Motion Bridge is not an equivalent joint-control interface. |
| Local video/layout or audio | `MediaBusClient`; video/layout requires local Orin shared memory. External hosts support remote PCM capture/RawBack playback, not local video/layout. |
| External camera video | Use the documented RTSP path; in ROS 2 this is the separate RTSP backend of `uniubi_media_driver`. |

Select libraries by final runtime location: `lib/x86_64/` for x86 hosts, `lib/aarch64/` for Orin, and `lib/aarch64_host/` for external ARM64 hosts. Both ARM64 platforms can report `aarch64`; explicitly use `-DPLATFORM=aarch64_host` where required. Inspect the matching README for available platforms and dependency versions. The public C++ build compiles examples, not the prebuilt SDK runtime itself.

For C++ consumers, prefer the exported `find_package(UniubiRobotSdk CONFIG REQUIRED)` targets `Uniubi::RobotMotionSdk` and, for media, `Uniubi::MediaBus`. For Python use the matching SDK root and binding build instructions; inspect `PYTHONPATH`, `LD_LIBRARY_PATH`, Python ABI, and loader dependencies before changing code to compensate for import failures. Build in a separate directory when changing platform/toolchain.

## Implement lifecycle correctly

For High-level integration, use the selected revision's `example_highlevel.cpp` or `example_highlevel.py` as the lifecycle reference:

1. Register discovery/log callbacks and select the NIC before service initialization. Discovery is asynchronous; collect and deduplicate SN callbacks and require explicit target selection.
2. Initialize the service, create the correct local or SN-addressed client, register observation/state callbacks, and connect. Connection and read-only queries do not acquire control.
3. Query capabilities before choosing action names and parameter ranges. Acquire control only when authorized, handle lease renewal/preemption, check return values and `getLastError`, and observe effective state after asynchronous changes.
4. End the active action, confirm its effective transition, release control, disconnect, and shut down the service. `releaseControl()` and `disconnect()` do not themselves stop an active action. `queryMotionState()` may successfully return `{}` when no action is active; it is not motor-readiness evidence.

For Low-level code, read `docs/how-to/low-level-control.md`, the matching Low-level API page, and the selected example before modifying a control loop. After `kConnected`, obtain `MotorLayout`, verify joint count/order, and address frames using returned limb/joint identifiers before enabling motion. Validate observation dimensions, finite values, normalization, SDK/model reordering, action scale, control rate, and watchdog behavior. A new model file alone does not establish compatibility.

Design cleanup in the original controller: reach an observed safe posture, stop control frames, disable motion, wait for effective `kConnected`, then call and check `restoreMotionControlMode()` / the verified Python binding, disconnect, and shut down. A separate restoration tool requires the original process to have exited first; it does not establish a safe posture or stop another controller. Exit, emergency stop, disconnect, and the remote-controller `M` button are not proof of built-in control restoration. Do not retry offline, malformed-layout, NaN, or cleanup failures blindly.

For media, verify frame ownership/lifetime, pixel or audio format, timestamps, queue bounds, and capture/playback cleanup from the matching API and example. Do not assume a successful MediaBus connection proves external video availability.

## Validate the affected behavior

Choose checks that cover the change without implying additional authorization:

- Compile affected C++ consumers/examples with the selected target libraries, or import the actual Python binding and run relevant existing tests. Report target versus build host for cross-builds.
- Test parsing, reordering, finite-value rejection, timeout, and cleanup logic without hardware where feasible. Use Mock/simulation for controller integration when available; report its separate evidence boundary.
- For authorized read-only hardware validation, use the maintained CLI's `--read-only` mode with the actual NIC and explicit external SN. Require successful capability/system/state queries and fresh, advancing observation frames, not just discovery or `connect()`.
- Hardware motion and control acquisition require an authorized plan, operator, emergency stop, and the documented posture/environment prerequisites. Static checks, import, RPC acceptance, and simulation do not prove physical behavior.

Return changed files, exact checks, revision/library provenance, observed results, and remaining gaps. Separate build, communication, simulation, control-state, and physical evidence.
