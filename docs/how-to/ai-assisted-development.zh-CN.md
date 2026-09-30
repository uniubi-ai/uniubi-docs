# 使用 AI 辅助机器人开发

[English](ai-assisted-development.md) | **简体中文**

## 目标

让 AI 编程助手根据你实际使用的源码版本，协助开发 UniUbi SDK 应用、ROS 2 集成和 RL 策略。这些 skills 发布在文档仓库中，服务于整个 UniUbi 项目生态。

## 选择 skills

| Skill | 职责 |
| --- | --- |
| [uniubi-robot-developer](../../skills/uniubi-robot-developer/SKILL.md) | 统一入口：选择开发路径，协调跨项目任务 |
| [uniubi-robot-sdk](../../skills/uniubi-robot-sdk/SKILL.md) | C++ / Python SDK 构建、应用、观测、控制和媒体 |
| [uniubi-robot-ros2](../../skills/uniubi-robot-ros2/SKILL.md) | ROS 2 节点、launch 配置、消息、服务和 bridge 集成 |
| [uniubi-robot-rl](../../skills/uniubi-robot-rl/SKILL.md) | uniubi_rl_lab 的任务、奖励、训练排障、导出和回放 |

跨项目开发可以安装全部四个，也可以单独安装专项 skill。统一入口按需读取可用的专项指导，不依赖子代理或特定模型。专项 skill 缺失时，仍可以根据已有仓库文档开展工作。

Skills 提供开发指导，不会安装 SDK、ROS 2、Isaac Lab、模型权重或设备软件。

## 安装

每个 skill 都是符合 [Agent Skills 格式](https://agentskills.io/specification)的独立目录，复制时保留 SKILL.md 和 references。其他 AI 助手的发现目录可能不同，请按对应工具的安装说明操作。这些文件不依赖私有服务器或凭据。

对于 Codex，当前[官方 skill 文档](https://learn.chatgpt.com/docs/build-skills)提供用户级目录 `~/.agents/skills` 和项目内的 `.agents/skills` 两种发现位置。

准备包含这些 skills 的 [uniubi-docs](https://github.com/uniubi-ai/uniubi-docs) 版本。在 AI 助手读取 skills 的机器或环境中，从该仓库根目录执行以下命令。按需安装时修改 `selected_skills`；仅在某个项目使用时，将 `skills_target` 改成该项目下 `.agents/skills` 的绝对路径。

```bash
cd /path/to/uniubi-docs
git rev-parse HEAD
```

```bash
bash <<'BASH'
set -eu
skills_source="$PWD/skills"
skills_target="$HOME/.agents/skills"
selected_skills="uniubi-robot-developer uniubi-robot-sdk uniubi-robot-ros2 uniubi-robot-rl"

for skill in $selected_skills; do
  test -f "$skills_source/$skill/SKILL.md" || {
    echo "Missing skill: $skills_source/$skill" >&2
    exit 1
  }
  if [ -e "$skills_target/$skill" ] || [ -L "$skills_target/$skill" ]; then
    echo "Already exists; review before updating: $skills_target/$skill" >&2
    exit 1
  fi
done
mkdir -p "$skills_target"
for skill in $selected_skills; do
  cp -R "$skills_source/$skill" "$skills_target/$skill"
done
echo "Installed skills in $skills_target"
BASH
```

命令遇到已有同名 skill 会退出，避免覆盖。升级时先比较已安装目录与所选源码版本，保留自己的修改，再明确替换已检查的目录。避免同时在用户级和项目级位置安装同名副本。

检查助手是否识别到安装的 skill 名称。如果 Codex 没有显示新安装的 skill，可重启后检查。也可以直接让助手读取本仓库中指定的 SKILL.md；这是显式使用，不代表已经配置自动发现。

## 开始任务

提供相关仓库路径和开发目标。涉及运行平台、固件版本或训练任务、checkpoint 时，补充已知信息，其余内容让助手从文件中核实。

下面的示例用自然语言指定 skill 名称。如果助手支持 skill 选择器或显式调用语法，也可以使用对应入口。

**应用开发**

> 使用 uniubi-robot-sdk。在 /path/to/uniubi_robot_sdk_py 中，为外部 Linux PC 编写最小的 IMU 只读示例。先核实实际版本和 API，包含订阅清理及数据新鲜度验证方法。

**ROS 2 集成**

> 使用 uniubi-robot-ros2。在 /path/to/uniubi_ros2 中添加消费 IMU 数据的业务节点。修改前核实已有 bridge 的 topic、消息类型、QoS 和 namespace，不启动机器人运动。

**RL 开发**

> 使用 uniubi-robot-rl。在 /path/to/uniubi_rl_lab 中，给我的现有任务增加一个奖励项。先检查是否已有等价实现，再接入当前任务并做静态检查，暂不启动训练。

**跨项目策略接入**

> 使用 uniubi-robot-developer。检查导出策略如何接入 Low-level SDK。对比训练保存配置与部署适配器的观测、归一化、关节顺序、动作缩放和控制周期，修复确认存在的不一致并离线验证，不部署真机。

**训练排障**

> 使用 uniubi-robot-rl。根据这个 run 目录的日志和保存配置排查训练失败，先确认实际任务和算法，再提出修复，不重启训练。

## 预期结果与边界

助手应定位相关源码、完成请求的修改、执行适量检查，并说明观察到的结果和未验证项。源码修改、导入、编译、训练运行、仿真、RPC 成功和真机物理行为属于不同验证阶段。

编写应用本身不等于授权固件修改、设备部署、机器人运动或长时间训练。真机前置条件和控制权交还遵循已有的 [High-level](high-level-control.zh-CN.md) 和 [Low-level](low-level-control.zh-CN.md) 指南；需要实际运行时，请明确操作范围。

缺少必要仓库、依赖、匹配版本的文档或硬件时，助手应说明具体限制，不能编造 API 或声称验证通过。

## 维护 skills

统一入口维护路由和跨项目契约，专项 skill 维护领域流程。API 细节优先引用当前源码和文档，避免复制整份手册。专项目录复制到文档仓库外后仍应能够独立使用。

修改后运行 `python3 scripts/check_docs.py` 检查格式和引用，并按 Agent Skills 格式验证每个 SKILL.md 的 frontmatter。在临时环境中按授权范围尝试上面的任务，检查领域选择、源码依据、生成的改动和验证结论。特别检查专项独立使用、缺少专项 skill，以及未授权硬件执行时的 RL 到 SDK 接入流程。

[返回操作指南](README.zh-CN.md)
