# MARBLE sparse bootstrap mapping experiment

Physical input supplied by the user, 2026-10-22: original SCTLR_EL1
`0x30d00988`, bits 3,7,8,11,20,22,23,28,29. E and E2 visible; M_OK and
all subsequent stage tiles absent; no sync-red. Preserved formulas produce
M `0x30d00989`, I `0x30d01989`, C `0x30d0198d`, XNU `0x3454593d`.
No SCTLR/TCR/TTBR/MAIR writes or cache maintenance were changed here.

All intervals below are half-open. A physical boot of this change has NOT
occurred. No CI dispatch, commit, push, device access or storage write occurred.

## Old map: exact source and linked-reference audit

Both calls to create_bootstrap_mapping use x24 **after** subtracting the
Mach-O header's offset from the original physBase. They use floor(x24/32MiB),
not a rounded-up block count. The helper masks the initial PA down to an
L2 boundary, uses ARM_TTE_BOOT_BLOCK, and increments the descriptor by 32MiB.
For the locally available staged image
`xnu/out-marble-sctlr/kernel.development.marble`:

- boot_args physBase: `0x840000000`; memSize `0x100000000`.
- original virtBase: `0xfffffe0006000000` (mkpayload aligns header down 32MiB).
- header VA `0xfffffe0007004000`, PA `0x841004000`.
- adjusted remaining memSize `0xfeffc000`; **127** L2 entries per alias.
- TTBR0 V=P: VA=PA `[0x840000000,0x93e000000)`.
- TTBR1 KVA: VA `[0xfffffe0006000000,0xfffffe0104000000)` to the same PAs.
- each descriptor = block PA OR `0x601`: AttrIndx0 (MAIR WB), SH2,
  AP00 EL1 RW, AF1, PXN0, UXN0, valid L2 block.
- TTBR0 L1[0] -> bootstrap_pagetables+0x8000; RAM L2[1056..1182].
- TTBR1 L1[2016] -> bootstrap_pagetables+0xc000; L2[3..129].
- each alias needs one L1 and one L2; framebuffer adds its own L3.

Thus the claim “all 128 blocks of the 4GiB aperture are WB” is slightly
inaccurate: **127 are WB, the last block is invalid**. The broad speculative
exposure still exists throughout those 127 blocks, including the block prefix
before the header. Existing validation tiles compare descriptors, not XPU
accessibility.

shim/mmu.c instead defaults its declared high window to Device-nGnRnE/XN,
then replaces image-containing blocks with L3 tables and promotes only image
pages to Normal-WB. Its MAIR indices are Device0/WB1/NC2; XNU's indices are
WB0/NC1/Device3. Copying shim descriptor numbers directly would be incorrect.

## New construction and exact range rules

Only MARBLE cold bootstrap construction changes. Other boards retain their
original two helper calls. No broad WB block helper runs on MARBLE.

Let H be the adjusted header PA, D the KVA-minus-PA delta, T boot_args
`topOfKernelData`, B=floor(H/32MiB)*32MiB, and
N=ceil((T-B)/32MiB). The loader establishes D from its original virtBase and
physBase; adjusting both equally in start.s preserves D. Loader virtBase and
physBase have the same 32MiB alignment. Runtime checks reject an incompatible
alias offset, unaligned T, a KVA L1 crossing, and N>16. Invalid layouts spin
before MMU enable rather than overrunning tables. Both new table objects also
have explicit runtime 16KiB alignment checks.

1. TTBR0 L1[0] and TTBR1 L1[2016] retain their existing L2 addresses.
2. All 128 RAM L2 positions [1056..1183] initially become Device/XN blocks.
3. Each of the N physical blocks intersecting [H,T) gets a **pair** of L3s,
   taken sequentially from marble_boot_l3: V=P then KVA. No block is WB.
4. A page intersecting any **nonempty LC_SEGMENT_64 vmsize range** becomes
   WB in both aliases. VM_PROT_EXECUTE in initprot selects EL1 executable;
   otherwise PXN is set. Shared pages inherit execution if either segment
   requires it. Zero-sized segments are ignored (including the lower-address
   __PRELINK_TEXT placeholder). All normal pages have UXN set.
5. The owned tail from maximum nonempty segment end through T is WB/XN in
   both aliases. This includes segment-end padding, ADT, boot_args, and any
   optional appended payload ramdisk. shim/loader.c validates destinations
   and places ADT after rounded kernel_end, boot_args after rounded ADT, and
   T one 16KiB page above boot_args. No loader format or code changed.
