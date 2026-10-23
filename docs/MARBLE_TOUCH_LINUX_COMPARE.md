# MARBLE GT9916 transport versus working Linux — 2026-10-23

Physical result: Hello/display, side buttons and synthetic HID PASS. The
active-init image4c57ea14...86ba25 was physically tested: touch still FAILS.
No early register/refusal log survived. **IF_DISABLE_RO, FIFO_IF_DISABLE,
DMA_MODE_EN, pin readbacks and first failing gate are not observed.**
Do not turn this source comparison into a claimed physical diagnosis.

USB CDC-ECM/live logging is checkpointed first (MARBLE_USB_LOG.md). The final
combined test will preserve all existing images/root/ADT and use its logger.
The corrections below are implemented and locally validated; runtime results remain unmeasured.

## Primary repositories compared

| Repository | Pinned head / findings |
|---|---|
| iLtanaka/linux-marble | ed120558cd2c5f970edc44e1273a8d7b6caed825, main |
| Halhadus/linux-marble | c9f87aac17d306786d1d15f67d8bdd226770e27a, main |
| wsdsbyswq/linux-marble | same c9f87aa head |
| LazyBonesLZY/linux-marble | same c9f87aa head |
| marble-alarm/linux-marble | 55628035410272e5f12a0ecfa1a0bc0878835110; packaging repo, not kernel source; PKGBUILD pins iLtanaka c9f87aa |
| iLtanaka/firmware-xiaomi-marble | eb8f66daf42b856e5e1845848e2b42ea4eea2cdb; complete recursive tree1887 entries, not truncated; no Goodix/GT9916/touch blob paths |
| iLtanaka/alt-mobile-marble | f8c32df3e0ac4eb0b76dc337d90a36656fc8f162; README reports GT9916 touchscreen working |
| iLtanaka/marble-device-support | 0156b222de9def538a0cf297c8419195441f4db4; touchboost opens platform-990000.spi-cs-0-event |
| iLtanaka/u-boot-marble | 4e1c8502a39213eca383b11bdb716749c2953d76; ACM gadget/menu/board DTS audited for USB |

All four actual kernel trees' inspected spi-geni-qcom.c, qcom-geni-se.c,
gpi.c and goodix_berlin_core.c copies are byte-identical. SHA256 respectively:

```text
c077b59c400d66e1b14c5194c0f062c9d0752471ffe155ecf7ed0e9d71a586ed
249348128bcc6d6431bc4c7e37098c3c9b3f7035d6c608634200f87861c1699e
a89b8e2e2e3b4f38d607700d461f814affc4c2614713c951c14388f273499a5a
6ca187f3f9ce5d5710514af41a4c0dd715b2a482caa5cc6f0fdace82ce3b35eb
```

iLtanaka's newer MARBLE DTS differs only in a speaker GPIO52 routing change
from the three c9f87aa forks; touch, GPI and USB sections match. There is no
fork-specific hidden GT9916 protocol workaround in the compared files.

Primary file references, all at ed120558:

- [MARBLE DTS](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/arch/arm64/boot/dts/qcom/sm8475-xiaomi-marble.dts)
  and [SM8450 base/pinctrl/DMA DTS](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/arch/arm64/boot/dts/qcom/sm8450.dtsi).
- [SPI GENI](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/drivers/spi/spi-geni-qcom.c),
  [GENI helper](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/drivers/soc/qcom/qcom-geni-se.c),
  [registers](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/include/linux/soc/qcom/geni-se.h),
  [GPI](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/drivers/dma/qcom/gpi.c),
  [GPI config](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/include/linux/dma/qcom-gpi-dma.h).
