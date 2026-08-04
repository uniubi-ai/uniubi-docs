# Uniubi SDK GitHub Migration Plan

本文档记录从当前 SDK 整理目录迁移到对外 GitHub SDK 仓库的部署计划。当前日期：2026-07-02。

## 1. 目标与边界

目标：

- 将 `local_edit/Sdk` 中的 SDK 相关内容拆分到对外 GitHub 仓库。
- 将 `local_edit/sdk_all_doc` 中已经拆分好的文档覆盖到对应仓库。
- 保持 SDK、Python binding、ROS 2 interface package、ROS 2 example package 的现有构建边界和包名约束。

边界：

- `uniubi-docs` 是跨仓文档总站，放完整教程、跨仓开发路径、架构说明、支持矩阵、故障排查和长期维护文档。
- 各代码仓 README 只保留当前版本最小闭环：仓库说明、安装或构建、最小示例、兼容性、安全提醒、跳转到文档总站。
- 各代码仓 `docs/` 只放与本仓强相关、需要随代码演进的详细说明；不能恢复一个跨仓大而全的 `Doc/` 目录。
- 现有 GitHub 仓库目录为空仓或参考骨架，不作为部署结构的权威来源。实际迁移以当前 SDK 工程结构和包构建要求为准。
- `SDK_SPLIT_PLAN.md` 不参与本轮迁移计划。

## 2. 仓库职责

| 仓库 | 职责 | 不应放入 |
|---|---|---|
| `uniubi-docs` | 文档总站、完整教程、跨仓开发路径、架构、支持矩阵、故障排查、DDS/ROS 2 wire contract 说明 | SDK 二进制库、ROS 2 package 源码、Python binding 源码 |
| `uniubi_robot_sdk` | C++ SDK 公开头、预编译运行库、C++ examples、CMake 工程 | Python binding 源码、ROS 2 msg/srv、完整跨仓教程 |
| `uniubi_robot_sdk_py` | Python package、pybind11 binding、Python examples、Python 构建配置 | C++ SDK 的完整副本、ROS 2 msg/srv |
| `uniubi_robot_msgs` | DDS IDL、ROS 2 msg/srv、协议 schema 的统一源头 | ROS 2 client example、C++/Python SDK |
| `uniubi_ros2` | 基于 `uniubi_robot_msgs` 的 ROS 2 client/example package | `.msg` / `.srv` 定义、C++ SDK 运行库 |
| `uniubi_examples` | 跨 SDK 的可运行 recipes 和组合示例 | 未验证存在的示例、协议定义源文件 |

## 3. 源目录到目标仓库映射

### 3.1 `uniubi-docs`

来源：

- `local_edit/sdk_all_doc/uniubi-docs/README.md`
- `local_edit/sdk_all_doc/uniubi-docs/docs/*.md`

目标：

```text
uniubi-docs/
├── README.md
└── docs/
    ├── BUILD.md
    ├── MIGRATION_PROGRESS.md
    ├── SDK_MIGRATION_PLAN.md
    ├── ros2_dds_interop_overview.md
    ├── uniubi_high_level_sdk.md
    ├── uniubi_low_level_sdk.md
    ├── uniubi_media_sdk.md
    └── uniubi_robot_dds_api.md
```

要求：

- 所有跨仓文档链接必须指向最终 GitHub 仓库 URL 或 `uniubi-docs/docs/...`。
- 不再引用 SDK 仓内的旧 `Doc/` 或 `doc/` 作为完整文档来源。
- 迁移计划和进度文档只在总站维护。

### 3.2 `uniubi_robot_sdk`

来源：

- `local_edit/Sdk/CMakeLists.txt`
- `local_edit/Sdk/cmake/`
- `local_edit/Sdk/Include/`
- `local_edit/Sdk/Lib/`
- `local_edit/Sdk/Examples/`
- `local_edit/sdk_all_doc/uniubi_robot_sdk/README.md`

目标：

```text
uniubi_robot_sdk/
├── README.md
├── CMakeLists.txt
├── cmake/
├── include/
│   └── uniubi/
│       └── robot_sdk/
├── lib/
│   ├── x86_64/
│   ├── aarch64/
│   └── i386/
└── examples/
```

迁移动作：

- `Include/*` 迁移为 `include/uniubi/robot_sdk/*`。
- `Lib/*` 迁移为 `lib/*`。
- `Examples/*` 迁移为 `examples/*`。
- CMake 中所有 `Lib/<arch>`、`Include`、`Examples` 路径同步改为 `lib/<arch>`、`include`、`examples`。
- C++ 示例统一使用 prefixed include：`#include "uniubi/robot_sdk/..."`。
- 对应的 CMake include root 必须是 `${UNIUBI_SDK_ROOT}/include`，不能写到 `${UNIUBI_SDK_ROOT}/include/uniubi/robot_sdk` 后再使用 prefixed include。

