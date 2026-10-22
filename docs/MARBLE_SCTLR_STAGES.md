# MARBLE staged SCTLR experiment — 2026-10-22

User's physical result for the previous cache experiment: all pre-MMU checks
are green; CACHE cyan, E and E2 visible; F and synchronous-red absent. IVAC
and IALLU completed. The old write reached pre-ISB stores; the synchronized
transition remains the failure boundary. Stale loader lines are no longer the
working explanation. No new physical result is claimed for this patch.

Only cold MARBLE takes the four-stage experiment. Warm MARBLE keeps the
original default write/ISB and F path. SWEET preprocessing is byte-identical.
All existing diagnostics remain. The low VBAR remains active through every
cold stage and F, then the existing code restores the KVA VBAR.

## Snapshot and register proof

Read SCTLR_EL1 into x14 immediately before the existing cold cache-maintenance
block. There is no earlier SCTLR write on the preprocessed cold entry path.
This is the original SCTLR delivered to XNU; no numerical firmware value is
recorded in available stage-0 notes. `shim/mmu.c` records/prints SCTLR0 at
runtime, but the captured number was not supplied. Do not infer that number
from the unrelated SWEET secondary EL2 setup constant.

x14 previously served as the KVA mapping cursor in start_first_cpu. After the
last create_bootstrap_mapping invocation its value has no consumer before
this new snapshot. Between the snapshot and F there are no calls or writes to
x14. The bit-cell macro only reads x14 with TBZ. Its next original use is as
scratch in APPLY_TUNABLES x12,x13,x14. Thus x14 survives the entire experiment,
including the full XNU-default stage. It is not a permanent runtime log.

The new inline stores use only x9-x13/NZCV, already dead at these locations.
x0 is dead at capture and is the original SCTLR scratch at transition; each
subsequent stage reloads it. No stack, LR, x20-x26 or boot_args modification.
The macro expansions in the assembled object contain no hidden calls.

The snapshot is encoded as 64 cells: bit b occupies x=16*b..16*b+7,
y=2208..2223, white (0xffffffff) for 1, dark blue (0xff102040) for 0.
Bit 0 is leftmost; there are eight blank pixels between cells. A single DSB SY
finishes the complete strip. Decode O=sum(white_bit[b]*2**b); bits 63..0
are all represented, including reserved/feature-dependent fields.

## Exact transition

Let O be that 64-bit original readback:

- M: `(O & ~0x0000000000081006) | 0x1` (clear A, WXN, C, I; set M).
- I: `read(SCTLR_EL1) | 0x1000` after M_OK. C remains clear, M set.
- C: `read(SCTLR_EL1) | 0x4` after I_OK. I and M remain set.
- XNU: `0x000000003454593d` after C_OK, through MSR_SCTLR_EL1_X0.

Each write has its own ISB SY, immediately followed by its marker (except the
retained E2 stores between the M write and its ISB). Every marker finishes
with DSB SY. All framebuffer addresses remain physical-valued, using the
existing V=P mapping after activation. No KVA branch is introduced.

In ordinary readback behavior, C equals `(O & ~0x80002) | 0x1005`, exactly the
preservation formula used by the physically successful shim/mmu.c. Unlike the
shim's single write, this experiment first disables C/I and enables them one
at a time. The shim's translation regime is simpler; its success alone does
not establish XNU's translation configuration works.

| Last visible stage | Location/color | Meaning if next stage is absent |
|---|---|---|
| E | x320,y2368 purple | Pre-SCTLR diagnostics entered; checks and M activation still ahead. If E2 appears but M_OK does not, M write ran but synchronized translation/marker failed with C/I clear. |
| M_OK | x448,y2272 green | M-only synchronized fetch and V=P stores worked. If I_OK is absent, failure is in the I-enable step/marker. |
| I_OK | x512,y2272 yellow | M+I synchronized fetch/stores worked. If C_OK is absent, failure is in the C-enable step/marker. |
| C_OK | x576,y2272 orange | Shim-style preserved SCTLR with M/C/I worked. If XNU_SCTLR_OK is absent, full-default switch/marker failed; investigate non-M/C/I differences. |
| XNU_SCTLR_OK | x640,y2272 white | Full XNU default crossed ISB and completed V=P framebuffer writes. F should follow via a direct branch. |
| F | x384,y2368 cyan-blue | Full staged transition completed; next existing action restores normal KVA VBAR. Does not prove arm_init or later bootstrap succeeds. |

