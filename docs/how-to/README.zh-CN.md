# 操作指南

[English](README.md) | **简体中文**

操作指南面向一个明确的开发任务：先说明目标和前置条件，再给出最小步骤、成功标准和下一步项目入口。

## 第一步：选择控制模式

| 目标 | 控制模式 | 导读 |
|---|---|---|
| 使用机器人内置动作能力，不单独控制每个关节 | High-level | [High-level：使用机器人内置动作](high-level-control.zh-CN.md) |
| 自己训练或运行控制策略，直接控制关节位置或扭矩 | Low-level | [Low-level：自定义关节控制策略](low-level-control.zh-CN.md) |

## 第二步：High-level 选择应用运行位置

| 运行位置 | 真机通信要求 | 关键边界 |
|---|---|---|
| 外部 Linux PC / 工控机 | 实际通信网卡 + 设备 ID（机器人 SN） | 只移动应用位置；内置运动服务仍在机器人端 |
| 机器人“大脑” | 机器人内部通信网卡；板载单设备客户端无需设备 ID | 应用和 SDK 运行在板载计算平台 |

设备 ID 可在 Uniubi App 的“基础信息”页面查看，也可通过 SDK 设备发现获取。Low-level 真机控制不提供外部主机路径，必须运行在机器人大脑侧。

## 第三步：在控制模式内选择实现方式

| 控制模式 | 实现方式 | 入口 |
|---|---|---|
| High-level | C++ / Python SDK | `MotionHighLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |
| High-level | ROS 2 | `uniubi_motion_bridge` → [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) → [`uniubi_ros2`](https://github.com/uniubi-ai/uniubi_ros2) |
| Low-level | C++ / Python SDK | `MotionLowLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |

关节级 Low-level 控制统一使用 SDK；ROS 2 Motion Bridge 不提供等价的关节级控制入口。

## 配套导读

| 任务 | 导读 | 适用阶段 |
|---|---|---|
| 从 App 获取设备 IP，并确认登录地址和服务端口 | [机器人网络接入](../core-concepts/device-network.zh-CN.md) | 连接真实机器人之前 |
| 准备构建和安装环境 | [构建、安装和交叉编译](../BUILD.zh-CN.md) | 进入 SDK 或 ROS 2 之前 |
| SDK 通用准备 | [SDK 通用准备](sdk-first-use.zh-CN.md) | 已选 High-level 或 Low-level，准备使用 SDK |
| 编写 ROS 2 业务节点 | [启动并验证 Motion bridge](ros2-motion-bridge.zh-CN.md) | 已选择 High-level + ROS 2 |
| 训练、导出和回放策略 | [训练与策略回放](train-export-replay.zh-CN.md) | Low-level 策略开发 |
| 没有真机，先验证 SDK 链路 | [Mock / Sim2Sim](mock-sim2sim.zh-CN.md) | SDK 链路验证 |
