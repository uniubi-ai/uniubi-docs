# Uniubi Robot High-level Python API Reference

**English** | [简体中文](high-level.zh-CN.md)

[API Reference](../README.md) · [C++ API](../cpp/high-level.md)

Python module: `robot_motion_sdk`
Primary client: `sdk.MotionHighLevelClient`

This page documents the High-level Python API for both onboard and external-host deployments. The external-host path has been validated on a real robot; select the network interface that actually reaches the robot before initialization and create the client with the target Device ID (SN).

## 1. Minimal Initialization and Shutdown

This example only connects and releases resources explicitly. It does not start an action:

```python
import robot_motion_sdk as sdk

sdk.service.set_network_interface("eth0.100")
if not sdk.service.initial(None, "pythonApiExample"):
    raise RuntimeError("SDK initialization failed")

client = sdk.MotionHighLevelClient()
try:
    if not client.connect():
        raise RuntimeError(f"connect failed: {client.get_last_error()}")
    print("state:", client.get_state())
finally:
    client.disconnect()
    sdk.service.shutdown()
```

> Do not rely on Python garbage collection to destroy the client. Normal exit, exceptions, and signal-driven exit must all reach `finally`.

## 2. Python API Coverage

**Global service (`sdk.service`, corresponding to the `IMotionSdkService` singleton):**

| Capability / native name | Python API |
|---|---|
| `version()` | `sdk.service.version()` —— Returns the SDK version string |
| `setLogCallback` | `sdk.service.set_log_callback(cb)`; signature `(level: LogLevel, msg: str) -> None` |
| `setNetworkInterface` | `sdk.service.set_network_interface(iface: str)` — select the actual external-host interface, or `eth0.100` for High-level on the robot brain |
| `setDiscoverCallback` | `sdk.service.set_discover_callback(cb)`; signature `(sn: str, info_json: str) -> None` |
| `isMultiDevice` | `sdk.service.is_multi_device() -> bool` |
| `discoverDevices` | `sdk.service.discover_devices(timeout_ms=10000) -> bool` (non-blocking) |
| `initialService` | `sdk.service.initial(file_or_none, server_name, timeout_ms=30000)` |
| `shutdown` | `sdk.service.shutdown()` |

**High-level client (`sdk.MotionHighLevelClient`, corresponding to `IMotionHighLevelClient`):**

