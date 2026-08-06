# Low-level：自定义关节控制策略

## 目标

自己训练或运行控制策略，并直接输出每个关节的位置或扭矩控制量。

典型目标包括：

- 在仿真中训练自己的 locomotion 策略；
- 将策略导出并接入机器人运行时；
- 自己实现关节位置或扭矩控制器，并验证控制周期、关节顺序和安全策略。

## 这条路径不解决什么问题

如果只是调用机器人内置的站立、行走、转向或其他动作能力，不需要自己控制每个关节，请转到 [High-level：使用机器人内置动作](high-level-control.md)。

## 统一使用 SDK

关节级 Low-level 控制统一使用 SDK 的 `MotionLowLevelClient`：

| 开发方式 | 入口 | 对应仓库 |
|---|---|---|
| C++ | `MotionLowLevelClient` | [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) |
| Python | `MotionLowLevelClient` | [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |

ROS 2 Motion Bridge 不提供等价的关节级控制入口。直接使用 DDS/RPC 或修改协议属于协议级维护/特殊集成路径，不是普通 Low-level 开发入口。

## 推荐开发路径

1. **训练或准备策略**：进入 [训练、导出和回放策略](train-export-replay.md)；确认 checkpoint 能在仿真中回放。
2. **准备 SDK**：阅读 [SDK 通用准备](sdk-first-use.md)，确认 C++/Python binding、头文件、运行库、架构和 ABI 匹配。
3. **验证 SDK 链路**：没有真机时，使用 [Mock / Sim2Sim](mock-sim2sim.md) 验证策略、仿真 bridge 和 SDK client 的闭环。
4. **进入真实机器人**：先只读，再进行低风险控制；确认控制周期、关节顺序、板端推理格式、急停和人工接管条件。

## 详细接口

- [C++ 低级控制 SDK](../uniubi_low_level_sdk.md)
- [`uniubi_robot_sdk` Low-level 示例](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/example_lowlevel.cpp)
- [`uniubi_robot_sdk_py` Low-level 示例](https://github.com/uniubi-ai/uniubi_robot_sdk_py/tree/main/examples)

低级位置或扭矩控制必须在空旷场地、急停可触达、有人值守的条件下验证。仿真或 Mock 通过不等于真实机器人安全通过。
