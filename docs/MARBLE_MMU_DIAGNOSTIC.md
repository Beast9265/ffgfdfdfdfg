# MARBLE MMU diagnostic (2026-10-22)

Source: Beast9265/ios-marble, marble branch; only start.s behavior in patch 0082
changed. No commit/push, new Actions run, device operation, or partition write.
Existing Actions run 39613073847 was downloaded read-only for its generated
headers and exact compile flags. User observed E but not F on physical hardware;
no new physical result is claimed.

## Screen legend

Every tile is 64x32 pixels, framebuffer PA 0xb8000000, stride 4320.
Existing entry markers and A–H coordinates/colors are unchanged. New check tiles
are green 0xff20d060 for equal/pass, red 0xffff2020 for fail. Checks continue after
failure and never modify the tested register/table to make it pass.

| y | x | Check |
|---|---|---|
|2368|576|TCR TG0=2, 16K|
|2368|640|TCR TG1=1, 16K|
|2368|704|IPS in 2..5 (40..48 bits), and <= ID_AA64MMFR0_EL1.PARange|
|2368|768|TTBR0 BADDR equals full-width x25|
|2368|832|TTBR1 BADDR equals full-width x25+0x4000|
|2368|896|MAIR equals 0x0c08044f00bb44ff|
|2272|0|post-ISB PC V=P executable L1/L2 chain|
|2272|64|post-ISB label KVA alias executable L1/L2 chain|
|2272|128|framebuffer exact L1/L2/L3 chain and first PTE|
|2272|256|low-vector V=P executable L1/L2 chain|
|2272|320|entire TCR equals TCR_EL1_BOOT (also checks both sizes)|
|2272|192|E2: pink 0xffff40a0, after SCTLR MSR and before ISB|
|2368|960|synchronous exception: bright red 0xffff0000, then spin|

All tiles lie inside 1080x2400, visible bytes 0x9e3400; last store remains below
the visible end. New cold-bootstrap validations are skipped if x21 != 0.

E without E2 suggests a direct SCTLR trap, but cannot prove it: SCTLR is a
context-changing write and translation may affect instruction/data accesses
before the explicit ISB. E2 includes many instructions, framebuffer stores and
a DSB. A fault anywhere in that sequence can also suppress E2. E+E2 without F
places failure at the ISB/subsequent fetch or F framebuffer access; it does not
prove TTBR1 execution failed. F proves post-ISB V=P execution and framebuffer
stores completed. Green prechecks independently audit both code aliases and
framebuffer descriptors, but do not prove a hardware walk accepted them.

The ISB does not change PC to KVA. The next PC is still physical-valued,
translated through TTBR0; normal cold boot reaches KVA later at `ret` to lr.
The TTBR1 alias of the post-ISB label is checked separately.

## Actual preprocessed configuration

Recovered DEVELOPMENT_ARM64_MARBLE flags: plain arm64,
-march=armv8.2-a+crypto; real generated assym.s/meta_features.h/export headers.
TCR_EL1_BOOT = **0x226511a511**, initialized into sysreg_restore.tcr_el1 in
cpu.c and loaded by common_start. Physical MRS results remain unknown until boot.
TG0=2 (16K), TG1=1 (16K), IPS=2 (40 bits), T0SZ=17, T1SZ=17 (47-bit halves).
Both walkers: outer shareable, inner/outer WB; TBI0=1, TBID0=0; bit37 is TBI0.
No TCR value changed. RAM maximum 0x93fffffff fits 40 bits. Runtime IPS check
also tests hardware PARange. Prior physical 16K support is user-reported;
this build does not newly measure TGran16.

SCTLR_EL1_DEFAULT = **0x3454593d**. All enabled bits:

