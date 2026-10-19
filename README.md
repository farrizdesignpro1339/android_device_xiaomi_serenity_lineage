# Device tree for the Xiaomi Redmi A5 / POCO C71 (serenity)

LineageOS device tree for the Redmi A5, built on the Unisoc T7250 platform.
Everything the port needs that is not a blob comes out of the stock factory ROM
listed below; nothing here is carried over from the PixelOS tree.

## Device specifications

| Basic                   | Spec                                                        |
| ----------------------- | :---------------------------------------------------------- |
| SoC                     | Unisoc T7250 (UMS9230), 12 nm                               |
| CPU                     | Octa-core (2x 1.8 GHz Cortex-A75 & 6x 1.6 GHz Cortex-A55)   |
| GPU                     | Mali-G57 MP1                                                |
| Memory                  | 3/4 GB LPDDR4X                                              |
| Shipped Android version | 15 (Go edition), vendor VNDK 33                             |
| Storage                 | 64/128 GB eMMC 5.1, dedicated microSD slot                   |
| Battery                 | Non-removable Li-Polymer 5200 mAh                           |
| Display                 | IPS LCD 120 Hz, 6.88 inches, 720 x 1640 pixels, 320 dpi      |
| Rear camera             | 32 MP f/2.0                                                 |
| Front camera            | 8 MP f/2.2                                                  |
| Fingerprint             | Side-mounted                                                |
| Models                  | 25028PC03G, 25028RN03A, 25028RN03I, 25028RN03Y, 25028RN03L   |

## Stock source

Everything that is copied rather than written was read out of one factory ROM
and its unpacked super:

| What                     | Where                                                     |
| :----------------------- | :-------------------------------------------------------- |
| kernel, dtb, dtbo        | `serenity_global-images-A15.0.32.0.VGWMIXM-...-global-86b67f47c4` |
| vendor, odm, vendor_dlkm | the same ROM, unpacked into a stock tree (see below)      |
| partition metadata       | `lpdump` of the stock super.img                           |
| fstab                    | first stage ramdisk of the stock vendor_boot              |

## Layout

```
BoardConfig.mk        partition sizes, AVB, prebuilt kernel wiring
device.mk             packages, kernel module loader config
lineage_serenity.mk   product identity
Android.bp            the vendor_dlkm module symlink, declared by hand
vendor.prop           generated from the stock vendor build.prop
odm.prop              generated from the stock odm build.prop
system.prop           volume steps and the game frame rate cap
proprietary-files.txt generated blob list
prebuilts/            kernel, dtb, dtbo and the .ko set, all stock
rootdir/etc/          the first stage fstab
configs/vintf/        stock manifest and matrices, framework matrix is ours
configs/overlay/      the runtime overlay declarations and the apk exclusion list
sepolicy/vendor/      generated from the stock policy
tools/                the generators, every one of them re-runnable
```

## Build

The tree has to sit at `device/xiaomi/serenity`, the vendor repo at
`vendor/xiaomi/serenity`:

```bash
git clone <this repo> device/xiaomi/serenity
repo init -u https://github.com/LineageOS/android.git -b lineage-23.2   # or -b lineage-22.0 / -b lineage-24.0
repo sync -c -j$(nproc)

# the vendor repo, either with extract-utils or without it
./device/xiaomi/serenity/extract-files.py
./device/xiaomi/serenity/setup-makefiles.py

source build/envsetup.sh
lunch lineage_serenity-userdebug
m bacon
```

`extract-files.py` needs the LineageOS checkout above. Without one,
`tools/make-vendor-repo.py` builds the same repo from the blob list directly,
which is how the current one was made:

```bash
./device/xiaomi/serenity/tools/make-vendor-repo.py "$SERENITY_STOCK" \
    ../android_vendor_xiaomi_serenity_lineage
```

It copies the blobs, writes `serenity-vendor.mk` as one PRODUCT_COPY_FILES
block and declares the symlinks in `Android.bp`. The blobs land as copies
rather than prebuilt modules, so nothing may ask for a vendor library by module
name; device.mk declares the handful it needs itself.

## Branches

| Branch | Platform | Shipping API | Notes |
| :--- | :--- | :--- | :--- |
| `dev` | shared | | the base every platform branch sits on |
| `lineage-22.0` | Android 15 | 35 | matches the stock system generation, lunch target `lineage_serenity-ap3a-userdebug` |
| `lineage-23.2` | Android 16 | 36 | the base |
| `lineage-24.0` | Android 17 | 36 | the toybox `[` builtin moves to a hand declared symlink |

