# Uniubi Robot Motion SDK Build Guide

**English** | [简体中文](BUILD.zh-CN.md)

This guide covers the C++ SDK, Python SDK, ROS 2 message package, and ROS 2 examples. The C++ and Python SDKs are built separately; `uniubi_robot_sdk` no longer builds the Python binding as a subdirectory.

Related documents:
- **High-level SDK API**: [`uniubi_high_level_sdk.md`](uniubi_high_level_sdk.md) — public C++/Python interfaces, enums, callbacks, and fields
- **Low-level SDK API**: [`uniubi_low_level_sdk.md`](uniubi_low_level_sdk.md) — public C++/Python interfaces, enums, callbacks, and fields
- **Media SDK API**: [`uniubi_media_sdk.md`](uniubi_media_sdk.md) — camera, microphone, raw-frame, and encoded-frame subscription
- **Direct DDS / ROS 2 API**: [`uniubi_robot_dds_api.md`](uniubi_robot_dds_api.md) — device protocol contracts and project templates for direct OMG DDS or ROS 2 integration without the SDK

---

## 0. Prerequisites

| Dependency | Requirement |
|---|---|
| Target system | Linux (`x86_64` / `aarch64` / `i386`) |
| glibc | **2.34 or later** on the build and runtime systems |
| Compiler | g++ ≥ 9 (supports C++14) |
| CMake | ≥ 3.18 |
| Python development files | Python 3.8+ and `python3-dev` for Python bindings |
| System runtime libraries | Installed on the target and available through the standard dynamic-library search path |
| SDK runtime libraries | `librobotMotionSdk.so`, `libmediaBus.so`, `libudbus.so`, and `libubase.so` from one version and architecture; `MediaBusClient` supports local on-board media subscription on `aarch64` only |

---

## 1. Repository Layout

### 1.1 `uniubi_robot_sdk`

```
uniubi_robot_sdk/
├── CMakeLists.txt                 C++ SDK example build entry point
├── cmake/
│   ├── UniubiRobotSdkConfig.cmake.in         CMake package template
│   └── toolchain-aarch64-linux-gnu.cmake     optional cross-toolchain example
├── include/uniubi/robot_sdk/      public SDK headers
│   ├── MotionSdkProtocol.h
│   ├── MotionSdkService.h
│   ├── MotionLowLevelClient.h
│   ├── MotionHighLevelClient.h
│   ├── MediaBusClient.h           MediaBus audio/video subscription interface
│   ├── Media/                     media-frame data structures
│   ├── Memory/                    low-level buffer types such as Packet
│   └── UBase/                     infrastructure headers such as Delegate and Define
├── lib/                           SDK runtime libraries by target architecture
│   ├── x86_64/   librobotMotionSdk.so  libmediaBus.so  libudbus.so  libubase.so
│   ├── aarch64/  librobotMotionSdk.so  libmediaBus.so  libudbus.so  libubase.so
│   └── i386/     librobotMotionSdk.so  libmediaBus.so  libudbus.so  libubase.so
├── examples/                      C++ examples
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
├── src/MediaFrameBindings.cpp         media-frame bindings; built only with UNIUBI_SDK_ENABLE_MEDIA=ON
├── src/MediaFrameBindings.h
├── ThirdParty/pybind11/include/...    vendored pybind11
├── robot_motion_sdk/__init__.py
├── robot_motion_sdk/media_frame.py    Python media wrapper; importable only when MEDIA_ENABLED=True
└── examples/*.py
```

