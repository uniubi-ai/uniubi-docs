# Uniubi Robot Motion SDK 构建指南

本指南覆盖 C++ SDK、Python SDK、ROS 2 消息包和 ROS 2 示例包的分仓构建方式。C++ SDK 与 Python SDK 分别构建；`uniubi_robot_sdk` 不再把 Python binding 作为子目录一起编译。

相关文档：
- **高级接口手册**：[`uniubi_high_level_sdk.md`](uniubi_high_level_sdk.md) —— 高级控制接口（C++/Python）公开接口、枚举、回调、字段定义
- **低级接口手册**：[`uniubi_low_level_sdk.md`](uniubi_low_level_sdk.md) —— 低级控制接口（C++/Python）公开接口、枚举、回调、字段定义
- **媒体总线手册**：[`uniubi_media_sdk.md`](uniubi_media_sdk.md) —— 摄像头 / 麦克风帧订阅（音视频原始帧 + 编码帧）接口
- **DDS / ROS 2 直连接入手册**：[`uniubi_robot_dds_api.md`](uniubi_robot_dds_api.md) —— 不走 SDK，直接用 OMG DDS 或 ROS 2 对接设备的协议契约 + 工程模板
- **构建说明**：本文件

---

## 0. 前置依赖

| 依赖 | 要求 |
|---|---|
| 目标系统 | Linux (x86_64 / aarch64 / i386) |
| glibc | **≥ 2.34**（编译机 + 运行机） |
| 编译器 | g++ ≥ 9（支持 C++14） |
| CMake | ≥ 3.18 |
| Python 开发头 | Python 3.8+ + `python3-dev`（Python 绑定需要） |
| 运行时基础库 | 目标机预装（标准动态库搜索路径下可加载） |
| SDK 运行库 | `librobotMotionSdk.so`、`libmediaBus.so`、`libudbus.so`、`libubase.so` 按同版本、同架构成组提供；`MediaBusClient` 功能仅 `aarch64` 板内本地媒体帧订阅使用 |

---

## 1. SDK 仓库结构

### 1.1 `uniubi_robot_sdk`

```
uniubi_robot_sdk/
├── CMakeLists.txt                 C++ SDK examples 工程入口
├── cmake/
│   ├── UniubiRobotSdkConfig.cmake.in         CMake package 模板
│   └── toolchain-aarch64-linux-gnu.cmake    （可选）交叉编译工具链样例
├── include/uniubi/robot_sdk/      SDK 公开头
│   ├── MotionSdkProtocol.h
│   ├── MotionSdkService.h
│   ├── MotionLowLevelClient.h
│   ├── MotionHighLevelClient.h
│   ├── MediaBusClient.h           媒体总线（音视频帧订阅）接口
│   ├── Media/                     媒体帧数据结构（Define.h / MediaBuffer.h / FrameInfo.h / MediaFrame.h）
│   ├── Memory/                    Packet 等底层缓冲类型
│   └── UBase/                     Delegate / Define 等基础设施头
├── lib/                           SDK 运行库，按目标架构分子目录
│   ├── x86_64/   librobotMotionSdk.so  libmediaBus.so  libudbus.so  libubase.so
│   ├── aarch64/  librobotMotionSdk.so  libmediaBus.so  libudbus.so  libubase.so
│   └── i386/     librobotMotionSdk.so  libmediaBus.so  libudbus.so  libubase.so
├── examples/                      C++ 示例
│   ├── CMakeLists.txt
│   ├── example_lowlevel.cpp
│   ├── example_highlevel.cpp
│   └── example_media_frames.cpp
└── README.md
```

### 1.2 `uniubi_robot_sdk_py`

```
uniubi_robot_sdk_py/
├── pyproject.toml
├── CMakeLists.txt
├── src/MotionSdkPython.cpp
├── src/MediaFrameBindings.cpp         媒体帧类型绑定；仅 UNIUBI_SDK_ENABLE_MEDIA=ON 时编译
├── src/MediaFrameBindings.h
├── ThirdParty/pybind11/include/...    vendored
├── robot_motion_sdk/__init__.py
├── robot_motion_sdk/media_frame.py    媒体帧 Python 包装层；仅 MEDIA_ENABLED=True 时可导入
└── examples/*.py
```

