# Uniubi Robot High-level Python API Reference

**English** | [简体中文](high-level.zh-CN.md)

[API Reference](../README.md) · [C++ API](../cpp/high-level.md)

Python module: `robot_motion_sdk`
Primary client: `sdk.MotionHighLevelClient`

This page documents the onboard High-level Python API. It does not claim external-host real-robot validation for Python; use the C++ page for the currently documented external-host path.

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
| `initialService` | `sdk.service.initial(file_or_none, server_name, timeout=30)` |
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
| `getPowerInfo` | `get_power_info(timeout_us=5000)`; `timeout_us` is the freshness window (microseconds), return `sdk.PowerObserved` or `None` |
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
highlevel> start walking
highlevel> send 3 {"lineVelocityX":0.3,"lineVelocityY":0,"velocity":0}
highlevel> stop
highlevel> release
highlevel> quit
```

When `send` expires it clears all three walking velocities but does not stop the current action; only `stop` calls `stop_action()`. `quit`, EOF, SIGINT, and SIGTERM all use one cleanup path: disable observations, clear walking velocity, release control, call `disconnect()` explicitly, and finally call `service.shutdown()` without relying on Python garbage collection.

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
    client.start_action("walking")
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
- Onboard High-level must select `eth0.100` before initialization. This page does not claim completed external-host real-robot validation for Python.

## 6. Troubleshooting

| Symptom | Check first |
|---|---|
| `sdk.service.initial(...)` fails | Library path, SDK/binding versions, configuration file, and whether the selected interface exists |
| State does not advance after `connect()` | Confirm that `eth0.100` exists and is `UP`, and that the robot runtime service is healthy |
| Process hangs during exit | Active callbacks or subscription threads, and missing `disconnect()` / `shutdown()` calls |
| API returns `None` or times out | Runtime service, observation switches, timeout units, and current client state |
