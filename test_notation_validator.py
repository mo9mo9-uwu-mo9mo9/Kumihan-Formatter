#!/usr/bin/env python3
"""
notation_validator.py の基本動作テスト
Issue #729 対応の品質保証
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from notation_validator import NotationValidator


def test_error_detection():
    """エラー検出機能のテスト"""
    print("🔍 エラー検出テスト")
    print("-" * 30)
    
    validator = NotationValidator()
    
    test_cases = [
        # 修正済みエラーパターン
        ("#太字# テスト#太字#", "重複キーワード"),
        ("#コード# value#コード#", "重複キーワード"),
        ("#太字# 内容", "閉じタグ不足"),
        
        # 正常パターン
        ("#太字# 正常テスト##", "正常"),
        ("#コード# console.log()##", "正常"),
        ("#ハイライト color=red# 重要##", "正常"),
    ]
    
    for text, expected in test_cases:
        is_valid, errors = validator.validate_text(text)
        
        if expected == "正常":
            status = "✅" if is_valid else "❌"
            print(f"{status} {text} -> {len(errors)}件エラー")
        else:
            status = "✅" if not is_valid else "❌"
            print(f"{status} {text} -> {expected} 検出")
            if errors:
                print(f"    {errors[0].error_type}: {errors[0].suggestion}")


def test_auto_fix():
    """自動修正機能のテスト"""
    print("\n🔧 自動修正テスト")
    print("-" * 30)
    
    validator = NotationValidator()
    
    test_cases = [
        "#太字# 項目0#太字#",
        "#コード# value_1_299_0#コード#",
    ]
    
    for original in test_cases:
        fixed = validator.fix_common_errors(original)
        print(f"修正前: {original}")
        print(f"修正後: {fixed}")
        print()


def test_templates():
    """テンプレート機能のテスト"""
    print("📋 テンプレート機能テスト")
    print("-" * 30)
    
    validator = NotationValidator()
    templates = validator.get_templates()
    
    for name, template in templates.items():
        print(f"{name}: {template}")


def main():
    """テスト実行"""
    print("🚀 notation_validator.py 基本動作テスト")
    print("=" * 50)
    
    test_error_detection()
    test_auto_fix()
    test_templates()
    
    print("\n✅ テスト完了")


if __name__ == "__main__":
    main()