# -*- mode: python ; coding: utf-8 -*-
import os # <-- Add this

block_cipher = None
project_root = os.path.dirname(SPEC) # <-- Get the directory containing this spec file

a = Analysis(
    ['main.py'], # Ensure this points to main.py
    pathex=[project_root], # <-- Explicitly add the project root directory
    binaries=[],
    datas=[
        ('database/database.db', 'database'),
        ('assets', 'assets')
    ],
    hiddenimports=[], # <-- See Step 4 if needed
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
# ... (rest of your spec file - PYZ, EXE, BUNDLE sections) ...

# Make sure the EXE and BUNDLE sections are configured correctly as before
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OurMoney',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo_icon.icns',
)
app = BUNDLE(
    exe,
    name='OurMoney.app',
    icon='assets/logo_icon.icns',
    bundle_identifier=None,
)