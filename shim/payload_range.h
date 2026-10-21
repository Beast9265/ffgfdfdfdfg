#pragma once
#include <stdint.h>
#include <stddef.h>

#define PAYLOAD_HEADER_SIZE 0x2a8U
static int payload_bytes_equal(const unsigned char *p, const char *s, unsigned n)
{
	for (unsigned i = 0; i < n; i++)
		if (p[i] != (unsigned char)s[i]) return 0;
	return 1;
}
static uint64_t payload_le(const unsigned char *p, unsigned n)
{
	uint64_t v = 0;
	for (unsigned i = 0; i < n; i++) v |= (uint64_t)p[i] << (8 * i);
	return v;
}
struct marble_payload_range {
	uintptr_t start, ramdisk_end;
	uint64_t size, bootconfig_size;
	int bootconfig;
};
/* Only inspect the two fixed trailers, never search vendor ramdisk bytes. */
static const char *marble_payload_locate(uintptr_t lo, uintptr_t hi,
    struct marble_payload_range *out)
{
	if (hi <= lo) return "invalid initrd range";
	uintptr_t end = hi;
	uint64_t span = hi - lo;
	out->bootconfig = 0;
	out->bootconfig_size = 0;
	if (span >= 12 && payload_bytes_equal((const unsigned char *)(hi - 12),
	    "#BOOTCONFIG\n", 12)) {
		if (span < 20) return "truncated bootconfig trailer";
		uint64_t size = payload_le((const unsigned char *)(hi - 20), 4);
		if (size > span - 20) return "invalid bootconfig size";
		end = hi - 20 - size;
		out->bootconfig = 1;
		out->bootconfig_size = size;
	}
	out->ramdisk_end = end;
	if (end - lo < 16) return "truncated MARBLE footer";
	uintptr_t footer = end - 16;
	if (!payload_bytes_equal((const unsigned char *)footer, "MRBLXNU1", 8))
		return "bad MARBLE footer magic";
	uint64_t size = payload_le((const unsigned char *)(footer + 8), 8);
	if (size < PAYLOAD_HEADER_SIZE) return "short XNU payload";
	if (size > footer - lo) return "XNU payload precedes initrd";
	uintptr_t start = footer - size;
	if (!payload_bytes_equal((const unsigned char *)start, "SWEETXNU", 8))
		return "no SWEETXNU payload";
	out->start = start;
	out->size = size;
	return 0;
}