| Capability / native name | Python API |
|---|---|
| `create(asMaster=false)` / `create(deviceId)` | `MotionHighLevelClient(device_id="", as_master=False)` constructor; use an empty ID onboard (role selected by `as_master`), while external-host device addressing requires an SN |
| `connect / disconnect` | `connect(lease_ms=0)` / `disconnect()` |
| `startControl / releaseControl` | `start_control(timeout_ms=10000)` / `release_control()` |
| `getState / getLastError` | `get_state()` / `get_last_error()` (return enum) |
| `emergencyStop / recoveryStand` | `emergency_stop(timeout_ms=5000)` / `recovery_stand(timeout_ms=5000)` |
| `damp / standUp / lieDown / move` | `damp()` / `stand_up()` / `lie_down()` / `move(vx, vy, vyaw, timeout_ms=5000)` |
| `startAction / stopAction / setActionParams` | `start_action(action, params=None, ...)` / `stop_action()` / `set_action_params(params=None)`; `params` connects to Python dict, binding internally converts to JSON |
| `queryMotionState / getMotionCapabilities / querySystemStatus` | `query_motion_state()` / `get_motion_capabilities()` / `query_system_status()`; return Python dict (automatic json.loads) |
| `getMotorLayout` | `get_motor_layout(timeout_ms=5000)`; return `sdk.MotorLayout`, failure `None` |
| `setObservedEnable` | `set_observed_enable(params=None, timeout_ms=5000)`; requires `HighLevelState.kControlled`: call `start_control()` and wait for the master-role switch and control acquisition. It returns the effective switch dict on success or `None` on failure; calling it while only `kConnected` fails with `HighLevelError.kActionRejected` |
| `getPowerInfo` | `get_power_info(timeout_ms=5)`; `timeout_ms` is the freshness window (milliseconds), return `sdk.PowerObserved` or `None` |
| `getSensorObservation` | `get_sensor_observation(timeout_ms=5000)`; Read the complete sensor buffer and return `sdk.SensorObserved` or `None` |
| `setMotionObservedCallback` | `set_motion_observed_callback(cb)`; signature `(obs: sdk.LowLevelMotionObserved)` |
| `setSensorObservedCallback` | `set_sensor_observed_callback(cb)`; register before `connect()`; signature `(sensor: sdk.SensorObserved)` |
| `getCameraLightBrightness / setCameraLightBrightness` | `get_camera_light_brightness()` (return dict / None) / `set_camera_light_brightness(brightness)`; `brightness` value 0~100 |
| `startAudioPlay / stopAudioPlay / pauseAudioPlay` | `start_audio_play(params)` / `stop_audio_play()` / `pause_audio_play()` |
| `addAudioFile / deleteAudioFile / queryAudioPlayDetail / queryAudioPlayList` | `add_audio_file(params)` / `delete_audio_file(params)` / `query_audio_play_detail()` / `query_audio_play_list(params=None)` |
| `createMediaBusClient` | `create_media_bus_client()`; returns `sdk.MediaBusClient` (see below) |
| `setConnectCallback` | `set_connect_callback(cb)` or decorator `@client.on_connect`; signature `(state, error)` |
| `setEventCallback` | `set_event_callback(cb)` or decorator `@client.on_event`; signature `(topic: str, payload_json: str)` |

**MediaBus client (`sdk.MediaBusClient`, corresponding to `IMediaBusClient` and returned by `create_media_bus_client()`):**

| Capability / native name | Python API |
|---|---|
| `setup / shutdown` | `setup()` / `shutdown()` |
| `getMediaLayout` | `get_media_layout()`; return `sdk.MediaLayout` or `None` |
| `startRawVideoFrame / stopRawVideoFrame` | `start_raw_video_frame(channel, callback)` / `stop_raw_video_frame(channel)`; callback signature `(channel: int, frame: sdk.VideoFrame)` |
| `startRawAudioFrame / stopRawAudioFrame` | `start_raw_audio_frame(channel, callback)` / `stop_raw_audio_frame(channel)`; callback signature `(channel: int, frame: sdk.AudioFrame)` |
| `startEncodedVideoFrame / stopEncodedVideoFrame` | `start_encoded_video_frame(channel, callback)` / `stop_encoded_video_frame(channel)`; callback signature `(channel: int, frame: sdk.EncodedVideoFrame)` |

**Media frame types**

| Python types | Corresponding C++ types | Common fields/methods |
|---|---|---|
| `sdk.AudioFrame` | `Uface::Media::AudioFrame` | `frame.data()`, `frame.size()`, `frame.get_fd()`, `frame.frame_info.sample_rate/sample_format/channel_count/timestamp/sequence` |
| `sdk.VideoFrame` | `Uface::Media::VideoFrame` | `frame.data()`, `frame.size()`, `frame.get_fd()`, `frame.frame_info.width/height/pixel_format/stride/timestamp/sequence`, `frame.plane_view(plane)` |
| `sdk.EncodedVideoFrame` | `Uface::Stream::CMediaFrame` | `frame.data()`, `frame.size()`, `frame.frame_type`, `frame.pts`, `frame.utc`, `frame.sequence`, `frame.frame_info`, `frame.video_info` |
| `sdk.VideoFramePlaneView` | Video plane read-only view | `rows`, `row_bytes`, `row_view(row)`, used to read non-contiguous/original video with stride by row |

