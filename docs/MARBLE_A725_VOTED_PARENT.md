# Mode7: inherited vote-controlled GPLL0 root test

User physical 0106 evidence (S0=S1): MODE=80000005, OPMODE=0,
L=4444001f, ALPHA=4000, USER=02000403, APSS_VOTE=1; 600MHz raw decode.
Only the legacy manual RUN prerequisite fails (REFUSAL=04).

## Why a separate voted readiness rule is justified

Exact pinned source: Qualcomm core-kernel
`992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0`, drivers/clk/qcom:

- gcc-waipio.c's Cape fixup selects fixed Lucid-OLE operations for GPLL0.
- clk-alpha-pll.h aliases those operations to fixed Lucid-EVO operations.
- [alpha_pll_lucid_evo_enable](https://github.com/crdroidandroid/android_kernel_xiaomi_sm8450/blob/992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0/drivers/clk/qcom/clk-alpha-pll.c)
  reads USER_CTL. With ENABLE_VOTE_RUN bit25 set, it calls clk_enable_regmap
  and immediately returns wait_for_pll_enable_lock, polling MODE31 with a
  100us bound. OPMODE is neither read nor written on this branch. The
  trion_pll_is_enabled test and OPMODE=RUN write are BELOW that early return,
  in the non-voted software-control branch.
- alpha_pll_lucid_is_enabled does call trion_pll_is_enabled (OPMODE.RUN and
  MODE.OUTCTRL). This is a distinct observational helper; it can report false
  for the supplied FSM state while the driver's voted enable callback would
  return success. Neither helper is a measured frequency test.
- [clk_core_enable](https://github.com/crdroidandroid/android_kernel_xiaomi_sm8450/blob/992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0/drivers/clk/clk.c)
  accepts the enable callback's success and increments enable_count; it does
  not call is_enabled to overrule that result. The fixed PLL uses plain
  clk_prepare_regmap, not the programmable PLL's calibration prepare path.

Inference: lock is the vendor's successful-enable criterion for the voted
branch. The supplied locked, correctly configured, inherited-vote state is
sufficient to attempt an isolated root test despite OPMODE=0. This does NOT
prove that OPMODE=0 universally means running, nor establish measured output
frequency. No public hardware FSM manual was obtained. Do not generalize this
exception to non-voted operation, other PLLs, or the old diagnostic modes.

## Patch0107 boundary

Only marblegpu=7 selects the new policy. Two qualified reads separated by
10us, plus bounded lock wait100us, require USER25 and output bits[1:0],
inherited APSS_VOTE0, MODE lock/reset/output, L[15:0]=31, ALPHA[15:0]=4000,
USER divider[13:10]=1. OPMODE may be0 or1; other values are refused.

The pre-power check is repeated after existing MX/CX/ACD/CX enable, after GPU
DIV gate acquisition, before each root, before rollback and after rollback.
The earlier post-CX L=ff/lock-loss observation is therefore still refused.
GPLL0 configuration and +62018 inherited vote are READ ONLY throughout.
Only +62000 bit16 can be temporarily acquired; sibling bits and inherited
bit16 are preserved. Root transitions/rollback reuse0105's bounded functions.
Loss of qualification after consumer acquisition, root uncertainty or failed
cleanup retains resources; no automatic retry or parent-power cut follows.

The new stage/screen are isolated copies so existing modes0–6 and their
manual-RUN/audit semantics remain byte-identical. No branch clock, GMU, GX,
SMMU, CPU, touch, storage or graphics implementation is changed. Firmware
preflight remains mandatory. No global PLL calibration, rate programming,
OPMODE write, inherited vote pulse, or secure operation is added.

Expected screen: a725-voted-roots-v1, VOTE-RUN POLICY, PRE MODE/OP/L,
MX/CX/ACD/CX, GPLL0 PARENT, three root results and rollback/release results.
PASS requires parent qualification before AND after CX, GMU/HUB/XO configs
(masked)00100602/00100603/00100001, successful root cleanup, CX rollback and
both vote releases, then normal SpringBoard/touch. This proves root
transactions only, not GPU/GMU execution or measured clock throughput.
Any FAIL/TIMEOUT/RESOURCE_RETAINED/hang: record the screen, cold reboot, and
return to the known-good SMP8 image before another experiment.

Local validation: full strict0001–0107 reverse/replay, MARBLE arm64 compile,
SWEET exclusion, original0105/0106 host tests, new actual-C mode7 tests with
MMIO write allowlist, inherited-gate restoration, all prerequisite failures,
post-CX L corruption, lock loss after gate/each forward root, and every
forward/reverse RCG update timeout. Host tests prove control flow, not clocks.
