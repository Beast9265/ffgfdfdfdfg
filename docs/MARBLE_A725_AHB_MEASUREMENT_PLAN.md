# 0111 investigation: active measurement withheld

No mode11, kernel patch0111, hardware write path or new boot image is added.
The source route is verified, but the requested pre-write ownership/current-state
and restoration requirements are not satisfied by the available physical data.
AHB state and the GMU startup gate remain unresolved.

## Updated physical evidence

The user confirms physical0110 source97796d814f88055a930c5bbf06b1379c5658fcdf:
REFUSAL00, CFG READS2, GPU snapshots12/12; AHB/HUB_CFG/GCC_CFG mappings
03d9911c/03d993f0/00181004; AHB0/0, GCC_CFG1/1; no device writes or votes.
SpringBoard, touch and gestures subsequently worked, with no observed regression.
This supersedes the pending0110 statements in historical handoffs.

Without GPU rail votes, the user observed CLK_OFF bit31 set for HUB_CX_INT,
GMU_CBCR and CXO_CBCR. Powered0109 had HUB_CX_INT00000001; its GMU/CXO stages
were acknowledged by checks requiring bit0 and clear bit31. Full raw powered
GMU/CXO words were not supplied here. The difference is consistent with
power-dependent branch state/visibility; it is not a regression or proof of
AHB activity. AHB's delay-only branch semantics differ from those HALT checks.
Both0110 and0109 reported AHB0, so this comparison does not resolve its gate.

## Exact pinned source

