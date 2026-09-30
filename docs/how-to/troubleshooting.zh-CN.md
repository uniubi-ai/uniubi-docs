# 按症状排查

[English](troubleshooting.md) | **简体中文**

从实际失败的阶段开始检查。先保存错误信息与[版本记录](version-selection.zh-CN.md)，再按下表进入对应说明。

| 症状 | 首先确认 | 处理入口 |
|---|---|---|
| 动态库找不到、GLIBC/GLIBCXX 不匹配 | 运行位置对应的库目录、依赖与库来源 | [构建故障排查](../BUILD.zh-CN.md#troubleshooting--faq) |
| Python binding 导入失败 | Python 版本、ELF 架构、SDK 路径，区分 Orin 与 ARM64 host | [构建故障排查](../BUILD.zh-CN.md#troubleshooting--faq) |
| 发现不到机器人、RPC 超时 | 当前设备 IP、实际网卡、SN 与部署位置；直连时检查 DontRoute 条件 | [机器人网络接入](../core-concepts/device-network.zh-CN.md)、[连接外设](connect-peripherals.zh-CN.md) |
| 连接成功但没有观测 | 是否开启对应观测、回调注册顺序、数据是否持续更新；区分客户端支持范围 | [传感器与运动观测](read-sensor-data.zh-CN.md) |
| High-level 无法取得控制权 | 遥控器连接状态、客户端状态和返回错误 | [High-level 流程](high-level-control.zh-CN.md) |
| Low-level 结束后遥控器不能恢复内置动作 | 原控制进程是否结束、是否完成恢复内置控制模式 | [Low-level 结束流程](low-level-control.zh-CN.md) |
| 远端媒体视频不可用 | 当前使用 RTSP 还是 MediaBus；远端 MediaBus 不支持视频订阅和布局查询 | [媒体接入](use-media-and-device-io.zh-CN.md) |
| Python 退出卡住 | 是否在业务控制线程按顺序停止订阅、释放客户端和 service | [High-level 退出说明](../api-reference/python/high-level.zh-CN.md#三退出死锁规避必读)、[Low-level 退出说明](../api-reference/python/low-level.zh-CN.md#三退出死锁规避必读) |

## 如何判断恢复

重新执行失败阶段的最小验证，记录返回状态和可观察结果。连接成功不代表观测正常；RPC 接受请求不代表动作已经完成。进入运动验证前，仍须满足对应控制指南的前置条件。

## 提交问题时附带什么

- 固件、各组件 commit、运行位置、OS/Python 版本及库目录；
- 最小复现命令、预期结果、实际错误和发生时间；
- 相关状态或日志，说明是否涉及真机动作。

分享前移除凭据、访问令牌和不应公开的设备/网络信息。

[返回操作指南](README.zh-CN.md)
