#!/usr/bin/env python3
"""Offline, fail-closed Android boot v0 Recovery ramdisk repacker for LG-D690.

No device access. Requires the Linux lz4 CLI with legacy (-l) mode.
Builds the ramdisk by preserving original newc CPIO records, inserting the
recovery-specific rc and genuine built ADB daemon, and recompressing to LZ4.
"""
import argparse
import gzip
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile

PARTITION_SIZE = 16 * 1024 * 1024
LZ4_MAGIC = b'\x02\x21\x4c\x18'


def align4(n):
    return (n + 3) & ~3


def entries_of(cpio):
    at = 0
    entries = []
    while at + 110 <= len(cpio):
        if cpio[at:at+6] != b'070701':
            raise ValueError('Malformed newc record at offset %d' % at)
        fields = [int(cpio[at+6+i*8:at+14+i*8], 16) for i in range(13)]
        ino, mode, uid, gid, nlink, mtime, size, devmaj, devmin, rdevmaj, rdevmin, ns, chk = fields
        if not (1 <= ns <= 4096):
            raise ValueError('Bad filename length')
        nend = at + 110 + ns
        if nend > len(cpio) or cpio[nend-1] != 0:
            raise ValueError('Invalid cpio name')
        name = cpio[at+110:nend-1].decode('utf-8')
        payload_start = align4(nend)
        end = payload_start + size
        if end > len(cpio):
            raise ValueError('Truncated cpio member')
        record_end = align4(end)
        entries.append((name, ino, at, record_end))
        at = record_end
        if name == 'TRAILER!!!':
            return entries
    raise ValueError('Missing newc trailer')


