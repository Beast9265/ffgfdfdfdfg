# MARBLE virtual timer bring-up (2026-10-22)

User physical evidence: exact Actions run **39723141106**, commit
`27eba3872b069658c5e109a4d59790aea2725d03`. All GIC breadcrumbs completed:
redistributor discovery PASS; WAKER PASS; IGROUPR0 skipped PASS;
ISENABLER0 mask `0x08000002` PASS; ICC_SRE_EL1 PASS;
ICC BPR1/PMR/CTLR PASS; GICD_CTLR PASS; ICC_IGRPEN1_EL1 PASS.
The following CNTV_CTL_EL0 write passed. CNTP_CTL_EL0 write raised undefined
instruction at `0xfffffe000747b9e8`, `_fiq_context_init + 0x14`:
`0xd51be228`, `msr CNTP_CTL_EL0, x8`. Symbolication is supplied by the user
for that exact artifact. Physical timer access is unavailable in this boot
environment; the controlling EL2/firmware trap policy is not established here.

Only the machine_routines.c section of patch 0082 changes. Preserve the exact
CNTV_CTL_EL0 enable write; MARBLE substitutes one kprintf breadcrumb for the
precautionary CNTP_CTL_EL0 mask write. Other platforms retain the original
write. Four nearby blank lines are removed to keep subsequent SWEET __LINE__
expansions unchanged. Expanded patch context enables strict git application.

The breadcrumb is safe on this observed boot path: serial/kprintf startup
and all preceding GIC kprintf calls have completed, interrupts remain disabled,
and MAX_CPUS=1. It prints once in current cold bring-up, with no timer-loop
logging. Future context initialization on resume would also print once.

## Physical timer audit

Full final XNU source search covers named registers, case variants, numeric
system register spellings (`S3_3_C14_C0_1`, `S3_3_C14_C2_{0,1,2}`), inline
assembly, macro definitions and raw instruction sites. The only physical timer
instruction is the precautionary CNTP_CTL_EL0 write in machine_routines.c.
No CNTP_TVAL_EL0, CNTP_CVAL_EL0 or CNTPCT_EL0 instruction exists in this source.
Relevant complete translation units are preprocessed with real MARBLE headers;
all physical timer register operands disappear. Full machine_routines.o
disassembly also has zero physical timer instructions.

| Site | Classification | Result |
| --- | --- | --- |
| _enable_virtual_timer CNTP_CTL_EL0 precaution | A before fix; C for MARBLE after fix | Excluded only for MARBLE; CNTV preserved |
| cpu_timebase_init comment saying CNTPCT_EL0 | A cold boot, B resume caller; comment only | Calls ml_get_hwclock, which reads CNTVCT_EL0 on MARBLE |
| proc_reg.h CNTP_CTL_EL0 bit aliases | C | Constants only; no access emitted |
| H13.h ACNTPCT comment | C | Other board documentation, no MARBLE instruction |
| CNTP_TVAL/CVAL and numeric/raw equivalents | No uses found | No additional patch required |

No remaining physical timer instruction was identified on suspend, resume or
secondary paths (B). Future firmware timer policy, SMP and suspend support need
fresh validation (D); this experiment makes no claim that those paths work.
CNTKCTL_EL1 event-stream/EL0 permission setup is unchanged: permission bits
are not accesses to the physical timer or physical count registers.

## Local validation

PASS: full reverse/replay 0001..0081, strict 0082 check and application with
`--whitespace=error`; real-header arm64 Mach-O machine_routines.c compilation;
complete SWEET `-E -P` output byte-identical without normalization.
The emitted fiq_context_init contains `d51be328 msr CNTV_CTL_EL0,x8`, followed
by a relocation to kprintf; no `msr CNTP_CTL_EL0` remains anywhere in the object.
Relevant machine_routines.c and cpu.c MARBLE preprocessing has zero CNTP
register operands. Source inventory finds no other physical timer instruction.

PASS: real-header pe_fiq.c preprocessing/compilation; timer INTID27, SGI1 and
ISENABLER0 mask0x08000002; Group1 ICC BPR1/PMR/CTLR/IGRPEN1 writes retained;
zero GICR_IGROUPR0 and GICR_IPRIORITYR MMIO expressions (the skip diagnostic
still names IGROUPR0). Every other 0082 file section is byte-identical to task
start. Thus GICR stride0x40000, GICD setup, sparse mapping, 16K alignment,
2.5MiB arena, MMU, allocator, framebuffer, abort diagnostics, OSLAR skip and
plain-arm64/16K/MAX_CPUS=1 configuration remain unchanged. ADT generator and
both known ADT warnings are unchanged. git diff --check passes.

Local artifacts: /tmp/cntp-{MARBLE,SWEET}-{before,after}.i,
/tmp/cntp-MARBLE.o, /tmp/cntp-disassembly.txt, /tmp/cntp-cpu.i,
/tmp/cntp-compile.log, /tmp/cntp-audit.py; GIC outputs /tmp/gic-*.
Local clang differs from CI Apple clang. Exact CI link, image packaging and
final hashes are recorded in NOTES.md after the automated workflow completes.
No physical-device command is authorized or performed by automation.

## Exact CI and package result

Source commit `62b42e842515f6389732cb6ad30beaf460bc4a2e`, Actions
[39724251384](https://github.com/Beast9265/ios-marble/actions/runs/39724251384)
PASS. Artifact: xnu/out-marble-ci-39724251384/kernel.development.marble.
All four executable sections scanned by physical timer instruction encoding:
zero CNTP_CTL/TVAL/CVAL or CNTPCT instructions; one CNTV_CTL write.
The same scanner against the old exact artifact detects its sole physical
timer instruction precisely at the reported fault PC, validating the scanner.
New linked fiq_context_init: CNTV MSR at `0xfffffe000747b9e0`, then kprintf;
former fault PC now contains ADD. No physical timer access remains on any
linked boot, resume or secondary path. Bootstrap-map audit also passes with
actual 3760-byte ADT and 160-page arena. Boot-v4 repack/inspection and
independent post-write boundaries/padding/component verification pass.

SHA256:

- Kernel: `650a50bf9e0e174f14ddf41111e11fd61760a318a2f48d6ef8009031fe9aea2b`
- Payload: `5562faacc4c8774909c13b37d4cf73b3096e158075b2bf47cd666d2b56743211`
- Boot image: `2fc4b0b8d93c534c48a0b8cfecbf11c978f96b33e912369b14bc6945ce841365`

Final image: `shim/out/marble-xnu/latest-marble-xnu.img` (16,637,952 bytes).
Hardware behavior remains untested by this automation. No device commands ran.
