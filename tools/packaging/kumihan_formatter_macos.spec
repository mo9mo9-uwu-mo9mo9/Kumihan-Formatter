"""PyInstaller spec file for Kumihan-Formatter macOS App
macOS向け.app形式パッケージング設定ファイル

Usage: pyinstaller kumihan_formatter_macos.spec
"""

import os
import sys
from pathlib import Path

# Get the directory containing this spec file
SPEC_DIR = Path(SPECPATH)
ROOT_DIR = SPEC_DIR

# Define application metadata
APP_NAME = 'Kumihan-Formatter'
APP_VERSION = '1.0.0'
APP_DESCRIPTION = 'Kumihan-Formatter - 美しい組版を、誰でも簡単に'
APP_COPYRIGHT = 'Copyright © 2025 mo9mo9-uwu-mo9mo9'
APP_IDENTIFIER = 'com.mo9mo9.kumihan-formatter'

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

# macOS executable configuration
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress executable
    console=False,  # No console window (GUI only)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Collect all files for the app bundle
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

# macOS App Bundle configuration
app = BUNDLE(
    coll,
    name=f'{APP_NAME}.app',
    icon=str(ROOT_DIR / 'kumihan_formatter' / 'assets' / 'icon.icns') if (ROOT_DIR / 'kumihan_formatter' / 'assets' / 'icon.icns').exists() else None,  # Add icon file path if available (*.icns)
    bundle_identifier=APP_IDENTIFIER,
    version=APP_VERSION,
    info_plist={
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleIdentifier': APP_IDENTIFIER,
        'CFBundleVersion': APP_VERSION,
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundleExecutable': APP_NAME,
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'KMHN',
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.15.0',
        'LSApplicationCategoryType': 'public.app-category.productivity',
        'NSDocumentTypes': [
            {
                'CFBundleTypeExtensions': ['txt', 'md'],
                'CFBundleTypeName': 'Text Document',
                'CFBundleTypeRole': 'Editor',
                'NSDocumentClass': 'Document',
            }
        ],
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeExtensions': ['txt', 'md'],
                'CFBundleTypeName': 'Text Document',
                'CFBundleTypeRole': 'Editor',
                'LSHandlerRank': 'Alternate',
            }
        ],
        'NSHumanReadableCopyright': APP_COPYRIGHT,
        'LSEnvironment': {
            'LC_CTYPE': 'UTF-8',
        },
        # Privacy permissions (if needed)
        'NSDesktopFolderUsageDescription': 'This app needs access to save formatted documents.',
        'NSDocumentsFolderUsageDescription': 'This app needs access to read and save documents.',
        'NSDownloadsFolderUsageDescription': 'This app needs access to save formatted documents.',
    },
)
