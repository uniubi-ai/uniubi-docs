# Train, Export, and Replay a Policy

**English** | [简体中文](train-export-replay.zh-CN.md)

## Goal

Register a task, run a minimal training job, confirm that its checkpoint can be replayed, and then continue to export, Sim2Sim, and deployment.

## Prerequisites

- [`uniubi_rl_lab`](https://github.com/uniubi-ai/uniubi_rl_lab)
- Python 3.11, Isaac Sim 5.1, Isaac Lab 2.3.2, and PyTorch 2.7.0 with CUDA 12.8
- An NVIDIA GPU and a working Isaac Lab installation

## 1. Install and List Tasks

```bash
cd /path/to/uniubi_rl_lab
python3 -m pip install -e source/uniubi_rl_lab
python3 scripts/list_envs.py
```

Confirm that `Uniubi-Cyvet-Velocity` appears in the task list.

## 2. Run Minimal Training

```bash
python3 scripts/rsl_rl/train.py --task=Uniubi-Cyvet-Velocity --headless --num_envs=16 --max_iterations=1 --device cuda:0
```

Success criteria: the task starts, reports the observation and action shapes, and creates a run directory that can be replayed.

## 3. Replay a Checkpoint

```bash
python3 scripts/rsl_rl/play.py --task=Uniubi-Cyvet-Velocity --checkpoint logs/rsl_rl/cyvet_velocity/<run>/model_<iter>.pt --num_envs=32
```

## 4. Continue to Deployment

Proceed in this order:

1. Export ONNX or another target inference format from an identified checkpoint.
2. Validate the same policy with local MuJoCo Sim2Sim.
3. When the SDK path also needs validation, use `uniubi_robot_mock` SDK Sim2Sim.
4. Finally verify the on-board inference format, SDK ABI, control rate, joint order, and safety behavior.

Passing training or simulation does not prove safe real-robot operation. See [`uniubi_rl_lab/deploy`](https://github.com/uniubi-ai/uniubi_rl_lab/tree/main/deploy) for deployment details.