|Bits|Meaning / audit|
|---|---|
|0|M: enable stage-1 MMU|
|2|C: data/unified cache enable|
|3,4|SA,SA0: stack alignment checks|
|5|CP15BEN: EL0 AArch32 barrier permission|
|8|SED: disable AArch32 SETEND|
|11|EOS: exception return synchronization; RES1 without FEAT_ExS|
|12|I: instruction cache enable|
|14|DZE: EL0 DC ZVA permission|
|18|nTWE: EL0 WFE permission|
|20|RES1 in ARMv8.2 baseline|
|22|EIS: exception-entry synchronization; RES1 without FEAT_ExS|
|26|UCI: EL0 cache maintenance permission|
|28,29|RES1 in baseline; architecture compatibility bits on newer cores|

No identified invalid or Apple-only enabled bit; SCTLR is unchanged. A=0,
WXN=0, EE/E0E=0; EnIA/EnIB/EnDA/EnDB (31/30/27/13)=0; DSSBS=0. The EL0
permission bits do not exercise those instructions during EL1 bring-up.
HAS_APPLE_PAC, __ARM_42BIT_PA_SPACE__, __ARM_ARCH_8_5__, __ARM_KERNEL_PROTECT__,
KERNEL_INTEGRITY_KTRR, KERNEL_INTEGRITY_CTRR, XNU_MONITOR and HAS_NEX_PG are
undefined/false in actual preprocessing. __ARM_16K_PG__=1. No Apple monitor
sysreg path is emitted at this transition. Generic CONFIG_KERNEL_INTEGRITY
being defined does not select KTRR/CTRR.

## Manual page-table audit

Let R=x25, P=runtime PA of _marble_post_mmu_isb, K=P+x22-x23,
B=runtime PA of marble_fb_tables. No newly linked kernel exists yet, so absolute
P/R/B for this revision cannot honestly be reported as measured addresses.
The checks use runtime ADR/ADRP and actual register/table reads, not old symbols.
Object: post-ISB label is section offset 0x2f28; SCTLR MSR 0x2ed4, ISB 0x2f24.
Linking may move the whole section or later data.

Actual 16K constants: PGBYTES=0x4000, 2048 entries/table, L1 shift36,
L2 shift25 (32MiB blocks), L3 shift14. L1 mask 0x7ff000000000,
L2 mask 0xffe000000, L2 output mask 0xfffffe000000.
ARM_TTE_BOOT_TABLE=3; ARM_TTE_BOOT_BLOCK=0x601 (Valid, block type,
outer shareable, AttrIndx0=WB, AF, EL1 RW, executable).

The header's containing 32MiB block corresponds to phys_base 0x840000000.
After header adjustment x22/x23 have matching within-block offsets; x24 is
reduced by that adjustment. Both mapped ranges fit a single 64GiB L1 slot.
The first create_bootstrap_mapping allocates R+0x8000 (V=P L2); the second
allocates R+0xc000 (KVA L2). TTBR0=R, TTBR1=R+0x4000; no >4GiB address
truncation occurs in the source mask 0x0000ffffffffffff. Runtime exact BADDR
comparisons include all high bits. Expected R is 16K-aligned in high RAM.

KVA walk:

1. Root R+0x4000. L1 index (K>>36)&2047 = **2016** for this kernel region.
2. L1 descriptor at R+0x4000+2016*8 is **(R+0xc000)|3**.
3. L2 index (K>>25)&2047 = **3** for the instruction region 0xfffffe00074....
4. L2 descriptor at R+0xc000+3*8 = **0x0000000840000601**.
5. Output PA = 0x840000000 + (K & 0x1ffffff) = **P**. AttrIndx0, AF,
   writable EL1, PXN/UXN clear; executable. Runtime exact descriptor checks
   verify the code bytes' PA block independently of mapping-construction return.

Actual next-fetch V=P walk: root R, L1 index0 -> (R+0x8000)|3;
L2 index **1056 (0x420)** -> same block descriptor 0x840000601;
output 0x840000000+(P&0x1ffffff)=P.

Illustration ONLY if the old section placement is retained: linked K would be
0xfffffe0007475f28, P=0x841475f28, block offset0x1475f28. Original successful
kernel symbols were LowExceptionVectorBase=0xfffffe0007474000,
bootstrap_pagetables=0xfffffe0007170000 and marble_fb_tables=0xfffffe0007b67000.
They are historical reference, not new-build addresses.

