# How-to Guides

**English** | [简体中文](README.zh-CN.md)

Each guide addresses a specific development task. It defines the goal and prerequisites, provides a minimal procedure, and states observable success criteria and the next project entry point.

> If you have not yet chosen a control mode, application runtime, or implementation, begin with the [Quick Start](../../README.md#quick-start).

## Environment and Device Access

| Task | Guide | When to use it |
|---|---|---|
| Obtain device IPs from the app and confirm the login address and service ports | [Robot network access](../core-concepts/device-network.md) | Before connecting to a real robot |
| Connect and power a USB, Ethernet, or other onboard peripheral | [Connect peripherals](connect-peripherals.md) | Before deploying an onboard perception or peripheral application |
| Prepare the build environment | [Build, installation, and cross-compilation](../BUILD.md) | Before SDK or ROS 2 development |
| Prepare an SDK project | [SDK first use](sdk-first-use.md) | After selecting High-level or Low-level SDK development |

## Control and Integration

| Task | Guide | When to use it |
|---|---|---|
| Use built-in motion capabilities without controlling individual joints | [Use built-in robot actions](high-level-control.md) | After selecting High-level in the Quick Start |
| Run a custom controller and directly command joint position or torque | [Run a custom joint-control policy](low-level-control.md) | After selecting Low-level in the Quick Start |
| Write a ROS 2 application node | [Start and validate Motion Bridge](ros2-motion-bridge.md) | After selecting High-level + ROS 2 |

## Training and Validation

| Task | Guide | When to use it |
|---|---|---|
| Train, export, and replay a policy | [Policy training and replay](train-export-replay.md) | During Low-level policy development |
| Validate the SDK path without hardware | [Mock / Sim2Sim](mock-sim2sim.md) | Before real-robot SDK testing |
