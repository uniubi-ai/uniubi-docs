# Advanced

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/advanced/README.zh-CN.md)

This section is for developers who have completed Quick Start, understand the control modes, and have finished basic validation. It covers protocols, DDS, QoS, and specialized integrations and is not the normal starting point for application development.

## Protocol-level Access

| Topic | Documentation | Use when |
|---|---|---|
| Direct DDS / ROS 2 integration | [DDS / ROS 2 API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/uniubi_robot_dds_api.md) | Integrating directly with the device protocol without the SDK |
| ROS 2 and DDS mapping | [ROS 2 / DDS Interoperability](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/ros2_dds_interop_overview.md) | Troubleshooting wire contracts, topics, services, and QoS mappings |

## Boundaries

- Direct DDS/RPC integration is not equivalent to standard Low-level SDK development. Joint-level Low-level control uses the SDK as its standard entry point.
- Do not modify `uniubi_robot_msgs/idl` merely because an existing field is unclear. Read the relevant API and How-to documentation first.
