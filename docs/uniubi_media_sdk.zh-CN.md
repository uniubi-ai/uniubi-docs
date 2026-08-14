# Uniubi Robot Motion SDK 媒体总线接口手册

[English](uniubi_media_sdk.md) | **简体中文**

媒体总线（`IMediaBusClient`）提供机器人摄像头 / 麦克风的**帧级订阅**，统一三类流：

- **视频原始帧**（`VideoFrame`）—— 摄像头解码后的 YUV / RGB 图像
- **音频原始帧**（`AudioFrame`）—— 麦克风 PCM 数据
- **视频编码帧**（`EncodedVideoFrame`）—— H264 / H265 / MJPEG 等编码码流

媒体总线与控制权无关：任何已 `connect` 的客户端（高级或低级）`setup` 后即可订阅，无需 `startControl`。

> ⚠️ **仅 `aarch64` 板内本地部署支持**：媒体帧订阅只在 SDK 与机器人同机（板内）且目标平台为 `aarch64` 时可用；**多设备 / 远端模式不提供帧订阅**。`x86_64` / `i386` 平台不要调用 `createMediaBusClient()` / `setup()` / `start*Frame()`。Python wheel 在 `x86_64` / `i386` 默认 `sdk.MEDIA_ENABLED == False`，`create_media_bus_client()` 会直接抛出 `RuntimeError("MediaBus is not available in this SDK build")`。

相关文档：
- **高级接口手册**：[`uniubi_high_level_sdk.md`](uniubi_high_level_sdk.zh-CN.md)
- **低级接口手册**：[`uniubi_low_level_sdk.md`](uniubi_low_level_sdk.zh-CN.md)
- **构建说明**：[`BUILD.md`](BUILD.zh-CN.md)

---

## 1. 获取客户端

`IMediaBusClient` 不单独创建，由已连接的高级 / 低级客户端派生：

```cpp
#include "uniubi/robot_sdk/MediaBusClient.h"
#include "uniubi/robot_sdk/MotionHighLevelClient.h"

auto client = uniubi::RobotSdk::IMotionHighLevelClient::create(/*asMaster=*/false);
auto media  = client->createMediaBusClient();   // 也可由 IMotionLowLevelClient::create() 派生
```

同一客户端多次调用 `createMediaBusClient()` 返回同一实例。客户端销毁时媒体总线随之失效。

---

## 2. 接口一览

| 接口 | 说明 |
|---|---|
| `bool setup()` | 启动媒体总线；订阅 / 查询前必须先调用，失败用 `getLastError()` 取因 |
| `void shutdown()` | 关闭媒体总线，自动停掉所有订阅 |
| `bool getMediaLayout(MediaLayout& layout)` | 查询音视频能力（mic / camera / 编码器数量） |
| `bool startRawVideoFrame(int32_t channel, RawVideoFrameCallback cb)` | 订阅视频原始帧 |
| `bool startRawAudioFrame(int32_t channel, RawAudioFrameCallback cb)` | 订阅音频原始帧 |
| `bool startEncodedVideoFrame(int32_t channel, EncodedVideoFrameCallback cb)` | 订阅视频编码帧 |
| `void stopRawVideoFrame(int32_t channel)` | 停止订阅视频原始帧 |
| `void stopRawAudioFrame(int32_t channel)` | 停止订阅音频原始帧 |
| `void stopEncodedVideoFrame(int32_t channel)` | 停止订阅视频编码帧 |
| `int32_t getLastError() const` | 取最后一次失败原因（`MediaBusError`） |

回调签名：

```cpp
using RawVideoFrameCallback     = std::function<void(int32_t channel, const VideoFrame& frame)>;
using RawAudioFrameCallback     = std::function<void(int32_t channel, const AudioFrame& frame)>;
using EncodedVideoFrameCallback = std::function<void(int32_t channel, const EncodedVideoFrame& frame)>;
```

---

## 3. 通道与能力

`channel` 取值范围由 `getMediaLayout` 返回的 `MediaLayout` 决定，越界返回 `kInvalidChannel`：

| 流类型 | 合法 channel 范围 |
|---|---|
| 视频原始帧 | `[0, cameraNum)` |
| 音频原始帧 | `[0, micNum)` |
| 视频编码帧 | `[0, videoEncoderNum)` |

```cpp
struct MediaLayout {
    uint32_t micNum;          // 麦克风数量
    uint32_t cameraNum;       // 摄像头数量
    uint32_t videoEncoderNum; // 视频编码通道数
};
```

---

## 4. 帧数据结构

帧对象在回调内有效，**不要跨回调持有指针**（零拷贝，底层缓冲随回调返回回收）。

