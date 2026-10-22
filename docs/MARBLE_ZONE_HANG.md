# MARBLE zone initialization hang experiment

## Physical baseline (user observation, 2026-10-22)

Source 62b42e842515f6389732cb6ad30beaf460bc4a2e; Actions 39724251384.
SHA256:

- Kernel: 650a50bf9e0e174f14ddf41111e11fd61760a318a2f48d6ef8009031fe9aea2b
- Payload: 5562faacc4c8774909c13b37d4cf73b3096e158075b2bf47cd666d2b56743211
- Boot: 2fc4b0b8d93c534c48a0b8cfecbf11c978f96b33e912369b14bc6945ce841365

CNTP skip physically passes. Observed progress includes arm_vm_init/MMU, GIC
Group 1, CNTV setup, VM bootstrap, IOKit, ATM/logging/firehose, scheduler,
BANK/IPC priority, KDP/PRNG/pthread/AMFI/MAC, platform expert, CPU registration,
buffer cache and `MARBLE CPU: boot CPU 0 registered, SGI1 verified,
initialization complete`. CPU0 and SGI1 are operational.

User reports no further output after `zone_init: map RO`, over one minute,
no panic or reboot: treat as a hard hang. A photograph also contains GEN0..DATA,
metadata/metabits/extra and VM bootstrap completion. No photo was independently
examined in this session. Source audit cannot establish which visible row was
last written. The proposed GENERAL_0 boundary is conditional on RO actually
being the newest execution output, rather than a retained row.

## Exact source audit: XNU 8796.141.3 + patches 0001..0082

`osfmk/kern/zalloc.c` defines a file-local `zone_init`. Its only executable
reference in the source is `STARTUP(ZALLOC, STARTUP_RANK_FIRST, zone_init)`.
`osfmk/kern/startup.h` registers its function pointer in the startup table;
the dispatcher in `osfmk/kern/startup.c:kernel_startup_initialize_upto` calls
`cur->func(cur->arg)`. There is no direct second call or CPU startup callback
that invokes zone_init. `zone_bootstrap`, `zone_set_map_sizes` and individual
zone creation are separate operations, not aliases for zone_init.

Normal chain:

```
arm_init -> kernel_bootstrap -> vm_mem_bootstrap
  -> vm_page_bootstrap / zone_bootstrap / vm_object_bootstrap / vm_map_init
  -> kmem_init -> startup through KMEM -> vm_fault_init
  -> startup through ZALLOC -> zone_init (rank FIRST)
     -> pgz submap
     -> VM, RO, GEN0, GEN1, GEN2, GEN3, DATA (nonzero ratios only)
     -> zone_metadata_init -> permanent zones / statistics -> return
```

The dispatcher sorts entries, retains a global cursor and asserts increasing
startup phases. It advances the cursor AFTER the callback returns, so it is
not intrinsically reentrant: a corrupt/unexpected recursive dispatcher call
inside a callback could in principle revisit the current entry. No such path
was found here, and CPU0 registration happens after VM bootstrap has returned.
An ordinary later dispatch resumes beyond ZALLOC. A repeat would therefore be
abnormal (unexpected control flow/corruption), not standard CPU initialization.
The diagnostics test rather than assume the physical result.

`pexpert/arm/pe_serial.c:fbcon_newline` advances rows modulo framebuffer height,
clearing only the current and next rows. It does not scroll. `fbcon_init` clears
the framebuffer on serial initialization. Therefore old rows from this boot
can remain adjacent to newer output, including across a wrap; top-to-bottom
photo order is not execution order. Earlier-boot residue is less directly
supported after a successful fbcon_init clear, but source alone cannot assign
the photograph's rows to an invocation. No framebuffer change is made.

## CPU0 audit and the patch 0065 premise

`ml_processor_register` in `osfmk/arm64/machine_routines.c` selects BootCpuData
for the boot logical ID, returns its existing per-CPU processor and installs
the IOCPU object as cpu_id. It does NOT call processor_init for the boot CPU.
The master processor is already online; processor_up set PROCESSOR_RUNNING
when the initial kernel thread was loaded. At the actual call CPU0 is executing
kernel work; this state is inferred from source, not a new physical state dump.
The IOCPU object's state is separately Unregistered until initCPU sets Running.

`processor_start -> processor_start_reason(REASON_SYSTEM) -> processor_startup`
in `osfmk/kern/processor.c` has an explicit master_processor branch BEFORE
secondary OFF_LINE/state checks or idle/startup-thread creation. It takes the
up/down lock, enables CPU power, binds/blocks the caller onto the master,
calls `cpu_start(cpu_id)`, restores binding and returns. It creates neither
an idle thread nor a dedicated processor_start_thread in this branch.

`osfmk/arm64/cpu.c:cpu_start` prints the observed cpu_start message. For the
current CPU it calls `cpu_machine_init` and configure_coresight_registers, then
returns. Only the other-CPU branch installs a reset entry/startup thread and
calls PE_cpu_start. CPU0 does not branch to start_first_cpu, arm_init,
kernel_bootstrap, vm_mem_bootstrap or the startup dispatcher.

