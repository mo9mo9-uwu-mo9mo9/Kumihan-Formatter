#!/usr/bin/env python3
"""
アルファ版ビルドスクリプト
Generate Mac/Windows executable files
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def main():
    """Main processing for alpha build"""

    # Move to project root
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)

    print("🚀 Kumihan-Formatter alpha build starting")
    print(f"📁 Project root: {project_root}")
    print(f"🖥️  Platform: {platform.system()}")

    # Check if PyInstaller is installed
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            check=True,
            capture_output=True,
        )
        print("✅ PyInstaller found")
    except subprocess.CalledProcessError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"], check=True
        )

    # Platform-specific settings
    system = platform.system()
    if system == "Darwin":  # macOS
        spec_file = "tools/packaging/kumihan_formatter_macos.spec"
        output_name = "Kumihan-Formatter"
    elif system == "Windows":
        spec_file = "tools/packaging/kumihan_formatter.spec"
        output_name = "kumihan_formatter_windows.exe"
    else:
        print(f"❌ Unsupported platform: {system}")
        sys.exit(1)

    # Execute build
    print(f"🔨 ビルド開始: {spec_file}")
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", spec_file],
            check=True,
        )

        # Check output file
        dist_path = project_root / "dist" / output_name
        if dist_path.exists():
            print(f"✅ ビルド成功: {dist_path}")

            # Execution test
            print("🧪 Execution testing...")
            result = subprocess.run(
                [str(dist_path), "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"✅ Execution test successful: {result.stdout.strip()}")
            else:
                print(f"⚠️  Execution test warning: {result.stderr}")
        else:
            print(f"❌ Build file not found: {dist_path}")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"❌ ビルドエラー: {e}")
        sys.exit(1)

    print("🎉 Alpha build completed")
    print(f"📦 Output file: dist/{output_name}")


if __name__ == "__main__":
    main()
