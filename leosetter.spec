# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# ── CustomTkinter: data files + all submodules (themes, fonts, lazy loaders) ──
ctk_datas,    ctk_binaries,    ctk_hiddenimports    = collect_all('customtkinter')
# ── tkintermapview: map tiles cache + submodules ──────────────────────────────
mapview_datas, mapview_binaries, mapview_hiddenimports = collect_all('tkintermapview')
# ── Pillow: collect all DLL / extension modules ───────────────────────────────
pil_datas,    pil_binaries,    pil_hiddenimports    = collect_all('PIL')

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[
        # ── Bundled ExifTool executable ────────────────────────────────────────
        (os.path.join('leosetter', 'tools', 'exiftool.exe'),  'leosetter/tools'),
        # ── ExifTool Perl libraries (the exiftool_files folder) ───────────────
        (os.path.join('leosetter', 'tools', 'exiftool_files'), 'leosetter/tools/exiftool_files'),
        *ctk_binaries,
        *mapview_binaries,
        *pil_binaries,
    ],
    datas=[
        # ── App theme ─────────────────────────────────────────────────────────
        (os.path.join('leosetter', 'leosetter_theme.json'), 'leosetter'),
        # ── Templates folder ──────────────────────────────────────────────────
        (os.path.join('leosetter', 'templates'),            'leosetter/templates'),
        # ── Default settings ──────────────────────────────────────────────────
        (os.path.join('leosetter', 'settings.json'),        'leosetter'),
        # ── App icons and assets ──────────────────────────────────────────────
        (os.path.join('assets', 'LeoSetter.ico'),  'assets'),
        (os.path.join('assets', 'LeoSetter.png'),  'assets'),
        (os.path.join('assets', 'blank.ico'),       'assets'),
        # ── Third-party bundled assets ────────────────────────────────────────
        *ctk_datas,
        *mapview_datas,
        *pil_datas,
    ],
    hiddenimports=[
        # ── CustomTkinter ──────────────────────────────────────────────────────
        *ctk_hiddenimports,
        # ── tkintermapview ─────────────────────────────────────────────────────
        *mapview_hiddenimports,
        # ── Pillow ─────────────────────────────────────────────────────────────
        *pil_hiddenimports,
        # ── Other runtime deps ─────────────────────────────────────────────────
        'darkdetect',
        'geopy',
        'geopy.geocoders',
        'geopy.geocoders.nominatim',
        'packaging',
        'packaging.version',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.simpledialog',
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
    console=False,                    # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('assets', 'LeoSetter.ico'),
    version='version_info.txt',       # Explorer version metadata
)
