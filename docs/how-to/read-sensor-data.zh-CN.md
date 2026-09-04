# 读取传感器与运动观测

[English](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/read-sensor-data.md) | **简体中文**

本文帮助应用读取 GPS、UWB、电机、IMU、遥控器、电源和 Walk 里程计。先按能力选择客户端，不要因为公共结构中出现某个字段就推断该客户端正式支持它。

## 支持范围

| 能力 | High-level | Low-level |
|---|---|---|
| GPS / UWB | 支持 | 支持 |
| Walk 平面里程计 | 支持；仅 Walk 模式产生有效值 | **不支持** |
| 电机 / IMU / 遥控器 | 观测回调 | `get_latest_observation()` |
| 轻量电源观测 | `get_power_info()` | `get_latest_observation().power` |

> Low-level 的正式 `SensorObserved` 契约只有 GPS 和 UWB。即使共享协议结构或某个 binding 版本中能看到 `odom` 字段，Low-level 应用也不得依赖它。

## High-level：GPS、UWB 和 Walk 里程计

High-level 开启传感器上报只要求已建立连接，不要求控制权。
如果业务还需要运动控制，或需要目标端为 master 才能提供本地电机/IMU 观测，再单独取控。
推荐顺序：

1. 在 `connect()` 前注册传感器回调；
2. `connect()`；
3. 调用 `set_observed_enable({"sensorEnable": True})`；
4. 从回调或 `get_sensor_observation()` 缓存读取；
5. 先关闭上报，再 `disconnect()`；如果业务另行取控，应在 `release_control()` 前关闭。

```python
def on_sensor(sensor):
    if sensor.gps.valid:
        print("GPS", sensor.gps.point.lat, sensor.gps.point.lng)
    if sensor.uwb.valid:
        print("UWB", sensor.uwb.distance, sensor.uwb.azimuth)
    if sensor.odom.valid:
        print("ODOM", sensor.odom.position[0], sensor.odom.position[1], sensor.odom.yaw)

client.set_sensor_observed_callback(on_sensor)  # 必须在 connect 前注册
client.connect()
state = client.set_observed_enable({"motionEnable": False, "sensorEnable": True})
if state is None:
    raise RuntimeError(client.get_last_error())

sensor = client.get_sensor_observation(timeout_ms=1500)
```

`get_sensor_observation()` 读取的是最近一帧缓存；没有先开启 `sensorEnable` 时，不保证存在新鲜数据。退出时应在断开前关闭 `sensorEnable`；如果业务因其他原因取了控制权，应在释放前关闭。

## Low-level：GPS 和 UWB

Low-level 不需要进入 `kPrepared` 即可读取 GPS/UWB；`kConnected` 或 `kPrepared` 均可调用。超时参数单位是 **毫秒**，与 High-level 一致。

```python
sensor = client.get_sensor_observation(timeout_ms=1000)
if sensor is not None:
    if sensor.gps.valid:
        print("GPS", sensor.gps.point.lat, sensor.gps.point.lng)
    if sensor.uwb.valid:
        print("UWB", sensor.uwb.distance, sensor.uwb.azimuth)
```

Low-level 不提供受支持的 Walk 里程计读取入口。需要 Walk 里程计时使用 High-level。

## 电机、IMU、遥控器和电源

- High-level：开启 `motionEnable` 后通过运控观测回调读取；电源也可通过 `get_power_info(timeout_ms=...)` 读取最新缓存。
- Low-level：在 `kPrepared` 中调用 `get_latest_observation(timeout_ms=...)`，返回电机、IMU、TRC 和轻量电源观测。

进入 Low-level `kPrepared` 会切换到关节级控制路径。不要仅为了读取电量而在无人值守的真机上进入 Low-level 控制模式；完整设备状态优先使用 High-level，见[查询设备状态](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/query-device-status.zh-CN.md)。

## 正确判断数据是否可用

- 收到 `SensorObserved` 不等于 GPS/UWB 有效；必须检查各自的 `valid`。
- `gps.valid == 0` 时，不得把 `lat=0`、`lng=0` 当作真实坐标。
- UWB 还应检查 `pair_state`，确认已经配对。
- Walk 里程计只在 Walk 模式中有效；退出 Walk 后 `valid` 会变为 false。

## 成功标准

- 能持续收到观测帧或读取到新鲜缓存；
- 业务只在对应 `valid` 有效时消费 GPS、UWB 或里程计；
