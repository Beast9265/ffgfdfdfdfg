# MARBLE touchscreen and USB v3 (2026-10-23)

Starting HEAD: `6dcf1e3cc9167e28bbbc683ab2d684456c39f23d`.
User physically tested the preceding combined image: Hello and keys work;
physical touch does nothing; Linux receives **no USB connection event** and
`lsusb` sees no device. These observations supersede the earlier documents'
“manual test pending” statements. They do not identify a specific failing
register. This iteration changes hardware initialization and adds independent
RAM, framebuffer and normal-filesystem diagnostics. Physical success is untested.

## Source ledger

Source files/commit metadata fetched into `/tmp/marble-v3-research`;
previous pinned Linux/U-Boot files remain `/tmp/marble-usb-research`.
No downloaded kernel/vendor firmware or device dumps enter git.

| Source | Commit | File/function and fact | Confidence / consequence |
|---|---|---|---|
| Captured stock DT | local `marble-dump/live.dts`; hash below | `spi@990000`, `m16t-touch@0`; SE4, GPIO16..21, 15MHz, L2C/L9C | Highest board evidence; retain bus/pins/rails |
| Captured stock log | prior input handoff | ROM BERLIN, PID9916R, VID00800294, sensor255, die22, IC-info191/event10308 | Actual resident FW identity; no new hardware measurement |
| Pzqqt current | `cf63f53980e17b503e595501b359697595fe8b24` | `goodix_9916r/goodix_brl_hw.c`: `brl_power_on`176, `brl_dev_confirm`284, `brl_reset`315, `brl_read_version`678, `brl_get_ic_info`948, `goodix_touch_handler`1136, `brl_event_handler`1242, `brl_after_event_handler`1311 | Direct device-derived driver; regulator settling30/15ms, normal reset100ms |
| Pzqqt adaptation | `f552724a9d07693e8651fe15cafc87554528fe39`; parent `fe4da7d72a7f36027a8b6baaa8f9161816c563c8` | `goodix_ts_core.c/.h`, panel selection and TM filenames; commit explicitly attributes stock reverse engineering | High; do not import another panel's firmware |
| Pzqqt voltage | `fa376fbbd886556f73030159b178395ad4c0ed27`; parent `4d4ad050ef33e77497b3a56f8f63d0afc6287df1` | `goodix_ts_power_init`, AVDD exactly3224000uV | High; keep3224mV request |
| Pzqqt import | `d4a2fc8bac2b064f6bb6d1e0c15c059a23f454d9`; parent `d47f3f65e71ec034d5a2cdfd63f077eadaa6c4ef` | import from ruby-s-oss; all eight requested Goodix files fetched at import and later revisions | Lineage, not proof of MARBLE behavior before adaptation |
| Pzqqt historical branch | `4fe1919d08a14983f5536f7296953d99db0dc8da` | historical Goodix files and path history; equivalent adaptations appear under rebased8c35c08/79ee35e | Independent lineage comparison; do not assume cherry-pick SHAs are identical |
| cupid kernel | `a699db2cdaa37e62f22f84fba32d877e2ce72253` | Goodix cleanup/MARBLE support, SPI/core/header changes | Ancestor comparison; not generic Berlin proof |
| cupid **devicetrees** | `ea5040868ed32ff5a9344d47f26490002a846092` | `qcom/marble-sm7475.dtsi`: L2C1.8/L9C3.224, SPI4, reset20/IRQ21; CS16mA/pull-up | Board evidence; differs from working Linux CS policy; retain requested6mA/no-pull |
| iLtanaka Linux | `ed120558cd2c5f970edc44e1273a8d7b6caed825` (current main independently checked) | `goodix_berlin_{spi,core}.c`, `spi-geni-qcom.c`, `qcom-geni-se.c`, `gpi.c` | Working-board comparison; generic reset3/15/4ms loses to vendor30/15/100ms |
| upstream Berlin-D | pinned prior source under `/tmp/marble-touchinit-sources/torvalds` | resident firmware operation, 8-byte prefix, version/info/events | Protocol cross-check, lower priority than9916R |
| iLtanaka U-Boot | `4e1c8502a39213eca383b11bdb716749c2953d76` (current main checked) | `drivers/phy/qcom/phy-qcom-snps-eusb2.c`, blob`b730c7e5...`; repeater-only supplies/reset helper, CPBIAS1, 19.2MHz; board DTS fixed ref clock | Strong USB initialization reference, including explicit comment describing nonenumeration without repeater initialization |
| Pzqqt USB downstream | same current cf63f539 | `drivers/usb/phy/phy-msm-snps-eusb2.c`, blob`ea4f164f...`; `drivers/usb/repeater/repeater-i2c-eusb2.c`, blob`c963d7c6...` | Exact IP corroboration of U-Boot sequence, supplies and100us reset |
| Linux PHY/repeater | ed120558 | `drivers/phy/phy-snps-eusb2.c`, blob`af4fa17a...`; `phy-nxp-ptn3222.c`, blob`6cb79b5c...` | Qualcomm eUSB programming; PTN mandatory init has no I2C writes |
| Linux GCC/glue | ed120558 | `gcc-sm8450.c`, `dwc3-qcom.c`, `core.h` | Exact register/mask/reset/UTMI sequence |
| October clock patch | Sushmit Singh Rathore, v2,2026-10-20 | [Parent eUSB3 clkref to bi_tcxo](https://lkml.iu.edu/2610.2/11008.html), [series rationale](https://lkml.iu.edu/2610.2/07975.html) | Metadata fixes reported0Hz; hardware gate9c00c, not9c010; no new hardware mux/divider in patch |

Upstream HEAD resolved to `734bef548a96e8774d6eef5dfa2026c6edc4e80b`.
GitHub contents/raw requests returned429; the current upstream eUSB, GCC and
DWC3 core were subsequently retrieved through their Git blob/tree APIs.
The eUSB blobaf4fa17a is byte-identical to the pinned iLtanaka implementation.
FEMTO and PTN source were also retrieved through kernel.googlesource. **FEMTO is
not the eUSB register programming source**. The pinned iLtanaka base DTS still
advertises `sm8450-usb-hs-phy`/`usb-snps-hs-7nm-phy`, while its separate eUSB
implementation matches `sm8550-snps-eusb2-phy`. That mismatch cannot establish
Linux selects the right driver merely from the DTS names. The actual U-Boot
eUSB driver and captured downstream eUSB driver agree on the register sequence;
those supply the implementation. Do not call a software clock-rate report a
measured electrical clock.

## Exact Goodix startup

Current vendor call flow (`goodix_ts_core.c`):

1. `goodix_ts_core_init` selects panel, registers SPI and platform driver.
2. SPI probe selects Berlin IC type and registers the platform device.
3. `goodix_ts_probe`3542 parses DT; obtains GPIOs; initializes regulators;
   initializes/selects active pinctrl; calls `goodix_ts_power_on`.
4. `brl_power_on`176: optional enable-GPIO delays3/15ms apply **only if those
   GPIOs exist**. MARBLE has regulators. Enable IOVDD; wait30–31ms; enable AVDD;
   wait15–15.1ms; drive reset high; `brl_reset_after` returns immediately for
   non-Berlin-A; sleep `GOODIX_NORMAL_RESET_DELAY_MS`100ms.
5. `brl_dev_confirm`284 writes eightAA to10000, reads eight, compares exactly;
   at most3 attempts,5ms after unsuccessful comparisons. Transport errors return.
6. `goodix_start_later_init`2698 launches `goodix_later_init_thread`2628.
   **Vendor code tries config acquisition and the optional updater before its
   final version/IC-info reads**. It is inaccurate to draw a universal flow
   putting all firmware decisions after those reads. Update failure is logged;
   version/info validity gates stage2 and IRQ initialization.
7. Version/info/config-id comparison; `goodix_send_ic_config` only sends if
   config exists and ID differs; stage2 requests IRQ; event handling/zero ACK.

`goodix_ts_gpio_setup` requests reset output-low before power-on. XNU explicitly
asserts low before voting rails, holds it throughout settling, releases high,
and now waits100ms **before confirm**. Explicit vendor reset is low2ms then
high/caller delay. No Berlin-A C900/D807/D806/D006/D808 operations are added.
The previous extra100ms *after* confirm is removed: it could never repair an
early failed confirm. New XNU lower-bound sequence is2+30+15+100=147ms before SPI.

| Property | Vendor9916R | Previous XNU | New XNU |
|---|---|---|---|
| IOVDD/AVDD | L2C1.8V then L9C3.224V | same votes | same, preserved request/completion records |
| Settling | regulator30ms, then15ms |3ms,15ms |30ms,15ms |
| Reset state | output-low requested; release after rails | explicit low | explicit low, timestamped |
| Reset pulse/delay |2ms low for explicit reset; normal100ms |2ms low,4ms release |2ms minimum low plus settling;100ms release |
| SPI | mode0,8bits,MSB,CS0,max15MHz | mode0,<=9.6MHz | unchanged conservative clock |
| Read bytes | F1+BE32+FF FF FF+zero clocks | exact | exact; RX starts8, clocks8+n |
| Write bytes | F0+BE32+payload, TX only | exact | exact, clocks5+n |
| CS | one spi_transfer,cs_change0 | automatic1/3 params0 | unchanged single assertion |
| GENI | resident protocol1; FIFO or GPI depending IF | FIFO-only guarded | same guarded mode with persistent exact state |
| Confirm |10000,AAx8,3/5ms | same, before sufficient wait | same after100ms |
| Version |10014; additive U8 LE checksum; packed28bytes | checked | unchanged raw bytes persisted |
| PID/VID/sensor |patch_pid offset10,vid18,sensor23 | same | unchanged, raw diagnostic includes all |
| IC-info |10070; LE length includes checksum; variable arrays then misc | bounded1024; legacy191/extended schema | unchanged, length/raw/command/event addresses saved |
| IRQ | GPIO21 active-low |10ms polling | same, initial level/first16transitions saved |
| Event |head8,point8,count low nibble,ID high nibble,LE16 x/y | same | same, first snapshots saved |
| ACK | vendor after-event zero, including some bad-frame paths | accepted-only, three malformed stops | preserved accepted-only policy, no unverified command writes |
| Firmware/config | resident boot precedes confirm; optional updater/config later | none uploaded | none uploaded or flashed |

Berlin-D framing is indirect in `goodix_brl_spi.c`: READ_PREFIX_LEN=1+4+4,
non-BRA uses **READ_PREFIX_LEN-1** for transfer length and memcpy offset.
The symbolic dummy constant4 does not mean four dummy bytes on this IC.
Writes use one TX-only transfer. XNU's maximum transfer1032 includes prefix.

No requested Goodix binary was found in the local repository/dump filename
search or previously inventoried firmware-xiaomi-marble tree. Existing stock
log identifies usable resident firmware before optional config lookup fails.
Vendor updater existence is not evidence that RAM upload is required. No
persistent controller flashing, firmware upload, or blind config sending.

### FIFO/GPI decision and remaining boundary

Captured DT has TX/RX DMA cells for SE4; that does not prove its runtime mode.
Linux `spi_geni_init` reads FIFO_IF_DISABLE, requests DMA channels, and selects
GENI_GPI_DMA if available; enabled FIFO uses the tested packed FIFO transport.
Downstream/working sources establish GPI hardware, but not XNU ownership of an
inherited ring/context or a valid IOVA mapping for SID5b6. The SE ID4 in DMA
cells is not a raw hardware channel index. Linux `gpi.c` allocates instances,
event/transfer rings, CONFIG/GO/DMA TREs and mapped coherent buffers; it does
not simply fill the inherited channel4 with physical pointers.

No safe ring/context/domain takeover has been established for the ABL state.
This image consequently **does not implement GPI** or map translated SID5b6.
It never clears the RO FIFO-disable condition. A disabled FIFO now produces
MT_FAILED/MH_FIFO_DISABLED with FW/SFW,IF,DMA,status,FIFO geometry/counts,
M_IRQ/DMA_IRQ/clock values independently readable on screen/file. This remains
a possible hardware blocker, not a claimed solved dependency. Likewise no
missing GENI firmware is guessed/loaded. Enabled FIFO still refuses busy engine,
nonempty FIFOs or outstanding DMA before changing local mode.

## USB hardware comparison

Captured stock DT resolves PM8350's command-DB suffix **b**. Do not derive
`ldoa5`/`smpa10` from the PMIC marketing name. Its USB PHY phandles234/235
resolve to L5B/LDOC10; repeater3e/2fa to SMPB10/LDOB2. PM8350C GPIO7 is SID2,
peripheral8e. These are separate from the working keys' SID0/SID1 peripherals.

| Resource | Old XNU | Source-backed operation / new XNU | Source |
|---|---|---|---|
| PHY supplies | inherited | L5B880mV, L10C1200mV, ACTIVE acknowledged votes | captured DT hsphy@88e3000; downstream phy_power |
| Repeater supplies | inherited | SMPB10=1800mV; LDOB2=3080mV | stock phandles; downstream minimum3075mV, PMIC5 PLDO8mV step rounds3080 |
| Repeater reset | inherited | validate unique EE0 APID/SID2:8e/type10/LV-MV subtype; latch low, VIN1/pull-disable/medium/input+output, enable; release high after votes;1ms settle | stock pinctrl, Linux pinctrl-spmi-gpio, U-Boot repeater helper |
| Repeater I2C | none | none required for minimal attach; stock eye tuning61@08/00@07 documented but not guessed into another bus | PTN init only supplies/reset; U-Boot working minimal helper |
| eUSB ref | read9c010 | enable **9c00c bit0**, verify gate,19.2MHz PHY PLL configuration | gcc_eusb3_0_clkref_en; stock ref_clk; October patch |
| PHY reset | inherited | GCC22000 bit0 assert100us/deassert | gcc-sm8450 reset table; downstream phy_reset |
| PHY init | inherited |28 ordered masked writes, CPBIAS1, PLL0x190, tuning, suspend/sleep/SIDDQ/POR release | downstream msm_eusb2_phy_init; U-Boot qcom_snps_eusb2_usb_init |
| PHY ready | no validation | register readback for each masked write; no invented PLL-lock bit | sources define APB transaction status, not a generic ready flag |
| USB GDSC | read-only | clear SW_COLLAPSE bit0@49004; poll POWER_ON31,10ms | GCC GDSC register/source |
| Master | inherited | validate shared GPLL0 lock; own RCG49028/cfg4902c=0x105 (GPLL0 /3,200MHz); bound update1ms | parent map0/frequency table |
| Mock UTMI | inherited | own RCG49040/cfg49044=1 (XO19.2MHz), require read-only postdivider49058=/1 | GCC source |
| Clocks | read-only | enable/verify cfg49084,master49018,aggre49088,sleep49020,UTMI49024,eUSBclkref9c00c | GCC branches; board source rates |
| DWC BCR | inherited |49000 assert500us/deassert | U-Boot Qualcomm glue: at least6sleep cycles |
| UTMI-as-PIPE | missing | QSCRATCH08: DIS bit8;100us; SEL0+PHYSTATUS_SW3;100us;clear DIS8 | dwc3_qcom_select_utmi_clk |
| VBUS | late override | HS10 bits20/28; SS30 bit24, masked/readback before gadget | dwc3_qcom_vbus_override_enable |
| Role | requires inherited DEVICE | validate5533 ID, select/readback GCTL DEVICE2 | dwc3_set_prtcap |
| UTMI interface | inherited |8-bit,TRDTIM9; clearSUSPHY6/ENBLSLPM8 | core.h; SM8450 DT quirks |
| SMMU | bypass-only refusal invisible | same safe bypass parser; CR0/ID0 and matching SMR/S2CR saved; explicit translated/fault reason | ARM SMMUv2 source and captured SID0 |
| DMA | contiguousPA, width guard | unchanged; physical address/width saved before reset | existing gadget, cache operations preserved |
| DWC start | soft reset/EP0/RUN | bounded soft reset, event ring,EP0,RUN, now refuse DEVCTRLHLT timeout; first32events/16SETUP saved | existing SWEET protocol code, MARBLE hardware scope |

The driver does not retune shared GPLL0, globally disable SMMU, initialize QMP,
change root/UFS, or write unrelated streams. If USB SID0 translates, no safe
owned page-table/context has been established; it refuses with
MU_FAILED/MH_DMA_TRANSLATED and matching stream state. UFS working with its
bypass stream is not evidence SID0 is bypass. **No translated USB domain or
GPI domain implementation is claimed.** Hardware initialization can still fail
at a source/ownership/readback gate; that is preserved independently of USB.

New PHY step table in `marble_usb_hw.c` is deliberately small and auditable.
It follows downstream/U-Boot in leaving common override enabled, rather than
silently importing the newer mainline end-of-init clearing difference. All
polls have deadlines; uncertain SPMI transactions poison that reset interface;
uncertain ACTIVE TCS transactions quarantine their slot. RPMh records include
resolved address, TCS slot, exact address/data for voltage/mode/enable, issued/
complete status. Completion/readback is evidence of the request, **not a
measurement of regulator output voltage**.

## Persistent diagnostics and controls

`struct marble_hw_diag` has separate touch/USB stage, failed_at, enum reason,
errno, bounded gate string,256records per subsystem and drop counts. Each
record holds label,before,after,absolute timestamp; stage transitions are
records. Terminal reason survives worker exit and cannot be overwritten by
later generic exits. Single-CPU short RAM operations disable preemption;
formatting never logs/recurses. Normal console RAM ring remains separate.

`marblehwdiag=1` starts the diagnostic worker after successful root mount.
It does **not** replace Setup by default. Hold **Volume Up + Volume Down for
2seconds**, then release both. The static overlay shows both final gates and
register pages. Volume Up selects next page, Volume Down previous; both2s
returns to GUI. Power is not involved. The working key sampling/HID delivery
is unchanged; a two-line hook supplies already sampled volume states to avoid
racing duplicate SPMI observer transactions. Key HID events still propagate.

AppleCLCD's existing CPU-present path is paused only while overlay is active;
the timer redraws the page even without a new GUI frame. The same framebuffer
mapping is used; no new cache alias. Console output continues to RAM but its
framebuffer drawing is suppressed while the page is visible. GUI dirty state
is retained for restoration. Display dimensions, normalization, surfaces and
presentation geometry are unchanged. Screen and file use separate64KiB buffers.

A dedicated worker attempts `/private/var/tmp/marble-hwdiag.txt` at90,120,180,
300seconds, and on the explicit diagnostic gesture. Maximum16attempts/boot,
64KiB/snapshot. It uses vnode_open with no-follow, requires a regular file,
vnode_setsize, vn_rdwr, fsync and close. Failure records errno and boot/workers
continue. No raw sectors, partition changes, root-image changes or mounts.
The file is best-effort; the framebuffer is the primary USB-independent reader.
Absolute timestamps are counter ticks, not milliseconds; delay tests validate
requested minimum intervals. A live MU_RUN with zero events and watchdog
DCTL/DSTS snapshots means hardware initialization/start completed in software
but no bus reset has yet arrived. That does not establish physical attachment.

Enum stage ordering is defined in `bsd/dev/marble_hwdiag.h`; screen values are
numeric so they fit. Reason7=FIFO_DISABLED,12=DMA_TRANSLATED (see header for
exact ordinal list); gate text and failed_at are authoritative. No synthetic
injection is enabled. `marbletouchinit=1 marbleusb=2 marbleusblog=1` select the
physical implementations. Keep all previous GUI/root/CPU0 arguments.

## Validation and artifact handoff

Tests extract actual replayed source and use ASan/UBSan. Existing protocol,
FIFO, malformed-event fuzz, TCS and SMMU suites are extended, not replaced.
V3 tests cover full hardware ordering, each masked-write failure, source-lock/
postdivider refusal, RCG timeout, PHY values, UTMI ordering, RAM bounds,
terminal-state retention, screen guard words on12pages and VFS source bounds.
Host models do not measure rails, bus clocks, SPMI hardware or a physical finger.

Build/hash/CI details are appended after exact-commit CI and packaging. Existing
rollback images and exact Hello ADT are preserved. No physical phone command is
executed by the agent. This is an attempted hardware fix, **not a claim that
physical touchscreen or USB enumeration now works**.
