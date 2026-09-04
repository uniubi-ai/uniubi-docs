# Query Device Status

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/query-device-status.zh-CN.md)

Applications must distinguish complete system status from the lightweight power observation carried in motion frames. They are different interfaces.

## Support matrix

| Information | High-level | Low-level |
|---|---|---|
| Complete device, battery, and network status | `query_system_status()` | Not supported |
| Lightweight power observation | `get_power_info()` | `get_latest_observation().power` |
| Real-time motors / IMU / remote controller | Motion-observation callback | `get_latest_observation()` |

## High-level: complete system status

`query_system_status()` is available in `kConnected`; acquiring motion control is unnecessary for a network or battery snapshot.

```python
status = client.query_system_status()
if status is None:
    raise RuntimeError(client.get_last_error())

battery = status.get("battery") or {}
network = status.get("network") or {}
print("battery", battery)
print("interfaces", list(network.keys()))
```

See the [Python High-level API: `query_system_status()` return schema](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/high-level.md#21-query_system_status-return-schema) for the complete dict schema and field semantics. Applications should tolerate optional fields that are unavailable on a device model or software build.

## High-level: lightweight power cache

`get_power_info(timeout_ms=...)` reads the latest power data carried in motion observations. Enable `motionEnable` while in `kControlled` first; without a fresh cache it returns `None`.

```python
client.set_observed_enable({"motionEnable": True, "sensorEnable": False})
power = client.get_power_info(timeout_ms=1000)
if power is not None:
    print(power.power, power.charge_voltage, power.temper)
```

## Low-level: lightweight power observation

Low-level does not provide `query_system_status()`. Read level, voltage, current, and temperature from `LowLevelMotionObserved.power`:

```python
obs = client.get_latest_observation(timeout_ms=20)
if obs is not None:
    print(obs.power.power, obs.power.charge_voltage, obs.power.temper)
```

This call requires `kPrepared` and belongs to a Low-level joint-control session. Do not enter Low-level control merely to populate a general status page. Use High-level when the application only needs a device, battery, or network snapshot.
