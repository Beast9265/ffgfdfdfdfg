/*
 * Milestone 4: act as iBoot for xnu.
 *
 * mkpayload.py already resolved the kernel's chained fixups and built the
 * ADT, so this only has to: find the payload in the ABL ramdisk, copy the
 * segments to phys_base + (vmaddr - virt_base), place the ADT and
 * boot_args behind the kernel, and jump to the entry point with the MMU
 * and caches off, x0 = boot_args (physical).
 */
#include <stdint.h>
#include "console.h"
#include "fdt.h"
#include "loader.h"
#ifdef SHIM_MARBLE_XNU
#include "payload_range.h"
#endif

#define BOOT_LINE_LENGTH	608
#define PAGE_16K		0x4000UL

struct payload_seg {
	uint64_t vmaddr, vmsize, file_off, file_size;
};

struct payload {
	char magic[8];
	uint32_t version, nsegs;
	uint64_t virt_base, entry_va, adt_off, adt_size, kernel_end;
	uint64_t phys_base, mem_size;
	char cmdline[BOOT_LINE_LENGTH];
	struct payload_seg segs[];
};

/* pexpert/pexpert/arm64/boot.h, Revision/Version 2 */
struct boot_video {
	uint64_t v_baseAddr, v_display, v_rowBytes, v_width, v_height, v_depth;
};

struct boot_args {
	uint16_t Revision, Version;
	uint64_t virtBase, physBase, memSize, topOfKernelData;
	struct boot_video Video;
	uint32_t machineType;
	uint64_t deviceTreeP;
	uint32_t deviceTreeLength;
	char CommandLine[BOOT_LINE_LENGTH];
	uint64_t bootFlags, memSizeActual;
};

_Static_assert(__builtin_offsetof(struct payload, segs) == 0x2a8, "payload header layout");
_Static_assert(__builtin_offsetof(struct boot_args, Video) == 40, "boot_args layout");
_Static_assert(__builtin_offsetof(struct boot_args, CommandLine) == 108, "boot_args layout");
_Static_assert(sizeof(struct boot_args) == 736, "boot_args layout");

/* MMU off: everything is Device memory, so copy in aligned 8-byte words. */
static void copy64(uintptr_t dst, uintptr_t src, uint64_t n)
{
	if ((dst | src) & 7) {
		volatile unsigned char *d = (volatile unsigned char *)dst;
		volatile const unsigned char *s = (volatile const unsigned char *)src;
		for (uint64_t i = 0; i < n; i++) d[i] = s[i];
		return;
	}
	volatile uint64_t *d = (volatile uint64_t *)dst;
	volatile const uint64_t *s = (volatile const uint64_t *)src;
	for (uint64_t i = 0; i < n / 8; i++)
		d[i] = s[i];
	/* Do not read or write beyond the validated range. */
	volatile unsigned char *db = (volatile unsigned char *)(dst + (n & ~7ULL));
	volatile const unsigned char *sb = (volatile const unsigned char *)(src + (n & ~7ULL));
	for (uint64_t i = 0; i < (n & 7); i++) db[i] = sb[i];
}

static void zero64(uintptr_t dst, uint64_t n)
{
	if (dst & 7) {
		volatile unsigned char *d = (volatile unsigned char *)dst;
		for (uint64_t i = 0; i < n; i++) d[i] = 0;
		return;
	}
	volatile uint64_t *d = (volatile uint64_t *)dst;
	for (uint64_t i = 0; i < n / 8; i++)
		d[i] = 0;
	volatile unsigned char *b = (volatile unsigned char *)(dst + (n & ~7ULL));
	for (uint64_t i = 0; i < (n & 7); i++) b[i] = 0;
}

static int magic_ok(const char *m)
{
	static const char want[] = "SWEETXNU";
	for (int i = 0; i < 8; i++)
		if (m[i] != want[i])
			return 0;
	return 1;
}

typedef void (*xnu_entry_t)(uint64_t boot_args_pa);

