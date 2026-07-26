# 宇泛智能机器狗高级控制 SDK 接口手册

> SDK 入口类：`uniubi::RobotSdk::IMotionHighLevelClient`
> C++ 头文件：`include/uniubi/robot_sdk/MotionHighLevelClient.h`

---

## 目录

- [一、SDK 概述](#一sdk-概述)
- [Quick Start](#quick-start)
- [开发工程模板](#开发工程模板)
- [二、枚举定义](#二枚举定义)
- [三、回调定义](#三回调定义)
  - [3.3 回调汇总](#33-回调汇总)
- [四、接口定义](#四接口定义)
  - [4.1 全局初始化与实例创建](#41-全局初始化与实例创建)
  - [4.2 生命周期与控制权](#42-生命周期与控制权)
  - [4.3 运控动作](#43-运控动作)
  - [4.4 音频播放器](#44-音频播放器)
  - [4.5 系统与设备](#45-系统与设备)
  - [4.6 音视频通道](#46-音视频通道imediabusclient)
  - [4.7 观测量数据面](#47-观测量数据面)
- [五、C++ 使用示例](#五c-使用示例)
- [六、Python SDK](#六python-sdk)
  - [6.1 binding 覆盖范围](#61-当前-binding-覆盖范围已与-c-接口对齐)
  - [6.2 退出死锁规避（必读）](#62--退出死锁规避必读)
  - [6.3 Python 使用示例](#63-python-使用示例)
- [七、注意事项](#七注意事项)
- [八、调试与故障排查](#八调试与故障排查)

---

## 一、SDK 概述

- 只有控制面，状态/数据查询走 query 接口；事件订阅通过 `EventCallback`
- 控制权由 `startControl` 显式获取，SDK 内部周期续约维持
- 直到 `releaseControl` / `disconnect` 主动释放，或服务端 session 超时被动失效
- 协议字段编码：UTF-8 JSON 字符串
- 支持直接部署在机器人大脑主板上开发自有应用（板内模式），也支持外部主机远端接入

---

## Quick Start

最小运行流程（完整版本见 §五）：

**C++**

```cpp
#include <chrono>
#include <thread>
#include "MotionSdkService.h"
#include "MotionHighLevelClient.h"

using namespace uniubi::RobotSdk;
using HLState = IMotionHighLevelClient::HighLevelState;

int main() {
    auto svc = IMotionSdkService::instance();
    svc->setNetworkInterface("eth0");        // 默认 eth0；如机器没有 eth0 必须改成实际网卡（板内可省略）
    svc->initialService(nullptr, "myApp");

    auto client = IMotionHighLevelClient::create();  // 板内单设备
    client->connect();                              // 进入高级模式
    client->startControl(/*timeout=*/30000);        // 请求控制权
    const auto controlDeadline = std::chrono::steady_clock::now() + std::chrono::seconds(30);
    while (client->getState() != static_cast<int32_t>(HLState::kControlled)) {
        if (std::chrono::steady_clock::now() >= controlDeadline) {
            client->disconnect();
            IMotionSdkService::instance()->shutdown();
            return 1;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }

    client->standUp();
    std::this_thread::sleep_for(std::chrono::seconds(5));
    client->lieDown();
    std::this_thread::sleep_for(std::chrono::seconds(5));

    client->releaseControl();
    client->disconnect();
    IMotionSdkService::instance()->shutdown();
    return 0;
}
```

**Python**

```python
import time
import robot_motion_sdk as sdk

sdk.service.set_network_interface("eth0")       # 默认 eth0；机器无 eth0 时改成实际网卡
sdk.service.initial(None, "myApp")
client = sdk.MotionHighLevelClient()             # 板内单设备
try:
    client.connect()
    client.start_control(timeout_ms=30000)
    deadline = time.monotonic() + 30.0
    while client.get_state() != sdk.HighLevelState.kControlled:
        if time.monotonic() >= deadline:
            raise TimeoutError("wait kControlled timeout")
        time.sleep(0.05)

    client.stand_up()
    time.sleep(5)
    client.lie_down()
    time.sleep(5)

    client.release_control()
finally:
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
| 公开头 | SDK 仓库 `include/uniubi/robot_sdk/` | `MotionSdkService.h` / `MotionHighLevelClient.h` / `MotionSdkProtocol.h` |
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
./my_robot_app                  # 默认网卡 eth0
./my_robot_app wlan0            # 用 wlan0 网卡（仅远端模式）
```

---

## 二、枚举定义

### 2.1 `HighLevelState` —— 客户端状态

| 值 | 含义 |
|---|---|
| `kDisconnected` (0) | 初始 / `disconnect()` 后 |
| `kConnected` (1) | SDK 就绪但未持有控制权 |
| `kControlled` (2) | 已通过 `startControl()` 取得控制权，可下发动作 |

### 2.2 `HighLevelError` —— 失败原因

| 值 | 含义 |
|---|---|
| `kNone` | 无错 |
| `kRpcConnectFailed` | SDK 未初始化 / 通信通道未就绪 |
| `kRpcAcquireRejected` | `startControl` 被拒（被他人占 / 整体超时） |
| `kRpcCallFailed` | RPC 调用失败（含超时 / 通道断 / 编解码错 / id 不匹配等）|
| `kSessionExpired` | lease 到期，服务端回收控制权 |
| `kSessionRevoked` | 被另一方接管 / sessionId 失配 |
| `kNotConnected` | 未 connect 即调需要连接的接口 |
| `kNotControlled` | 未持权即调动作类接口 |
| `kDataNotUpdate` | 观测量数据面未就绪（如 `getPowerInfo` 新鲜度窗口内无数据） |
| `kActionRejected` | RPC 动作被服务端拒 |
| `kInvalidParam` | 入参非法（如动作参数 JSON 解析失败） |

---

## 三、回调定义

### 3.1 `ConnectCallback` —— 控制权变化

```cpp
using ConnectCallback = std::function<void(HighLevelState state, HighLevelError error)>;
```

回调由 SDK 内部线程触发。典型时序：

| 触发场景 | state | error |
|---|---|---|
| `startControl` 成功 | `kControlled` | `kNone` |
| 自己 `releaseControl` 完成 | `kConnected` | `kNone` |
| `startControl` 整体超时 | `kConnected` | `kRpcAcquireRejected` |
| lease 到期 | `kConnected` | `kSessionExpired` |
| 被另一方接管 | `kConnected` | `kSessionRevoked` |

### 3.2 `EventCallback` —— 业务事件

```cpp
using EventCallback = std::function<void(const std::string& topic, const std::string& payloadJson)>;
```

事件派发线程触发。`connect()` 时 SDK 内部订阅以下事件：

| topic | 用途 |
|---|---|
| `statistics/play_list` | 音频播放状态变化 |
| `statistics/device_status` | 设备状态变化（电池/网络） |

> 控制权变化由 SDK 内部消费并体现在 `HighLevelState`，**不通过此回调上抛**。

### 3.3 回调汇总

SDK 暴露的回调，注册时机和用途见下表。

| 回调 | 用途 | 注册接口 |
|---|---|---|
| `LogCallback` | 接收 SDK 内部日志输出（调试 / 运维可重定向到自家日志框架） | `IMotionSdkService::setLogCallback` |
| `DeviceDiscover` | 多设备发现期间，每收到一台机器人响应触发一次（上抛 SN + 设备详情 JSON） | `IMotionSdkService::setDiscoverCallback` |
| `ConnectCallback` | 控制权 / 连接状态变化（建联 / 失权 / 重连等），驱动调用方状态机 | `IMotionHighLevelClient::setConnectCallback` |
| `EventCallback` | 服务端主动推送的业务事件（音频状态、设备状态等） | `IMotionHighLevelClient::setEventCallback` |
| `MotionObservedCallback` | 运控观测量 `LowLevelMotionObserved`（含 power），需先 `setObservedEnable` 开启 | `IMotionHighLevelClient::setMotionObservedCallback` |
| `GPSCallback` | GPS 观测帧 `GPSFrame`，需先 `setObservedEnable` 开启 | `IMotionHighLevelClient::setGPSCallback` |
| `RawAudioFrameCallback` | 接收音频原始帧 `AudioFrame`，回调参数 `(channel, frame)` | `IMediaBusClient::startRawAudioFrame` |
| `RawVideoFrameCallback` | 接收视频原始帧 `VideoFrame`，回调参数 `(channel, frame)` | `IMediaBusClient::startRawVideoFrame` |
| `EncodedVideoFrameCallback` | 接收视频编码帧 `EncodedVideoFrame`，回调参数 `(channel, frame)` | `IMediaBusClient::startEncodedVideoFrame` |

#### 回调内严禁阻塞

**所有回调函数体内严禁执行任何阻塞操作 —— 回调由 SDK / 媒体数据线程触发，阻塞会直接把内部线程卡住**：

- ❌ 不能 `sleep` / 等待 mutex / 等待 condvar
- ❌ 不能调任何同步 RPC 接口（`startControl` / `startAction` / `queryXxx` / 等）
- ❌ 不能做磁盘 IO / 网络 IO / 大块内存分配
- ❌ 不能 `disconnect()` / `shutdown()` 本对象
- ❌ 媒体帧回调里不要直接长时间编码/转码/落盘；需要保存帧时建议把必要元数据和数据引用/拷贝投递给业务线程处理

**视频原始帧访问必须按 plane + stride**：`VideoFrame` 的物理/虚拟内存布局由平台决定，特别是 NVIDIA 平台可能多平面且不连续。不要把 `frame.data()` 当作整张图的连续内存直接按 `width * height * bpp` 读取；应根据 `VideoFrameInfo.pixelFormat` 判断平面数量，再按 `virAddr[plane] + row * stride[plane]` 逐行访问有效宽度。

内部线程被卡死后果是连锁的：事件投递停摆、状态机不再推进、心跳超时被服务端踢线、重连流程也无法启动。

**正确做法**：在回调里只做"轻量记录 / 通知"：

```cpp
client->setConnectCallback([&](HighLevelState s, HighLevelError e) {
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
| `server` | `const char*` | 应用标识，用于 RPC / 日志区分多实例（如 `"myAppHighLevel"`），调用方自定义 |
| `timeout` | `uint32_t` | 等待系统环境就绪的超时（**秒**，默认 30）。板内模式下若 SDK 比系统环境先起，可能需要等待；超时未就绪返回 `false` |

进程级一次性初始化，必须在创建任何 client 之前调用。返回 `true` 表示初始化成功。

```cpp
/// SDK 版本字符串，格式："<semver> (commit <git-short-sha>)"，如 "0.1.0 (commit 7bb376b2)"
/// 任意时刻可调，无需先 initialService；可用于运行时日志 / bug 上报 / 兼容性检查
static const char* version();
```

> **版本兼容性**：SDK 与机器人侧约定走 OMG XTYPES `@appendable`（IDL 字段可追加，向后兼容）。若 SDK 与机器人版本严重不一致，典型现象是 RPC 调用**静默无响应**（DDS 报 `RequestedIncompatibleQos` 但不抛错）。出现这种现象时把 `version()` 输出贴到故障报告里。

#### 4.1.2 setter / 查询接口（必须在 `initialService` 之前调用）

```cpp
/// 注册日志回调
void setLogCallback(LogCallback cb);

/// 多设备场景下指定 SDK 使用的网络接口（如 "eth0"、"wlan0"）
/// 板内单设备模式忽略；远端模式不指定时由 Cyclone DDS 自动选择
void setNetworkInterface(const char* iface);

/// 多设备场景下注册设备发现回调
/// cb(sn, infoJson) —— infoJson 是设备详情 JSON 字符串，典型字段见下方
void setDiscoverCallback(DeviceDiscover cb);

/// 查询当前部署是否多设备
///   板内（SDK 与机器人同机）→ false
///   远端主机 / 多机器人      → true
bool isMultiDevice() const;

/// 主动发起一次设备发现（非阻塞）
///   - 当前已有发现窗口未过期 → 延长窗口到至少 timeoutMs
///   - 窗口已过期            → 开新窗口
/// 期间收到的每条机器人响应通过 setDiscoverCallback 注册的回调上抛
bool discoverDevices(uint32_t timeoutMs = 10000);
```

##### `setDiscoverCallback` 回调参数 `info` 的 schema

`info` 是 JSON 字符串，调用方自行 `parse`。典型字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| `version` | string | 整机软件版本 |
| `brainVersion` | string | 大脑（高层算法）版本 |
| `deviceCP` | string | 主控芯片标识 |
| `deviceModel` | string | 设备型号 |
| `productDate` | string | 出厂日期 |
| `network` | object | 网络状态（同 `querySystemStatus.network`，含 `ether` / `hotspot` / `mobile` / `wlan` 子对象） |

> 设备版本演进可能新增字段；客户端遇未知字段宽容透传（不解析也不报错）。完整 `network` 子结构参见 [§4.5.1 querySystemStatus](#451-querysystemstatus-出参字段)。

##### 关于 `setNetworkInterface`

远端模式下 SDK 在 `/tmp/motion_sdk_host_<pid>.xml` 自动渲染 Cyclone DDS QoS profile（`shutdown` 时清理）。该 profile 决定 DDS 走哪张网卡：

- **默认值** `"eth0"` —— 不调 `setNetworkInterface` 时 SDK 用 eth0 渲染 profile。`<NetworkInterface name="eth0" priority="3" multicast="default" presence_required="true" />`。`presence_required="true"` 表示该网卡若不存在 SDK 启动直接失败（早期暴露问题）
- **调** `setNetworkInterface("wlan0")` 等 → 覆盖默认值，按你指定的网卡名渲染
- 主机如果没有 `eth0`（比如笔记本只有 `wlan0` / `enp3s0`），**必须显式 setNetworkInterface 否则起不来**

##### 如何查询本机可用网卡

在跑 SDK 的主机上选合适的网卡名（必须是**实际连接到机器人所在网段**的那个）：

```bash
# 方法 1：推荐，列出所有 interface 名 + 状态
ip -br link
#  lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
#  eth0             UP             aa:bb:cc:dd:ee:ff <BROADCAST,MULTICAST,UP>
#  wlan0            UP             aa:bb:cc:dd:ee:01 <BROADCAST,MULTICAST,UP>

# 方法 2：看 IP 地址 + 路由，确认哪个网卡能到机器人
ip -br addr
ip route

# 方法 3：旧系统兼容
ifconfig -s

# 方法 4：内核侧文件枚举
ls /sys/class/net/
```

挑选规则：
1. 状态必须是 `UP`
2. 必须有 IP 且与机器人在同一 LAN（或路由可达）
3. 推荐用有线网卡（`eth*` / `enp*`）；wifi（`wlan*`）多播稳定性差，且漫游时 DDS discovery 可能丢
4. **不能用** `lo`（回环）—— 除非 SDK 与机器人同机部署（那个场景属于板内模式，用不到 setNetworkInterface）

把挑出的名字直接传给 `setNetworkInterface("eth0")` 即可。

##### 多设备场景下完整流程

```cpp
auto svc = IMotionSdkService::instance();

/// 1. 在 initialService 之前注册回调 + 网卡（必须的顺序）
svc->setLogCallback(...);
svc->setNetworkInterface("eth0");
svc->setDiscoverCallback([](const std::string& sn, const std::string& info) {
    /// 用户自己维护设备表：解析 info（JSON 字符串）拿到 deviceModel / network / version 等
    printf("device online: sn=%s info=%s\n", sn.c_str(), info.c_str());
});

/// 2. 全局初始化
svc->initialService(nullptr, "myApp");

/// 3. 判断是否需要发现
if (svc->isMultiDevice()) {
    svc->discoverDevices(2000);     // 非阻塞；2s 内回调上抛在线设备
    // ... 用户线程等 SN 收齐后选 target
    auto client = IMotionHighLevelClient::create(target_sn);
} else {
    auto client = IMotionHighLevelClient::create();   // 板内单设备，create(bool)
}
```

#### 4.1.3 客户端实例创建

`create` 提供两个重载，分别对应板内单设备与远端按 SN 两种部署：

```cpp
/// 板内单设备：进程单例。asMaster 指定是否以 master 角色入会
static std::shared_ptr<IMotionHighLevelClient> create(bool asMaster = false);

/// 远端多设备：按目标机器人 SN 创建
static std::shared_ptr<IMotionHighLevelClient> create(std::string deviceId);
```

| 重载 | 参数 | 说明 |
|---|---|---|
| `create(bool asMaster = false)` | `asMaster` | **板内单设备**用，进程单例；`asMaster` 指定本端是否以 master 角色入会 |
| `create(std::string deviceId)` | `deviceId` | **远端多设备**用，目标机器人 SN；空串会返回 `nullptr` |

远端模式下 SDK 内部把 `deviceId` 作为路由字段塞进每个 RPC 请求，只有 SN 匹配的机器人响应；多个 HL client 各自持有自己的目标 SN，互不串扰。

##### 拿到 `deviceId` 的两种途径

1. **通过 `discoverDevices` 在线搜索**：调 `setDiscoverCallback` 注册回调 + `discoverDevices(timeoutMs)` 主动扫，回调里拿到 SN。适合"客户端不预先知道有哪些机器人在网内"的场景（详见下面 §4.1.2 多设备完整流程）。
2. **跳过搜索，直接用已知 SN 构造**：如果调用方已经通过**其他途径**（配置文件 / 用户输入 / 二维码扫描 / 资产管理系统 / 上一次会话保存的 SN 等）知道目标机器人 SN，**直接** `create(sn)` 即可，**不需要先调 `discoverDevices`**。

```cpp
/// 场景：SN 来自用户配置 / 部署清单
const std::string sn = loadDeviceSnFromConfig();   // 你的来源逻辑
auto client = IMotionHighLevelClient::create(sn);
client->connect();
```

后续 `connect` / `startControl` / 动作调用按正常流程走 —— SDK 通过 RPC 直接定位该 SN 的机器人。如果该 SN 在网内不存在或不响应，`connect` 失败时 `getLastError()` 会返 `kRpcCallFailed` / `kRpcConnectFailed`。

### 4.2 生命周期与控制权

| 方法 | 状态要求 | 说明 |
|---|---|---|
| `bool connect(int32_t leaseMs = 0)` | 任意 | 进入高级模式。`leaseMs<=0` 时 SDK 默认 60000ms；有效范围 5s ~ 5min，超出按边界值替代。**注意 `leaseMs` 是 int32** |
| `void disconnect()` | 任意 | 关闭连接与事件订阅 |
| `bool startControl(uint32_t timeout = 10000)` | 已 connect | 异步请求控制权；`timeout` 是整体截止时间（ms） |
| `bool releaseControl()` | `kControlled` | 异步释放，完成后状态切回 `kConnected` |
| `int32_t getState() const` | 任意 | 当前 `HighLevelState` |
| `int32_t getLastError() const` | 任意 | 读后清零的最后失败原因 |
| `void setConnectCallback(ConnectCallback cb)` | `kDisconnected` | 必须 connect 前注册 |
| `void setEventCallback(EventCallback cb)` | `kDisconnected` | 必须 connect 前注册 |
| `IMediaBusClient::Ptr createMediaBusClient()` | 任意 | 创建音视频通道客户端；仅 `aarch64` 板内本地媒体帧订阅使用，详见 §4.6 |

### 4.3 运控动作

#### 4.3.1 控制类（需 `kControlled`）

| 方法 | 参数 |
|---|---|
| `bool emergencyStop(uint32_t timeout = 5000)` | 急停 |
| `bool recoveryStand(uint32_t timeout = 5000)` | 跌倒后恢复站立（自我翻正 + 起立）|
| `bool startAction(const std::string& action, const std::string& paramsJson = "", uint32_t timeout = 5000)` | `action`：动作名；`paramsJson` 字段以 `getMotionCapabilities()` 返回的 `params` 列表为准，一次性动作可传 `""` |
| `bool stopAction(uint32_t timeout = 5000)` | 停止当前动作 |
| `bool setActionParams(const std::string& paramsJson = "", uint32_t timeout = 5000)` | 运行期调当前动作参数（不切动作）；可调字段由当前动作的 `params` 列表决定（见 `getMotionCapabilities`），**全量重写语义**（未传字段归 0）|
| `bool setRawControlCmd(TRCStickFrame& frame)` | 动作控制帧（按钮 + 摇杆 + 扳机），见下节 |
| `bool damp(uint32_t timeout = 5000)` | 进入阻尼/慢沉（软卸力），关节低刚度可控下沉 |
| `bool lieDown(uint32_t timeout = 5000)` | 趴下/卧倒 |
| `bool standUp(uint32_t timeout = 5000)` | 站立 |
| `bool move(float vx, float vy, float vyaw, uint32_t timeout = 5000)` | 行走：`vx` 前后线速度（正前进）、`vy` 左右线速度、`vyaw` 转向角速度；持续生效直到 `stopAction` 或后续动作/参数覆盖 |

**动作安全分级**

- 推荐新手首次联调使用 `standUp()` / `lieDown()`，或 `startAction("standing")` / `startAction("laying")`。
- `walking` / `move` / `bipedStand` / `handstand` / `leftSideStand` / `rightSideStand` / `waveBody` / `waveHand` / `heartSit` / `tweak` / `peakLoadStand` / `jump*` / `damp` 属于高风险运动动作，应在空旷场地、机器人姿态稳定、具备人工接管条件时执行。
- `emergencyStop`、音频播放/暂停/停止、音频文件增删、摄像头补光灯亮度设置、TRC 归零帧不属于高风险运动动作，但仍要求调用方持有控制权或满足对应接口前置条件。

#### 4.3.1.1 `setRawControlCmd` —— 原始运动控制，模拟遥控手柄

本接口采用 50Hz 帧式输入，模拟遥控手柄的连续操作。**该接口走不可靠通道，不保证每一帧都送达**。需要可靠投递的场景请使用 `startAction()` 等 RPC 接口；本接口适用于连续摇杆 / 按键这类采样型输入。

接口同时承担两类输入：
- **按键组合切换动作**：通过 `buttons[]` 设置组合按键，触发 posture 动作（见下表映射）—— 等价于 `startAction()` 的功能
- **摇杆设置实时控制量**：通过 `axes[]` 设置摇杆量，控制当前动作的速度等运行期参数 —— 等价于 `setActionParams()` 的功能（例如 `walking` 时通过摇杆调节 `lineVelocityX / lineVelocityY / velocity`）

两类输入可同时在一帧中携带。

**标准遥控功能映射**

下表的 posture 动作快照来自 RobotService `motionCapacity` 的 `motionTRC.motionMap.posture`。对外按键名 Stand / Motion 在 SDK 中分别对应 `buttonBack` / `buttonStart`；`startAction()` 等 RPC 仍使用内部动作名。设备实际开放动作、`priority`、`exact`、`minHoldTime`、`axisRequire` 以 `getMotionCapabilities()` 返回为准。

| 分类 | 用户操作 | 中文标准名 | 英文标准名 | 用户说明 | SDK 输入 / 内部动作 |
|---|---|---|---|---|---|
| 安全 | LB + RB | 急停 | Emergency Stop | 立刻停下并趴下 | `buttonLB + buttonRB`；`emergencyStop` |
| 姿态 | LB + Y | 双足站立 | Two-Leg Stand | 后腿站起来 | `buttonLB + buttonY`；`bipedStand` |
| 姿态 | LB + A | 倒立 | Handstand | 前脚撑地倒立 | `buttonLB + buttonA`；`handstand` |
| 姿态 | LB + X | 左侧双足站立 | Left-Side Stand | 用左侧两脚站立 | `buttonLB + buttonX`；`leftSideStand` |
| 姿态 | LB + B | 右侧双足站立 | Right-Side Stand | 用右侧两脚站立 | `buttonLB + buttonB`；`rightSideStand` |
| 状态 | Stand + A | 趴下 | Lie Down | 趴到地上，进入安全低姿态 | `buttonBack + buttonA`；`laying` |
| 状态 | Stand + Y | 行走 | Walking | 进入可移动状态 | `buttonBack + buttonY`；`walking` |
| 状态 | Motion | 站立 | Standing | 进入站立状态 | `buttonStart`；`standing`（priority 0） |
| 表演 | LB + Motion | 扭一扭 | Wiggle | 原地扭动表演 | `buttonLB + buttonStart`；`waveBody` |
| 表演 | B | 招手 | Wave Hand | 执行招手动作 | `buttonB`；`waveHand` |
| 表演 | 按住 Y 1 秒 | 坐起画心 | Heart Sit | 坐起并完成画心动作 | `buttonY`；`heartSit`（minHoldTime 1000） |
| 移动 | 按住 A 1 秒 | 低速微动 | Tweak | 进入低速小幅移动模式 | `buttonA`；`tweak`（minHoldTime 1000） |
| 姿态 | Motion | 负重站立 | Peak Load Stand | 进入负重站立状态 | `buttonStart`；`peakLoadStand`（priority 2） |
| 特技 | RB + 方向键上 | 前跳 | Forward Jump | 向前跳一下 | `buttonRB + buttonUp`；`jumpForward` |
| 特技 | RB + Y | 前空翻 | Front Flip | 向前翻一下 | `buttonRB + buttonY`；`jumpFrontflip` |
| 特技 | RB + B | 侧空翻 | Side Flip | 向侧方翻转 | `buttonRB + buttonB` 且 `axesRT` ∈ [-1.0, 0.49]；`jumpSideflip` |
| 特技 | RB + A | 后空翻 | Back Flip | 向后翻一下 | `buttonRB + buttonA` 且 `axesRT` ∈ [-1.0, 0.49]；`jumpBackflip` |
| 特技 | 按住 RT + RB + A | 后空翻两圈 | Double Back Flip | 按住保险键后向后翻两圈 | `buttonRB + buttonA` 且 `axesRT` ∈ [0.5, 1.0]；`jumpDoubleBackflip` |
| 特技 | 按住 RT + RB + B | 侧空翻两圈 | Double Side Flip | 按住保险键后向侧方翻两圈 | `buttonRB + buttonB` 且 `axesRT` ∈ [0.5, 1.0]；`jumpDoubleSideflip` |
| 行走 | 左摇杆上 | 前进 | Forward | 往前走 | `axesLY` → `lineVelocityX > 0`（`walking`） |
| 行走 | 左摇杆下 | 后退 | Backward | 往后走 | `axesLY` → `lineVelocityX < 0`（`walking`） |
| 行走 | 左摇杆左 | 左移 | Move Left | 横着向左走 | `axesLX` → `lineVelocityY < 0`（`walking`） |
| 行走 | 左摇杆右 | 右移 | Move Right | 横着向右走 | `axesLX` → `lineVelocityY > 0`（`walking`） |
| 转向 | 右摇杆左 | 左转 | Turn Left | 向左转身 | `axesRX` → `velocity > 0`（`walking`） |
| 转向 | 右摇杆右 | 右转 | Turn Right | 向右转身 | `axesRX` → `velocity < 0`（`walking`） |
| 速度 | 方向键上 | 加速 | Speed Up | 走得更快 | `buttonUp`；切换 fast profile |
| 速度 | 方向键下 | 减速 | Slow Down | 走得更慢 | `buttonDown`；切换 slow profile |

字段语义：

- 表中的 `button*` 和 `axes*` 名称直接对应 `ButtonDefine` / `AxesDefine` 枚举。
- `buttonStart` 同时匹配 `standing`（priority 0）和 `peakLoadStand`（priority 2）；同一帧多个动作命中时由服务端按能力配置的 priority 和当前可用动作决策。
- `waveHand` / `heartSit` / `tweak` 的 `minHoldTime` 均为 `1000`；其余 posture 动作当前为 `0`。
- RT 在 SDK 中对应 `axesRT`；当前配置以 0.5 为单次 / 双次翻转动作的分界值。
- `require` / `axisRequire` / `priority` / `exact` / `minHoldTime` 不建议硬编码，应通过 `getMotionCapabilities()` 读取当前设备配置。

**前置条件**（任一不满足则 `setRawControlCmd` 返回 `false`）

- 当前必须处于 `kControlled`（已 `startControl` 持权）
- 服务端在 acquire 响应里下发了 `rawActionId`（未下发 → 该设备不支持 raw cmd，调用恒失败）
- `frame.valid` 必须为非 0

**使用约束**

- 不可靠传输：建议同一组合以 20ms 间隔重发 3 次以提高送达概率
- 触发后下一帧建议将组合按键清零，否则可能重复命中同一动作
- 急停优先推荐使用 `emergencyStop()` 接口（走可靠 RPC 通道）；raw cmd 中的 `emergencyStop` 组合用于模拟遥控器急停

#### 4.3.1.2 `walking` 动作参数（`startAction` / `setActionParams`）

动作的可调参数由服务端动态下发 —— 调用方应通过 `getMotionCapabilities()` 查询每个动作的 `params` 列表（字段名 / `min` / `max` / `unit`），不应硬编码。一次性动作（如 `jumpBackflip`）通常无可调参数。

`walking` 一般配置如下（实际取值以 `getMotionCapabilities` 返回为准）：

| paramsJson 字段 | 类型 | 含义 | 单位 |
|---|---|---|---|
| `velocity`      | float | **偏航角速度**（yaw rate），正左转负右转 | rad/s |
| `lineVelocityX` | float | 前后线速度，正前进负后退               | m/s   |
| `lineVelocityY` | float | 侧向线速度，正右负左                   | m/s   |

字段名与 `getMotionCapabilities` 返回的 `params[].name` 一致，也与 `queryMotionState` 返回的字段一致 —— **同一套 key 贯穿三处**，调用方学一次即可。

**示例**：

```json
// 直行 0.5 m/s
{"lineVelocityX": 0.5, "lineVelocityY": 0.0, "velocity": 0.0}

// 原地左转 0.5 rad/s
{"lineVelocityX": 0.0, "lineVelocityY": 0.0, "velocity": 0.5}

// setActionParams 是全量重写：要保留侧移/旋转的当前值，必须三个字段都重新传
{"lineVelocityX": 0.8, "lineVelocityY": 0.0, "velocity": 0.0}
```

**几条语义约定**：

- **全量重写**：`setActionParams` 跟 `startAction` 一样是**全量语义**——调用一次就用这次的 params 覆盖整套运行期参数，**未传字段归 0**。要保留 X 速度只改 yaw，必须三个字段都传齐
- **范围由服务端限制**：超出 `getMotionCapabilities` 返回的 `min`/`max` 时被服务端 clamp 到边界；不会报错
- **零速度不等于停止**：要停下来用 `stopAction()`，不要靠下发 `{lineVelocityX:0, lineVelocityY:0, velocity:0}`
- **三个字段独立**：完整运动需三轴组合（如边走边转：`{lineVelocityX: 0.5, velocity: 0.3}`）

**C++ 调用示例**：

```cpp
// 启动 walking 并立即设速度
client->startAction("walking", R"({"lineVelocityX":0.5,"lineVelocityY":0.0,"velocity":0.0})");

// 运行期调速（全量重写，必须把要保留的字段都带上）
client->setActionParams(R"({"lineVelocityX":0.8,"lineVelocityY":0.0,"velocity":0.0})");

// 停止
client->stopAction();
```

#### 4.3.2 查询类（需 `kConnected`）

| 方法 | 出参 |
|---|---|
| `bool queryMotionState(std::string& out, uint32_t timeout = 5000)` | 当前运控实际生效的动作 + 控制速度 JSON，schema 见下 |
| `bool getMotionCapabilities(std::string& out, uint32_t timeout = 5000)` | 支持的高级动作集合（含按键组合 + 可调参数）JSON，schema 见下 |
| `bool getMotorLayout(MotorLayout& layout, uint32_t timeout = 5000)` | 电机硬件布局（电机数 + 每电机 `limbNo`/`jointNo`/`name`）；`kConnected` 后即可调，SDK 内部缓存 |

##### `queryMotionState` 出参示例

```json
// 有活动动作
{
  "action":        "walking",
  "velocity":       0.0,
  "lineVelocityX":  0.5,
  "lineVelocityY":  0.0
}

// 无活动动作（已 stopAction / 还没 startAction）
{}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `action`        | string | 当前生效的动作名（运控环最近一拍计算结果）|
| `velocity`      | float  | 当前角速度（rad/s） |
| `lineVelocityX` | float  | 当前前后线速度（m/s） |
| `lineVelocityY` | float  | 当前横移线速度（m/s） |

> 返回值与 `out` 是两层独立语义：
> - `return false` → **RPC 层失败**（未 connect / RPC 超时 / 通道不可用），通过 `getLastError()` 取错误码
> - `return true` → RPC 成功；若**无活动动作**，`out` 是空对象 `{}`（调用方据此判断"当前无可查询动作"，不要假设字段一定存在）

##### `getMotionCapabilities` 出参示例

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

| 字段 | 类型 | 说明 |
|---|---|---|
| `actions[].name`    | string         | 动作名，传给 `startAction` 的 `action` 参数 |
| `actions[].mapping.require` | array<string\> | 触发该动作必须按下的 `ButtonDefine` 名称 |
| `actions[].mapping.axisRequire` | array<object\> | 额外轴值条件；每项含 `axis`、`min`、`max`，`axis` 为 `AxesDefine` 名称 |
| `actions[].mapping.priority` | integer | 同一帧多个动作命中时的优先级，数值越大优先级越高 |
| `actions[].mapping.exact` | bool | `true` 表示除 `require` 外不能有其它按钮同时按下 |
| `actions[].mapping.minHoldTime` | number | 最小按住时间（ms）；当前 `waveHand` / `heartSit` / `tweak` 为 `1000`，其余 posture 动作为 `0` |
| `actions[].params`  | array<object\> | 该动作可调的运行期参数（一次性动作没有此字段）|
| `params[].name`     | string         | 参数字段名，用作 `startAction` / `setActionParams` 里 `params` JSON 的 key |
| `params[].min/max`  | float          | 取值范围；超出会被服务端 clamp |
| `params[].unit`     | string         | 单位（如 `"m/s"` / `"rad/s"`）；服务端未配置该字段时不输出 |

### 4.4 音频播放器

音频播放接口直接挂在主客户端上：

```cpp
client->startAudioPlay(R"({"list":[{"id":"1"}],"volume":50,"repeat":1})");
```

#### 4.4.1 控制类（需 `kControlled`）

| 方法 | 参数 | 备注 |
|---|---|---|
| `bool startAudioPlay(const std::string& paramsJson, uint32_t timeout = 5000)` | 见下表 | 复用 RPC，按字段决定语义 |
| `bool stopAudioPlay(uint32_t timeout = 5000)` | — | 空参即停止 |
| `bool pauseAudioPlay(uint32_t timeout = 5000)` | 内部传 `{"pause":true}` | 恢复用 `startAudioPlay` 的 resume 形态 |
| `bool addAudioFile(const std::string& paramsJson, uint32_t timeout = 30000)` | `{"id":"custom_1","name":"hello.mp3","file":"/data/hello.mp3"}` 或 URL 形态 | 新增自定义音频文件 |
| `bool deleteAudioFile(const std::string& paramsJson, uint32_t timeout = 5000)` | `{"id":"1"}` | id 为待删音频 ID |

**`startAudioPlay.paramsJson` 形态**

| 场景 | paramsJson |
|---|---|
| 启动播放列表 | `{"list":[{"id":"1"},{"id":"2"}],"volume":50,"repeat":1}` |
| 调音量 | `{"volume":50}` |
| 恢复播放 | `{"resume":true}` |
| 修改重复次数 | `{"repeat":-1}` (`-1`=无限循环；`>0`=次数；`0` 无意义) |

#### 4.4.2 查询类（需 `kConnected`）

| 方法 | 入参 paramsJson | 出参 out（UTF-8 JSON） |
|---|---|---|
| `bool queryAudioPlayDetail(std::string& out, uint32_t timeout = 5000)` | — | 见 4.4.2.1 |
| `bool queryAudioPlayList(std::string& out, const std::string& paramsJson = "", uint32_t timeout = 5000)` | `{"type":"customVoice"}` | 见 4.4.2.2 |

##### 4.4.2.1 `queryAudioPlayDetail` 出参字段

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

| 字段 | 类型 | 说明 |
|---|---|---|
| `channel` | int | 播放通道，含义由设备侧定义 |
| `playing` | bool | 是否处于播放中 |
| `paused` | bool | 是否处于暂停态 |
| `repeat` | int | 重复配置：`-1`=无限循环；`>0`=循环次数；`0` 无意义 |
| `index` | int | 当前播放下标，从 0 开始 |
| `count` | int | 当前播放列表总数 |
| `volume` | int | 当前音量，范围 0~100 |
| `currentId` | string | 当前播放音频 ID |
| `list` | array<string\> | 当前播放列表，元素为音频 ID |

##### 4.4.2.2 `queryAudioPlayList` 出参字段

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

| 字段 | 类型 | 说明 |
|---|---|---|
| `customVoice` | array<object\> | 音频文件数组，每项见下表 |
| `customVoice[].id` | string | 音频 ID |
| `customVoice[].name` | string | 音频名称 |
| `customVoice[].duration` | int | 时长（秒） |
| `customVoice[].size` | int | 文件大小（字节） |
| `customVoice[].createAt` | int64 | 创建时间戳（毫秒） |
| `customVoice[].describe` | string | 备注 |
| `remaining` | int | 剩余可上传数量/容量配额，精确语义由设备侧定义 |

#### 4.4.3 播放状态实时上报（通过 `EventCallback`）

| topic | payload 编码 |
|---|---|
| `statistics/play_list` | UTF-8 JSON 文本 |

**payload 示例**：

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

**字段**：同 4.4.2.1 `queryAudioPlayDetail` 出参；多一个 `event` 字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `event` | string | 事件名，具体枚举值由设备侧定义（如 `"changed"`） |

#### 4.4.4 音频原始帧订阅

音频原始帧已统一到 `IMediaBusClient`（见 §4.6），仅 `aarch64` 板内本地部署可订阅。通过 `client->createMediaBusClient()` 拿到通道后 `startRawAudioFrame(channel, cb)` 订阅，帧类型为 MediaBus 的 `AudioFrame`：

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

    // PCM 数据：frame.data(), frame.size()
});

// 退出或不再需要时停止订阅
media->stopRawAudioFrame(0);
```

`AudioFrame` 继承自 `Uface::Media::MediaBuffer`：

| 字段 / 方法 | 说明 |
|---|---|
| `frame.data()` / `frame.size()` | 音频原始数据指针和字节数，通常为 PCM |
| `frame.getFd()` | 若底层使用共享内存 / DMA，可返回关联 fd；无 fd 时由平台决定 |
| `frame.getFrameInfo()` | 返回 `AudioFrameInfo` |
| `AudioFrameInfo.sampleRate` | 采样率，如 8000 / 16000 |
| `AudioFrameInfo.sampleFormat` | 采样位宽，如 8 / 16 |
| `AudioFrameInfo.channelCount` | 声道数，常见 1 / 2 |
| `AudioFrameInfo.dataType` | 数据类型，0 表示 PCM，1 表示 WAV |
| `AudioFrameInfo.timestamp` / `sequence` | 时间戳与帧序号 |

> `AudioFrame` 的数据生命周期由 SDK / MediaBus 管理。回调返回后如果业务线程还要使用数据，应自行拷贝 `frame.data()` 对应的 `frame.size()` 字节，或确认持有对象的生命周期满足使用要求。

### 4.5 系统与设备

| 方法 | 状态 | 说明 |
|---|---|---|
| `bool querySystemStatus(std::string& out, uint32_t timeout = 5000)` | `kConnected` | 出参 JSON，含 `battery` + `network` 两个子对象，见 4.5.1 |
| `bool setObservedEnable(const std::string& json, std::string& ret, uint32_t timeout = 5000)` | `kConnected` | 开/停观测量上报（运控观测 + GPS），出参 `ret` 回带实际生效开关，见 §4.7 |

摄像头前灯亮度直接挂在主客户端上：

```cpp
client->setCameraLightBrightness(50);
```

| 方法 | 状态 | 说明 |
|---|---|---|
| `bool getCameraLightBrightness(std::string& out, uint32_t timeout = 5000)` | `kControlled` | 查询摄像头前灯亮度，出参 `out` 为 JSON 字符串 |
| `bool setCameraLightBrightness(int32_t brightness, uint32_t timeout = 5000)` | `kControlled` | 控制摄像头前灯亮度，`brightness` 取值 0~100（**`brightness` 仍是 int32**）|

#### 4.5.1 `querySystemStatus` 出参字段

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

**`battery` 字段说明**：

| 字段 | 类型 | 单位 | 含义 |
|---|---|---|---|
| `abnormalStatus` | uint8 | — | 功率电路是否异常，非 0 表示异常 |
| `statusCode` | uint16 | — | BMS 状态码，位掩码组合（见下表） |
| `cycleCount` | uint16 | 次 | 电池累计充放电循环次数 |
| `remainChargeTime` | uint16 | 分钟 | 剩余充电时间（充电中有效） |
| `remainDischargeTime` | uint16 | 分钟 | 剩余放电时间（按当前负载估算） |
| `power` | float | % | 当前电池电量百分比，范围 0~100 |
| `health` | float | % | 电池健康度百分比，范围 0~100 |
| `temperature` | float | °C | 电池温度，有符号浮点 |
| `fullCharge` | float | mAh | 满充容量 |
| `remaining` | float | mAh | 剩余容量 |
| `current` | float | A | 当前充放电电流（正充电、负放电） |
| `voltage` | float | V | 当前总电压 |

**`battery.statusCode` 位掩码**（`statusCode & bit != 0` 表示对应保护位有效）：

| 位 | 值 | 含义 |
|---|---|---|
| bit0 | 0x0001 | pack 欠压保护 |
| bit1 | 0x0002 | cell 欠压保护 |
| bit2 | 0x0004 | pack 过压保护 |
| bit3 | 0x0008 | cell 过压保护 |
| bit4 | 0x0010 | 充电结束 |
| bit5 | 0x0020 | 放电过流保护 |
| bit6 | 0x0040 | 充电过流保护 |
| bit7 | 0x0080 | 短路保护 |
| bit8 | 0x0100 | 放电低温保护 |
| bit9 | 0x0200 | 充电低温保护 |
| bit10 | 0x0400 | 放电高温保护 |
| bit11 | 0x0800 | 充电高温保护 |
| bit12 | 0x1000 | MOS 高温保护 |
| bit13 | 0x2000 | Cell 采集断线保护 |
| bit14 | 0x4000 | Cell 电压失衡保护 |
| bit15 | 0x8000 | Cell 电压失效保护 |

**`network.<iface>.status` 枚举值**：

| 值 | 含义 |
|---|---|
| `0` | 已连接 (connected) |
| `1` | 未连接 (disconnected) |
| `2` | 连接中 (connecting) |

**`network.mobile.signalLevel` 枚举值**（仅 `mobile` 子对象有此字段）：

| 值 | 含义 |
|---|---|
| `0` | 信号好（> 22dB） |
| `2` | 信号中等（> 15dB） |
| `3` | 信号差（≤ 15dB） |

`network.mobile.simCardSta`：`true` 表示 SIM 卡已就绪，`false` 表示未插入 / 未识别。

#### 4.5.2 系统状态实时上报（通过 `EventCallback`）

| topic | payload 编码 | 触发 |
|---|---|---|
| `statistics/device_status` | UTF-8 JSON 文本 | 按需，仅推变化字段 |

**payload 示例**（仅 `network.ether.ipv4Addr` 变化时）：

```json
{
  "network": {
    "ether": { "enable": true, "ipv4Addr": "192.0.2.10", "ipv4Gateway": "192.0.2.1", "ipv4Mask": "255.255.255.0", "mac": "02:00:00:00:00:01", "status": 0 }
  }
}
```

**字段**：与 4.5.1 `querySystemStatus` 出参同结构；服务端**只下推有变化的字段**，未变化字段不出现（不是 `null`）。调用方需做局部 merge / patch。

### 4.6 音视频通道（`IMediaBusClient`）

音视频帧（视频原始帧 / 视频编码帧 / 音频原始帧）统一通过 `IMediaBusClient` 订阅。该能力仅支持 `aarch64` 板内本地部署；`x86_64` / `i386` 平台不要调用 `createMediaBusClient()`、`setup()` 或 `start*Frame()`。由 `client->createMediaBusClient()` 工厂分配，`setup()` 后即可订阅；**媒体订阅与控制权无关**，不需要 `startControl`。

```cpp
auto media = client->createMediaBusClient();
media->setup();

// 查询音视频硬件布局（mic / camera / 编码器数量）
MediaLayout layout = {};
media->getMediaLayout(layout);

// 原始帧：VideoFrame
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

// 编码帧：EncodedVideoFrame
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

| 方法 | 说明 |
|---|---|
| `bool setup()` | 初始化媒体总线连接（订阅前必须先调用）|
| `void shutdown()` | 断开媒体总线连接，停止所有订阅 |
| `int32_t getLastError() const` | 最后一次失败原因（`MediaBusError`）|
| `bool getMediaLayout(MediaLayout& layout)` | 查询音视频硬件布局（`micNum` / `cameraNum` / `videoEncoderNum`）|
| `bool startRawVideoFrame(int32_t channel, RawVideoFrameCallback cb)` | 订阅视频原始帧；`cb` 为空返回 `false`，签名 `(int32_t channel, const VideoFrame&)` |
| `void stopRawVideoFrame(int32_t channel)` | 停止订阅视频原始帧 |
| `bool startEncodedVideoFrame(int32_t channel, EncodedVideoFrameCallback cb)` | 订阅视频编码帧；签名 `(int32_t channel, const EncodedVideoFrame&)`（**无 stream 参数**）|
| `void stopEncodedVideoFrame(int32_t channel)` | 停止订阅视频编码帧 |
| `bool startRawAudioFrame(int32_t channel, RawAudioFrameCallback cb)` | 订阅音频原始帧；签名 `(int32_t channel, const AudioFrame&)` |
| `void stopRawAudioFrame(int32_t channel)` | 停止订阅音频原始帧 |

`MediaBusError`（`getLastError` 返回值）：

| 值 | 含义 |
|---|---|
| `kNone` | 无错 |
| `kNotSetup` | 未启动（未 `setup` 即调用订阅 / 查询接口）|
| `kConfigLoadFailed` | 加载媒体配置失败 |
| `kConfigInvalid` | 媒体配置缺少 `streamDefine` 等必填项 |
| `kMediaInitFailed` | 初始化媒体流服务失败 |
| `kMediaStartFailed` | 启动媒体流服务失败 |
| `kInvalidChannel` | 通道号非法（< 0 或 ≥ 对应硬件数量）|
| `kInvalidCallback` | 帧回调为空 |
| `kSourceUnavailable` | 编码源不可用（创建失败 / 无视频轨）|
| `kSourceStartFailed` | 编码源启动失败 |

**`VideoFrame` 原始帧格式**

> **重要：视频帧数据必须按照 plane 和 stride 访问。** `width` / `height` 表示有效图像尺寸，`stride[plane]` 表示该平面每行实际跨距，通常大于等于有效行字节数；多平面格式还应使用对应 `virAddr[plane]`。不能假设 `frame.data()` 是完整连续图像，也不能按 `width * height` 一次性读完整帧。

`VideoFrame` 继承自 `Uface::Media::MediaBuffer`：

| 字段 / 方法 | 说明 |
|---|---|
| `frame.data()` / `frame.size()` | 数据指针和字节数；部分平台可能只保证第 0 平面连续 |
| `frame.getFd()` | 若底层使用共享内存 / DMA，可返回关联 fd；无 fd 时由平台决定 |
| `frame.getFrameInfo()` | 返回 `VideoFrameInfo` |
| `VideoFrameInfo.width` / `height` | 图像有效宽高 |
| `VideoFrameInfo.pixelFormat` | 像素格式，见 `Uface::Media::MediaPixelFormat` |
| `VideoFrameInfo.stride[3]` | 各平面水平跨距 / 每行实际跨度，单位字节 |
| `VideoFrameInfo.virAddr[3]` | 各平面虚拟地址；多平面格式应优先按平面地址 + stride 读取 |
| `VideoFrameInfo.timestamp` / `sequence` | 时间戳与帧序号 |

访问方式示意：

```cpp
const auto& info = frame.getFrameInfo();
const uint8_t* y = info.virAddr[0] ? info.virAddr[0] : frame.data();
for (uint32_t row = 0; row < info.height; ++row) {
    const uint8_t* line = y + static_cast<size_t>(row) * info.stride[0];
    // 只处理有效宽度 info.width；不要把 stride padding 当作图像数据
    processLine(line, info.width);
}
```

NVIDIA 平台的视频原始帧可能是多平面且内存不连续，保存 / 处理时务必按 `VideoFrameInfo.virAddr[plane]` 与 `stride[plane]` 逐平面逐行读取有效数据。完整处理逻辑见 `examples/example_media_frames.cpp`。

**`EncodedVideoFrame` 编码帧格式**

视频编码帧使用 `EncodedVideoFrame`，该类型是 `Uface::Stream::CMediaFrame` 的 SDK 公开别名，不再额外封装 `VideoPacket`：

| 字段 / 方法 | 说明 |
|---|---|
| `frame.getBuffer()` / `frame.size()` | 编码数据指针和字节数 |
| `frame.getFrameType()` | 帧类型，常见 `videoIFrame` / `videoPFrame` / `videoBFrame` / `imageFrame` |
| `frame.getPts()` / `frame.getUtc()` / `frame.getSequence()` | PTS / UTC / 编码帧序号 |
| `frame.getExtraData()` | `Uface::Stream::FrameInfo` 扩展头 |
| `FrameInfo.detail.video.encode` | 编码类型，见 `Uface::Media::VideoEncode`，如 H264 / H265 / MJPEG / JPEG |
| `FrameInfo.detail.video.width` / `height` | 编码图像宽高 |
| `FrameInfo.detail.video.fpsNum` / `fpsDen` | 帧率分子 / 分母 |

完整 C++ 测试程序：`examples/example_media_frames.cpp`。该示例同时订阅音频原始帧、视频原始帧、视频编码帧，并将前三类各 10 帧保存到 `/tmp/media_frame_dump`。

### 4.7 观测量数据面

高级客户端可开启观测量上报，把运控观测（IMU + 电机 + 电源）与 GPS 帧通过回调推给调用方。整体流程：

1. `connect` 之前/之后注册回调：`setMotionObservedCallback` / `setGPSCallback`；
2. 调 `setObservedEnable(json, ret)` 传 JSON 开关开启服务端推送；`ret` 回带当前实际生效的开关状态；
3. 服务端按帧推送，运控观测经 `MotionObservedCallback(LowLevelMotionObserved)`、GPS 经 `GPSCallback(GPSFrame)` 上抛；
4. 另有 `getPowerInfo` 直接取最近一帧电源观测（按新鲜度窗口）。

| 方法 | 状态 | 说明 |
|---|---|---|
| `bool setObservedEnable(const std::string& json, std::string& ret, uint32_t timeout = 5000)` | `kConnected` | 观测量上报开关，`json` 为开关字段（如 `{"motionEnable":true,"sensorEnable":true}`）；出参 `ret` 回带当前实际生效的开关 JSON。服务端 hook 不做鉴权 |
| `void setMotionObservedCallback(MotionObservedCallback cb)` | 任意 | 注册运控观测量回调，签名 `void(const LowLevelMotionObserved&)`（含 power）|
| `void setGPSCallback(GPSCallback cb)` | 任意 | 注册 GPS 数据回调，签名 `void(const GPSFrame&)` |
| `bool getPowerInfo(PowerObserved* power, uint32_t timeout)` | `kConnected` | 取最近一帧电源观测；**需先 `setObservedEnable({"motionEnable":true})` 开启运控观测**（电源量随运控观测帧上报），否则窗口内无数据恒返 `false`。`timeout` 是**新鲜度窗口（微秒，us）**：仅当最近 `timeout` us 内有观测数据才返回 `true`，否则返回 `false`（`getLastError()` → `kDataNotUpdate`）|

`setObservedEnable` 入参 JSON 开关字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| `motionEnable` | bool | 开启后推送运控观测（IMU + 电机 + 电源），经 `setMotionObservedCallback` 回调上抛 |
| `sensorEnable` | bool | 开启后推送传感器观测（GPS），经 `setGPSCallback` 回调上抛 |

**观测量数据类型**（字段以 `MotionSdkProtocol.h` 为准）：

- `LowLevelMotionObserved`：`systemSta` / `motorNum` / `imu`（`IMUObserved`）/ `trc`（`TRCStickFrame`）/ `power`（`PowerObserved`）/ `motors[]`（`MotorObserved`）。各子结构字段语义参见低级 SDK 手册。
- `GPSFrame`：`valid`（1=有效）/ `speed`（km/h）/ `level`（信号等级，见 `GPSSignalLevel`）/ `rssi`（信号强度原始值，单位 dbm）/ `point`（`GEOGPoint`，含 `lat` / `lng`，单位 deg）。
- `PowerObserved`：`power`（电量 %）/ `health`（健康度 %）/ `temper`（电池温度 ℃）/ `chargeCurrent`（实时电流 A）/ `chargeVoltage`（当前总电压 V）。

```cpp
client->setMotionObservedCallback([](const LowLevelMotionObserved& obs) {
    // ✓ 轻量记录 / 投递业务线程；回调内严禁阻塞
});
client->setGPSCallback([](const GPSFrame& gps) {
    // ✓ 轻量记录
});
std::string observedState;
client->setObservedEnable(R"({"motionEnable":true,"sensorEnable":true})", observedState);
// observedState 回带当前实际生效的开关，如 {"motionEnable":true,"sensorEnable":true}

PowerObserved power = {};
if (client->getPowerInfo(&power, /*timeout_us=*/200000)) {
    printf("battery=%.1f%% voltage=%.2fV\n", power.power, power.chargeVoltage);
}
```

---

## 五、C++ 使用示例

完整可运行示例：`examples/example_highlevel.cpp`（同目录有对应 `CMakeLists.txt`）

```cpp
#include <chrono>
#include <thread>
#include <cstdio>
#include <string>
#include "MotionSdkService.h"
#include "MotionHighLevelClient.h"

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
    svc->setNetworkInterface(argc > 1 ? argv[1] : "eth0");   // 远端/多设备指定网卡；板内忽略

    if (!svc->initialService(nullptr, "myAppHighLevel")) return 1;

    std::string deviceId;
    if (svc->isMultiDevice()) {
        fprintf(stderr, "multi-device mode: use discoverDevices() first to obtain a SN\n");
        svc->shutdown();
        return 1;
    }
    auto client = IMotionHighLevelClient::create(deviceId);
    client->setConnectCallback(&onConnect);
    client->setEventCallback(&onEvent);

    if (!client->connect()) {                          // SDK 默认 60s lease
        IMotionSdkService::instance()->shutdown();
        return 1;
    }

    // 不持权可调的查询
    std::string caps, sysStatus;
    client->getMotionCapabilities(caps);
    client->querySystemStatus(sysStatus);

    // 取控制权
    if (!client->startControl(30000)) {
        client->disconnect();
        IMotionSdkService::instance()->shutdown();
        return 1;
    }
    const auto controlDeadline = std::chrono::steady_clock::now() + std::chrono::seconds(30);
    while (client->getState() != IMotionHighLevelClient::kControlled) {
        if (std::chrono::steady_clock::now() >= controlDeadline) {
            client->disconnect();
            IMotionSdkService::instance()->shutdown();
            return 1;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }

    // 安全动作 + 音频 + 数据上报
    client->standUp();
    std::this_thread::sleep_for(std::chrono::seconds(5));
    client->lieDown();
    std::this_thread::sleep_for(std::chrono::seconds(5));

    client->startAudioPlay(R"({"list":[{"id":"1"}],"volume":50,"repeat":1})");
    std::this_thread::sleep_for(std::chrono::seconds(5));
    client->pauseAudioPlay();
    client->stopAudioPlay();

    std::string observedState;
    client->setObservedEnable(R"({"motionEnable":true,"sensorEnable":true})", observedState);
    std::this_thread::sleep_for(std::chrono::seconds(5));
    client->setObservedEnable(R"({"motionEnable":false,"sensorEnable":false})", observedState);

    // 退出 —— 显式 release + disconnect + shutdown
    client->releaseControl();
    client->disconnect();
    IMotionSdkService::instance()->shutdown();
    return 0;
}
```

### 5.2 媒体帧订阅示例

完整可运行示例：`examples/example_media_frames.cpp`，仅 `aarch64` 板内本地部署构建和运行。

```bash
# config 省略或传 "-" 时使用 SDK 内置 MediaBus 配置
./example_media_frames [config|-] [client_id] [device_id|-] [video_channel] [audio_channel] [seconds] [network_iface|-]

# 常用：订阅 video_channel=0、audio_channel=0，运行 10 秒
./example_media_frames - mediaFrameExample - 0 0 10 eth0
```

输出内容：

- 通过 `client->createMediaBusClient()` 创建通道并 `setup()`
- 订阅 `VideoFrame` 原始视频帧（`startRawVideoFrame`）
- 订阅 `EncodedVideoFrame` 视频编码帧（`startEncodedVideoFrame`，回调签名 `(channel, frame)`）
- 订阅 `AudioFrame` 音频原始帧（`startRawAudioFrame`）
- 默认保存前三类各 10 帧到 `/tmp/media_frame_dump`
- raw video 保存逻辑按 `virAddr[] + stride[]` 逐平面逐行写入，兼容 NVIDIA 非连续内存

### 5.3 多设备示例（远端模式）

跟 §五.1（单设备）不同的两个点：用 `discoverDevices` 收集网上的 SN，用具体 SN 创建 client。

```cpp
#include <chrono>
#include <mutex>
#include <thread>
#include <vector>
#include <cstdio>
#include "MotionSdkService.h"
#include "MotionHighLevelClient.h"

using namespace uniubi::RobotSdk;

int main(int argc, char** argv) {
    auto svc = IMotionSdkService::instance();
    svc->setNetworkInterface(argc > 1 ? argv[1] : "eth0");

    /// 1) 收集发现到的 SN（回调里只做轻量记录，不能阻塞）
    std::mutex devMutex;
    std::vector<std::string> devices;
    svc->setDiscoverCallback([&](const std::string& sn, const std::string& info) {
        std::lock_guard<std::mutex> lk(devMutex);
        if (std::find(devices.begin(), devices.end(), sn) == devices.end()) {
            printf("[discover] sn=%s info=%s\n", sn.c_str(), info.c_str());
            devices.push_back(sn);
        }
    });

    if (!svc->initialService(nullptr, "myMultiApp")) return 1;

    if (!svc->isMultiDevice()) {
        fprintf(stderr, "current deployment is single-device, use §5.1 instead\n");
        svc->shutdown();
        return 1;
    }

    /// 2) 发起一次发现，2s 内收集所有响应
    svc->discoverDevices(2000);
    std::this_thread::sleep_for(std::chrono::milliseconds(2100));

    std::vector<std::string> snapshot;
    { std::lock_guard<std::mutex> lk(devMutex); snapshot = devices; }
    if (snapshot.empty()) {
        fprintf(stderr, "no device discovered, check network interface / robot status\n");
        svc->shutdown();
        return 1;
    }
    printf("found %zu device(s)\n", snapshot.size());

    /// 3) 对每台机器人各开一个 HL client，并发执行
    std::vector<std::shared_ptr<IMotionHighLevelClient>> clients;
    for (const auto& sn : snapshot) {
        auto c = IMotionHighLevelClient::create(sn);
        if (!c) { fprintf(stderr, "create(%s) failed\n", sn.c_str()); continue; }
        if (!c->connect()) { fprintf(stderr, "connect(%s) failed\n", sn.c_str()); continue; }
        clients.push_back(c);
    }

    /// 4) 各自独立操作（每个 client 内部 deviceId 已绑定，互不串扰）
    for (auto& c : clients) {
        if (!c->startControl(30000)) {
            fprintf(stderr, "startControl failed\n");
        }
    }
    for (auto& c : clients) {
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(30);
        while (c->getState() != IMotionHighLevelClient::kControlled &&
               std::chrono::steady_clock::now() < deadline) {
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
        if (c->getState() != IMotionHighLevelClient::kControlled) {
            fprintf(stderr, "wait kControlled timeout\n");
            continue;
        }
        c->standUp();
    }

    std::this_thread::sleep_for(std::chrono::seconds(5));

    /// 5) 退出 —— 各 client 各自 release + disconnect
    for (auto& c : clients) {
        c->lieDown();
    }
    std::this_thread::sleep_for(std::chrono::seconds(5));

    for (auto& c : clients) {
        c->releaseControl();
        c->disconnect();
    }
    svc->shutdown();
    return 0;
}
```

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
| `setNetworkInterface` | `sdk.service.set_network_interface(iface: str)` —— 远端/多设备指定网卡，板内忽略 |
| `setDiscoverCallback` | `sdk.service.set_discover_callback(cb)`；签名 `(sn: str, info_json: str) -> None` |
| `isMultiDevice` | `sdk.service.is_multi_device() -> bool` |
| `discoverDevices` | `sdk.service.discover_devices(timeout_ms=10000) -> bool`（非阻塞） |
| `initialService` | `sdk.service.initial(file_or_none, server_name, timeout=30)` |
| `shutdown` | `sdk.service.shutdown()` |

**HighLevel client（`sdk.MotionHighLevelClient` —— 对应 `IMotionHighLevelClient`）：**

| C++ 接口 | Python wrapper |
|---|---|
| `create(asMaster=false)` / `create(deviceId)` | `MotionHighLevelClient(device_id="", as_master=False)` 构造；板内空串（按 `as_master` 协商主从）、远端必传 SN |
| `connect / disconnect` | `connect(lease_ms=0)` / `disconnect()` |
| `startControl / releaseControl` | `start_control(timeout_ms=10000)` / `release_control()` |
| `getState / getLastError` | `get_state()` / `get_last_error()`（返回 enum） |
| `emergencyStop / recoveryStand` | `emergency_stop(timeout_ms=5000)` / `recovery_stand(timeout_ms=5000)` |
| `damp / standUp / lieDown / move` | `damp()` / `stand_up()` / `lie_down()` / `move(vx, vy, vyaw, timeout_ms=5000)` |
| `startAction / stopAction / setActionParams` | `start_action(action, params=None, ...)` / `stop_action()` / `set_action_params(params=None)`；`params` 接 Python dict，binding 内部转 JSON |
| `setRawControlCmd` | `set_raw_control_cmd(frame)`；`frame` 是 `sdk.TRCStickFrame()`，可读写 `valid / control_id / buttons / axes`（list ↔ array 自动互转） |
| `queryMotionState / getMotionCapabilities / querySystemStatus` | `query_motion_state()` / `get_motion_capabilities()` / `query_system_status()`；返回 Python dict（自动 json.loads） |
| `getMotorLayout` | `get_motor_layout(timeout_ms=5000)`；返回 `sdk.MotorLayout`，失败 `None` |
| `setObservedEnable` | `set_observed_enable(params=None, timeout_ms=5000)`；`params` 接 dict（如 `{"motionEnable":True,"sensorEnable":True}`），成功返回当前实际开关 dict、失败返回 `None` |
| `getPowerInfo` | `get_power_info(timeout_us=5000)`；`timeout_us` 是新鲜度窗口（微秒），返回 `sdk.PowerObserved` 或 `None` |
| `setMotionObservedCallback` | `set_motion_observed_callback(cb)`；签名 `(obs: sdk.LowLevelMotionObserved)` |
| `setGPSCallback` | `set_gps_callback(cb)`；签名 `(gps: sdk.GPSFrame)` |
| `getCameraLightBrightness / setCameraLightBrightness` | `get_camera_light_brightness()`（返回 dict / None）/ `set_camera_light_brightness(brightness)`；`brightness` 取值 0~100 |
| `startAudioPlay / stopAudioPlay / pauseAudioPlay` | `start_audio_play(params)` / `stop_audio_play()` / `pause_audio_play()` |
| `addAudioFile / deleteAudioFile / queryAudioPlayDetail / queryAudioPlayList` | `add_audio_file(params)` / `delete_audio_file(params)` / `query_audio_play_detail()` / `query_audio_play_list(params=None)` |
| `createMediaBusClient` | `create_media_bus_client()`；返回 `sdk.MediaBusClient`，仅 `aarch64` 板内本地媒体帧订阅使用；Python 需先确认 `sdk.MEDIA_ENABLED == True`（见下表）|
| `setConnectCallback` | `set_connect_callback(cb)` 或装饰器 `@client.on_connect`；签名 `(state, error)` |
| `setEventCallback` | `set_event_callback(cb)` 或装饰器 `@client.on_event`；签名 `(topic: str, payload_json: str)` |

**MediaBus client（`sdk.MediaBusClient` —— 对应 `IMediaBusClient`，由 `create_media_bus_client()` 工厂分配；仅 `aarch64` 板内本地部署使用）：**

Python native binding 通过 `UNIUBI_SDK_ENABLE_MEDIA` 控制媒体帧绑定。默认 `aarch64=ON`、`x86_64/i386=OFF`。运行时用 `sdk.MEDIA_ENABLED` 判断；为 `False` 时 `create_media_bus_client()` 会抛出 `RuntimeError("MediaBus is not available in this SDK build")`，且不会提供 `VideoFrame` / `AudioFrame` / `EncodedVideoFrame` 等媒体类型。

| C++ 接口 | Python wrapper |
|---|---|
| `setup / shutdown` | `setup()` / `shutdown()` |
| `getMediaLayout` | `get_media_layout()`；返回 `sdk.MediaLayout` 或 `None` |
| `startRawVideoFrame / stopRawVideoFrame` | `start_raw_video_frame(channel, callback)` / `stop_raw_video_frame(channel)`；回调签名 `(channel: int, frame: sdk.VideoFrame)` |
| `startRawAudioFrame / stopRawAudioFrame` | `start_raw_audio_frame(channel, callback)` / `stop_raw_audio_frame(channel)`；回调签名 `(channel: int, frame: sdk.AudioFrame)` |
| `startEncodedVideoFrame / stopEncodedVideoFrame` | `start_encoded_video_frame(channel, callback)` / `stop_encoded_video_frame(channel)`；回调签名 `(channel: int, frame: sdk.EncodedVideoFrame)` |

**媒体帧类型**

| Python 类型 | 对应 C++ 类型 | 常用字段 / 方法 |
|---|---|---|
| `sdk.AudioFrame` | `Uface::Media::AudioFrame` | `frame.data()`、`frame.size()`、`frame.get_fd()`、`frame.frame_info.sample_rate/sample_format/channel_count/timestamp/sequence` |
| `sdk.VideoFrame` | `Uface::Media::VideoFrame` | `frame.data()`、`frame.size()`、`frame.get_fd()`、`frame.frame_info.width/height/pixel_format/stride/timestamp/sequence`、`frame.plane_view(plane)` |
| `sdk.EncodedVideoFrame` | `Uface::Stream::CMediaFrame` | `frame.data()`、`frame.size()`、`frame.frame_type`、`frame.pts`、`frame.utc`、`frame.sequence`、`frame.frame_info`、`frame.video_info` |
| `sdk.VideoFramePlaneView` | 视频平面只读视图 | `rows`、`row_bytes`、`row_view(row)`，用于按行读取非连续 / 带 stride 的原始视频 |

Python API 不暴露 MediaBus Python 包，帧格式由 Motion SDK 自身封装；编码帧使用 `EncodedVideoFrame`，没有 `VideoPacket` Python 公共类型。`sdk.CMediaFrame` 保留为底层兼容别名。

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
    client = sdk.MotionHighLevelClient()
    client.connect()
    ...
    # 函数结束，client 进入 GC —— 死锁风险

# ✓ 正确：try/finally 显式释放
def main():
    client = sdk.MotionHighLevelClient()
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

完整可运行示例：`uniubi_robot_sdk_py/examples/example_highlevel.py`

### 6.3 Python 使用示例

完整可运行版本：`uniubi_robot_sdk_py/examples/example_highlevel.py`

```python
import json, signal, sys, time
import robot_motion_sdk as sdk

_stop = False
def _on_signal(signum, frame):
    global _stop
    _stop = True

signal.signal(signal.SIGINT, _on_signal)
signal.signal(signal.SIGTERM, _on_signal)

def main():
    iface = sys.argv[1] if len(sys.argv) > 1 else "eth0"
    sdk.service.set_network_interface(iface)

    if not sdk.service.initial(None, "myAppHighLevel"):
        return 1

    if sdk.service.is_multi_device():
        print("multi-device mode: use discover_devices() first to obtain a SN")
        sdk.service.shutdown()
        return 1
    client = sdk.MotionHighLevelClient()
    try:
        @client.on_connect
        def _on_connect(state, err):
            if state == sdk.HighLevelState.kControlled:
                print("[high] control acquired")
            elif state == sdk.HighLevelState.kConnected:
                if err == sdk.HighLevelError.kSessionExpired:   print("[high] lease expired")
                elif err == sdk.HighLevelError.kSessionRevoked: print("[high] preempted")
                else:                                            print("[high] released")

        @client.on_event
        def _on_event(topic, payload_json):
            info = json.loads(payload_json) if payload_json else {}
            if topic == "statistics/play_list":
                print(f"[evt] play: {info}")
            elif topic == "statistics/device_status":
                print(f"[evt] dev:  {info}")

        if not client.connect(lease_ms=60000):
            return 1

        if not client.start_control(timeout_ms=30000):
            return 1

        deadline = time.monotonic() + 30.0
        while client.get_state() != sdk.HighLevelState.kControlled:
            if _stop or time.monotonic() > deadline:
                return 1
            time.sleep(0.05)

        client.stand_up()
        for _ in range(50):
            if _stop: break
            time.sleep(0.1)
        client.lie_down()
        for _ in range(50):
            if _stop: break
            time.sleep(0.1)

        client.start_audio_play({"list": [{"id": "1"}], "volume": 50, "repeat": 1})
        time.sleep(5)
        client.pause_audio_play()
        client.stop_audio_play()

        client.release_control()
    finally:
        client.disconnect()
        sdk.service.shutdown()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

媒体帧订阅完整示例：`uniubi_robot_sdk_py/examples/example_media_frames.py`，仅 `aarch64` 板内本地部署运行。

```bash
git clone https://github.com/uniubi-ai/uniubi_robot_sdk_py.git ~/uniubi_robot_sdk_py
export PYTHONPATH=~/uniubi_robot_sdk_py:$PYTHONPATH
python3 ~/uniubi_robot_sdk_py/examples/example_media_frames.py \
    [config|-] [client_id] [device_id|-] [video_channel] [audio_channel] [seconds] [network_iface|-]
```

最小用法：

```python
import time
import robot_motion_sdk as sdk

if not sdk.MEDIA_ENABLED:
    raise RuntimeError("current wheel does not include MediaBus bindings")

sdk.service.set_network_interface("eth0")
sdk.service.initial(None, "mediaFramePythonExample")

client = sdk.MotionHighLevelClient()
media = client.create_media_bus_client()
try:
    media.setup()
    media.start_raw_video_frame(0, lambda ch, frame: print("raw", ch, frame.size()))
    media.start_encoded_video_frame(0, lambda ch, frame: print("encoded", ch, frame.size()))
    media.start_raw_audio_frame(0, lambda ch, frame: print("audio", ch, frame.size()))
    time.sleep(10)
finally:
    media.stop_encoded_video_frame(0)
    media.stop_raw_video_frame(0)
    media.stop_raw_audio_frame(0)
    media.shutdown()
    client.disconnect()
    sdk.service.shutdown()
```

> Python 中 `frame.data()` 返回 `bytes` 拷贝；处理 NVIDIA 原始视频帧时推荐使用 `frame.plane_view(plane).row_view(row)` 按行读取，示例程序已实现保存逻辑。

---

## 七、注意事项

1. **回调注册时机**：`setConnectCallback` / `setEventCallback` 必须在 `connect()` 之前注册，连接之后注册的回调不会生效。
2. **回调线程**：`ConnectCallback` 与 `EventCallback` 均在 SDK 内部线程触发；回调里反调 SDK 接口要保证可重入。
3. **状态查询**：`getState()` / `getLastError()` 线程安全；`getLastError()` 读后清零。
4. **lease 默认值**：`connect(0)` → 使用默认 60s；服务端将值限制在 5s ~ 5min 内，最终生效值由服务端确定。
5. **持权判断**：动作类接口（`emergencyStop` / `startAction` / `stopAction` / 音频控制 / 摄像头灯）必须在 `kControlled` 状态下调，否则返 `false` + `kNotControlled`。
6. **暂不对外提供的接口**：高层 SDK 当前交付版不暴露运控主控查询/切换能力；该能力会在大小脑服务契约补齐后再开放。

---

## 八、调试与故障排查

### 8.1 机器人侧最小验证（先验）

调用 SDK 之前先把机器人侧的"对端"确认好，避免在客户端瞎找原因。

| 检查项 | 命令 / 方法 | 期望结果 |
|---|---|---|
| 网络可达 | `ping <机器人 IP>` | 有回包，延迟稳定 |
| 网卡多播能力 | `ip -d link show <iface>` | flag 含 `MULTICAST,UP` |
| DDS Discovery 流量 | `sudo tcpdump -i <iface> 'udp and (port 7400 or port 7401)'` | 客户端启动后能看到双向 SPDP 包 |
| 防火墙 | `sudo iptables -L` / `ufw status` | 无规则阻断 UDP 多播 / port 7400+ |

机器人侧（如可登录设备）：

```bash
# 1) 进程是否在跑
ps -ef | grep robotServer

# 2) DDS 发现端口监听
sudo ss -lup | grep -E '7400|7401'

# 3) 实时日志（路径以你们部署为准）
journalctl -u robotServer -f
```

### 8.2 SDK 端常见现象排查

| 现象 | 检查项 | 解决思路 |
|---|---|---|
| `initialService` 返回 false | 日志 `errorf` 输出 | 看错误码：`kRpcConnectFailed` → DDS 域起不来（网卡 / 多播 / domain id 不对） |
| `discoverDevices` 触发后回调一次没进 | 1. 是否 setNetworkInterface 选了能到机器人的网卡<br>2. `isMultiDevice()` 是否返 true<br>3. 机器人侧 `robotServer.discoverDevice.request` topic 是否被订阅 | 多设备模式必须正确指定网卡；若 isMultiDevice 返 false 说明 SDK 自检成板内模式，不该走 discover 流程 |
| `create(sn)` 返回 nullptr | SDK 自检成远端但 deviceId 传空 | 远端模式 deviceId 必须非空（板内才允许空） |
| `connect()` 之后 state 一直停在 `kDisconnected` | 1. 看 ConnectCallback 推过来的 error 码<br>2. `tcpdump` 是否双向有包<br>3. 机器人侧 `checkDeviceId` 配的 SN 与你传的是否一致 | `kRpcConnectFailed` → DDS 通道 / robotServer RPC 还没起；deviceId 不匹配 → 机器人 filter 静默丢弃所有请求 |
| `startControl` 后没切 `kControlled` | 1. ConnectCallback 是否报了 error<br>2. 是否被另一台 client 抢权 | `kRpcAcquireRejected` → 控制权被别人占 / acquireMode 超时；`kSessionRevoked` → 别人接管 |
| 动作类接口（`startAction` / `setActionParams` / `stopAction` / `setRawControlCmd`）返 false，state 显示 `kControlled` | `getLastError()` 取值 | `kSessionExpired` → lease 到期；`kSessionRevoked` → 被接管；`kActionRejected` → 服务端拒绝（按业务码处理）|
| **静默无响应**（任何接口都 timeout） | DDS QoS 不兼容（最常见） | 客户端 / 服务端 IDL 版本或 Cyclone DDS 版本不一致；用 `ddsperf sanity` 做最小握手验证 |

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
