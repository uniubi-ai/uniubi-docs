# 宇泛机器人运动 SDK 构建指南

[English](BUILD.md) | **简体中文**

本指南覆盖 C++ SDK、Python SDK、ROS 2 消息包和 ROS 2 示例包的分仓构建方式。C++ SDK 与 Python SDK 分别构建；`uniubi_robot_sdk` 不再把 Python binding 作为子目录一起编译。

相关文档：
- **高级接口手册**：[`uniubi_high_level_sdk.md`](uniubi_high_level_sdk.zh-CN.md) —— 高级控制接口（C++/Python）公开接口、枚举、回调、字段定义
- **低级接口手册**：[`uniubi_low_level_sdk.md`](uniubi_low_level_sdk.zh-CN.md) —— 低级控制接口（C++/Python）公开接口、枚举、回调、字段定义
- **媒体总线手册**：[`uniubi_media_sdk.md`](uniubi_media_sdk.zh-CN.md) —— 摄像头 / 麦克风帧订阅（音视频原始帧 + 编码帧）接口
- **DDS / ROS 2 直连接入手册**：[`uniubi_robot_dds_api.md`](uniubi_robot_dds_api.zh-CN.md) —— 不走 SDK，直接用 OMG DDS 或 ROS 2 对接设备的协议契约 + 工程模板
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
│   ├── example_lowlevel_tensorrt.cpp
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

### A. 构建 C++ 示例

```bash
git clone https://github.com/uniubi-ai/uniubi_robot_sdk.git ~/uniubi_robot_sdk
export SDK_ROOT=~/uniubi_robot_sdk
cd "$SDK_ROOT"
cmake -S . -B build
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

JetPack 6.2.1 Orin 原生构建时，C++ TensorRT Low-level 示例默认开启。也可以显式
控制：

```bash
cmake -S . -B build -DBUILD_SDK_TENSORRT_EXAMPLE=ON
cmake --build build --target example_lowlevel_tensorrt -j$(nproc)
```

该目标使用 JetPack 预装的 CUDA 12.6 / TensorRT 10.3 C++ 开发文件，不依赖
PyTorch。非 Orin 构建和交叉编译默认关闭，不影响普通 SDK examples。

### D. 构建选项汇总

| 变量 | 类型 | 默认 | 来源 | 说明 |
|---|---|---|---|---|
| `UNIUBI_SDK_ROOT` | path | （未设） | `-D` / 环境变量 | SDK 安装前缀；CMake 在 `${UNIUBI_SDK_ROOT}/lib/<arch>/` 下找 `librobotMotionSdk.so`。未设时 fallback 仓库内自带 `lib/<arch>/` 与 `/opt/uniubi/lib/<arch>/` |
| `BUILD_SDK_CPP_EXAMPLES` | option | `ON` | `-D` | 是否编 C++ examples（`examples/example_*`） |
| `BUILD_SDK_TENSORRT_EXAMPLE` | option | Orin 原生构建 `ON`，其他 `OFF` | `-D` | 是否构建 `example_lowlevel_tensorrt` |
| `UNIUBI_TENSORRT_ROOT` | path | （未设） | `-D` | TensorRT 目标端开发文件根目录；交叉编译示例时使用 |
| `UNIUBI_CUDA_ROOT` | path | （未设） | `-D` | CUDA 目标端开发文件根目录；交叉编译示例时使用 |
| `CMAKE_TOOLCHAIN_FILE` | path | （未设） | `-D` | 交叉编译工具链文件路径；样例 `cmake/toolchain-aarch64-linux-gnu.cmake` |
| `CMAKE_SYSTEM_PROCESSOR` | string | host arch | toolchain file | 目标 arch；决定 `lib/<arch>/` 子目录选择，本机编无需手动设 |
| `CMAKE_BUILD_TYPE` | string | `Release` | `-D` | 标准 CMake 选项，`Debug` / `RelWithDebInfo` 等可选 |

### 产物

| 产物 | 位置 |
|---|---|
| C++ 示例 | `build/examples/example_lowlevel`、`build/examples/example_highlevel`；`aarch64` 目标额外构建 `example_media_frames`；Orin 原生构建额外构建 `example_lowlevel_tensorrt` |
| 安装后的示例 | `<prefix>/bin/example_lowlevel`、`<prefix>/bin/example_highlevel`；按构建选项可额外包含 `example_media_frames`、`example_lowlevel_tensorrt` |
| CMake package | `<prefix>/lib/cmake/UniubiRobotSdk/` |

---

## 3. 交叉编译（例：x86_64 → aarch64）

```bash
# x86_64 主机安装交叉工具
sudo apt install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

