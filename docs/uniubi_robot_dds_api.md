# 宇泛机器狗 DDS / ROS 2 直连接入 API

> 适用对象：不借助本厂商 SDK，直接用 OMG DDS（推荐 Cyclone DDS 0.10.5）或 ROS 2 对接设备的开发者。
> 与高级控制 SDK（`docs/uniubi_high_level_sdk.md`）能力对齐，是其底层协议契约的对外描述。

---

## 目录

- [一、概述与 DDS 通道对接规范](#一概述与-dds-通道对接规范)
  - [1.1 接入方式](#11-接入方式)
  - [1.2 DDS 基础](#12-dds-基础)
  - [1.3 三类通道](#13-三类通道)
    - [1.3.1 RPC 通道](#131-rpc-通道请求-应答)
    - [1.3.2 事件通道](#132-事件通道设备主动推送)
    - [1.3.3 数据订阅发布通道](#133-数据订阅发布通道开放型-pubsub)
    - [1.3.4 Topic 汇总](#134-topic-汇总)
  - [1.4 开发工程模板](#14-开发工程模板)
- [二、业务消息格式规范](#二业务消息格式规范)
  - [2.1 RPC 消息规范](#21-rpc-消息规范)
    - [2.1.1 RPC 请求 payload 格式](#211-rpc-请求-payload-格式)
    - [2.1.2 RPC 回复 payload 格式](#212-rpc-回复-payload-格式)
    - [2.1.3 业务成败双层判定](#213-业务成败双层判定)
  - [2.2 事件通道](#22-事件通道)
- [三、业务流](#三业务流)
  - [3.1 控制权生命周期](#31-控制权生命周期)
  - [3.2 RPC 方法列表](#32-rpc-方法列表)
  - [3.3 RPC 方法详解](#33-rpc-方法详解)
    - [3.3.1 会话管理](#331-会话管理)
    - [3.3.2 动作控制](#332-动作控制)
    - [3.3.3 数据上报](#333-数据上报)
    - [3.3.4 状态查询](#334-状态查询)
    - [3.3.5 音频控制](#335-音频控制)
    - [3.3.6 系统设置](#336-系统设置)
  - [3.4 实时控制帧 (TRC)](#34-实时控制帧-trc)
  - [3.5 运控观测量订阅](#35-运控观测量订阅)
  - [3.6 事件接收与分发](#36-事件接收与分发)
  - [3.7 关闭](#37-关闭)
  - [3.8 断网与多端](#38-断网与多端)
- [四、消息格式与字段](#四消息格式与字段)
  - [4.1 TRC 控制帧](#41-trc-控制帧)
  - [4.2 观测量](#42-观测量)
  - [4.3 事件](#43-事件)
  - [4.4 错误码](#44-错误码)
- [附录 A · 客户端自检清单](#附录-a--客户端自检清单)
- [附录 B · Python 接入要点](#附录-b--python-接入要点)
- [附录 C · C++ 接入要点](#附录-c--c-接入要点)
- [附录 D · 错误处理决策表与静默失败排查](#附录-d--错误处理决策表与静默失败排查)

---

## 一、概述与 DDS 通道对接规范

本章覆盖两件事：

1. 协议适用范围与接入方式（[§1.1](#11-接入方式)）
2. 客户端按本协议接入 DDS 时必须遵守的通道层规范 —— DDS 基础参数、IDL 类型扩展性、QoS 与三类通道的形态约定（[§1.2](#12-dds-基础) / [§1.3](#13-三类通道)）

本章**不涉及任何业务名字 / 值**（如 `serverName`、`service`、方法名、topic 取值等都在 [§3](#三业务流) / [§4](#四消息格式与字段) 给出）。通道层任一项不对齐，DDS 会**静默丢弃**样本，没有任何错误反馈。

### 1.1 接入方式

| 接入方式 | 适用场景 |
|---|---|
| **OMG DDS 原生**（C/C++/Java/Python/Go） | 任何 OMG DDS 实现（Cyclone DDS 0.10.5 / RTI Connext / Fast DDS / OpenDDS）按本协议描述的 IDL + QoS 直接对接 |
| **ROS2** | ROS 2 节点直接按 IDL 建立 DDS Topic，无需 ROS Message 转换；rmw 推荐 Cyclone DDS。ROS 2 `.msg` / `.srv` 与本协议 IDL 的命名 / 类型 / QoS 映射规范见 [`ros2_dds_interop_overview.md`](ros2_dds_interop_overview.md) |

两种方式底层等价 —— 在同一 DDS Domain 上 publish/subscribe 同一组 IDL 类型，差异仅在客户端框架。

### 1.2 DDS 基础

#### 域 / Discovery

- **DDS Domain ID**：固定 **`42`**（业务域 "host"，承载本协议的全部 RPC、事件、数据通道）。客户端 DDS profile / 运行时 join 的 domain id 必须与之一致，否则 discovery 完全不可见
- **Discovery**：标准 OMG SPDP / SEDP 多播。客户端与机器人需在同一二层网络或多播路由可达；不需要手动指定对端地址
- **Participant 数**：每个进程一个 `DomainParticipant` 即可，所有 topic 复用之

#### DDS profile（Cyclone DDS 推荐配置）

机器人侧使用 Cyclone DDS 跑这条业务域。客户端如果也用 Cyclone DDS，建议加载下面这份 profile（**只需按部署环境改 `<NetworkInterface name="...">` 的网卡名**）：

```xml
<?xml version="1.0" encoding="utf-8"?>
<CycloneDDS
  xmlns="https://cdds.io/config"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="https://cdds.io/config https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd"
>
  <Domain Id="42">
    <General>
      <Interfaces>
        <!-- 客户端按需替换 name 为本机实际网卡（eth0 / enp3s0 / wlan0 …）；presence_required="true" 让网卡缺失时立刻失败 -->
        <NetworkInterface name="eth0" priority="3" multicast="default" presence_required="true" />
      </Interfaces>
      <AllowMulticast>true</AllowMulticast>
      <MaxMessageSize>65500B</MaxMessageSize>
    </General>

    <SharedMemory>
      <Enable>true</Enable>
      <LogLevel>info</LogLevel>
    </SharedMemory>

    <Tracing>
      <Verbosity>none</Verbosity>
    </Tracing>
  </Domain>
</CycloneDDS>
```

**关键字段含义**：

| 字段 | 必须 / 推荐 | 说明 |
|---|---|---|
| `Domain Id="42"` | **必须**与机器人侧一致 | 业务域固定 42，不可改 |
| `<NetworkInterface name="...">` | **建议明确指定** | 多网卡 / 跨网段 / wifi+有线 共存时，不指定可能导致 DDS 在错误的网卡上协商；指定 `presence_required="true"` 让网卡不存在时启动直接失败，避免事后排查 |
| `<AllowMulticast>true` | 必须 | discovery 走多播；如果网络环境完全禁用多播，需要改成 peers list（参见 Cyclone DDS 文档 `<Peers>` 字段） |
| `<MaxMessageSize>65500B` | 推荐 | 单条 UDP 包上限；过低会触发分片影响吞吐 |
| `<SharedMemory><Enable>` | 可选 | 同机器内不同进程间走 SHM 加速；若客户端总是跨网络可关闭 |

**应用如何加载该 profile**

| 方式 | 做法 |
|---|---|
| 环境变量 | `export CYCLONEDDS_URI=file:///path/to/host_config.xml` 后再启动应用 |
| 代码层 | Cyclone DDS API 创建 `DomainParticipant` 时通过 `dds_create_domain` 或 `participant_qos` 加载（具体参考 Cyclone DDS C/C++ 文档） |

> 若使用 **RTI Connext / Fast DDS / OpenDDS** 等其它 OMG DDS 实现，按各自厂商的 QoS profile 语法重写一份等价配置即可 —— 只要 **Domain Id = 42 + 多播 discovery + 通用 QoS（§1.2 后续小节）** 对齐，跨实现互通没问题。

#### IDL 类型扩展性（OMG XTYPES）

| 类型 | Extensibility |
|---|---|
| `Header` | `@final`（显式标注，不可扩展） |
| 其他业务 / 信封类型 | 默认 `@appendable`（允许末尾追加新字段，不允许删除或重排） |

客户端 IDL 必须与此一致；某些 DDS 实现（如 Fast DDS）若标注不一致会导致 discovery 不匹配。

#### 其他 IDL 约定

- 所有 `string` 字段均为 **unbounded**（无长度上限）。
- 所有 topic 均为 **keyless**（IDL 中无 `@key`，每 topic 仅一个 instance）。

#### 通用 QoS（所有通道都加）

| QoS Policy | 取值 | 选择原因 |
|---|---|---|
| `DATA_REPRESENTATION` | `[XCDR1, XCDR2]` | 兼容新旧 |
| `TYPE_CONSISTENCY_ENFORCEMENT` | `ALLOW_TYPE_COERCION` | 允许 IDL 字段顺序差异 / 增减 |

#### QoS 不匹配的后果

DDS 触发 `RequestedIncompatibleQos`，sample **静默不投递**（不报错）。每个通道的具体 QoS 见各自小节。

### 1.3 三类通道

设备与客户端之间存在三类通道（按通信模式区分，不绑业务）：

| 通道 | 模式 | 载荷形态 | 详见 |
|---|---|---|---|
| RPC 通道 | 请求-应答 | 信封 + JSON payload | [§1.3.1](#131-rpc-通道请求-应答) |
| 事件通道 | 设备→客户端单向，带信封 + magic | 信封 + JSON payload | [§1.3.2](#132-事件通道设备主动推送) |
| 数据订阅发布通道 | 单向 pub/sub，开放型 | IDL 结构体直接作 payload | [§1.3.3](#133-数据订阅发布通道开放型-pubsub) |

#### 1.3.1 RPC 通道（请求-应答）

承载所有业务请求-响应类调用。

**Topic 命名模式**

```
rq/${serverName}Request    // 请求，客户端 → 设备
rr/${serverName}Reply      // 响应，设备 → 客户端
```

`rq/` / `rr/` 是本协议固定前缀（与 ROS 2 命名约定一致），不可改；对开发者提供 RPC 通道的请求 topic 为 `rq/robotServerRequest`，RPC 响应的 topic 为 `rr/robotServerReply`。

**IDL 定义**

```idl
module uniubi {
  module dds_ {
    @final
    struct Header {
        uint64 clientId;
        uint64 requestId;
    };
  };

  module srv {
    module dds_ {

      struct System_Request_ {
          uniubi::dds_::Header  header;
          uint64                timestamp;
          string                service;
          string                device_id;
          string                method;
          string                payload;
      };

      struct System_Response_ {
          uniubi::dds_::Header  header;
          uint32                code;
          uint64                timestamp;
          string                device_id;
          string                payload;
      };

    };
  };
};
```

**信封字段语义**

请求：

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `header.clientId` | uint64 | 是 | 客户端 id；每个客户端唯一固定 id |
| `header.requestId` | uint64 | 是 | 请求 id；单调递增 |
| `timestamp` | uint64 | 是 | 调试时间戳 |
| `service` | string | 是 | 业务路由 |
| `device_id` | string | 是 | 目标设备 SN；设备只会响应 SN 为自己的 RPC 请求 |
| `method` | string | 是 | 业务方法名 |
| `payload` | string | 是 | 业务参数 JSON 字符串 |

响应：

| 字段 | 类型 | 含义 |
|---|---|---|
| `header.clientId` / `header.requestId` | uint64 | 回显请求 |
| `code` | uint32 | RPC 协议层 code（取值见下表）；`0` = RPC 消息路由成功；非 0 表示错误，具体错误参考 code 取值表格 |
| `timestamp` | uint64 | 调试时间戳 |
| `device_id` | string | 设备 SN；设备只会响应 SN 为自己的 RPC 请求 |
| `payload` | string | 业务响应 JSON 字符串 |

**`code` 取值**

| code | 名称 | 含义 | 触发场景 | 客户端动作 |
|---|---|---|---|---|
| `0` | SUCCESS | 路由成功 | handler 已返回，业务结果看 payload | 进入业务层判定（[§2.1.3](#213-业务成败双层判定)） |
| `1` | TIMEOUT | 框架层超时 | 设备 handler 内部超时 | 不可重试；检查设备状态 |
| `2` | SERVER_ERROR | 服务端错误 | handler 抛出异常 / 内部错 | 不可重试；上报 |
| `3` | METHOD_NOT_FOUND | 方法不存在 | 设备不支持请求的 `method` | 检查 method / 固件版本 |
| `4` | INVALID_REQUEST | 请求非法 | 信封字段缺失 / 类型错 | 检查请求结构 |
| `5` | SERVER_UNPREPARE | 服务未就绪 | 设备启动早期 | 退避 1–3s 重试 |
| `6` | SERVICE_NOT_FOUND | 服务不存在 | `service` 字段值不合法 | 检查 service 拼写 |
| `7` | DESERIALIZE_ERROR | 反序列化失败 | `payload` 不是合法 JSON | 检查 payload 序列化 |

**响应匹配（协议级强制约束）**

客户端必须按以下三项同时匹配响应，任一不匹配视为响应不属于本次调用，**必须丢弃并继续等待目标响应**：

| 匹配项 | 规则 |
|---|---|
| `System_Response_.header.clientId` | == 请求.`header.clientId` |
| `System_Response_.header.requestId` | == 请求.`header.requestId` |
| `System_Response_.device_id` | == 请求.`device_id` |

- `Header.clientId` 进程内全局唯一（启动时随机 uint64）
- `Header.requestId` session 内单调递增，绝不重复
- `device_id` 以本次请求配置的目标设备 SN 为准；同 Domain 存在多台设备时，非目标设备响应不能作为成功或失败结果
- **着重注意：每次请求 `header.requestId` 单调递增**
- 不要因为收到非目标设备响应而重新发送同一方法请求；正确行为是在本次请求超时窗口内持续等待目标设备响应，直到命中三项匹配或本地超时

**QoS**

| QoS Policy | 取值 | 说明 |
|---|---|---|
| `RELIABILITY` | `RELIABLE` | RPC 不可丢，依赖 DDS 重传 |
| `RELIABILITY.max_blocking_time` | `100 ms` | 防止调用线程被网络拖死 |
| `HISTORY` | `KEEP_LAST, depth=10` | 缓存最近 10 个 sample |
| `DURABILITY` | `VOLATILE` | 不持久化；后加入的 reader 不补发历史 |
| `DATA_REPRESENTATION` | `[XCDR1, XCDR2]` | 兼容新旧 |
| `TYPE_CONSISTENCY_ENFORCEMENT` | `ALLOW_TYPE_COERCION` | 允许 IDL 字段顺序差异 / 增减 |

请求与响应 topic 的 reader/writer 必须**采用完全相同的 QoS**。

#### 1.3.2 事件通道（设备主动推送）

承载设备主动推送的业务事件（状态变化、控制权变化等）。单向、不重传。区别于通用 pub/sub（[§1.3.3](#133-数据订阅发布通道开放型-pubsub)）：带固定信封 + `magic` 校验 + wire/业务 topic 二级路由。

**Topic 命名模式**

```
rt/${serverName}/Event     // 设备 → 客户端
```

`rt/` 是本协议固定前缀（与 ROS 2 命名约定一致），不可改；对开发者提供事件通道的 topic 为 `rt/robotServer/Event`。

**IDL 定义**

```idl
module uniubi {
  module dds_ {
    @final
    struct Header {
        uint64 clientId;
        uint64 requestId;
    };
  };

  module msg {
    module dds_ {

      struct EventMessage_ {
          uniubi::dds_::Header  header;
          uint32                magic;       // 固定 = 0x53425645，校验失败必须丢弃
          uint64                timestamp;   // 调试时间戳
          string                topic;       // 业务 topic（取值见 §4.3），见 [§4](#四消息格式与字段)
          string                payload;     // 事件 JSON 字符串
      };

    };
  };
};
```

**信封字段语义**

| 字段 | 类型 | 含义 |
|---|---|---|
| `header.clientId` | uint64 | 事件源 id（设备生成），可用于过滤本端 loop-back |
| `header.requestId` | uint64 | 设备内部事件序号 |
| `magic` | uint32 | 协议校验常量，固定 = `0x53425645`（ASCII `"EVBS"`）；**校验失败必须整帧丢弃** |
| `timestamp` | uint64 | 调试时间戳 |
| `topic` | string | 业务 topic 字符串（不是 DDS wire-level topic）；具体取值由业务约定（见 [§4](#四消息格式与字段)）；客户端遇未知值**宽容透传**给业务层 |
| `payload` | string | JSON 字符串，schema 随 `topic` 取值而异（详见 [§4](#四消息格式与字段)） |

**QoS**

| QoS Policy | 取值 | 说明 |
|---|---|---|
| `RELIABILITY` | `BEST_EFFORT` | reader 离线时不积压在设备侧 |
| `HISTORY` | `KEEP_LAST, depth=10` | reader 最多积压 10 条 |
| `DURABILITY` | `VOLATILE` | 不补发历史；初值需 RPC 主动查询 |
| `DATA_REPRESENTATION` | `[XCDR1, XCDR2]` | 兼容新旧 |
| `TYPE_CONSISTENCY_ENFORCEMENT` | `ALLOW_TYPE_COERCION` | 允许 IDL 字段顺序差异 / 增减 |

#### 1.3.3 数据订阅发布通道（开放型 pub/sub）

承载客户端 ↔ 设备的高频单向流。本通道不绑定固定业务，是**留给业务层扩展**的开放型通道，IDL 结构体直接作为 payload，无 JSON 信封。

**Topic 命名模式**

```
rt/<scopeName>
```

`rt/` 是本协议固定前缀（与 ROS 2 命名约定一致），不可改；`<scopeName>` 由具体业务约定。

**载荷形态**

整个 IDL 结构体即 payload，**不嵌套 JSON 字符串**。新业务追加新 topic 时，建议继续遵循"IDL 结构体直接作 payload"的约定。

**QoS（协议级强制项）**

| QoS Policy | 取值 | 说明 |
|---|---|---|
| `DATA_REPRESENTATION` | `[XCDR1, XCDR2]` | 兼容新旧 |
| `TYPE_CONSISTENCY_ENFORCEMENT` | `ALLOW_TYPE_COERCION` | 允许 IDL 字段顺序差异 / 增减 |

其余 QoS（`RELIABILITY` / `HISTORY` / `DURABILITY` 等）由具体业务约定，本协议不在此处给出默认值。各业务通道的 `scopeName`、IDL 类型与完整 QoS 见 [§3](#三业务流) / [§4](#四消息格式与字段)。

#### 1.3.4 Topic 汇总

DDS wire-level topic 一览（客户端建 Writer/Reader 时使用）：

| Topic | 方向 | 通道类型 | IDL 类型 | 用途 / 详见 |
|---|---|---|---|---|
| `rq/robotServerRequest` | 客户端 → 设备 | RPC 请求 | `System_Request_` | [§1.3.1](#131-rpc-通道请求-应答) |
| `rr/robotServerReply` | 设备 → 客户端 | RPC 应答 | `System_Response_` | [§1.3.1](#131-rpc-通道请求-应答) |
| `rt/robotServer/Event` | 设备 → 客户端 | 事件通道 | `EventMessage_` | [§1.3.2](#132-事件通道设备主动推送) / [§4.3](#43-事件) |
| `rt/motion/trc` | 客户端 → 设备 | 数据 pub/sub | `RemoteControl_` | TRC 实时控制帧 [§3.4](#34-实时控制帧-trc) / [§4.1](#41-trc-控制帧) |
| `rt/motion/observed` | 设备 → 客户端 | 数据 pub/sub | `MotionObserved_` | 运控观测量 [§3.5](#35-运控观测量订阅) / [§4.2](#42-观测量) |
| `rt/sensor/observed` | 设备 → 客户端 | 数据 pub/sub | `SensorObserved_` | 传感器观测量（GPS / UWB）[§3.5](#35-运控观测量订阅) / [§4.2](#42-观测量) |

> `rq/` / `rr/` / `rt/` 是 ROS 2 命名约定下的固定前缀，客户端必须按此 wire-level 名字订阅 / 发布 —— 跟 SDK 内部使用的"逻辑 topic 名"（如 `robotServer.host.event`、`motion/trc`）不同，那些是 SDK 内部 EventBus / Publisher 包装层的命名，DDS 上不可见。

### 1.4 开发工程模板

本节给出最小可起跑的项目模板，开发者照着复制 + 补 IDL 即可编译 + 运行。

#### 1.4.1 依赖安装

机器人侧使用 **Cyclone DDS 0.10.5**；客户端建议使用相同主版本。

```bash
# Ubuntu/Debian：从源码编译
git clone --depth=1 -b 0.10.5 https://github.com/eclipse-cyclonedds/cyclonedds
cd cyclonedds && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/usr/local -DBUILD_IDLC=ON ..
make -j$(nproc) && sudo make install
sudo ldconfig

# 如需 C++ 绑定（推荐）：cyclonedds-cxx
git clone --depth=1 -b 0.10.5 https://github.com/eclipse-cyclonedds/cyclonedds-cxx
cd cyclonedds-cxx && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
make -j$(nproc) && sudo make install
sudo ldconfig
```

校验：

```bash
which idlc                       # /usr/local/bin/idlc（IDL 编译器）
ldconfig -p | grep ddsc          # libddsc.so.0 已生效
ldconfig -p | grep ddscxx        # libddscxx.so.0（C++ 绑定）
```

#### 1.4.2 工程目录结构

```
my_robot_client/
├── CMakeLists.txt
├── host_config.xml          # DDS profile，复制 §1.2 给出的样例后改 NetworkInterface 网卡名
├── idl/                     # 从 uniubi_robot_msgs/idl/ 整目录拷贝过来
│   ├── Request.idl
│   ├── RPCMessage.idl
│   ├── EventMessage.idl
│   ├── MotorState.idl
│   ├── MotionObserved.idl
│   ├── SensorObserved.idl
│   └── RemoteControl.idl
└── src/
    └── main.cpp             # 应用代码
```

完整 IDL 文件由 [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) 仓库的 `idl/` 提供，**整目录拷出来即可**（带 `#include` 依赖关系，缺一不可）。每个文件覆盖的协议范围：

| 文件 | 内容 |
|---|---|
| `Request.idl` | 公共 `Header`（clientId / requestId），所有信封共用 |
| `RPCMessage.idl` | `System_Request_` / `System_Response_`（RPC 请求 / 应答信封） |
| `EventMessage.idl` | `EventMessage_`（事件通道信封） |
| `MotorState.idl` | `MotorHeader`（电机寻址：limbsNo / jointNo） |
| `MotionObserved.idl` | `IMUState` / `Vector3f` / `Quaternionf` / `MotorObserved` / `PowerObserved` / 运控观测帧 |
| `SensorObserved.idl` | `GPSFrame` / `GEOGPoint` / `UWBRawObserved` / 传感器观测帧 |
| `RemoteControl.idl` | `RemoteControl_`（遥控手柄帧） |

> 客户端不需要全部使用，按场景挑：纯 RPC 接入只用 `Request.idl + RPCMessage.idl`；如果还要订阅事件、观测量、遥控，按需补 `EventMessage.idl` / `MotionObserved.idl` / `SensorObserved.idl` / `RemoteControl.idl` 等。

#### 1.4.3 CMakeLists.txt 样例

```cmake
cmake_minimum_required(VERSION 3.16)
project(my_robot_client CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(CycloneDDS         REQUIRED)
find_package(CycloneDDS-CXX     REQUIRED)

# IDL → 自动生成 C++ 代码（编译期）
# 文件顺序无关；idlc 会按 #include 关系解析依赖
idlc_generate(TARGET sdk_idl
              FILES
                  idl/Request.idl
                  idl/RPCMessage.idl
                  idl/EventMessage.idl
                  idl/MotorState.idl
                  idl/MotionObserved.idl
                  idl/RemoteControl.idl
              FEATURES extended-types)

add_executable(my_client src/main.cpp)
target_link_libraries(my_client
        sdk_idl
        CycloneDDS-CXX::ddscxx)
```

#### 1.4.4 构建 + 运行

```bash
mkdir -p build && cd build
cmake ..
make -j$(nproc)

# 让 Cyclone DDS 加载本目录下的 profile（决定 domain 42 + 走哪张网卡）
export CYCLONEDDS_URI=file://$PWD/../host_config.xml

./my_client
```

#### 1.4.5 启动顺序与最小验证

1. **确保机器人已上电、网络可达**；客户端机器 `ip a` 能看到自己声明的网卡（如 `eth0`）
2. **客户端进程启动后**，DDS Discovery 走 SPDP 多播。若 5 秒内仍 publish/subscribe 不到任何 sample：
   - 检查 `host_config.xml` 里 `Domain Id="42"` 与机器人侧一致
   - 检查 `<NetworkInterface name="...">` 是否选到了真正与机器人互通的网卡
   - 抓 udp 多播包确认多播未被防火墙挡：`sudo tcpdump -i eth0 udp port 7400`（Cyclone DDS 默认 discovery 端口）
3. **协议级最小验证**：参考 [§3.3.4 状态查询](#334-状态查询) 中 `getMotionCapabilities` —— 一次无副作用的 RPC，能返回设备支持的动作列表即代表通道打通

具体每个 RPC 的信封 / payload / topic name 见 [§3 业务流](#三业务流) 和 [§4 消息格式与字段](#四消息格式与字段)。客户端按这两节装填 `System_Request_` + 发布到对应 topic 即可。

---

## 二、业务消息格式规范

本章定义业务层消息载荷的结构 —— RPC 通道的 payload JSON 信封（[§2.1](#21-rpc-消息规范)）与事件通道的 topic 约定（[§2.2](#22-事件通道)）。具体方法 / 事件的字段在 [§3](#三业务流) / [§4](#四消息格式与字段) 给出。

### 2.1 RPC 消息规范

`System_Request_` / `System_Response_` 的 IDL 与字段语义见 [§1.3.1](#131-rpc-通道请求-应答)。本节专讲 `payload` 字段内 JSON 信封的结构 —— 所有业务方法共用同一信封；具体方法的 `params` 字段在 [§3.3](#33-rpc-方法详解) 各方法详解中给出。

| 方向 | Topic |
|---|---|
| 请求（客户端 → 设备） | `rq/robotServerRequest` |
| 回复（设备 → 客户端） | `rr/robotServerReply` |

#### 2.1.1 RPC 请求 payload 格式

```jsonc
{
  "call":   { "clientId": "<string>" },
  "params": { /* 方法专属字段 */ }
}
```

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `call` | object | 是 | 调用方上下文 |
| `call.clientId` | string | 是 | RPC 客户端 id；客户端 id 需要按照具体业务接口的要求来填写 |
| `params` | object | 是 | 方法专属参数；无参填 `{}`（**不可省略**） |

#### 2.1.2 RPC 回复 payload 格式

```jsonc
{ "code": <uint32>, "result": <bool>, "params": { ... } }
```

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `code` | uint32 | 是 | 业务 errno（取值见 [§4.4.1](#441-业务层-payloadcode)）；`0` = 成功 |
| `result` | bool | 是 | `true` = 业务成功；`false` = 业务失败 |
| `params` | object | 否 | handler 返回数据；可选，按具体业务接口而异 |

读取顺序：先看 `result` 判定业务成败，失败时再看 `code` 取失败原因；`params` 由具体方法决定是否存在（详见 [§3.3](#33-rpc-方法详解) 各方法的"响应 `params`"）。

#### 2.1.3 业务成败双层判定

RPC 协议层成功 ≠ 业务层成功。判定一次 RPC 业务成功须**同时**满足：

| 层 | 字段 | 必满足 |
|---|---|---|
| 协议层 | `System_Response_.code` | `== 0` |
| 业务层 | `payload.result` | `== true` |

```
business_ok = (response.code == 0) AND (payload.result == true)
```

### 2.2 事件通道

事件通道的 IDL（`EventMessage_`）、信封字段与 QoS 见 [§1.3.2](#132-事件通道设备主动推送)，对外 topic 固定为 `rt/robotServer/Event`。

事件 `EventMessage_.payload` 字段为 JSON 字符串，其 schema 随 `EventMessage_.topic` 字段值（业务 topic）而异 —— 详见 [§4.3](#43-事件)。

---

## 三、业务流

本章描述基于 Cyclone DDS（[§1](#一概述与-dds-通道对接规范)）提供的机器狗业务能力。[§3.1](#31-控制权生命周期) 是各业务共用的基础 —— 控制权生命周期；[§3.2](#32-rpc-方法列表) 列出全部 RPC 方法；[§3.3](#33-rpc-方法详解) 分类详解每个方法的消息格式 / 字段 / 使用注意；[§3.4](#34-实时控制帧-trc) 起按场景介绍非 RPC 通道（TRC / 运控观测量 / 事件）与关闭、断网处理。

#### 能力清单

本协议当前覆盖以下业务能力，每项能力对应一个或多个 [§3.3](#33-rpc-方法详解) 中的 RPC 方法或 [§3.4](#34-实时控制帧-trc)-[§3.6](#36-事件接收与分发) 的通道操作：

| 能力 | 典型场景 |
|---|---|
| 调度预置动作（走、站、跳等） | 自动化作业、任务编排 |
| 实时手柄 / 摇杆控制（50–100 Hz） | 远程操控、遥操作训练 |
| 订阅设备状态事件（电池、网络、播放等） | 监控面板、告警 |
| 音频文件管理与播放控制 | 语音提示、人机交互 |
| 查询设备能力与系统状态 | 健康检查、能力适配 |
| 订阅运控高频观测量 | 训练数据采集、远程监视 |

### 3.1 控制权生命周期

要执行控制操作（如动作控制、下发遥控指令、音乐播放等），客户端必须先获取到设备的控制权。设备的控制权是**独占的**，不允许多个客户端同时执行控制。完整的控制权生命周期：

```
   ① 获取控制权 (takeMotionControl)
            │
            ▼
   ② 执行控制业务（下发动作 / TRC 帧 / 音频播放 ...）
            │
            ▼
   ③ 周期性续约 (renewMotionControl)
            │
            ▼
   ④ 业务完成后释放控制权 (releaseMotionControl)
```

- **租约机制**：客户端必须按照一定的周期对控制权续约；未续约或者超期，设备自动收回当前客户端的控制权。
- **查询类接口不需要控制权**：默认所有查询类接口任何客户端都可调用 / 订阅；如有需要控制权的查询接口，会在该接口处单独说明。

详细取控 / 续约 / 释放调用方式见 [§3.3.1](#331-会话管理) 会话管理。

### 3.2 RPC 方法列表

| serviceName | 方法 (method) | 功能描述 | 需要控制权 |
|---|---|---|:---:|
| `robotAppService` | `takeMotionControl` | 申请控制权 | 否 |
| `robotAppService` | `renewMotionControl` | 控制权续约 | 是 |
| `robotAppService` | `releaseMotionControl` | 释放控制权 | 否 |
| `robotAppService` | `startMotionAction` | 触发预置动作 | 是 |
| `robotAppService` | `stopMotionAction` | 停止当前动作 | 是 |
| `robotAppService` | `setMotionActionParams` | 运行期改动作子参数 | 是 |
| `robotAppService` | `emergencyStopMotion` | 紧急制动 | 是 |
| `robotAppService` | `setMotionObservedEnable` | 开关运控观测量 | 否 |
| `robotAppService` | `queryMotionState` | 查询运控状态 | 否 |
| `robotAppService` | `getMotionCapabilities` | 查询设备支持的动作集合 | 否 |
| `robotAppService` | `getSystemStatus` | 拉取系统状态快照 | 否 |
| `robotAppService` | `startPlayList` | 启动 / 恢复音频播放 | 是 |
| `robotAppService` | `stopPlayList` | 停止 / 暂停音频播放 | 是 |
| `robotAppService` | `getAudioPlayList` | 查询音频文件清单 | 否 |
| `robotAppService` | `getAudioPlayDetail` | 查询当前播放详情 | 否 |
| `robotAppService` | `addAudioFile` | 上传 / 新增音频文件 | 是 |
| `robotAppService` | `deleteAudioFile` | 删除音频文件 | 是 |
| `robotAppService` | `getCameraLightBrightness` | 查询相机补光灯亮度 | 是 |
| `robotAppService` | `setCameraLightBrightness` | 设置相机补光灯亮度 | 是 |

调用模板（所有方法共用）：

```jsonc
// System_Request_
{
  "header":    { "clientId": <session-id>, "requestId": <seq> },
  "timestamp": <now-ms>,
  "service":   "robotAppService",
  "device_id": "<设备 SN>",
  "method":    "<上表 method 列>",
  "payload":   "<JSON 字符串化的 {call, params}>"
}
```

### 3.3 RPC 方法详解

每个方法给出：**请求 `params`**（消息格式 + 字段）、**响应 `params`**（消息格式 + 字段）、**使用注意**。

**方法速查表**

| 方法 | 持权要求 | 关键参数 | 详见 |
|---|---|---|---|
| `takeMotionControl` | 无 | `leaseTimeout`(ms) | [§3.3.1](#331-会话管理) |
| `renewMotionControl` | 持权 | `controller` | [§3.3.1](#331-会话管理) |
| `releaseMotionControl` | 持权 | `controller` | [§3.3.1](#331-会话管理) |
| `startMotionAction` | 持权 | `action` / `params` | [§3.3.2](#332-动作控制) |
| `stopMotionAction` | 持权 | — | [§3.3.2](#332-动作控制) |
| `setMotionActionParams` | 持权 | `params`（按当前 action schema） | [§3.3.2](#332-动作控制) |
| `emergencyStopMotion` | 持权 | — | [§3.3.2](#332-动作控制) |
| `setMotionObservedEnable` | 无 | `motionEnable`(bool), `sensorEnable`(bool) | [§3.3.3](#333-数据上报) |
| `queryMotionState` | 无 | — | [§3.3.4](#334-状态查询) |
| `getMotionCapabilities` | 无 | — | [§3.3.4](#334-状态查询) |
| `getSystemStatus` | 无 | — | [§3.3.4](#334-状态查询) |
| `startPlayList` | 持权 | `list` / `volume` / `repeat` 等 | [§3.3.5](#335-音频控制) |
| `stopPlayList` | 持权 | — | [§3.3.5](#335-音频控制) |
| `getAudioPlayList` | 无 | `type`(如 customVoice) | [§3.3.5](#335-音频控制) |
| `getAudioPlayDetail` | 无 | — | [§3.3.5](#335-音频控制) |
| `addAudioFile` | 持权 | `id` / `name` / `file` 或 `url` 等 | [§3.3.5](#335-音频控制) |
| `deleteAudioFile` | 持权 | `id` | [§3.3.5](#335-音频控制) |
| `getCameraLightBrightness` | 持权 | — | [§3.3.6](#336-系统设置) |
| `setCameraLightBrightness` | 持权 | `brightness`(0~100) | [§3.3.6](#336-系统设置) |

> 所有 RPC 通过同一对 wire topic `rq/robotServerRequest` / `rr/robotServerReply` 收发；服务名固定 `robotAppService` / `motionService` / `audioService` 之一（具体见各方法详解）。

#### 3.3.1 会话管理

`takeMotionControl` / `renewMotionControl` / `releaseMotionControl` 共同实现控制权生命周期（[§3.1](#31-控制权生命周期)）。

##### `takeMotionControl`

申请高级控制模式控制权。成功后客户端持有控制权。已持权时再次调用会刷新 `leaseTimeout` 并返回相同 `controller`。

**请求 `params`**

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `leaseTimeout` | uint32 | 是 | 租约时长 ms；建议 5000–60000 |

```jsonc
{ "call": { "clientId": "my-app" }, "params": { "leaseTimeout": 30000 } }
```

**响应 `params`**（成功时）

| 字段 | 类型 | 出现条件 | 含义 |
|---|---|---|---|
| `controller` | string（16 字节） | 始终 | 后续持权 RPC 的 `call.clientId` 必须填此值 |
| `leaseTimeout` | uint32 | 始终 | 设备最终生效的租约 ms |
| `rawActionId` | uint64 | 设备启用 TRC 时 | TRC 帧 `RemoteControl_.controller` 取此值；缺失或 0 表示 TRC 不可用 |

```jsonc
{ "result": true, "params": { "controller": "0xGUefQ7T9VWxulv", "leaseTimeout": 30000, "rawActionId": 1234567890 } }
```

**使用注意**

- 取控成功后客户端持有控制权，需**立即**启动定时续约
- 后续所有持权 RPC 的 `payload.call.clientId` 必须切换为响应里的 `controller`
- 失败 `0x1D controlWasSeized`：控制权已被其他客户端持有；等对方释放或租约超时
- `leaseTimeout` 建议 5000–60000 ms —— 客户端崩溃后设备等到租约超时才释放，不宜过长

##### `renewMotionControl`

续约控制权。客户端**必须**周期调用，否则租约超时后设备自动收回。

**请求 `params`**：`{}`

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": {} }
```

**响应 `params`**（成功时）

| 字段 | 类型 | 含义 |
|---|---|---|
| `leaseTimeout` | uint32 | 续约后的剩余租约时长 ms |

```jsonc
{ "result": true, "params": { "leaseTimeout": 30000 } }
```

**使用注意**

- 续约周期建议 `clamp(leaseTimeout / 3, 200 ms, 10 s)`
- 任一次续约 RPC 超时或返失败立即视为已失权
- 失败 `0x10 operatorInvalid`：租约已过期，立即按"失权处理"流程

##### `releaseMotionControl`

主动归还控制权后，其他客户端可立即接管。

**请求 `params`**：`{}` —— 响应 `params` 也为空（仅 `result: true`）。

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": {} }
```

**使用注意**

- 调用后客户端应将 `payload.call.clientId` 切回自定义标识，停止续约线程
- 即便对方未应答，本端也应认为不再持权
- 关闭流程必须在 RPC endpoint 销毁前完成（见 [§3.7](#37-关闭)）

##### 失权处理（统一流程）

以下任一情形触发：

| 触发条件 |
|---|
| 续约 RPC 超时或返失败 |
| 续约 RPC 返 `0x10 operatorInvalid`（租约已过期） |
| 任意 RPC 返 `0x1C noOperationPerm` / `0x1D controlWasSeized` |
| 收到事件 `robotServer.control.status` 且 `controlled == false`（且自己原本是持权方） |
| 长时间断网超过租约期（设备已自动收权） |

统一处理动作：

```
① 立即停止 TRC 帧发送
② 停止后台续约线程
③ 若有正在执行的预置动作，调一次 stopMotionAction 通知设备清理状态
   （此调用大概率返 0x1C，可忽略返回结果）
④ 客户端不再持有控制权
⑤ 通知业务层
```

失权后**不需要重建 DDS endpoint**，重新 `takeMotionControl` 时必须使用**新响应里的 `controller` / `rawActionId`**，不要复用旧值。

#### 3.3.2 动作控制

`startMotionAction` / `stopMotionAction` / `setMotionActionParams` / `emergencyStopMotion` 共同实现动作下发与停止。

##### `startMotionAction`

触发设备执行预置动作。RPC 返回时设备已开始动作，运动本身异步。

**请求 `params`**

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `action` | string | 是 | 动作名；必须在 `getMotionCapabilities` 返回列表内 |
| `params` | object | 否 | 动作子参数；字段名/范围/单位通过 `getMotionCapabilities` 的 `actions[].params` 动态查询。一次性动作（如 `jumpBackflip`）通常无参数，可省略或填 `{}` |

```jsonc
{
  "call": { "clientId": "0xGUefQ7T9VWxulv" },
  "params": {
    "action": "walking",
    "params": { "velocity": 0.0, "lineVelocityX": 0.5, "lineVelocityY": 0.0 }
  }
}
```

**典型 `action` 取值**

`walking` / `standing` / `laying` / `bipedStand` / `handstand` / `waveBody` / `peakLoadStand` / `jumpFrontflip` / `jumpSideflip` / `jumpBackflip` / `jumpDoubleBackflip` / `jumpDoubleSideflip`

**响应 `params`**：成功时为空（仅 `result: true`）。

**使用注意**

- 实际支持的动作随设备型号与固件版本而异，须通过 `getMotionCapabilities` 动态查询，**不应在客户端硬编码**
- RPC 返回成功只表示**请求被设备接受**，物理运动可能持续数秒；判定动作真正完成有三种方式：
  - 轮询 `queryMotionState`，看 `params.action` 字段变化（适合站立/坐下等简单动作）
  - 订阅运控观测量（[§3.5](#35-运控观测量订阅)），监测 `motor[i].velocity` 接近 0 且持续若干帧
  - 预估等待（适合跳跃等简短固定动作）
- 典型失败：
  - `0x08 outOfDeviceCaps`：动作不在 capabilities，先 `getMotionCapabilities` 校验
  - `0x09 operationTempNotAllow`：`emergencyStopMotion` 冷却期，退避 3–5s 重试
  - `0x1C noOperationPerm`：已失权，走失权处理流程

##### `stopMotionAction`

停止当前动作。设备走收尾流程（非立即停）。停止后**保留控制权**。

**请求 `params`**：`{}` —— 响应 `params` 为空。

**使用注意**

- 要立即停请用 `emergencyStopMotion`
- 关闭流程中需在 release 之前调用，否则设备在交还控制权前仍可能持续执行上一动作

##### `setMotionActionParams`

在动作执行过程中动态修改子参数（**不切换动作**）。

**请求 `params`**

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `params` | object | 是 | 子参数；字段名 / 范围 / 单位见 `getMotionCapabilities` 返回的对应 action 的 `params` 列表 |

以 `walking` 为例（字段名 / 范围以 `getMotionCapabilities` 返回的为准）：

| 字段 | 类型 | 单位 | 含义 |
|---|---|---|---|
| `velocity`      | float | rad/s | 偏航角速度（yaw rate），正左转负右转 |
| `lineVelocityX` | float | m/s   | 前后线速度，正前进负后退 |
| `lineVelocityY` | float | m/s   | 侧向线速度，正右负左 |

```jsonc
{
  "call": { "clientId": "0xGUefQ7T9VWxulv" },
  "params": { "params": { "velocity": 0.0, "lineVelocityX": 0.5, "lineVelocityY": 0.0 } }
}
```

**响应 `params`**：成功时为空。

**使用注意**

- **全量重写**：`setMotionActionParams` 跟 `startMotionAction` 一样是**全量语义**——本次调用的 `params` 覆盖整套运行期参数，**未传字段归 0**。要只改 yaw 但保留 X 速度，必须三个字段都传齐
- **范围由服务端裁剪**：超出范围不报错，按边界值代替；实际能力上限通过 `getMotionCapabilities` 查询
- **零速度不等于停止**：要停下来用 `stopMotionAction`，不要靠下发 `{lineVelocityX:0, lineVelocityY:0, velocity:0}`
- **三个字段独立**：完整运动须三轴组合（如边走边转：`{"lineVelocityX":0.5,"velocity":0.3}`）

##### `emergencyStopMotion`

紧急制动 —— 设备立即切断运动输出，不走收尾流程。停止后**保留控制权**。

**请求 `params`**：`{}` —— 响应 `params` 为空。

**使用注意**

- 紧急停后**短时间内（约几秒）设备拒绝新动作**（返 `0x09 operationTempNotAllow`）
- 急停场景应使用本 RPC（走可靠通道），不要靠 TRC 帧

#### 3.3.3 数据上报

##### `setMotionObservedEnable`

控制运控观测量（[§3.5](#35-运控观测量订阅)）的对外发布开关。`motionEnable`/`sensorEnable` 分别独立控制 `MotionObserved_`、`SensorObserved_` 两路推送。

**请求 `params`**

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `motionEnable` | bool | 否 | `true` = 开启 `MotionObserved_` 推送；`false`/缺省 = 关闭 |
| `sensorEnable` | bool | 否 | `true` = 开启 `SensorObserved_` 推送；`false`/缺省 = 关闭 |

```jsonc
{ "call": { "clientId": "my-app" }, "params": { "motionEnable": true, "sensorEnable": false } }
```

**响应 `params`**：返回设置后的实际开关状态。

| 字段 | 类型 | 含义 |
|---|---|---|
| `motionEnable` | bool | 当前 `MotionObserved_` 推送开关 |
| `sensorEnable` | bool | 当前 `SensorObserved_` 推送开关 |

**使用注意**

- 默认关闭，且不持久化到配置：服务端重启后回到关闭态，需重新调用开启
- 不强制要求持权，但 `payload.call.clientId` 不能为空
- 调用顺序见 [§3.5](#35-运控观测量订阅)：**先订阅 reader 再调用本 RPC 开启推送**；反序会丢前若干毫秒的帧

#### 3.3.4 状态查询

##### `queryMotionState`

查询当前运控环最近一拍的实际生效动作 + 控制速度。

**请求 `params`**：`{}`

**响应 `params`**

| 字段 | 类型 | 含义 |
|---|---|---|
| `action`        | string | 当前生效动作名（运控环最近一拍 posture matching 结果）|
| `velocity`      | float  | 角速度（rad/s） |
| `lineVelocityX` | float  | 前后线速度（m/s） |
| `lineVelocityY` | float  | 横移线速度（m/s） |

> **无活动动作时**：RPC 成功（`result: true`）、`params` 为空对象 `{}`。
> 注意区分两层：
> - `result: false` → 服务端拒绝或 RPC 通道异常，按 RPC 错误码处理（参见 [§4.4 错误码](#44-错误码)）
> - `result: true` + `params: {}` → 服务端就是没活动动作；不要把这个当失败处理

```jsonc
// 有活动动作
{
  "result": true,
  "params": {
    "action":        "walking",
    "velocity":       0.0,
    "lineVelocityX":  0.5,
    "lineVelocityY":  0.0
  }
}

// 无活动动作（例如已 stopMotionAction）
{ "result": true, "params": {} }
```

**使用注意**

- 速度字段名 `velocity` / `lineVelocityX` / `lineVelocityY` 跟 `startMotionAction` / `setMotionActionParams` 的 `params` 入参字段名一致，方便回写
- 常用于动作完成判定（轮询 100–500 ms）；未来固件可能扩展更多字段，客户端应**忽略未知字段**以保持向前兼容

##### `getMotionCapabilities`

查询当前设备支持的预置动作集合 —— 含按键组合 + 可调参数（min/max/unit）。建议作为接入流程的首个 RPC 调用，业务侧据此动态渲染。

**请求 `params`**：`{}`

**响应 `params`**

| 字段 | 类型 | 含义 |
|---|---|---|
| `actions[].name`    | string         | 动作名，传给 `startMotionAction` 的 `action` 参数 |
| `actions[].mapping.require` | array<string\> | 触发该动作必须按下的按钮名，取值对应 TRC 按键字段 |
| `actions[].mapping.axisRequire` | array<object\> | 额外轴值条件；每项含 `axis`、`min`、`max`，`axis` 为 TRC 轴字段 |
| `actions[].mapping.priority` | integer | 同一帧多个动作命中时的优先级，数值越大优先级越高 |
| `actions[].mapping.exact` | bool | `true` 表示除 `require` 外不能有其它按钮同时按下 |
| `actions[].mapping.minHoldTime` | number | 最小按住时间（ms）；当前 `waveHand` / `heartSit` / `tweak` 为 `1000`，其余 posture 动作为 `0` |
| `actions[].params`  | array<object\> | 该动作可调的运行期参数；一次性动作无此字段 |
| `params[].name`     | string         | 参数 key，用作 `startMotionAction` / `setMotionActionParams` 的 `params` JSON 的 key |
| `params[].min/max`  | float          | 取值范围；超出会被服务端 clamp |
| `params[].unit`     | string         | 单位（如 `"m/s"` / `"rad/s"`）；服务端未配置则不输出 |

```jsonc
{
  "result": true,
  "params": {
    "actions": [
      {
        "name": "walking",
        "mapping": {
          "require": ["buttonBack", "buttonY"],
          "priority": 0,
          "minHoldTime": 0,
          "exact": true
        },
        "params": [
          { "name": "velocity",      "min": -2.0, "max": 2.0, "unit": "rad/s" },
          { "name": "lineVelocityX", "min": -1.0, "max": 1.0, "unit": "m/s"   },
          { "name": "lineVelocityY", "min": -0.5, "max": 0.5, "unit": "m/s"   }
        ]
      },
      {
        "name": "jumpBackflip",
        "mapping": {
          "require": ["buttonRB", "buttonA"],
          "priority": 1,
          "minHoldTime": 0,
          "exact": true,
          "axisRequire": [
            { "axis": "axesRT", "min": -1.0, "max": 0.49 }
          ]
        }
      },
      {
        "name": "emergencyStop",
        "mapping": {
          "require": ["buttonLB", "buttonRB"],
          "priority": 10,
          "minHoldTime": 0
        }
      }
    ]
  }
}
```

**使用注意**

- 建议接入后首个 RPC 调用本方法，验证 DDS 链路 / IDL / QoS / `device_id` 全部对齐
- 客户端 UI / 业务逻辑不应硬编码动作列表 / 参数范围
- 启动期一次构建快照，运行期直接返 cache，多次调用零成本

##### `getSystemStatus`

拉取**一次**完整设备系统状态快照。事件订阅为增量推送，**首次连接后须通过本方法获取完整快照**。

**请求 `params`**：`{}`

**响应 `params`**（顶层 key 按子系统分组，客户端按需消费）

```jsonc
{
  "result": true,
  "params": {
    "battery": {
      "abnormalStatus": 0, "statusCode": 0, "cycleCount": 186,
      "remainChargeTime": 52, "remainDischargeTime": 198,
      "power": 76.5, "health": 93.2, "temperature": 31.4,
      "fullCharge": 5180.0, "remaining": 3962.7, "current": 1.84, "voltage": 15.28
    },
    "network": {
      "ether":   { "enable": true,  "ipv4Addr": "...", "ipv4Gateway": "...", "ipv4Mask": "...", "mac": "...", "status": 0 },
      "hotspot": { "enable": false, "ipv4Addr": "...", "ipv4Gateway": "...", "ipv4Mask": "...", "mac": "...", "status": 1 },
      "mobile":  { "enable": true,  "ipv4Addr": "...", "ipv4Gateway": "...", "ipv4Mask": "...", "mac": "...", "signalLevel": 0, "simCardSta": true, "status": 0 },
      "wlan":    { "enable": true,  "ipv4Addr": "...", "ipv4Gateway": "...", "ipv4Mask": "...", "mac": "...", "status": 0 }
    }
  }
}
```

**`battery` 字段**

| 字段 | 类型 | 单位 | 含义 |
|---|---|---|---|
| `abnormalStatus` | uint8 | — | 功率电路是否异常，非 0 表示异常 |
| `statusCode` | uint16 | — | BMS 状态码，位掩码组合（见下表） |
| `cycleCount` | uint16 | 次 | 电池累计充放电循环次数 |
| `remainChargeTime` | uint16 | 分钟 | 剩余充电时间（充电中有效） |
| `remainDischargeTime` | uint16 | 分钟 | 剩余放电时间（按当前负载估算） |
| `power` | float | % | 当前电池电量百分比，0~100 |
| `health` | float | % | 电池健康度，0~100 |
| `temperature` | float | °C | 电池温度（有符号） |
| `fullCharge` | float | mAh | 满充容量 |
| `remaining` | float | mAh | 剩余容量 |
| `current` | float | A | 当前充放电电流（正充电、负放电） |
| `voltage` | float | V | 当前总电压 |

**`battery.statusCode` 位掩码**（`statusCode & bit != 0` 表示对应保护位有效）

| 位 | 值 | 含义 |
|---|---|---|
| bit0 | `0x0001` | pack 欠压保护 |
| bit1 | `0x0002` | cell 欠压保护 |
| bit2 | `0x0004` | pack 过压保护 |
| bit3 | `0x0008` | cell 过压保护 |
| bit4 | `0x0010` | 充电结束 |
| bit5 | `0x0020` | 放电过流保护 |
| bit6 | `0x0040` | 充电过流保护 |
| bit7 | `0x0080` | 短路保护 |
| bit8 | `0x0100` | 放电低温保护 |
| bit9 | `0x0200` | 充电低温保护 |
| bit10 | `0x0400` | 放电高温保护 |
| bit11 | `0x0800` | 充电高温保护 |
| bit12 | `0x1000` | MOS 高温保护 |
| bit13 | `0x2000` | Cell 采集断线保护 |
| bit14 | `0x4000` | Cell 电压失衡保护 |
| bit15 | `0x8000` | Cell 电压失效保护 |

**`network.<iface>.status` 枚举值**

| 值 | 含义 |
|---|---|
| `0` | 已连接 |
| `1` | 未连接 |
| `2` | 连接中 |

**`network.mobile.signalLevel` 枚举值**（仅 `mobile` 子对象）

| 值 | 含义 |
|---|---|
| `0` | 信号好（> 22 dB） |
| `2` | 信号中等（> 15 dB） |
| `3` | 信号差（≤ 15 dB） |

`network.mobile.simCardSta`：`true` = SIM 卡已就绪，`false` = 未插入或未识别。

**使用注意**

- 首次接入必须主动调一次本方法获取完整快照；后续变化通过事件 `statistics/device_status`（[§4.3](#43-事件)）增量推送
- 客户端需做**局部 merge / patch** 维护完整状态视图

#### 3.3.5 音频控制

##### `startPlayList`

播放音频文件列表，或恢复 `stopPlayList { "pause": true }` 暂停的播放。

**请求 `params`** —— 两种用法二选一：

*用法 A · 启动新列表*

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `list` | array<object\> | 是 | 待播文件，每项 `{ "id": <string> }`；`id` 通过 `getAudioPlayList` 获取 |
| `volume` | uint8 | 是 | 音量 0–100 |
| `repeat` | int32 | 是 | 循环次数；`-1` = 无限循环，`>0` = 次数，`0` 无意义 |

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "list": [{"id":"1"},{"id":"2"}], "volume": 50, "repeat": 1 } }
```

*用法 B · 恢复暂停*

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `resume` | bool | 是 | 固定 `true`，恢复 `stopPlayList { "pause": true }` 暂停的播放 |

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "resume": true } }
```

**响应 `params`**：成功时为空。

**使用注意**

- A/B 两种用法互斥，一次调用只能携带其中一组字段
- 播放状态变化通过事件 `statistics/play_list`（[§4.3](#43-事件)）订阅；首次快照用 `getAudioPlayDetail`

##### `stopPlayList`

停止或暂停音频播放。

**请求 `params`**

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `pause` | bool | 否 | `true` = 暂停，保留播放位置（可用 `startPlayList { "resume": true }` 恢复）；`false` 或字段缺失 = 停止并清空设备播放队列（**不可恢复**） |

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": {} }              // 停止
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "pause": true } } // 暂停
```

**响应 `params`**：成功时为空。

**使用注意**：停止（不带 `pause`）与暂停语义不同；前者清空队列不可恢复，后者保留位置可 `resume`。

##### `getAudioPlayList`

查询设备上已存音频文件清单。返回的 `id` 可作为 `startPlayList` / `deleteAudioFile` 的入参。

**请求 `params`**

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `type` | string | 否 | 过滤类别，可选 `"customVoice"`（仅返回自定义）；字段缺失 = 返回全量 |

**响应 `params`**

| 字段 | 类型 | 含义 |
|---|---|---|
| `list` | array<object\> | 文件列表 |
| `list[*].id` | string | 文件 id |
| `list[*].name` | string | 文件名 |
| `list[*].duration` | int | 时长（秒） |
| `list[*].size` | int | 文件大小（字节） |
| `list[*].createAt` | int64 | 创建时间戳（毫秒） |
| `list[*].describe` | string | 备注 |
| `remaining` | int | 剩余可上传数量 / 容量配额（精确语义由设备侧定义） |

```jsonc
{
  "result": true,
  "params": {
    "customVoice": [
      { "id": "1", "name": "walk", "duration": 12, "size": 320000, "createAt": 1712745600000, "describe": "示例备注" }
    ],
    "remaining": 20
  }
}
```

**使用注意**：返回为空集时正常（`0x28 dataResourceEmpty`，业务侧空集处理）。

##### `getAudioPlayDetail`

查询当前播放详情。事件 `statistics/play_list` 会推送增量变化，**首次快照须通过本方法获取**。

**请求 `params`**：`{}`

**响应 `params`**

| 字段 | 类型 | 含义 |
|---|---|---|
| `channel` | int | 播放通道，含义由设备侧定义 |
| `playing` | bool | 是否正在播放 |
| `paused` | bool | 是否暂停 |
| `repeat` | int | 重复配置：`-1`=无限循环；`>0`=次数；`0` 无意义 |
| `index` | int | 当前播放下标（从 0 起） |
| `count` | int | 当前播放列表总数 |
| `volume` | int | 当前音量，0~100 |
| `currentId` | string | 当前播放音频 ID |
| `list` | array<string\> | 当前播放列表，元素为音频 ID |

```jsonc
{
  "result": true,
  "params": {
    "channel": 0, "playing": true, "paused": false, "repeat": 1,
    "index": 0, "count": 2, "volume": 50,
    "currentId": "audio_1", "list": ["audio_1", "audio_2"]
  }
}
```

##### `addAudioFile`

向设备新增（上传）一个自定义音频文件。支持**两种获取文件的方式**：

- **`file` 模式（本地路径）**：调用方传入设备能直接读到的本地文件路径（如客户端跟机器人板内同部署、文件已在本机/共享盘上）。无下载步骤，最快。
- **`url` 模式（远程下载）**：调用方传入 HTTP URL，**机器人在 RPC 调用期间从该 URL 下载文件**到本地后再入库。调用方需要部署 HTTP 文件服务器把音频放出来，机器人能直接 GET 到。

**两种模式 `file` 和 `url` 二选一**（同时给两个时优先 `url`）。

| 部署形态 | 推荐 |
|---|---|
| SDK 应用与机器人同板内（板内模式） | 用 `file` —— 文件本来就在板上，直接给路径 |
| SDK 应用在远端主机（多机器人 / 外部机器） | 用 `url` —— 需自己跑一个 HTTP 文件服务器把音频暴露出来 |

**请求 `params`**

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `id` | string | 是 | 文件 id；客户端自定义，需保证不与已存在的非系统文件冲突 |
| `name` | string | 是 | 文件名（含扩展名，如 `"hello.mp3"`） |
| `file` | string | 二选一 | **本地路径模式**：机器人侧能直接读到的文件绝对路径 |
| `url` | string | 二选一 | **远程下载模式**：HTTP URL，机器人会拉取后入库 |
| `describe` | string | 否 | 备注 / 描述 |

```jsonc
// 本地路径模式（板内部署）
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "id": "custom_1", "name": "hello.mp3", "file": "/var/audio/hello.mp3", "describe": "示例" } }

// 远程下载模式（外部主机部署）
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "id": "custom_1", "name": "hello.mp3", "url": "http://192.168.1.x:8000/audio/hello.mp3", "describe": "示例" } }
```

**响应 `params`**：成功时为空。

**使用注意**

- 新增成功后，文件归类为 `customVoice`，可通过 `getAudioPlayList` 查询，亦可作为 `startPlayList` / `deleteAudioFile` 的 `id` 入参
- 支持的音频格式：`mp3` / `wav` 等常见格式；具体支持列表与单文件大小上限由设备方按机型给出
- `url` 模式：设备会在 RPC 调用期间完成下载，整体响应时间随网络与文件大小而变化；建议客户端使用比默认 5s 更长的本地超时（如 30s）
- `file` 模式：路径必须是机器人能访问的；走 NAS / 共享盘时确认挂载与读权限
- 典型失败：`0x01 paramsTypeError` / `0x02 paramsDeletion`（字段错）；`0x08 outOfDeviceCaps`（达到设备最大可存储音频数）；`id` 冲突（与已有非系统文件相同）；`url` 拉取失败 / `file` 路径不存在

##### `deleteAudioFile`

删除设备上指定 id 的音频文件。仅允许删除 `customVoice` 类；删除系统预置音频会返错误码。

**请求 `params`**

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `id` | string | 是 | 待删文件 id；通过 `getAudioPlayList` 获取 |

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "id": "1" } }
```

**响应 `params`**：成功时为空。

**使用注意**：典型失败 `0x21 fileNotExist`，检查 `id` 是否仍存在。

#### 3.3.6 系统设置

##### `getCameraLightBrightness`

查询机身相机补光灯当前亮度。

**请求 `params`**：无（仅 `call.clientId`）。

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" } }
```

**响应 `params`**：当前亮度。

```jsonc
{ "brightness": 50 }
```

**使用注意**：需持有控制权，否则返回 `kNotControlled`。

---

##### `setCameraLightBrightness`

设置机身相机补光灯亮度。

**请求 `params`**

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `brightness` | uint8 | 是 | 亮度，0~100 |

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "brightness": 50 } }
```

**响应 `params`**：成功时为空。

**使用注意**：典型失败 `0x04 paramsOutRange`，检查参数值域。

##### `getCameraLightBrightness`

查询机身相机补光灯控制状态和亮度。

**请求 `params`**：可为空。

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" } }
```

**响应 `params`**

| 字段 | 类型 | 含义 |
|---|---|---|
| `control` | bool | 当前是否由手动控制亮度 |
| `brightness` | int | 当前配置亮度，0~100 |

```json
{ "control": true, "brightness": 50 }
```

---

### 3.4 实时控制帧 (TRC)

TRC 是数据订阅发布通道（[§1.3.3](#133-数据订阅发布通道开放型-pubsub)）在"客户端→设备"方向的具体使用，承载手柄 / 摇杆采样型输入。

| 项 | 取值 |
|---|---|
| Topic | `rt/motion/trc` |
| 载荷类型 | `uniubi::msg::dds_::RemoteControl_`（[§4.1](#41-trc-控制帧)） |
| 推送频率 | 50–100 Hz |
| 鉴权字段 | `RemoteControl_.controller = rawActionId`（uint64，**不是** `controller` 字符串） |

#### QoS

| QoS Policy | 取值 | 选择原因 |
|---|---|---|
| `RELIABILITY` | `BEST_EFFORT` | 高频流不重传；下一帧自动覆盖 |
| `HISTORY` | `KEEP_LAST, depth=10` | 缓存最近 10 帧 |
| `DURABILITY` | `VOLATILE` | reader 加入晚了不补发老帧 |
| `DATA_REPRESENTATION` | `[XCDR1, XCDR2]` | 兼容新旧 |
| `TYPE_CONSISTENCY_ENFORCEMENT` | `ALLOW_TYPE_COERCION` | 允许 IDL 字段顺序差异 / 增减 |

#### 调用前提

```
① 已持有控制权
② rawActionId != 0
```

任一不满足，设备**静默丢弃**所有 TRC 帧。

#### 发送步骤

```
构造 RemoteControl_:
  trc.controller = rawActionId
  trc.timestamp  = monotonic_sequence
  trc.<button>   = 0 / 1
  trc.<axis>     = float in 范围（见 [§4.1](#41-trc-控制帧)）
DDS write 到 rt/motion/trc，不等响应，立即返回
```

#### 单帧瞬时语义

- 按键状态**单帧瞬时** —— 保持按下需持续推帧
- 触发后下一帧须将按键清零，否则会持续触发
- 停止动作必须主动下发一帧全 0，否则设备维持上一帧
- 建议同一按键组合以 20ms 间隔重发 3 次，提高送达概率（BestEffort 不保证每帧到达）

#### 急停场景

走 RPC 通道（`emergencyStopMotion`），不要靠 TRC 帧 —— TRC 走不可靠通道。

### 3.5 运控观测量订阅

运控观测量订阅基于数据订阅发布通道（[§1.3.3](#133-数据订阅发布通道开放型-pubsub)）的"设备→客户端"方向，承载 50 Hz 的运控观测帧（IMU + 多电机）。

| 项 | 取值 |
|---|---|
| Topic | `rt/motion/observed` |
| 载荷类型 | `uniubi::msg::dds_::MotionObserved_`（[§4.2](#42-观测量)） |
| 推送频率 | 50 Hz（每帧约 1 KB，带宽 ≈ 50 KB/s） |
| 默认状态 | **关闭** |

#### QoS

| QoS Policy | 取值 | 选择原因 |
|---|---|---|
| `RELIABILITY` | `BEST_EFFORT` | 高频流不重传；下一帧自动覆盖 |
| `HISTORY` | `KEEP_LAST, depth=10` | 缓存最近 10 帧 |
| `DURABILITY` | `VOLATILE` | reader 加入晚了不补发老帧 |
| `DATA_REPRESENTATION` | `[XCDR1, XCDR2]` | 兼容新旧 |
| `TYPE_CONSISTENCY_ENFORCEMENT` | `ALLOW_TYPE_COERCION` | 允许 IDL 字段顺序差异 / 增减 |

#### 启停约定（顺序敏感）

```
开启：
  ① reader 已订阅 rt/motion/observed
  ② 调用 RPC setMotionObservedEnable（[§3.3.3](#333-数据上报)），params: {"motionEnable": true}
  ③ 设备开始按 50 Hz 推送

关闭：
  ④ 调用 RPC setMotionObservedEnable，params: {"motionEnable": false}
  ⑤ 销毁 reader（可选；session 不关闭可保留）
```

必须**先订阅再开推送**，反序会丢前若干毫秒的帧。`setMotionObservedEnable` 不强制要求持权，但 `payload.call.clientId` 不能为空 —— 未持权时也可调用。

#### 传感器观测量（`rt/sensor/observed`）

传感器观测（GPS / UWB）走独立 topic `rt/sensor/observed`，与运控观测同属"设备→客户端"数据通道，载荷为 `uniubi::msg::dds_::SensorObserved_`（[§4.2](#42-观测量)）。

| 项 | 取值 |
|---|---|
| Topic | `rt/sensor/observed` |
| 载荷类型 | `uniubi::msg::dds_::SensorObserved_`（[§4.2](#42-观测量)） |
| 默认状态 | **关闭** |

QoS、启停约定与运控观测量一致（同上：`BEST_EFFORT` / `KEEP_LAST` / `VOLATILE` / `ALLOW_TYPE_COERCION`；先订阅再开推送），开关同样经 [§3.3.3](#333-数据上报) 的数据上报 RPC 控制。无对应传感器硬件的设备不写入数据。

> 该 topic 的设备侧发布依赖具体机型的传感器配置；无 GPS / UWB 硬件的设备不发布本 topic。

### 3.6 事件接收与分发

客户端收到 `EventMessage_` 后的处理流程：

```
收到 EventMessage_
   │
   ├─► magic != 0x53425645  →  丢弃
   │
   ├─► (可选) header.clientId == 本端 id  →  本端 loop-back，丢弃
   │
   ├─► 按 `EventMessage_.topic` 字段值分发：
   │
   │   ┌─ "robotServer.host.event"（容器模式）
   │   │   └─► 解析 payload JSON，按内层 event 字段二次分发
   │   │       业务 payload 在 detail 字段
   │   │
   │   ├─ "robotServer.control.status"（直通模式）
   │   │   └─► payload JSON 直接传给业务 handler
   │   │
   │   └─ 未知 `EventMessage_.topic` 值
   │       └─► 透传给业务层（向前兼容设备新增事件）
   │
   └─► 完成
```

| 术语 | 当前已定义取值 | 位置 |
|---|---|---|
| 业务 topic（`EventMessage_.topic` 字段值） | `robotServer.host.event` / `robotServer.control.status` | `EventMessage_.topic` |
| 子业务 topic | 多个（如 `statistics/device_status`） | 容器型业务 topic 内层 `payload.event` |

各 `EventMessage_.topic` 值与子业务 topic 的 payload schema 见 [§4.3](#43-事件)。

### 3.7 关闭

按以下顺序关闭，避免设备侧状态残留：

```
① 若仍持有控制权：
   a. 发一帧全 0 TRC（停止当前 TRC 控制）
   b. 调 stopMotionAction
   c. 若开启了运控观测量：调 setMotionObservedEnable(motionEnable=false)
   d. 调 releaseMotionControl（等响应到达再继续；超时也无所谓）
   e. 停止后台续约线程

② 销毁运控观测量 reader / TRC writer / 事件 reader
③ 销毁 RPC reader / writer
④ 销毁 DomainParticipant
```

**顺序敏感**：RPC 调用（c、d）必须在 RPC endpoint 销毁（③）之前完成；停止指令必须在 release 之前下发，否则设备在交还控制权前仍可能持续执行上一动作。

### 3.8 断网与多端

#### 断网与租约

| 场景 | 表现 / 处理 |
|---|---|
| 短时网络抖动（< 10 s） | DDS reliable QoS 自动补传 RPC；TRC / 运控观测量可能丢若干帧自动恢复；续约期间失败走"失权处理"流程（[§3.3.1](#331-会话管理)） |
| 设备重启 / 长时间断网（> 30 s） | discovery 重新收敛后**不必销毁本端 endpoint**；先调 `getMotionCapabilities` 探活；按需重新 `takeMotionControl` |
| 客户端进程意外退出 | 设备等到租约超时才释放控制权；重启客户端视为新 session；若旧租约未过期，新 session 会返 `0x1D`，需等待 |

重连判定信号（任选其一）：DDS publication-matched 监听器 / 定时探活 / 任意 RPC 连续 3 次超时。

#### 同设备多客户端

允许"一个持权 + N 个只读观察者"。每个客户端用独立的 `Header.clientId`（uint64）与 `payload.call.clientId`（string）；响应通过 `clientId` + `requestId` + `device_id` 匹配（[§1.3.1](#131-rpc-通道请求-应答)）自动路由到正确客户端。

#### 同网多设备

`EventMessage_` / `MotionObserved_` / `RemoteControl_` 等广播消息**不含 `device_id` 字段** —— 同 Domain 内所有 reader 都会收到所有设备的广播。客户端必须做**应用层过滤**：

- 单设备场景：所有广播按本端持有的 device_id 归属
- 多设备同时持权场景：用 `controller` token 关联（事件 `payload.controller == 本端 controller` 才消费）

---

## 四、消息格式与字段

本章是 RPC 之外通道的字段字典 —— TRC 控制帧、观测量、事件 schema、错误码。RPC 业务消息格式见 [§2](#二业务消息格式规范)，各 RPC 方法 params 字段见 [§3.3](#33-rpc-方法详解)。

### 4.1 TRC 控制帧

#### IDL（`uniubi::msg::dds_::RemoteControl_`）

```idl
module uniubi {
  module msg {
    module dds_ {

      struct RemoteControl_ {
          uint64   controller;   // 鉴权字段，填 takeMotionControl 响应里的 rawActionId
          uint64   timestamp;    // 客户端维护的递增相对值；同一控制会话内必须单调递增

          // 16 个数字按键（uint8，0 = 未按 / 1 = 按下，单帧瞬时）
          uint8    back;
          uint8    start;
          uint8    lb;
          uint8    rb;
          uint8    f1;
          uint8    f2;
          uint8    a;
          uint8    b;
          uint8    x;
          uint8    y;
          uint8    up;
          uint8    down;
          uint8    left;
          uint8    right;
          uint8    ls;
          uint8    rs;

          // 6 个模拟轴（float）
          float    stickLX;      // 摇杆量纲 [-1.0, 1.0]
          float    stickLY;
          float    stickRX;
          float    stickRY;
          float    triggerL;     // 扳机量纲 [0.0, 1.0]
          float    triggerR;
      };

    };
  };
};
```

#### 按键物理映射

| IDL 字段 | 物理映射 |
|---|---|
| `back` | Stand 键；动作语义由设备能力配置决定 |
| `start` | Motion 键；动作语义由设备能力配置决定 |
| `lb` / `rb` | 左 / 右肩键（Left/Right Bumper） |
| `f1` / `f2` | 功能键 1 / 2 |
| `a` / `b` / `x` / `y` | ABXY 键 |
| `up` / `down` / `left` / `right` | 方向键 D-Pad |
| `ls` / `rs` | 左 / 右摇杆按下（Stick Click） |

#### 摇杆 / 扳机映射

| IDL 字段 | 物理映射 | 范围 |
|---|---|---|
| `stickLX` | 左摇杆横轴 | [-1.0, 1.0] |
| `stickLY` | 左摇杆纵轴（典型用作前后） | [-1.0, 1.0] |
| `stickRX` | 右摇杆横轴 | [-1.0, 1.0] |
| `stickRY` | 右摇杆纵轴 | [-1.0, 1.0] |
| `triggerL` | 左扳机 | [0.0, 1.0] |
| `triggerR` | 右扳机 | [0.0, 1.0] |

#### 标准遥控功能映射

TRC 帧承担两类输入：
- **按键组合切换动作**：将 `require` 中的按键同时置 1，且满足 `axisRequire`（如有），即可触发对应预置动作（等价于 `startMotionAction`）
- **摇杆设置实时控制量**：摇杆 / 扳机 float 量驱动运行期参数（等价于 `setMotionActionParams`，例如 `walking` 时通过摇杆调 `lineVelocityX` / `lineVelocityY` / `velocity`）

两类输入可同时在一帧中携带。

下表的 posture 动作快照来自 RobotService `motionCapacity` 的 `motionTRC.motionMap.posture`。对外按键名 Stand / Motion 在 DDS 中分别对应 `back` / `start`，在 SDK 中分别对应 `buttonBack` / `buttonStart`。实际开放动作和 `require` / `axisRequire` / `priority` / `exact` / `minHoldTime` 以 `getMotionCapabilities` 返回为准。

| 分类 | 用户操作 | 中文标准名 | 英文标准名 | 用户说明 | DDS 字段 / 内部动作 |
|---|---|---|---|---|---|
| 安全 | LB + RB | 急停 | Emergency Stop | 立刻停下并趴下 | `lb + rb`；`emergencyStop` |
| 姿态 | LB + Y | 双足站立 | Two-Leg Stand | 后腿站起来 | `lb + y`；`bipedStand` |
| 姿态 | LB + A | 倒立 | Handstand | 前脚撑地倒立 | `lb + a`；`handstand` |
| 姿态 | LB + X | 左侧双足站立 | Left-Side Stand | 用左侧两脚站立 | `lb + x`；`leftSideStand` |
| 姿态 | LB + B | 右侧双足站立 | Right-Side Stand | 用右侧两脚站立 | `lb + b`；`rightSideStand` |
| 状态 | Stand + A | 趴下 | Lie Down | 趴到地上，进入安全低姿态 | `back + a`；`laying` |
| 状态 | Stand + Y | 行走 | Walking | 进入可移动状态 | `back + y`；`walking` |
| 状态 | Motion | 站立 | Standing | 进入站立状态 | `start`；`standing`（priority 0） |
| 表演 | LB + Motion | 扭一扭 | Wiggle | 原地扭动表演 | `lb + start`；`waveBody` |
| 表演 | B | 招手 | Wave Hand | 执行招手动作 | `b`；`waveHand` |
| 表演 | 按住 Y 1 秒 | 坐起画心 | Heart Sit | 坐起并完成画心动作 | `y`；`heartSit`（minHoldTime 1000） |
| 移动 | 按住 A 1 秒 | 低速微动 | Tweak | 进入低速小幅移动模式 | `a`；`tweak`（minHoldTime 1000） |
| 姿态 | Motion | 负重站立 | Peak Load Stand | 进入负重站立状态 | `start`；`peakLoadStand`（priority 2） |
| 特技 | RB + 方向键上 | 前跳 | Forward Jump | 向前跳一下 | `rb + up`；`jumpForward` |
| 特技 | RB + Y | 前空翻 | Front Flip | 向前翻一下 | `rb + y`；`jumpFrontflip` |
| 特技 | RB + B | 侧空翻 | Side Flip | 向侧方翻转 | `rb + b` 且 `triggerR` ∈ [-1.0, 0.49]；`jumpSideflip` |
| 特技 | RB + A | 后空翻 | Back Flip | 向后翻一下 | `rb + a` 且 `triggerR` ∈ [-1.0, 0.49]；`jumpBackflip` |
| 特技 | 按住 RT + RB + A | 后空翻两圈 | Double Back Flip | 按住保险键后向后翻两圈 | `rb + a` 且 `triggerR` ∈ [0.5, 1.0]；`jumpDoubleBackflip` |
| 特技 | 按住 RT + RB + B | 侧空翻两圈 | Double Side Flip | 按住保险键后向侧方翻两圈 | `rb + b` 且 `triggerR` ∈ [0.5, 1.0]；`jumpDoubleSideflip` |
| 行走 | 左摇杆上 | 前进 | Forward | 往前走 | `stickLY` → `lineVelocityX > 0`（`walking`） |
| 行走 | 左摇杆下 | 后退 | Backward | 往后走 | `stickLY` → `lineVelocityX < 0`（`walking`） |
| 行走 | 左摇杆左 | 左移 | Move Left | 横着向左走 | `stickLX` → `lineVelocityY < 0`（`walking`） |
| 行走 | 左摇杆右 | 右移 | Move Right | 横着向右走 | `stickLX` → `lineVelocityY > 0`（`walking`） |
| 转向 | 右摇杆左 | 左转 | Turn Left | 向左转身 | `stickRX` → `velocity > 0`（`walking`） |
| 转向 | 右摇杆右 | 右转 | Turn Right | 向右转身 | `stickRX` → `velocity < 0`（`walking`） |
| 速度 | 方向键上 | 加速 | Speed Up | 走得更快 | `up`；切换 fast profile |
| 速度 | 方向键下 | 减速 | Slow Down | 走得更慢 | `down`；切换 slow profile |

`buttonStart` 同时匹配 `standing`（priority 0）和 `peakLoadStand`（priority 2）；同一帧多个动作命中时由服务端按能力配置的 priority 和当前可用动作决策。`waveHand` / `heartSit` / `tweak` 的 `minHoldTime` 均为 `1000`，其余 posture 动作当前为 `0`。`exact=true` 表示除 `require` 外不能有其它按钮同时按下；`emergencyStop` 未配置 `exact`，允许与其它按钮同时出现时仍按最高优先级触发。上述字段由 `getMotionCapabilities` 下发，不建议客户端按文档表格硬编码。

#### 帧丢弃条件

| 条件 | 原因 |
|---|---|
| `controller != 当前 rawActionId` | 鉴权失败 |
| 设备未持权 / 无客户端持权 | 通道未激活 |
| 设备未启用 TRC（`takeMotionControl` 响应里 `rawActionId` 缺失或 0） | 通道不可用 |
| QoS 不匹配 | DDS 层 `RequestedIncompatibleQos`，sample 不投递 |
| 字段范围越界（如 `stickLX = 5.0`） | 设备做范围裁剪，行为不可预期 |

**排查方法**：发送一帧后立刻调 `queryMotionState`，若 `params.action` 未变化，说明帧未生效。

---

### 4.2 观测量

#### IDL（`uniubi::msg::dds_::MotionObserved_` 及其依赖）

```idl
module uniubi {
  module dds_ {

    struct Vector3f {
        int8        error;       // 单分量错误码（0 = 正常）
        float       x;
        float       y;
        float       z;
    };

    struct Quaternionf {
        int8        error;
        float       w;
        float       x;
        float       y;
        float       z;
    };

    struct IMUState {
        float       temp;        // °C
        Vector3f    accel;       // 加速度 m/s²；x=roll/y=pitch/z=yaw
        Vector3f    gyro;        // 角速度 rad/s；x=roll/y=pitch/z=yaw
        Vector3f    mag;         // 磁力计 μT
        Vector3f    euler;       // 欧拉角 rad；x=roll[-π,π], y=pitch[-π/2,π/2], z=yaw[-π,π]
        Quaternionf quaternion;  // 单位四元数
    };

    struct MotorHeader {
        uint32      limbsNo;
        uint32      jointNo;
    };

    struct MotorObserved {
        uint8       enable;
        uint8       online;
        uint8       error;       // 故障码（取值见下）
        float       position;
        float       velocity;
        float       torque;
        float       temp;
        float       voltage;
        float       lossRate;
        float       maxTorque;   // 当前电机最大扭矩 N·m
        MotorHeader header;
    };

    struct PowerObserved {
        float       power;          // 当前电池电量 %
        float       health;         // 健康度 %
        float       temper;         // 电池温度 ℃
        float       chargeCurrent;  // 实时电流 A
        float       chargeVoltage;  // 当前总电压 V
    };

  };

  module msg {
    module dds_ {

      const uint32 MAX_MOTOR_NUM = 16;

      struct MotionObserved_ {
          uniubi::dds_::IMUState        imu;
          int32                         motorNum;     // 有效电机数量（≤ MAX_MOTOR_NUM）
          uint64                        timestamp;    // 递增相对时间戳，单位 us（设备内部服务使用，非墙钟，跨主机对齐勿用）
          uniubi::dds_::MotorObserved   motor[MAX_MOTOR_NUM];  // 定长 16；仅前 motorNum 个有效
          uniubi::dds_::PowerObserved   power;        // 整机电源 / 电池状态
      };

    };
  };
};
```

> 注意：DDS IDL 的 `MotorHeader` 是 wire contract，字段为 `uint32 limbsNo/jointNo`。C++/Python SDK POD 中的 `MotorHeader` 是 SDK ABI 结构，字段为 `uint16_t limbNo/jointNo`。两者属于不同边界，不能直接混用或按内存布局转换；跨 DDS 与 SDK 边界时必须按字段名和语义显式转换。

#### IMU 字段量纲

| 字段 | 量纲 | 说明 |
|---|---|---|
| `imu.temp` | °C | IMU 芯片温度 |
| `imu.accel` | m/s² | 三轴加速度 |
| `imu.gyro` | rad/s | 三轴角速度 |
| `imu.mag` | μT | 三轴磁力计 |
| `imu.euler` | rad | (roll, pitch, yaw)；roll ∈ [-π, π]，pitch ∈ [-π/2, π/2]，yaw ∈ [-π, π] |
| `imu.quaternion` | — | 单位四元数 (w, x, y, z) |

每个 `Vector3f` / `Quaternionf` 的 `error` 字段（`IMUDeviceErrno`）：`0` 正常 · `1` 数据无效 · `64` IMU 控制板离线 · `65` 控制板未就绪 · `66` 控制板升级中 · `67` 模组参数未就绪 · `68` 加热/未就绪。其中 `0/1` 由 IMU 上报、`64+` 由 SDK/服务端检测填入；`mag` / `quaternion` 部分机型不上报，`error` 恒为 `1`。

#### Motor 字段量纲

| 字段 | 量纲 | 说明 |
|---|---|---|
| `motor[i].enable` | 0/1 | 使能状态 |
| `motor[i].online` | 0/1 | 在线状态 |
| `motor[i].error` | uint8 | 故障码；0 = 正常，非 0 取值见 [§4.4.2](#442-电机-error-子码) |
| `motor[i].position` | rad | 当前关节角度 |
| `motor[i].velocity` | rad/s | 当前关节角速度 |
| `motor[i].torque` | N·m | 前馈力矩 |
| `motor[i].temp` | °C | 电机温度 |
| `motor[i].voltage` | V | 母线电压 |
| `motor[i].lossRate` | % | 通信丢包率 |
| `motor[i].maxTorque` | N·m | 当前电机最大扭矩 |
| `motor[i].header.limbsNo` | uint32 | 肢编号；编号规则随机型 |
| `motor[i].header.jointNo` | uint32 | 肢内关节编号；编号规则随机型 |

`limbsNo` / `jointNo` 具体编号规则随机型变化。客户端应把每个 `motor[i]` 当作独立条目处理，通过 `header` 字段查表，**不要假设固定电机数量或顺序**（如"四足 = 12 路 = 0..11"）。

#### 顶层字段

| 字段 | 量纲 | 说明 |
|---|---|---|
| `motorNum` | int32 | 有效电机数；具体数量随机型 |
| `timestamp` | us | 设备递增相对时间戳（单调递增，非 wall clock，跨主机勿对齐） |
| `motor[16]` | 定长数组 | 仅前 `motorNum` 个元素有效 |
| `power` | `PowerObserved` | 整机电源 / 电池状态，字段见下 |

#### Power 字段量纲

| 字段 | 量纲 | 说明 |
|---|---|---|
| `power.power` | % | 当前电池电量 |
| `power.health` | % | 电池健康度 |
| `power.temper` | ℃ | 电池温度 |
| `power.chargeCurrent` | A | 实时电流 |
| `power.chargeVoltage` | V | 当前总电压 |

#### 传感器观测 `SensorObserved_`（topic `rt/sensor/observed`）

承载 GPS / UWB 观测，独立于 `MotionObserved_`，订阅见 [§3.5](#35-运控观测量订阅)。

##### IDL（`uniubi::msg::dds_::SensorObserved_` 及其依赖）

```idl
module uniubi {
  module dds_ {

    enum GPSSignalLevel {
        gpsGre38db,   // 信号强（> 38 dB）
        gpsGre30db,   // 信号中（> 30 dB）
        gpsLes30db    // 信号弱（≤ 30 dB）
    };

    struct GEOGPoint {
        float       lat;        // 纬度 deg
        float       lng;        // 经度 deg
    };

    struct GPSFrame {
        uint32      valid;      // 1=有效，0=异常
        float       speed;      // GPS 测速 km/h
        int32       level;      // 信号等级，取值见 GPSSignalLevel
        int32       rssi;       // 信号强度原始值 单位 dbm
        GEOGPoint   point;      // 坐标点
    };

    enum UWBPairState {
        uwbPairNone,      // 未配对
        uwbInPairing,     // 配对中
        uwbPairSuccess,   // 配对成功
        uwbPairFailed     // 配对失败
    };

    struct UWBRawObserved {
        uint8       valid;      // 数据是否有效
        uint8       pairState;  // 是否配对，取值见 UWBPairState
        int16       rssi;       // 信号强度 单位 dbm
        uint16      pitch;      // 俯仰角 deg，[0, 360)
        uint16      azimuth;    // 方位角 deg，[0, 360)，正前方 0 度、逆时针递增
        uint32      distance;   // 距离 cm
    };

  };

  module msg {
    module dds_ {

      struct SensorObserved_ {
          uint64                          timestamp;  // 递增相对时间戳，单位 us（设备内部服务使用，非墙钟）
          uniubi::dds_::GPSFrame          gps;        // GPS 观测
          uniubi::dds_::UWBRawObserved    uwb;        // UWB 观测
      };

    };
  };
};
```

##### GPS 字段量纲

| 字段 | 量纲 | 说明 |
|---|---|---|
| `gps.valid` | 0/1 | 1=本帧 GPS 有效 |
| `gps.speed` | km/h | GPS 测速 |
| `gps.level` | — | 信号等级，取值见 `GPSSignalLevel`（0 强 / 1 中 / 2 弱）|
| `gps.rssi` | dbm | 信号强度原始值 |
| `gps.point.lat` | deg | 纬度 |
| `gps.point.lng` | deg | 经度 |

##### UWB 字段量纲

| 字段 | 量纲 | 说明 |
|---|---|---|
| `uwb.valid` | 0/1 | 1=本帧 UWB 有效 |
| `uwb.pairState` | 枚举 | 配对状态，取值见 `UWBPairState`（0 未配对 / 1 配对中 / 2 配对成功 / 3 配对失败）|
| `uwb.rssi` | dbm | 信号强度 |
| `uwb.pitch` | deg | 俯仰角，[0, 360) |
| `uwb.azimuth` | deg | 方位角，[0, 360)，正前方 0 度、逆时针递增 |
| `uwb.distance` | cm | 距离 |

---

### 4.3 事件

`EventMessage_` 的 IDL 与信封字段见 [§1.3.2](#132-事件通道设备主动推送)。本节定义 `payload` JSON 的 schema —— 按 `EventMessage_.topic` 字段值（业务 topic）而异。

> 注意区分两层 topic：DDS wire-level topic 始终是 `rt/robotServer/Event`（[§1.3.4](#134-topic-汇总)），下面表里的"业务 topic"是 `EventMessage_.topic` 这个 string 字段的取值，客户端按它路由到对应 handler。

当前已定义 **2 个业务 topic**（设备版本演进可能新增；客户端遇未知值应宽容透传）：

| `EventMessage_.topic` 取值 | 封装模式 | 含义 |
|---|---|---|
| `robotServer.host.event` | 容器模式 | 业务事件容器；真实业务子 topic 在 payload 内层 `event` 字段 |
| `robotServer.control.status` | 直通模式 | 控制权状态变化 |

#### 4.3.1 容器模式 `robotServer.host.event`

**`EventMessage_.payload` 结构**

| 字段 | 类型 | 出现条件 | 含义 |
|---|---|---|---|
| `caller` | string | 始终 | 触发源（一般为空串 `""`） |
| `event` | string | 始终 | 业务 topic，取值见下表 |
| `detail` | object | 始终 | 业务 payload，结构按 `event` 不同而异 |

示例：

```jsonc
{
  "caller": "",
  "event":  "statistics/device_status",
  "detail": { "battery": { "power": 85.0 } }
}
```

**已定义业务 topic**

| `event` 取值 | 触发条件 | `detail` 内容 |
|---|---|---|
| `statistics/device_status` | 电池 / 网络等子系统状态变化 | 单子系统快照（**分批推送**），如 `{"battery":{...}}` 或 `{"network":{...}}` |
| `statistics/play_list` | 音频播放状态变化（开始 / 暂停 / 结束 / 切歌） | 当前播放详情，字段同 `getAudioPlayDetail` 响应，外加 `event` 字段（取值如 `"changed"`） |

##### `statistics/device_status` 字段语义

字段与 `getSystemStatus` 响应同结构。服务端**只下推有变化的字段**，未变化的字段不出现（不是 `null`）。客户端需做**局部 merge / patch** 来维护完整状态视图。

首次完整快照通过 `getSystemStatus` 主动查询（[§3.3.4](#334-状态查询)）。

##### `statistics/play_list` 字段语义

字段与 `getAudioPlayDetail` 响应同结构，**多一个 `event` 字段**：

| 字段 | 类型 | 含义 |
|---|---|---|
| `event` | string | 事件名，具体枚举值由设备侧定义（如 `"changed"`） |

#### 4.3.2 直通模式 `robotServer.control.status`

**`EventMessage_.payload` 结构**

| 字段 | 类型 | 出现条件 | 含义 |
|---|---|---|---|
| `controlled` | bool | 始终 | 设备当前是否被持权 |
| `controlRole` | string | 始终 | 当前控制角色（取值如 `"external_high_level"`） |
| `controller` | string | 始终 | 当前持权方的 `controller` token；未持权时为空串 |
| `controlMode` | string | 当前固件 | 当前控制模式名；早期固件可能缺失 |

```jsonc
{
  "controlled":  true,
  "controlRole": "external_high_level",
  "controller":  "0xGUefQ7T9VWxulv",
  "controlMode": "external_high_level"
}
```

**触发时机**

- 任意客户端 `takeMotionControl` 成功
- 任意客户端 `releaseMotionControl`
- 设备侧租约超时自动收权
- 设备侧因故障强制释放

**`controlled == false` 时的判断**：如果本端是原持权方（本端记录的 `controller` 与 `payload.controller` 不匹配，或 `payload.controller` 为空串），应立即按 [§3.3.1](#331-会话管理) 走"失权处理"流程。

---

### 4.4 错误码

> RPC 协议层 code（`System_Response_.code`）见 [§1.3.1](#131-rpc-通道请求-应答) "code 取值"。

#### 4.4.1 业务层 payload.code

业务 errno，响应 payload 中始终存在；`0` 表示业务成功，非 0 表示业务失败（须同时配合 `payload.result == false`）。

| code（hex） | code（dec） | 名称 | 含义 | 典型触发 |
|---|---|---|---|---|
| `0x01` | 1 | paramsTypeError | 参数类型错误 | 所有方法 |
| `0x02` | 2 | paramsDeletion | 参数缺失 | 所有方法 |
| `0x03` | 3 | paramsParseError | 参数解析错误 | 所有方法 |
| `0x04` | 4 | paramsOutRange | 参数超出范围 | `setCameraLightBrightness`（亮度 > 100） |
| `0x05` | 5 | paramsExpired | 参数过期（如带时效令牌） | 持权类调用 |
| `0x06` | 6 | paramsIllegal | 参数非法 | `startMotionAction`（action 名拼错） |
| `0x07` | 7 | interfaceNotFound | 接口未实现（路由层找不到） | 旧固件未注册的方法 |
| `0x08` | 8 | outOfDeviceCaps | 超出设备能力 | `startMotionAction`（动作不在 capabilities） |
| `0x09` | 9 | operationTempNotAllow | 操作当前不允许 | `emergencyStopMotion` 后冷却期 |
| `0x0A` | 10 | methodNotSupport | 方法不支持 | 设备 / 固件版本旧 |
| `0x0B` | 11 | deviceNoCapability | 设备无对应能力 | 某些机型不支持特定动作 |
| `0x0C` | 12 | operateUnsupport | 操作不支持 | 配置不允许的操作 |
| `0x0E` | 14 | methodNotImpl | 方法未实现（handler 是协议占位） | 部分系统设置类 |
| `0x0F` | 15 | interStatusInvalid | 内部状态错误 | 设备状态机异常 |
| `0x10` | 16 | operatorInvalid | 操作者非法 | `renewMotionControl`（租约已过期） |
| `0x12` | 18 | operateTimeout | 操作超时 | 设备内部超时 |
| `0x13` | 19 | deviceInBusy | 设备正忙 | 并发请求过多 |
| `0x19` | 25 | serviceNotReady | 服务未就绪 | 设备启动早期 |
| `0x1A` | 26 | serviceOffline | 服务不在线 | 子服务挂掉 |
| `0x1C` | 28 | noOperationPerm | 无操作权限 | `payload.call.clientId != controller` |
| `0x1D` | 29 | controlWasSeized | 控制权被夺 | `takeMotionControl`（被他人持有）或本端被抢权 |
| `0x1E` | 30 | deviceIsNotBound | 设备未绑定 | 设备未完成激活 |
| `0x1F` | 31 | devIoNodeOccupied | 设备节点被占用 | 同一物理端口被多服务占用 |
| `0x21` | 33 | fileNotExist | 文件不存在 | `deleteAudioFile` / `startPlayList`（id 错） |
| `0x22` | 34 | openFileFailed | 打开文件失败 | 同上 |
| `0x23` | 35 | writeFileFailed | 写文件失败 | 音频上传场景 |
| `0x28` | 40 | dataResourceEmpty | 数据资源为空 | `getAudioPlayList`（无音频文件） |

#### 4.4.2 电机 error 子码

`MotionObserved_.motor[i].error` 字段（uint8）取值：

| code（dec） | 名称 | 含义 | 严重性 |
|---|---|---|---|
| `0` | motorNormal | 正常 | — |
| `1` | motorPreDriver | 预驱故障（驱动级硬件异常） | 高 |
| `2` | motorEcodeError | 编码器故障 | 高 |
| `3` | motorOverSpeed | 过速 | 高 |
| `4` | motorOverTempe | 过温（短时可恢复） | 中 |
| `5` | motorOverCurrent | 过流 | 高 |
| `6` | motorOverVoltage | 过压 | 高 |
| `59` | motorPGAbnormality | PG 异常 | 高 |
| `60` | motorHWUndervoltage | 硬件欠压 | 高 |
| `63` | motorCommError | 通信错误 | 高 |
| `64` | motorControlOffline | 控制板离线 | 严重（电机失联） |
| `65` | controlMotorNotEnable | 未使能 | 中 |
| `66` | motorControlNotReady | 控制未就绪 | 中 |
| `67` | motorControlUpgrade | 升级中 | 中 |
| `68` | motorNoCalibrated | 未标定 | 严重（配置问题） |
| `69` | motorURDFNotMapped | 标定丢失 | 严重（配置问题） |

按严重性归类：

- **可恢复**：`motorOverTempe`（过温，等冷却后恢复）
- **需停机**：`motorPreDriver` / `motorEcodeError` / `motorOverSpeed` / `motorOverCurrent` / `motorOverVoltage` / `motorPGAbnormality` / `motorHWUndervoltage` / `motorCommError`
- **配置 / 失联**：`motorControlOffline` / `controlMotorNotEnable` / `motorControlNotReady` / `motorControlUpgrade` / `motorNoCalibrated` / `motorURDFNotMapped`

出现**任何**非 0 子码，建议立即 `emergencyStopMotion` 并提示运维介入。

---

## 附录 A · 客户端自检清单

接入完成前，请确认客户端实现满足以下检查项：

**DDS 层**
- [ ] DDS Domain ID 与设备一致
- [ ] 6 个 endpoint 已建立且 publication / subscription 匹配
- [ ] 每个通道的 QoS 与本协议 [§1.3](#13-三类通道) 完全一致（含 `DATA_REPRESENTATION` 与 `TYPE_CONSISTENCY_ENFORCEMENT`）
- [ ] `Header` 类型标 `@final` 注解

**RPC 信封层**
- [ ] `System_Request_.service` 固定填 `"robotAppService"`
- [ ] `System_Request_.device_id` 必填非空
- [ ] `Header.clientId` 进程内唯一（启动时随机 uint64）
- [ ] `Header.requestId` session 内单调递增、永不重复
- [ ] 响应匹配（clientId + requestId + device_id，[§1.3.1](#131-rpc-通道请求-应答)）

**业务层**
- [ ] 业务成功满足双层判定（`response.code==0` ∧ `payload.result==true`，[§2.1.3](#213-业务成败双层判定)）
- [ ] 取控成功后所有 RPC 的 `payload.call.clientId` 切换为 `controller` 字段值
- [ ] 释权后切回自定义 clientId
- [ ] 动作列表通过 `getMotionCapabilities` 动态获取，不硬编码

**TRC 通道**
- [ ] `RemoteControl_.controller` 字段填 `rawActionId`（uint64），**不是** `controller` token（string）
- [ ] 帧推送频率 50–100 Hz
- [ ] 停止时主动下发一帧全 0

**续约**
- [ ] 后台续约线程已启动，频率 `clamp(leaseTimeout/3, 200ms, 10s)`
- [ ] 续约失败立即视为失权 + 触发失权处理流程

**运控观测量**
- [ ] 先订阅 reader 再发 `setMotionObservedEnable(motionEnable=true)`（顺序敏感）
- [ ] 关闭时先发 `setMotionObservedEnable(motionEnable=false)` 再销毁 reader

**事件**
- [ ] 事件回调内校验 `magic == 0x53425645`
- [ ] 容器模式事件（`robotServer.host.event`）按 `payload.event` 二次分发
- [ ] 直通模式事件（`robotServer.control.status`）原样传给业务 handler
- [ ] 未知 `EventMessage_.topic` 值 宽容透传（向前兼容设备新增事件）

**状态机**
- [ ] 实现 [§3.1](#31-控制权生命周期) 列出的控制权生命周期流程（取控 → 业务 → 续约 → 释放）
- [ ] 每个 RPC 的"是否需要控制权"（见 [§3.2](#32-rpc-方法列表) 方法列表）已在客户端代码里强校验
- [ ] 错误码按附录 D 决策表处理，不静默忽略

---

## 附录 B · Python 接入要点

适用于 `cyclonedds-python` 等 Python DDS 绑定。

### B.1 接入步骤

1. **声明 IDL 类型**：按 [§1.3](#13-三类通道) 给出的 struct 定义，用 `cyclonedds.idl.IdlStruct` 子类化，`typename=` 显式传入完整模块路径
2. **建 DataWriter / DataReader**：按每通道的 QoS 表逐项配置
3. **取控后切换 `clientId`**：所有持权 RPC 的 `payload.call.clientId` 必须填响应里的 `controller`
4. **后台续约线程**：周期 `clamp(leaseTimeout/3, 200ms, 10s)`；失败立即按 [§3.3.1](#331-会话管理) 失权处理流程
5. **事件回调**：先校验 `magic == 0x53425645`，再按 `EventMessage_.topic` 字段值分发

### B.2 cyclonedds-python 实现注意点

| 注意点 | 说明 |
|---|---|
| `@final` 注解 | 必须从 `cyclonedds.idl.annotations` 导入；与 `@dataclass` 同时使用，写在 dataclass 之后 |
| `typename=` 必传 | 否则会生成包含模块路径的默认类型名，与设备端不匹配 |
| `Reliability.Reliable(...)` | 是工厂，必须传 `max_blocking_time`；`BestEffort` 是单例 |
| `DataRepresentation` Policy | 0.10.x 版本用 `use_cdrv0_representation` / `use_xcdrv2_representation` 双 bool；不同小版本 API 有差异 |
| Type discovery | 默认会发出 type info；若与设备的 cyclonedds C++ 版本不匹配会拒绝，可通过 `cls.__idl__.fill_type_data` 关闭 |
| 字段命名 | IDL 是 camelCase（如 `clientId`）；切勿 Python 化重命名为 snake_case，否则 wire 不匹配 |

### B.3 快速验证链路

接入完成后建议先调一次 `getMotionCapabilities`（无须持权）验证 DDS 链路 / IDL / QoS / `device_id` 全部对齐：

- 收到 `code=0` 且 `result=true` → 链路通
- `code=4` 且 `device_id` 字段非空 → `device_id` 写错了，按响应回填的 SN 改回
- 5 秒无响应 → Domain 不一致 / 多播路由不通 / topic 名拼错 / QoS 不匹配

---

## 附录 C · C++ 接入要点

C++ 客户端可选任一 OMG DDS 实现：Eclipse Cyclone DDS C++ / RTI Connext / eProsima Fast DDS / OpenDDS。

### C.1 IDL 文件组织

本协议涉及的 IDL 文件由 [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) 仓库发布，位于该仓库根目录的 `idl/` 下。

文件清单与 include 关系：

| 文件 | 包含类型 | 依赖 |
|---|---|---|
| `Request.idl` | `Header` | — |
| `RPCMessage.idl` | `System_Request_` / `System_Response_` | `Request.idl` |
| `EventMessage.idl` | `EventMessage_` | `Request.idl` |
| `MotorState.idl` | `MotorHeader` + 常量 `MAX_MOTOR_NUM` | — |
| `MotionObserved.idl` | `Vector3f` / `Quaternionf` / `IMUState` / `MotorObserved` / `PowerObserved` / `MotionObserved_` | `MotorState.idl` |
| `SensorObserved.idl` | `GPSSignalLevel` / `GEOGPoint` / `GPSFrame` / `UWBRawObserved` / `SensorObserved_` | — |
| `RemoteControl.idl` | `RemoteControl_` | — |

直接从该目录拷贝 .idl 文件到项目，用对应 DDS 实现的 IDL 编译器生成 C++ 类型（Cyclone DDS C++ 用 `idlc -l cxx`；RTI 用 `rtiddsgen`；Fast DDS 用 `fastddsgen`）。

### C.2 接入要点

- **IDL `@final` 注解**：须开启 IDL 编译器的 XTYPES 支持；具体开关随实现而异，多数支持以 "IDL4" 或 "XTYPES" 为名的命令行选项
- **JSON 序列化**：C++ 标准库无 JSON 支持，推荐 `nlohmann/json` 或 `rapidjson`
- **续约线程**：用 `std::thread` + `std::condition_variable` 实现，周期 `clamp(leaseTimeout/3, 200ms, 10s)`
- **事件订阅回调**：和 RPC 同 participant 但独立 reader；回调内**不要做长时间业务处理**，否则会阻塞 DDS 内部线程
- **TRC 高频写**：用独立 writer + `BEST_EFFORT` QoS；不要复用 RPC writer，QoS 不兼容
- **错误码常量**：按 [§4.4](#44-错误码) 表生成 `enum class DeviceErrorCode : uint32_t { ... }`，便于业务层 switch 处理

### C.3 不同 DDS 实现的注意点

| 实现 | 注意点 |
|---|---|
| **Eclipse Cyclone DDS C++（ddscxx）** | 设备端实现，对接最自然；XTYPES 注解默认支持；命名空间 `org::eclipse::cyclonedds::dds::*` |
| **RTI Connext** | XTYPES 完整支持；多播 discovery 默认开启；QoS API 风格为 `DDS_*Qos` 结构体；商业授权 |
| **eProsima Fast DDS** | RTPS / simple discovery 默认与 Cyclone DDS 互通；XTYPES 注解需在 IDL 编译器开启对应选项 |
| **OpenDDS** | 默认 InfoRepo discovery，与 Cyclone DDS 互通需切到 RTPS discovery；XTYPES 需 build 时显式启用 |

切换 DDS 实现时，按以下顺序验证互通：

1. Domain ID 一致
2. SPDP / SEDP 多播能否互通（同一二层网络或多播路由可达）
3. IDL 类型 `typename` + 模块路径一致
4. 各通道的 QoS 全部匹配（含 `DATA_REPRESENTATION` / `TYPE_CONSISTENCY_ENFORCEMENT`；RPC 通道再加 `max_blocking_time`）
5. 跑一次 `getMotionCapabilities` 烟囱测试，按附录 B.3 判定结果

---

## 附录 D · 错误处理决策表与静默失败排查

### D.1 错误处理决策表

按错误来源查处理动作。涉及控制权的错误仅在已持权时有意义，须走 [§3.3.1](#331-会话管理) 失权处理流程。

| 错误来源 | 处理动作 |
|---|---|
| **本地超时**（5s 内无响应） | 用新 `requestId` 重试，连续 3 次失败熔断上报 |
| **RPC code=1 / 2**（设备异常） | 不可重试，上报业务层；持权时须释放控制权 |
| **RPC code=3 / 4 / 6 / 7**（请求格式错） | 不可重试，按 code 含义检查 `method` / 信封 / `service` / JSON 拼写 |
| **RPC code=5**（服务未就绪） | 退避 1–3s 重试 |
| **payload 0x01–0x08**（参数类） | 不可重试，检查 `params` 必填字段、类型、值域 |
| **payload 0x09**（临时不允许） | 退避 3–5s 重试（典型场景：`emergencyStopMotion` 冷却期） |
| **payload 0x0A / 0x0E**（不支持 / 未实现） | 不可重试 |
| **payload 0x13**（设备忙） | 退避 500ms 重试 |
| **payload 0x10 / 0x1C / 0x1D**（持权异常） | 走失权处理（[§3.3.1](#331-会话管理)） |
| **事件 `controlled=false`** 且本端为原持权方 | 同上 |
| **`motor[i].error` ≠ 0** | 立即 `emergencyStopMotion` + 告警 |
| **TRC 帧无效果**（`queryMotionState` 验证） | 排查 `RemoteControl_.controller` 是否填 `rawActionId`（uint64），以及当前是否持权 |
| **DDS discovery 长时间未收敛** | 检查 Domain / 多播路由 / `device_id` |

**重试时序**：第 1 次 50ms / 第 2 次 500ms / 第 3 次 2s；连续 3 次失败熔断上报。

### D.2 静默失败排查清单

设备完全无响应（错误码层面无可识别信号）时，按下表核对：

| 现象 | 可能原因 |
|---|---|
| RPC 完全收不到响应 | Domain 不一致 / 多播路由不通 / `device_id` 写空 / topic 名拼错 / QoS 不匹配 |
| 收到响应但 device_id 不匹配 | 同网多设备，响应被串扰；检查响应 `device_id` 是否等于请求 `device_id` |
| TRC 帧无效果 | `RemoteControl_.controller` 未填 `rawActionId`（错填了 `controller` 字符串） / 未持权 / 设备未启用 TRC |
| 运控观测量不推 | 未调 `setMotionObservedEnable(motionEnable=true)` / reader 在 enable 之后才订阅（丢前几帧） |
| 事件收不到 | DDS topic `rt/robotServer/Event` 拼错 / `magic` 常量写错（应 `0x53425645`） / 自端 loop-back 过滤误把对端事件也滤掉 |
