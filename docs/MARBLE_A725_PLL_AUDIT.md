# Cape GPLL0 refusal and read-only audit (0106)

Physical observation on c47c046 / 0105: MX/CX/ACD/CX enable and cleanup PASS;
GPLL0 MODE=5, OPMODE=0, APSS_VOTE=1, L=444400ff, ALPHA=4000,
USER=02000403. The parent is refused with ENXIO before root programming.
The root CMD/CFG zeros on that screen are unfilled result fields, not reads.

## Source-backed conclusions

Pinned Qualcomm sources are core-kernel commit
`992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0`:
[gcc-waipio.c](https://github.com/crdroidandroid/android_kernel_xiaomi_sm8450/blob/992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0/drivers/clk/qcom/gcc-waipio.c),
[clk-alpha-pll.c](https://github.com/crdroidandroid/android_kernel_xiaomi_sm8450/blob/992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0/drivers/clk/qcom/clk-alpha-pll.c),
its header, clk-regmap.c, clk-rpmh.c and gpucc-waipio.c. Extra source cache:
`research/a725-0106/`; existing sources: `research/a725-0105/references/`.

- Factory DT identifies GCC at 00100000+1f4200 as qcom,cape-gcc. The Cape
  fixup selects Lucid-OLE for GPLL0 and GPLL4. GPLL0 base is zero; MODE +00,
  OPMODE +04, STATUS +0c, L +10, ALPHA +14, USER_CTL +18. These 0105 offsets
  are correct. GPLL4 has the same layout at +4000; audit reads it as a control.
- MODE bit31 is LOCK_DET, bit2 RESET_N, bit0 OUTCTRL; OPMODE RUN=1,
  STANDBY=0. USER_CTL bit25 is ENABLE_VOTE_RUN; USER[13:10]=1 selects /2.
  The observed USER has both vote-run and /2 enabled; MODE has reset/output
  bits set but no lock, and OPMODE reports standby. No usable parent is proven.
- Lucid-OLE ops alias the EVO ops. In vote-run mode the fixed PLL enable
  callback uses clk_enable_regmap: RMW APSS_VOTE +62018 bit0, then waits up to
  100us on MODE lock. It does not write OPMODE in this mode. Disable clears
  that vote. GPLL0 has no driver configuration object supplying a safe new L.
  Inherited bit0=1 is not a vote owned by this implementation: clearing or
  pulsing it could affect other GPLL0 consumers. 0106 never touches it.
- The separate GPU source gates are +62000 bits15 (main) and16 (divided),
  BRANCH_HALT_DELAY (10us). They do not replace the global PLL vote. Factory
  GPUCC clocks resolve GCC IDs43/44 to these gates. GCC IDs38/39 are GPLL0
  and its /2 output. DT protected-clocks IDs58..70 are different clocks;
  the DT does not establish that GPLL0 reads are security-filtered.
- Factory xo_board is 76.8MHz, but GCC/GPUCC bi_tcxo is RPMH_CXO_CLK ID0
  through waipio_bi_tcxo, whose divider is 4: 19.2MHz. Do not substitute
  76.8MHz in the PLL calculation. Driver recalc masks L[15:0] and uses a
  16-bit alpha: expected L=31/ALPHA=4000 gives 600MHz; the reported L=ff
  gives 4,900,800,000Hz. This is a register decode, NOT measured frequency.
  Neither bit25 nor the calibration bits [31:16] explain the ff low bits.
- Published GMU rates are TCXO19.2MHz, GPLL0_DIV200MHz, GPU_PLL1/2 500MHz.
  TCXO is a legitimate GMU parent, but the HUB rate table only supplies
  GPLL0-derived150/240/300MHz. A raw TCXO mux selection for HUB is not a
  published operating rate. GPU_PLL1 would require another verified PLL
  setup/ownership sequence; it is not an established safe fallback here.

Pong at `64ddf288...` and Mondrian at `7fad03b8...` enable GPU source gates
and configure GPU-local PLLs; they do not explain this inconsistent GPLL0
view or establish permission to reconfigure MARBLE's shared GPLL0. Jebbranch
at `c03d18a3...` programs GPU roots/gates but likewise does not validate this
GPLL0 state. Their shortcuts cannot substitute for 0105's strict checks.

The software refusal is explained; the physical cause of this register state
is **unresolved**. A bootloader-inherited standby/misconfiguration and a
restricted register view are hypotheses, not findings. No safe PLL-write fix
is established. Do not toggle the inherited vote, mask ff down to 1f, change
L/OPMODE, or remove validation based on these observations.

## Isolated next test

0106 adds only mode6 (`marblegpu=6 marblegpuvisual=1`), gated by existing
firmware preflight. Before GPUCC mapping or any rail operation, map GCC and
read GPLL0/GPLL4 twice, 1000us apart, including status and global/GPU votes.
No GPUCC, GMU, GX or SMMU access, MMIO write, or RPMh/SCM call is reachable.
Visual delay is 10 seconds only with the visual flag. Modes0–5, especially
0105 validation, are preserved verbatim except accepting the additional mode.

Expected screen: `a725-pll-audit-v1`, S0/S1 GPLL0 and GPLL4 register groups,
LOCK/OUT/RESET_N/VOTE_RUN, APSS_VOTE/GPU_GATES, GPLL0 REFUSAL and a raw rate
decode. The reported 0105 values yield REFUSAL=0d (lock + run + rate), not a
parent PASS. CAPTURE COMPLETE means reads completed; it proves no clock/GPU
operation. Require a complete photo followed by normal SpringBoard/touch.
A hang is failure: cold reboot and manually boot the known-good SMP8 image.
Do not repeat GPU power experiments in an uncertain power session.

If mode6 already shows this state, it predates GPU power/ACD; if it shows a
valid parent, the mode5 power sequence or timing becomes the next comparison.
GPLL4 is a reference for the register view, not proof that GPLL0 is safe.
If the contradictory view persists, obtain a qualified same-device live
Linux/firmware trace of the same documented registers and clk_summary before
and after the vendor GPLL0 enable callback, with the exact driver revision.
No Android installation, storage overwrite or automatic phone boot is needed
or authorized by this patch. Hardware rate proof would require a separately
source-audited measurement path; this audit does not program a debug mux.
