#
# SPDX-FileCopyrightText: The Serenity Project
# SPDX-License-Identifier: Apache-2.0
#

# Inherit from the device configuration
$(call inherit-product, $(LOCAL_PATH)/device.mk)

# The stock system is Android 17, the vendor is API 33
PRODUCT_SHIPPING_API_LEVEL := 36

## Device identifier, this must come after all inclusions
PRODUCT_BRAND := xiaomi
PRODUCT_DEVICE := serenity
PRODUCT_MANUFACTURER := xiaomi
PRODUCT_MODEL := Redmi A5
PRODUCT_NAME := lineage_serenity

PRODUCT_SYSTEM_DEFAULT_LANGUAGE := en-US
PRODUCT_SYSTEM_DEFAULT_COUNTRY := US

PRODUCT_GMS_CLIENTID_BASE := android-xiaomi-serenity

PRODUCT_BUILD_PROP_OVERRIDES += \
    PRIVATE_BUILD_DESC="serenity-user 17 ... release-keys" \
    BuildFingerprint=xiaomi/serenity/serenity:17/.../...:user/release-keys
