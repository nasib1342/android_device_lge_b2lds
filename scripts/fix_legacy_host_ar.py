#!/usr/bin/env python3
"""Fix Android 5.1 host whole-static archive extraction for pathful `ar t` members.

Only updates the known legacy host macro, with strict assertions. This script
runs in GitHub Actions on the freshly-synced AOSP build checkout.
"""
from pathlib import Path
import sys


def fix(source: str) -> str:
    begin_marker = "define _extract-and-include-single-host-whole-static-lib"
    if source.count(begin_marker) != 1:
        raise ValueError("Expected exactly one host whole-static extraction macro")
    start = source.index(begin_marker)
    end = source.find("\nendef", start)
    if end == -1:
        raise ValueError("Cannot find end of host whole-static extraction macro")
    before = source[:start]
    block = source[start:end]
    after = source[end:]

    # Replace only the 5.1 host extraction recipe. No target/ARM archiver changes.
    old_filelist = 'filelist="$$filelist $$ldir/$$f";'
    if block.count(old_filelist) != 1:
        raise ValueError("Unrecognized host archive filelist layout")
    lines = block.splitlines(keepends=True)
    result = []
    changed_ar = 0
    changed_list = 0
    for line in lines:
        if ' > $$ldir/$$f;' in line and ' p ' in line:
            indent = line[:len(line) - len(line.lstrip())]
            # In GNU ar, `pP` reads pathful archive members by their full name.
            # The extracted output uses the basename, NOT the absolute path.
            result.append(indent + 'obj=$${f##*/}; \\\n')
            line = line.replace(' p ', ' pP ', 1).replace(' > $$ldir/$$f;', ' > $$ldir/$$obj;')
            changed_ar += 1
        elif old_filelist in line:
            line = line.replace(old_filelist, 'filelist="$$filelist $$ldir/$$obj";')
            changed_list += 1
        result.append(line)
    if changed_ar != 1 or changed_list != 1:
        raise ValueError(f"Expected one host recipe match, got extraction={changed_ar} list={changed_list}")
    patched = before + ''.join(result) + after
    if 'pP ' not in patched[start:end+64]:
        raise ValueError('Host archive patch verification failed')
    return patched


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('Usage: fix_legacy_host_ar.py path/to/build/core/definitions.mk')
    p = Path(sys.argv[1])
    if not p.is_file():
        raise SystemExit(f'ERROR: AOSP definitions.mk missing: {p}')
    old = p.read_text(encoding='utf-8')
    try:
        new = fix(old)
    except ValueError as e:
        raise SystemExit(f'ERROR: refusing unknown build system layout: {e}')
    p.write_text(new, encoding='utf-8')
    print('PATCHED Android 5.1 host whole-static archive extraction: GNU ar pP + basename')


if __name__ == '__main__':
    main()
