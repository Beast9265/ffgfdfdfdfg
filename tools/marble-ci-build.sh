#!/usr/bin/env bash
set -euo pipefail

REPO="Beast9265/ios-marble"
BRANCH="marble"
WORKFLOW="xnu.yml"

RAMDISK=""
CMDLINE_EXTRA=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --ramdisk|--cmdline-extra)
            [[ $# -ge 2 ]] || { echo "ERROR: $1 needs a value"; exit 1; }
            if [[ "$1" == --ramdisk ]]; then RAMDISK="$2"; else CMDLINE_EXTRA="$2"; fi
            shift 2 ;;
        --*) echo "ERROR: unknown option $1"; exit 1 ;;
        *) break ;;
    esac
done
[[ $# -eq 1 ]] || { echo "Usage: $0 [--ramdisk PATH] [--cmdline-extra ARGS] \"commit message\""; exit 1; }
COMMIT_MSG="$1"
# Resolve before changing directory. No default behavior changes.
if [[ -n "$RAMDISK" ]]; then
    [[ -s "$RAMDISK" ]] || { echo "ERROR: missing/empty RAMDisk: $RAMDISK"; exit 1; }
    RAMDISK="$(realpath "$RAMDISK")"
fi
# Physically verified MARBLE SMP8/UFS/bitbang-touch baseline.  Keep this
# explicit: mkadt.py and mkpayload.py intentionally have generic one-CPU
# defaults which are not suitable for a normal MARBLE phone image.
CMDLINE="debug=0xc serial=3 cpus=8 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 ufsrw=1 rootrw=1 launchd_unsecure_cache=1 marbleguidiag=1 marblehwdiag=1 marbleusb=0 marbleusblog=0 marbletouch=1 marbletouchinit=1 marbletouchbb=1 sweetfb_noconsole=1 marblesmpsample=1"
if [[ -n "$CMDLINE_EXTRA" ]]; then CMDLINE+=" $CMDLINE_EXTRA"; fi
[[ ${#CMDLINE} -lt 608 ]] || { echo "ERROR: cmdline too long"; exit 1; }
PAYLOAD_ARGS=()
if [[ -n "$RAMDISK" ]]; then PAYLOAD_ARGS=(--ramdisk "$RAMDISK"); fi

cd "$(git rev-parse --show-toplevel)"

echo "========================================"
echo "MARBLE XNU CI + LOCAL PACKAGING"
echo "========================================"

# ------------------------------------------------------------------
# Safety / prerequisites
# ------------------------------------------------------------------

if [[ "$(git branch --show-current)" != "$BRANCH" ]]; then
    echo "ERROR: must be on branch '$BRANCH'"
    exit 1
fi

command -v git >/dev/null
command -v gh >/dev/null
command -v python3 >/dev/null

gh auth status >/dev/null

if [[ ! -f marble-boot-backup-clean/boot_a.img ]]; then
    echo "ERROR: missing marble-boot-backup-clean/boot_a.img"
    exit 1
fi

echo
echo "== Repository validation =="

git diff --check
git diff --cached --check

if git diff --cached --quiet; then
    echo "ERROR: nothing is staged."
    echo "Codex must stage only the intended source/docs changes first."
    exit 1
fi

echo
git diff --cached --stat

# Never allow common generated/private artifacts into the commit.
BAD_STAGED="$(
    git diff --cached --name-only |
    grep -E '(^|/)(boot_a\.img|.*\.ipsw|.*\.img|.*\.payload|kernel\.development\.marble|ramdisk\.bin)$' \
    || true
)"

if [[ -n "$BAD_STAGED" ]]; then
    echo
    echo "ERROR: generated/private artifacts are staged:"
    echo "$BAD_STAGED"
    exit 1
fi

# ------------------------------------------------------------------
# Commit + push
# ------------------------------------------------------------------

echo
echo "== Commit =="

git commit -m "$COMMIT_MSG"

COMMIT_SHA="$(git rev-parse HEAD)"
SHORT_SHA="$(git rev-parse --short HEAD)"

echo "Commit: $COMMIT_SHA"

echo
echo "== Push =="

git push origin "$BRANCH"

# ------------------------------------------------------------------
# GitHub Actions
# ------------------------------------------------------------------

echo
echo "== Trigger GitHub Actions =="

gh workflow run "$WORKFLOW" \
    -R "$REPO" \
    --ref "$BRANCH" \
    -f macos_version=13.5 \
    -f kernel_config=DEVELOPMENT \
    -f machine_config=MARBLE \
    -f keep_going=true

echo
echo "Waiting for workflow run to appear..."

RUN_ID=""

for _ in $(seq 1 30); do
    RUN_ID="$(
        gh run list \
            -R "$REPO" \
            --workflow "$WORKFLOW" \
            --branch "$BRANCH" \
            --limit 20 \
            --json databaseId,headSha,event \
            --jq ".[] | select(.headSha == \"$COMMIT_SHA\" and .event == \"workflow_dispatch\") | .databaseId" \
            | head -1
    )"

    if [[ -n "$RUN_ID" ]]; then
        break
    fi

    sleep 2
done

if [[ -z "$RUN_ID" ]]; then
    echo "ERROR: could not find workflow run for $COMMIT_SHA"
    exit 1
fi

echo "Actions run: $RUN_ID"

echo
echo "== Watch build =="

gh run watch "$RUN_ID" \
    -R "$REPO" \
    --exit-status

# ------------------------------------------------------------------
# Download exact artifact
# ------------------------------------------------------------------

echo
echo "== Download exact XNU artifact =="

ARTIFACT_DIR="xnu/out-marble-ci-${RUN_ID}"

mkdir "$ARTIFACT_DIR" # fail rather than reuse/delete an old artifact directory

gh run download "$RUN_ID" \
    -R "$REPO" \
    -n xnu-kernel \
    -D "$ARTIFACT_DIR"

KERNEL="$(
    find "$ARTIFACT_DIR" \
        -type f \
        -name 'kernel.development.marble' \
        -print \
        -quit
)"

if [[ -z "$KERNEL" || ! -f "$KERNEL" ]]; then
    echo "ERROR: kernel.development.marble not found in Actions artifact"
    exit 1
fi

echo "Kernel: $KERNEL"
file "$KERNEL"

# ------------------------------------------------------------------
# ADT + XNU payload
# ------------------------------------------------------------------

echo
echo "== Generate MARBLE ADT =="

mkdir -p shim/out/marble-xnu

python3 tools/mkadt.py \
    shim/out/marble-xnu/marble.adt \
    --marble \
    --marble-cpus 8 \
    --dump

echo
echo "== Build XNU payload =="

# Rebuild the known diagnostic root after CI, before embedding its bytes.
if [[ "$RAMDISK" == "$(pwd)/shim/out/marble-xnu/marble-init" ]]; then
    clang -target arm64-apple-ios16.0 -DMARBLE_INIT -c tools/sweet-init.S \
        -o shim/out/marble-xnu/marble-init.o
    python3 tools/mkinit.py shim/out/marble-xnu/marble-init.o "$RAMDISK"
fi

# HFS diagnostic root: rebuild init and filesystem after the exact CI download.
if [[ "$RAMDISK" == "$(pwd)/shim/out/marble-xnu/MarbleRoot.img" ]]; then
    clang -target arm64-apple-ios16.0 -DMARBLE_INIT -c tools/sweet-init.S \
        -o shim/out/marble-xnu/marble-init.o
    python3 tools/mkinit.py shim/out/marble-xnu/marble-init.o \
        shim/out/marble-xnu/marble-init
    ROOT_TMP="$(mktemp -d shim/out/marble-xnu/hfs-build-XXXXXX)"
    python3 tools/mkmarble-test-root.py shim/out/marble-xnu/marble-init "$ROOT_TMP/MarbleRoot.img"
    mv "$ROOT_TMP/MarbleRoot.img" "$RAMDISK"
    rmdir "$ROOT_TMP"
    sha256sum shim/out/marble-xnu/marble-init
fi

python3 tools/mkpayload.py \
    "$KERNEL" \
    shim/out/marble-xnu/marble.adt \
    shim/out/marble-xnu/marble-xnu.payload \
    --cmdline "$CMDLINE" "${PAYLOAD_ARGS[@]}"

# Audit the bytes that will actually be wrapped into boot.img, not merely the
# input ADT and shell variable.  This catches accidental one-CPU defaults or a
# truncated/replaced command line before packaging.
python3 - shim/out/marble-xnu/marble-xnu.payload "$CMDLINE" <<'PY'
import pathlib
import struct
import sys

sys.path.insert(0, 'tools')
import adt
import mkadt

payload = pathlib.Path(sys.argv[1]).read_bytes()
expected = sys.argv[2]
if payload[:8] != b'SWEETXNU':
    raise SystemExit('ERROR: generated payload has invalid magic')
actual = payload[0x48:0x48 + 608].split(b'\0', 1)[0].decode()
if actual != expected:
    raise SystemExit(f'ERROR: generated payload command line mismatch: {actual!r}')
adt_offset, adt_size = struct.unpack_from('<QQ', payload, 0x20)
adt_blob = payload[adt_offset:adt_offset + adt_size]
root, end = adt.parse(adt_blob)
topology = mkadt.cpu_topology(adt_blob)
if end != len(adt_blob) or [mpidr for mpidr, _ in topology] != [i << 8 for i in range(8)]:
    raise SystemExit(f'ERROR: generated payload is not MARBLE SMP8: {topology!r}')
print('Payload audit: exact command line and eight embedded ADT CPUs verified')
PY

if [[ -n "$RAMDISK" ]]; then
    python3 tools/marble-ramdisk-audit.py "$KERNEL" \
        shim/out/marble-xnu/marble-xnu.payload "$RAMDISK"
fi

# ------------------------------------------------------------------
# Shim
# ------------------------------------------------------------------

echo
echo "== Build MARBLE XNU shim =="

BOARD=marble-xnu shim/build.sh

# ------------------------------------------------------------------
# Android boot v4 package
# ------------------------------------------------------------------

FINAL_IMAGE="shim/out/marble-xnu/latest-marble-xnu.img"

rm -f "$FINAL_IMAGE"

echo
echo "== Repack boot image =="

python3 tools/mkbootv4_marble.py repack \
    marble-boot-backup-clean/boot_a.img \
    shim/out/marble-xnu/Image \
    "$FINAL_IMAGE" \
    --xnu-payload shim/out/marble-xnu/marble-xnu.payload

echo
echo "== Verify boot image =="

python3 tools/mkbootv4_marble.py inspect \
    "$FINAL_IMAGE"

# ------------------------------------------------------------------
# Final hashes
# ------------------------------------------------------------------

echo
echo "== SHA256 =="

KERNEL_SHA="$(sha256sum "$KERNEL" | awk '{print $1}')"
ADT_SHA="$(sha256sum shim/out/marble-xnu/marble.adt | awk '{print $1}')"
PAYLOAD_SHA="$(sha256sum shim/out/marble-xnu/marble-xnu.payload | awk '{print $1}')"
SHIM_SHA="$(sha256sum shim/out/marble-xnu/Image | awk '{print $1}')"
BOOT_SHA="$(sha256sum "$FINAL_IMAGE" | awk '{print $1}')"

echo "Kernel : $KERNEL_SHA"
echo "ADT    : $ADT_SHA"
if [[ -n "$RAMDISK" ]]; then sha256sum "$RAMDISK"; fi
echo "Payload: $PAYLOAD_SHA"
echo "Shim   : $SHIM_SHA"
echo "Boot   : $BOOT_SHA"

# ------------------------------------------------------------------
# Final answer
# ------------------------------------------------------------------

ABS_IMAGE="$(realpath "$FINAL_IMAGE")"

echo
echo "========================================"
echo "MARBLE XNU READY"
echo "========================================"
echo "Commit      : $SHORT_SHA"
echo "Actions run : $RUN_ID"
echo "Boot SHA256 : $BOOT_SHA"
echo "Image       : $ABS_IMAGE"
echo
echo "NO DEVICE OPERATION WAS PERFORMED."
echo
echo "BOOT MANUALLY:"
echo
echo "fastboot boot \"$ABS_IMAGE\""
echo
echo "========================================"
