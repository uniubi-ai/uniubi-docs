# Uniubi Robot Low-level C++ API Reference

**English** | [简体中文](low-level.zh-CN.md)

[API Reference](../README.md) · [Python API](../python/low-level.md)

> SDK entry class: `uniubi::RobotSdk::IMotionLowLevelClient`
> C++ header file: `include/uniubi/robot_sdk/MotionLowLevelClient.h`

---

## Table of contents

- [1. SDK Overview](#1-sdk-overview)
- [Quick Start](#quick-start)
- [Development project template](#development-project-template)
- [2. Enumeration definition](#2-enumeration-definition)
- [3. Callback definition](#3-callback-definition)
- [4. Interface definition](#4-interface-definition)
- [5. C++ usage examples](#5-c-usage-examples)
- [6. Precautions](#6-precautions)
- [7. Debugging and Troubleshooting](#7-debugging-and-troubleshooting)

---

## 1. SDK Overview

- Supports **single-device, on-board deployment only**: the SDK and MotionServer run on the same computer and connect through local services (no remote, UDP, or multi-device mode).
- The control plane uses RPC, and the data plane uses on-board shared memory (SHM), both of which use binary structures directly instead of JSON.
- The `IMotionLowLevelClient::create()` factory takes no arguments. Repeated calls within one process return the same process-wide singleton.
- The SDK manages control acquisition and renewal internally. Applications use only `setMotionEnable(true/false)` to enter or leave the prepared state.
- The SDK advances the state machine internally; callers observe it through `ConnectCallback` or `getState()`.

---

## Quick Start

Minimal read-only flow (see §5 for the full interactive CLI). This section only connects and queries the motor layout; it does not call `setMotionEnable(true)` or send control frames:

**C++**

```cpp
#include <chrono>
#include <stdexcept>
#include <thread>
#include "uniubi/robot_sdk/MotionSdkService.h"
#include "uniubi/robot_sdk/MotionLowLevelClient.h"

using namespace uniubi::RobotSdk;
using LLState = IMotionLowLevelClient::LowLevelState;

int main() {
    auto svc = IMotionSdkService::instance();
    if (!svc->initialService(nullptr, "myReadOnlyApp")) return 1;

    auto client = IMotionLowLevelClient::create();
    try {
        if (!client->connect(/*observedHz=*/500)) {
            throw std::runtime_error("connect start failed");
        }
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(10);
        while (client->getState() != static_cast<int32_t>(LLState::kConnected)) {
            if (std::chrono::steady_clock::now() >= deadline) {
                throw std::runtime_error("connect timeout");
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }

        MotorLayout layout = {};
        if (!client->getMotorLayout(layout)) {
            throw std::runtime_error("getMotorLayout failed");
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


## Development project template

This is the smallest buildable project template. Copy it, add the application code, then build and run it.

> For complete build instructions (including cross-compilation/wheel packaging/Troubleshooting), see [`BUILD.md`](../../BUILD.md).

### Dependencies

| Dependencies | Source | Description |
|---|---|---|
| `librobotMotionSdk.so` | SDK install prefix `lib/<arch>/` | Precompiled runtime library selected for the target architecture |
| Public headers | SDK install prefix `include/uniubi/robot_sdk/` | `MotionSdkService.h` / `MotionLowLevelClient.h` / `MotionSdkProtocol.h` |
| Compiler | g++ ≥ 9 (supports C++14) | |
| Runtime basic library | Pre-installed on target machine (standard dynamic library path) | No need for customers to install Cyclone DDS additionally - already linked into SDK .so |

### Project directory

```
my_robot_app/
├── CMakeLists.txt
└── src/
    └── main.cpp             # Application code; see the complete example in §5
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

# Ensure that the SDK shared libraries are on the runtime search path
case "$(uname -m)" in
  x86_64|amd64) SDK_ARCH=x86_64 ;;
  aarch64|arm64) SDK_ARCH=aarch64 ;;
  i386|i486|i586|i686) SDK_ARCH=i386 ;;
  *) echo "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac
export LD_LIBRARY_PATH="$UNIUBI_SDK_PREFIX/lib/$SDK_ARCH${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" ./build/my_robot_app
```

The current device requires root permissions to run the SDK program. `sudo` is not required for the build; `LD_LIBRARY_PATH` is explicitly passed in during runtime to avoid `sudo` from not being able to find the SDK dynamic library after cleaning up the current user environment.

---

## 2. Enumeration definition

### 2.1 `LowLevelState` — Client state

| Value | Meaning |
|---|---|
| `kDisconnected` (0) | Initial / After `disconnect()` |
| `kConnecting` (1) | First connection attempt (not connected yet) |
| `kConnected` (2) | The control plane + data plane channel is ready, but prepare is not turned on → `sendControl` is invalid |
| `kPrepared` (3) | `sendControl` will be adopted by the server only if prepare is enabled |
| `kConnectionLost` (4) | Once connected/prepared, due to session failure/server abnormal disconnection, the SDK is automatically reconnecting |

### 2.2 `LowLevelError` — Failure reason

| Value | Meaning |
|---|---|
| `kNone` | No error |
| `kRpcConnectFailed` | SDK is not initialized or the communication channel is not ready |
| `kRpcAcquireRejected` | The request to obtain control was rejected by the server (occupied by others/the server is unreachable) |
| `kPrepareRejected` | Motion-control switch request failed |
| `kSessionExpired` | The session expired and was recycled by the server |
| `kSessionReleased` | The session was actively released by the server |
| `kServerStop` | The server actively closes the channel |
| `kRpcCallFailed` | RPC call failure (including timeout/channel disconnection/codec error/id mismatch, etc.)|
| `kNotConnected` | The interface requires an established connection |
| `kNotPrepared` | Currently not prepared, control cannot be issued |
| `kInvalidArgument` | Invalid argument, such as `motorNum == 0` or `motorNum > kLowLevelMaxMotorNum` |
| `kMasterSwitchFailed` | Failed to switch the local end to the motion-control master during connection (the other end is still in operation control/rejected by the server) |

### 2.3 `MotionControlMode` — Motion-control execution mode

Identifies whether motion control runs on the main computer or the motion controller. This enum remains defined in `MotionSdkProtocol.h`, but **no current client API returns it**. The Low-level SDK only exposes `restoreMotionControlMode()` to restore the default motion-control mode.

| Value | Meaning |
|---|---|
| `cerebellumMode` (0) | Motion-controller execution |
| `brainControlMode` (1) | Main-computer execution |
| `motionModeNotReady` (255) | Motion-control mode is not ready |

---

## 3. Callback definition

### 3.1 `ConnectCallback` —— Status change

```cpp
using ConnectCallback = std::function<void(LowLevelState state, LowLevelError error)>;
```

Callbacks are triggered by SDK internal threads. Any session exception (expiration/release/server outage) will be regarded as a logical disconnection, and the state will be transferred to `kConnectionLost`. The SDK will automatically try to reconnect, and return to `kConnected` after success.

Typical timing:

| trigger scene | state | error |
|---|---|---|
| Failed to switch motion-control master | `kConnecting` | `kMasterSwitchFailed` |
| Control plane + data plane connection established successfully | `kConnected` | `kNone` |
| `setMotionEnable(true)` Success | `kPrepared` | `kNone` |
| `setMotionEnable(false)` Success | `kConnected` | `kNotPrepared` |
| Session expiration | `kConnectionLost` | `kSessionExpired` |
| The server actively stops the service | `kConnectionLost` | `kServerStop` |

### 3.2 Callback summary

The SDK exposes a total of 2 callbacks. The registration timing and usage are shown in the table below.

| Callback | Purpose | Registration interface |
|---|---|---|
| `LogCallback` | Receive SDK internal log output (debugging/operation and maintenance can be redirected to your own log framework) | `IMotionSdkService::setLogCallback` |
| `ConnectCallback` | Connection/prepare state changes (connection establishment/session exceptions, etc.), driving the caller state machine | `IMotionLowLevelClient::setConnectCallback` |

#### Blocking is strictly prohibited within callbacks

**It is strictly prohibited to perform any blocking operations within the body of all callback functions - callbacks are triggered by SDK internal threads, and blocking will directly block the internal threads**:

- ❌ cannot `sleep` / wait for mutex / wait for condvar
- ❌ Cannot adjust any synchronous RPC interface (`emergencyStop` / `getMotorLayout`, etc.)
- ❌ Cannot do disk IO / network IO / large memory allocation
- ❌ Cannot `disconnect()` / `shutdown()` this object

The consequences of internal threads being stuck are chain-linked: the delivery of observation frames stops, the state machine no longer advances, the heartbeat times out and the server kicks it off, and the reconnection process cannot be started.

**Correct approach**: Only do "lightweight recording/notification" in the callback:

```cpp
client->setConnectCallback([&](LowLevelState s, LowLevelError e) {
    /// ✓ Set an atomic flag
    mLastState.store(s);
    /// ✓ Post a semaphore or notify_one a condition variable for the application thread
    mStateChangedCv.notify_one();
    /// ✓ Enqueue an event for an application worker thread
    mEventQueue.push({s, e});
});
```

The business thread performs actual processing after sensing the signal (including detuning the SDK interface, IO, calculation, etc.).

---

## 4. Interface definition

### 4.1 Global initialization and instance creation

The RPC control plane and event subscription of the SDK are implemented based on [Eclipse Cyclone DDS](https://cyclonedds.io/). The DDS topology (domain, QoS profile, client/event subscription declaration) is constructed internally by the SDK, and **the caller does not need to prepare JSON configuration or XML files**. Developers only need to pass in the necessary parameters before `initialService` through the following setters.

#### 4.1.1 Global initialization

```cpp
bool IMotionSdkService::initialService(const char* file, const char* server, uint32_t timeout = 30);
```

| Parameters | Type | Description |
|---|---|---|
| `file` | `const char*` | Reserved: JSON configuration file path. The current SDK default DDS configuration has been built in, just pass `nullptr` |
| `server` | `const char*` | Application identifier, used for RPC/log to distinguish multiple instances (such as `"myAppLowLevel"`), customized by the caller |
| `timeout` | `uint32_t` | Timeout waiting for the system environment to be ready (** seconds **, default 30). In on-board mode, if the SDK starts earlier than the system environment, you may need to wait; if it times out and is not ready, it will return `false` |

Process-level one-time initialization, must be called before any client is created. Returning `true` indicates successful initialization.

```cpp
/// SDK version string: "<semver> (commit <git-short-sha>)", for example "1.0.0 (commit <sha>)"
/// Available before initialService; suitable for runtime logs, bug reports, and compatibility checks
static const char* version();
```

> **Version Compatibility**: The SDK and the robot side agree to OMG XTYPES `@appendable` (the IDL field can be appended, backward compatible). If the SDK is seriously inconsistent with the robot version, the typical phenomenon is that the RPC call/data plane binary package is silently unresponsive (DDS reports `RequestedIncompatibleQos` but does not throw an error). When this phenomenon occurs, paste the `version()` output into the fault report.

#### 4.1.2 setter / query interface (must be called before `initialService`)

The low-level SDK is only deployed on a single device on the board, without the need for remote capabilities such as network interface selection/device discovery, and only log callback registration is retained:

```cpp
/// Register the log callback before initialService
void setLogCallback(LogCallback cb);
```

> `setNetworkInterface` / `setDiscoverCallback` / `isMultiDevice` / `discoverDevices` and other interfaces only serve the advanced remote mode, and the low-level SDK on the board is not involved.

#### 4.1.3 Client instance creation

```cpp
static std::shared_ptr<IMotionLowLevelClient> create();
```

No factory parameters, directly connected to the local MotionServer. The low-level SDK is **on-board process-level singleton**: calling `create()` multiple times in the same process returns the same instance. Returns a null pointer on failure.

```cpp
auto svc = IMotionSdkService::instance();
svc->initialService(nullptr, "myAppLowLevel");
auto client = IMotionLowLevelClient::create();
```

### 4.2 Life cycle and status switching

| Method | Status Requirements | Description |
|---|---|---|
| `bool connect(uint32_t observedHz = 500, uint32_t leaseMs = 0)` | Any | Non-blocking, the connection is automatically completed by the SDK. `observedHz`: expected observation frequency; `leaseMs`: control lease (ms), 0 = use the server default value (the server clamps/verifies the real value according to its own policy, and the SDK renews the contract according to the real value) |
| `void disconnect()` | Any | Close the connection; idempotent |
| `bool setMotionEnable(bool enable)` | `kConnected` / `kPrepared` | **Asynchronous**: Only record the intent, the SDK cuts `kConnected ↔ kPrepared` and callback after the RPC is completed |
| `bool emergencyStop(uint32_t timeout = 5000)` | `kPrepared` | Emergency stop (synchronous RPC, timeout unit ms) |
| `int32_t getState() const` | Any | Current `LowLevelState` |
| `int32_t getLastError() const` | Any | The last failure reason for clearing after reading |
| `void setConnectCallback(ConnectCallback cb)` | Any | Registration status callback |
| `IMediaBusClient::Ptr createMediaBusClient()` | Any | Create an audio and video frame subscription channel; only used for local media frame subscription on the `aarch64` board (see the MediaBus documentation for usage) |
| `bool restoreMotionControlMode(uint32_t timeout = 5000)` | `kConnected` | Restore the motion-control mode to the factory default; synchronize RPC, timeout unit ms |

#### `connect`’s timeout and retry strategy (important)

- The SDK does not set an overall timeout for the connect process, and will retry in an infinite loop according to the built-in backoff policy until it succeeds or is explicitly interrupted by `disconnect()`
- `ConnectCallback(state, error)` will be triggered every time an intermediate link fails, and the caller can sense the progress accordingly.
- If the caller needs "N seconds/N failed attempts to give up" semantics, he or she can accumulate the number of failures in `ConnectCallback` or compare it with the wall time. When the threshold is reached, `disconnect()` is called to terminate (the SDK will not give up on its own initiative and gives the caller full decision-making power)
- **Impotent for weight retry**: The SDK generates a stable token when the instance is created and carries it with the right request; if the server has successfully granted but the reply is lost on the link, the SDK will identify the server as the same caller when retrying the right, **reuse the original `sessionId` and refresh the lease and return successfully**, and will not be permanently stuck by `controlWasSeized` due to its last success. The token is an internal detail of the SDK and the caller does not need to be aware of it.

### 4.3 Data plane interface

| Method | Status Requirements | Description |
|---|---|---|
| `bool sendControl(const MotorCtrlAction& action, const LowLevelMotionCmd* cmd = nullptr)` | `kPrepared` | Send a frame of control; action-related control frames are recommended to be transmitted to `cmd`, and fill in `action` and `acName` at the same time; `motorNum` must ∈ `[1, kLowLevelMaxMotorNum]`, otherwise `kInvalidArgument` will be returned |
| `bool sendMaxTorque(const MotorCtrlAction& action)` | `kPrepared` | Set the maximum torque of the motor; use each element of `header` to position the motor and `torque` to carry the target upper limit; `motorNum` must ∈ `[1, kLowLevelMaxMotorNum]`, otherwise `kInvalidArgument` |
| `bool getLatestObservation(LowLevelMotionObserved* obs, uint32_t timeout)` | `kPrepared` | Obtain one frame of motion observation (motor/IMU/TRC/power supply) within the specified `timeout` (**ms**); return false if not obtained |
| `bool getSensorObservation(SensorObserved* sensor, uint32_t timeout)` | `kConnected` / `kPrepared` | Read GPS + UWB sensor observations; Walk odometry is not provided. The call is independent of prepare; `timeout` is in **us**; without sensor hardware it waits until timeout and returns false |
| `bool getMotorLayout(MotorLayout& layout, uint32_t timeout = 5000)` | `kConnected` | Hardware motor layout (unchanged after startup, SDK internal cache; first time RPC, timeout unit ms) |

#### 4.3.1 `sendMaxTorque` ——Set the maximum torque of the motor

This interface multiplexes `MotorCtrlAction`, but each `MotorCtrl` only uses `header.limbNo` / `header.jointNo` and `torque`. The following assumes that `maxTorqueNm` is an N·m upper limit array that has been verified by the business side according to the current model and has a length not less than `layout.motorNum`:

```cpp
MotorLayout layout = {};
if (!client->getMotorLayout(layout)) {
    return false;
}

MotorCtrlAction limits = {};
limits.motorNum = layout.motorNum;
for (uint32_t i = 0; i < layout.motorNum; ++i) {
    limits.motors[i].header.limbNo = layout.motors[i].limbNo;
    limits.motors[i].header.jointNo = layout.motors[i].jointNo;
    limits.motors[i].torque = maxTorqueNm[i];
}

if (!client->sendMaxTorque(limits)) {
    return false;
}
```

- Returning `true` only means that the configuration frame has been submitted to the shared memory, but does not mean that the motor side has been switched.
- The bottom layer has a torque switching window of about 10 ms by default, during which position control instructions are not supported. This interface is used for low-frequency configuration and should not be placed in the high-frequency `sendControl()` loop, nor should it continue to deliver position control frames within the switching window.
- The current observation value can be confirmed through `motors[i].maxTorque` returned by subsequent `getLatestObservation()`.
- Public headers, Python native binding and `librobotMotionSdk.so` must come from the same SDK, and mismatched header files and runtime libraries cannot be mixed.

### 4.4 Key data structure (from `MotionSdkProtocol.h`)

#### 4.4.1 `MotorCtrlAction` - Control delivery

```cpp
struct MotorCtrlAction {
    uint32_t   motorNum;                              // Number of active motors
    MotorCtrl  motors[kLowLevelMaxMotorNum];          // Per-motor control values
};

struct MotorCtrl {
    float       position;       // Target position (rad)
    float       velocity;       // Target velocity (rad/s)
    float       kpGain;         // Position-loop gain, Nm/rad (>= 0)
    float       kdGain;         // Velocity-loop gain, Nm/(rad/s) (>= 0)
    float       torque;         // Feedforward torque (Nm)
    MotorHeader header;         // {limbNo, jointNo}
};

struct MotorHeader { uint16_t limbNo; uint16_t jointNo; };
```

> Note: `MotorHeader` here is the SDK POD/ABI structure, and the field is `uint16_t limbNo/jointNo`. `MotorHeader` in DDS IDL wire struct uses `uint32 limbsNo/jointNo`. The two belong to different boundaries and cannot be converted directly according to the memory layout; when crossing DDS, they must be explicitly converted according to field names and semantics.

**Motor joint definition (quadruped)**:
- `limbNo`：FL=0 / FR=1 / RL=2 / RR=3
- `jointNo`：crotch=0/thigh=1/calf=2

#### 4.4.2 `LowLevelMotionCmd` —— Low-level operation control instructions

```cpp
struct LowLevelMotionCmd {
    int32_t action = -1;                 // Action ID, for example standing = 1
    char    acName[kMotionActionLength]; // Action name, for example "standing"
    float   velocity = 0.0f;
    float   velocityX = 0.0f;
    float   velocityY = 0.0f;
};
```

Action-related control frames should be filled in `action` and `acName` at the same time, for example, `action = 1` and `acName = "standing"` are used when performing standing. In this way, the internal processing and external observation of the server can obtain consistent action semantics.

#### 4.4.3 `LowLevelMotionObserved` - Observations

```cpp
struct LowLevelMotionObserved {
    uint8_t         systemSta;                            // System state (busy and other flags)
    uint32_t        motorNum;
    IMUObserved     imu;                                  // temp + accel/gyro/mag/euler/quaternion
    TRCStickFrame   trc;                                  // Sticks/buttons
    PowerObserved   power;                                // Battery
    MotorObserved   motors[kLowLevelMaxMotorNum];
};

struct IMUObserved {
    float        temp;          // IMU temperature (°C)
    Vector3f     accel;         // Acceleration, m/s² (x/y/z); {int8 error; float x,y,z}
    Vector3f     gyro;          // Angular velocity, rad/s (x/y/z)
    Vector3f     mag;           // Magnetic field, μT (x/y/z)
    Vector3f     euler;         // Euler angles, rad (x=roll [-π,π] / y=pitch [-π/2,π/2] / z=yaw [-π,π])
    Quaternionf  quaternion;    // Unitless orientation quaternion; {int8 error; float w,x,y,z}
};

struct PowerObserved {
    float power;             // Charge percentage (0~100)
    float health;            // Health percentage (0~100)
    float temper;            // Battery temperature (°C)
    float chargeCurrent;     // Charge/discharge current (A); positive=charging, negative=discharging
    float chargeVoltage;     // Total voltage (V)
};

struct MotorObserved {
    uint8_t      enable;     // 1 = powered and ready
    uint8_t      online;     // 1 = bus online
    uint8_t      error;      // Error code; see MotorDeviceErrno below
    float        position;   // Current position (rad)
    float        velocity;   // Current velocity (rad/s)
    float        torque;     // Current torque (Nm)
    float        temp;       // Motor temperature (°C)
    float        voltage;    // Motor terminal voltage (V)
    float        lossRate;   // Communication packet-loss rate (%)
    float        maxTorque;  // Maximum motor torque (Nm)
    MotorHeader  header;
};
```

**`IMUObserved` subfield `error` error code enumeration (`IMUDeviceErrno`)**:

The `error` fields of Vector3f / Quaternionf share this enumeration, which independently identifies whether the data of `accel` / `gyro` / `mag` / `euler` / `quaternion` is trustworthy.

| value | name | meaning |
|---|---|---|
| `0` | `imuNormal` | Data is valid |
| `1` | `imuInvalid` | IMU data is invalid (this quantity is currently untrustworthy) |
| `64` | `imuControlOffline` | IMU control board offline |
| `65` | `imuControlNotReady` | Control board not ready |
| `66` | `imuControlUpgrade` | Control board upgrading |
| `67` | `imuControlNotParams` | IMU module parameters are not ready |
| `68` | `imuNotReady` | IMU heating / not ready |

> `0` / `1` is reported by IMU, `64+` is filled in after detection by SDK / server (such as SPI communication interruption). `mag` / `quaternion` is not reported on some models, and the error field is always `imuInvalid`.

**`MotorObserved.error` error code enumeration (`MotorDeviceErrno`)**:

| value | name | meaning |
|---|---|---|
| `0` | `motorNormal` | No fault |
| `1` | `motorPreDriver` | Pre-drive failure |
| `2` | `motorEcodeError` | Encoder failure |
| `3` | `motorOverSpeed` | Overspeed fault |
| `4` | `motorOverTempe` | Overtemperature fault |
| `5` | `motorOverCurrent` | Overcurrent fault |
| `6` | `motorOverVoltage` | Overvoltage fault |
| `59` | `motorPGAbnormality` | PG exception |
| `60` | `motorHWUndervoltage` | Hardware undervoltage |
| `63` | `motorCommError` | Communication error |
| `64` | `motorControlOffline` | Control board offline |
| `65` | `controlMotorNotEnable` | Not enabled |
| `66` | `motorControlNotReady` | Control not ready |
| `67` | `motorControlUpgrade` | Upgrading |
| `68` | `motorNoCalibrated` | Not calibrated |
| `69` | `motorURDFNotMapped` | Calibration lost |

> `0~6` / `59` / `60` / `63` is reported by the motor, `64+` is filled in after detection by the SDK / server (such as the control board is offline, not enabled, lacks calibration data, etc.).

> `PowerObserved` on the low-level data plane and high-level query `querySystemStatus.battery` (see Advanced Interface Manual §4.5.1 for details) describe the same physical battery, but `PowerObserved` is a lightweight subset embedded in the observation frame (real-time performance is priority), and `querySystemStatus.battery` is a more complete snapshot (including BMS status code, cycle times, etc., according to query response).

#### 4.4.4 `MotorLayout` - Hardware layout

```cpp
struct MotorLayout {
    uint32_t   motorNum;
    MotorInfo  motors[kLowLevelMaxMotorNum];
};
struct MotorInfo {
    uint16_t  limbNo;
    uint16_t  jointNo;
    char      name[28];   // "<limb>.<joint>"; for example "leftFront.hip"
};
```

Currently DV500 12-joint `MotorLayout` uses leg-major sequence:

```text
FL_ABAD, FL_HIP, FL_KNEE,
FR_ABAD, FR_HIP, FR_KNEE,
RL_ABAD, RL_HIP, RL_KNEE,
RR_ABAD, RR_HIP, RR_KNEE
```

The application must call `getMotorLayout()` / `get_motor_layout()` to obtain and validate the actual layout. It must then construct control frames from `limbNo` / `jointNo` (Python: `limb_no` / `joint_no`) instead of relying only on fixed array indices. If the joint count or `(limbNo, jointNo)` sequence does not match the layout supported by the application, it must refuse to enable control before calling `setMotionEnable(true)` / `set_motion_enable(True)`.

This order is the SDK/robot data contract; it does not define the policy model's input or output order. The model order is defined by its training and export contract. Deployment code must explicitly perform the bidirectional reorder `SDK order → model order → SDK order`.

#### 4.4.5 `TRCStickFrame` ——Remote Controller Frame

```cpp
struct TRCStickFrame {
    uint32_t  valid;                  // Frame validity; nonzero means valid
    uint8_t   buttons[BUTTON_MAX];    // Button state: 1 = pressed, 0 = released
    float     axes[AXES_MAX];         // Stick and trigger values
    uint64_t  controlId;              // Caller-managed control ID for frame deduplication
};
```

**`buttons[]` index enumeration (`ButtonDefine`)**:

| Index name | Value | Meaning |
|---|---|---|
| `buttonBack` / `buttonStart` | 0 / 1 | External button name Stand / Motion; action semantics are determined by device capability configuration |
| `buttonLB` / `buttonRB` | 2 / 3 | Left/right shoulder keys |
| `buttonF1` / `buttonF2` | 4 / 5 | Customized function keys |
| `buttonA` / `buttonB` / `buttonX` / `buttonY` | 6 / 7 / 8 / 9 | Main function keys |
| `buttonUp` / `buttonDown` / `buttonLeft` / `buttonRight` | 10 / 11 / 12 / 13 | Direction keys |
| `buttonLS` / `buttonRS` | 14 / 15 | Left / right joystick button |

**`axes[]` index enumeration (`AxesDefine`)**:

| Index name | Value | Meaning | Typical range |
|---|---|---|---|
| `axesLX` / `axesLY` | 0 / 1 | Left joystick X / Y | -1.0 ~ 1.0 |
| `axesRX` / `axesRY` | 2 / 3 | Right joystick X / Y | -1.0 ~ 1.0 |
| `axesLT` / `axesRT` | 4 / 5 | Left / right trigger | 0.0 ~ 1.0 |

The external button names Stand / Motion correspond to `buttonBack` / `buttonStart` respectively in the SDK. The specific action combination is subject to `mapping` returned by device `getMotionCapabilities()`; see the high-level TRC document for the current standard mapping. RT condition corresponds to `axesRT`.

#### 4.4.6 `SensorObserved` - Sensor Observation (GPS + UWB)

Returned by `getSensorObservation(SensorObserved*, uint32_t timeout)` (`timeout` unit us, has nothing to do with prepare, any one of `kConnected` / `kPrepared` can be read).

> The supported Low-level contract contains GPS and UWB only; Walk odometry is not supported. Even if a shared protocol structure contains `odom`, Low-level applications must not read or depend on it.

```cpp
struct SensorObserved {
    GPSFrame        gps;
    UWBRawObserved  uwb;
};

struct GPSFrame {
    uint32_t   valid;     // 1 = valid, 0 = invalid
    float      speed;     // GPS speed, km/h
    int32_t    level;     // Signal level; see GPSSignalLevel
    int32_t    rssi;      // Raw signal strength, dBm
    GEOGPoint  point;     // Coordinates
};

struct GEOGPoint {
    float      lat;       // Latitude, deg
    float      lng;       // Longitude, deg
};

struct UWBRawObserved {
    uint8_t    valid;     // Whether the data is valid
    uint8_t    pairState; // Pairing state; see UWBPairState
    int16_t    rssi;      // Signal strength, dBm
    uint16_t   pitch;     // Pitch, deg [0, 360), used to project spatial distance horizontally
    uint16_t   azimuth;   // Azimuth, deg [0, 360); 0 is forward, increasing counterclockwise
    uint32_t   distance;  // Distance, cm
};
```

**`GPSFrame.level` value enumeration (`GPSSignalLevel`)**:

| value | name | meaning |
|---|---|---|
| `0` | `gpsGre38db` | Strong signal |
| `1` | `gpsGre30db` | Signaling |
| `2` | `gpsLes30db` | Weak signal |

**`UWBRawObserved.pairState` value enumeration (`UWBPairState`)**:

| value | name | meaning |
|---|---|---|
| `0` | `uwbPairNone` | Not paired |
| `1` | `uwbInPairing` | Pairing |
| `2` | `uwbPairSuccess` | Pairing successful |
| `3` | `uwbPairFailed` | Pairing failed |

> If there is no data written to the device without corresponding sensor hardware, `getSensorObservation` will wait until timeout and return false.

#### 4.4.7 Coordinate system type `GEOGCoordMode` (reserved)

`GEOGCoordMode` (`gcj02` / `wgs84` / `bd09` / `mapBar`) has been defined in the public header and exported as Python `sdk.GEOGCoordMode`, but currently has no observation field reference (reserved for coordinate transformation purposes).

> All structures are `#pragma pack(push, 1)`, with fixed byte-level alignment and cross-architecture binary compatibility.

---

## 5. C++ usage examples

> **Safety:** Run the general posture-control example only while the robot is secured in a safety rig with all four feet clear of the ground. Validate the TensorRT policy in two stages: test only `stand` and `lay` in the rig; after confirming the posture and joint directions, move the robot to open, level, obstacle-free ground before testing `walk`. Never execute `walk` while the feet are suspended. Keep the emergency stop within reach and assign a dedicated operator throughout both stages.

The general posture-control program is implemented in [`example_lowlevel.cpp`](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/example_lowlevel.cpp); the C++ ONNX/TensorRT policy program is implemented in [`example_lowlevel_tensorrt.cpp`](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/example_lowlevel_tensorrt.cpp). Build and run instructions are in the same repository's [`examples/README.md`](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/README.md). This API reference explains the control flow and model contract without duplicating the complete example source, preventing the two copies from drifting.

### 5.1 General posture-control example

At startup, the program establishes a Low-level connection but does not call `setMotionEnable(true)` or execute a posture command automatically:

```text
lowlevel> status
lowlevel> motors
lowlevel> stand
lowlevel> lie
lowlevel> damping
lowlevel> release
lowlevel> quit
```

- `stand`: Call `setMotionEnable(true)` on demand to smoothly move from the real-time joint position to the standing target and maintain it continuously.
- `lie` / `lie-down`: Call `setMotionEnable(true)` on demand to smoothly move from real-time joint positions to the prone target and maintain it.
- `damping`: Enable Low-level on demand, set position stiffness to 0, and retain speed damping.
- `release`: Send short-term damping first, then stop the control thread and call `setMotionEnable(false)`.
- `quit` / `Ctrl+C`: Run the release sequence, call `restoreMotionControlMode()` to return control to the built-in motion controller, and then disconnect.

The attitude control period is 50 Hz, the default trajectory time is 2 seconds, and the position change in a single cycle does not exceed 0.25 rad. The program matches observation and control according to `(limbNo, jointNo)` and does not rely on the array order; when the actual tracking error exceeds 0.25 rad, trajectory advancement is suspended. The attitude command only supports the standard DV500 12-joint layout, other layouts will be rejected.

Low-level SDK does not have `take` / `startControl` interface: `connect()` establishes and maintains session, `setMotionEnable(true/false)` switches prepare. The CLI directly follows this set of semantics without adding fake permission commands.

Standing target is `hip=0.0, thigh=0.8, calf=-1.5` rad per leg. The target for lying down is `thigh=1.10, calf=-2.72` rad, the left leg is `hip=+0.48` rad, and the right leg is `hip=-0.48` rad. Kp/Kd uses the proven stand/lay configuration in DV500 board header `motionCapacity`.

### 5.2 C++ TensorRT policy example

`example_lowlevel_tensorrt` targets an Orin running JetPack 6.2.1 and accepts a static-shape `[1,45] -> [1,12]` ONNX model directly. It rebuilds a strict FP32 TensorRT engine every time the process starts, never reads or writes an `.engine` cache, and explicitly disables TensorRT's default TF32 mode. The example depends only on the TensorRT/CUDA C++ libraries included with JetPack and the robot SDK; it does not depend on PyTorch or ONNX Runtime.

Start with model-only validation. `--validate-only` builds the engine and runs one zero-input inference without initializing the SDK, connecting to the robot, or enabling control:

```bash
taskset -c 2 ./build/examples/example_lowlevel_tensorrt \
  --onnx /path/to/policy.onnx --validate-only
```

For real-hardware operation, bind the process to CPU 2 to reduce scheduling jitter and stabilize observation latency and the 50 Hz control period:

```bash
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  taskset -c 2 ./build/examples/example_lowlevel_tensorrt \
  --onnx /path/to/policy.onnx
```

After connection, the program must complete the following verification before allowing `setMotionEnable(true)`:

1. `getMotorLayout()` is returned and the number of joints is exactly 12;
2. The actual `(limbNo, jointNo)` sequence complies with the SDK leg-major contract in §4.4.3;
3. The ONNX input and output shape is `[1,45] -> [1,12]`, and the tensor dtype is float32.

The input and output of this example model use joint-major order:

```text
FL_ABAD, FR_ABAD, RL_ABAD, RR_ABAD,
FL_HIP,  FR_HIP,  RL_HIP,  RR_HIP,
FL_KNEE, FR_KNEE, RL_KNEE, RR_KNEE
```

When constructing model input, the program explicitly performs `SDK leg-major -> model joint-major`. When parsing model output, it performs `model joint-major -> SDK leg-major`, then constructs each `MotorCtrl` from the `limbNo` / `jointNo` values returned by `MotorLayout`. Do not mistake the example model order for the SDK order. When replacing the model, revalidate the model order, observation definition, normalization, action scale, tensor shapes, and control frequency.

Validate real-hardware motion in two stages. First, secure the robot in a safety rig with all four feet clear of the ground, and execute only:

```text
lowlevel> stand
lowlevel> lay
lowlevel> quit
```

After confirming the posture, joint directions, and emergency-stop path, place the robot on open, level, obstacle-free ground and execute:

```text
lowlevel> stand
lowlevel> walk 0.5 0 0
lowlevel> stop
lowlevel> lay
lowlevel> quit
```

Never execute `walk` while the feet are suspended. Keep the emergency stop within reach and staffed during both stages.

On exit, the TensorRT example calls `setMotionEnable(false)` only if the client is in the prepared state, then disconnects the client and shuts down the SDK. It does **not** call `emergencyStop()` or `restoreMotionControlMode()`. These exit semantics intentionally differ from the general posture-control example in §5.1.

Both native compilation on Orin and cross-compilation on Ubuntu 22.04 x86_64 for JetPack 6.2.1 have been verified on hardware. Cross-compilation must use NVIDIA's `cross-linux-aarch64` repository and pin the complete TensorRT package set to 10.3; do not install the repository's latest default versions. For repository configuration, version pinning, CMake parameters, disk usage, and deployment instructions, see [`BUILD.md` §3.1](../../BUILD.md#31-additional-requirements-for-the-tensorrt-example).

---

## 6. Precautions

1. **Callback registration timing**: `setConnectCallback` It is recommended to call it before `connect()` to facilitate the first time perception of the first connection status.
2. **Callback thread**: `ConnectCallback` is triggered in the SDK internal thread; the SDK interface in the callback must be reentrant.
3. **Status Query**: `getState()` / `getLastError()` is thread safe; `getLastError()` is cleared after reading.
4. **`setMotionEnable` is asynchronous**: Returning true only means that the request has been accepted, the state is advanced to `kPrepared` / `kConnected` by the SDK, and the caller should be aware of it through `getState()` or `ConnectCallback`.
5. **`sendControl` / `sendMaxTorque` only takes effect in `kPrepared`**: other states return false + `kNotPrepared` / `kNotConnected`; `motorNum` must ∈ `[1, kLowLevelMaxMotorNum]`, otherwise return `kInvalidArgument` (no implicit clamp).
6. **`sendMaxTorque` is a low-frequency configuration interface**: After submission, it is asynchronous hardware switching. By default, do not continue to send position control frames within about 10 ms; confirm `maxTorque` through subsequent observations.
7. **Observation pull mode**: `getLatestObservation` obtains motion observations within the specified timeout, and returns false if not obtained.
8. **`getMotorLayout` cache**: The first time RPC is used, the SDK local cache is hit, and the hardware configuration remains unchanged after startup.
9. **lease default value**: `connect(observedHz, 0)` → Use the default 60s; the final effective value is determined by the server, and the SDK automatically renews according to the real value.
10. **Automatic reconnection after disconnection**: In the `kConnectionLost` state, the SDK will automatically retry according to the built-in backoff policy, and no external manual intervention is required; if you need to give up actively, call `disconnect()`.

---

## 7. Debugging and Troubleshooting

### 7.1 Minimum verification on the robot side (a priori)

Before calling the SDK, first confirm the "opposite end" on the robot side to avoid blindly searching for reasons on the client side.

| Check items | Command/Method | Expected results |
|---|---|---|
| Is motionServer running | `ps -ef \| grep motionServer` | The process exists |
| Shared memory permissions | `ls -la /dev/shm/ \| grep motion` | The file exists and is readable by the current user |
| Real-time log | `journalctl -u motionServer -f` | Screen refresh without error |

### 7.2 Troubleshooting common phenomena on the SDK side

| Phenomenon | Check items | Solution ideas |
|---|---|---|
| `initialService` returns false | Log `errorf` output | See error code: `kRpcConnectFailed` → DDS domain cannot be started (domain id is incorrect/local environment is not ready) |
| `create()` returns nullptr | Whether the SDK has `initialService` successfully | Must be successfully initialized before `create()` |
| `connect()` has been at `kConnecting` | 1. The error code <br>2 pushed by ConnectCallback. SHM file permission <br>3. Is the motionServer on the robot side running? | `kRpcAcquireRejected` → The control right is occupied by others; `kMasterSwitchFailed` → Switch to the motion control master Failed (the peer is still operating and controlling) |
| After `setMotionEnable(true)`, the state does not cut `kPrepared` | 1. `getLastError()` gets the error code <br>2. ConnectCallback whether to report `kPrepareRejected` | The robot side motor power-on process is slow (joint self-test + calibration), you may need to wait a few seconds to dozens of seconds |
| `getLatestObservation` frequently returns false | 1. Is the current state `kPrepared`<br>2. Is the observed frequency (observedHz) set too high and exceeds the hardware capability | The on-board SHM mode should hardly lose; continuous loss indicates that the frequency exceeds the hardware capability or the server is abnormal |
| `sendControl` returns false, state displays `kPrepared` | `getLastError()` value; whether `motorNum` is legal | `kSessionExpired` → The server session is invalid, waiting for automatic reconnection; `kInvalidArgument` → action.motorNum exceeds [1, kLowLevelMaxMotorNum] |
| `MotorObserved.error` non-0 | See §4.4.2 `MotorDeviceErrno` enumeration | `0~6`/`59`/`60`/`63` is the fault reported by the motor; `64+` is the status detected by the SDK/server (such as `motorControlOffline`) |
| **Silent no response** (timeout for any interface) | DDS QoS incompatibility | Client/server IDL or Cyclone DDS versions are inconsistent; use `ddsperf sanity` for minimum handshake |

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