cmake -S . -B build-aarch64 \
      -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain-aarch64-linux-gnu.cmake
cmake --build build-aarch64 -j
cmake --install build-aarch64 --prefix "$HOME/.local/uniubi-aarch64"
```

`uniubi-aarch64` 中的 `bin/`、`lib/aarch64/`、`include/` 和 CMake package 都是目标端产物。将所需安装目录部署到 Orin 后运行；不要在 x86_64 编译主机上执行其中的程序。

**自定义工具链**：复制 `cmake/toolchain-aarch64-linux-gnu.cmake` 改 `CMAKE_C/CXX_COMPILER` 和（可选）`CMAKE_SYSROOT`。

> **交叉编 Python 绑定**：Python SDK 在 `uniubi_robot_sdk_py` 仓库内独立构建；交叉编时需在目标 sysroot 里准备**目标 arch 的 `python3-dev`**（Python 头 + libpython），否则配置失败。

### 3.1 交叉编译 TensorRT 示例的额外边界

普通 C++ SDK examples 只需要仓库提供的 aarch64 SDK 运行库。TensorRT 示例还需要
与目标 JetPack 完全匹配的 aarch64 TensorRT/CUDA 头文件和链接库，因此交叉编译时
不会默认启用，也不能链接主机 x86_64 的 NVIDIA 库。

以下流程已在 Ubuntu 22.04 x86_64 主机完成交叉编译，并将产物部署到 JetPack 6.2.1
（CUDA 12.6 / TensorRT 10.3）Orin 实机验证通过。NVIDIA 的交叉包位于专用的
`ubuntu2204/cross-linux-aarch64` 软件源，不在普通的 `ubuntu2204/x86_64` 源。

先安装交叉软件源和编译器；如果所在网络需要 HTTP 代理，只对当前命令设置
`http_proxy` / `https_proxy` 即可，无需写入系统配置：

```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/cross-linux-aarch64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu
```

该软件源当前默认的 `tensorrt-dev-cross-aarch64` 可能高于机器人运行时版本。JetPack
6.2.1 目标必须将 TensorRT 交叉开发包整组固定在 10.3，不能直接安装默认 candidate：

```text
# /etc/apt/preferences.d/uniubi-tensorrt-10-3-cross
Package: tensorrt-dev-cross-aarch64 libnvinfer*-cross-aarch64 libnvonnxparsers*-cross-aarch64
Pin: version 10.3.0.26-1+cuda12.5
Pin-Priority: 1001
```

安装 CUDA 12.6 与 TensorRT 10.3 的 aarch64 交叉开发文件：

```bash
sudo apt install cuda-cross-aarch64-12-6 tensorrt-dev-cross-aarch64