当前库状态：

- 核心运控 SDK 支持 `x86_64` / `aarch64` / `i386`。
- 运行库包按同版本、同架构成组提供，不能只按当前是否调用媒体接口随意删库。
- `MediaBusClient` / `example_media_frames` 仅支持 `aarch64` 板内本地部署；`x86_64` / `i386` 平台不调用 media client 接口，示例构建不生成 `example_media_frames`。

### 3.3 `uniubi_robot_sdk_py`

来源：

- `local_edit/Sdk/Python/`
- `local_edit/sdk_all_doc/uniubi_robot_sdk_py/README.md`

目标：

```text
uniubi_robot_sdk_py/
├── README.md
├── pyproject.toml
├── CMakeLists.txt
├── src/
├── robot_motion_sdk/
├── ThirdParty/
│   └── pybind11/
└── examples/
```

硬约束：

- 目标仓库根目录必须是 `local_edit/Sdk/Python/` 的内容，不能再套一层 `Python/`。
- Python package 名必须保持 `robot_motion_sdk`。
- native 扩展模块名必须保持 `_uniubi_robot_motion_py_native`。
- `pyproject.toml`、`CMakeLists.txt`、`src/`、`robot_motion_sdk/`、`ThirdParty/pybind11/`、`examples/` 必须整体保留。
- Python binding 通过 `UNIUBI_SDK_ROOT` 找 `uniubi_robot_sdk` 的 C++ 头和 `.so`；不能把 C++ SDK 整体复制进 Python 仓。

原因：

- `pyproject.toml` 中 wheel package 指向 `robot_motion_sdk`。
- `CMakeLists.txt` 会把 native `.so` 输出到 `robot_motion_sdk` 包目录。
- `robot_motion_sdk/__init__.py` 导入 `_uniubi_robot_motion_py_native`。

### 3.4 `uniubi_robot_msgs`

来源：

- `local_edit/Sdk/IDL/*.idl`
- `local_edit/Sdk/ROS2/src/uniubi/`
- `local_edit/sdk_all_doc/uniubi_robot_msgs/README.md`

目标：

```text
uniubi_robot_msgs/
├── README.md
├── idl/
└── ros2/
    ├── CMakeLists.txt
    ├── package.xml
    ├── msg/
    └── srv/
```

硬约束：

- GitHub 仓库名可以是 `uniubi_robot_msgs`，但 ROS 2 package 名必须保持 `uniubi`。
- `ros2/package.xml` 中 `<name>uniubi</name>` 不能改。
- `ros2/CMakeLists.txt` 中 `project(uniubi)` 不能改。
- `msg/*.msg`、`srv/System.srv` 的文件名和字段兼容性不能随意改。
- `idl/` 文件必须整目录保留在一起，因为存在同目录 include 关系：
  - `RPCMessage.idl` include `Request.idl`
  - `EventMessage.idl` include `Request.idl`
  - `MotionObserved.idl` include `MotorState.idl`
- 下游仓库不得复制 `.msg` / `.srv` 定义，应通过构建或安装本仓库的 `uniubi` package 获取接口。

### 3.5 `uniubi_ros2`

来源：

- `local_edit/Sdk/ROS2/examples/src/uniubi_interface_test/`
- `local_edit/sdk_all_doc/uniubi_ros2/README.md`

目标：

```text
uniubi_ros2/
├── README.md
└── src/
    └── uniubi_interface_test/
        ├── CMakeLists.txt
        ├── package.xml
        ├── include/
        │   └── uniubi_interface_test/
        ├── src/
        └── third_party/
            └── jsoncpp/
```

硬约束：

- 本仓不维护 `.msg` / `.srv` 定义。
- `uniubi_interface_test` package 名保持不变，除非同步修改所有 CMake、package.xml、include、运行命令和文档。
- `package.xml` 中对 `uniubi` 的依赖必须保留。
- `CMakeLists.txt` 中 `find_package(uniubi REQUIRED)` 必须保留。
- `include/uniubi_interface_test/`、`src/`、`third_party/jsoncpp/` 的相对结构不能随意打散。

### 3.6 `uniubi_examples`

来源：

- 当前已存在并可验证的 C++、Python、ROS 2 示例。

要求：

- 只迁移真实存在并可构建或可运行的示例。
- 不提前承诺未落地的 DDS direct examples 或 safe suite。
- 示例 README 应清楚标注依赖仓库、运行前置条件和真实机器人安全等级。

## 4. 文档迁移规则

执行顺序：

