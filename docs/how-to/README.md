# How-to Guides

**English** | [简体中文](README.zh-CN.md)

Each guide addresses a specific development task. It defines the goal and prerequisites, provides a minimal procedure, and states observable success criteria and the next project entry point.

## Step 1: Choose a Control Mode

| Goal | Control mode | Guide |
|---|---|---|
| Use built-in motion capabilities without controlling individual joints | High-level | [Use built-in robot actions](high-level-control.md) |
| Train or run your own controller and directly command joint position or torque | Low-level | [Run a custom joint-control policy](low-level-control.md) |

## Step 2: Choose an Implementation

| Control mode | Implementation | Entry point |
|---|---|---|
| High-level | C++ / Python SDK | `MotionHighLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |
| High-level | ROS 2 | `uniubi_motion_bridge` → [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) → [`uniubi_ros2`](https://github.com/uniubi-ai/uniubi_ros2) |
| Low-level | C++ / Python SDK | `MotionLowLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |

ROS 2 Motion Bridge does not provide an equivalent joint-level Low-level interface.

## Supporting Guides

| Task | Guide | When to use it |
|---|---|---|
| Confirm device addresses, exposed ports, and compute-module access | [Device network and compute-module access](../core-concepts/device-network.md) | Before connecting to a real robot |
| Prepare the build environment | [Build, installation, and cross-compilation](../BUILD.md) | Before SDK or ROS 2 development |
| Prepare an SDK project | [SDK first use](sdk-first-use.md) | After selecting High-level or Low-level SDK development |
| Write a ROS 2 application node | [Start and validate Motion Bridge](ros2-motion-bridge.md) | After selecting High-level + ROS 2 |
| Train, export, and replay a policy | [Policy training and replay](train-export-replay.md) | During Low-level policy development |
| Validate the SDK path without hardware | [Mock / Sim2Sim](mock-sim2sim.md) | Before real-robot SDK testing |

## Guide Structure

Each guide should contain:

1. **Goal and scope**
2. **Prerequisites**
3. **Minimal procedure**
4. **Expected results**
5. **Success criteria**
6. **Safety and cleanup**
7. **Troubleshooting**
8. **Next steps**

Every procedure should include an observable result so that developers can distinguish successful execution from a command that merely returned.
