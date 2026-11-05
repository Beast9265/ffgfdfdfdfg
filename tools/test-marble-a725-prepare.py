#!/usr/bin/env python3
"""Compile portable A725 preparation with sanitizers; firmware stays outside git."""
from pathlib import Path
import os,subprocess,sys,tempfile
root=Path(__file__).resolve().parents[1]
fw=Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix='a725-prepare-') as d:
 exe=Path(d)/'test'
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer',str(root/'gpu/a725/tests/prepare_test.c'),str(root/'gpu/a725/a725_prepare.c'),str(root/'gpu/a725/upstream/AdrenoFirmware.c'),str(root/'gpu/a725/upstream/ArmSmmu4K.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe),str(fw)],env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'},check=True)
