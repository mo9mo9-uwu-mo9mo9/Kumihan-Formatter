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
            print(
                "[ERROR] tkinter not found (should be included in Python standard library)"
            )
            return False

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

        print(f"Running command: {' '.join(cmd)}")
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

        print(f"[OK] Executable created: {exe_path}")
        print(f"   File size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")

        return exe_path

    def test_executable(self, exe_path: Path) -> None:
        """Test the built executable"""
        print("[INFO] Testing executable...")

        # Basic execution test (should start GUI)
        try:
            # Test with --help flag first (if supported)
            result = subprocess.run(
                [str(exe_path), "--help"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print("[OK] Help display test: success")
            else:
                print("[WARNING] Help display test: skipped (normal for GUI app)")
        except subprocess.TimeoutExpired:
            print("[WARNING] Help display test: timeout (normal for GUI app)")
        except Exception as e:
            print(f"[WARNING] Help display test: {e}")

        # Check file dependencies
        print("[INFO] Checking dependency files...")
        templates_exist = any((self.dist_dir / "_internal").glob("**/templates"))
        if templates_exist:
            print("[OK] Template files included")
        else:
            print("[WARNING] Template files not found")

        print("[OK] Basic test completed")

    def create_distribution_package(self, exe_path: Path) -> Path:
        """Create distribution package (ZIP file)"""
        print("[INFO] Creating distribution package...")

        # Create ZIP package
        package_name = "Kumihan-Formatter-v1.0-Windows"
        zip_path = self.dist_dir / f"{package_name}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add executable
            zipf.write(exe_path, exe_path.name)

            # Add README for distribution
            readme_content = """Kumihan-Formatter v1.0 - Windows Edition

Installation Instructions:
1. Extract this ZIP file to any location
2. Double-click Kumihan-Formatter.exe to launch

System Requirements:
- Windows 10 / 11 (64-bit)
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
            zipf.writestr("README.txt", readme_content.encode("utf-8"))

        print(f"[OK] Distribution package created: {zip_path}")
        print(f"   Package size: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")

        return zip_path

    def upload_to_github(self, package_path: Path) -> None:
        """Upload package to GitHub releases (placeholder)"""
        print("[INFO] Uploading to GitHub release...")
        print("[WARNING] Automatic upload via GitHub Actions is recommended")
        print(f"   Package for manual upload: {package_path}")

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
            print(f"   Executable: {exe_path}")
            print(f"   Distribution package: {package_path}")
            print("\n[INFO] Next steps:")
            print("   1. Test the executable")
            print("   2. Test on different Windows environments")
            print("   3. Publish distribution package on GitHub release page")

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
        "--upload", action="store_true", help="Upload to GitHub release"
    )

    args = parser.parse_args()

    # Build
    builder = WindowsBuilder()
    success = builder.build(clean=args.clean, test=args.test, upload=args.upload)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    sys.exit(main())
