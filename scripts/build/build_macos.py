#!/usr/bin/env python3
"""macOS App Build Script for Kumihan-Formatter
macOS .app packaging build script

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
from pathlib import Path


class MacOSBuilder:
    """macOS App builder for Kumihan-Formatter"""

    def __init__(self, root_dir: Path | None = None):
        self.root_dir = root_dir or Path(__file__).parent.parent.parent
        self.dist_dir = self.root_dir / "dist"
        self.build_dir = self.root_dir / "build"
        self.spec_file = (
            self.root_dir / "tools" / "packaging" / "kumihan_formatter_macos.spec"
        )
        self.app_name = "Kumihan-Formatter.app"
        self.app_path = self.dist_dir / self.app_name

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        print("[INFO] Checking dependencies...")

        # Check PyInstaller
        try:
            import PyInstaller

            print(f"[OK] PyInstaller {PyInstaller.__version__} found")
        except ImportError:
            print("[ERROR] PyInstaller not found")
            print("Install command: pip install pyinstaller")
            return False

        # Check main package
        try:
            import kumihan_formatter

            print("[OK] kumihan_formatter found")
        except ImportError:
            print("[ERROR] kumihan_formatter package not found")
            print("Please ensure running from current directory")
            return False

        # Check GUI dependencies
        try:
            import tkinter

            print("[OK] tkinter available")
        except ImportError:
            print("[ERROR] tkinter not found")
            return False

        # Check macOS specific tools
        if sys.platform == "darwin":
            print("[OK] macOS platform confirmed")
        else:
            print("[WARNING] Non-macOS platform")

        return True

    def clean_build_dirs(self) -> None:
        """Clean build and dist directories"""
        print("[INFO] Cleaning build directories...")

        dirs_to_clean = [self.dist_dir, self.build_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                print(f"   Removing: {dir_path}")
                shutil.rmtree(dir_path)
            else:
                print(f"   Skip: {dir_path} (does not exist)")

    def install_pyinstaller_if_needed(self) -> None:
        """Install PyInstaller if not available"""
        try:
            import PyInstaller
        except ImportError:
            print("[INFO] Installing PyInstaller...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pyinstaller"]
            )

    def build_app(self) -> Path:
        """Build the macOS app using PyInstaller"""
        print("[INFO] Building macOS App...")

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

        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.root_dir)

        if result.returncode != 0:
            raise RuntimeError(
                f"PyInstaller failed with return code {result.returncode}"
            )

        # Check if app was created
        if not self.app_path.exists():
            raise FileNotFoundError(f"Built app not found: {self.app_path}")

        print(f"[OK] App bundle created: {self.app_path}")

        # Calculate app size
        app_size = self._get_directory_size(self.app_path)
        print(f"   App size: {app_size / 1024 / 1024:.1f} MB")

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
        print("[INFO] Signing app bundle...")

        if not identity:
            # Try to find available signing identities
            result = subprocess.run(
                ["security", "find-identity", "-v", "-p", "codesigning"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout:
                print("Available signing identities:")
                print(result.stdout)
                print(
                    "[WARNING] Please specify identity with --sign option for signing"
                )
                return
            else:
                print("[ERROR] Signing identity not found")
                print("Developer account signing required")
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

        print(f"Signing command: {' '.join(cmd)}")
        result: subprocess.CompletedProcess[str] = subprocess.run(cmd, text=True)

        if result.returncode == 0:
            print("[OK] Signing completed")
        else:
            print("[ERROR] Signing failed")
            raise RuntimeError(
                f"Code signing failed with return code {result.returncode}"
            )

    def notarize_app(self, app_path: Path) -> None:
        """Notarize the app bundle"""
        print("[INFO] Notarizing app bundle...")
        print("[WARNING] Notarization requires Apple ID configuration")
        print(
            "詳細: https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution"
        )

        # This would require Apple ID credentials and is beyond basic setup
        print("[INFO] Please run notarization manually:")
        print(
            f"   1. Compress app to ZIP: ditto -c -k --keepParent {app_path} {app_path.name}.zip"
        )
        print(
            f"   2. Run notarization: xcrun notarytool submit {app_path.name}.zip --apple-id YOUR_APPLE_ID --password YOUR_APP_PASSWORD --team-id YOUR_TEAM_ID --wait"
        )

    def test_app(self, app_path: Path) -> None:
        """Test the built app"""
        print("[INFO] Testing app bundle...")

        # Check app bundle structure
        executable_path = app_path / "Contents" / "MacOS" / "Kumihan-Formatter"
        if executable_path.exists():
            print("[OK] Executable found")
        else:
            print("[ERROR] Executable not found")

        # Check Info.plist
        info_plist_path = app_path / "Contents" / "Info.plist"
        if info_plist_path.exists():
            print("[OK] Info.plist found")
        else:
            print("[ERROR] Info.plist not found")

        # Check Resources directory
        resources_path = app_path / "Contents" / "Resources"
        if resources_path.exists():
            print("[OK] Resources directory found")
        else:
            print("[ERROR] Resources directory not found")

        # Basic execution test
        try:
            # Try to get app info
            result = subprocess.run(
                ["mdls", "-name", "kMDItemDisplayName", str(app_path)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print("[OK] Application information retrieved")
            else:
                print("[WARNING] Failed to retrieve application information")
        except Exception as e:
            print(f"[WARNING] Error during testing: {e}")

        print("[OK] Basic test completed")

    def create_distribution_package(self, app_path: Path) -> Path:
        """Create distribution package (DMG or ZIP)"""
        print("[INFO] Creating distribution package...")

        # Create ZIP package for simple distribution
        package_name = "Kumihan-Formatter-v1.0-macOS"
        zip_path = self.dist_dir / f"{package_name}.zip"

        print(f"Creating ZIP package: {zip_path}")

        # Create ZIP using ditto (preserves resource forks and extended attributes)
        cmd = ["ditto", "-c", "-k", "--keepParent", str(app_path), str(zip_path)]

        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise RuntimeError(
                f"ZIP creation failed with return code {result.returncode}"
            )

        # Create installation instructions
        readme_content = """Kumihan-Formatter v1.0 - macOS Edition

