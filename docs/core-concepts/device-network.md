# Device Network and Robot Compute Module Access

**English** | [简体中文](device-network.zh-CN.md)

A Uniubi robot includes a motion controller and a robot compute module on which developer applications run. Access to the compute module differs between wireless and wired connections.

## Network Topology

| Connection | Externally visible address | Compute-module access |
|---|---|---|
| Wireless | Motion-controller IP shown in the app | The compute module has no separately reachable wireless IP; access is bridged through the motion controller |
| Wired | Compute module's wired IP | Connect directly to the compute module's wired address |

## Wireless Connection

The compute module does not expose an independent wireless IP. When the robot is connected over Wi-Fi, the app displays the motion-controller IP, and only selected compute-module ports are reachable through that address.

- Use the device's exposed **20000–29999** port range for services that must be reached over the wireless bridge.
- Do not assume that every listening port on the compute module is reachable over Wi-Fi.
- SSH access to the compute module is bridged through the motion controller. Use the IP displayed in the app as the SSH address.

SSH users, keys, and passwords are determined by the device delivery configuration. Never place credentials in a public repository or example command.

## Wired Connection

On a wired network, the compute module obtains its own IP address. The development machine can connect directly to that address without the wireless bridge's application-port restriction.

If the wired IP is unknown, first SSH through the motion-controller IP shown in the app, then run this command on the compute module:

```bash
ip -br -4 addr
```

Use the IPv4 address of the active wired interface. Do not confuse the motion-controller IP displayed in the app with the compute module's wired IP.

## Choosing a Connection During Development

- For a service hosted on the compute module and reached over the robot's wireless connection, use a port in the `20000–29999` range.
- Prefer the wired connection for unrestricted port access, large transfers, or network troubleshooting.
- When an SDK or DDS program requires an explicit network interface, select the interface that actually reaches the robot. Use `ip -br addr` to determine its name.