- [Berlin SPI](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/drivers/input/touchscreen/goodix_berlin_spi.c)
  and [Berlin core](https://github.com/iLtanaka/linux-marble/blob/ed120558cd2c5f970edc44e1273a8d7b6caed825/drivers/input/touchscreen/goodix_berlin_core.c).

## Layer comparison and final source behavior

| Subsystem | Working Linux behavior | Previous XNU touchinit | Mismatch / correction |
|---|---|---|---|
| Rails | L2/vddio1.8V then L9/avdd3.224V, settle3/15ms | command-DB resolved active votes, same settling | Keep guarded vote helper unchanged; results unobserved |
| Reset | GPIO20 active-low, release after rails, wait4ms | physical low/high and one reset | Keep; not a proven current failure |
| TLMM data/clock16–18 | qup4/function1; **no explicit drive or bias properties** in base Linux pinctrl | forces6mA/no-pull from Android state | Change only mux, preserve other inherited settings as Linux does |
| TLMM CS19 | qup4/function1,6mA,bias-disable |16mA,pull-up | Correct masked value to0x84, not0x1c7 |
| Reset/IRQ20/21 | GPIO reset output/IRQ input; pull-up8mA board states | source-backed pull-up8mA | Keep |
| SE4 clocks | runtime power/clock/OPP, <=15MHz | owned GCC bits, XO selection/divider <=9.6MHz | Keep conservative lower rate, explicitly log selection; not a measured frequency |
| GENI firmware | resident SPI accepted; invalid protocol can load **SE firmware** | requires resident SPI protocol1 | Keep no-loader stop; distinguish SE firmware from Goodix firmware |
| Mode discovery | reads GENI_IF_DISABLE_RO/FIFO_IF_DISABLE | did not read; forced DMA_MODE_EN bit0 clear | Read/log before any mode write; FIFO only if bit0 clear |
| GPI DMA | FIFO-disabled prefers GENI_GPI_DMA, TX/RX dmaengine channels | no GPI implementation | Stop with explicit GPI/SMMU gate if disabled; do not pretend FIFO works |
| SMMU | gpi_dma0 stream0x5b6 retained; dma_alloc_coherent/dmaengine mapping | no GPI rings/mapping | No direct-GPI-DMA assumption or SMMU writes |
| Packing | geni_se_config_packing(8,4,true,true,true) | constants7f8fe/ffefe | Constants actually agree; derive from Linux vector fields and test |
| Word length |8-MIN_WORD_LEN(4) =4; byte granularity0 |4/0 | Keep, explicitly test |
| SPI speed | max15MHz, actual clock selected per transfer | XO/divider <=9.6MHz | Conservative slower clock, no PLL changes |
| CS | normal single transfer, cs_change0, params0, automatic CS0 | opcode8/assert + opcode3/FRAGMENTATION + opcode9/deassert | Remove explicit CS commands and fragmentation |
| Read prefix | F1+BE32+three FF dummy+payload, TX/RX opcode3 | same prefix | Keep framing; fix master-command semantics |
| Write prefix | F0+BE32+payload, TX-only opcode1 | same prefix, full-duplex engine | Use Linux TX-only command for writes; no extra RX requirement |
| Version |0x10014, checksum/compatible PID | same, no exact VID whitelist | Keep |
| IC-info |0x10070, structure/length/checksum | bounded supported stock/extended schema | Keep until physical metadata proves otherwise |
| Event read |26 first, extra contacts after |26 first, remaining only | Keep |
| IRQ | GPIO21 level-low IRQ |10ms GPIO polling | Allowed first-input design; keep |
| ACK | clear status after handling; upstream also clears some bad frames | accepted-only ACK; three bad frames stop | Keep user's stricter no-invalid-ACK policy |

No higher-level Goodix protocol, Apple HID, key, display or root fix is justified
by this source comparison. A corrected FIFO path still cannot work if the
inherited serial engine exposes only GPI. The next log must decide that.

## Firmware distinction and runtime evidence boundary

Berlin core explicitly supports already programmed firmware/config for A/D.
The complete firmware-xiaomi-marble tree has no external Goodix blob. Android
saved evidence at2.209s confirms device connect/ROM BERLIN/PID9916R, even before
its optional config-file lookup fails ENOENT. No Goodix firmware/config uploader
is required for ordinary Linux operation or added to XNU.

This does **not** mean every GENI controller needs no firmware: Linux's
spi-geni-qcom probes protocol, and can call geni_load_se_firmware for protocol0.
That is Qualcomm sequencer code, not GT9916 firmware. XNU will identify a missing
resident SPI protocol and stop; it will not write arbitrary sequencer RAM.

Saved Android log shows spi_geni990000 probe, tx_fifo16/rx_fifo16/width32 and
successful device confirm. It does **not** report IF_DISABLE_RO, DMA_MODE_EN or
which transfer path was selected. FIFO geometry alone cannot establish mode.
No saved working Linux runtime mode dump was found locally. GPI is therefore
source-supported and possibly required, not yet physically proven required.

Linux actually contains a FIFO fallback when FIFO_IF_DISABLE is set but GPI
channel acquisition fails (except EPROBE_DEFER). That fallback is not evidence
that our inherited state safely supports FIFO. This build deliberately refuses
that case instead of clearing the RO/interface-disable condition or loading FW.

## GPI ownership and safe deferral

Base DTS gpi_dma0@0x00900000 size0x60000 has12 channels, mask0x7e and apps-SMMU
SID0x5b6; SE4 dmas cells are TX(0,4,SPI)/RX(1,4,SPI). The4 is SE ID, **not proof
of an inherited GPI instance ownership index**. Linux allocates channels,
coherent DMA event/transfer rings, programs context ownership and uses16-byte
CONFIG/GO/DMA TREs with physical/DMA address and completion/error validation.
Its coherent DMA addresses are IOMMU-domain addresses, not necessarily XNU PAs.

No current XNU channel/event ownership, domain, safe IOVA aperture, identity
mapping or bounded teardown has been established. Thus no GPI driver or SMMU
bypass is introduced. Per-channel GPI registers are not blindly read as though
instance4 belonged to us. A FIFO-disabled log will explicitly identify this
remaining dependency. Only source-backed synchronous GPI implementation after
that evidence is appropriate; firmware uploads are unrelated.

## Final source diagnostics and validation

Before any mode write, mode dump includes FW0x68/SFW0x6c, protocol,
IF_DISABLE_RO0x64 and FIFO_IF_DISABLE bit0, STATUS0x40, DMA_MODE_EN0x258,
TX/RX HW FIFO geometry0xe24/0xe28, counts0x800/0x804, M_IRQ0x610,
DMA_TX/RX_IRQ0xc40/0xd40, clock0x48 and selection0x7c. Physical values are
UNKNOWN; the USB log is the next source of truth. An enabled FIFO and idle
DMA/engine are rechecked immediately before FIFO selection writes.

Raw TLMM config is logged before and after each SPI pin change. GPIO19 is
`(before & ~0x1ff) | 0x84` (mux1, drive=(6/2)-1=2, pull0). Old source
programmed masked0x1c7 (drive7=16mA,pull3); that is not an observed raw
register value. GPIO16..18 are `(before & ~0x3c) | 4`, preserving drive,
bias, OE and unrelated bits. Base TLMM@f100000 and stride1000 agree with
both mainline SM8450 and captured CAPE bank offset. Physical before/after
register values cannot be reported until the next manual boot.

The8-bit packing is derived from START shift5, DIR4, LEN1, STOP0 and vector
stride10, yielding cfg0=0x7f8fe/cfg1=0xffefe for TX and RX. Byte granularity0,
word length4, mode0, loopback0, CS0 and no CS-toggle/fragmentation.
Writes use TX-only1, reads TX|RX3; each Goodix message owns one automatic CS
interval. Current transport limits remain1032bytes and5ms, uncertainty
quarantines rather than reset/retry. FIFO-disabled state never clears DMA
mode or writes a GPI/SMMU context. No new higher-level Goodix operation.

Tests extend tools/test-marble-input.py with1032 read and1032 write FIFO
lengths, automatic-CS opcode/zero params, exact read/write prefixes, confirm,
version/IC-info checksums, all0..10 contacts, no-invalid-ACK and100000 malformed
cases. New extracted-function tests cover all65536 GPIO19 input configs,
mux-only data pins, FIFO disable/unreadable/busy/outstanding-DMA refusal with
zero writes, Linux-derived packing/word length. Existing power/reset/confirm
and RPMh ownership/quarantine suites remain passing. USB descriptor/ring/SMMU
tests are included. Complete82-patch replay/source equality, CI-header arm64
compiles and non-MARBLE preprocessing equality pass; physical results pending.

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
