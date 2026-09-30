# Repositories and documentation

Use repository names as search keys inside the user-provided workspace. Do not require every repository to be cloned for a narrow task.

| Repository | Responsibility | Start with |
| --- | --- | --- |
| [uniubi-docs](https://github.com/uniubi-ai/uniubi-docs) | Ecosystem concepts, compatibility, task guides, API reference | README, docs/how-to, docs/api-reference |
| [uniubi_robot_sdk](https://github.com/uniubi-ai/uniubi_robot_sdk) | C++ SDK and native runtime integration | README, include, examples |
| [uniubi_robot_sdk_py](https://github.com/uniubi-ai/uniubi_robot_sdk_py) | Python bindings and examples | README, examples, dependency pins |
| [uniubi_robot_msgs](https://github.com/uniubi-ai/uniubi_robot_msgs) | Shared message definitions | README and interface definitions |
| [uniubi_ros2](https://github.com/uniubi-ai/uniubi_ros2) | ROS 2 bridge, drivers, launch/configuration | README and selected package |
| [uniubi_rl_lab](https://github.com/uniubi-ai/uniubi_rl_lab) | RL tasks, training, replay and policy deployment | README, source, scripts, deploy |
| [uniubi_robot_mock](https://github.com/uniubi-ai/uniubi_robot_mock) | Mock/Sim2Sim SDK integration | README and applicable simulator guide |

Read the matching language page when present; use the task's actual source revision to resolve stale examples or differences between documents. Do not translate C++ method names into guessed Python names.

## Task-to-document map

The paths below are relative to the selected `uniubi-docs` checkout, not the installed skill folder:

| Need | Document |
| --- | --- |
| Choose firmware, runtime library and source versions | `docs/how-to/version-selection.md`, `docs/BUILD.md` |
| Network, runtime location and device identity | `docs/core-concepts/device-network.md`, `docs/core-concepts/README.md` |
| First SDK connection | `docs/how-to/sdk-first-use.md` |
| High-level / Low-level lifecycle | `docs/how-to/high-level-control.md`, `docs/how-to/low-level-control.md` |
| ROS 2 bridge | `docs/how-to/ros2-motion-bridge.md` |
| Sensors / system status | `docs/how-to/read-sensor-data.md`, `docs/how-to/query-device-status.md` |
| Media and RTSP | `docs/how-to/use-media-and-device-io.md` |
| Training and replay | `docs/how-to/train-export-replay.md` |
| SDK simulation | `docs/how-to/mock-sim2sim.md` |
| Existing failure | `docs/how-to/troubleshooting.md` |
| Language-specific API | `docs/api-reference/python/`, `docs/api-reference/cpp/` |

Chinese counterparts use `.zh-CN.md`. If no local docs are available and network access is available, use the public repository to read the needed document at a compatible tag/commit. Record the reference consulted. If compatibility or access cannot be established, say what remains unknown and use available source evidence; do not present guessed signatures or an unverified default-branch example as confirmed behavior.