E2 stays at x192,y2272 pink. Its revised meaning is specifically **M-only
MSR executed, before its ISB**, rather than full-default MSR executed.
Marker absence localizes a transition interval; absence of synchronous-red
does not prove no exception occurred, since vector fetch/store visibility can
also fail. No differing SCTLR bit is declared invalid from difference alone.

## Bitwise comparison with XNU

The original numerical value remains unknown until the new strip or the old
SCTLR0 console value is read. Exact comparison for all 64 bits is
`difference = O ^ 0x000000003454593d`; bit b differs iff `(difference >> b)&1`.
XNU's set bits are {0,2,3,4,5,8,11,12,14,18,20,22,26,28,29}; all other bits
are zero. This fully specifies the bitwise comparison without inventing O.

| Field | Bit(s) | XNU value | Preserved M/I/C behavior |
|---|---|---|---|
| A | 1 | 0 | Force 0 |
| SA / SA0 | 3 / 4 | 1 / 1 | Preserve O |
| WXN | 19 | 0 | Force 0 |
| EIS / EOS | 22 / 11 | 1 / 1 | Preserve O |
| UCI | 26 | 1 | Preserve O |
| DZE | 14 | 1 | Preserve O |
| nTWE | 18 | 1 | Preserve O |
| CP15BEN | 5 | 1 | Preserve O |
| XNU SCTLR_RESERVED compatibility mask | 29,28,20 | 1,1,1 | Preserve O |

XNU's SCTLR_RESERVED mask sets bits 29,28,20. Its separate EIS/EOS defaults
set bits 22/11, fields historically treated as RES1 on earlier architectures.
Interpret these fields using implemented CPU features.
This table is a source/default comparison, not a CPU feature-validity claim.

## Validation and scope

Observed PASS locally:

1. `git diff --check`.
2. Reverse/replay of all 0001..0081 in isolated downloaded buildtree.
3. Strict `git apply --check --whitespace=error` and application of 0082.
4. Complete MARBLE start.s preprocessing and plain arm64 Mach-O assembly with
   real generated headers, local clang targeting armv8.2-a+crypto.
5. Emitted instruction inspection: M write/ISB offsets 0x4680/0x46d0,
   I 0x4728/0x472c, C 0x4784/0x4788, XNU 0x47e8/0x47ec;
   normal warm path 0x4850/0x4854. M mask instructions and individual I/C ORRs
   verified. All marker loops end in DSB SY. Offsets are object section offsets,
   not final linked PAs. F label is 0x4858.
6. x14 liveness, x9-x13 scratch, no calls/stack dependence as above.
7. All literal diagnostic tiles and 64 new cells within 1080x2400,
   stride4320, visible framebuffer size0x9e3400. New tiles do not overlap any
   old tile. Snapshot strip ends at x1015,y2223.
8. Full SWEET preprocessing byte-identical to exact task-start source.
9. Real-header MARBLE pe_fiq.c preprocessing: zero GICR_IPRIORITYR references.
10. All unrelated 0082 file sections byte-identical. Removing only the snapshot
    macro/block and replacing the staged block recovers the exact previous
    start.s (apart from its updated scratch comment). This proves translation
    setup, mappings, cache maintenance and existing diagnostics unchanged.

TCR remains 0x226511a511: T0SZ/T1SZ17, TG0=2/TG1=1, IPS2. No TTBR, MAIR,
descriptor, framebuffer mapping, GIC, timer27, SGI1, stride0x40000, ADT,
loader/payload, storage, SMP, boot_args or RAM-window edits. MARBLE cold OSLAR
remains skipped; 16K/plain arm64/MAX_CPUS1 configuration remains unchanged.

Safe for a diagnostic GitHub Actions build. Full kernel link and physical
execution are not yet verified; CI's Apple clang differs from local clang.
Resolve final linked stage PCs/table addresses from that build before treating
object offsets as device addresses. No CI dispatched, commit, push, device
operation or storage write.

Local artifacts: /tmp/sctlr-{before.patch,before-start.s,verify.py,audit.py,
disassembly.txt}, /tmp/mmu-start.{s,macros,o}, /tmp/marble-mmu-tree.
