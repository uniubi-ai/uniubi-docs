---
name: uniubi-robot-ros2
description: Develop, explain, build, and troubleshoot Uniubi ROS 2 applications and packages, including Motion Bridge, the C++ motion client, direct DDS interfaces, messages, and media backends. Use for launch/configuration and interface changes or ROS 2 validation; joint-level SDK policy control belongs to uniubi-robot-sdk.
---

# Uniubi Robot ROS 2

Implement against the user's actual ROS 2 and firmware delivery. API lookup, source edits, and local validation do not authorize deployment, robot motion, or ownership acquisition.

## Locate the contracts

Find the user's `uniubi_ros2`, `uniubi_robot_msgs`, and relevant documentation checkout, or identify installed package prefixes and provenance. Follow applicable `AGENTS.md`, including remote source authority; inspect full commits, branch/tag, working-tree changes, dependency locks, ROS distribution, and sourced overlays. Preserve user changes and existing build/install trees. Do not infer the loaded package from the current directory.

Use the installed delivery's compatibility information and `dependencies.lock`; matching branch names do not establish compatible repositories. Inspect the selected revision's README before preparing dependencies or changing overlays. Public entry points:

- [ROS 2 repository](https://github.com/uniubi-ai/uniubi_ros2): README, `docs/ros2_usage_modes.md`, `docs/motion_bridge.md`, `docs/runtime_notes.md`, and source packages.
- [Message repository](https://github.com/uniubi-ai/uniubi_robot_msgs): adjacent `ros2/` and `idl/` trees and `docs/protocol_notes.md`.
- [Documentation](https://github.com/uniubi-ai/uniubi-docs): `docs/how-to/ros2-motion-bridge.md`, `docs/uniubi_robot_dds_api.md`, and `docs/how-to/version-selection.md`.

Resolve those paths in the user's checkout or open public links at the matching tag/commit. This skill has no dependency on the docs repository's directory layout. Current `main` links are discovery aids, not proof of installed behavior.

## Choose the correct package

| Goal | Package/path |
|---|---|
| Common action control and standard observations | `uniubi_motion_bridge`; default application-facing integration. |
| Advanced custom C++ High-level flow | `uniubi_motion_client`; compiled ROS 2 wrapper with explicit executor/lifecycle handling. |
| Raw fields, new RPC, wire or QoS debugging | Direct DDS/ROS 2 protocol using message package `uniubi`, sourced from `uniubi_robot_msgs/ros2`. The repository name is not the ROS package/type prefix. |
| Camera/audio | Independent `uniubi_media_driver`; inspect its README and `RTSP.md`. |

Motion Bridge, the C++ motion client, and direct protocol integration communicate via DDS/services without linking `librobotMotionSdk.so`. MediaBus media links the SDK. MediaBus video/layout runs on Orin locally; external x86/ARM64 camera access uses RTSP. Remote MediaBus audio is a separate supported path. For direct joint-level control use the SDK Low-level client, not a new Motion Bridge velocity topic.

## Configure for the runtime location

Verify the robot's network and selected delivery before applying these documented defaults:

| Runtime | Domain | RPC / Event | Observation source |
|---|---|---|---|
| External host | `42` | `robotServer` / `/robotServer/Event` | `sensor_observed`, SN-addressed raw topics |
| Orin brain | `1` | `cerebellumServer` / `/robotCereServer/Event` | `cere_motion_state`, native `rt/cere/motionState` |

Select the actual robot-facing NIC, `rmw_cyclonedds_cpp`, `ROS_LOCALHOST_ONLY=0`, and appropriate `CYCLONEDDS_URI`. Domain configuration does not make an offline robot reachable. Use `DontRoute` only for the documented same-subnet wired topology; do not copy it into routed networking. `device_id` is the target SN/deviceNo, not an IP, and is required for the bridge. Internal cerebellum observation frames carry no device ID and cannot select among multiple robots on that topic.

Inspect `src/uniubi_motion_bridge/config/motion_bridge.yaml` and `launch/motion_bridge.launch.py` for supported overrides. The launch exposes `config_file`, `device_id`, `namespace`, and `frame_prefix`; provide a custom YAML for other parameters instead of inventing launch arguments. An omitted frame prefix must preserve a custom YAML's setting. Check actual namespaced graph names rather than assuming all endpoints are absolute.

## Preserve application and wire semantics

For bridge code or applications, inspect the service definitions, `MotionStatus.msg`, callbacks, configuration, and tests:

- `motion/start_action` uses `uniubi_motion_bridge/srv/StartMotionAction` with action and JSON parameters; it acquires/maintains control on demand. Query capabilities first. The bridge forwards the action and does not insert a zero-velocity transition for the caller.
- `cmd_vel` maps `linear.x`, `linear.y`, and `angular.z` to `lineVelocityX`, `lineVelocityY`, and `velocity`. Positive lateral velocity stays positive-left. It does not acquire control, start/switch actions, or provide a response per message. The timeout sends one all-zero parameter update; it does not stop the action or release ownership.
- `stop_action` and `release_control` are different operations. In the documented delivery, stopping asynchronously returns the action to zero-speed walking while retaining control; confirm effective action and velocities through `motion/status` rather than assuming standing.
- Standard observations include `odom`, `joint_states`, `imu/data`, and `battery_state`. Odometry is accumulated device position/yaw; do not integrate it again. Check timestamp units, validity handling, frame IDs, and battery percentage conversion. No TF publisher should be assumed without source evidence.
- For `uniubi_motion_client`, register callbacks before connection and keep an executor spinning. Handle lease renewal, preemption, and response deadlines; stop the action before release/disconnect. Connection is not ownership.

For message/protocol changes, treat `uniubi_robot_msgs` IDL and ROS definitions as the contract. Trace generated type support, native DDS type names, serialization, fields, QoS, and all client/bridge conversions before editing. Do not alter wire layout, names, units, validity flags, defaults, or public service schemas as an incidental fix. Preserve adjacent `idl/` and `ros2/` directories because the native cerebellum reader consumes the IDL. Raw observed publishers may require explicit enabling after the reader exists; subscriptions and RPC/Events are channels of one protocol, not interchangeable control alternatives.

For camera work, inspect `media_driver.launch.py`: `video_backend:=mediabus` selects `uniubi_media_driver_node`; `video_backend:=rtsp` selects `uniubi_rtsp_driver_node`, using `host` or `rtsp_config_file`. Verify URL/channel, reconnect behavior, image encoding, stamps, and queue bounds. RTSP can be built without the SDK; MediaBus requires matching platform libraries.

## Implement and validate

Use the chosen revision's dependency preparation and build instructions. The motion package set is `uniubi uniubi_motion_client uniubi_motion_bridge`; media is optional. Avoid overwriting existing checkout/symlink destinations. Select a fresh build directory or workspace when changing ABI, platform, or overlay. Confirm package/type lookup with `ros2 pkg prefix` and `ros2 interface show` after sourcing the intended overlay.

Build affected packages and run relevant existing tests with `colcon test` and `colcon test-result --verbose`, using a non-hardware environment where possible. Add focused regression coverage for changed serialization/conversion, namespace/frame behavior, async RPC cancellation, timeout, or backend configuration. Do not weaken tests to obtain a pass.

For authorized read-only integration, verify graph endpoints/types/QoS, successful query responses, continuously advancing observation timestamps, expected frame IDs, and source/device selection. Do not call `start_action` merely to make observations appear. Keep one intended control entry point per robot; competing bridge/client processes can preempt one another.

A hardware action check requires separate authorization and the documented operator/emergency-stop prerequisites. For an authorized first High-level check, consult current capabilities and use explicit all-zero walking parameters, then verify effective status; `{}` does not establish zero defaults. Build, launch, discovery, and service acceptance are separate from observed physical behavior.

Report files changed, repository and overlay provenance, exact checks and results, logs/evidence, and unverified hardware or compatibility gaps.
