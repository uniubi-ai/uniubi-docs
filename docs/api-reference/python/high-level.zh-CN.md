# 宇泛机器人 High-level Python API 参考

[English](high-level.md) | **简体中文**

[返回 API 参考](../README.zh-CN.md) · [查看 C++ API](../cpp/high-level.zh-CN.md)

Python 模块：`robot_motion_sdk`
主要客户端：`sdk.MotionHighLevelClient`

本页说明板载 High-level Python API。当前文档不据此声称 Python 已完成外部主机真机验证；外部主机已确认的路径以 C++ 文档为准。

## 一、最小初始化与退出

以下示例只建立连接并显式释放资源，不会自动执行动作：

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

> 不要依赖 Python 垃圾回收销毁客户端。所有正常退出、异常和信号退出路径都必须进入 `finally`。

## 二、Python API 覆盖范围

**全局服务（`sdk.service` —— 对应 `IMotionSdkService` 单例）：**

| 功能 / native 名称 | Python API |
|---|---|
| `version()` | `sdk.service.version()` —— 返回 SDK 版本字符串 |
| `setLogCallback` | `sdk.service.set_log_callback(cb)`；签名 `(level: LogLevel, msg: str) -> None` |
| `setNetworkInterface` | `sdk.service.set_network_interface(iface: str)` —— 外部主机指定实际网卡；大脑侧 High-level 指定 `eth0.100` |
| `setDiscoverCallback` | `sdk.service.set_discover_callback(cb)`；签名 `(sn: str, info_json: str) -> None` |
| `isMultiDevice` | `sdk.service.is_multi_device() -> bool` |
| `discoverDevices` | `sdk.service.discover_devices(timeout_ms=10000) -> bool`（非阻塞） |
| `initialService` | `sdk.service.initial(file_or_none, server_name, timeout_ms=30000)` |
| `shutdown` | `sdk.service.shutdown()` |

**HighLevel client（`sdk.MotionHighLevelClient` —— 对应 `IMotionHighLevelClient`）：**

| 功能 / native 名称 | Python API |
|---|---|
| `create(asMaster=false)` / `create(deviceId)` | `MotionHighLevelClient(device_id="", as_master=False)` 构造；板内空串（按 `as_master` 协商主从）、远端必传 SN |
| `connect / disconnect` | `connect(lease_ms=0)` / `disconnect()` |
| `startControl / releaseControl` | `start_control(timeout_ms=10000)` / `release_control()` |
| `getState / getLastError` | `get_state()` / `get_last_error()`（返回 enum） |
| `emergencyStop / recoveryStand` | `emergency_stop(timeout_ms=5000)` / `recovery_stand(timeout_ms=5000)` |
| `damp / standUp / lieDown / move` | `damp()` / `stand_up()` / `lie_down()` / `move(vx, vy, vyaw, timeout_ms=5000)` |
| `startAction / stopAction / setActionParams` | `start_action(action, params=None, ...)` / `stop_action()` / `set_action_params(params=None)`；`params` 接 Python dict，binding 内部转 JSON |
| `queryMotionState / getMotionCapabilities / querySystemStatus` | `query_motion_state()` / `get_motion_capabilities()` / `query_system_status()`；返回 Python dict（自动 json.loads） |
| `getMotorLayout` | `get_motor_layout(timeout_ms=5000)`；返回 `sdk.MotorLayout`，失败 `None` |
| `setObservedEnable` | `set_observed_enable(params=None, timeout_ms=5000)`；要求 `HighLevelState.kControlled`：先调用 `start_control()`，等待目标端完成 master role 切换并取得控制权。成功返回实际开关 dict，失败返回 `None`；仅处于 `kConnected` 时调用会失败并返回 `HighLevelError.kActionRejected` |
| `getPowerInfo` | `get_power_info(timeout_ms=5)`；`timeout_ms` 是新鲜度窗口（毫秒），返回 `sdk.PowerObserved` 或 `None` |
| `getSensorObservation` | `get_sensor_observation(timeout_ms=5000)`；读取完整传感器缓存，返回 `sdk.SensorObserved` 或 `None` |
| `setMotionObservedCallback` | `set_motion_observed_callback(cb)`；签名 `(obs: sdk.LowLevelMotionObserved)` |
| `setSensorObservedCallback` | `set_sensor_observed_callback(cb)`；须在 `connect()` 前注册，签名 `(sensor: sdk.SensorObserved)` |
| `getCameraLightBrightness / setCameraLightBrightness` | `get_camera_light_brightness()`（返回 dict / None）/ `set_camera_light_brightness(brightness)`；`brightness` 取值 0~100 |
| `startAudioPlay / stopAudioPlay / pauseAudioPlay` | `start_audio_play(params)` / `stop_audio_play()` / `pause_audio_play()` |
| `addAudioFile / deleteAudioFile / queryAudioPlayDetail / queryAudioPlayList` | `add_audio_file(params)` / `delete_audio_file(params)` / `query_audio_play_detail()` / `query_audio_play_list(params=None)` |
| `createMediaBusClient` | `create_media_bus_client()`；返回 `sdk.MediaBusClient`（见下表）|
| `setConnectCallback` | `set_connect_callback(cb)` 或装饰器 `@client.on_connect`；签名 `(state, error)` |
| `setEventCallback` | `set_event_callback(cb)` 或装饰器 `@client.on_event`；签名 `(topic: str, payload_json: str)` |

