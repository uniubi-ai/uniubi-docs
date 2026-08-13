# Advanced

[English](README.md) | **简体中文**

本节面向已经完成 Quick Start、理解控制模式并完成基础验证的开发者。这里的内容涉及协议、DDS、QoS 和特殊集成，不是普通开发的第一入口。

## 协议与底层接入

| 主题 | 文档 | 适用场景 |
|---|---|---|
| DDS / ROS 2 直连接入 | [DDS / ROS 2 API](../uniubi_robot_dds_api.zh-CN.md) | 不使用 SDK，直接对接设备协议 |
| ROS 2 与 DDS 映射 | [ROS 2 / DDS Interop](../ros2_dds_interop_overview.zh-CN.md) | 排查 wire contract、topic、service 和 QoS 映射 |

## 阅读边界

- 直接 DDS / RPC 不等于普通 Low-level SDK 开发；关节级 Low-level 仍以 SDK 为标准入口。
- 不要因为不会使用现有字段就修改 `uniubi_robot_msgs/idl`；先阅读 API 和对应 How-to。
