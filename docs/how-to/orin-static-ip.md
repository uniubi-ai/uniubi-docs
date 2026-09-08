# Configure a Static IP on the Robot Brain Ethernet Port

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/orin-static-ip.zh-CN.md)

## Goal and Scope

Configure a persistent static IPv4 address on the Orin brain's external Ethernet port to connect a LiDAR unit, Ethernet camera, or another network peripheral.

This guide applies to delivered systems that manage `eth0` through `/data/config/robotBrainConfig`. The fields and activation procedure follow the RobotBrain static IP configuration instructions. Confirm that the current device uses this configuration method; follow the corresponding delivery instructions for other systems.

For wiring and power, see [Connect Peripherals](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/connect-peripherals.md). This procedure configures external interface `eth0`. Do not modify the brain-to-cerebellum interface `eth0.100`.

## 1. Log In and Check the Network

Obtain a reachable device IP from the app and log in with your approved developer account. Replace the placeholders:

```bash
ssh <developer-account>@<current-device-ip>
```

Inspect interfaces and addresses:

```bash
ip -br link
ip -br addr
```

Confirm that the RJ45 port maps to `eth0` and record the peripheral IP and subnet mask. The brain and peripheral must have different, conflict-free addresses in the same subnet. Changing the wired IP may disconnect your wired SSH session. Prepare working Wi-Fi access or ensure the development host can reach the new subnet.

## 2. Back Up the Configuration

Use a session with permission to read and write the configuration file:

```bash
cp -p /data/config/robotBrainConfig /data/config/robotBrainConfig.bak
```

If that backup already exists, use a different backup filename to preserve it. If access is denied, use the administrative privileges granted with the delivered device.

## 3. Edit the Static IP Configuration

```bash
vi /data/config/robotBrainConfig
```

Locate the existing `network.master`, confirm that `enable` is `true`, and edit its `netInfo` fields. The following is only an example of the relevant fields. **Do not replace the entire file with this example.** Preserve other network settings, `priority`, `routes`, and unrelated fields.

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

| Field | Configuration |
|---|---|
| `method` | IPv4: `0` for DHCP, `1` for static IP, `2` to disable IPv4 |
| `ipv4Addr` | Static IP of the brain's external port; `192.168.10.50` in this example |
| `ipv4Mask` | Subnet mask; `255.255.255.0` in this example |
| `ipv4Gateway` | Gateway required by the delivered configuration; must be in the same subnet as `ipv4Addr` |
| `dns` | One or two DNS addresses appropriate for the actual network |
| `ipv6Method` | IPv6: `0` for DHCP, `1` for a static address, `2` to disable IPv6; the example disables IPv6 |

The RobotBrain instructions require `method`, `ipv4Addr`, `ipv4Mask`, and `ipv4Gateway` in static IPv4 mode. The configuration does not take effect if the address and gateway are in different subnets. For a direct LiDAR connection without an actual gateway, ask the device provider which gateway value this system requires instead of copying the example.

All addresses are examples and must be adapted to the actual network. Preserve other existing values when only configuring IPv4; do not change the MTU or existing IPv6 settings just to match the example.

## 4. Save and Restart

Save the file, check that the JSON is valid, and confirm that unrelated settings remain intact. Finish development tasks on the device. When the device can be restarted, follow the delivered configuration instructions:

```bash
reboot -f
```

This command forces a reboot and disconnects the SSH session. It requires the appropriate privileges on the device.

## 5. Reconnect and Verify

After startup, connect the development host to a network that can reach the new IP and log in using the configured address:

```bash
ssh <developer-account>@192.168.10.50
```

Check the address and test the peripheral:

```bash
ip -4 addr show dev eth0
ip route show dev eth0
ping -c 3 <peripheral-ip>
```

Success means that `eth0` retains the configured static address after reboot and the peripheral is reachable. Then verify data reception with the peripheral driver or application; IP reachability alone does not prove LiDAR integration. If the peripheral does not respond to ICMP, verify its actual service or driver instead.

## Troubleshooting

### A manually changed IP reverts after a while

RobotBrain manages the port configuration on this delivered system. A temporary interface address change may be overwritten when the service reapplies its configuration. Edit the configuration file described here and verify after reboot. Check that `method` is `1` and that the address, mask, and gateway meet the requirements.

### Login fails after the change

Check that the development host can reach the new subnet and that there are no address conflicts. Check the current IP in the app. Use working Wi-Fi access or the maintenance access provided with the device to inspect the configuration. To roll back, restore the backup from step 2 to the original path and restart as described in step 4.

### The IP is correct but no LiDAR data arrives

Check the LiDAR's own IP, subnet mask, destination host IP, data port, and driver settings. Configuring the brain's static IP does not automatically change peripheral settings.

## Related Guides

- [Connect Peripherals](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/connect-peripherals.md)
- [Robot Network Access](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/core-concepts/device-network.md)
