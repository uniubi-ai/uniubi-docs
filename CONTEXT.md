# Uniubi Robot Development

[简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/CONTEXT.zh-CN.md) | **English**

This glossary defines the control and deployment language used across the Uniubi developer documentation.

## Control abstractions

**High-level control**:
A control abstraction in which an application expresses actions or motion intent and the robot's built-in motion capability closes the joint-level loop.
_Avoid_: brain-side control, remote control mode

**Low-level control**:
A control abstraction in which an application owns the joint-level policy or controller and continuously produces joint targets.
_Avoid_: SDK control

**High-level application**:
A developer-owned process that uses High-level control. Its deployment location may be an external host or the robot brain.
_Avoid_: brain application

## Runtime locations

**External host**:
A Linux PC or industrial computer outside the robot that runs a High-level application over a network connection.
_Avoid_: multi-robot host, remote robot

**Robot brain**:
The robot's onboard general-purpose compute platform for developer applications, perception, planning, and model inference.
_Avoid_: motion controller

**Motion controller (cerebellum)**:
The robot-side controller that provides built-in motion capabilities and their real-time execution.
_Avoid_: developer host, robot brain

## Robot identity

**Device ID**:
The robot serial number that identifies the target robot to a High-level application. It is distinct from an IP address or network interface.
_Avoid_: robot IP, interface address
