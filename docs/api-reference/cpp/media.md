# Uniubi Robot MediaBus C++ API Reference

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/media.zh-CN.md)

[API Reference](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/README.md) · [Python API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/media.md)

The media bus (`IMediaBusClient`) provides **frame-level subscriptions** to the robot's cameras and microphones through three stream types:

- **Raw video frames** (`VideoFrame`) — camera YUV / RGB images
- **Raw audio frames** (`AudioFrame`) — microphone PCM data
- **Encoded video frames** (`EncodedVideoFrame`) — H264 / H265 / MJPEG and other encoded streams

Media subscriptions are independent of motion control ownership. A connected High-level or Low-level client can subscribe after `setup()` without calling `startControl()`.

> MediaBus is enabled by default on x86_64, i386, aarch64, and aarch64_host. Local Orin deployment supports video, audio, and layout queries; remote deployment supports PCM capture and RawBack playback via `media.setup(host)`. Remote video subscriptions and layout queries return `kNotSupported`. SDK headers, runtime libraries, Python extensions, and device software must use matching versions.

Related documents:
- **High-level API reference:** [High-level C++ API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/high-level.md)
- **Low-level API reference:** [Low-level C++ API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/low-level.md)
- **Build instructions:** [Build guide](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/BUILD.md)

---

## 1. Get the client

Create `IMediaBusClient` from a connected High-level or Low-level client; it cannot be created independently:

```cpp
#include "uniubi/robot_sdk/MediaBusClient.h"
#include "uniubi/robot_sdk/MotionHighLevelClient.h"

auto client = uniubi::RobotSdk::IMotionHighLevelClient::create(/*asMaster=*/false);
auto media  = client->createMediaBusClient();   // Can also be obtained from an IMotionLowLevelClient instance
```

Repeated calls to `createMediaBusClient()` on the same client return the same instance. The media bus becomes invalid when its parent client is destroyed.

---

## 2. Interface list

| Interface | Description |
|---|---|
| `bool setup(std::string host = {})` | Start the media bus. Call this before subscriptions or queries; use `getLastError()` if it fails |
| `IAudioRawBackStream::Ptr createAudioRawBack()` | Get local or remote playback after setting up the media client |
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

## 3. Local channels and capabilities

In local mode, the `MediaLayout` returned by `getMediaLayout()` determines the valid `channel` range. An out-of-range channel produces `kInvalidChannel`:

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
    kInvalidParam,        // Invalid parameter
    kCaptureFailed,       // Capture registration failed
    kConnectFailed,       // Remote connection startup failed
    kNotSupported,        // Unsupported in this deployment mode
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
#include "uniubi/robot_sdk/MediaBusClient.h"
#include "uniubi/robot_sdk/MotionHighLevelClient.h"
#include "uniubi/robot_sdk/MotionSdkService.h"

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

The complete example writes raw video plane by plane, audio PCM, and encoded streams to disk: `examples/example_media_frames.cpp`. It builds on all supported architectures; this video example runs in local Orin deployment.

---

## 8. Important Considerations

- **Frame pointer lifetime is limited to the callback:** zero-copy buffers are recycled after the callback returns. Copy data within the callback if it must be retained.
- **Callbacks run on the SDK media thread:** do not block or perform expensive work in a callback. Hand off time-consuming processing to an application queue or worker thread.
- **Read raw video by plane:** as described in §4.1, do not assume that `data()` contains one contiguous image.
- **Call `shutdown()` before exit:** otherwise subscription threads may remain active and deadlock with garbage collection or destruction. Stop subscriptions explicitly and call `shutdown()` before exit.

## PCM audio / RawBack

Call `media.setup(host)` (omit host locally), then `createAudioRawBack()` to obtain playback. Call `setup()`, wait for `ready()`, then use `setVolume()` and `write(frame)`. Call playback `shutdown()` before shutting down the media client. `reset()` clears the playback queue. PCM must be 16 kHz, s16le, mono.

Successful setup indicates initialization or connection startup; verify capture by counting actual frames and playback at the device output. AudioFrame objects may be retained after capture callbacks. Stop subscriptions and shut down on the application control thread.

[PCM audio guide](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/stream-pcm-audio.md).
