# 使用 Mock / Sim2Sim 验证 SDK 链路

[English](mock-sim2sim.md) | **简体中文**

## 目标

没有真机时，先验证 SDK、仿真 bridge 和 RobotService mock 的闭环通信。

## 前置条件

- x86_64 Ubuntu 22.04 Linux VM。
- MuJoCo；Isaac Gym 作为可选后端需要 NVIDIA GPU 和独立 Python 3.8 环境。
- [`uniubi_robot_mock`](https://github.com/uniubi-ai/uniubi_robot_mock)。

## 验证顺序

1. 将 `mockService/uniubi_mock/` 部署到 VM 的 `/uniubi_mock`。
2. 按 mock 仓库文档启动 `robotMonitorServer`、`motionServer` 和 `robotServer`。
3. 如 VM 网卡不是默认接口，配置 `/uniubi_mock/etc/dds/host_config.xml`。
4. 启动 `simulation/sim2sim` 中的仿真 bridge，并设置当前目录的 `PYTHONPATH`。
5. 运行 C++ 或 Python SDK client，验证状态、指令和反馈闭环。

详细命令：

- [Mock runtime 部署和排查](https://github.com/uniubi-ai/uniubi_robot_mock/blob/main/docs/mock_service.md)
- [仿真环境准备](https://github.com/uniubi-ai/uniubi_robot_mock/blob/main/docs/simulation_setup.md)
- [SDK Sim2Sim](https://github.com/uniubi-ai/uniubi_robot_mock/blob/main/docs/sim2sim_sdk.md)

## 成功标准

- mock 服务、仿真 bridge 和 SDK client 均保持运行；
- 状态和控制消息能完成闭环；
- 能区分 SDK/协议链路问题和 MuJoCo 控制器问题。

## 边界

Mock / Sim2Sim 不能替代真实机器人上的 ABI、网络、控制周期、急停和安全动作验证。真实机器人联调仍按只读、低风险动作、低速运动的顺序进行。
