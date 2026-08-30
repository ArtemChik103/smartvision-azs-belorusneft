# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\pvppv\\Desktop\\roo\\neft\\tools\\installer_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\pvppv\\Desktop\\roo\\neft\\dist\\SmartVision-AZS', 'payload')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='SmartVision-AZS-v1.2.0-Setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\pvppv\\Desktop\\roo\\neft\\desktop_icon.ico'],
)