A VNDK 33 vendor throughout, which is normal: VNDK is frozen, a vendor stays
where it is and the platform moves on. What the tree declares is the vendor
snapshot, so the shipping API follows the platform, not the vendor.

`configs/vintf/framework_compatibility_matrix.xml` names the sepolicy versions
the platform can load a vendor policy for. It stops at 202404 on
`lineage-22.0`, because that is what Android 15 has; the other two carry 202504
as well. Naming a version the platform does not know is a build failure.

`dev` holds what the three platform branches share, and each platform branch
sits on it. A change that belongs to every platform goes to `dev` and is then
merged into the three. A change that belongs to one platform goes straight to
that branch.

Do not merge one platform branch into another. They are siblings, not a chain,
and a merge drags the other branch's platform bits along: merging
`lineage-22.0` into `lineage-23.2` would take the Android 15 shipping API and
the trimmed compatibility matrix with it, and merging `lineage-24.0` into
`lineage-23.2` would take the Android 17 changes, where the platform still
ships the toybox symlink farm and init_boot still wants its own header
version.

The files that differ per branch, and so are the only places a merge from
`dev` can conflict, are `platform.mk`, the one line with the shipping API, and
`configs/vintf/framework_compatibility_matrix.xml`, which names the sepolicy
versions the platform can load a vendor policy for. This README is the same
everywhere, so it never conflicts.

## Regenerating

The tools take their paths from the environment, so they work from anywhere:

```bash
export SERENITY_TREE=$PWD                      # this tree
export SERENITY_STOCK=/path/to/stock/tree      # unpacked vendor and odm
export SERENITY_AOSP=$ANDROID_BUILD_TOP        # only needed by the sepolicy tools
export SERENITY_VENDOR_REPO=$ANDROID_BUILD_TOP/vendor/xiaomi/serenity

./tools/gen-blobs.py  "$SERENITY_STOCK"        # proprietary-files.txt
./tools/gen-props.py  "$SERENITY_STOCK"        # vendor.prop, odm.prop
./tools/gen-overlay-decls.py "$SERENITY_STOCK"   # overlay declarations
./tools/gen-blobs.py  "$SERENITY_STOCK" -x configs/overlay/overlay-exclude.txt
./tools/make-vendor-repo.py "$SERENITY_STOCK" ../android_vendor_xiaomi_serenity_lineage
./tools/genpolicy.py                            # report only, writes nothing
./tools/emit.py                                 # sepolicy/vendor
```

`genpolicy.py --write` is a no-op, the writer is `emit.py`. genpolicy only
prints what it found.

## Lunch targets

| Branch | Lunch target |
| :--- | :--- |
| `lineage-22.0` | `lineage_serenity-ap3a-userdebug` |
| `lineage-23.2` | `lineage_serenity-userdebug` |
| `lineage-24.0` | `lineage_serenity-userdebug` |

Android 15 is AP3A, so the LineageOS 22 target carries the platform suffix. The
product makefile is `lineage_serenity.mk` on every branch and `PRODUCT_NAME` is
`lineage_serenity` on every branch; only the lunch choice differs. The 22.0
branch lists the plain spelling as well, so `lunch lineage_serenity-userdebug`
works there too.

## Notes on the numbers

The stock super is 5120 MiB and carries the `virtual_ab_device` flag with two
groups, `group_unisoc_a` and `group_unisoc_b`, both capped at 5364514816. The
build makes one group and suffixes the slot itself, so `BOARD_GROUP_UNISOC_SIZE`
is that same 5364514816.

The kernel is a prebuilt. Xiaomi never published a GPL kernel for the T7250,
and the vendor snapshot is VNDK 33, which predates the GKI 6.x the platform
wants to boot, so the stock kernel and its module set are what runs. The
consequence is that the tree builds a `kernel/` that is really just the stock
image plus the module directory, and nothing in the port can change kernel
behaviour.

The blob list drops `vendor/firmware/backup` and `vendor/firmware/Simulation`,
roughly 1.5 GB of camera tuning data for sensors this phone does not have and
for the tuning tool. What is left is about 1.9 GB of blobs, which is what lets
the vendor, odm and the Android 15 system fit inside the 5120 MiB group.

`prebuilts/modules/` carries the stock `modules.load` plus the two boot mode
lists, and `init.insmod.cfg` goes to `vendor_dlkm/lib/modules` from device.mk
because the loader reads it from there.