[`uniubi_robot_msgs`](https://github.com/uniubi-ai/uniubi_robot_msgs) is the authoritative source for IDL, ROS 2 messages/services, and protocol schemas. Cross-repository development guides are maintained in [`uniubi-docs`](https://github.com/uniubi-ai/uniubi-docs), not duplicated in the C++ SDK repository.

---

## 2. Build the C++ SDK Natively

### A. Build the C++ examples

```bash
git clone https://github.com/uniubi-ai/uniubi_robot_sdk.git ~/uniubi_robot_sdk
cd ~/uniubi_robot_sdk
cmake -S . -B build [-DUNIUBI_SDK_ROOT=$PWD]
cmake --build build -j$(nproc)
```

CMake searches for `librobotMotionSdk.so`, `libmediaBus.so`, and `libubase.so` under `lib/<arch>/`. Dynamic loading also requires `libudbus.so` from the same directory. Keep all four libraries at the same version and architecture. The `aarch64` target builds the media example by default. Search order:

1. `${UNIUBI_SDK_ROOT}/lib/<arch>` (`-D` command line or environment variable)
2. `${CMAKE_CURRENT_SOURCE_DIR}/lib/<arch>` (included in the repository)
3. `/opt/uniubi/lib/<arch>` (default prefix)

> Media-frame subscription supports only local on-board deployment on `aarch64`. `x86_64` and `i386` builds do not enable `example_media_frames`; applications on those platforms must not call `createMediaBusClient()`, `setup()`, or `start*Frame()`. Keep the delivered `.so` files as a matched version and architecture set even when the application does not call a media interface.

`<arch>` is automatically determined by `CMAKE_SYSTEM_PROCESSOR`:

| `CMAKE_SYSTEM_PROCESSOR` | Selected subdirectory |
|---|---|
| `x86_64` / `amd64` / `AMD64` | `x86_64` |
| `aarch64` / `arm64` / `ARM64` | `aarch64` |
| `i386` / `i486` / `i586` / `i686` / `x86` | `i386` |

During cross-compilation, the toolchain file sets `CMAKE_SYSTEM_PROCESSOR`; do not override the target architecture manually.

### B. Install for use by an application

```bash
cmake --install build --prefix "$HOME/.local/uniubi"
```

Installation includes public headers, runtime libraries for the target architecture, the CMake package, and example programs. Consumer projects can link exported targets instead of locating `.so` files manually:

```cmake
find_package(UniubiRobotSdk CONFIG REQUIRED)
target_link_libraries(my_robot_app PRIVATE Uniubi::RobotMotionSdk)
# MediaBus applications also link Uniubi::MediaBus
```

Pass the installation prefix when configuring the consumer project:

```bash
cmake -S . -B build -DCMAKE_PREFIX_PATH="$HOME/.local/uniubi"
```

### C. Selective build

```bash
cmake -S . -B build -DBUILD_SDK_CPP_EXAMPLES=OFF       # configure only; do not build examples
```

On a native JetPack 6.2.1 Orin build, the C++ TensorRT Low-level example is enabled by default. It can also be enabled explicitly:

```bash
cmake -S . -B build -DBUILD_SDK_TENSORRT_EXAMPLE=ON
cmake --build build --target example_lowlevel_tensorrt -j$(nproc)
```

This target uses the CUDA 12.6 and TensorRT 10.3 C++ development files provided by JetPack and does not depend on PyTorch. It is disabled by default for non-Orin and cross builds and does not affect the other SDK examples.

### D. Summary of build options

| Variable | Type | Default | Source | Description |
|---|---|---|---|---|
| `UNIUBI_SDK_ROOT` | path | unset | `-D` / environment | SDK root; CMake looks for `librobotMotionSdk.so` under `${UNIUBI_SDK_ROOT}/lib/<arch>/`. Without it, CMake searches the repository's `lib/<arch>/` and `/opt/uniubi/lib/<arch>/` |
| `BUILD_SDK_CPP_EXAMPLES` | option | `ON` | `-D` | Whether to compile C++ examples (`examples/example_*`) |
| `BUILD_SDK_TENSORRT_EXAMPLE` | option | Orin natively builds `ON`, others `OFF` | `-D` | Whether to build `example_lowlevel_tensorrt` |
| `UNIUBI_TENSORRT_ROOT` | path | unset | `-D` | Root of target TensorRT development files for cross-compiling the example |
| `UNIUBI_CUDA_ROOT` | path | unset | `-D` | Root of target CUDA development files for cross-compiling the example |
| `CMAKE_TOOLCHAIN_FILE` | path | unset | `-D` | Cross-toolchain file, for example `cmake/toolchain-aarch64-linux-gnu.cmake` |
| `CMAKE_SYSTEM_PROCESSOR` | string | host architecture | toolchain file | Target architecture and `lib/<arch>/` selector; do not set manually for a native build |
| `CMAKE_BUILD_TYPE` | string | `Release` | `-D` | Standard CMake options, `Debug` / `RelWithDebInfo`, etc. are optional |

### Build outputs

| Output | Location |
|---|---|
| C++ examples | `build/examples/example_lowlevel`, `build/examples/example_highlevel`; `aarch64` additionally builds `example_media_frames`; native Orin additionally builds `example_lowlevel_tensorrt` |
| Installed examples | `<prefix>/bin/example_lowlevel`, `<prefix>/bin/example_highlevel`, plus examples enabled by the media and TensorRT build options |
| CMake package | `<prefix>/lib/cmake/UniubiRobotSdk/` |

---

## 3. Cross-compile from x86_64 to aarch64

```bash
# Install the cross toolchain on the x86_64 host
sudo apt install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

cmake -S . -B build-aarch64 \
      -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain-aarch64-linux-gnu.cmake \
      [-DUNIUBI_SDK_ROOT=$SDK_ROOT]                   # the toolchain selects lib/aarch64/
cmake --build build-aarch64 -j
cmake --install build-aarch64 --prefix "$HOME/.local/uniubi-aarch64"
```

The `bin/`, `lib/aarch64/`, `include/`, and CMake package under `uniubi-aarch64` are target artifacts. Deploy the required installation tree to Orin before running it. Do not execute aarch64 programs on the x86_64 build host.

**Custom toolchain:** copy `cmake/toolchain-aarch64-linux-gnu.cmake` and adjust `CMAKE_C_COMPILER`, `CMAKE_CXX_COMPILER`, and optionally `CMAKE_SYSROOT`.

> **Cross-compiling Python bindings:** the Python SDK is built independently in `uniubi_robot_sdk_py`. Its target sysroot must contain the target-architecture `python3-dev` files (Python headers and `libpython`) or configuration will fail.

### 3.1 Additional requirements for the TensorRT example

The standard C++ SDK examples require only the delivered aarch64 SDK runtime set. The TensorRT example also requires aarch64 TensorRT and CUDA headers and libraries compatible with the target JetPack. It is therefore disabled by default during cross-compilation. Never link the host's x86_64 NVIDIA libraries into the target program.

The following workflow was validated on an Ubuntu 22.04 x86_64 host and on a JetPack 6.2.1 Orin target with CUDA 12.6 and TensorRT 10.3. NVIDIA publishes the required cross packages in the dedicated `ubuntu2204/cross-linux-aarch64` repository, not the standard `ubuntu2204/x86_64` repository.

Install the cross repository and compiler first. If an HTTP proxy is required, set `http_proxy` and `https_proxy` only for the relevant command; no persistent system configuration is necessary.

```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/cross-linux-aarch64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu
```

The default `tensorrt-dev-cross-aarch64` candidate may be newer than the robot runtime. For a JetPack 6.2.1 target, pin the complete TensorRT cross-development package set to 10.3 instead of installing the default candidate:

```text
# /etc/apt/preferences.d/uniubi-tensorrt-10-3-cross
Package: tensorrt-dev-cross-aarch64 libnvinfer*-cross-aarch64 libnvonnxparsers*-cross-aarch64
Pin: version 10.3.0.26-1+cuda12.5
Pin-Priority: 1001
```

Install the aarch64 cross-development files for CUDA 12.6 and TensorRT 10.3:

```bash
sudo apt install cuda-cross-aarch64-12-6 tensorrt-dev-cross-aarch64

apt-cache policy cuda-cross-aarch64-12-6 tensorrt-dev-cross-aarch64
```

This package set downloads approximately 1.14 GB and occupies approximately 3.72 GB after installation. The TensorRT 10.3 cross-package version contains `+cuda12.5`, but provides the aarch64 TensorRT 10.3 ABI, headers, and link libraries required by JetPack 6.2.1. CUDA uses `cuda-cross-aarch64-12-6`. The cross host builds the application, not the engine; the application rebuilds the engine from ONNX each time it starts on Orin.

After installation, the files are located at:

```text
/usr/include/aarch64-linux-gnu/NvInfer.h
/usr/include/aarch64-linux-gnu/NvOnnxParser.h
/usr/lib/aarch64-linux-gnu/libnvinfer.so
/usr/lib/aarch64-linux-gnu/libnvonnxparser.so
/usr/local/cuda-12.6/targets/aarch64-linux/include/cuda_runtime_api.h
/usr/local/cuda-12.6/targets/aarch64-linux/lib/libcudart.so
```

Explicitly enable the TensorRT example with the SDK toolchain:

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

The output is `build-aarch64/examples/example_lowlevel_tensorrt`. Jetson TensorRT also depends on target runtime libraries such as `libnvdla_compiler.so` and `libcudla.so.1`, for which the official cross package does not provide complete implementations. The SDK CMake configuration allows those target symbols to remain unresolved during aarch64 cross-linking; they are resolved by Orin's `/vendor/usr/lib` at runtime. Do not add x86_64 NVIDIA libraries to the link path.

Deploy the matching SDK `lib/aarch64/` runtime set with the program. Run `--validate-only` on Orin first and confirm dynamic-library loading, ONNX parsing, FP32 engine construction, and one inference before any Low-level connection or control test. The SDK repository does not redistribute NVIDIA binary libraries. Native compilation on Orin remains an alternative to installing the cross dependencies on the host.

---

## 4. Run the C++ Examples

SDK programs require root privileges on current devices; compilation does not. Because `sudo` may remove `LD_LIBRARY_PATH`, pass the dynamic-library path explicitly with `sudo env` at runtime.

```bash
case "$(uname -m)" in
  x86_64|amd64) SDK_ARCH=x86_64 ;;
  aarch64|arm64) SDK_ARCH=aarch64 ;;
  i386|i486|i586|i686) SDK_ARCH=i386 ;;
  *) echo "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac
export LD_LIBRARY_PATH="$SDK_ROOT/lib/$SDK_ARCH${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

# Start with the read-only High-level CLI
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  ./build/examples/example_highlevel --read-only

# Low-level CLI; startup does not enable control
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  ./build/examples/example_lowlevel

# Orin C++ TensorRT Low-level: validate the model before hardware interaction
taskset -c 2 ./build/examples/example_lowlevel_tensorrt \
  --onnx /path/to/policy.onnx --validate-only
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  taskset -c 2 ./build/examples/example_lowlevel_tensorrt \
  --onnx /path/to/policy.onnx
# Local on-board aarch64 only
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  ./build/examples/example_media_frames
```

In the High-level CLI, begin with `status`, `motors`, `sensor 5`, and `odom 5`; enter `take` only when control is required. In the Low-level CLI, begin with `status` and `motors`, then use `stand`, `lie`, `damping`, and `release` as needed. Low-level has no `take` command. Enter `help` in either CLI for its complete command set.

**Before running:**

- Confirm that the target robot is ready.
- No SDK-side JSON/XML file is required; the SDK constructs its DDS configuration internally.
- For remote or multi-device use, call `setNetworkInterface("eth0")` with the actual robot-facing interface before `initialService`.
- Run SDK programs with root privileges. On-board Low-level and MediaBus also access restricted shared-memory resources.

---

## 5. Build and Use the Python SDK

SDK programs still require root privileges at runtime. Use the system `python3` directly on the robot compute module.

### A. Use `PYTHONPATH` during development

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

### B. Install into `site-packages` with pip

```bash
git clone https://github.com/uniubi-ai/uniubi_robot_sdk_py.git ~/uniubi_robot_sdk_py
cd ~/uniubi_robot_sdk_py
sudo -H env UNIUBI_SDK_ROOT=~/uniubi_robot_sdk \
  python3 -m pip install .
# Or pass the CMake variable with -C (equivalent to UNIUBI_SDK_ROOT)
sudo -H python3 -m pip install . \
  -Ccmake.define.UNIUBI_SDK_ROOT=~/uniubi_robot_sdk
# Editable development install (.py changes are immediate; C++ changes require reinstall)
sudo -H env UNIUBI_SDK_ROOT=~/uniubi_robot_sdk \
  python3 -m pip install -e .
```

`uniubi_robot_sdk_py/CMakeLists.txt` is self-contained. pip invokes CMake through the `scikit-build-core` backend, which supports editable installation with `pip install -e .` and CMake options through `-Ccmake.define.*`.

### Python MediaBus build switch

The Python native binding uses `UNIUBI_SDK_ENABLE_MEDIA` to control media-frame bindings:

| Variable | Default | Description |
|---|---|---|
| `UNIUBI_SDK_ENABLE_MEDIA` | `aarch64=ON`; `x86_64/i386=OFF` | An `OFF` build retains LowLevel/HighLevel motion interfaces; `create_media_bus_client()` reports that MediaBus is unavailable |

At runtime, use `sdk.MEDIA_ENABLED` to determine whether the wheel includes media bindings. When it is `False`, `create_media_bus_client()` raises `RuntimeError("MediaBus is not available in this SDK build")`, and importing `robot_motion_sdk.media_frame` raises `ImportError("MediaBus is not available in this SDK build")`.

Media-frame subscription supports only local on-board `aarch64` deployment. `x86_64` and `i386` wheels disable media bindings by default and cannot use the media client.

### C. Build a distributable wheel

```bash
cd ~/uniubi_robot_sdk_py
UNIUBI_SDK_ROOT=~/uniubi_robot_sdk pip wheel . -w dist/
# → dist/uniubi_robot_motion_sdk-1.0.0-cp310-cp310-linux_aarch64.whl
```

Install the wheel:

```bash
pip install uniubi_robot_motion_sdk-1.0.0-cp310-cp310-linux_aarch64.whl
```

---

## 6. Multi-architecture and Python-version Matrix

Each combination produces a separate wheel:

```
(x86_64 / aarch64 / i386)  ×  (cp38 / cp39 / cp310 / cp311 / cp312)  =  15 wheels
```

Recommended approach:

- Run the matrix with `cibuildwheel` and GitHub Actions or another CI system.
- Use `auditwheel repair` to bundle `librobotMotionSdk.so`, `libmediaBus.so`, `libudbus.so`, `libubase.so`, and required transitive dependencies. `aarch64` wheels default to `MEDIA_ENABLED=True`; `x86_64` and `i386` wheels default to `False`.
- Verify that the resulting wheel can be installed with a single `pip install` command.

---

## 7. Key Constraints

- `UNIUBI_SDK_ROOT/lib/<arch>/librobotMotionSdk.so` must exist. If `CMAKE_SYSTEM_PROCESSOR` does not match the `.so` architecture during cross-compilation, the linker reports `ELF class mismatch`.
- Required runtime libraries must be loadable on the target. For wheel distribution, use `auditwheel repair` to bundle the supported dependencies.
- The minimum supported glibc is **2.34**. An older runtime reports `GLIBC_X.Y not found`.
- The toolchain determines the highest glibc version referenced at build time. Inspect the actual requirement of `librobotMotionSdk.so` with:
  ```bash
  objdump -T librobotMotionSdk.so | grep -oP 'GLIBC_\K[0-9.]+' | sort -V | tail -1
  ```

---

## 8. Verification

After building, run a minimal import test:

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

For end-to-end examples, see `examples/example_lowlevel.cpp`, `examples/example_highlevel.cpp`, and `uniubi_robot_sdk_py/examples/`.

---

## 9. Troubleshooting / FAQ

### 9.1 `error while loading shared libraries: librobotMotionSdk.so: cannot open shared object file`

`LD_LIBRARY_PATH` does not point to the correct architecture directory. Check:

```bash
echo $LD_LIBRARY_PATH                          # must include $SDK_ROOT/lib/<arch>
ls $SDK_ROOT/lib/$(uname -m)/librobotMotionSdk.so   # file must exist
```

On 32-bit x86, `uname -m` may return `i686`; map it to the SDK's `i386` directory.

### 9.2 `/lib/.../libc.so.6: version 'GLIBC_2.34' not found`

The target glibc is older than 2.34. Either:

- Upgrade the target system (glibc ≥ 2.34 from Ubuntu 22.04 / Debian 12 / CentOS Stream 9)
- obtain an SDK runtime built for the target's older glibc with a compatible toolchain.

Inspect the `.so` requirement with: `objdump -T librobotMotionSdk.so | grep -oP 'GLIBC_\K[0-9.]+' | sort -V | tail -1`

### 9.3 `motion rpc call ... failed` (cannot connect to the robot)

Check in this order:

1. Confirm that `setNetworkInterface` names the robot-facing interface shown by `ip a` or `ifconfig`.
2. Confirm that the target robot is ready.
3. Confirm DDS connectivity: matching domain IDs and multicast permitted by the firewall.

### 9.4 Missing root privileges or SHM `Permission denied`

SDK programs require root privileges on current devices. On-board Low-level and MediaBus data planes also access restricted shared memory. Configure the dynamic-library path first, then run:

```bash
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  ./build/examples/example_lowlevel
```

### 9.5 Python `ImportError: cannot import name '_uniubi_robot_motion_py_native'`

The wheel does not match the architecture or Python version. Check:

```bash
python3 --version                                                # must match the wheel's cp3XX tag
file ~/uniubi_robot_sdk_py/robot_motion_sdk/_uniubi_robot_motion_py_native.*.so # inspect ELF architecture
```

Or rebuild and reinstall it: `cd ~/uniubi_robot_sdk_py && UNIUBI_SDK_ROOT=$SDK_ROOT pip install . --force-reinstall`.

### 9.6 Python program gets stuck/deadlocked when exiting

If the application does not explicitly call `disconnect()` and `service.shutdown()`, garbage collection can deadlock the GIL against an internal SDK thread. Follow section 6.2 of the relevant API manual and **release resources explicitly in `try/finally`**.
