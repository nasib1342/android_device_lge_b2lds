# Release name
PRODUCT_RELEASE_NAME := b2lds

# Inherit from the common Open Source product configuration
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit some common CM stuff.
$(call inherit-product, vendor/cm/config/common_full_phone.mk)

# Inherit device configuration
$(call inherit-product, device/lge/b2lds/device_b2lds.mk)

# Boot animation
TARGET_SCREEN_HEIGHT := 960
TARGET_SCREEN_WIDTH := 540

## Device identifier. This must come after all inclusions
PRODUCT_DEVICE := b2lds
PRODUCT_NAME := cm_b2lds
PRODUCT_BRAND := lge
PRODUCT_MODEL := LG-D690
PRODUCT_MANUFACTURER := lge

PRODUCT_GMS_CLIENTID_BASE := android-mediatek

