#!/usr/bin/env python3
"""macOS App Build Script for Kumihan-Formatter
macOS向け.app形式パッケージング用ビルドスクリプト

Usage:
    python build_macos.py [--clean] [--test] [--sign] [--notarize]

Options:
    --clean      Clean build directories before building
    --test       Test the built app after building
    --sign       Sign the app bundle (requires developer certificate)
    --notarize   Notarize the app bundle (requires Apple ID setup)
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


class MacOSBuilder:
    """macOS App builder for Kumihan-Formatter"""

    def __init__(self, root_dir: Path | None = None):
        self.root_dir = root_dir or Path(__file__).parent
        self.dist_dir = self.root_dir / "dist"
        self.build_dir = self.root_dir / "build"
        self.spec_file = self.root_dir / "kumihan_formatter_macos.spec"
        self.app_name = "Kumihan-Formatter.app"
        self.app_path = self.dist_dir / self.app_name

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        print("📋 依存関係をチェック中...")

        # Check PyInstaller
        try:
            import PyInstaller

            print(f"✅ PyInstaller {PyInstaller.__version__} が見つかりました")
        except ImportError:
            print("❌ PyInstaller が見つかりません")
            print("インストールコマンド: pip install pyinstaller")
            return False

        # Check main package
        try:
            import kumihan_formatter

            print(f"✅ kumihan_formatter が見つかりました")
        except ImportError:
            print("❌ kumihan_formatter パッケージが見つかりません")
            print("現在のディレクトリから実行していることを確認してください")
            return False

        # Check GUI dependencies
        try:
            import tkinter

            print("✅ tkinter が利用可能です")
        except ImportError:
            print("❌ tkinter が見つかりません")
            return False

        # Check macOS specific tools
        if sys.platform == "darwin":
            print("✅ macOS プラットフォームを確認しました")
        else:
            print("⚠️  macOS以外のプラットフォームです")

        return True

    def clean_build_dirs(self) -> None:
        """Clean build and dist directories"""
        print("🧹 ビルドディレクトリをクリーンアップ中...")

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
            print("📦 PyInstaller をインストール中...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pyinstaller"]
            )

    def build_app(self) -> Path:
        """Build the macOS app using PyInstaller"""
        print("🔨 macOS Appをビルド中...")

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

        # Check if app was created
        if not self.app_path.exists():
            raise FileNotFoundError(f"Built app not found: {self.app_path}")

        print(f"✅ Appバンドルが作成されました: {self.app_path}")

        # Calculate app size
        app_size = self._get_directory_size(self.app_path)
        print(f"   アプリサイズ: {app_size / 1024 / 1024:.1f} MB")

        return self.app_path

    def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory"""
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = Path(dirpath) / filename
                if file_path.exists():
                    total += file_path.stat().st_size
        return total

    def sign_app(self, app_path: Path, identity: str | None = None) -> None:
        """Sign the app bundle"""
        print("🔏 Appバンドルに署名中...")

        if not identity:
            # Try to find available signing identities
            result = subprocess.run(
                ["security", "find-identity", "-v", "-p", "codesigning"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout:
                print("利用可能な署名アイデンティティ:")
                print(result.stdout)
                print(
                    "⚠️  署名するには--signオプションでアイデンティティを指定してください"
                )
                return
            else:
                print("❌ 署名アイデンティティが見つかりません")
                print("開発者アカウントでの署名が必要です")
                return

        # Sign the app
        cmd = [
            "codesign",
            "--deep",
            "--force",
            "--verify",
            "--verbose",
            "--sign",
            identity,
            str(app_path),
        ]

        print(f"署名コマンド: {' '.join(cmd)}")
        result = subprocess.run(cmd)

        if result.returncode == 0:
            print("✅ 署名が完了しました")
        else:
            print("❌ 署名に失敗しました")
            raise RuntimeError(
                f"Code signing failed with return code {result.returncode}"
            )

    def notarize_app(self, app_path: Path) -> None:
        """Notarize the app bundle"""
        print("🔐 Appバンドルをnotarization中...")
        print("⚠️  notarizationにはApple IDの設定が必要です")
        print(
            "詳細: https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution"
        )

        # This would require Apple ID credentials and is beyond basic setup
        print("🏗️  手動でnotarizationを実行してください:")
        print(
            f"   1. アプリをZIPに圧縮: ditto -c -k --keepParent {app_path} {app_path.name}.zip"
        )
        print(
            f"   2. notarizationを実行: xcrun notarytool submit {app_path.name}.zip --apple-id YOUR_APPLE_ID --password YOUR_APP_PASSWORD --team-id YOUR_TEAM_ID --wait"
        )

    def test_app(self, app_path: Path) -> None:
        """Test the built app"""
        print("🧪 Appバンドルをテスト中...")

        # Check app bundle structure
        executable_path = app_path / "Contents" / "MacOS" / "Kumihan-Formatter"
        if executable_path.exists():
            print("✅ 実行ファイルが見つかりました")
        else:
            print("❌ 実行ファイルが見つかりません")

        # Check Info.plist
        info_plist_path = app_path / "Contents" / "Info.plist"
        if info_plist_path.exists():
            print("✅ Info.plistが見つかりました")
        else:
            print("❌ Info.plistが見つかりません")

        # Check Resources directory
        resources_path = app_path / "Contents" / "Resources"
        if resources_path.exists():
            print("✅ Resourcesディレクトリが見つかりました")
        else:
            print("❌ Resourcesディレクトリが見つかりません")

        # Basic execution test
        try:
            # Try to get app info
            result = subprocess.run(
                ["mdls", "-name", "kMDItemDisplayName", str(app_path)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print("✅ アプリケーション情報を取得できました")
            else:
                print("⚠️  アプリケーション情報の取得に失敗しました")
        except Exception as e:
            print(f"⚠️  テスト中にエラーが発生しました: {e}")

        print("✅ 基本テスト完了")

    def create_distribution_package(self, app_path: Path) -> Path:
        """Create distribution package (DMG or ZIP)"""
        print("📦 配布パッケージを作成中...")

        # Create ZIP package for simple distribution
        package_name = f"Kumihan-Formatter-v1.0-macOS"
        zip_path = self.dist_dir / f"{package_name}.zip"

        print(f"ZIPパッケージを作成中: {zip_path}")

        # Create ZIP using ditto (preserves resource forks and extended attributes)
        cmd = ["ditto", "-c", "-k", "--keepParent", str(app_path), str(zip_path)]

        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise RuntimeError(
                f"ZIP creation failed with return code {result.returncode}"
            )

        # Create installation instructions
        readme_content = """Kumihan-Formatter v1.0 - macOS版

【インストール方法】
1. このZIPファイルをダウンロードして展開してください
2. Kumihan-Formatter.appを「アプリケーション」フォルダにドラッグ&ドロップしてください
3. 初回起動時に「開発元を確認できません」と表示される場合：
   - アプリを右クリック → 「開く」を選択
   - または システム環境設定 → セキュリティとプライバシー → 「このまま開く」

【システム要件】
- macOS 10.15 (Catalina) 以降
- Intel/Apple Silicon Mac 対応
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

        readme_path = self.dist_dir / "README.txt"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        zip_size = zip_path.stat().st_size
        print(f"✅ 配布パッケージが作成されました: {zip_path}")
        print(f"   パッケージサイズ: {zip_size / 1024 / 1024:.1f} MB")

        return zip_path

    def build(
        self,
        clean: bool = False,
        test: bool = False,
        sign: bool = False,
        notarize: bool = False,
        sign_identity: str | None = None,
    ) -> bool:
        """Main build process"""
        print("🏗️  Kumihan-Formatter macOS版ビルドを開始します...")
        print(f"   プロジェクトディレクトリ: {self.root_dir}")

        try:
            # Check dependencies
            if not self.check_dependencies():
                print("❌ 依存関係のチェックに失敗しました")
                return False

            # Install PyInstaller if needed
            self.install_pyinstaller_if_needed()

            # Clean build directories if requested
            if clean:
                self.clean_build_dirs()

            # Build app
            app_path = self.build_app()

            # Sign app if requested
            if sign:
                self.sign_app(app_path, sign_identity)

            # Notarize app if requested
            if notarize:
                self.notarize_app(app_path)

            # Test app if requested
            if test:
                self.test_app(app_path)

            # Create distribution package
            package_path = self.create_distribution_package(app_path)

            print("\n✅ ビルドが完了しました！")
            print(f"   Appバンドル: {app_path}")
            print(f"   配布パッケージ: {package_path}")
            print("\n📋 次のステップ:")
            print("   1. Appバンドルをテストしてください")
            print("   2. 異なるmacOSバージョンでテストしてください")
            print("   3. 必要に応じて署名・notarizationを実行してください")
            print("   4. GitHub リリースページで配布パッケージを公開してください")

            return True

        except Exception as e:
            print(f"\n❌ ビルドに失敗しました: {e}")
            import traceback

            traceback.print_exc()
            return False


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter macOS版ビルドスクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--clean", action="store_true", help="ビルド前にディレクトリをクリーンアップ"
    )
    parser.add_argument(
        "--test", action="store_true", help="ビルド後にAppバンドルをテスト"
    )
    parser.add_argument("--sign", action="store_true", help="Appバンドルに署名")
    parser.add_argument(
        "--notarize", action="store_true", help="Appバンドルをnotarization"
    )
    parser.add_argument("--sign-identity", help="署名に使用するアイデンティティ")

    args = parser.parse_args()

    # Build
    builder = MacOSBuilder()
    success = builder.build(
        clean=args.clean,
        test=args.test,
        sign=args.sign,
        notarize=args.notarize,
        sign_identity=args.sign_identity,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