Framebuffer walk, independent of KVA:

1. VA=PA=0xb8000000, root R (TTBR0), L1 index0, descriptor **(R+0x8000)|3**.
2. L2 index **92 (0x5c)**, descriptor at R+0x8000+92*8 = **B|3**.
3. L3 index **0**; first PTE at B is **0x00600000b8000607**.
4. PA output mask gives exactly **0xb8000000**; valid page type bits[1:0]=3,
   AF=1, AttrIndx1=Normal-NC (MAIR byte0x44), SH=outer, AP=00 (EL1 RW),
   PXN=UXN=1. Offset0 gives requested PA exactly.
5. Existing loop writes 633 pages through PA0xb89e0000. 0x9e4000 mapped bytes
   includes 0xc00 unavoidable final-page padding. No geometry/table change.

Runtime chain checks compare exact expected parent descriptors before any child
load, so invalid pointers are not followed. Exact comparisons also reject
unexpected AP/XN/AF/type/attribute bits. The framebuffer check audits the first
PTE, not all 633 entries or actual device acceptance.

## Vector and register safety

Through E the original VBAR installation and breadcrumbs remain in order.
After checks, cold MARBLE installs the low vector PA and ISBs before SCTLR.
Its code is inside the existing executable V=P kernel block, independently
checked. All four synchronous vector slots branch to a handler aligned beyond
all sixteen 128-byte slots, inside the original 4K vector region. Other slots
still spin. No allocation, stack, call, SP, or C dependency. After F the normal
KVA ExceptionVectorsBase is reinstalled and synchronized. Warm boot keeps its
original vector selection before SCTLR and skips bootstrap-table checks.

Exception handler destroys only x9-x13/NZCV; ELR_EL1, ESR_EL1, FAR_EL1,
SPSR_EL1, x0, x20-x26, lr and both SP banks remain intact. Normal checks/E2
also use only x9-x13/NZCV. These temporaries are dead after table setup and
before common_start's next MIDR/tunable scratch use. x0 is used only to install
the low vector immediately before its unconditional SCTLR reload; after F the
normal VBAR setup uses x9. No bootstrap value is saved on an unready stack.

A red exception tile confirms a synchronous exception reached this EL1 vector;
it cannot identify ESR without a later register read. A trap routed to EL2/EL3
is invisible here. Exception entry may synchronize the changed translation
state. A malformed V=P code or framebuffer mapping may prevent the handler
from executing/drawing, including recursive faults. Absence of red is not proof
of absence of an exception. This build narrows evidence; it cannot guarantee
five-way classification solely from framebuffer colors.

## Validation observations

- Reversed downloaded patch stack, replayed all 0001..0081 successfully.
- Final 0082 git apply --check --whitespace=error and actual application pass.
- git diff --check passes.
- Complete MARBLE start.s preprocesses and assembles to arm64 Mach-O with actual
  generated build headers and recovered flags (local clang 19, not Apple CI clang).
- SCTLR/TCR expressions numerically evaluated from actual preprocessing; emitted
  MSR/E2/DSB/ISB/F order checked in object disassembly.
- Complete SWEET start.s preprocessed output equals task-start output bytewise
  with the same real generated headers and SWEET board selection.
- Every other 0082 file section is byte-identical to task start. GIC source,
  timer27/SGI1/stride0x40000, loader/payload/boot_args/storage/ADT untouched.
- MARBLE pe_fiq.c preprocessing succeeds, zero GICR_IPRIORITYR references.
  Cold MARBLE OSLAR_EL1 remains absent; SWEET path retained.
- No full new kernel link, hardware walk/boot result, or CI run is claimed.

Safe to submit to GitHub Actions as a diagnostic source build. Full Apple-toolchain
assembly/link and the newly linked absolute addresses must be checked there.
No Actions build was dispatched, and nothing was committed or pushed.

Artifacts: /tmp/marble-mmu-tree, /tmp/mmu-start.s, /tmp/mmu-start.macros,
/tmp/mmu-start.o, /tmp/mmu-disassembly.txt, /tmp/mmu-cc-command.json,
/tmp/mmu-verify.py, /tmp/mmu-extra.py; downloaded run log /tmp/marble-mmu-build.log.

