# MARBLE GICR group-store experiment (2026-10-22)

Physical evidence supplied by the user from Actions run 39719201880: allocator
crash cleared; arm_vm_init and serial/kprintf startup complete. New SEA:
PC fffffe0007a01e08, LR fffffe0007a01df4, FAR fffffe000b3e8080,
ESR 96000010. No new physical boot or Actions run performed here.

Local xnu/out-marble-allocator/kernel.development.marble independently matches
_pe_init_fiq=fffffe0007a01c68 and instruction b8080d09 at PC (+0x1a0).
Disassembly: add x8,x20,x19; add x8,x8,#0x10000; mov w9,#-1;
str w9,[x8,#0x80]!. With user-measured PE base fffffe000b3d8000,
base+0x10080=FAR; physical 0x17180000+0x10080=0x17190080.
Thus this is IGROUPR0, separate from protected priority PA 0x17190400.
Run provenance is user supplied; local instruction/symbol match is observed.

Only pe_fiq.c section of 0082 changed. MARBLE skips all IGROUPR0 and
IPRIORITYR MMIO; ISENABLER0 remains at offset0x10100, mask0x08000002
(timer27, SGI1). Discovery/WAKER and all Group1 system-register operations
remain. Three blank lines before the WAKER timeout were removed to preserve
SWEET __LINE__ expansions exactly. No ADT or other source change.

ADT audit: pe_identify_machine.c pe_arm_map_interrupt_controller uses
SecureDTFindEntry("interrupt-controller", "master", ...). device_tree.c
find_entry uses strcmp on the value. tools/mkadt.py emits an empty property
on /arm-io/gic, so the generic lookup does not match. pe_init_fiq independently
uses SecureDTLookupEntry on /arm-io/gic and maps its reg regions.
pe_arm_init_debug searches device_type="cpu-debug-interface"; mkadt.py
builds no such node. These explain the warnings; ADT remains unchanged.

Validation: all81 patches reversed then replayed successfully; strict0082
--check and application with --whitespace=error passed. Complete final MARBLE
pe_fiq.c preprocessed and compiled with real generated XNU headers, local
clang targeting arm64 Mach-O (-march=armv8.2-a+crypto).
SWEET complete -E -P output before/after byte-identical, without normalization.
Preprocessed MMIO expressions contain neither0x10080 nor0x10400; the only
IGROUPR0 text remaining is the requested diagnostic string. Timer initializer27,
SGI1, Group1 ICC writes verified. Other0082 sections byte-identical, preserving
OSLAR exclusion, sparse map/arena/table pools, 16K/plain-arm64/oneCPU setup.
git diff --check passed. Artifacts /tmp/gic-{MARBLE,SWEET}-{before,after}.i,
/tmp/gic-MARBLE.o, /tmp/gic-compile.log, /tmp/gic-final-path.txt.

Safe for diagnostic GitHub Actions BUILD. Full new kernel link and hardware
behavior remain untested; ISENABLER0 and subsequent accesses intentionally
remain experiments. No commit/push, CI dispatch or device/storage operation.

Resulting source from discovery through MARBLE Group1 completion:

```c
	// Find the redistributor for this processor
	vm_offset_t gicr_pe_base = find_gicr_pe_base();
#if defined(MARBLE)
	kprintf("MARBLE GIC: redistributor PE found\n");
#endif
	// Mark this PE to be awake
	uint32_t gicr_waker = gicr_read32(GICR_WAKER);
	if (gicr_waker & GICR_WAKER_CHILDRENASLEEP) {
		gicr_waker &= ~GICR_WAKER_PROCESSORSLEEP;
		gicr_write32(GICR_WAKER, gicr_waker);
		uint64_t gicr_wake_deadline;
		nanoseconds_to_deadline(os_atomic_load(&gicr_wake_timeout_ns, relaxed), &gicr_wake_deadline);
		while (gicr_read32(GICR_WAKER) & GICR_WAKER_CHILDRENASLEEP) {
			// Spin
			if (gicr_wake_timeout_ns > 0 && mach_absolute_time() > gicr_wake_deadline) {
				panic("%s: core %u timed out waiting for redistributor to wake up",
				    __func__, ml_get_cpu_number_local());
			}
		}
	}

#if defined(MARBLE)
	kprintf("MARBLE GIC: WAKER done\n");
#endif

#if (defined(SWEET) || defined(MARBLE))
	/*
	 * Real hardware with two security states: Group 0 is TrustZone's and
	 * non-secure writes to it are ignored. Everything we own is Group 1 NS
	 * and arrives as an IRQ (see sleh_irq). GICR_IGROUPR0 reads as zero
	 * from the non-secure side even after this write; delivery still works.
	 */
#if defined(MARBLE)
	/* Firmware owns group routing; MMU-on write at PA 0x17190080 aborts. */
	kprintf("MARBLE GIC: skip GICR_IGROUPR0\n");
#else
	gicr_write32(GICR_IGROUPR0, 0xFFFFFFFF);
#endif
#if !defined(MARBLE) /* Protected window: MARBLE aborts at 0x17190400. */
	for (unsigned int i = 0; i < 32; i += 4) {
		gicr_write32(GICR_IPRIORITYR0 + i, 0xA0A0A0A0);
	}
#endif
#if defined(MARBLE)
	kprintf("MARBLE GIC: enable PPI/SGI begin\n");
#endif
	gicr_write32(GICR_ISENABLER0, (1U << sweet_vtimer_intid) | (1U << QUALCOMM_IPI_SGI));
#if defined(MARBLE)
	kprintf("MARBLE GIC: enable PPI/SGI done\n");
#endif
#else
	// Configure timers and legacy FIQ to be group 0
	gicr_write32(GICR_IGROUPR0, 0x81FFFFFF);

	// Enable PPI 27
	gicr_write32(GICR_ISENABLER0, (1 << 27));
#endif /* SWEET */

	// Enable system register access
	uint64_t icc_sre = __builtin_arm_rsr64("ICC_SRE_EL1");
	icc_sre |= ICC_SRE_SRE;
	__builtin_arm_wsr64("ICC_SRE_EL1", icc_sre);
	__builtin_arm_isb(ISB_SY);
#if defined(MARBLE)
	kprintf("MARBLE GIC: ICC_SRE_EL1 done\n");
#endif

#if (defined(SWEET) || defined(MARBLE))
	__builtin_arm_wsr64("ICC_BPR1_EL1", 0);
#else
	// Set priority masks and binary point for group 0
	__builtin_arm_wsr64("ICC_BPR0_EL1", 0);
#endif /* SWEET */
	__builtin_arm_wsr64("ICC_PMR_EL1", 0xFF);

	// Set EOI mode of this processor
	uint64_t icc_ctlr = __builtin_arm_rsr64("ICC_CTLR_EL1");
	icc_ctlr &= ~ICC_CTLR_EOIMODE;
	__builtin_arm_wsr64("ICC_CTLR_EL1", icc_ctlr);
#if defined(MARBLE)
	kprintf("MARBLE GIC: BPR1/PMR/ICC_CTLR done\n");
#endif

#if (defined(SWEET) || defined(MARBLE))
#if defined(MARBLE)
	kprintf("MARBLE GIC: GICD_CTLR begin\n");
#endif
	// ABL leaves only ARE_NS set; Linux writes ARE_NS | EnableGrp1A | EnableGrp1
	uint32_t gicd_ctlr = gicd_read32(GICD_CTLR);
	gicd_ctlr |= GICD_CTLR_ARE_NS | GICD_CTLR_ENABLEGRP1A | GICD_CTLR_ENABLEGRP1;
	gicd_write32(GICD_CTLR, gicd_ctlr);
	while (gicd_read32(GICD_CTLR) & GICD_CTLR_RWP) {
		;
	}
#if defined(MARBLE)
	kprintf("MARBLE GIC: GICD_CTLR done\n");
#endif
	__builtin_arm_wsr64("ICC_IGRPEN1_EL1", 1);
	__builtin_arm_isb(ISB_SY);
#if defined(MARBLE)
	kprintf("MARBLE GIC: ICC_IGRPEN1_EL1 done\n");
#endif
#endif /* Qualcomm Group1 path shown above */
```
