# ios-a71

**Porting Apple's XNU/iOS userland to a Samsung Galaxy A71 (SM-A715F).**

This is a fork of [dipa-studio/ios-sweet](https://github.com/dipa-studio/ios-sweet), which ports Apple's open-source XNU kernel (xnu-8796, the iOS 16 generation) and the unmodified **iOS 16.7.16 (20H392) iPhone X userland** to the Xiaomi Redmi Note 10 Pro (codename `sweet`, Qualcomm SM7150 / Snapdragon 732G). That upstream project boots all the way to the iOS home screen on its target device - see its README for that status.

This fork retargets the same kernel at the **Samsung Galaxy A71** (`SM-A715F`, Snapdragon 730, same `sdmmagpie`/SM7150 chip family). Comparing both devices' real device trees found exact address matches on UFS, GIC, the splash framebuffer, and even touch/button GPIO pin numbers - strong evidence this is a board variant of the same reference silicon rather than a cross-SoC port.

> Experimental, unfinished, **not yet booted on real A71 hardware**. See "A71 status" below for exactly what is and isn't done.

## A71 status (this fork)

- **Kernel**: builds clean via CI (`.github/workflows/xnu.yml`, `MACHINE_CONFIG=A71`), passed a generic QEMU smoke-test boot (no panic). No A71-specific kernel changes were needed at the CPU/GIC/UFS/PMIC level - those addresses already matched upstream's exactly.
- **Touch**: a new driver (`xnu/patches/0082-a71-st-fts-touch.patch`) for A71's actual touch IC (STMicroelectronics FTS5CU56A, not the Goodix/Focaltech chips upstream supports) - protocol decoded from Samsung's own GPL-published kernel source for this exact chip. **Untested on hardware.**
- **Display**: genuinely unsolved. A71's panel is DSI *command* mode; upstream's entire display trick (CPU writes pixels into the ABL splash buffer, hardware free-runs, zero driver code) only works on *video* mode panels like the Redmi's. A read-only diagnostic (`xnu/patches/0083-a71-display-autorefresh-probe.patch`) is in place to tell us, on first real boot, whether hardware autorefresh can substitute - no real display driver exists yet.
- **Boot image**: built and structurally verified (`shim/out/shim-boot.img` - gitignored, build it yourself per the steps below).
- **Bootloader**: unlocked (`OEM LOCK: OFF` confirmed via Download Mode).
- **Flashing**: blocked, not on the phone side but on tooling - Samsung has no `fastboot boot` equivalent, only Odin's proprietary protocol, and neither native macOS nor a QEMU-passthrough Linux VM could get heimdall (open-source Odin-protocol client) past its USB handshake on this host. A real Linux machine or Windows+Odin would likely work; this specific dev machine could not.

## What works (upstream, Redmi Note 10 Pro)

| Area | State |
| --- | --- |
| Boot | Stock Xiaomi bootloader → `fastboot boot` of our shim → XNU. Nothing is flashed to the boot partitions |
| CPU | 6 of the 8 cores (the six Cortex-A55s) via PSCI, 16K pages, GICv3 interrupts, timers |
| Memory | About 3.95 GiB of the upper DDR bank |
| Storage | Own UFS host driver; the iOS root is a journaled HFS+ volume in `userdata`, read/write |
| iOS userland | Real iPhone X 16.7.16 root filesystem and shared cache; launchd and the system daemons run |
| Display | Kernel IOSurface + IOMobileFramebuffer (`AppleCLCD`) services; CoreAnimation renders in software; frames are copied into the bootloader's framebuffer. Presented to iOS as an iPhone X panel (1125×2436) |
| GUI | backboardd, SpringBoard, lock screen, home screen, Control Center, notification center, Settings |
| Touch | Goodix GT9896 over I²C (GENI), rail enabled through RPMh, delivered as HID digitizer events |
| Buttons | Power, volume up/down (PMIC through SPMI) as HID consumer keys; lock/wake works |
| Battery | IOPMPowerSource service (static 100 %, charging icon; real fuel-gauge readout prepared) |
| Device identity | iPhone X (`iPhone10,3` / `D22AP`): no Home button, gesture UI |
| Activation | Native "Hactivation" path of mobileactivationd, chosen through device-tree security status. No Apple servers involved |

## What does not work (yet)

- **Navigation:** you cannot leave an app (the home gesture and AssistiveTouch Home do nothing yet).
- **No Wi-Fi, Bluetooth, cellular, audio, camera, sensors, GPS or SEP / Face ID.** Daemons for them start and fail or keep relaunching.
- **No GPU.** Everything is drawn by the CPU at roughly 20–30 fps. The two Cortex-A76 cores are not used yet.
- **Few apps.** The image has only what is on the system volume. There is no App Store, no Apple ID, and some Settings pages are empty.
- **Slow boot:** about 4 minutes on the Apple logo.
- **Security is off:** permissive code signing (AMFI) and sandbox policies, a stub AppleKeyStore, no data protection. Do not put anything personal on it.

## How it boots

Upstream, on the Redmi (stock Xiaomi bootloader, has `fastboot boot`):

```
ABL (stock Xiaomi bootloader, unlocked)
  -> fastboot boot shim-boot.img              (temporary; nothing is flashed to boot)
     -> shim: own MMU setup, reads the live FDT, loads the payload from the ramdisk
        -> XNU Mach-O + generated Apple Device Tree (ADT) + boot-args
           -> XNU -> UFS driver -> HFS+ root in the userdata partition
              -> dyld + shared cache -> launchd -> daemons -> backboardd + SpringBoard
```

On the A71, there is no `fastboot boot` - Samsung only has Odin's protocol over USB, which flashes a partition for real rather than booting a disposable image. The notes (`A71-NOTES.md`, one directory up) track which partition-flash strategy (`recovery` vs `boot`) is actually safest; nothing has been flashed yet.

There is no serial port (the debug UART is wired as SPI on this board - true for both devices, same SoC). The kernel draws its console into the framebuffer that ABL leaves at `0x9c000000`, and keeps a persistent 4 MiB log ring at the end of `userdata`. You read that log from OrangeFox recovery with `tools/a71-log-pull.sh`, so you don't have to film the screen.

## How to do it yourself (upstream steps - A71 flashing differs, see above)

You need a Redmi Note 10 Pro (`sweet`, global or Indian variant, SM7150) with an **unlocked bootloader**, a Linux PC, and a GitHub account for the kernel build. This is the exact path upstream used for their screenshots; other variants or firmware may need changes. **Everything on `userdata` is lost.** Bootloaders, recovery, modem and persist partitions are never touched.

### 0. Back up the phone

Boot OrangeFox (or any recovery with adb root) temporarily and pull at least `persist`, `modemst1`, `modemst2`, `fsg`, `fsc` and `boot`, `dtbo`, `vbmeta`. They contain per-device calibration data. Keep them off git; `.gitignore` already excludes `backup/`, `dtb/` and `recovery/`.

The shim needs the stock DTB. Unpack your phone's stock `boot.img`:

```sh
python3 tools/unpack_bootv2.py backup/boot.img dtb/boot_unpacked   # -> dtb/boot_unpacked/dtb
```

### 1. Build the kernel

The kernel builds on GitHub's macOS runners with [blacktop/darwin-xnu-build](https://github.com/blacktop/darwin-xnu-build). The workflow fetches xnu-8796, applies `xnu/patches/` in order, and also stages the pinned open-source libpthread, HFS and BearSSL sources it needs. Fork the repo (public repos get free macOS minutes) and run:

```sh
gh workflow run xnu.yml -R YOU/ios-a71
gh run download RUN_ID -R YOU/ios-a71 -n xnu-kernel -D xnu/out
```

To check a patch locally before spending a CI run, `tools/xnu-cc.py` replays the compile commands of a previous CI log for single files.

### 2. Build the iOS root image

Download the iPhone X (iPhone10,3) iOS 16.7.16 (20H392) IPSW from Apple. Then, on Linux, with `apfs-fuse`, `hfsprogs` and sudo:

```sh
# OS, SystemOS and AppOS disk images from the IPSW (see BuildManifest.plist for their names)
tools/mkiosroot.sh OS.dmg SystemOS.dmg AppOS.dmg ios16-root.img 16G
sudo fsck.hfsplus -fy ios16-root.img
sudo mount -t hfsplus -o loop,force ios16-root.img /mnt/iosroot
sudo python3 tools/a71-root-tweaks.py /mnt/iosroot
sudo umount /mnt/iosroot
img2simg ios16-root.img ios16-root.simg
```

`mkiosroot.sh` copies the OS volume and both cryptexes into one case-sensitive journaled HFS+ volume. It adds the dyld cache links, the plain system keybag and the log directories the daemons expect. `a71-root-tweaks.py` applies the bring-up changes: it skips Setup, seeds the activation state, removes the baseband daemon, disables the watchdogs that kill slow apps and the crash-looping media paths, and so on. The script's header explains each change.

The device tree builder copies `/product` from the real iPhone X device tree, which MobileGestalt needs. Extract it once, without downloading the whole IPSW:

```sh
python3 tools/remotezip.py IPSW_URL DeviceTree.d22ap.im4p research/ipsw-x/dt
ipsw img4 im4p extract research/ipsw-x/dt/Firmware/all_flash/DeviceTree.d22ap.im4p -o research/ipsw-x/d22ap.adt
```

### 3. Build the boot image

Needs `aarch64-linux-gnu-gcc` and `mkbootimg`.

```sh
python3 tools/mkadt.py shim/out/a71.adt --highmem
python3 tools/mkpayload.py xnu/out/kernel.development.a71 shim/out/a71.adt shim/out/payload.bin \
    --cmdline 'debug=0xc serial=3 cpus=6 keepsyms=1 -enable_kprintf_spam -noprogress rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 wdt_test=no_user_checkin ufsrw=1 rootrw=1 launchd_unsecure_cache=1 wdt=-1 a71fb_noconsole=1 a71fb_hz=30'
shim/build.sh ../shim/out/payload.bin      # -> shim/out/shim-boot.img
```

What the less obvious boot-args do:

| Boot-arg | Effect |
| --- | --- |
| `rd=ufsroot0 ufsrw=1 rootrw=1` | Root on the `userdata` partition, writable |
| `cpus=6` | Start the six A55 cores; `cpus=1` is the safe fallback |
| `launchd_unsecure_cache=1` | launchd accepts its job cache without AMFI |
| `wdt=-1 wdt_test=no_user_checkin` | No hardware watchdog |
| `a71fb_noconsole=1` | Stop drawing kernel text over the GUI. It still goes to the persistent log; panics are drawn |
| `a71fb_hz=30` | Panel refresh rate of the CPU copy |
| `a71touch=0`, `a71keys=0` | Disable the touch or button driver |

### 4. Flash the root and boot

Upstream (Redmi, has `fastboot boot`):

```sh
fastboot -S 512M flash userdata ios16-root.simg   # ~7 minutes; do not unplug
# Xiaomi's fastboot often hangs after a large flash: re-enter fastboot with Power + Volume down
fastboot boot shim/out/shim-boot.img
```

On A71 this step is different and still unresolved - no `fastboot boot`, only Odin's protocol, which this fork has not yet gotten a working client for (heimdall's USB handshake failed both natively on macOS and through a QEMU-passthrough Linux VM on this dev machine; untried: a real Linux box, or Windows with actual Odin). See `A71-NOTES.md` for the partition-choice tradeoff once a working flashing path exists.

