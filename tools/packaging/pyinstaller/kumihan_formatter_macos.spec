# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Kumihan Formatter macOS .app
"""
import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリ
ROOT_DIR = Path(SPECPATH).parent
SRC_DIR = ROOT_DIR / "kumihan_formatter"
TEMPLATES_DIR = SRC_DIR / "templates"

block_cipher = None

# Analysis - ソースコードとデータファイルの分析
a = Analysis(
    [str(SRC_DIR / 'gui_launcher.py')],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=[
        # テンプレートファイルを含める
        (str(TEMPLATES_DIR), 'kumihan_formatter/templates'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.font',
        '_tkinter',
        'kumihan_formatter.core',
        'kumihan_formatter.config',
        'kumihan_formatter.core.config.config_loader',
        'kumihan_formatter.commands.convert.convert_processor',
        'kumihan_formatter.utils',
        'jinja2',
        'markupsafe',
        'logging.config',
        'json',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PyQt5',
        'PyQt6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ - Pythonモジュールのアーカイブ
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# EXE - 実行ファイルの作成
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Kumihan Formatter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUIアプリケーションなのでコンソールなし
    disable_windowed_traceback=False,
    argv_emulation=True,  # macOSでのドラッグ&ドロップ対応
    target_arch=None,  # 現在のアーキテクチャでビルド
    codesign_identity=None,
    entitlements_file=None,
)

# COLLECT - 依存ファイルの収集
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Kumihan Formatter'
)

# BUNDLE - macOS .appバンドルの作成
app = BUNDLE(
    coll,
    name='Kumihan Formatter.app',
    icon=str(ROOT_DIR / 'assets' / 'icon.icns') if (ROOT_DIR / 'assets' / 'icon.icns').exists() else None,
    bundle_identifier='com.kumihan.formatter',
    info_plist={
        'CFBundleName': 'Kumihan Formatter',
        'CFBundleDisplayName': 'Kumihan Formatter',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleIdentifier': 'com.kumihan.formatter',
        'CFBundleExecutable': 'Kumihan Formatter',
        'CFBundleIconFile': 'icon.icns',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'KMHN',
        'LSMinimumSystemVersion': '10.13.0',
        'LSApplicationCategoryType': 'public.app-category.productivity',
        'NSHighResolutionCapable': True,
        'NSSupportsAutomaticGraphicsSwitching': True,
        'NSHumanReadableCopyright': 'Copyright © 2024 Kumihan Formatter',
        'NSRequiresAquaSystemAppearance': False,  # ダークモード対応
        # ドキュメントタイプの登録
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Text Document',
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeExtensions': ['txt'],
                'LSItemContentTypes': ['public.plain-text'],
            }
        ],
        # ファイルドロップ対応
        'NSServices': [
            {
                'NSMenuItem': {
                    'default': 'Convert with Kumihan Formatter'
                },
                'NSMessage': 'convertFiles',
                'NSPortName': 'Kumihan Formatter',
                'NSSendTypes': ['NSFilenamesPboardType'],
            }
        ],
    },
)
