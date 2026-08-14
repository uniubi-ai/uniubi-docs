# Uniubi Docs

[English](README.md) | **简体中文**

Uniubi 开源开发文档中心，帮助你从具体任务开始，经过导读和最小验证，再进入对应仓库。

## Quick Start

根 README 先帮助你判断控制模式，再引导你选择实现方式和具体仓库。不要先按语言或仓库选择入口。

### 1. 选择控制模式

| 你要做什么 | 控制模式 | 先读哪篇导读 |
|---|---|---|
| 使用机器人内置动作能力，不单独控制每个关节 | High-level | [High-level：使用机器人内置动作](docs/how-to/high-level-control.zh-CN.md) |
| 自己训练或运行控制策略，直接控制关节位置或扭矩 | Low-level | [Low-level：自定义关节控制策略](docs/how-to/low-level-control.zh-CN.md) |

### 2. 再选择实现方式

| 控制模式 | 可选实现方式 | 对应入口 |
|---|---|---|
| High-level | C++ / Python SDK | `MotionHighLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |
| High-level | ROS 2 | `uniubi_motion_bridge` → [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) → [`uniubi_ros2`](https://github.com/uniubi-ai/uniubi_ros2) |
| Low-level | C++ / Python SDK | `MotionLowLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |

关节级 Low-level 控制统一使用 SDK；ROS 2 Motion Bridge 不提供等价的关节级控制入口。

### 3. 从具体任务开始

确定控制模式和实现方式后，直接进入当前要完成的任务：

- [构建和安装 SDK](docs/BUILD.zh-CN.md)：准备本机或板端的 C++ / Python 开发环境。
- [使用 High-level 控制](docs/how-to/high-level-control.zh-CN.md)：在真实机器人上读取状态并调用内置动作。
- [使用 ROS 2 Motion Bridge](docs/how-to/ros2-motion-bridge.zh-CN.md)：通过 ROS 2 接入 High-level 能力。
- [使用 Low-level 控制](docs/how-to/low-level-control.zh-CN.md)：先在安全吊架上验证姿态，再到空旷平整地面验证策略行走。
- [训练、导出和回放策略](docs/how-to/train-export-replay.zh-CN.md)：开发并部署自己的 Low-level 策略。

每篇导读都从一个具体任务开始，不要求先认识全部仓库，也不要求先读完整 API。其他开发和排查专题可在 [How-to 指南](docs/how-to/README.zh-CN.md) 中按需查阅。

## Core Concepts

先理解大小脑分工、High-level / Low-level 的定义、实现边界和仓库职责，再进入具体 How-to 或 API 文档。

包含：

- 大脑与小脑的职责分工；
- 设备网络、大脑访问方式与端口边界；
- High-level / Low-level 控制抽象；
- 控制权生命周期与各层组件职责。

[进入 Core Concepts](docs/core-concepts/README.zh-CN.md)

## How-to

按具体开发任务完成环境准备、最小验证和后续操作。

包含：

- SDK 构建、安装和首次连接；
- High-level、Low-level 实机控制；
- ROS 2 Motion Bridge 接入；
- Low-level 策略训练、导出和回放。

[进入 How-to 指南](docs/how-to/README.zh-CN.md)

## API Reference

在确定控制模式并完成最小验证后，查阅 SDK 和媒体接口的字段、生命周期与示例。

包含：

- High-level SDK API；
- Low-level SDK API；
- 摄像头、麦克风和编码帧等 Media SDK API。

[进入 API Reference](docs/api-reference/README.zh-CN.md)

## Advanced

DDS / ROS 2 直连、协议映射和特殊集成等内容只在确有需要时阅读。

包含：

- DDS / RPC 直连接入；
- Discovery、QoS 和底层协议字段；
- ROS 2 topic、service 与 DDS wire contract 映射。

[进入 Advanced](docs/advanced/README.zh-CN.md)

## 安全说明

首次真实机器人联调应先完成只读检查，再验证站立、趴下等低风险动作。行走和其他 locomotion 只能在空旷、平整、无障碍场地验证，且必须有人值守并保持急停可触达。

Low-level 行走策略首次验证时，应将机器人可靠固定在安全吊架上并保持四脚完全腾空，只验证 `stand` 和 `lay`。确认姿态、关节方向和急停行为正常后，再落地按 `stand` → `walk` → `stop` → `lay` 验证；禁止在悬空状态执行 `walk`。

跳跃、双足站立、倒立、阻尼和关节力矩控制需要匹配的测试场地、可触达的急停以及明确的人工接管方案。

## 许可证

本仓库中的 UniUbi 原创文档和代码使用 Apache License 2.0。详见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
