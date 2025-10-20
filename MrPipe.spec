# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=[],
    datas=[
        ('assets/image.png', 'assets'),  # Include splash image
        ('assets/logo.icns', 'assets'),  # Include icns icon
        ('assets/logo.ico', 'assets'),  # Include ico icon
        ('assets/trash.svg', 'assets'),  # Include icone poubelle
        ('assets/start.svg', 'assets'),  # Include icone start
        ('assets/stop.svg', 'assets'),  # Include icone stop
        ('assets/ico.ico', 'assets'),  # Include window icon
        ('assets/animation.mp4', 'assets'),  # Include Hipster Pipe animation video
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtNetwork',
        'PyQt6.QtDBus',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
        'PyQt6.sip',
        'gitlab',
        'gitlab.v4',
        'gitlab.v4.objects',
        'configparser',
        'json',
        'requests',
        'urllib3',
        'certifi',
        'chardet',
        'idna',
        'sip',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
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
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo.icns',  # Use logo.icns as icon
)

app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='Mr. Pipe.app',
    icon='assets/logo.icns',  # Use logo.icns as app icon
    bundle_identifier='com.mrpipe.app',
    version='1.1.0',
    info_plist={
        'CFBundleName': 'Mr. Pipe',
        'CFBundleDisplayName': 'Mr. Pipe',
        'CFBundleIdentifier': 'com.mrpipe.app',
        'CFBundleVersion': '1.1.0',
        'CFBundleShortVersionString': '1.1',
        'NSHumanReadableCopyright': 'Copyright © 2024 Mr. Pipe. All rights reserved.',
        'LSMinimumSystemVersion': '10.12',
        'CFBundleExecutable': 'Mr. Pipe',
    }
)
