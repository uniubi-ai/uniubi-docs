# Start and Validate ROS 2 Motion Bridge

**English** | [简体中文](ros2-motion-bridge.zh-CN.md)

## Goal

Start `uniubi_motion_bridge` for a ROS 2 application, complete read-only observation checks, and only then decide whether to enter the control workflow.

This guide does not cover raw DDS/RPC development. For protocol-level integration, see the [DDS / ROS 2 API](../uniubi_robot_dds_api.md).

## Prerequisites

- ROS 2 Humble is installed and sourced.
- The development host or Orin is on a network and DDS domain from which the robot can be discovered.
- The target robot's `device_id` is known; it corresponds to `deviceNo` in device information.
- Cyclone DDS is recommended. For multiple robots, use a separate `ROS_DOMAIN_ID` for each robot.
- On a multi-interface host, configure `CYCLONEDDS_URI` for the robot-facing interface before starting.

## 1. Build the Message Package and Bridge

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

Success criterion: `colcon build` succeeds and `ros2 pkg list` contains `uniubi`, `uniubi_motion_client`, and `uniubi_motion_bridge`.

## 2. Configure the Runtime Environment

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=42
export ROS_LOCALHOST_ONLY=0
export ROBOT_DEVICE_ID="$(python3 -c 'import json; print(json.load(open("/tmp/deviceInfo"))["deviceNo"])')"
```

If device information is not available at `/tmp/deviceInfo`, set `ROBOT_DEVICE_ID` to the target robot's actual `deviceNo`. Do not confuse the robot SN with the ROS domain ID.

## 3. Start the Bridge

```bash
ros2 launch uniubi_motion_bridge motion_bridge.launch.py \
  device_id:="$ROBOT_DEVICE_ID"
```

Minimum startup criteria:

- The bridge node remains running.
- It discovers `robotServer`.
- It does not request motion-control ownership at startup.
- If the device ID, DDS domain, or network interface is wrong, diagnose connectivity before attempting an action.

## 4. Validate Read-only Observations

Open another terminal and source the environment again:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 node list | grep uniubi_motion_bridge
ros2 topic echo --once /odom nav_msgs/msg/Odometry
ros2 topic echo --once /joint_states sensor_msgs/msg/JointState
ros2 topic echo --once /imu/data sensor_msgs/msg/Imu
ros2 topic echo --once /battery_state sensor_msgs/msg/BatteryState
```

Success criteria:

- `uniubi_motion_bridge` appears in the node list.
- Standard topics receive valid samples.
- Read-only subscriptions do not require motion-control ownership.
- If topics have no data, first check networking, `ROS_DOMAIN_ID`, RMW, the selected interface, and `device_id`.

## 5. Control Boundaries

Starting the bridge does not start robot motion. Before entering control:

- confirm that the action and parameters are supported by the device;
- prepare the test area, emergency stop, and manual-takeover procedure;
- explicitly stop the action and release control when the application finishes; and
- do not treat `/cmd_vel` as an ownership-acquisition or action-start interface.

Use the bridge for standard application development. For more detailed High-level control, read the [`uniubi_motion_client` usage modes](https://github.com/uniubi-ai/uniubi_ros2/blob/main/docs/ros2_usage_modes.md).

## Troubleshooting

| Symptom | Check first |
|---|---|
| Bridge cannot discover `robotServer` | DDS domain, RMW, network interface, `CYCLONEDDS_URI`, and device network |
| Node runs but topics have no data | `device_id`, robot-service status, topic name, and QoS |
| Read-only data works but control fails | Device capabilities, control lifecycle, action parameters, and safety state |
| Multiple robots receive one another's data | Reuse of the same `ROS_DOMAIN_ID` |
