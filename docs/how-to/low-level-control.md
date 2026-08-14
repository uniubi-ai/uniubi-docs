# Low-level: Run a Custom Joint-control Policy

**English** | [简体中文](low-level-control.zh-CN.md)

## Goal

Run your own policy or controller and directly generate position or torque commands for individual joints.

Typical goals include:

- training a locomotion policy in simulation;
- exporting the policy and integrating it with the robot runtime; and
- implementing a joint position or torque controller while validating timing, joint order, and safety behavior.

## Out of Scope

If you only need built-in standing, walking, turning, or other actions, follow [High-level: Use Built-in Robot Actions](high-level-control.md).

## Use the SDK

Joint-level Low-level control uses the SDK's `MotionLowLevelClient`:

| Language | Entry point | Repository |
|---|---|---|
| C++ | `MotionLowLevelClient` | [`uniubi_robot_sdk`](https://github.com/uniubi-ai/uniubi_robot_sdk) |
| Python | `MotionLowLevelClient` | [`uniubi_robot_sdk_py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py) |

ROS 2 Motion Bridge does not provide an equivalent joint-level interface. Direct DDS/RPC integration and protocol changes are specialized protocol-level work, not the standard Low-level development path.

## Recommended Workflow

1. **Train or prepare the policy:** follow [Policy Training, Export, and Replay](train-export-replay.md) and confirm checkpoint replay in simulation.
2. **Prepare the SDK:** follow [SDK First Use](sdk-first-use.md) and verify that bindings, headers, runtime libraries, architecture, and ABI match.
3. **Validate the SDK path:** use [Mock / Sim2Sim](mock-sim2sim.md) to validate the policy, simulation bridge, and SDK client without hardware.
4. **Move to the real robot:** begin with read-only checks and low-risk posture validation. Verify the control rate, joint order, on-board inference format, emergency stop, and manual-takeover procedure.

## SDK and Model Joint Order

The current `MotorLayout` contains 12 joints in SDK/robot leg-major order:

```text
FL_ABAD, FL_HIP, FL_KNEE,
FR_ABAD, FR_HIP, FR_KNEE,
RL_ABAD, RL_HIP, RL_KNEE,
RR_ABAD, RR_HIP, RR_KNEE
```

After reaching `kConnected`, a Low-level application must call `client.get_motor_layout()` and verify both joint count and order. Construct each control frame with the `limb_no` and `joint_no` returned by the corresponding `MotorInfo`; do not rely only on hard-coded array indexes. Refuse to call `set_motion_enable(true)` if the count or order does not match.

Model input and output order is defined by the model's training and export contract and may differ from the SDK's leg-major order. Declare SDK order and model order separately, and explicitly reorder before model inference and after reading model output. When replacing a model, verify the observation definition, normalization, action scale, input/output shapes, and control rate as well as the ONNX file.

On the robot compute module, pinning a C++ or Python TensorRT Low-level process to CPU 2 with `taskset -c 2` is recommended to reduce scheduler jitter and stabilize observation latency and the 50 Hz control period. If the device uses another CPU-isolation plan, select the dedicated core assigned to the controller.

Reference implementations:

- C++: [`example_lowlevel_tensorrt.cpp`](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/example_lowlevel_tensorrt.cpp)
- Python: [`example_lowlevel_tensorrt.py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/examples/example_lowlevel_tensorrt.py)

Both examples accept ONNX input and rebuild the TensorRT engine at every process startup without PyTorch. The C++ example disables TF32 and uses strict FP32. Its `--validate-only` mode validates ONNX parsing, engine construction, and one zero-input inference without connecting to the robot. Never reuse an unverified joint reorder or observation contract when replacing the model.

## Staged Real-robot Validation

For the first hardware test, secure the robot on a reliable safety rig with all four feet fully clear. Validate only `stand` and `lay`. After confirming posture, joint direction, and emergency-stop behavior, place the robot on clear, level, obstacle-free ground and validate `stand` → `walk` → `stop` → `lay`.

Never execute `walk` while the robot is suspended. During both stages, keep the emergency stop within reach and have a dedicated operator attend the robot.

## Detailed Interfaces

- [Python Low-level API](../api-reference/python/low-level.md)
- [C++ Low-level API](../api-reference/cpp/low-level.md)
- [`uniubi_robot_sdk` Low-level example](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/example_lowlevel.cpp)
- [`uniubi_robot_sdk_py` examples](https://github.com/uniubi-ai/uniubi_robot_sdk_py/tree/main/examples)

Passing simulation or Mock validation does not prove safe real-robot operation.
