# A725 preparation infrastructure

This directory is a portable, host-tested preparation library. It is NOT
linked into the kernel and has no device-I/O callback or hardware loader.
The new mode11 kernel snapshot is independent of this library.

Board rules are adapted individually from yukoimi/hackios-marble revision
8e50e532f09b3042165048c3c72e04b5a8e68898:
`marble_gpu_plan.h`, `marble_gmu_memory.h`, `marble_gmu_resources.h`, and
`marble_gmu_tcm.h`. New adaptations retain the reference root APSL2.0 license
at LICENSE.APSL. The active SMMU, TCM and boot transaction code is NOT imported.

Unmodified upstream sources copied from that reference, with adjacent licenses:

- UniXNU/AdrenoFirmware40fdb8ea87606612ac6f1e80bbb49955d0ce4051:
  AdrenoFirmware.c/.h, BSD-2-Clause-Patent.
- UniXNU/ArmSmmu4K4d0d6598b1a36aeec3de01091893fa6660e49388:
  ArmSmmu4K.c/.h, MIT.

upstream/SHA256.json records imported file identities. Third-party sources
retain their per-file notices and distinct licenses. No vendor firmware,
Apple binary, device dump or generated table is committed.

Qualcomm verification: LineageOS android_kernel_qcom_sm8450-modules
51cf4da5f05c82122a22413f0fe310023abb80ee, graphics-kernel/adreno_gen7_gmu.c
`gen7_gmu_vma`, `load_tcm` and `gen7_gmu_load_fw`; gen7_reg.h. ITCM/DTCM
register indices1b400/1c400 are dword offsets from GPU base03d00000;
relative to GMU03d68000 these become5000/9000 byte offsets. They are used
only to describe host shadow placement, never as pointers.

Implemented and tested:

- Parse complete firmware block streams with bounded capacity/ranges/alignment.
- Validate the currently audited factory shape: six system-RAM reservations,
  51 native4KiB pages/0x33000 backing, one RAM payload and three TCM payloads
  totaling135 words. Different layouts require a new profile audit.
- Map firmware VMAs to a caller-described, contiguous backing model. Execute
  permission is limited to the GMU cache VMA; other VMAs are non-executable.
- Stage RAM payloads with zero padding in ordinary host RAM, and overlay TCM
  payloads on an ordinary32KiB shadow while preserving unspecified bytes.
- Build inactive32-bit IOVA/36-bit PA native4KiB tables, privileged mappings,
  explicit cache/shareability attributes, table/data alias and capacity guards.
- Record DT stream SID5/flags400; no context-bank/stream/ASID ownership assumed.

The36-bit output profile follows the same-phone reference, not a physical
SMMU IDR measurement from this port. It must be corroborated before activation.
Device-stage RW/execute permissions are not CPU permissions. The reference's
WB/inner-shareable table attributes remain a candidate; CPU aliases, coherency,
cache maintenance and table-walk support must be physically verified later.
No new memory is allocated, mapped or made DMA-visible on the phone.

All buffers/plan/result inputs and outputs must be caller-owned, disjoint,
accessible and immutable where documented. PAs are model metadata only;
these functions never access those physical addresses. Structure/shape
validation is not firmware authenticity. Existing firmware inventory/SHA256
validation remains required before any future hardware loader.

A725LiveOperationAllowed returns false for every operation/evidence value;
A725_LIVE_IMPLEMENTATION_AVAILABLE is fixed0. There is no live implementation
behind it. No boot argument, proof bitmask or model result unlocks measurement,
power writes, SID/CB/TTBR programming, device TCM writes, reset or startup.

Not yet implemented: kernel RAM allocation/ownership, log/HFI resource
allocation, live stream/context leases, cache maintenance, hardware TCM
snapshot/write/rollback, secure CX/ZAP, firmware reset/start/readiness or HFI.
Never free/reassign future DMA backing or cut clock/power parents while
quiescence/detach/cleanup is uncertain. Those live lifecycle operations need
separate physically verified stages.
