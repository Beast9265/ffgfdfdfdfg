#include "../a725_prepare.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint64_t tables[8*512], table_before[8*512];
static uint8_t ram[0x35000], before[0x35000];
static uint64_t leaf(const ArmSmmu4KResult *r,uint64_t pool,uint32_t va)
{
    unsigned level=r->start_level;size_t at=0;
    while(level<3){uint64_t e=tables[at*512+((va>>(39-9*level))&511)];assert((e&3)==3);at=(size_t)(((e&0x0000fffffffff000ULL)-pool)/4096);level++;}
    return tables[at*512+((va>>12)&511)];
}
int main(int argc,char **argv)
{
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);assert(!fseek(f,0,SEEK_END));
    long length=ftell(f);assert(length>0);rewind(f);size_t n=(size_t)length;
    uint8_t *fw=malloc(n),*bad=malloc(n);assert(fw&&bad);assert(fread(fw,1,n,f)==n);fclose(f);
    A725GmuPlan p;assert(A725PlanGmu(fw,n,0x91000000,&p));
    assert(p.range_count==6&&p.pages==51&&p.backing_bytes==0x33000&&p.payload_count==4&&p.tcm_words==135);
    assert(p.sid==5&&p.stream_flags==0x400);
    assert(p.payloads[0].tcm_offset==0x5000&&p.payloads[2].tcm_offset==0xcf98&&p.payloads[3].tcm_offset==0xcfdc);
    memset(ram,0xa5,sizeof(ram));assert(A725PrepareRam(fw,n,0x91000000,ram,sizeof(ram),&p));
    for(size_t j=0;j<p.payload_count;j++)if(!p.payloads[j].tcm){
        A725Payload *b=p.payloads+j;assert(!memcmp(ram+b->backing_offset,fw+b->image_offset,b->bytes));
    }
    for(size_t at=0;at<p.backing_bytes;at++){
        uint8_t expected=0;
        for(size_t j=0;j<p.payload_count;j++){
            const A725Payload *b=p.payloads+j;
            if(!b->tcm&&at>=b->backing_offset&&at-b->backing_offset<b->bytes)
                expected=fw[b->image_offset+at-b->backing_offset];
        }
        assert(ram[at]==expected);
    }
    for(size_t i=p.backing_bytes;i<sizeof(ram);i++)assert(ram[i]==0xa5);
    static uint8_t shadow[0x8000];memset(shadow,0x5a,sizeof(shadow));
    assert(A725StageTcmShadow(fw,n,0x91000000,shadow,sizeof(shadow),&p));
    for(size_t at=0;at<sizeof(shadow);at++){
        uint8_t expected=0x5a;
        for(size_t j=0;j<p.payload_count;j++){
            const A725Payload *b=p.payloads+j;
            if(b->tcm&&at>=b->tcm_offset-0x5000&&at-(b->tcm_offset-0x5000)<b->bytes)
                expected=fw[b->image_offset+at-(b->tcm_offset-0x5000)];
        }
        assert(shadow[at]==expected);
    }
    // Every truncation of the current audited image must fail before staging.
    for(size_t bytes=0;bytes<n;bytes++)assert(!A725PlanGmu(fw,bytes,0x91000000,&p));
    assert(A725PlanGmu(fw,n,0x91000000,&p));
    memset(ram,0xa5,sizeof(ram));memcpy(before,ram,sizeof(ram));
    assert(!A725PrepareRam(fw,n,0x91000000,ram,0x32fff,&p));assert(!memcmp(ram,before,sizeof(ram)));
    memcpy(bad,fw,n);bad[4]=1;assert(!A725PrepareRam(bad,n,0x91000000,ram,sizeof(ram),&p));assert(!memcmp(ram,before,sizeof(ram)));
    assert(!A725PlanGmu(fw,n,0x91000001,&p));assert(!A725PlanGmu(fw,n,(1ULL<<36)-4096,&p));
    // Unknown metadata, overlapping reservations, payload outside known VMA.
    for(unsigned failure=0;failure<3;failure++){
        memcpy(bad,fw,n);
        if(failure==0)bad[8]=6;
        if(failure==1)memcpy(bad+48,bad+16,4);
        if(failure==2){memset(bad+0xb0,0xff,4);}
        assert(!A725PlanGmu(bad,n,0x91000000,&p));
    }
    assert(A725PlanGmu(fw,n,0x91000000,&p));
    ArmSmmu4KResult result;assert(A725BuildInactiveTables(&p,0x90000000,tables,8,&result)==ArmSmmu4KSuccess);
    assert(result.leaf_pages==51&&result.table_pages<=8&&result.mair==0xff44);
    for(size_t j=0;j<p.range_count;j++)for(uint64_t at=0;at<p.ranges[j].bytes;at+=4096){
        uint64_t e=leaf(&result,0x90000000,(uint32_t)(p.ranges[j].iova+at));
        assert((e&0x0000fffffffff000ULL)==p.ranges[j].physical+at);
        assert((e&3)==3&&(e&(1u<<10))&&!(e&(1u<<6))); // 4K valid, AF, privileged
        assert((e&(3ULL<<53))==(j<4?0:(3ULL<<53))); // NC VMAs non-executable
    }
    memcpy(table_before,tables,sizeof(tables));
    assert(A725BuildInactiveTables(&p,0x90000000,tables,1,&result)==ArmSmmu4KCapacity);
    assert(!memcmp(tables,table_before,sizeof(tables)));
    assert(A725BuildInactiveTables(&p,0x91000000,tables,8,&result)==ArmSmmu4KOverlap);
    assert(!memcmp(tables,table_before,sizeof(tables)));
    p.sid=0;assert(A725BuildInactiveTables(&p,0x90000000,tables,8,&result)==ArmSmmu4KArgument);
    assert(!memcmp(tables,table_before,sizeof(tables)));
    assert(A725PlanGmu(fw,n,0x91000000,&p));p.ranges[4].permissions|=ArmSmmu4KExecute;
    assert(A725BuildInactiveTables(&p,0x90000000,tables,8,&result)==ArmSmmu4KBadRange);
    for(unsigned op=0;op<32;op++)assert(!A725LiveOperationAllowed(op,0xffffffff));
    free(fw);free(bad);
    puts("PASS A725 host preparation: factory firmware plan, all truncations, RAM staging/guard bytes, invalid metadata/ranges, inactive native4K translations/permissions, capacity/alias refusal, live guards always disabled");
}
