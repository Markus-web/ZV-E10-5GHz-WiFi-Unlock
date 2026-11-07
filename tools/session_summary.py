#!/usr/bin/env python3
"""Summarize a private Wi-Fi session without exposing raw camera evidence."""
import argparse
import json
from pathlib import Path


FACTORY = '5ad8746a229da259fe00b297e8f897d682f7ae9a13393025b3d1c95a808e68d7'
PATCHED = '14f42cc09ee1b9ddde5352482c13b68e5a5e97d9d79e8456087b5e0b7af6ff6a'
TARGET_SIZE = 17694160
BACKUP_KEYS = ('0x1071c54', '0xa5000b', '0xa5000c')


def load_json(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('Cannot read JSON: ' + path.name) from exc
    if not isinstance(value, dict):
        raise ValueError('Expected JSON object: ' + path.name)
    return value


def classify_library(response):
    if response.get('size') != TARGET_SIZE:
        return 'unknown'
    return {FACTORY: 'factory', PATCHED: 'patched'}.get(
        response.get('sha256'), 'unknown')


def classify_backup(response):
    backup = response.get('backup')
    if not isinstance(backup, dict):
        return 'unknown'
    values = tuple(str(backup.get(key, '')).lower() for key in BACKUP_KEYS)
    return {
        ('00', '09', '09'): 'factory-observed',
        ('01', '02', '16'): 'china-tested',
        ('01', '0e', '17'): 'europe-reference',
    }.get(values, 'other')


def usr_mount_state(response):
    rows = []
    for line in str(response.get('mounts', '')).splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[1] == '/usr':
            rows.append(fields)
    if len(rows) != 1:
        return 'missing-or-ambiguous'
    device, _, filesystem, options = rows[0][:4]
    if (device, filesystem) != ('/dev/nflasha15', 'ext2'):
        return 'unexpected'
    return 'read-only' if 'ro' in options.split(',') else 'writable'


def summarize(session):
    session = Path(session)
    state = load_json(session / 'state.json')
    responses = []
    response_dir = session / 'responses'
    if response_dir.is_dir():
        responses = [load_json(path) for path in sorted(response_dir.glob('*.json'))]

    inspect = next((item for item in responses
                    if {'size', 'sha256', 'backup', 'mounts'} <= item.keys()), None)
    boot = next((item for item in responses if isinstance(item.get('page1'), dict)), None)
    close = next((item for item in responses if item.get('action') == 'close'), None)

    library = classify_library(inspect or {})
    backup = classify_backup(inspect or {})
    mount = usr_mount_state(inspect or {})
    page = (boot or {}).get('page1', {})
    page_type = page.get('type', 'missing')
    page_count = page.get('count')
    warm_resume = bool((boot or {}).get('warm_resume_markers', []))

    checks = {
        'closed': state.get('state') == 'closed',
        'read_only': state.get('write_mode') is False,
        'commands_recorded': isinstance(state.get('commands_completed'), int)
                             and state['commands_completed'] >= 2,
        'no_refusals': state.get('refused_count') == 0,
        'terminal_closed': state.get('terminal_closed') is True,
        'service_returned': state.get('service_returned') is True,
        'known_library': library in ('factory', 'patched'),
        'usr_read_only': mount == 'read-only',
        'known_page': (page_type, page_count) in (('TypeRK', 4), ('TypeNB', 5)),
        'close_accepted': bool(close and close.get('accepted') is True),
    }
    return {
        'privacy': 'raw paths, mounts, property IDs/values, process IDs and addresses omitted',
        'session': {
            'state': state.get('state', 'unknown'),
            'write_mode': bool(state.get('write_mode')),
            'commands_completed': state.get('commands_completed'),
            'refused_count': state.get('refused_count'),
        },
        'inspection': {
            'library': library,
            'backup_profile': backup,
            'usr_mount': mount,
        },
        'boot': {
            'page_type': page_type,
            'page_count': page_count,
            'warm_resume_detected': warm_resume,
        },
        'checks': checks,
        'valid_read_only_session': all(checks.values()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session', type=Path,
                        help='private session directory containing state.json and responses/')
    args = parser.parse_args()
    try:
        result = summarize(args.session)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['valid_read_only_session'] else 1)


if __name__ == '__main__':
    main()
