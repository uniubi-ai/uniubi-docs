# 版本选择与升级

[English](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/version-selection.md) | **简体中文**

## 目标

在构建前选对固件、SDK 和目标平台，并留下可复现的版本记录。兼容范围以[首页兼容表](https://github.com/uniubi-ai/uniubi-docs/blob/main/README.zh-CN.md#固件sdk-兼容表)为入口；`main` 是持续更新的分支，不是固定的已验证发布包。

## 1. 确认设备与部署平台

从 App 基础信息记录当前固件完整版本、设备型号，以及应用运行位置。根据[构建指南](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/BUILD.zh-CN.md)选择运行库：

| 运行位置 | SDK 库目录 | 核对事项 |
|---|---|---|
| 机器人 Orin 大脑 | `lib/aarch64/` | JetPack、Python、推理依赖 |
| 外部 x86_64 Linux 主机 | `lib/x86_64/` | glibc、libstdc++、Python |
| 外部 ARM64 Linux 主机 | `lib/aarch64_host/` | 使用 host 库，不以 `uname -m` 单独判断 |

外部 ARM64 与 Orin 都可能报告 `aarch64`；Python wheel 标签也可能相同，不能据此互换运行库。

## 2. 选择并记录各仓库引用

按首页兼容表确定分支或 tag，使用对应仓库 README 的获取方式。已有工作区先检查未提交改动；在独立目录准备升级候选，保留当前可工作的环境。

分别记录实际使用的仓库，不要求不同仓库的 commit 相同，也不要仅因 tag 名称相似就假定它们已配套验证：

| 组件 | 需要记录的内容 |
|---|---|
| C++ SDK | tag/分支、完整 commit、目标库目录 |
| Python SDK（使用时） | tag/分支、完整 commit、Python 版本、binding/wheel 来源 |
| Msgs / ROS 2（使用时） | 各自 tag/分支、完整 commit、ROS 2 发行版 |
| 运行库 | 与头文件/binding 配套的交付来源、文件校验值 |

在每个相关仓库目录运行以下只读命令：

```bash
git status --short
git rev-parse HEAD
git describe --tags --always
```

预期得到工作区改动列表、完整 commit 和版本描述。空的状态输出表示没有未提交改动；有改动时应记录补丁，不能只靠 commit 复现。查不到兼容表指定的 tag 或无法确认库来源时，先确认对应交付版本，不自动换成最新 `main`。

## 3. 安装与验证

1. 按[构建指南](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/BUILD.zh-CN.md)准备同版本、同架构的头文件、运行库与 Python binding；避免旧环境的 `PYTHONPATH`、`LD_LIBRARY_PATH` 混入另一套 SDK。
2. 完成[SDK 通用准备](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/sdk-first-use.zh-CN.md)中的导入、连接和只读观测验证。
3. 使用 ROS 2 时再按[Motion Bridge 指南](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/ros2-motion-bridge.zh-CN.md)检查消息与服务。
4. 记录实际检查结果：导入通过、只读观测通过、仿真通过、真机控制通过是不同验证阶段。只填写已经完成的阶段。

建议随应用保存以下记录：

```text
验证日期：
设备型号 / 固件完整版本：
运行位置 / OS / Python / ROS 2：
SDK / Python SDK / Msgs / ROS 2 commits：
运行库目录 / 交付来源 / 校验值：
执行的验证及结果：
未验证项：
```

## 4. 升级与回退

升级前查看各组件的 Release/变更记录，重点核对 ABI、消息字段、依赖和动作参数变化。保留旧版本记录、运行库和应用配置，在候选环境完成上述检查后再切换应用。

发现不兼容时，停止候选应用，并在设备固件仍兼容的前提下恢复原先整套应用、binding 和运行库。固件回退需要单独确认支持流程，不能通过切换 SDK 自动完成。涉及 Low-level 的应用切换，先完成[结束与交还控制](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/low-level-control.zh-CN.md)。

[返回操作指南](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/README.zh-CN.md)
