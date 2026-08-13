# High-level: Use Built-in Robot Actions

**English** | [简体中文](high-level-control.zh-CN.md)

## Goal

Use motion and locomotion capabilities already provided by the robot. The application sends actions or motion intent and does not generate position, velocity, or torque commands for individual joints.

Typical goals include:

- making the robot stand, lie down, or perform another built-in action;
- using built-in walking, steering, and speed control; and
- writing a ROS 2 application node that invokes robot motion capabilities.

## Out of Scope

If your application runs its own policy and directly outputs joint position or torque targets, follow [Low-level: Run a Custom Joint-control Policy](low-level-control.md).

## Choose an Implementation

| Development path | Entry point | Use when |
|---|---|---|
| C++ / Python SDK | `MotionHighLevelClient` | Developing a control or observation application directly against the SDK |
| ROS 2 | `uniubi_motion_bridge` | Developing a ROS 2 application with standard topics and services |

For SDK development, first complete [SDK First Use](sdk-first-use.md). For ROS 2, follow [Start and Validate ROS 2 Motion Bridge](ros2-motion-bridge.md).

## Repositories

- C++ SDK: [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk)
- Python SDK: [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py)
- ROS 2 interfaces and bridge: [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) → [`uniubi_ros2`](https://github.com/uniubi-ai/uniubi_ros2)

`uniubi_robot_msgs` is the authoritative source for ROS 2 interfaces and build dependencies. It is not the normal place for application-specific changes.

## Minimum Success Criteria

1. Build or import the SDK, or build the ROS 2 bridge.
2. Complete read-only observation checks before requesting control.
3. With the emergency stop reachable and an operator ready to intervene, validate low-risk actions such as standing and lying down before low-speed locomotion.

See the [High-level SDK API](../uniubi_high_level_sdk.md) and [ROS 2 Motion Bridge guide](ros2-motion-bridge.md) for lifecycle and safety details.
