# 维护已批准的接口变更

> 本文只适用于接口维护者已确认的协议变更。普通开发者不得因为接入需求直接修改 robotServer / DDS wire contract；如果只是使用现有接口，请从 Quick Start 和 API Reference 开始。

## 先确认是否真的需要改协议

优先区分以下情况：

- 只是不会使用现有字段：阅读 API 文档或对应 How-to，不修改协议。
- 只是 ROS 2 / SDK 映射错误：优先修复消费者映射、文档或示例，不改变协议源头。
- 确实需要新增或变更 wire contract：先完成接口评审，明确兼容性、版本、发布对象和下游负责人。

## 源头和边界

- [`uniubi_robot_msgs/idl`](https://github.com/uniubi-ai/uniubi_robot_msgs/tree/main/idl) 是已发布接口定义的统一来源。
- “统一来源”表示变更后的正式定义集中在这里维护，不表示任何开发者都可以直接修改协议。
- ROS 2 `msg/srv` 和 schema 必须与经过批准的 IDL 保持映射关系。
- 下游 SDK、ROS 2 client/bridge 和示例不复制消息定义，也不能通过下游仓库绕过接口评审。

## 变更获批后的验证顺序

1. 记录批准的变更范围、兼容性要求、版本和回滚方式。
2. 修改 `uniubi_robot_msgs/idl` 或对应 schema，并确认字段语义、单位、生命周期和兼容性。
3. 构建 `uniubi_robot_msgs`，检查生成的 ROS 2 interface。
4. 更新 `uniubi_ros2`、SDK 映射或示例中的消费者。
5. 检查 DDS / ROS 2 QoS、请求响应、Event 和控制权语义。
6. 按消息包 → ROS 2 client/bridge → SDK 映射 → 示例的顺序构建和验证。

## 最小接口检查

```bash
cd uniubi_robot_msgs
colcon build --packages-select uniubi
. install/setup.bash
ros2 interface show uniubi/srv/System
ros2 interface show uniubi/msg/MotionObserved
```

## 完成标准

- 变更有明确的接口维护者和评审结论；
- IDL、ROS 2 msg/srv 和 schema 的字段语义一致；
- 下游构建不依赖复制的消息定义；
- SDK / ROS 2 映射和示例验证通过；
- 文档同步说明版本、兼容性和发布影响。

协议字段和 QoS 细节见 [DDS / ROS 2 直连接入 API](../uniubi_robot_dds_api.md) 和 [ROS 2 与 DDS 映射](../ros2_dds_interop_overview.md)。
