# Uniubi Docs

**English** | [简体中文](README.zh-CN.md)

Uniubi Docs is the central documentation site for developing with Uniubi robots. Start with the task you want to complete, run the smallest useful validation, and then continue to the relevant repository and API reference.

> Obtain secondary-development access and embodied-intelligence platform materials from the [Embodied Intelligence Developer Portal](https://www.uniubi.com/developer/embodied); if access is not enabled yet, follow the page instructions to sign in or apply.

## Quick Start

Choose a control mode first. For High-level, choose the application runtime next, then select an implementation. Do not begin by choosing a programming language or repository.

> Before connecting to a real robot, read [Robot Network Access](docs/core-concepts/device-network.md) to obtain the device IPs from the app and confirm the login address, externally accessible service ports, and network interface. Skip this when working only with Mock / Sim2Sim, offline builds, or training.

### 1. Choose a control mode

| Goal | Control mode | Start here |
|---|---|---|
| Use the robot's built-in motion capabilities without controlling individual joints | High-level | [High-level: use built-in robot actions](docs/how-to/high-level-control.md) |
| Train or run your own controller and directly command joint position or torque | Low-level | [Low-level: run a custom joint-control policy](docs/how-to/low-level-control.md) |

### 2. For High-level, choose the application runtime

| Runtime location | When to use it | Real-robot connection requirements |
|---|---|---|
| External Linux PC / industrial PC | Keep the application off the robot brain | The actual network interface that reaches the robot + Device ID (robot SN) |
| Robot brain | Deploy the application and SDK on the onboard compute platform | The robot's internal communication interface; the onboard single-device client needs no Device ID |

Both locations use the same High-level capabilities, and the real-time motion service always remains on the robot. Obtain the Device ID from the Basic Information page in the Uniubi App or through SDK device discovery. See the [High-level dual-deployment architecture](docs/core-concepts/README.md#two-deployment-locations-for-high-level-applications) for the complete boundary.

### 3. Choose an implementation

| Control mode | Implementation | Entry point |
|---|---|---|
| High-level | C++ / Python SDK | `MotionHighLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |
| High-level | ROS 2 | `uniubi_motion_bridge` → [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) → [`uniubi_ros2`](https://github.com/uniubi-ai/uniubi_ros2) |
| Low-level | C++ / Python SDK | `MotionLowLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |

Joint-level Low-level control uses the SDK. ROS 2 Motion Bridge does not provide an equivalent joint-level control interface.

### 4. Continue with your task

- [Build and install the SDK](docs/BUILD.md): prepare a native, on-board, or cross-compilation environment for C++ and Python development.
- [Use High-level control](docs/how-to/high-level-control.md): use High-level interfaces from an external computer or the robot's compute module to read state and invoke built-in actions; target Mock / Sim2Sim or a real robot.
- [Use ROS 2 Motion Bridge](docs/how-to/ros2-motion-bridge.md): access High-level capabilities from ROS 2.
- [Use Low-level control](docs/how-to/low-level-control.md): validate posture on a safety rig before validating policy walking on clear, level ground.
- [Train, export, and replay a policy](docs/how-to/train-export-replay.md): develop and deploy a custom Low-level policy.
- [Read sensor and motion observations](docs/how-to/read-sensor-data.md): read GPS, UWB, motors, IMU, power, and High-level Walk odometry.
- [Query device status](docs/how-to/query-device-status.md): distinguish complete system status from Low-level lightweight power observations.
- [Use voice, lights, and media frames](docs/how-to/use-media-and-device-io.md): integrate voice playback, camera lights, video, and microphone data.

Each guide begins with a concrete task and an observable success criterion. See the [How-to guides](docs/how-to/README.md) for additional development and troubleshooting workflows.

## Core Concepts

Understand brain and cerebellum responsibilities, High-level and Low-level control, component responsibilities, device networking, and the control lifecycle before moving to implementation details.

[Read Core Concepts](docs/core-concepts/README.md)

## How-to Guides

Follow task-oriented instructions for environment setup, first connection, peripheral connectivity and power, real-robot control, ROS 2 integration, sensor and device data, media integration, and policy deployment.

[Browse the How-to guides](docs/how-to/README.md)

## API Reference

After choosing a control mode and completing minimal validation, use the API reference for interface fields, state machines, lifecycle rules, and examples.

[Browse the API Reference](docs/api-reference/README.md)

## Advanced

Use the Advanced section only when you need direct DDS/RPC access, QoS details, protocol mappings, or a specialized integration.

[Browse Advanced topics](docs/advanced/README.md)

## Safety

Before requesting High-level control on a real robot, disconnect the remote controller: either power it off, or press and hold its `M` button until the robot announces “遥控器连接已断开” (remote controller disconnected). While the remote controller remains connected, the High-level client cannot obtain control ownership. Read-only checks do not require this step.

For the first High Level real-robot integration, begin with read-only checks, then validate ownership, action startup, and status feedback by starting `walking` with all three velocity fields explicitly set to zero. `standing` and `laying` depend on the current posture and the server state machine, so they are not a universal round-trip test. Validate walking with nonzero velocity and other locomotion only on clear, level, obstacle-free ground with the emergency stop within reach and an operator attending the robot.

Before triggering any action other than `laying`, enter zero-velocity `walking` and use the state query to confirm that the effective action is `walking`; only then trigger the target action. `laying` does not require this preliminary transition.

For a Low-level walking policy, secure the robot on a safety rig with all four feet clear and validate only `stand` and `lay`. After posture, joint direction, and emergency-stop behavior are confirmed, move the robot to the ground and validate `stand` → `walk` → `stop` → `lay`. Never execute `walk` while the robot is suspended.

Jumping, bipedal standing, handstands, damping, and joint-torque control require an appropriate test area, a reachable emergency stop, and a clear manual-takeover plan.

## License

Original Uniubi documentation and code in this repository are licensed under the Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
