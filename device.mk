#
# SPDX-FileCopyrightText: The Redmi A5 (serenity) Project
# SPDX-License-Identifier: Apache-2.0
#

LOCAL_PATH := device/xiaomi/serenity

# Inherit some common Lineage stuff
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)

# Inherit from the serenity vendor blobs
$(call inherit-product, vendor/xiaomi/serenity/serenity-vendor.mk)

# APEX
$(call inherit-product, $(SRC_TARGET_DIR)/product/updatable_apex.mk)

# Virtual A/B with compressed snapshots
PRODUCT_VIRTUAL_AB_COMPRESSION_METHOD := lz4
PRODUCT_VIRTUAL_AB_COMPRESSION_FACTOR := 65536
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/generic_ramdisk.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/vabc_features.mk)

# Boot control
# The stock manifest registers vendor.sprd.hardware.boot@1.2-service, which is
# the Unisoc pass-through, so the AOSP boot HAL is the one that runs
PRODUCT_PACKAGES += \
    android.hardware.boot@1.2-impl \
    android.hardware.boot@1.2-impl.recovery \
    android.hardware.boot@1.2-service

# Xiaomi remote key provisioning
PRODUCT_PACKAGES += \
    rkp_factory_extraction_tool

# OTA
PRODUCT_PACKAGES += \
    update_engine \
    update_engine_sideload \
    update_verifier

PRODUCT_PACKAGES += \
    checkpoint_gc \
    otapreopt_script

AB_OTA_POSTINSTALL_CONFIG += \
    RUN_POSTINSTALL_system=true \
    POSTINSTALL_PATH_system=system/bin/otapreopt_script \
    FILESYSTEM_TYPE_system=erofs \
    POSTINSTALL_OPTIONAL_system=true

AB_OTA_POSTINSTALL_CONFIG += \
    RUN_POSTINSTALL_vendor=true \
    POSTINSTALL_PATH_vendor=bin/checkpoint_gc \
    FILESYSTEM_TYPE_vendor=erofs \
    POSTINSTALL_OPTIONAL_vendor=true

# fastbootd
PRODUCT_PACKAGES += \
    android.hardware.fastboot@1.1-impl-mock \
    fastbootd

# Runtime resource overlays
# The stock ships 31 overlay apks and declares none of them, there is no
# overlay element anywhere in vendor, odm or product, so on stock they are
# inert. configs/overlay/overlay-decls.xml declares the eight target packages
# that a LineageOS build can take, and tools/gen-overlay-decls.py writes the
# list of apks that must not ship alongside them.
# PRODUCT_ENFORCE_RRO_TARGETS is left unset on purpose: turning it on turns
# every undeclared overlay into a build error, and the declaration is generated
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/overlay/overlay-decls.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/overlay-decls.xml

# Kernel modules, the loader config and the boot mode lists
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/prebuilts/modules/init.insmod.cfg:vendor_dlkm/lib/modules/init.insmod.cfg \
    $(LOCAL_PATH)/prebuilts/modules/modules.load.cali:vendor_dlkm/lib/modules/modules.load.cali \
    $(LOCAL_PATH)/prebuilts/modules/modules.load.charger:vendor_dlkm/lib/modules/modules.load.charger

# Symlinks declared by hand: the module loader path, and the toybox [ builtin
PRODUCT_PACKAGES += \
    vendor_lib_modules \
    vendor_bin_lbracket

# Toybox, the platform builds the binary and its symlink farm
PRODUCT_PACKAGES += \
    toybox_vendor

# Vendor tools, the platform builds the same file at the same path
PRODUCT_PACKAGES += \
    awk_vendor \
    dumpsys_vendor \
    logwrapper_vendor \
    sh_vendor

# Partitions
PRODUCT_USE_DYNAMIC_PARTITIONS := true

# Rootdir, the fstab has to sit in the first stage ramdisk to mount super
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/rootdir/etc/fstab.serenity:$(TARGET_VENDOR_RAMDISK_OUT)/first_stage_ramdisk/fstab.serenity