### 4.1 `VideoFrame`（视频原始帧）

| 访问器 | 含义 |
|---|---|
| `size()` | 字节数 |
| `data()` | 首平面虚拟地址 |
| `getFd()` | 帧内存 fd（零拷贝传递用） |
| `getFrameInfo()` | `VideoFrameInfo`：`width` / `height` / `pixelFormat` / `stride[3]` / `virAddr[3]` / `timestamp` / `sequence` |

> 注意：原始图像可能分平面（plane）且非连续（NVIDIA 平台尤甚）。务必按 `pixelFormat` + `stride[i]` + `virAddr[i]` 逐平面、逐行读取，**不要把 `data()` 当成连续整图**。具体拆平面写法见 `examples/example_media_frames.cpp` 的 `dumpVideoFramePayload`。

`pixelFormat` 取值（`MediaPixelFormat` / Python `sdk.MediaPixelFormat`，枚举量前缀 `mediaPixelFormat`，完整定义见 `Media/MediaBuffer.h`）：

| 类别 | 枚举量 |
|---|---|
| 半平面 YUV | `NV12` / `NV21` / `NV16` / `NV61` |
| 平面 YUV | `YUV420P` / `YUV422P` / `YUV444P` / `YUV420M` / `YUV422M` / `YUV422RM` / `YUV444M` / `YUV400`（灰度）|
| 打包 YUV | `YUYV422` / `UYVY422` |
| 打包 RGB | `RGB888` / `BGR888` / `RGBA8888` / `BGRA8888` / `ARGB8888` / `ABGR8888` / `ARGB1555` / `ABGR1555` / `RGB565` |
| 平面 RGB | `RGB888Planar` / `BGR888Planar` |
| 单通道 16bit | `S16C1`（有符号）/ `U16C1`（无符号）|

> 另有 `mediaPixelFormatUnknown`（未知 / 未设置）。每种格式的平面数 / 行跨度规则不同，拆平面写法见 §8.1 与示例。

### 4.2 `AudioFrame`（音频原始帧）

| 访问器 | 含义 |
|---|---|
| `size()` | 字节数 |
| `data()` | PCM 数据地址 |
| `getFd()` | 帧内存 fd |
| `getFrameInfo()` | `AudioFrameInfo`：`sampleRate` / `sampleFormat`（位宽） / `channelCount` / `dataType` / `timestamp` / `sequence` |

### 4.3 `EncodedVideoFrame`（视频编码帧）

| 访问器 | 含义 |
|---|---|
| `size()` | 码流字节数 |
| `getBuffer()` | 码流数据地址 |
| `getFrameType()` | 帧类型（I / P / B 等） |
| `getSequence()` | 序号 |
| `getPts()` | 显示时间戳 |
| `getUtc()` | UTC 时间戳 |
| `getExtraData()` | 转 `Uface::Stream::FrameInfo*`，`detail.video`：`encode`（H264/H265/...）、`width` / `height` / `fpsNum` / `fpsDen` |

---

## 5. 错误码

```cpp
typedef enum {
    kNone = 0,
    kNotSetup,            // 未启动（未 setup 即调用订阅 / 查询接口）
    kConfigLoadFailed,    // 加载媒体配置失败
    kConfigInvalid,       // 媒体配置缺少 streamDefine 等必填项
    kMediaInitFailed,     // 初始化媒体流服务失败
    kMediaStartFailed,    // 启动媒体流服务失败
    kInvalidChannel,      // 通道号非法（< 0 或 >= 对应硬件数量）
    kInvalidCallback,     // 帧回调为空
    kSourceUnavailable,   // 编码源不可用（创建失败 / 无视频轨）
    kSourceStartFailed,   // 编码源启动失败
} MediaBusError;
```

`setup()` / `start*` / `getMediaLayout()` 返回 `false` 时调 `getLastError()` 取因。

---

## 6. 调用顺序

以下流程仅适用于 `aarch64` 板内本地部署。

```
connect 客户端
  └─ createMediaBusClient()
       └─ setup()                              // 失败 → getLastError()
            ├─ getMediaLayout(layout)          // 拿通道数量
            ├─ startRawVideoFrame(ch, cb)      // 按需订阅
            ├─ startRawAudioFrame(ch, cb)
            ├─ startEncodedVideoFrame(ch, cb)
            │     ... 回调持续到 stop / shutdown ...
            ├─ stopRawVideoFrame(ch)           // 可选，单路停
            └─ shutdown()                      // 停掉所有订阅
```

---

## 7. C++ 示例

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

// ... 运行 ...