const char *loader_boot(uintptr_t dtb)
{
	uint64_t rd_start, rd_end;

	if (!fdt_chosen_u64(dtb, "linux,initrd-start", &rd_start) ||
	    !fdt_chosen_u64(dtb, "linux,initrd-end", &rd_end))
		return "no initrd in /chosen";
#ifdef SHIM_MARBLE_XNU
	con_hex("INITRD lo=", rd_start);
	con_hex("INITRD hi=", rd_end);
#else
	con_hex2("INITRD", "lo=", rd_start, "hi=", rd_end);
#endif

	if (rd_end <= rd_start || rd_start > UINTPTR_MAX || rd_end > UINTPTR_MAX)
		return "invalid initrd range";
	uint64_t payload_start = rd_start, payload_size = rd_end - rd_start;
#ifdef SHIM_MARBLE_XNU
	struct marble_payload_range range;
	const char *error = marble_payload_locate(rd_start, rd_end, &range);
	if (error) return error;
	if (range.bootconfig) con_hex("BCFG size=", range.bootconfig_size);
	con_hex("RDEND", range.ramdisk_end);
	payload_start = range.start;
	payload_size = range.size;
	con_hex("PAYLOAD lo=", payload_start);
	con_hex("PAYLOAD size=", payload_size);
#endif
	if (payload_size < sizeof(struct payload)) return "short payload header";
	/* Vendor ramdisk concatenation need not preserve payload alignment. */
	struct payload header;
	copy64((uintptr_t)&header, payload_start, sizeof(header));
	const struct payload *p = &header;
	if (!magic_ok(p->magic)) return "no SWEETXNU payload";
#ifndef SHIM_MARBLE_XNU
	if (payload_start & 7) return "unaligned SWEET payload";
#endif
	if (p->version != 1 || (p->adt_off & 7))
		return "bad payload header";
	if (!p->nsegs || p->nsegs > 64 ||
	    p->nsegs > (payload_size - sizeof(*p)) / sizeof(struct payload_seg))
		return "invalid segment table";
	if (p->adt_off > payload_size || p->adt_size > payload_size - p->adt_off ||
	    p->adt_size > UINT32_MAX) return "invalid ADT range";
	if (!p->mem_size || p->mem_size > UINT64_MAX - p->phys_base)
		return "invalid memory range";
#ifdef SHIM_MARBLE_XNU
	if (p->phys_base != 0x840000000ULL || p->mem_size != 0x100000000ULL)
		return "wrong MARBLE memory window";
#endif
	struct payload_seg segments[64];
	copy64((uintptr_t)segments, payload_start + sizeof(*p),
	    p->nsegs * sizeof(struct payload_seg));
	uint64_t ram_end = p->phys_base + p->mem_size;
	if (p->kernel_end < p->virt_base ||
	    p->kernel_end - p->virt_base > p->mem_size)
		return "invalid kernel end";
	uint64_t adt_pa = p->phys_base + (p->kernel_end - p->virt_base);
	if (p->adt_size > ram_end - adt_pa ||
	    adt_pa + p->adt_size > UINT64_MAX - (PAGE_16K - 1))
		return "ADT exceeds memory";
	uint64_t ba_pa = (adt_pa + p->adt_size + PAGE_16K - 1) & ~(PAGE_16K - 1);
	if (ba_pa > ram_end || PAGE_16K > ram_end - ba_pa)
		return "boot_args exceeds memory";
	uint64_t top = ba_pa + PAGE_16K;
	if (p->entry_va < p->virt_base || p->entry_va - p->virt_base >= p->mem_size)
		return "entry outside memory";
	/* Complete validation before the first destination write. */
	for (uint32_t i = 0; i < p->nsegs; i++) {
		const struct payload_seg *seg = &segments[i];
		if (seg->file_off > payload_size || seg->file_size > payload_size - seg->file_off)
			return "segment source exceeds payload";
		if (seg->vmsize > UINT64_MAX - seg->vmaddr || seg->vmaddr < p->virt_base ||
		    seg->vmaddr - p->virt_base > p->mem_size ||
		    seg->vmsize > p->mem_size - (seg->vmaddr - p->virt_base) ||
		    seg->file_size > seg->vmsize)
			return "segment destination exceeds memory";
		if (seg->vmaddr + seg->vmsize > p->kernel_end)
			return "segment exceeds kernel end";
	}

	con_hex2("PHYS", "base=", p->phys_base, "size=", p->mem_size);
	con_hex("VIRT", p->virt_base);
	con_hex("ENTRY", p->entry_va);

	/* The payload must not overlap where the kernel goes. */
	if (rd_end > p->phys_base && rd_start < p->phys_base + p->mem_size)
		return "ramdisk overlaps kernel memory";

	for (uint32_t i = 0; i < p->nsegs; i++) {
		const struct payload_seg *s = &segments[i];
		uintptr_t dst = p->phys_base + (s->vmaddr - p->virt_base);
		copy64(dst, payload_start + s->file_off, s->file_size);
		if (s->vmsize > s->file_size)
			zero64(dst + s->file_size, s->vmsize - s->file_size);
	}
	con_hex2("SEGS", "n=", p->nsegs, "end=", adt_pa);

	/* ADT, then boot_args, behind the kernel; everything below topOfKernelData is ours. */
	copy64(adt_pa, payload_start + p->adt_off, p->adt_size);

	zero64(ba_pa, PAGE_16K);
	volatile struct boot_args *ba = (volatile struct boot_args *)ba_pa;
	ba->Revision = 2;
	ba->Version = 2;
	ba->virtBase = p->virt_base;
	ba->physBase = p->phys_base;
	ba->memSize = p->mem_size;
	ba->topOfKernelData = top;
	ba->Video.v_baseAddr = FB_BASE;
	ba->Video.v_display = 1;
	ba->Video.v_rowBytes = FB_STRIDE;
	ba->Video.v_width = FB_W;
	ba->Video.v_height = FB_H;
	ba->Video.v_depth = 32;
	ba->deviceTreeP = p->kernel_end;	/* xnu reads it with the MMU on: a VA */
	ba->deviceTreeLength = (uint32_t)p->adt_size;
	for (int i = 0; i < BOOT_LINE_LENGTH; i++)
		ba->CommandLine[i] = p->cmdline[i];
	ba->memSizeActual = p->mem_size;
	con_hex2("BOOTARG", "pa=", ba_pa, "top=", top);

	uintptr_t entry_pa = p->phys_base + (p->entry_va - p->virt_base);
	con_hex("JUMP", entry_pa);
	con_str("XNU", "jumping (fbcon clears screen)");

	/* Everything was written with the MMU and caches off; drop any stale I-cache lines too. */
	__asm__ volatile("dsb sy; ic iallu; dsb sy; isb" ::: "memory");
	((xnu_entry_t)entry_pa)(ba_pa);
	return "xnu returned";
}
