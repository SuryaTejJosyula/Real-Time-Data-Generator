# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for Fabric Real-Time Data Generator
# Build with:  python -m PyInstaller fabric_rtdg.spec
#

import sys
from pathlib import Path

ROOT = Path(SPECPATH)   # directory that contains this .spec file

# ── Data files to bundle ────────────────────────────────────────────────────
# Each entry: (source_glob_or_path, destination_folder_inside_bundle)
datas = [
    (str(ROOT / "assets" / "styles" / "dark_theme.qss"),  "assets/styles"),
    (str(ROOT / "assets" / "icons"  / "real_time_intelligence_icon.svg"), "assets/icons"),
]

# ── Hidden imports ──────────────────────────────────────────────────────────
# Modules that PyInstaller's static analysis misses (dynamic imports,
# plugin systems, etc.)
hidden_imports = [
    # PyQt6 / Qt SVG support
    "PyQt6.QtSvg",
    "PyQt6.QtSvgWidgets",
    # qtawesome — loads icon font files at runtime
    "qtawesome",
    "qtawesome.iconic_font",
    # azure-eventhub transport layers
    "azure.eventhub",
    "azure.eventhub._transport",
    "uamqp",
    # Faker locale data
    "faker",
    "faker.providers",
    "faker.providers.address",
    "faker.providers.date_time",
    "faker.providers.misc",
    "faker.providers.person",
    # Our own generators (dynamically imported via importlib)
    "core.generators.retail",
    "core.generators.healthcare",
    "core.generators.finance",
    "core.generators.manufacturing",
    "core.generators.transportation",
    "core.generators.energy",
    "core.generators.telecom",
    "core.generators.smart_city",
]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "unittest", "email", "html", "http",
        "xmlrpc", "ftplib", "pydoc", "doctest",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FabricRTDG",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    # windowed=True → no console window; set to False for debugging
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon= requires a .ico file on Windows; omit to use default Python icon
    # To add a custom icon: convert real_time_intelligence_icon.svg to .ico
    # and set icon="assets/icons/app.ico"
)
