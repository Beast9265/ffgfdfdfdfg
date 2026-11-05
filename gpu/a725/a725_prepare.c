/* SPDX-License-Identifier: APSL-2.0 */
/* A725 VMA/prealloc/loading rules adapted from yukoimi/hackios-marble
 * 8e50e532 and pinned Qualcomm Gen7_4_0; see PROVENANCE.md. Host RAM only. */
#include "a725_prepare.h"
static const AdrenoFirmwareRegion regions[] = {
    {0,0x4000,0}, {0x4000,0xffc000,1}, {0x10004000,0x4000,2},
    {0x60000000,0x20000000,3}, {0xc0000000,0x20000000,4}
};
static int region(uint32_t address, uint64_t bytes)
{
    for (unsigned i=0; i<5; i++)
        if (bytes && address>=regions[i].address && bytes<=regions[i].bytes &&
            address-regions[i].address<=regions[i].bytes-bytes) return (int)i;
    return -1;
}
static int overlap(uintptr_t a, size_t n, uintptr_t b, size_t m)
{
    if (n>UINTPTR_MAX-a || m>UINTPTR_MAX-b) return 1;
    return a<b+m && b<a+n;
}
int A725PlanGmu(const uint8_t *fw, size_t bytes, uint64_t pa, A725GmuPlan *out)
{
    if (!out) return 0;
    *out=(A725GmuPlan){0};
    if (!pa || (pa&4095) || pa>=(UINT64_C(1)<<36)) return 0;
    AdrenoFirmwareBlock blocks[32]; size_t count=0;
    if (AdrenoFirmwarePlanGmu(fw,bytes,regions,5,blocks,32,&count)!=AdrenoFirmwareSuccess) return 0;
    A725GmuPlan p={0}; unsigned payload_seen=0;
    p.sid=A725_GMU_SID; p.stream_flags=A725_GMU_STREAM_FLAGS;
    for (size_t i=0; i<count; i++) {
        const AdrenoFirmwareBlock *b=blocks+i;
        if (b->bytes) {payload_seen=1; continue;}
        if (payload_seen || (b->type!=1 && b->type!=7)) return 0;
        int id=region(b->address,b->value);
        if (id<0) return 0;
        if (id==0 || id==2) continue;
        uint64_t n=((uint64_t)b->value+4095)&~UINT64_C(4095);
        if ((b->address&4095) || region(b->address,n)!=id || p.range_count==6 ||
            p.backing_bytes>0x34000 || n>0x34000-p.backing_bytes ||
            n>(UINT64_C(1)<<36)-pa-p.backing_bytes) return 0;
        if (p.range_count && b->address<p.ranges[p.range_count-1].iova+p.ranges[p.range_count-1].bytes) return 0;
        unsigned perms=ArmSmmu4KRead|ArmSmmu4KWrite|ArmSmmu4KPrivileged;
        if (id==1) perms|=ArmSmmu4KExecute;
        p.ranges[p.range_count++]=(ArmSmmu4KRange){b->address,pa+p.backing_bytes,n,perms,1,3};
        p.backing_bytes+=(size_t)n; p.pages+=(size_t)(n/4096);
    }
    if (!p.range_count) return 0;
    for (size_t i=0; i<count; i++) {
        const AdrenoFirmwareBlock *b=blocks+i;
        if (!b->bytes) continue;
        if (p.payload_count==A725_PLAN_MAX_PAYLOADS) return 0;
        A725Payload load={b->payload_offset,b->bytes,0,b->address,0,0};
        unsigned id=b->region_identifier;
        if (id==0 || id==2) {
            load.tcm=1;
            load.tcm_offset=(id==0?0x5000u:0x9000u)+(b->address-regions[id].address);
            p.tcm_words+=b->bytes/4;
        } else {
            unsigned found=0;
            for (size_t j=0; j<p.range_count; j++) {
                const ArmSmmu4KRange *r=p.ranges+j;
                if (b->address>=r->iova && b->bytes<=r->bytes && b->address-r->iova<=r->bytes-b->bytes) {
                    load.backing_offset=(size_t)(r->physical-pa+b->address-r->iova); found++;
                }
            }
            if (found!=1) return 0;
        }
        /* Refuse overlapping firmware payloads, including separate TCM blocks. */
        for (size_t j=0;j<p.payload_count;j++)
            if (b->address<(uint64_t)p.payloads[j].address+p.payloads[j].bytes &&
                p.payloads[j].address<(uint64_t)b->address+b->bytes) return 0;
        p.payloads[p.payload_count++]=load;
    }
    /* Fail closed for the currently audited factory GMU profile, as the
     * reference resource planner does. New layouts require a profile audit. */
    if (p.range_count!=6 || p.pages!=51 || p.backing_bytes!=0x33000 ||
        p.payload_count!=4 || p.tcm_words!=135) return 0;
    static const uint32_t tcm_addresses[3]={0,0x10007f98,0x10007fdc};
    static const size_t tcm_sizes[3]={0x1dc,0x28,0x18};
    unsigned tcm_count=0, ram_count=0;
    for (size_t i=0;i<p.payload_count;i++) {
        const A725Payload *b=p.payloads+i;
        if (b->tcm) {
            if (tcm_count>=3 || b->address!=tcm_addresses[tcm_count] ||
                b->bytes!=tcm_sizes[tcm_count]) return 0;
            tcm_count++;
        } else ram_count++;
    }
    if (tcm_count!=3 || ram_count!=1) return 0;
    *out=p; return 1;
}
int A725PrepareRam(const uint8_t *fw, size_t bytes, uint64_t pa,
    uint8_t *ram, size_t capacity, A725GmuPlan *out)
{
    if (!out) return 0;
    *out=(A725GmuPlan){0}; A725GmuPlan p;
    if (!ram || !A725PlanGmu(fw,bytes,pa,&p) || capacity<p.backing_bytes ||
        overlap((uintptr_t)fw,bytes,(uintptr_t)ram,capacity) ||
        overlap((uintptr_t)out,sizeof(*out),(uintptr_t)ram,capacity)) return 0;
    for (size_t i=0;i<p.backing_bytes;i++) ram[i]=0;
    for (size_t j=0;j<p.payload_count;j++) {
        const A725Payload *b=p.payloads+j;
        if (b->tcm) continue;
        for (size_t i=0;i<b->bytes;i++) ram[b->backing_offset+i]=fw[b->image_offset+i];
    }
    *out=p; return 1;
}
int A725StageTcmShadow(const uint8_t *fw, size_t bytes, uint64_t pa,
    uint8_t *shadow, size_t capacity, A725GmuPlan *out)
{
    if (!out) return 0;
    *out=(A725GmuPlan){0}; A725GmuPlan p;
    if (!shadow || capacity!=0x8000 || !A725PlanGmu(fw,bytes,pa,&p) ||
        overlap((uintptr_t)fw,bytes,(uintptr_t)shadow,capacity) ||
        overlap((uintptr_t)out,sizeof(*out),(uintptr_t)shadow,capacity)) return 0;
    for (size_t j=0;j<p.payload_count;j++) {
        const A725Payload *b=p.payloads+j;
        if (b->tcm && (b->tcm_offset<0x5000 || b->bytes>capacity ||
            b->tcm_offset-0x5000>capacity-b->bytes)) return 0;
    }
    for (size_t j=0;j<p.payload_count;j++) {
        const A725Payload *b=p.payloads+j;
        if (!b->tcm) continue;
        for (size_t i=0;i<b->bytes;i++) shadow[b->tcm_offset-0x5000+i]=fw[b->image_offset+i];
    }
    *out=p; return 1;
}
ArmSmmu4KStatus A725BuildInactiveTables(const A725GmuPlan *p, uint64_t pa,
    uint64_t *tables, size_t capacity, ArmSmmu4KResult *out)
{
    if (out) *out=(ArmSmmu4KResult){0};
    if (!p || p->sid!=5 || p->stream_flags!=0x400 || !p->range_count || p->range_count>6 ||
        p->pages>64 || capacity>8 || !p->backing_bytes || p->backing_bytes>0x34000 || !p->ranges[0].physical) return ArmSmmu4KArgument;
    /* Validate board ranges/permissions even if caller mutates a plan. */
    size_t pages=0; uint64_t consumed=0, backing=p->ranges[0].physical;
    for (size_t i=0;i<p->range_count;i++) {
        const ArmSmmu4KRange *r=p->ranges+i; int id=region((uint32_t)r->iova,r->bytes);
        unsigned perms=ArmSmmu4KRead|ArmSmmu4KWrite|ArmSmmu4KPrivileged;
        if (id==1) perms|=ArmSmmu4KExecute;
        if (r->iova>UINT32_MAX || id<0 || id==0 || id==2 || r->permissions!=perms ||
            r->writeback!=1 || r->shareability!=3 || r->physical!=backing+consumed) return ArmSmmu4KBadRange;
        consumed+=r->bytes; pages+=(size_t)(r->bytes/4096);
    }
    if (pages!=p->pages || consumed!=p->backing_bytes) return ArmSmmu4KBadRange;
    const ArmSmmu4KConfig cfg={32,36,pa,64};
    return ArmSmmu4KBuild(&cfg,p->ranges,p->range_count,tables,capacity,out);
}
int A725LiveOperationAllowed(unsigned op, uint32_t evidence)
{
    (void)op; (void)evidence;
    return A725_LIVE_IMPLEMENTATION_AVAILABLE;
}
