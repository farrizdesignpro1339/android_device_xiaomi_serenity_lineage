#
# SPDX-FileCopyrightText: The Redmi A5 (serenity) Project
# SPDX-License-Identifier: Apache-2.0
#

# Inherit from the device configuration
$(call inherit-product, $(LOCAL_PATH)/device.mk)

# The stock system is Android 15 and the vendor is a VNDK 33 snapshot, so the
# platform runs a newer Android than the vendor does, which is the normal
# shape of a port: VNDK is frozen and a vendor never moves
PRODUCT_SHIPPING_API_LEVEL := 36

## Device identifier, this must come after all inclusions
PRODUCT_BRAND := Redmi
PRODUCT_DEVICE := serenity
PRODUCT_MANUFACTURER := Xiaomi
PRODUCT_MODEL := 25028RN03Y
PRODUCT_NAME := lineage_serenity

PRODUCT_SYSTEM_DEFAULT_LANGUAGE := id-ID
PRODUCT_SYSTEM_DEFAULT_COUNTRY := ID

PRODUCT_GMS_CLIENTID_BASE := android-xiaomi-serenity

PRODUCT_BUILD_PROP_OVERRIDES += \
    PRIVATE_BUILD_DESC="mivendor_ums9230-user 15 AP3A.240905.015.A2 A15.0.32.0.VGWMIXM release-keys" \
    BuildFingerprint=Redmi/mivendor_ums9230/mivendor_ums9230:15/AP3A.240905.015.A2/A15.0.32.0.VGWMIXM:user/release-keys