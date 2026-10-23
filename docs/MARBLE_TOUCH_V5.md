# MARBLE touch v5: QUP wrapper HWCG validation

This iteration is touch-only. USB, display, HID, keys, storage, product identity,
Goodix protocol and GPI/SMMU programming are unchanged. Physical success is
not claimed until the user boots the resulting image.

## Physical v4 evidence

The user observed no physical touch. The now-readable overlay reported:

```text
TOUCH s17 at20 reason19 err-1
QUP0 S_AHB halt timeout
```

The corresponding registers were:

```text
GCC_VOTE_62008_BEFORE = 400283c0
GCC_VOTE_62008_AFTER  = 400283c0
S4_CBCR_274dc         = 00004220
M_AHB_27004           = 00000000
S_AHB_27008           = 80000002
S4_CMD_274e4          = 80000000
S4_CFG_274e8          = 00100000
S4_DFS_274f8          = 00000021
```

Thus v4 reached `MT_CLOCK_S_AHB`. It still had not accessed GENI or contacted
the Goodix controller.

## Source-backed correction

Pinned vendor source is Pzqqt/android_kernel_xiaomi_marble commit
`cf63f53980e17b503e595501b359697595fe8b24`.

`drivers/clk/qcom/gcc-waipio.c` declares both QUP wrapper-0 AHB clocks as
`BRANCH_HALT_VOTED`, with CBCR registers `0x27004` and `0x27008`, HWCG bit 1,
and GCC vote bits 6 and 7 respectively. The S4 branch at `0x274dc` is voted but
has no `hwcg_reg` or `hwcg_bit` declaration.

In the same commit, `drivers/clk/qcom/clk-branch.c` implements
`clk_branch_in_hwcg_mode()` and makes `clk_branch_wait()` return success when a
declared branch's HWCG bit is set. Therefore physical S_AHB `0x80000002` is a
valid hardware-gated state even though `CLK_OFF` bit 31 remains set. V4's
unconditional bit-31 poll was a false failure.

V5 retains the vote and readback, then applies Qualcomm's semantics only to
M_AHB and S_AHB:

- unreadable `0xffffffff` fails;
- HWCG bit 1 records `M_AHB_HWCG_ACCEPTED` or `S_AHB_HWCG_ACCEPTED` and passes;
- without HWCG, the bounded `CLK_OFF` poll remains and success records
  `*_CLK_OFF_CLEAR`;
- timeout keeps the existing branch-specific reason and register snapshot.

S4 retains strict `CLK_OFF` validation. No HWCG shortcut is applied to it.

## Validation and safety

Focused ASan/UBSan tests cover AHB CBCR values `0x80000002`, `0x00000002`,
`0x00000000`, `0x80000000`, and `0xffffffff`. S4 separately rejects
`0x80000000` (including a set bit 1) and accepts `0x00000000`. Existing source,
clock-order, Goodix framing/parser, FIFO, power/reset and malformed-frame tests
remain enabled. All 82 patches replay cleanly with strict patch 0082 checking;
the generated touch unit compiles with actual CI headers to arm64 Mach-O.
SWEET, VMAPPLE, BCM2837 and T8103 preprocessing is unchanged from v4. All
other generated patch-0082 sources, including USB and overlay code, compare
byte-for-byte with v4.

If the physical probe reaches FIFO-disabled/GPI state, the existing read-only
snapshot and safe refusal remain. V5 adds no GPI rings, SMMU changes, firmware
upload, or persistent controller writes. Diagnostics remain in RAM, the stable
overlay, and `/private/var/tmp/marble-hwdiag.txt`.

Final source, CI and artifact hashes will be appended after the exact build is
verified and packaged.
