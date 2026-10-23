# MARBLE remote debug feasibility — 2026-10-23

Audit only, performed **after** touchinit artifact packaging succeeded. No USB,
SSH, VNC, root or physical-device changes were made. Kernel examined: source
`efb27bc77c45dca4443167dc347c0c14d1eb0ea0`, CI39903264776. Device-mode
register state and host enumeration after XNU are **not observed**; no phone
commands or new host USB trace were collected.

## USB device transport

Captured `/home/beast/marble-dump/live.dts` (SHA in MARBLE_INPUT_HW.md):
`/soc/ssusb@a600000`, compatible `qcom,dwc-usb3-msm`, wrapper range
`0x0a600000/0x100000`; child `dwc3@a600000`, `snps,dwc3`, range
`0x0a600000/0xd93c`, `dr_mode=otg`, `maximum-speed=high-speed`.
It specifies USB3_GDSC, core/interface/bus/UTMI/sleep clocks, core reset,
role-switch/extcon, eUSB2 usage, two PHY phandles and IOMMU/DMA properties.
These need MARBLE-specific resolution before writing USB hardware. Matching
SWEET's controller base does **not** make its PHY/GCC/DMA constants portable.
The Android DTS establishes hardware capability, not inherited XNU state.

Full82-patch replay and final Mach-O audit:

- `bsd/conf/files` includes `bsd/dev/sweet_usb.c`, but the entire implementation
  is gated `ARM64_BOARD_CONFIG_SWEET`. It supplies custom DWC3 EP0/bulk/CDC-ECM,
  ifnet and live logs, not Apple's normal usbmux function.
- Final MARBLE symbols contain no `sweet_usb`, `dwc3`, `AppleUSBDevice`,
  `AppleUSBDeviceMux`, or `IOUSBDevice`. KernelConfigTables has no Apple USB
  device or mux personalities. The source tree has no other USB/DWC3 driver.
- Thus this MARBLE kernel lacks both a working board USB device controller
  backend and Apple's USB device/mux service integration. Stock iOS userspace
  alone cannot supply missing controller endpoints/DMA/IOKit services.
- No evidence establishes normal-mode iOS USB enumeration on the host. ABL's
  ability to use USB before XNU does not establish enumeration after takeover.

Normal usbmux is therefore **not available in the current implementation**.
It requires board clock/power/PHY/role/DMA validation, a DWC3 device controller,
control/bulk endpoints and compatible Apple USB function/IOKit user-client
protocol (or a deliberately implemented equivalent usbmux device protocol).
Descriptor-only enumeration or CDC-ECM is insufficient to claim usbmux works.

