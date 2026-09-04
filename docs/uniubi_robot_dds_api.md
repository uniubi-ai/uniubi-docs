# Uniubi Quadruped DDS / ROS 2 Direct Integration API

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/uniubi_robot_dds_api.zh-CN.md)

> Intended audience: developers integrating directly with a robot through OMG DDS (Cyclone DDS 0.10.5 recommended) or ROS 2 without using the Uniubi SDK.
> This document describes the underlying protocol contract exposed by the High-level SDK and is aligned with its capabilities.

---

## Table of contents

- [1. Overview and DDS channel integration requirements](#1-overview-and-dds-channel-integration-requirements)
- [1.1 Access method ](#11-access-method)
- [1.2 DDS Basic ](#12-dds-basics)
- [1.3 Category 3 channel ](#13-category-3-channels)
- [1.3.1 RPC channel ](#131-rpc-channel-request-reply)
- [1.3.2 Event channel ](#132-event-channel-active-push-by-device)
- [1.3.3 Data subscription publishing channel ](#133-data-subscription-and-publishing-channel-open-pubsub)
- [1.3.4 Topic Summary ](#134-topic-summary)
- [1.4 Development project template ](#14-development-project-template)
- [2. Business message format specification ](#2-business-message-format-specifications)
- [2.1 RPC message specification ](#21-rpc-message-specification)
- [2.1.1 RPC request payload format ](#211-rpc-request-payload-format)
- [2.1.2 RPC reply payload format ](#212-rpc-reply-payload-format)
- [2.1.3 Double-layer judgment of business success or failure ](#213-two-level-judgment-of-business-success-or-failure)
- [2.2 Event channel ](#22-event-channel)
- [3. Business flow ](#3-business-flow)
- [3.1 Control life cycle ](#31-control-life-cycle)
- [3.2 RPC method list ](#32-rpc-method-list)
- [3.3 Detailed explanation of RPC method ](#33-detailed-explanation-of-rpc-method)
- [3.3.1 Session Management ](#331-session-management)
- [3.3.2 Action control ](#332-action-control)
- [3.3.3 Data reporting ](#333-data-reporting)
- [3.3.4 Status query ](#334-status-query)
- [3.3.5 Audio Control ](#335-audio-control)
- [3.3.6 System Settings ](#336-system-settings)
- [3.4 Real-time Control Frame (TRC)](#34-real-time-control-frame-trc)
- [3.5 Motion Observation Subscription](#35-motion-observation-subscription)
- [3.6 Event reception and distribution ](#36-event-reception-and-distribution)
- [3.7 Close ](#37-close)
- [3.8 Disconnection and multi-terminal ](#38-disconnection-and-multiple-terminals)
- [4. Message format and fields ](#4-message-format-and-fields)
- [4.1 TRC control frame ](#41-trc-control-frame)
- [4.2 Observations ](#42-observations)
- [4.3 Event ](#43-events)
- [4.4 Error code ](#44-error-code)
- [Appendix A · Client self-check list](#appendix-a-client-self-check-list)
- [Appendix B · Python access points](#appendix-b-python-access-points)
- [Appendix C · C++ access points](#appendix-c-c-access-points)
- [Appendix D · Error handling decision table and silent failure troubleshooting](#appendix-d-error-handling-decision-table-and-silent-failure-troubleshooting)

---

## 1. Overview and DDS channel integration requirements

This chapter covers two areas:

1. Scope of application and access method of the agreement ([§1.1](#11-access-method))
2. The channel-layer requirements that a DDS client must follow: core DDS parameters, IDL extensibility, QoS, and the three channel patterns ([§1.2](#12-dds-basics) / [§1.3](#13-category-3-channels)).

This chapter **does not define business-layer names or values**. Values such as `serverName`, `service`, method names, and topics are defined in [§3](#3-business-flow) and [§4](#4-message-format-and-fields). If any channel-layer setting is incompatible, DDS may silently drop samples without reporting an application-level error.

### 1.1 Access method

| Access method | Applicable scenarios |
|---|---|
| **Native OMG DDS** (C/C++/Java/Python/Go) | Use any OMG DDS implementation (Cyclone DDS 0.10.5 / RTI Connext / Fast DDS / OpenDDS) with the IDL and QoS defined by this protocol |
| **ROS 2** | Create DDS topics directly from the IDL without ROS message conversion; Cyclone DDS is recommended for the RMW. See [`ros2_dds_interop_overview.md`](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/ros2_dds_interop_overview.md) for ROS 2 `.msg` / `.srv` naming, type, and QoS mappings |

The two methods are equivalent at the wire level: both publish and subscribe to the same IDL types in the same DDS domain. Only the client framework differs.

### 1.2 DDS Basics

#### Domain/Discovery

- **DDS Domain ID**: fixed at **`42`** (the `host` domain carrying every RPC, event, and data channel in this protocol). The client's DDS profile/runtime must join the same domain or discovery will fail completely.
- **Discovery**: Standard OMG SPDP/SEDP multicast. The client and robot need to be on the same Layer 2 network or reachable via multicast routes; there is no need to manually specify the peer address.
- **Participant number**: One `DomainParticipant` per process is enough, and all topics reuse it

#### DDS profile (Cyclone DDS recommended configuration)

The robot side uses Cyclone DDS to run this business domain. If the client also uses Cyclone DDS, it is recommended to load the following profile (**Just change the network card name of `<NetworkInterface name="...">` according to the deployment environment**):

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
        <!-- Replace name with the client's actual interface (eth0 / enp3s0 / wlan0 ...).
             presence_required="true" fails immediately when the interface is absent. -->
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

**Key field meaning**:

| Fields | Required/Recommended | Description |
|---|---|---|
| `Domain Id="42"` | **Must** be consistent with the robot side | The business domain is fixed at 42 and cannot be changed |
| `<NetworkInterface name="...">` | **It is recommended to specify clearly** | When multiple network cards/cross-network segments/wifi+wired coexist, not specifying may cause DDS to negotiate on the wrong network card; specifying `presence_required="true"` will cause the startup to fail directly when the network card does not exist, avoiding subsequent troubleshooting |
| `<AllowMulticast>true` | Must | Discovery uses multicast; if the network environment completely disables multicast, it needs to be changed to peers list (see the Cyclone DDS document `<Peers>` field) |
| `<MaxMessageSize>65500B` | Recommended | The upper limit of a single UDP packet; if it is too low, it will trigger fragmentation and affect throughput |
| `<SharedMemory><Enable>` | Optional | SHM acceleration between different processes in the same machine; if the client always crosses the network, it can be turned off |

**How ​​the application loads this profile**

| Method | Practice |
|---|---|
| Environment variables | `export CYCLONEDDS_URI=file:///path/to/host_config.xml` before starting the application |
| Code layer | Cyclone DDS API is loaded through `dds_create_domain` or `participant_qos` when creating `DomainParticipant` (refer to Cyclone DDS C/C++ documentation for details) |

> With another OMG DDS implementation such as **RTI Connext, Fast DDS, or OpenDDS**, express the equivalent settings using that implementation's QoS syntax. Cross-implementation interoperability requires **Domain ID 42, multicast discovery, and the common QoS defined later in §1.2** to match.

#### IDL type extensibility (OMG XTYPES)

| Type | Extensibility |
|---|---|
| `Header` | `@final` (explicitly marked, not expandable) |
| Other Business/Envelope Type | Default `@appendable` (new fields are allowed to be appended at the end, deletion or rearrangement is not allowed) |

Client IDL must be consistent with this; some DDS implementations (such as Fast DDS) can cause discovery mismatches if annotations are inconsistent.

#### Other IDL conventions

- All `string` fields are **unbounded** (no upper limit on length).
- All topics are **keyless** (there is no `@key` in IDL, there is only one instance per topic).

#### Common QoS (applies to all channels)

| QoS Policy | Value | Reason for selection |
|---|---|---|
| `DATA_REPRESENTATION` | `[XCDR1, XCDR2]` | Compatible with new and old |
| `TYPE_CONSISTENCY_ENFORCEMENT` | `ALLOW_TYPE_COERCION` | Allow IDL field order differences/increases and decreases |

#### Consequences of QoS mismatch

DDS triggers `RequestedIncompatibleQos`, sample **silently does not deliver** (no error reported). The specific QoS for each channel is described in the respective subsections.

### 1.3 Category 3 channels

There are three types of channels between the device and the client (differentiated by communication mode, not tied to services):

| Channel | Mode | Load form | See details |
|---|---|---|---|
| RPC channel | request-reply | envelope + JSON payload | [§1.3.1](#131-rpc-channel-request-reply) |
| event channel | device → client one-way, with envelope + magic | envelope + JSON payload | [§1.3.2](#132-event-channel-active-push-by-device) |
| Data subscription and publishing channel | One-way pub/sub, open type | IDL structure is directly used as payload | [§1.3.3](#133-data-subscription-and-publishing-channel-open-pubsub) |

#### 1.3.1 RPC channel (request-reply)

Hosts all business request-response class calls.

**Topic naming pattern**

```
rq/${serverName}Request    // Request: client → device
rr/${serverName}Reply      // Reply: device → client
```

`rq/` / `rr/` is a fixed prefix of this protocol (consistent with the ROS 2 naming convention) and cannot be changed; the topic of the request for the RPC channel provided by the developer is `rq/robotServerRequest`, and the topic of the RPC response is `rr/robotServerReply`.

**IDL definition**

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

**Envelope field semantics**

ask:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `header.clientId` | uint64 | Yes | Client id; a unique fixed id for each client |
| `header.requestId` | uint64 | Yes | Request id; monotonically increasing |
| `timestamp` | uint64 | Yes | Debug timestamp |
| `service` | string | Yes | Business routing |
| `device_id` | string | Yes | Target device SN; the device will only respond to RPC requests with SN for itself |
| `method` | string | Yes | Business method name |
| `payload` | string | Yes | Business parameter JSON string |

response:

| Field | Type | Meaning |
|---|---|---|
| `header.clientId` / `header.requestId` | uint64 | Echo request |
| `code` | uint32 | RPC protocol layer code (see the table below for values); `0` = RPC message routing is successful; non-0 indicates an error. For specific errors, please refer to the code value table |
| `timestamp` | uint64 | Debug timestamp |
| `device_id` | string | Device SN; the device will only respond to RPC requests with the SN as its own |
| `payload` | string | Business response JSON string |

**`code` value**

| code | name | meaning | trigger scenario | client action |
|---|---|---|---|---|
| `0` | SUCCESS | Routing successful | handler has returned, the business results can be found in payload | Enter business layer determination ([§2.1.3](#213-two-level-judgment-of-business-success-or-failure)) |
| `1` | TIMEOUT | Framework layer timeout | Device handler internal timeout | No retry; Check device status |
| `2` | SERVER_ERROR | Server error | handler threw exception / internal error | Cannot retry; report |
| `3` | METHOD_NOT_FOUND | Method does not exist | Device does not support requested `method` | Check method / firmware version |
| `4` | INVALID_REQUEST | Illegal request | Missing envelope field/wrong type | Check request structure |
| `5` | SERVER_UNPREPARE | Service not ready | Device startup early | Back off 1–3s and try again |
| `6` | SERVICE_NOT_FOUND | Service does not exist | `service` field value is illegal | Check service spelling |
| `7` | DESERIALIZE_ERROR | Deserialization failed | `payload` is not a valid JSON | Check payload serialization |

**Response matching (protocol level mandatory constraints)**

The client must match the response according to the following two items at the same time. If any one does not match, the response is deemed not to belong to this call and must be discarded:

| Matches | Rules |
|---|---|
| `System_Response_.header.clientId` | == request.`header.clientId` |
| `System_Response_.header.requestId` | == request.`header.requestId` |

- `Header.clientId` is globally unique within the process (random uint64 at startup)
- `Header.requestId` monotonically increases within the session and never repeats
- **Important note: Each request `header.requestId` increases monotonically**

**QoS**

| QoS Policy | Value | Description |
|---|---|---|
| `RELIABILITY` | `RELIABLE` | RPC cannot be lost and relies on DDS retransmission |
| `RELIABILITY.max_blocking_time` | `100 ms` | Prevent the calling thread from being dragged to death by the network |
| `HISTORY` | `KEEP_LAST, depth=10` | Cache the latest 10 samples |
| `DURABILITY` | `VOLATILE` | Not persistent; readers added later will not reissue history |
| `DATA_REPRESENTATION` | `[XCDR1, XCDR2]` | Compatible with new and old |
| `TYPE_CONSISTENCY_ENFORCEMENT` | `ALLOW_TYPE_COERCION` | Allow IDL field order differences/increases and decreases |

The reader/writer of the request and response topic must use exactly the same QoS.

#### 1.3.2 Event channel (active push by device)

Bears business events actively pushed by the device (status changes, control rights changes, etc.). One-way, no retransmission. Different from general pub/sub ([§1.3.3](#133-data-subscription-and-publishing-channel-open-pubsub)): with fixed envelope + `magic` verification + wire/business topic secondary routing.

**Topic naming pattern**

```
rt/${serverName}/Event     // Device → client
```

`rt/` is a fixed prefix of this protocol (consistent with the ROS 2 naming convention) and cannot be changed; the topic for event channels provided to developers is `rt/robotServer/Event`.

**IDL definition**

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
          uint32                magic;       // Fixed at 0x53425645; discard on validation failure
          uint64                timestamp;   // Debug timestamp
          string                topic;       // Business topic; see §4.3 and §4
          string                payload;     // Event JSON string
      };

    };
  };
};
```

**Envelope field semantics**

| Field | Type | Meaning |
|---|---|---|
| `header.clientId` | uint64 | Event source id (generated by device), which can be used to filter the local loop-back |
| `header.requestId` | uint64 | Device internal event sequence number |
| `magic` | uint32 | Protocol check constant, fixed = `0x53425645` (ASCII `"EVBS"`); **If the check fails, the entire frame must be discarded** |
| `timestamp` | uint64 | Debug timestamp |
| `topic` | string | Application-level topic name, not a DDS wire topic. See [§4](#4-message-format-and-fields) for defined values. Clients must pass unknown values through to the application layer without rejecting them |
| `payload` | string | JSON string, schema varies with the value of `topic` (see [§4](#4-message-format-and-fields) for details) |

**QoS**

| QoS Policy | Value | Description |
|---|---|---|
| `RELIABILITY` | `BEST_EFFORT` | reader is not backlogged on the device side when offline |
| `HISTORY` | `KEEP_LAST, depth=10` | reader has a maximum backlog of 10 items |
| `DURABILITY` | `VOLATILE` | No reissue history; initial value requires RPC active query |
| `DATA_REPRESENTATION` | `[XCDR1, XCDR2]` | Compatible with new and old |
| `TYPE_CONSISTENCY_ENFORCEMENT` | `ALLOW_TYPE_COERCION` | Allow IDL field order differences/increases and decreases |

#### 1.3.3 Data subscription and publishing channel (open pub/sub)

Carrying high-frequency unidirectional streams of clients ↔ devices. This channel is not bound to fixed services and is an open channel reserved for business layer expansion. The IDL structure is directly used as the payload without a JSON envelope.

**Topic naming pattern**

```
rt/<scopeName>
```

`rt/` is the fixed prefix of this agreement (consistent with the ROS 2 naming convention) and cannot be changed; `<scopeName>` is agreed upon by the specific business.

**Load form**

The entire IDL structure is the payload, **no nested JSON string**. When adding a new topic to a new business, it is recommended to continue to follow the convention of "directly using the IDL structure as the payload".

**QoS (protocol-level enforcement)**

| QoS Policy | Value | Description |
|---|---|---|
| `DATA_REPRESENTATION` | `[XCDR1, XCDR2]` | Compatible with new and old |
| `TYPE_CONSISTENCY_ENFORCEMENT` | `ALLOW_TYPE_COERCION` | Allow IDL field order differences/increases and decreases |

The remaining QoS (`RELIABILITY` / `HISTORY` / `DURABILITY`, etc.) are agreed upon by specific services, and this agreement does not give default values ​​here. For the `scopeName`, IDL type and complete QoS of each service channel, see [§3](#3-business-flow) / [§4](#4-message-format-and-fields).

#### 1.3.4 Topic summary

List of DDS wire-level topics (used when the client creates Writer/Reader):

| Topic | Direction | Channel Type | IDL Type | Usage / Details |
|---|---|---|---|---|
| `rq/robotServerRequest` | Client → Device | RPC Request | `System_Request_` | [§1.3.1](#131-rpc-channel-request-reply) |
| `rr/robotServerReply` | Device → Client | RPC Response | `System_Response_` | [§1.3.1](#131-rpc-channel-request-reply) |
| `rt/robotServer/Event` | Device → Client | Event Channel | `EventMessage_` | [§1.3.2](#132-event-channel-active-push-by-device) / [§4.3](#43-events) |
| `rt/motion/trc` | Client → Device | Data pub/sub | `RemoteControl_` | TRC real-time control frame [§3.4](#34-real-time-control-frame-trc) / [§4.1](#41-trc-control-frame) |
| `rt/motion/observed` | Device → Client | Data pub/sub | `MotionObserved_` | Motion observation [§3.5](#35-motion-observation-subscription) / [§4.2](#42-observations) |
| `rt/sensor/observed` | Device → Client | Data pub/sub | `SensorObserved_` | Sensor observations (GPS / UWB / Walk odometer) [§3.5](#35-motion-observation-subscription) / [§4.2](#42-observations) |

> `rq/` / `rr/` / `rt/` is a fixed prefix under the ROS 2 naming convention. The client must subscribe/publish according to this wire-level name - different from the "logical topic names" used internally by the SDK (such as `robotServer.host.event`, `motion/trc`), which are SDK internal EventBus / Publisher Naming of the packaging layer, not visible on DDS.

### 1.4 Development project template

This section provides the smallest project template that can be started. Developers can compile and run by copying and adding IDL.

#### 1.4.1 Dependency installation

The robot side uses **Cyclone DDS 0.10.5**; the client is recommended to use the same major version.

```bash
# Ubuntu/Debian: build from source
git clone --depth=1 -b 0.10.5 https://github.com/eclipse-cyclonedds/cyclonedds
cd cyclonedds && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/usr/local -DBUILD_IDLC=ON ..
make -j$(nproc) && sudo make install
sudo ldconfig

# Recommended C++ binding: cyclonedds-cxx
git clone --depth=1 -b 0.10.5 https://github.com/eclipse-cyclonedds/cyclonedds-cxx
cd cyclonedds-cxx && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
make -j$(nproc) && sudo make install
sudo ldconfig
```

check:

```bash
which idlc                       # /usr/local/bin/idlc (IDL compiler)
ldconfig -p | grep ddsc          # libddsc.so.0 is available
ldconfig -p | grep ddscxx        # libddscxx.so.0 (C++ binding)
```

#### 1.4.2 Project directory structure

```
my_robot_client/
├── CMakeLists.txt
├── host_config.xml          # DDS profile; copy §1.2 and set the NetworkInterface name
├── idl/                     # Complete copy of IDL/ from the SDK repository
│   ├── Request.idl
│   ├── RPCMessage.idl
│   ├── EventMessage.idl
│   ├── MotorState.idl
│   ├── MotionObserved.idl
│   ├── SensorObserved.idl
│   └── RemoteControl.idl
└── src/
    └── main.cpp             # Application code
```

The SDK repository provides the complete IDL set under `IDL/`. **Copy the entire directory** so every `#include` dependency is preserved. Each file covers the following protocol scope:

| Documentation | Content |
|---|---|
| `Request.idl` | Public `Header` (clientId/requestId), shared by all envelopes |
| `RPCMessage.idl` | `System_Request_` / `System_Response_` (RPC request/reply envelope) |
| `EventMessage.idl` | `EventMessage_` (event channel envelope) |
| `MotorState.idl` | `MotorHeader` (motor addressing: limbsNo/jointNo) |
| `MotionObserved.idl` | `IMUState` / `Vector3f` / `Quaternionf` / `MotorObserved` / `PowerObserved` / Motion observation frame |
| `SensorObserved.idl` | `GPSFrame` / `GEOGPoint` / `UWBRawObserved` / Sensor observation frame |
| `RemoteControl.idl` | `RemoteControl_` (remote control handle frame) |

> The client does not need to use all of them, choose according to the scenario: only use `Request.idl + RPCMessage.idl` for pure RPC access; if you also need to subscribe to events, observations, and remote control, add `EventMessage.idl` / `MotionObserved.idl` / `SensorObserved.idl` / `RemoteControl.idl`, etc. as needed.

#### 1.4.3 CMakeLists.txt sample

```cmake
cmake_minimum_required(VERSION 3.16)
project(my_robot_client CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(CycloneDDS         REQUIRED)
find_package(CycloneDDS-CXX     REQUIRED)

# IDL → generated C++ code (at build time)
# File order is irrelevant; idlc resolves #include dependencies
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

#### 1.4.4 Build + Run

```bash
mkdir -p build && cd build
cmake ..
make -j$(nproc)

# Load this directory's Cyclone DDS profile (domain 42 and network interface)
export CYCLONEDDS_URI=file://$PWD/../host_config.xml

./my_client
```

#### 1.4.5 Startup sequence and minimum verification

1. **Make sure the robot is powered on and the network is reachable**; the client machine `ip a` can see its declared network card (such as `eth0`)
2. **After the client process is started**, DDS Discovery uses SPDP multicast. If there is still no sample published/subscribe within 5 seconds:
- Check that `Domain Id="42"` in `host_config.xml` is consistent with the robot side
- Check whether `<NetworkInterface name="...">` has selected a network card that can actually communicate with the robot
- Capture udp multicast packets to confirm that multicast is not blocked by the firewall: `sudo tcpdump -i eth0 udp port 7400` (Cyclone DDS default discovery port)
3. **Protocol level minimum verification**: Refer to [§3.3.4 Status query ](#334-status-query) `getMotionCapabilities` - an RPC without side effects, which can return the action list supported by the device, means the channel is open

For the specific envelope/payload/topic name of each RPC, see [§3 Business flow ](#3-business-flow) and [§4 Message format and fields ](#4-message-format-and-fields). The client can load `System_Request_` + according to these two sections and publish it to the corresponding topic.

---

## 2. Business message format specifications

This chapter defines the structure of the business layer message payload - the payload JSON envelope of the RPC channel ([§2.1](#21-rpc-message-specification)) and the topic convention of the event channel ([§2.2](#22-event-channel))). The fields of specific methods/events are given in [§3](#3-business-flow) / [§4](#4-message-format-and-fields).

### 2.1 RPC message specification

For the IDL and field semantics of `System_Request_` / `System_Response_`, see [§1.3.1](#131-rpc-channel-request-reply). This section focuses on the structure of the JSON envelope in the `payload` field - all business methods share the same envelope; the `params` field of the specific method is given in [§3.3](#33-detailed-explanation-of-rpc-method) Detailed explanation of each method.

| Directions | Topic |
|---|---|
| Request (Client → Device) | `rq/robotServerRequest` |
| Reply (Device → Client) | `rr/robotServerReply` |

#### 2.1.1 RPC request payload format

```jsonc
{
  "call":   { "clientId": "<string>" },
  "params": { /* method-specific fields */ }
}
```

| Field | Type | Required | Meaning |
|---|---|---|---|
| `call` | object | yes | caller context |
| `call.clientId` | string | Yes | RPC client id; the client id needs to be filled in according to the requirements of the specific business interface |
| `params` | object | Yes | Method-specific parameters; no parameters to fill in `{}` (**cannot be omitted**) |

#### 2.1.2 RPC reply payload format

```jsonc
{ "code": <uint32>, "result": <bool>, "params": { ... } }
```

| Field | Type | Required | Meaning |
|---|---|---|---|
| `code` | uint32 | Yes | Business errno (see [§4.4.1](#441-business-layer-payloadcode) for value); `0` = Success |
| `result` | bool | Yes | `true` = Business success; `false` = Business failure |
| `params` | object | No | handler returns data; optional, varies according to specific business interface |

Reading sequence: first look at `result` to determine the success or failure of the business. If it fails, look at `code` to get the reason for the failure; whether `params` exists is determined by the specific method (for details, see [§3.3](#33-detailed-explanation-of-rpc-method) "Response `params`" of each method).

#### 2.1.3 Two-level judgment of business success or failure

RPC protocol layer success ≠ business layer success. To determine the success of an RPC business, the following must be met at the same time:

| Layer | Field | Required |
|---|---|---|
| Protocol layer | `System_Response_.code` | `== 0` |
| Business layer | `payload.result` | `== true` |

```
business_ok = (response.code == 0) AND (payload.result == true)
```

### 2.2 Event channel

For the IDL (`EventMessage_`), envelope field and QoS of the event channel, see [§1.3.2](#132-event-channel-active-push-by-device). The external topic is fixed to `rt/robotServer/Event`.

The event `EventMessage_.payload` field is a JSON string, and its schema varies with the `EventMessage_.topic` field value (business topic) - see [§4.3](#43-events) for details.

---

## 3. Business flow

This chapter describes the robot capabilities exposed over Cyclone DDS ([§1](#1-overview-and-dds-channel-integration-requirements)). [§3.1](#31-control-life-cycle) defines the control lifecycle shared by all capabilities; [§3.2](#32-rpc-method-list) lists every RPC method; [§3.3](#33-detailed-explanation-of-rpc-method) documents each method's message format, fields, and usage; and [§3.4](#34-real-time-control-frame-trc) begins the non-RPC channels (TRC, motion observations, and events), shutdown, and network-disconnection handling.

#### Competency List

This Agreement currently covers the following business capabilities, each of which corresponds to one or more RPC methods in [§3.3](#33-detailed-explanation-of-rpc-method) or channel operations in [§3.4](#34-real-time-control-frame-trc)-[§3.6](#36-event-reception-and-distribution):

| Capabilities | Typical scenarios |
|---|---|
| Scheduling preset actions (walking, standing, jumping, etc.) | Automated jobs, task arrangement |
| Real-time handle/joystick control (50–100 Hz) | Remote control, teleoperation training |
| Subscribe to device status events (battery, network, playback, etc.) | Monitoring panel, alarms |
| Audio file management and playback control | Voice prompts, human-computer interaction |
| Query device capabilities and system status | Health check, capability adaptation |
| Subscription to operation control high-frequency observations | Training data collection, remote monitoring |

### 3.1 Control life cycle

To perform control operations (such as motion control, issuing remote control commands, music playback, etc.), the client must first obtain control of the device. Control of the device is **exclusive** and multiple clients are not allowed to perform control at the same time. Complete control life cycle:

```
   ① Acquire control (takeMotionControl)
            │
            ▼
   ② Execute control operations (actions / TRC frames / audio playback ...)
            │
            ▼
   ③ Renew periodically (renewMotionControl)
            │
            ▼
   ④ Release control when finished (releaseMotionControl)
```

- **Lease mechanism**: The client must renew control ownership periodically. If renewal stops or the lease expires, the device automatically revokes that client's control ownership.
- **Query APIs do not require control ownership by default**: any client may call or subscribe to them unless an individual API explicitly states otherwise.

For detailed control/renewal/release calling methods, see [§3.3.1](#331-session-management) Session Management.

### 3.2 RPC method list

| serviceName | method | function description | control required |
|---|---|---|:---:|
| `robotAppService` | `takeMotionControl` | Apply for control | No |
| `robotAppService` | `renewMotionControl` | Control right renewal | Yes |
| `robotAppService` | `releaseMotionControl` | Release control | No |
| `robotAppService` | `startMotionAction` | Trigger preset action | Yes |
| `robotAppService` | `stopMotionAction` | Stop current action | Yes |
| `robotAppService` | `setMotionActionParams` | Change subparameters during runtime | Yes |
| `robotAppService` | `emergencyStopMotion` | Emergency brake | Yes |
| `robotAppService` | `setMotionObservedEnable` | Switch motion observation measurement | No |
| `robotAppService` | `queryMotionState` | Query operation control status | No |
| `robotAppService` | `getMotionCapabilities` | Query the set of actions supported by the device | No |
| `robotAppService` | `getSystemStatus` | Pull system status snapshot | No |
| `robotAppService` | `startPlayList` | Start/resume audio playback | Yes |
| `robotAppService` | `stopPlayList` | Stop/pause audio playback | Yes |
| `robotAppService` | `getAudioPlayList` | Query audio file list | No |
| `robotAppService` | `getAudioPlayDetail` | Query current playback details | No |
| `robotAppService` | `addAudioFile` | Upload/Add audio file | Yes |
| `robotAppService` | `deleteAudioFile` | Delete audio files | Yes |
| `robotAppService` | `getCameraLightBrightness` | Query the camera fill light brightness | Yes |
| `robotAppService` | `setCameraLightBrightness` | Set camera fill light brightness | Yes |

Call template (common to all methods):

```jsonc
// System_Request_
{
  "header":    { "clientId": <session-id>, "requestId": <seq> },
  "timestamp": <now-ms>,
  "service":   "robotAppService",
  "device_id": "<device SN>",
  "method":    "<method from the table above>",
  "payload":   "<JSON-encoded {call, params}>"
}
```

### 3.3 Detailed explanation of RPC method

Each method gives: **Request `params`** (message format + fields), **Response `params`** (message format + fields), **Usage Notes**.

**Method Cheat Sheet**

| Method | Control requirement | Key parameters | Details |
|---|---|---|---|
| `takeMotionControl` | None | `leaseTimeout`(ms) | [§3.3.1](#331-session-management) |
| `renewMotionControl` | Holding rights | `controller` | [§3.3.1](#331-session-management) |
| `releaseMotionControl` | Holding rights | `controller` | [§3.3.1](#331-session-management) |
| `startMotionAction` | Holding rights | `action` / `params` | [§3.3.2](#332-action-control) |
| `stopMotionAction` | Holding rights | — | [§3.3.2](#332-action-control) |
| `setMotionActionParams` | Holding rights | `params` (according to current action schema) | [§3.3.2](#332-action-control) |
| `emergencyStopMotion` | Holding rights | — | [§3.3.2](#332-action-control) |
| `setMotionObservedEnable` | Connected | `motionEnable`(bool), `sensorEnable`(bool) | [§3.3.3](#333-data-reporting) |
| `queryMotionState` | None | — | [§3.3.4](#334-status-query) |
| `getMotionCapabilities` | None | — | [§3.3.4](#334-status-query) |
| `getSystemStatus` | None | — | [§3.3.4](#334-status-query) |
| `startPlayList` | Holding rights | `list` / `volume` / `repeat`, etc. | [§3.3.5](#335-audio-control) |
| `stopPlayList` | Holding rights | — | [§3.3.5](#335-audio-control) |
| `getAudioPlayList` | None | `type` (such as customVoice) | [§3.3.5](#335-audio-control) |
| `getAudioPlayDetail` | None | — | [§3.3.5](#335-audio-control) |
| `addAudioFile` | Holding rights | `id` / `name` / `file` or `url`, etc. | [§3.3.5](#335-audio-control) |
| `deleteAudioFile` | Holding rights | `id` | [§3.3.5](#335-audio-control) |
| `getCameraLightBrightness` | Holding rights | — | [§3.3.6](#336-system-settings) |
| `setCameraLightBrightness` | Holding rights | `brightness`(0~100) | [§3.3.6](#336-system-settings) |

> All RPCs are sent and received through the same pair of wire topic `rq/robotServerRequest` / `rr/robotServerReply`; the service name is fixed to one of `robotAppService` / `motionService` / `audioService` (see the details of each method for details).

#### 3.3.1 Session Management

`takeMotionControl` / `renewMotionControl` / `releaseMotionControl` jointly realize the control life cycle ([§3.1](#31-control-life-cycle)).

##### `takeMotionControl`

Request High-level control ownership. On success, the client becomes the control owner. Calling the method again while already holding control refreshes `leaseTimeout` and returns the same `controller` token.

**Request `params`**

| Field | Type | Required | Meaning |
|---|---|---|---|
| `leaseTimeout` | uint32 | Yes | Lease duration ms; recommended 5000–60000 |

```jsonc
{ "call": { "clientId": "my-app" }, "params": { "leaseTimeout": 30000 } }
```

**Response `params`** (on success)

| Field | Type | Occurrence conditions | Meaning |
|---|---|---|---|
| `controller` | string (16 bytes) | Always | This value must be filled in for `call.clientId` of subsequent rights-holding RPCs |
| `leaseTimeout` | uint32 | Always | The final effective lease of the device ms |
| `rawActionId` | uint64 | When the device enables TRC | TRC frame `RemoteControl_.controller` takes this value; missing or 0 means TRC is not available |

```jsonc
{ "result": true, "params": { "controller": "0xGUefQ7T9VWxulv", "leaseTimeout": 30000, "rawActionId": 1234567890 } }
```

**Usage Note**

- After successful control, the client holds control and needs to start the scheduled renewal **immediately**
- `payload.call.clientId` in all subsequent rights-holding RPCs must be switched to `controller` in the response
- Failure `0x1D controlWasSeized`: Control is already held by another client; wait for the other party to release or the lease expires
- `leaseTimeout` recommends 5000–60000 ms - after the client crashes, the device will not be released until the lease expires. It should not be too long.

##### `renewMotionControl`

Renewal control. The client must be called periodically, otherwise the device will be automatically reclaimed after the lease expires.

**Request `params`**: `{}`

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": {} }
```

**Response `params`** (on success)

| Field | Type | Meaning |
|---|---|---|
| `leaseTimeout` | uint32 | Remaining lease duration after renewal ms |

```jsonc
{ "result": true, "params": { "leaseTimeout": 30000 } }
```

**Usage Note**

- Suggested renewal period `clamp(leaseTimeout / 3, 200 ms, 10 s)`
- Any renewal RPC that times out or fails will be immediately deemed to have been lost.
- Failure `0x10 operatorInvalid`: The lease has expired, immediately follow the "loss of rights processing" process

##### `releaseMotionControl`

After actively returning control, other clients can take over immediately.

**Request `params`**: `{}` - response `params` is also empty (only `result: true`).

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": {} }
```

**Usage Note**

- After the call, the client should switch `payload.call.clientId` back to the custom identification and stop the renewal thread.
- Even if the other party does not respond, the local party should consider that it no longer holds the right.
- The shutdown process must be completed before the RPC endpoint is destroyed (see [§3.7](#37-close))

##### Loss of rights processing (unified process)

Triggered by any of the following situations:

| Trigger conditions |
|---|
| Renewal RPC timed out or failed |
| Renew RPC return `0x10 operatorInvalid` (lease has expired) |
| Any RPC returns `0x1C noOperationPerm` / `0x1D controlWasSeized` |
| Received events `robotServer.control.status` and `controlled == false` (and I was originally the rights holder) |
| Long-term disconnection exceeds the lease period (the device has automatically recovered rights) |

Unified processing actions:

```
① Stop sending TRC frames immediately
② Stop the background renewal thread
③ If a preset action is running, call stopMotionAction once so the device can clean up
   (this call will probably return 0x1C; ignore that result)
④ Mark the client as no longer holding control
⑤ Notify the application layer
```

There is no need to rebuild the DDS endpoint after losing authority. When re-`takeMotionControl`, you must use the `controller` / `rawActionId` in the new response. Do not reuse the old value.

#### 3.3.2 Action Control

`startMotionAction` / `stopMotionAction` / `setMotionActionParams` / `emergencyStopMotion` jointly realize action issuing and stopping.

##### `startMotionAction`

Trigger the device to perform preset actions. The device has started moving when the RPC returns, and the movement itself is asynchronous.

**Request `params`**

| Field | Type | Required | Meaning |
|---|---|---|---|
| `action` | string | Yes | Action name; must be in the `getMotionCapabilities` return list |
| `params` | object | No | Action sub-parameter; field name/range/unit is dynamically queried through `actions[].params` of `getMotionCapabilities`. One-time actions (such as `jumpBackflip`) usually have no parameters and can be omitted or filled in. `{}` |

```jsonc
{
  "call": { "clientId": "0xGUefQ7T9VWxulv" },
  "params": {
    "action": "walking",
    "params": { "velocity": 0.0, "lineVelocityX": 0.5, "lineVelocityY": 0.0 }
  }
}
```

**Typical `action` value**

`walking` / `standing` / `laying` / `bipedStand` / `handstand` / `waveBody` / `peakLoadStand` / `jumpFrontflip` / `jumpSideflip` / `jumpBackflip` / `jumpDoubleBackflip` / `jumpDoubleSideflip`

**Response to `params`**: Empty on success (`result: true` only).

**Usage Note**

- The actual supported actions vary with the device model and firmware version, and must be dynamically queried through `getMotionCapabilities`, **should not be hard-coded on the client**
- Before triggering any action other than `laying`, use `startMotionAction` to start `walking` with all three velocities set to zero, poll `queryMotionState` until `params.action` is `walking`, and only then trigger the target action. `laying` does not require this preliminary transition
- RPC return success only means that the request was accepted by the device, and the physical movement may last for several seconds; there are three ways to determine that the action is truly completed:
- Poll `queryMotionState` to see changes in the `params.action` field (suitable for simple actions such as standing/sitting down)
- Subscribe to the motion observation volume ([§3.5](#35-motion-observation-subscription)), monitor `motor[i].velocity` to be close to 0 and last for several frames
- Anticipated waiting (suitable for short fixed actions such as jumping)
- Typical failures:
- `0x08 outOfDeviceCaps`: The action is not in capabilities, check `getMotionCapabilities` first
- `0x09 operationTempNotAllow`: `emergencyStopMotion` cooling period, retreat 3–5s and try again
- `0x1C noOperationPerm`: lost rights, lost rights handling process

##### `stopMotionAction`

Stop current action. The device goes through the closing process (not stopped immediately), then returns the effective action to `walking` with all three walking velocities set to zero. **Retain control** after stopping. Starting `walking` with full zero parameters is the equivalent explicit action transition.

**Request `params`**: `{}` - Response `params` is empty.

**Usage Note**

- To stop immediately please use `emergencyStopMotion`
- The shutdown process needs to be called before release, otherwise the device may continue to perform the previous action before returning control.

##### `setMotionActionParams`

Dynamically modify sub-parameters during action execution (**without switching actions**).

**Request `params`**

| Field | Type | Required | Meaning |
|---|---|---|---|
| `params` | object | yes | sub-parameter; for field name/range/unit, see `getMotionCapabilities` `params` list corresponding to the action returned |

Take `walking` as an example (the field name/range is subject to the one returned by `getMotionCapabilities`):

| Field | Type | Unit | Meaning |
|---|---|---|---|
| `velocity` | float | rad/s | Yaw rate (yaw rate), positive left turn, negative right turn |
| `lineVelocityX` | float | m/s | Front and rear linear speed, positive forward and negative backward |
| `lineVelocityY` | float | m/s | Lateral linear velocity, positive right and negative left |

```jsonc
{
  "call": { "clientId": "0xGUefQ7T9VWxulv" },
  "params": { "params": { "velocity": 0.0, "lineVelocityX": 0.5, "lineVelocityY": 0.0 } }
}
```

**Response `params`**: Empty on success.

**Usage Note**

- **Full rewrite**: `setMotionActionParams` has the same **full semantics** as `startMotionAction` - `params` called this time covers the entire set of runtime parameters, and **untransmitted fields return to 0**. To change only yaw but retain X speed, all three fields must be passed
- **The range is cut by the server**: No error will be reported when exceeding the range, and it will be replaced by the boundary value; the actual upper limit of the capacity can be queried through `getMotionCapabilities`
- **Zero speed parameters do not mean stop**: `setMotionActionParams({lineVelocityX:0, lineVelocityY:0, velocity:0})` only makes the current action zero-speed. To stop it, use `stopMotionAction`, or call `startMotionAction` for `walking` with all three fields explicitly zero. Both transitions are asynchronous.
- **Three fields are independent**: Complete movement requires a combination of three axes (such as walking and turning: `{"lineVelocityX":0.5,"velocity":0.3}`)

##### `emergencyStopMotion`

Emergency braking - the equipment immediately cuts off the motion output without going through the finishing process. **Retain control** after stopping.

**Request `params`**: `{}` - Response `params` is empty.

**Usage Note**

- After emergency stop, the device refuses new actions for a short period of time (about a few seconds) (returns to `0x09 operationTempNotAllow`)
- This RPC (reliable channel) should be used in emergency stop scenarios, do not rely on TRC frames

#### 3.3.3 Data reporting

##### `setMotionObservedEnable`

Controls the external release switch of motion observations ([§3.5](#35-motion-observation-subscription)). `motionEnable`/`sensorEnable` independently control the two-way push of `MotionObserved_` and `SensorObserved_`.

**Request `params`**

| Field | Type | Required | Meaning |
|---|---|---|---|
| `motionEnable` | bool | No | `true` = Enable `MotionObserved_` push; `false`/Default = Disable |
| `sensorEnable` | bool | No | `true` = Enable `SensorObserved_` push; `false`/Default = Disable |

```jsonc
{ "call": { "clientId": "my-app" }, "params": { "motionEnable": true, "sensorEnable": false } }
```

**Response `params`**: Return the actual switch state after setting.

| Field | Type | Meaning |
|---|---|---|
| `motionEnable` | bool | Current `MotionObserved_` push switch |
| `sensorEnable` | bool | Current `SensorObserved_` push switch |

**Usage Note**

- It is closed by default and is not persisted to the configuration: the server returns to the closed state after restarting and needs to be turned on again.
- `payload.call.clientId` identifies the RPC session. The current SDK and server do not perform a control-ownership check for this switch. The target MotionServer should already be the master when the caller needs local motor/IMU observations; raw DDS `takeMotionControl` only acquires control and does not replace the master-role switch performed by High-level `startControl()`
- For the calling sequence, see [§3.5](#35-motion-observation-subscription): **Subscribe to the reader first and then call this RPC to start pushing**; reverse order will lose the first few milliseconds of frames

#### 3.3.4 Status Query

##### `queryMotionState`

Query the actual effective action + control speed of the latest beat of the current operation control loop.

**Request `params`**: `{}`

**Response `params`**

| Field | Type | Meaning |
|---|---|---|
| `action` | string | Current effective action name (the latest posture matching result of the motion control loop) |
| `velocity` | float | Angular velocity (rad/s) |
| `lineVelocityX` | float | Front and rear linear speed (m/s) |
| `lineVelocityY` | float | Traverse linear speed (m/s) |

> **When there is no active action**: RPC successful (`result: true`), `params` is empty object `{}`.
> Pay attention to distinguish two layers:
> - `result: false` → Server rejection or RPC channel exception, handle according to RPC error code (see [§4.4 Error code ](#44-error-code))
> - `result: true` + `params: {}` → There is no active action on the server; do not treat this as a failure

```jsonc
// Active action
{
  "result": true,
  "params": {
    "action":        "walking",
    "velocity":       0.0,
    "lineVelocityX":  0.5,
    "lineVelocityY":  0.0
  }
}

// After stopMotionAction, the effective action is zero-speed walking
{
  "result": true,
  "params": {
    "action":        "walking",
    "velocity":      0.0,
    "lineVelocityX": 0.0,
    "lineVelocityY": 0.0
  }
}
```

**Usage Note**

- The speed field name `velocity` / `lineVelocityX` / `lineVelocityY` is consistent with the `params` input parameter field name of `startMotionAction` / `setMotionActionParams`, making it easy to write back
- Commonly used for action completion determination (polling 100–500 ms); future firmware may expand more fields, and clients should **ignore unknown fields** to maintain forward compatibility

##### `getMotionCapabilities`

Query the set of preset actions supported by the current device - including key combinations + adjustable parameters (min/max/unit). It is recommended to be the first RPC call in the access process, and the business side will render dynamically accordingly.

**Request `params`**: `{}`

**Response `params`**

| Field | Type | Meaning |
|---|---|---|
| `actions[].name` | string | Action name, `action` parameter passed to `startMotionAction` |
| `actions[].mapping.require` | array<string\> | The name of the button that must be pressed to trigger this action, the value corresponds to the TRC button field |
| `actions[].mapping.axisRequire` | array<object\> | Additional axis value conditions; each item contains `axis`, `min`, `max`, `axis` is the TRC axis field |
| `actions[].mapping.priority` | integer | The priority when multiple actions hit in the same frame. The larger the value, the higher the priority |
| `actions[].mapping.exact` | bool | `true` means that no other buttons except `require` can be pressed at the same time |
| `actions[].mapping.minHoldTime` | number | Minimum hold time, currently mapped to `0` |
| `actions[].params` | array<object\> | Adjustable runtime parameters for this action; one-time actions do not have this field |
| `params[].name` | string | Parameter key, used as the key of `params` JSON of `startMotionAction` / `setMotionActionParams` |
| `params[].min/max` | float | Value range; if exceeded, the server will clamp |
| `params[].unit` | string | Unit (such as `"m/s"` / `"rad/s"`); if the server is not configured, it will not output |

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

**Usage Note**

- It is recommended to call this method on the first RPC after access to verify that the DDS link / IDL / QoS / `device_id` are all aligned
- Client UI/business logic should not hardcode action lists/parameter ranges
- Build a snapshot once during the startup period and return it directly to the cache during the runtime, with zero cost for multiple calls.

##### `getSystemStatus`

Pull a complete device system state snapshot **once**. Event subscription is incremental push. **You must obtain a complete snapshot through this method after the first connection**.

**Request `params`**: `{}`

**Response `params`** (top-level keys are grouped by subsystem, and the client consumes them on demand)

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

**`battery` field**

| Field | Type | Unit | Meaning |
|---|---|---|---|
| `abnormalStatus` | uint8 | — | Whether the power circuit is abnormal, non-0 means abnormal |
| `statusCode` | uint16 | — | BMS status code, bit mask combination (see table below) |
| `cycleCount` | uint16 | times | The cumulative number of battery charge and discharge cycles |
| `remainChargeTime` | uint16 | Minutes | Remaining charging time (valid during charging) |
| `remainDischargeTime` | uint16 | Minutes | Remaining discharge time (estimated based on current load) |
| `power` | float | % | Current battery power percentage, 0~100 |
| `health` | float | % | Battery health, 0~100 |
| `temperature` | float | °C | Battery temperature (signed) |
| `fullCharge` | float | mAh | Full charge capacity |
| `remaining` | float | mAh | remaining capacity |
| `current` | float | A | Current charge and discharge current (positive charge, negative discharge) |
| `voltage` | float | V | Current total voltage |

**`battery.statusCode` bit mask** (`statusCode & bit != 0` indicates that the corresponding protection bit is valid)

| bit | value | meaning |
|---|---|---|
| bit0 | `0x0001` | pack undervoltage protection |
| bit1 | `0x0002` | cell undervoltage protection |
| bit2 | `0x0004` | pack overvoltage protection |
| bit3 | `0x0008` | cell overvoltage protection |
| bit4 | `0x0010` | Charging completed |
| bit5 | `0x0020` | Discharge overcurrent protection |
| bit6 | `0x0040` | Charging overcurrent protection |
| bit7 | `0x0080` | Short circuit protection |
| bit8 | `0x0100` | Discharge low temperature protection |
| bit9 | `0x0200` | Charging low temperature protection |
| bit10 | `0x0400` | Discharge high temperature protection |
| bit11 | `0x0800` | Charging high temperature protection |
| bit12 | `0x1000` | MOS high temperature protection |
| bit13 | `0x2000` | Cell collection disconnection protection |
| bit14 | `0x4000` | Cell voltage imbalance protection |
| bit15 | `0x8000` | Cell voltage failure protection |

**`network.<iface>.status` enumeration value**

| Value | Meaning |
|---|---|
| `0` | Connected |
| `1` | Not connected |
| `2` | Connecting |

**`network.mobile.signalLevel` values** (`mobile` object only)

| Value | Meaning |
|---|---|
| `0` | Good signal (> 22 dB) |
| `2` | Moderate signal (> 15 dB) |
| `3` | Poor signal (≤ 15 dB) |

`network.mobile.simCardSta`: `true` = SIM card ready, `false` = not inserted or not recognized.

**Usage Note**

- When accessing for the first time, you must actively call this method to obtain a complete snapshot; subsequent changes are pushed incrementally through event `statistics/device_status` ([§4.3](#43-events))
- The client needs to do **partial merge/patch** to maintain a complete status view

#### 3.3.5 Audio Control

##### `startPlayList`

Play a list of audio files, or resume `stopPlayList { "pause": true }` paused playback.

**Request `params`** - Choose one of two usages:

*Usage A · Start new list*

| Field | Type | Required | Meaning |
|---|---|---|---|
| `list` | array<object\> | Yes | Files to be played, each item `{ "id": <string> }`; `id` obtained through `getAudioPlayList` |
| `volume` | uint8 | Yes | Volume 0–100 |
| `repeat` | int32 | Yes | Number of loops; `-1` = infinite loop, `>0` = times, `0` meaningless |

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "list": [{"id":"1"},{"id":"2"}], "volume": 50, "repeat": 1 } }
```

*Usage B·Resume pause*

| Field | Type | Required | Meaning |
|---|---|---|---|
| `resume` | bool | yes | Fixed `true`, resume paused playback of `stopPlayList { "pause": true }` |

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "resume": true } }
```

**Response `params`**: Empty on success.

**Usage Note**

- The two usages of A/B are mutually exclusive. Only one set of fields can be carried in one call.
- Playback status changes are subscribed through event `statistics/play_list` ([§4.3](#43-events)); the first snapshot is using `getAudioPlayDetail`

##### `stopPlayList`

Stop or pause audio playback.

**Request `params`**

| Field | Type | Required | Meaning |
|---|---|---|---|
| `pause` | bool | No | `true` = pause, keep playback position (can be resumed with `startPlayList { "resume": true }`); `false` or missing field = stop and clear the device playback queue (**not resumable**) |

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": {} }              // Stop
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "pause": true } } // Pause
```

**Response `params`**: Empty on success.

**Usage Note**: Stop (without `pause`) has different semantics from pause; the former clears the queue and cannot be restored, while the latter can reserve the position `resume`.

##### `getAudioPlayList`

Query the list of audio files stored on the device. The returned `id` can be used as the input parameter of `startPlayList` / `deleteAudioFile`.

**Request `params`**

| Field | Type | Required | Meaning |
|---|---|---|---|
| `type` | string | No | Filter category, optional `"customVoice"` (only return custom); missing field = return full amount |

**Response `params`**

| Field | Type | Meaning |
|---|---|---|
| `list` | array<object\> | File list |
| `list[*].id` | string | file id |
| `list[*].name` | string | file name |
| `list[*].duration` | int | Duration (seconds) |
| `list[*].size` | int | File size (bytes) |
| `list[*].createAt` | int64 | Creation timestamp (milliseconds) |
| `list[*].describe` | string | Remarks |
| `remaining` | int | Remaining uploadable quantity/capacity quota (precise semantics are defined by the device side) |

```jsonc
{
  "result": true,
  "params": {
    "customVoice": [
      { "id": "1", "name": "walk", "duration": 12, "size": 320000, "createAt": 1712745600000, "describe": "example note" }
    ],
    "remaining": 20
  }
}
```

**Usage Note**: It is normal when the empty set is returned (`0x28 dataResourceEmpty`, empty set processing on the business side).

##### `getAudioPlayDetail`

Query the current playback details. Event `statistics/play_list` will push incremental changes, and **the first snapshot must be obtained through this method**.

**Request `params`**: `{}`

**Response `params`**

| Field | Type | Meaning |
|---|---|---|
| `channel` | int | Playback channel, the meaning is defined by the device side |
| `playing` | bool | Is it playing |
| `paused` | bool | Whether to pause |
| `repeat` | int | Repeat configuration: `-1`=infinite loop; `>0`=number of times; `0` meaningless |
| `index` | int | Current playback index (starting from 0) |
| `count` | int | Total number of current playlists |
| `volume` | int | Current volume, 0~100 |
| `currentId` | string | Currently playing audio ID |
| `list` | array<string\> | Current playlist, the element is audio ID |

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

Add (upload) a custom audio file to the device. Supports **two ways of obtaining files**:

- **`file` mode (local path)**: The caller passes in a local file path that the device can directly read (for example, the client and the robot board are deployed at the same time, and the file is already on the local machine/shared disk). No download steps, fastest.
- **`url` mode (remote download)**: The caller passes in the HTTP URL, and **the robot downloads the file** from this URL during the RPC call to the local and then stores it in the database. The caller needs to deploy an HTTP file server to play the audio, and the robot can directly GET it.

**Choose one of the two modes `file` and `url`** (give priority to `url` when given both at the same time).

| Deployment form | Recommendation |
|---|---|
| The SDK application and the robot are on the same board (in-board mode) | Use `file` - the file is already on the board, just give the path directly |
| SDK application on remote host (multiple robots/external machines) | Use `url` - you need to run an HTTP file server yourself to expose the audio |

**Request `params`**

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | Yes | File id; customized by the client, ensure that it does not conflict with existing non-system files |
| `name` | string | Yes | File name (including extension, such as `"hello.mp3"`) |
| `file` | string | Choose one of the two | **Local path mode**: The absolute path of the file that can be read directly by the robot side |
| `url` | string | Choose one of the two | **Remote download mode**: HTTP URL, the robot will pull it and put it into the database |
| `describe` | string | No | Notes/Description |

```jsonc
// Local-path mode (on-board deployment)
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "id": "custom_1", "name": "hello.mp3", "file": "/var/audio/hello.mp3", "describe": "example" } }

// Remote-download mode (external host deployment)
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "id": "custom_1", "name": "hello.mp3", "url": "http://192.168.1.x:8000/audio/hello.mp3", "describe": "example" } }
```

**Response `params`**: Empty on success.

**Usage Note**

- After the addition is successful, the file will be classified as `customVoice` and can be queried through `getAudioPlayList` or used as `id` of `startPlayList` / `deleteAudioFile`.
- Supported audio formats: `mp3` / `wav` and other common formats; the specific support list and single file size limit are given by the device according to the model.
- `url` mode: The device will complete the download during the RPC call, and the overall response time varies with the network and file size; it is recommended that the client uses a local timeout longer than the default 5s (such as 30s)
- `file` mode: The path must be accessible to the robot; confirm the mounting and read permissions when using NAS/shared disks
- Typical failures: `0x01 paramsTypeError` / `0x02 paramsDeletion` (field error); `0x08 outOfDeviceCaps` (the maximum number of audios that can be stored in the device is reached); `id` conflicts (same as existing non-system files); `url` pull failure / `file` path does not exist

##### `deleteAudioFile`

Delete the audio file with the specified id on the device. Only the `customVoice` class is allowed to be deleted; deleting system preset audio will return an error code.

**Request `params`**

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | Yes | The id of the file to be deleted; obtained through `getAudioPlayList` |

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "id": "1" } }
```

**Response `params`**: Empty on success.

**Usage Note**: Typical failure is `0x21 fileNotExist`, check whether `id` still exists.

#### 3.3.6 System settings

##### `getCameraLightBrightness`

Query the current brightness of the body camera fill light.

**Request `params`**: None (`call.clientId` only).

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" } }
```

**Response `params`**: Current brightness.

```jsonc
{ "brightness": 50 }
```

**Usage Note**: You need to hold control rights, otherwise `kNotControlled` will be returned.

---

##### `setCameraLightBrightness`

Set the brightness of the body camera fill light.

**Request `params`**

| Field | Type | Required | Meaning |
|---|---|---|---|
| `brightness` | uint8 | Yes | Brightness, 0~100 |

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" }, "params": { "brightness": 50 } }
```

**Response `params`**: Empty on success.

**Usage Note**: Typical failure is `0x04 paramsOutRange`, check the parameter value range.

##### `getCameraLightBrightness`

Query the control status and brightness of the body camera's fill light.

**Request `params`**: Can be null.

```jsonc
{ "call": { "clientId": "0xGUefQ7T9VWxulv" } }
```

**Response `params`**

| Field | Type | Meaning |
|---|---|---|
| `control` | bool | Whether the brightness is currently controlled manually |
| `brightness` | int | Current configuration brightness, 0~100 |

```json
{ "control": true, "brightness": 50 }
```

---

### 3.4 Real-Time Control Frame (TRC)

TRC is the specific use of the data subscription publishing channel ([§1.3.3](#133-data-subscription-and-publishing-channel-open-pubsub)) in the "client→device" direction, carrying handle/joystick sampling type input.

| item | value |
|---|---|
| Topic | `rt/motion/trc` |
| Load type | `uniubi::msg::dds_::RemoteControl_` ([§4.1](#41-trc-control-frame)) |
| Push frequency | 50–100 Hz |
| Authentication field | `RemoteControl_.controller = rawActionId` (uint64, **not** `controller` string) |

#### QoS

| QoS Policy | Value | Reason for selection |
|---|---|---|
| `RELIABILITY` | `BEST_EFFORT` | High-frequency streams are not retransmitted; the next frame is automatically covered |
| `HISTORY` | `KEEP_LAST, depth=10` | Cache the last 10 frames |
| `DURABILITY` | `VOLATILE` | reader joined late and will not resend old frames |
| `DATA_REPRESENTATION` | `[XCDR1, XCDR2]` | Compatible with new and old |
| `TYPE_CONSISTENCY_ENFORCEMENT` | `ALLOW_TYPE_COERCION` | Allow IDL field order differences/increases and decreases |

#### Calling premise

```
① Control is held
② rawActionId != 0
```

If any of these are not met, the device silently discards all TRC frames.

#### Sending steps

```
Construct RemoteControl_:
  trc.controller = rawActionId
  trc.timestamp  = now_ms
  trc.<button>   = 0 / 1
  trc.<axis>     = float in the range defined by [§4.1](#41-trc-control-frame)
DDS-write to rt/motion/trc; return immediately without waiting for a response
```

#### Single frame transient semantics

- Button status **single frame instant** - keep pressing to continue pushing frames
- The button must be cleared in the next frame after triggering, otherwise it will continue to trigger.
- The stop action must actively deliver a frame of all 0s, otherwise the device will maintain the previous frame
- It is recommended to resend the same key combination three times at 20ms intervals to increase the delivery probability (BestEffort does not guarantee the arrival of each frame)

#### Emergency stop scene

Use the RPC channel (`emergencyStopMotion`), do not rely on TRC frames - TRC uses an unreliable channel.

### 3.5 Motion Observation Subscription

Motion observation subscription is based on the "device → client" direction of the data subscription publishing channel ([§1.3.3](#133-data-subscription-and-publishing-channel-open-pubsub)), carrying 50 Hz motion observation frames (IMU + multi-motor).

| item | value |
|---|---|
| Topic | `rt/motion/observed` |
| Load type | `uniubi::msg::dds_::MotionObserved_` ([§4.2](#42-observations)) |
| Push frequency | 50 Hz (~1 KB per frame, bandwidth ≈ 50 KB/s) |
| Default state | **Off** |

#### QoS

| QoS Policy | Value | Reason for selection |
|---|---|---|
| `RELIABILITY` | `BEST_EFFORT` | High-frequency streams are not retransmitted; the next frame is automatically covered |
| `HISTORY` | `KEEP_LAST, depth=10` | Cache the last 10 frames |
| `DURABILITY` | `VOLATILE` | reader joined late and will not resend old frames |
| `DATA_REPRESENTATION` | `[XCDR1, XCDR2]` | Compatible with new and old |
| `TYPE_CONSISTENCY_ENFORCEMENT` | `ALLOW_TYPE_COERCION` | Allow IDL field order differences/increases and decreases |

#### Start and stop convention (sequence sensitive)

```
Enable:
  ① Subscribe the reader to rt/motion/observed
  ② Ensure that the target MotionServer is already the master when local motor/IMU observations are needed
  ③ Call RPC setMotionObservedEnable ([§3.3.3](#333-data-reporting)), params: {"motionEnable": true}
  ④ The device starts publishing at 50 Hz

Disable:
  ⑤ Call RPC setMotionObservedEnable, params: {"motionEnable": false}
  ⑥ Release motion control only if the client acquired it for another operation
  ⑦ Destroy the reader (optional; retain it while the session remains open)
```

The protocol order is **subscribe first, ensure that the target endpoint is the master when local motor/IMU observations are needed, and then enable push**. This switch itself does not require control ownership. `takeMotionControl` does not switch the master role; a slave endpoint may not provide local motor/IMU observations. The current ROS 2 `MotionHighLevelClient` implementation enables the server push before creating its raw subscriptions, so its first observation frames may be lost; this is an implementation limitation, not the protocol order.

#### Sensor observation (`rt/sensor/observed`)

Sensor observation (GPS / UWB / Walk odometer) goes through the independent topic `rt/sensor/observed`, which belongs to the same "device → client" data channel as the motion observation, and the payload is `uniubi::msg::dds_::SensorObserved_` ([§4.2](#42-observations)).

| item | value |
|---|---|
| Topic | `rt/sensor/observed` |
| Load type | `uniubi::msg::dds_::SensorObserved_` ([§4.2](#42-observations)) |
| Default state | **Off** |

QoS, start and stop conventions are consistent with motion observations (same as above: `BEST_EFFORT` / `KEEP_LAST` / `VOLATILE` / `ALLOW_TYPE_COERCION`; subscribe first and then enable push). The switch also reports the data of [§3.3.3](#333-data-reporting) for RPC control. Devices without corresponding sensor hardware do not write data.

> `odom` does not rely on GPS / UWB hardware; open `sensorEnable` and publish it with this topic. When GPS/UWB is not present, its respective `valid` field remains invalid.

> This section describes the DDS wire contract. `SensorObserved_` contains `odom` on the wire, but this does not mean that the Low-level SDK supports Walk odometry. The public Low-level `SensorObserved` contract contains GPS/UWB only.

### 3.6 Event reception and distribution

The processing flow after the client receives `EventMessage_`:

```
Receive EventMessage_
   │
   ├─► magic != 0x53425645  →  discard
   │
   ├─► (optional) header.clientId == this client ID  →  local loopback; discard
   │
   ├─► Dispatch by `EventMessage_.topic`:
   │
   │   ┌─ "robotServer.host.event" (container mode)
   │   │   └─► Parse payload JSON and dispatch again by the nested event field
   │   │       The business payload is in detail
   │   │
   │   ├─ "robotServer.control.status" (pass-through mode)
   │   │   └─► Pass payload JSON directly to the business handler
   │   │
   │   └─ Unknown `EventMessage_.topic`
   │       └─► Pass through to the business layer (forward-compatible with new device events)
   │
   └─► Done
```

| Terminology | Currently defined values ​​| Location |
|---|---|---|
| Business topic (`EventMessage_.topic` field value) | `robotServer.host.event` / `robotServer.control.status` | `EventMessage_.topic` |
| Sub-business topic | Multiple (such as `statistics/device_status`) | Container-type business topic inner layer `payload.event` |

For the payload schema of each `EventMessage_.topic` value and sub-business topic, see [§4.3](#43-events).

### 3.7 Close

Shut down in the following order to avoid residual status on the device side:

```
① If control is still held:
   a. Send one all-zero TRC frame (stop current TRC control)
   b. Call stopMotionAction
   c. If motion observations are enabled, call setMotionObservedEnable(motionEnable=false)
   d. Call releaseMotionControl (wait for the response before continuing; timeout is acceptable)
   e. Stop the background renewal thread

② Destroy the motion-observation reader, TRC writer, and event reader
③ Destroy the RPC reader and writer
④ Destroy the DomainParticipant
```

**Sequence Sensitive**: RPC calls (c, d) must be completed before the RPC endpoint is destroyed (③); the stop command must be issued before release, otherwise the device may continue to perform the previous action before returning control.

### 3.8 Disconnection and multiple terminals

#### Disconnection and lease

| Scene | Performance/Processing |
|---|---|
| Short-term network jitter (< 10 s) | DDS reliable QoS automatically retransmits RPC; TRC/motion observation may lose several frames and automatically recover; failure during renewal period will go through the "loss of rights processing" process ([§3.3.1](#331-session-management)) |
| Device restart/long-term network disconnection (> 30 s) | After discovery re-convergence, it is not necessary to destroy the local endpoint**; first adjust `getMotionCapabilities` to detect activity; restart `takeMotionControl` as needed |
| The client process unexpectedly exits | The device waits until the lease expires before releasing control; restarting the client is considered a new session; if the old lease has not expired, the new session will return `0x1D` and you need to wait |

Reconnection determination signal (choose one): DDS publication-matched listener/timing detection/any RPC timeout 3 times in a row.

#### Multiple clients on the same device

Allows "one rights holder + N read-only observers". Each client uses an independent `Header.clientId` (uint64) and `payload.call.clientId` (string); the response is automatically routed to the correct client via the `clientId` + `requestId` match ([§1.3.1](#131-rpc-channel-request-reply)]).

#### Multiple devices on the same network

Broadcast messages such as `EventMessage_` / `MotionObserved_` / `RemoteControl_` **do not contain the `device_id` field** - all readers in the same Domain will receive broadcasts from all devices. The client must do **application layer filtering**:

- Single device scenario: All broadcasts are owned by the device_id held by the local end
- Multiple devices hold rights at the same time: associate them using the `controller` token (consume an event only when `payload.controller == this client's controller`)

---

## 4. Message format and fields

This chapter is a dictionary of fields for channels outside of RPC - TRC control frames, observations, event schema, error codes. See [§2](#2-business-message-format-specifications) for the RPC business message format, and see [§3.3](#33-detailed-explanation-of-rpc-method) for the params field of each RPC method.

### 4.1 TRC control frame

#### IDL（`uniubi::msg::dds_::RemoteControl_`）

```idl
module uniubi {
  module msg {
    module dds_ {

      struct RemoteControl_ {
          uint64   controller;   // Authorization field: rawActionId from takeMotionControl
          uint64   timestamp;    // Client send time, milliseconds since epoch

          // 16 digital buttons (uint8; 0 = released, 1 = pressed for this frame)
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

          // 6 analog axes (float)
          float    stickLX;      // Stick range [-1.0, 1.0]
          float    stickLY;
          float    stickRX;
          float    stickRY;
          float    triggerL;     // Trigger range [0.0, 1.0]
          float    triggerR;
      };

    };
  };
};
```

#### Key physical mapping

| IDL fields | Physical mapping |
|---|---|
| `back` | Back / Select key |
| `start` | Start key |
| `lb` / `rb` | Left/right shoulder button (Left/Right Bumper) |
| `f1` / `f2` | Function keys 1 / 2 |
| `a` / `b` / `x` / `y` | ABXY key |
| `up` / `down` / `left` / `right` | Directional keys D-Pad |
| `ls` / `rs` | Left / right joystick press (Stick Click) |

#### Joystick/Trigger Mapping

| IDL fields | Physical mapping | Range |
|---|---|---|
| `stickLX` | Left joystick horizontal axis | [-1.0, 1.0] |
| `stickLY` | Left joystick vertical axis (typically forward/backward) | [-1.0, 1.0] |
| `stickRX` | Right joystick horizontal axis | [-1.0, 1.0] |
| `stickRY` | Right joystick vertical axis | [-1.0, 1.0] |
| `triggerL` | Left trigger | [0.0, 1.0] |
| `triggerR` | Right trigger | [0.0, 1.0] |

#### Key combination → Action mapping

TRC frames bear two types of input:
- **Button combination switching action**: Set the buttons in `require` to 1 at the same time and meet `axisRequire` (if any), the corresponding preset action can be triggered (equivalent to `startMotionAction`)
- **Joystick setting real-time control volume**: The joystick/trigger float volume drives the running parameters (equivalent to `setMotionActionParams`, for example, when `walking` is set, `lineVelocityX` / `lineVelocityY` / `velocity` is adjusted by the joystick)

Both types of input can be carried simultaneously in a frame.

The following table completely corresponds to `motionTRC.motionMap.posture` of RobotService `motionCapacity`. The external button name Stand / Motion corresponds to `back` / `start` in DDS, and `buttonBack` / `buttonStart` in SDK respectively; the actual open action and mapping of the device are still subject to the return of `getMotionCapabilities`.

| action | meaning | require | axisRequire | priority | exact | minHoldTime |
|---|---|---|---|---:|---|---:|
| `emergencyStop` | Emergency stop | `lb + rb` | - | 10 | false | 0 |
| `bipedStand` | Standing on two feet | `lb + y` | - | 1 | true | 0 |
| `handstand` | Handstand | `lb + a` | - | 1 | true | 0 |
| `leftSideStand` | Standing on the left side | `lb + x` | - | 1 | true | 0 |
| `rightSideStand` | Standing on the right side | `lb + b` | - | 1 | true | 0 |
| `laying` | Get down | `back + a` | - | 0 | true | 0 |
| `walking` | walking | `back + y` | - | 0 | true | 0 |
| `standing` | standing | `start` | - | 0 | true | 0 |
| `waveBody` | Body swing | `lb + start` | - | 2 | true | 0 |
| `waveHand` | beckoning | `b` | - | 2 | true | 1000 |
| `heartSit` | Sit up and draw the heart | `y` | - | 2 | true | 1000 |
| `tweak` | Stand still / Low speed inching | `a` | - | 2 | true | 1000 |
| `peakLoadStand` | Standing with weight | `start` | - | 2 | true | 0 |
| `jumpForward` | Jump forward | `rb + up` | - | 1 | true | 0 |
| `jumpFrontflip` | Front flip | `rb + y` | - | 1 | true | 0 |
| `jumpSideflip` | Side flip | `rb + b` | `triggerR` in `[-1.0, 0.49]` | 1 | true | 0 |
| `jumpBackflip` | Backflip | `rb + a` | `triggerR` in `[-1.0, 0.49]` | 1 | true | 0 |
| `jumpDoubleBackflip` | Double backflip | `rb + a` | `triggerR` in `[0.5, 1.0]` | 2 | true | 0 |
| `jumpDoubleSideflip` | Bilateral somersault | `rb + b` | `triggerR` in `[0.5, 1.0]` | 2 | true | 0 |

`exact=true` means that no other buttons can be pressed at the same time except `require`; `emergencyStop` is not configured and `exact` is allowed to be triggered with the highest priority even when other buttons appear at the same time. The current `minHoldTime` of `waveHand` / `heartSit` / `tweak` is `1000`, and the rest are `0`.

#### Frame drop conditions

| Condition | Reason |
|---|---|
| `controller != current rawActionId` | Authentication failed |
| The device does not hold the rights / No client holds the rights | The channel is not activated |
| The device does not enable TRC (`rawActionId` is missing or 0 in the `takeMotionControl` response) | The channel is not available |
| QoS mismatch | DDS layer `RequestedIncompatibleQos`, sample not delivered |
| The field range is out of bounds (such as `stickLX = 5.0`) | The device performs range clipping and the behavior is unpredictable |

**Troubleshooting method**: Adjust `queryMotionState` immediately after sending a frame. If `params.action` does not change, it means that the frame has not taken effect.

---

### 4.2 Observations

#### IDL (`uniubi::msg::dds_::MotionObserved_` and its dependencies)

```idl
module uniubi {
  module dds_ {

    struct Vector3f {
        int8        error;       // Per-component error code (0 = normal)
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
        Vector3f    accel;       // Acceleration, m/s²; x=roll/y=pitch/z=yaw
        Vector3f    gyro;        // Angular velocity, rad/s; x=roll/y=pitch/z=yaw
        Vector3f    mag;         // Magnetometer, μT
        Vector3f    euler;       // Euler angles, rad; x=roll[-π,π], y=pitch[-π/2,π/2], z=yaw[-π,π]
        Quaternionf quaternion;  // Unit quaternion
    };

    struct MotorHeader {
        uint32      limbsNo;
        uint32      jointNo;
    };

    struct MotorObserved {
        uint8       enable;
        uint8       online;
        uint8       error;       // Fault code; values below
        float       position;
        float       velocity;
        float       torque;
        float       temp;
        float       voltage;
        float       lossRate;
        float       maxTorque;   // Current motor maximum torque, N·m
        MotorHeader header;
    };

    struct PowerObserved {
        float       power;          // Current battery level, %
        float       health;         // Health, %
        float       temper;         // Battery temperature, °C
        float       chargeCurrent;  // Instantaneous current, A
        float       chargeVoltage;  // Current total voltage, V
    };

  };

  module msg {
    module dds_ {

      const uint32 MAX_MOTOR_NUM = 16;

      struct MotionObserved_ {
          uniubi::dds_::IMUState        imu;
          int32                         motorNum;     // Valid motor count (<= MAX_MOTOR_NUM)
          uint64                        timestamp;    // Monotonic relative timestamp in us; device-internal, not wall time or cross-host aligned
          uniubi::dds_::MotorObserved   motor[MAX_MOTOR_NUM];  // Fixed length 16; only the first motorNum entries are valid
          uniubi::dds_::PowerObserved   power;        // System power/battery state
      };

    };
  };
};
```

> Note: `MotorHeader` of DDS IDL is wire contract, and the field is `uint32 limbsNo/jointNo`. `MotorHeader` in the C++/Python SDK POD is the SDK ABI structure with the field `uint16_t limbNo/jointNo`. The two belong to different boundaries and cannot be mixed directly or converted according to memory layout; when crossing the boundary between DDS and SDK, they must be explicitly converted according to field names and semantics.

#### IMU field dimensions

| Field | Dimension | Description |
|---|---|---|
| `imu.temp` | °C | IMU chip temperature |
| `imu.accel` | m/s² | Three-axis acceleration |
| `imu.gyro` | rad/s | Three-axis angular velocity |
| `imu.mag` | μT | Three-axis magnetometer |
| `imu.euler` | rad | (roll, pitch, yaw)；roll ∈ [-π, π]，pitch ∈ [-π/2, π/2]，yaw ∈ [-π, π] |
| `imu.quaternion` | — | Unit quaternion (w, x, y, z) |

`error` field (`IMUDeviceErrno`) of each `Vector3f` / `Quaternionf`: `0` normal · `1` data invalid · `64` IMU control board offline · `65` control board not ready · `66` control board is being upgraded · `67` module parameters are not ready · `68` heating/not ready. Among them, `0/1` is reported by the IMU, and `64+` is detected and filled in by the SDK/server. Some models of `mag` / `quaternion` are not reported, and `error` is always `1`.

#### Motor field dimension

| Field | Dimension | Description |
|---|---|---|
| `motor[i].enable` | 0/1 | Enable status |
| `motor[i].online` | 0/1 | Online status |
| `motor[i].error` | uint8 | Fault code; 0 = normal, non-0 value, see [§4.4.2](#442-motor-error-subcode) |
| `motor[i].position` | rad | Current joint angle |
| `motor[i].velocity` | rad/s | Current joint angular velocity |
| `motor[i].torque` | N·m | Feedforward torque |
| `motor[i].temp` | °C | Motor temperature |
| `motor[i].voltage` | V | Bus voltage |
| `motor[i].lossRate` | % | Communication packet loss rate |
| `motor[i].maxTorque` | N·m | Current maximum torque of the motor |
| `motor[i].header.limbsNo` | uint32 | Limb number; random numbering rule |
| `motor[i].header.jointNo` | uint32 | Joint number within the limb; random numbering pattern |

`limbsNo` / `jointNo` The specific numbering rules vary randomly. The client should treat each `motor[i]` as an independent entry, look up the table through the `header` field, and do not assume a fixed number or order of motors (such as "quad = 12 = 0..11").

#### Top-level fields

| Field | Dimension | Description |
|---|---|---|
| `motorNum` | int32 | Number of valid motors; specific number is random |
| `timestamp` | us | Device increment relative timestamp (monotonically increasing, not wall clock, do not align across hosts) |
| `motor[16]` | Fixed-length array | Only the first `motorNum` elements are valid |
| `power` | `PowerObserved` | Machine power/battery status, see fields below |

#### Power field dimension

| Field | Dimension | Description |
|---|---|---|
| `power.power` | % | Current battery power |
| `power.health` | % | Battery health |
| `power.temper` | ℃ | Battery temperature |
| `power.chargeCurrent` | A | Real-time current |
| `power.chargeVoltage` | V | Current total voltage |

#### Sensor observation `SensorObserved_` (topic `rt/sensor/observed`)

Carrying GPS / UWB / Walk odometer, independent of `MotionObserved_`, subscription see [§3.5](#35-motion-observation-subscription).

##### IDL (`uniubi::msg::dds_::SensorObserved_` and its dependencies)

```idl
module uniubi {
  module dds_ {

    enum GPSSignalLevel {
        gpsGre38db,   // Strong signal (> 38 dB)
        gpsGre30db,   // Medium signal (> 30 dB)
        gpsLes30db    // Weak signal (<= 30 dB)
    };

    struct GEOGPoint {
        float       lat;        // Latitude, deg
        float       lng;        // Longitude, deg
    };

    struct GPSFrame {
        uint32      valid;      // 1 = valid, 0 = invalid
        float       speed;      // GPS speed, km/h
        int32       level;      // Signal level; see GPSSignalLevel
        int32       rssi;       // Raw signal strength, dBm
        GEOGPoint   point;      // Coordinates
    };

    enum UWBPairState {
        uwbPairNone,      // Not paired
        uwbInPairing,     // Pairing
        uwbPairSuccess,   // Pairing succeeded
        uwbPairFailed     // Pairing failed
    };

    struct UWBRawObserved {
        uint8       valid;      // Whether data is valid
        uint8       pairState;  // Pairing state; see UWBPairState
        int16       rssi;       // Signal strength, dBm
        uint16      pitch;      // Pitch, deg [0, 360)
        uint16      azimuth;    // Azimuth, deg [0, 360); 0 is forward, increasing counterclockwise
        uint32      distance;   // Distance, cm
    };

    typedef float OdomVector3[3];
    struct MotionOdometry {
        uint8       valid;
        uint32      epoch;
        float       yaw;
        float       yawSpeed;
        OdomVector3 position;
        OdomVector3 velocity;
    };

  };

  module msg {
    module dds_ {

      struct SensorObserved_ {
          uint64                          timestamp;  // Monotonic relative timestamp in us; device-internal, not wall time
          uniubi::dds_::GPSFrame          gps;        // GPS observation
          uniubi::dds_::UWBRawObserved    uwb;        // UWB observation
          uniubi::dds_::MotionOdometry    odom;       // Walk planar odometry
      };

    };
  };
};
```

##### GPS field dimensions

| Field | Dimension | Description |
|---|---|---|
| `gps.valid` | 0/1 | 1=GPS is valid in this frame |
| `gps.speed` | km/h | GPS speed measurement |
| `gps.level` | — | Signal level, see `GPSSignalLevel` for values ​​(0 strong / 1 medium / 2 weak) |
| `gps.rssi` | dbm | Original signal strength value |
| `gps.point.lat` | deg | latitude |
| `gps.point.lng` | deg | longitude |

##### UWB field dimensions

| Field | Dimension | Description |
|---|---|---|
| `uwb.valid` | 0/1 | 1=This frame UWB is valid |
| `uwb.pairState` | Enumeration | Pairing status, see `UWBPairState` for the value (0 not paired / 1 pairing / 2 pairing successful / 3 pairing failed) |
| `uwb.rssi` | dbm | signal strength |
| `uwb.pitch` | deg | pitch angle, [0, 360) |
| `uwb.azimuth` | deg | Azimuth angle, [0, 360), 0 degrees directly ahead, increasing counterclockwise |
| `uwb.distance` | cm | distance |

##### Walk odometer field `odom`

| Field | Dimension | Description |
|---|---|---|
| `position[0]` | m | Accumulated X displacement under the current `epoch` origin point |
| `position[1]` | m | Accumulated Y displacement under the current `epoch` origin |
| `position[2]` | — | Reserved field, currently fixed to `0`, does not represent height estimation |
| `velocity[0]` | m/s | X-direction model predicted speed of this system |
| `velocity[1]` | m/s | Y-direction model predicted speed of this system |
| `velocity[2]` | — | Reserved field, currently fixed to `0`, does not represent vertical speed |
| `yaw` | rad | Current accumulated yaw angle at `epoch` origin |
| `yawSpeed` | rad/s | Differential angular velocity of adjacent effective IMU yaw |
| `epoch` | — | The origin generation of the Walking valid interval; incremented when entering Walking again |
| `valid` | — | Whether the current plane odometry frame is valid; does not contain the reserved Z component |

---

### 4.3 Events

See [§1.3.2](#132-event-channel-active-push-by-device) for the IDL and envelope fields of `EventMessage_`. This section defines the schema of `payload` JSON - which varies according to the `EventMessage_.topic` field value (business topic).

> Pay attention to distinguishing two levels of topics: DDS wire-level topic is always `rt/robotServer/Event` ([§1.3.4](#134-topic-summary)). The "business topic" in the table below is the value of the string field `EventMessage_.topic`, and the client is routed to the corresponding handler according to it.

Currently **2 business topics** have been defined (may be added as the device version evolves; the client should tolerate transparent transmission when encountering unknown values):

| `EventMessage_.topic` value | Encapsulation mode | Meaning |
|---|---|---|
| `robotServer.host.event` | Container mode | Business event container; the real business subtopic is in the `event` field inside the payload |
| `robotServer.control.status` | Pass-through mode | Control status change |

#### 4.3.1 Container mode `robotServer.host.event`

**`EventMessage_.payload` Structure**

| Field | Type | Occurrence conditions | Meaning |
|---|---|---|---|
| `caller` | string | always | trigger source (usually empty string `""`) |
| `event` | string | Always | Business topic, the values ​​are shown in the table below |
| `detail` | object | always | business payload, the structure varies according to `event` |

Example:

```jsonc
{
  "caller": "",
  "event":  "statistics/device_status",
  "detail": { "battery": { "power": 85.0 } }
}
```

**Business topic defined**

| `event` value | Trigger condition | `detail` content |
|---|---|---|
| `statistics/device_status` | Battery/network and other subsystem status changes | Single subsystem snapshot (**push in batches**), such as `{"battery":{...}}` or `{"network":{...}}` |
| `statistics/play_list` | Audio playback status changes (start/pause/end/switch song) | Current playback details, the fields are the same as the `getAudioPlayDetail` response, plus the `event` field (the value is like `"changed"`) |

##### `statistics/device_status` field semantics

The fields have the same structure as the `getSystemStatus` response. The server **only pushes down the changed fields**, and the unchanged fields do not appear (not `null`). The client needs to do **partial merge/patch** to maintain a complete status view.

The first full snapshot is actively queried via `getSystemStatus` ([§3.3.4](#334-status-query)).

##### `statistics/play_list` field semantics

The fields have the same structure as the `getAudioPlayDetail` response, with one more `event` field**:

| Field | Type | Meaning |
|---|---|---|
| `event` | string | Event name, the specific enumeration value is defined by the device side (such as `"changed"`) |

#### 4.3.2 Pass-through mode `robotServer.control.status`

**`EventMessage_.payload` Structure**

| Field | Type | Occurrence conditions | Meaning |
|---|---|---|---|
| `controlled` | bool | always | whether the device is currently authorized |
| `controlRole` | string | always | current control role (value such as `"external_high_level"`) |
| `controller` | string | Always | `controller` token of the current rights holder; empty string when no rights are held |
| `controlMode` | string | Current firmware | Current control mode name; earlier firmware may be missing |

```jsonc
{
  "controlled":  true,
  "controlRole": "external_high_level",
  "controller":  "0xGUefQ7T9VWxulv",
  "controlMode": "external_high_level"
}
```

**Trigger time**

- Any client `takeMotionControl` succeeded
- Any client `releaseMotionControl`
- Automatically collect rights when the lease expires on the device side
- Forced release due to malfunction on the device side

**Judgment when `controlled == false`**: If this end is the original right holder (the `controller` and `payload.controller` recorded by this end do not match, or `payload.controller` is an empty string), you should immediately go through the "loss of rights processing" process according to [§3.3.1](#331-session-management).

---

### 4.4 Error code

> For RPC protocol layer code (`System_Response_.code`), see [§1.3.1](#131-rpc-channel-request-reply) "code value".

#### 4.4.1 Business layer payload.code

Business errno always exists in the response payload; `0` indicates business success, non-0 indicates business failure (`payload.result == false` must be used at the same time).

| code(hex) | code(dec) | name | meaning | typical trigger |
|---|---|---|---|---|
| `0x01` | 1 | paramsTypeError | Parameter type error | All methods |
| `0x02` | 2 | paramsDeletion | Parameter missing | All methods |
| `0x03` | 3 | paramsParseError | Parameter parsing error | All methods |
| `0x04` | 4 | paramsOutRange | Parameter out of range | `setCameraLightBrightness` (brightness > 100) |
| `0x05` | 5 | paramsExpired | Parameter expiration (such as time-limited token) | Rights-holding class call |
| `0x06` | 6 | paramsIllegal | Illegal parameters | `startMotionAction` (action name is misspelled) |
| `0x07` | 7 | interfaceNotFound | The interface is not implemented (the routing layer cannot be found) | The old firmware is not registered method |
| `0x08` | 8 | outOfDeviceCaps | Beyond device capabilities | `startMotionAction` (action not in capabilities) |
| `0x09` | 9 | operationTempNotAllow | Operation is currently not allowed | `emergencyStopMotion` Post-cooling period |
| `0x0A` | 10 | methodNotSupport | Method not supported | Device/firmware version old |
| `0x0B` | 11 | deviceNoCapability | The device has no corresponding capability | Some models do not support specific actions |
| `0x0C` | 12 | operateUnsupport | Operation not supported | Configure operations not allowed |
| `0x0E` | 14 | methodNotImpl | The method is not implemented (handler is a protocol placeholder) | Some system setting classes |
| `0x0F` | 15 | interStatusInvalid | Internal status error | Device state machine exception |
| `0x10` | 16 | operatorInvalid | Illegal operator | `renewMotionControl` (lease has expired) |
| `0x12` | 18 | operateTimeout | Operation timeout | Device internal timeout |
| `0x13` | 19 | deviceInBusy | The device is busy | Too many concurrent requests |
| `0x19` | 25 | serviceNotReady | Service not ready | Device startup early |
| `0x1A` | 26 | serviceOffline | The service is not online | The sub-service is down |
| `0x1C` | 28 | noOperationPerm | No operation permission | `payload.call.clientId != controller` |
| `0x1D` | 29 | controlWasSeized | Control rights seized | `takeMotionControl` (held by others) or the local end has been seized |
| `0x1E` | 30 | deviceIsNotBound | The device is not bound | The device has not completed activation |
| `0x1F` | 31 | devIoNodeOccupied | The device node is occupied | The same physical port is occupied by multiple services |
| `0x21` | 33 | fileNotExist | The file does not exist | `deleteAudioFile` / `startPlayList` (wrong id) |
| `0x22` | 34 | openFileFailed | Failed to open file | Same as above |
| `0x23` | 35 | writeFileFailed | File writing failed | Audio upload scenario |
| `0x28` | 40 | dataResourceEmpty | The data resource is empty | `getAudioPlayList` (no audio file) |

#### 4.4.2 Motor error subcode

`MotionObserved_.motor[i].error` field (uint8) value:

| code(dec) | name | meaning | severity |
|---|---|---|---|
| `0` | motorNormal | Normal | — |
| `1` | motorPreDriver | Pre-drive fault (driver level hardware abnormality) | High |
| `2` | motorEcodeError | Encoder failure | High |
| `3` | motorOverSpeed ​​| Overspeed | High |
| `4` | motorOverTempe | Overtemperature (recoverable in a short time) | Medium |
| `5` | motorOverCurrent | Overcurrent | High |
| `6` | motorOverVoltage | Overvoltage | High |
| `59` | motorPGAbnormality | PG abnormality | High |
| `60` | motorHWUndervoltage | Hardware undervoltage | High |
| `63` | motorCommError | Communication error | High |
| `64` | motorControlOffline | Control board offline | Serious (motor lost connection) |
| `65` | controlMotorNotEnable | Not enabled | Medium |
| `66` | motorControlNotReady | Control not ready | Medium |
| `67` | motorControlUpgrade | Upgrading | Medium |
| `68` | motorNoCalibrated | Not calibrated | Serious (configuration problem) |
| `69` | motorURDFNotMapped | Calibration lost | Critical (configuration problem) |

Classified by severity:

- **Recoverable**: `motorOverTempe` (over temperature, recover after cooling down)
- **Stop required**: `motorPreDriver` / `motorEcodeError` / `motorOverSpeed` / `motorOverCurrent` / `motorOverVoltage` / `motorPGAbnormality` / `motorHWUndervoltage` / `motorCommError`
- **Configuration / Lost connection**: `motorControlOffline` / `controlMotorNotEnable` / `motorControlNotReady` / `motorControlUpgrade` / `motorNoCalibrated` / `motorURDFNotMapped`

If **any** non-0 subcode appears, it is recommended to immediately `emergencyStopMotion` and prompt operation and maintenance intervention.

---

## Appendix A Client self-check list

Before the access is completed, please confirm that the client implementation meets the following check items:

**DDS Layer**
- [ ] DDS Domain ID is consistent with the device
- [ ] 6 endpoints have been established and publication / subscription match
- [ ] The QoS of each channel is completely consistent with this protocol [§1.3](#13-category-3-channels) (including `DATA_REPRESENTATION` and `TYPE_CONSISTENCY_ENFORCEMENT`)
- [ ] `Header` type mark `@final` annotation

**RPC envelope layer**
- [ ] `System_Request_.service` Fixed `"robotAppService"`
- [ ] `System_Request_.device_id` Required, not empty
- [ ] `Header.clientId` unique within the process (random uint64 at startup)
- [ ] `Header.requestId` monotonically increases within the session and never repeats
- [ ] response matching (clientId + requestId, [§1.3.1](#131-rpc-channel-request-reply))

**Business layer**
- [ ] The business successfully meets the two-layer determination (`response.code==0` ∧ `payload.result==true`, [§2.1.3](#213-two-level-judgment-of-business-success-or-failure))
- [ ] After successful control, the `payload.call.clientId` of all RPCs is switched to the `controller` field value.
- [ ] Switch back to custom clientId after releasing rights
- [ ] The action list is obtained dynamically through `getMotionCapabilities` and is not hard-coded.

**TRC Channel**
- [ ] `RemoteControl_.controller` field is filled with `rawActionId` (uint64), **not** `controller` token (string)
- [ ] frame push frequency 50–100 Hz
- [ ] Actively send a frame of all 0s when stopping

**Renewal**
- [ ] The background renewal thread has been started, frequency `clamp(leaseTimeout/3, 200ms, 10s)`
- [ ] Failure to renew the contract will be immediately deemed as a loss of rights + trigger the loss of rights processing process

**Motion Observations**
- [ ] Subscribe to reader first and then send `setMotionObservedEnable(motionEnable=true)` (order sensitive)
- [ ] When closing, send `setMotionObservedEnable(motionEnable=false)` first and then destroy the reader

**event**
- [ ] Verification within event callback `magic == 0x53425645`
- [ ] Container mode event (`robotServer.host.event`) is distributed twice as `payload.event`
- [ ] Pass-through mode event (`robotServer.control.status`) is passed to the business handler as it is
- [ ] Unknown `EventMessage_.topic` value Tolerant transparent transmission (new event for forward compatible devices)

**State Machine**
- [ ] Implement the control life cycle process listed in [§3.1](#31-control-life-cycle) (control → business → renewal → release)
- [ ] "Whether control is required" for each RPC (see [§3.2](#32-rpc-method-list) method list) has been strongly verified in the client code
- [ ] Error codes are processed according to the decision table in Appendix D and are not ignored silently.

---

## Appendix B Python access points

Applicable to Python DDS bindings such as `cyclonedds-python`.

### B.1 Access steps

1. **Declare IDL type**: According to the struct definition given in [§1.3](#13-category-3-channels), subclass it with `cyclonedds.idl.IdlStruct`, and explicitly pass in the complete module path for `typename=`
2. **Create DataWriter/DataReader**: Configure item by item according to the QoS table of each channel
3. **Switch to `clientId` after taking control**: `payload.call.clientId` of all RPC-holding RPCs must fill in `controller` in the response
4. **Background renewal thread**: Period `clamp(leaseTimeout/3, 200ms, 10s)`; if failed, press [§3.3.1](#331-session-management) immediately for loss of rights processing process
5. **Event callback**: Verify `magic == 0x53425645` first, and then distribute according to the `EventMessage_.topic` field value

### B.2 cyclonedds-python implementation notes

| Notes | Description |
|---|---|
| `@final` annotation | Must be imported from `cyclonedds.idl.annotations`; used together with `@dataclass`, written after dataclass |
| `typename=` must be passed | Otherwise, the default type name containing the module path will be generated, which does not match the device side |
| `Reliability.Reliable(...)` | is a factory, `max_blocking_time` must be passed; `BestEffort` is a singleton |
| `DataRepresentation` Policy | 0.10.x version uses `use_cdrv0_representation` / `use_xcdrv2_representation` double bool; different minor versions have different APIs |
| Type discovery | Type info will be emitted by default; if it does not match the cyclonedds C++ version of the device, it will be rejected and can be turned off by `cls.__idl__.fill_type_data` |
| Field naming | IDL is camelCase (such as `clientId`); do not rename to snake_case Pythonically, otherwise the wire will not match |

### B.3 Quick verification link

After the access is completed, it is recommended to adjust `getMotionCapabilities` (no rights required) to verify that the DDS link / IDL / QoS / `device_id` are all aligned:

- Receive `code=0` and `result=true` → link pass
- `code=4` and the `device_id` field is not empty → `device_id` is written incorrectly, change it back according to the SN filled in in the response
- No response for 5 seconds → Domain inconsistency/multicast routing failure/topic name misspelling/QoS mismatch

---

## Appendix C C++ access points

The C++ client can choose any OMG DDS implementation: Eclipse Cyclone DDS C++ / RTI Connext / eProsima Fast DDS / OpenDDS.

### C.1 IDL file organization

The IDL file involved in this agreement is released together with the SDK and is located under `IDL/` in the repository root.

File list and include relationship:

| Files | Included Types | Dependencies |
|---|---|---|
| `Request.idl` | `Header` | — |
| `RPCMessage.idl` | `System_Request_` / `System_Response_` | `Request.idl` |
| `EventMessage.idl` | `EventMessage_` | `Request.idl` |
| `MotorState.idl` | `MotorHeader` + constant `MAX_MOTOR_NUM` | — |
| `MotionObserved.idl` | `Vector3f` / `Quaternionf` / `IMUState` / `MotorObserved` / `PowerObserved` / `MotionObserved_` | `MotorState.idl` |
| `SensorObserved.idl` | `GPSSignalLevel` / `GEOGPoint` / `GPSFrame` / `UWBRawObserved` / `SensorObserved_` | — |
| `RemoteControl.idl` | `RemoteControl_` | — |

Copy the .idl file directly from this directory to the project, and use the IDL compiler corresponding to the DDS implementation to generate the C++ type (`idlc -l cxx` for Cyclone DDS C++; `rtiddsgen` for RTI; `fastddsgen` for Fast DDS).

### C.2 Access points

- **IDL `@final` Note**: XTYPES support of the IDL compiler must be turned on; the specific switch varies with the implementation, most support command line options named "IDL4" or "XTYPES"
- **JSON serialization**: The C++ standard library does not have JSON support. `nlohmann/json` or `rapidjson` is recommended.
- **Renewal thread**: implemented with `std::thread` + `std::condition_variable`, cycle `clamp(leaseTimeout/3, 200ms, 10s)`
- **Event subscription callback**: Same as RPC participant but independent reader; **Do not do long-term business processing** within the callback, otherwise it will block the DDS internal thread
- **TRC high-frequency writing**: use independent writer + `BEST_EFFORT` QoS; do not reuse RPC writer, QoS is not compatible
- **Error code constant**: Generate `enum class DeviceErrorCode : uint32_t { ... }` according to [§4.4](#44-error-code) table to facilitate business layer switch processing

### C.3 Notes on different DDS implementations

| Implementation | Notes |
|---|---|
| **Eclipse Cyclone DDS C++ (ddscxx)** | Device-side implementation, the most direct integration; XTYPES annotations are supported by default; namespace `org::eclipse::cyclonedds::dds::*` |
| **RTI Connext** | XTYPES is fully supported; multicast discovery is enabled by default; QoS API style is `DDS_*Qos` structure; commercial authorization |
| **eProsima Fast DDS** | RTPS / simple discovery interoperates with Cyclone DDS by default; XTYPES annotation needs to enable the corresponding option in the IDL compiler |
| **OpenDDS** | Default InfoRepo discovery, interoperability with Cyclone DDS requires switching to RTPS discovery; XTYPES needs to be explicitly enabled when building |

When switching DDS implementations, verify interoperability in the following order:

1. Domain ID is consistent
2. Can SPDP / SEDP multicast interoperate (the same layer 2 network or multicast route is reachable)
3. IDL type `typename` + module path is consistent
4. The QoS of each channel is all matched (including `DATA_REPRESENTATION` / `TYPE_CONSISTENCY_ENFORCEMENT`; RPC channel plus `max_blocking_time`)
5. Run the `getMotionCapabilities` chimney test once and determine the result according to Appendix B.3

---

## Appendix D Error handling decision table and silent failure troubleshooting

### D.1 Error handling decision table

Check the processing action according to the error source. Errors involving control rights are only meaningful when the rights are already held, and the [§3.3.1](#331-session-management) loss of rights processing process must be followed.

| Error source | Processing action |
|---|---|
| **Local timeout** (no response within 5s) | Try again with new `requestId`, and report 3 consecutive failed circuit breakers |
| **RPC code=1 / 2** (device abnormality) | Cannot retry, report to the business layer; control rights must be released when holding rights |
| **RPC code=3 / 4 / 6 / 7** (request format error) | Unable to retry, check the code meaning `method` / envelope / `service` / JSON spelling |
| **RPC code=5** (service not ready) | Back off 1–3s and try again |
| **payload 0x01–0x08** (parameter class) | No retry, check `params` required fields, types, value ranges |
| **payload 0x09** (temporarily not allowed) | Back off 3–5s and try again (typical scenario: `emergencyStopMotion` cooling period) |
| **payload 0x0A / 0x0E** (not supported / not implemented) | Not retryable |
| **payload 0x13** (device busy) | Back off 500ms and try again |
| **payload 0x10 / 0x1C / 0x1D** (right holding exception) | Lost right processing ([§3.3.1](#331-session-management)) |
| **Event `controlled=false`** and this end is the original rights holder | Same as above |
| **`motor[i].error` ≠ 0** | Immediate `emergencyStopMotion` + Alarm |
| **TRC frame has no effect** (`queryMotionState` verification) | Check whether `RemoteControl_.controller` is filled with `rawActionId` (uint64), and whether it currently holds the rights |
| **DDS discovery has not converged for a long time** | Check Domain / Multicast Routing / `device_id` |

**Retry timing**: 1st time 50ms / 2nd time 500ms / 3rd time 2s; 3 consecutive failed circuit breaker reports.

### D.2 Quiet Failure Troubleshooting Checklist

When the device is completely unresponsive (no identifiable signal at the error code level), check the following table:

| Phenomenon | Possible causes |
|---|---|
| RPC cannot receive any response at all | Domain inconsistency / multicast routing unavailable / `device_id` is empty / topic name is misspelled / QoS does not match |
| Response received but device_id does not match | Multiple devices on the same network, the response is crosstalked; check whether the response `device_id` is equal to the request `device_id` |
| TRC frame has no effect | `RemoteControl_.controller` is not filled in `rawActionId` (the `controller` string is filled in incorrectly) / no rights are held / TRC is not enabled on the device |
| Motion observation is not pushed | Unadjusted `setMotionObservedEnable(motionEnable=true)` / reader is subscribed after enable (the first few frames are lost) |
| The event cannot be received | DDS topic `rt/robotServer/Event` is misspelled / `magic` constant is written incorrectly (should be `0x53425645`) / self-end loop-back filtering mistakenly filters out the peer events |
