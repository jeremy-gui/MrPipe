#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Configuration for PyInstaller
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(Path(__file__).parent)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'gitlab',
        'configparser',
        'json',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Mr. Pipe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window
    icon=None,  # Can add icon later
)

app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='Mr. Pipe.app',
    icon=None,
    bundle_identifier='com.mrpipe.app',
    version='1.1.0',
    info_plist={
        'CFBundleName': 'Mr. Pipe',
        'CFBundleDisplayName': 'Mr. Pipe',
        'CFBundleIdentifier': 'com.mrpipe.app',
        'CFBundleVersion': '1.1.0',
        'CFBundleShortVersionString': '1.1',
        'NSHumanReadableCopyright': 'Copyright © 2024 Mr. Pipe. All rights reserved.',
    }
)
