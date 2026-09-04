# Read Sensor and Motion Observations

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/read-sensor-data.zh-CN.md)

This guide shows how applications read GPS, UWB, motors, IMU, remote-controller input, power, and Walk odometry. Choose a client by its supported contract; do not infer support merely because a shared structure contains a field.

## Support matrix

| Capability | High-level | Low-level |
|---|---|---|
| GPS / UWB | Supported | Supported |
| Walk planar odometry | Supported; valid only in Walk mode | **Not supported** |
| Motors / IMU / remote controller | Observation callback | `get_latest_observation()` |
| Lightweight power observation | `get_power_info()` | `get_latest_observation().power` |

> The supported Low-level `SensorObserved` contract contains GPS and UWB only. A shared protocol structure or a particular binding build may expose an `odom` member, but Low-level applications must not depend on it.

## High-level: GPS, UWB, and Walk odometry

Enabling High-level sensor reporting requires an established connection, not control ownership.
If the application also needs motion control, or needs the target endpoint to be master for local
motor/IMU observations, acquire control separately. Use this order:

1. Register the sensor callback before `connect()`;
2. call `connect()`;
3. call `set_observed_enable({"sensorEnable": True})`;
4. read from the callback or the `get_sensor_observation()` cache;
5. disable reporting before `disconnect()`; if control was acquired separately, do this before `release_control()`.

```python
def on_sensor(sensor):
    if sensor.gps.valid:
        print("GPS", sensor.gps.point.lat, sensor.gps.point.lng)
    if sensor.uwb.valid:
        print("UWB", sensor.uwb.distance, sensor.uwb.azimuth)
    if sensor.odom.valid:
        print("ODOM", sensor.odom.position[0], sensor.odom.position[1], sensor.odom.yaw)

client.set_sensor_observed_callback(on_sensor)  # Register before connect
client.connect()
state = client.set_observed_enable({"motionEnable": False, "sensorEnable": True})
if state is None:
    raise RuntimeError(client.get_last_error())

sensor = client.get_sensor_observation(timeout_ms=1500)
```

`get_sensor_observation()` reads the latest cache. Without first enabling `sensorEnable`, fresh data is not guaranteed. Disable `sensorEnable` before disconnecting; if the application acquired control for another purpose, disable it before releasing control.

## Low-level: GPS and UWB

Low-level can read GPS/UWB in either `kConnected` or `kPrepared`; entering `kPrepared` is not required. Its timeout is in **milliseconds**, consistent with High-level.

```python
sensor = client.get_sensor_observation(timeout_ms=1000)
if sensor is not None:
    if sensor.gps.valid:
        print("GPS", sensor.gps.point.lat, sensor.gps.point.lng)
    if sensor.uwb.valid:
        print("UWB", sensor.uwb.distance, sensor.uwb.azimuth)
```

Low-level has no supported Walk-odometry access path. Use High-level when Walk odometry is required.

## Motors, IMU, remote controller, and power

- High-level: enable `motionEnable` and read the motion callback; use `get_power_info(timeout_ms=...)` for the latest power cache.
- Low-level: in `kPrepared`, call `get_latest_observation(timeout_ms=...)` for motors, IMU, TRC, and lightweight power data.

Entering Low-level `kPrepared` switches the robot to the joint-control path. Do not enter Low-level control on an unattended robot merely to read battery level. Prefer High-level for complete status; see [Query Device Status](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/query-device-status.md).

## Validate data before use

- Receiving `SensorObserved` does not make GPS/UWB valid; check each `valid` field.
- When `gps.valid == 0`, do not treat zero latitude and longitude as a real location.
- For UWB, also check `pair_state` to confirm pairing.
- Walk odometry is valid only in Walk mode; `valid` becomes false after leaving Walk.

## Success criteria

- Observation frames or a fresh cache are received continuously;
- the application consumes GPS, UWB, or odometry only when its `valid` field is set;
