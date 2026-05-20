# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\projects\\eduRAG\\master_eduRAG\\run_server.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\projects\\eduRAG\\master_eduRAG\\frontend\\dist', 'frontend/dist'), ('D:\\projects\\eduRAG\\master_eduRAG\\app', 'app'), ('D:\\projects\\eduRAG\\master_eduRAG\\config', 'config'), ('D:\\projects\\eduRAG\\master_eduRAG\\src', 'src')],
    hiddenimports=['uvicorn', 'fastapi', 'pydantic', 'sqlalchemy', 'networkx', 'cv2', 'pymupdf', 'passlib.handlers.bcrypt', 'multipart', 'websockets'],
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
    name='master_eduRAG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
