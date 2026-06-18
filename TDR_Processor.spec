# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

datas = [
    ('dashboard_api.py', '.'),
    ('dashboard.html', '.'),
    ('locales.json', '.'),
    ('assets', 'assets'),
    ('tdr_dashboard.pbix', '.'),
]
datas += collect_data_files('tkinterdnd2')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'dashboard_api',
        'watchdog',
        'watchdog.events',
        'watchdog.observers',
        'utils.watcher',
        'schedule',
        'ttkbootstrap',
        'keyring',
        'keyring.backends.Windows',
        'pystray',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'tkinterdnd2',
        'plyer',
        'plyer.platforms.win.notification',
        'pythonjsonlogger',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'streamlit',
        'plotly',
        'scipy',
    ],
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
    name='TDR_Processor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
