## Specify phone tech before including full_phone
$(call inherit-product, vendor/slim/config/gsm.mk)

# Release name
PRODUCT_RELEASE_NAME := b2lds

# Inherit from the common Open Source product configuration
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit some common SLIM stuff.
$(call inherit-product, vendor/slim/config/common_full_phone.mk)

# Inherit device configuration
$(call inherit-product, device/lge/b2lds/device_b2lds.mk)

# Boot animation
TARGET_SCREEN_HEIGHT := 960
TARGET_SCREEN_WIDTH := 540

## Device identifier. This must come after all inclusions
BOARD_VENDOR := lge
PRODUCT_DEVICE := b2lds
PRODUCT_NAME := slim_b2lds
PRODUCT_BRAND := lge
PRODUCT_MODEL := b2lds
PRODUCT_MANUFACTURER := lge
TARGET_VENDOR := lge
PRODUCT_RELEASE_NAME := b2lds

PRODUCT_GMS_CLIENTID_BASE := android-mediatek

#verify fingerprint ID
PRODUCT_BUILD_PROP_OVERRIDES += BUILD_UTC_DATE=0