1. 先覆盖 `uniubi-docs`，确保总站链接和完整教程最新。
2. 再覆盖各代码仓 README。
3. 如确有分仓专属细节，再创建对应代码仓 `docs/`，避免把跨仓教程散落到多个仓库。

规则：

- `uniubi-docs` 可以引用所有仓库。
- 代码仓 README 保留最小闭环说明，并链接到 `uniubi-docs` 中的完整接口手册。
- 代码仓 README 中的目录结构必须与迁移后的真实仓库结构一致。
- 文档中的本地路径以最终仓库视角书写，不使用当前整理目录的临时路径。
- 对外文档不引用 `local_edit/`、`Build/Sdk`、旧 `Doc/`，除非是在本迁移计划中说明来源。

## 5. 验证计划

### 5.1 文档验证

```bash
cd local_edit/sdk_all_doc
rg -n "\bdoc/|/Doc\b|Doc/|SDK_SPLIT_PLAN|SDK 仓库 `IDL/`|仓库根目录的 `IDL/`" .
```

要求：

- 除迁移计划中说明历史来源外，不应再有旧 `Doc/` 或 SDK 仓内 `IDL/` 归属描述。
- Markdown 相对链接在 `uniubi-docs` 内可解析。
- 分仓 README 的目录结构与目标仓库布局一致。

### 5.2 C++ SDK 验证

在 Linux 环境执行：

```bash
cd uniubi_robot_sdk
cmake -S . -B build
cmake --build build -j
```

`librobotMotionSdk.so`、`libmediaBus.so`、`libudbus.so`、`libubase.so` 必须按同版本、同架构在目标架构的 `lib/<arch>/` 下成组放置。媒体帧订阅功能仅 `aarch64` 板内本地部署可用。若使用外部安装前缀，可通过 `UNIUBI_SDK_ROOT` 指定。

### 5.3 Python SDK 验证

```bash
git clone https://github.com/uniubi-ai/uniubi_robot_sdk.git ~/uniubi_robot_sdk
cd uniubi_robot_sdk_py
UNIUBI_SDK_ROOT=~/uniubi_robot_sdk pip install .
python3 -c "import robot_motion_sdk as sdk; print(sdk.MotionHighLevelClient)"
```

### 5.4 ROS 2 messages 验证

```bash
mkdir -p ~/ros2_ws/src
cp -r uniubi_robot_msgs/ros2 ~/ros2_ws/src/uniubi
cd ~/ros2_ws
colcon build --packages-select uniubi
. install/setup.bash
ros2 interface show uniubi/srv/System
ros2 interface show uniubi/msg/MotionObserved
```

### 5.5 ROS 2 example 验证

```bash
mkdir -p ~/ros2_ws/src
cp -r uniubi_robot_msgs/ros2 ~/ros2_ws/src/uniubi
cp -r uniubi_ros2/src/uniubi_motion_client ~/ros2_ws/src/
cd ~/ros2_ws
colcon build --packages-select uniubi uniubi_motion_client
. install/setup.bash
ros2 run uniubi_motion_client motion_high_level_client_example
```

真实机器人运行前必须确认 DDS Domain、RMW、网卡、`device_id` 和安全动作范围。

## 6. 风险与处理

| 风险 | 影响 | 处理 |
|---|---|---|
| Python 仓根目录多套一层 `Python/` | `pip install .` 找不到 package 或构建路径错误 | 直接以 `local_edit/Sdk/Python/` 内容作为仓库根 |
| ROS 2 package `uniubi` 被改名 | 下游 `find_package(uniubi)`、`uniubi/srv/System`、运行文档全部失效 | 仓库名和 package 名分离，package 名保持 `uniubi` |
| `uniubi_ros2` 复制 msg/srv | 接口定义分叉，wire contract 漂移 | msg/srv 只在 `uniubi_robot_msgs` 维护 |
| IDL 拆散 | `#include` 解析失败或 DDS 类型生成失败 | `idl/` 整目录发布 |
| include root 写错 | C++ 示例找不到 `uniubi/robot_sdk/...` | include root 使用 `${UNIUBI_SDK_ROOT}/include` |
| README 宣称的示例不存在 | 用户按 README 无法复现 | 只写当前仓库真实存在的示例 |
| 首跑示例包含高风险动作 | 真实机器人联调风险升高 | README 首跑示例使用 `standUp` / `lieDown`，walking 等动作明确列入高风险 |

## 7. 交付顺序

1. 完成文档总站和分仓 README 的一致性修正。
2. 建立五个目标仓库的实际内容。
3. 分别执行 C++、Python、ROS 2 msg、ROS 2 example 的最小构建验证。
4. 按验证结果更新 `MIGRATION_PROGRESS.md`。
5. 发布 tag 或 release draft，并在 `uniubi-docs` 更新对应版本号和支持矩阵。
