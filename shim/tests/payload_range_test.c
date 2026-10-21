#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../payload_range.h"
static unsigned char rd[4096];
static void le(unsigned char *p, uint64_t v, unsigned n)
{
    for (unsigned i=0; i<n; i++) p[i] = v >> (8*i);
}
static size_t fixture(int config)
{
    memset(rd, 0xa5, sizeof(rd));
    /* Two arbitrary vendor entries; embedded decoys must be ignored. */
    memcpy(rd, "SWEETXNU", 8);
    memcpy(rd+128, "MRBLXNU1", 8);
    memcpy(rd+256, "SWEETXNU", 8);
    memcpy(rd+256+PAYLOAD_HEADER_SIZE, "MRBLXNU1", 8);
    le(rd+256+PAYLOAD_HEADER_SIZE+8, PAYLOAD_HEADER_SIZE, 8);
    size_t end=256+PAYLOAD_HEADER_SIZE+16;
    if (config) {
        memset(rd+end, 0, 32); /* parameters plus alignment padding */
        memcpy(rd+end, "a=b\n", 4);
        le(rd+end+32, 32, 4);
        le(rd+end+36, 304, 4);
        memcpy(rd+end+40, "#BOOTCONFIG\n", 12);
        end += 52;
    }
    return end;
}
static const char *locate(size_t end, struct marble_payload_range *r)
{
    return marble_payload_locate((uintptr_t)rd, (uintptr_t)rd+end, r);
}
int main(void)
{
    struct marble_payload_range r;
    for (int config=0; config<2; config++) {
        size_t end=fixture(config);
        assert(!locate(end,&r));
        assert(r.start==(uintptr_t)rd+256 && r.size==PAYLOAD_HEADER_SIZE);
        assert(r.bootconfig==config && r.bootconfig_size==(config?32:0));
    }
    size_t end=fixture(0), footer=end-16;
    rd[footer]^=1; assert(locate(end,&r));
    fixture(0); le(rd+footer+8,0,8); assert(locate(end,&r));
    fixture(0); le(rd+footer+8,UINT64_MAX,8); assert(locate(end,&r));
    fixture(0); le(rd+footer+8,footer+1,8); assert(locate(end,&r));
    end=fixture(1); le(rd+end-20,end,4); assert(locate(end,&r));
    fixture(0); assert(locate(15,&r)); assert(locate(footer+8,&r));
    assert(marble_payload_locate(10,10,&r));
    assert(marble_payload_locate(UINTPTR_MAX,1,&r));
    memcpy(rd,"#BOOTCONFIG\n",12); assert(locate(12,&r));
    puts("PASS: actual C locator concatenation A/B and malformed ranges");
}