media->stopEncodedVideoFrame(0);
media->shutdown();
client->disconnect();
service->shutdown();
```

完整示例（含原始视频按平面落盘、音频 PCM、编码码流落盘）：`examples/example_media_frames.cpp`，仅 `aarch64` 板内本地部署构建和运行。

---

## 8. Python 用法

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

media.start_encoded_video_frame(0, on_enc)   # 回调 (channel, EncodedVideoFrame)
# media.start_raw_video_frame(0, on_video)   # 回调 (channel, VideoFrame)
# media.start_raw_audio_frame(0, on_audio)   # 回调 (channel, AudioFrame)

# ... 运行 ...

media.stop_encoded_video_frame(0)
media.shutdown()
client.disconnect()
sdk.service.shutdown()
```

`MediaBusClient` 支持 `with` 上下文（退出自动 `shutdown`）。完整示例：`uniubi_robot_sdk_py/examples/example_media_frames.py`，仅 `aarch64` 板内本地部署运行。

Python native binding 使用 `UNIUBI_SDK_ENABLE_MEDIA` 控制媒体帧绑定。默认值为 `aarch64=ON`、`x86_64/i386=OFF`。`sdk.MEDIA_ENABLED == False` 时，`robot_motion_sdk.media_frame` 不可导入，`MediaBusError` 为 `None`，不会提供媒体帧类型。

### 8.1 Python 帧访问

回调里拿到的 `frame` 是 `VideoFrame` / `AudioFrame` / `EncodedVideoFrame` 包装对象，访问器与 C++ 一一对应（snake_case）：

**`VideoFrame`（视频原始帧）**

| 访问 | 含义 |
|---|---|
| `frame.size()` / `frame.get_fd()` | 字节数 / 帧内存 fd |
| `frame.data()` | 首平面字节（**拷贝**，可跨回调留存） |
| `frame.frame_info` | `VideoFrameInfo`：`.width` / `.height` / `.pixel_format`（`sdk.MediaPixelFormat`）/ `.sequence` / `.timestamp` / `.stride`（长度 3） / `.stride_v` / `.rotate` |
| `frame.plane_view(plane)` | 指定平面的零拷贝视图：`.rows` / `.row_bytes` / `.row_view(row)`（可 `memoryview(...)`）|

> 原始图像可能分平面且非连续（NVIDIA 平台尤甚）。务必按 `pixel_format` + `stride` + `plane_view().row_view()` 逐平面逐行读，**不要把 `data()` 当连续整图**。逐平面落盘写法见 `example_media_frames.py` 的 `_dump_video_frame_payload`。

**`AudioFrame`（音频原始帧）**

| 访问 | 含义 |
|---|---|
| `frame.size()` / `frame.data()` | 字节数 / PCM 字节（拷贝） |
| `frame.frame_info` | `AudioFrameInfo`：`.sample_rate` / `.sample_format`（位宽）/ `.channel_count` / `.sequence` / `.timestamp` |

**`EncodedVideoFrame`（视频编码帧）**

| 访问 | 含义 |
|---|---|
| `frame.size()` / `frame.data()` | 码流字节数 / 码流字节（拷贝） |
| `frame.frame_type` / `frame.sequence` / `frame.pts` / `frame.utc` | 帧类型（`sdk.FrameType`）/ 序号 / 显示时间戳 / UTC |
| `frame.video_info` | `EncodedVideoFrameInfo`（**可能为 `None`**）：`.encode`（`sdk.VideoEncode`）/ `.width` / `.height` / `.fps_num` / `.fps_den` |
| `frame.frame_info` | `EncodedFrameInfo`（可能为 `None`）：`.change`（流参数是否变更）等 |

> **拷贝 vs 零拷贝**：`frame.data()` 返回的是 `bytes` 拷贝，可跨回调留存；`frame.plane_view()` / `frame.view()` 是零拷贝 buffer 视图，**仅回调内有效**（底层缓冲回调返回即回收）。需要留存像素请在回调里 `memcpy` 出来。

---

## 9. 注意事项

- **帧指针生命周期仅限回调内**：零拷贝设计，回调返回后底层缓冲即回收；需要留存请在回调里 `memcpy` 出来。
- **回调在 SDK 媒体线程触发**：回调里不要做重活 / 阻塞，避免拖累后续帧；耗时处理转交自己的队列 / 线程。
- **原始视频按平面读**：见 §4.1，勿把 `data()` 当连续整图。
- **退出务必 `shutdown()`**：否则订阅线程不退，且与 GC / 析构争用可能死锁（Python 见各手册 §6.2，建议 `with` 或 try/finally）。
