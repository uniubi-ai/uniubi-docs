# 操作指南

[English](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/README.md) | **简体中文**

操作指南面向一个明确的开发任务：先说明目标和前置条件，再给出最小步骤、成功标准和下一步项目入口。

> 尚未确定控制模式、应用运行位置或实现方式时，请先阅读[快速开始](https://github.com/uniubi-ai/uniubi-docs/blob/main/README.zh-CN.md#快速开始)。

## 环境与设备接入

| 任务 | 导读 | 适用阶段 |
|---|---|---|
| 从 App 获取设备 IP，并确认登录地址和服务端口 | [机器人网络接入](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/core-concepts/device-network.zh-CN.md) | 连接真实机器人之前 |
| 连接 USB、网络或其他上装外设并为其供电 | [连接外设](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/connect-peripherals.zh-CN.md) | 部署板载感知或其他外设应用之前 |
| 准备构建和安装环境 | [构建、安装和交叉编译](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/BUILD.zh-CN.md) | 进入 SDK 或 ROS 2 之前 |
| SDK 通用准备 | [SDK 通用准备](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/sdk-first-use.zh-CN.md) | 已选 High-level 或 Low-level，准备使用 SDK |

## 控制与集成

| 任务 | 导读 | 适用阶段 |
|---|---|---|
| 使用机器人内置动作能力，不单独控制每个关节 | [High-level：使用机器人内置动作](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/high-level-control.zh-CN.md) | 已在快速开始中选择 High-level |
| 运行自己的控制策略，直接控制关节位置或扭矩 | [Low-level：自定义关节控制策略](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/low-level-control.zh-CN.md) | 已在快速开始中选择 Low-level |
| 编写 ROS 2 业务节点 | [启动并验证 Motion bridge](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/ros2-motion-bridge.zh-CN.md) | 已选择 High-level + ROS 2 |

## 应用数据与设备能力

| 任务 | 导读 | 支持范围 |
|---|---|---|
| 读取 GPS、UWB、电机、IMU、电源和 Walk 里程计 | [读取传感器与运动观测](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/read-sensor-data.zh-CN.md) | GPS/UWB 支持 High-level 与 Low-level；Walk 里程计仅 High-level |
| 查询设备、电池和网络状态 | [查询设备状态](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/query-device-status.zh-CN.md) | 完整状态仅 High-level；Low-level 只有轻量电源观测 |
| 使用语音、摄像头灯光、视频和麦克风数据 | [使用语音、灯光和媒体帧](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/use-media-and-device-io.zh-CN.md) | 语音/灯光仅 High-level；MediaBus 可由两类客户端创建 |

## 训练与验证

| 任务 | 导读 | 适用阶段 |
|---|---|---|
| 训练、导出和回放策略 | [训练与策略回放](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/train-export-replay.zh-CN.md) | Low-level 策略开发 |
| 没有真机，先验证 SDK 链路 | [Mock / Sim2Sim](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/mock-sim2sim.zh-CN.md) | SDK 链路验证 |