The stock ships 31 runtime overlay apks and declares none of them: there is no
`overlay` element in vendor, odm or product, so on stock they never apply.
`tools/gen-overlay-decls.py` reads each manifest with aapt, keeps the eight
target packages a LineageOS build actually has, and writes both the
declaration and the list of apks that must stay out of the vendor repo. The
apks come in pairs per platform, for example `AospBtOverlay` against
`AospBtOverlay_Qogirl6` and `NetworkStackOverlayGo` against the Gsi cut, and a
declaration is per target package, so the losing half of a pair has to be left
out of the image entirely, not merely left undeclared. `PRODUCT_ENFORCE_RRO_TARGETS`
is unset on purpose for the same reason: an overlay that survives the generator
but is not declared would fail the build instead of the boot.

Whether the surviving overlays apply depends on the overlayable policy in their
manifests matching what the target package declares, so check logcat for RRO
failures before assuming they took.

Symlinks are carried by the `SYMLINK=` directive in the blob list, which is
how extract-utils reads them: the blob is the file the chain ends at, and the
directive names the paths that have to point at it. That covers
`vulkan.ums9230.so` and the four `libOpenCL` aliases per architecture. The
vendor/odm and tsx_data links point outside the tree, so they are declared by
hand in the vendor repo instead.

The fstab is the full one, not the 11 lines the stock vendor ramdisk ships.
Xiaomi mounts data, cache and the sdcard from init rc, and a LineageOS port
needs them in the fstab instead.

## Verification

Four checkers came over from the Z2577 port and all of them run here. They read
the tree, the vendor repo and the stock tree, and the only thing they cannot do
without a LineageOS checkout is compare against the platform policy.

```bash
export SERENITY_TREE=$PWD
export SERENITY_STOCK=/path/to/stock/tree
export SERENITY_VENDOR_REPO=../android_vendor_xiaomi_serenity_lineage
export SERENITY_PLATFORM_VINTF=$SERENITY_STOCK/system/etc/vintf

python3 tools/check_policy.py          # the sepolicy against the stock CIL
python3 tools/preflight.py             # both repos: modules, copies, blobs
python3 tools/elf_audit.py             # every .so, SONAME and dependency
python3 tools/vintf_coverage.py        # vendor manifest against the platform matrices
```

Where they stand:

| Check | Result |
| :--- | :--- |
| sepolicy | nothing unresolved, nothing declared twice, 961 labels resolve |
| preflight | 0 findings, 17 notes, every note an AOSP module it cannot see here |
| ELF | 0 SONAME missing, 0 SONAME with nothing providing it, 0 unresolved deps |
| VINTF | every `android.hardware.*` HAL the vendor declares is in a platform matrix |

The sepolicy is emitted in the classic .te form, not the CIL s-expression the
stock ships: `allow src tgt:class perms`, `allowxperm` for extended ioctls,
`type_transition` for the transitions, and `genfscon fs "path" u:object_r:type:s0`
for the genfs lines. `tools/emit.py` does that conversion and it also fixes up
the CIL shape in three places that are easy to get wrong: an ioctl range becomes
`a - b`, a class-context pair takes its first entry, and a transition with no
name has four arguments rather than five.

The prebuilt policy is generated from the stock CIL, so it is the vendor half
only. Whether a `hal_*_default` domain belongs to the platform or to this tree
is decided by walking `system/sepolicy/vendor`, which needs `SERENITY_AOSP`. With
it unset, every domain the stock declares is declared here, which is the safe
direction: a duplicate declaration is one line to delete, a missing one breaks
hundreds of rules. Point `SERENITY_AOSP` at a checkout and run `emit.py` again
to drop the ones the platform owns.

## What still needs work

- The sepolicy passes every checker here but has never been compiled. The one
  thing that cannot be checked without a LineageOS checkout is which
  `hal_*_default` domains the platform already declares; see Verification.
- No kernel source, so no kernel level features: no KernelSU, no per device
  tuning, no way to fix a driver bug in the port.
- Camera, fingerprint and the fingerprint HAL policy were not tested on
  hardware from this tree.
- The overlay declaration targets `com.android.connectivity.resources` and
  `com.android.wifi.resources`, both modules. On a build without the matching
  module the declaration is dead weight and the apks are ignored at boot.
- Play Integrity will fail, the ROM is signed with the AOSP test keys.