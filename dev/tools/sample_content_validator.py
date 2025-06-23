#!/usr/bin/env python3
"""
sample_content.py 内のサンプルテキスト検証スクリプト
"""

import tempfile
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

try:
    from kumihan_formatter.sample_content import SHOWCASE_SAMPLE
    from syntax_validator import SyntaxValidator
except ImportError as e:
    print(f"インポートエラー: {e}")
    sys.exit(1)


def main():
    """sample_content.py 内のサンプルテキストを検証"""
    print("📝 sample_content.py 内のサンプルテキストをチェック...")
    
    # 一時ファイルに保存して検証
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(SHOWCASE_SAMPLE)
        temp_path = Path(f.name)

    try:
        validator = SyntaxValidator()
        errors = validator.validate_file(temp_path)

        # SHOWCASE_SAMPLEでは目次マーカーは許可する（例外処理）
        filtered_errors = []
        for error in errors:
            if error.error_type == "INVALID_MARKER" and ";;;目次;;;" in error.message:
                # SHOWCASE_SAMPLEでの目次マーカーは許可
                continue
            filtered_errors.append(error)

        if filtered_errors:
            print(f"❌ SHOWCASE_SAMPLE に {len(filtered_errors)} 個のエラーが見つかりました:")
            for error in filtered_errors:
                print(f"   Line {error.line_number}: {error.message}")
                if error.suggestion:
                    print(f"      💡 {error.suggestion}")
            sys.exit(1)
        else:
            print("✅ SHOWCASE_SAMPLE: 記法エラーなし")

    finally:
        # 一時ファイルを削除
        os.unlink(temp_path)


if __name__ == '__main__':
    main()