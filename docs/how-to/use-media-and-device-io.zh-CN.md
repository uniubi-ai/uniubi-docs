# 使用语音、灯光和媒体帧

[English](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/use-media-and-device-io.md) | **简体中文**

语音播放、麦克风音频、摄像头视频和摄像头灯光属于不同能力。先区分控制面与媒体数据面。

## 支持范围

| 能力 | High-level | Low-level | 控制权要求 |
|---|---|---|---|
| 语音播放、暂停、文件管理 | 支持 | 不支持 | High-level `kControlled` |
| 摄像头灯光 | 支持 | 不支持 | High-level `kControlled` |
| 麦克风原始音频 | MediaBus | MediaBus | 与运动控制权无关 |
| 摄像头原始帧 / 编码帧 | MediaBus | MediaBus | 与运动控制权无关 |

> x86_64、i386、aarch64 默认开启 MediaBus。Orin 本机模式支持视频、音频和布局查询；远端模式通过 `media.setup(host)` 支持 PCM 采集和 RawBack 播放。远端视频订阅和布局查询返回 `kNotSupported`。SDK 头文件、运行库、Python 扩展与设备软件必须版本匹配。

## High-level：播放语音

语音播放和文件管理属于 High-level 控制面，应在 `kControlled` 下调用。

```python
client.start_audio_play({
    "list": [{"id": "1"}],
    "volume": 50,
    "repeat": 1,
})

detail = client.query_audio_play_detail()
client.pause_audio_play()
client.stop_audio_play()
```

自定义音频文件使用 `add_audio_file()` / `delete_audio_file()`；文件 ID、URL/本地文件模式和格式限制见 High-level API。语音播放不是麦克风采集接口。

## 自定义音频：通过 URL 上传并播放

播放服务在 **DV500** 上，SDK 通常运行在 **Orin 或 PC** 上，因此这些部署应使用 `url`。Orin 上的文件路径不是 DV500 的本地路径；`file` 仅适用于文件已经在 DV500 上且播放服务能直接读取的情况。

### 1. 准备文件和 HTTP 地址

将 `turn_left_90.wav` 放在 Orin 的独立目录中，在该目录启动 HTTP 服务：

```bash
cd ~/audio
python3 -m http.server 8000 --bind 172.29.110.2
```

这里假设 Orin 的 `eth0.100` 地址为 `172.29.110.2`，请用 `ip -4 addr show eth0.100` 核对。对应 URL 为 `http://172.29.110.2:8000/turn_left_90.wav`。保持这个终端运行，直到文件入库。

文件也可以放在 PC 的独立目录，通过 `python3 -m http.server 8000` 提供服务；URL 使用 **DV500 能访问的 PC IP**，确认网络路由和防火墙允许访问。不要使用 `localhost`，也不要把电脑文件路径作为 `file` 传入。

本次实机验证使用 16 kHz、单声道、16 位 PCM WAV，58,446 字节、1.824 秒。其他编码和大小限制需按目标机型确认。

### 2. 在 Orin 上添加并播放

以下示例假设 Python SDK 已安装，`import robot_motion_sdk` 可用。保存为 `play_custom_audio.py`，然后在另一个终端运行：

```bash
sudo python3 -u play_custom_audio.py
```

若 SDK 位于自定义目录，使用 `sudo env PYTHONPATH=<SDK包父目录> python3 -u play_custom_audio.py`。板上 SDK 锁文件为 root 属主时需要 sudo；不能仅依赖普通用户的 Python 环境。

