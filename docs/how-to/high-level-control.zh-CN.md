# High-level：使用机器人内置动作

[English](high-level-control.md) | **简体中文**

![High-level 双部署拓扑](../core-concepts/images/high-level-dual-deployment.zh-CN.png)

## 目标

使用机器人已经提供的动作和运动能力。应用表达的是动作或运动意图，不单独生成每个关节的位置、速度或扭矩控制量。

典型目标包括：

- 让机器人站立、趴下或执行已有动作；
- 使用机器人已有的行走、转向和速度控制能力；
- 在 ROS 2 中编写调用机器人运动能力的业务节点。

## 常见 High-level 动作

不同产品型号和软件版本开放的动作可能不同。下表根据当前 `motionCapacity` 提供常见动作索引；
设备实际支持的动作、参数字段、取值范围和单位，以运行时能力查询结果为准：C++ 调用
`getMotionCapabilities()`，Python 调用 `get_motion_capabilities()`，ROS 2 调用
`/motion/query_capabilities`。

`startAction()` / `start_action()` 只需发送一次，不需要周期性重复发送；动作是否已经开始或完成，
应通过状态查询确认，不能只依据 RPC 返回成功判断。

速度范围中，`vx` 对应 `lineVelocityX`（m/s），`vy` 对应 `lineVelocityY`（m/s），`wz`
对应 `velocity`（rad/s）；“无”表示调用该动作时不传速度指令。

| 动作类别 | 名称 | 动作 key | 速度指令范围 | 动作说明 |
|---|---|---|---|---|
| 基础姿态 | 趴下 | `laying` | 无 | 让机器人进入稳定趴卧姿态。 |
| 基础姿态 | 站立 | `standing` | 无 | 让机器人进入稳定站立姿态。 |
| 行走与运动 | 行走 | `walking` | 慢速：`vx [-1.5, 1.5]`，`vy [-1, 1]`，`wz [-3, 3]`；快速：`vx [-2.5, 3]`，`vy [-1, 1]`，`wz [-3, 3]` | 控制前后、侧向和转向运动；默认使用慢速档。 |
| 行走与运动 | 原地踏步 | `tweak` | `vx/vy [-0.2, 0.2]`，`wz [-0.5, 0.5]` | 执行原地踏步或低速微动。 |
| 特殊姿态 | 双足站立 | `bipedStand` | `vx/vy [-0.3, 0.3]`，`wz [-1.5, 1.5]` | 以后腿支撑进入双足站立姿态。 |
| 特殊姿态 | 倒立 | `handstand` | `vx/vy [-0.3, 0.3]`，`wz [-1.5, 1.5]` | 以前腿支撑进入倒立姿态。 |
| 特殊姿态 | 左侧站立 | `leftSideStand` | `vx/vy [-0.3, 0.3]`，`wz [-1.5, 1.5]` | 进入左侧支撑的侧立姿态。 |
| 特殊姿态 | 右侧站立 | `rightSideStand` | `vx/vy [-0.3, 0.3]`，`wz [-1.5, 1.5]` | 进入右侧支撑的侧立姿态。 |
| 互动展示 | 身体摆动 | `waveBody` | `vx [-0.06, 0.05]`，`vy [-0.23, 0.23]`，`wz [-0.35, 0.35]` | 执行身体摆动展示动作。 |
| 互动展示 | 招手 | `waveHand` | 无 | 执行抬腿招手展示动作。 |
| 互动展示 | 坐姿画心 | `heartSit` | 无 | 进入坐姿并执行画心展示动作。 |
| 跳跃动作 | 前跳 | `jumpForward` | 无 | 向前完成一次跳跃。 |
| 跳跃动作 | 前空翻 | `jumpFrontflip` | 无 | 完成一次前空翻。 |
| 跳跃动作 | 侧空翻 | `jumpSideflip` | 无 | 完成一次侧空翻。 |
| 跳跃动作 | 左侧空翻 | `jumpLeftSideflip` | 无 | 完成一次左侧空翻。 |
| 跳跃动作 | 后空翻 | `jumpBackflip` | 无 | 完成一次后空翻。 |
| 跳跃动作 | 双后空翻 | `jumpDoubleBackflip` | 无 | 完成一次双后空翻。 |
| 跳跃动作 | 双侧空翻 | `jumpDoubleSideflip` | 无 | 完成一次双侧空翻。 |
| 跳跃动作 | 双左侧空翻 | `jumpDoubleLeftSideflip` | 无 | 完成一次双左侧空翻。 |
| 安全控制 | 紧急停止 | `emergencyStop` | 无 | 请求机器人立即进入紧急停止流程。 |

