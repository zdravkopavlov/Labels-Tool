# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

# Set paths relative to this spec file's location
project_dir = os.getcwd()

a = Analysis(
    ['New_Editor_MOCKUP4.py'],
    pathex=[project_dir],
    binaries=[],
    datas=[
        (os.path.join('fonts', '*'), 'fonts'),
        (os.path.join('resources', '*'), 'resources'),
    ],
    hiddenimports=[],
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
    name='LabelEditor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # True for debug console, False for GUI only
    icon=None  # You can specify an .ico file here if you want a custom app icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LabelEditor'
)
