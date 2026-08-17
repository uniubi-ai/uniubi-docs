# Uniubi Robot High-level C++ API Reference

**English** | [简体中文](high-level.zh-CN.md)

[API Reference](../README.md) · [Python API](../python/high-level.md)

> SDK entry class: `uniubi::RobotSdk::IMotionHighLevelClient`
> C++ header file: `include/uniubi/robot_sdk/MotionHighLevelClient.h`

---

## Table of contents

- [1. SDK overview](#1-sdk-overview)
- [Quick Start: onboard application](#quick-start-onboard-application)
- [Development project template](#development-project-template)
- [2. Enumeration definitions](#2-enumeration-definitions)
- [3. Callback definitions](#3-callback-definitions)
- [4. Interface reference](#4-interface-reference)
- [5. C++ usage examples](#5-c-usage-examples)
- [6. Important considerations](#6-important-considerations)
- [7. Debugging and troubleshooting](#7-debugging-and-troubleshooting)

---

## 1. SDK overview

- Control commands use the control plane, status and data are obtained through query interfaces, and events are delivered through `EventCallback`.
- Control ownership is acquired explicitly with `startControl` and maintained by periodic SDK lease renewal.
- Ownership remains active until `releaseControl()` or `disconnect()` releases it, or until the server session expires.
- Protocol field encoding: UTF-8 JSON string
High-level real-robot applications support two deployment modes. The built-in motion service always remains on the robot.

| Deployment mode | Application and SDK client | Required target information |
|---|---|---|
| External host | Linux PC or industrial computer | Set the host interface that is actually connected to the robot network and create the client with the target device ID (SN). Obtain the SN from the Basic Information page in the Uniubi App or SDK discovery. |
| Onboard | Robot compute module (“brain”) | No device ID is required; use `create(bool asMaster = false)`. |

This boundary is specific to High-level control. For Low-level control on real hardware, the joint-control application still runs onboard.

The remainder of this page focuses on the C++ SDK. See the corresponding API and How-to pages for the external-host Python SDK and ROS 2 paths.

---

## Quick Start: onboard application

Minimal read-only flow (see §5 for the full interactive CLI). This section neither acquires control ownership nor starts an action:

**C++**

```cpp
#include <chrono>
#include <stdexcept>
#include <string>
#include <thread>
#include "uniubi/robot_sdk/MotionSdkService.h"
#include "uniubi/robot_sdk/MotionHighLevelClient.h"

using namespace uniubi::RobotSdk;
using HLState = IMotionHighLevelClient::HighLevelState;

int main() {
    auto svc = IMotionSdkService::instance();
    svc->setNetworkInterface("eth0.100");  // required for onboard High-level communication
    if (!svc->initialService(nullptr, "myReadOnlyApp")) return 1;

    auto client = IMotionHighLevelClient::create();
    try {
        if (!client->connect()) throw std::runtime_error("connect start failed");
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(10);
        while (client->getState() != static_cast<int32_t>(HLState::kConnected)) {
            if (std::chrono::steady_clock::now() >= deadline) {
                throw std::runtime_error("connect timeout");
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }

        std::string capabilities;
        if (!client->getMotionCapabilities(capabilities)) {
            throw std::runtime_error("getMotionCapabilities failed");
        }
    } catch (...) {
        client->disconnect();
        svc->shutdown();
        return 1;
    }
    client->disconnect();
    svc->shutdown();
    return 0;
}
```


### Quick Start: external Linux PC or industrial computer

The built-in motion service remains on the robot. The external C++ application selects its actual robot-facing interface and supplies a device ID (SN) obtained from the Basic Information page in the Uniubi App or SDK discovery:

```cpp
auto svc = IMotionSdkService::instance();
svc->setNetworkInterface("enp3s0");  // actual interface connected to the robot network
if (!svc->initialService(nullptr, "myExternalReadOnlyApp")) return 1;

const std::string targetSn = loadDeviceSnFromConfig();  // App/config/operator selection
auto client = IMotionHighLevelClient::create(targetSn);
if (!client) {
    svc->shutdown();
    return 1;
}
client->setConnectCallback(onConnect);  // register before connect()
if (!client->connect()) {
    svc->shutdown();
    return 1;
}
// Wait for kConnected, then perform read-only queries.
client->disconnect();
svc->shutdown();
```

The following example demonstrates the complete external-host C++ SDK connection flow. Use the corresponding entry points on the Python SDK and ROS 2 pages for those implementations.

---

## Development project template

This minimal project template can be copied as a starting point for an application.

> For complete build instructions (including cross-compilation/wheel packaging/Troubleshooting), see [`BUILD.md`](../../BUILD.md).

### Dependencies

| Dependencies | Source | Description |
|---|---|---|
| `librobotMotionSdk.so` | SDK install prefix `lib/<arch>/` | Precompiled runtime library selected for the target architecture |
| Public headers | SDK install prefix `include/uniubi/robot_sdk/` | `MotionSdkService.h` / `MotionHighLevelClient.h` / `MotionSdkProtocol.h` |
| Compiler | g++ ≥ 9 (supports C++14) | |
| Runtime basic library | Pre-installed on target machine (standard dynamic library path) | No need for customers to install Cyclone DDS additionally - already linked into SDK .so |

### Project directory

```
my_robot_app/
├── CMakeLists.txt
└── src/
    └── main.cpp             ← Application code (see the complete example in §5)
```

### CMakeLists.txt sample

```cmake
cmake_minimum_required(VERSION 3.18)
project(my_robot_app CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(UniubiRobotSdk CONFIG REQUIRED)

add_executable(my_robot_app src/main.cpp)
target_link_libraries(my_robot_app PRIVATE Uniubi::RobotMotionSdk)
```

### Build + Run

```bash
export UNIUBI_SDK_PREFIX=/path/to/installed/uniubi
cmake -S . -B build -DCMAKE_PREFIX_PATH="$UNIUBI_SDK_PREFIX"
cmake --build build -j"$(nproc)"

# Ensure the SDK shared library is on the runtime library path
case "$(uname -m)" in
  x86_64|amd64) SDK_ARCH=x86_64 ;;
  aarch64|arm64) SDK_ARCH=aarch64 ;;
  i386|i486|i586|i686) SDK_ARCH=i386 ;;
  *) echo "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac
export LD_LIBRARY_PATH="$UNIUBI_SDK_PREFIX/lib/$SDK_ARCH${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" ./build/my_robot_app
```

The current device runtime requires root privileges for SDK applications. Building does not require `sudo`. Pass `LD_LIBRARY_PATH` explicitly at runtime because `sudo` may sanitize the current user's environment and otherwise hide the SDK shared library.

---

## 2. Enumeration definitions

### 2.1 `HighLevelState` — Client state

| Value | Meaning |
|---|---|
| `kDisconnected` (0) | Initial state or state after `disconnect()` |
| `kConnected` (1) | SDK connected without control ownership |
| `kControlled` (2) | Control acquired through `startControl()`; actions may be issued |

### 2.2 `HighLevelError` — Failure reason

| Value | Meaning |
|---|---|
| `kNone` | No error |
| `kRpcConnectFailed` | SDK not initialized or communication channel not ready |
| `kRpcAcquireRejected` | `startControl` rejected because control is held elsewhere or the overall timeout elapsed |
| `kRpcCallFailed` | RPC failure, including timeout, channel disconnection, codec error, or ID mismatch |
| `kSessionExpired` | Lease expired and the server reclaimed control |
| `kSessionRevoked` | Control was taken over by another party or the session ID did not match |
| `kNotConnected` | The called interface requires a connected client |
| `kNotControlled` | The called action interface requires control ownership |
| `kDataNotUpdate` | Observation data is not ready, for example because `getPowerInfo` found no data in the freshness window |
| `kActionRejected` | RPC action rejected by server |
| `kInvalidParam` | Illegal input parameter (such as action parameter JSON parsing failed) |

---

## 3. Callback definitions

### 3.1 `ConnectCallback` — Control-state changes

```cpp
using ConnectCallback = std::function<void(HighLevelState state, HighLevelError error)>;
```

Callbacks run on SDK internal threads. Typical events are:

| Trigger | State | Error |
|---|---|---|
| `startControl` succeeds | `kControlled` | `kNone` |
| The client completes `releaseControl` | `kConnected` | `kNone` |
| Overall `startControl` timeout | `kConnected` | `kRpcAcquireRejected` |
| Lease expires | `kConnected` | `kSessionExpired` |
| Another party takes control | `kConnected` | `kSessionRevoked` |

### 3.2 `EventCallback` — Application events

```cpp
using EventCallback = std::function<void(const std::string& topic, const std::string& payloadJson)>;
```

The event-dispatch thread invokes this callback. After `connect()`, the SDK subscribes internally to:

| topic | purpose |
|---|---|
| `statistics/play_list` | Audio playback status changes |
| `statistics/device_status` | Device status changes (battery/network) |

> The SDK consumes control-ownership changes internally and reflects them in `HighLevelState`; they are **not delivered through this callback**.

### 3.3 Callback summary

The table below summarizes the SDK callbacks, their purpose, and their registration interfaces.

| Callback | Purpose | Registration interface |
|---|---|---|
| `LogCallback` | Receive SDK logs for redirection into the application's logging framework | `IMotionSdkService::setLogCallback` |
| `DeviceDiscover` | Receive one callback per robot response during multi-device discovery, with the SN and device-details JSON | `IMotionSdkService::setDiscoverCallback` |
| `ConnectCallback` | Receive control-ownership and connection-state changes to drive the caller's state machine | `IMotionHighLevelClient::setConnectCallback` |
| `EventCallback` | Business events actively pushed by the server (audio status, device status, etc.) | `IMotionHighLevelClient::setEventCallback` |
| `MotionObservedCallback` | Receive `LowLevelMotionObserved` motion observations, including power; enable them first with `setObservedEnable` | `IMotionHighLevelClient::setMotionObservedCallback` |
| `SensorObservedCallback` | Receive complete `SensorObserved` data (GPS / UWB / Walk odometry); enable `sensorEnable` first | `IMotionHighLevelClient::setSensorObservedCallback` |
| `RawAudioFrameCallback` | Receive raw `AudioFrame` data as `(channel, frame)` | `IMediaBusClient::startRawAudioFrame` |
| `RawVideoFrameCallback` | Receive raw `VideoFrame` data as `(channel, frame)` | `IMediaBusClient::startRawVideoFrame` |
| `EncodedVideoFrameCallback` | Receive encoded `EncodedVideoFrame` data as `(channel, frame)` | `IMediaBusClient::startEncodedVideoFrame` |

#### Blocking is strictly prohibited within callbacks

**Never block inside a callback. Callbacks run on SDK or media threads, so blocking also blocks the internal thread:**

- ❌ Do not `sleep`, wait for a mutex, or wait on a condition variable.
- ❌ Do not call synchronous RPC interfaces such as `startControl`, `startAction`, or `queryXxx`.
- ❌ Do not perform disk I/O, network I/O, or large allocations.
- ❌ Do not call `disconnect()` or `shutdown()` on the object.
- ❌ Do not perform lengthy encoding, transcoding, or frame output in a media callback. Hand the required metadata and a data reference or copy to an application worker thread.

**Access raw video by plane and stride.** The platform determines the physical and virtual layout of `VideoFrame`; NVIDIA platforms in particular may use non-contiguous planes. Do not treat `frame.data()` as one contiguous `width * height * bpp` image. Determine the plane count from `VideoFrameInfo.pixelFormat`, then use `virAddr[plane] + row * stride[plane]` to read the valid width row by row.

Blocking an internal thread can stop event delivery, prevent state-machine progress, cause heartbeat expiry and server-side disconnection, and prevent reconnection.

**Correct approach:** perform only lightweight state recording or notification in the callback:

```cpp
client->setConnectCallback([&](HighLevelState s, HighLevelError e) {
    /// ✓ Update an atomic flag
    mLastState.store(s);
    /// ✓ Post a semaphore or notify an application-thread condition variable
    mStateChangedCv.notify_one();
    /// ✓ Enqueue an event for a worker thread
    mEventQueue.push({s, e});
});
```

The application thread performs the actual SDK calls, I/O, and computation after receiving the notification.

---

## 4. Interface reference

### 4.1 Global initialization and instance creation

The SDK implements its RPC control plane and event subscriptions with [Eclipse Cyclone DDS](https://cyclonedds.io/). It constructs the DDS topology internally, including the domain, QoS profile, and client/event subscriptions, so **callers do not need to provide JSON configuration or XML files**. Set the required parameters through the following methods before `initialService()`.

#### 4.1.1 Global initialization

```cpp
bool IMotionSdkService::initialService(const char* file, const char* server, uint32_t timeoutMs = 30000);
```

| Parameters | Type | Description |
|---|---|---|
| `file` | `const char*` | Reserved JSON configuration path. The SDK includes its default DDS configuration; pass `nullptr` |
| `server` | `const char*` | Application identifier, used for RPC/log to distinguish multiple instances (such as `"myAppHighLevel"`), customized by the caller |
| `timeoutMs` | `uint32_t` | Timeout while waiting for the system environment (**milliseconds**, default 30000). Onboard startup may require this wait if the SDK starts before the system services; returns `false` if readiness is not reached in time |

This process-wide initialization must run once before creating any client. A return value of `true` indicates success.

```cpp
/// SDK version string: "<semver> (commit <git-short-sha>)", e.g. "1.0.0 (commit <sha>)"
/// Available at any time without initialService; use it in runtime logs, bug reports, and compatibility checks
static const char* version();
```

> **Version compatibility:** The SDK and robot runtime use OMG XTypes `@appendable`, allowing backward-compatible IDL field additions. A severe version mismatch commonly appears as a silent RPC with no response: DDS reports `RequestedIncompatibleQos` without throwing an exception. Include the `version()` output in the fault report when this occurs.

#### 4.1.2 Setters and queries (call before `initialService`)

```cpp
/// Register the log callback
void setLogCallback(LogCallback cb);

/// Select the SDK network interface before initialization (e.g. "eth0" or "wlan0")
/// Ignored onboard; an external host must set the actual robot-facing interface before initialization
void setNetworkInterface(const char* iface);

/// Register the device-discovery callback for external-host device-addressing mode
/// cb(sn, infoJson): infoJson is a device-details JSON string; typical fields are listed below
void setDiscoverCallback(DeviceDiscover cb);

/// Return whether the current deployment uses external-host device addressing
///   Onboard (SDK and robot on the same machine) -> false
///   External host (even one robot)               -> true
bool isMultiDevice() const;

/// Start one non-blocking device-discovery window
///   - If a discovery window is active, extend it to at least timeoutMs
///   - If the previous window expired, open a new one
/// A true return means only that the request was issued; responses arrive asynchronously through the callback
bool discoverDevices(uint32_t timeoutMs = 10000);
```

##### `setDiscoverCallback` callback parameter `info` schema

`info` is a JSON string that the caller parses. Typical fields are:

| Field | Type | Meaning |
|---|---|---|
| `version` | string | Robot software version |
| `brainVersion` | string | High-level algorithm version |
| `deviceCP` | string | Main control chip identification |
| `deviceModel` | string | Device model |
| `productDate` | string | Production date |
| `network` | object | Network status (same as `querySystemStatus.network`, including `ether` / `hotspot` / `mobile` / `wlan` sub-objects) |

> New fields may be added as device software evolves. Clients must tolerate unknown fields without treating them as errors. See [§4.5.1 `querySystemStatus`](#451-querysystemstatus-fields) for the complete `network` structure.

##### About `setNetworkInterface`

In external-host device-addressing mode, the SDK generates a Cyclone DDS QoS profile at `/tmp/motion_sdk_host_<pid>.xml` and removes it during `shutdown()`. This profile selects the network interface used by DDS:

- The default remains `eth0` for compatibility. High-level applications on the robot brain must call `setNetworkInterface("eth0.100")`; external hosts select the interface that actually reaches the robot network.
- Calling `setNetworkInterface(...)` overrides the default and generates the communication profile for that interface.
- The selected interface must exist and be available, or SDK initialization fails.

##### How to query the available network cards of this machine

Select the appropriate network card name on the host running the SDK (must be the one actually connected to the network segment where the robot is located):

```bash
# Method 1 (recommended): list all interface names and states
ip -br link
#  lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
#  eth0             UP             aa:bb:cc:dd:ee:ff <BROADCAST,MULTICAST,UP>
#  wlan0            UP             aa:bb:cc:dd:ee:01 <BROADCAST,MULTICAST,UP>

# Method 2: inspect addresses and routes to identify the robot-facing interface
ip -br addr
ip route

# Method 3: compatibility with older systems
ifconfig -s

# Method 4: enumerate kernel network devices
ls /sys/class/net/
```

Selection criteria:
1. The status must be `UP`
2. Must have an IP and be in the same LAN as the robot (or the route is reachable)
3. Prefer a wired interface (`eth*` / `enp*`). Wi-Fi (`wlan*`) multicast may be less stable, and DDS discovery can be lost during roaming.
4. **Do not use** `lo` (loopback). Onboard High-level applications use `eth0.100`.

Just pass the selected name directly to `setNetworkInterface("eth0")`.

##### Complete process in multi-device scenario

```cpp
auto svc = IMotionSdkService::instance();

/// 1. Register the discovery callback first, then select the actual interface
svc->setLogCallback(...);
std::atomic<bool> gotResponse{false};
svc->setDiscoverCallback([&](const std::string& sn, const std::string& info) {
    /// Maintain an application device table by parsing deviceModel, network, version, etc. from info JSON
    printf("device online: sn=%s info=%s\n", sn.c_str(), info.c_str());
    gotResponse.store(true);
});
svc->setNetworkInterface("eth0");

/// 2. Initialize the global service
svc->initialService(nullptr, "myApp");

/// 3. Open a full 5 s discovery window; true means only that the request was issued
if (svc->isMultiDevice()) {
    if (!svc->discoverDevices(5000)) return 1;
    std::this_thread::sleep_for(std::chrono::milliseconds(5100));
    if (!gotResponse.load()) {
        svc->discoverDevices(5000);  // retry once after checking interface / robot status
        std::this_thread::sleep_for(std::chrono::milliseconds(5100));
    }
    // Deduplicate by SN and require explicit target selection; never pick the first response implicitly.
    auto client = IMotionHighLevelClient::create(target_sn);
} else {
    auto client = IMotionHighLevelClient::create();   // Onboard single-device overload: create(bool)
}
```

#### 4.1.3 Client instance creation

`create` provides separate overloads for onboard single-device deployment and remote selection by SN:

```cpp
/// Onboard single-device process singleton; asMaster selects the master role
static std::shared_ptr<IMotionHighLevelClient> create(bool asMaster = false);

/// external-host device-addressing mode: create a client for the target robot SN
static std::shared_ptr<IMotionHighLevelClient> create(std::string deviceId);
```

| Overload | Parameters | Description |
|---|---|---|
| `create(bool asMaster = false)` | `asMaster` | **Onboard single-device:** process singleton; `asMaster` selects whether the client joins with the master role |
| `create(std::string deviceId)` | `deviceId` | **External host (device addressed):** target robot SN; an empty string returns `nullptr` |

In external-host device-addressing mode, the SDK inserts `deviceId` into every RPC request for routing, and only the matching robot responds. Each High-level client retains its own target SN, preventing cross-talk between clients.

##### Ways to get `deviceId`

1. **Uniubi App (recommended for first use):** open the robot's **Basic Information** page and copy its Device ID / SN.
2. **SDK device discovery:** register `setDiscoverCallback`, call `discoverDevices(timeoutMs)`, and obtain each SN from the callback. If several robots respond and the target IP is known, parse `info` and match that IP against `network.ether.ipv4Addr`, `network.wlan.ipv4Addr`, `network.hotspot.ipv4Addr`, and `network.mobile.ipv4Addr`. Use the SN from the matching result; the IP itself is not a `deviceId`.
3. **Another trusted source:** if the target SN comes from configuration, user input, a QR code, an asset-management system, or a previous session, call `create(sn)` directly. Calling `discoverDevices` first is unnecessary.

```cpp
/// Example: obtain the SN from application configuration or a deployment manifest
const std::string sn = loadDeviceSnFromConfig();   // Application-defined source
auto client = IMotionHighLevelClient::create(sn);
client->connect();
```

Subsequent `connect`, `startControl`, and action calls follow the normal flow. The SDK routes RPCs directly to that SN. If the robot is absent or does not respond, a failed `connect` reports `kRpcCallFailed` or `kRpcConnectFailed` through `getLastError()`.

### 4.2 Lifecycle and control ownership

| Method | Status Requirements | Description |
|---|---|---|
| `bool connect(int32_t leaseMs = 0)` | Any | Enter High-level mode. For `leaseMs<=0`, the SDK uses 60000 ms. Values outside the valid 5 s to 5 min range are clamped. **`leaseMs` is `int32_t`** |
| `void disconnect()` | Any | Close connection and event subscription |
| `bool startControl(uint32_t timeoutMs = 10000)` | Connected | Request control asynchronously; `timeoutMs` is the overall deadline in milliseconds |
| `bool releaseControl()` | `kControlled` | Asynchronous release, the state switches back to `kConnected` after completion |
| `int32_t getState() const` | Any | Current `HighLevelState` |
| `int32_t getLastError() const` | Any | Return the latest failure reason and clear it after reading |
| `void setConnectCallback(ConnectCallback cb)` | `kDisconnected` | Must register before connect |
| `void setEventCallback(EventCallback cb)` | `kDisconnected` | Must register before connect |
| `IMediaBusClient::Ptr createMediaBusClient()` | Any | Create audio and video channel client (see §4.6 for details) |

### 4.3 Motion-control actions

#### 4.3.1 Control methods (require `kControlled`)

| Method | Purpose |
|---|---|
| `bool emergencyStop(uint32_t timeoutMs = 5000)` | Emergency stop |
| `bool recoveryStand(uint32_t timeoutMs = 5000)` | Return to standing after falling (self-righting + standing up) |
| `bool startAction(const std::string& action, const std::string& paramsJson = "", uint32_t timeoutMs = 5000)` | Start an action. Fields in `paramsJson` must match the action's `params` list from `getMotionCapabilities()`; pass `""` for one-shot actions without parameters |
| `bool stopAction(uint32_t timeoutMs = 5000)` | Stop current action |
| `bool setActionParams(const std::string& paramsJson = "", uint32_t timeoutMs = 5000)` | Update current action parameters without switching actions. The action's `params` list from `getMotionCapabilities` defines adjustable fields. Uses **full rewrite semantics**: omitted fields return to 0 |
| `bool damp(uint32_t timeoutMs = 5000)` | Enter low-stiffness damping mode so the robot can settle under controlled resistance |
| `bool lieDown(uint32_t timeoutMs = 5000)` | Lie down |
| `bool standUp(uint32_t timeoutMs = 5000)` | Stand |
| `bool move(float vx, float vy, float vyaw, uint32_t timeoutMs = 5000)` | Walking command: `vx` longitudinal velocity (positive forward), `vy` lateral velocity, and `vyaw` yaw rate; remains active until `stopAction` or a subsequent action/parameter update |

`stopAction()` stops the current action through the server's asynchronous finalization path, then returns the effective action to `walking` with all three walking velocities set to zero while retaining control. Starting `walking` with full zero parameters is the equivalent explicit way to end the current action. `/cmd_vel` or `setActionParams()` updates the current action's supported parameters (including speed parameters for actions such as `bipedStand` and `handstand`); it does not switch actions.

**Action safety classification**

- For initial hardware integration, complete read-only checks first, then call `startAction("walking", R"({"lineVelocityX":0.0,"lineVelocityY":0.0,"velocity":0.0})")` to validate ownership, action startup, and status feedback.
- Before triggering any action other than `laying`, call the zero-velocity `walking` transition above and poll `queryMotionState()` until the effective action is `walking`; only then call the target action. `laying` does not require this preliminary transition.
- `standUp()` / `lieDown()` and the corresponding `standing` / `laying` actions depend on the current posture and server state machine, so they are not a universal round-trip test; for example, `standing` cannot be triggered directly from `laying`.
- `walking` / `move` with nonzero velocity, plus `bipedStand` / `handstand` / `waveBody` / `peakLoadStand` / `jumpFrontflip` / `jumpSideflip` / `jumpBackflip` / `jumpDoubleBackflip` / `jumpDoubleSideflip` / `damp`, are high-risk motion actions. Run them only in an open area with stable robot posture and manual takeover available.
- `emergencyStop`, audio playback/pause/stop, audio-file management, and camera-light brightness are not high-risk motion actions, but their control-ownership and interface prerequisites still apply.

#### 4.3.1.1 `walking` action parameters (`startAction` / `setActionParams`)

The server reports each action's adjustable parameters dynamically. Query `getMotionCapabilities()` and use the returned `params` entries (`name`, `min`, `max`, and `unit`) instead of hard-coding them. One-shot actions such as `jumpBackflip` usually have no adjustable parameters.

`walking` commonly exposes the following fields; always use the current values returned by `getMotionCapabilities()`:

| paramsJson field | type | meaning | unit |
|---|---|---|---|
| `controlProfile` | string | Walking control profile: currently `"slow"` (default) or `"fast"` | — |
| `velocity` | float | **Yaw rate**; positive turns left, negative turns right | rad/s |
| `lineVelocityX` | float | Longitudinal velocity, positive forward and negative backward | m/s |
| `lineVelocityY` | float | Lateral velocity, positive right and negative left | m/s |

The three velocity keys match both `getMotionCapabilities().actions[].params[].name` and the
velocity fields returned by `queryMotionState()`. `controlProfile` separately takes the profile
name string; numeric IDs in the capability configuration are internal values, not RPC inputs.

**Example**:

```json
// Move forward at 0.5 m/s
{"lineVelocityX": 0.5, "lineVelocityY": 0.0, "velocity": 0.0}

// Turn left in place at 0.5 rad/s
{"lineVelocityX": 0.0, "lineVelocityY": 0.0, "velocity": 0.5}

// setActionParams fully rewrites the parameters; resend all three fields to preserve existing values
{"lineVelocityX": 0.8, "lineVelocityY": 0.0, "velocity": 0.0}

// Switch to the fast profile at zero velocity; use a string, not internal numeric ID 1
{"controlProfile": "fast", "lineVelocityX": 0.0, "lineVelocityY": 0.0, "velocity": 0.0}
```

**Parameter semantics:**

- **Full velocity rewrite:** `setActionParams()` and `startAction()` rebuild the numeric action parameters, so omitted velocity axes become 0. To change yaw while preserving X velocity, resend all three velocity fields. `controlProfile` changes only when a valid profile-name string is supplied explicitly.
- **Server-side clamping:** values outside the `min`/`max` range reported by `getMotionCapabilities()` are clamped to the nearest boundary without an error.
- **Zero velocity is not an action stop:** use `stopAction()` to stop the current action; sending all-zero velocity fields only clears its velocity parameters.
- **Independent axes:** combine the three fields as needed, for example `{lineVelocityX: 0.5, velocity: 0.3}` to move forward while turning.
- **Profile names are strings:** use `"slow"` or `"fast"` for `controlProfile`. Sending numeric `0` or `1` is rejected as a parameter type error. Switch profiles with all three axes at zero, wait for a successful response and stable posture, and then increase velocity gradually. Some server versions do not return the profile name in motion-state JSON.

**C++ calling example**:

```cpp
// Start walking and set velocity immediately
client->startAction("walking", R"({"lineVelocityX":0.5,"lineVelocityY":0.0,"velocity":0.0})");

// Adjust velocity at runtime (full rewrite; include every field that must be preserved)
client->setActionParams(R"({"lineVelocityX":0.8,"lineVelocityY":0.0,"velocity":0.0})");

// Switch to the fast profile at zero velocity
client->setActionParams(R"({"controlProfile":"fast","lineVelocityX":0.0,"lineVelocityY":0.0,"velocity":0.0})");

// Stop
client->stopAction();
```

#### 4.3.2 Query methods (require `kConnected`)

| Method | Result |
|---|---|
| `bool queryMotionState(std::string& out, uint32_t timeoutMs = 5000)` | Current effective motion action and commanded velocity as JSON; see the schema below |
| `bool getMotionCapabilities(std::string& out, uint32_t timeoutMs = 5000)` | Supported actions, controller mappings, and adjustable parameters as JSON; see the schema below |
| `bool getMotorLayout(MotorLayout& layout, uint32_t timeoutMs = 5000)` | Motor count and each motor's `limbNo`, `jointNo`, and `name`; available after `kConnected` and cached by the SDK |

##### `queryMotionState` response example

```json
// Active action
{
  "action":        "walking",
  "velocity":       0.0,
  "lineVelocityX":  0.5,
  "lineVelocityY":  0.0
}

// No active action (after stopAction or before startAction)
{}
```

| Field | Type | Description |
|---|---|---|
| `action` | string | Currently effective action name from the latest motion-control cycle |
| `velocity` | float | Current angular velocity (rad/s) |
| `lineVelocityX` | float | Current longitudinal velocity (m/s) |
| `lineVelocityY` | float | Current lateral velocity (m/s) |

> The return value reports RPC success, while `out` reports motion state:
> - `false`: the RPC failed because the client was not connected, the call timed out, or the channel was unavailable. Call `getLastError()` for the error code.
> - `true`: the RPC succeeded. If there is no active action, `out` is `{}`; callers must not assume that action fields are present.

##### `getMotionCapabilities` parameter output example

```json
{
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
```

| Field | Type | Description |
|---|---|---|
| `actions[].name` | string | Action name passed to `startAction()` |
| `actions[].mapping.require` | array<string\> | `ButtonDefine` names that must be pressed to trigger the action |
| `actions[].mapping.axisRequire` | array<object\> | Additional axis conditions; each entry contains an `AxesDefine` name plus `min` and `max` |
| `actions[].mapping.priority` | integer | Priority when multiple mappings match in one frame; larger values take precedence |
| `actions[].mapping.exact` | bool | If `true`, no buttons other than those in `require` may be pressed |
| `actions[].mapping.minHoldTime` | number | Minimum hold time; currently reported as `0` |
| `actions[].params` | array<object\> | Adjustable runtime parameters; omitted for one-shot actions |
| `params[].name` | string | JSON key used by `startAction()` and `setActionParams()` |
| `params[].min/max` | float | Supported value range; the server clamps out-of-range values |
| `params[].unit` | string | Unit such as `"m/s"` or `"rad/s"`; omitted when not configured |

### 4.4 Audio Player

Audio playback is controlled directly through the High-level client:

```cpp
client->startAudioPlay(R"({"list":[{"id":"1"}],"volume":50,"repeat":1})");
```

#### 4.4.1 Control methods (require `kControlled`)

| Method | Parameters | Purpose |
|---|---|---|
| `bool startAudioPlay(const std::string& paramsJson, uint32_t timeoutMs = 5000)` | See the table below | Start, resume, or update playback according to the supplied fields |
| `bool stopAudioPlay(uint32_t timeoutMs = 5000)` | — | Stop playback |
| `bool pauseAudioPlay(uint32_t timeoutMs = 5000)` | Sends `{"pause":true}` internally | Pause playback; resume with `startAudioPlay()` and `{"resume":true}` |
| `bool addAudioFile(const std::string& paramsJson, uint32_t timeoutMs = 30000)` | `{"id":"custom_1","name":"hello.mp3","file":"/data/hello.mp3"}` or URL form | Add custom audio file |
| `bool deleteAudioFile(const std::string& paramsJson, uint32_t timeoutMs = 5000)` | `{"id":"1"}` | Delete the specified audio ID |

**`startAudioPlay.paramsJson` form**

| Operation | `paramsJson` |
|---|---|
| Start playlist | `{"list":[{"id":"1"},{"id":"2"}],"volume":50,"repeat":1}` |
| Adjust volume | `{"volume":50}` |
| Resume playback | `{"resume":true}` |
| Change repeat count | `{"repeat":-1}` (`-1` repeats indefinitely; positive values specify a count; `0` has no effect) |

#### 4.4.2 Query methods (require `kConnected`)

| Method | `paramsJson` input | `out` result (UTF-8 JSON) |
|---|---|---|
| `bool queryAudioPlayDetail(std::string& out, uint32_t timeoutMs = 5000)` | — | See 4.4.2.1 |
| `bool queryAudioPlayList(std::string& out, const std::string& paramsJson = "", uint32_t timeoutMs = 5000)` | `{"type":"customVoice"}` | See 4.4.2.2 |

##### 4.4.2.1 `queryAudioPlayDetail` response fields

```json
{
  "channel": 0,
  "playing": true,
  "paused": false,
  "repeat": 1,
  "index": 0,
  "count": 2,
  "volume": 50,
  "currentId": "audio_1",
  "list": ["audio_1", "audio_2"]
}
```

| Field | Type | Description |
|---|---|---|
| `channel` | int | Playback channel, the meaning is defined by the device side |
| `playing` | bool | Whether it is playing |
| `paused` | bool | Whether it is in paused state |
| `repeat` | int | Repeat configuration: `-1`=infinite loop; `>0`=number of loops; `0` meaningless |
| `index` | int | Current playback index, starting from 0 |
| `count` | int | Total number of current playlists |
| `volume` | int | Current volume, range 0~100 |
| `currentId` | string | Currently playing audio ID |
| `list` | array<string\> | Current playlist, the element is audio ID |

##### 4.4.2.2 `queryAudioPlayList` parameter field

```json
{
  "customVoice": [
    {
      "id": "1",
      "name": "walk",
      "duration": 12,
      "size": 320000,
      "createAt": 1712745600000,
      "describe": "示例备注"
    }
  ],
  "remaining": 20
}
```

| Field | Type | Description |
|---|---|---|
| `customVoice` | array<object\> | Array of audio files, each item is shown in the table below |
| `customVoice[].id` | string | Audio ID |
| `customVoice[].name` | string | audio name |
| `customVoice[].duration` | int | Duration (seconds) |
| `customVoice[].size` | int | File size (bytes) |
| `customVoice[].createAt` | int64 | Creation timestamp (milliseconds) |
| `customVoice[].describe` | string | Remarks |
| `remaining` | int | The remaining uploadable quantity/capacity quota, the precise semantics are defined by the device side |

#### 4.4.3 Real-time reporting of playback status (via `EventCallback`)

| topic | payload encoding |
|---|---|
| `statistics/play_list` | UTF-8 JSON text |

**payload example**:

```json
{
  "event": "changed",
  "channel": 0,
  "playing": true,
  "paused": false,
  "repeat": 1,
  "index": 0,
  "count": 2,
  "volume": 50,
  "currentId": "audio_1",
  "list": ["audio_1", "audio_2"]
}
```

**Field**: Same as 4.4.2.1 `queryAudioPlayDetail` parameter; one more `event` field:

| Field | Type | Description |
|---|---|---|
| `event` | string | Event name, the specific enumeration value is defined by the device side (such as `"changed"`) |

#### 4.4.4 Raw audio frame subscription

The original audio frame has been unified to `IMediaBusClient` (see §4.6). After getting the channel through `client->createMediaBusClient()`, subscribe to `startRawAudioFrame(channel, cb)`. The frame type is `AudioFrame` of MediaBus:

```cpp
auto media = client->createMediaBusClient();
media->setup();
bool ok = media->startRawAudioFrame(0, [](int32_t channel, const AudioFrame& frame) {
    const auto& info = frame.getFrameInfo();
    printf("audio ch=%d size=%u rate=%u bit=%u channels=%u ts=%llu seq=%llu\n",
           channel,
           frame.size(),
           info.sampleRate,
           info.sampleFormat,
           info.channelCount,
           static_cast<unsigned long long>(info.timestamp),
           static_cast<unsigned long long>(info.sequence));

    // PCM data: frame.data(), frame.size()
});

// Stop the subscription before exit or when it is no longer needed
media->stopRawAudioFrame(0);
```

`AudioFrame` inherits from `Uface::Media::MediaBuffer`:

| Field/Method | Description |
|---|---|
| `frame.data()` / `frame.size()` | Audio raw data pointer and number of bytes, usually PCM |
| `frame.getFd()` | Associated file descriptor when the platform uses shared memory or DMA; availability is platform-dependent |
| `frame.getFrameInfo()` | Return `AudioFrameInfo` |
| `AudioFrameInfo.sampleRate` | Sampling rate, such as 8000 / 16000 |
| `AudioFrameInfo.sampleFormat` | Sampling bit width, such as 8 / 16 |
| `AudioFrameInfo.channelCount` | Number of channels, common 1 / 2 |
| `AudioFrameInfo.dataType` | Data type, 0 means PCM, 1 means WAV |
| `AudioFrameInfo.timestamp` / `sequence` | Timestamp and frame number |

> SDK/MediaBus manages the `AudioFrame` lifetime. To use its data after the callback returns, copy `frame.size()` bytes from `frame.data()` during the callback. Do not retain a view unless its lifetime is explicitly guaranteed.

### 4.5 System and device

| Method | Status | Description |
|---|---|---|
| `bool querySystemStatus(std::string& out, uint32_t timeoutMs = 5000)` | `kConnected` | Output parameter JSON, including two sub-objects `battery` + `network`, see 4.5.1 |
| `bool setObservedEnable(const std::string& json, std::string& ret, uint32_t timeoutMs = 5000)` | `kControlled` | Enable or disable motion and complete sensor observations; control must be acquired first. `ret` returns the switches actually in effect. See §4.7 |

Camera-light brightness is controlled directly through the High-level client:

```cpp
client->setCameraLightBrightness(50);
```

| Method | Status | Description |
|---|---|---|
| `bool getCameraLightBrightness(std::string& out, uint32_t timeoutMs = 5000)` | `kControlled` | Return camera-light brightness as JSON in `out` |
| `bool setCameraLightBrightness(int32_t brightness, uint32_t timeoutMs = 5000)` | `kControlled` | Set camera-light brightness to an integer from 0 to 100 |

#### 4.5.1 `querySystemStatus` fields

```json
{
  "battery": {
    "abnormalStatus": 0,
    "statusCode": 0,
    "cycleCount": 186,
    "remainChargeTime": 52,
    "remainDischargeTime": 198,
    "power": 76.5,
    "health": 93.2,
    "temperature": 31.4,
    "fullCharge": 5180.0,
    "remaining": 3962.7,
    "current": 1.84,
    "voltage": 15.28
  },
  "network": {
    "ether":   { "enable": true,  "ipv4Addr": "...", "ipv4Gateway": "...", "ipv4Mask": "...", "mac": "...", "status": 0 },
    "hotspot": { "enable": false, "ipv4Addr": "...", "ipv4Gateway": "...", "ipv4Mask": "...", "mac": "...", "status": 1 },
    "mobile":  { "enable": true,  "ipv4Addr": "...", "ipv4Gateway": "...", "ipv4Mask": "...", "mac": "...", "signalLevel": 0, "simCardSta": true, "status": 0 },
    "wlan":    { "enable": true,  "ipv4Addr": "...", "ipv4Gateway": "...", "ipv4Mask": "...", "mac": "...", "status": 0 }
  }
}
```

**`battery` field description**:

| Field | Type | Unit | Meaning |
|---|---|---|---|
| `abnormalStatus` | uint8 | — | Power-circuit fault flag; nonzero indicates a fault |
| `statusCode` | uint16 | — | BMS status bitmask (see the table below) |
| `cycleCount` | uint16 | cycles | Accumulated charge/discharge cycles |
| `remainChargeTime` | uint16 | min | Estimated time to full charge; valid while charging |
| `remainDischargeTime` | uint16 | min | Estimated remaining runtime at the current load |
| `power` | float | % | State of charge, range 0–100 |
| `health` | float | % | Battery state of health, range 0–100 |
| `temperature` | float | °C | Battery temperature |
| `fullCharge` | float | mAh | Full charge capacity |
| `remaining` | float | mAh | Remaining capacity |
| `current` | float | A | Battery current; positive while charging, negative while discharging |
| `voltage` | float | V | Total battery voltage |

**`battery.statusCode` bit mask** (`statusCode & bit != 0` indicates that the corresponding protection bit is valid):

| bit | value | meaning |
|---|---|---|
| bit0 | 0x0001 | pack undervoltage protection |
| bit1 | 0x0002 | cell under-voltage protection |
| bit2 | 0x0004 | pack overvoltage protection |
| bit3 | 0x0008 | cell overvoltage protection |
| bit4 | 0x0010 | Charging ends |
| bit5 | 0x0020 | Discharge overcurrent protection |
| bit6 | 0x0040 | Charging overcurrent protection |
| bit7 | 0x0080 | Short circuit protection |
| bit8 | 0x0100 | Discharge low temperature protection |
| bit9 | 0x0200 | Charging low temperature protection |
| bit10 | 0x0400 | Discharge high temperature protection |
| bit11 | 0x0800 | Charging high temperature protection |
| bit12 | 0x1000 | MOS high temperature protection |
| bit13 | 0x2000 | Cell collection disconnection protection |
| bit14 | 0x4000 | Cell voltage imbalance protection |
| bit15 | 0x8000 | Cell voltage failure protection |

**`network.<iface>.status` values:**

| Value | Meaning |
|---|---|
| `0` | Connected |
| `1` | Disconnected |
| `2` | Connecting |

**`network.mobile.signalLevel` values** (present only in the `mobile` object):

| Value | Meaning |
|---|---|
| `0` | Good signal (> 22dB) |
| `2` | Moderate signal (> 15dB) |
| `3` | Poor signal (≤ 15 dB) |

`network.mobile.simCardSta`: `true` means the SIM card is ready, `false` means not inserted/not recognized.

#### 4.5.2 Real-time reporting of system status (via `EventCallback`)

| topic | payload encoding | trigger |
|---|---|---|
| `statistics/device_status` | UTF-8 JSON text | On demand, only push changed fields |

**payload example** (only when `network.ether.ipv4Addr` changes):

```json
{
  "network": {
    "ether": { "enable": true, "ipv4Addr": "192.168.51.149", "ipv4Gateway": "192.168.50.1", "ipv4Mask": "255.255.254.0", "mac": "e0:3c:1c:b8:ea:60", "status": 0 }
  }
}
```

**Fields:** the payload uses the same structure as §4.5.1. The server **publishes only changed fields**; unchanged fields are omitted rather than set to `null`. Callers must merge each payload as a partial update.

### 4.6 Audio and video channels (`IMediaBusClient`)

`IMediaBusClient` provides raw video, encoded video, and raw audio subscriptions. Obtain it through `client->createMediaBusClient()` and subscribe after `setup()`. **Media subscriptions are independent of motion control ownership**, so `startControl()` is not required.

```cpp
auto media = client->createMediaBusClient();
media->setup();

// Query the media hardware layout (microphone, camera, and encoder counts)
MediaLayout layout = {};
media->getMediaLayout(layout);

// Raw frame: VideoFrame
media->startRawVideoFrame(0, [](int32_t channel, const VideoFrame& frame) {
    const auto& info = frame.getFrameInfo();
    printf("video raw ch=%d size=%u %ux%u fmt=%d ts=%llu seq=%llu\n",
           channel,
           frame.size(),
           info.width,
           info.height,
           static_cast<int>(info.pixelFormat),
           static_cast<unsigned long long>(info.timestamp),
           static_cast<unsigned long long>(info.sequence));
});

// Encoded frame: EncodedVideoFrame
media->startEncodedVideoFrame(0, [](int32_t channel, const EncodedVideoFrame& frame) {
    const auto* info = reinterpret_cast<const Uface::Stream::FrameInfo*>(frame.getExtraData());
    printf("video encoded ch=%d size=%d frameType=0x%02x seq=%d\n",
           channel,
           frame.size(),
           frame.getFrameType(),
           frame.getSequence());
    if (info) {
        printf("codec=%u %ux%u\n",
               info->detail.video.encode,
               info->detail.video.width,
               info->detail.video.height);
    }
});

media->stopEncodedVideoFrame(0);
media->stopRawVideoFrame(0);
media->shutdown();
```

| Method | Description |
|---|---|
| `bool setup()` | Initialize media bus connection (must be called before subscribing) |
| `void shutdown()` | Disconnect the media bus and stop all subscriptions |
| `int32_t getLastError() const` | Reason for the last failure (`MediaBusError`) |
| `bool getMediaLayout(MediaLayout& layout)` | Query the audio and video hardware layout (`micNum` / `cameraNum` / `videoEncoderNum`) |
| `bool startRawVideoFrame(int32_t channel, RawVideoFrameCallback cb)` | Subscribe to raw video frames; an empty `cb` returns `false`; signature `(int32_t channel, const VideoFrame&)` |
| `void stopRawVideoFrame(int32_t channel)` | Stop a raw video subscription |
| `bool startEncodedVideoFrame(int32_t channel, EncodedVideoFrameCallback cb)` | Subscribe to encoded video frames; signature `(int32_t channel, const EncodedVideoFrame&)` (**no stream parameter**) |
| `void stopEncodedVideoFrame(int32_t channel)` | Stop an encoded video subscription |
| `bool startRawAudioFrame(int32_t channel, RawAudioFrameCallback cb)` | Subscribe to raw audio frames; signature `(int32_t channel, const AudioFrame&)` |
| `void stopRawAudioFrame(int32_t channel)` | Stop a raw audio subscription |

`MediaBusError` (`getLastError` return value):

| Value | Meaning |
|---|---|
| `kNone` | No error |
| `kNotSetup` | Not started (the subscription/query interface is called without `setup`) |
| `kConfigLoadFailed` | Failed to load media configuration |
| `kConfigInvalid` | The media configuration is missing required fields such as `streamDefine` |
| `kMediaInitFailed` | Failed to initialize media streaming service |
| `kMediaStartFailed` | Failed to start media streaming service |
| `kInvalidChannel` | Illegal channel number (< 0 or ≥ corresponding hardware quantity) |
| `kInvalidCallback` | Frame callback is empty |
| `kSourceUnavailable` | Encoding source unavailable (creation failed / no video track) |
| `kSourceStartFailed` | Failed to start encoding source |

**`VideoFrame` raw frame format**

> **Important: Video frame data must be accessed according to plane and stride. ** `width` / `height` represents the effective image size, `stride[plane]` represents the actual span of each row of the plane, which is usually greater than or equal to the number of valid row bytes; multi-plane formats should also use the corresponding `virAddr[plane]`. It cannot be assumed that `frame.data()` is a complete continuous image, nor can `width * height` read the entire frame at one time.

`VideoFrame` inherits from `Uface::Media::MediaBuffer`:

| Field/Method | Description |
|---|---|
| `frame.data()` / `frame.size()` | Data pointer and number of bytes; some platforms may only guarantee the continuity of the 0th plane |
| `frame.getFd()` | If the underlying layer uses shared memory/DMA, the associated fd can be returned; if there is no fd, it is determined by the platform |
| `frame.getFrameInfo()` | Return `VideoFrameInfo` |
| `VideoFrameInfo.width` / `height` | Effective image width and height |
| `VideoFrameInfo.pixelFormat` | Pixel format, see `Uface::Media::MediaPixelFormat` |
| `VideoFrameInfo.stride[3]` | Horizontal span of each plane / actual span of each row, unit byte |
| `VideoFrameInfo.virAddr[3]` | Virtual address of each plane; multi-plane format should be read first according to plane address + stride |
| `VideoFrameInfo.timestamp` / `sequence` | Timestamp and frame number |

Access instructions:

```cpp
const auto& info = frame.getFrameInfo();
const uint8_t* y = info.virAddr[0] ? info.virAddr[0] : frame.data();
for (uint32_t row = 0; row < info.height; ++row) {
    const uint8_t* line = y + static_cast<size_t>(row) * info.stride[0];
    // Process only the valid info.width; do not treat stride padding as image data
    processLine(line, info.width);
}
```

The original video frame of the NVIDIA platform may be multi-plane and the memory is not continuous. When saving/processing, be sure to read the valid data per plane and line by line according to `VideoFrameInfo.virAddr[plane]` and `stride[plane]`. See `Examples/example_media_frames.cpp` for complete processing logic.

**`EncodedVideoFrame` encoded frame format**

Encoded video uses `EncodedVideoFrame`, the SDK's public alias for `Uface::Stream::CMediaFrame`; there is no additional `VideoPacket` wrapper:

| Field/Method | Description |
|---|---|
| `frame.getBuffer()` / `frame.size()` | Encoded data pointer and number of bytes |
| `frame.getFrameType()` | Frame type, common `videoIFrame` / `videoPFrame` / `videoBFrame` / `imageFrame` |
| `frame.getPts()` / `frame.getUtc()` / `frame.getSequence()` | PTS / UTC / Encoding frame number |
| `frame.getExtraData()` | `Uface::Stream::FrameInfo` expansion head |
| `FrameInfo.detail.video.encode` | Encoding type, see `Uface::Media::VideoEncode`, such as H264 / H265 / MJPEG / JPEG |
| `FrameInfo.detail.video.width` / `height` | Encoded image width and height |
| `FrameInfo.detail.video.fpsNum` / `fpsDen` | Frame rate numerator / denominator |

The complete C++ test program is `Examples/example_media_frames.cpp`. It subscribes to raw audio, raw video, and encoded video simultaneously and saves ten frames of each stream to `/tmp/media_frame_dump`.

### 4.7 Observation data path

High-level clients can enable observation reporting and receive motion observations (IMU, motors, and power) and complete sensor observations (GPS, UWB, and Walk odometry) through callbacks:

1. Register `setMotionObservedCallback` / `setSensorObservedCallback` before `connect`;
2. call `connect()`;
3. call `startControl()` and wait for the target endpoint to complete the master-role switch and enter `kControlled`;
4. call `setObservedEnable(json, ret)` with the JSON switches; `ret` returns the switches currently in effect;
5. the server publishes frames through `MotionObservedCallback` and `SensorObservedCallback`;
6. read through `sensor.gps` / `sensor.uwb` / `sensor.odom` or the `getSensorObservation` cache; use `getPowerInfo` for power;
7. disable observation reporting before calling `releaseControl()`.

| Method | Status | Description |
|---|---|---|
| `bool setObservedEnable(const std::string& json, std::string& ret, uint32_t timeoutMs = 5000)` | `kControlled` | Observation reporting switch. `startControl()` switches the target endpoint to the master role before acquiring control; a slave endpoint does not own motor/IMU data and cannot provide valid motion observations. Calling this method while only `kConnected` is rejected with `kActionRejected` |
| `void setMotionObservedCallback(MotionObservedCallback cb)` | Any | Register the motion-observation callback with signature `void(const LowLevelMotionObserved&)`, including power |
| `void setSensorObservedCallback(SensorObservedCallback cb)` | `kDisconnected` | Register full sensor observation callback, signature `void(const SensorObserved&)`; data includes GPS, UWB and odometry |
| `bool getSensorObservation(SensorObserved* sensor, uint32_t timeoutMs = 5000)` | `kConnected` | Read the complete sensor observation cache without sending RPC; `timeoutMs` is the data freshness window (ms) |
| `bool getPowerInfo(PowerObserved* power, uint32_t timeoutMs)` | `kConnected` | Read the latest power observation. **First enable motion observations with `setObservedEnable({"motionEnable":true})`**, because power is carried in motion-observation frames. Without fresh data the method returns `false`. `timeoutMs` is the **freshness window in milliseconds (ms)**; data newer than this window returns `true`, otherwise `false` with `getLastError()` → `kDataNotUpdate` |

`setObservedEnable` input parameter JSON switch field:

| Field | Type | Meaning |
|---|---|---|
| `motionEnable` | bool | Enable motion observations (IMU + motors + power) delivered to `setMotionObservedCallback` |
| `sensorEnable` | bool | Enable sensor observations (GPS + UWB + Walk odometry) delivered to `setSensorObservedCallback` |

**Observation data type** (fields are subject to `MotionSdkProtocol.h`):

- `LowLevelMotionObserved`: `systemSta`/`motorNum`/`imu` (`IMUObserved`)/`trc` (`TRCStickFrame`)/`power` (`PowerObserved`)/ `motors[]` (`MotorObserved`). For the semantics of each substructure field, please refer to the low-level SDK manual.
- `MotionOdometry`: `position[0:2]` is the cumulative plane position under the current `epoch` origin, `velocity[0:2]` is the speed predicted by the robot system model; `yaw` / `yawSpeed` are the cumulative yaw angle and yaw angular velocity respectively. The odometer is only available in Walk mode. When exiting Walk, retain the end value of the current interval and set `valid` to false; when entering Walk again, automatically establish a new origin and increment `epoch`. `position[2]` / `velocity[2]` is currently fixed to `0` and should not be interpreted as altitude or vertical speed.
- The external publishing frequency is configured by `odometry.publishFrequencyHz` of the walking action in `motionCapacity`, and the default is `50 Hz`; model inference and internal integration frequency are not affected by this configuration.
- `SensorObserved.gps` (`GPSFrame`): `valid` (1=valid)/`speed` (km/h)/`level` (signal level, see `GPSSignalLevel`)/`rssi` (original value of signal strength, unit dbm)/ `point` (`GEOGPoint`, including `lat` / `lng`, unit deg).
- `PowerObserved`: `power` (power %) / `health` (health %) / `temper` (battery temperature ℃) / `chargeCurrent` (real-time current A) / `chargeVoltage` (current total voltage V).

```cpp
client->setMotionObservedCallback([](const LowLevelMotionObserved& obs) {
    // ✓ Record lightweight state or notify an application thread; never block here
});
client->setSensorObservedCallback([](const SensorObserved& sensor) {
    const GPSFrame& gps = sensor.gps;
    const MotionOdometry& odom = sensor.odom;
    // ✓ Keep callback work lightweight; read GPS, UWB, and odometry from sensor
    printf("gps=%u epoch=%u x=%.3f y=%.3f yaw=%.3f valid=%u\n",
           gps.valid, odom.epoch, odom.position[0], odom.position[1], odom.yaw, odom.valid);
});
std::string observedState;
client->setObservedEnable(R"({"motionEnable":true,"sensorEnable":true})", observedState);
// observedState returns the switches currently in effect, e.g. {"motionEnable":true,"sensorEnable":true}

PowerObserved power = {};
if (client->getPowerInfo(&power, /*timeoutMs=*/200)) {
    printf("battery=%.1f%% voltage=%.2fV\n", power.power, power.chargeVoltage);
}
```

---

## 5. C++ usage examples

Complete runnable example: `Examples/example_highlevel.cpp` (corresponding `CMakeLists.txt` in the same directory)

```cpp
#include <chrono>
#include <thread>
#include <cstdio>
#include <string>
#include "uniubi/robot_sdk/MotionSdkService.h"
#include "uniubi/robot_sdk/MotionHighLevelClient.h"

using namespace uniubi::RobotSdk;
using HLState = IMotionHighLevelClient::HighLevelState;
using HLError = IMotionHighLevelClient::HighLevelError;

static void onConnect(HLState state, HLError err) {
    switch (state) {
        case IMotionHighLevelClient::kControlled:
            printf("[high] control acquired\n");
            break;
        case IMotionHighLevelClient::kConnected:
            if (err == HLError::kSessionExpired)          printf("[high] lease expired\n");
            else if (err == HLError::kSessionRevoked)     printf("[high] preempted\n");
            else if (err == HLError::kRpcAcquireRejected) printf("[high] startControl rejected\n");
            else                                          printf("[high] released\n");
            break;
        default: break;
    }
}

static void onEvent(const std::string& topic, const std::string& payload) {
    if (topic == "statistics/play_list")          printf("[evt] play: %s\n", payload.c_str());
    else if (topic == "statistics/device_status") printf("[evt] dev:  %s\n", payload.c_str());
}

int main(int argc, char** argv) {
    auto svc = IMotionSdkService::instance();
    svc->setNetworkInterface(argc > 1 ? argv[1] : "eth0");   // external host: actual interface; onboard High-level: eth0.100

    if (!svc->initialService(nullptr, "myAppHighLevel")) return 1;

    std::string deviceId;
    if (svc->isMultiDevice()) {
        fprintf(stderr, "external-host device-addressing mode: use discoverDevices() first to obtain a SN\n");
        svc->shutdown();
        return 1;
    }
    auto client = IMotionHighLevelClient::create(deviceId);
    client->setConnectCallback(&onConnect);
    client->setEventCallback(&onEvent);

    if (!client->connect()) {                          // SDK default lease: 60 s
        IMotionSdkService::instance()->shutdown();
        return 1;
    }

    // Queries that do not require control ownership
    std::string caps, sysStatus;
    client->getMotionCapabilities(caps);
    client->querySystemStatus(sysStatus);

    // Acquire control ownership
    if (!client->startControl(10000)) {
        client->disconnect();
        IMotionSdkService::instance()->shutdown();
        return 1;
    }
    while (client->getState() != IMotionHighLevelClient::kControlled)
        std::this_thread::sleep_for(std::chrono::milliseconds(50));

    // Motion, audio, and observation reporting
    client->startAction("walking", "");
    std::this_thread::sleep_for(std::chrono::seconds(5));
    client->stopAction();

    client->startAudioPlay(R"({"list":[{"id":"1"}],"volume":50,"repeat":1})");
    std::this_thread::sleep_for(std::chrono::seconds(2));
    client->pauseAudioPlay();
    client->stopAudioPlay();

    std::string observedState;
    client->setObservedEnable(R"({"motionEnable":true,"sensorEnable":true})", observedState);
    std::this_thread::sleep_for(std::chrono::seconds(2));
    client->setObservedEnable(R"({"motionEnable":false,"sensorEnable":false})", observedState);

    // Exit with explicit release, disconnect, and shutdown
    client->releaseControl();
    client->disconnect();
    IMotionSdkService::instance()->shutdown();
    return 0;
}
```

### 5.2 Media frame subscription example

Full runnable example: `Examples/example_media_frames.cpp`.

```bash
# Omit config or pass "-" to use the SDK's built-in MediaBus configuration
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  ./example_media_frames [config|-] [client_id] [device_id|-] [video_channel] [audio_channel] [stream] [seconds] [network_iface|-]

# Typical: subscribe to channel=0, audio_channel=0, and the main stream for 10 seconds
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  ./example_media_frames - mediaFrameExample - 0 0 0 10 eth0
```

Output content:

- Create channel via `client->createMediaBusClient()` and `setup()`
- Subscribe to `VideoFrame` original video frame (`startRawVideoFrame`)
- Subscribe to encoded `EncodedVideoFrame` data (`startEncodedVideoFrame`, callback signature `(channel, frame)`)
- Subscribe to raw `AudioFrame` data (`startRawAudioFrame`)
- By default, 10 frames of each of the first three categories are saved to `/tmp/media_frame_dump`
- raw video save logic is written plane by plane and line by line according to `virAddr[] + stride[]`, compatible with NVIDIA non-contiguous memory

### 5.3 External-host example (device addressing)

Register the discovery callback first, set the actual robot-facing interface, and only then initialize the service. A `true` return from `discoverDevices` means only that the request was issued; responses arrive asynchronously.

The example deduplicates callbacks by SN, waits 5 seconds, and retries once if no callback arrives. It only prints discovery results and never creates a client or acquires control. If the robot IP is already known, match it against `network.ether.ipv4Addr`, `network.wlan.ipv4Addr`, `network.hotspot.ipv4Addr`, or `network.mobile.ipv4Addr` in `info` to identify the corresponding SN. The IP filters discovery results; the final High-level client is still created with the SN.

```cpp
#include <chrono>
#include <mutex>
#include <thread>
#include <map>
#include <cstdio>
#include "uniubi/robot_sdk/MotionSdkService.h"
#include "uniubi/robot_sdk/MotionHighLevelClient.h"

using namespace uniubi::RobotSdk;

int main(int argc, char** argv) {
    auto svc = IMotionSdkService::instance();

    if (argc < 2) {
        fprintf(stderr, "usage: %s <robot-facing-interface>\n", argv[0]);
        return 2;
    }

    /// 1) Store the latest info JSON for each SN; callback work stays lightweight
    std::mutex devMutex;
    std::map<std::string, std::string> devices;
    svc->setDiscoverCallback([&](const std::string& sn, const std::string& info) {
        std::lock_guard<std::mutex> lk(devMutex);
        devices[sn] = info;
    });

    svc->setNetworkInterface(argv[1]);  // actual robot-facing interface, before init
    if (!svc->initialService(nullptr, "myMultiApp")) return 1;

    if (!svc->isMultiDevice()) {
        fprintf(stderr, "current deployment is single-device, use §5.1 instead\n");
        svc->shutdown();
        return 1;
    }

    /// 2) true means only that the request was issued; responses arrive via callback
    if (!svc->discoverDevices(5000)) {
        fprintf(stderr, "failed to issue discovery request\n");
        svc->shutdown();
        return 1;
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(5100));

    std::map<std::string, std::string> snapshot;
    { std::lock_guard<std::mutex> lk(devMutex); snapshot = devices; }
    if (snapshot.empty()) {
        fprintf(stderr, "no callback in 5 s; check interface / robot status and retry\n");
        svc->discoverDevices(5000);
        std::this_thread::sleep_for(std::chrono::milliseconds(5100));
        { std::lock_guard<std::mutex> lk(devMutex); snapshot = devices; }
    }
    if (snapshot.empty()) {
        fprintf(stderr, "no device discovered, check network interface / robot status\n");
        svc->shutdown();
        return 1;
    }
    printf("found %zu device(s)\n", snapshot.size());
    for (const auto& [sn, info] : snapshot) {
        printf("SN=%s info=%s\n", sn.c_str(), info.c_str());
    }
    printf("Choose an SN explicitly, or match the known robot IP against "
           "network.*.ipv4Addr, then use that SN in the external-host Quick Start.\n");

    /// Discovery only: do not create a client, acquire control, or select a robot automatically.
    svc->shutdown();
    return 0;
}
```

---

## 6. Important considerations

1. **Callback registration:** register `setConnectCallback` and `setEventCallback` before `connect()`; callbacks registered after connection do not take effect.
2. **Callback thread:** `ConnectCallback` and `EventCallback` run on an internal SDK thread. Do not block that thread or call non-reentrant SDK operations from a callback.
3. **State queries:** `getState()` and `getLastError()` are thread-safe; reading `getLastError()` clears the stored error.
4. **Default lease:** `connect(0)` requests the 60-second default. The server clamps the effective lease to the supported range of 5 seconds to 5 minutes.
5. **Control ownership:** action methods (`emergencyStop`, `startAction`, `stopAction`, audio control, and camera-light control) require `kControlled`; otherwise they return `false` and set `kNotControlled`.
6. **Interface not yet public:** The current High-level SDK does not expose motion-control master-role query or switching. This capability will be added after the High-level service contract is finalized.

---

## 7. Debugging and troubleshooting

### 7.1 Minimum robot-side verification

Before calling the SDK, verify the robot-side service and network path so that server-side failures are not misdiagnosed as client problems.

| Check items | Command/Method | Expected results |
|---|---|---|
| The network is reachable | `ping <robot IP>` | There is a packet return and the delay is stable |
| Network card multicast capability | `ip -d link show <iface>` | flag contains `MULTICAST,UP` |
| DDS Discovery traffic | `sudo tcpdump -i <iface> 'udp and (port 7400 or port 7401)'` | The client can see bidirectional SPDP packets after starting |
| Firewall | `sudo iptables -L` / `ufw status` | Block UDP multicast without rules / port 7400+ |

Robot side (if the device can be logged in):

```bash
# 1) Confirm the process is running
ps -ef | grep robotServer

# 2) Check DDS discovery ports
sudo ss -lup | grep -E '7400|7401'

# 3) Follow runtime logs (adapt the path to your deployment)
journalctl -u robotServer -f
```

### 7.2 Troubleshooting common phenomena on the SDK side

| Phenomenon | Check items | Solution ideas |
|---|---|---|
| `initialService` returns false | Log `errorf` output | See error code: `kRpcConnectFailed` → DDS domain cannot be started (network card/multicast/domain id is incorrect) |
| `discoverDevices` The callback did not come in once after being triggered | 1. Whether setNetworkInterface has selected the network card <br>2 that can reach the robot. Whether `isMultiDevice()` returns true<br>3. Whether the `robotServer.discoverDevice.request` topic on the robot side is subscribed | The network card must be correctly specified in external-host device-addressing mode; if isMultiDevice returns false Description The SDK self-checks into on-board mode and should not go through the discover process |
| `create(sn)` returns nullptr | SDK reports external-host device addressing but deviceId is empty | External-host deviceId must be non-empty (empty is allowed only on the board) |
| After `connect()`, the state has stopped at `kDisconnected` | 1. Check the error code <br>2 pushed by ConnectCallback. Whether `tcpdump` has packets in both directions <br>3. Is the SN assigned to `checkDeviceId` on the robot side consistent with what you passed | `kRpcConnectFailed` → DDS channel / robotServer RPC has not started yet; deviceId does not match → robot filter silently discards all requests |
| `startControl` did not transition to `kControlled` | 1. Error reported by `ConnectCallback`<br>2. Whether another client took control | `kRpcAcquireRejected` → control held elsewhere or acquisition timeout; `kSessionRevoked` → another client took over |
| Action class interface (`startAction` / `setActionParams` / `stopAction`) returns false, state displays `kControlled` | `getLastError()` value | `kSessionExpired` → lease expires; `kSessionRevoked` → is taken over; `kActionRejected` → Rejected by the server (processed according to business code) |
| **Silent no response** (timeout for any interface) | DDS QoS incompatibility (most common) | Client/server IDL versions or Cyclone DDS versions are inconsistent; use `ddsperf sanity` for minimum handshake verification |

### 7.3 Open SDK internal log

```cpp
IMotionSdkService::instance()->setLogCallback([](IMotionSdkService::LogLevel lv,
                                                  const char* msg, int32_t len) {
    static const char* tags[] = {"DBG","TRC","INF","WRN","ERR","FAT"};
    fprintf(stderr, "[sdk %s] %.*s\n", tags[lv], len, msg);
});
```

When the callback is not registered, the SDK outputs the log to `stdout` by default. For production environments, it is recommended to connect to your own log system for centralized viewing.

---
