LOCAL_PATH := device/lge/b2lds

# Proprietary configuration (optional when vendor files are absent)
-include vendor/lge/b2lds/BoardConfigVendor.mk
-include vendor/lge/b2lds/b2lds-vendor.mk

# Device headers
TARGET_SPECIFIC_HEADER_PATH := device/lge/b2lds/include

# Platform
TARGET_BOARD_PLATFORM := mt6582
TARGET_NO_BOOTLOADER := true

# Architecture
TARGET_ARCH := arm
TARGET_CPU_ABI := armeabi-v7a
TARGET_CPU_ABI2 := armeabi
TARGET_ARCH_VARIANT := armv7-a-neon
TARGET_CPU_VARIANT := cortex-a7
TARGET_CPU_SMP := true

# Bootloader
TARGET_BOOTLOADER_BOARD_NAME := mt6582

# Partition sizes (verified against /proc/dumchar_info)
BOARD_BOOTIMAGE_PARTITION_SIZE := 16777216
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 16777216
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 2147483648
BOARD_USERDATAIMAGE_PARTITION_SIZE := 4613734400
BOARD_CACHEIMAGE_PARTITION_SIZE := 838860800
BOARD_CACHEIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_FLASH_BLOCK_SIZE := 131072

# Prebuilt kernel and recovery fstab
TARGET_PREBUILT_KERNEL := $(LOCAL_PATH)/prebuilt/kernel
TARGET_RECOVERY_FSTAB := $(LOCAL_PATH)/recovery/recovery.fstab

# Legacy MediaTek boot image format
BOARD_MKBOOTIMG_ARGS := --base 0x80000000 --pagesize 2048 --kernel_offset 0x00008000 --ramdisk_offset 0x04000000 --tags_offset 0x00000100 --mtk 1
BOARD_KERNEL_BASE := 0x80000000
BOARD_KERNEL_PAGESIZE := 2048
BOARD_CUSTOM_BOOTIMG := true
BOARD_CUSTOM_MKBOOTIMG := mtkbootimg
BOARD_CUSTOM_BOOTIMG_MK := $(LOCAL_PATH)/bootimg.mk
TARGET_KMODULES := true

# Device identity
TARGET_OTA_ASSERT_DEVICE := b2lds
COMMON_GLOBAL_CFLAGS += -DDISABLE_HW_ID_MATCH_CHECK
TARGET_RUNNING_WITHOUT_SYNC_FRAMEWORK := true

# Disable memcpy optimization for legacy audio libraries
TARGET_CPU_MEMCPY_OPT_DISABLE := true

# EGL
BOARD_EGL_CFG := device/lge/b2lds/configs/egl.cfg
USE_OPENGL_RENDERER := true
BOARD_EGL_WORKAROUND_BUG_10194508 := true

# MediaTek hardware
BOARD_HAS_MTK_HARDWARE := true
MTK_HARDWARE := true
COMMON_GLOBAL_CFLAGS += -DMTK_HARDWARE -DADD_LEGACY_ACQUIRE_BUFFER_SYMBOL
COMMON_GLOBAL_CPPFLAGS += -DMTK_HARDWARE
ADDITIONAL_DEFAULT_PROPERTIES += ro.mount.fs=EXT4

# RIL and connectivity
BOARD_RIL_CLASS := ../../../device/lge/b2lds/ril/
BOARD_CONNECTIVITY_VENDOR := MediaTek
BOARD_CONNECTIVITY_MODULE := conn_soc

# Wi-Fi
WPA_SUPPLICANT_VERSION := VER_0_8_X
BOARD_HOSTAPD_DRIVER := NL80211
BOARD_HOSTAPD_PRIVATE_LIB := lib_driver_cmd_mt66xx
BOARD_WPA_SUPPLICANT_DRIVER := NL80211
BOARD_WPA_SUPPLICANT_PRIVATE_LIB := lib_driver_cmd_mt66xx
WIFI_DRIVER_FW_PATH_PARAM := "/dev/wmtWifi"
WIFI_DRIVER_FW_PATH_STA := STA
WIFI_DRIVER_FW_PATH_AP := AP
WIFI_DRIVER_FW_PATH_P2P := P2P

# Bluetooth
BOARD_HAVE_BLUETOOTH := true
BOARD_HAVE_BLUETOOTH_MTK := true
BOARD_BLUETOOTH_DOES_NOT_USE_RFKILL := true
BOARD_BLUETOOTH_BDROID_BUILDCFG_INCLUDE_DIR := device/lge/b2lds/bluetooth

# TWRP storage: Android uses emulated storage under /data/media, not /emmc.
RECOVERY_GRAPHICS_USE_LINELENGTH := true
TW_INTERNAL_STORAGE_PATH := "/data/media"
TW_INTERNAL_STORAGE_MOUNT_POINT := "data"
TW_EXTERNAL_STORAGE_PATH := "/external_sd"
TW_EXTERNAL_STORAGE_MOUNT_POINT := "external_sd"
TW_DEFAULT_EXTERNAL_STORAGE := false
RECOVERY_SDCARD_ON_DATA := true

# Legacy Android 5.x ext4 encryption configuration.
# Actual userdata partition from /proc/dumchar_info is mmcblk0p11.
TW_INCLUDE_JB_CRYPTO := true
TW_CRYPTO_FS_TYPE := "ext4"
TW_CRYPTO_REAL_BLKDEV := "/dev/block/mmcblk0p11"
TW_CRYPTO_MNT_POINT := "/data"
TW_CRYPTO_FS_OPTIONS := "nosuid,nodev,noatime,discard,noauto_da_alloc,data=ordered"
BOARD_HAS_LARGE_FILESYSTEM := true

# Display
DEVICE_SCREEN_WIDTH := 540
DEVICE_SCREEN_HEIGHT := 960
TARGET_SCREEN_WIDTH := 540
TARGET_SCREEN_HEIGHT := 960
TW_BRIGHTNESS_PATH := /sys/class/leds/lcd-backlight/brightness
TW_MAX_BRIGHTNESS := 255
DEVICE_RESOLUTION := 540x960
PORTRAIT_MDPI := 540x960
TW_THEME := portrait_mdpi
BOARD_HAS_MTK_CPU := true
BOARD_NEEDS_MTK_GETSIZE := true
BOARD_HAS_NO_SELECT_BUTTON := true
TW_CUSTOM_CPU_TEMP_PATH := /sys/devices/virtual/thermal/thermal_zone1/temp
TARGET_USE_CUSTOM_LUN_FILE_PATH := "/sys/devices/virtual/android_usb/android0/f_mass_storage/lun%d/file"

# SELinux policy
BOARD_SEPOLICY_DIRS += device/lge/b2lds/sepolicy
BOARD_SEPOLICY_UNION := device.te app.te system.te netd.te file_contexts
TARGET_SYSTEM_PROP := $(LOCAL_PATH)/system.prop

# Filesystem settings
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_SPARSE_EXT_DISABLED := false
USE_MINIKIN := true

# Legacy build workaround. The workflow adjusts OUT to OUT_DIR when needed.
$(shell mkdir -p $(OUT)/obj/KERNEL_OBJ/usr)
