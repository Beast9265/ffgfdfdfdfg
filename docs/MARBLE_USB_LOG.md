# MARBLE USB CDC-ECM live console — 2026-10-23

USB-only local checkpoint precedes functional touch changes. Physical USB
results are pending. This ports the final SWEET0072–0077 implementation;
Apple usbmux, SSH and VNC are not implemented. No root change or storage log.
The previous touchinit image was physically tested and touch still failed;
its first refusing gate is unknown because framebuffer output scrolled away.

## Hardware provenance

Local captured live.dts SHA256 and Android evidence are recorded in
MARBLE_INPUT_HW.md. Additional primary sources are pinned, never copied from
SWEET's hardware definitions:

- [Linux MARBLE DTS](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/arch/arm64/boot/dts/qcom/sm8475-xiaomi-marble.dts),
  [SM8450 base DTS](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/arch/arm64/boot/dts/qcom/sm8450.dtsi)
  and [GCC](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/drivers/clk/qcom/gcc-sm8450.c).
- [U-Boot board config](https://github.com/iLtanaka/u-boot-marble/blob/4e1c8502a39213eca383b11bdb716749c2953d76/board/qualcomm/xiaomi-marble.config),
  [board environment](https://github.com/iLtanaka/u-boot-marble/blob/4e1c8502a39213eca383b11bdb716749c2953d76/board/qualcomm/xiaomi-marble.env),
  [DTS](https://github.com/iLtanaka/u-boot-marble/blob/4e1c8502a39213eca383b11bdb716749c2953d76/dts/upstream/src/arm64/qcom/sm8475-xiaomi-marble.dts),
  [Qualcomm gadget glue](https://github.com/iLtanaka/u-boot-marble/blob/4e1c8502a39213eca383b11bdb716749c2953d76/drivers/usb/dwc3/dwc3-generic.c).
  Config explicitly enables gadget/ACM/ACM_NOWAIT and menu serial_on uses
  usbacm. It also notes the one-gadget-slot conflict with fastboot/UMS.
- [Linux wrapper](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/drivers/usb/dwc3/dwc3-qcom.c),
  [DWC3 registers](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/drivers/usb/dwc3/core.h),
  [SMMU registers](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/drivers/iommu/arm/arm-smmu/arm-smmu.h).

| Resource | MARBLE value |
|---|---|
| DWC3 | 0x0a600000; core register window mapped0xd000 |
| QSCRATCH | core+0xf8800 =0x0a6f8800 |
| GCC | 0x00100000, mapped0xa0000 to include CLKREF |
| USB30_PRIM GDSCR | GCC+0x49004, power-on bit31 |
| master / sleep / mock UTMI branch | 0x49018 /0x49020 /0x49024 |
| cfg-NoC / aggregate AXI branch | 0x49084 /0x49088 |
| CLKREF | 0x9c010 |
| HS PHY | eUSB2@0x088e3000; **not SWEET QUSB2** |
| repeater | NXP PTN3222 I2C@0x4f, PM8350C GPIO7 reset |
| USB DMA | apps-SMMUv2@0x15000000, stream ID0 |

Captured Android uses qcom,usb-snps-eusb2-phy and nxp,eusb2-repeater; Linux
binds PTN3222 and uses the eUSB2 PHY provider. The driver deliberately inherits
ABL's PHY/repeater: no PHY reset, repeater I2C, PMIC or clock programming.
GCC is read-only. Only powered/running master/sleep/UTMI/cfg/aggregate clocks,
DWC3 identity0x5533xxxx and port capability DEVICE allow gadget startup.
If they are unavailable, stop before unsafe gated register accesses. This
build cannot promise USB starts without the first physical hardware result.

Direct physical DMA is **not assumed** from successful UFS. Before controller
reset/endpoints, read bounded SMMUv2 CR0/ID0 and stream0 SMR/S2CR matches:
CLIENTPD with bypass, an explicit unique BYPASS stream, or unmatched/default
bypass are accepted. Translation, FAULT, duplicate mappings, unreadable identity
and unsupported geometry refuse. No SMMU writes or borrowed address mapping.
DWC3 AWIDTH must cover the allocated contiguous16KiB area. Firmware-owned event
buffers are replaced only after this check and a completed device soft reset.
Caches use the proven physical-address flush/invalidate operations. Runtime
SMMU mode and DMA/PHY state remain unknown until tested; a refusal may itself
prevent USB output and will require a separate source-backed USB fix.

## Shared implementation and safety

Final SWEET descriptors/EP0 state machine, bulk OUT0x01/IN0x81, interrupt IN0x82,
512-byte high-speed bulk, cluster-mbuf RX and32-frame TX queue are reused.
MARBLE manufacturer/product are ios-marble / Marble iOS USB debug; test
VID:PID1209:0001 and host MAC02:00:5e:77:ee:01 remain. Phone ue0 gets
192.168.7.2/24 in-kernel; no configd/root preference is needed for local UDP.

A MARBLE worker starts15s after successful root mounting, outside UFS code and
before the60s touch probe. Defaults are marbleusb=0, marbleusblog=1; dedicated
image passes marbleusb=2 marbleusblog=1. marbleusb=1 is read-only probe.
DWC3 core reset/endpoint commands/events follow mature SWEET; both reset waits
are bounded500ms with sleep on MARBLE. Endpoint commands are bounded1ms.
Polled event counts must be aligned and <=4KiB or the MARBLE worker stops.
QSCRATCH VBUS override sets HS+0x10 bits20/28 and SS+0x30 bit24, preserving
other bits. No firmware, PHY, GIC or SMMU reprogramming.

Only the existing4MiB **RAM ring** and sweet_log_append/copy/position are
shared with MARBLE. _cnputs captures before normal console output. Persistent
writer/start/header remain SWEET-only, absent from the MARBLE object; UFS
submission/read/write/root policy bodies are unchanged. Console mute stays
SWEET-only. Non-MARBLE preprocessed tokens match with __LINE__ normalized and
adjacent C string literals folded (normal C translation phase6).

The USB log thread never prints. It sends1400-byte UDP datagrams to
192.168.7.1:5140 every100ms, starting with the previous64KiB. MARBLE waits for
an ARP from the host's assigned IPv4 address before consuming backlog; advances
only on successful complete socket send, and limits each wake to8 chunks
(11200bytes), below the32-frame TX queue. RAM retention remains4MiB, so a host
that waits too long can lose overwritten history. UDP is best effort, not an
acknowledged archival transport. Start the host receiver promptly.

## Manual host use

Linux requires cdc_ether, Python3, iproute2 and root for interface configuration;
NetworkManager and iputils ping are optional. Allow inbound UDP5140 on this
interface in the host firewall. The script does not alter firewall rules.
No DHCP, NAT, Internet connectivity, usbmux, SSH or VNC is required.

`tools/marble-usbnet.sh` binds UDP5140 **before** waiting/configuring the link,
selects by exact manufacturer/product plus MAC (rejects multiple matches),
temporarily stops NetworkManager managing only that interface, assigns
192.168.7.1/24 and raises it. An outgoing harmless UDP probe triggers ARP;
optional --ping checks the link. Received phone data is printed and appended
to the requested file. Stop with Ctrl-C. There is no automatic phone action.

```sh
sudo ~/ios-marble/tools/marble-usbnet.sh --ping \
  ~/ios-marble/logs/marble-touch-live.txt
```

It can be started before the manual phone boot. Expected **pending physical**
logs: MARBLE USB connected, ECM endpoints configured, ue0 address up, then
full touch startup and refusal/probe text. No USB success is claimed yet.

Local USB checkpoint: full82-patch replay/source equality, four real-CI-header
arm64 compiles, symbol closure,12 non-MARBLE equivalence checks, ASan/UBSan
CDC descriptors/strings, RAM ring wrap, SMMU bypass/translation/fault/duplicate/
EXID tests; logger bounds/no-print assertions; host shell/embedded Python
syntax. No host interface configuration or phone commands were executed.

## USB-only checkpoint packaged

Source `cdc38016c5522fff9c6917c97bb29b15022bcfe9`, [CI39907701061 success](https://github.com/Beast9265/ios-marble/actions/runs/39907701061).
Kernel `c4a96d7cdfda215069f1dce8168ebd8dd02a6f0516b22e6e43ca3e24db0c42f9`; exact Hello ADT `35f0bff762c339e86a0e67392267ed148ae06b24703b682ce2327c9296ed84e3`.
Payload `ae83421e07a79f82ca1f07d6e7902a60337471b1e418a8a0ab6ec89af358f8a4`.
Boot `latest-marble-xnu-usblog.img`: `68b47e27a79339f3f707ee3f96a2362d05d457302077b0cedbf19e2f34f4fdb3`.
This standalone checkpoint was built/packaged before functional touch edits.
It uses marbleusb=2 marbleusblog=1 marbletouch=0; buttons remain enabled and
synthetic injection off. Exact artifact/full-link/bootstrap/footer/wrapper
checks pass, all prior images preserved. Physical USB remains UNTESTED.

## Final combined USB-log + Linux SPI checkpoint — manual test pending

Kernel source `3dedd6976ddacdab275db0c984219d32bf7ed0a0`, [CI39908684058 SUCCESS](https://github.com/Beast9265/ios-marble/actions/runs/39908684058),
exact headSha independently verified. USB-only checkpoint remains from
cdc38016c5522fff9c6917c97bb29b15022bcfe9 / successful CI39907701061.

| Artifact | SHA256 |
|---|---|
| Kernel | `387e16ac712f728224604c5fe53456fe281d236e6edb9603f398de728b0a35bd` |
| Exact Hello ADT | `35f0bff762c339e86a0e67392267ed148ae06b24703b682ce2327c9296ed84e3` |
| marble-xnu-touch-usblog.payload | `12524e89b6a9180b2d34602cefe4095d8d119ef03c320ef89f9ae6f749741b3d` |
| latest-marble-xnu-touch-usblog.img | `d68c7b333aee6ac9bf75927346cae9514834a5e05d9835cf18a1f32d1dc7d9eb` |

Command line (no synthetic injection):

```text
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 ufsrw=1 rootrw=1 launchd_unsecure_cache=1 marbleguidiag=1 marbleusb=2 marbleusblog=1 marbletouchinit=1
```

Fresh exact CI artifact SHA256SUMS, arm64/full link zero undefined, payload
segment/fixup equality, boot-v4 metadata/padding/footer/content, bootstrap
capacity/aliases/stacks/tables, timer scan and linked HID personalities pass.
Linked USB init/RAM-log hooks and diagnostics present; SWEET persistent disk
writer/start absent. Five preserved images rehashed unchanged: Hello rollback,
normal physical-input, hidtest, touchinit and USB-only checkpoint.
setup-fast raw7ca8c990...22798 and sparsecec3daf0...4aa01 were rehashed unchanged.
No root image generated/mounted/modified, retention cleanup, SSH/VNC install,
fastboot/adb or other phone commands. No SMP, display, identity, key/HID, AKS,
sandbox or UFS hardware/read/write/root policy changes. UFS file changes are
only shared RAM-ring guards; persistent writer remains SWEET-only.

USB enumeration/CDC-ECM/UDP and corrected physical touch are **UNTESTED**.
Actual GPIO before/after, IF_DISABLE_RO/FIFO_IF_DISABLE/DMA_MODE_EN and first
physical failure remain UNKNOWN. FIFO is selected only if enabled/idle. If
disabled, stop names GPI/SID5b6 ownership/IOVA dependency; no unsafe GPI or
SMMU workaround. USB itself also requires validated inherited clocks/device
mode/direct-DMA bypass and refuses otherwise; UDP transport is best effort.

Manual combined test (host receiver may be started before boot):

```sh
fastboot boot \
  ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu-touch-usblog.img
sudo ~/ios-marble/tools/marble-usbnet.sh \
  ~/ios-marble/logs/marble-touch-live.txt
```

Expected next evidence: connected/ECM/ue0 USB messages in the saved log,
then complete touch mode/power/reset/confirm/version/IC-info/polling gates.
If probing succeeds, tap(i) then physical bottom-edge swipe. Send the log;
no physical success or exact prior blocker is claimed by this build.
