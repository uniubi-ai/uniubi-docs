---
name: uniubi-robot-rl
description: Create Uniubi RL Lab locomotion tasks, edit rewards, diagnose training, and export or replay identified policies while preserving the SDK deployment contract. Use for uniubi_rl_lab work, not generic RL or automatic real-robot control.
---

# Uniubi Robot RL

Work from the user's actual `uniubi_rl_lab` checkout and selected Python environment. This skill is portable: the paths below are relative to that checkout, not to this skill folder. Discover repository locations from the user or workspace; do not assume a sibling repository, machine, environment name, or remote host. Read applicable repository instructions and record branch, commit, working-tree changes, interpreter, and installed simulator/RSL-RL versions before editing or running.

The public baseline inspected for this skill is commit `55dd5c5`: Cyvet manager-based velocity tracking with an MLP PPO policy. Recheck the selected revision before relying on these paths or contracts. The baseline README specifies Python 3.11, Isaac Sim 5.1, Isaac Lab 2.3.2, PyTorch 2.7.0 CUDA 12.8, and RSL-RL >=3.0.1; these are a baseline, not permission to change an existing environment.

## Find the execution path

Inspect only the files relevant to the request:

| Concern | Baseline path |
|---|---|
| Task registration | `source/uniubi_rl_lab/uniubi_rl_lab/tasks/locomotion/robots/cyvet/__init__.py` |
| Environment, observations, actions, rewards, events, curriculum | `source/uniubi_rl_lab/uniubi_rl_lab/tasks/locomotion/robots/cyvet/cyvet_env_cfg.py` |
| PPO policy and algorithm config | `source/uniubi_rl_lab/uniubi_rl_lab/tasks/locomotion/agents/rsl_rl_ppo_cfg.py` |
| Custom MDP terms and exports | `source/uniubi_rl_lab/uniubi_rl_lab/tasks/locomotion/mdp/` |
| Robot and actuator config | `source/uniubi_rl_lab/uniubi_rl_lab/assets/robots/uniubi.py`, `uniubi_actuators.py` in the same directory |
| Training, playback/export, CLI overrides | `scripts/rsl_rl/train.py`, `play.py`, `cli_args.py` in the same directory |
| Registration/debug probes | `scripts/list_envs.py`, `scripts/zero_agent.py`, `scripts/random_agent.py` |
| MuJoCo replay | `deploy/sim2sim/play_mujoco.py`, `deploy/sim2sim/configs/cyvet.yaml` |
| Deployment contract | `deploy/README.md`, `deploy/sim2real/README.md` |

`tasks/__init__.py` imports task packages through `import_packages`. The baseline Gym ID is `Uniubi-Cyvet-Velocity`, with `ManagerBasedRLEnv`, `env_cfg_entry_point`, `play_env_cfg_entry_point`, and `rsl_rl_cfg_entry_point` registration keys. Trace the entrypoint actually used by the script: baseline `play.py` requests `env_cfg_entry_point` through the Hydra decorator and does not explicitly select `play_env_cfg_entry_point`. It also changes command ranges to `limit_ranges` and removes standing-command sampling. Do not assume a play-class registration alone changes playback behavior.

The baseline registered runner is `PPORunnerCfg` with PPO. Train/play dispatch support `OnPolicyRunner` and `DistillationRunner`, but a generic dispatcher does not establish a configured teacher/student workflow. Verify the registered runner, algorithm, network, checkpoint loading, and observation groups before changing algorithms. Do not transplant AMP, ULT, DAgger, QAT, or private training scripts into this public workflow without a requested implementation and source evidence.

## Create a task or change rewards

Start from the closest existing task. Give a new task its own configuration classes and unique Gym ID; preserve existing registrations and user changes. Connect the environment and agent entrypoints, ensure package discovery reaches the new module, and choose an experiment name that keeps unrelated runs separate. Add a robot asset or actuator variant only when needed by the request.

For rewards, search existing Uniubi and imported Isaac Lab MDP functions before adding a function. Keep the reward in the task's `RewardsCfg` using `RewardTermCfg`; expose a custom function through `mdp/__init__.py` when required. Check sensor/body/joint selectors, command names, sign and weight, units, and per-environment tensor shape. Check zero command, reset, contact/no-contact, and finite outputs where relevant. Avoid changing observations, curriculum, terminations, or actuator settings as an incidental reward fix.

Validate syntax/import wiring first. Registration listing and zero/random agents launch Isaac Sim; they are runtime probes, not cheap static checks. Use them only in a suitable environment and with a defined stop condition. Report which behavior was actually checked; syntax or task listing does not establish learning quality.

## Diagnose and run training

Trace failures in order: interpreter/dependencies and simulator startup, package/task registration, asset/sensor selection, reset and observation/action shapes, runner/checkpoint compatibility, then optimization and reward metrics. Inspect the first meaningful error rather than repeatedly launching the same job. Avoid repeated launches without new diagnostic evidence. Stop when the authorized resource bound is reached or continuing requires a design change.

Training defaults are large (4096 environments and 50000 iterations at the baseline). Run training only within the user's authorization and agreed resource/time bounds. For an authorized smoke test, a baseline example from the checkout root is:

