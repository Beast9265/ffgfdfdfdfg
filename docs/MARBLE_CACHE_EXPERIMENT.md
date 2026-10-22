# MARBLE cold-bootstrap cache experiment (2026-10-22)

Physical observation supplied by user: all pre-MMU checks green, E and E2
visible, F and sync-red absent. This supports testing stale cache state at
synchronized translation activation; it does not prove that cause. No new boot.

Only 0082 start.s changes: one cold-only block immediately before E, after
bootstrap and framebuffer tables are complete. No existing code is removed.

## Exact assembly

```asm
#if defined(MARBLE)
 /* Cold boot only: loader RAM writes and bootstrap tables are authoritative.
  * x23 is the adjusted Mach-O header PA; topOfKernelData is exclusive and
  * includes the ADT and boot_args page. Both lie in loader-validated RAM.
  * x9-x13/NZCV are dead here; preserve x20-x26, LR and both stacks.
  * Never clean stale ABL lines back over the freshly written image. */
 cbnz x21, Lmarble_cache_done
 mov x9, x23
 ldr x10, [x20, BA_TOP_OF_KERNEL_DATA]
 mrs x11, CTR_EL0
 ubfx x11, x11, #16, #4
 mov x12, #4
 lsl x11, x12, x11
 sub x12, x11, #1
 bic x9, x9, x12
Lmarble_cache_invalidate:
 cmp x9, x10
 b.hs Lmarble_cache_complete
 dc ivac, x9
 add x9, x9, x11
 b Lmarble_cache_invalidate
Lmarble_cache_complete:
 dsb sy
 ic iallu
 dsb sy
 isb
 MARBLE_BOOT_MARK cache, 384, 0xff00ffff, 2272
Lmarble_cache_done:
#endif

```

## Physical interval and coverage

Exact runtime interval: [x23 & ~(line - 1), boot_args->topOfKernelData),
issuing DC IVAC at line increments. The last operation affects its entire line.
Before rounding x23 is the actual physical Mach-O header, adjusted at
Lkernelcache_base_found; it is NOT the original boot_args physBase.
End loads BA_TOP_OF_KERNEL_DATA (generated offset 32) through x20 PA.
line = 4 << ((CTR_EL0 >> 16) & 15), matching shim/mmu.c.

Loader proof: shim/loader.c validates MARBLE RAM as
[0x840000000, 0x940000000), every segment and kernel_end, ADT placement,
and a complete 16K boot_args page. ADT starts at page-rounded kernel end;
boot_args starts at align_up(ADT end, 16K); top = boot_args PA + 0x4000.
The kernel's bootstrap_pagetables and marble_fb_tables are static linked
allocations within the loaded/zeroed Mach-O segment extents. tools/mkpayload.py
uses first __TEXT/header as kernel start. Historical kernel inspection confirms
all segment starts are at/above the header. It has header PA 0x841004000;
this is an example, not a prediction of the next linked image. The new build's
exact numeric start/end must come from its payload and loader BOOTARG/top log.
No numeric end is guessed from an old kernel or old ADT size.

No sweep of the 4GiB window: only the contiguous owned kernel-to-boot_args
allocation. Even the maximum CTR encoding's 128KiB line rounding stays within
these 128KiB-aligned RAM bounds. No framebuffer/MMIO or low Qualcomm carve-out
is an invalidate operand. The completion tile separately writes the existing
framebuffer aperture, as other diagnostics do.

## Register audit

New loop writes only x9-x12 and NZCV. Tile writes x9-x13/NZCV. These scratch
registers are already dead at the adjacent E marker and are overwritten before
use in the validation block. x20, x21, x23 are read only; x22/x24/x25/x26,
LR, SP_EL0 and SP_EL1 are untouched. No calls or stack accesses. Warm path
branches around the whole experiment; it cannot use a warm cpu-data pointer
as boot_args. Tile is cyan at x384..447, y2272..2303, after final ISB.

## Comparison with shim/mmu.c (unchanged differences)

- Cache maintenance: shim invalidates its image (including static table pool)
  with IVAC, DSB SY, IC IALLU, DSB SY, ISB before programming translation
  registers. Loader already does DSB SY/IC IALLU/DSB SY/ISB but no DC IVAC.
  This experiment adds the same maintenance for XNU after register setup,
  before E/checks/SCTLR, including newly constructed tables.
- Barrier order: shim programs MAIR, TCR, TTBR0, then ISB, TLBI VMALLE1,
  DSB NSH, ISB. XNU programs TCR, TTBR0 via set_mmu_ttb (DSB ISH,
  MSR, ISB), TTBR1, MAIR, ISB, TLBI, DSB ISH, then its conditional
  TLBI/IC sequence and existing DSB SY/ISB. Neither order is changed.
  Both finish SCTLR write with ISB; XNU retains E2 between them.
- TCR: shim 0x1409cb51c, 36-bit VA/L2 start (T0SZ28), inner-shareable
  WBWA walks, TTBR1 disabled, IPS36. XNU 0x226511a511, T0SZ/T1SZ17,
  outer-shareable WBWA walks for both halves, 16K, IPS40. Other XNU TCR
  controls remain as before. No values changed.
- TTBR: shim uses one identity L2 root and does not program TTBR1 (EPD1).
  XNU uses x25 V=P L1 root and x25+16K KVA L1 root with masked addresses.
- MAIR differs: shim 0x44ff00 with Device/WB/NC indices 0/1/2; XNU's
  broader existing attribute table and all descriptor indices are unchanged.
- SCTLR: shim reads old SCTLR, clears A/WXN, sets M/C/I, preserves other
  bits. XNU writes SCTLR_EL1_DEFAULT = 0x3454593d via existing macro.
  No old-value-preservation experiment is included.

## Validation

PASS: git diff --check; reverse/replay 0001..0081; strict 0082 check and
application; complete MARBLE start.s preprocess and arm64 Mach-O assembly
with actual generated headers; SWEET complete start.s preprocessing byte
identical to task-start; all unrelated 0082 patch sections identical;
removing exactly the new block reproduces task-start start.s byte for byte.
Thus all existing checks, E/E2/F/sync-red, settings and layouts remain.
PASS: MARBLE pe_fiq.c preprocess, zero GICR_IPRIORITYR references; cold
start_first_cpu OSLAR remains skipped. A separate pre-existing warm/reset
OSLAR instruction remains untouched (not a regression).
PASS: RAM-bound/rounding and scratch-register assertions.

Artifacts: /tmp/cache-before.patch, /tmp/cache-before-start.s,
/tmp/cache-verify.py, /tmp/cache-audit.py; established compile inputs and
outputs /tmp/mmu-clean-command.json, /tmp/mmu-start.{s,macros,o}.
Safe for a diagnostic GitHub Actions build. Full new kernel link and physical
result remain unverified. No commit, push, CI dispatch, device/storage action.