**MediaBus client（`sdk.MediaBusClient` —— 对应 `IMediaBusClient`，由 `create_media_bus_client()` 工厂分配）：**

| 功能 / native 名称 | Python API |
|---|---|
| `setup / shutdown` | `setup()` / `shutdown()` |
| `getMediaLayout` | `get_media_layout()`；返回 `sdk.MediaLayout` 或 `None` |
| `startRawVideoFrame / stopRawVideoFrame` | `start_raw_video_frame(channel, callback)` / `stop_raw_video_frame(channel)`；回调签名 `(channel: int, frame: sdk.VideoFrame)` |
| `startRawAudioFrame / stopRawAudioFrame` | `start_raw_audio_frame(channel, callback)` / `stop_raw_audio_frame(channel)`；回调签名 `(channel: int, frame: sdk.AudioFrame)` |
| `startEncodedVideoFrame / stopEncodedVideoFrame` | `start_encoded_video_frame(channel, callback)` / `stop_encoded_video_frame(channel)`；回调签名 `(channel: int, frame: sdk.EncodedVideoFrame)` |

**媒体帧类型**

| Python 类型 | 对应 C++ 类型 | 常用字段 / 方法 |
|---|---|---|
| `sdk.AudioFrame` | `Uface::Media::AudioFrame` | `frame.data()`、`frame.size()`、`frame.get_fd()`、`frame.frame_info.sample_rate/sample_format/channel_count/timestamp/sequence` |
| `sdk.VideoFrame` | `Uface::Media::VideoFrame` | `frame.data()`、`frame.size()`、`frame.get_fd()`、`frame.frame_info.width/height/pixel_format/stride/timestamp/sequence`、`frame.plane_view(plane)` |
| `sdk.EncodedVideoFrame` | `Uface::Stream::CMediaFrame` | `frame.data()`、`frame.size()`、`frame.frame_type`、`frame.pts`、`frame.utc`、`frame.sequence`、`frame.frame_info`、`frame.video_info` |
| `sdk.VideoFramePlaneView` | 视频平面只读视图 | `rows`、`row_bytes`、`row_view(row)`，用于按行读取非连续 / 带 stride 的原始视频 |

Python API 不暴露 MediaBus Python 包，帧格式由 Motion SDK 自身封装；编码帧使用 `EncodedVideoFrame`，没有 `VideoPacket` Python 公共类型。`sdk.CMediaFrame` 保留为底层兼容别名。

## 三、退出死锁规避（必读）

**典型死锁场景**：
- Python 主线程持有 GIL → 解释器 atexit 阶段开始 GC
- GC 析构 `client` 触发 C++ 析构链 → 内部 `disconnect()` → 等待 SDK 内部线程结束
- SDK 内部线程在 RPC 调用中，需要主线程释放 GIL 才能继续
- SDK 内部线程持有的 Python 回调对象需要析构 —— 析构也需要 GIL
- **主线程等内部线程结束 → 内部线程等 GIL → 死锁**

**规避做法**：