IDL、ROS 2 msg/srv 和协议 schema 的统一源头是 [`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs)。完整教程和跨仓说明统一维护在 [`uniubi-docs`](https://github.com/uniubi-ai/uniubi-docs)，不随 C++ SDK 仓放置跨仓完整文档。

---

## 2. C++ SDK 构建（本机架构）

### A. 构建 C++ examples

```bash
git clone https://github.com/uniubi-ai/uniubi_robot_sdk.git ~/uniubi_robot_sdk
cd ~/uniubi_robot_sdk
cmake -S . -B build [-DUNIUBI_SDK_ROOT=$PWD]
cmake --build build -j$(nproc)
```

CMake 在 `lib/<arch>/` 下查找 `librobotMotionSdk.so`、`libmediaBus.so`、`libubase.so`；动态加载时还需要同目录中的 `libudbus.so`。这四个运行库按同版本、同架构成组提供；`aarch64` 目标默认同时构建媒体示例。查找顺序：

1. `${UNIUBI_SDK_ROOT}/lib/<arch>`（`-D` 命令行 或环境变量）
2. `${CMAKE_CURRENT_SOURCE_DIR}/lib/<arch>`（仓库内自带）
3. `/opt/uniubi/lib/<arch>`（默认前缀）

> 媒体帧订阅仅支持 `aarch64` 板内本地部署。`x86_64` / `i386` 构建不会启用 `example_media_frames`；业务代码在这些平台不要调用 `createMediaBusClient()` / `setup()` / `start*Frame()`。注意：运行库包仍需保持同版本、同架构 `.so` 文件成组放置，不能只按当前是否调用媒体接口随意删库。

`<arch>` 由 `CMAKE_SYSTEM_PROCESSOR` 自动决定：

| CMAKE_SYSTEM_PROCESSOR | 选用子目录 |
|---|---|
| `x86_64` / `amd64` / `AMD64` | `x86_64` |
| `aarch64` / `arm64` / `ARM64` | `aarch64` |
| `i386` / `i486` / `i586` / `i686` / `x86` | `i386` |

交叉编译时由工具链文件设置 `CMAKE_SYSTEM_PROCESSOR`，无需手动指定目标 arch。

### B. 安装并供业务工程使用

```bash
cmake --install build --prefix "$HOME/.local/uniubi"
```

安装内容包括公开头文件、当前目标架构的运行库、CMake package 和示例程序。业务工程不需要自行查找 `.so`：

```cmake
find_package(UniubiRobotSdk CONFIG REQUIRED)
target_link_libraries(my_robot_app PRIVATE Uniubi::RobotMotionSdk)
# MediaBus 应用额外链接 Uniubi::MediaBus
```

配置业务工程时指定安装前缀：

```bash
cmake -S . -B build -DCMAKE_PREFIX_PATH="$HOME/.local/uniubi"
```

### C. 选择性构建

```bash
cmake -S . -B build -DBUILD_SDK_CPP_EXAMPLES=OFF       # 只做 configure，不编 examples
```

### D. 构建选项汇总

| 变量 | 类型 | 默认 | 来源 | 说明 |
|---|---|---|---|---|
| `UNIUBI_SDK_ROOT` | path | （未设） | `-D` / 环境变量 | SDK 安装前缀；CMake 在 `${UNIUBI_SDK_ROOT}/lib/<arch>/` 下找 `librobotMotionSdk.so`。未设时 fallback 仓库内自带 `lib/<arch>/` 与 `/opt/uniubi/lib/<arch>/` |
| `BUILD_SDK_CPP_EXAMPLES` | option | `ON` | `-D` | 是否编 C++ examples（`examples/example_*`） |
| `CMAKE_TOOLCHAIN_FILE` | path | （未设） | `-D` | 交叉编译工具链文件路径；样例 `cmake/toolchain-aarch64-linux-gnu.cmake` |
| `CMAKE_SYSTEM_PROCESSOR` | string | host arch | toolchain file | 目标 arch；决定 `lib/<arch>/` 子目录选择，本机编无需手动设 |
| `CMAKE_BUILD_TYPE` | string | `Release` | `-D` | 标准 CMake 选项，`Debug` / `RelWithDebInfo` 等可选 |

### 产物

| 产物 | 位置 |
|---|---|
| C++ 示例 | `build/examples/example_lowlevel`、`build/examples/example_highlevel`；`aarch64` 目标额外构建 `build/examples/example_media_frames` |
| 安装后的示例 | `<prefix>/bin/example_lowlevel`、`<prefix>/bin/example_highlevel`；`aarch64` 目标可额外包含 `<prefix>/bin/example_media_frames` |
| CMake package | `<prefix>/lib/cmake/UniubiRobotSdk/` |

---

## 3. 交叉编译（例：x86_64 → aarch64）

```bash
# x86_64 主机安装交叉工具
sudo apt install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

cmake -S . -B build-aarch64 \
      -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain-aarch64-linux-gnu.cmake \
      [-DUNIUBI_SDK_ROOT=$SDK_ROOT]                   # 工具链文件已设 CMAKE_SYSTEM_PROCESSOR=aarch64，CMake 自动从 lib/aarch64/ 取 .so
cmake --build build-aarch64 -j
cmake --install build-aarch64 --prefix "$HOME/.local/uniubi-aarch64"
```

`uniubi-aarch64` 中的 `bin/`、`lib/aarch64/`、`include/` 和 CMake package 都是目标端产物。将所需安装目录部署到 Orin 后运行；不要在 x86_64 编译主机上执行其中的程序。

**自定义工具链**：复制 `cmake/toolchain-aarch64-linux-gnu.cmake` 改 `CMAKE_C/CXX_COMPILER` 和（可选）`CMAKE_SYSROOT`。

> **交叉编 Python 绑定**：Python SDK 在 `uniubi_robot_sdk_py` 仓库内独立构建；交叉编时需在目标 sysroot 里准备**目标 arch 的 `python3-dev`**（Python 头 + libpython），否则配置失败。

---

## 4. 运行 C++ 示例

当前设备运行 SDK 程序需要 root 权限，构建过程不需要 `sudo`。由于 `sudo` 可能清理 `LD_LIBRARY_PATH`，运行时应通过 `sudo env` 显式传入动态库路径。

```bash
case "$(uname -m)" in
  x86_64|amd64) SDK_ARCH=x86_64 ;;
  aarch64|arm64) SDK_ARCH=aarch64 ;;
  i386|i486|i586|i686) SDK_ARCH=i386 ;;
  *) echo "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac
