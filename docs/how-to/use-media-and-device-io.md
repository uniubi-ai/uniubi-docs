# Use Voice, Lights, and Media Frames

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/use-media-and-device-io.zh-CN.md)

Voice playback, microphone audio, camera video, and camera lights are separate capabilities. Distinguish control-plane operations from media data first.

## Support matrix

| Capability | High-level | Low-level | Control requirement |
|---|---|---|---|
| Voice playback, pause, and file management | Supported | Not supported | High-level `kControlled` |
| Camera light | Supported | Not supported | High-level `kControlled` |
| Raw microphone audio | MediaBus | MediaBus | Independent of motion control |
| Raw / encoded camera video | MediaBus | MediaBus | Independent of motion control |

> MediaBus supports local on-board deployment on `aarch64` only. Confirm `sdk.MEDIA_ENABLED == True` before use. Remote PCs, multi-device mode, `x86_64`, and `i386` do not provide media-frame subscriptions.

## High-level: play voice audio

Voice playback and file management are High-level control-plane operations and require `kControlled`.

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

Use `add_audio_file()` / `delete_audio_file()` for custom files. See the High-level API for file IDs, URL/local-file modes, and format restrictions. Voice playback is not a microphone-capture interface.

## High-level: control the camera light

```python
current = client.get_camera_light_brightness()
if not client.set_camera_light_brightness(50):
    raise RuntimeError(client.get_last_error())
```

Brightness ranges from 0 to 100. Follow the High-level API control requirements for both reading and writing.

## High-level / Low-level: subscribe to media frames

Either motion client can create the same `MediaBusClient`. Media subscription does not require `start_control()` or `set_motion_enable()`.

```python
if not sdk.MEDIA_ENABLED:
    raise RuntimeError("MediaBus is unavailable in this SDK build")

media = client.create_media_bus_client()  # High-level or Low-level client
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

On shutdown, call the matching `stop_*_frame()` methods before `media.shutdown()`. Copy frame data inside the callback if it must outlive the callback; do not retain an underlying view indefinitely.
