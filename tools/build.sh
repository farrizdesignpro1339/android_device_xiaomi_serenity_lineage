#!/usr/bin/env bash
#
# SPDX-FileCopyrightText: The Redmi A5 (serenity) Project
# SPDX-License-Identifier: Apache-2.0
#
# Build LineageOS for the Redmi A5 (serenity) on a machine that has never
# seen a LineageOS checkout before.
#
#   ./tools/build.sh [lineage-22.0|lineage-23.2|lineage-24.0]
#
# It checks the machine first, because a build that dies two hours in over a
# missing package is a bad afternoon, then it syncs shallow, builds and leaves
# the images where the user expects them.
#
set -euo pipefail

BRANCH="${1:-lineage-23.2}"
TREE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOP="$(cd "$TREE/../.." && pwd)"
JOBS="$(nproc)"
LOG="$TOP/build-$BRANCH.log"

# A build wants about 16 GB of memory and 100 GB of disk. The disk number is
# for a shallow sync, a full one is three times that.
MIN_RAM_GB=12
MIN_DISK_GB=80
MIN_THREADS=4

say() { printf '\n\033[1;33m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

say "checking the machine"
[ "$(uname -s)" = Linux ] || die "Android builds need Linux, this is $(uname -s)"

RAM_GB=$(( $(awk '/MemTotal/ {print $2}' /proc/meminfo) / 1024 / 1024 ))
THREADS="$(nproc)"
DISK_GB=$(( $(df -BG --output=avail "$TOP" | tail -1 | tr -dc '0-9') ))
printf '  memory   %s GB\n  threads  %s\n  disk     %s GB free in %s\n' \
    "$RAM_GB" "$THREADS" "$DISK_GB" "$TOP"

[ "$RAM_GB" -ge "$MIN_RAM_GB" ] || \
    die "only $RAM_GB GB of memory, the build needs at least $MIN_RAM_GB GB. \
Close everything else and check for swap pressure"
[ "$THREADS" -ge "$MIN_THREADS" ] || \
    die "only $THREADS threads, the build needs at least $MIN_THREADS"
[ "$DISK_GB" -ge "$MIN_DISK_GB" ] || \
    die "only $DISK_GB GB free in $TOP, the build needs at least $MIN_DISK_GB GB"

for tool in git repo python3 make clang; do
    command -v "$tool" >/dev/null 2>&1 || die "$tool is not installed"
done

# The build writes outside the tree, so a sync has to land next to it
if [ ! -d "$TOP/.repo" ]; then
    say "initialising the source tree in $TOP"
    repo init -u https://github.com/LineageOS/android.git -b "$BRANCH" \
        --git-lfs --depth 1
fi

# The device tree and the vendor repo have to be where repo expects them
mkdir -p "$TOP/device/xiaomi" "$TOP/vendor/xiaomi"
if [ ! -d "$TOP/device/xiaomi/serenity/.git" ]; then
    say "cloning the device tree"
    git clone -b "$BRANCH" --depth 1 \
        https://github.com/farrizdesignpro1339/android_device_xiaomi_serenity_lineage.git \
        "$TOP/device/xiaomi/serenity"
fi
if [ ! -d "$TOP/vendor/xiaomi/serenity/.git" ]; then
    say "cloning the vendor blobs"
    git clone -b "$BRANCH" \
        https://github.com/farrizdesignpro1339/android_vendor_xiaomi_serenity_lineage.git \
        "$TOP/vendor/xiaomi/serenity"
fi

# The build finds device trees through the manifest, not by looking at the
# filesystem, so a tree that only sits in device/ is invisible to lunch. That
# is what "Trying dependencies-only mode on a non-existing device tree?" means.
say "registering the device tree and the vendor repo in the manifest"
mkdir -p "$TOP/.repo/local_manifests"
cat > "$TOP/.repo/local_manifests/serenity.xml" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <project name="farrizdesignpro1339/android_device_xiaomi_serenity_lineage"
           path="device/xiaomi/serenity"
           branch="$BRANCH" />
  <project name="farrizdesignpro1339/android_vendor_xiaomi_serenity_lineage"
           path="vendor/xiaomi/serenity"
           branch="$BRANCH" />
</manifest>
EOF

say "syncing, shallow, $JOBS jobs"
repo sync -c -j"$JOBS" --depth 1 --fail-fast

# A second build is much faster with a cache, and the cache has to sit on disk
if command -v ccache >/dev/null 2>&1; then
    CACHE_DIR="$TOP/.ccache"
    mkdir -p "$CACHE_DIR"
    say "pointing ccache at $CACHE_DIR"
    {
        echo "export CCACHE_DIR=$CACHE_DIR"
        echo "export CCACHE_BASEDIR=$TOP"
        echo "export CCACHE_MAXSIZE=20G"
        echo "export USE_CCACHE=1"
    } > "$TOP/ccache.env"
    # shellcheck disable=SC1091
    . "$TOP/ccache.env"
fi

say "building lineage_serenity, this is the slow part"
# shellcheck disable=SC1091
. "$TOP/build/envsetup.sh" >/dev/null
lunch lineage_serenity-userdebug >/dev/null
mka bacon -j"$JOBS" 2>&1 | tee "$LOG"

say "done, images in $TOP/out/target/product/serenity"
ls -la "$TOP/out/target/product/serenity"/*.zip 2>/dev/null || true