The Python API does not expose a separate MediaBus package; the Motion SDK provides the frame wrappers directly. Encoded frames use `EncodedVideoFrame`, with no public Python `VideoPacket` type. `sdk.CMediaFrame` remains as a Low-level compatibility alias.

### 2.1 `query_system_status()` return schema

`query_system_status(timeout_ms=5000)` is available in `HighLevelState.kConnected`; it does not require motion-control ownership. On success it returns a Python dict containing `battery` and `network`. On failure it returns `None`; call `get_last_error()` for the reason.

```python
status = client.query_system_status()
if status is None:
    raise RuntimeError(client.get_last_error())

battery = status.get("battery") or {}
network = status.get("network") or {}
```

Typical return value:

```json
{
  "battery": {
    "abnormalStatus": 0,
    "statusCode": 0,
    "cycleCount": 186,
    "remainChargeTime": 52,
    "remainDischargeTime": 198,
    "power": 76.5,
    "health": 93.2,
    "temperature": 31.4,
    "fullCharge": 5180.0,
    "remaining": 3962.7,
    "current": 1.84,
    "voltage": 15.28
  },
  "network": {
    "ether":   { "enable": true,  "ipv4Addr": "...", "ipv4Gateway": "...", "ipv4Mask": "...", "mac": "...", "status": 0 },
    "hotspot": { "enable": false, "ipv4Addr": "...", "ipv4Gateway": "...", "ipv4Mask": "...", "mac": "...", "status": 1 },
    "mobile":  { "enable": true,  "ipv4Addr": "...", "ipv4Gateway": "...", "ipv4Mask": "...", "mac": "...", "signalLevel": 0, "simCardSta": true, "status": 0 },
    "wlan":    { "enable": true,  "ipv4Addr": "...", "ipv4Gateway": "...", "ipv4Mask": "...", "mac": "...", "status": 0 }
  }
}
```

`battery` fields:

| Field | Python type | Unit | Meaning |
|---|---|---|---|
| `abnormalStatus` | `int` | — | Power-circuit fault flag; nonzero indicates a fault |
| `statusCode` | `int` | — | BMS status bitmask; see the table below |
| `cycleCount` | `int` | cycles | Accumulated charge/discharge cycles |
| `remainChargeTime` | `int` | min | Estimated time to full charge; valid while charging |
| `remainDischargeTime` | `int` | min | Estimated remaining runtime at the current load |
| `power` | `float` | % | State of charge, range 0–100 |
| `health` | `float` | % | Battery state of health, range 0–100 |
| `temperature` | `float` | °C | Battery temperature |
| `fullCharge` | `float` | mAh | Full-charge capacity |
| `remaining` | `float` | mAh | Remaining capacity |
| `current` | `float` | A | Battery current; positive while charging, negative while discharging |
| `voltage` | `float` | V | Total battery voltage |

`battery.statusCode` bitmask (`statusCode & bit != 0` means the protection bit is active):

| Bit | Value | Meaning |
|---|---|---|
| bit0 | `0x0001` | Pack undervoltage protection |
| bit1 | `0x0002` | Cell undervoltage protection |
| bit2 | `0x0004` | Pack overvoltage protection |
| bit3 | `0x0008` | Cell overvoltage protection |
| bit4 | `0x0010` | Charging complete |
| bit5 | `0x0020` | Discharge overcurrent protection |
| bit6 | `0x0040` | Charge overcurrent protection |
| bit7 | `0x0080` | Short-circuit protection |
| bit8 | `0x0100` | Low-temperature discharge protection |
| bit9 | `0x0200` | Low-temperature charge protection |
| bit10 | `0x0400` | High-temperature discharge protection |
| bit11 | `0x0800` | High-temperature charge protection |
| bit12 | `0x1000` | MOS overtemperature protection |
| bit13 | `0x2000` | Cell-sampling disconnect protection |
| bit14 | `0x4000` | Cell-voltage imbalance protection |
| bit15 | `0x8000` | Cell-voltage measurement failure |