def newc(name, payload, mode, ino):
    name_bytes = name.encode('utf-8') + b'\0'
    fields = [ino, mode, 0, 0, 1, 0, len(payload), 0, 0, 0, 0, len(name_bytes), 0]
    header = b'070701' + b''.join(('%08x' % v).encode() for v in fields)
    record = header + name_bytes
    record += b'\0' * (align4(len(record)) - len(record))
    record += payload
    record += b'\0' * (align4(len(record)) - len(record))
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--image', required=True)
    ap.add_argument('--adbd', required=True)
    ap.add_argument('--device-rc', required=True)
    ap.add_argument('--file-contexts', required=True)
    ap.add_argument('--ctr-fstab', required=True)
    ap.add_argument('--output', required=True)
    opt = ap.parse_args()
    image_path = Path(opt.image)
    output_path = Path(opt.output)
    if image_path.resolve() == output_path.resolve():
        raise SystemExit('Refusing in-place modification')
    img = image_path.read_bytes()
    if img[:8] != b'ANDROID!':
        raise SystemExit('Unexpected Android boot image magic')
    ks, ka, rs, ra = struct.unpack_from('<4I', img, 8)
    second = struct.unpack_from('<I', img, 24)[0]
    page = struct.unpack_from('<I', img, 36)[0]
    if page != 2048 or second != 0 or ka != 0x80008000 or ra != 0x84000000:
        raise SystemExit('Unexpected boot header/layout; refusing repack')
    ko = page
    ro = page + align4page(ks, page)
    if ro + rs > len(img):
        raise SystemExit('Truncated recovery image')
    kernel = img[ko:ko+ks]
    gzip_data = img[ro:ro+rs]
    if not gzip_data.startswith(b'\x1f\x8b'):
        raise SystemExit('Expected input gzip ramdisk, refusing to guess')
    cpio = gzip.decompress(gzip_data)
    entries = entries_of(cpio)
    names = {n for n, _, _, _ in entries}
    if 'sbin/recovery' not in names or 'init.rc' not in names:
        raise SystemExit('Not a recognizable TWRP CPIO')
    if any(n in names for n in ('sbin/adbd', 'init.recovery.b2lds.rc', 'file_contexts')):
        raise SystemExit('One or more target files already exist; refusing overwrite')
    adbd = Path(opt.adbd).read_bytes()
    if adbd[:5] != b'\x7fELF\x01' or struct.unpack_from('<H', adbd, 18)[0] != 40:
        raise SystemExit('ADBD must be a genuine ELF32 ARM executable')
    rc = Path(opt.device_rc).read_bytes()
    if b'start adbd' not in rc:
        raise SystemExit('Unexpected device-specific init.recovery.b2lds.rc')
    # A complete generated Android 5.1 file_contexts, NOT the tiny device-only
    # policy fragment. The generated file must correspond to this recovery's policy.
    fc = Path(opt.file_contexts).read_bytes()
    if b'\x00' in fc or len(fc) < 1024:
        raise SystemExit('Refusing missing, binary or partial file_contexts')
    context_lines = [line for line in fc.decode('utf-8').splitlines()
                     if line.strip() and not line.lstrip().startswith('#')]
    if len(context_lines) < 30 or not all(
        len(line.split()) >= 2 and 'u:object_r:' in line for line in context_lines
    ):
        raise SystemExit('Generated file_contexts is not a complete text policy')
    ctr = Path(opt.ctr_fstab).read_bytes()
    if b'\x00' in ctr or len(ctr) < 200:
        raise SystemExit('Invalid ctr.fstab')
    mount_map = {}
    for line in ctr.decode('utf-8').splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[0].startswith('/'):
            mount_map[fields[0]] = fields[2]
    for mount, blk in {'/system': '/dev/block/mmcblk0p9',
                       '/cache': '/dev/block/mmcblk0p10',
                       '/data': '/dev/block/mmcblk0p11'}.items():
        if mount_map.get(mount) != blk:
            raise SystemExit(f'Invalid ctr.fstab: {mount} points to {mount_map.get(mount)}')
    if 'etc/ctr.fstab' not in names:
        raise SystemExit('Built ramdisk has no etc/ctr.fstab to replace')
    maxino = max(ino for _, ino, _, _ in entries)
    trailer = next((start for n, _, start, _ in entries if n == 'TRAILER!!!'), None)
    assert trailer is not None
    # Replace the old ctr.fstab record instead of appending a duplicate name.
    # Keep all other CPIO records byte-for-byte identical.
    cpio_parts = []
    for name, ino, start, end in entries:
        if name == 'TRAILER!!!':
            break
        if name == 'etc/ctr.fstab':
            prev_mode = int(cpio[start+14:start+22], 16)
            if (prev_mode & 0o170000) != 0o100000:
                raise SystemExit('Unexpected type for etc/ctr.fstab')
            cpio_parts.append(newc(name, ctr, prev_mode, ino))
        else:
            cpio_parts.append(cpio[start:end])
    cpio_new = (b''.join(cpio_parts) +
                newc('sbin/adbd', adbd, 0o100755, maxino + 1) +
                newc('init.recovery.b2lds.rc', rc, 0o100644, maxino + 2) +
                newc('file_contexts', fc, 0o100644, maxino + 3) +
                cpio[trailer:])
    names_new = {n for n, _, _, _ in entries_of(cpio_new)}
    assert {'sbin/adbd', 'init.recovery.b2lds.rc', 'file_contexts', 'etc/ctr.fstab'}.issubset(names_new)
    if len(names_new) != len(entries) + 3:  # three additions and one in-place replacement
        raise SystemExit('Unexpected CPIO entry count')
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / 'ramdisk.cpio'
        comp = Path(td) / 'ramdisk.lz4'
        raw.write_bytes(cpio_new)
        subprocess.run(['lz4', '-l', '-9', str(raw), str(comp)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        packed = comp.read_bytes()
        if not packed.startswith(LZ4_MAGIC):
            raise SystemExit('LZ4 did not produce LEGACY header')
        unpacked = subprocess.run(['lz4', '-d', '-c', str(comp)], check=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
        if unpacked != cpio_new:
            raise SystemExit('LZ4 roundtrip verification failed')
    new_image = bytearray(img[:ro])
    new_image += packed
    new_image += b'\0' * (align4page(len(packed), page) - len(packed))
    if len(new_image) > PARTITION_SIZE:
        raise SystemExit('Image exceeds 16 MiB recovery partition')
    # Boot header v0: kernel + size, ramdisk + size, empty second + size.
    struct.pack_into('<I', new_image, 16, len(packed))
    digest = hashlib.sha1(kernel + struct.pack('<I', ks) +
                          packed + struct.pack('<I', len(packed)) +
                          struct.pack('<I', 0)).digest()
    new_image[576:608] = digest.ljust(32, b'\0')
    if new_image[ko:ko+ks] != kernel:
        raise SystemExit('Kernel altered unexpectedly')
    new_image += b'\0' * (PARTITION_SIZE - len(new_image))
    output_path.write_bytes(new_image)
    print('LZ4 Legacy magic: PASS')
    print('LZ4 roundtrip: PASS')
    print('Added: sbin/adbd, init.recovery.b2lds.rc, file_contexts')
    print('Replaced: etc/ctr.fstab with verified LG partition map')
    print('Original kernel unchanged:', len(kernel), 'bytes')
    print('Final image:', len(new_image), 'bytes')
    print('SHA256:', hashlib.sha256(new_image).hexdigest())


def align4page(size, page):
    return (size + page - 1) // page * page


if __name__ == '__main__':
    main()
