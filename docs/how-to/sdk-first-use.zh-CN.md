# SDK 通用准备

[English](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/sdk-first-use.md) | **简体中文**

> 本文不是控制模式选择页。请先从 [How-to 入口](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/README.zh-CN.md) 选择 High-level 或 Low-level，再回到本文准备 SDK。

## 目标

完成一次 C++ 或 Python SDK 的构建/导入，并在进入控制流程前完成只读验证。

## SDK 与控制模式

| 控制模式 | SDK 入口 | 说明 |
|---|---|---|
| High-level | `MotionHighLevelClient` | 调用机器人内置动作能力，不单独控制每个关节 |
| Low-level | `MotionLowLevelClient` | 运行自己的控制策略，直接控制关节位置或扭矩 |

Low-level 关节控制使用 SDK 的 `MotionLowLevelClient`。ROS 2 Motion Bridge 不提供等价的关节级控制入口。

## 选择部署模式

| 模式 | High-level 真机 | Low-level 真机 |
|---|---|---|
| 外部 Linux PC / 工控机 | 支持。选择实际连接机器人网络的网卡，并传入目标设备 ID（SN）；SN 可在 Uniubi App 的“基础信息”页面查看，也可通过 SDK discovery 获取。内置运动服务仍运行在机器人端。 | 不属于当前真机部署路径；关节控制应用应运行在板内。 |
| 机器人大脑 | 支持，不需要设备 ID。 | 当前真机关节控制要求运行在板内。 |

外部主机做 High-level discovery 时，顺序是：先注册发现回调并设置网卡，再初始化 service。发现是异步的：返回 `true` 只表示请求已发出。最多等待 5 秒接收回调；没有回调时重试；按 SN 去重，并要求明确选择目标设备，不自动取第一台。已知机器人 IP 时，可与回调 `info` 的 `network.*.ipv4Addr` 比对，筛出对应 SN；最终客户端仍传 SN，而不是 IP。

外部主机 High-level C++ SDK、Python SDK 和 ROS 2 路径均已完成真机验证。三种路径都必须选择实际连接机器人网络的网卡，并使用目标设备 ID（SN）寻址机器人。

## 前置条件

- Linux 环境，以及目标架构对应的 SDK 运行库。
- 已按 [机器人网络接入](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/core-concepts/device-network.zh-CN.md) 从 App 获取当前设备 IP，并确认登录地址、对外服务端口和通信网卡。外部 High-level 模式必须选择实际连接机器人网络的网卡；大脑侧 High-level 模式必须指定 `eth0.100`。
- 外部 Linux High-level 应用不统一要求 root；板载、Low-level 与 Media 运行时按目标设备要求配置权限。C++ 构建不要求 `sudo`；Python SDK 在大脑上直接安装到系统 `python3`，板载示例按对应 README 使用 `sudo env` 保留动态库环境。
- C++ SDK 与 Python binding 使用同一套 ABI、架构和版本。
- 先阅读 [构建、安装和交叉编译](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/BUILD.zh-CN.md)。

## 1. 选择入口

| 语言 | 项目 | 适合场景 |
|---|---|---|
| C++ | [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) | C++ 控制、观测和示例开发 |
| Python | [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) | Python 控制、观测和策略接入 |

## 2. 完成最小构建或导入

C++ 项目先完成 configure 和 examples 构建：

```bash
cd uniubi_robot_sdk
cmake -S . -B build
cmake --build build -j
```

Python 项目需要先准备 C++ SDK，再安装 binding：

```bash
cd uniubi_robot_sdk_py
export UNIUBI_SDK_ROOT=/path/to/uniubi_robot_sdk
UNIUBI_SDK_ROOT="$UNIUBI_SDK_ROOT" python3 -m pip install .
python3 -c "import robot_motion_sdk as sdk; print(sdk.MotionHighLevelClient)"
```

如果 Linux 动态库、架构或媒体库不匹配，回到 [构建指南](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/BUILD.zh-CN.md) 检查，不要先修改 Python binding。

## 3. 只读验证

先验证导入、连接和观测数据；不要把首次运行直接扩展成 walking、跳跃或低级力矩控制。

成功标准：

- C++ 示例或 Python 包构建/导入成功；
- 能完成只读通信或观测验证；
- 能明确当前 SDK 运行库、架构和 ABI；
- 只有在只读验证通过后，才进入对应的 High-level 或 Low-level 控制文档。

## 下一步

- High-level：[使用机器人内置动作](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/high-level-control.zh-CN.md)、[Python API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/high-level.zh-CN.md) 或 [C++ API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/high-level.zh-CN.md)
- Low-level：[自定义关节控制策略](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/low-level-control.zh-CN.md)、[Python API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/low-level.zh-CN.md) 或 [C++ API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/low-level.zh-CN.md)
- 媒体帧：[Python API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/media.zh-CN.md) 或 [C++ API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/media.zh-CN.md)
- 项目级构建细节：[`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) 和 [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) 的 README
