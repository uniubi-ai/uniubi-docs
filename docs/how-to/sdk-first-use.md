# SDK First Use

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/sdk-first-use.zh-CN.md)

> This page does not choose a control mode. Select High-level or Low-level from the [How-to entry point](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/README.md), then return here to prepare the SDK.

## Goal

Build or import the C++ or Python SDK and complete read-only validation before entering a control workflow.

## SDK Entry Points

| Control mode | SDK entry point | Purpose |
|---|---|---|
| High-level | `MotionHighLevelClient` | Invoke built-in robot actions without controlling individual joints |
| Low-level | `MotionLowLevelClient` | Run a custom controller and directly command joint position or torque |

Joint-level Low-level control uses `MotionLowLevelClient`. ROS 2 Motion Bridge does not provide an equivalent interface.

## Choose the Deployment Mode

| Mode | High-level real robot | Low-level real robot |
|---|---|---|
| External Linux PC / industrial computer | Supported. Select the actual robot-facing network interface and provide the target device ID (SN), obtained from the Basic Information page in the Uniubi App or SDK discovery. The built-in motion service remains on the robot. | Not the hardware deployment path; run the joint-control application onboard. |
| Robot compute module (“brain”) | Supported. No device ID is required. | Required for current real-hardware joint control. |

For High-level discovery from an external host, configure in this order: register the discovery callback and set the network interface, then initialize the service. Discovery is asynchronous: a `true` return means only that the request was issued. Wait up to 5 seconds for callbacks, retry if none arrive, deduplicate by SN, and require explicit target selection instead of automatically choosing the first response. When the robot IP is known, match it against `network.*.ipv4Addr` in callback `info` to identify the corresponding SN; the client still receives the SN, not the IP.

The external-host High-level C++ SDK, Python SDK, and ROS 2 paths have all been validated on a real robot. Each path must select the network interface that actually reaches the robot and address the target by its Device ID (SN).

## Prerequisites

- A Linux environment and SDK runtime libraries for the target architecture
- Device IPs obtained from the app, plus a confirmed login address, externally accessible service ports, and robot-facing network interface; see [Robot Network Access](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/core-concepts/device-network.md). External High-level mode must use the interface that actually reaches the robot network; onboard High-level mode must select `eth0.100`
- An external Linux High-level application does not have a blanket root requirement. Onboard, Low-level, and Media runtimes follow the permissions required by the target device; C++ compilation itself does not require `sudo`
- Matching C++ SDK, Python binding, architecture, version, and ABI
- Completion of the [Build, Installation, and Cross-compilation Guide](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/BUILD.md)

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

If runtime libraries, architecture, or media libraries do not match, return to the [Build Guide](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/BUILD.md). Do not modify the Python binding to work around an environment mismatch.

## 3. Complete Read-only Validation

Validate import, connection, and observations first. Do not turn the first run into a walking, jumping, or joint-torque test.

Success criteria:

- The C++ example builds or the Python package imports successfully.
- Read-only communication and observations work.
- The active SDK runtime-library version, architecture, and ABI are known.
- Only then proceed to the relevant High-level or Low-level control guide.

## Next Steps

- High-level: [Use Built-in Robot Actions](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/high-level-control.md), then choose the [Python API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/high-level.md) or [C++ API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/high-level.md)
- Low-level: [Run a Custom Joint-control Policy](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/low-level-control.md), then choose the [Python API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/low-level.md) or [C++ API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/low-level.md)
- Media frames: choose the [Python API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/media.md) or [C++ API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/media.md)
- Repository-specific build details: [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) and [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py)
