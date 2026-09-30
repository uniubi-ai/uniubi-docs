# ROS 2 MSG/SRV to DDS IDL mapping specification

**English** | [简体中文](ros2_dds_interop_overview.zh-CN.md)

This document explains how ROS 2 `.msg` and `.srv` interface files map to DDS IDL for native OMG DDS integration, including DDS topic names, DDS type names, and request/response correlation rules.

ROS 2 APIs normally hide DDS details. Native DDS integration must implement the wire contract used by the selected ROS 2 RMW. This document covers standard message publish/subscribe and service request/reply traffic.

## Overall process

From ROS 2 interface to DDS native access, it is recommended to process in the following order:

1. Confirm the visible name of ROS 2: topic name or service name, including the complete name after namespace/remap.
2. Confirm the package, subdirectory and file name of the interface file: `.msg` or `.srv`.
3. Generate DDS IDL according to the mapping rules from ROS 2 to DDS IDL.
4. Generate native language type support using the target DDS's IDL compiler.
5. Create a DDS topic according to ROS 2 DDS naming rules.
6. Configure reader/writer according to ROS 2 default QoS or interface convention.

Flow:

```text
ROS 2 .msg/.srv
      |
      v
ROS 2 IDL / DDS IDL mapping
      |
      v
DDS IDL files
      |
      v
DDS type-support code
      |
      v
dds_create_topic + dds_create_reader/writer
```

## Naming rules

Under the default ROS namespace convention, ROS 2 names are mapped to DDS topic names:

| ROS 2 entity | DDS topic name |
|---|---|
| topic `/<topic_name>` | `rt/<topic_name>` |
| service `/<service_name>` request | `rq/<service_name>Request` |
| service `/<service_name>` reply | `rr/<service_name>Reply` |

Things to note:

- ROS 2 names will first go through namespace, remap, relative/absolute name resolution, and then enter the DDS layer.
- The native DDS side should use the full resolved name, not just the short name from the source code.
- By default, ordinary topics use the `rt` prefix, and services use the `rq` / `rr` prefix.
- If `avoid_ros_namespace_conventions` is enabled on the ROS 2 end, the above prefix rules will be bypassed; it is recommended not to enable this option for external interoperability interfaces.

Example:

| ROS 2 name | DDS topic |
|---|---|
| `/robot/status` | `rt/robot/status` |
| `/robot/reset` request | `rq/robot/resetRequest` |
| `/robot/reset` reply | `rr/robot/resetReply` |

## Robot data topics

The robot's native DDS data channels follow the ROS 2 naming convention above: an `rt/` topic prefix and a `<module>::msg::dds_::<Type>_` type name. See [`uniubi_robot_dds_api.md`](uniubi_robot_dds_api.md) for complete IDL definitions and field dimensions. The following table lists the wire-level names required for native DDS integration:

| DDS topic | Direction | DDS type | IDL file | Purpose |
|---|---|---|---|---|
| `rt/motion/trc` | Client → Device | `uniubi::msg::dds_::RemoteControl_` | `RemoteControl.idl` | TRC real-time remote control frame |
| `rt/motion/observed` | Device → Client | `uniubi::msg::dds_::MotionObserved_` | `MotionObserved.idl` | Motion observations (IMU / motor / power) |
| `rt/sensor/observed` | Device → Client | `uniubi::msg::dds_::SensorObserved_` | `SensorObserved.idl` | Sensor observations (GPS / UWB / Walk odometer) |
| `rt/robotServer/Event` | Device → Client | `uniubi::msg::dds_::EventMessage_` | `EventMessage.idl` | Device actively pushes events |

> Walk odometry is carried in the `odom` field of `rt/sensor/observed`. `position[2]` and `velocity[2]` are reserved for 3-D compatibility and are currently fixed at `0`. `rt/robotServer/Event` uses fixed `BEST_EFFORT` / `KEEP_LAST` / `VOLATILE` QoS. The reliability, history, and durability of `trc`, `observed`, and `sensor` are defined by their respective business contracts; see §1.3 of `uniubi_robot_dds_api.md`. The RPC channel (`rq/robotServerRequest` / `rr/robotServerReply`) does not use the generic RMW service header described later. It uses `uniubi::dds_::Header{ uint64 clientId; uint64 requestId }` and correlates requests and replies by `clientId` and `requestId`; see `uniubi_robot_dds_api.md`.

## General principles of type mapping

The ROS 2 interface path will be mapped to the DDS IDL module:

```text
<package>/msg/<Type>.msg  ->  <package>::msg::dds_::<Type>_
<package>/srv/<Name>.srv  ->  <package>::srv::dds_::<Name>_Request_
                              <package>::srv::dds_::<Name>_Response_
```

When corresponding to an IDL file, the common structure is:

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

Type Notes:

- Structure names usually have a trailing underscore, such as `String_`, `Reset_Request_`.
- Field names must be based on the actual generated DDS IDL; do not infer them based on ROS 2 C++ field names.
- The generator may adjust field names if they conflict with IDL keywords.
- Use the complete DDS module path for the nested message field.
- The boundaries of arrays, sequences, and strings must be consistent with the ROS 2 interface.
- There may be differences in details between different ROS 2 releases or different RMWs; when publishing the interface to the outside world, the target ROS 2/RMW combination should be fixed, and the actual exported DDS IDL shall prevail.

## File-level correspondence

It is recommended to organize DDS IDL files according to the ROS 2 interface path so that include and type names can be consistent:

