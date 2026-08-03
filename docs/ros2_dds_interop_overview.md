# ROS 2 MSG/SRV 到 DDS IDL 的映射规范

本文说明使用 OMG DDS 原生接口接入 ROS 2 时，如何把 ROS 2 的 `.msg`、`.srv` 接口文件对应到 DDS IDL 文件，以及由此得到 DDS topic 名、DDS 类型名和请求/响应匹配规则。

ROS 2 的上层 API 会隐藏 DDS 细节；原生 DDS 接入时，需要显式使用 ROS 2 RMW 在 DDS 层使用的 wire contract。本文当前只覆盖普通消息发布订阅和 service 请求响应。

## 总体流程

从 ROS 2 接口到 DDS 原生接入，推荐按以下顺序处理：

1. 确认 ROS 2 可见名称：topic 名或 service 名，包含 namespace/remap 后的完整名称。
2. 确认接口文件：`.msg` 或 `.srv` 所在 package、子目录和文件名。
3. 按 ROS 2 到 DDS IDL 的映射规则生成 DDS IDL。
4. 使用目标 DDS 的 IDL 编译器生成本语言类型支持。
5. 按 ROS 2 DDS 命名规则创建 DDS topic。
6. 按 ROS 2 默认 QoS 或接口约定配置 reader/writer。

示意：

```text
ROS 2 .msg/.srv
      |
      v
ROS 2 IDL / DDS IDL 映射
      |
      v
DDS IDL 文件
      |
      v
DDS 类型支持代码
      |
      v
dds_create_topic + dds_create_reader/writer
```

## 命名规则

默认 ROS namespace convention 下，ROS 2 名称会映射为 DDS topic 名：

| ROS 2 实体 | DDS topic 名 |
|---|---|
| topic `/<topic_name>` | `rt/<topic_name>` |
| service `/<service_name>` request | `rq/<service_name>Request` |
| service `/<service_name>` reply | `rr/<service_name>Reply` |

注意事项：

- ROS 2 名称会先经过 namespace、remap、相对/绝对名解析，再进入 DDS 层。
- 原生 DDS 端应使用解析后的完整名称，不要只使用源码中的短名。
- 默认情况下普通 topic 使用 `rt` 前缀，service 使用 `rq` / `rr` 前缀。
- 如果 ROS 2 端启用 `avoid_ros_namespace_conventions`，上述前缀规则会被绕过；对外互通接口建议不要启用该选项。

示例：

| ROS 2 名称 | DDS topic |
|---|---|
| `/robot/status` | `rt/robot/status` |
| `/robot/reset` request | `rq/robot/resetRequest` |
| `/robot/reset` reply | `rr/robot/resetReply` |

## 本机器人数据 topic 一览（具体映射）

本机器人的原生 DDS 数据通道遵循上述 ROS 2 命名约定（`rt/` 前缀 + `<module>::msg::dds_::<Type>_` 类型名）。完整 IDL 与字段量纲见 [`uniubi_robot_dds_api.md`](uniubi_robot_dds_api.md)，下表给出 ROS 2 原生接入时需要的 wire 名称：

| DDS topic | 方向 | DDS 类型 | IDL 文件 | 用途 |
|---|---|---|---|---|
| `rt/motion/trc` | 客户端 → 设备 | `uniubi::msg::dds_::RemoteControl_` | `RemoteControl.idl` | TRC 实时遥控帧 |
| `rt/motion/observed` | 设备 → 客户端 | `uniubi::msg::dds_::MotionObserved_` | `MotionObserved.idl` | 运控观测量（IMU / 电机 / 电源）|
| `rt/motion/odometry` | 设备 → 客户端 | `uniubi::msg::dds_::MotionOdometry_` | `MotionOdometry.idl` | Walk 模型平面里程计 |
| `rt/sensor/observed` | 设备 → 客户端 | `uniubi::msg::dds_::SensorObserved_` | `SensorObserved.idl` | 传感器观测量（GPS / UWB）|
| `rt/robotServer/Event` | 设备 → 客户端 | `uniubi::msg::dds_::EventMessage_` | `EventMessage.idl` | 设备主动推送事件 |

