"""Offline synthetic boot-v4 validation; contains no private image data."""
import contextlib
import io
from pathlib import Path
import struct
import tempfile
import unittest

import mkbootv4_marble as boot


def fixture():
    data = bytearray(12288)
    data[:8] = b'ANDROID!'
    struct.pack_into('<4I', data, 8, 3, 5, 0x220001aa, 1584)
    struct.pack_into('<I', data, 24, 0x12345678)  # reserved metadata
    struct.pack_into('<I', data, 40, 4)
    data[44:48] = b'test'
    data[4096:4099] = b'old'
    data[8192:8197] = b'cpio!'
    return data


class BootTests(unittest.TestCase):
    def test_reject_malformed(self):
        for offset, value in ((0, 0), (8, 0), (8, 0xffffffff),
                              (12, 0xffffffff), (20, 1580), (40, 3),
                              (1580, 0xffffffff)):
            data = fixture()
            struct.pack_into('<I', data, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                boot.parse(data)
        for length in (0, 1583, 4098, 8196, 12287):
            with self.subTest(length=length), self.assertRaises(ValueError):
                boot.parse(fixture()[:length])
        with self.assertRaises(ValueError):
            boot.align(boot.MAX_OFFSET)

    def test_deterministic_and_independent_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stock = root / 'stock'
            stock.write_bytes(fixture() + b'AVBfPRIVATE-TRAILER')
            with contextlib.redirect_stdout(io.StringIO()):
                boot.pack(stock, b'new' * 2000, root / 'a')
                boot.pack(stock, b'new' * 2000, root / 'b')
                boot.pack(stock, b'old', root / 'control', control=True)
            a = (root / 'a').read_bytes()
            self.assertEqual(a, (root / 'b').read_bytes())
            self.assertEqual((root / 'control').read_bytes(), fixture())
            self.assertEqual(a[12:1584], fixture()[12:1584])
            for offset in (0, 20, 40, 4096, 12288, len(a)-1):
                damaged = bytearray(a)
                damaged[offset] ^= 1
                with self.subTest(offset=offset), self.assertRaises(ValueError):
                    boot.independent_verify(damaged, a[:1584], b'new' * 2000, b'cpio!')
            with self.assertRaises(FileExistsError), contextlib.redirect_stdout(io.StringIO()):
                boot.pack(stock, b'new', root / 'a')


if __name__ == '__main__':
    unittest.main()
