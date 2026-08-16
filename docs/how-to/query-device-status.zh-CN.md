# 查询设备状态

[English](query-device-status.md) | **简体中文**

应用通常需要区分“完整系统状态”和“控制帧中的轻量电源观测”。两者不是同一接口。

## 支持范围

| 信息 | High-level | Low-level |
|---|---|---|
| 完整设备、电池和网络状态 | `query_system_status()` | 不支持 |
| 轻量电源观测 | `get_power_info()` | `get_latest_observation().power` |
| 电机 / IMU / 遥控器实时状态 | 运控观测回调 | `get_latest_observation()` |

## High-level：完整系统状态

`query_system_status()` 在 `kConnected` 即可调用，不需要为了查询网络或电池快照取得运动控制权。

```python
status = client.query_system_status()
if status is None:
    raise RuntimeError(client.get_last_error())

battery = status.get("battery") or {}
network = status.get("network") or {}
print("battery", battery)
print("interfaces", list(network.keys()))
```

完整 dict schema 和字段语义见 [Python High-level API：`query_system_status()` 返回结构](../api-reference/python/high-level.zh-CN.md#21-query_system_status-返回结构)。业务应容忍设备型号或软件版本没有提供某个可选字段。

## High-level：轻量电源缓存

`get_power_info(timeout_ms=...)` 读取运控观测中的最近一帧电源数据。必须先在 `kControlled` 下开启 `motionEnable`，否则没有新鲜缓存时返回 `None`。

```python
client.set_observed_enable({"motionEnable": True, "sensorEnable": False})
power = client.get_power_info(timeout_ms=1000)
if power is not None:
    print(power.power, power.charge_voltage, power.temper)
```

## Low-level：轻量电源观测

Low-level 没有 `query_system_status()`。电量、电压、电流和温度只能从 `LowLevelMotionObserved.power` 读取：

```python
obs = client.get_latest_observation(timeout_ms=20)
if obs is not None:
    print(obs.power.power, obs.power.charge_voltage, obs.power.temper)
```

该接口要求 `kPrepared`，属于 Low-level 关节控制会话。不要为了普通状态页临时进入 Low-level 控制；应用只需要设备、电池或网络快照时应使用 High-level。
