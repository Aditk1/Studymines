# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend/dist', 'frontend/dist'),
        ('config', 'config'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        # Web & API Framework
        'fastapi',
        'uvicorn',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.lifespan.on',
        'python-multipart',
        'websockets',
        
        # Database
        'sqlalchemy',
        'sqlalchemy.sql.default_comparator',
        'sqlite3',
        'bcrypt',
        'passlib',
        'passlib.handlers.bcrypt',
        'jwt',
        
        # ML / AI / OCR
        'torch',
        'transformers',
        'sentence_transformers',
        'spacy',
        'paddleocr',
        'paddlepaddle',
        'docling',
        'marker',
        'cv2',
        
        # Knowledge Graph & Vector Store
        'networkx',
        'chromadb',
        'cdlib',
        'leidenalg',
        'igraph',
        
        # Document Parsers
        'fitz',  # PyMuPDF
        'docx',
        'pptx',
        
        # Analytics & Metrics
        'matplotlib',
        'seaborn',
        'pandas',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='master_eduRAG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='master_eduRAG_app',
)
