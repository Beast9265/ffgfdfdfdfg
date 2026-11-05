# 0110: read-only AHB mapping audit

## Physical 0109 evidence

User reports `a725-ahb-latch-v1` mode9, source
`ea712baa8d0e42cfcb981350c8c25982b0d160da`: CFG_AHB00000001,
REFUSAL000, WRITE1; HUB AHB/CX dividers0, HUB_AON/HUB_CX_INT1;
AHB before and0/1/10/100/200us all0; AHB TIMEOUT, errno60, RETAINED1.
iOS subsequently booted normal SpringBoard with touchscreen working.
This supersedes the pending0109 handoff. Cold reboot before any next test.
The observation proves the NS software view stayed0, not that AHB is disabled,
that the store never reached the controller, or that a master executed.

## Audit conclusions

| Question | Evidence and remaining uncertainty |
|---|---|
| Physical address / mapping | Live factory DT has qcom,cape-gpucc reg03d90000+a000. Exact pinned gpucc-waipio.c uses AHB offset911c, hence03d9911c. Re-fetched driver byte-matches the previously audited copy. ml_io_map -> io_map with VM_WIMG_IO; pmap maps non-DRAM IO as Device-nGnRnE. All base/offset/length arithmetic is in range and aligned. AHBCBCR911c and successful HUB/GMU root offsets are in the same4KiB page03d99000, arguing against a page permission error; this is inference, not a live translation result from0109.0110 checks its own live mappings. |
| Do writes reach controller? |0108/0109 use a volatile32-bit store followed by DSB SY, then raw volatile reads. Root writes through the same GPUCC mapping succeeded previously. These support general controller reachability, not acceptance of the specific AHB write. Neither a store instruction nor a CPU permission preflight proves interconnect/security/controller acceptance. |
| Different readback? | Driver enable_mask BIT0, no inversion, clk_branch2_ops. clk_is_enabled_regmap reads bit0, but clk_branch_wait with BRANCH_HALT_DELAY merely delays10us and returns0; it does not check bit0/CLK_OFF. A write ignored by the hardware could still satisfy that callback's software contract. No authority establishing AHB as write-only/RAZ or guaranteeing bit0 latch was found. |
| Missing power/reset/parent? | AHB's parent is RO divider9430[3:0] -> HUB root93ec/93f0. Divider ops have no enable/set-rate; AHB has no branch-specific voltage table.0109 guarded CX/root/parent, observed both HUB branches1, dividers0. No documented AHB-specific reset, extra vote or preceding sibling gate was identified. Do not pulse reset, write divider, enable GX or import GPUCC probe writes as a speculative fix. |
| Firmware/security ownership? | No secure takeover operation is specified for this branch in the audited driver. No SM7475 hardware TRM/security ownership contract was obtained. Restricted/RAZ or overridden NS access remains a hypothesis. PAR does not interrogate that policy. |
| Ordering/barriers? | Linux ARM64 __raw_writel is STR32; writel adds __iowmb (dma_wmb) before the store. Our path uses volatileSTR32 plus DSB SY after the store. Mapping is requested strongly ordered Device. No source evidence identifies another required AHB barrier or write sequence. Do not infer that a stronger completion barrier forces a protected gate to accept a write.0110 issues no device store. |
| Is the extra readback appropriate? | It is a stricter conservative diagnostic condition than the vendor delay-only enable return. Failure is not proof of clock-off. Removing it would establish callback completion only, not a working AHB clock. Existing modes are preserved;0110 reports unresolved state instead of promoting zeros to ACK or failure. Independent evidence is required before changing the readiness policy or progressing. |

## Pinned sources