apt-cache policy cuda-cross-aarch64-12-6 tensorrt-dev-cross-aarch64
```

实测该组合下载约 1.14 GB，安装后约占用 3.72 GB。TensorRT 10.3 交叉包的版本字符串
带有 `+cuda12.5`，但它提供的是 JetPack 6.2.1 TensorRT 10.3 ABI 所需的 aarch64
头文件与链接库；CUDA runtime 仍使用 `cuda-cross-aarch64-12-6`。应用不在交叉主机
构建 engine，而是在 Orin 每次启动时从 ONNX 现场构建。

安装后，文件位于：

```text
/usr/include/aarch64-linux-gnu/NvInfer.h
/usr/include/aarch64-linux-gnu/NvOnnxParser.h
/usr/lib/aarch64-linux-gnu/libnvinfer.so
/usr/lib/aarch64-linux-gnu/libnvonnxparser.so
/usr/local/cuda-12.6/targets/aarch64-linux/include/cuda_runtime_api.h
/usr/local/cuda-12.6/targets/aarch64-linux/lib/libcudart.so
```

使用 SDK 自带工具链显式启用 TensorRT 示例：

```bash
cmake -S . -B build-aarch64 \
  -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain-aarch64-linux-gnu.cmake \
  -DBUILD_SDK_TENSORRT_EXAMPLE=ON \
  -DBUILD_SDK_MEDIA_EXAMPLE=OFF \
  -DUNIUBI_TENSORRT_ROOT=/usr \
  -DUNIUBI_CUDA_ROOT=/usr/local/cuda-12.6 \
  -DCMAKE_BUILD_TYPE=Release

cmake --build build-aarch64 --target example_lowlevel_tensorrt -j$(nproc)
```

产物为 `build-aarch64/examples/example_lowlevel_tensorrt`。Jetson TensorRT 还依赖
`libnvdla_compiler.so`、`libcudla.so.1` 等目标端运行库，官方交叉包不提供完整实现；
SDK CMake 在 aarch64 交叉链接时允许这些目标端符号保持未解析，最终由 Orin 的
`/vendor/usr/lib` 提供。不能因此把 x86_64 NVIDIA 库加入链接路径。

部署时应同时携带同一 SDK 版本的 `lib/aarch64/`。先在 Orin 执行
`--validate-only`，确认动态库解析、ONNX 解析、FP32 engine 构建和一次推理全部成功，
再进入 Low-level 连接与控制验证。SDK 仓库不分发 NVIDIA 二进制库；不希望在交叉
主机安装上述依赖时，仍可选择直接在 Orin 上原生编译。

---

## 4. 运行 C++ 示例

当前设备运行 SDK 程序需要 root 权限，构建过程不需要 `sudo`。由于 `sudo` 可能清理 `LD_LIBRARY_PATH`，运行时应通过 `sudo env` 显式传入动态库路径。

```bash
export SDK_ROOT="${SDK_ROOT:-$HOME/uniubi_robot_sdk}"
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

# Orin C++ TensorRT Low-level：先做纯模型验证，再进入实机交互
taskset -c 2 ./build/examples/example_lowlevel_tensorrt \
  --onnx /path/to/policy.onnx --validate-only
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  taskset -c 2 ./build/examples/example_lowlevel_tensorrt \
  --onnx /path/to/policy.onnx
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
case "$(uname -m)" in
  x86_64|amd64) SDK_ARCH=x86_64 ;;
  aarch64|arm64) SDK_ARCH=aarch64 ;;
  i386|i486|i586|i686) SDK_ARCH=i386 ;;
  *) echo "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac
export UNIUBI_SDK_ROOT=~/uniubi_robot_sdk
export LD_LIBRARY_PATH="$UNIUBI_SDK_ROOT/lib/$SDK_ARCH${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PYTHONPATH=~/uniubi_robot_sdk_py
sudo env \
  LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  PYTHONPATH="$PYTHONPATH" \
  python3 ~/uniubi_robot_sdk_py/examples/example_lowlevel.py