### 选择 `walking` 控制档位

`walking` 通过可选的字符串参数 `controlProfile` 选择控制档位。当前支持：

- `"slow"`：慢速档，也是默认档位。
- `"fast"`：快速档。

能力配置中的数字 `id`（例如 `0` / `1`）是机器人内部 profile ID，不能作为
High-level RPC 的 `controlProfile` 参数；传入数字会被服务端以参数类型错误拒绝。
切换档位时建议先将三轴速度清零，并在一次全量参数调用中明确传入三轴：

```text
highlevel> start walking {"controlProfile":"slow","lineVelocityX":0.0,"lineVelocityY":0.0,"velocity":0.0}
highlevel> set {"controlProfile":"fast","lineVelocityX":0.0,"lineVelocityY":0.0,"velocity":0.0}
highlevel> state
```

确认设置请求成功且机器人保持零速稳定后，再逐步设置目标速度。`set` 只修改当前动作参数，
不会切换动作；部分服务端版本的状态查询不回传档位名称，不能只靠状态 JSON 验证档位。

## 先选择应用部署位置

High-level 真机应用支持两种部署模式。两种模式下，内置运动服务都继续运行在机器人端；变化的只是业务应用与 SDK 客户端的位置。

| 部署模式 | 应用位置 | 网络与目标选择 |
|---|---|---|
| 外部主机 | Linux PC 或工控机 | 选择实际连接机器人网络的主机网卡，再用目标设备 ID（SN）创建客户端。SN 可在 Uniubi App 的“基础信息”页面查看，也可通过 SDK discovery 获取。 |
| 板内 | 机器人大脑 | 不需要设备 ID，使用板内单设备客户端重载。 |

外部主机使用 discovery 时，按以下顺序执行：

1. 先注册发现回调，并设置实际连接机器人网络的网卡。
2. 再初始化 SDK service。
3. 发起发现。`true` 只表示请求已发出；设备响应通过回调异步到达。
4. 5 秒内没有任何回调时，检查网卡和机器人状态后重试发现。
5. 按 SN 去重，并由应用或操作员明确选择目标机器人；不要静默自动选择第一台。若已知机器人 IP，可将它与回调 `info` 中 `network.ether.ipv4Addr`、`network.wlan.ipv4Addr`、`network.hotspot.ipv4Addr`、`network.mobile.ipv4Addr` 比对，筛出对应 SN。

IP 只用于网络可达性和筛选发现结果；创建 High-level 客户端时仍传入设备 ID（SN），不能把 IP 当作 `device_id`。

Low-level 真机的部署边界不同：关节控制应用仍运行在板内。具体见 Low-level 文档。

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

## 真机取权前：先断开遥控器

申请 High-level 控制权前，关闭遥控器，或长按遥控器 `M` 键切换，直到听到“遥控器连接已断开”
的语音提示。遥控器仍连接时，High-level 无法取得控制权；只读检查不要求断开遥控器。

High-level 控制过程中如遇紧急情况，可再次按 `M` 键，直到听到“遥控器已连接”的语音提示，
再开始使用遥控器接管。

![遥控器按键示意图，M 键位于手柄正面下方中央](images/remote-controller-buttons.png)

_此图只用于定位遥控器按键；High-level 取权以本节文字说明的断连前置条件为准。_

## 最小成功标准

1. 完成 SDK 构建/导入，或完成 ROS 2 bridge 构建。
2. 先完成只读观测验证。
3. 触发 `laying` 以外的动作前，先启动三轴速度均为 0 的 `walking`，并通过状态查询确认
   实际动作已经进入 `walking`，再触发目标动作。`laying` 不要求这一步前置切换。
4. 在具备急停和人工接管条件后，再执行站立、趴下或低速运动等低风险动作。

High-level 控制流程和安全边界见 [Python API](../api-reference/python/high-level.zh-CN.md)、[C++ API](../api-reference/cpp/high-level.zh-CN.md) 及 [ROS 2 Motion bridge 导读](ros2-motion-bridge.zh-CN.md)。

外部主机 High-level C++ SDK、Python SDK 和 ROS 2 路径均已完成真机验证；使用时都必须选择实际连接机器人网络的网卡，并传入目标设备 ID（SN）。
