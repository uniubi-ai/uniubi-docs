# 使用语音、灯光和媒体帧

[English](use-media-and-device-io.md) | **简体中文**

语音播放、麦克风音频、摄像头视频和摄像头灯光属于不同能力。先区分控制面与媒体数据面。

## 支持范围

| 能力 | High-level | Low-level | 控制权要求 |
|---|---|---|---|
| 语音播放、暂停、文件管理 | 支持 | 不支持 | High-level `kControlled` |
| 摄像头灯光 | 支持 | 不支持 | High-level `kControlled` |
| 麦克风原始音频 | MediaBus | MediaBus | 与运动控制权无关 |
| 摄像头原始帧 / 编码帧 | MediaBus | MediaBus | 与运动控制权无关 |

> MediaBus 仅支持 `aarch64` 机器人板内本地部署。运行前确认 `sdk.MEDIA_ENABLED == True`；远端 PC、多设备模式及 `x86_64/i386` 不提供媒体帧订阅。

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
