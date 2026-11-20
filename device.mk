#
# SPDX-FileCopyrightText: The Serenity Project
# SPDX-License-Identifier: Apache-2.0
#

# Inherit some common Lineage stuff
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)

# Inherit from the Serenity vendor blobs
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
PRODUCT_PACKAGES += \
    android.hardware.boot@1.2-impl \
    android.hardware.boot@1.2-impl.recovery \
    android.hardware.boot@1.2-service

# Power stats, the platform builds the service the blob list used to ship
PRODUCT_PACKAGES += \
    android.hardware.power.stats-service.example

# DRM, health and sensors, the platform builds what the blob list used to ship
PRODUCT_PACKAGES += \
    android.hardware.drm-service.clearkey \
    android.hardware.health-service.example \
    android.hardware.sensors-service.multihal \
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

# Kernel modules, the loader config and the boot mode lists
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/prebuilts/modules/init.insmod.cfg:vendor_dlkm/lib/modules/init.insmod.cfg \
    $(LOCAL_PATH)/prebuilts/modules/modules.load.cali:vendor_dlkm/lib/modules/modules.load.cali \
    $(LOCAL_PATH)/prebuilts/modules/modules.load.charger:vendor_dlkm/lib/modules/modules.load.charger

# Symlinks declared by hand: the module loader path
PRODUCT_PACKAGES += \
    vendor_lib_modules

# Toybox, the platform builds the binary and its symlink farm
PRODUCT_PACKAGES += \
    toybox_vendor

# Vendor tools, the platform builds the same file at the same path
PRODUCT_PACKAGES += \
    awk_vendor \
    dumpsys_vendor \
    logwrapper_vendor \
    sh_vendor

# RRO overlays (prebuilt APK di prebuilts/overlay/)
PRODUCT_PACKAGES += \
    BluetoothLegacyOverlay \
    BluetoothOverlay \
    DataOnlyOverlay \
    DataOnlySingleSimOverlay \
    DualSimOverlay \
    MultiuserOverlays \
    NetworkStackOverlayGo \
    NetworkStackOverlayGsi \
    SettingsProviderOverlay \
    SystemUIOverlay \
    TetheringConfigOverlay \
    TetheringConfigOverlayGo \
    TetheringConfigOverlayGsi \
    UnisocConnectivityOverlayGo \
    UnisocConnectivityOverlayGsi \
    unisoc_overlay_colordisplay \
    unisoc_overlay_core \
    unisoc_overlay_core_go \
    unisoc_overlay_core_max_cached_processed_16 \
    unisoc_overlay_core_navbar \
    unisoc_overlay_core_pinner_service \
    unisoc_overlay_core_pinner_service_qogirl6 \
    unisoc_overlay_core_wifi_display \
    unisoc_overlay_display_doze \
    unisoc_overlay_display_thermal_refreshratepolicy \
    unisoc_overlay_display_vrr \
    unisoc_overlay_phone \
    unisoc_overlay_phone_core \
    unisoc_overlay_phone_hac \
    unisoc_overlay_power_cpuT606 \
    unisoc_overlay_power_cpuT616 \
    unisoc_overlay_power_qogirl6 \
    unisoc_overlay_uwb_bt_l6 \
    unisoc_overlay_uwb_bt_m2 \
    unisoc_overlay_uwb_bt_m3 \
    unisoc_overlay_uwb_bt_m3le \
    unisoc_overlay_uwb_bt_m3lite \
    unisoc_overlay_uwb_bt_m3lite_Integ \
    unisoc_overlay_uwb_bt_m3lite_Inter \
    unisoc_res_overlay_colordisplay \
    unisoc_res_overlay_power_qogirl6 \
    unisoc_res_overlay_workduration \
    WifiAXDLOverlay \
    WifiAXDLOverlayGoogle \
    WifiAXEOverlay \
    WifiAXEOverlayGoogle \
    WifiDisplayUnavailableOverlay \
    WifiOnlyOverlay \
    WifiOnlySettingsOverlay \
    WifiOverlay \
    WifiOverlayGoogle

# RRO overlays (source-based, compile dari XML)
PRODUCT_PACKAGES += \
    FrameworkResOverlay \
    SystemUIOverlay

# Partitions
PRODUCT_USE_DYNAMIC_PARTITIONS := true

# Rootdir, the fstab has to sit in the first stage ramdisk to mount super
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/rootdir/etc/fstab.serenity:$(TARGET_VENDOR_RAMDISK_OUT)/first_stage_ramdisk/fstab.serenity