```python
# ❌ 不要这样：靠 GC 析构
def main():
    client = sdk.MotionHighLevelClient()
    client.connect()
    ...
    # 函数结束，client 进入 GC —— 死锁风险

# ✓ 正确：try/finally 显式释放
def main():
    client = sdk.MotionHighLevelClient()
    try:
        client.connect()
        ...
    finally:
        client.disconnect()       # 主线程持 GIL，SDK binding 内部释放 GIL，内部线程才能继续完成清理
        sdk.service.shutdown()
```

**SIGINT/SIGTERM 处理**：handler 内**只置位标志**，不做任何 IO / SDK 调用；在主循环检测标志后走 finally：

```python
_stop = False
def _on_signal(signum, frame):
    global _stop
    _stop = True
signal.signal(signal.SIGINT, _on_signal)
signal.signal(signal.SIGTERM, _on_signal)
```

完整可运行示例：[`uniubi_robot_sdk_py/examples/example_highlevel.py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/examples/example_highlevel.py)

## 四、Python 使用示例

Python 示例参考 8 号狗 Orin 上验证过的交互控制台，与 C++ `example_highlevel` 保持一致：进程保持一个 High-level 连接和控制 lease，动作启动、参数修改和停止是相互独立的命令，程序不会自动执行动作。

大脑上直接使用系统 `python3`。先将 Python SDK 安装到系统 Python，再以 root 权限运行示例。

首次连接使用只读模式：

```bash
sudo env \
  LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  python3 examples/example_highlevel.py --read-only
```

进入 CLI 后先做只读检查：

```text
highlevel> status
highlevel> motors
highlevel> sensor 5
highlevel> odom 5
```

需要控制时显式取权并执行动作：

```text
highlevel> take
highlevel> start walking
highlevel> send 3 {"lineVelocityX":0.3,"lineVelocityY":0,"velocity":0}
highlevel> stop
highlevel> release
highlevel> quit
```

`send` 到时后会清零 walking 三轴速度，但不会停止当前动作；只有 `stop` 调用 `stop_action()`。`quit`、EOF、SIGINT 和 SIGTERM 都会进入统一清理流程：关闭观测、清零 walking 速度、释放控制权、显式 `disconnect()`，最后 `service.shutdown()`，不依赖 Python GC。

完整命令以程序内 `help` 为准，完整源码见 [`uniubi_robot_sdk_py/examples/example_highlevel.py`](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/examples/example_highlevel.py)。底层 API 的最小生命周期如下：

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

媒体帧订阅完整示例：`Python/examples/example_media_frames.py`。

```bash
export PYTHONPATH=$SDK_ROOT/Python:$PYTHONPATH
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" PYTHONPATH="$PYTHONPATH" \
  python3 $SDK_ROOT/Python/examples/example_media_frames.py \
    [config|-] [client_id] [device_id|-] [video_channel] [audio_channel] [stream] [seconds] [network_iface|-]
```

最小用法：

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

> Python 中 `frame.data()` 返回 `bytes` 拷贝；处理 NVIDIA 原始视频帧时推荐使用 `frame.plane_view(plane).row_view(row)` 按行读取，示例程序已实现保存逻辑。

---


## 五、注意事项

- 回调中不要执行阻塞 IO、长时间计算或 SDK 重入调用；耗时处理转交业务线程。
- `robot_motion_sdk`、native binding 和 `librobotMotionSdk.so` 必须来自同一 SDK 版本与目标架构。
- 所有退出路径都要显式 `disconnect()`，最后调用 `sdk.service.shutdown()`。
- 大脑侧 High-level 必须在初始化前指定 `eth0.100`；外部主机 Python 尚未在本文中声明完成真机验证。

## 六、常见问题

| 现象 | 优先检查 |
|---|---|
| `sdk.service.initial(...)` 失败 | 动态库路径、SDK/绑定版本、配置文件和所选网卡是否存在 |
| `connect()` 后状态不变化 | 确认 `eth0.100` 存在且为 `UP`，机器人运行时服务正常 |
| 程序退出卡住 | 是否仍有回调或订阅线程，以及是否遗漏 `disconnect()` / `shutdown()` |
| 返回 `None` 或超时 | 运行时服务、观测开关、接口超时单位及当前客户端状态 |
