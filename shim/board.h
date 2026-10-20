#pragma once
/*
 * Per-board constants. build.sh passes -DBOARD_<NAME> (default: sweet).
 *
 * BOARD_MPIDR(i): MPIDR (Aff1:Aff0) of physical core i, the value PSCI
 * CPU_ON expects. IMEM_RESTART_REASON / PSHOLD: 0 = not known for the
 * board yet; reset() then relies on PSCI SYSTEM_RESET alone.
 */

#if defined(BOARD_GINKGO)
/* Redmi Note 8, SM6125. Mainline sm6125.dtsi + sm6125-xiaomi-ginkgo-common.dtsi */
#define BOARD_NAME		"ginkgo"
#define GICD_BASE		0x0f200000UL
#define GICR_BASE		0x0f300000UL
#define FB_BASE			0x5c000000UL	/* reserved-memory cont_splash_mem */
#define FB_W			1080
#define FB_H			2340
#define BOARD_MPIDR(i)		((((uint64_t)(i) >> 2) << 8) | ((uint64_t)(i) & 3))
#define BOARD_HAS_UFS		0		/* eMMC on sdhc_1 */
#define IMEM_RESTART_REASON	0UL		/* TODO: qcom,msm-imem restart_reason from the stock DTB */
#define PSHOLD			0UL		/* TODO: qcom,pshold from the stock DTB */

#else
/* Redmi Note 10 Pro, SM7150 (sweet live FDT) */
#define BOARD_SWEET		1
#define BOARD_NAME		"sweet"
#define GICD_BASE		0x17a00000UL
#define GICR_BASE		0x17a60000UL
#define FB_BASE			0x9c000000UL	/* reserved-memory cont_splash_region */
#define FB_W			1080
#define FB_H			2400
#define BOARD_MPIDR(i)		((uint64_t)(i) << 8)
#define BOARD_HAS_UFS		1
#define IMEM_RESTART_REASON	0x146aa65cUL	/* qcom,msm-imem restart_reason@65c */
#define PSHOLD			0x0c264000UL
#endif

#define FB_STRIDE		(FB_W * 4)	/* a8r8g8b8, matches mainline simplefb */
