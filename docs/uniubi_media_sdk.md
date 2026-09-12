# MediaBus SDK API Language Entry

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/uniubi_media_sdk.zh-CN.md)

The MediaBus API reference is now separated by language:

- [Python API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/media.md): for media-frame subscriptions through `robot_motion_sdk`.
- [C++ API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/media.md): for native applications using `IMediaBusClient`.

[API Reference](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/README.md)

## NV21 and four-channel PCM capture examples

Both SDK repositories provide a `config/sdk_config.json` reference template and `--capture-all`: five NV21 images per camera plus four 16000 Hz / 16-bit / mono PCM files, defaulting to 20 seconds (640000 bytes) each. Review and deploy the configuration to `/etc/robot/sdk_config.json` on the board; the repository file is not activated automatically.

- [C++](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/docs/media-capture.md)
- [Python](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/docs/media-capture.md)
