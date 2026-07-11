# Uniubi SDK Migration Progress

本文档跟踪 SDK 对外 GitHub 仓库迁移进度。当前日期：2026-07-03。

## 状态说明

| 状态 | 含义 |
|---|---|
| `todo` | 尚未开始 |
| `doing` | 正在整理或迁移 |
| `blocked` | 受缺失文件、环境或决策阻塞 |
| `done` | 已完成并通过对应验证 |
| `watch` | 已有结论，但后续迁移时必须重点复核 |

## 总体进度

| 项 | 状态 | 说明 |
|---|---|---|
| 文档分工规则 | `done` | `uniubi-docs` 负责完整教程和跨仓文档；分仓 README 只保留最小闭环 |
| 文档总站内容 | `done` | 已整理到 `local_edit/sdk_all_doc/uniubi-docs`，本轮新增迁移计划和进度跟踪 |
| 旧 `Doc/` 引用清理 | `done` | 已从分仓 README 和总站常规文档中移除旧 SDK 仓内 `doc/` 目录描述 |
| C++ SDK 迁移 | `done` | 已将 C++ SDK 公开头、预编译库、CMake 和 examples 部署到 `uniubi_robot_sdk` |
| Python SDK 迁移 | `done` | 已以 `local_edit/Sdk/Python/` 内容作为 `uniubi_robot_sdk_py` 仓库根 |
| ROS 2 msg/srv 迁移 | `done` | 已将 IDL 与 `ROS2/src/uniubi` 部署到 `uniubi_robot_msgs` |
| ROS 2 example 迁移 | `done` | 已将 `ROS2/examples/src/uniubi_interface_test` 部署到 `uniubi_ros2` |
| examples 仓库迁移 | `done` | 已移除未落地示例承诺，仅保留 README 和总站链接 |
| Linux 构建验证 | `blocked` | 当前整理环境为 macOS，Linux `.so` 构建和 ROS 2 colcon 验证需在 Linux 环境执行 |
| macOS 结构验证 | `done` | C++ SDK 与 Python SDK CMake configure 成功；源码编译可到 Linux `.so` 链接阶段 |

## 仓库进度

### `uniubi-docs`

| 检查项 | 状态 | 说明 |
|---|---|---|
| README 仓库导航 | `done` | 已列出 SDK、Python、msgs、ROS 2、examples 等仓库 |
| 完整接口手册 | `done` | high-level、low-level、media、DDS/ROS 2 文档已拆到 `docs/` |
| 构建指南 | `done` | 已按分仓构建方式更新；MediaBus 仅标记为 aarch64 板内本地能力，Python x86/i386 wheel 默认关闭媒体绑定 |
| 迁移计划 | `done` | 见 `docs/SDK_MIGRATION_PLAN.md` |
| 进度跟踪 | `done` | 本文件 |

### `uniubi_robot_sdk`

| 检查项 | 状态 | 说明 |
|---|---|---|
| README 最小闭环 | `done` | 已有构建、运行、最小 C++ 示例和总站链接 |
| 目录结构 | `done` | 已使用 `include/`、`lib/`、`examples/` |
| include root | `done` | CMake include root 使用 `include`，公开头和 examples 使用 `uniubi/robot_sdk/...` 前缀 |
| 媒体库 | `done` | `MediaBusClient` / 媒体帧订阅仅支持 aarch64 板内本地部署 |
| 安全示例 | `watch` | README 首跑示例应只用 `standUp` / `lieDown`；实际 examples 中如仍有 walking，需要改示例或改文档安全表述 |

### `uniubi_robot_sdk_py`

| 检查项 | 状态 | 说明 |
|---|---|---|
| README 最小闭环 | `done` | 已包含安装、最小 LowLevel/HighLevel 示例、安全提醒和总站链接 |
| 仓库根目录 | `done` | 已以 `local_edit/Sdk/Python/` 内容为仓库根，未嵌套 `Python/` |
| package 名 | `watch` | 必须保持 `robot_motion_sdk` |
| native 模块名 | `watch` | 必须保持 `_uniubi_robot_motion_py_native` |
| C++ SDK 依赖 | `done` | 通过 `UNIUBI_SDK_ROOT` 或同级 `../uniubi_robot_sdk` 找 C++ SDK，未复制 C++ SDK 全量内容 |
| 媒体绑定开关 | `done` | 2026-07-03 版 SDK 通过 `UNIUBI_SDK_ENABLE_MEDIA` 控制 Python 媒体绑定；默认 `aarch64=ON`、`x86_64/i386=OFF`，运行时用 `sdk.MEDIA_ENABLED` 判断 |
| Linux pip 验证 | `blocked` | 需在 Linux 且具备对应 arch `.so` 的环境执行 |

