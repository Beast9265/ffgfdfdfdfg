# MARBLE Stage-0 Diagnostic Shim

## Scope and hardware facts

Target: POCO F5 / Redmi Note 12 Turbo (`marble`, Qualcomm SM7475).
The values below are authoritative user-supplied facts, encoded in the board
configuration where needed. They have **not** been verified by a shim boot.

| Component | MARBLE values |
| --- | --- |
| Retained ABL framebuffer | PA `0xb8000000`, reservation `0x02b00000`, 1080×2400, 32 bpp, expected stride 4320 bytes |
| GIC distributor | `0x17100000`, size `0x10000` |
| GIC redistributors | `0x17180000`, size `0x200000`, stride `0x40000` |
| Virtual timer | Live DT PPI 11 / INTID 27; Android boot log reports 19.20 MHz (virt/virt) |
| PSCI | `arm,psci-1.0`, `smc` |
| UFS host / PHY | `0x01d84000` (size `0x3000`) / `0x01d80000` |
| Userdata GPT name | `userdata` |
| Future XNU RAM window | base `0x840000000`, size `0x100000000` |
| Restart reason | IMEM `0x146aa65c`; existing bootloader-request value `0x77665500` is unverified on MARBLE |
| Stock images | boot header v4; vendor_boot header v4 with 4096-byte pages; DTB supplied by vendor_boot |

## Build and behavior

```sh
BOARD=marble shim/build.sh
# SWEET compile-only regression check, without its private DTB:
SHIM_RAW_ONLY=1 BOARD=sweet shim/build.sh
```

Requires GNU AArch64 GCC/binutils and GNU awk. MARBLE outputs
`shim/out/marble/{Image,shim.elf}` only. Payload arguments are rejected.
SWEET remains the default with its existing v2 packaging and XNU loader.
No workflow, kernel patch or ADT generator changes are needed for stage 0.

MARBLE draws the existing console into ABL's splash buffer, reports PSCI and
SMCCC versions/reset support, tests GIC Group 1 virtual-timer interrupts and
SGI-to-self, then pauses 20 seconds for a photo. The UFS page runs with the MMU
off and stays visible for 40 seconds. It preserves every existing UFS readiness,
idle-doorbell and transfer-list readback check. Only TEST UNIT READY (0x00),
READ CAPACITY(10) (0x25), and READ(10) (0x28) are sent, on LUN 0. Host-controller
register writes and DMA into shim-owned buffers are required; no storage writes
are issued. No PHY, GPU, touch, Wi-Fi, audio or modem initialization occurs.

The final page enables the existing 16K MMU design. The low 8 GiB stays mapped;
MARBLE additionally maps `[0x840000000, 0x940000000)` as Device, execute-never.
Only shim image pages become write-back cacheable. Framebuffer mappings are
Normal-NC for `FB_VISIBLE_SIZE = FB_STRIDE * FB_H` (10,368,000 bytes),
statically checked against the reservation and rounded to 32 MiB block boundaries.
Only the block at `0xb8000000` becomes Normal-NC; `0xba000000` stays Device. `AT S1E1R` checks both ends of
the high window without accessing its RAM. The 12 GiB hole remains unmapped.
MARBLE `now()` uses `cntvct_el0`, matching the virtual timer; SWEET keeps
`cntpct_el0`. The UFS probe retains its existing `cntvct_el0` behavior.
Reset follows after 40 seconds using only PSCI_SYSTEM_RESET: MARBLE writes
neither IMEM_RESTART_REASON nor PSHOLD. The IMEM address is verified, but the
bootloader-request value is unverified on MARBLE. If reset returns, the shim
executes WFE forever. XNU and secondary CPU code are excluded.

## Packaging blockers and remaining unknowns

No MARBLE boot image has been packaged or physically tested. Inspect private
original boot_a/vendor_boot_a headers and vendor DTB before choosing a v4
packaging command. Verify kernel compression/acceptance of a raw ARM64 Image,
header metadata/command line, ramdisk requirements and vendor ramdisk handling,
ABL Image placement and entry EL/cache state, DTB handoff, and non-overlapping
reserved-memory ranges. Confirm shim DMA buffers are accessible to the retained
UFS controller (including address-width/IOMMU constraints), LUN 0 uses 4096-byte
blocks, retained framebuffer pixel order/stride, GIC security state and reset
behavior. The existing probe assumes 4 KiB UFS blocks; its results are diagnostic,
not confirmation of filesystem or GPT validity. Preserve vendor_boot unchanged.
Keep original images, DTBs and device identifiers private and outside git.

## Physical test procedure (after packaging review)

1. Review the diff and privately verify the packaging inputs above. Back up
   original images; establish a known working way to return to the bootloader.
2. Prepare and inspect a temporary v4 boot image containing only the diagnostic
   Image. Reuse the installed vendor_boot; do not replace it or flash partitions.
3. With explicit user authorization, temporarily boot the reviewed image.
   No device command was run as part of this implementation.
4. Film all three console pages. Expect CNTFRQ `0x124f800`, roughly 30 virtual
   timer IRQs and 10 SGI IRQs, with zero unexpected IRQs. Record actual counts,
   PSCI results, UFS status, GPT output, and any blue panic ESR/ELR/FAR/stage.
5. Expect MMU rc zero; PAR bit 0 clear for image/framebuffer/GIC/high-window
   endpoints and set for the hole. Record reset behavior and verify Android
   still boots. Do not infer storage accessibility from translation alone.

## Local validation

Both raw builds pass without compiler warnings. C objects contain zero ABS64
relocations; both linked ELFs have no relocations. The sole start.o ABS64 is
the expected Image header size. The AArch64 little-endian Image is 180224 bytes
(`0x2c000`), with ARM64 magic and matching image_size. SHA256:
`b344ada1efa0502547a151fd171843b8150d4e58688a04e81f2cf69688cbefa1`.
Symbol inspection confirms no loader or secondary entry/main. UFS command code
is byte-for-byte unchanged. A temporary host harness extracted the actual MMU
table construction and checked every L2/L3 entry for low, high and block-crossing
image placements for both boards, plus rejection beyond 64 GiB. It also asserts
exactly one Normal-NC L2 block per board and explicitly checks MARBLE
`0xb8000000` as Normal-NC and `0xba000000` as Device. This validates
table construction, not hardware behavior. No CI run, boot, flash, commit or push.