> `rt/motion/odometry` 固定使用 `BEST_EFFORT` / `KEEP_LAST, depth=1` / `VOLATILE`；`position[2]` 和 `velocity[2]` 是三维兼容保留字段，当前固定为 `0`，不代表高度或垂直速度。`rt/robotServer/Event` 固定 `BEST_EFFORT` / `KEEP_LAST` / `VOLATILE`；`trc` / `observed` / `sensor` 三路的 reliability / history / durability 由具体业务约定（见 `uniubi_robot_dds_api.md` §1.3）。RPC 通道（`rq/robotServerRequest` / `rr/robotServerReply`）**不**复用本文后述的通用 RMW service header，而是自定义 `uniubi::dds_::Header{ uint64 clientId; uint64 requestId }`，按 `clientId` / `requestId` 关联请求与响应，详见 `uniubi_robot_dds_api.md`。

ROS 2 消息字段使用 snake_case，对应 `uniubi/msg/MotionOdometry.msg`：

```text
float32[3] position
float32[3] velocity
float32 yaw
float32 yaw_speed
uint64 timestamp_us
uint32 epoch
bool valid
```

`position[0:2]` 是 motionServer 已结合 IMU yaw 积分得到的当前 `epoch` 世界系累计位姿，`velocity[0:2]` 是机器人本体系模型预测速度。里程计值仅在 Walk 模式有效，调用方直接消费 `position` / `yaw`，不要再次积分。进入 Walk 或显式 reset 时累计位姿清零且 `epoch` 递增；从 Walk 切换到任意其他动作时，`position` / `yaw` 立即清零、`epoch` 递增、`valid=false`。只有 `valid=true` 的帧可用于更新平面定位。完整字段单位、发布频率与生命周期语义见 [`uniubi_robot_dds_api.md`](uniubi_robot_dds_api.md#walk-模型里程计-motionodometry_)。

## 类型映射总则

ROS 2 接口路径会映射为 DDS IDL module：

```text
<package>/msg/<Type>.msg  ->  <package>::msg::dds_::<Type>_
<package>/srv/<Name>.srv  ->  <package>::srv::dds_::<Name>_Request_
                              <package>::srv::dds_::<Name>_Response_
```

对应到 IDL 文件时，常见结构为：

```idl
module <package> {
  module msg_or_srv {
    module dds_ {
      struct <TypeName>_ {
        ...
      };
    };
  };
};
```

类型注意事项：

- 结构体名通常带尾部下划线，例如 `String_`、`Reset_Request_`。
- 字段名必须以实际生成的 DDS IDL 为准；不要按 ROS 2 C++ 字段名自行推断。
- 如果字段名与 IDL 关键字冲突，生成器可能会调整字段名。
- nested message 字段要使用完整 DDS module 路径。
- 数组、sequence、string 的边界必须与 ROS 2 接口一致。
- 不同 ROS 2 发行版或不同 RMW 可能存在细节差异；对外发布接口时应固定目标 ROS 2/RMW 组合，并以实际导出的 DDS IDL 为准。

## 文件级对应关系

建议按 ROS 2 接口路径组织 DDS IDL 文件，便于 include 和类型名保持一致：

| ROS 2 接口文件 | DDS IDL 文件 | DDS 类型 |
|---|---|---|
| `<package>/msg/<Type>.msg` | `<package>/msg/<Type>.idl` | `<package>::msg::dds_::<Type>_` |
| `<package>/srv/<Service>.srv` | `<package>/srv/<Service>.idl` | `<package>::srv::dds_::<Service>_Request_` / `<Service>_Response_` |
| service header | `ros_service.idl` 或目标 RMW 导出的等价 header IDL | `ros_service::msg::dds_::Header_` |

嵌套类型需要在 DDS IDL 中显式 include。例如某个字段类型来自 `builtin_interfaces/msg/Time.msg`，则 DDS IDL 中应 include 对应的 `builtin_interfaces/msg/Time.idl`，字段类型写为：

```idl
builtin_interfaces::msg::dds_::Time_ stamp;
```

service 的 request/response 结构体需要 include service header 所在 IDL。header 的 module 名必须与接入双方实际使用的 DDS 类型一致；如果目标 RMW 导出的 header module 名不同，应以目标 RMW 为准，不能只改 include 文件名。

## `.msg` 到 DDS IDL

`.msg` 文件对应一个 DDS topic payload 结构体。映射步骤：

1. 文件所在 package 变成最外层 module。
2. `msg` 目录变成 `module msg`。
3. 增加 `module dds_`。
4. 文件名变成结构体名，并追加尾部下划线。
5. 字段按 ROS 2 类型映射为 IDL 字段。
6. 用于 topic 发布订阅的消息结构体可标注 `@topic`。

示例：ROS 2 `.msg`

```text
# std_msgs/msg/String.msg
string data
```

对应 DDS IDL：

```idl
module std_msgs {
    module msg {
        module dds_ {
            @topic
            struct String_ {
                string data;
            };
        };
    };
};
```

原生 DDS 创建 topic 时使用 DDS 层 topic 名和 DDS 类型描述：

```text
DDS topic name: rt/<topic_name>
DDS type:       std_msgs::msg::dds_::String_
```

## `.srv` 到 DDS IDL

`.srv` 文件由 `---` 分隔为 request 和 response。DDS 层需要两个结构体和两个 DDS topic：

```text
<ServiceName>_Request_
<ServiceName>_Response_
```

service 的 DDS topic 命名：

```text
rq/<service_name>Request    // client -> server
rr/<service_name>Reply      // server -> client
```

### Request/Response 结构体

ROS 2 service 的业务字段来自 `.srv` 文件：

```text
# <Package>/srv/<ServiceName>.srv
<request fields>
---
<response fields>
```

映射到 DDS IDL 时，request 和 response 分别进入 `module <package>::srv::dds_`。用于直接 DDS 互通的 service wire 类型必须包含请求匹配 header，且 header 放在业务字段之前：

```idl
module ros_service {
    module msg {
        module dds_ {
            struct Header_ {
                octet writer_guid[8];
                uint64 seq;
            };
        };
    };
};
```

示例：ROS 2 `.srv`

```text
# example_interfaces/srv/AddTwoInts.srv
int64 a
int64 b
---
int64 sum
```

对应 DDS IDL：

```idl
#include "ros_service.idl"

module example_interfaces {
  module srv {
    module dds_ {
      struct AddTwoInts_Request_ {
        ros_service::msg::dds_::Header_ header;
        int64 a;
        int64 b;
      };

      struct AddTwoInts_Response_ {
        ros_service::msg::dds_::Header_ header;
        int64 sum;
      };
    };
  };
};
```

实际字段名需要以目标 ROS 2/RMW 生成出的 DDS IDL 为准；有些生成结果可能会给字段名追加下划线。

### Service 匹配规则

ROS 2 service client 依赖 request header 匹配响应。原生 DDS 端必须遵守：

1. client 发送 request 前，生成本次请求的 `seq`。
2. client 将自身 request writer 的 GUID 写入 `header.writer_guid`。
3. client 将请求序号写入 `header.seq`。
4. server 处理 request 后，response 必须原样复制 request header。
5. client 收到 response 后，用 `writer_guid + seq` 判断 response 是否属于本次请求。

如果 response header 没有回填，ROS 2 client 即使收到 DDS sample，也无法把它关联到 pending request。

### Uniubi `System.srv` 索引

`uniubi/srv/System.srv` 是 ROS 2 示例客户端使用的 service 接口，不是原生 DDS `RPCMessage.idl` 的逐字段镜像。普通二次开发通常复用 `uniubi_ros2` 示例封装；需要扩展 RPC 时，可在示例客户端封装层补充新的调用方法。

字段边界如下：

- `Header.msg` 来自 `Request.idl`，包含 `client_id` / `request_id`；`System.srv` 不含该 Header 字段。
- `System.srv` 请求和响应都包含 `device_id`。`uniubi_ros2` 示例要求填写目标设备 SN，并将其写入每个请求；robotServer 只响应目标 SN 匹配的请求，ROS 2/RMW 再通过 service request header 关联响应。示例检查响应 `code` 和业务 payload，不额外比较 `response.device_id`。
- 原生 DDS RPC 的完整请求 / 响应规则以 `uniubi_robot_dds_api.md` 为准。

跨链路定位如下：

- ROS 2 示例与调用约定见 `uniubi_ros2/docs/runtime_notes.md`。
- `System.srv` 的接口定义和 IDL 映射边界见 `uniubi_robot_msgs/docs/protocol_notes.md`。
- 原生 DDS RPC 规则见 `uniubi_robot_dds_api.md`。

## 基础类型映射

常见 ROS 2 字段类型到 DDS IDL 的对应关系：

| ROS 2 类型 | DDS IDL 类型 |
|---|---|
| `bool` | `boolean` |
| `byte` | `octet` |
| `char` | `char` |
| `float32` | `float` |
| `float64` | `double` |
| `int8` / `uint8` | `int8` / `uint8` |
| `int16` / `uint16` | `int16` / `uint16` |
| `int32` / `uint32` | `int32` / `uint32` |
| `int64` / `uint64` | `int64` / `uint64` |
| `string` | `string` |
| `string<=N` | `string<N>` |
| `T[]` | `sequence<T>` |
| `T[<=N]` | `sequence<T, N>` |
| `T[N]` | `T field[N]` |

复杂类型字段使用完整 DDS 类型名。例如：

```idl
builtin_interfaces::msg::dds_::Time_ stamp;
```

如果 `.msg` / `.srv` 引用了其他接口，DDS IDL 中需要 `#include` 对应 IDL 文件。

## QoS 注意事项

DDS endpoint 匹配遵循 requested/offered 兼容关系。ROS 2 默认 QoS 可作为原生 DDS 端的默认参考：

| 场景 | HISTORY | RELIABILITY | DURABILITY |
|---|---|---|---|
| 普通 topic 默认 QoS | `KEEP_LAST, depth=10` | `RELIABLE` | `VOLATILE` |
| sensor data QoS | `KEEP_LAST, depth=5` | `BEST_EFFORT` | `VOLATILE` |
| service 默认 QoS | `KEEP_LAST, depth=10` | `RELIABLE` | `VOLATILE` |

常见不兼容：

| 问题 | 结果 |
|---|---|
| reader 请求 `RELIABLE`，writer 只提供 `BEST_EFFORT` | 不匹配或不投递 |
| reader 请求 `TRANSIENT_LOCAL`，writer 只提供 `VOLATILE` | 不匹配或不投递 |
| 类型名相同但字段布局不一致 | 可能 discovery 失败或样本无法反序列化 |
| service 只匹配 request 或只匹配 reply | service 调用无法完成 |

排查时不要只看 discovery。DDS graph 能看到 endpoint，不代表 QoS 和类型一定兼容。

## 对接检查清单

| 检查项 | 必查内容 |
|---|---|
| Domain | DDS Domain 是否与 ROS 2 `ROS_DOMAIN_ID` 一致 |
| 名称 | namespace/remap 后的 ROS 2 全名是否确认 |
| DDS topic | 是否使用 `rt` / `rq` / `rr` 前缀和正确后缀 |
| IDL module | package、`msg`/`srv`、`dds_` 三层 module 是否正确 |
| 结构体名 | 是否使用尾部下划线形式 |
| 字段 | 字段名、字段顺序、数组/sequence/string 边界是否一致 |
| include | 嵌套类型是否包含对应 IDL |
| service header | request/response 是否包含并回显 header |
| QoS | reliability、durability、history/depth 是否与 ROS 2 对端兼容 |
| 类型支持 | 是否用同一份 DDS IDL 生成 reader/writer 使用的类型支持 |
