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

ROOT = Path(__file__).resolve().parent.parent
TOOLKIT = Path(os.environ.get('ZVE10_TOOLKIT', ROOT / 'vendor/zv-e10-toolkit')).resolve()
HOST = TOOLKIT / 'linux/host'
if not (HOST / 'zve10_common.py').is_file():
    raise SystemExit('Set ZVE10_TOOLKIT to your zv-e10-toolkit checkout; see docs/install.md')
sys.path.insert(0, str(HOST))
import zve10_common as common
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


def save_private(folder, name, data):
    with (folder / name).open('xb') as f:
        f.write(data)
    (folder / name).chmod(0o600)
    common.restore_owner(folder / name)


def dispatch(camera, req, folder, allow_write):
    action = req.get('action')
    token = uuid.uuid4().hex
    if action == 'inspect':
        data = read_file(camera, TARGET)
        values = {hex(k): backup_properties.dispatch(camera, {'action': 'backup-read', 'id': hex(k)}, folder, False)['value'] for k in KEYS}
        save_private(folder, token + '-CautionConfig.so', data)
        for path in ('/setting/Backup.bin', '/setting/Backup.bak'):
            save_private(folder, token + '-' + Path(path).name, read_file(camera, path))
        return {'size': len(data), 'sha256': digest(data), 'backup': values,
                'mounts': run(camera, 'busybox cat /proc/mounts'), 'snapshot': token}
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
        remote = '/tmp/zve10-wifi-' + action
        # Upload ONLY our small helper, never replace the Sony library.
        run(camera, ': > ' + remote)
        try:
            for pos in range(0, len(helper), 48):
                run(camera, "echo '" + helper[pos:pos+48].hex() + "' | busybox xxd -r -p >> " + remote)
            if read_file(camera, remote) != helper:
                raise RuntimeError('Helper upload mismatch')
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
            run(camera, 'busybox rm ' + remote)
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
