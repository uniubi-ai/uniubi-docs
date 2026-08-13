# How-to Guides

[English](README.md) | **简体中文**

How-to 文档面向一个明确的开发任务：先说明目标和前置条件，再给出最小步骤、成功标准和下一步项目入口。

## 第一步：选择控制模式

| 目标 | 控制模式 | 导读 |
|---|---|---|
| 使用机器人内置动作能力，不单独控制每个关节 | High-level | [High-level：使用机器人内置动作](high-level-control.zh-CN.md) |
| 自己训练或运行控制策略，直接控制关节位置或扭矩 | Low-level | [Low-level：自定义关节控制策略](low-level-control.zh-CN.md) |

## 第二步：在控制模式内选择实现方式

| 控制模式 | 实现方式 | 入口 |
|---|---|---|
| High-level | C++ / Python SDK | `MotionHighLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |
| High-level | ROS 2 | `uniubi_motion_bridge` → [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) → [`uniubi_ros2`](https://github.com/uniubi-ai/uniubi_ros2) |
| Low-level | C++ / Python SDK | `MotionLowLevelClient` → [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) / [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |

关节级 Low-level 控制统一使用 SDK；ROS 2 Motion Bridge 不提供等价的关节级控制入口。

## 配套导读

| 任务 | 导读 | 适用阶段 |
|---|---|---|
| 确认设备 IP、端口和大脑访问方式 | [设备网络与大脑访问](../core-concepts/device-network.zh-CN.md) | 连接真实机器人之前 |
| 准备构建和安装环境 | [构建、安装和交叉编译](../BUILD.zh-CN.md) | 进入 SDK 或 ROS 2 之前 |
| SDK 通用准备 | [SDK 通用准备](sdk-first-use.zh-CN.md) | 已选 High-level 或 Low-level，准备使用 SDK |
| 编写 ROS 2 业务节点 | [启动并验证 Motion bridge](ros2-motion-bridge.zh-CN.md) | 已选择 High-level + ROS 2 |
| 训练、导出和回放策略 | [训练与策略回放](train-export-replay.zh-CN.md) | Low-level 策略开发 |
| 没有真机，先验证 SDK 链路 | [Mock / Sim2Sim](mock-sim2sim.zh-CN.md) | SDK 链路验证 |

## How-to 的统一写法

每篇导读按以下顺序组织：

1. **目标和范围**：说明解决什么问题，不解决什么问题。
2. **前置条件**：系统、架构、依赖仓库、网络和权限。
3. **最小步骤**：可以直接复制执行的命令或操作。
4. **预期结果**：日志、topic、文件或状态应该是什么。
5. **成功标准**：明确什么算完成。
6. **安全与清理**：停止动作、释放控制权、清理进程或构建目录。
7. **失败排查**：按现象映射到环境、版本、QoS、设备 ID 或 ABI。
8. **继续阅读**：链接到 Core Concepts、API Reference 和对应仓库 README。

How-to 的每一步都应绑定一个可观察的验证结果，避免只写“执行命令”而没有判断标准。
