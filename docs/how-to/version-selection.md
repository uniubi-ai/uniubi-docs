# Version Selection and Upgrades

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/version-selection.zh-CN.md)

## Goal

Select firmware, SDK revisions, and deployment platform before building, and keep a reproducible version record. Start with the [compatibility table](https://github.com/uniubi-ai/uniubi-docs/blob/main/README.md#firmwaresdk-compatibility). `main` is a moving branch, not a fixed, validated release bundle.

## 1. Identify the Device and Deployment Platform

Record the complete firmware version and device model from the app's basic information, plus the application runtime location. Select libraries using the [build guide](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/BUILD.md):

| Runtime location | SDK library directory | Check |
|---|---|---|
| Robot Orin brain | `lib/aarch64/` | JetPack, Python, inference dependencies |
| External x86_64 Linux host | `lib/x86_64/` | glibc, libstdc++, Python |
| External ARM64 Linux host | `lib/aarch64_host/` | Use host libraries; do not decide from `uname -m` alone |

External ARM64 hosts and Orin may both report `aarch64` and use identical wheel platform tags. This does not make their runtime libraries interchangeable.

## 2. Select and Record Repository Revisions

Use the homepage compatibility table to select a branch or tag, then follow the relevant repository README to obtain it. Check existing workspaces for uncommitted changes. Prepare upgrades in a separate directory and preserve the working environment.

Record each repository actually used. Commits need not match across repositories, and similarly named tags do not prove that a combination has been validated:

| Component | Record |
|---|---|
| C++ SDK | Tag/branch, full commit, target library directory |
| Python SDK, if used | Tag/branch, full commit, Python version, binding/wheel provenance |
| Msgs / ROS 2, if used | Each tag/branch and full commit, ROS 2 distribution |
| Runtime libraries | Delivery source matching the headers/binding, file checksums |

Run these read-only commands inside each relevant repository:

```bash
git status --short
git rev-parse HEAD
git describe --tags --always
```

Expect a working-tree change list, a full commit, and a version description. Empty status output means no uncommitted changes. Record patches when present: a commit alone cannot reproduce them. If a required tag is missing or library provenance is unknown, confirm the corresponding delivery rather than automatically switching to the latest `main`.

## 3. Install and Validate

1. Follow the [build guide](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/BUILD.md) to match headers, libraries, and Python bindings by version and architecture. Avoid mixing another SDK through stale `PYTHONPATH` or `LD_LIBRARY_PATH` settings.
2. Complete import, connection, and read-only observation checks in [SDK First Use](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/sdk-first-use.md).
3. For ROS 2, also check messages and services using the [Motion Bridge guide](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/ros2-motion-bridge.md).
4. Record the actual results. Import, read-only observations, simulation, and hardware control are separate validation stages; only claim stages that were completed.

Keep this record with the application:

```text
Validation date:
Device model / complete firmware version:
Runtime location / OS / Python / ROS 2:
SDK / Python SDK / Msgs / ROS 2 commits:
Library directory / delivery source / checksums:
Checks performed and results:
Unverified items:
```

## 4. Upgrade and Roll Back

Read component releases/changelogs before upgrading, focusing on ABI, message fields, dependencies, and action parameters. Preserve the old version record, libraries, and application configuration. Validate the candidate environment before switching the application.

If incompatible, stop the candidate application and restore the complete previous application, binding, and runtime-library set, provided it still supports the device firmware. Firmware rollback requires its own supported procedure; switching SDK versions does not perform it. For Low-level applications, complete [shutdown and control handback](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/low-level-control.md) before switching.

[Back to How-to Guides](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/README.md)
