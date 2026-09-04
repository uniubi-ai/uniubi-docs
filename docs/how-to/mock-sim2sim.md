# Validate the SDK Path with Mock / Sim2Sim

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/mock-sim2sim.zh-CN.md)

## Goal

Without a real robot, validate the closed-loop communication path between an SDK client, the simulation bridge, and RobotService Mock.

## Prerequisites

- An x86_64 Ubuntu 22.04 Linux VM
- MuJoCo; the optional Isaac Gym backend requires an NVIDIA GPU and a standalone Python 3.8 environment
- [`uniubi_robot_mock`](https://github.com/uniubi-ai/uniubi_robot_mock)

## Validation Order

1. Deploy `mockService/uniubi_mock/` to `/uniubi_mock` in the VM.
2. Start `robotMonitorServer`, `motionServer`, and `robotServer` as described by the Mock documentation.
3. If the VM's robot-facing interface is not the default, configure `/uniubi_mock/etc/dds/host_config.xml`.
4. Start the simulation bridge under `simulation/sim2sim` and set `PYTHONPATH` for the current directory.
5. Run a C++ or Python SDK client and validate state, commands, and feedback.

Detailed instructions:

- [Mock runtime deployment and troubleshooting](https://github.com/uniubi-ai/uniubi_robot_mock/blob/main/docs/mock_service.md)
- [Simulation environment setup](https://github.com/uniubi-ai/uniubi_robot_mock/blob/main/docs/simulation_setup.md)
- [SDK Sim2Sim](https://github.com/uniubi-ai/uniubi_robot_mock/blob/main/docs/sim2sim_sdk.md)

## Success Criteria

- The Mock services, simulation bridge, and SDK client remain running.
- Commands and observations complete a closed loop.
- SDK/protocol failures can be distinguished from MuJoCo controller failures.

## Boundary

Mock / Sim2Sim does not validate real-robot ABI, networking, control timing, emergency-stop behavior, or motion safety. Real-robot testing must still begin with read-only checks and low-risk posture validation before locomotion.
