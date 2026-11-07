"""Offline only: safety boundaries, transaction ordering, failed USB responses."""
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import wifi
import wbi
import jiritsu_upload


class UploadTests(unittest.TestCase):
    def test_single_write_and_exact_readback(self):
        camera = Mock()
        camera._sendAdjustControlPacket.return_value = bytes(4)
        reader = Mock(return_value=b'helper')
        path = '/tmp/jiritsu/zve10-wifi-patch'
        jiritsu_upload.upload(camera, path, b'helper', reader)
        self.assertEqual(camera._sendAdjustControlPacket.call_args_list[1].args,
                         (0x1001, 16, b'\0\xff\0helper'))
        self.assertEqual(camera._sendAdjustControlPacket.call_count, 2)
        reader.assert_called_once_with(camera, path, 65536)

    def test_bad_response_or_readback(self):
        for response, remote in ((b'', b'helper'), (struct.pack('<I', 1), b'helper'),
                                 (bytes(4), b'helpe'), (bytes(4), b'wrong!')):
            camera = Mock()
            camera._sendAdjustControlPacket.return_value = response
            with self.assertRaises(RuntimeError):
                jiritsu_upload.upload(camera, '/tmp/jiritsu/zve10-wifi-patch', b'helper', Mock(return_value=remote))

    def test_bad_upload_never_remounts_or_executes_and_cleans_up(self):
        for action in ('patch', 'restore'):
            with tempfile.TemporaryDirectory() as directory, \
                    patch.object(wifi, 'check_firmware'), patch.object(wifi, 'verify'), \
                    patch.object(wifi, 'read_file', return_value=b'known library'), \
                    patch.object(wifi, 'run', return_value='/dev/nflasha15 /usr ext2 ro 0 0') as run, \
                    patch.object(wifi, 'upload_verified', side_effect=RuntimeError('Helper upload mismatch')):
                with self.assertRaisesRegex(RuntimeError, 'mismatch'):
                    wifi.dispatch(Mock(), {'action': action}, Path(directory), True)
                commands = [c.args[1] for c in run.call_args_list]
                self.assertNotIn('mount -o remount,rw /usr', commands)
                self.assertNotIn('/tmp/jiritsu/zve10-wifi-' + action, commands)
                self.assertEqual(commands[-1], 'busybox rm -f /tmp/jiritsu/zve10-wifi-' + action)


