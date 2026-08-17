# 宇泛开发者文档

[English](README.md) | **简体中文**

Uniubi 开源开发文档中心，帮助你从具体任务开始，经过导读和最小验证，再进入对应仓库。

> 二次开发权限和具身智能开发平台资料请统一从[具身智能开发者平台](https://www.uniubi.com/developer/embodied)获取；如尚未开通权限，请按页面指引登录或提交申请。

<a id="quick-start"></a>
## 快速开始

根 README 先帮助你判断控制模式；选择 High-level 时再确定应用运行位置，最后选择实现方式和具体仓库。不要先按语言或仓库选择入口。

> 需要连接真实机器人时，先阅读 [机器人网络接入](docs/core-concepts/device-network.zh-CN.md)，从 App 获取设备 IP，确认登录地址、对外服务端口和通信网卡；仅进行 Mock / Sim2Sim、离线构建或训练时可按需跳过。

### 1. 选择控制模式

| 你要做什么 | 控制模式 | 先读哪篇导读 |
|---|---|---|
| 使用机器人内置动作能力，不单独控制每个关节 | High-level | [High-level：使用机器人内置动作](docs/how-to/high-level-control.zh-CN.md) |
| 自己训练或运行控制策略，直接控制关节位置或扭矩 | Low-level | [Low-level：自定义关节控制策略](docs/how-to/low-level-control.zh-CN.md) |

### 2. 如果选择 High-level，再选择应用运行位置

| 运行位置 | 适用方式 | 连接真机时需要什么 |
|---|---|---|
| 外部 Linux PC / 工控机 | 应用不部署到机器人“大脑” | 能够到达机器人的实际网卡 + 设备 ID（机器人 SN） |
| 机器人“大脑” | 应用与 SDK 部署在板载计算平台 | 机器人内部通信网卡；板载单设备客户端无需设备 ID |

两种方式调用相同的 High-level 能力，实时运动服务始终运行在机器人端。设备 ID 可在 Uniubi App 的“基础信息”页面查看，也可通过 SDK 设备发现获取。完整边界见 [High-level 双部署架构](docs/core-concepts/README.zh-CN.md#high-level-应用的两种部署位置)。

### 3. 再选择实现方式

| 控制模式 | 可选实现方式 | 对应入口 |
|---|---|---|
| High-level | C++ / Python SDK | `MotionHighLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |
| High-level | ROS 2 | `uniubi_motion_bridge` → [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) → [`uniubi_ros2`](https://github.com/uniubi-ai/uniubi_ros2) |
| Low-level | C++ / Python SDK | `MotionLowLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |

关节级 Low-level 控制统一使用 SDK；ROS 2 Motion Bridge 不提供等价的关节级控制入口。

### 4. 从具体任务开始

确定控制模式和实现方式后，直接进入当前要完成的任务：

- [构建和安装 SDK](docs/BUILD.zh-CN.md)：准备本机或板端的 C++ / Python 开发环境。
- [使用 High-level 控制](docs/how-to/high-level-control.zh-CN.md)：通过外部电脑或机器人“大脑”使用 High-level 接口，读取状态并调用内置动作；目标可为 Mock / Sim2Sim 或真实机器人。
- [使用 ROS 2 Motion Bridge](docs/how-to/ros2-motion-bridge.zh-CN.md)：通过 ROS 2 接入 High-level 能力。
- [使用 Low-level 控制](docs/how-to/low-level-control.zh-CN.md)：先在安全吊架上验证姿态，再到空旷平整地面验证策略行走。
- [训练、导出和回放策略](docs/how-to/train-export-replay.zh-CN.md)：开发并部署自己的 Low-level 策略。
- [读取传感器与运动观测](docs/how-to/read-sensor-data.zh-CN.md)：读取 GPS、UWB、电机、IMU、电源和 High-level Walk 里程计。
- [查询设备状态](docs/how-to/query-device-status.zh-CN.md)：区分完整系统状态与 Low-level 轻量电源观测。
- [使用语音、灯光和媒体帧](docs/how-to/use-media-and-device-io.zh-CN.md)：接入语音播放、摄像头灯光、视频和麦克风数据。

每篇导读都从一个具体任务开始，不要求先认识全部仓库，也不要求先读完整 API。其他开发和排查专题可在 [操作指南](docs/how-to/README.zh-CN.md) 中按需查阅。

<a id="core-concepts"></a>
## 核心概念

先理解大小脑分工、High-level / Low-level 的定义、实现边界和仓库职责，再进入具体操作指南或 API 文档。

包含：

- 大脑与小脑的职责分工；
- 设备 IP、登录方式与服务端口边界；
- High-level / Low-level 控制抽象；
- 控制权生命周期与各层组件职责。

[进入核心概念](docs/core-concepts/README.zh-CN.md)

<a id="how-to"></a>
## 操作指南

按具体开发任务完成环境准备、最小验证和后续操作。

包含：

- SDK 构建、安装和首次连接；
- USB、以太网外设接入与直流供电；
- High-level、Low-level 实机控制；
- ROS 2 Motion Bridge 接入；
- GPS、UWB、设备状态、语音、灯光和媒体数据接入；
- Low-level 策略训练、导出和回放。

[进入操作指南](docs/how-to/README.zh-CN.md)

<a id="api-reference"></a>
## API 参考

在确定控制模式并完成最小验证后，查阅 SDK 和媒体接口的字段、生命周期与示例。

包含：

- High-level SDK API；
- Low-level SDK API；
- 摄像头、麦克风和编码帧等 Media SDK API。

[进入 API 参考](docs/api-reference/README.zh-CN.md)

<a id="advanced"></a>
## 高级主题

DDS / ROS 2 直连、协议映射和特殊集成等内容只在确有需要时阅读。

包含：

- DDS / RPC 直连接入；
- Discovery、QoS 和底层协议字段；
- ROS 2 topic、service 与 DDS wire contract 映射。

[进入高级主题](docs/advanced/README.zh-CN.md)

## 安全说明

真机申请 High-level 控制权前，必须先让遥控器断开：关闭遥控器，或长按遥控器 `M` 键切换，
直到听到“遥控器连接已断开”的语音提示。遥控器仍连接时，High-level 无法取得控制权；只读检查不要求断开遥控器。

首次 High-level 真实机器人联调应先完成只读检查，再以三个速度字段均显式为 0 的 `walking`
验证取权、动作启动和状态反馈。`standing` / `laying` 受当前姿态和服务端状态机约束，不能作为
通用的往返测试流程。触发 `laying` 以外的动作前，应先进入全零速 `walking`，通过状态查询确认
实际动作已经是 `walking`，再触发目标动作；`laying` 不要求这一步前置切换。
带非零速度的行走和其他 locomotion 只能在空旷、平整、无障碍场地验证，
且必须有人值守并保持急停可触达。

Low-level 行走策略首次验证时，应将机器人可靠固定在安全吊架上并保持四脚完全腾空，只验证 `stand` 和 `lay`。确认姿态、关节方向和急停行为正常后，再落地按 `stand` → `walk` → `stop` → `lay` 验证；禁止在悬空状态执行 `walk`。

跳跃、双足站立、倒立、阻尼和关节力矩控制需要匹配的测试场地、可触达的急停以及明确的人工接管方案。

## 许可证

本仓库中的 UniUbi 原创文档和代码使用 Apache License 2.0。详见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
