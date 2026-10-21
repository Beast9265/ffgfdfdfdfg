#pragma once

/* SWEET remains the default. MARBLE is diagnostic-only, never an XNU target. */
#ifdef SHIM_MARBLE
#define FB_BASE         0xb8000000UL
#define FB_RESERVED     0x02b00000UL
#define GICD_BASE       0x17100000UL
#define GICR_BASE       0x17180000UL
#define GICR_SIZE       0x200000UL
#define GICR_PE_SIZE    0x40000UL
#define VTIMER_INTID    27
#define HIGH_MAP_BASE   0x840000000UL
#define HIGH_MAP_SIZE   0x100000000UL
#else
#define FB_BASE         0x9c000000UL
#define FB_RESERVED     0x01700000UL
#define GICD_BASE       0x17a00000UL
#define GICR_BASE       0x17a60000UL
#define GICR_SIZE       0x100000UL
#define GICR_PE_SIZE    0x20000UL
#define VTIMER_INTID    19
#define PSHOLD          0x0c264000UL
#endif

#define FB_W            1080
#define FB_H            2400
#define FB_STRIDE       4320
#define FB_VISIBLE_SIZE (FB_STRIDE * FB_H)
_Static_assert(FB_VISIBLE_SIZE <= FB_RESERVED, "visible framebuffer exceeds reservation");
#define UFS_BASE        0x01d84000UL
#define IMEM_RESTART_REASON 0x146aa65cUL
#define TIMER_HZ        19200000UL
#define IDENTITY_LOW_SIZE (8UL << 30)
#define IDENTITY_LIMIT  (64UL << 30)
