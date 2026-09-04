# 宇泛机器人 Low-level Python API 参考

[English](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/python/low-level.md) | **简体中文**

[返回 API 参考](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/README.zh-CN.md) · [查看 C++ API](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/api-reference/cpp/low-level.zh-CN.md)

Python 模块：`robot_motion_sdk`
主要客户端：`sdk.MotionLowLevelClient`

真机 Low-level Python 程序必须运行在机器人“大脑”侧，并先在吊架、急停可触达的条件下完成只读与零动作验证。

## 一、最小初始化与退出

以下示例只建立连接并显式释放资源，不会自动执行动作：

```python
import robot_motion_sdk as sdk

if not sdk.service.initial(None, "pythonApiExample"):
    raise RuntimeError("SDK initialization failed")

client = sdk.MotionLowLevelClient()
try:
    if not client.connect():
        raise RuntimeError(f"connect failed: {client.get_last_error()}")
    print("state:", client.get_state())
finally:
    client.disconnect()
    sdk.service.shutdown()
```

> 不要依赖 Python 垃圾回收销毁客户端。所有正常退出、异常和信号退出路径都必须进入 `finally`。

## 二、Python API 覆盖范围

**全局服务（`sdk.service` —— 对应 `IMotionSdkService` 单例）：**

| 功能 / native 名称 | Python API |
|---|---|
| `version()` | `sdk.service.version()` —— 返回 SDK 版本字符串 |
| `setLogCallback` | `sdk.service.set_log_callback(cb)`；签名 `(level: LogLevel, msg: str) -> None` |
| `initialService` | `sdk.service.initial(file_or_none, server_name, timeout_ms=30000)` |
| `shutdown` | `sdk.service.shutdown()` |

**LowLevel client（`sdk.MotionLowLevelClient` —— 对应 `IMotionLowLevelClient`）：**

| 功能 / native 名称 | Python API |
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
| `getSensorObservation` | `get_sensor_observation(timeout_ms=5)`；返回 `SensorObserved` 或 `None`（仅 GPS + UWB，不支持 Walk 里程计；timeout 单位 ms，默认 5ms） |
| `getMotorLayout` | `get_motor_layout(timeout_ms=5000)`；返回 `MotorLayout` 或 `None` |
| `restoreMotionControlMode` | `restore_motion_control_mode(timeout_ms=5000)`；返回 bool |
| `setConnectCallback` | `set_connect_callback(cb)` 或装饰器 `@client.on_connect`；签名 `(state, error)` |

数据结构 `MotorCtrl / MotorCtrlAction / LowLevelMotionCmd / MotorObserved / MotorInfo / MotorLayout / IMUObserved / Vector3f / Quaternionf / PowerObserved / TRCStickFrame / LowLevelMotionObserved / SensorObserved / GPSFrame / GEOGPoint / UWBRawObserved` 全部 expose 为 Python 类（字段下划线命名：`limb_no`, `joint_no`, `kp_gain`, `kd_gain`, `motor_num`, `charge_voltage`, `velocity_x` 等）。

> Low-level 不支持 Walk 里程计。即使共享协议结构或某个 binding 版本出现 `odom` 字段，也不属于公开支持契约，应用不得依赖。

## 三、退出死锁规避（必读）

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

## 四、Python 使用示例

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


## 五、注意事项

- 回调中不要执行阻塞 IO、长时间计算或 SDK 重入调用；耗时处理转交业务线程。
- `robot_motion_sdk`、native binding 和 `librobotMotionSdk.so` 必须来自同一 SDK 版本与目标架构。
- 所有退出路径都要显式 `disconnect()`，最后调用 `sdk.service.shutdown()`。
- Low-level 真机程序必须在大脑侧运行；使能控制前必须核对电机布局、关节方向、急停和人工接管。

## 六、常见问题

| 现象 | 优先检查 |
|---|---|
| `sdk.service.initial(...)` 失败 | 动态库路径、SDK/绑定版本、配置文件和所选网卡是否存在 |
| 无法进入 `kPrepared` | 确认已连接、`set_motion_enable(True)` 请求成功，且没有其他控制方占用 |
| 程序退出卡住 | 是否仍有回调或订阅线程，以及是否遗漏 `disconnect()` / `shutdown()` |
| 返回 `None` 或超时 | 运行时服务、观测开关、接口超时单位及当前客户端状态 |
