# -*- mode: python ; coding: utf-8 -*-

import os

def recursive_datas(source_folder, target_folder):
    file_list = []
    for root, dirs, files in os.walk(source_folder):
        for f in files:
            full_src = os.path.join(root, f)
            rel_path = os.path.relpath(full_src, source_folder)
            # The tuple is (file_on_disk, folder_in_dist)
            file_list.append((full_src, os.path.join(target_folder, os.path.dirname(rel_path))))
    return file_list

block_cipher = None

datas = []
datas += recursive_datas('resources', 'resources')
datas += recursive_datas('fonts', 'fonts')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
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
    name='Labels_Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True if you want a console
    icon='icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Labels_Tool_3'
)
