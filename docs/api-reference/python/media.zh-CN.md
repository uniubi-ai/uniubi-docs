# 宇泛机器人 MediaBus Python API 参考

[English](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/media.md) | **简体中文**

[返回 API 参考](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/README.zh-CN.md) · [查看 C++ API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/media.zh-CN.md)

Python 模块：`robot_motion_sdk`

> x86_64、i386、aarch64、aarch64_host 默认开启 MediaBus。Orin 本机模式支持视频、音频和布局查询；远端模式通过 `media.setup(host)` 支持 PCM 采集和 RawBack 播放。远端视频订阅和布局查询返回 `kNotSupported`。SDK 头文件、运行库、Python 扩展与设备软件必须版本匹配。

## 一、API 一览

检查 binding 是否启用：`sdk.MEDIA_ENABLED`。

**MediaBus client（`sdk.MediaBusClient` —— 对应 `IMediaBusClient`，由 `create_media_bus_client()` 工厂分配）：**

| 功能 / native 名称 | Python API |
|---|---|
| `setup / shutdown` | `setup(host="")` / `shutdown()` |
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

## 二、使用示例

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

Python native binding 使用 `UNIUBI_SDK_ENABLE_MEDIA` 控制媒体帧绑定。所有支持架构默认 `ON`。`sdk.MEDIA_ENABLED == False` 时，`robot_motion_sdk.media_frame` 不可导入，`MediaBusError` 为 `None`，不会提供媒体帧类型。

## 三、帧数据访问

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

## 四、注意事项

- **帧指针生命周期仅限回调内**：零拷贝设计，回调返回后底层缓冲即回收；需要留存请在回调里 `memcpy` 出来。
- **回调在 SDK 媒体线程触发**：回调里不要做重活 / 阻塞，避免拖累后续帧；耗时处理转交自己的队列 / 线程。
- **原始视频按平面读**：见“帧数据访问”，勿把 `data()` 当连续整图。
- **退出务必 `shutdown()`**：否则订阅线程不退，且与 GC / 析构争用可能死锁（使用 `with` 或 `try/finally` 显式清理）。


## PCM audio / RawBack

先调用 `media.setup(host)`（本机省略 host），再调用 `create_audio_raw_back()` 获取播放对象，依次调用 `setup()`、等待 `ready()`、`set_volume()`、`write(frame)`。结束时调用播放对象 `shutdown()`，再关闭媒体 client。`reset()` 清空播放队列。仅支持 16 kHz、s16le、单声道 PCM。

`setup()` 成功只表示初始化或连接启动；通过实际回调统计验证采集，通过设备输出验证播放。采集回调可以保留 AudioFrame；停止订阅及关闭请在业务控制线程调用。

[PCM audio guide](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/stream-pcm-audio.zh-CN.md).
