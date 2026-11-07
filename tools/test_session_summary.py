#!/usr/bin/env python3
"""Offline tests for the privacy-safe session summary."""
import json
from pathlib import Path
import tempfile
import unittest

import session_summary as summary


class SessionSummaryTests(unittest.TestCase):
    def make_session(self, *, write_mode=False, library=summary.FACTORY,
                     backup=('00', '09', '09'), page=('TypeRK', 4), closed=True):
        temp = tempfile.TemporaryDirectory()
        folder = Path(temp.name)
        (folder / 'responses').mkdir()
        state = {
            'state': 'closed' if closed else 'ready',
            'write_mode': write_mode,
            'commands_completed': 2,
            'refused_count': 0,
            'terminal_closed': closed,
            'service_returned': closed,
        }
        (folder / 'state.json').write_text(json.dumps(state))
        inspect = {
            'size': summary.TARGET_SIZE,
            'sha256': library,
            'backup': dict(zip(summary.BACKUP_KEYS, backup)),
            'mounts': '/dev/nflasha15 /usr ext2 ro,relatime 0 0\n',
            'snapshot': 'private-token',
        }
        boot_check = {
            'pid': 157,
            'caution_base': '0x1234',
            'page1': {'type': page[0], 'count': page[1], 'table': '0x5678'},
            'warm_resume_markers': ['private boot-log line'],
        }
        close = {'action': 'close', 'accepted': True}
        for index, value in enumerate((inspect, boot_check, close)):
            (folder / 'responses' / f'{index}.json').write_text(json.dumps(value))
        return temp, folder

    def test_factory_read_only_session(self):
        temp, folder = self.make_session()
        self.addCleanup(temp.cleanup)
        result = summary.summarize(folder)
        self.assertTrue(result['valid_read_only_session'])
        self.assertEqual(result['inspection']['library'], 'factory')
        self.assertEqual(result['inspection']['backup_profile'], 'factory-observed')
        self.assertEqual(result['boot']['page_type'], 'TypeRK')
        self.assertTrue(result['boot']['warm_resume_detected'])

    def test_patched_china_session(self):
        temp, folder = self.make_session(
            library=summary.PATCHED, backup=('01', '02', '16'), page=('TypeNB', 5))
        self.addCleanup(temp.cleanup)
        result = summary.summarize(folder)
        self.assertTrue(result['valid_read_only_session'])
        self.assertEqual(result['inspection']['library'], 'patched')
        self.assertEqual(result['inspection']['backup_profile'], 'china-tested')

    def test_europe_reference_classification(self):
        temp, folder = self.make_session(
            library=summary.PATCHED, backup=('01', '0E', '17'), page=('TypeNB', 5))
        self.addCleanup(temp.cleanup)
        result = summary.summarize(folder)
        self.assertTrue(result['valid_read_only_session'])
        self.assertEqual(result['inspection']['backup_profile'], 'europe-reference')

    def test_write_or_unknown_state_is_not_accepted(self):
        temp, folder = self.make_session(write_mode=True, library='bad')
        self.addCleanup(temp.cleanup)
        result = summary.summarize(folder)
        self.assertFalse(result['valid_read_only_session'])
        self.assertFalse(result['checks']['read_only'])
        self.assertFalse(result['checks']['known_library'])

    def test_summary_omits_raw_private_values(self):
        temp, folder = self.make_session()
        self.addCleanup(temp.cleanup)
        rendered = json.dumps(summary.summarize(folder))
        for private in ('private-token', 'private boot-log line', '0x1071c54',
                        '/dev/nflasha15', '0x1234', '0x5678'):
            self.assertNotIn(private, rendered)


if __name__ == '__main__':
    unittest.main()