export LD_LIBRARY_PATH="$SDK_ROOT/lib/$SDK_ARCH${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

# 首次连接先运行 High-level 只读 CLI
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  ./build/examples/example_highlevel --read-only

# Low-level 交互 CLI；启动不使能，姿态/阻尼命令按需使能
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  ./build/examples/example_lowlevel
# 仅 aarch64 板内本地部署：
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  ./build/examples/example_media_frames
```

High-level CLI 启动后输入 `status`、`motors`、`sensor 5`、`odom 5` 做只读检查；需要控制时再输入 `take`。Low-level CLI 同样先输入 `status`、`motors`，再按需执行 `stand`、`lie`、`damping` 和 `release`；Low-level 不提供 `take` 命令。完整命令以各 CLI 内的 `help` 为准。

**前置**：
- 目标机器人已就绪
- SDK 端**无需准备 JSON / XML 配置文件**；DDS 配置由 SDK 内部构造
- 远端 / 多设备场景：调用方在 `initialService` 之前调 `setNetworkInterface("eth0")` 指定网卡（详见接口手册 §4.1.2）
- SDK 程序统一使用 root 权限启动；板内 Low-level 和 MediaBus 还会访问受限的共享内存资源

---

## 5. Python SDK 构建 —— 三种使用方式

实际运行 SDK 程序仍需 root 权限。大脑上直接使用系统 `python3`。

### A. PYTHONPATH 直接用（开发期，无需安装）

```bash
git clone https://github.com/uniubi-ai/uniubi_robot_sdk_py.git ~/uniubi_robot_sdk_py
ARCH=$(uname -m)
export UNIUBI_SDK_ROOT=~/uniubi_robot_sdk
export LD_LIBRARY_PATH=$UNIUBI_SDK_ROOT/lib/$ARCH:$LD_LIBRARY_PATH
export PYTHONPATH=~/uniubi_robot_sdk_py
sudo env \
  LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  PYTHONPATH="$PYTHONPATH" \
  python3 ~/uniubi_robot_sdk_py/examples/example_lowlevel.py