`osfmk/arm/cpu_common.c:cpu_machine_init` calls optional cache dispatch,
PE_cpu_machine_init(cpu_id, !StartedState), sets StartedState and initializes
interrupts. `iokit/Kernel/IOCPU.cpp:PE_cpu_machine_init` calls IOCPU::initCPU.
MARBLE's callback broadcasts CPU_BOOTED, validates the self SGI, and sets its
IOCPU state Running. Removing processor_start would skip that callback and
break the existing completion/state check. Calling it again arbitrarily after
StartedState was already set would be a separate concern; the successful
MARBLE callback accepts only boot=true. There is no evidence of such a repeat.

Patch 0018 called processor_start synchronously inside SweetCPU::start.
Patch 0065 removed that LOCATION, not the boot CPU operation: it publishes
CPU registrations and launches SweetCPU::startAll on a kernel thread. After
waiting for every selected CPU, startAll loops `i=0; i<num_cpus; i++`, calls
processor_start for EACH CPU (including zero), and waits for per-CPU SGI/init
completion. This permits IOKit to finish matching every CPU before coordinated
SMP startup; the source does not show a fix for CPU0 restarting kernel startup.
Current SWEET retains this coordinator loop. MARBLE retains the earlier
synchronous arrangement appropriate to one CPU, not an obsolete reset bug.

Upstream `iokit/Kernel/arm/AppleARMSMP.cpp:startCPU` likewise loops over all
selected topology CPUs, registers each and calls processor_start for each,
including the boot CPU. IOKitKeys.h documents IOAllCPUInitialized as published
after processor_start has been called on all CPUs at boot. AppleARMSMP's later
comment that processor_start is not called on the boot CPU concerns SLEEP
RESUME, not the initial registration loop. Generic IOCPU's resume loop also
skips the already-woken boot CPU. These distinct paths must not be conflated.

Conclusion: retain processor_start. No justified CPU correction was identified.
This is a diagnostic-only build; all existing 0082 sections remain identical.

## Instrumentation and interpretation

Only new 0082 target: osfmk/kern/zalloc.c. MARBLE-only code uses kprintf, already
available before VM bootstrap, with no diagnostic allocation, lock, timeout,
register write or allocator behavior change. A zero-initialized ordinary static
unsigned counter increments at entry; single-CPU startup makes a plain increment
appropriate. The invocation is captured in a local for the completion message.
It persists for this kernel boot, not across new boots. Existing per-CPU
cpu_stat.timer_cnt is read for liveness context, not changed. Explicit #line
restores baseline source line numbers after conditional blocks so SWEET's
__LINE__-generated identifiers and panic sites preprocess identically too.

Expected sequence, for generation 1:

```
MARBLE ZONE: zone_init enter #1 t=T
zone_init: pgzalloc ...             (existing CONFIG_PROB_GZALLOC output)
MARBLE ZONE: VM enter t=T
MARBLE ZONE: VM early > t=T
MARBLE ZONE: VM early < t=T
MARBLE ZONE: VM suballoc > t=T
MARBLE ZONE: VM suballoc < t=T
MARBLE ZONE: VM guard1 > t=T
MARBLE ZONE: VM guard1 < t=T
MARBLE ZONE: VM guard2 > t=T
MARBLE ZONE: VM guard2 < t=T
zone_init: map VM ...              (existing output)
MARBLE ZONE: VM complete t=T
```

Then the same sequence for RO, GEN0..GEN3, DATA (only nonzero submaps), then:

```
MARBLE ZONE: metadata begin
zone_init: metadata ... / metabits ... / extra ...
MARBLE ZONE: metadata done
MARBLE ZONE: zone_init complete #1 t=T
```

`>` means immediately before the named call and `<` immediately after it,
before the guard result's error check. The existing map print remains near the
end; `complete` follows owner/bounds/budget updates. Rows remain short enough
for the framebuffer. The submap `enter` also distinguishes arithmetic/range
setup before the first requested call.

| Newest breadcrumb | Boundary indicated if no later output |
|---|---|
| zone_init enter | setup / PGZ path, before first nonzero submap |
| GEN0 enter | size/range/options setup, before early-map registration |
| GEN0 early > | vm_map_will_allocate_early_map, or its return/next output |
| GEN0 early < | between registration and suballoc-before print |
| GEN0 suballoc > | kmem_suballoc, including map allocation and parent insertion |
| GEN0 suballoc < | returned; RO-only protection adjustment / first guard preparation |
| GEN0 guard1 > | first vm_map_enter |
| GEN0 guard1 < | returned; result check / last guard preparation |
| GEN0 guard2 > | last vm_map_enter |
| GEN0 guard2 < | returned; result check / existing map print / budget updates |
| GEN0 complete | function finished its work; next submap or following boundary |
| metadata begin | zone_metadata_init |
| metadata done | later permanent-zone/statistics work |
| zone_init complete #1 | zone_init returned next; seek a later startup hang |
| zone_init enter #2 | genuine second function entry within this boot |

