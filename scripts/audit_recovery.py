#!/usr/bin/env python3
"""Read-only QA for LG-D690 recovery.img. Never writes to a device.

Run: python3 scripts/audit_recovery.py --image recovery.img --kernel prebuilt/kernel
The audit is deliberately conservative: it rejects unknown compression/extra MTK
wrappers rather than assuming they work on the LG-D690 stock boot chain.
"""
import argparse
import gzip
import hashlib
import posixpath
import shutil
import struct
import subprocess
import sys

MTK_MAGIC = struct.pack('<I', 0x58881688)
LZ4_LEGACY = b'\x02\x21\x4c\x18'


def parse_cpio(raw, err, warn):
    entries = {}
    at = 0
    while at + 110 <= len(raw):
        if raw[at:at + 6] not in (b'070701', b'070702'):
            err('Invalid CPIO header at offset %d' % at)
            return
        try:
            mode = int(raw[at + 14:at + 22], 16)
            data_len = int(raw[at + 54:at + 62], 16)
            name_len = int(raw[at + 94:at + 102], 16)
        except ValueError:
            err('Invalid CPIO numeric field at %d' % at)
            return
        if not (1 <= name_len <= 4096):
            err('Invalid CPIO name length at %d' % at)
            return
        ns = at + 110
        ne = ns + name_len
        if ne > len(raw) or raw[ne - 1] != 0:
            err('Invalid CPIO filename at %d' % at)
            return
        name = raw[ns:ne - 1].decode('utf-8', 'replace').lstrip('/')
        start = (ne + 3) & ~3
        end = start + data_len
        if end > len(raw):
            err('Truncated CPIO data for %s' % name)
            return
        if name == 'TRAILER!!!':
            break
        entries[name] = (mode, raw[start:end])
        at = (end + 3) & ~3
    else:
        err('CPIO TRAILER!!! was not found')
        return

    links = 0
    suspicious = []
    missing = []
    for name, (mode, payload) in entries.items():
        kind = mode & 0o170000
        if kind == 0o120000:
            links += 1
            dst = payload.decode('utf-8', 'replace')
            location = (dst.lstrip('/') if dst.startswith('/')
                        else posixpath.join(posixpath.dirname(name), dst))
            resolved = posixpath.normpath(location)
            if resolved not in entries:
                missing.append((name, dst))
        elif kind == 0o100000 and name.startswith('sbin/') and payload in (
            b'busybox', b'toolbox', b'pigz', b'../init', b'/sbin/busybox'
        ):
            suspicious.append((name, payload.decode()))
    print('CPIO: %d entries, %d symlinks, %d stub files' % (
        len(entries), links, len(suspicious)))
    for name, dst in suspicious[:10]:
        err('Text file likely meant to be symlink: %s -> %s' % (name, dst))
    if len(suspicious) > 10:
        err('%d additional suspected fake symlinks' % (len(suspicious) - 10))
    for name, dst in missing[:10]:
        warn('Broken link: %s -> %s' % (name, dst))

    for path in ('init', 'init.rc', 'sbin/recovery', 'sbin/linker', 'sbin/ueventd'):
        if path not in entries:
            err('Mandatory ramdisk entry missing: ' + path)
    if 'init' in entries and entries['init'][1][:5] != b'\x7fELF\x01':
        err('init is not ELF32')
    rc = entries.get('init.rc', (0, b''))[1].decode('utf-8', 'replace')
    if 'service adbd /sbin/adbd' in rc and 'sbin/adbd' not in entries:
        err('init.rc uses /sbin/adbd but executable is missing')
    for line in rc.splitlines():
        if line.strip().startswith('import '):
            imp = line.strip().split(None, 1)[1].lstrip('/')
            imp = imp.replace('${ro.hardware}', 'b2lds')
            if '${' not in imp and imp not in entries:
                warn('Optional init.rc import missing: ' + imp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--kernel', required=True)
    args = parser.parse_args()
    problems = []
    def err(message):
        problems.append(message)
        print('ERROR:', message)
    def warn(message):
        print('WARN: ', message)
    img = open(args.image, 'rb').read()
    stock_kernel = open(args.kernel, 'rb').read()
    if len(img) > 16777216:
        err('Recovery image exceeds 16 MiB')
    if len(img) < 2048 or img[:8] != b'ANDROID!':
        err('Invalid Android boot image')
        return 1
    ksz, kaddr = struct.unpack_from('<II', img, 8)
    rsz, raddr = struct.unpack_from('<II', img, 16)
    second_size = struct.unpack_from('<I', img, 24)[0]
    page = struct.unpack_from('<I', img, 36)[0]
    cmdline = img[64:576].split(b'\0', 1)[0].decode('utf-8', 'replace')
    print('Image bytes:', len(img), 'kernel:', ksz, 'ramdisk:', rsz, 'page:', page)
    print('Kernel load: 0x%08x; ramdisk load: 0x%08x' % (kaddr, raddr))
    print('Cmdline:', cmdline)
    if page != 2048:
        err('Unexpected page size')
        return 1
    if kaddr != 0x80008000 or raddr != 0x84000000:
        err('Unexpected RAM load addresses')
    if second_size != 0:
        err('Unexpected nonempty second stage')
    if 'androidboot.hardware=b2lds' not in cmdline:
        err('androidboot.hardware=b2lds missing')
    ko = page
    ro = page + ((ksz + page - 1) // page) * page
    if ro + rsz > len(img):
        err('Kernel/ramdisk length exceeds image')
        return 1
    kernel = img[ko:ko + ksz]
    ramdisk = img[ro:ro + rsz]
    if kernel != stock_kernel:
        err('Kernel is NOT byte-identical to verified stock prebuilt/kernel')
        if kernel.startswith(MTK_MAGIC):
            err('Detected unwanted MTK 512-byte kernel wrapper')
    else:
        print('Stock kernel: MATCH')
    if ramdisk.startswith(MTK_MAGIC):
        err('Unexpected MTK wrapper around ramdisk')
        ramdisk = ramdisk[512:]
    digest = hashlib.sha1(kernel + struct.pack('<I', ksz) + ramdisk +
                          struct.pack('<I', rsz) + struct.pack('<I', second_size)).digest()
    # Hash is evaluated only for unwrapped images with no device-tree segment.
    if not img[ro:ro + rsz].startswith(MTK_MAGIC) and second_size == 0:
        if digest != img[576:596]:
            warn('Android v0 SHA1 header differs from expected value')
        else:
            print('Header SHA1: MATCH')
    if ramdisk.startswith(LZ4_LEGACY):
        print('Ramdisk: LZ4 Legacy')
        if shutil.which('lz4') is None:
            err('lz4 executable not found; cannot audit decompressed CPIO')
        else:
            done = subprocess.run(['lz4', '-d', '-c'], input=ramdisk,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if done.returncode:
                err('LZ4 decompression failed: ' + done.stderr.decode(errors='replace')[:200])
            else:
                parse_cpio(done.stdout, err, warn)
    elif ramdisk.startswith(b'\x1f\x8b'):
        err('Ramdisk is gzip, but LG stock recovery uses LZ4 Legacy')
        try:
            parse_cpio(gzip.decompress(ramdisk), err, warn)
        except Exception as ex:
            warn('Could not read gzip CPIO: ' + str(ex))
    else:
        err('Unknown ramdisk compression')
    print('OVERALL:', 'FAIL' if problems else 'PASS')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
