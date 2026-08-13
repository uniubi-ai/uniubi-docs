# High-level：使用机器人内置动作

[English](high-level-control.md) | **简体中文**

## 目标

使用机器人已经提供的动作和运动能力。应用表达的是动作或运动意图，不单独生成每个关节的位置、速度或扭矩控制量。

典型目标包括：

- 让机器人站立、趴下或执行已有动作；
- 使用机器人已有的行走、转向和速度控制能力；
- 在 ROS 2 中编写调用机器人运动能力的业务节点。

## 这条路径不解决什么问题

如果你要自己训练或运行控制策略，并直接输出每个关节的位置或扭矩，请转到 [Low-level：自定义关节控制策略](low-level-control.zh-CN.md)。

## 选择实现方式

| 开发方式 | 入口 | 适合场景 |
|---|---|---|
| C++ / Python SDK | `MotionHighLevelClient` | 直接使用 SDK 开发控制或观测程序 |
| ROS 2 | `uniubi_motion_bridge` | 编写普通 ROS 2 业务节点，使用标准 topic/service |

如果使用 SDK，先完成 [SDK 通用准备](sdk-first-use.zh-CN.md)。如果使用 ROS 2，直接进入 [启动并验证 Motion bridge](ros2-motion-bridge.zh-CN.md)。

## 对应仓库

- C++ SDK：[`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk)
- Python SDK：[`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py)
- ROS 2 接口和 bridge：[`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) → [`uniubi_ros2`](https://github.com/uniubi-ai/uniubi_ros2)

`uniubi_robot_msgs` 是 ROS 2 构建依赖和接口来源，不是普通业务开发的修改入口。

## 最小成功标准

1. 完成 SDK 构建/导入，或完成 ROS 2 bridge 构建。
2. 先完成只读观测验证。
3. 在具备急停和人工接管条件后，再执行站立、趴下或低速运动等低风险动作。

High-level 控制流程和安全边界见 [C++ 高级控制 SDK](../uniubi_high_level_sdk.zh-CN.md) 及 [ROS 2 Motion bridge 导读](ros2-motion-bridge.zh-CN.md)。
