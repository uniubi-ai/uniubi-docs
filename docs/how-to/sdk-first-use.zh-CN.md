# SDK 通用准备

[English](sdk-first-use.md) | **简体中文**

> 本文不是控制模式选择页。请先从 [How-to 入口](README.zh-CN.md) 选择 High-level 或 Low-level，再回到本文准备 SDK。

## 目标

完成一次 C++ 或 Python SDK 的构建/导入，并在进入控制流程前完成只读验证。

## SDK 与控制模式

| 控制模式 | SDK 入口 | 说明 |
|---|---|---|
| High-level | `MotionHighLevelClient` | 调用机器人内置动作能力，不单独控制每个关节 |
| Low-level | `MotionLowLevelClient` | 运行自己的控制策略，直接控制关节位置或扭矩 |

Low-level 关节控制使用 SDK 的 `MotionLowLevelClient`。ROS 2 Motion Bridge 不提供等价的关节级控制入口。

## 前置条件

- Linux 环境，以及目标架构对应的 SDK 运行库。
- 已按 [机器人网络接入](../core-concepts/device-network.zh-CN.md) 从 App 获取当前设备 IP，并确认登录地址、对外服务端口和通信网卡。外部 High-level 模式必须选择实际连接机器人网络的网卡；大脑侧 High-level 模式必须指定 `eth0.100`。
- 当前设备运行 SDK 程序需要 root 权限；C++ 构建不要求 `sudo`，Python SDK 在大脑上直接安装到系统 `python3`，运行示例时按对应 README 使用 `sudo env` 保留动态库环境。
- C++ SDK 与 Python binding 使用同一套 ABI、架构和版本。
- 先阅读 [构建、安装和交叉编译](../BUILD.zh-CN.md)。

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

如果 Linux 动态库、架构或媒体库不匹配，回到 [构建指南](../BUILD.zh-CN.md) 检查，不要先修改 Python binding。

## 3. 只读验证

先验证导入、连接和观测数据；不要把首次运行直接扩展成 walking、跳跃或低级力矩控制。

成功标准：

- C++ 示例或 Python 包构建/导入成功；
- 能完成只读通信或观测验证；
- 能明确当前 SDK 运行库、架构和 ABI；
- 只有在只读验证通过后，才进入对应的 High-level 或 Low-level 控制文档。

## 下一步

- High-level：[使用机器人内置动作](high-level-control.zh-CN.md) 和 [`uniubi_high_level_sdk.md`](../uniubi_high_level_sdk.zh-CN.md)
- Low-level：[自定义关节控制策略](low-level-control.zh-CN.md) 和 [`uniubi_low_level_sdk.md`](../uniubi_low_level_sdk.zh-CN.md)
- 媒体帧：[`uniubi_media_sdk.md`](../uniubi_media_sdk.zh-CN.md)
- 项目级构建细节：[`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) 和 [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) 的 README
