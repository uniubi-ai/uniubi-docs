# SDK First Use

**English** | [简体中文](sdk-first-use.zh-CN.md)

> This page does not choose a control mode. Select High-level or Low-level from the [How-to entry point](README.md), then return here to prepare the SDK.

## Goal

Build or import the C++ or Python SDK and complete read-only validation before entering a control workflow.

## SDK Entry Points

| Control mode | SDK entry point | Purpose |
|---|---|---|
| High-level | `MotionHighLevelClient` | Invoke built-in robot actions without controlling individual joints |
| Low-level | `MotionLowLevelClient` | Run a custom controller and directly command joint position or torque |

Joint-level Low-level control uses `MotionLowLevelClient`. ROS 2 Motion Bridge does not provide an equivalent interface.

## Prerequisites

- A Linux environment and SDK runtime libraries for the target architecture
- Device IPs obtained from the app, plus a confirmed login address, externally accessible service ports, and robot-facing network interface; see [Robot Network Access](../core-concepts/device-network.md). External High-level mode must use the interface that actually reaches the robot network; onboard High-level mode must select `eth0.100`
- Root privileges when running SDK programs on current devices; C++ compilation itself does not require `sudo`
- Matching C++ SDK, Python binding, architecture, version, and ABI
- Completion of the [Build, Installation, and Cross-compilation Guide](../BUILD.md)

On the robot compute module, install the Python SDK into the system `python3`. Run examples with the `sudo env` form documented by the corresponding SDK README so that the dynamic-library environment is preserved.

## 1. Choose a Language

| Language | Repository | Use when |
|---|---|---|
| C++ | [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) | Developing C++ control, observation, or example applications |
| Python | [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) | Developing Python control, observation, or policy integration |

## 2. Complete a Minimal Build or Import

Build the C++ SDK examples:

```bash
cd uniubi_robot_sdk
cmake -S . -B build
cmake --build build -j
```

For Python, prepare the C++ SDK first, then install the binding:

```bash
cd uniubi_robot_sdk_py
export UNIUBI_SDK_ROOT=/path/to/uniubi_robot_sdk
UNIUBI_SDK_ROOT="$UNIUBI_SDK_ROOT" python3 -m pip install .
python3 -c "import robot_motion_sdk as sdk; print(sdk.MotionHighLevelClient)"
```

If runtime libraries, architecture, or media libraries do not match, return to the [Build Guide](../BUILD.md). Do not modify the Python binding to work around an environment mismatch.

## 3. Complete Read-only Validation

Validate import, connection, and observations first. Do not turn the first run into a walking, jumping, or joint-torque test.

Success criteria:

- The C++ example builds or the Python package imports successfully.
- Read-only communication and observations work.
- The active SDK runtime-library version, architecture, and ABI are known.
- Only then proceed to the relevant High-level or Low-level control guide.

## Next Steps

- High-level: [Use Built-in Robot Actions](high-level-control.md) and the [High-level SDK API](../uniubi_high_level_sdk.md)
- Low-level: [Run a Custom Joint-control Policy](low-level-control.md) and the [Low-level SDK API](../uniubi_low_level_sdk.md)
- Media frames: [Media SDK API](../uniubi_media_sdk.md)
- Repository-specific build details: [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) and [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py)
