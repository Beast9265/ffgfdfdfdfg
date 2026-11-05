/* SPDX-License-Identifier: APSL-2.0 */
/* A725 host preparation only. No device callbacks, MMIO or activation API. */
#ifndef A725_PREPARE_H
#define A725_PREPARE_H
#include "upstream/AdrenoFirmware.h"
#include "upstream/ArmSmmu4K.h"
#define A725_GMU_SID 5u
#define A725_GMU_STREAM_FLAGS 0x400u
#define A725_PLAN_MAX_RANGES 8u
#define A725_PLAN_MAX_PAYLOADS 8u
#define A725_LIVE_IMPLEMENTATION_AVAILABLE 0
enum A725LiveOperation {
    A725DebugMeasure, A725PowerClock, A725SmmuActivate, A725DeviceTcmWrite,
    A725FirmwareStart, A725HfiActivate, A725GxActivate, A725CpSubmit
};

typedef struct {
    size_t image_offset, bytes, backing_offset;
    uint32_t address, tcm_offset;
    unsigned tcm;
} A725Payload;
typedef struct {
    ArmSmmu4KRange ranges[A725_PLAN_MAX_RANGES];
    A725Payload payloads[A725_PLAN_MAX_PAYLOADS];
    size_t range_count, payload_count, backing_bytes, pages, tcm_words;
    uint32_t sid, stream_flags;
} A725GmuPlan;
/* All input/output buffers must be caller-owned and disjoint. PA arguments
 * describe an inactive model; this code never maps or touches those PAs.
 * Parser/plan success does not authenticate firmware or establish ownership. */
#ifdef __cplusplus
extern "C" {
#endif
int A725PlanGmu(const uint8_t *, size_t, uint64_t backing_pa, A725GmuPlan *);
/* Rebuild the plan before copying into ordinary caller-owned host RAM.
 * TCM payloads are planned only, NEVER written to a device. Zero padding.
 * Failure leaves backing untouched. Inputs must remain immutable throughout. */
int A725PrepareRam(const uint8_t *, size_t, uint64_t backing_pa,
    uint8_t *backing, size_t capacity, A725GmuPlan *);
/* Apply only planned TCM payloads to a caller-owned 32KiB shadow image.
 * Unspecified bytes are preserved. This is NOT a hardware TCM transaction. */
int A725StageTcmShadow(const uint8_t *, size_t, uint64_t backing_pa,
    uint8_t *shadow, size_t capacity, A725GmuPlan *);
/* Build inactive 4KiB tables in ordinary host RAM. Never write SID/CB/TTBR,
 * invalidate a TLB or enable translation. GMU profile only, not GPU SID0. */
ArmSmmu4KStatus A725BuildInactiveTables(const A725GmuPlan *, uint64_t pool_pa,
    uint64_t *tables, size_t capacity_pages, ArmSmmu4KResult *);
/* Hard-disabled, regardless of evidence or boot arguments. No live code exists. */
int A725LiveOperationAllowed(unsigned operation, uint32_t physical_evidence);
#ifdef __cplusplus
}
#endif
#endif
