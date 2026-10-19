#
# SPDX-FileCopyrightText: The Redmi A5 (serenity) Project
# SPDX-License-Identifier: Apache-2.0
#
# The one value that differs between the platform branches. The vendor is a
# VNDK 33 snapshot on all of them, which is normal: VNDK is frozen, a vendor
# stays where it is and the platform moves on. What the tree declares is the
# vendor snapshot, so the shipping API follows the platform, not the vendor.
#
#   lineage-22.0  Android 15
#   lineage-23.2  Android 16
#   lineage-24.0  Android 17
#
PRODUCT_SHIPPING_API_LEVEL := 36
