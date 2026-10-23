"""Offline MARBLE ADT/payload contract; no hardware or private fixtures."""
import struct
import unittest
from unittest.mock import patch
import adt
import mkadt
import mkpayload


class MarbleTreeTests(unittest.TestCase):
    def test_marble_roundtrip(self):
        # Synthetic metadata fixture: tests never require an Apple artifact.
        product_props = [('artwork-device-idiom', mkadt.cstr('phone')),
                         ('artwork-device-subtype', mkadt.u32(2436)),
                         ('artwork-scale-factor', mkadt.u32(3))]
        with patch.object(mkadt, 'd22ap_product', return_value=product_props):
            blob = adt.serialize(mkadt.build(seed=bytes(64), marble=True))
        root, end = adt.parse(blob)
        self.assertEqual(end, len(blob))
        child = lambda n, name: next(c for c in n.children if c.name == name)
        q = lambda n, key: struct.unpack('<Q', n.prop(key))[0]
        u = lambda n, key: struct.unpack('<I', n.prop(key))[0]
        chosen = child(root, 'chosen')
        self.assertEqual((q(chosen, 'dram-base'), q(chosen, 'dram-size')),
                         (0x840000000, 0x100000000))
        self.assertEqual(mkpayload.adt_dram(blob), (0x840000000, 0x100000000))
        self.assertEqual(q(chosen, 'unique-chip-id'), 0x4d4152424c450001)
        cpus = child(root, 'cpus').children
        self.assertEqual(len(cpus), 1)
        self.assertEqual(u(cpus[0], 'reg'), 0)
        self.assertEqual(cpus[0].prop('compatible'), b'qcom,marble-cpu\0ARM,v8\0')
        product = child(root, 'product')
        self.assertEqual(product.prop('artwork-device-idiom'), b'phone\0')
        self.assertEqual(u(product, 'artwork-device-subtype'), 2436)
        self.assertEqual(u(product, 'artwork-scale-factor'), 3)
        io = child(root, 'arm-io')
        self.assertEqual([c.name for c in io.children], ['gic', 'disp0'])
        display = child(io, 'disp0')
        self.assertEqual((u(display, 'canvas-width'), u(display, 'canvas-height')), (1125, 2436))
        self.assertEqual(u(chosen, 'display-scale'), 3)
        gic = child(io, 'gic')
        self.assertEqual(struct.unpack('<4Q', gic.prop('reg')),
                         (0x17100000-mkadt.SOC_BASE, 0x10000,
                          0x17180000-mkadt.SOC_BASE, 0x200000))
        self.assertEqual(u(gic, 'virtual-timer-intid'), 27)
        self.assertEqual(u(cpus[0], 'timebase-frequency'), 19200000)
        fb = child(root, 'sweet-fbcon')
        self.assertEqual(struct.unpack('<2Q', fb.prop('reg')), (0xb8000000, 0x009e3400))
        self.assertEqual(tuple(u(fb, p) for p in ('width','height','stride')), (1080,2400,4320))
        self.assertEqual(root.prop('compatible'),
                         b'D22AP\0iPhone10,3\0xiaomi,marble\0qcom,sm7475\0AppleARM\0')
        self.assertNotIn('sweet-ufs', [c.name for c in root.children])
        ufs = child(root, 'marble-ufs')
        self.assertEqual(struct.unpack('<2Q', ufs.prop('reg')), (0x01d84000, 0x3000))
        self.assertEqual(ufs.prop('compatible'), b'qcom,ufshc\0')

    def test_marble_rejects_missing_or_incompatible_artwork_metadata(self):
        for props in (None, [], [('artwork-device-idiom', mkadt.cstr('pad'))]):
            with self.subTest(props=props), patch.object(mkadt, 'd22ap_product', return_value=props):
                with self.assertRaisesRegex(ValueError, 'D22AP /product artwork metadata'):
                    mkadt.build(seed=bytes(64), marble=True)

    def test_modes_are_exclusive_and_sweet_remains_default(self):
        for kwargs in ({'qemu': True}, {'highmem': True}):
            with self.assertRaises(ValueError):
                mkadt.build(marble=True, **kwargs)
        root = mkadt.build(seed=bytes(64))
        self.assertIn(b'xiaomi,sweet\0', root.prop('compatible'))
        self.assertEqual(len(next(c for c in root.children if c.name == 'cpus').children), 8)


if __name__ == '__main__':
    unittest.main()
