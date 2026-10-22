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
CMDLINE="debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam"
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
    --dump

echo
echo "== Build XNU payload =="

# Rebuild the known diagnostic root after CI, before embedding its bytes.
if [[ "$RAMDISK" == "$(pwd)/shim/out/marble-xnu/marble-init" ]]; then
    clang -target arm64-apple-ios16.0 -DMARBLE_INIT -c tools/sweet-init.S \
        -o shim/out/marble-xnu/marble-init.o
    python3 tools/mkinit.py shim/out/marble-xnu/marble-init.o "$RAMDISK"
fi

python3 tools/mkpayload.py \
    "$KERNEL" \
    shim/out/marble-xnu/marble.adt \
    shim/out/marble-xnu/marble-xnu.payload \
    --cmdline "$CMDLINE" "${PAYLOAD_ARGS[@]}"

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
