"""PyInstaller spec file for Kumihan-Formatter Windows GUI
Windows向けexe形式パッケージング設定ファイル

Usage: pyinstaller kumihan_formatter.spec
"""

import os
import sys
from pathlib import Path

# Get the directory containing this spec file
SPEC_DIR = Path(SPECPATH)
ROOT_DIR = SPEC_DIR.parent.parent  # Navigate to project root

# Define application metadata
APP_NAME = 'Kumihan-Formatter'
APP_VERSION = '1.0.0'
APP_DESCRIPTION = 'Kumihan-Formatter - 美しい組版を、誰でも簡単に'
APP_COPYRIGHT = 'Copyright © 2025 mo9mo9-uwu-mo9mo9'

# Entry point
ENTRY_POINT = str(ROOT_DIR / 'kumihan_formatter' / 'gui_launcher.py')

# Data files and directories to include
datas = [
    # Templates directory
    (str(ROOT_DIR / 'kumihan_formatter' / 'templates'), 'kumihan_formatter/templates'),
    # Examples directory (for sample generation)
    (str(ROOT_DIR / 'examples'), 'examples'),
    # Dev tools (for test file generation)
    (str(ROOT_DIR / 'dev' / 'tools'), 'dev/tools'),
    # Configuration files
    (str(ROOT_DIR / 'pyproject.toml'), '.'),
]

# Hidden imports (modules that PyInstaller might miss)
hiddenimports = [
    'kumihan_formatter',
    'kumihan_formatter.cli',
    'kumihan_formatter.gui_launcher',
    'kumihan_formatter.commands',
    'kumihan_formatter.commands.convert',
    'kumihan_formatter.commands.convert.convert_command',
    'kumihan_formatter.commands.sample',
    'kumihan_formatter.commands.check_syntax',
    'kumihan_formatter.core',
    'kumihan_formatter.core.config',
    'kumihan_formatter.core.config.config_manager',
    'kumihan_formatter.core.rendering',
    'kumihan_formatter.core.utilities',
    'kumihan_formatter.core.validators',
    'kumihan_formatter.core.error_handling',
    'kumihan_formatter.ui',
    'kumihan_formatter.ui.console_ui',
    'kumihan_formatter.parser',
    'kumihan_formatter.renderer',
    'kumihan_formatter.sample_content',
    'jinja2',
    'jinja2.ext',
    'click',
    'rich',
    'rich.console',
    'rich.progress',
    'rich.table',
    'watchdog',
    'pyyaml',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'webbrowser',
    'threading',
    'pathlib',
    'datetime',
    'json',
    'yaml',
    'html',
    'xml',
    'xml.etree',
    'xml.etree.ElementTree',
]

# Exclude unnecessary modules to reduce size
excludes = [
    'test',
    'tests',
    'pytest',
    'unittest',
    'doctest',
    'pdb',
    'profile',
    'cProfile',
    'pstats',
    'trace',
    'tracemalloc',
    'turtle',
    'tkinter.test',
    'idlelib',
    'lib2to3',
    'distutils',
    'setuptools',
    'pip',
    'wheel',
    'black',
    'isort',
    'flake8',
    'pylint',
    'mypy',
]

# Analysis configuration
a = Analysis(
    [ENTRY_POINT],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries and optimize
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Windows executable configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress executable
    upx_exclude=[],
    console=False,  # No console window (GUI only)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-specific options
    version='version_info.txt',  # We'll create this separately
    icon=str(ROOT_DIR / 'kumihan_formatter' / 'assets' / 'icon.ico') if (ROOT_DIR / 'kumihan_formatter' / 'assets' / 'icon.ico').exists() else None,  # Add icon file path if available
    # Manifest options
    manifest=None,
    # Additional Windows options
    uac_admin=False,
    uac_uiaccess=False,
)

# Optional: Create Windows installer (uncomment if needed)
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name=APP_NAME
# )
