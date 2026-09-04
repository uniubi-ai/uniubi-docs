# Robot Network Access

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/core-concepts/device-network.zh-CN.md)

Before connecting to a real robot, use the device app to obtain its current 4G, Wi-Fi, and wired IP information. A development host can use the Wi-Fi IP or wired IP to log in to the device. Login accounts and authentication methods are determined by the device delivery configuration.

## Network Access

The diagram shows only the developer-facing access flow and the communication interface between the robot's brain and cerebellum. It does not represent the robot's internal network routing:

![Robot network access](https://raw.githubusercontent.com/uniubi-ai/uniubi-docs/main/docs/core-concepts/images/device-network-topology.en.png)

## Getting Device IPs from the App

| Network information in the app | Use |
|---|---|
| 4G IP | Shows the device's current 4G network information; this guide does not use it as a development-host login address |
| Wi-Fi IP | A development host can use this address to log in to the device |
| Wired IP | A development host can use this address to log in to the device |

IP addresses can change with the network currently connected to the device. Before each real-robot session, use the current values shown in the app instead of keeping an address hard-coded in scripts or configuration.

## Logging In from a Development Host

1. Confirm the current Wi-Fi IP or wired IP in the app.
2. Make sure the development host can reach the corresponding network.
3. Log in to the device using the selected IP.

Login users, keys, and passwords are determined by the device delivery configuration. Never place credentials in a public repository or example command.

## Externally Accessible Service Ports

- User services that must be reached from outside the device should use the **`20000–29999`** port range.
- Other ports are reserved for internal device services. User applications should not occupy them or assume that they are reachable from outside the device.

The port range may change with the product configuration. Follow the current device documentation and delivery configuration when deploying a service.

## Brain-to-Cerebellum Communication

Inside the robot, the brain and cerebellum communicate bidirectionally through `eth0.100`.

- When a High-level SDK or DDS program runs on the robot's brain, it must explicitly select `eth0.100` to communicate with the cerebellum.
- When a High-level program runs on an external computer, select the interface on that computer that actually reaches the robot network; do not configure `eth0.100` there.
- The real-robot Low-level SDK must still run on the robot's brain. Network reachability does not change this deployment requirement.
