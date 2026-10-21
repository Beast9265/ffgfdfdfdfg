#!/bin/bash
# Build the shim and wrap it in a boot.img v2 that mirrors the stock PixelOS header.
set -euo pipefail
cd "$(dirname "$0")"
CC=aarch64-linux-gnu-gcc
OBJCOPY=aarch64-linux-gnu-objcopy
CFLAGS="-O2 -ffreestanding -nostdlib -fno-pic -mgeneral-regs-only -mstrict-align -fno-stack-protector -Wall -Wextra"
board=${BOARD:-sweet}
case "$board" in
sweet)
	out=out
	sources=(start.S shim.c console.c mmu.c fdt.c loader.c ufs.c)
	;;
marble-xnu)
	[ "$#" -le 1 ] || { echo "marble-xnu accepts one optional payload" >&2; exit 1; }
	[ "$#" = 0 ] || [ -s "$1" ] || { echo "missing/empty XNU payload" >&2; exit 1; }
	out=out/marble-xnu
	CFLAGS+=" -DSHIM_MARBLE -DSHIM_MARBLE_XNU -ffunction-sections -fdata-sections"
	sources=(start.S shim.c console.c mmu.c fdt.c loader.c)
	;;
marble)
	[ "$#" = 0 ] || { echo "MARBLE stage 0 rejects payload arguments" >&2; exit 1; }
	out=out/marble
	CFLAGS+=" -DSHIM_MARBLE"
	sources=(start.S shim.c console.c mmu.c ufs.c)
	;;
*) echo "Unknown BOARD: $board" >&2; exit 1 ;;
esac
mkdir -p "$out"
objects=()
cobjects=()
for f in "${sources[@]}"; do
	obj="$out/${f%.*}.o"
	$CC $CFLAGS -c "$f" -o "$obj"
	objects+=("$obj")
	[[ "$f" != *.c ]] || cobjects+=("$obj")
done
# The image runs wherever ABL puts it with no relocation pass: only the
# header's image_size (start.o, linked at 0) may be an absolute address.
abs=$(aarch64-linux-gnu-readelf -r "${cobjects[@]}" | grep -c ABS64 || true)
[ "$abs" = 0 ] || { echo "error: $abs absolute relocations in C objects" >&2; exit 1; }
ldflags=()
[ "$board" != marble-xnu ] || ldflags+=(-Wl,--gc-sections)
$CC $CFLAGS "${ldflags[@]}" -static -T shim.ld -Wl,--build-id=none -Wl,--no-warn-rwx-segments -Wl,-N \
	"${objects[@]}" -o "$out/shim.elf"
$OBJCOPY -O binary "$out/shim.elf" "$out/Image"
# ABL copies the file; pad to image_size so .bss/stacks exist as zeroed bytes.
size=$(aarch64-linux-gnu-nm "$out/shim.elf" | awk '$3=="_end"{print strtonum("0x"$1)}')
truncate -s "$size" "$out/Image"
if [ "$board" = marble-xnu ] && [ -n "${1:-}" ]; then
	cp "$1" "$out/ramdisk.bin"
	echo "Payload copied to $out/ramdisk.bin; use explicit v4 repack --xnu-payload."
fi
if [ "$board" = marble ] || [ "$board" = marble-xnu ] || [ "${SHIM_RAW_ONLY:-0}" = 1 ]; then
	echo "$board raw Image only; boot packaging requires board-specific verification."
	ls -l "$out/Image" "$out/shim.elf"
	exit 0
fi
# Ramdisk: an xnu payload (tools/mkpayload.py) if given as $1, else an empty
# newc cpio (ABL dislikes a zero-size ramdisk on some builds) -> diagnostics.
if [ -n "${1:-}" ]; then
	cp "$1" out/ramdisk.bin
else
	(cd out && rm -rf rd && mkdir rd && cd rd && find . | cpio -o -H newc --quiet | gzip -9 > ../ramdisk.bin)
fi
mkbootimg --header_version 2 --kernel out/Image --ramdisk out/ramdisk.bin \
	--dtb ../dtb/boot_unpacked/dtb --base 0 --kernel_offset 0x8000 --ramdisk_offset 0x1000000 \
	--tags_offset 0x100 --dtb_offset 0x1f00000 --pagesize 4096 \
	--os_version 17.0.0 --os_patch_level 2035-06 \
	--cmdline "console=null" -o out/shim-boot.img
# Host render of the console layout.
gcc -O1 -Wall -o out/host_test console.c host_test.c && ./out/host_test
ls -l out/Image out/shim-boot.img
