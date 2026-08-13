# Uniubi Robot Motion SDK Media Bus API Reference

**English** | [简体中文](uniubi_media_sdk.zh-CN.md)

The media bus (`IMediaBusClient`) provides **frame-level subscriptions** to the robot's cameras and microphones through three stream types:

- **Raw video frames** (`VideoFrame`) — camera YUV / RGB images
- **Raw audio frames** (`AudioFrame`) — microphone PCM data
- **Encoded video frames** (`EncodedVideoFrame`) — H264 / H265 / MJPEG and other encoded streams

Media subscriptions are independent of motion control ownership. A connected High-level or Low-level client can subscribe after `setup()` without calling `startControl()`.

> ⚠️ **Supported only for local deployment on an `aarch64` robot compute board:** media frame subscriptions require the SDK and robot runtime to run on the same machine. **Multi-device and remote modes do not provide frame subscriptions.** Do not call `createMediaBusClient()` / `setup()` / `start*Frame()` on `x86_64` or `i386`. Python wheels for those platforms set `sdk.MEDIA_ENABLED == False` by default, and `create_media_bus_client()` raises `RuntimeError("MediaBus is not available in this SDK build")`.

Related documents:
- **High-level API reference:** [`uniubi_high_level_sdk.md`](uniubi_high_level_sdk.md)
- **Low-level API reference:** [`uniubi_low_level_sdk.md`](uniubi_low_level_sdk.md)
- **Build instructions:** [`BUILD.md`](BUILD.md)

---

## 1. Get the client

Create `IMediaBusClient` from a connected High-level or Low-level client; it cannot be created independently:

```cpp
#include "MediaBusClient.h"
#include "MotionHighLevelClient.h"

auto client = uniubi::RobotSdk::IMotionHighLevelClient::create(/*asMaster=*/false);
auto media  = client->createMediaBusClient();   // Can also be obtained from an IMotionLowLevelClient instance
```

Repeated calls to `createMediaBusClient()` on the same client return the same instance. The media bus becomes invalid when its parent client is destroyed.

---

## 2. Interface list

| Interface | Description |
|---|---|
| `bool setup()` | Start the media bus. Call this before subscriptions or queries; use `getLastError()` if it fails |
| `void shutdown()` | Close the media bus and automatically stop all subscriptions |
| `bool getMediaLayout(MediaLayout& layout)` | Query audio and video capabilities (microphone, camera, and encoder counts) |
| `bool startRawVideoFrame(int32_t channel, RawVideoFrameCallback cb)` | Subscribe to raw video frames |
| `bool startRawAudioFrame(int32_t channel, RawAudioFrameCallback cb)` | Subscribe to raw audio frames |
| `bool startEncodedVideoFrame(int32_t channel, EncodedVideoFrameCallback cb)` | Subscribe to encoded video frames |
| `void stopRawVideoFrame(int32_t channel)` | Stop a raw video subscription |
| `void stopRawAudioFrame(int32_t channel)` | Stop a raw audio subscription |
| `void stopEncodedVideoFrame(int32_t channel)` | Stop an encoded video subscription |
| `int32_t getLastError() const` | Get the last failure reason (`MediaBusError`) |

Callback signature:

```cpp
using RawVideoFrameCallback     = std::function<void(int32_t channel, const VideoFrame& frame)>;
using RawAudioFrameCallback     = std::function<void(int32_t channel, const AudioFrame& frame)>;
using EncodedVideoFrameCallback = std::function<void(int32_t channel, const EncodedVideoFrame& frame)>;
```

---

## 3. Channels and capabilities

The `MediaLayout` returned by `getMediaLayout()` determines the valid `channel` range. An out-of-range channel produces `kInvalidChannel`:

| Stream type | Valid channel range |
|---|---|
| Raw video frame | `[0, cameraNum)` |
| Raw audio frame | `[0, micNum)` |
| Encoded video frame | `[0, videoEncoderNum)` |

```cpp
struct MediaLayout {
    uint32_t micNum;          // Number of microphones
    uint32_t cameraNum;       // Number of cameras
    uint32_t videoEncoderNum; // Number of video encoder channels
};
```

---

## 4. Frame data structures

Frame objects are valid only during the callback. **Do not retain pointers after the callback returns:** zero-copy buffers are then recycled.

### 4.1 `VideoFrame` (raw video frame)

| Accessor | Meaning |
|---|---|
| `size()` | Number of bytes |
| `data()` | First plane virtual address |
| `getFd()` | Frame-memory file descriptor (for zero-copy transfer) |
| `getFrameInfo()` | `VideoFrameInfo`：`width` / `height` / `pixelFormat` / `stride[3]` / `virAddr[3]` / `timestamp` / `sequence` |

> A raw image may use multiple non-contiguous planes, especially on NVIDIA platforms. Interpret `pixelFormat`, `stride[i]`, and `virAddr[i]`, and read each plane row by row. **Do not assume that `data()` points to one contiguous image.** See `dumpVideoFramePayload` in `examples/example_media_frames.cpp` for a plane-aware implementation.

`pixelFormat` value (`MediaPixelFormat` / Python `sdk.MediaPixelFormat`, enumeration prefix `mediaPixelFormat`, see `Media/MediaBuffer.h` for complete definition):

