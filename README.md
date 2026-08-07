# Uniubi Docs

Uniubi 开源开发文档中心，帮助你从具体任务开始，经过导读和最小验证，再进入对应仓库。

## Quick Start

根 README 先帮助你判断控制模式，再引导你选择实现方式和具体仓库。不要先按语言或仓库选择入口。

### 1. 选择控制模式

| 你要做什么 | 控制模式 | 先读哪篇导读 |
|---|---|---|
| 使用机器人内置动作能力，不单独控制每个关节 | High-level | [High-level：使用机器人内置动作](docs/how-to/high-level-control.md) |
| 自己训练或运行控制策略，直接控制关节位置或扭矩 | Low-level | [Low-level：自定义关节控制策略](docs/how-to/low-level-control.md) |

### 2. 再选择实现方式

| 控制模式 | 可选实现方式 | 对应入口 |
|---|---|---|
| High-level | C++ / Python SDK | `MotionHighLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |
| High-level | ROS 2 | `uniubi_motion_bridge` → [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) → [`uniubi_ros2`](https://github.com/uniubi-ai/uniubi_ros2) |
| Low-level | C++ / Python SDK | `MotionLowLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |

关节级 Low-level 控制统一使用 SDK；ROS 2 Motion Bridge 不提供等价的关节级控制入口。

### 3. 进入配套流程

确定控制模式后，再按需要进入配套流程：

- [训练、导出和回放策略](docs/how-to/train-export-replay.md)：训练或部署自己的 Low-level 策略。
- [Mock / Sim2Sim](docs/how-to/mock-sim2sim.md)：没有真机时验证 SDK 链路。

每篇导读都从一个具体任务开始，不要求你先认识全部仓库，也不要求先读完整 API。

## Core Concepts

先理解 High-level / Low-level 的定义、实现边界和仓库职责，再进入具体 How-to 或 API 文档。

[进入 Core Concepts](docs/core-concepts/README.md)

## How-to

按具体开发任务完成环境准备、最小验证和后续操作。

[进入 How-to 指南](docs/how-to/README.md)

## API Reference

在确定控制模式并完成最小验证后，查阅 SDK 和媒体接口的字段、生命周期与示例。

[进入 API Reference](docs/api-reference/README.md)

## Advanced

DDS / ROS 2 直连、协议映射和特殊集成等内容只在确有需要时阅读。

[进入 Advanced](docs/advanced/README.md)

## 安全说明

首次实机联调按“只读 → 站立/趴下 → 低速运动 → 完整动作”的顺序进行。walking、跳跃、双足、倒立、damp 和低级力矩控制必须在空旷场地、急停可触达、有人值守的条件下验证。

首次真实机器人联调建议先做只读验证，再执行站立、趴下等低风险动作。`walking`、`move`、`bipedStand`、`handstand`、`jump*`、`damp` 等动作应在空旷场地、姿态稳定、具备人工接管条件时执行。

## 许可证

本仓库中的 UniUbi 原创文档和代码使用 Apache License 2.0。详见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
