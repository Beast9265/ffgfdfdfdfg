"""ADT-only product restoration contract, using synthetic metadata."""
import importlib.util
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

import adt
import mkadt

spec = importlib.util.spec_from_file_location('product_adt', Path(__file__).with_name('marble-product-adt.py'))
product = importlib.util.module_from_spec(spec)
spec.loader.exec_module(product)
PROPS = [('artwork-device-idiom', b'phone\0'),
         ('artwork-device-subtype', struct.pack('<I', 2436)),
         ('artwork-scale-factor', struct.pack('<I', 3))]


class ProductTests(unittest.TestCase):
    def old_blob(self):
        with patch.object(mkadt, 'd22ap_product', return_value=PROPS):
            root = mkadt.build(seed=bytes(range(64)), marble=True)
        root.children = [child for child in root.children if child.name != 'product']
        return adt.serialize(root)

    def test_only_adds_product_and_preserves_existing_bytes(self):
        before, _ = adt.parse(self.old_blob())
        after, _ = adt.parse(product.restore_product(self.old_blob(), PROPS))
        self.assertEqual(before.props, after.props)
        self.assertEqual([adt.serialize(c) for c in before.children],
                         [adt.serialize(c) for c in after.children[:-1]])
        self.assertEqual(after.children[-1].name, 'product')
        self.assertEqual(after.children[-1].prop('artwork-device-idiom'), b'phone\0')

    def test_rejects_overwrite_other_board_bad_props_and_trailing_data(self):
        blob = self.old_blob()
        cases = [(product.restore_product(blob, PROPS), PROPS),
                 (blob, PROPS[:-1]), (blob + b'junk', PROPS),
                 (blob, PROPS + [('name', b'fake\0')])]
        for value, props in cases:
            with self.assertRaises(ValueError):
                product.restore_product(value, props)
        root, _ = adt.parse(blob)
        root.props = [(key, flags, b'other\0' if key == 'compatible' else value)
                      for key, flags, value in root.props]
        with self.assertRaises(ValueError):
            product.restore_product(adt.serialize(root), PROPS)