| Category | Enumeration |
|---|---|
| Semi-planar YUV | `NV12` / `NV21` / `NV16` / `NV61` |
| Planar YUV | `YUV420P` / `YUV422P` / `YUV444P` / `YUV420M` / `YUV422M` / `YUV422RM` / `YUV444M` / `YUV400` (grayscale) |
| Packed YUV | `YUYV422` / `UYVY422` |
| Packed RGB | `RGB888` / `BGR888` / `RGBA8888` / `BGRA8888` / `ARGB8888` / `ABGR8888` / `ARGB1555` / `ABGR1555` / `RGB565` |
| Planar RGB | `RGB888Planar` / `BGR888Planar` |
| Single-channel 16-bit | `S16C1` (signed) / `U16C1` (unsigned) |

> `mediaPixelFormatUnknown` means unknown or unset. Plane counts and row spans vary by format. See §8.1 and the examples for plane-aware access.

### 4.2 `AudioFrame` (raw audio frame)

| Accessor | Meaning |
|---|---|
| `size()` | Number of bytes |
| `data()` | PCM data address |
| `getFd()` | Frame memory fd |
| `getFrameInfo()` | `AudioFrameInfo`: `sampleRate` / `sampleFormat` (bit width) / `channelCount` / `dataType` / `timestamp` / `sequence` |

### 4.3 `EncodedVideoFrame` (encoded video frame)

| Accessor | Meaning |
|---|---|
| `size()` | Encoded stream size in bytes |
| `getBuffer()` | Encoded stream data address |
| `getFrameType()` | Frame type (I/P/B, etc.) |
| `getSequence()` | Sequence number |
| `getPts()` | Presentation timestamp |
| `getUtc()` | UTC timestamp |
| `getExtraData()` | Cast to `Uface::Stream::FrameInfo*`; `detail.video` provides `encode` (H264/H265/...), `width` / `height` / `fpsNum` / `fpsDen` |

---

## 5. Error codes

```cpp
typedef enum {
    kNone = 0,
    kNotSetup,            // Not started (subscription/query called before setup)
    kConfigLoadFailed,    // Failed to load the media configuration
    kConfigInvalid,       // Required media configuration, such as streamDefine, is missing
    kMediaInitFailed,     // Failed to initialize the media-stream service
    kMediaStartFailed,    // Failed to start the media-stream service
    kInvalidChannel,      // Invalid channel (< 0 or >= the corresponding hardware count)
    kInvalidCallback,     // Frame callback is empty
    kSourceUnavailable,   // Encoded source unavailable (creation failed or no video track)
    kSourceStartFailed,   // Failed to start the encoded source
} MediaBusError;
```

If `setup()`, a `start*` method, or `getMediaLayout()` returns `false`, call `getLastError()` for the cause.

---

## 6. Calling sequence

The following sequence applies only to local deployment on an `aarch64` robot compute board.

```
connect client
  └─ createMediaBusClient()
       └─ setup()                              // On failure → getLastError()
            ├─ getMediaLayout(layout)          // Read channel counts
            ├─ startRawVideoFrame(ch, cb)      // Subscribe as needed
            ├─ startRawAudioFrame(ch, cb)
            ├─ startEncodedVideoFrame(ch, cb)
            │     ... callbacks continue until stop / shutdown ...
            ├─ stopRawVideoFrame(ch)           // Optional: stop one channel
            └─ shutdown()                      // Stop all subscriptions
```

---

## 7. C++ example

```cpp
#include "MediaBusClient.h"
#include "MotionHighLevelClient.h"
#include "MotionSdkService.h"

using namespace uniubi::RobotSdk;

auto* service = IMotionSdkService::instance();
service->initialService(nullptr, "mediaExample");

auto client = IMotionHighLevelClient::create(/*asMaster=*/false);
auto media  = client->createMediaBusClient();
if (!media->setup()) {
    printf("media setup failed: %d\n", media->getLastError());
    return;
}

MediaLayout layout = {};
media->getMediaLayout(layout);
printf("camera=%u mic=%u encoder=%u\n", layout.cameraNum, layout.micNum, layout.videoEncoderNum);

media->startEncodedVideoFrame(0, [](int32_t ch, const EncodedVideoFrame& frame) {
    printf("[enc] ch=%d size=%d type=%d\n", ch, frame.size(), frame.getFrameType());
});

// ... run ...

media->stopEncodedVideoFrame(0);
media->shutdown();
client->disconnect();
service->shutdown();
```

The complete example writes raw video plane by plane, audio PCM, and encoded streams to disk: `examples/example_media_frames.cpp`. It is built and run only for local `aarch64` deployment.

---

## 8. Python usage

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

### 8.1 Python frame access

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

## 9. Important considerations

- **Frame pointer lifetime is limited to the callback:** zero-copy buffers are recycled after the callback returns. Copy data within the callback if it must be retained.
- **Callbacks run on the SDK media thread:** do not block or perform expensive work in a callback. Hand off time-consuming processing to an application queue or worker thread.
- **Read raw video by plane:** as described in §4.1, do not assume that `data()` contains one contiguous image.
- **Call `shutdown()` before exit:** otherwise subscription threads may remain active and deadlock with garbage collection or destruction. For Python, use a `with` block or `try/finally` as described in §6.2 of the relevant SDK manual.