### `uniubi_robot_msgs`

| 检查项 | 状态 | 说明 |
|---|---|---|
| README 最小闭环 | `done` | 已包含目录结构、协议规则、ROS 2 构建和总站链接 |
| ROS 2 package 名 | `watch` | 仓库名是 `uniubi_robot_msgs`，但 ROS 2 package 名必须保持 `uniubi` |
| IDL 归属 | `done` | IDL 的对外归属应统一为本仓 `idl/` |
| msg/srv 文件 | `done` | 已保留 `msg/*.msg` 与 `srv/System.srv` 文件名和字段 |
| colcon 验证 | `blocked` | 需 ROS 2 Linux 环境执行 |

### `uniubi_ros2`

| 检查项 | 状态 | 说明 |
|---|---|---|
| README 最小闭环 | `done` | 已包含前置条件、构建、运行、安全策略和总站链接 |
| msg/srv 边界 | `done` | 本仓不维护 `.msg` / `.srv` |
| package 名 | `done` | `uniubi_interface_test` 保持不变 |
| 依赖关系 | `done` | 保留对 `uniubi_robot_msgs` 提供的 `uniubi` package 的依赖 |
| third_party/jsoncpp | `done` | 保持在 example package 内，未打散相对 include/source 路径 |
| colcon 验证 | `blocked` | 需 ROS 2 Linux 环境执行 |

### `uniubi_examples`

| 检查项 | 状态 | 说明 |
|---|---|---|
| README 最小闭环 | `done` | 只列文档入口和已确认依赖，不承诺未落地示例 |
| DDS direct examples | `done` | 未迁移不存在的代码，仅保留 DDS 文档入口 |
| 安全等级 | `watch` | 示例默认动作必须与文档安全描述一致 |

## 当前显著问题

| 问题 | 影响 | 处理状态 |
|---|---|---|
| 部分文档仍提到旧 SDK 仓内 `doc/` 或 `Doc/` | 与“总站放完整文档”的分工冲突 | `done` |
| DDS 文档曾把 IDL 来源写成 SDK 仓 `IDL/` | 与 `uniubi_robot_msgs` 作为协议源头冲突 | `done` |
| CMake include root 示例可能与 prefixed include 冲突 | 用户复制后编译失败 | `done` |
| MediaBus 平台边界不清 | x86_64/i386 开发者误调 media client 接口 | `done`，已限定为 aarch64 板内本地能力 |
| 实际 high-level 示例如默认执行 `walking` | 与“首次联调安全动作”描述冲突 | `watch`，迁移代码时复核 |
| Python LowLevel 示例写 `set_network_interface("eth0")` | 板内低级控制场景可能误导 | `watch`，后续可拆分板内/远端说明 |

## 验证记录

| 检查 | 状态 | 结果 |
|---|---|---|
| C++ SDK CMake configure | `done` | `cmake -S uniubi_robot_sdk -B /tmp/uniubi_robot_sdk_build -DBUILD_SDK_CPP_EXAMPLES=ON` 成功，库路径解析到 `lib/aarch64/*.so` |
| C++ SDK macOS build | `blocked` | 示例源码编译通过，链接阶段因 macOS `ld` 无法链接 Linux `.so` 报 `unknown file type`；需 Linux 环境最终验证 |
| Python SDK CMake configure | `done` | `cmake -S uniubi_robot_sdk_py -B /tmp/uniubi_robot_sdk_py_build -DUNIUBI_SDK_ROOT=.../uniubi_robot_sdk` 成功 |
| Python SDK macOS build | `blocked` | binding 源码编译通过，链接阶段因 macOS `ld` 无法链接 Linux `.so` 报 `unknown file type`；需 Linux 环境最终验证 |
| ROS 2 package 边界扫描 | `done` | `uniubi_robot_msgs` 保持 package `uniubi`；`uniubi_ros2` 保持 package `uniubi_interface_test` 并依赖 `uniubi` |

## 下一步

1. 在 Linux 环境执行 C++、Python、ROS 2 messages、ROS 2 example 的最小验证。
2. 将 Linux 验证结果回填到本文档，把对应验证项从 `blocked` 改为 `done`。