`NOTES.md` records the stock20H392 compiled launchd list includes lockdownd;
older SWEET logs show it can crash. This audit did not remount current userdata
or establish current lockdownd liveness/pairing. Those remain runtime checks,
including launchd activation, lockdown socket, trust/pairing and relevant
usbmux service availability. Host `usbmuxd`/`iproxy` is not a replacement for the
missing device-side transport. See [primary libusbmuxd documentation](https://github.com/libimobiledevice/libusbmuxd).

## SSH target

Feasible after a usable network transport exists. Stock root has not been
augmented with a debug SSH daemon in this task; no current sshd is claimed.
Build/sign a compatible arm64 iOS OpenSSH or Dropbear plus its actual dylib
closure, unique host keys, authorized public keys, private writable state and
an explicit debug-only launchd enable. Disable password/root-password login;
never distribute a known/default password. Validate launchd execution and
local TCP22 independently before testing transport forwarding.

Desired usbmux host flow, **future design, not currently functional**:

```sh
iproxy 2222:22
ssh -p 2222 root@localhost
```

A MARBLE port of SWEET's CDC-ECM transport could provide a simpler first debug
network and SSH directly to a USB network address. That is an alternative to
normal usbmux; it does not make iproxy work. It needs its own source-backed
SM7475 PHY/GCC/IOMMU/DMA bring-up, so is not included in the touch image.

## TrollVNC target

Primary reference is current [owngoal-dev/TrollVNC](https://github.com/owngoal-dev/TrollVNC),
resolved2026-10-23 to `cfdb737e72977d961eb7d0a8110d2fe1a58551d7`,
Makefile version3.2-272. No Veency-based assumptions.

Examined pinned [Makefile](https://github.com/owngoal-dev/TrollVNC/blob/cfdb737e72977d961eb7d0a8110d2fe1a58551d7/Makefile),
[ScreenCapturer.mm](https://github.com/owngoal-dev/TrollVNC/blob/cfdb737e72977d961eb7d0a8110d2fe1a58551d7/src/ScreenCapturer.mm),
[STHIDEventGenerator.mm](https://github.com/owngoal-dev/TrollVNC/blob/cfdb737e72977d961eb7d0a8110d2fe1a58551d7/src/STHIDEventGenerator.mm),
and [server entitlements](https://github.com/owngoal-dev/TrollVNC/blob/cfdb737e72977d961eb7d0a8110d2fe1a58551d7/src/trollvncserver.entitlements).

- Build targets arm64 and iOS minimum14 (legacy)/15 (alternate scheme), so
  iOS16.7.16 meets deployment-target requirements. This is not proof that all
  private runtime APIs work on this custom kernel/root.
- Device capture gets `_unjailedReferenceBoundsInPixels`, allocates BGRA
  IOSurfaces, uses `CARenderServerGetDirtyFrameCount` and
  `CARenderServerRenderDisplay("LCD")`, then
  `IOSurfaceAcceleratorCreate/GetRunLoopSource/TransferSurface`. The simulator
  path skips accelerator transfer; that is not the normal device path.
- Current SweetSurface implements basic create/lookup/map/lock/port operations
  needed for the GUI, but source personalities and final MARBLE symbols have
  **no IOSurfaceAccelerator / IOSurfaceAcceleratorClient**. This is a concrete
  missing kernel service required by the unmodified device capture path.
  Successful AppleCLCD presentation does not prove this accelerator exists.
  Unchanged TrollVNC capture is therefore not established and is expected to
  need adaptation. A future CPU-copy capture path could avoid that requirement
  after proving CARenderServer capture succeeds; do not redesign the working
  display or enable a GPU merely for VNC. No direct IOMobileFramebuffer screen
  read is used in the examined capture path.
- Input uses `IOHIDEventSystemClientCreate/DispatchEvent` with private event
  creation APIs and sender metadata, rather than calling marble_hid_touch.
  Backboard's daemon/client dispatch, entitlements and gesture handling need
  independent runtime validation; the synthetic kernel HID test does not
  establish this userspace injection route.
- Requires linked Accelerate, CoreGraphics/CoreMedia/CoreVideo, Foundation,
  IOKit, IOSurface, QuartzCore, UIKit, UserNotifications, FrontBoardServices,
  Preferences, and the built libvncserver/crypto/SSL/lzo2/turbojpeg/png18/sasl2/z
  dependency closure (static versus dynamic packaging must be inspected).
  Its entitlement file includes platform-application, global/secure QuartzCore
  capture, private HID dispatch/manager, protected IOSurface and specific IOKit
  user-client access. Preserve least required privileges when making a later
  debug package; do not assume arbitrary entitlements alone supply kernel APIs.

Future VNC target explicitly configures server port5900 (upstream default is
5901), then host `iproxy 5900:5900`, client `localhost:5900`. Keep debug opt-in
and authenticate/restrict listeners. No server installed or launched here.

## Recommended implementation order

1. Finish physical touch testing with the dedicated touchinit image.
2. Separate USB project: bounded MARBLE power/clock/PHY/role/DMA state probe;
   then EP0 enumeration and safe bulk transfers with exact board sources.
3. Choose transport explicitly: CDC-ECM for a first debug IP link, or implement
   and validate the full normal usbmux contract. Confirm host enumeration and
   endpoint behavior; then test host forwarding and stock service state.
4. Add debug-only key-authenticated SSH, with local daemon/dependency testing.
5. Run a small IOSurface/CARenderServer capture and userspace HID-dispatch probe;
   adapt TrollVNC's missing accelerator path in userspace if needed, then test
   view-only VNC before remote touch/gestures. Keep GUI/kernel behavior stable.