`network` may contain `ether`, `hotspot`, `mobile`, and `wlan` dictionaries. Interfaces or fields unavailable on a device model or software version may be omitted, so application code should read them with `.get()`.

| Field | Python type | Meaning |
|---|---|---|
| `enable` | `bool` | Whether the interface is enabled |
| `ipv4Addr` | `str` | IPv4 address |
| `ipv4Gateway` | `str` | IPv4 gateway |
| `ipv4Mask` | `str` | IPv4 subnet mask |
| `mac` | `str` | MAC address |
| `status` | `int` | `0` connected, `1` disconnected, `2` connecting |
| `signalLevel` | `int` | `mobile` only: `0` good (>22 dB), `2` moderate (>15 dB), `3` poor (≤15 dB) |
| `simCardSta` | `bool` | `mobile` only: whether the SIM card is ready |

## 3. Exit Deadlock Avoidance

**Typical deadlock sequence:**
- The Python main thread holds the GIL while interpreter shutdown starts garbage collection.
- Garbage collection destroys `client`, enters the C++ destruction chain, calls internal `disconnect()`, and waits for an SDK thread.
- The SDK thread needs the GIL released before its RPC path can continue.
- Destroying Python callback objects held by that SDK thread also requires the GIL.
- **Main thread waits for internal thread to end → internal thread waits for GIL → deadlock**

**Avoidance**:

```python
# ❌ Incorrect: relying on garbage collection for destruction
def main():
    client = sdk.MotionHighLevelClient()
    client.connect()
    ...
    # Function returns and client enters GC: deadlock risk

# ✓ Correct: explicit cleanup with try/finally
def main():
    client = sdk.MotionHighLevelClient()
    try:
        client.connect()
        ...
    finally:
        client.disconnect()       # The binding releases the GIL so SDK threads can complete cleanup
        sdk.service.shutdown()
```

**SIGINT/SIGTERM handling:** the handler must **only set a flag** and must not perform I/O or SDK calls. Let the main loop observe the flag and perform cleanup in `finally`:

```python
_stop = False
def _on_signal(signum, frame):
    global _stop
    _stop = True
signal.signal(signal.SIGINT, _on_signal)
signal.signal(signal.SIGTERM, _on_signal)
```

Full runnable example: [`uniubi_robot_sdk_py/examples/example_highlevel.py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/examples/example_highlevel.py)

## 4. Python Usage Examples

The Python example provides the interactive console verified on Dog No. 8's Orin and follows the same behavior as C++ `example_highlevel`: the process maintains a High-level connection and control lease; starting an action, updating parameters, and stopping are separate commands; and startup never triggers an action automatically.

Use the system `python3` on the robot compute board. Install the Python SDK into that interpreter, then run the example with root privileges.

Use read-only mode for the first connection:

```bash
sudo env \
  LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  python3 examples/example_highlevel.py --read-only
```

After entering the CLI, do a read-only check:

```text
highlevel> status
highlevel> motors
highlevel> sensor 5
highlevel> odom 5
```

Acquire control explicitly before issuing actions:

```text
highlevel> take
highlevel> start walking {"lineVelocityX":0.0,"lineVelocityY":0.0,"velocity":0.0}
highlevel> send 3 {"lineVelocityX":0.3,"lineVelocityY":0,"velocity":0}
highlevel> stop
highlevel> release
highlevel> quit
```

When `send` expires it clears all three walking velocities but does not stop the current action; only `stop` calls `stop_action()`. `quit`, EOF, SIGINT, and SIGTERM all use one cleanup path: disable observations, clear walking velocity, release control, call `disconnect()` explicitly, and finally call `service.shutdown()` without relying on Python garbage collection.

`stop_action()` stops the current action through the asynchronous finalization path, then returns the effective action to zero-speed `walking` while retaining control. Calling `start_action("walking", {"lineVelocityX": 0.0, "lineVelocityY": 0.0, "velocity": 0.0})` is the equivalent explicit transition. `set_action_params()` or `/cmd_vel` updates the current action's supported parameters, including speed parameters for actions such as `bipedStand` and `handstand`; it does not stop or switch the action.

Use the program's `help` command for the complete command set. The full source is [`uniubi_robot_sdk_py/examples/example_highlevel.py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/examples/example_highlevel.py). The minimal underlying API lifecycle is:

