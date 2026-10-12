# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Detectar si existe código ofuscado previamente por PyArmor
SRC_DIR = 'build/obf' if os.path.exists('build/obf/main.py') else '.'
if SRC_DIR != '.' and os.path.abspath(SRC_DIR) not in sys.path:
    sys.path.insert(0, os.path.abspath(SRC_DIR))

# Recolectar datos y temas de CustomTkinter
datas = collect_data_files('customtkinter')
if os.path.exists('mcp_server.py'):
    datas.append(('mcp_server.py', '.'))
if os.path.exists('assets'):
    datas.append(('assets', 'assets'))


# Módulos ocultos requeridos (estándar y terceros para soportar ofuscación)
hiddenimports = [
    'sqlite3',
    'json',
    'csv',
    'calendar',
    'datetime',
    'logging',
    're',
    'shutil',
    'ssl',
    'tempfile',
    'threading',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'urllib',
    'urllib.request',
    'urllib.error',
    'unicodedata',
    'platform',
    'numpy',
    'darkdetect',
    'customtkinter',
    'PIL',
    'PIL._tkinter_finder',
    'matplotlib',
    'matplotlib.backends.backend_tkagg',
]

# Incluir runtime de PyArmor si existe
if os.path.exists(SRC_DIR):
    for item in os.listdir(SRC_DIR):
        if item.startswith('pyarmor_runtime_'):
            hiddenimports.append(item)
            datas.append((os.path.join(SRC_DIR, item), item))

hiddenimports += collect_submodules('ui')
hiddenimports += collect_submodules('database')
hiddenimports += collect_submodules('services')
hiddenimports += collect_submodules('controllers')
hiddenimports += collect_submodules('core')

entry_script = os.path.join(SRC_DIR, 'main.py')

a = Analysis(
    [entry_script],
    pathex=[SRC_DIR, '.'],
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
    name='montu',
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
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
    icon='assets/icon.icns' if sys.platform == 'darwin' and os.path.exists('assets/icon.icns') else ('assets/icon.ico' if os.path.exists('assets/icon.ico') else None),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='montu',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Montu.app',
        icon='assets/icon.icns' if os.path.exists('assets/icon.icns') else None,
        bundle_identifier='com.lauramoreno.montu',
        info_plist={
            'CFBundleName': 'Montu',
            'CFBundleDisplayName': 'Montu',
            'CFBundleGetInfoString': 'Montu - Gestor Financiero Multimoneda creado por Laura Moreno Montoya',
            'CFBundleIdentifier': 'com.lauramoreno.montu',
            'CFBundleVersion': '1.2.1',
            'CFBundleShortVersionString': '1.2.1',
            'NSHumanReadableCopyright': '© 2026 Laura Moreno Montoya. Todos los derechos reservados.',
            'NSHighResolutionCapable': 'True',
        },
    )