| ROS 2 interface file | DDS IDL file | DDS type |
|---|---|---|
| `<package>/msg/<Type>.msg` | `<package>/msg/<Type>.idl` | `<package>::msg::dds_::<Type>_` |
| `<package>/srv/<Service>.srv` | `<package>/srv/<Service>.idl` | `<package>::srv::dds_::<Service>_Request_` / `<Service>_Response_` |
| service header | `ros_service.idl` or the equivalent header IDL exported by the target RMW | `ros_service::msg::dds_::Header_` |

Nested types need to be explicitly included in the DDS IDL. For example, if a field type comes from `builtin_interfaces/msg/Time.msg`, the corresponding `builtin_interfaces/msg/Time.idl` should be included in the DDS IDL, and the field type is written as:

```idl
builtin_interfaces::msg::dds_::Time_ stamp;
```

The request/response structure of service needs to include the IDL where the service header is located. The module name of the header must be consistent with the DDS type actually used by both access parties; if the header module name exported by the target RMW is different, the target RMW should prevail, and you cannot just change the include file name.

## `.msg` to DDS IDL

The `.msg` file corresponds to a DDS topic payload structure. Mapping steps:

1. The package where the file is located becomes the outermost module.
2. The `msg` directory becomes `module msg`.
3. Add `module dds_`.
4. The file name becomes the structure name, and a trailing underscore is appended.
5. Fields are mapped to IDL fields by ROS 2 type.
6. The message structure used for topic publishing and subscription can be marked `@topic`.

Example: ROS 2 `.msg`

```text
# std_msgs/msg/String.msg
string data
```

Corresponding DDS IDL:

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

Native DDS uses the DDS layer topic name and DDS type description when creating a topic:

```text
DDS topic name: rt/<topic_name>
DDS type:       std_msgs::msg::dds_::String_
```

## `.srv` to DDS IDL

The `.srv` file is separated into request and response by `---`. The DDS layer requires two structures and two DDS topics:

```text
<ServiceName>_Request_
<ServiceName>_Response_
```

DDS topic naming of service:

```text
rq/<service_name>Request    // client -> server
rr/<service_name>Reply      // server -> client
```

### Request/Response structure

The business fields of ROS 2 service come from the `.srv` file:

```text
# <Package>/srv/<ServiceName>.srv
<request fields>
---
<response fields>
```

When mapped to DDS IDL, request and response enter `module <package>::srv::dds_` respectively. The service wire type used for direct DDS intercommunication must include the request matching header, and the header is placed before the business field:

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

Example: ROS 2 `.srv`

```text
# example_interfaces/srv/AddTwoInts.srv
int64 a
int64 b
---
int64 sum
```

Corresponding DDS IDL:

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

The actual field name needs to be based on the DDS IDL generated by the target ROS 2/RMW; some generated results may append underscores to the field name.

### Service matching rules

ROS 2 service client relies on request headers to match responses. The native DDS side must comply with:

1. Before the client sends the request, `seq` of this request is generated.
2. The client writes the GUID of its own request writer into `header.writer_guid`.
3. The client writes the request sequence number into `header.seq`.
4. After the server processes the request, the response must copy the request header as it is.
5. After the client receives the response, it uses `writer_guid + seq` to determine whether the response belongs to this request.

If the response header is not backfilled, even if the ROS 2 client receives the DDS sample, it cannot associate it with the pending request.

## Basic type mapping

Correspondence between common ROS 2 field types and DDS IDL:

| ROS 2 types | DDS IDL types |
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

Complex type fields use the full DDS type name. For example:

```idl
builtin_interfaces::msg::dds_::Time_ stamp;
```

If `.msg` / `.srv` references other interfaces, the IDL file corresponding to `#include` is required in the DDS IDL.

## QoS Considerations

DDS endpoint matching follows the requested/offered compatibility relationship. ROS 2 default QoS can be used as a default reference for the native DDS side:

| Scene | HISTORY | RELIABILITY | DURABILITY |
|---|---|---|---|
| Common topic Default QoS | `KEEP_LAST, depth=10` | `RELIABLE` | `VOLATILE` |
| sensor data QoS | `KEEP_LAST, depth=5` | `BEST_EFFORT` | `VOLATILE` |
| service default QoS | `KEEP_LAST, depth=10` | `RELIABLE` | `VOLATILE` |

Common incompatibilities:

| Question | Result |
|---|---|
| reader requests `RELIABLE`, writer only provides `BEST_EFFORT` | does not match or does not deliver |
| reader requests `TRANSIENT_LOCAL`, writer only provides `VOLATILE` | does not match or does not deliver |
| The type names are the same but the field layout is inconsistent | Discovery may fail or the sample cannot be deserialized |
| service only matches request or only reply | service call cannot be completed |

Don’t just look at discovery when troubleshooting. Just because the endpoint can be seen in the DDS graph does not mean that the QoS and type are necessarily compatible.

## Integration checklist

| Check items | Must-check contents |
|---|---|
| Domain | Is the DDS Domain consistent with ROS 2 `ROS_DOMAIN_ID` |
| Name | Is the full name of ROS 2 after namespace/remap confirmed |
| DDS topic | Whether to use `rt` / `rq` / `rr` prefix and correct suffix |
| IDL module | package, `msg`/`srv`, `dds_` three-layer module is correct |
| Structure name | Whether to use trailing underscore form |
| Field | Field name, field order, array/sequence/string boundaries are consistent |
| include | Whether the nested type includes the corresponding IDL |
| service header | whether request/response contains and echoes header |
| QoS | reliability, durability, history/depth are compatible with ROS 2 peers |
| Type support | Whether to use the same DDS IDL to generate the type support used by reader/writer |