- [Qualcomm core-kernel992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0](https://github.com/crdroidandroid/android_kernel_xiaomi_sm8450/tree/992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0):
  drivers/clk/qcom/gpucc-waipio.c, clk-branch.c, clk-regmap.c,
  clk-regmap-divider.c, debugcc-waipio.c; arch/arm64/include/asm/io.h.
- Cape DT2e649a7f3e762903eedad43d8256b91e28b512d8; local factory DT identity
  and hardware ranges are recorded in MARBLE_A725_BRINGUP.md. Device dumps
  remain outside git.
- [yukoimi/hackios-marble8e50e532f09b3042165048c3c72e04b5a8e68898](https://github.com/yukoimi/hackios-marble/tree/8e50e532f09b3042165048c3c72e04b5a8e68898)
  remains branch HEAD. Its clock_preflight checks inherited GCC_CFG_AHB;
  marble_gpu_power.h writes AHB then checks other branch statuses; it does not
  independently verify the AHB enable latch. Its later clock transaction
  measures GMU/HUB_CX_INT. Those historical results do not prove our AHB gate.
- Replayed XNU: osfmk/arm64/machine_routines.c ml_io_map;
  osfmk/arm/io_map.c alignment/length/mapping; osfmk/arm/pmap/pmap.c
  wimg_to_pte; osfmk/arm64/proc_reg.h MAIR_DISABLE;
  machine_routines_asm.s mmu_kvtop/mmu_kvtop_wpreflight.
- [Arm architecture register specification](https://documentation-service.arm.com/static/6023d5362cb3723f202089b8)
  defines AT S1E1W as a translation with EL1 write permissions, not a device
  store. [Arm PAR register description](https://documentation-service.arm.com/static/5e7b6c837158f500bd5c03fc)
  identifies F, PA[47:12] and memory attributes[63:56].

## Smallest next hardware step

Opt-in `marblegpu=10 marblegpuvisual=1`, build `a725-ahb-readonly-v1`.
Modes0–9 are unchanged apart from accepting mode10. No MMIO write, rail vote,
AHB enable attempt, power/clock/reset transition, SCM, SMMU, GMU firmware/HFI,
GX or CP operation. No userspace/touch/SMP/display/rootfs change.

Using the existing ml_io_map API/ranges, capture AT S1E1R and AT S1E1W/PAR for
AHB03d9911c, HUB_CFG03d993f0, GCC_CFG00181004. Like XNU's mmu_kvtop, mask
IRQ/FIQ briefly during AT/PAR access, then restore DAIF; also preserve PAR.
These instructions can walk CPU page tables; they do not store to a device.
Require no translation fault, exact output PA and Device-nGnRnE attribute00
for both access checks. Any mismatch refuses all MMIO reads, without remapping.

Then, twice1ms apart: read inherited GCC_CFG_AHB first, require bit0 and reject
all-ones; only then read12 previously audited GPUCC control/status registers.
The read allowlist is AHB,CX_GDSCR,CX_HWCTRL,GX_GDSCR,AHB/CX dividers,
HUB_AON,HUB_CX_INT,HUB_CMD/HUB_CFG,GMU_CBCR,CXO_CBCR. Stop on all-ones;
never read SMMU/GMU execution apertures or unclassified error/reset registers.
Each pass is bounded, with no retry. No hardware lease is acquired, so no
clock rollback or retained-resource path is needed in this mode.

Snapshots represent inherited cold-boot state, NOT0109's powered state. Do
not interpret different CX/root/branch values as a powered regression. Zeros
are reported as observations. Incomplete reads are counted and marked NOT
READ, not synthesized successful samples. A capture result NEVER says AHB PASS.

Screen: mapping output PAs and raw R/W PAR, REFUSAL, valid config read count,
GCC_CFG S0/S1, GPUCC read counts,12 named S0/S1 rows, CAPTURE COMPLETE/REFUSED,
and `AHB CLOCK STATE UNRESOLVED`. PA fields are valid only when PAR.F=0.
Refusal bits01/02/04 correspond to AHB/HUB_CFG/GCC_CFG translation,08 to
configuration gate,10 to all-ones register read.

Expected diagnostic completion: correct mapped PAs/attributes, REFUSAL00,
CFG READS2, GPUCC READ COUNTS12/12, CAPTURE COMPLETE and terminal
`stage=10 stop=MMIO_AUDIT_COMPLETE result=CAPTURED writes=0 AHB_STATE=UNRESOLVED`,
then normal SpringBoard/touch/SMP8. AHB0/0 is acceptable observation; it does
not clear the clock gate or authorize firmware startup.

Failure: mapping fault/mismatch, unexpected attribute, missing configuration
gate, all-ones capture, hang/reboot or baseline regression. Photograph the
entire screen, stop, cold reboot and analyze before another GPU experiment.
0110 does not re-enable or release any resources retained by a prior boot:
a cold reboot is required BEFORE this image, regardless of working SpringBoard.
Known-good manual recovery remains marble-smp8-test.img; never flash partitions.

## Independent evidence needed before proceeding

A concrete measurement route exists in the pinned debugcc-waipio.c:
`gpu_cc_ahb_clk` selector0x16 at GPUCC debug mux9564; GPU debug post-div9270,
measurement branch9274, then the GCC debug measurement path. This is independent
of AHB CBCR bit0 readback and differs from reference's GMU selector1e and
HUB_CX_INT selector20.0110 DOES NOT configure or run this measurement engine.

A future bounded measurement lease needs separate ownership/idle-engine
checks, pinned divider/scaling/counter semantics, known live reference/control
clock, at least two integration windows with advancing counts, expected
AHB-parent/divider relationship, and exact restoration/retention of the shared
mux/gates/counter and power parents. Measure without repeatedly forcing AHB.
A nonzero count alone can select the wrong signal; clock measurement alone
also does not prove a GMU/AHB consumer transaction. Do not advance to firmware
from an uncorroborated counter.

Other sufficient authority would be applicable SM7475 TRM/secure policy
explicitly explaining NS AHB readback, corroborated by owner-controlled clock
measurement/trace or documented harmless peripheral access under a known
lease. Random GMU/SMMU reads can fault/reset the phone and are not acceptable
independent tests. CPU PAR success cannot substitute for bus acceptance.
Until that evidence is obtained, the AHB state and startup gate stay unresolved.

## Local validation

Actual-C PAR decoder and capture tests cover read/write translation faults,
wrong PA, normal/posted attributes, configuration gate loss, every all-ones
snapshot read, zero AHB snapshots,26-read allowlist and visual-only delay.
The extracted module has no device-write/power API. ARM64 object disassembly
verifies AT S1E1R/W, ISBs and DAIF/PAR preservation. Host AT is mocked; only
physical testing can supply actual translation/register values.

## Verified build and recovery

Source `97796d814f88055a930c5bbf06b1379c5658fcdf`;
one successful exact-commit [CI42040333616](https://github.com/Beast9265/ffgfdfdfdfg/actions/runs/42040333616),
13.5/DEVELOPMENT/MARBLE/keep_going=true. Full110 patch replay/source equality,
ARM64 Mach-O object/disassembly, SWEET exclusion, modes0–9 preservation,
actual-C mode10 and0105–0109 regressions,12 firmware/ADT/boot tests and final
boot-v4/payload/arguments/SMP8/all-six-firmware checks PASS.

Distinct image: `shim/out/marble-xnu/marble-a725-ahb-readonly-test-42040333616.img`.
Final verified copy: `shim/out/marble-xnu/latest-marble-xnu.img`.

- Kernel SHA256: `420fbfc163bb36ded5fc7118091606b341cbc7d5ef1381917a83bf14800afb38`
- Payload SHA256: `702e1ae03ddf715d765842b591c9ebd9a51978b3374ae1dc53f86f90b526194e`
- Image SHA256: `6e19def8477a249ae6688046c1eb31ddde94a71d26641e2d8125ea84b696eb24`

After a user-performed cold reboot, manual only:

```sh
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
```

After any refusal/failure/hang, stop and cold reboot before recovery or another
experiment. Known-good manual recovery:

```sh
fastboot boot ~/ios-marble/shim/out/marble-xnu/marble-smp8-test.img
```

0105–0109 and known-good recovery hashes were verified unchanged. No phone,
rootfs or partition operation performed. Physical0110 remains pending;
AHB/controller state and permission to start firmware remain unresolved.
