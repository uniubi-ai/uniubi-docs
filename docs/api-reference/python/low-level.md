# Uniubi Robot Low-level Python API Reference

**English** | [简体中文](low-level.zh-CN.md)

[API Reference](../README.md) · [C++ API](../cpp/low-level.md)

Python module: `robot_motion_sdk`
Primary client: `sdk.MotionLowLevelClient`

A real-robot Low-level Python program must run on the robot brain. Begin with read-only and zero-action checks on a safety rig with an accessible emergency stop.

## 1. Minimal Initialization and Shutdown

This example only connects and releases resources explicitly. It does not start an action:

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

> Do not rely on Python garbage collection to destroy the client. Normal exit, exceptions, and signal-driven exit must all reach `finally`.

## 2. Python API Coverage

**Global service (`sdk.service` - corresponding to `IMotionSdkService` singleton): **

| Capability / native name | Python API |
|---|---|
| `version()` | `sdk.service.version()` —— Returns the SDK version string |
| `setLogCallback` | `sdk.service.set_log_callback(cb)`; signature `(level: LogLevel, msg: str) -> None` |
| `initialService` | `sdk.service.initial(file_or_none, server_name, timeout=30)` |
| `shutdown` | `sdk.service.shutdown()` |

**LowLevel client (`sdk.MotionLowLevelClient` - corresponding to `IMotionLowLevelClient`): **

| Capability / native name | Python API |
|---|---|
| `create()` | `MotionLowLevelClient()` No-parameter structure (single device on the board) |
| `connect / disconnect` | `connect(observed_hz=500, lease_ms=0)` / `disconnect()` |
| `getState / getLastError` | `get_state()` / `get_last_error()` (return enum) |
| `setMotionEnable` | `set_motion_enable(enable)` |
| `emergencyStop` | `emergency_stop(timeout_ms=5000)` |
| `createMediaBusClient` | `create_media_bus_client()`; return `MediaBusClient` (the same client reuses the same instance, only `aarch64` on-board local media frame subscription is used; Python needs to confirm `sdk.MEDIA_ENABLED == True` first) |
| `sendControl(action[, cmd])` | `send_control(action, cmd=None)`; `action` is `sdk.MotorCtrlAction()`, and the action-related control frame is transmitted to `sdk.LowLevelMotionCmd()` and filled in `action/ac_name` |
| `sendMaxTorque(action)` | `send_max_torque(action)`; use `action.motors[i].torque` to represent the target maximum torque |
| `getLatestObservation` | `get_latest_observation(timeout_ms=5)`; return `LowLevelMotionObserved` or `None` |
| `getSensorObservation` | `get_sensor_observation(timeout_us=5000)`; return `SensorObserved` or `None` (GPS + UWB only; Walk odometry is not supported; timeout unit us, default 5000us=5ms) |
| `getMotorLayout` | `get_motor_layout(timeout_ms=5000)`; return `MotorLayout` or `None` |
| `restoreMotionControlMode` | `restore_motion_control_mode(timeout_ms=5000)`; return bool |
| `setConnectCallback` | `set_connect_callback(cb)` or decorator `@client.on_connect`; signature `(state, error)` |

The data structure `MotorCtrl / MotorCtrlAction / LowLevelMotionCmd / MotorObserved / MotorInfo / MotorLayout / IMUObserved / Vector3f / Quaternionf / PowerObserved / TRCStickFrame / LowLevelMotionObserved / SensorObserved / GPSFrame / GEOGPoint / UWBRawObserved` is all exposed as Python classes (fields are named underlined: `limb_no`, `joint_no`, `kp_gain`, `kd_gain`, `motor_num`, `charge_voltage`, `velocity_x`, etc.).

> Low-level does not support Walk odometry. An `odom` member exposed by a shared protocol structure or a particular binding build is outside the public support contract and must not be used by applications.

## 3. Exit Deadlock Avoidance

**Typical deadlock scenario**:
- Python main thread holds GIL → interpreter atexit phase starts GC
- GC destruction `client` triggers C++ destruction chain → internal `disconnect()` → waits for the SDK internal thread to end
- The SDK internal thread needs the main thread to release the GIL before it can continue during the RPC call.
- The Python callback object held by the SDK internal thread needs to be destroyed - destruction also requires GIL
- **Main thread waits for internal thread to end → internal thread waits for GIL → deadlock**

**Avoidance**:

```python
# ❌ Do not rely on GC destruction
def main():
    client = sdk.MotionLowLevelClient()
    client.connect()
    ...
    # Function returns and client enters GC — deadlock risk

# ✓ Correct: release explicitly with try/finally
def main():
    client = sdk.MotionLowLevelClient()
    try:
        client.connect()
        ...
    finally:
        client.disconnect()       # Main thread holds the GIL; the binding releases it so internal cleanup can finish
        sdk.service.shutdown()
```

**SIGINT/SIGTERM processing**: **only sets the flag** in the handler and does not make any IO/SDK calls; go after the main loop detects the flag and finally:

```python
_stop = False
def _on_signal(signum, frame):
    global _stop
    _stop = True
signal.signal(signal.SIGINT, _on_signal)
signal.signal(signal.SIGTERM, _on_signal)
```

Complete runnable example: `uniubi_robot_sdk_py/examples/example_lowlevel.py`

## 4. Python Usage Examples

Complete runnable version: `uniubi_robot_sdk_py/examples/example_lowlevel.py`

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

        # Safety prerequisites for the first hardware run:
        # - Use a safety rig, keep the emergency stop reachable, and ensure the area is clear.
        # - The zero targets, gains, and feedforward torques below form only a communication/observation template, not a standing controller;
        # - A real closed-loop controller must initialize its target from the current observed pose
        #   and use validated damping, gain, and torque policies.
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


## 5. Important Considerations

- Do not perform blocking I/O, long computations, or SDK re-entry in callbacks. Hand expensive work to an application thread.
- `robot_motion_sdk`, its native binding, and `librobotMotionSdk.so` must come from the same SDK version and target architecture.
- Every exit path must call `disconnect()` explicitly, followed by `sdk.service.shutdown()`.
- A real-robot Low-level program must run on the robot brain. Before enabling control, verify the motor layout, joint directions, emergency stop, and manual takeover.

## 6. Troubleshooting

| Symptom | Check first |
|---|---|
| `sdk.service.initial(...)` fails | Library path, SDK/binding versions, configuration file, and whether the selected interface exists |
| Client does not reach `kPrepared` | Confirm connection, a successful `set_motion_enable(True)` request, and that no other controller holds ownership |
| Process hangs during exit | Active callbacks or subscription threads, and missing `disconnect()` / `shutdown()` calls |
| API returns `None` or times out | Runtime service, observation switches, timeout units, and current client state |
