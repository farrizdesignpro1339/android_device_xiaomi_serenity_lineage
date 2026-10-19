PRODUCT_MAKEFILES := \
    $(LOCAL_DIR)/lineage_serenity.mk

# Android 15 is AP3A and the lunch target carries the platform suffix on this
# branch, the product makefile keeps the plain name. The plain choices are
# listed too, so both spellings work.
COMMON_LUNCH_CHOICES := \
    lineage_serenity-ap3a-user \
    lineage_serenity-ap3a-userdebug \
    lineage_serenity-ap3a-eng \
    lineage_serenity-user \
    lineage_serenity-userdebug \
    lineage_serenity-eng
