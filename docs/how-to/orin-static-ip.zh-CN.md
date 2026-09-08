# 大脑网口静态 IP 配置

[English](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/orin-static-ip.md) | **简体中文**

## 目标与适用范围

为 Orin 大脑的对外网口配置持久化静态 IPv4 地址，用于连接激光雷达、网络摄像头等外设。

本文适用于通过 `/data/config/robotBrainConfig` 管理 `eth0` 的交付系统，配置字段和生效步骤依据 RobotBrain 静态 IP 配置说明。操作前确认当前设备使用这一配置方式；其他交付系统应遵循对应的网络配置说明。

外设接线和供电见[连接外设](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/connect-peripherals.zh-CN.md)。本文配置对外接口 `eth0`，不要修改大小脑通信接口 `eth0.100`。

## 1. 登录并确认网络

从 App 获取当前可访问的设备 IP，使用已申请的开发账号登录。将以下占位符替换为实际值：

```bash
ssh <开发账号>@<设备当前IP>
```

检查网口和地址：

```bash
ip -br link
ip -br addr
```

确认 RJ45 对应 `eth0`，并记录外设的 IP 和子网掩码。大脑与外设应位于同一网段，地址不同且不与其他设备冲突。修改有线 IP 后，原有有线 SSH 连接可能断开；提前准备可用的 Wi-Fi 登录方式，或让开发机能够访问新网段。

## 2. 备份配置

在具有配置文件读写权限的会话中执行：

```bash
cp -p /data/config/robotBrainConfig /data/config/robotBrainConfig.bak
```

如果已有该备份，请先使用其他文件名保存本次备份，避免覆盖需要保留的配置。遇到权限不足时，使用交付方授予的管理权限。

## 3. 修改静态 IP 配置

```bash
vi /data/config/robotBrainConfig
```

找到现有 `network.master`，确认 `enable` 为 `true`，并修改其中的 `netInfo`。下面只是相关字段示例，**不要用它覆盖整个文件**；保留其他网络配置、`priority`、`routes` 和无关字段。

```json
{
  "network": {
    "master": {
      "enable": true,
      "mtu": 1500,
      "netInfo": {
        "method": 1,
        "ipv4Addr": "192.168.10.50",
        "ipv4Mask": "255.255.255.0",
        "ipv4Gateway": "192.168.10.1",
        "dns": ["192.168.10.1", "8.8.8.8"],
        "ipv6Method": 2
      }
    }
  }
}
```

| 字段 | 配置说明 |
|---|---|
| `method` | IPv4：`0` 为 DHCP，`1` 为静态 IP，`2` 为关闭 IPv4 |
| `ipv4Addr` | 大脑对外网口的静态 IP；示例为 `192.168.10.50` |
| `ipv4Mask` | 子网掩码；示例为 `255.255.255.0` |
| `ipv4Gateway` | 网关地址；按交付配置要求填写，必须与 `ipv4Addr` 在同一网段 |
| `dns` | DNS 地址，可配置 1 到 2 个；按现场网络填写 |
| `ipv6Method` | IPv6：`0` 为 DHCP，`1` 为静态地址，`2` 为关闭 IPv6；示例关闭 IPv6 |

按 RobotBrain 配置说明，静态 IPv4 模式必须填写 `method`、`ipv4Addr`、`ipv4Mask` 和 `ipv4Gateway`；地址与网关不在同一子网时配置不会生效。雷达直连且没有实际网关时，应由交付方确认该系统应填写的网关值，不要直接照抄示例网关。

上述地址均为示例，应根据现场网络替换。只需配置 IPv4 时，其他字段保留设备原有值；不要为了匹配示例而改变 MTU 或现有 IPv6 设置。

## 4. 保存并重启

保存文件，确认 JSON 格式正确且无关配置未被删除。结束设备上的开发任务，在允许重启设备时，按照交付配置说明执行：

```bash
reboot -f
```

该命令会强制重启，当前 SSH 会话将断开。执行需要设备授予的相应权限。

## 5. 重新连接并验证

设备启动完成后，将开发机接入可访问新 IP 的网络，使用实际配置的地址重新登录：

```bash
ssh <开发账号>@192.168.10.50
```

检查地址并测试外设：

```bash
ip -4 addr show dev eth0
ip route show dev eth0
ping -c 3 <外设IP>
```

成功标准：重启后 `eth0` 仍使用配置的静态地址，且外设网络可达。随后使用外设驱动或应用确认数据接收；IP 可达不等于雷达数据接入已经完成。若外设不响应 ICMP，应结合其实际服务或驱动验证。

## 常见问题

### 手动改完 IP，过一会又恢复

当前交付系统由 RobotBrain 管理网口配置，临时修改接口地址可能被服务重新应用的配置覆盖。应修改本文所述配置文件并完成重启验证，检查 `method` 是否为 `1`，以及地址、掩码和网关是否符合要求。

### 修改后无法重新登录

确认开发机能访问新网段、两端地址不冲突，并从 App 核对当前 IP。通过可用的 Wi-Fi 或交付方提供的维护入口登录，检查配置；需要恢复时，将第 2 步保留的备份恢复到原路径，再按第 4 步重启。

### IP 正确但无法收到雷达数据

检查雷达自身的 IP、掩码、目标主机 IP、数据端口和驱动配置。大脑侧静态 IP 配置不会自动修改外设参数。

## 相关文档

- [连接外设](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/connect-peripherals.zh-CN.md)
- [机器人网络接入](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/core-concepts/device-network.zh-CN.md)
