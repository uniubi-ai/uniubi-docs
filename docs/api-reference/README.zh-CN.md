# API 参考

[English](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/README.md) | **简体中文**

API 参考按编程语言分开。普通应用开发者可以直接从 Python 开始，不需要先理解 C++ 类、头文件或 CMake 工程。

## 选择语言和控制领域

| 领域 | Python API | C++ API | 适用场景 |
|---|---|---|---|
| High-level | [Python](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/high-level.zh-CN.md) | [C++](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/high-level.zh-CN.md) | 调用机器人内置动作能力 |
| Low-level | [Python](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/low-level.zh-CN.md) | [C++](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/low-level.zh-CN.md) | 自己运行策略并控制关节位置或扭矩 |
| MediaBus | [Python](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/media.zh-CN.md) | [C++](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/media.zh-CN.md) | 订阅摄像头、麦克风和编码帧 |

## 常用应用能力索引

| 能力 | High-level 入口 | Low-level 入口 | 操作指南 |
|---|---|---|---|
| 电机 / IMU / 遥控器 | `setObservedEnable(motionEnable)` + 回调；Python 为 `set_observed_enable()` | `getLatestObservation()`；Python 为 `get_latest_observation()` | [读取传感器与运动观测](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/read-sensor-data.zh-CN.md) |
| GPS / UWB | `setObservedEnable(sensorEnable)` + 回调/缓存 | `getSensorObservation()` | [读取传感器与运动观测](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/read-sensor-data.zh-CN.md) |
| Walk 里程计 | `SensorObserved.odom` | **不支持** | [读取传感器与运动观测](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/read-sensor-data.zh-CN.md) |
| 完整设备 / 电池 / 网络状态 | `querySystemStatus()`；Python 为 `query_system_status()` | **不支持** | [查询设备状态](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/query-device-status.zh-CN.md) |
| 轻量电源观测 | `getPowerInfo()`；Python 为 `get_power_info()` | `getLatestObservation().power` | [查询设备状态](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/query-device-status.zh-CN.md) |
| 语音播放与文件管理 | `startAudioPlay()` 等 High-level 接口 | **不支持** | [使用语音、灯光和媒体帧](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/use-media-and-device-io.zh-CN.md) |
| 摄像头灯光 | `get/setCameraLightBrightness()` | **不支持** | [使用语音、灯光和媒体帧](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/use-media-and-device-io.zh-CN.md) |
| 摄像头视频 / 麦克风音频 | `createMediaBusClient()` | `createMediaBusClient()` | [使用语音、灯光和媒体帧](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/use-media-and-device-io.zh-CN.md) |

> 共享协议结构中存在某个字段，不代表所有客户端都提供相同支持契约。尤其是 Walk 里程计：High-level 明确支持，Low-level 不支持。

## 如何选择

- 使用 Python 包、希望快速完成导入和业务验证：直接进入 Python API。
- 开发 native 应用、需要 CMake、头文件或 C++ 回调类型：进入 C++ API。
- Python 与 C++ 的能力边界并非在所有平台上完全相同；以对应语言页面标注的部署和平台限制为准。
- 需要原始 DDS / RPC、QoS 或协议字段：进入 [高级主题](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/advanced/README.zh-CN.md)。

如果还没有确定 High-level / Low-level，先阅读 [核心概念](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/core-concepts/README.zh-CN.md)；如果尚未完成构建和只读验证，先阅读 [操作指南](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/README.zh-CN.md)。