6. Segment gaps and block prefixes/suffixes stay Device/XN in V=P and invalid
   in KVA. All RAM outside these N blocks stays Device/XN in V=P and invalid
   in KVA. The exact Device range is the complement of the WB page union in
   `[0x840000000,0x940000000)`. There is no Device alias of any WB page.
7. Framebuffer L2[92] still points to a separate 633-page Normal-NC L3;
   `[0xb8000000,0xb89e4000)` covers the visible bytes plus 0xc00 rounding.
   The rest of that L3 remains zero. Framebuffer has no high KVA RAM alias.

Storage: two existing root pages, two existing L2 pages, **2N RAM L3 pages**,
and one framebuffer L3. The new pool reserves 32*16KiB = 512KiB, supporting
16 block pairs / 512MiB. It is a loaded segment object, so the loader includes
it automatically in kernel_end and T. Only 2N pages of that capacity are used.
For the previous image's ranges N=2: four RAM L3s, nine active total table
pages, with 126 Device L2 blocks plus two RAM L3 pointers in TTBR0. New linked
N and absolute addresses must be measured after linking, not copied from the
previous image. Pool capacity remains mapped as normal XN loaded data.

## Descriptors (PA OR flags)

| Purpose | Flags | AttrIndx | SH | AP | AF | PXN | UXN |
|---|---|---:|---:|---:|---:|---:|---:|
| Default Device L2 block | `0x006000000000040d` | 3 | 0 | 00 | 1 | 1 | 1 |
| Default Device L3 page | `0x006000000000040f` | 3 | 0 | 00 | 1 | 1 | 1 |
| WB executable L3 page | `0x0040000000000703` | 0 | 3 | 00 | 1 | 0 | 1 |
| WB data/table L3 page | `0x0060000000000703` | 0 | 3 | 00 | 1 | 1 | 1 |
| Framebuffer NC L3 page | `0x0060000000000607` | 1 | 2 | 00 | 1 | 1 | 1 |

L1/L2 table descriptor = aligned next-table PA OR 3, no table XN restriction.
Device SH0 matches shim; normal WB SH3 matches shim. MAIR remains unchanged:
index3=0x00 Device-nGnRnE, index0=0xff WB, index1=0x44 NC. AP00 deliberately
allows EL1 writes, including bootstrap data in otherwise read-only segments;
this experiment does not implement final kernel W^X protections. Every
non-executable loaded segment page and page-table page is XN; there is no
convenience executable WB aperture.

## Coverage and linked-address limit

All start.s code, low vectors, arm_init and its pre-entry data references are
within loaded Mach-O segment pages. Bootstrap tables and marble_fb_tables are
C globals in loaded data; the new pool is also explicitly in loaded data.
Both stacks are statically allocated in `osfmk/arm/data.s` __BOOTDATA, not
allocated above topOfKernelData. Stack top is exclusive; the page below it
is checked. ADT and boot_args occupy the owned tail. Both aliases use identical
WB attributes/permissions for each normal physical page.

`tools/marble-bootstrap-audit.py KERNEL --adt-size 3760` checks the actual
linked segment ranges, named executable entry/vector/arm_init symbols,
complete stack ranges, complete table objects, pool capacity/alignment,
and prints exact coalesced WB/Device/KVA intervals. Use the exact ADT byte
length of the payload. Its default mode **requires the new pool symbol** and
rejects an older image. `--reference` is explicitly an old-image comparison.

Reference results for the staged image (NOT new linked addresses):

| PA range | New policy applied to old image layout |
|---|---|
| `[0x840000000,0x841004000)` | Device/XN, KVA invalid |
| `[0x841004000,0x8412cc000)` | WB/XN |
| `[0x8412cc000,0x841ac0000)` | WB executable |
| `[0x841ac0000,0x842030000)` | WB/XN |
| `[0x842030000,0x940000000)` | Device/XN, KVA invalid |

Old-image stack PAs: interrupt `[0x841c2c000,0x841c30000)`, exception
`[0x841c34000,0x841c38000)`; both below old kernel end `0x842028000` and
old T `0x842030000`. Bootstrap table PA `0x841170000`; entry PA
`0x841473488`; low-vector PA `0x841474000`. A new full link is not available,
so **exact new numerical WB endpoints and table/stack PAs remain pending**.
The source construction uses actual segment addresses/T, not these examples.