```

### B. 使用 pip 安装（安装到 site-packages）

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

### MediaBus Python 绑定构建开关

Python native binding 使用 `UNIUBI_SDK_ENABLE_MEDIA` 控制是否编译媒体帧绑定：

| 变量 | 默认 | 说明 |
|---|---|---|
| `UNIUBI_SDK_ENABLE_MEDIA` | `aarch64=ON`；`x86_64/i386=OFF` | `ON` 时编译 `MediaFrameBindings.cpp` 并提供 `MediaBusError`、`VideoFrame` / `AudioFrame` / `EncodedVideoFrame` 等媒体类型；`OFF` 时保留 LowLevel / HighLevel 运控接口，`create_media_bus_client()` 调用会抛出不可用错误 |

运行时可用 `sdk.MEDIA_ENABLED` 判断当前 wheel 是否包含媒体绑定。`False` 时 `create_media_bus_client()` 抛出 `RuntimeError("MediaBus is not available in this SDK build")`，`robot_motion_sdk.media_frame` 导入抛出 `ImportError("MediaBus is not available in this SDK build")`。

媒体帧订阅仍只支持 `aarch64` 板内本地部署；`x86_64` / `i386` wheel 默认关闭媒体绑定，不能调用 media client 接口。

### C. 生成 wheel 包（分发给客户）

```bash
cd ~/uniubi_robot_sdk_py
UNIUBI_SDK_ROOT=~/uniubi_robot_sdk python3 -m pip wheel . -w dist/
# → dist/uniubi_robot_motion_sdk-1.0.0-cp310-cp310-linux_aarch64.whl
```

客户端安装：

```bash
python3 -m pip install uniubi_robot_motion_sdk-1.0.0-cp310-cp310-linux_aarch64.whl
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
export SDK_ROOT="${SDK_ROOT:-$HOME/uniubi_robot_sdk}"
case "$(uname -m)" in
  x86_64|amd64) SDK_ARCH=x86_64 ;;
  aarch64|arm64) SDK_ARCH=aarch64 ;;
  i386|i486|i586|i686) SDK_ARCH=i386 ;;
  *) echo "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac
LD_LIBRARY_PATH="$SDK_ROOT/lib/$SDK_ARCH" \
PYTHONPATH=~/uniubi_robot_sdk_py \
python3 -c "
import robot_motion_sdk as sdk
print('LowLevelState:', list(sdk.LowLevelState.__members__))
print('clients:', sdk.MotionLowLevelClient, sdk.MotionHighLevelClient)
"
```

端到端联调示例参见 `examples/example_lowlevel.cpp` / `examples/example_highlevel.cpp` 及 `uniubi_robot_sdk_py/examples/`。

---

<a id="troubleshooting--faq"></a>
## 9. 故障排查 / 常见问题

### 9.1 `error while loading shared libraries: librobotMotionSdk.so: cannot open shared object file`

`LD_LIBRARY_PATH` 没有指向正确的 arch 子目录。检查：

```bash
export SDK_ROOT="${SDK_ROOT:-$HOME/uniubi_robot_sdk}"
case "$(uname -m)" in
  x86_64|amd64) SDK_ARCH=x86_64 ;;
  aarch64|arm64) SDK_ARCH=aarch64 ;;
  i386|i486|i586|i686) SDK_ARCH=i386 ;;
  *) echo "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac
echo $LD_LIBRARY_PATH                          # 应包含 $SDK_ROOT/lib/<arch>
ls "$SDK_ROOT/lib/$SDK_ARCH/librobotMotionSdk.so"   # 文件必须存在
```

上述映射会将 32 位 x86 的 `i686` 统一转换为 SDK 的 `i386` 子目录。

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

或重新本机编：`cd ~/uniubi_robot_sdk_py && UNIUBI_SDK_ROOT=$SDK_ROOT python3 -m pip install . --force-reinstall`。

### 9.6 Python 程序退出时卡住 / 死锁

未显式 `disconnect()` + `service.shutdown()`，靠 GC 析构会与 SDK 内部线程发生 GIL 死锁。两份手册的 §6.2 有详细规避做法 —— **必须 try/finally 显式释放**。
