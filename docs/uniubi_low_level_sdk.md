# 宇泛智能机器狗低级控制 SDK 接口手册

> SDK 入口类：`uniubi::RobotSdk::IMotionLowLevelClient`
> C++ 头文件：`include/uniubi/robot_sdk/MotionLowLevelClient.h`

---

## 目录

- [一、SDK 概述](#一sdk-概述)
- [Quick Start](#quick-start)
- [开发工程模板](#开发工程模板)
- [二、枚举定义](#二枚举定义)
- [三、回调定义](#三回调定义)
  - [3.2 回调汇总](#32-回调汇总)
- [四、接口定义](#四接口定义)
  - [4.1 全局初始化与实例创建](#41-全局初始化与实例创建)
  - [4.2 生命周期与状态切换](#42-生命周期与状态切换)
  - [4.3 数据面接口](#43-数据面接口)
  - [4.4 关键数据结构](#44-关键数据结构来自-motionsdkprotocolh)
- [五、C++ 使用示例](#五c-使用示例)
- [六、Python SDK](#六python-sdk)
  - [6.1 binding 覆盖范围](#61-当前-binding-覆盖范围已与-c-接口对齐)
  - [6.2 退出死锁规避（必读）](#62--退出死锁规避必读)
  - [6.3 Python 使用示例](#63-python-使用示例)
- [七、注意事项](#七注意事项)
- [八、调试与故障排查](#八调试与故障排查)

---

## 一、SDK 概述

- 仅支持**板内单设备**部署：SDK 与 MotionServer 运行于同一台机器，直连本地服务（无远端 / UDP / 多设备）
- 控制面走 RPC，数据面走板内共享内存（SHM），均直接走二进制结构，不走 JSON
- 工厂 `IMotionLowLevelClient::create()` 无参；同进程内多次 `create()` 返回同一实例（进程级单例）
- 控制权获取/续约由 SDK 内部自动维持，外部只用 `setMotionEnable(true/false)` 切 prepare
- 状态机由 SDK 内部推进，调用方通过 `ConnectCallback` / `getState()` 感知

---

## Quick Start

最小运行流程（完整版本见 §五）：

**C++**

```cpp
#include <unistd.h>
#include "MotionSdkService.h"
#include "MotionLowLevelClient.h"

using namespace uniubi::RobotSdk;
using LLState = IMotionLowLevelClient::LowLevelState;

int main() {
    auto svc = IMotionSdkService::instance();
    svc->initialService(nullptr, "myApp");

    auto client = IMotionLowLevelClient::create();   // 板内单设备，无参；同进程返回同一实例
    client->connect(/*observedHz=*/500);
    while (client->getState() != static_cast<int32_t>(LLState::kConnected)) usleep(10000);

    client->setMotionEnable(true);
    while (client->getState() != static_cast<int32_t>(LLState::kPrepared))  usleep(10000);

    /// 周期下发 sendControl(...) + 拉取 getLatestObservation(...)
    /// 具体 MotorCtrlAction 构造与控制循环见 §五

    client->setMotionEnable(false);
    client->disconnect();
    IMotionSdkService::instance()->shutdown();
    return 0;
}
```

**Python**

```python
import time
import robot_motion_sdk as sdk

sdk.service.initial(None, "myApp")
client = sdk.MotionLowLevelClient()              # 板内单设备，无参
try:
    client.connect(observed_hz=500)
    while client.get_state() != sdk.LowLevelState.kConnected: time.sleep(0.01)

    client.set_motion_enable(True)
    while client.get_state() != sdk.LowLevelState.kPrepared:  time.sleep(0.01)

    # 周期 send_control(...) + get_latest_observation(...)，完整循环见 §6.3
finally:
    client.set_motion_enable(False)
    client.disconnect()
    sdk.service.shutdown()
```

> Python 退出必须走 `try/finally`，原因详见 [§6.2](#62--退出死锁规避必读)。

---

## 开发工程模板

最小可起跑的项目模板，开发者照着复制 + 写自己的应用代码即可编译运行。

> 完整构建说明（含交叉编译 / wheel 打包 / Troubleshooting）参见 [`BUILD.md`](BUILD.md)。

### 依赖

| 依赖 | 来源 | 说明 |
|---|---|---|
| `librobotMotionSdk.so` | SDK 仓库 `lib/<arch>/` | 预编译运行库，按目标架构选 |
| 公开头 | SDK 仓库 `include/uniubi/robot_sdk/` | `MotionSdkService.h` / `MotionLowLevelClient.h` / `MotionSdkProtocol.h` |
| 编译器 | g++ ≥ 9（支持 C++14） | |
| 运行时基础库 | 目标机预装（标准动态库路径） | 不需要客户额外装 Cyclone DDS —— 已链接进 SDK .so |

### 工程目录

```
my_robot_app/
├── CMakeLists.txt
└── src/
    └── main.cpp             ← 用户应用代码（参考 §五 完整示例）
```

### CMakeLists.txt 样例

```cmake
cmake_minimum_required(VERSION 3.16)
project(my_robot_app CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 1) 指定 SDK 安装前缀（默认 /opt/uniubi/；源码仓库可用 ~/uniubi_robot_sdk）
set(UNIUBI_SDK_ROOT "$ENV{HOME}/uniubi_robot_sdk" CACHE PATH "Uniubi SDK install root")

# 2) 按目标架构自动选 Lib 子目录（x86_64 / aarch64 / i386）
if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|amd64|AMD64)$")
    set(ARCH_DIR "x86_64")
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(aarch64|arm64|ARM64)$")
    set(ARCH_DIR "aarch64")
else()
    set(ARCH_DIR "i386")
endif()

# 3) 定位 SDK .so 与公开头
find_library(SDK_LIB robotMotionSdk
             PATHS ${UNIUBI_SDK_ROOT}/lib/${ARCH_DIR}
             NO_DEFAULT_PATH REQUIRED)

add_executable(my_robot_app src/main.cpp)
target_include_directories(my_robot_app PRIVATE ${UNIUBI_SDK_ROOT}/include)
target_link_libraries(my_robot_app PRIVATE ${SDK_LIB} pthread)
```

### 构建 + 运行

```bash
mkdir -p build && cd build
cmake -DUNIUBI_SDK_ROOT=~/uniubi_robot_sdk ..
make -j$(nproc)

# 运行前确保 SDK .so 在动态库路径
export LD_LIBRARY_PATH=~/uniubi_robot_sdk/lib/$(uname -m):$LD_LIBRARY_PATH
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" ./my_robot_app
```

当前设备运行 SDK 程序需要 root 权限。构建不需要 `sudo`；运行时显式传入 `LD_LIBRARY_PATH`，避免 `sudo` 清理当前用户环境后找不到 SDK 动态库。

---

## 二、枚举定义

### 2.1 `LowLevelState` —— 客户端状态

| 值 | 含义 |
|---|---|
| `kDisconnected` (0) | 初始 / `disconnect()` 后 |
| `kConnecting` (1) | 首次连接尝试中（尚未连上） |
| `kConnected` (2) | 控制面 + 数据面通道就绪，但 prepare 未开 → `sendControl` 无效 |
| `kPrepared` (3) | prepare 已开，`sendControl` 才会被服务端采纳 |
| `kConnectionLost` (4) | 曾经 connected/prepared，因 session 失效 / 服务端异常掉线，SDK 正在自动重连 |

### 2.2 `LowLevelError` —— 失败原因

| 值 | 含义 |
|---|---|
| `kNone` | 无错 |
| `kRpcConnectFailed` | SDK 未初始化或通信通道未就绪 |
| `kRpcAcquireRejected` | 请求获取控制权被服务端拒绝（被他人占用 / 服务端不可达） |
| `kPrepareRejected` | 运控开关请求失败 |
| `kSessionExpired` | session 到期被服务端回收 |
| `kSessionReleased` | session 被服务端主动释放 |
| `kServerStop` | 服务端主动关闭通道 |
| `kRpcCallFailed` | RPC 调用失败（含超时 / 通道断 / 编解码错 / id 不匹配等）|
| `kNotConnected` | 未 connect 即调需要连接的接口 |
| `kNotPrepared` | 当前未 prepare，无法下发控制 |
| `kInvalidArgument` | 入参非法（如 `motorNum == 0` 或 `> kLowLevelMaxMotorNum`） |
| `kMasterSwitchFailed` | 连接时切换本端为运控 master 失败（对端仍在运控 / 服务端拒绝） |

### 2.3 `MotionControlMode` —— 运控执行模式

标识由大脑还是小脑执行运控。该枚举仍定义于协议头 `MotionSdkProtocol.h`，但当前**没有任何 client 接口返回它**；低级 SDK 只提供 `restoreMotionControlMode()` 把运控模式恢复到默认。

| 值 | 含义 |
|---|---|
| `cerebellumMode` (0) | 小脑执行运控 |
| `brainControlMode` (1) | 大脑执行运控 |
| `motionModeNotReady` (255) | 运控模式未就绪 |

---

## 三、回调定义

### 3.1 `ConnectCallback` —— 状态变化

```cpp
using ConnectCallback = std::function<void(LowLevelState state, LowLevelError error)>;
```

回调由 SDK 内部线程触发。任何 session 异常（到期 / 被释放 / 服务端停服）统一视为逻辑断连，state 转入 `kConnectionLost`，SDK 自动尝试重连，成功后回 `kConnected`。

典型时序：

| 触发场景 | state | error |
|---|---|---|
| 切换运控 master 失败 | `kConnecting` | `kMasterSwitchFailed` |
| 控制面 + 数据面建联成功 | `kConnected` | `kNone` |
| `setMotionEnable(true)` 成功 | `kPrepared` | `kNone` |
| `setMotionEnable(false)` 成功 | `kConnected` | `kNotPrepared` |
| Session 到期 | `kConnectionLost` | `kSessionExpired` |
| 服务端主动停服 | `kConnectionLost` | `kServerStop` |

### 3.2 回调汇总

SDK 共暴露 2 种回调，注册时机和用途见下表。

| 回调 | 用途 | 注册接口 |
|---|---|---|
| `LogCallback` | 接收 SDK 内部日志输出（调试 / 运维可重定向到自家日志框架） | `IMotionSdkService::setLogCallback` |
| `ConnectCallback` | 连接 / prepare 状态变化（建联 / session 异常等），驱动调用方状态机 | `IMotionLowLevelClient::setConnectCallback` |

#### 回调内严禁阻塞

**所有回调函数体内严禁执行任何阻塞操作 —— 回调由 SDK 内部线程触发，阻塞会直接把内部线程卡住**：

- ❌ 不能 `sleep` / 等待 mutex / 等待 condvar
- ❌ 不能调任何同步 RPC 接口（`emergencyStop` / `getMotorLayout` 等）
- ❌ 不能做磁盘 IO / 网络 IO / 大块内存分配
- ❌ 不能 `disconnect()` / `shutdown()` 本对象

内部线程被卡死后果是连锁的：观测帧投递停摆、状态机不再推进、心跳超时被服务端踢线、重连流程也无法启动。

**正确做法**：在回调里只做"轻量记录 / 通知"：

```cpp
client->setConnectCallback([&](LowLevelState s, LowLevelError e) {
    /// ✓ 写一个 atomic 标志
    mLastState.store(s);
    /// ✓ post 一个信号量 / notify_one 一个 condvar 给业务线程
    mStateChangedCv.notify_one();
    /// ✓ enqueue 一个事件到业务队列，让 worker 线程处理
    mEventQueue.push({s, e});
});
```

业务线程感知到信号后再做实际处理（包括反调 SDK 接口、IO、计算等）。

---

## 四、接口定义

### 4.1 全局初始化与实例创建

SDK 的 RPC 控制面与事件订阅基于 [Eclipse Cyclone DDS](https://cyclonedds.io/) 实现。DDS 拓扑（domain、QoS profile、客户端 / 事件订阅声明）由 SDK 内部构造，**调用方无需准备 JSON 配置或 XML 文件**。开发者只需通过下面几个 setter 在 `initialService` 之前传入必要参数。

#### 4.1.1 全局初始化

```cpp
bool IMotionSdkService::initialService(const char* file, const char* server, uint32_t timeout = 30);
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `file` | `const char*` | 预留：JSON 配置文件路径。当前 SDK 默认 DDS 配置已内置，传 `nullptr` 即可 |
| `server` | `const char*` | 应用标识，用于 RPC / 日志区分多实例（如 `"myAppLowLevel"`），调用方自定义 |
| `timeout` | `uint32_t` | 等待系统环境就绪的超时（**秒**，默认 30）。板内模式下若 SDK 比系统环境先起，可能需要等待；超时未就绪返回 `false` |

进程级一次性初始化，必须在创建任何 client 之前调用。返回 `true` 表示初始化成功。

```cpp
/// SDK 版本字符串，格式："<semver> (commit <git-short-sha>)"，如 "0.1.0 (commit 7bb376b2)"
/// 任意时刻可调，无需先 initialService；可用于运行时日志 / bug 上报 / 兼容性检查
static const char* version();
```

> **版本兼容性**：SDK 与机器人侧约定走 OMG XTYPES `@appendable`（IDL 字段可追加，向后兼容）。若 SDK 与机器人版本严重不一致，典型现象是 RPC 调用 / 数据面 binary 包**静默无响应**（DDS 报 `RequestedIncompatibleQos` 但不抛错）。出现这种现象时把 `version()` 输出贴到故障报告里。

#### 4.1.2 setter / 查询接口（必须在 `initialService` 之前调用）

低级 SDK 仅板内单设备部署，无需网络接口选择 / 设备发现等远端能力，仅保留日志回调注册：

```cpp
/// 注册日志回调（必须在 initialService 之前调用）
void setLogCallback(LogCallback cb);
```

> `setNetworkInterface` / `setDiscoverCallback` / `isMultiDevice` / `discoverDevices` 等接口仅为高级远端模式服务，板内低级 SDK 不涉及。

#### 4.1.3 客户端实例创建

```cpp
static std::shared_ptr<IMotionLowLevelClient> create();
```

无参工厂，直连本机 MotionServer。低级 SDK 为**板内进程级单例**：同一进程内多次调用 `create()` 返回同一实例。失败返回空指针。

```cpp
auto svc = IMotionSdkService::instance();
svc->initialService(nullptr, "myAppLowLevel");
auto client = IMotionLowLevelClient::create();
```

### 4.2 生命周期与状态切换

| 方法 | 状态要求 | 说明 |
|---|---|---|
| `bool connect(uint32_t observedHz = 500, uint32_t leaseMs = 0)` | 任意 | 非阻塞，连接由 SDK 自动完成全流程。`observedHz`：期望观测频率；`leaseMs`：控制权租约（ms），0 = 使用 server 默认值（server 按自身策略 clamp/校验后下发真实值，SDK 按真实值续约） |
| `void disconnect()` | 任意 | 关闭连接；幂等 |
| `bool setMotionEnable(bool enable)` | `kConnected` / `kPrepared` | **异步**：仅记录意图，SDK 在 RPC 完成后切 `kConnected ↔ kPrepared` 并回调 |
| `bool emergencyStop(uint32_t timeout = 5000)` | `kPrepared` | 急停（同步 RPC，timeout 单位 ms） |
| `int32_t getState() const` | 任意 | 当前 `LowLevelState` |
| `int32_t getLastError() const` | 任意 | 读后清零的最后失败原因 |
| `void setConnectCallback(ConnectCallback cb)` | 任意 | 注册状态回调 |
| `IMediaBusClient::Ptr createMediaBusClient()` | 任意 | 创建音视频帧订阅通道；仅 `aarch64` 板内本地媒体帧订阅使用（用法见 MediaBus 文档） |
| `bool restoreMotionControlMode(uint32_t timeout = 5000)` | `kConnected` 后即可 | 恢复运控模式到出厂默认；同步 RPC，timeout 单位 ms |

#### `connect` 的超时与重试策略（重要）

- SDK 对 connect 流程 **不设整体超时**，会按内置退避策略无限循环重试，直到成功或被 `disconnect()` 显式打断
- 每一次中间环节失败都会触发 `ConnectCallback(state, error)`，调用方可据此感知进度
- 调用方如需 "N 秒 / N 次失败放弃" 语义，自行在 `ConnectCallback` 中累计失败次数或比对墙上时间，达到阈值后调用 `disconnect()` 终止（SDK 不主动放弃，给调用方完整决策权）
- **取权重试幂等**：SDK 在实例创建时生成一个稳定令牌随取权请求携带；若服务端已成功授予但回复在链路上丢失，SDK 重试取权时服务端识别为同一调用方，**复用原 `sessionId` 并刷新租约后成功返回**，不会因自己上一次的成功而被 `controlWasSeized` 永久卡死。令牌为 SDK 内部细节，调用方无需感知

### 4.3 数据面接口

| 方法 | 状态要求 | 说明 |
|---|---|---|
| `bool sendControl(const MotorCtrlAction& action, const LowLevelMotionCmd* cmd = nullptr)` | `kPrepared` | 下发一帧控制；动作相关控制帧建议传 `cmd`，并同时填写 `action` 和 `acName`；`motorNum` 必须 ∈ `[1, kLowLevelMaxMotorNum]`，否则返 `kInvalidArgument` |
| `bool sendMaxTorque(const MotorCtrlAction& action)` | `kPrepared` | 设置电机最大扭矩；使用各元素的 `header` 定位电机、`torque` 携带目标上限；`motorNum` 必须 ∈ `[1, kLowLevelMaxMotorNum]`，否则返 `kInvalidArgument` |
| `bool getLatestObservation(LowLevelMotionObserved* obs, uint32_t timeout)` | `kPrepared` | 在指定 `timeout`（**ms**）内获取一帧运控观测量（电机/IMU/TRC/电源）；未取到返回 false |
| `bool getSensorObservation(SensorObserved* sensor, uint32_t timeout)` | `kConnected` / `kPrepared` 任一 | 获取一帧传感器观测（GPS + UWB），与 prepare 无关、传感器常驻采集；`timeout` 单位 **us**；无传感器硬件设备会等到超时返 false |
| `bool getMotorLayout(MotorLayout& layout, uint32_t timeout = 5000)` | `kConnected` 后即可 | 硬件电机布局（启动后不变，SDK 内部缓存；首次走 RPC，timeout 单位 ms） |

#### 4.3.1 `sendMaxTorque` —— 设置电机最大扭矩

该接口复用 `MotorCtrlAction`，但每个 `MotorCtrl` 只使用 `header.limbNo` / `header.jointNo` 和 `torque`。以下假设 `maxTorqueNm` 是业务侧按当前机型校验过、长度不小于 `layout.motorNum` 的 N·m 上限数组：

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

- 返回 `true` 只代表配置帧已提交到共享内存，不代表电机侧已经完成切换。
- 底层默认存在约 10 ms 的扭矩切换窗口，期间不支持位置控制指令。该接口用于低频配置，不应放入高频 `sendControl()` 循环，也不要在切换窗口内继续下发位置控制帧。
- 可通过后续 `getLatestObservation()` 返回的 `motors[i].maxTorque` 确认当前观测值。
- 公开头、Python native binding 和 `librobotMotionSdk.so` 必须来自同一套 SDK，不能混用不匹配的头文件与运行库。

### 4.4 关键数据结构（来自 `MotionSdkProtocol.h`）

#### 4.4.1 `MotorCtrlAction` —— 控制下发

```cpp
struct MotorCtrlAction {
    uint32_t   motorNum;                              // 实际生效电机数
    MotorCtrl  motors[kLowLevelMaxMotorNum];          // 每电机控制量
};

struct MotorCtrl {
    float       position;       // 目标位置 (rad)
    float       velocity;       // 目标速度 (rad/s)
    float       kpGain;         // 位置环增益，单位：Nm/rad（≥ 0）
    float       kdGain;         // 速度环增益，单位：Nm/(rad/s)（≥ 0）
    float       torque;         // 前馈力矩 (Nm)
    MotorHeader header;         // {limbNo, jointNo}
};

struct MotorHeader { uint16_t limbNo; uint16_t jointNo; };
```

> 注意：这里的 `MotorHeader` 是 SDK POD/ABI 结构，字段为 `uint16_t limbNo/jointNo`。DDS IDL wire struct 中的 `MotorHeader` 使用 `uint32 limbsNo/jointNo`。两者属于不同边界，不能直接按内存布局互转；跨 DDS 时必须按字段名和语义显式转换。

**电机关节定义（四足）**：
- `limbNo`：FL=0 / FR=1 / RL=2 / RR=3
- `jointNo`：胯=0 / 大腿=1 / 小腿=2

#### 4.4.2 `LowLevelMotionCmd` —— 低级运控操作指令

```cpp
struct LowLevelMotionCmd {
    int32_t action = -1;                 // 动作 id，如 standing = 1
    char    acName[kMotionActionLength]; // 动作名，如 "standing"
    float   velocity = 0.0f;
    float   velocityX = 0.0f;
    float   velocityY = 0.0f;
};
```

动作相关控制帧应同时填写 `action` 和 `acName`，例如执行站立时使用 `action = 1`、`acName = "standing"`。这样服务端内部处理和外部观测都能拿到一致的动作语义。

#### 4.4.3 `LowLevelMotionObserved` —— 观测量

```cpp
struct LowLevelMotionObserved {
    uint8_t         systemSta;                            // 系统状态（busy 等标志）
    uint32_t        motorNum;
    IMUObserved     imu;                                  // temp + accel/gyro/mag/euler/quaternion
    TRCStickFrame   trc;                                  // 摇杆/按键
    PowerObserved   power;                                // 电池
    MotorObserved   motors[kLowLevelMaxMotorNum];
};

struct IMUObserved {
    float        temp;          // IMU 温度 (°C)
    Vector3f     accel;         // 加速度 m/s²  (x/y/z)；{int8 error; float x,y,z}
    Vector3f     gyro;          // 角速度 rad/s (x/y/z)
    Vector3f     mag;           // 磁场   μT    (x/y/z)
    Vector3f     euler;         // 欧拉角 rad   (x=roll [-π,π] / y=pitch [-π/2,π/2] / z=yaw [-π,π])
    Quaternionf  quaternion;    // 姿态四元数，无量纲；{int8 error; float w,x,y,z}
};

struct PowerObserved {
    float power;             // 电量百分比 (0~100)
    float health;            // 健康度百分比 (0~100)
    float temper;            // 电池温度 (°C)
    float chargeCurrent;     // 充放电电流 (A)，正充负放
    float chargeVoltage;     // 总电压 (V)
};

struct MotorObserved {
    uint8_t      enable;     // 1 = 上电就绪
    uint8_t      online;     // 1 = 总线在线
    uint8_t      error;      // 错误码，见下方 "MotorDeviceErrno" 表
    float        position;   // 当前位置 (rad)
    float        velocity;   // 当前速度 (rad/s)
    float        torque;     // 当前力矩 (Nm)
    float        temp;       // 电机温度 (°C)
    float        voltage;    // 电机端电压 (V)
    float        lossRate;   // 通信丢包率 (%)
    float        maxTorque;  // 电机最大扭矩 (Nm)
    MotorHeader  header;
};
```

**`IMUObserved` 子字段 `error` 错误码枚举（`IMUDeviceErrno`）**：

Vector3f / Quaternionf 的 `error` 字段共用此枚举，分别独立标识 `accel` / `gyro` / `mag` / `euler` / `quaternion` 各路数据是否可信。

| 值 | 名称 | 含义 |
|---|---|---|
| `0` | `imuNormal` | 数据有效 |
| `1` | `imuInvalid` | IMU 数据无效（该量当前不可信） |
| `64` | `imuControlOffline` | IMU 控制板离线 |
| `65` | `imuControlNotReady` | 控制板未就绪 |
| `66` | `imuControlUpgrade` | 控制板升级中 |
| `67` | `imuControlNotParams` | IMU 模组参数未就绪 |
| `68` | `imuNotReady` | IMU 加热 / 未就绪 |

> `0` / `1` 由 IMU 上报，`64+` 由 SDK / 服务端检测后填入（如 SPI 通信中断）。`mag` / `quaternion` 在某些机型上未上报，error 字段恒为 `imuInvalid`。

**`MotorObserved.error` 错误码枚举（`MotorDeviceErrno`）**：

| 值 | 名称 | 含义 |
|---|---|---|
| `0` | `motorNormal` | 无故障 |
| `1` | `motorPreDriver` | 预驱故障 |
| `2` | `motorEcodeError` | 编码器故障 |
| `3` | `motorOverSpeed` | 过速故障 |
| `4` | `motorOverTempe` | 过温故障 |
| `5` | `motorOverCurrent` | 过流故障 |
| `6` | `motorOverVoltage` | 过压故障 |
| `59` | `motorPGAbnormality` | PG 异常 |
| `60` | `motorHWUndervoltage` | 硬件欠压 |
| `63` | `motorCommError` | 通信错误 |
| `64` | `motorControlOffline` | 控制板离线 |
| `65` | `controlMotorNotEnable` | 未使能 |
| `66` | `motorControlNotReady` | 控制未就绪 |
| `67` | `motorControlUpgrade` | 升级中 |
| `68` | `motorNoCalibrated` | 未标定 |
| `69` | `motorURDFNotMapped` | 标定丢失 |

> `0~6` / `59` / `60` / `63` 由电机上报，`64+` 由 SDK / 服务端检测后填入（如控制板离线、未使能、缺标定数据等）。

> 低级数据面的 `PowerObserved` 与高级查询 `querySystemStatus.battery`（详见高级接口手册 §4.5.1）描述同一物理电池，但 `PowerObserved` 是嵌入观测帧的轻量子集（实时性优先），`querySystemStatus.battery` 是更完整的快照（含 BMS 状态码、循环次数等，按查询响应）。

#### 4.4.3 `MotorLayout` —— 硬件布局

```cpp
struct MotorLayout {
    uint32_t   motorNum;
    MotorInfo  motors[kLowLevelMaxMotorNum];
};
struct MotorInfo {
    uint16_t  limbNo;
    uint16_t  jointNo;
    char      name[28];   // "<limb>.<joint>"，如 "leftFront.hip"
};
```

#### 4.4.4 `TRCStickFrame` —— 遥控手柄帧

```cpp
struct TRCStickFrame {
    uint32_t  valid;                  // 帧是否有效，非 0 视为有效
    uint8_t   buttons[BUTTON_MAX];    // 按键状态：每位置 1 = 按下，0 = 释放
    float     axes[AXES_MAX];         // 摇杆 / 扳机量
    uint64_t  controlId;              // 控制 ID，由调用方维护用于帧序去重
};
```

**`buttons[]` 索引枚举（`ButtonDefine`）**：

| 索引名 | 值 | 含义 |
|---|---|---|
| `buttonBack` / `buttonStart` | 0 / 1 | 对外按键名 Stand / Motion；动作语义由设备能力配置决定 |
| `buttonLB` / `buttonRB` | 2 / 3 | 左 / 右肩键 |
| `buttonF1` / `buttonF2` | 4 / 5 | 自定义功能键 |
| `buttonA` / `buttonB` / `buttonX` / `buttonY` | 6 / 7 / 8 / 9 | 主功能键 |
| `buttonUp` / `buttonDown` / `buttonLeft` / `buttonRight` | 10 / 11 / 12 / 13 | 方向键 |
| `buttonLS` / `buttonRS` | 14 / 15 | 左 / 右摇杆按键 |

**`axes[]` 索引枚举（`AxesDefine`）**：

| 索引名 | 值 | 含义 | 典型范围 |
|---|---|---|---|
| `axesLX` / `axesLY` | 0 / 1 | 左摇杆 X / Y | -1.0 ~ 1.0 |
| `axesRX` / `axesRY` | 2 / 3 | 右摇杆 X / Y | -1.0 ~ 1.0 |
| `axesLT` / `axesRT` | 4 / 5 | 左 / 右扳机 | 0.0 ~ 1.0 |

对外按键名 Stand / Motion 在 SDK 中分别对应 `buttonBack` / `buttonStart`。具体动作组合以设备 `getMotionCapabilities()` 返回的 `mapping` 为准；当前标准映射见高阶 TRC 文档。RT 条件对应 `axesRT`。

#### 4.4.5 `SensorObserved` —— 传感器观测（GPS + UWB）

由 `getSensorObservation(SensorObserved*, uint32_t timeout)` 返回（`timeout` 单位 us，与 prepare 无关，`kConnected` / `kPrepared` 任一即可读）。

```cpp
struct SensorObserved {
    GPSFrame        gps;
    UWBRawObserved  uwb;
};

struct GPSFrame {
    uint32_t   valid;     // 1=有效，0=异常
    float      speed;     // GPS 测速，km/h
    int32_t    level;     // 信号等级，见 GPSSignalLevel
    int32_t    rssi;      // 信号强度原始值 单位 dbm
    GEOGPoint  point;     // 坐标信息
};

struct GEOGPoint {
    float      lat;       // 纬度，deg
    float      lng;       // 经度，deg
};

struct UWBRawObserved {
    uint8_t    valid;     // 数据是否有效
    uint8_t    pairState; // 配对状态，见 UWBPairState
    int16_t    rssi;      // 信号强度 单位 dbm
    uint16_t   pitch;     // 俯仰角，deg [0,360)，用于将空间距离投影到水平距离
    uint16_t   azimuth;   // 方位角，deg [0,360)，正前方 0 度、逆时针递增
    uint32_t   distance;  // 距离，cm
};
```

**`GPSFrame.level` 取值枚举（`GPSSignalLevel`）**：

| 值 | 名称 | 含义 |
|---|---|---|
| `0` | `gpsGre38db` | 信号强 |
| `1` | `gpsGre30db` | 信号中 |
| `2` | `gpsLes30db` | 信号弱 |

**`UWBRawObserved.pairState` 取值枚举（`UWBPairState`）**：

| 值 | 名称 | 含义 |
|---|---|---|
| `0` | `uwbPairNone` | 未配对 |
| `1` | `uwbInPairing` | 配对中 |
| `2` | `uwbPairSuccess` | 配对成功 |
| `3` | `uwbPairFailed` | 配对失败 |

> 无对应传感器硬件的设备无数据写入，`getSensorObservation` 会等待至超时返回 false。

#### 4.4.6 坐标系类型 `GEOGCoordMode`（保留）

`GEOGCoordMode`（`gcj02` / `wgs84` / `bd09` / `mapBar`）已在公开头定义、并导出为 Python `sdk.GEOGCoordMode`，但当前**无观测字段引用**（保留给坐标转换用途）。

> 所有结构均 `#pragma pack(push, 1)`，字节级对齐固定，跨架构二进制兼容。

---

## 五、C++ 使用示例

> **实机测试前必须将机器狗可靠吊起，使四脚完全腾空，并确保四肢在完整运动范围内能够自由活动、不会碰到地面、吊架或周围物体。测试过程中必须保持急停可触达并由专人值守；本示例不得直接落地运行。**

完整可运行程序以 [`uniubi_robot_sdk/examples/example_lowlevel.cpp`](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/example_lowlevel.cpp) 为准；构建与运行方式见同仓库的 [`examples/README.md`](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/README.md)。API 手册只解释控制流程，不复制整份示例源码，避免两处实现漂移。

启动程序后会建立 Low-level 连接，但不会调用 `setMotionEnable(true)`，也不会自动执行姿态：

```text
lowlevel> status
lowlevel> motors
lowlevel> stand
lowlevel> lie
lowlevel> damping
lowlevel> release
lowlevel> quit
```

- `stand`：按需调用 `setMotionEnable(true)`，从实时关节位置平滑移动到站立目标并持续保持。
- `lie` / `lie-down`：按需调用 `setMotionEnable(true)`，从实时关节位置平滑移动到趴下目标并持续保持。
- `damping`：按需使能 Low-level，位置刚度设为 0，保留速度阻尼。
- `release`：先发送短时阻尼，再停止控制线程并调用 `setMotionEnable(false)`。
- `quit` / `Ctrl+C`：执行释放流程，并在断开前调用 `restoreMotionControlMode()` 恢复内置运控。

姿态控制周期为 50 Hz，默认轨迹时间为 2 秒，单周期位置变化不超过 0.25 rad。程序按 `(limbNo, jointNo)` 匹配观测与控制，不依赖数组顺序；当实际跟踪误差超过 0.25 rad 时暂停轨迹推进。姿态命令只支持标准 DV500 12 关节布局，其他布局会被拒绝。

Low-level SDK 没有 `take` / `startControl` 接口：`connect()` 建立并维护 session，`setMotionEnable(true/false)` 切换 prepare。CLI 直接沿用这套语义，不增加伪造的取权命令。

站立目标每腿为 `hip=0.0, thigh=0.8, calf=-1.5` rad。趴下目标为 `thigh=1.10, calf=-2.72` rad，左腿 `hip=+0.48` rad、右腿 `hip=-0.48` rad。Kp/Kd 使用 DV500 板端 `motionCapacity` 中已经验证的站立/趴下配置。

---

## 六、Python SDK

模块：`robot_motion_sdk`，源码 `uniubi_robot_sdk_py/`
- pybind11 binding：`uniubi_robot_sdk_py/src/MotionSdkPython.cpp`
- Python wrapper：`uniubi_robot_sdk_py/robot_motion_sdk/__init__.py`
- pybind11 依赖：`uniubi_robot_sdk_py/ThirdParty/pybind11/`

### 6.1 当前 binding 覆盖范围（已与 C++ 接口对齐）

**全局服务（`sdk.service` —— 对应 `IMotionSdkService` 单例）：**

| C++ 接口 | Python wrapper |
|---|---|
| `version()` | `sdk.service.version()` —— 返回 SDK 版本字符串 |
| `setLogCallback` | `sdk.service.set_log_callback(cb)`；签名 `(level: LogLevel, msg: str) -> None` |
| `initialService` | `sdk.service.initial(file_or_none, server_name, timeout=30)` |
| `shutdown` | `sdk.service.shutdown()` |

**LowLevel client（`sdk.MotionLowLevelClient` —— 对应 `IMotionLowLevelClient`）：**

| C++ 接口 | Python wrapper |
|---|---|
| `create()` | `MotionLowLevelClient()` 无参构造（板内单设备） |
| `connect / disconnect` | `connect(observed_hz=500, lease_ms=0)` / `disconnect()` |
| `getState / getLastError` | `get_state()` / `get_last_error()`（返回 enum） |
| `setMotionEnable` | `set_motion_enable(enable)` |
| `emergencyStop` | `emergency_stop(timeout_ms=5000)` |
| `createMediaBusClient` | `create_media_bus_client()`；返回 `MediaBusClient`（同一 client 复用同一实例，仅 `aarch64` 板内本地媒体帧订阅使用；Python 需先确认 `sdk.MEDIA_ENABLED == True`） |
| `sendControl(action[, cmd])` | `send_control(action, cmd=None)`；`action` 是 `sdk.MotorCtrlAction()`，动作相关控制帧传 `sdk.LowLevelMotionCmd()` 并填写 `action/ac_name` |
| `sendMaxTorque(action)` | `send_max_torque(action)`；使用 `action.motors[i].torque` 表示目标最大扭矩 |
| `getLatestObservation` | `get_latest_observation(timeout_ms=5)`；返回 `LowLevelMotionObserved` 或 `None` |
| `getSensorObservation` | `get_sensor_observation(timeout_us=5000)`；返回 `SensorObserved` 或 `None`（GPS + UWB，timeout 单位 us，默认 5000us=5ms） |
| `getMotorLayout` | `get_motor_layout(timeout_ms=5000)`；返回 `MotorLayout` 或 `None` |
| `restoreMotionControlMode` | `restore_motion_control_mode(timeout_ms=5000)`；返回 bool |
| `setConnectCallback` | `set_connect_callback(cb)` 或装饰器 `@client.on_connect`；签名 `(state, error)` |

数据结构 `MotorCtrl / MotorCtrlAction / LowLevelMotionCmd / MotorObserved / MotorInfo / MotorLayout / IMUObserved / Vector3f / Quaternionf / PowerObserved / TRCStickFrame / LowLevelMotionObserved / SensorObserved / GPSFrame / GEOGPoint / UWBRawObserved` 全部 expose 为 Python 类（字段下划线命名：`limb_no`, `joint_no`, `kp_gain`, `kd_gain`, `motor_num`, `charge_voltage`, `velocity_x` 等）。

### 6.2 ⚠ 退出死锁规避（必读）

**典型死锁场景**：
- Python 主线程持有 GIL → 解释器 atexit 阶段开始 GC
- GC 析构 `client` 触发 C++ 析构链 → 内部 `disconnect()` → 等待 SDK 内部线程结束
- SDK 内部线程在 RPC 调用中，需要主线程释放 GIL 才能继续
- SDK 内部线程持有的 Python 回调对象需要析构 —— 析构也需要 GIL
- **主线程等内部线程结束 → 内部线程等 GIL → 死锁**

**规避做法**：

```python
# ❌ 不要这样：靠 GC 析构
def main():
    client = sdk.MotionLowLevelClient()
    client.connect()
    ...
    # 函数结束，client 进入 GC —— 死锁风险

# ✓ 正确：try/finally 显式释放
def main():
    client = sdk.MotionLowLevelClient()
    try:
        client.connect()
        ...
    finally:
        client.disconnect()       # 主线程持 GIL，SDK binding 内部释放 GIL，内部线程才能继续完成清理
        sdk.service.shutdown()
```

**SIGINT/SIGTERM 处理**：handler 内**只置位标志**，不做任何 IO / SDK 调用；在主循环检测标志后走 finally：

```python
_stop = False
def _on_signal(signum, frame):
    global _stop
    _stop = True
signal.signal(signal.SIGINT, _on_signal)
signal.signal(signal.SIGTERM, _on_signal)
```

完整可运行示例：`uniubi_robot_sdk_py/examples/example_lowlevel.py`

### 6.3 Python 使用示例

完整可运行版本：`uniubi_robot_sdk_py/examples/example_lowlevel.py`

```python
import signal
import sys
import threading
import time

import robot_motion_sdk as sdk


_stop = False
def _on_signal(signum, frame):
    global _stop
    _stop = True


def main() -> int:
    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    if not sdk.service.initial(None, "myAppLowLevel"):
        print("SDK init failed")
        return 1

    client = sdk.MotionLowLevelClient()
    try:
        state_event = threading.Event()

        @client.on_connect
        def _on_connect(state: sdk.LowLevelState, err: sdk.LowLevelError):
            if state == sdk.LowLevelState.kPrepared:
                print("[low] prepared (ready for send_control)")
            elif state == sdk.LowLevelState.kConnected:
                print("[low] connected (call set_motion_enable to prepare)")
            elif state == sdk.LowLevelState.kConnecting:
                print(f"[low] connecting: err={err}")
            elif state == sdk.LowLevelState.kConnectionLost:
                print(f"[low] connection lost (auto-reconnecting): err={err}")
            elif state == sdk.LowLevelState.kDisconnected:
                print(f"[low] disconnected: err={err}")
            if err == sdk.LowLevelError.kMasterSwitchFailed:
                print("[low] master role switch failed (peer may hold motion), retrying...")
            state_event.set()

        def wait_state_cb(target: sdk.LowLevelState, timeout_s: float) -> bool:
            deadline = time.monotonic() + timeout_s
            while client.get_state() != target:
                if _stop:
                    return False
                remain = deadline - time.monotonic()
                if remain <= 0:
                    return False
                state_event.clear()
                state_event.wait(remain)
            return True

        if not client.connect(observed_hz=500, lease_ms=60000):
            print(f"connect failed: {client.get_last_error()}")
            return 1

        if not wait_state_cb(sdk.LowLevelState.kConnected, 10.0):
            print("wait connected timeout")
            return 1

        if not client.set_motion_enable(True):
            print(f"set_motion_enable(True) request rejected: {client.get_last_error()}")
            return 1

        if not wait_state_cb(sdk.LowLevelState.kPrepared, 60.0):
            print("wait prepared timeout")
            return 1

        layout = client.get_motor_layout()
        if layout is None:
            print(f"get_motor_layout failed: {client.get_last_error()}")
            client.set_motion_enable(False)
            return 1
        print(f"[low] motor layout: {layout.motor_num} motor(s)")
        for i, mi in enumerate(layout.motors):
            print(f"  motor[{i}]: limb={mi.limb_no} joint={mi.joint_no} name={mi.name}")

        # 硬件首跑安全前提：
        # - 仅在吊架 / 急停可触达 / 空旷场地条件下运行；
        # - 下方零目标、零增益、零前馈力矩只是通信与观测闭环模板，不是平衡站立控制器；
        # - 真实闭环控制应从当前观测姿态初始化目标，并使用经过验证的阻尼、增益和力矩策略。
        action = sdk.MotorCtrlAction()
        motors = []
        for mi in layout.motors:
            m = sdk.MotorCtrl()
            m.limb_no = mi.limb_no
            m.joint_no = mi.joint_no
            m.position = 0.0
            m.velocity = 0.0
            m.kp_gain = 0.0
            m.kd_gain = 0.0
            m.torque = 0.0
            motors.append(m)
        action.motor_num = len(motors)
        action.motors = motors

        cmd = sdk.LowLevelMotionCmd()
        cmd.action = 1
        cmd.ac_name = "standing"

        cycle_period = 0.020   # 50Hz
        obs_timeout_ms = 5
        deadline = time.monotonic() + 60.0
        next_cycle = time.monotonic()
        dump_at = time.monotonic()

        while time.monotonic() < deadline:
            if _stop:
                break
            next_cycle += cycle_period

            obs = client.get_latest_observation(obs_timeout_ms)
            if obs is None:
                sleep = next_cycle - time.monotonic()
                if sleep > 0: time.sleep(sleep)
                continue

            now = time.monotonic()
            if now - dump_at >= 1.0:
                a = obs.imu.accel; g = obs.imu.gyro; q = obs.imu.quaternion
                m0 = obs.motors[0]
                print(f"[obs] imu: temp={obs.imu.temp:.1f}  "
                      f"accel=({a.x:+.2f},{a.y:+.2f},{a.z:+.2f})  "
                      f"gyro=({g.x:+.3f},{g.y:+.3f},{g.z:+.3f})  "
                      f"quat=({q.w:.3f},{q.x:.3f},{q.y:.3f},{q.z:.3f})  "
                      f"power={obs.power.charge_voltage:.2f}V  "
                      f"motor[0]: pos={m0.position:+.3f} vel={m0.velocity:+.3f} torq={m0.torque:+.3f}")
                dump_at = now

            if not client.send_control(action, cmd):
                print(f"send_control failed: {client.get_last_error()}")
                break

            sleep = next_cycle - time.monotonic()
            if sleep > 0: time.sleep(sleep)

        client.set_motion_enable(False)
    finally:
        try: client.disconnect()
        except Exception as e: print(f"disconnect raised: {e}")
        try: sdk.service.shutdown()
        except Exception as e: print(f"shutdown raised: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## 七、注意事项

1. **回调注册时机**：`setConnectCallback` 建议在 `connect()` 之前调，便于第一时间感知首次连接状态。
2. **回调线程**：`ConnectCallback` 在 SDK 内部线程触发；回调里反调 SDK 接口要保证可重入。
3. **状态查询**：`getState()` / `getLastError()` 线程安全；`getLastError()` 读后清零。
4. **`setMotionEnable` 是异步**：返回 true 仅表示请求已受理，state 由 SDK 推进至 `kPrepared` / `kConnected`，调用方应通过 `getState()` 或 `ConnectCallback` 感知到位。
5. **`sendControl` / `sendMaxTorque` 仅在 `kPrepared` 生效**：其它状态返 false + `kNotPrepared` / `kNotConnected`；`motorNum` 必须 ∈ `[1, kLowLevelMaxMotorNum]`，否则返 `kInvalidArgument`（不做隐式 clamp）。
6. **`sendMaxTorque` 是低频配置接口**：提交后为异步硬件切换，默认约 10 ms 内不要继续下发位置控制帧；通过后续观测确认 `maxTorque`。
7. **观测拉模式**：`getLatestObservation` 在指定 timeout 内获取运控观测量，未取到返回 false。
8. **`getMotorLayout` 缓存**：首次走 RPC，命中后 SDK 本地缓存，硬件配置启动后不变。
9. **lease 默认值**：`connect(observedHz, 0)` → 使用默认 60s；最终生效值由服务端确定，SDK 按真实值自动续约。
10. **断连自动重连**：`kConnectionLost` 状态下 SDK 按内置退避策略自动重试，外部不需手动干预；如需主动放弃，调用 `disconnect()`。

---

## 八、调试与故障排查

### 8.1 机器人侧最小验证（先验）

调用 SDK 之前先把机器人侧的"对端"确认好，避免在客户端瞎找原因。

| 检查项 | 命令 / 方法 | 期望结果 |
|---|---|---|
| motionServer 是否在跑 | `ps -ef \| grep motionServer` | 进程存在 |
| 共享内存权限 | `ls -la /dev/shm/ \| grep motion` | 文件存在且当前用户可读 |
| 实时日志 | `journalctl -u motionServer -f` | 无报错刷屏 |

### 8.2 SDK 端常见现象排查

| 现象 | 检查项 | 解决思路 |
|---|---|---|
| `initialService` 返回 false | 日志 `errorf` 输出 | 看错误码：`kRpcConnectFailed` → DDS 域起不来（domain id 不对 / 本机环境未就绪） |
| `create()` 返回 nullptr | SDK 是否已 `initialService` 成功 | 必须先成功初始化再 `create()` |
| `connect()` 一直在 `kConnecting` | 1. ConnectCallback 推的 error 码<br>2. SHM 文件权限<br>3. 机器人侧 motionServer 是否在跑 | `kRpcAcquireRejected` → 控制权被别人占；`kMasterSwitchFailed` → 切换运控 master 失败（对端仍在运控） |
| `setMotionEnable(true)` 后 state 不切 `kPrepared` | 1. `getLastError()` 取错误码<br>2. ConnectCallback 是否报 `kPrepareRejected` | 机器人侧 motor 上电流程慢（关节自检 + 校准），可能需要等几秒到几十秒 |
| `getLatestObservation` 频繁返 false | 1. 当前 state 是不是 `kPrepared`<br>2. 观测频率（observedHz）是否设得过高、超出硬件能力 | 板内 SHM 模式应该几乎不丢；持续丢说明频率超出硬件能力或服务端异常 |
| `sendControl` 返 false，state 显示 `kPrepared` | `getLastError()` 取值；`motorNum` 是否合法 | `kSessionExpired` → 服务端 session 失效，等自动重连；`kInvalidArgument` → action.motorNum 超出 [1, kLowLevelMaxMotorNum] |
| `MotorObserved.error` 非 0 | 看 §4.4.2 `MotorDeviceErrno` 枚举 | `0~6`/`59`/`60`/`63` 是电机上报故障；`64+` 是 SDK / 服务端检测的状态（如 `motorControlOffline`） |
| **静默无响应**（任何接口都 timeout） | DDS QoS 不兼容 | 客户端 / 服务端 IDL 或 Cyclone DDS 版本不一致；用 `ddsperf sanity` 做最小握手 |

### 8.3 打开 SDK 内部日志

```cpp
IMotionSdkService::instance()->setLogCallback([](IMotionSdkService::LogLevel lv,
                                                  const char* msg, int32_t len) {
    static const char* tags[] = {"DBG","TRC","INF","WRN","ERR","FAT"};
    fprintf(stderr, "[sdk %s] %.*s\n", tags[lv], len, msg);
});
```

不注册 callback 时 SDK 默认把日志输出到 `stdout`。生产环境建议接进自家日志系统集中查看。

---
