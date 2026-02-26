# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all customtkinter assets (themes, fonts, icons)
ctk_datas = collect_data_files('customtkinter')
# Collect all tkintermapview tiles/assets
mapview_datas = collect_data_files('tkintermapview')

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[
        # Bundle the Windows exiftool executable
        (os.path.join('leosetter', 'tools', 'exiftool.exe'), 'leosetter/tools'),
    ],
    datas=[
        # App theme and templates
        (os.path.join('leosetter', 'leosetter_theme.json'), 'leosetter'),
        (os.path.join('leosetter', 'templates'), 'leosetter/templates'),
        # App icons and assets
        (os.path.join('assets', 'LeoSetter.ico'), 'assets'),
        (os.path.join('assets', 'LeoSetter.png'), 'assets'),
        (os.path.join('assets', 'blank.ico'),      'assets'),
        # CustomTkinter bundled assets (fonts, built-in themes, icons)
        *ctk_datas,
        # tkintermapview bundled assets
        *mapview_datas,
    ],
    hiddenimports=[
        'customtkinter',
        'tkintermapview',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'darkdetect',
        'geopy',
        'geopy.geocoders',
        'packaging',       # ctk runtime dep
        'packaging.version',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LeoSetter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                   # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('assets', 'LeoSetter.ico'),
    version='version_info.txt',      # optional: version metadata shown in Explorer
)
