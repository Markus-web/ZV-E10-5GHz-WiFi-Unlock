#!/usr/bin/env python3
"""Wi-Fi-specific actions using zv-e10-toolkit's existing service server/client.
No connection, queue, framing, authentication or teardown implementation here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

import jiritsu_upload
import wbi

ROOT = Path(__file__).resolve().parent.parent
TOOLKIT = Path(os.environ.get('ZVE10_TOOLKIT', ROOT / 'vendor/zv-e10-toolkit')).resolve()
HOST = TOOLKIT / 'linux/host'
if not (HOST / 'zve10_common.py').is_file():
    raise SystemExit('Set ZVE10_TOOLKIT to your zv-e10-toolkit checkout; see docs/install.md')
sys.path.insert(0, str(HOST))
import zve10_common as common
from zve10_read_file_jiritsu import read_file as jiritsu_read_file
try:
    import zve10_backup_properties as backup_properties
except ImportError as exc:
    raise SystemExit('Toolkit Backup-property update is missing; see docs/install.md') from exc

TARGET = '/usr/lib/CautionConfig.so'
SIZE = 17694160
FACTORY = '5ad8746a229da259fe00b297e8f897d682f7ae9a13393025b3d1c95a808e68d7'
PATCHED = '14f42cc09ee1b9ddde5352482c13b68e5a5e97d9d79e8456087b5e0b7af6ff6a'
OFFSET = 0xD778E4
KEYS = (0x01071C54, 0x00A5000B, 0x00A5000C)
FIRMWARE = b'30110_05.2025031501'  # system 2.02; reject 2.03 (30110_06.2026060501)
HELPER_HASHES = {
    'patch': 'f8270987db52912e987d2a8c8fd7576096085571a1aa5de73bc98fe21c865ea6',
    'restore': 'ae3ce7d823a4e19a162befd236db9af99f222bc3b48a44468288b62888a7f712',
}
PAGE1_VMA = 0x011EB858
TYPE_NB_VMA = 0x010E2AD8
TYPE_RK_VMA = 0x010E2BBC


def parse_page1(node_hex, base):
    data = bytes.fromhex(''.join(node_hex.split()))
    if len(data) != 12:
        raise RuntimeError('Short Page1 read; STOP')
    table = int.from_bytes(data[4:8], 'little')
    count = int.from_bytes(data[8:12], 'little')
    kind = ('TypeNB' if (table, count) == (base + TYPE_NB_VMA, 5)
            else 'TypeRK' if (table, count) == (base + TYPE_RK_VMA, 4)
            else 'unknown')
    return {'type': kind, 'table': hex(table), 'count': count}


def boot_check(camera):
    # Read the running process, never use stale absolute addresses or write memory.
    pid_text = run(camera, 'busybox pidof im.elf').strip()
    if not pid_text.isdecimal():
        raise RuntimeError('Expected exactly one im.elf process; STOP')
    maps = run(camera, 'busybox grep CautionConfig.so /proc/' + pid_text + '/maps')
    rows = [line.split() for line in maps.splitlines() if line.endswith('/usr/lib/CautionConfig.so')]
    heads = [row for row in rows if len(row) >= 6 and row[1:3] == ['r-xp', '00000000']]
    if len(heads) != 1:
        raise RuntimeError('CautionConfig.so module base not unique; STOP')
    base = int(heads[0][0].split('-')[0], 16)
    address = base + PAGE1_VMA
    raw = run(camera, f'busybox dd if=/proc/{pid_text}/mem bs=1 skip={address} count=12 2>/dev/null | busybox xxd -p')
    page = parse_page1(raw, base)
    log = common.command(camera.dev, 'unlock_boot_log',
                         'busybox dmesg | busybox grep -i -E "WARMBOOT|Low-level resume|Waking up from system sleep"', 60)
    if log['exit_code'] not in (0, 1) or (log['exit_code'] == 1 and log['output'].strip()):
        raise RuntimeError('Boot-log check failed; STOP: ' + str(log))
    markers = [line.strip() for line in log['output'].splitlines() if line.strip()]
    return {'pid': int(pid_text), 'caution_base': hex(base), 'page1_address': hex(address),
            'page1': page, 'warm_resume_markers': markers,
            'assessment': ('warm-resume detected' if markers else
                           'no warm-resume marker observed; confirm menu on camera')}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(data, expected):
    if len(data) != SIZE or digest(data) != expected:
        raise ValueError('Unknown/truncated CautionConfig.so; STOP, do not patch or reboot')


def run(camera, cmd):
    result = common.command(camera.dev, 'unlock', cmd, 60)
    if result['exit_code'] != 0:
        raise RuntimeError(str(result))
    return result['output']


def read_file(camera, path):
    common.set_terminal_timeout(camera, 30000)
    status, data = common.read_path(camera, path)
    if status not in (0, 1) or data is None:
        raise RuntimeError('FileControl read failed: ' + path)
    return bytes(data)


def check_firmware(camera):
    # Check on every operation, even if a server was started with an override.
    versions = [read_file(camera, '/version.txt') for _ in range(2)]
    if versions != [FIRMWARE, FIRMWARE]:
        raise ValueError('Only ZV-E10 system 2.02 (30110_05.2025031501) is supported; STOP: ' + repr(versions))


def upload_verified(camera, path, data):
    jiritsu_upload.upload(camera, path, data, jiritsu_read_file)


def save_private(folder, name, data):
    fd = os.open(folder / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    (folder / name).chmod(0o600)
    common.restore_owner(folder / name)


def dispatch(camera, req, folder, allow_write):
    action = req.get('action')
    token = uuid.uuid4().hex
    if action in ('wbi-prepare', 'wbi-drop'):
        return wbi.dispatch(camera, req, folder, allow_write, sys.modules[__name__])
    check_firmware(camera)
    if action == 'inspect':
        data = read_file(camera, TARGET)
        values = {hex(k): backup_properties.dispatch(camera, {'action': 'backup-read', 'id': hex(k)}, folder, False)['value'] for k in KEYS}
        save_private(folder, token + '-CautionConfig.so', data)
        for path in ('/setting/Backup.bin', '/setting/Backup.bak'):
            save_private(folder, token + '-' + Path(path).name, read_file(camera, path))
        return {'size': len(data), 'sha256': digest(data), 'backup': values,
                'mounts': run(camera, 'busybox cat /proc/mounts'), 'snapshot': token}
    if action == 'boot-check':
        return boot_check(camera)
    if not allow_write:
        raise ValueError('Read-only session; restart with --owner-authorized-write after owner confirmation')
    if action == 'backup-write':
        key = int(req['id'], 0)
        expected, value = bytes.fromhex(req['expected']), bytes.fromhex(req['value'])
        if key not in KEYS or len(expected) != 1 or len(value) != 1:
            raise ValueError('Only the three one-byte Backup properties are supported')
        if (key == KEYS[0] and value[0] not in (0, 1)) or (key in KEYS[1:] and not 1 <= value[0] <= 26):
            raise ValueError('Value outside known template range')
        return backup_properties.dispatch(camera, req, folder, allow_write)
    if action in ('patch', 'restore'):
        before_hash, after_hash = (FACTORY, PATCHED) if action == 'patch' else (PATCHED, FACTORY)
        data = read_file(camera, TARGET)
        verify(data, before_hash)
        save_private(folder, token + '-before-' + action + '.so', data)
        mounts = run(camera, 'busybox cat /proc/mounts')
        rows = [line.split() for line in mounts.splitlines() if len(line.split()) >= 4 and line.split()[1] == '/usr']
        if len(rows) != 1 or rows[0][0] != '/dev/nflasha15' or rows[0][2] != 'ext2' or 'ro' not in rows[0][3].split(','):
            raise ValueError('Unexpected /usr mount; no write')
        helper = (ROOT / 'tools' / (action + '.arm')).read_bytes()
        if digest(helper) != HELPER_HASHES[action]:
            raise ValueError('Unknown local ARM helper hash; STOP')
        remote = '/tmp/jiritsu/zve10-wifi-' + action
        # Reuse the 2.02-tested single SET_FILE2 write and full Jiritsu GET_FILE.
        run(camera, 'busybox mkdir -p /tmp/jiritsu')
        try:
            upload_verified(camera, remote, helper)
            run(camera, 'busybox chmod 700 ' + remote)
            try:
                run(camera, 'mount -o remount,rw /usr')
                # The helper checks old byte, writes without O_TRUNC, fsyncs, reads back.
                run(camera, remote)
                after = read_file(camera, TARGET)
                save_private(folder, token + '-after-' + action + '.so', after)
                verify(after, after_hash)
                diffs = [i for i, (a, b) in enumerate(zip(data, after)) if a != b]
                if diffs != [OFFSET]:
                    raise RuntimeError('Unexpected full-file difference')
            finally:
                run(camera, 'mount -o remount,ro /usr')
            return {'sha256': digest(after), 'size': len(after), 'only_difference': hex(OFFSET)}
        finally:
            run(camera, 'busybox rm -f ' + remote)
    raise ValueError('Unknown action')


def main():
    # Forward server lifecycle to the existing toolkit without reimplementing it.
    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        import zve10_terminal_server as server
        if not hasattr(server, 'REQUEST_HANDLER'):
            raise SystemExit('This toolkit lacks the action extension; see docs/install.md for the required toolkit update')
        server.REQUEST_HANDLER = dispatch
        server.main()
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('request',))
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('json_request')
    args = parser.parse_args()
    # Existing client owns queue serialization, response polling and timeouts.
    import zve10_terminal_client as client
    folder = args.session.resolve()
    if client.read_state(folder).get('state') != 'ready':
        raise SystemExit('Session is not ready')
    answer = client.submit(folder, json.loads(args.json_request), timeout=360)
    print(json.dumps(answer, indent=2))
    if 'error' in answer or 'refused' in answer:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
