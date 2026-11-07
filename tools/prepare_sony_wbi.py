#!/usr/bin/env python3
"""Offline: select and verify the known Sony utility from an extracted updater.
See docs/wbi.md for obtaining and unpacking the owner's official Sony package.
Never connects to a camera; never executes an updater or extracted program.
"""
import argparse
from pathlib import Path
import wbi


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-tree', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    candidates = []
    for path in args.from_tree.rglob('ud_wbi_drop.elf'):
        if path.is_symlink() or not path.is_file():
            continue
        data = path.read_bytes()
        try:
            wbi.validate_tool(data)
        except ValueError:
            continue
        candidates.append(data)
    if not candidates:
        parser.error('No matching 6200-byte Sony ELF found; stop, do not use another binary')
    args.out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with args.out.open('xb') as stream:
        args.out.chmod(0o600)
        stream.write(candidates[0])
    print('Verified Sony tool:', args.out)
    print('SHA-256:', wbi.TOOL_HASH)
    print('Source package version 2.03 is NOT the supported camera system version: only 2.02.')


if __name__ == '__main__':
    main()
