#!/usr/bin/env python3
"""Offline checks only. Optional private Sony files are never copied into this repo."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import struct
import tempfile
from unittest.mock import patch
import wifi as s


def loads(path):
    data = path.read_bytes()
    assert data[:7] == b'\x7fELF\x01\x01\x01'
    assert struct.unpack_from('<H', data, 18)[0] == 40  # ARM
    start = struct.unpack_from('<I', data, 28)[0]
    step, count = struct.unpack_from('<HH', data, 42)
    result = []
    for i in range(count):
        kind, off, va, pa, size, mem, flags, align = struct.unpack_from('<8I', data, start+i*step)
        if kind == 1:
            result.append((va, mem, flags, data[off:off+size]))
    assert len(result) == 2
    assert struct.unpack_from('<I', data, 24)[0] == 0x10000
    return result


class FakeCamera:
    def __init__(self, mismatch=False):
        self.value = b'\x09'
        self.saved = []
        self.writes = []
        self.mismatch = mismatch

    def readBackup(self, key):
        return b'\x08' if self.mismatch and self.writes else self.value

    def writeBackup(self, key, value):
        self.writes.append((key, value))
        self.value = value

    def saveBackup(self, subsystem):
        self.saved.append(subsystem)


def fails(fn, cls=ValueError):
    try:
        fn()
    except cls:
        return
    raise AssertionError('Expected rejection')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--factory', type=Path)
    parser.add_argument('--patched', type=Path)
    parser.add_argument('--tested-helper', type=Path)
    args = parser.parse_args()
    checks = []
    for p in (s.ROOT / 'tools').glob('*.py'):
        ast.parse(p.read_text())
    checks.append('Python AST parse')
    a, b = loads(s.ROOT/'tools/patch.arm'), loads(s.ROOT/'tools/restore.arm')
    assert a[0] == b[0], 'Executable code/addresses must match'
    assert a[1][:3] == b[1][:3]
    diffs = [i for i,(x,y) in enumerate(zip(a[1][3], b[1][3])) if x != y]
    assert len(a[1][3]) == len(b[1][3]) and len(diffs) == 2
    assert all({a[1][3][i], b[1][3][i]} == {0x20, 0x1b} for i in diffs)
    checks.append('ARM ELF load segments: inverse helper differs only in two data bytes')
    if args.tested_helper:
        assert loads(args.tested_helper) == a
        assert hashlib.md5((s.ROOT/'tools/patch.arm').read_bytes()).hexdigest() == '8a1bd57091f544a758300b7151d94f05'
        checks.append('Packaged patch ELF identical to demonstrated camera-tested binary')
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        req = {'action':'backup-write', 'id':'0x00A5000B', 'expected':'09', 'value':'02'}
        camera = FakeCamera()
        fails(lambda:s.dispatch(camera, req, folder, False))
        assert not camera.writes
        fails(lambda:s.dispatch(camera, {**req,'expected':'08'},folder,True))
        assert not camera.writes
        fails(lambda:s.dispatch(camera, {**req,'id':'0x00A5000A'},folder,True))
        fails(lambda:s.dispatch(camera, {**req,'value':'ff'},folder,True))
        answer = s.dispatch(camera, req, folder, True)
        assert answer['match'] and camera.saved == [0xA5]
        assert any(json.loads(p.read_text())['original'] == '09' for p in folder.glob('*.json'))
        bad = FakeCamera(mismatch=True)
        fails(lambda:s.dispatch(bad, req, folder, True), RuntimeError)
        checks.append('Backup guards, original preservation, subsystem save, readback failure')
        with patch.object(s,'read_file',return_value=b'truncated'), patch.object(s,'run') as run:
            fails(lambda:s.dispatch(camera,{'action':'patch'},folder,True))
            run.assert_not_called()
        checks.append('Truncated/unknown library refuses all shell writes')
        if args.factory and args.patched:
            factory, patched = args.factory.read_bytes(), args.patched.read_bytes()
            s.verify(factory,s.FACTORY); s.verify(patched,s.PATCHED)
            assert [i for i,(x,y) in enumerate(zip(factory,patched)) if x!=y] == [s.OFFSET]
            assert factory[s.OFFSET] == 0x20 and patched[s.OFFSET] == 0x1b
            checks.append('Private factory/patched full hashes, size and unique byte difference')
            for action, before, after in (('patch',factory,patched),('restore',patched,factory)):
                helper = (s.ROOT/'tools'/f'{action}.arm').read_bytes()
                with patch.object(s,'read_file',side_effect=[before,helper,after]), patch.object(s,'run',return_value='/dev/nflasha15 /usr ext2 ro,relatime 0 0') as run:
                    result = s.dispatch(camera,{'action':action},folder,True)
                    assert result['size'] == s.SIZE
                    commands = [c.args[1] for c in run.call_args_list]
                    assert 'mount -o remount,rw /usr' in commands
                    assert commands[-2:] == ['mount -o remount,ro /usr',f'busybox rm /tmp/zve10-wifi-{action}']
                with patch.object(s,'read_file',side_effect=[before,helper]), patch.object(s,'run',return_value='/dev/nflasha15 /usr ext2 ro,relatime 0 0') as run:
                    def fail_helper(cam, cmd):
                        if cmd == f'/tmp/zve10-wifi-{action}':
                            raise RuntimeError('simulated I/O failure')
                        return '/dev/nflasha15 /usr ext2 ro,relatime 0 0'
                    run.side_effect = fail_helper
                    fails(lambda:s.dispatch(camera,{'action':action},folder,True),RuntimeError)
                    commands = [c.args[1] for c in run.call_args_list]
                    assert 'mount -o remount,ro /usr' in commands
                with patch.object(s,'read_file',return_value=before),patch.object(s,'run',return_value='/dev/other /usr ext4 rw 0 0') as run:
                    fails(lambda:s.dispatch(camera,{'action':action},folder,True))
                    assert len(run.call_args_list) == 1
            checks.append('Fake-camera patch/restore, mount guards, remount after helper failure')
    print(json.dumps({'offline_only':True,'camera_connected':False,'checks_passed':checks},indent=2))


if __name__ == '__main__':
    main()
