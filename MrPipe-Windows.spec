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
        ('assets/ico.ico', 'assets'),  # Include window icon for Windows
        ('assets/logo.ico', 'assets'),  # Include app icon for Windows
        ('assets/trash.svg', 'assets'),  # Include icone poubelle
        ('assets/start.svg', 'assets'),  # Include icone start
        ('assets/stop.svg', 'assets'),  # Include icone stop
        ('version_info.txt', '.'),  # Include version info
        ('assets/success-1.mp4', 'assets'),  # Include Hipster Pipe success video 1
        ('assets/success-2.mp4', 'assets'),  # Include Hipster Pipe success video 2
        ('assets/success-3.mp4', 'assets'),  # Include Hipster Pipe success video 3
        ('assets/fail.mp4', 'assets'),  # Include Hipster Pipe fail video
        ('assets/etonne.mp4', 'assets'),  # Include Hipster Pipe activation video
        ('assets/about.mp4', 'assets'),  # Include About dialog video
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
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
    icon='assets/logo.ico',  # Use logo.ico as icon for Windows
    version_file='version_info.txt',  # Add version info for Windows
)

# Comment out the macOS bundle for Windows build
# app = BUNDLE(
#     exe,
#     name='Mr. Pipe.app',
#     icon='logo.png',
#     bundle_identifier='com.mrpipe.app',
#     version='1.1.0',
#     info_plist={
#         'CFBundleName': 'Mr. Pipe',
#         'CFBundleDisplayName': 'Mr. Pipe',
#         'CFBundleIdentifier': 'com.mrpipe.app',
#         'CFBundleVersion': '1.1.0',
#         'CFBundleShortVersionString': '1.1',
#         'NSHumanReadableCopyright': 'Copyright © 2024 Mr. Pipe. All rights reserved.',
#         'LSMinimumSystemVersion': '10.12',
#         'CFBundleExecutable': 'Mr. Pipe',
#     }
# )