```bash
python scripts/rsl_rl/train.py --task=Uniubi-Cyvet-Velocity \
  --headless --num_envs=16 --max_iterations=1 --device cuda:0
```

Check available GPU resources and the actual flags in the selected revision before launch. Record command, PID, log path, task/revision, seed, effective environment count and iteration bound, and exit status. Stop only the process you launched. A smoke run proves startup and a bounded learning step, not convergence.

Runs use `logs/rsl_rl/<experiment_name>/<timestamp>_<run_name>/` and save `params/env.yaml`, `params/agent.yaml`, checkpoints, TensorBoard events, simulator logs under `isaaclab/`, and Git snapshots. For comparisons or resuming, inspect the saved run configurations and checkpoint identity, not only today's source configuration. Keep terrain, command ranges, episode/termination rules, seeds, normalization, actuator limits, and evaluation protocol matched. Report protocol changes separately from policy improvement.

## Export and replay an identified checkpoint

Use an explicit task and checkpoint path. Baseline playback builds the environment from the current registry; it does not automatically reconstruct it from the checkpoint's saved YAML. Compare the saved run configuration against that registry before loading/exporting, including architecture and normalization. Export still starts Isaac Sim and creates an environment; it is not a simulator-free conversion.

```bash
python scripts/rsl_rl/play.py --task=Uniubi-Cyvet-Velocity \
  --checkpoint /absolute/path/to/model_<iteration>.pt \
  --headless --num_envs=1 --export-only
```

This writes `exported/policy.onnx` and `exported/policy.pt` beside the checkpoint and may overwrite previous exports there. Preserve valuable existing artifacts. Record checkpoint/export hashes, source revision, configuration and exported I/O shapes. The exporter passes the actor or student normalizer when present; ensure deployment does not omit or double-apply it.

For local MuJoCo replay, use a task-matched copy of `deploy/sim2sim/configs/cyvet.yaml` with an explicit checkpoint, network settings, joint mapping, actuator contract and bounded duration. Keep the copied YAML beside the original, or rebase its relative asset paths: the runner resolves `robot.xml_path` and `robot.robot_xml_path` relative to the configuration file, so a copy in another directory needs corrected or absolute XML paths.

```bash
python deploy/sim2sim/play_mujoco.py --config /absolute/path/to/replay.yaml --dry-run
python deploy/sim2sim/play_mujoco.py --config /absolute/path/to/replay.yaml \
  --duration 10 --cmd-vx 0.5 --cmd-vy 0 --cmd-yaw 0
```

The baseline local runner loads the RSL-RL actor-critic checkpoint, not ONNX. Its dry run checks configuration, joint-count agreement and file existence; it can pass with no checkpoint configured and does not execute inference or physics. Revalidate support before using normalized, recurrent, student, or other non-baseline policies. Isaac playback without video normally runs until the simulator stops; use an explicit cancellation plan or supported bounded video options instead of leaving it unattended.

## Preserve the SDK deployment interface

For the baseline Cyvet policy, verify float32 `[1,45] -> [1,12]`. Actor inputs are angular velocity (scale 0.2), projected gravity, `[vx,vy,yaw]`, joint position relative to default, joint velocity (scale 0.05), and previous action. The critic's 60-element observation is not the actor deployment input. Model joints are joint-major: FL/FR/RL/RR ABAD, then HIP, then KNEE. Default joint positions are 0, 0.8, -1.58 rad; action scale is 0.25; policy period is `0.004 * 5 = 0.02` seconds. Reference PD gains are Kp 35 and Kd 1. Re-derive every value for another task or checkpoint, including clipping, gravity/velocity frames, quaternion convention, reset of previous action, normalization and torque limits.

SDK `MotorLayout` is leg-major in the public reference. Validate the actual layout with `getMotorLayout()` and implement both state and action reorders; never equate policy indices with SDK motor indices. Match SDK headers, libraries and example revision. An export or successful sim2sim run does not prove board compatibility or physical behavior.

Use the checked-out deployment guides for current details. Public cross-repository references carried by the baseline README are:

- [SDK sim2sim bridge](https://github.com/uniubi-ai/uniubi_robot_mock/blob/main/docs/sim2sim_sdk.md)
- [C++ TensorRT policy example](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/example_lowlevel_tensorrt.cpp)
- [Python TensorRT policy example](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/examples/example_lowlevel_tensorrt.py)
- [Low-level API and control boundaries](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/low-level-control.md)

Inspect the target revision before using these moving links. Keep the skill usable without another personal skill or a documentation checkout. Preparing artifacts does not authorize upload, installing board software, enabling Low-level control or moving a robot. When board validation is requested and authorized, start with model-only `--validate-only` after checking its actual source semantics. Physical tests require the requested operator/safety setup and separate evidence. The baseline TensorRT examples disable motion and disconnect on exit; they do not restore built-in motion control. Define handback before an authorized robot test rather than assuming disconnect restores it.

Return changed files, checks performed, commands and evidence paths, and remaining gaps. Distinguish static checks, simulator execution, export, model-only board validation and observed physical behavior.