Every output boundary includes possible faults/stalls in printing itself; a
breadcrumb narrows execution, not a proof that a named callee is faulty.
Both #1 and #2 completing still proves repeat entry. A physically retained
GEN0 line or repeat printf text alone does not. With wrapping output the entry
can be overwritten; completion retains its generation number too. Record the
newest marker next to the blank cursor rows, rather than assuming the bottom
visible row is newest. No metadata-loop spam added.

## Timer and liveness

SGI1 success proves an interrupt path, not normal CNTV IRQ delivery. Source
path: clock_init -> rtclock_init -> timer_resync_deadlines -> setPop/set clock
pop -> machine timer programming (CNTV_TVAL_EL0). CNTV INTID27 is acknowledged
through ICC_IAR1 in sleh_irq, routed to rtclock_intr(TRUE), then EOIR1.
rtclock_intr increments cpu_stat.timer_cnt before deadline handling.
SIGPdec in cpu_signal_handler can also call rtclock_intr(FALSE), so `t=` counts
handler entries, not exclusively hardware timer IRQs. There is no existing
exclusive CNTV interrupt counter added by this experiment.

Normal zone_init is BEFORE kernel_bootstrap's clock_init and initial scheduler
thread loading, so zero t values here are plausible and do not diagnose a
missing timer. By the later CPU SGI milestone clock_init has run, but no physical
counter/timer-specific observation supplied proves a timer interrupt fired.
CNTV setup/enable does not prove an interrupt was delivered.

vm_map_will_allocate_early_map only checks/appends an early owner. kmem_suballoc
creates a map, calls vm_map_enter on its parent, checks results/sets bounds.
The guard calls insert fixed permanent entries. vm_map_steal_memory reserves
map/entry/hole bootstrap storage expressly for this phase before metadata can
expand zones. No periodic tick is part of this successful path. General map
locking/Z_WAITOK allocation paths can wait if invariants fail; a missing timer
could aggravate a later timed wait, but no source evidence makes it the cause
here. A self-lock or corrupt early allocator state cannot be repaired by ticks.
Do not change allocator or timers based on this hypothesis.

## Validation and build

Local observed PASS:

- Reverse/replay all 0001..0081; strict `git apply --whitespace=error` check and
  application of 0082. Final applied source equals compiled source.
- Real-header DEVELOPMENT ARM64 MARBLE zalloc.c compile to Mach-O object using
  the existing extracted buildtree, generated headers and local clang.
- SWEET full `-E -P` output before/after is byte-identical, including __LINE__.
- Every preexisting 0082 section byte-identical to baseline: safe sparse mapping,
  160-page arena, system registers, CNTV/CNTP policy, timer27, SGI1, GICR stride,
  skipped IGROUPR0/IPRIORITYR, Group1 ICC, framebuffer/ADT/UFS and one CPU.
- Relevant MARBLE machine_routines/cpu preprocessing and machine_routines object:
  zero physical timer instructions. GIC preprocessing: timer27, SGI1 mask
  0x08000002, unchanged Group1 ICC and zero IGROUPR0/IPRIORITYR MMIO operations.
- New zalloc object disassembly inspected; diagnostics are calls/counter loads,
  no timer configuration or MMIO accesses introduced. The baseline linked kernel
  also independently scans clean for physical timer instruction encodings.
- git diff --check. Local clang produces existing upstream warning noise;
  full Apple CI link remains the authoritative build check.

Local artifacts: /tmp/zone-{before.c,before.patch,MARBLE.o,compile.log,
MARBLE-before.i,MARBLE-after.i,SWEET-before.i,SWEET-after.i,disassembly.txt},
/tmp/zone-validate.py, /tmp/zone-baseline-audit.py. Replay and compile commands
are recorded in those scripts; this temporary buildtree is not staged.

Automated exact-commit CI and packaging results are recorded in NOTES.md after
completion. No phone command is executed. The next physical result must identify
the new image's provenance and generation/boundary marker. A successful build
alone does not establish that the physical hang is fixed.

Exact source commit b3008501e9a78e92c2d2005cfd0cb59ac190f1a8 built successfully
in Actions [39726707388](https://github.com/Beast9265/ios-marble/actions/runs/39726707388)
(build 3m14s). Independent run metadata confirms that head SHA. The downloaded
linked kernel passes the physical-timer encoding scan (four executable sections,
zero physical-timer instructions, one CNTV_CTL MSR), sparse mapping audit with
actual 3760-byte ADT/160-page arena, and diagnostic-call disassembly inspection.
The helper completed payload/shim generation, stock boot_a repacking, boot-v4
inspection and independent post-write verification. Final hashes and manual
boot command are in the active NOTES handoff. Physical diagnostic result pending.
