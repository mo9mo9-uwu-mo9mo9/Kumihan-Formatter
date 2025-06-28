#!/usr/bin/env python3
"""
Enhanced Error Reporting Demo - エラーレポート機能のデモ

新しいユーザーフレンドリーなエラーメッセージをテスト・デモする
"""

import tempfile
from pathlib import Path
import sys

# パスを追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# テスト対象のインポート
from kumihan_formatter.core.error_reporting import (
    DetailedError, ErrorReport, ErrorReportBuilder,
    ErrorSeverity, ErrorCategory, ErrorLocation, FixSuggestion
)


def demo_basic_error():
    """基本的なエラー表示のデモ"""
    print("=" * 60)
    print("🧪 基本的なエラー表示のデモ")
    print("=" * 60)
    
    error = DetailedError(
        error_id="demo_001",
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.SYNTAX,
        title="記法エラーの例",
        message=";;;見だし1 は正しいキーワードではありません。'見出し1' が正しいキーワードです。",
        location=ErrorLocation(line=3),
        highlighted_line=";;;見だし1",
        fix_suggestions=[
            FixSuggestion(
                description="'見だし' を '見出し' に修正する",
                original_text=";;;見だし1",
                suggested_text=";;;見出し1",
                confidence=0.95
            )
        ]
    )
    
    print(str(error))
    print()


def demo_error_with_context():
    """コンテキスト付きエラーのデモ"""
    print("=" * 60)
    print("🧪 コンテキスト付きエラーのデモ")
    print("=" * 60)
    
    # テスト用のファイルを作成
    test_content = """;;;見出し1
タイトル内容
;;;

これは正常な内容です。

;;;見だし2
問題のある内容
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_path = Path(f.name)
    
    try:
        # コンテキスト付きエラーを作成
        error = ErrorReportBuilder.create_syntax_error(
            title="スペルミスエラー",
            message="キーワードにスペルミスがあります",
            file_path=temp_path,
            line_number=6,
            problem_text=";;;見だし2"
        )
        
        print(str(error))
        print()
    
    finally:
        temp_path.unlink()  # 一時ファイルを削除


def demo_enhanced_error():
    """拡張エラー（スマート修正提案付き）のデモ"""
    print("=" * 60)
    print("🧪 拡張エラー（スマート修正提案付き）のデモ")
    print("=" * 60)
    
    test_content = """;;;見出し1
正常な内容
;;;

;;;ハイライド color=#ff0000
スペルミスのある内容
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_path = Path(f.name)
    
    try:
        # 拡張エラーを作成
        error = ErrorReportBuilder.create_enhanced_syntax_error(
            title="不正なキーワード",
            message="'ハイライド' は有効なキーワードではありません",
            file_path=temp_path,
            line_number=5,
            problem_text=";;;ハイライド color=#ff0000",
            error_type="invalid_keyword"
        )
        
        print(str(error))
        print()
    
    finally:
        temp_path.unlink()


def demo_error_report():
    """統合エラーレポートのデモ"""
    print("=" * 60)
    print("🧪 統合エラーレポートのデモ")
    print("=" * 60)
    
    test_content = """;;;見出し1
正常な内容
;;;

;;;見だし2
未閉じブロック内容

;;;ハイライド color=#ff0000
さらなる問題
;;;
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_path = Path(f.name)
    
    try:
        # エラーレポートを作成
        report = ErrorReport(temp_path)
        
        # 複数のエラーを追加
        error1 = ErrorReportBuilder.create_enhanced_syntax_error(
            title="スペルミス",
            message="'見だし' は正しくありません",
            file_path=temp_path,
            line_number=4,
            problem_text=";;;見だし2",
            error_type="invalid_keyword"
        )
        report.add_error(error1)
        
        error2 = ErrorReportBuilder.create_enhanced_syntax_error(
            title="未閉じブロック",
            message="ブロックが正しく閉じられていません",
            file_path=temp_path,
            line_number=5,
            problem_text="未閉じブロック内容",
            error_type="unclosed_block"
        )
        report.add_error(error2)
        
        warning = DetailedError(
            error_id="warn_001",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.STRUCTURE,
            title="改善推奨",
            message="より良い記法があります",
            file_path=temp_path,
            location=ErrorLocation(line=7),
            fix_suggestions=[
                FixSuggestion(
                    description="'ハイライド' を 'ハイライト' に修正",
                    confidence=0.9
                )
            ]
        )
        report.add_error(warning)
        
        # レポートを表示
        print(report.to_console_output())
        
        # ファイルレポートも作成
        report_file = temp_path.parent / f"{temp_path.stem}_error_report.txt"
        report.to_file_report(report_file)
        print(f"\n📄 詳細レポートファイル: {report_file}")
        
    finally:
        temp_path.unlink()


def demo_success_report():
    """成功時のレポートデモ"""
    print("=" * 60)
    print("🧪 エラーなし（成功）レポートのデモ")
    print("=" * 60)
    
    report = ErrorReport()
    print(report.to_console_output())


def main():
    """メイン関数"""
    print("🚀 Enhanced Error Reporting Demo")
    print("Phase 2で実装したユーザーフレンドリーなエラーメッセージのデモです")
    print()
    
    try:
        demo_basic_error()
        demo_error_with_context()
        demo_enhanced_error()
        demo_error_report()
        demo_success_report()
        
        print("=" * 60)
        print("✅ すべてのデモが正常に完了しました！")
        print("=" * 60)
    
    except Exception as e:
        print(f"❌ デモ実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())