The first boot takes about 4–5 minutes on the Apple logo, then the lock screen appears. Swipe up to unlock. To get back to fastboot, hold Power + Volume down.

### 5. Read the kernel log

```sh
fastboot boot recovery/recovery.img        # OrangeFox, temporary
tools/a71-log-pull.sh logs/boot.txt      # 4 MiB console ring from the end of userdata
adb reboot bootloader
```

The log contains crash reports with backtraces (`CRASH name ...`), IOKit traces of backboardd and SpringBoard, and the drivers' `A71 ...` lines. `tools/a71-crash.py` symbolicates them against the shared cache.

### QEMU

`tools/qemu-a71.py` boots the same kernel on QEMU `virt` with a test RAM-disk root. It is useful for kernel-only changes; see `NOTES.md`.

## Repository layout

| Path | What |
| --- | --- |
| `shim/` | Bare-metal boot shim (C + asm) packed as an Android boot.img v2 |
| `xnu/patches/` | The XNU patch series (applied in order by CI), plus staging scripts for libpthread, HFS and BearSSL |
| `.github/workflows/xnu.yml` | Kernel CI build |
| `tools/mkadt.py` | Generates the Apple Device Tree from a71's MMIO layout and the iPhone X identity |
| `tools/mkpayload.py` | Packs kernel + ADT + boot-args into the shim payload |
| `tools/mkiosroot.sh` | Builds the HFS+ iOS root from the IPSW images |
| `tools/a71-root-tweaks.py` | Bring-up changes to the root (Setup skip, activation, daemons) |
| `tools/a71-log-pull.sh`, `a71-log.py` | Read the persistent kernel log from recovery |
| `tools/a71-crash.py` | Symbolicate console crash reports |
| `tools/xnu-cc.py` | Local single-file compile check from a CI log |
| `tools/qemu-a71.py` | QEMU test boots with framebuffer text decoding |
| `tools/adt.py`, `remotezip.py`, `unpack_bootv2.py`, `sparsediff.py` | Helpers |
| `NOTES.md` | Detailed engineering log: every boot, crash and decision, plus hardware facts |

