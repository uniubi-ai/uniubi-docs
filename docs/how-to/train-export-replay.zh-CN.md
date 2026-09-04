# 训练、导出和回放策略

[English](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/train-export-replay.md) | **简体中文**

## 目标

从任务注册和最小训练开始，确认 checkpoint 可回放，再进入导出、Sim2Sim 和部署。

## 前置条件

- [`uniubi_rl_lab`](https://github.com/uniubi-ai/uniubi_rl_lab)。
- Python 3.11、Isaac Sim 5.1、Isaac Lab 2.3.2、PyTorch 2.7.0 CUDA 12.8。
- NVIDIA GPU 和已完成的 Isaac Lab 安装。

## 1. 安装并检查任务

```bash
cd /path/to/uniubi_rl_lab
python3 -m pip install -e source/uniubi_rl_lab
python3 scripts/list_envs.py
```

确认任务列表中包含 `Uniubi-Cyvet-Velocity`。

## 2. 运行最小训练

```bash
python3 scripts/rsl_rl/train.py --task=Uniubi-Cyvet-Velocity --headless --num_envs=16 --max_iterations=1 --device cuda:0
```

成功标准：任务能启动，输出 observation/action shape，并生成可回放的运行记录。

## 3. 回放 checkpoint

```bash
python3 scripts/rsl_rl/play.py --task=Uniubi-Cyvet-Velocity --checkpoint logs/rsl_rl/cyvet_velocity/<run>/model_<iter>.pt --num_envs=32
```

## 4. 进入部署链路

按以下顺序推进：

1. 从 checkpoint 导出 ONNX 或目标推理格式。
2. 先做本地 MuJoCo Sim2Sim。
3. 需要验证 SDK 链路时，再进入 `uniubi_robot_mock` SDK Sim2Sim。
4. 最后核对板端推理格式、SDK ABI、控制周期、关节顺序和安全策略。

训练或仿真通过不等于真机安全通过。部署细节见 [`uniubi_rl_lab/deploy`](https://github.com/uniubi-ai/uniubi_rl_lab/tree/main/deploy)。
