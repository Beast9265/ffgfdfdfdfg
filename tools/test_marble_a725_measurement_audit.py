"""Offline source-parser and counter-failure tests; no device execution."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('measurement_audit', Path(__file__).with_name('marble-a725-measurement-audit.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class MeasurementAuditTests(unittest.TestCase):
    def test_table_alignment_and_selector(self):
        text = '''static const char *const test_parent_names[] = {
 "other", "gpu_cc_ahb_clk",
};
static int test_sels[] = {
 0x99, /* unrelated16 */ 0x16,
};'''
        self.assertEqual(audit.selector(text, 'test', 'gpu_cc_ahb_clk'), 0x16)
        for bad in (text.replace('0x99,', ''), text.replace('"other"', '"gpu_cc_ahb_clk"')):
            with self.assertRaises(ValueError):
                audit.selector(bad, 'test', 'gpu_cc_ahb_clk')

    def test_counter_failures_are_not_clock_off_or_pass(self):
        for pair in ((0, 0), (100, 100), (100, 1)):
            self.assertEqual(audit.decode_pair(*pair)['status'], 'NO_ADVANCE_OR_INVALID_REFERENCE')
        for pair in ((-1, 10), (1, 0x1ffffff), (1, 0xffffffff)):
            self.assertEqual(audit.decode_pair(*pair)['status'], 'INVALID_OR_SATURATED')
        for s, f in ((False, True), (True, False), (False, False)):
            self.assertEqual(audit.decode_pair(100, 3200, s, f)['status'], 'TIMEOUT')
        self.assertEqual(audit.decode_pair(1, 1000000)['status'], 'INCONSISTENT_WINDOWS')

    def test_valid_counts_are_only_arithmetic(self):
        for hz in (19200000, 37500000, 75000000, 150000000, 300000000):
            counts = [round(((hz / 4) * (ticks * 10 + 35) / 4800000 - 15) / 10)
                      for ticks in (4096, 131072)]
            result = audit.decode_pair(*counts)
            self.assertEqual(result['status'], 'COUNTS_CONSISTENT_ONLY')
            self.assertLess(abs(result['hz'] - hz), 1000)
            self.assertFalse(result['ahb_verified'])
            self.assertFalse(result['writes_authorized'])


if __name__ == '__main__':
    unittest.main()
