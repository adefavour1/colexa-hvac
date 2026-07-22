# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for COLEXA_HVAC.exe

Build with:
    pyinstaller COLEXA_HVAC.spec

Note: PyInstaller packages the Python interpreter and Streamlit runtime.
The resulting executable launches a local Streamlit server and opens the
default browser to it - it does not use any internet/cloud service.
"""

import os
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

datas = []
binaries = []
hiddenimports = []

for package in ["streamlit", "plotly", "openpyxl", "reportlab", "pandas", "PIL"]:
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

# Bundle application resources
datas += [
    ("assets", "assets"),
    ("pages", "pages"),
    ("utils", "utils"),
    ("database", "database"),
]

a = Analysis(
    ["run_colexa.py"],
    pathex=[os.path.abspath(".")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="COLEXA_HVAC",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=None,
)
