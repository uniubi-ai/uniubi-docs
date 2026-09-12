# PCM 音频采集与播放

普通 ARM64 外部主机请选择 `aarch64_host`：构建传入 `-DPLATFORM=aarch64_host`（Python 为 `-Ccmake.define.PLATFORM=aarch64_host`），运行时使用 `lib/aarch64_host/`。其媒体能力与 x86 远端模式相同，仅支持远程音频；Orin 本地视频/布局示例仍使用 `aarch64`。

x86_64、i386 和 aarch64 默认启用媒体接口。SDK 与设备软件必须版本匹配。

| 模式 | 采集 / 播放 | 初始化 |
|---|---|---|
| Orin 本机 | SHM 音视频采集、PCM RawBack 播放、布局查询 | `media.setup()` |
| 远端 PC | 网络 PCM 采集与 RawBack 播放 | `media.setup(host)`，host 为 DV500 地址 |

远端模式不支持视频订阅或布局查询，返回 `kNotSupported`。先建立 High-level client 连接，再创建 MediaBus client。远端音频需保证主机能够访问机器人，且设备音频服务及对应采集通道已启用。本机采集前需确认 `/etc/robot/sdk_config.json` 中的通道配置与设备一致，详见[本机采集配置](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/docs/media-capture.zh-CN.md)。

## 运行完整示例

Python 远端播放并同时采集 source 0：

```bash
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" python3 examples/example_audio_rawback.py input.pcm \
  --host <DV500_IP> --device-id <ROBOT_SN> --interface <DDS_INTERFACE> \
  --volume 20 --capture-channel 0
```

本机模式省略 `--host` 和 `--device-id`。仅播放时省略 `--capture-channel`。C++ 对应示例为 `example_audio_rawback`，参数见 `--help`。`example_audio` 是本机采集示例；`example_media_frames` 是本机视频/布局示例。

## 四路同时采集

使用 Python SDK 的 [example_audio_capture.py](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/examples/example_audio_capture.py)，在同一个 MediaBus client 上同时保持通道 **0、1、2、3** 的订阅，每路独立保存。示例只采集音频，不申请运动控制权，也不播放声音。设备必须已配置并启用这四个音源；通道编号不是一个音频帧中的四个声道。

先按[构建指南](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/BUILD.zh-CN.md)安装对应平台的 C++ 运行库和 Python SDK。以下命令在 Python SDK 仓库根目录执行，`UNIUBI_SDK_ROOT` 指向配套 C++ SDK 仓库。每次使用新的输出目录；示例不会覆盖已有目录。

### 大脑本地（`aarch64`）

使用大脑板的系统 Python，并确认本机音频通道配置已就绪：

```bash
export UNIUBI_SDK_ROOT=/path/to/uniubi_robot_sdk
sudo env LD_LIBRARY_PATH="$UNIUBI_SDK_ROOT/lib/aarch64:${LD_LIBRARY_PATH:-}" \
  python3 examples/example_audio_capture.py \
  --seconds 20 --output /tmp/pcm4-brain-01
```

### x86 host（`x86_64`）

将 `ROBOT_IP`、`ROBOT_SN`、`HOST_INTERFACE` 分别替换为机器人地址、设备 SN 和主机上能访问机器人的网卡名称。外部主机必须同时提供这三个参数：

```bash
export UNIUBI_SDK_ROOT=/path/to/uniubi_robot_sdk
LD_LIBRARY_PATH="$UNIUBI_SDK_ROOT/lib/x86_64:${LD_LIBRARY_PATH:-}" \
  python3 examples/example_audio_capture.py \
  --host ROBOT_IP --device-id ROBOT_SN --interface HOST_INTERFACE \
  --seconds 20 --output /tmp/pcm4-x86-01
```

### ARM64 host（`aarch64_host`）

Python SDK 安装时须指定 `-Ccmake.define.PLATFORM=aarch64_host`，运行时使用对应 host 库。参数替换规则与 x86 host 相同：

```bash
export UNIUBI_SDK_ROOT=/path/to/uniubi_robot_sdk
LD_LIBRARY_PATH="$UNIUBI_SDK_ROOT/lib/aarch64_host:${LD_LIBRARY_PATH:-}" \
  python3 examples/example_audio_capture.py \
  --host ROBOT_IP --device-id ROBOT_SN --interface HOST_INTERFACE \
  --seconds 20 --output /tmp/pcm4-arm64-host-01
```

### 输出、停止和验收

输出目录包含 `channel0.pcm`～`channel3.pcm` 和逐路统计文件 `summary.json`。

- **数据格式**：每个文件均为无文件头的 16 kHz、signed 16-bit little-endian、单声道 PCM。四路分别存储，不交织、不合并。
- **采集时长**：`--seconds` 为每路目标样本时长，取值 1～60，默认 20 秒。每路目标长度为 `seconds × 16000 × 2` 字节；20 秒应各为 **640000 字节**。回调只累计到目标长度，全部订阅建立后最多等待目标时长加 5 秒。
- **停止清理**：四路均足量后自动停止；也可按 Ctrl+C 提前结束。主线程依次停止所有已成功订阅的通道，关闭 media、断开 client、关闭 SDK，再分别保存已采集数据。启动中途失败也会清理先前已成功的订阅；提前中断或异常会在汇总中标记失败。
- **通过条件**：进程退出码为 0，`summary.json` 中 `result` 为 `PASS`，四路均有帧且各自达到目标字节数，`format_errors`、`timestamp_errors` 均为 0，`errors` 为空。初始化、订阅、清理或写盘失败均不能算通过；已有部分文件不代表完整采集成功。
- **有效性边界**：检查每路时间戳严格递增，静音 PCM 仍视为有效数据。足量文件不能证明采集期间无丢帧，也不能证明四路在同一时刻开始或严格同步；这些需另行验证。

可先检查文件长度和汇总，再按需试听各路：

```bash
wc -c /tmp/pcm4-brain-01/channel*.pcm
cat /tmp/pcm4-brain-01/summary.json
aplay -t raw -f S16_LE -r 16000 -c 1 /tmp/pcm4-brain-01/channel0.pcm
```

将路径替换为本次输出目录。以上是运行与验收方法，不代表四路采集已完成三端真机验证。

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
