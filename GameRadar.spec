# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

build_support = str(Path.cwd() / 'build_support')
pythonpath = os.environ.get('PYTHONPATH')
os.environ['PYTHONPATH'] = build_support if not pythonpath else build_support + os.pathsep + pythonpath


a = Analysis(
    ['src\\game_radar\\app.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GameRadar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
