# Uniubi Robot MediaBus Python API Reference

**English** | [简体中文](media.zh-CN.md)

[API Reference](../README.md) · [C++ API](../cpp/media.md)

Python module: `robot_motion_sdk`

> The MediaBus Python API is supported only when the SDK and robot runtime run together on an onboard `aarch64` system. The `x86_64` and `i386` wheels do not include media-frame bindings by default.

## 1. API Overview

| Capability | Python API |
|---|---|
| Check bindings | `sdk.MEDIA_ENABLED` |
| Create client | `client.create_media_bus_client()` |
| Start / stop | `media.setup()` / `media.shutdown()` |
| Query layout | `media.get_media_layout()` |
| Raw video | `start_raw_video_frame()` / `stop_raw_video_frame()` |
| Raw audio | `start_raw_audio_frame()` / `stop_raw_audio_frame()` |
| Encoded video | `start_encoded_video_frame()` / `stop_encoded_video_frame()` |

## 2. Usage Example

```python
import robot_motion_sdk as sdk

if not sdk.MEDIA_ENABLED:
    raise RuntimeError("current wheel does not include MediaBus bindings")

sdk.service.initial(None, "mediaExample")

client = sdk.MotionHighLevelClient(as_master=False)
client.connect()

media = client.create_media_bus_client()
if not media.setup():
    print("media setup failed:", media.get_last_error())   # MediaBusError

layout = media.get_media_layout()
print("camera", layout.camera_num, "mic", layout.mic_num, "encoder", layout.video_encoder_num)

def on_enc(channel, frame):
    print("[enc] ch", channel, "size", frame.size())

media.start_encoded_video_frame(0, on_enc)   # Callback: (channel, EncodedVideoFrame)
# media.start_raw_video_frame(0, on_video)   # Callback: (channel, VideoFrame)
# media.start_raw_audio_frame(0, on_audio)   # Callback: (channel, AudioFrame)

# ... run ...

media.stop_encoded_video_frame(0)
media.shutdown()
client.disconnect()
sdk.service.shutdown()
```

`MediaBusClient` supports the `with` context manager, which calls `shutdown()` on exit. The complete example is `uniubi_robot_sdk_py/examples/example_media_frames.py` and runs only in local `aarch64` deployment.

The native Python binding uses `UNIUBI_SDK_ENABLE_MEDIA` to control media-frame bindings. The defaults are `aarch64=ON` and `x86_64/i386=OFF`. When `sdk.MEDIA_ENABLED == False`, `robot_motion_sdk.media_frame` cannot be imported, `MediaBusError` is `None`, and media frame types are unavailable.

## 3. Frame Data Access

The callback receives a `VideoFrame`, `AudioFrame`, or `EncodedVideoFrame` wrapper. Its snake_case accessors correspond directly to the C++ API:

**`VideoFrame` (raw video frame)**

| Access | Meaning |
|---|---|
| `frame.size()` / `frame.get_fd()` | Number of bytes / frame memory fd |
| `frame.data()` | First plane byte (**copy**, can be retained across callbacks) |
| `frame.frame_info` | `VideoFrameInfo`: `.width` / `.height` / `.pixel_format` (`sdk.MediaPixelFormat`) / `.sequence` / `.timestamp` / `.stride` (length 3) / `.stride_v` / `.rotate` |
| `frame.plane_view(plane)` | Zero-copy view of the specified plane: `.rows` / `.row_bytes` / `.row_view(row)` (can be `memoryview(...)`) |

> A raw image may use non-contiguous planes, especially on NVIDIA platforms. Interpret `pixel_format` and `stride`, then read each plane row by row through `plane_view().row_view()`. **Do not assume that `data()` contains one contiguous image.** See `example_media_frames.py` and `_dump_video_frame_payload` for plane-aware output.

**`AudioFrame` (raw audio frame)**

| Access | Meaning |
|---|---|
| `frame.size()` / `frame.data()` | Number of bytes / PCM bytes (copy) |
| `frame.frame_info` | `AudioFrameInfo`: `.sample_rate`/`.sample_format` (bit width)/`.channel_count`/`.sequence`/`.timestamp` |

**`EncodedVideoFrame` (encoded video frame)**

| Access | Meaning |
|---|---|
| `frame.size()` / `frame.data()` | Encoded stream size / encoded stream bytes (copy) |
| `frame.frame_type` / `frame.sequence` / `frame.pts` / `frame.utc` | Frame type (`sdk.FrameType`) / sequence number / presentation timestamp / UTC |
| `frame.video_info` | `EncodedVideoFrameInfo` (**may be `None`**): `.encode` (`sdk.VideoEncode`)/`.width`/`.height`/`.fps_num`/`.fps_den` |
| `frame.frame_info` | `EncodedFrameInfo` (possibly `None`): `.change` (whether the stream parameters are changed), etc. |

> **Copy versus zero-copy:** `frame.data()` returns a `bytes` copy that may be retained after the callback. `frame.plane_view()` / `frame.view()` returns a zero-copy buffer view that is **valid only during the callback** because the underlying buffer is recycled afterward. Copy the pixels within the callback if they must be retained.

---

## 4. Important Considerations

- **Frame pointer lifetime is limited to the callback:** zero-copy buffers are recycled after the callback returns. Copy data within the callback if it must be retained.
- **Callbacks run on the SDK media thread:** do not block or perform expensive work in a callback. Hand off time-consuming processing to an application queue or worker thread.
- **Read raw video by plane:** as described in §4.1, do not assume that `data()` contains one contiguous image.
- **Call `shutdown()` before exit:** otherwise subscription threads may remain active and deadlock with garbage collection or destruction. Use `with` or `try/finally` for explicit cleanup.
