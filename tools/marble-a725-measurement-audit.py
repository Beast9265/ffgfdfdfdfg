#!/usr/bin/env python3
"""Offline Cape debugcc audit. Reads source files only; never authorizes MMIO."""
import argparse
import json
from pathlib import Path
import re


def source(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"expected regular source file: {path}")
    return path.read_text()


def initializer(text, kind, name):
    match = re.search(r'static\s+' + kind + r'\s+' + name + r'\s*=\s*\{(.*?)\n\};', text, re.S)
    if not match:
        raise ValueError(f"missing initializer: {name}")
    return match.group(1)


def value(text, name):
    match = re.search(r'\.' + name + r'\s*=\s*(0[xX][0-9a-fA-F]+|[0-9]+)\s*,', text)
    if not match:
        raise ValueError(f"missing numeric field: {name}")
    return int(match.group(1), 0)


def selector(text, prefix, parent):
    names = initializer(text, r'const char \*const', prefix + r'_parent_names\[\]')
    sels = initializer(text, r'int', prefix + r'_sels\[\]')
    names = re.findall(r'"([^"]+)"', names)
    sels = re.sub(r'/\*.*?\*/', '', sels, flags=re.S)
    numbers = [int(x, 0) for x in re.findall(r'0[xX][0-9a-fA-F]+|\b[0-9]+\b', sels)]
    if len(names) != len(numbers) or names.count(parent) != 1:
        raise ValueError(f"ambiguous/mismatched selector table: {prefix}")
    return numbers[names.index(parent)]


def audit(debugcc, clock_debug, rpmh, board_xo_hz):
    gpu = initializer(debugcc, r'struct clk_debug_mux', 'gpu_cc_debug_mux')
    gcc = initializer(debugcc, r'struct clk_debug_mux', 'gcc_debug_mux')
    measure = initializer(debugcc, r'struct measure_clk_data', 'debug_mux_priv')
    expected = ((gpu, {'debug_offset': 0x9564, 'post_div_offset': 0x9270,
                      'cbcr_offset': 0x9274, 'src_sel_mask': 0xff,
                      'post_div_mask': 15, 'post_div_val': 2}),
                (gcc, {'debug_offset': 0x72000, 'post_div_offset': 0x72004,
                      'cbcr_offset': 0x72008, 'src_sel_mask': 0x3ff,
                      'post_div_mask': 15, 'post_div_val': 2}),
                (measure, {'ctl_reg': 0x72038, 'status_reg': 0x7203c,
                           'xo_div4_cbcr': 0x7200c}))
    for block, fields in expected:
        for field, wanted in fields.items():
            if value(block, field) != wanted:
                raise ValueError(f"unexpected {field}")
    if '.pre_div_vals' in gpu or '.pre_div_vals' in gcc:
        raise ValueError('additional divider needs re-audit')
    for block in (gpu, gcc):
        if value(block, 'src_sel_shift') or value(block, 'post_div_shift'):
            raise ValueError('unexpected field shift')
    if selector(debugcc, 'gpu_cc_debug_mux', 'gpu_cc_ahb_clk') != 0x16:
        raise ValueError('AHB selector mismatch')
    if selector(debugcc, 'gcc_debug_mux', 'gpu_cc_debug_mux') != 0x16e:
        raise ValueError('GCC route mismatch')
    match = re.search(r'DEFINE_CLK_RPMH_ARC\(waipio,\s*bi_tcxo,\s*bi_tcxo_ao,\s*"xo.lvl",\s*0x3,\s*(\d+)\)', rpmh)
    if not match or int(match.group(1)) != 4 or board_xo_hz != 76800000:
        raise ValueError('XO/provider rate needs re-audit')
    if not re.search(r'#define\s+TCXO_DIV_4_HZ\s+4800000\b', clock_debug):
        raise ValueError('counter reference constant mismatch')
    return {
        'source_route_verified': True,
        'gpu_selector': '0x16', 'gcc_selector': '0x16e',
        'nominal_reference_hz': board_xo_hz // 4 // 4,
        'mux_scale': 4, 'windows': [0x1000, 0x20000],
        'window_us_nominal': [4096 * 1e6 / 4800000, 131072 * 1e6 / 4800000],
        'hardware_observed': False, 'writes_authorized': False,
        'missing': ['live debug mux/gate/CTL/STATUS snapshots',
                    'exclusive shared-engine ownership evidence',
                    'live reference/control measurement',
                    'bounded stop and restoration verification contract'],
    }


def decode_pair(short_count, full_count, short_done=True, full_done=True):
    """Counter arithmetic only: no signal identity, reference or AHB PASS claim."""
    if not short_done or not full_done:
        return {'status': 'TIMEOUT', 'hz': None}
    if any(not isinstance(x, int) or not 0 <= x < 0x1ffffff
           for x in (short_count, full_count)):
        return {'status': 'INVALID_OR_SATURATED', 'hz': None}
    if full_count <= short_count:
        return {'status': 'NO_ADVANCE_OR_INVALID_REFERENCE', 'hz': None}
    # Pinned clk-debug.c affine calibration, two /2 debug post dividers.
    hz = ((full_count * 10 + 15) * 4800000 // (0x20000 * 10 + 35)) * 4
    slope_hz = (full_count - short_count) * 4800000 * 4 // (0x20000 - 0x1000)
    if abs(hz - slope_hz) > max(10000, hz // 100):
        return {'status': 'INCONSISTENT_WINDOWS', 'hz': None}
    return {'status': 'COUNTS_CONSISTENT_ONLY', 'hz': hz,
            'ahb_verified': False, 'writes_authorized': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('debugcc')
    parser.add_argument('clk_debug')
    parser.add_argument('clk_rpmh')
    parser.add_argument('--board-xo-hz', type=int, required=True)
    args = parser.parse_args()
    try:
        report = audit(source(args.debugcc), source(args.clk_debug),
                       source(args.clk_rpmh), args.board_xo_hz)
    except ValueError as error:
        parser.exit(1, f"source audit refused: {error}\n")
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
