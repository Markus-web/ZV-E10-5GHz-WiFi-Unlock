"""Reuse the 2.02-tested SET_FILE_PATH / SET_FILE2 upload sequence.
Transport and GET_FILE decryption stay in Sony-PMCA-RE / zv-e10-toolkit.
"""
import struct


def upload(camera, path, data, readback):
    if not path.startswith('/tmp/jiritsu/zve10-wifi-') or '..' in path or '\0' in path:
        raise ValueError('Upload is restricted to Wi-Fi temporary files')
    if not data or len(data) > 65536:
        raise ValueError('Only small helpers/configuration files may be uploaded')
    for code, payload in ((15, b'\0' + path.encode('ascii') + b'\0'),
                          (16, b'\0\xff\0' + data)):
        response = camera._sendAdjustControlPacket(0x1001, code, payload)
        if len(response) < 4:
            raise RuntimeError('Short Jiritsu upload response; STOP')
        status = struct.unpack_from('<I', response)[0]
        if status:
            raise RuntimeError('Jiritsu command %d failed: 0x%08x; STOP' % (code, status))
    # Host comparison; camera BusyBox hashes and hex dumps are not trusted.
    if readback(camera, path, 65536) != data:
        raise RuntimeError('Helper upload mismatch; STOP before execution')
