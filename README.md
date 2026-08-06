# Uniubi Docs

Uniubi 开源开发文档中心，提供按目标选择的开发路径、跨仓库索引、接口手册和协议说明。

默认入口：[`docs/START_HERE.md`](docs/START_HERE.md)。如果还不确定应该使用哪个仓库或接入方式，请先从这里开始。

## 仓库导航

| 仓库 | 内容 |
|---|---|
| [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) | DDS IDL、ROS 2 msg/srv、schema 的统一源头 |
| [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) | C++ SDK、头文件、预编译库、C++ 示例 |
| [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) | Python SDK、pybind11 binding、Python 示例 |
| [`uniubi_ros2`](https://github.com/uniubi-ai/uniubi_ros2) | ROS 2 client、Motion bridge 和 ROS 2 示例 |
| [`uniubi_examples`](https://github.com/uniubi-ai/uniubi_examples) | 跨仓示例索引；实际示例代码随所属仓库维护 |

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
| 开始开发、选择仓库和流程导航 | [docs/START_HERE.md](docs/START_HERE.md) |
| 构建、安装、交叉编译 | [docs/BUILD.md](docs/BUILD.md) |
| C++ 高级控制 SDK | [docs/uniubi_high_level_sdk.md](docs/uniubi_high_level_sdk.md) |
| C++ 低级控制 SDK | [docs/uniubi_low_level_sdk.md](docs/uniubi_low_level_sdk.md) |
| 媒体总线 | [docs/uniubi_media_sdk.md](docs/uniubi_media_sdk.md) |
| DDS / ROS 2 直连接入 API | [docs/uniubi_robot_dds_api.md](docs/uniubi_robot_dds_api.md) |
| ROS 2 与 DDS 映射 | [docs/ros2_dds_interop_overview.md](docs/ros2_dds_interop_overview.md) |

## 开发路径

1. 先阅读 [docs/START_HERE.md](docs/START_HERE.md)，按目标、平台和是否有真机选择开发路径。
2. SDK 用户再进入 C++ 或 Python 仓库；ROS 2 用户先构建 `uniubi_robot_msgs`，再构建 `uniubi_ros2`。
3. 没有真机时先走 `uniubi_robot_mock` 或 `uniubi_rl_lab` 的仿真路径。
4. 需要维护接口或分仓时，按协议文档和各仓库 README 的验证要求执行。

## 安全说明

首次真实机器人联调建议先做只读验证，再执行站立、趴下等低风险动作。`walking`、`move`、`bipedStand`、`handstand`、`jump*`、`damp` 等动作应在空旷场地、姿态稳定、具备人工接管条件时执行。

## 许可证

本仓库中的 UniUbi 原创文档和代码使用 Apache License 2.0。详见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
