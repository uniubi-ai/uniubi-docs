# API Reference

**English** | [简体中文](README.zh-CN.md)

The API reference is separated by programming language. Application developers can start directly with Python without first learning C++ classes, headers, or CMake projects.

## Choose a Language and Control Area

| Area | Python API | C++ API | Use when |
|---|---|---|---|
| High-level | [Python](python/high-level.md) | [C++](cpp/high-level.md) | Invoking built-in robot actions |
| Low-level | [Python](python/low-level.md) | [C++](cpp/low-level.md) | Running a custom policy and commanding joint position or torque |
| MediaBus | [Python](python/media.md) | [C++](cpp/media.md) | Subscribing to camera, microphone, and encoded frames |

## Choosing Between Them

- If you use the Python package and want the shortest path to application validation, begin with the Python API.
- If you build a native application and need CMake, headers, or C++ callback types, use the C++ API.
- Python and C++ do not have identical deployment and platform coverage in every environment. Follow the boundary stated on the selected language page.
- For raw DDS/RPC, QoS, or protocol fields, use [Advanced](../advanced/README.md).

If you have not chosen High-level or Low-level control, begin with [Core Concepts](../core-concepts/README.md). If build and read-only validation are incomplete, follow the [How-to guides](../how-to/README.md).
