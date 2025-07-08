#!/usr/bin/env python3
"""
アルファ版ビルドスクリプト
Mac/Windows用実行ファイルを生成
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def main():
    """アルファ版ビルドのメイン処理"""

    # プロジェクトルートに移動
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)

    print("🚀 Kumihan-Formatter アルファ版ビルド開始")
    print(f"📁 プロジェクトルート: {project_root}")
    print(f"🖥️  プラットフォーム: {platform.system()}")

    # PyInstallerがインストールされているか確認
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            check=True,
            capture_output=True,
        )
        print("✅ PyInstaller が見つかりました")
    except subprocess.CalledProcessError:
        print("❌ PyInstaller が見つかりません。インストールしています...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"], check=True
        )

    # プラットフォーム別の設定
    system = platform.system()
    if system == "Darwin":  # macOS
        spec_file = "tools/packaging/kumihan_formatter_macos.spec"
        output_name = "Kumihan-Formatter"
    elif system == "Windows":
        spec_file = "tools/packaging/kumihan_formatter.spec"
        output_name = "kumihan_formatter_windows.exe"
    else:
        print(f"❌ 未対応のプラットフォーム: {system}")
        sys.exit(1)

    # ビルド実行
    print(f"🔨 ビルド開始: {spec_file}")
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", spec_file],
            check=True,
        )

        # 出力ファイルの確認
        dist_path = project_root / "dist" / output_name
        if dist_path.exists():
            print(f"✅ ビルド成功: {dist_path}")

            # 実行テスト
            print("🧪 実行テスト中...")
            result = subprocess.run(
                [str(dist_path), "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"✅ 実行テスト成功: {result.stdout.strip()}")
            else:
                print(f"⚠️  実行テストで警告: {result.stderr}")
        else:
            print(f"❌ ビルドファイルが見つかりません: {dist_path}")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"❌ ビルドエラー: {e}")
        sys.exit(1)

    print("🎉 アルファ版ビルド完了")
    print(f"📦 出力ファイル: dist/{output_name}")


if __name__ == "__main__":
    main()
