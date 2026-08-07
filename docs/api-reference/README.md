# API Reference

本页面向已经确定控制模式并完成最小验证的开发者。先看对应 How-to，再把本页作为接口查询入口。

## SDK API

| 领域 | 文档 | 适用场景 |
|---|---|---|
| High-level 控制 | [High-level SDK API](../uniubi_high_level_sdk.md) | 调用机器人内置动作能力 |
| Low-level 控制 | [Low-level SDK API](../uniubi_low_level_sdk.md) | 自己运行策略并控制关节位置或扭矩 |
| 媒体总线 | [Media SDK API](../uniubi_media_sdk.md) | 订阅摄像头、麦克风和编码帧 |

## 使用建议

- 还没有确定 High-level / Low-level：先回到 [Core Concepts](../core-concepts/README.md)。
- 还没有完成构建、导入和只读验证：先阅读 [How-to](../how-to/README.md)。
- 需要原始 DDS / RPC、QoS 或协议字段：进入 [Advanced](../advanced/README.md)，不要从本页直接开始。
