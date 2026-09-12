# PCM 音频采集与播放

x86_64、i386 和 aarch64 默认启用媒体接口。SDK 与设备软件必须版本匹配。

| 模式 | 采集 / 播放 | 初始化 |
|---|---|---|
| Orin 本机 | SHM 音视频采集、PCM RawBack 播放、布局查询 | `media.setup()` |
| 远端 PC | 网络 PCM 采集与 RawBack 播放 | `media.setup(host)`，host 为 DV500 地址 |

远端模式不支持视频订阅或布局查询，返回 `kNotSupported`。先建立 High-level client 连接，再创建 MediaBus client。远端音频使用设备 TCP 1000 服务；设备音频服务及对应通道必须已配置并运行。本机模式使用 `/etc/robot/sdk_config.json` 的 `streamDefine` 和 SHM，RawBack 通道为 `robotsdk.audioRawBack`。

## 运行完整示例

Python 远端播放并同时采集 source 0：

```bash
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" python3 examples/example_audio_rawback.py input.pcm \
  --host <DV500_IP> --device-id <ROBOT_SN> --interface <DDS_INTERFACE> \
  --volume 20 --capture-channel 0
```

本机模式省略 `--host` 和 `--device-id`。仅播放时省略 `--capture-channel`。C++ 对应示例为 `example_audio_rawback`，参数见 `--help`。`example_audio` 是本机采集示例；`example_media_frames` 是本机视频/布局示例。

## Python 接口顺序

以下片段假定 High-level client 已连接；完整示例还处理连接等待、错误检查、PCM 文件读取和退出清理。

```python
import time
import robot_motion_sdk as sdk

media = client.create_media_bus_client()
playback = None
try:
    if not media.setup(host):  # host="" locally
        raise RuntimeError(media.get_last_error())
    playback = media.create_audio_raw_back()
    if playback is None:
        raise RuntimeError(media.get_last_error())
    if not playback.setup():
        raise RuntimeError(playback.get_last_error())
    deadline = time.monotonic() + 5
    while not playback.ready():
        if time.monotonic() >= deadline:
            raise TimeoutError(playback.get_last_error())
        time.sleep(0.02)
    if not playback.set_volume(20):
        raise RuntimeError(playback.get_last_error())
    # Feed AudioFrame objects at the PCM sample rate; see the complete example.
finally:
    if playback is not None:
        playback.shutdown()
    media.shutdown()
```

C++ 对应 `createMediaBusClient()` → `setup(host)` → `createAudioRawBack()` → `setup()` / `ready()` / `setVolume()` / `write()` / `shutdown()`，播放类型定义见 `AudioRawBackStream.h`。

## PCM 格式与生命周期

- 固定 16 kHz、signed 16-bit little-endian、单声道；SDK 不做重采样。Python `AudioFrameInfo` 使用 `sample_rate=16000`、`sample_format=16`、`channel_count=1`。
- 示例以 1280 字节 / 40 ms 节奏发送，末尾补两个静音帧并等待尾音。成功写入不等于已由扬声器播放，协议没有 drain 确认。
- `media.start_raw_audio_frame(source, callback)` 启动采集，回调接收 `(channel, AudioFrame)`。远端 source 为设备音源索引；应按设备配置选择，不调用远端布局查询。
- `setup()` 成功只表示初始化或连接启动；播放前等待 `ready()`，采集需要实际收到帧才能确认通路正常。
- 同一 MediaBus client 重复创建 RawBack 返回同一底层流。`reset()` 清空播放队列；结束时先 `playback.shutdown()`，再停止采集、关闭 media、断开 client、关闭 SDK service。
- 在业务控制线程停止订阅和关闭，不在采集回调内执行。采集回调可保留 AudioFrame，其音频数据和元信息保持有效。

[Python 示例](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/examples/example_audio_rawback.py) · [C++ 示例](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/example_audio_rawback.cpp)
