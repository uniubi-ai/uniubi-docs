# 启动并验证 ROS 2 Motion bridge

[English](ros2-motion-bridge.md) | **简体中文**

## 目标

面向普通 ROS 2 业务节点，启动 `uniubi_motion_bridge`，先完成只读观测验证，再决定是否进入控制流程。

本指南不覆盖原始 DDS / RPC 协议开发；需要协议级接入时，转到 [DDS / ROS 2 直连接入 API](../uniubi_robot_dds_api.zh-CN.md)。

## 前置条件

- ROS 2 Humble 已安装并完成环境配置。
- 开发机或 Orin 与机器人处于同一可发现网络和 DDS Domain。
- 已确认目标机器人的 `device_id`，它对应设备信息中的 `deviceNo`。
- 推荐使用 Cyclone DDS；多机器人场景为每条机器人使用独立的 `ROS_DOMAIN_ID`。
- 如果存在多个网卡，提前配置 `CYCLONEDDS_URI` 指向机器人所在网卡。

## 1. 构建消息包和 bridge

```bash
mkdir -p ~/ros2_ws/src

git clone https://github.com/uniubi-ai/uniubi_robot_msgs.git ~/uniubi_robot_msgs
cp -r ~/uniubi_robot_msgs/ros2 ~/ros2_ws/src/uniubi

git clone https://github.com/uniubi-ai/uniubi_ros2.git ~/uniubi_ros2
cp -r ~/uniubi_ros2/src/uniubi_motion_client ~/ros2_ws/src/
cp -r ~/uniubi_ros2/src/uniubi_motion_bridge ~/ros2_ws/src/

cd ~/ros2_ws
colcon build --packages-select uniubi uniubi_motion_client uniubi_motion_bridge
. install/setup.bash
```

成功标准：`colcon build` 返回成功，并且 `ros2 pkg list` 中能找到
`uniubi`、`uniubi_motion_client` 和 `uniubi_motion_bridge`。

## 2. 配置运行环境

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=42
export ROS_LOCALHOST_ONLY=0
export ROBOT_DEVICE_ID="$(python3 -c 'import json; print(json.load(open("/tmp/deviceInfo"))["deviceNo"])')"
```

如果设备信息不在 `/tmp/deviceInfo`，将 `ROBOT_DEVICE_ID` 替换为设备信息中的
`deviceNo`；不要把机器人 SN 和 ROS Domain 混为一谈。

## 3. 启动 bridge

```bash
ros2 launch uniubi_motion_bridge motion_bridge.launch.py \
  device_id:="$ROBOT_DEVICE_ID"
```

启动成功的最低标准：

- bridge 节点保持运行；
- 能发现 robotServer；
- 启动阶段不会自动申请运动控制权；
- 未配置正确的设备 ID、DDS Domain 或网卡时，应先排查连接，不要直接尝试动作。

## 4. 先做只读观测验证

另开终端并重新 source 环境：

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 node list | grep uniubi_motion_bridge
ros2 topic echo --once /odom nav_msgs/msg/Odometry
ros2 topic echo --once /joint_states sensor_msgs/msg/JointState
ros2 topic echo --once /imu/data sensor_msgs/msg/Imu
ros2 topic echo --once /battery_state sensor_msgs/msg/BatteryState
```

成功标准：

- `uniubi_motion_bridge` 出现在节点列表；
- 标准 topic 能收到有效样本；
- 只读订阅不需要申请运动控制权；
- topic 没有数据时，优先检查网络、`ROS_DOMAIN_ID`、RMW、网卡和 `device_id`。

## 5. 控制流程的边界

bridge 启动本身不等于机器人已经开始运动。控制流程需要额外确认：

- 动作类型和参数是否在设备能力范围内；
- 场地、急停和人工接管是否准备就绪；
- 业务结束后显式停止动作并释放控制权；
- 不要把 `/cmd_vel` 当作取权或启动动作的接口。

普通业务优先使用 bridge；需要更细粒度的高级控制时，再阅读
[`uniubi_motion_client` 的选型说明](https://github.com/uniubi-ai/uniubi_ros2/blob/main/docs/ros2_usage_modes.md)。

## 常见排查

| 现象 | 优先检查 |
|---|---|
| bridge 无法发现 robotServer | DDS Domain、RMW、网卡、`CYCLONEDDS_URI`、设备网络 |
| 节点启动但 topic 无数据 | `device_id`、机器人服务状态、topic 名和 QoS |
| 只读正常但控制失败 | 设备能力、控制权生命周期、动作参数和安全状态 |
| 多台机器人互相收到数据 | 是否复用了同一个 `ROS_DOMAIN_ID` |
