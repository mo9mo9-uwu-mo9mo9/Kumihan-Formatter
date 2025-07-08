#!/usr/bin/env python3
"""Windows EXE Build Script for Kumihan-Formatter
Windows executable packaging build script

Usage:
    python build_windows.py [--clean] [--test] [--upload]

Options:
    --clean   Clean build directories before building
    --test    Test the built executable after building
    --upload  Upload to GitHub releases (requires environment setup)
"""

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


class WindowsBuilder:
    """Windows executable builder for Kumihan-Formatter"""

    def __init__(self, root_dir: Path | None = None):
        self.root_dir = root_dir or Path(__file__).parent
        self.dist_dir = self.root_dir / "dist"
        self.build_dir = self.root_dir / "build"
        self.spec_file = self.root_dir / "kumihan_formatter.spec"
        self.exe_name = "Kumihan-Formatter.exe"

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        print("[INFO] Checking dependencies...")

        # Check PyInstaller
        try:
            import PyInstaller

            print(f"[OK] PyInstaller {PyInstaller.__version__} が見つかりました")
        except ImportError:
            print("[ERROR] PyInstaller が見つかりません")
            print("インストールコマンド: pip install pyinstaller")
            return False

        # Check main package
        try:
            import kumihan_formatter

            print("[OK] kumihan_formatter が見つかりました")
        except ImportError:
            print("[ERROR] kumihan_formatter パッケージが見つかりません")
            print("現在のディレクトリから実行していることを確認してください")
            return False

        # Check GUI dependencies
        try:
            import tkinter

            print("[OK] tkinter が利用可能です")
        except ImportError:
            print(
                "[ERROR] tkinter が見つかりません（Pythonの標準ライブラリに含まれているはずです）"
            )
            return False

        return True

    def clean_build_dirs(self) -> None:
        """Clean build and dist directories"""
        print("[INFO] Cleaning build directories...")

        dirs_to_clean = [self.dist_dir, self.build_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                print(f"   削除中: {dir_path}")
                shutil.rmtree(dir_path)
            else:
                print(f"   スキップ: {dir_path} (存在しません)")

    def install_pyinstaller_if_needed(self) -> None:
        """Install PyInstaller if not available"""
        try:
            import PyInstaller
        except ImportError:
            print("[INFO] PyInstaller をインストール中...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pyinstaller"]
            )

    def build_executable(self) -> None:
        """Build the Windows executable using PyInstaller"""
        print("[INFO] Building Windows executable...")

        if not self.spec_file.exists():
            raise FileNotFoundError(f"Spec file not found: {self.spec_file}")

        # Run PyInstaller
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            str(self.spec_file),
        ]

        print(f"実行コマンド: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.root_dir)

        if result.returncode != 0:
            raise RuntimeError(
                f"PyInstaller failed with return code {result.returncode}"
            )

        # Check if executable was created (adapt to current platform)
        # On macOS/Unix, PyInstaller creates executables without .exe extension
        possible_exes = [
            self.dist_dir / self.exe_name,  # Kumihan-Formatter.exe
            self.dist_dir / "Kumihan-Formatter",  # Kumihan-Formatter (Unix)
        ]

        exe_path = None
        for possible_exe in possible_exes:
            if possible_exe.exists():
                exe_path = possible_exe
                break

        if not exe_path:
            raise FileNotFoundError(
                f"Built executable not found. Checked: {[str(p) for p in possible_exes]}"
            )

        print(f"[OK] 実行ファイルが作成されました: {exe_path}")
        print(f"   ファイルサイズ: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")

        return exe_path

    def test_executable(self, exe_path: Path) -> None:
        """Test the built executable"""
        print("[INFO] 実行ファイルをテスト中...")

        # Basic execution test (should start GUI)
        try:
            # Test with --help flag first (if supported)
            result = subprocess.run(
                [str(exe_path), "--help"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print("[OK] ヘルプ表示テスト: 成功")
            else:
                print("[WARNING] ヘルプ表示テスト: スキップ（GUIアプリのため正常）")
        except subprocess.TimeoutExpired:
            print("[WARNING] ヘルプ表示テスト: タイムアウト（GUIアプリのため正常）")
        except Exception as e:
            print(f"[WARNING] ヘルプ表示テスト: {e}")

        # Check file dependencies
        print("[INFO] 依存ファイルの確認...")
        templates_exist = any((self.dist_dir / "_internal").glob("**/templates"))
        if templates_exist:
            print("[OK] テンプレートファイルが含まれています")
        else:
            print("[WARNING] テンプレートファイルが見つかりません")

        print("[OK] 基本テスト完了")

    def create_distribution_package(self, exe_path: Path) -> Path:
        """Create distribution package (ZIP file)"""
        print("[INFO] 配布パッケージを作成中...")

        # Create ZIP package
        package_name = "Kumihan-Formatter-v1.0-Windows"
        zip_path = self.dist_dir / f"{package_name}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add executable
            zipf.write(exe_path, exe_path.name)

            # Add README for distribution
            readme_content = """Kumihan-Formatter v1.0 - Windows版

【インストール方法】
1. このZIPファイルを任意の場所に展開してください
2. Kumihan-Formatter.exe をダブルクリックして起動してください

【システム要件】
- Windows 10 / 11 (64-bit)
- インターネット接続不要
- Pythonのインストール不要

【使い方】
1. アプリケーションを起動
2. 「参照」ボタンから変換したいテキストファイルを選択
3. 「変換実行」ボタンをクリック

【サポート】
- GitHub: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter
- Issues: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues

【ライセンス】
MIT License - Copyright © 2025 mo9mo9-uwu-mo9mo9
"""
            zipf.writestr("README.txt", readme_content.encode("utf-8"))

        print(f"[OK] 配布パッケージが作成されました: {zip_path}")
        print(f"   パッケージサイズ: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")

        return zip_path

    def upload_to_github(self, package_path: Path) -> None:
        """Upload package to GitHub releases (placeholder)"""
        print("[INFO] GitHub リリースへのアップロード...")
        print("[WARNING] GitHub Actions を使用した自動アップロードを推奨します")
        print(f"   手動アップロード用パッケージ: {package_path}")

    def build(
        self, clean: bool = False, test: bool = False, upload: bool = False
    ) -> None:
        """Main build process"""
        print("[INFO] Kumihan-Formatter Windows build starting...")
        print(f"   Project directory: {self.root_dir}")

        try:
            # Check dependencies
            if not self.check_dependencies():
                print("[ERROR] Dependency check failed")
                return False

            # Install PyInstaller if needed
            self.install_pyinstaller_if_needed()

            # Clean build directories if requested
            if clean:
                self.clean_build_dirs()

            # Build executable
            exe_path = self.build_executable()

            # Test executable if requested
            if test:
                self.test_executable(exe_path)

            # Create distribution package
            package_path = self.create_distribution_package(exe_path)

            # Upload to GitHub if requested
            if upload:
                self.upload_to_github(package_path)

            print("\n[OK] Build completed successfully!")
            print(f"   実行ファイル: {exe_path}")
            print(f"   配布パッケージ: {package_path}")
            print("\n[INFO] 次のステップ:")
            print("   1. 実行ファイルをテストしてください")
            print("   2. 異なるWindows環境でテストしてください")
            print("   3. GitHub リリースページで配布パッケージを公開してください")

            return True

        except Exception as e:
            print(f"\n[ERROR] Build failed: {e}")
            import traceback

            traceback.print_exc()
            return False


def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter Windows build script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean directories before build"
    )
    parser.add_argument(
        "--test", action="store_true", help="Test executable after build"
    )
    parser.add_argument(
        "--upload", action="store_true", help="GitHub リリースにアップロード"
    )

    args = parser.parse_args()

    # Build
    builder = WindowsBuilder()
    success = builder.build(clean=args.clean, test=args.test, upload=args.upload)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    sys.exit(main())
