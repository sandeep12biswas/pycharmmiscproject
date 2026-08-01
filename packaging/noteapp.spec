# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for NoteApp. Build from the project root with:

    pyinstaller packaging/noteapp.spec

`resources/` (styles/icons) is bundled via `datas` and read back at runtime
through app.config.RESOURCES_DIR, which is aware of PyInstaller's frozen
sys._MEIPASS layout -- see app/config.py's _resources_dir()."""

from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).parent  # noqa: F821 -- SPECPATH is injected by PyInstaller
MAIN_SCRIPT = str(PROJECT_ROOT / "main.py")
RESOURCES_DIR = str(PROJECT_ROOT / "resources")
SCHEMA_SQL = str(PROJECT_ROOT / "app" / "db" / "schema.sql")

a = Analysis(  # noqa: F821 -- Analysis/PYZ/EXE/COLLECT are injected by PyInstaller
    [MAIN_SCRIPT],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (RESOURCES_DIR, "resources"),
        # PyInstaller only bundles .py sources into the PYZ archive; a plain
        # data file living next to app/db/migrations.py (which resolves it
        # via Path(__file__).parent / "schema.sql" at runtime) needs its own
        # explicit datas entry or it's silently missing from the frozen build.
        (SCHEMA_SQL, "app/db"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NoteApp",
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

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="NoteApp",
)