## Additional finding: framebuffer table alignment

The staged kernel's marble_fb_tables symbol is PA `0x841b67000`, only 4KiB
aligned. Its link arguments force __DATA,__common and __DATA,__bss alignment
0x1000. Thus even an aligned(16384) C declaration did not ensure a 16KiB-aligned
final table. The old exact-descriptor check did not catch this. This may
independently obscure post-MMU markers: absence of M_OK is not conclusive
proof that the instruction immediately after ISB was never fetched if the
framebuffer translation itself is faulty.

Both marble_boot_l3 and marble_fb_tables now use the existing __DATA,__data
section, whose link arguments specify 0x4000 alignment. No linker options or
framebuffer descriptors change. The real arm_vm_init.c compile succeeds;
llvm-readobj shows section alignment14, pool offset0x98000, framebuffer offset
0x118000, both 16KiB aligned in that object. The final linked-image audit must
still verify absolute placement. This means a future M_OK supports a bootstrap
mapping failure but **cannot uniquely isolate carve-out speculation** from
the framebuffer-alignment correction in this experiment.

## Repository DT inspection

Read-only extraction by the vendor_boot v4 header's dtb_size/dtb offset and
parsing of concatenated FDTs plus backed-up dtbo_a.img found 106 FDTs total.
No explicit reserved-memory `reg` interval overlaps the declared high aperture.
A second scan of all 16-byte address/size `reg` tuples also found no overlap.
Examples of explicit low reservations: hyp `[0x80000000,0x80600000)`, CDSP
secure heap `[0x80c00000,0x85200000)`, modem `[0x8bc00000,0x9ee00000)`.
These are **not** addresses in the 0x8xxxxxxxx high aperture.

However, dynamic shared-dma-pool reservations such as va_md_mem (16MiB),
demura_heap_memory (40MiB), and ramoops have broad alloc-ranges that can
include high memory, with no resolved PA in the stored downstream DTBs.
Bootloader fixups, actual chosen overlay, dynamic allocations, and XPU policy
are not fully recoverable from those static images. Therefore no particular
high carve-out is identified and high RAM cannot be certified free of them.
All unknown high pages remain Device/XN regardless. Dumps and extracted DTS
remain private in /tmp; none are added to git.

## Validation and next step

Observed PASS:

- Reverse/replay all 0001..0081; strict final 0082 check and actual apply.
- Complete MARBLE start.s preprocess and plain arm64 Mach-O assemble with
  actual generated/exported headers; actual arm_vm_init.c C cross-compile.
- Actual emitted constructor executed in QEMU with synthetic load commands:
  all 128 default Device blocks and 4096 L3 descriptors checked; second case
  crosses an L2 boundary and checks 8192 L3 descriptors. Code/data/gaps/tail,
  zero-sized lower segment and identical normal aliases covered. This tests
  the constructor, not Qualcomm speculation or a complete XNU MMU transition.
- Full old-image page-union/symbol/stack audit, explicitly reference-only;
  linked framebuffer alignment defect identified rather than waived silently.
- SWEET start.s and arm_vm_init.c preprocessed bytes identical to task start.
- Every other 0082 patch section byte-identical. SCTLR snapshot/cache/stages
  and subsequent start.s code byte-identical; TCR stays 0x226511a511.
- Zero MARBLE GICR_IPRIORITYR references; existing cold OSLAR exclusion retained.
- Existing framebuffer mapping descriptors and geometry retained; NC, never WB.
- git diff --check.

No full new kernel link/physical result is claimed. Safe for a diagnostic
GitHub Actions **build**; run the linked-image audit before packing/temporary
boot. No CI run was dispatched. Retain E/E2/M_OK/I_OK/C_OK/XNU_SCTLR_OK/F,
all validation tiles, original-SCTLR bit strip, cache tile and sync-red.
The next requested physical observation remains E + E2 + M_OK.

Local validation artifacts: /tmp/safe-{before.patch,before-start.s,edit.py,
regenerate.py,check.py,qemu.py,qemu-multi.py,image-audit.txt,arm_vm_init.o,
vm-object.txt,reserved.py,reserved.txt}; /tmp/mmu-start.{s,macros,o};
/tmp/marble-mmu-tree; /tmp/safe-vm-command.json.