```python
import time
import robot_motion_sdk as sdk

sdk.service.set_network_interface("eth0.100")
sdk.service.initial(None, "myAppHighLevel")
client = sdk.MotionHighLevelClient()
try:
    client.connect(lease_ms=60000)
    client.start_control(timeout_ms=10000)
    while client.get_state() != sdk.HighLevelState.kControlled:
        time.sleep(0.05)
    client.start_action("walking", {"lineVelocityX": 0.0,
                                    "lineVelocityY": 0.0,
                                    "velocity": 0.0})
    client.set_action_params({"lineVelocityX": 0.3})
    time.sleep(3)
    client.set_action_params({"lineVelocityX": 0.0,
                              "lineVelocityY": 0.0,
                              "velocity": 0.0})
    client.stop_action()
    client.release_control()
finally:
    client.disconnect()
    sdk.service.shutdown()
```

Complete example of media frame subscription: `Python/examples/example_media_frames.py`.

```bash
export PYTHONPATH=$SDK_ROOT/Python:$PYTHONPATH
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" PYTHONPATH="$PYTHONPATH" \
  python3 $SDK_ROOT/Python/examples/example_media_frames.py \
    [config|-] [client_id] [device_id|-] [video_channel] [audio_channel] [stream] [seconds] [network_iface|-]
```

Minimal usage:

```python
import time
import robot_motion_sdk as sdk

sdk.service.set_network_interface("eth0.100")
sdk.service.initial(None, "mediaFramePythonExample")

client = sdk.MotionHighLevelClient()
media = client.create_media_bus_client()
try:
    media.setup()
    media.start_raw_video_frame(0, lambda ch, frame: print("raw", ch, frame.size()))
    media.start_encoded_video_frame(0, lambda ch, frame: print("encoded", ch, frame.size()))
    media.start_raw_audio_frame(0, lambda ch, frame: print("audio", ch, frame.size()))
    time.sleep(10)
finally:
    media.stop_encoded_video_frame(0)
    media.stop_raw_video_frame(0)
    media.stop_raw_audio_frame(0)
    media.shutdown()
    client.disconnect()
    sdk.service.shutdown()
```

> In Python, `frame.data()` returns a `bytes` copy. For raw NVIDIA video frames, use `frame.plane_view(plane).row_view(row)` for row-wise access; the example implements the complete save path.

---


## 5. Important Considerations

- Do not perform blocking I/O, long computations, or SDK re-entry in callbacks. Hand expensive work to an application thread.
- `robot_motion_sdk`, its native binding, and `librobotMotionSdk.so` must come from the same SDK version and target architecture.
- Every exit path must call `disconnect()` explicitly, followed by `sdk.service.shutdown()`.
- Onboard High-level must select `eth0.100` before initialization. An external host must select the interface that actually reaches the robot and create the client with the target Device ID (SN).

## 6. Troubleshooting

| Symptom | Check first |
|---|---|
| `sdk.service.initial(...)` fails | Library path, SDK/binding versions, configuration file, and whether the selected interface exists |
| State does not advance after `connect()` | Confirm that `eth0.100` exists and is `UP`, and that the robot runtime service is healthy |
| Process hangs during exit | Active callbacks or subscription threads, and missing `disconnect()` / `shutdown()` calls |
| API returns `None` or times out | Runtime service, observation switches, timeout units, and current client state |
