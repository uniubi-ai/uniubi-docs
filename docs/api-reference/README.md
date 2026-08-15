# API Reference

**English** | [简体中文](README.zh-CN.md)

The API reference is separated by programming language. Application developers can start directly with Python without first learning C++ classes, headers, or CMake projects.

## Choose a Language and Control Area

| Area | Python API | C++ API | Use when |
|---|---|---|---|
| High-level | [Python](python/high-level.md) | [C++](cpp/high-level.md) | Invoking built-in robot actions |
| Low-level | [Python](python/low-level.md) | [C++](cpp/low-level.md) | Running a custom policy and commanding joint position or torque |
| MediaBus | [Python](python/media.md) | [C++](cpp/media.md) | Subscribing to camera, microphone, and encoded frames |

## Common application capability index

| Capability | High-level entry point | Low-level entry point | Guide |
|---|---|---|---|
| Motors / IMU / remote controller | `setObservedEnable(motionEnable)` + callback; Python: `set_observed_enable()` | `getLatestObservation()`; Python: `get_latest_observation()` | [Read sensor and motion observations](../how-to/read-sensor-data.md) |
| GPS / UWB | `setObservedEnable(sensorEnable)` + callback/cache | `getSensorObservation()` | [Read sensor and motion observations](../how-to/read-sensor-data.md) |
| Walk odometry | `SensorObserved.odom` | **Not supported** | [Read sensor and motion observations](../how-to/read-sensor-data.md) |
| Complete device / battery / network status | `querySystemStatus()`; Python: `query_system_status()` | **Not supported** | [Query device status](../how-to/query-device-status.md) |
| Lightweight power observation | `getPowerInfo()`; Python: `get_power_info()` | `getLatestObservation().power` | [Query device status](../how-to/query-device-status.md) |
| Voice playback and file management | High-level `startAudioPlay()` and related methods | **Not supported** | [Use voice, lights, and media frames](../how-to/use-media-and-device-io.md) |
| Camera light | `get/setCameraLightBrightness()` | **Not supported** | [Use voice, lights, and media frames](../how-to/use-media-and-device-io.md) |
| Camera video / microphone audio | `createMediaBusClient()` | `createMediaBusClient()` | [Use voice, lights, and media frames](../how-to/use-media-and-device-io.md) |

> A field in a shared protocol structure does not imply the same supported contract in every client. In particular, Walk odometry is supported by High-level and is not supported by Low-level.

## Choosing Between Them

- If you use the Python package and want the shortest path to application validation, begin with the Python API.
- If you build a native application and need CMake, headers, or C++ callback types, use the C++ API.
- Python and C++ do not have identical deployment and platform coverage in every environment. Follow the boundary stated on the selected language page.
- For raw DDS/RPC, QoS, or protocol fields, use [Advanced](../advanced/README.md).

If you have not chosen High-level or Low-level control, begin with [Core Concepts](../core-concepts/README.md). If build and read-only validation are incomplete, follow the [How-to guides](../how-to/README.md).