```python
import time
import robot_motion_sdk as sdk

AUDIO_ID = "custom_turn_left_90"
URL = "http://172.29.110.2:8000/turn_left_90.wav"
client = None

def require(ok, operation):
    if not ok:
        raise RuntimeError(f"{operation}: {client.get_last_error()}")

def wait_until(check, seconds, message):
    deadline = time.monotonic() + seconds
    while not check():
        if time.monotonic() >= deadline:
            raise RuntimeError(message)
        time.sleep(0.2)

def audio_ready():
    result = client.query_audio_play_list({"type": "customVoice"})
    return result is not None and any(
        item["id"] == AUDIO_ID for item in result.get("customVoice", [])
    )

sdk.service.set_network_interface("eth0.100")
try:
    if not sdk.service.initial(None, "custom-audio-example"):
        raise RuntimeError("SDK initialization failed")
    if sdk.service.is_multi_device():
        raise RuntimeError("This example requires on-board Orin deployment")
    client = sdk.MotionHighLevelClient()
    require(client.connect(lease_ms=60000), "connect")
    wait_until(lambda: client.query_audio_play_detail() is not None,
               10, "Audio RPC unavailable")
    detail = client.query_audio_play_detail()
    if detail is None or detail.get("playing"):
        raise RuntimeError("Cannot start: status unavailable or audio already playing")
    require(client.start_control(timeout_ms=10000), "start_control")
    wait_until(lambda: client.get_state() == sdk.HighLevelState.kControlled,
               12, "Control acquisition timed out")
    if not audio_ready():
        require(client.add_audio_file({
            "id": AUDIO_ID,
            "name": "turn_left_90.wav",
            "url": URL,
            "describe": "Custom voice prompt",
        }, timeout_ms=30000), "add_audio_file")
        wait_until(audio_ready, 30, "Audio download/import did not finish")
    require(client.start_audio_play({
        "list": [{"id": AUDIO_ID}], "volume": 50, "repeat": 1,
    }), "start_audio_play")
    # Observe this short clip; retain control until playback has stopped.
    deadline = time.monotonic() + 15
    while True:
        detail = client.query_audio_play_detail()
        print(detail, flush=True)
        if detail is not None and detail.get("currentId") == AUDIO_ID:
            if not detail.get("playing"):
                break
        if time.monotonic() >= deadline:
            client.stop_audio_play()
            raise RuntimeError("Playback observation timed out")
        time.sleep(0.2)
finally:
    if client is not None:
        try:
            if client.get_state() == sdk.HighLevelState.kControlled:
                client.release_control()
        finally:
            client.disconnect()
    sdk.service.shutdown()
```

### 3. 判断结果和重复播放

- `start_control()` 可能先返回，必须等待状态达到 `kControlled`。
- **`add_audio_file()` 返回成功不代表下载入库已完成。** 轮询 `query_audio_play_list({"type":"customVoice"})`，直到目标 ID 出现，再调用播放；过早播放可能被拒绝。
- HTTP 日志应有来自 DV500 的 `GET` 和 `200`；文件入库后可关闭 HTTP 服务。后续播放使用 ID，无需再次下载。
- 重跑示例会复用同一 ID，不覆盖文件。换音频应换一个唯一 ID；不要用同一 ID 误认为已更新内容。
- `playing: true → false` 表示设备报告开始播放后结束；也可订阅播放事件。实机测试收到 `started → stopped`，实际听感仍需现场确认。

脚本播放一次、音量 50，并释放控制权，不发送运动动作。示例的播放观察上限是 15 秒，长音频应相应调整。若添加后 30 秒仍查不到 ID，检查 HTTP 日志、DV500 网络可达性、格式和存储容量，不要直接继续播放。

## High-level：控制摄像头灯光

```python
current = client.get_camera_light_brightness()
if not client.set_camera_light_brightness(50):
    raise RuntimeError(client.get_last_error())
```

亮度范围为 0–100，读取和设置均按 High-level API 的控制权要求执行。

## High-level / Low-level：订阅媒体帧

两类运动客户端都可派生同一种 `MediaBusClient`。媒体订阅不要求调用 `start_control()` 或 `set_motion_enable()`。

```python
if not sdk.MEDIA_ENABLED:
    raise RuntimeError("MediaBus is unavailable in this SDK build")

media = client.create_media_bus_client()  # client 可为 High-level 或 Low-level
if not media.setup():
    raise RuntimeError(media.get_last_error())

def on_video(channel, frame):
    print("raw video", channel, frame.size())

def on_encoded(channel, frame):
    print("encoded video", channel, frame.size())

def on_audio(channel, frame):
    print("microphone", channel, frame.size())

media.start_raw_video_frame(0, on_video)
media.start_encoded_video_frame(0, on_encoded)
media.start_raw_audio_frame(0, on_audio)
```

停止时先调用对应的 `stop_*_frame()`，再 `media.shutdown()`。回调返回后如需继续使用帧数据，应在回调内复制数据，不要长期持有底层视图。
