# MARBLE real-input bring-up — 2026-10-23

## Proven checkpoint and scope

User physically observed iOS 16.7.16 Setup Hello (animated ciao / Scorri verso
l'alto), status/battery/info button and home indicator. The bounding-path ADT
fix succeeded. Physical keys and touch are the next blocker. No input result
from the new kernel is claimed until the user tests it.

HELLO-SCREEN-KNOWN-GOOD, independently rehashed before edits:

| Artifact | SHA256 |
|---|---|
| Kernel, CI39888158542 | `462dc21b476550949aaebdd335c5e6584f120c3481bfbda2cae92958398160d9` |
| ADT | `35f0bff762c339e86a0e67392267ed148ae06b24703b682ce2327c9296ed84e3` |
| Payload | `823706ba303643c4880d235abac8aaa2145983c23258c2af119f0019f3f0906c` |
| Boot | `789377d9cc9de5027038b074e3c0c61121f2229594e7895282933a44b1eb6242` |
| setup-fast raw | `7ca8c990f98875d892ffa38f769f4a8bb5af23bdbabb4ee50d69d2df13822798` |
| setup-fast sparse | `cec3daf08e3236065d14c3939c48051430c7737f798c2b7d8affb475c3f4aa01` |

Preserved named boot copy:
`shim/out/marble-xnu/hello-known-good-marble-xnu.img`, same boot SHA256.
No new root, userdata edits or root retention cleanup. No changes to graphics,
/product, identity, migration, UFS, sandbox, AKS, daemons or CPU topology.

## Evidence and provenance

Local sources were searched before downloading:

* `/home/beast/marble-dump/live.dts`, captured device tree, SHA256
  `404b5d14a0bdd34ef7f5aab5af366a2766e219a164451cab2df0b55fd8ded287`.
* `/home/beast/marble-dump/dmesg-clean.txt`, saved Android boot, SHA256
  `a2c0a60f650a055d39f6cafea747fb1f2dab31cb11bba7a69dd7c7d1135c7b41`.
  These device dumps stay outside git; no new phone access was performed.
* `/home/beast/src/pmaports-marble/device/testing/linux-xiaomi-marble/`
  `0011-0001-arm64-dts-qcom-add-xiaomi-marble-placeholder.patch`, SHA256
  `b1f7feb1ebc370f82f2910d9314ce253955c317df5f809ebc730a0e6a2286971`.
  This local export has no git metadata. It identifies actual stock supplies,
  SPI4 wiring and measured 10x touch coordinates. Also inspected local
  adaptation-xiaomi-marble and pmbootstrap exports; no complete vendor kernel
  tree was present there.

Only relevant public source files were fetched into `/tmp/marble-input-vendor`:
[MiCode MARBLE vendor source, pinned 48952ed36228217531482b39d5bef13e7fd808ec](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/tree/48952ed36228217531482b39d5bef13e7fd808ec).
Specific authoritative files:

* [SPMI arbiter v7](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/48952ed36228217531482b39d5bef13e7fd808ec/drivers/spmi/spmi-pmic-arb.c)
* [Gen3 PON keys](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/48952ed36228217531482b39d5bef13e7fd808ec/drivers/input/misc/pm8941-pwrkey.c)
* [PMIC GPIO](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/48952ed36228217531482b39d5bef13e7fd808ec/drivers/pinctrl/qcom/pinctrl-spmi-gpio.c)
* [CAPE TLMM definitions](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/48952ed36228217531482b39d5bef13e7fd808ec/drivers/pinctrl/qcom/pinctrl-cape.h)
* [Actual qcom,spi-geni driver](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/48952ed36228217531482b39d5bef13e7fd808ec/drivers/spi/spi-msm-geni.c)
  and [GENI register header](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/48952ed36228217531482b39d5bef13e7fd808ec/include/linux/msm-geni-se.h).
* Goodix [SPI framing](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/48952ed36228217531482b39d5bef13e7fd808ec/drivers/input/touchscreen/goodix_9916/goodix_brl_spi.c),
  [extended IC-info/report parser](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/48952ed36228217531482b39d5bef13e7fd808ec/drivers/input/touchscreen/goodix_9916/goodix_brl_hw.c),
  [packed extended layout](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/48952ed36228217531482b39d5bef13e7fd808ec/drivers/input/touchscreen/goodix_9916/goodix_ts_core.h),
  and the [stock Berlin layout](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/48952ed36228217531482b39d5bef13e7fd808ec/drivers/input/touchscreen/goodix_berlin_driver/goodix_ts_core.h).
  Vendor touchscreen Makefile selects goodix_berlin_driver for
  CONFIG_TOUCHSCREEN_GOODIX_BRL. The two IC-info layouts are distinguished
  structurally; extended fields are not assumed present in the stock layout.
* [SM8450-family GCC](https://github.com/torvalds/linux/blob/v6.12/drivers/clk/qcom/gcc-sm8450.c)
  and [GENI packing implementation](https://github.com/torvalds/linux/blob/v6.12/drivers/soc/qcom/qcom-geni-se.c).
  MARBLE's local postmarketOS SM8475 description uses this SoC family.
  GCC registers are **read only** in this implementation.

## Linked HID audit and shared backend

The Hello kernel's actual Mach-O contains SweetHIDButtons, SweetHIDTouch,
IOHIDEvent, IOHIDEventServiceQueue, IOHIDEventServiceUserClient, and
sweet_hid_key/touch symbols. Its compile configuration includes all four HID
translation units through iokit/conf/files.arm64. SweetHID.cpp itself is not
SWEET-gated. However its **personalities** in KernelConfigTables.cpp are
SWEET-only; the linked MARBLE personality string has no SweetHIDButtons or
SweetHIDTouch entries. Therefore the old kernel cannot instantiate those
services on IOResources; no evidence supports claiming backboardd opened them.

0082 now generalizes only those two personalities to SWEET || MARBLE, keeping
SweetBattery SWEET-only. The Apple-facing event/queue/user-client sources are
unchanged. They are board-independent IPC/event serialization code. The same
SweetHID class names/ABI are deliberately retained; MARBLE gets C entry points
`marble_hid_key(0..2, down)` and `marble_hid_touch(id, down, panel_x, panel_y)`.
No physical Home key is exposed by the MARBLE hardware driver.

Consumer page0x0c usages: power0x30, volume-up0xe9, volume-down0xea.
Touch is a built-in, display-integrated digitizer collection with finger
children, up to10 contacts and normalized16.16 coordinates. Existing0071
FromEdgeTip behavior stays intact through contact release.

MARBLE-only logs identify service registration and successful user-client open
with process name. Registration/opening/receipt in backboardd is still a
**physical test criterion**, not a local test result. Existing SWEET backend
behavior is preserved: before/after SWEET, BCM2837 and T8103 preprocessed token
streams match with __LINE__ normalized. Other0082 sections and patches are
byte-identical; no SWEET physical driver changed.

## Physical keys

| Key | Device-tree source | Hardware and status |
|---|---|---|
| Power | spmi@c42d000 / pmk8350@0 / pon_hlos@1300 / pwrkey | SID0, HLOS PON0x1300, RT0x1310 bit7, asserted high |
| Volume-down | same / resin | SID0 RT0x1310 bit6, asserted high |
| Volume-up | gpio_keys / vol_up -> phandle0x5f6 GPIO6 | PM8350 SID1 GPIO controller0x8800; GPIO6 base0x8d00; RT0x8d10 bit0, active low |

The side fingerprint assembly is not the power-key event transport. Its
separate GPIO40/41 nodes are left untouched. Local DTS lines9687–9740,
10164–10210 and28868–28884 establish the key wiring. The PMIC GPIO6 pinctrl
uses normal input with pull-up; physical contact is active low. PON RT status
bits are reported directly by the vendor input driver; they are not the old
SWEET PON0x810 bits0/1.

SPMI primary bus EE0, arbiter v7 (saved Android log explicitly0x70000000):
core0x0c400000/0x3000, config0x0c42d000/0x4000,
observer0x0c440000/0x80000. APID table core+0x2000+4*n,
owner config+4*n, primary count core+4 &0x7ff.
Observer channel offset0x20*APID (not SWEET v5 stride0x80), status+8,
read-data+0x18. PPIDs0x013 and0x18d. Extended-read opcode1<<27,
low address byte<<4, byte count0 (one byte).

`bsd/dev/marble_keys.c` validates v7/count/ranges, PON subtype9 and enabled
LV/MV GPIO type0x10/subtype0x10–0x13 in input mode. Reads subtype/mode/enable
before polling. No PMIC configuration, PON reset settings or interrupt ACKs.
ABL readability has not yet been observed under XNU; failed reads or unexpected
identity withhold keys. Normal polling20ms; observer timeout1000us per read.
A runtime transaction failure releases held keys and quarantines polling.
Disable with marblekeys=0.

## Touch identification and wiring

This device is **not** SWEET's GT9896/I2C controller:

* DTS `/soc/spi@990000/m16t-touch@0`, compatible `goodix,gt9916S`.
  I2C node at the same base is disabled; SPI node is enabled.
* Saved Android log lines2624 and4523–4525: BerlinD, ROM `BERLIN`, PID `9916R`.
  Lines7093–7128: ROM VID02 00 04, firmware VID00 80 02 94, sensor255;
  IC-info length191, die0x22, config0x6552E4F8/version0x11,
  touch-data0x10308, header8, point8. These are **saved Android observations**,
  not claimed new XNU output. Controller identification must succeed again.
* QUPv3 wrapper0 global SE4, SPI MMIO0x00990000/0x4000, CS0 (no I2C address).
  Vendor maximum SPI frequency15MHz. SPI mode0, 8-bit MSB-first.
* TLMM node0x0f000000, but CAPE `REG_BASE=0x100000`, so GPIO bank mapping
  starts at0x0f100000. Per-pin stride0x1000; config+0, IO+4;
  mux bits2–5, output-enable bit9, input bit0/output bit1.
  GPIO16/17/18 and19(CS) use qup4 function1. ResetGPIO20 is active low;
  IRQGPIO21 active low/level-low. No GPIO mux/reset/IRQ writes are made.
* Default pinctrl: qupv3_se4_spi_active plus mi_ts_cs_active;
  touch default mi_ts_active GPIO20/21 pull-ups. Sleep states are not installed.
* iovdd PM8350C L2, RPMh `ldoc2`, 1800000uV;
  avdd PM8350C L9, `ldoc9`, 3224000uV (DTS supply phandles0x303/0x30a).
  No RPMh/TCS transaction is implemented: inherited power sufficiency is not
  measured yet. No evidence justifies a new vote in this build.
* DTS lists three panel phandles and two TM firmware/config names selected
  with GPIO119/117 panel IDs. No other touch-controller compatible appears in
  the captured live tree. This driver does not probe arbitrary addresses or
  assume the exact firmware from the compatible string alone.

The local postmarketOS patch records measured super-resolution coordinates
(max10354/23125), using10800x24000. Newer vendor IC-info includes screen_max
fields. The implementation reads these dynamically for the supported extended
layout. The stock layout has no screen_max extension: only the exact captured
9916R/BERLIN/VID00 80 02 94/die22 tuple may use the documented10x range. Unknown
firmware/layout/range is withheld rather than guessing a factor.

## Transport, inherited state and protocol

One worker starts60s after HID registration. Before any SE writes it logs FW
protocol/version, command-active bits, DMA mode, FIFO geometry/counts, M clock
and selection, GCC vote/branch/RCG registers, GPIO16–21 state and expected rails.
No rail voltage is claimed measured. It requires idle inherited SPI protocol1,
FIFO mode, 32-bit FIFOs with depth4–63, enabled M clock and running branch
clocks, correct SPI mux, reset GPIO output high and IRQ GPIO input. If ABL did
not leave that state, logs stop at an explicit read-only rejection. No firmware
load, reset, clock enable, vote or retry is attempted.

GCC read offsets, SM8450-family source: vote0x62008; SE4 branch0x274dc;
wrapper0 master/slave AHB0x27004/0x27008; SE4 RCG0x274e4/config0x274e8.
These reads diagnose inherited state; there is no claim of measured SPI clock
frequency. The driver preserves inherited clock selection/divider.

After the safe gate: local polled SE interrupt enable0; SPI mode0/CS0/8-bit,
byte granularity0 and TX/RX packing cfg0=0x7f8fe/cfg1=0xffefe (Linux's 4x8-bit
MSB-first vector algorithm), CS_TOGGLE cleared. Actual vendor full-duplex
opcode is3, not opcode7; CS assert8, deassert9, fragmentation bit2 retains CS
until deassert. Timeout1ms for each CS command,5ms per duplex transfer;
FIFO counts above declared depth, extra RX bytes, error IRQs or incomplete
transfers quarantine the transport. At most1032 bytes per exchange. No cancel,
abort, reset/retry loop or DMA descriptors. A timed-out transaction is not
reused. All local SE IRQ acknowledgements concern this driver's own polling;
external firmware-owned PMIC/GPIO interrupts are not acknowledged.

Berlin-D read:0xf1 +32-bit big-endian address +3 dummy0xff bytes, then data
in the same CS transaction. Version0x10014 (28bytes), IC-info0x10070 (length
then <=1023bytes). Validate byte-sum16 LE checksums and PID9916 before reading
reports; validate IC-info lengths/count arrays, report version1/0, head8/point8,
address range and geometry. No persistent controller operation is issued.

Poll IRQ low every10ms; read header8 and count*8+2 bytes. Header/status0x80,
count<=10, byte-sum16 checksums, unique IDs<10, finger type and coordinates are
validated before any event is emitted. Contact ID=byte0>>4; x/y LE16 at+2/+4.
Each full snapshot emits down/move and releases missing contacts. The sole IC
write is0xf0 +event-address +zero status byte to ACK a fully validated frame.
Config/firmware requests and unsupported packets stop with a bounded message;
no firmware/config upload or calibration. Stop releases any held HID contacts.
Disable with marbletouch=0.

## Mapping and edge gestures

Controller coordinates divide by proven uniform resolution factor to physical
1080x2400, then use the unchanged SWEET0061 mapping: clamp to0..1079/2399,
add centered crop offsets22/18, normalize by1125/2436. No aspect stretch.
Physical corners map to logical pixels(22,18) and(1101,2417).
The shared0071 policy marks a contact starting within48 physical pixels of an
edge with kIOHIDDigitizerEventFromEdgeTip for its full life, including release.
Thus a bottom-edge swipe has the mature UIKit edge classification.

## Synthetic path and diagnostics

`marblehidtest=N` is off by default; accepted delay60–600s. Packaged test uses
300s and marblekeys=0 marbletouch=0, separating HID from physical bus accesses.
The timer requires both services opened plus an alive Setup process, then a
10s settling interval. Readiness retries at most6 times with10s spacing.
Exactly one volume-up down/up100ms apart, wait5s, one info-area tap at physical
(1040,2320) down/up100ms apart, then stop. No Home or automatic Setup skip.
The tap location is a diagnostic target, not a claimed pixel-perfect UI hit.
Kernel service/queue/consumer behavior still requires physical observation;
local compile tests cannot prove UIKit receipt.

With marbleguidiag=1: registration once/service; client-open max16/boot;
shared HID key lines64/boot; touch down/move/up32/boot. Saturating atomic
reservations keep budgets from wrapping. Key-driver transition lines64/boot,
then event delivery continues silently. Hardware setup/probe logs are one-shot;
refusal includes PMIC register/status values, and unsupported IC-info may print
at most64 bytes in4 complete16-byte rows after a successful read.
No poll-by-poll logs. One failure terminates each hardware worker. Existing
crash/stderr/heap diagnostic budgets remain unchanged.

## Local checks and build handoff

* Full0001..0082 reverse/replay, strict0082 added-source whitespace, exact
  resulting-source comparison.
* All four changed/new C/C++ units compile to arm64 using actual CI headers.
  Their undefined references close against the existing kernel and new objects.
* SWEET/BCM2837/T8103 shared preprocessed tokens unchanged; Apple event/queue/
  user-client files and all other0082 sections unchanged.
* `tools/test-marble-input.py TREE`: actual extracted parser/FIFO code under
  ASan/UBSan; all1032 transfer lengths/order, CS/duplex opcodes, impossible FIFO,
  timeout/busy failures, both IC-info schemas, checksums, duplicate IDs, complete
  snapshot rejection, 10x down/move/up mapping,100000 malformed/truncated inputs.
* Ten existing unit tests and repository validation pass.

Changes:0082 (two personalities, shared backend MARBLE branches, bsd/conf/files,
new marble_keys.c/marble_touch.c); test-marble-input.py; this report; NOTES;
physical-success update in MARBLE_BOUNDINGPATH.md. .gitattributes exempts unified
patch context prefixes from source-style whitespace checks; actual source
additions still pass git apply --whitespace=error. No generated/private blobs
are staged. Build/source/artifact results are appended after exact CI finishes.


## Final diagnostic recovery

Recovered existing final diagnostic edits from authoritative0082, rather than
recreating or copying another source representation. Fresh complete patch replay
matches the surviving generation tree byte-for-byte. Both physical units plus
the shared HID/config units compile with actual CI headers. Final replayed
parser/FIFO sanitizer tests, shared non-MARBLE token equality, symbol closure,
ten unit tests and repository validation pass again.

Prior CI39896552164 completed successfully for9317cc483f485c130aa373a814c23c5b9e49d99b.
It proves the main implementation builds, but predates the final diagnostics
and is not the final packaged artifact. Final source/run/hashes follow below.
Unrelated untracked bootstrap documentation and sparse-script executable-mode
change remain outside the input commit. Exact Hello ADT bytes are reused;
no root build, userdata edits or cleanup.

Expected log forms (placeholders are not measured XNU values):

```text
MARBLE HID: buttons service registered (test delay N s)
MARBLE HID: touch service registered
MARBLE HID: SweetHIDButtons open by IOHIDEventServiceUserClient (backboardd) -> 1
MARBLE KEYS: arb=... apids=... PON9 SID0:1310 apid... bits7/6 high; PM8350 SID1:8d10 apid... bit0 low; initial=.../...
MARBLE KEYS: power down
MARBLE KEYS: power up
```

If the identity/readability gate refuses keys, exact diagnostic format:

```text
MARBLE KEYS: withheld arb=%#x APIDs=%u/%u status=%#x PON1305=%#x GPIO8d04/05=%#x/%#x mode=%#x en=%#x RT=%#x/%#x (ff may be unread)
```

Touch probe reports inherited registers before writes, then either a refusal or:

```text
MARBLE TOUCH: SPI SE4@990000 CS0 fw=... proto... status=... DMA=... FIFO=.../... clock=... sel=...
MARBLE TOUCH: identified GT9916R ROMBERLIN FW=00.80.02.94 sensor255
MARBLE TOUCH: IC-info len191 event=0x10308 head8 point8 range10800x24000 factor10
MARBLE TOUCH: polling active, inherited controller config, 10 contacts
MARBLE TOUCH: id=0 down x=... y=...
MARBLE TOUCH: id=0 move x=... y=...
MARBLE TOUCH: id=0 up x=... y=...
```

The identification values above are expected from the saved Android log;
new XNU output may differ. An unsupported metadata frame prints:
`MARBLE TOUCH: IC-info/checksum/report geometry unsupported len%u; withheld`.
With marbleguidiag=1 and a completed metadata read, at most4 rows of16 bytes
follow as `MARBLE TOUCH: IC-info[%u] ...`; every row must be inside len and64.
No hardware safety gate or acceptance criterion was weakened by these diagnostics.
Physical input and UIKit receipt remain **UNTESTED**.
