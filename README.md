# Uniubi Docs

Uniubi SDK 文档中心，提供二次开发所需的跨仓库索引、接口手册和协议说明。

## 仓库导航

| 仓库 | 内容 |
|---|---|
| [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) | DDS IDL、ROS 2 msg/srv、schema 的统一源头 |
| [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) | C++ SDK、头文件、预编译库、C++ 示例 |
| [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) | Python SDK、pybind11 binding、Python 示例 |
| [`uniubi_ros2`](https://github.com/uniubi-ai/uniubi_ros2) | ROS 2 集成包、ROS 2 client/example |
| [`uniubi_examples`](https://github.com/uniubi-ai/uniubi_examples) | 跨 SDK 示例、综合 demo、可运行 recipes |

相关仓库：

| 仓库 | 内容 |
|---|---|
| [`uniubi_robot_mock`](https://github.com/uniubi-ai/uniubi_robot_mock) | x86_64 RobotService mock runtime、MuJoCo / Isaac Gym simulator bridge |
| [`uniubi_robot_description`](https://github.com/uniubi-ai/uniubi_robot_description) | URDF、MJCF、USD、mesh 和可视化资产 |
| [`uniubi_rl_lab`](https://github.com/uniubi-ai/uniubi_rl_lab) | 强化学习环境、训练流程和 sim-to-real 检查 |
| [`.github`](https://github.com/uniubi-ai/.github) | 组织 profile、PR 模板和社区健康文件 |

## 文档索引

| 主题 | 文档 |
|---|---|
| 构建、安装、交叉编译 | [docs/BUILD.md](docs/BUILD.md) |
| SDK GitHub 迁移计划 | [docs/SDK_MIGRATION_PLAN.md](docs/SDK_MIGRATION_PLAN.md) |
| SDK 迁移进度跟踪 | [docs/MIGRATION_PROGRESS.md](docs/MIGRATION_PROGRESS.md) |
| C++ 高级控制 SDK | [docs/uniubi_high_level_sdk.md](docs/uniubi_high_level_sdk.md) |
| C++ 低级控制 SDK | [docs/uniubi_low_level_sdk.md](docs/uniubi_low_level_sdk.md) |
| 媒体总线 | [docs/uniubi_media_sdk.md](docs/uniubi_media_sdk.md) |
| DDS / ROS 2 直连接入 API | [docs/uniubi_robot_dds_api.md](docs/uniubi_robot_dds_api.md) |
| ROS 2 与 DDS 映射 | [docs/ros2_dds_interop_overview.md](docs/ros2_dds_interop_overview.md) |

## 开发路径

1. 先阅读 [docs/BUILD.md](docs/BUILD.md)，确认平台、glibc、动态库和构建方式。
2. C++ 用户从 [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) 的 README 和示例开始。
3. Python 用户从 [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) 的 README 和示例开始。
4. ROS 2 用户先构建 [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs)，再构建 [`uniubi_ros2`](https://github.com/uniubi-ai/uniubi_ros2)。
5. 需要直接对接 DDS / ROS 2 wire contract 时，阅读 [docs/uniubi_robot_dds_api.md](docs/uniubi_robot_dds_api.md)。
6. 需要部署或复核 GitHub 分仓时，按 [docs/SDK_MIGRATION_PLAN.md](docs/SDK_MIGRATION_PLAN.md) 执行，并在 [docs/MIGRATION_PROGRESS.md](docs/MIGRATION_PROGRESS.md) 更新进度。

## 安全说明

首次真实机器人联调建议只执行站立、趴下等低风险动作。`walking`、`move`、`bipedStand`、`handstand`、`jump*`、`damp` 等动作应在空旷场地、姿态稳定、具备人工接管条件时执行。

## 许可证

本仓库中的 UniUbi 原创文档和代码使用 Apache License 2.0。详见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
