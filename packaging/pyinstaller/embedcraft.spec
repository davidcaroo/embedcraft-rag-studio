# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for EmbedCraft RAG Studio.

Builds two executables in --onedir mode:
1. EmbedCraft.exe (windowed GUI application)
2. embedcraft.exe (console CLI application)
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

project_root = Path.cwd().resolve()
src_dir = project_root / "src"

# Collect all dynamic imports and data packages
hidden_imports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "sqlite3",
    "sqlalchemy.dialects.sqlite",
    "pydantic",
    "typer",
    "rich",
    "structlog",
    "keyring",
    "keyring.backends.Windows",
    "pyarrow",
    "pyarrow.parquet",
    "yaml",
    "fitz",  # PyMuPDF
    "docx",
    "pptx",
    "openpyxl",
    "bs4",
    "lancedb",
] + collect_submodules("embedcraft")

datas = [
    (str(src_dir / "embedcraft" / "gui" / "styles.py"), "embedcraft/gui"),
    (str(src_dir / "embedcraft" / "gui" / "theme.py"), "embedcraft/gui"),
]

# 1. Analysis for GUI Application
a_gui = Analysis(
    [str(src_dir / "embedcraft" / "gui" / "app.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_gui = PYZ(a_gui.pure, a_gui.zipped_data, cipher=block_cipher)

exe_gui = EXE(
    pyz_gui,
    a_gui.scripts,
    [],
    exclude_binaries=True,
    name="EmbedCraft",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # Windowed GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 2. Analysis for CLI Application
a_cli = Analysis(
    [str(src_dir / "embedcraft" / "cli" / "app.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_cli = PYZ(a_cli.pure, a_cli.zipped_data, cipher=block_cipher)

exe_cli = EXE(
    pyz_cli,
    a_cli.scripts,
    [],
    exclude_binaries=True,
    name="embedcraft",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # Console CLI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 3. Unified Distribution Directory
coll = COLLECT(
    exe_gui,
    a_gui.binaries,
    a_gui.zipfiles,
    a_gui.datas,
    exe_cli,
    a_cli.binaries,
    a_cli.zipfiles,
    a_cli.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="EmbedCraft-Studio",
)
