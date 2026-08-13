# Device Network and Robot Compute Module Access

**English** | [简体中文](device-network.zh-CN.md)

A Uniubi robot includes a cerebellum (motion controller) for standard functions such as core motion control, remote-controller input, and UWB, plus a brain (compute module) that provides greater general-purpose compute for extension applications. See [Brain and Cerebellum](README.md#1-brain-and-cerebellum) for the full responsibility boundary. Accessing the compute module works essentially the same over wireless and wired connections; the difference is that the compute module can also have its own IP address when wired.

## Network Topology

| Connection | Available address | Notes |
|---|---|---|
| Wireless | Motion-controller IP shown in the app | Access to the compute module is bridged through the motion controller |
| Wired | Motion-controller IP shown in the app, or the compute module's own wired IP | Access operations stay the same; the compute module's independent IP is also available |

## Wireless Connection

The compute module does not expose an independent wireless IP. When the robot is connected over Wi-Fi, the app displays the motion-controller IP, and only selected compute-module ports are reachable through that address.

- Use the device's exposed **20000–29999** port range for services that must be reached over the wireless bridge.
- Do not assume that every listening port on the compute module is reachable over Wi-Fi.
- SSH access to the compute module is bridged through the motion controller. Use the IP displayed in the app as the SSH address.

SSH users, keys, and passwords are determined by the device delivery configuration. Never place credentials in a public repository or example command.

## Wired Connection

On a wired network, the compute module can obtain its own IP address, giving the development machine an additional address for direct access. Operations such as SSH and service access are essentially the same as with a wireless connection.

If the wired IP is unknown, first SSH through the motion-controller IP shown in the app, then run this command on the compute module:

```bash
ip -br -4 addr
```

Use the IPv4 address of the active wired interface. Both the motion-controller IP displayed in the app and the compute module's wired IP can serve as access points, but they are different addresses.

## Choosing an Address During Development

- When reaching a compute-module service through the motion-controller IP shown in the app, use a port in the device's exposed `20000–29999` range.
- With a wired connection, either keep using the existing access point or use the compute module's independent IP; the application-level operations do not change.
- When an SDK or DDS program requires an explicit network interface, select the interface that actually reaches the robot. Use `ip -br addr` to determine its name.
