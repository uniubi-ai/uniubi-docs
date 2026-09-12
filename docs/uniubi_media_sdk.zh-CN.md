# MediaBus SDK API 语言入口

普通 ARM64 外部主机请选择 `aarch64_host`：构建传入 `-DPLATFORM=aarch64_host`（Python 为 `-Ccmake.define.PLATFORM=aarch64_host`），运行时使用 `lib/aarch64_host/`。其媒体能力与 x86 远端模式相同，仅支持远程音频；Orin 本地视频/布局示例仍使用 `aarch64`。

[English](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/uniubi_media_sdk.md) | **简体中文**

MediaBus API 参考已按语言拆分：

- [Python API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/media.zh-CN.md)：面向使用 `robot_motion_sdk` 订阅媒体帧的开发者。
- [C++ API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/media.zh-CN.md)：面向使用 `IMediaBusClient` 的 native 应用。

[返回 API 参考](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/README.zh-CN.md)

## NV21 与四路 PCM 采集示例

两个 SDK 均提供 `config/sdk_config.json` 参考模板和 `--capture-all` 模式：每路摄像头 5 张 NV21，四路 16000 Hz / 16-bit / 单声道 PCM，默认每路 20 秒（640000 字节）。配置仍需核对后部署到板端 `/etc/robot/sdk_config.json`；项目文件不会自动生效。

- [C++](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/docs/media-capture.zh-CN.md)
- [Python](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/docs/media-capture.zh-CN.md)
