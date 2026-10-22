#!/usr/bin/env bash
# Convert a local raw root image, then compare its entire sparse expansion.
set -euo pipefail
[[ $# == 2 ]] || { echo "Usage: $0 ROOT.img ROOT.simg" >&2; exit 2; }
raw=$(realpath "$1")
out=$2
[[ -f $raw && -s $raw && ! -e $out ]] || { echo 'Missing raw image or output exists' >&2; exit 1; }
work=$(mktemp -d "$(dirname "$out")/sparse-check-XXXXXX")
trap 'rm -f "$work/expanded.img"; rmdir "$work"' EXIT
img2simg "$raw" "$out"
simg2img "$out" "$work/expanded.img"
cmp "$raw" "$work/expanded.img"
echo "PASS sparse expansion: all $(stat -c %s "$raw") source bytes identical"
sha256sum "$raw" "$out"