Architecture reference: [Arm memory management guide](https://developer.arm.com/-/media/Arm%20Developer%20Community/PDF/Learn%20the%20Architecture/LearnTheArchitecture-MemoryManagement-101811_0100_00_en.pdf?revision=1fdc3375-d81c-4457-b786-04fb98557de0).

## Exact resulting start.s transition

```asm
#if defined(MARBLE)
	/* E: translation registers and KVA VBAR ready; x9-x13 and NZCV dead here. */
	MARBLE_BOOT_MARK E, 320, 0xff8000ff
#endif
#if defined(MARBLE)
 cbnz x21, Lmarble_checks_done
 /* Cold bootstrap diagnostic. All scratch below confined to x9-x13/NZCV.
  * Read back actual system registers, never repair a failed value. */
 mrs x9, TCR_EL1
 ubfx x10, x9, #14, #2
 cmp x10, #2
 MARBLE_CHECK tg0, 576
 mrs x9, TCR_EL1
 ubfx x10, x9, #30, #2
 cmp x10, #1
 MARBLE_CHECK tg1, 640
 mrs x9, TCR_EL1
 ubfx x10, x9, #32, #3
 /* IPS 2..5: 40..48 bits; 6 requires LPA support, not selected here. */
 sub x10, x10, #2
 cmp x10, #3
 cset x11, ls
 mrs x12, ID_AA64MMFR0_EL1
 and x12, x12, #15
 add x10, x10, #2
 cmp x12, x10
 cset x12, hs
 and x11, x11, x12
 cmp x11, #1
 MARBLE_CHECK ips, 704
 mrs x9, TCR_EL1
 MOV64 x10, TCR_EL1_BOOT
 cmp x9, x10
 MARBLE_CHECK tcrfull, 320, 2272
 mrs x9, TTBR0_EL1
 MOV64 x10, TTBR_BADDR_MASK
 and x9, x9, x10
 cmp x9, x25
 MARBLE_CHECK ttbr0, 768
 mrs x9, TTBR1_EL1
 MOV64 x10, TTBR_BADDR_MASK
 and x9, x9, x10
 add x10, x25, #PGBYTES
 cmp x9, x10
 MARBLE_CHECK ttbr1, 832
 mrs x9, MAIR_EL1
 /* Require the entire programmed MAIR, not just framebuffer AttrIndx. */
 MOV64 x10, ((MAIR_WRITEBACK << MAIR_ATTR_SHIFT(CACHE_ATTRINDX_WRITEBACK)) | (MAIR_INNERWRITEBACK << MAIR_ATTR_SHIFT(CACHE_ATTRINDX_INNERWRITEBACK)) | (MAIR_DISABLE << MAIR_ATTR_SHIFT(CACHE_ATTRINDX_DISABLE)) | (MAIR_WRITETHRU << MAIR_ATTR_SHIFT(CACHE_ATTRINDX_WRITETHRU)) | (MAIR_WRITECOMB << MAIR_ATTR_SHIFT(CACHE_ATTRINDX_WRITECOMB)) | (MAIR_POSTED << MAIR_ATTR_SHIFT(CACHE_ATTRINDX_POSTED)) | (MAIR_POSTED_REORDERED << MAIR_ATTR_SHIFT(CACHE_ATTRINDX_POSTED_REORDERED)) | (MAIR_POSTED_COMBINED_REORDERED << MAIR_ATTR_SHIFT(CACHE_ATTRINDX_POSTED_COMBINED_REORDERED)))
 cmp x9, x10
 MARBLE_CHECK mair, 896
 /* Expected L2 allocations: V=P x25+2 pages, KVA x25+3 pages.
  * 4GiB RAM spans one L1 entry (64GiB), so each consumes one L2. */
 mov x9, x25
 adr x10, _marble_post_mmu_isb
 add x11, x25, #(2 * PGBYTES)
 MARBLE_L2 vp
 MOV64 x11, ARM_TTE_BLOCK_L2_MASK
 and x10, x10, x11
 MOV64 x11, ARM_TTE_BOOT_BLOCK
 orr x10, x10, x11
 cmp x9, x10
Lmarble_walk_fail_vp:
 MARBLE_CHECK vpcode, 0, 2272
 add x9, x25, #PGBYTES
 adr x10, _marble_post_mmu_isb
 add x10, x10, x22
 sub x10, x10, x23
 add x11, x25, #(3 * PGBYTES)
 MARBLE_L2 kva
 adr x10, _marble_post_mmu_isb
 MOV64 x11, ARM_TTE_BLOCK_L2_MASK
 and x10, x10, x11
 MOV64 x11, ARM_TTE_BOOT_BLOCK
 orr x10, x10, x11
 cmp x9, x10
Lmarble_walk_fail_kva:
 MARBLE_CHECK kvacode, 64, 2272
 mov x9, x25
 MOV64 x10, 0xb8000000
 add x11, x25, #(2 * PGBYTES)
 MARBLE_L2 fb
 adrp x11, EXT(marble_fb_tables)@page
 add x11, x11, EXT(marble_fb_tables)@pageoff
 orr x12, x11, #(ARM_TTE_VALID | ARM_TTE_TYPE_TABLE)
 cmp x9, x12
 b.ne Lmarble_walk_fail_fb
 ldr x9, [x11]
 MOV64 x10, (0xb8000000 | ARM_PTE_TYPE_VALID | ARM_PTE_SH(SH_OUTER_MEMORY) | ARM_PTE_ATTRINDX(CACHE_ATTRINDX_WRITECOMB) | ARM_PTE_AF | ARM_PTE_PNX | ARM_PTE_NX)
 cmp x9, x10
Lmarble_walk_fail_fb:
 MARBLE_CHECK fb, 128, 2272
 mov x9, x25
 adrp x10, EXT(LowExceptionVectorBase)@page
 add x10, x10, EXT(LowExceptionVectorBase)@pageoff
 add x11, x25, #(2 * PGBYTES)
 MARBLE_L2 vectors
 adrp x10, EXT(LowExceptionVectorBase)@page
 add x10, x10, EXT(LowExceptionVectorBase)@pageoff
 MOV64 x11, ARM_TTE_BLOCK_L2_MASK
 and x10, x10, x11
 MOV64 x11, ARM_TTE_BOOT_BLOCK
 orr x10, x10, x11
 cmp x9, x10
Lmarble_walk_fail_vectors:
 MARBLE_CHECK vectors, 256, 2272
 /* Retain fetchable V=P vectors across transition. Restore KVA VBAR after F.
  * x0 may be overwritten here: next instruction reloads SCTLR default. */
 adrp x0, EXT(LowExceptionVectorBase)@page
 add x0, x0, EXT(LowExceptionVectorBase)@pageoff
 msr VBAR_EL1, x0
 isb
Lmarble_checks_done:
#endif
	MOV64   x0, SCTLR_EL1_DEFAULT
	MSR_SCTLR_EL1_X0
#if defined(MARBLE)
 /* Context-changing MSR: pre-ISB execution is not a guaranteed MMU-off
  * interval. This separates a direct trap only, not precise activation. */
 MARBLE_BOOT_MARK E2, 192, 0xffff40a0, 2272
#endif
	isb		sy
#if defined(MARBLE)
.globl _marble_post_mmu_isb
_marble_post_mmu_isb:
#endif
#if defined(MARBLE)
	/* F: MMU on; framebuffer accessed through bootstrap V=P; x9-x13 and NZCV dead here. */
	MARBLE_BOOT_MARK F, 384, 0xff00c0ff
 /* Now the normal KVA vector is fetchable through TTBR1. */
 adrp x9, EXT(ExceptionVectorsBase)@page
 add x9, x9, EXT(ExceptionVectorsBase)@pageoff
 add x9, x9, x22
 sub x9, x9, x23
 msr VBAR_EL1, x9
 isb
#endif

```