Qualcomm core-kernel revision
[992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0](https://github.com/crdroidandroid/android_kernel_xiaomi_sm8450/tree/992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0/drivers/clk/qcom):
debugcc-waipio.c, clk-debug.c/h, clk-rpmh.c, clk-regmap.c and gpucc-waipio.c.
Re-fetched sources are cached outside git in research/a725-0111.
Live DT identifies qcom,cape-gcc, qcom,cape-gpucc, qcom,waipio-debugcc and
qcom,waipio-rpmh-clk; device dumps remain outside git.

Same-phone comparison:
[yukoimi/hackios-marble8e50e532f09b3042165048c3c72e04b5a8e68898](https://github.com/yukoimi/hackios-marble/tree/8e50e532f09b3042165048c3c72e04b5a8e68898),
marble_gmu_clocks.h and clock/power guards. Its active measurement uses GMU1e
and HUB_CX_INT20, not AHB16. Its historical results do not establish ownership
or clock activity in our current boot. Patches0108–0110 were also reviewed;
none captures the shared debug measurement state listed below.

## Requirements audit

| Requirement | Finding | Status |
|---|---|---|
| 1. Exact registers | GPUCC base03d90000, GCC base00100000; addresses below | Source established |
| 2. AHB selector | gpu_cc_debug_mux parent gpu_cc_ahb_clk maps to16; GCC routes GPU debug mux at16e | Source established |
| 3. Ownership/current state |0110 did not read the muxes, gates, CTL or STATUS | Missing physical evidence |
| 4. Other driver | Reviewed replayed XNU driver/address scan found no debug-engine writer; Linux uses clk_debug_lock/clk_reg_lock, which coordinate Linux callers only | No identified XNU owner; inherited/firmware ownership not established |
| 5. Reference | Board XO76.8MHz -> waipio bi_tcxo /4=19.2MHz -> counter XO/4=4.8MHz | Nominal source chain established; live availability/control not measured |
| 6. Procedure/timeout | Source clear/start/done/stop protocol and two windows known; vendor wait is unbounded | Needs bounded port and controlled stop verification |
| 7. Safe restoration | Source manipulates shared settings and command bits; no current snapshot or independently verified stop/restore behavior in this boot | Not established |
| 8. Failed restoration | Proposed quarantine/retention/no retry/cold reboot policy below | Defined policy only; no active transaction implemented |

## Register and scaling inventory

| Role | Physical address | Fields used by source |
|---|---|---|
| GPU debug selector |03d99564 |[7:0], AHB16 |
| GPU post-divider |03d99270 |[3:0], program1 for /2 |
| GPU debug branch |03d99274 |bit0 |
| GCC debug selector |00172000 |[9:0], GPU route16e |
| GCC post-divider |00172004 |[3:0], program1 for /2 |
| GCC debug branch |00172008 |bit0 |
| XO/4 reference branch |0017200c |bit0 |
| Counter CTL |00172038 |terminal count[19:0], CNT_EN20, CLR_CNT21 |
| Counter STATUS |0017203c |DONE25, raw count[24:0], read-only |

No GPU/GCC pre-divider table applies to this route in the pinned source.
Both debug muxes have post_div_val2; total output scale is4. GPU_CC_AHB_CLK
itself is03d9911c, parent HUB root via read-only9430[3:0]+1. That branch is
NOT a permitted write target for any proposed measurement transaction.

The live DT board oscillator is76.8MHz, not19.2MHz. clk-rpmh.c's waipio
bi_tcxo uses div4 and recalc_rate returns parent/div. debugcc's xo_clk_src
references that provider. The additional measurement divider gives4.8MHz,
matching clk-debug.c TCXO_DIV_4_HZ. This establishes nominal scaling, not
independent confirmation that the reference branch is running in this boot.

Vendor run_measurement: clear CNT_EN; assert CLR_CNT; delay1us (three4.8MHz
reference cycles fit); clear CLR_CNT; set terminal count; set CNT_EN; wait
DONE; clear CNT_EN; read25-bit result. It uses an unbounded while loop.
Windows1000/20000 hex correspond to4096/131072 reference ticks, nominally
0.853333/27.306667ms. A future40ms wall-clock deadline per window is a proposed
bound, not a device-validated guarantee. Do not copy the IRQ-masked unbounded
vendor wait into the working iOS path.

The source rate formula for the full window, including both debug /2 stages:
`floor(((count*10+15)*4800000)/(131072*10+35))*4` Hz, using64-bit arithmetic.
Two-window advance/slope and a known live control signal are also needed.
Synthetic examples:19.2MHz gives approximately4098/131074 counts;150MHz gives
32026/1024026. These are model values, NEVER physical results. Equal counts
or a timeout without valid reference/control cannot distinguish clock-off,
a stale counter, wrong route or failed measurement hardware.

## Exact missing evidence before an active test

1. Stable read-only snapshots of all nine debug registers above in a known
   cold-boot state, and again in the intended powered/root-qualified state.
   Include CNT_EN/CLR_CNT, both debug branch enables, XO/4 enable, mux/divider
   values and STATUS.0110's unrelated snapshots cannot substitute for these.
2. An ownership account permitting exclusive use and disposal of the previous
   counter result. Disabled bits/stability alone do not prove ownership; a
   software mutex cannot exclude boot/security firmware. Refuse an inherited
   enabled/busy/unknown owner rather than toggling its bits.
3. A safe reference acquisition/control phase: Linux explicitly prepares the
   XO provider before enabling XO/4. Either qualify an inherited reference
   lease or audit its exact owner/vote lifecycle; do not pulse an inherited
   XO vote. Verify a known live control, two window durations/count advance,
   route readbacks and consistent scaling before interpreting AHB counts.
4. A bounded stop/restore contract. DONE is completion, not an ownership/idle
   lock. CTL contains commands, not just passive configuration. Require stop
   and clear control to be verified before changing routing/dividers or
   withdrawing acquired clock/power parents. STATUS is not restorable by
   writing back its old count, and must remain read-only.

The yukoimi count helper adds a40ms poll but clears CNT_EN without validating
that stop before outer cleanup. Its restoration writes whole saved words;
that can overwrite a concurrent owner's changes. The vendor query also leaves
mux selections changed and does not preserve all inherited gate settings.
Neither implementation is an independently proven rollback for our image.
Do not import either transaction unchanged.

## Required behavior of a future transaction

After ownership is established, snapshot only stable controls; reject any
inherited active engine/unknown state. Serialize all in-tree callers and
preserve unrelated bits. Do not modify GPLL0 config/vote or force AHB.
Acquire only permitted debug/reference leases inside already qualified power/
root leases. Measure a live control and AHB with bounded two-window sampling;
no retry after timeout, lost guards, unexpected owner or inconsistent result.

Stop/verify counter first. Restore only owned fields in a documented reverse
order and verify them; release acquired gates and enclosing parents last.
If stop/restoration is uncertain, retain acquired debug/reference and enclosing
root/rail resources; do not reset the shared engine, cut parents or continue
to GMU/HFI/GX/CP. Report RESOURCE RETAINED, allow only the established diagnostic
handoff, and require cold reboot plus analysis before another GPU experiment.
This is a proposed policy, not a hardware-tested implementation.

## Host work and validation

`tools/marble-a725-measurement-audit.py` reads source files only. It cross-checks
selector-table alignment, register/mask/shift/divider values and nominal XO
chain. It always reports writes_authorized=false/hardware_observed=false.
Its counter arithmetic reports COUNTS_CONSISTENT_ONLY, never AHB PASS.
Unit tests and mutation tests cover wrong selectors/offsets/reference, malformed
tables, timeout flags, no advance, saturation and inconsistent windows.
Those tests cannot establish ownership or restoration on the phone.

Revalidated unchanged kernel source: full110-patch strict reverse/replay and
source equality; ARM64 MARBLE Mach-O object compile; SWEET exclusion compile;
actual-C0105–0110 refusal/timeout/retention regressions all PASS. Existing0110
packaging was independently rechecked: boot-v4/locator/payload/arguments,
SMP8, all six firmware digests, latest/recovery hashes all PASS.

No new CI run or image is justified for this host-only audit. The preserved,
physically tested0110 image remains:
`shim/out/marble-xnu/marble-a725-ahb-readonly-test-42040333616.img`, SHA256
`6e19def8477a249ae6688046c1eb31ddde94a71d26641e2d8125ea84b696eb24`.
Its source is97796d814f88055a930c5bbf06b1379c5658fcdf, CI42040333616.
Known-good recovery SHA256 remains
`2d08c2be1ca1c7841cac85081a6c6b725713980cec16b97bf85cfe8695c402d5`.
No phone, partition or rootfs operation occurred; no image was generated or
modified. No new boot/test command is recommended until the missing ownership/current-state evidence and
safe transaction contract are resolved.
