#!/usr/bin/env python3
"""TDD Test Runner - 自動テスト実行システム"""

import subprocess
import sys
from pathlib import Path

def run_tdd_tests():
    """TDDテストの実行"""
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=kumihan_formatter",
        "--cov-report=term-missing",
        "--cov-fail-under=70",
        "--maxfail=3",
        "-x",  # 最初の失敗で停止
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ テスト失敗 - TDD要求違反")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    else:
        print("✅ 全テスト通過 - TDD要求満足")
        
if __name__ == "__main__":
    run_tdd_tests()
