# Connect USB and Ethernet Peripherals

**English** | [简体中文](connect-peripherals.zh-CN.md)

## Goal

Connect a USB or Ethernet peripheral to the robot compute module (the “brain”), then verify that the operating system can reach it.

This guide applies to the Creator version. It describes external peripheral connectivity only; it does not change the control path between the robot brain and motion-control subsystem (the “cerebellum”).

## Interface Boundaries

| Interface | Connected to | Intended use |
|---|---|---|
| `USB-EXT` Type-C | Robot brain | USB cameras, sensors, storage devices, and other supported USB peripherals |
| `USB-BASE` Type-C | Motion-control subsystem | Reserved for the cerebellum; do not use it as a robot-brain peripheral port |
| RJ45 Ethernet | Robot brain | Ethernet cameras, LiDAR units, and other network peripherals |

The two Type-C connectors look similar, but only the connector marked `USB-EXT` is available to applications running on the robot brain. Identify the connector by its PCB silkscreen, not by connector position alone.

## 1. Connect a USB Peripheral

1. Power off the peripheral if its installation procedure requires it.
2. Locate the Type-C connector whose PCB silkscreen reads `USB-EXT`.
3. Connect the peripheral to `USB-EXT`. Do not connect it to `USB-BASE`.
4. On the robot brain, inspect USB enumeration:

   ```bash
   lsusb
   ```

5. If the device does not appear, inspect recent kernel messages and verify its cable, power requirement, and Linux driver support:

   ```bash
   dmesg | tail -n 50
   ```

Success means that the expected device appears in USB enumeration and its application-facing device node or driver is available.

## 2. Connect an Ethernet Peripheral

The robot brain does not currently run a DHCP server on the external Ethernet connection. Connecting a cable therefore does not automatically assign an IP address to the peripheral.

Before testing connectivity:

1. Determine the peripheral's configured IP address and subnet prefix.
2. Identify the robot-brain network interface connected to the RJ45 port:

   ```bash
   ip -br link
   ip -br addr
   ```

3. Configure a static IP address for the robot-brain interface in the same subnet as the peripheral.
4. Ensure that the two addresses are different and do not conflict with another device.
5. If the peripheral address is configurable, configure both endpoints consistently. Follow the network-management method supplied with the delivered system when making the robot-brain configuration persistent.
6. Verify reachability:

   ```bash
   ping -c 3 <peripheral-ip>
   ```

Do not copy an interface name or IP address from another robot without checking the current device. Network-interface names and delivered network settings may differ.

Success means that the robot brain has an address in the peripheral's subnet and can reach the peripheral's IP address without an address conflict.

## 3. Troubleshooting

### The USB peripheral is not visible on the robot brain

- Confirm that the cable is connected to `USB-EXT`, not `USB-BASE`.
- Check whether the peripheral requires separate power.
- Check USB enumeration, kernel messages, and driver support.

### Ethernet link is present but the peripheral is unreachable

- Confirm that both endpoints use static IP addresses in the same subnet.
- Confirm that the addresses are different.
- Recheck the selected robot-brain network interface.
- Check the peripheral's subnet mask, service port, firewall, and service listening address.

### The peripheral is reachable but the application cannot open it

Network or USB reachability proves only the transport path. Continue by checking device permissions, the required driver or runtime library, and application-specific configuration.

## Next Steps

- For robot login addresses and externally accessible service ports, see [Robot Network Access](../core-concepts/device-network.md).
- For camera-frame access through the Uniubi SDK, see the [Media API](../api-reference/README.md).
- For a ROS 2 application, continue with [Start and Validate Motion Bridge](ros2-motion-bridge.md) or the relevant device driver.
