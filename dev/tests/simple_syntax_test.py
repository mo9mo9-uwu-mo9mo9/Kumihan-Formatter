#!/usr/bin/env python3
"""
シンプルな記法検証テスト（pytest非依存版）
"""

import sys
import tempfile
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from syntax_validator import SyntaxValidator


def test_valid_syntax():
    """正しい記法のテスト"""
    valid_content = """;;;見出し1
タイトル
;;;

これは正しい段落です。

;;;太字
強調テキスト
;;;

- 正しいリスト項目
- ;;;枠線;;; 正しいキーワード付きリスト

;;;ハイライト color=#ffe6e6
正しいハイライトブロック
;;;
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(valid_content)
        temp_path = Path(f.name)
    
    try:
        validator = SyntaxValidator()
        errors = validator.validate_file(temp_path)
        
        if len(errors) > 0:
            print(f"❌ 正しい記法でエラーが検出されました: {len(errors)} 個")
            for error in errors:
                print(f"   Line {error.line_number}: {error.message}")
            return False
        else:
            print("✅ 正しい記法テスト: PASS")
            return True
    finally:
        os.unlink(temp_path)


def test_invalid_syntax():
    """不正な記法のテスト"""
    invalid_content = """# これは非サポート記法です

**太字** は使えません

;;;見出し1
正しい記法
;;;
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(invalid_content)
        temp_path = Path(f.name)
    
    try:
        validator = SyntaxValidator()
        errors = validator.validate_file(temp_path)
        
        if len(errors) >= 2:  # # 記法と **太字** 記法の2つのエラーを期待
            print("✅ 不正な記法検出テスト: PASS")
            return True
        else:
            print(f"❌ 期待される不正記法が検出されませんでした: {len(errors)} 個")
            return False
    finally:
        os.unlink(temp_path)


def test_examples_files():
    """examples/ ディレクトリのファイルテスト"""
    examples_dir = project_root / "examples"
    
    if not examples_dir.exists():
        print("⏭️  examples/ ディレクトリが見つかりません")
        return True
    
    validator = SyntaxValidator()
    all_errors = []
    
    for txt_file in examples_dir.glob("*.txt"):
        errors = validator.validate_file(txt_file)
        all_errors.extend(errors)
        
        if errors:
            print(f"❌ {txt_file.name}: {len(errors)} エラー")
            for error in errors:
                print(f"   Line {error.line_number}: {error.message}")
    
    if len(all_errors) == 0:
        print("✅ examples/ ファイルテスト: PASS")
        return True
    else:
        print(f"❌ examples/ に {len(all_errors)} 個のエラーがあります")
        return False


def test_sample_content():
    """sample_content.py のテスト"""
    try:
        from kumihan_formatter.sample_content import SHOWCASE_SAMPLE
    except ImportError:
        print("⏭️  sample_content モジュールが見つかりません")
        return True
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(SHOWCASE_SAMPLE)
        temp_path = Path(f.name)
    
    try:
        validator = SyntaxValidator()
        errors = validator.validate_file(temp_path)
        
        if len(errors) == 0:
            print("✅ SHOWCASE_SAMPLE テスト: PASS")
            return True
        else:
            print(f"❌ SHOWCASE_SAMPLE に {len(errors)} 個のエラーがあります")
            for error in errors:
                print(f"   Line {error.line_number}: {error.message}")
            return False
    finally:
        os.unlink(temp_path)


def main():
    """全テストを実行"""
    print("🔍 記法検証テストを開始...")
    
    tests = [
        test_valid_syntax,
        test_invalid_syntax,
        test_examples_files,
        test_sample_content
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ テスト {test.__name__} でエラー: {e}")
    
    print(f"\n📊 テスト結果: {passed}/{total} 通過")
    
    if passed == total:
        print("✅ 全テスト通過")
        sys.exit(0)
    else:
        print("❌ テスト失敗あり")
        sys.exit(1)


if __name__ == "__main__":
    main()