```

### B. pip install（装到 site-packages）

```bash
git clone https://github.com/uniubi-ai/uniubi_robot_sdk_py.git ~/uniubi_robot_sdk_py
cd ~/uniubi_robot_sdk_py
sudo -H env UNIUBI_SDK_ROOT=~/uniubi_robot_sdk \
  python3 -m pip install .
# 或用 -C 透传 cmake 变量（等价于设 UNIUBI_SDK_ROOT 环境变量）：
sudo -H python3 -m pip install . \
  -Ccmake.define.UNIUBI_SDK_ROOT=~/uniubi_robot_sdk
# 开发期可编辑安装（改 .py 即时生效，改 C++ 需重装）：
sudo -H env UNIUBI_SDK_ROOT=~/uniubi_robot_sdk \
  python3 -m pip install -e .
```

`uniubi_robot_sdk_py/CMakeLists.txt` 自包含，pip 通过 `scikit-build-core` 后端调用 cmake（支持 `pip install -e .` 可编辑安装与 `-Ccmake.define.*` 透传）。

### Python MediaBus 构建开关

Python native binding 使用 `UNIUBI_SDK_ENABLE_MEDIA` 控制是否编译媒体帧绑定：

| 变量 | 默认 | 说明 |
|---|---|---|
| `UNIUBI_SDK_ENABLE_MEDIA` | `aarch64=ON`；`x86_64/i386=OFF` | `ON` 时编译 `MediaFrameBindings.cpp` 并提供 `MediaBusError`、`VideoFrame` / `AudioFrame` / `EncodedVideoFrame` 等媒体类型；`OFF` 时保留 LowLevel / HighLevel 运控接口，`create_media_bus_client()` 调用会抛出不可用错误 |

运行时可用 `sdk.MEDIA_ENABLED` 判断当前 wheel 是否包含媒体绑定。`False` 时 `create_media_bus_client()` 抛出 `RuntimeError("MediaBus is not available in this SDK build")`，`robot_motion_sdk.media_frame` 导入抛出 `ImportError("MediaBus is not available in this SDK build")`。

媒体帧订阅仍只支持 `aarch64` 板内本地部署；`x86_64` / `i386` wheel 默认关闭媒体绑定，不能调用 media client 接口。

### C. 生成 wheel（分发给客户）

```bash
cd ~/uniubi_robot_sdk_py
UNIUBI_SDK_ROOT=~/uniubi_robot_sdk pip wheel . -w dist/
# → dist/uniubi_robot_motion_sdk-0.1.0-cp310-cp310-linux_aarch64.whl
```

客户端安装：

```bash
pip install uniubi_robot_motion_sdk-0.1.0-cp310-cp310-linux_aarch64.whl
```

---

## 6. 多架构 / 多 Python 版本矩阵（开源分发参考）

每个组合产一份 wheel：

```
(x86_64 / aarch64 / i386)  ×  (cp38 / cp39 / cp310 / cp311 / cp312)  =  15 wheels
```

推荐流程：

- `cibuildwheel` + GitHub Actions / 自建 CI 跑矩阵
- 配合 `auditwheel repair` 把 `librobotMotionSdk.so` / `libmediaBus.so` / `libudbus.so` / `libubase.so` 等 transitive deps 一起塞进 wheel；`aarch64` wheel 默认 `MEDIA_ENABLED=True`，`x86_64` / `i386` wheel 默认 `MEDIA_ENABLED=False`
- 客户端 `pip install` 一行装好，无须额外配置

---

## 7. 关键约束

- `UNIUBI_SDK_ROOT/lib/<arch>/librobotMotionSdk.so` 必须存在；若交叉编译时 CMAKE_SYSTEM_PROCESSOR 与实际 .so 架构不匹配会报 `ELF class mismatch`
- SDK 运行所需的基础动态库目标机必须可加载；做 wheel 分发时由 `auditwheel repair` 自动 bundle 进 wheel
- glibc 最低 **2.34**；运行机 glibc 必须 ≥ 此版本，否则会报 `GLIBC_X.Y not found`
- 编译期上限受 toolchain 限制（不同发行版/工具链可达 2.34/2.35 等）；`librobotMotionSdk.so` 实际真实最低要求（≤ toolchain 上限）可用以下命令查：
  ```bash
  objdump -T librobotMotionSdk.so | grep -oP 'GLIBC_\K[0-9.]+' | sort -V | tail -1
  ```

---

## 8. 验证

构建完成后做最小化导入测试：

```bash
ARCH=$(uname -m)
LD_LIBRARY_PATH=$SDK_ROOT/lib/$ARCH \
PYTHONPATH=~/uniubi_robot_sdk_py \
python3 -c "
import robot_motion_sdk as sdk
print('LowLevelState:', list(sdk.LowLevelState.__members__))
print('clients:', sdk.MotionLowLevelClient, sdk.MotionHighLevelClient)
"
```

端到端联调示例参见 `examples/example_lowlevel.cpp` / `examples/example_highlevel.cpp` 及 `uniubi_robot_sdk_py/examples/`。

---

## 9. Troubleshooting / FAQ

### 9.1 `error while loading shared libraries: librobotMotionSdk.so: cannot open shared object file`

`LD_LIBRARY_PATH` 没有指向正确的 arch 子目录。检查：

```bash
echo $LD_LIBRARY_PATH                          # 应包含 $SDK_ROOT/lib/<arch>
ls $SDK_ROOT/lib/$(uname -m)/librobotMotionSdk.so   # 文件必须存在
```

注意 32 位 x86 系统 `uname -m` 返回 `i686`，需手改为 `i386` 对应子目录。

### 9.2 `/lib/.../libc.so.6: version 'GLIBC_2.34' not found`

目标机 glibc < 2.34。两种处理：

- 升级目标机系统（Ubuntu 22.04 / Debian 12 / CentOS Stream 9 起 glibc ≥ 2.34）
- 改用更低 glibc 上限的 toolchain 重编 `librobotMotionSdk.so`

确认 .so 真实要求：`objdump -T librobotMotionSdk.so | grep -oP 'GLIBC_\K[0-9.]+' | sort -V | tail -1`

### 9.3 `motion rpc call ... failed`（无法连接到机器人）

排查顺序：

1. `setNetworkInterface` 指定的网卡名是否正确（在主机上 `ip a` / `ifconfig` 可见）
2. 目标机器人是否已就绪
3. DDS 网络是否通：同一 domain ID、组播未被防火墙挡

### 9.4 未使用 root 权限或出现 SHM `Permission denied`

当前设备上的 SDK 程序必须以 root 权限运行。板内部署时 Low-level 和 MediaBus 数据面还会访问受限共享内存。先配置动态库路径，再按本文示例使用：

```bash
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  ./build/examples/example_lowlevel
```

### 9.5 Python `ImportError: cannot import name '_uniubi_robot_motion_py_native'`

wheel 与本机架构 / Python 版本不匹配。检查：

```bash
python3 --version                                                # 确认与 wheel 的 cp3XX 一致
file ~/uniubi_robot_sdk_py/robot_motion_sdk/_uniubi_robot_motion_py_native.*.so # 检查 ELF arch
```

或重新本机编：`cd ~/uniubi_robot_sdk_py && UNIUBI_SDK_ROOT=$SDK_ROOT pip install . --force-reinstall`。

### 9.6 Python 程序退出时卡住 / 死锁

未显式 `disconnect()` + `service.shutdown()`，靠 GC 析构会与 SDK 内部线程发生 GIL 死锁。两份手册的 §6.2 有详细规避做法 —— **必须 try/finally 显式释放**。