Installation Instructions:
1. Download and extract this ZIP file
2. Drag Kumihan-Formatter.app to your Applications folder
3. If "Unidentified developer" warning appears on first launch:
   - Right-click the app → Select "Open"
   - Or go to System Preferences → Security & Privacy → "Open Anyway"

System Requirements:
- macOS 10.15 (Catalina) or later
- Intel/Apple Silicon Mac support
- No internet connection required
- No Python installation required

Usage:
1. Launch the application
2. Use "Browse" button to select text file for conversion
3. Click "Convert" button

Support:
- GitHub: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter
- Issues: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues

License:
MIT License - Copyright © 2025 mo9mo9-uwu-mo9mo9
"""

        readme_path = self.dist_dir / "README.txt"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        zip_size = zip_path.stat().st_size
        print(f"[OK] Distribution package created: {zip_path}")
        print(f"   Package size: {zip_size / 1024 / 1024:.1f} MB")

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
        print("[INFO] Kumihan-Formatter macOS build starting...")
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

            print("\n[OK] Build completed successfully!")
            print(f"   App bundle: {app_path}")
            print(f"   Distribution package: {package_path}")
            print("\n[INFO] Next steps:")
            print("   1. Test the app bundle")
            print("   2. Test on different macOS versions")
            print("   3. Run signing/notarization if needed")
            print("   4. Publish distribution package on GitHub release page")

            return True

        except Exception as e:
            print(f"\n[ERROR] Build failed: {e}")
            import traceback

            traceback.print_exc()
            return False


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter macOS build script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean directories before build"
    )
    parser.add_argument(
        "--test", action="store_true", help="Test app bundle after build"
    )
    parser.add_argument("--sign", action="store_true", help="Sign app bundle")
    parser.add_argument("--notarize", action="store_true", help="Notarize app bundle")
    parser.add_argument("--sign-identity", help="Identity to use for signing")

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
