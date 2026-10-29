#!/usr/bin/env python3
import importlib.util
import pathlib
import struct
import tempfile
import unittest


PATH = pathlib.Path(__file__).with_name('marble-a725-firmware.py')
SPEC = importlib.util.spec_from_file_location('marble_a725_firmware', PATH)
FW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FW)


class FirmwareTest(unittest.TestCase):
    @staticmethod
    def write_zap(root):
        ehdr = bytearray(0x34)
        ehdr[:6] = b'\x7fELF\x01\x01'
        struct.pack_into('<H', ehdr, 0x12, 164)
        struct.pack_into('<I', ehdr, 0x1c, 0x34)
        struct.pack_into('<HH', ehdr, 0x2a, 0x20, 2)
        b00 = bytes(ehdr) + struct.pack('<8I', 0, 0, 0, 0, 0x74, 0, 0, 0) + \
            struct.pack('<8I', 0, 0x1000, 0, 0, 4, 4, 2 << 24, 0x1000)
        b01 = b'HASH'
        mdt = b00 + b01
        (root / 'a730_zap.mdt').write_bytes(mdt)
        (root / 'a730_zap.b00').write_bytes(b00)
        (root / 'a730_zap.b01').write_bytes(b01)
        return mdt

    def test_gmu_block_bounds(self):
        valid = struct.pack('<4I4s', 0, 4, 0, 0, b'GMU!')
        self.assertEqual(FW.validate_gmu(valid)['blocks'], 1)
        with self.assertRaisesRegex(ValueError, 'exceeds image'):
            FW.validate_gmu(struct.pack('<4I', 0, 4, 0, 0))
        with self.assertRaisesRegex(ValueError, 'invalid range'):
            FW.validate_gmu(struct.pack('<4I4s', 0x20000000, 4, 0, 0, b'bad!'))

    def test_sqe_and_mdt(self):
        self.assertEqual(FW.validate_sqe(struct.pack('<2I', 0, 2))['dwords'], 2)
        with self.assertRaises(ValueError):
            FW.validate_sqe(struct.pack('<2I', 1, 0))
        mdt = bytearray(0x54)
        mdt[:6] = b'\x7fELF\x01\x01'
        struct.pack_into('<H', mdt, 0x12, 164)
        struct.pack_into('<I', mdt, 0x1c, 0x34)
        struct.pack_into('<HH', mdt, 0x2a, 0x20, 1)
        self.assertEqual(FW.validate_mdt(mdt)['program_headers'], 1)

    def test_inventory_requires_unique_complete_set(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / 'gmu_gen70000.bin').write_bytes(
                struct.pack('<4I4s', 0, 4, 0, 0, b'GMU!'))
            (root / 'a730_sqe.fw').write_bytes(struct.pack('<2I', 0, 2))
            self.write_zap(root)
            result = FW.inventory(root)
            self.assertEqual(set(result['firmware']), set(FW.PRIMARY_NAMES))
            self.assertEqual(set(result['zap_segments']),
                             {'a730_zap.b00', 'a730_zap.b01'})
            (root / 'a730_zap.b01').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError, 'does not match program header'):
                FW.inventory(root)


if __name__ == '__main__':
    unittest.main()
