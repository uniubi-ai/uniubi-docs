# Troubleshooting by Symptom

**English** | [简体中文](troubleshooting.zh-CN.md)

Start at the stage that actually failed. Save the error and [version record](version-selection.md), then use the relevant guide below.

| Symptom | First check | Guide |
|---|---|---|
| Missing library or GLIBC/GLIBCXX mismatch | Library directory for the deployment platform, dependencies, and provenance | [Build troubleshooting](../BUILD.md#troubleshooting--faq) |
| Python binding import fails | Python version, ELF architecture, SDK paths; distinguish Orin from ARM64 host | [Build troubleshooting](../BUILD.md#troubleshooting--faq) |
| No discovery responses or RPC timeout | Current device IP, actual interface, SN, runtime location; DontRoute conditions for direct Ethernet | [Robot network access](../core-concepts/device-network.md), [peripherals](connect-peripherals.md) |
| Connected but no observations | Observation switches, callback registration order, advancing data, and client support | [Sensor and motion observations](read-sensor-data.md) |
| High-level cannot acquire control | Remote-controller connection, client state, returned error | [High-level workflow](high-level-control.md) |
| Built-in remote-control actions unavailable after Low-level exits | Original process stopped and built-in control mode restored | [Low-level shutdown workflow](low-level-control.md) |
| Remote camera video unavailable | RTSP versus MediaBus; remote MediaBus does not support video subscriptions or layout queries | [Media integration](use-media-and-device-io.md) |
| Python hangs on exit | Subscriptions, client, and service released in order from the application control thread | [High-level shutdown](../api-reference/python/high-level.md#3-exit-deadlock-avoidance), [Low-level shutdown](../api-reference/python/low-level.md#3-exit-deadlock-avoidance) |

## Confirm Recovery

Repeat the smallest check for the failed stage and record both returned state and observable results. A connection does not prove observations are arriving; RPC acceptance does not prove an action completed. Meet the control guide's prerequisites before any motion validation.

## Include in a Problem Report

- Firmware, component commits, runtime location, OS/Python versions, and library directory;
- minimal reproduction command, expected result, actual error, and timestamp;
- relevant state or logs, identifying whether physical motion was involved.

Remove credentials, access tokens, and device/network information that should not be public before sharing.

[Back to How-to Guides](README.md)
