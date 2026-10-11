# Inherit from b2lds device
$(call inherit-product, device/lge/b2lds/device_b2lds.mk)

# Inherit some common Omni stuff.
$(call inherit-product, vendor/omni/config/common.mk)

PRODUCT_DEVICE := b2lds
PRODUCT_NAME := omni_b2lds
PRODUCT_BRAND := lge
PRODUCT_MODEL := LG-D690
PRODUCT_MANUFACTURER := lge

PRODUCT_BUILD_PROP_OVERRIDES += \
    PRIVATE_BUILD_DESC="b2lds_global_com-user 5.0.2 LRX22G 190571719b265 release-keys"

BUILD_FINGERPRINT := lge/b2lds_global_com/b2lds:5.0.2/LRX22G/190571719b265:user/release-keys
