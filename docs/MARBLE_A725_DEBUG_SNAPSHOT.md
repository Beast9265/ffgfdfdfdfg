# 0111 inherited debug snapshot and host GMU preparation

## Read-side-effect audit

An isolated `marblegpu=11 marblegpuvisual=1` mode reads all nine shared
measurement registers, twice1ms apart, without acquiring or changing hardware.
No active debug measurement or GMU startup is implemented.

Authority: Qualcomm core-kernel992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0,
[clk-debug.c](https://github.com/crdroidandroid/android_kernel_xiaomi_sm8450/blob/992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0/drivers/clk/qcom/clk-debug.c),
[debugcc-waipio.c](https://github.com/crdroidandroid/android_kernel_xiaomi_sm8450/blob/992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0/drivers/clk/qcom/debugcc-waipio.c),
and matching GPUCC/GCC regmaps. Live DT uses these Cape/waipio controllers.
The source contracts justify ordinary non-destructive reads under the existing
qualified configuration bus; no hardware TRM providing broader guarantees
was obtained. Unknown registers are excluded.

| Register | Physical address | Why the read is justified |
|---|---|---|
| GPU selector |03d99564 |clk_debug_mux_get_parent reads selection; set_parent uses masked RMW |
| GPU divider |03d99270 |set_parent uses regmap_update_bits: normal read before masked update |
| GPU debug gate |03d99274 |enable/disable_debug_clks use masked RMW of bit0 |
| GCC selector |00172000 |same mux get_parent/RMW contract |
| GCC divider |00172004 |same post-divider RMW contract |
| GCC debug gate |00172008 |same branch RMW contract |
| XO/4 gate |0017200c |measure_rate explicitly regmap_reads this word before setting enable |
| Counter control |00172038 |run_measurement repeatedly RMWs command/config fields; clear is a WRITE to CLR_CNT21, not a read |
| Counter status |0017203c |run_measurement polls it repeatedly and reads count again after stopping; reads do not acknowledge/clear DONE or count |

These driver accesses are through the uncached MMIO regmaps, not a software
register shadow. The reference yukoimi/hackios-marble
8e50e532f09b3042165048c3c72e04b5a8e68898 also snapshots the debug controls
and polls STATUS, but its active transaction is not imported.

Mode11 verifies AT/PAR read/write translations and Device-nGnRnE attributes
for every target and GCC_CFG_AHB00181004 before any register read. AT write
preflight is not a device store. Both passes first require inherited CFG_AHB
bit0 and reject all-ones. The device-read allowlist is exactly the nine words
above plus that configuration gate:20 reads total on complete capture.
No writes, clock/rail votes, counter start/stop/clear, mux programming or AHB
enable attempt occurs. No SMMU/GMU/TCM execution aperture is accessed.

Busy, DONE, nonzero counts or changing words are preserved and reported as
observations. No clock/ownership readiness is inferred. The changed-word mask
uses table order above, bit0=GPU selector through bit8=STATUS. Existing firmware
structure/hash preflight remains mandatory. Modes0–10 retain their source
functions and semantics; only the accepted mode range is extended.

## Host preparation integrated in this change

[The portable library](../gpu/a725/PROVENANCE.md) individually adapts A725 VMA,
preallocation, permissions and payload-placement rules, with unmodified
AdrenoFirmware and ArmSmmu4K parser/table-builder sources and adjacent licenses.
It is host-integrated, ARM64-compiled, and NOT linked into the kernel.

Implemented: strict factory-profile GMU parsing; six reservations/51 pages;
RAM payload staging with zero padding;135-word TCM payload placement in an
ordinary32KiB shadow preserving other bytes; inactive native4KiB SMMU tables
with explicit permissions, address/capacity/alias checks and SID5/flags400
metadata. No device access or activation follows a successful plan.

Every live-operation guard is fixed disabled, even with all evidence bits set.
There is no implementation that boot arguments can unlock. No new kernel
allocation, live SMMU context/stream/TTBR programming, hardware TCM load,
cache maintenance, reset/firmware start, HFI, GX or CP is present.
This is preparation infrastructure, not a working GMU or GPU driver.

The existing firmware validator verifies actual factory file identities before
host tests. Structure validation alone is not authentication. The36-bit output
profile and WB/shareability choices follow the same-phone reference and still
need physical verification before any live device mapping.

Host tests use actual local firmware without committing its bytes. ASan/UBSan
cover every truncation, malformed/overlapping metadata, invalid payload ranges,
capacity failure, guard bytes, exact RAM/TCM shadow content, every generated
4KiB leaf/permissions, table/data alias refusal and permanently disabled live
operations. The upstream source identities and licenses are recorded locally
in gpu/a725/upstream/SHA256.json and adjacent license files.

## Physical screen and acceptance

After a user-performed cold reboot, photograph the ten-second
`a725-debug-inherited-v1 (mode11)` screen. It shows MAPS10/10, REFUSAL,
CFG READS, configuration gate snapshots, target9/9 snapshot counts, all nine
S0/S1 words, changed mask and decoded EN/CLR/DONE/count. Missing reads display
NOT READ. Config fields are valid only below the reported CFG READS count.

Capture success: REFUSAL0, CFG READS2, counts9/9, CAPTURE COMPLETE and terminal
`stage=11 stop=DEBUG_INHERITED_SNAPSHOT result=CAPTURED writes=0`, then normal
SpringBoard, touch/gestures and SMP8. A busy/changing engine may still be
captured successfully; it blocks active measurement and must not be stopped.
The screen always labels ownership/AHB clock state unresolved.

Failure: mapping/gate refusal, all-ones read, partial capture, hang/reboot or
baseline regression. Photograph, stop, cold reboot and analyze before another
GPU experiment. This mode acquires no hardware lease and has none to unwind;
it does not clear prior retained state, so cold reboot is required before it.
No automated phone operation is permitted. Known-good recovery is unchanged.

## Exactly what evidence is needed next

1. Mode11's nine raw snapshot pairs, map/refusal/read counts, busy/changed
   observations, and normal SpringBoard/touch result. Stable disabled controls
   are an input to ownership analysis, not exclusive ownership proof.
2. An exclusive debug/reference lease and qualified live reference/control
   measurement, with bounded stop and owned-field restoration verified before
   any future AHB interpretation. No active measurement is enabled here.
3. Independent AHB clock activity under qualified CX/HUB roots, without forcing
   AHB or changing GPLL0. Unpowered CLK_OFF reports are not powered evidence.
4. Before live GMU memory work: clocks/power/SCM/reset quiescence ownership,
   safe SMMU access plus IDR geometry/output width, exact SID5 context/stream
   leases, owned backing/table buffers, cache visibility/coherency, bounded
   invalidate/detach and retention on uncertainty. No CB0 ownership is assumed.
5. Before a device firmware copy/start: pinned identities, verified mappings,
   guarded TCM snapshot/readback/rollback and retained backing on uncertain
   quiescence, secure prerequisites, then separately gated CM3 readiness/HFI.
