# MARBLE real-input bring-up — 2026-10-23

## Current physical result — 2026-10-23

Physical buttons PASS. Synthetic volume event PASS. Synthetic touch down/up
PASS; touch HID service is proven sufficiently for hardware bring-up.
Physical GT9916R touchscreen FAIL. The Apple-facing HID/backend, key driver,
normalization and edge classification are frozen. GUI and Setup Hello PASS.

Exact reported synthetic log:

```text
MARBLE HIDTEST: one volume-up then info tap
MARBLE HID: key 0xe9 down
MARBLE HID: key 0xe9 up
MARBLE TOUCH: id=0 down x=1040 y=2320 edge
MARBLE TOUCH: id=0 up x=1040 y=2320 edge
MARBLE HIDTEST: complete, injection disabled
```

No actual inherited SPI/GPIO/power/refusal dump was supplied with this result.
The active-init hypothesis is source-backed, but the precise old failing gate
or electrical state remains unknown. Historical sections below describe the
previous conservative build; active-init changes are recorded separately.

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


## Final packaged input test — awaiting physical validation

Final source: `7f2758cd0f89ff5cd68cde63475aaa354074ce79`
(`marble: improve guarded input diagnostics`).
[CI39897578714](https://github.com/Beast9265/ios-marble/actions/runs/39897578714)
completed **success**, with headSha exactly matching that source and inputs
13.5 / DEVELOPMENT / MARBLE / keep_going=true. Fresh artifact directory:
`xnu/out-marble-ci-39897578714`. Prior successful39896552164 is not packaged.

| Final artifact | SHA256 |
|---|---|
| Kernel | `79dccb0c015e7490b6a9467ceb727d055b83013d21d5e4de632a5a45ffd6db8d` |
| ADT (same physical Hello bytes) | `35f0bff762c339e86a0e67392267ed148ae06b24703b682ce2327c9296ed84e3` |
| Physical payload | `ded93b3420d89485575a113fe604bb587662c4f62e371a589d4abca113281e56` |
| latest-marble-xnu.img | `a9dfc2ef7fe7990411a6403a7503694ec55fbcbdc8383a91b77c9ecc5a0cb3e8` |
| Synthetic payload | `bfa66d40e3df1dca5c2f2de7e77080406d74005fcbf16d54216d872dbb64062b` |
| latest-marble-xnu-hidtest.img | `dd2ef2d1355a7f1ca71ddd43c8a4ce1d78b4d4fed087a52298c287b7b8821236` |

Images/payloads/ADT are under `shim/out/marble-xnu/`; generated manifest
`marble-input-39897578714.json` records exact arguments and hashes. Known-good
Hello image `hello-known-good-marble-xnu.img` remains
`789377d9cc9de5027038b074e3c0c61121f2229594e7895282933a44b1eb6242`.
The setup-fast raw/sparse were rehashed and match the checkpoint table above.
No new root, writes to userdata, root cleanup or physical phone operations.

Physical payload command line is byte-identical to the Hello image's line:

```text
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 ufsrw=1 rootrw=1 launchd_unsecure_cache=1 marbleguidiag=1
```

Synthetic image adds only `marblehidtest=300 marblekeys=0 marbletouch=0`.
Both use identical final kernel segments and exact known-good ADT. The earlier
regeneration semantic check normalized bookkeeping only; packaged bytes are
extracted/verified against the physical Hello image, preserving random seed,
phandles, ordering and all /product properties. No input ADT changes required.

Post-build verification passed: artifact SHA256SUMS, arm64 Mach-O, full link
with zero undefined symbols; every payload segment matches the exact rebased
CI kernel; independent boot-v4 header/stock metadata/bounds/padding/size/shim/
locator footer checks on both images; bootstrap mapping/capacity/alias audit.
Shim SHA256 remains586713d3b4c5862f73443cb1e5f555e465a9ffa5f3e2662672d41fff1715ee05.
Linked personality string now contains SweetHIDButtons and SweetHIDTouch on
IOResources, without SweetBattery. Linked physical entry points and the final
refusal diagnostic strings are present. No physical-timer instructions, one
CNTV_CTL MSR; SWEET sampler remains excluded. Full CI logs confirm0082 applied
and physical/HID units compiled. Runtime service registration/opening, actual
inherited state, real input and UIKit receipt remain **UNTESTED**.

Only manual phone commands, synthetic first (allow~300s plus readiness and
settling for its one volume-up/info-tap sequence):

```sh
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu-hidtest.img
```

Then test physical power/volume/tap/drag and bottom-edge swipe:

```sh
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
```

No userdata flash is needed. The next physical success criterion is retained
Hello rendering, HID service opens by backboardd, key transitions and contact
down/move/up reaching iOS, then a real bottom-edge swipe advancing Hello.

## Active Berlin-D test — 2026-10-23

This section supersedes the inherited-only hardware policy above. Keys and
Apple-facing HID sources remain byte-identical. Dedicated image argument:
`marbletouchinit=1`; default remains inherited-only. No root change.

The precise previous failure is **unknown**: no physical startup/refusal logs
were captured. Missing active initialization is the leading hypothesis, not a
proven electrical diagnosis. Synthetic contacts are not SPI reports.

Additional pinned primary references:

- [Current Linux Berlin core](https://github.com/torvalds/linux/blob/734bef548a96e8774d6eef5dfa2026c6edc4e80b/drivers/input/touchscreen/goodix_berlin_core.c)
  and [SPI](https://github.com/torvalds/linux/blob/734bef548a96e8774d6eef5dfa2026c6edc4e80b/drivers/input/touchscreen/goodix_berlin_spi.c):
  power sequence, confirm, 26-byte initial event snapshot.
- [Goodix guide](https://github.com/goodix/goodix_ts_berlin/blob/6c4b81587d43cf4ebf59cc63fe2916d77e4e8ce2/docs/Porting_Guide.md):
  GT9916 is Berlin-D; no Berlin-A reset-after register operations are used.
- [Linux RSC](https://github.com/torvalds/linux/blob/734bef548a96e8774d6eef5dfa2026c6edc4e80b/drivers/soc/qcom/rpmh-rsc.c),
  [command DB](https://github.com/torvalds/linux/blob/734bef548a96e8774d6eef5dfa2026c6edc4e80b/drivers/soc/qcom/cmd-db.c),
  [regulator votes](https://github.com/torvalds/linux/blob/734bef548a96e8774d6eef5dfa2026c6edc4e80b/drivers/regulator/qcom-rpmh-regulator.c),
  [GCC](https://github.com/torvalds/linux/blob/734bef548a96e8774d6eef5dfa2026c6edc4e80b/drivers/clk/qcom/gcc-sm8450.c),
  [DFS/RCG](https://github.com/torvalds/linux/blob/734bef548a96e8774d6eef5dfa2026c6edc4e80b/drivers/clk/qcom/clk-rcg2.c).
  Captured DTS supplies board addresses and ownership, rather than SWEET.

Hardware remains SPI SE4 `0x00990000`, CS0, mode0, 8-bit MSB first; no I2C.
CAPE TLMM bank `0x0f100000`: GPIO16–18 qup4/function1/no-pull/6mA;
GPIO19 CS qup4/function1/pull-up/16mA; GPIO20 reset GPIO output/pull-up/8mA;
GPIO21 IRQ GPIO input/pull-up/8mA. Only those six configurations are changed.
**Reset asserted = physical LOW; released = physical HIGH.** GPIO20's latch
is set before output enable. Upstream logical GPIO0 releases its active-low
reset descriptor; copying logical constants into raw TLMM would invert reset.
The captured vendor DTS itself uses legacy goodix,reset-gpio flags0, and its
legacy driver drives raw GPIO1 to release; this is not a captured active-low
gpiod descriptor. Both references agree on the physical low/high sequence.

Captured reserved command DB is `0x80860000`, size `0x20000`; apps RSC DRV2
is `0x17a20000`, TCS offset `0xd00`. Captured ordering is ACTIVE3, SLEEP2,
WAKE2, CONTROL0, FAST1. Resolve both `ldoc2` and `ldoc9` before any vote:
validate DB magic/version/header/entry/aux bounds, unique VRM resources and
address alignment. Resource addresses are never guessed. Only an empty idle
ACTIVE TCS0–2 can be borrowed; sleep/wake/FAST slots remain untouched.
Known RSC revisions1/2 and3 select their respective Linux register layouts.
Vote voltage in mV, PMIC5 LDO HPM mode7, then enable1, with ACK completion.
Each transaction has a 100ms maximum; uncertain writes/timeouts quarantine
that slot for the boot, with no reset/retry. On proven completion restore the
inactive command payload, control mode and own IRQ-enable bit. Other IRQ
bits and inherited payloads are preserved. No SPMI/PMIC direct writes.

Sequence: resident SPI firmware/idle geometry check; command DB preparation;
assert reset once; configure owned pins; wait2ms; VDDIO ldoc2 1800000uV vote,
wait3ms; AVDD ldoc9 3224000uV vote, wait15ms; release reset, wait4ms; configure
FIFO; confirm at `0x10000` by writing eight AA bytes and reading all eight.
At most3 comparison attempts, 5ms apart; a transport failure stops immediately.
Then wait100ms, read version28 bytes at `0x10014`, checksum and PID9916;
read length/IC-info at `0x10070`. No firmware/config upload or calibration.

GCC `0x00100000`: preserve votes at `0x62008`, add only bits6/7/14 for
master/slave AHB and SE4. Branches `0x27004/0x27008/0x274dc` must clear
CLK_OFF within1ms. Select an existing XO DFS level or set this engine's RCG
`0x274e4/0x274e8` to XO19.2MHz; divider2 gives at most9.6MHz, below the
captured15MHz limit. No PLL or DFS-table changes. No resident SPI protocol
firmware means STOP, not a firmware loader. Busy sequencers, nonempty FIFO,
unsupported32-bit FIFO geometry or outstanding DMA also stop. Idle DMA can
be switched to polled FIFO with local GSI/IRQ delivery disabled, using Linux
GENI I/O initialization. FIFO packing and transfer code are unchanged.

Version VID is no longer an exact whitelist. Checksummed Berlin/9916 and
structural IC-info validation admit compatible firmware revisions. Stock
legacy layout still requires captured die0x22 and uses the independently
measured10800x24000 range; extended layout reads its actual range. Both
require header8/point8, bounded event address, ten contacts maximum, supported
customer/version fields, and the matching panel aspect/coordinate scale.

Event reads now start with26 bytes. Counts0–2 use that snapshot; larger counts
read only `(count-2)*8` additional bytes at event+26. Full header/contact
checksums, unique IDs and coordinate bounds precede any HID delivery/ACK.
Status0 is harmless. A malformed frame is dropped without ACK; three
consecutive malformed snapshots quarantine the worker. Transport or unsupported
firmware/config/gesture requests stop immediately. This intentionally retains
the user's stricter no-invalid-ACK rule, rather than upstream's bad-frame ACK.
Polling remains10ms; normalization/edge classification are unchanged.

Diagnostics are one-shot per worker/probe stage: worker start before60s delay,
MMIO success, initial GCC and GPIO16–21 registers/physical reset+IRQ, GENI
FW/SFW/protocol/status/DMA/FIFO, DB lookup, each vote, reset and configured pins,
SPI ready, each confirm's eight returned bytes, version and IC-info reads.
Any refusing probe prints its gate or stage-specific failure. Failed version
prints28 raw bytes; failed IC-info prints at most64 bytes. Confirm is at most3
attempts; two rail transactions; malformed packets produce only final stop.
Existing shared HID contact logs retain their32-event budget. No poll logging.
Clock failure prevents unsafe unclocked GENI reads; its branch gate is explicit.

Expected success sequence (all hardware results still UNTESTED):

```text
MARBLE TOUCH: worker started; probe after 60s active-init=1
MARBLE TOUCH: MMIO mappings successful; active-init=1
MARBLE TOUCH: VDDIO ldoc2 1800000 vote OK errno=0
MARBLE TOUCH: AVDD ldoc9 3224000 vote OK errno=0
MARBLE TOUCH: reset released ...
MARBLE TOUCH: SPI SE4 mode0 8-bit MSB CS0 FIFO ready
MARBLE TOUCH: device confirm PASS attempt=1 rx=aa aa aa aa aa aa aa aa
MARBLE TOUCH: identified GT9916R ...
MARBLE TOUCH: IC-info len... event=... head8 point8 range10800x24000 factor10
MARBLE TOUCH: polling active, 10 contacts, 10ms
```

Local validation includes complete82-patch replay/source equality, CI-header
arm64 compiles and ASan/UBSan tests of existing FIFO/parser fuzz cases plus
power/reset ordering and failures, confirm framing/retries, initial26 contact
snapshots0/1/2/3/10, invalid/no-ACK behavior, command DB bounds/duplicates,
v2/v3 ACTIVE-only ownership, inherited payload preservation and timeout
quarantine. Tests model hardware; they do not establish voltage or touch works.

## Packaged active-init checkpoint — physical test pending

Source `efb27bc77c45dca4443167dc347c0c14d1eb0ea0`, successful MARBLE DEVELOPMENT CI [39903264776](https://github.com/Beast9265/ios-marble/actions/runs/39903264776).
Supersedes cancelled intermediate39903081131. Exact successful artifact only.

| Artifact | SHA256 |
|---|---|
| Kernel | `0686533d463d808f125c0e8151a9f2ce23ef0514eed69d5f5e5de4fcddb6b822` |
| Exact Hello ADT | `35f0bff762c339e86a0e67392267ed148ae06b24703b682ce2327c9296ed84e3` |
| marble-xnu-touchinit.payload | `b2258a3dc047499959c7cf4f7878cd73eb7cfbaa5d566ebb7da57176de92a34d` |
| latest-marble-xnu-touchinit.img | `4c57ea14c85e47d16db710758db9d54a564c3c5308d8b2fa29c1ec81f386ba25` |

Arm64/full-link zero undefined, artifact SHA256SUMS, boot-v4 metadata/padding,
payload segments/chained fixups/footer, bootstrap capacity/alias attributes,
CPU0 timer audit all pass. Command line is unchanged plus `marbletouchinit=1`,
with cpus=1 and marbleguidiag=1; synthetic injection remains off.
All three previous images retained and rehashed unchanged, including Hello
rollback789377d9...1eb6242. setup-fast raw/sparse rehashed unchanged; no mount
writes, root generation, retention cleanup or phone commands. Keys/HID/display
sources untouched. Rail votes, actual inherited registers, confirm/version
results and physical touch remain UNTESTED.

Read [MARBLE_REMOTE_DEBUG.md](MARBLE_REMOTE_DEBUG.md) for the subsequent
documentation-only USB/SSH/TrollVNC audit. USB device/mux and IOSurfaceAccelerator
are missing from the linked MARBLE implementation; no remote service installed.

Manual physical test:

```sh
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu-touchinit.img
```
