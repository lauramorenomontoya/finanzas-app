# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Recolectar datos y temas de CustomTkinter
datas = collect_data_files('customtkinter')

# Módulos ocultos requeridos
hiddenimports = [
    'customtkinter',
    'PIL',
    'PIL._tkinter_finder',
    'matplotlib',
    'matplotlib.backends.backend_tkagg',
]
hiddenimports += collect_submodules('ui')
hiddenimports += collect_submodules('database')
hiddenimports += collect_submodules('services')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tests'],
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
    name='ControlFinanciero',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ControlFinanciero',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='ControlFinanciero.app',
        icon=None,
        bundle_identifier='com.controlfinanciero.app',
        info_plist={
            'CFBundleName': 'Control Financiero',
            'CFBundleDisplayName': 'Control Financiero',
            'CFBundleGetInfoString': 'Gestor Financiero Multimoneda',
            'CFBundleIdentifier': 'com.controlfinanciero.app',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': 'True',
        },
    )