Not in git: partition backups, live device trees, recovery images, Apple firmware and root images, and downloaded or generated build trees. They contain device serials and calibration data, or Apple's copyrighted files.

## Kernel patches

| # | What |
| --- | --- |
| 0001–0009 | Toolchain compatibility, A71 machine config, non-PAC arm64, stubs for Apple-internal pieces |
| 0010–0018 | Early framebuffer console, physmap fix, PRNG without corecrypto, device-tree platform expert, timer PPI, boot CPU driver |
| 0019–0020 | Apple open-source libpthread kernel provider; BearSSL AES |
| 0021–0027 | RAM-disk root, mockfs, SHA-256, minimal AMFI, Apple open-source HFS+, MD5 |
| 0028–0034 | UFS host driver and root device, read/write root, DMA above 4 GiB |
| 0035–0045 | Entitlements, bindfs, AppleKeyStore stub, IOWatchdog, console crash reports |
| 0046 | IOSurface (IOCoreSurfaceRoot) and IOMobileFramebuffer (AppleCLCD) services |
| 0047–0055 | Diagnostics: persistent log, /dev/null tee, IOKit trace, heap strings and user stack sampler on crash; permissive Sandbox policy; HFS rename-swap; AppleKeyStore selectors |
| 0056–0057 | Throttled panel copy; no external identity resolver |
| 0058 | HID event services. Apple's IOHIDFamily-1915.140.3 user client and event queue, matching the iOS 16.7 userland |
| 0059 | iPhone X identity (`hw.product` / `hw.target` from the device tree) |
| 0060 | Power and volume keys over SPMI; touch over GENI I²C |
| 0061 | Present the display as 1125×2436 |
| 0062 | RPMh regulator vote for the touch rail; battery power source |
| 0063 | GENI FIFO packing fix and the Goodix GT9896 protocol |
| 0064 | Grant PRIV_WORK_INTERVAL (UIKit's CoreAnimation work interval) |
| 0065 | SMP: secondary A55 cores via PSCI CPU_ON |
| 0066–0067 | Fault-region crash info; console mute |
| 0068 | IOSurface lookup semantics for already-mapped surfaces |
| 0069 | Batched persistent-log flushes |
| 0082 | **A71-specific.** ST FTS5CU56A touch driver (replaces/complements Goodix for this board's actual touch IC) |
| 0083 | **A71-specific.** Read-only MDSS autorefresh probe, to inform the real display-driver work still ahead |

## Key hardware facts (upstream, Redmi Note 10 Pro)

- RAM: payloads use the upper bank, `0x100000000` + `0xfcc00000` (about 3.95 GiB), above Qualcomm's protected carve-outs.
- GICv3 with security extensions: the timer goes through Group 1 IRQ (virtual timer INTID 19), not FIQ as on Apple silicon.
- PSCI through `smc`, 19.2 MHz timer, ARMv8.2 without pointer authentication. MPIDR uses Aff1 for the core number.
- Panel: 1080×2400 DSC video mode, continuous splash from ABL, no refresh kick needed.
- Touch: Goodix GT9896 at I²C `0x5d` on QUP SE7 (`0xa84000`), powered by PM6150L LDO11 through RPMh.
- Buttons: power and volume down on the PM6150 PON block, volume up on PM6150L GPIO2 (SPMI SID 4).

More in [`NOTES.md`](NOTES.md).

## Key hardware facts (A71, this fork)

- Same `sdmmagpie` SoC family as the Redmi: UFS host controller, GICv3, and the splash framebuffer are at **identical physical addresses** to the ones above - confirmed by diffing a real A71 boot.img's device tree against this repo's hardcoded constants.
- Touch: ST FTS5CU56A at I²C `0x49` on the same QUP SE7 bus (`0xa84000`) the Redmi's Goodix touch uses. Reset/IRQ GPIO pin numbers (8/9) also match exactly.
- Panel: Samsung AMOLED (DDIC `ANA6705` or `S6E3FA9` depending on production batch - 4 variants seen across this unit's `dtbo.img`, not yet narrowed down), 1080×2400, **DSI command mode** - unlike the Redmi's video mode, this does not free-run without software or hardware-autorefresh help. See `xnu/patches/0083-a71-display-autorefresh-probe.patch`.
- MDSS/SDE register offsets (`mdss_mdp@ae00000`, `qcom,sde-intf-off`, `qcom,sde-pp-off`) read directly from this unit's own device tree; the autorefresh register offsets within those blocks are from Samsung's GPL-published kernel source for this board, not a public datasheet.

More in [`A71-NOTES.md`](../A71-NOTES.md) (one directory up, in the parent project folder).

## Credits

Built on Apple's open-source releases (xnu, IOHIDFamily, libpthread, hfs), [BearSSL](https://bearssl.org), [blacktop/darwin-xnu-build](https://github.com/blacktop/darwin-xnu-build), [ipsw](https://github.com/blacktop/ipsw), Qualcomm/Xiaomi's published Linux kernel sources for the hardware details, and [OrangeFox Recovery](https://orangefox.download). iOS itself is Apple's and is not distributed here.

This fork additionally draws on Samsung's GPL-published kernel source for the SM-A715F (for the ST FTS touch protocol and MDSS/SDE register offsets), and on [Henrik Grimler's maintained Heimdall fork](https://git.sr.ht/~grimler/Heimdall) for Odin-protocol tooling.