class VersionTests(unittest.TestCase):
    def test_reject_203_and_inconsistent_reads_before_any_write(self):
        for versions in ((b'30110_06.2026060501',) * 2, (wifi.FIRMWARE, b'bad')):
            with patch.object(wifi, 'read_file', side_effect=versions), patch.object(wifi, 'run') as run:
                with self.assertRaisesRegex(ValueError, '2.02'):
                    wifi.dispatch(Mock(), {'action': 'patch'}, Path('.'), True)
                run.assert_not_called()

    def test_known_version(self):
        with patch.object(wifi, 'read_file', return_value=wifi.FIRMWARE):
            wifi.check_firmware(Mock())

    def test_unknown_library_and_sony_tool(self):
        with self.assertRaises(ValueError):
            wifi.verify(b'bad', wifi.FACTORY)
        with self.assertRaises(ValueError):
            wbi.validate_tool(bytes(6200))

    def test_changed_local_helper_hash_stops_before_upload(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(wifi, 'check_firmware'), patch.object(wifi, 'verify'), patch.object(wifi, 'read_file', return_value=b'known library'), patch.object(Path, 'read_bytes', return_value=b'changed helper'), patch.object(wifi, 'run', return_value='/dev/nflasha15 /usr ext2 ro 0 0') as run, patch.object(wifi, 'upload_verified') as upload:
            with self.assertRaisesRegex(ValueError, 'helper hash'):
                wifi.dispatch(Mock(), {'action': 'patch'}, Path(directory), True)
            upload.assert_not_called()
            self.assertEqual(run.call_count, 1)  # mount inspection only



class WbiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        # Small synthetic partition for transaction tests, no Sony/private bytes.
        self.size_patch = patch.object(wbi, 'SIZE', 1024)
        self.size_patch.start()
        self.addCleanup(self.size_patch.stop)
        self.before = b'WBI1' + b'x' * 1020
        self.after = bytes(512) + self.before[512:]
        self.ops = Mock()
        def save(folder, name, data):
            with (folder / name).open('xb') as stream:
                stream.write(data)
        self.ops.save_private.side_effect = save
        self.ops.run.return_value = '[UD_WBI_DROP] /dev/nflasha5 wbi_drop\n'
        self.camera = Mock()
        self.tool_patch = patch.object(wbi, 'validate_tool')
        self.tool_patch.start()
        self.addCleanup(self.tool_patch.stop)
        self.identity_patch = patch.object(wbi, 'identity', return_value={'device': wbi.DEVICE})
        self.identity_mock = self.identity_patch.start()
        self.addCleanup(self.identity_patch.stop)
        self.tool = self.folder / 'sony.elf'
        self.tool.write_bytes(b'synthetic test tool')

    def prepare(self, reads=None):
        def read(camera, folder, name, ops):
            data = next(iterator)
            (folder / name).write_bytes(data)
            return data
        iterator = iter(reads or [self.before, self.before])
        with patch.object(wbi, 'read_partition', side_effect=read):
            return wbi.dispatch(self.camera, {'action': 'wbi-prepare', 'model': 'ZV-E10',
                'displayed_firmware': '2.02', 'sony_tool': str(self.tool)}, self.folder, False, self.ops)

    def drop(self, prepared, reads=None, **kwargs):
        request = {'action': 'wbi-drop', 'prepared': prepared['token'], 'sony_tool': str(self.tool),
                   'confirm_emmc_write': prepared['confirmation'], 'recovery_ready': True, **kwargs}
        iterator = iter(reads or [self.before, self.after])
        def read(camera, folder, name, ops):
            data = next(iterator)
            (folder / name).write_bytes(data)
            return data
        with patch.object(wbi, 'read_partition', side_effect=read):
            return wbi.dispatch(self.camera, request, self.folder, True, self.ops)

    def test_success_and_one_time_token(self):
        prepared = self.prepare()
        result = self.drop(prepared)
        self.assertTrue(result['write_attempted'])
        self.assertIn('only first 512', result['status'])
        self.ops.upload_verified.assert_any_call(self.camera, unittest.mock.ANY, wbi.CONFIG)
        with self.assertRaises(FileExistsError):
            self.drop(prepared)
        executions = [c for c in self.ops.run.call_args_list if './ud_wbi_drop.elf' in c.args[1]]
        self.assertEqual(len(executions), 1)

    def test_double_backup_mismatch_prevents_write_and_saves_diagnostics(self):
        with self.assertRaisesRegex(ValueError, 'differ'):
            self.prepare([self.before, self.before[:-1] + b'y'])
        self.ops.upload_verified.assert_not_called()
        self.assertTrue(list(self.folder.glob('wbi-*-result.json')))
        self.assertEqual(len(list(self.folder.glob('*-read*.bin'))), 2)

    def test_already_invalid_never_writes(self):
        prepared = self.prepare([self.after, self.after])
        self.assertEqual(prepared['status'], 'already-invalid')
        with self.assertRaisesRegex(ValueError, 'already invalid'):
            self.drop(prepared)
        self.ops.run.assert_not_called()
        self.ops.upload_verified.assert_not_called()

    def test_header_size_and_device_guards(self):
        for bad in (b'BAD!' + self.before[4:], self.before[:-1]):
            with self.assertRaises(ValueError):
                wbi.validate_backups(bad, bad)
        for partitions, geometry in (('1 5 1 nflasha5', '1:5 180224 122880'),
                                     ('1 5 61440 nflasha5', '1:6 180224 122880'),
                                     ('1 5 61440 nflasha5', '1:5 0 122880'),
                                     ('1 5 61440 nflasha6', '1:5 180224 122880')):
            with self.assertRaises(ValueError):
                wbi.validate_partition(partitions, geometry)
        wbi.validate_partition('1 5 61440 nflasha5', '1:5\n180224\n122880')

    def test_no_confirmation_or_recovery_plan_no_write(self):
        prepared = self.prepare()
        for change in ({'confirm_emmc_write': 'yes'}, {'recovery_ready': False}):
            with self.assertRaises(ValueError):
                self.drop(prepared, **change)
        self.ops.upload_verified.assert_not_called()
        self.ops.run.assert_not_called()

    def test_identity_change_and_stale_partition_no_write(self):
        prepared = self.prepare()
        self.identity_mock.return_value = {'device': '/dev/unknown'}
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            self.drop(prepared)
        self.identity_mock.return_value = prepared['identity']
        with self.assertRaisesRegex(ValueError, 'changed since double backup'):
            self.drop(prepared, [self.before[:-1] + b'z'])
        self.ops.upload_verified.assert_not_called()

    def test_unexpected_postwrite_difference_is_explicit_and_preserved(self):
        prepared = self.prepare()
        with self.assertRaisesRegex(RuntimeError, 'outside expected first 512'):
            self.drop(prepared, [self.before, self.after[:-1] + b'z'])
        self.assertTrue(list(self.folder.glob('*-after.bin')))
        results = [json.loads(p.read_text()) for p in self.folder.glob('*-result.json')]
        self.assertTrue(any(r['write_attempted'] and 'error' in r for r in results))

    def test_upload_failure_cleans_files_and_never_runs_sony_tool(self):
        prepared = self.prepare()
        self.ops.upload_verified.side_effect = RuntimeError('upload mismatch')
        with self.assertRaisesRegex(RuntimeError, 'mismatch'):
            self.drop(prepared)
        commands = [c.args[1] for c in self.ops.run.call_args_list]
        self.assertFalse(any('./ud_wbi_drop.elf' in cmd for cmd in commands))
        self.assertTrue(any('busybox rm -f' in cmd for cmd in commands))

    def test_execution_failure_still_reads_full_partition(self):
        prepared = self.prepare()
        def run(camera, cmd):
            if './ud_wbi_drop.elf' in cmd:
                raise TimeoutError('response lost')
            return ''
        self.ops.run.side_effect = run
        with self.assertRaisesRegex(RuntimeError, 'failed despite expected readback'):
            self.drop(prepared)
        self.assertTrue(list(self.folder.glob('*-after.bin')))

    def test_wrong_owner_model_or_version_no_access(self):
        for model, version in (('ZV-E10M2', '2.02'), ('ZV-E10', '2.03')):
            with self.assertRaises(ValueError):
                wbi.dispatch(self.camera, {'action':'wbi-prepare', 'model':model,
                             'displayed_firmware':version}, self.folder, False, self.ops)
        self.identity_mock.assert_not_called()


class RawReadTests(unittest.TestCase):
    def test_bounded_stream_keeps_partial_and_complete_evidence(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(wbi, 'SIZE', 1024):
            folder = Path(directory)
            ops = Mock()
            def read(camera, path, sink):
                self.assertEqual(path, '/dev/nflasha5')
                sink.write(b'a' * 512)
                sink.write(b'b' * 512)
                return 0, None
            ops.common.read_path.side_effect = read
            self.assertEqual(wbi.read_partition(Mock(), folder, 'complete.bin', ops), b'a'*512+b'b'*512)
            self.assertEqual((folder/'complete.bin').stat().st_mode & 0o777, 0o600)
            def short(camera, path, sink):
                sink.write(b'partial')
                return 0, None
            ops.common.read_path.side_effect = short
            with self.assertRaisesRegex(RuntimeError, 'Incomplete'):
                wbi.read_partition(Mock(), folder, 'short.bin', ops)
            self.assertEqual((folder/'short.bin').read_bytes(), b'partial')
            def oversized(camera, path, sink):
                sink.write(b'valid')
                sink.write(bytes(1024))
            ops.common.read_path.side_effect = oversized
            with self.assertRaisesRegex(RuntimeError, 'exceeds'):
                wbi.read_partition(Mock(), folder, 'oversized.bin', ops)
            self.assertEqual((folder/'oversized.bin').read_bytes(), b'valid')

    def test_block_node_identity_and_config_hash(self):
        self.assertEqual(wbi.sha(wbi.CONFIG), wbi.CONFIG_HASH)
        partitions, geometry = '1 5 61440 nflasha5', '1:5 180224 122880'
        wbi.validate_partition(partitions, geometry, 'brw------- 1 root root 1, 5 Nov 7 08:00 /dev/nflasha5')
        with self.assertRaisesRegex(ValueError, 'node'):
            wbi.validate_partition(partitions, geometry, 'brw------- 1 root root 1, 6 Nov 7 08:00 /dev/nflasha5')

    def test_model_fingerprint_failure_preserves_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            with patch.object(wifi, 'check_firmware'), patch.object(wifi, 'read_file', return_value=b'unknown model'), patch.object(wifi, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'fingerprint'):
                    wbi.identity(Mock(), wifi, folder)
                run.assert_not_called()
            self.assertTrue(list(folder.glob('wbi-identity-*.json')))


if __name__ == '__main__':
    unittest.main()
