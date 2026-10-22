# MARBLE bounded early allocator mapping

All ranges are half-open. User physical observation, workflow 39717047014:
MMU-on stages 1..7 pass; original early abort PC=0xfffffe0007abadbc,
LR=0xfffffe000746a684, FAR=x0=0xfffffe00080b4000, ESR=0x96000047.
The locally available out-marble-safe kernel agrees exactly on _bzero
0xfffffe0007abada0 and _arm_vm_init 0xfffffe000746a4d0. The instruction at
bzero+0x1c is the user-symbolicated first store; LR is arm_vm_init+0x1b4.
ESR indicates a current-EL write translation fault at L3.

## Exact failure

Loader physBase=0x840000000, virtBase=0xfffffe0006000000. Kernel segment
end rounds to PA0x8420ac000; 3760-byte ADT rounds boot_args to0x8420b0000;
topOfKernelData=0x8420b4000. No appended ramdisk is assumed for this layout.
Initial avail_start is exactly topOfKernelData. With KTRR/CTRR absent,
alloc_ptpage(TRUE) forces map_static=FALSE: invalid_tte gets PA0x8420b4000,
VA0xfffffe00080b4000, and avail_start advances to0x8420b8000. kvtophys
computes its PA without making the VA accessible. The subsequent bzero faults.
This is the first allocation, not a nearby global or a later page.

Previously the owned tail was [0x8420ac000,0x8420b4000); its endpoint was
exclusive. The containing 32MiB block has paired L3s, but this exact page
is Device/XN in TTBR0 and zero/invalid in TTBR1. The reported L3 fault is
therefore the expected descriptor result at the exact allocator endpoint.

## Derived upper bound before TTBR1 replacement

16KiB pages; 2048 entries/table; L2 span32MiB; L1 span64GiB.
For the current 4GiB, ARM_LARGE_MEMORY, non-KASAN, non-monitor,
non-KTRR/CTRR, non-kernel-protect MARBLE configuration:

| Allocation source | Maximum pages |
|---|---:|
| invalid_tte and cpu_tte roots | 2 |
| init_ptpages kernel region and dynamic boundary | 1 |
| init_ptpages separate physmap region | 1 |
| arm_vm_prot_init and owned-tail protection L3s | 16 |
| arm_vm_physmap_init L3s | 138 |
| explicit low-globals L3 | 1 |
| sweet_early_map_final framebuffer L3 | 1 |
| Total | 160 |

The safe-map constructor rejects layouts whose header block through arena
end exceeds16*32MiB or crosses the kernel L1. Consequently all kernel segment,
BOOTDATA/stack guard and owned-tail protection calls share at most16 L3s.
Repeated protection changes reuse existing tables. init_ptpages allocates
only empty L1 slots: its dynamic-boundary call reuses the initial kernel L2.
The physmap L1 count is ((4GiB+1GiB+8*32MiB)>>36)+1=1. Its random slide
is below1GiB, so its full4GiB+256MiB envelope remains in that L1.
Conservatively covering that entire envelope with L3s costs136 aligned
32MiB spans; allow two additional edge spans (138). Only two physmap slide
calls execute here, with ALLOW_BLOCK; actual allocations are much smaller.
This allowance covers their boundary rounding without relying on block use.
The kernel and physmap L3 sets are distinct; the low-globals and framebuffer
slots are counted separately. No extra percentage margin is added.

alloc_ptpage sites in arm_vm_map and arm_replace_identity_map are excluded
by kernel-protect/monitor and KTRR/CTRR respectively. EL0 expansion, PPL
stacks and KASAN are absent. The remaining direct allocations after
set_mmu_ttb_alternate (pmap/bootstrap heap/CPU-window tables) use the final
physmap and do not require this bootstrap arena. arm_vm_physmap_init changes
the phystokv lookup only after constructing the mappings; no allocator call
intervenes before the TTBR1 write. The arena is mapped capacity, not a separate
reservation: alloc_ptpage advances avail_start normally and VM retains unused
pages. Changes to these configuration/layout assumptions require a new bound.

## New mapping

Arena = [T,T+160*0x4000), size0x280000 (2.5MiB). For the failing linked
layout this is PA[0x8420b4000,0x842334000),
KVA[0xfffffe00080b4000,0xfffffe0008334000).
invalid_tte and cpu_tte occupy its first two pages. A new link can move T;
assembly always reads the actual boot_args value and never modifies it.

The constructor extends the existing owned-tail endpoint in a register after
validating segment ends. It rechecks aperture, pool and KVA L1 bounds. Its
existing paired L3 emitter replaces the Device identity entries and writes
identical WB/XN descriptors to both aliases. No extra WB block is introduced.
Flags are0x0060000000000703: AttrIndx0 (MAIR0xff), SH3, AP00 EL1 writable,
AF1, PXN1, UXN1, valid L3 page. First descriptors for the failing layout:
invalid_tte=0x00600008420b4703, cpu_tte=0x00600008420b8703.

Old sparse WB union ends at0x8420b4000; new union ends at0x842334000.
All earlier segment/gap policies are unchanged. The remaining high aperture
through0x940000000 stays Device/XN in TTBR0 and invalid in TTBR1.
Framebuffer stays633 NC/XN pages, flags0x0060000000000607. The historical
127 WB L2 blocks are not restored. Cache/MAIR/TCR/SCTLR/TTBR operations,
loader/ADT, alignment, GIC/timer and all abort/staged diagnostics are unchanged.
Three MARBLE-only sweet_early_mark calls reuse stage7 safely and label
invalid_tte allocation, completed zeroing and completed cpu_tte zeroing.

## Validation observations

- Reversed and replayed0001..0081; final strict0082 check/application passes.
- git diff --check passes.
- Complete real-header start.s MARBLE preprocessing and plain-arm64 assembly
  pass; complete arm_vm_init.c translation unit compiles to Mach-O arm64.
- Actual preprocessed constructor assembled/executed in QEMU;8192 L3 entries
  checked across two block pairs, including all160 arena pages, identical
  aliases, XN, segment gaps and untouched unknown Device/invalid pages.
- Linked-layout audit with ADT3760 verifies the complete arena and prints both
  first-page addresses; existing code/stacks/table/alignment checks pass.
  tools/marble-bootstrap-audit.py now defaults to160 allocator pages;
  --allocator-pages0 reproduces the prior sparse endpoint. This is policy
  applied to the existing link, not evidence of a newly linked image.
- SWEET start.s and arm_vm_init.c preprocessing byte-identical to task start
  with __LINE__ normalized (line-generated locations otherwise move).
- Zero preprocessed MARBLE GICR_IPRIORITYR references. Other patch sections
  byte-identical; assembly outside the arena insertion byte-identical.
- Framebuffer descriptor construction unchanged; abort handler retained.

Safe for a GitHub Actions build. No full kernel link, new CI dispatch or new
physical boot was performed. Re-audit the new linked image with actual ADT
size before packing. No commit/push or device/storage operation occurred.
Local evidence: /tmp/arena-{edit.py,validate.py,qemu.py,compile.log,vm.o,
linked-audit.txt,before.patch,before-start.s,before-vm.c}, /tmp/mmu-start.{s,o}.
