# API 参考

[English](README.md) | **简体中文**

API 参考按编程语言分开。普通应用开发者可以直接从 Python 开始，不需要先理解 C++ 类、头文件或 CMake 工程。

## 选择语言和控制领域

| 领域 | Python API | C++ API | 适用场景 |
|---|---|---|---|
| High-level | [Python](python/high-level.zh-CN.md) | [C++](cpp/high-level.zh-CN.md) | 调用机器人内置动作能力 |
| Low-level | [Python](python/low-level.zh-CN.md) | [C++](cpp/low-level.zh-CN.md) | 自己运行策略并控制关节位置或扭矩 |
| MediaBus | [Python](python/media.zh-CN.md) | [C++](cpp/media.zh-CN.md) | 订阅摄像头、麦克风和编码帧 |

## 如何选择

- 使用 Python 包、希望快速完成导入和业务验证：直接进入 Python API。
- 开发 native 应用、需要 CMake、头文件或 C++ 回调类型：进入 C++ API。
- Python 与 C++ 的能力边界并非在所有平台上完全相同；以对应语言页面标注的部署和平台限制为准。
- 需要原始 DDS / RPC、QoS 或协议字段：进入 [高级主题](../advanced/README.zh-CN.md)。

如果还没有确定 High-level / Low-level，先阅读 [核心概念](../core-concepts/README.zh-CN.md)；如果尚未完成构建和只读验证，先阅读 [操作指南](../how-to/README.zh-CN.md)。
