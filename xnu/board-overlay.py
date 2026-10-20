#!/usr/bin/env python3
"""Adapt the copied SWEET patch series to another board before the CI build.

Usage: board-overlay.py BOARD PATCH_DIR   (BOARD: sweet = no changes, ginkgo)

ginkgo (Redmi Note 8, SM6125) has Cortex-A53/A73 cores: ARMv8.0, so no LSE
atomics and no PAN. The SWEET machine config targets ARMv8.2 (A55/A76).
The early framebuffer console (0010, 0012) hard-codes sweet's splash
address 0x9c000000, which is kernel RAM on ginkgo (splash at 0x5c000000,
1080x2340). 0012's context lines repeat 0010's result, so both change.
Each edit replaces one line in place, so hunk line counts stay valid.
"""
import os, sys

EDITS = {
    'ginkgo': [
        ('0004-sweet-machine-config.patch',
         '+MACHINE_FLAGS_ARM64_SWEET = -DARM64_BOARD_CONFIG_SWEET                -march=armv8.2-a+crypto\n',
         '+MACHINE_FLAGS_ARM64_SWEET = -DARM64_BOARD_CONFIG_SWEET -DSWEET_GINKGO -march=armv8-a+crypto\n'),
        ('0004-sweet-machine-config.patch',
         '+#define __ARM_PAN_AVAILABLE__     1\n',
         '+/* ginkgo: Cortex-A53/A73 are ARMv8.0, no PAN */\n'),
        ('0010-sweet-early-framebuffer-debug.patch',
         '+\tMOV64\tx0, (0x9c000000 + 2368 * 4320)\n',
         '+\tMOV64\tx0, (0x5c000000 + 2308 * 4320)\n'),
        ('0010-sweet-early-framebuffer-debug.patch',
         '+\tMOV64\tx10, 0x9c000000\n',
         '+\tMOV64\tx10, 0x5c000000\n'),
        ('0010-sweet-early-framebuffer-debug.patch',
         '+#define EARLY_FB ((volatile uint32_t *)(uintptr_t)0x9c000000)\n',
         '+#define EARLY_FB ((volatile uint32_t *)(uintptr_t)0x5c000000)\n'),
        ('0010-sweet-early-framebuffer-debug.patch',
         '+#define EARLY_HEIGHT 2400u\n',
         '+#define EARLY_HEIGHT 2340u\n'),
        ('0012-sweet-keep-debug-console-after-ttbr0.patch',
         '+\t*slot = 0x9c000000ULL | ARM_TTE_VALID | ARM_TTE_TYPE_BLOCK |\n',
         '+\t*slot = 0x5c000000ULL | ARM_TTE_VALID | ARM_TTE_TYPE_BLOCK |\n'),
        ('0012-sweet-keep-debug-console-after-ttbr0.patch',
         '-#define EARLY_FB ((volatile uint32_t *)(uintptr_t)0x9c000000)\n',
         '-#define EARLY_FB ((volatile uint32_t *)(uintptr_t)0x5c000000)\n'),
        ('0012-sweet-keep-debug-console-after-ttbr0.patch',
         '+static volatile uint32_t *early_fb = (volatile uint32_t *)(uintptr_t)0x9c000000;\n',
         '+static volatile uint32_t *early_fb = (volatile uint32_t *)(uintptr_t)0x5c000000;\n'),
        ('0012-sweet-keep-debug-console-after-ttbr0.patch',
         ' #define EARLY_HEIGHT 2400u\n',
         ' #define EARLY_HEIGHT 2340u\n'),
    ],
}


def main():
    board, patch_dir = sys.argv[1], sys.argv[2]
    if board == 'sweet':
        return
    if board not in EDITS:
        raise SystemExit(f'unknown board {board!r}')
    for name, old, new in EDITS[board]:
        path = os.path.join(patch_dir, name)
        lines = open(path, newline='').read().splitlines(keepends=True)
        hits = [i for i, l in enumerate(lines) if l.rstrip('\r\n') == old.rstrip('\n')]
        if len(hits) != 1:
            raise SystemExit(f'{name}: expected exactly one {old.strip()!r}, found {len(hits)}')
        i = hits[0]
        lines[i] = new.rstrip('\n') + lines[i][len(lines[i].rstrip('\r\n')):]
        open(path, 'w', newline='').write(''.join(lines))
        print(f'{board}: {name}: {old.strip()} -> {new.strip()}')


if __name__ == '__main__':
    main()
