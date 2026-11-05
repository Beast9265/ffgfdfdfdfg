# 0109: AHB enable-latch investigation

## Physical evidence and remaining gate

The user physically tested mode8 / `a725-gmu-dependencies-v1`, source
`669acd653a5babca624c514dfa5fafc530bec440`, CI42033150162.
MX/CX, AOP ACD, CX enable, voted parent, three roots, GMU/CXO/AXI/MEMNOC
acknowledged. AHB timed out with CBCR00000000, inherited0, errno60;
HUB/APB were not attempted. Root cleanup, CX rollback and rail releases were
not attempted; RESOURCE RETAINED1. iOS subsequently reached normal
SpringBoard with working touchscreen and gestures. This preserves the
baseline but is a failed clock-dependency test, not GPU initialization.
Cold reboot is required before another GPU experiment. No phone operation
is performed by automation. Physical0109 result is pending.

## Source audit: answers to the seven questions

Authoritative core-kernel revision is
[992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0](https://github.com/crdroidandroid/android_kernel_xiaomi_sm8450/tree/992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0/drivers/clk/qcom).
Cape DT revision is
[2e649a7f3e762903eedad43d8256b91e28b512d8](https://github.com/LineageOS/android_kernel_xiaomi_sm8450-devicetrees/blob/2e649a7f3e762903eedad43d8256b91e28b512d8/qcom/cape-gpu.dtsi).
The same-phone reference HEAD remains
[yukoimi/hackios-marble 8e50e532f09b3042165048c3c72e04b5a8e68898](https://github.com/yukoimi/hackios-marble/tree/8e50e532f09b3042165048c3c72e04b5a8e68898).
Its docs/MARBLE-GPU.md, marble_adreno.c clock_preflight and
marble_gpu/{marble_gpu_power,marble_gmu_clocks,marble_gmu_preflight}.h were
compared with our0104/0108 helpers. No A640/A650/A642L addresses were imported.

| Question | Finding | Limit / action |
|---|---|---|
| 1. Correct address? | gpucc-waipio.c `gpu_cc_ahb_clk` uses halt/enable offset911c; GPUCC base03d90000 gives PA03d9911c. Cape fixup changes PLL/rate data, not this branch offset. | Confirmed from pinned driver and reference, not inferred from a zero read. |
| 2. Bits correct? | enable_mask BIT(0), no inverted flag, clk_branch2_ops. clk_enable_regmap performs masked bit0 update. CLK_OFF is bit31 for branch2 status. | AHB uses BRANCH_HALT_DELAY, so bit31 is not its enable-success criterion. Do not equate CLK_OFF0 alone with a valid software lease. |
| 3. Missing parent/domain? | AHB parent is gpu_cc_hub_ahb_div_clk_src: GPUCC9430[3:0], clk_regmap_div_ro_ops, parent HUB RCG93ec/93f0. Its parent is NOT hub_clk branch9148. CX must be owned/powered. |0108 already qualified HUB root and CX. It did not capture the RO divider or config-bus gate.0109 observes them without changing either. Values/rates are not measured frequency evidence. |
| 4. Required prior branch/vote? | Cape DT GMU list is GMU, CXO, DDR AXI, MEMNOC, AHB, HUB_CX_INT, optional AOSS APB. CCF enables AHB's parent chain, not the sibling HUB_AON/HUB_CX_INT branches. | No AHB-specific extra vote or sibling-enable prerequisite found.0109 requires inherited GCC CFG_AHB enable at GCC81004, as reference clock_preflight does. Never enable that critical gate itself. |
| 5. Ownership blocks write? | Driver describes a reversible software bit0; it does not describe a secure ownership takeover for AHB. GCC CFG_AHB is critical, HWCG bit1, BRANCH_HALT_VOTED. | No published hardware TRM/security ownership proof was obtained. A dropped/self-clearing write or restricted view remains a hypothesis. Do not pulse reset, change ownership, program divider, or write GPUCC9534 just because Linux probe does. |
| 6. Polling bug? | clk_branch_wait DELAY does udelay10 and returns0. Our0108 delay helper also delays10, then additionally requires enable bit0 to read back. Therefore AHB errno60 is a failed enable-latch check, not a vendor halt-poll timeout. | It does not establish that 200us halt polling expired. Removing the readback would hide the failure.0109 captures timed readbacks, retaining the10us requirement. |
| 7. Can HUB follow? | DT hub_clk is HUB_CX_INT at9148 (RO divider942c), not HUB_AON at93e8.0108 source mapping9148 is correct; the broad earlier AON label referred to ops/lifetime, not the branch name. |0109 reads both siblings for diagnosis, qualifies inherited9148 before the AHB attempt, and only reaches the normal final HUB check after AHB latch/guards pass. Neither AON branch is written or disabled. Physical dependency PASS remains required before firmware startup. |

The reference's earlier CX transaction writes AHB and SMMU bits and observes
other clock statuses; it does not independently prove that its AHB bit0 held.
Its later clock transaction measures GMU/HUB via debug muxes. Neither is a
justification to bypass our failed AHB readback or to import SMMU/debug writes.

## Mode9 hardware boundary

`marblegpu=9 marblegpuvisual=1` alone selects `a725-ahb-latch-v1`.
Modes0–8 remain byte-identical apart from extending the accepted mode range.
The existing firmware, voted-parent, MX/CX/AOP/CX and root leases are reused.

Before any power write, require inherited GCC CFG_AHB bit0 and reject an
all-ones read. An absent gate stops before GPUCC reads/power writes in the
stage. Before AHB, capture RO HUB/CX dividers, HUB_AON/HUB_CX_INT, CX HWCTRL
and GX GDSCR. Require owned powered CX, collapsed non-HW-controlled GX,
inherited running HUB_CX_INT, exact qualified HUB root and voted GPLL0.
Readability of AHB0 is never a permission test on its own.

Unknown AHB control bits are refused. An inherited bit0 is preserved without
writing. Otherwise issue exactly one bit0 RMW and capture raw CBCR at
0/1/10/100/200us. No automatic retry or alternative register write. Reject
unexpected bits/all-ones reads and changed dividers/failed post-guards.
Success requires bit0 at10,100,200us; a latch first appearing after10us is
still failure. This verifies an enable latch under the vendor DELAY contract,
not independent AHB frequency or GMU execution. CLK_OFF remains visible raw.

On AHB timeout or guard uncertainty, retain acquired branch/root/CX/rail
resources; issue no branch-off/root restore/CX-off/release transaction. On a
successful capture, run the final inherited HUB check, then restore acquired
reversible branch bits in reverse before root/divider-gate cleanup, CX rollback
and CX/MX releases. Any failed cleanup retains upstream resources. Earlier
root/branch and transport failure quarantine remains intact. Never change
inherited global GPLL0 config/vote, AON branches, reset, GX, SMMU, TCM, SCM,
firmware start, HFI or CP. There is no new service/userland/rendering path.

## What to photograph

Ten-second screen: build/mode, GCC CFG_AHB, REFUSAL mask, WRITE flag,
HUB AHB/CX divider values, HUB_AON/HUB_CX_INT, CX HWCTRL/GX GDSCR,
AHB BEFORE/T0/T1/T10/T100/T200/AFTER, per-clock results, branch error/cleanup,
root cleanup, CX rollback, releases and RETAINED. AFTER is valid only when
branch cleanup is ACKNOWLEDGED;0 in an unfilled field is not an MMIO result.

Refusal bits:001 config bus,002 invalid divider view,004 CX off,008 GX owner,
010 inherited HUB_CX_INT unavailable,020 HUB root,040 voted parent,
080 unknown AHB control bits,100 post-guard/divider change,200 invalid CBCR bits.

Diagnostic PASS requires all required clocks ACKNOWLEDGED (APB optional NOT
ATTEMPTED), stable bit0 samples at10/100/200us, REFUSAL0, branch error0,
branch/root cleanup, CX rollback and both releases ACKNOWLEDGED, RETAINED0;
terminal `stage=9 stop=AHB_LATCH_TEST_COMPLETE result=PASS`; then normal
SpringBoard, gestures, touch and SMP8. An ACK is latch/lease evidence only.

FAIL: any missing required dependency, FAILED/TIMEOUT, nonzero refusal/error,
retention, hang/reboot or baseline regression. Photograph, stop, cold reboot
and analyze before another GPU experiment. Do not advance to firmware startup.
An all-zero sample sequence reproduces the unresolved0108 latch failure; a
late or self-clearing sequence narrows timing/ownership hypotheses without
proving which mechanism caused it.

## Host validation

Actual mode9 C is compiled against the existing root/branch MMIO allowlist:
stable and inherited latch, ignored write, late latch, self-clear, invalid
readback, config-bus/GX/HUB/divider/control refusals, each RCG timeout and failed
branch cleanup. Tests enforce one AHB enable write, bounded capture, no HUB
progress after AHB failure, no forbidden writes and upstream retention.
Power services are mocked; host PASS does not replace physical testing.

Further prepare-path audit: `clk_regmap_div_ro_ops` has round/recalc/init/debug
callbacks, no enable or set-rate callback. AHB's `clk_prepare_regmap` returns
immediately without a branch-specific `vdd_data.rate_max`, which this AHB
initializer does not supply. Parent RCG voltage dependencies remain covered
by the existing rail/root stage. This is source evidence against inventing an
AHB-only vote, not proof of the physical bus/security state.

T0/T1/T10/T100/T200 denote requested cumulative delay offsets after the one
write (or inherited-state observation), not independently timestamped sample
latencies or measured clock rates. Interrupts can stretch those intervals.

## Verified build and manual image

Source commit `ea712baa8d0e42cfcb981350c8c25982b0d160da`;
one successful exact-commit [CI42036219174](https://github.com/Beast9265/ffgfdfdfdfg/actions/runs/42036219174),
13.5/DEVELOPMENT/MARBLE/keep_going=true. No retry/older artifact substitution.
Full109 replay, source equality, modes0–8 preservation, ARM64 Mach-O object,
SWEET exclusion, new actual-C and0105–0108 tests,12 firmware/ADT/boot tests and
final boot-v4/payload/cmdline/SMP8/all-six-firmware checks PASS.

Distinct image: `shim/out/marble-xnu/marble-a725-ahb-latch-test-42036219174.img`.
Final verified copy: `shim/out/marble-xnu/latest-marble-xnu.img`.

- Kernel SHA256: `54c2bead97a936522a42a3358b4def82a3b090c68f422b3ba265c07df2d35c2e`
- Payload SHA256: `e738871573f92f086d01bb5107e7230889e96f0daa3fd425c11044d8eb417d32`
- Image SHA256: `d36a9c2f568ec76376e0f44010537c84cf1a782355f30bbf7501be13cb4f0e6f`

After a user-performed cold reboot, manual command only:

```sh
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
```

No phone/rootfs/partition operation performed. Physically tested0107,
baseline-preserving0108 and known-good SMP8 image hashes remain unchanged.
Physical0109 result and cause of the0108 AHB failure remain unverified.
