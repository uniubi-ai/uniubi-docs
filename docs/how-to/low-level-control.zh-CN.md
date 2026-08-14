# Low-level：自定义关节控制策略

[English](low-level-control.md) | **简体中文**

## 目标

自己训练或运行控制策略，并直接输出每个关节的位置或扭矩控制量。

典型目标包括：

- 在仿真中训练自己的 locomotion 策略；
- 将策略导出并接入机器人运行时；
- 自己实现关节位置或扭矩控制器，并验证控制周期、关节顺序和安全策略。

## 这条路径不解决什么问题

如果只是调用机器人内置的站立、行走、转向或其他动作能力，不需要自己控制每个关节，请转到 [High-level：使用机器人内置动作](high-level-control.zh-CN.md)。

## 统一使用 SDK

关节级 Low-level 控制统一使用 SDK 的 `MotionLowLevelClient`：

| 开发方式 | 入口 | 对应仓库 |
|---|---|---|
| C++ | `MotionLowLevelClient` | [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) |
| Python | `MotionLowLevelClient` | [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |

ROS 2 Motion Bridge 不提供等价的关节级控制入口。直接使用 DDS/RPC 或修改协议属于协议级维护/特殊集成路径，不是普通 Low-level 开发入口。

## 推荐开发路径

1. **训练或准备策略**：进入 [训练、导出和回放策略](train-export-replay.zh-CN.md)；确认 checkpoint 能在仿真中回放。
2. **准备 SDK**：阅读 [SDK 通用准备](sdk-first-use.zh-CN.md)，确认 C++/Python binding、头文件、运行库、架构和 ABI 匹配。
3. **验证 SDK 链路**：没有真机时，使用 [Mock / Sim2Sim](mock-sim2sim.zh-CN.md) 验证策略、仿真 bridge 和 SDK client 的闭环。
4. **进入真实机器人**：先只读，再进行低风险控制；确认控制周期、关节顺序、板端推理格式、急停和人工接管条件。

## SDK 与模型关节顺序

当前 `MotorLayout` 返回 12 个关节，SDK/机器人采用 leg-major 顺序：

```text
FL_ABAD, FL_HIP, FL_KNEE,
FR_ABAD, FR_HIP, FR_KNEE,
RL_ABAD, RL_HIP, RL_KNEE,
RR_ABAD, RR_HIP, RR_KNEE
```

Low-level 程序必须在 `kConnected` 后调用 `client.get_motor_layout()`，校验关节数量和
实际顺序，再使用每个 `MotorInfo` 返回的 `limb_no`、`joint_no` 构造控制帧。不能仅
依赖硬编码数组下标；数量或顺序不匹配时，应在 `set_motion_enable(true)` 前拒绝运行。

模型输入输出顺序由模型训练和导出契约决定，可能不同于 SDK 的 leg-major 顺序。
模型运行程序必须分别声明 SDK 顺序和模型顺序，并在构造模型输入前、解析模型输出后
显式完成双向重排。替换模型时还需同时核对 observation 定义、归一化、action scale、
输入输出 shape 和控制频率，不能只替换 ONNX 文件。

板端运行 C++ 或 Python Low-level TensorRT 控制进程时，建议通过 `taskset -c 2` 绑定 CPU 2，
以减少调度抖动，使观测数据获取耗时和 50 Hz 控制周期更稳定。如果设备已有不同的
CPU 隔离或核分配方案，应选择实际分配给该控制进程的独立核心。

TensorRT 参考实现：

- C++：[`example_lowlevel_tensorrt.cpp`](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/example_lowlevel_tensorrt.cpp)
- Python：[`example_lowlevel_tensorrt.py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/examples/example_lowlevel_tensorrt.py)

两个板端示例都输入 ONNX，并在每次进程启动时重新构建 TensorRT engine，不依赖
PyTorch；C++ 示例还显式关闭 TF32，使用严格 FP32。C++ 示例提供
`--validate-only`，可在不初始化 SDK、不连接机器人的情况下先验证 ONNX 解析、
engine 构建和一次零输入推理。替换模型时不得复用未经核对的关节重排或
observation 契约。

## 实机分阶段验证

首次验证时，将机器狗可靠固定在安全吊架上，保持四脚完全腾空，只验证 `stand` 和
`lay`。确认姿态、关节方向和急停均正常后，将机器狗放到空旷、平整、无障碍地面，
再按 `stand` → `walk` → `stop` → `lay` 的顺序验证策略行走。不要在四脚腾空时执行
`walk`；两个阶段都必须保持急停可触达并由专人值守。

## 详细接口

- [Python Low-level API](../api-reference/python/low-level.zh-CN.md)
- [C++ Low-level API](../api-reference/cpp/low-level.zh-CN.md)
- [`uniubi_robot_sdk` Low-level 示例](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/example_lowlevel.cpp)
- [`uniubi_robot_sdk_py` Low-level 示例](https://github.com/uniubi-ai/uniubi_robot_sdk_py/tree/main/examples)

低级位置或扭矩控制必须在空旷场地、急停可触达、有人值守的条件下验证。仿真或 Mock 通过不等于真实机器人安全通过。
