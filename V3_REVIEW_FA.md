# LG-D690 / b2lds — اصلاحیهٔ آزمایشی TWRP v3

این بسته **فقط وصلهٔ سورس GitHub** است، نه فایل ریکاوری قابل فلش.
برای شاخهٔ `twrp-fix-v3` طراحی شده و شامل فقط سه فایل اصلی تغییر (`.github/workflows/build.yml`، `scripts/repack_recovery_v3.py`، `scripts/audit_recovery.py`) و همین راهنماست.

## اصلاح مشکلات بیلد قبلی

1. بعد از `make recoveryimage`، با `make -j4 adbd` فایل اجرایی واقعی Android 5.1 ساخته می‌شود. محل خروجی در `recovery/root/sbin/adbd` یا `system/bin/adbd` یا `root/sbin/adbd` بررسی و ELF32 ARM بودن آن کنترل می‌شود. اگر پیدا نشد، Build خطا می‌دهد.
2. اسکریپت Repack فایل `init.recovery.b2lds.rc` موجود در مخزن و `adbd` ساخته‌شده را داخل CPIO قرار می‌دهد. سپس با `lz4 -l -9` رم‌دیسک را در قالب **LZ4 Legacy** بازفشرده می‌کند و round-trip آن را بررسی می‌کند.
3. هدر و SHA1 بازسازی می‌شود، کرنل اصلی حفظ می‌گردد و اگر حجم بیشتر از پارتیشن 16MiB شد، عملیات متوقف می‌شود.
4. ممیزی خودکار صحت کرنل، SHA1، فشرده‌سازی، Symlinkها، وجود `adbd` و `init.recovery.b2lds.rc` را بررسی می‌کند. اگر FAIL شود، Artifact به‌عنوان خروجی سالم منتشر نمی‌شود.

## محدودهٔ تأیید

- ساختار YAML و نحو Python بررسی شد.
- **آزمون ساختاری آفلاین** روی ایمیج GZIP شمارهٔ ۷ با یک ELF32 آزمایشی به‌جای adbd واقعی و یک شبیه‌ساز موقت CLI `lz4` انجام شد؛ خروجی تست `OVERALL: PASS` داده است.
- این آزمون **ساخت واقعی adbd، اجرای lz4 سیستم GitHub، سازگاری SELinux و بوت‌شدن گوشی را اثبات نمی‌کند**.
- هش یا ایمیج آزمون با ELF آزمایشی، برای فلش مناسب نیست و داخل این ZIP قرار ندارد.
- هنوز ۴ import اختیاری از `init.rc` غایب‌اند. همچنین رفتار `ueventd.rc` و `file_contexts` و پارتیشن‌های fstab قبل از آزمایش واقعی باید بررسی شوند.

## نصب

فایل ZIP را در `C:\lglaf-master` قرار دهید و **روی شاخهٔ `twrp-fix-v3`** با `Expand-Archive -Force` در `C:\lglaf-master\b2lds_source_review` استخراج کنید. ابتدا `git status --short --branch` و `git diff --check` را ببینید. بدون بازبینی، چیزی به گوشی فلش نکنید.
