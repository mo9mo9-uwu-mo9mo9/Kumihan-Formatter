#!/usr/bin/env python3
"""
Enhanced Error Reporting Tests - 強化されたエラーレポートのテスト

Phase 2で実装したユーザーフレンドリーなエラーメッセージ機能をテストする
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# テスト対象のインポート
from kumihan_formatter.core.error_reporting import (
    DetailedError, ErrorReport, ErrorReportBuilder,
    ErrorSeverity, ErrorCategory, ErrorLocation, FixSuggestion
)


class TestDetailedErrorDisplay:
    """DetailedErrorの表示機能テスト"""
    
    def test_basic_error_display(self):
        """基本的なエラー表示"""
        error = DetailedError(
            error_id="test_001",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYNTAX,
            title="テスト記法エラー",
            message="これはテスト用のエラーメッセージです",
            location=ErrorLocation(line=5),
            highlighted_line=";;;不正なマーカー",
        )
        
        display = str(error)
        
        # 絵文字が含まれていることを確認
        assert "❌" in display
        assert "テスト記法エラー" in display
        assert "これはテスト用のエラーメッセージです" in display
        assert "行5" in display
        assert ";;;不正なマーカー" in display
    
    def test_error_with_context_lines(self):
        """コンテキスト行付きエラー表示"""
        error = DetailedError(
            error_id="test_002",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.STRUCTURE,
            title="構造警告",
            message="構造に問題があります",
            context_lines=[
                "  3  │ ;;;見出し1",
                "  4  │ タイトル",
                "  5 →│ ;;;",  # 問題行
                "  6  │ ",
                "  7  │ 次の内容"
            ]
        )
        
        display = str(error)
        
        # コンテキスト表示の確認
        assert "⚠️" in display  # 警告の絵文字
        assert "📝 周辺コード:" in display
        assert "  3  │ ;;;見出し1" in display
        assert "  5 →│ ;;;" in display  # 問題行がマークされている
    
    def test_error_with_fix_suggestions(self):
        """修正提案付きエラー表示"""
        suggestions = [
            FixSuggestion(
                description="閉じマーカーを追加する",
                original_text=";;;見出し1",
                suggested_text=";;;見出し1\n内容\n;;;",
                confidence=0.9
            ),
            FixSuggestion(
                description="ブロックを削除する",
                confidence=0.7
            )
        ]
        
        error = DetailedError(
            error_id="test_003",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.STRUCTURE,
            title="未閉じブロック",
            message="ブロックが閉じられていません",
            fix_suggestions=suggestions
        )
        
        display = str(error)
        
        # 修正提案の表示確認
        assert "💡 修正方法:" in display
        assert "🎯" in display  # 高信頼度の提案
        assert "💭" in display  # 中信頼度の提案
        assert "閉じマーカーを追加する" in display
        assert "ブロックを削除する" in display


class TestErrorReport:
    """ErrorReportクラスのテスト"""
    
    def test_empty_report_display(self):
        """エラーなしレポートの表示"""
        report = ErrorReport()
        display = report.to_console_output()
        
        # 成功メッセージの確認
        assert "🎉 素晴らしい！記法エラーは見つかりませんでした！" in display
        assert "✨" in display
    
    def test_report_with_errors_and_warnings(self):
        """エラー・警告混在レポートの表示"""
        report = ErrorReport()
        
        # エラーを追加
        error = DetailedError(
            error_id="err_001",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYNTAX,
            title="記法エラー",
            message="記法に問題があります"
        )
        report.add_error(error)
        
        # 警告を追加
        warning = DetailedError(
            error_id="warn_001",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.STRUCTURE,
            title="構造警告",
            message="構造を改善できます"
        )
        report.add_error(warning)
        
        display = report.to_console_output()
        
        # レポート構造の確認
        assert "🚨 修正が必要な問題" in display
        assert "⚠️  改善推奨事項" in display
        assert "【問題 1】" in display
        assert "【改善案 1】" in display
        assert "🔧 次のステップ:" in display
    
    def test_report_summary(self):
        """レポートサマリーのテスト"""
        report = ErrorReport()
        
        # 複数のエラー・警告を追加
        for i in range(2):
            error = DetailedError(
                error_id=f"err_{i}",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.SYNTAX,
                title=f"エラー{i}",
                message=f"エラーメッセージ{i}"
            )
            report.add_error(error)
        
        for i in range(3):
            warning = DetailedError(
                error_id=f"warn_{i}",
                severity=ErrorSeverity.WARNING,
                category=ErrorCategory.STRUCTURE,
                title=f"警告{i}",
                message=f"警告メッセージ{i}"
            )
            report.add_error(warning)
        
        summary = report.get_summary()
        assert "2個のエラー" in summary
        assert "3個の警告" in summary


class TestErrorReportBuilder:
    """ErrorReportBuilderのテスト"""
    
    def test_create_syntax_error_with_context(self):
        """コンテキスト付き記法エラー作成"""
        # テンポラリファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(";;;見出し1\n")
            f.write("タイトル\n")
            f.write(";;;不正なマーカー\n")  # 問題行
            f.write("内容\n")
            f.write(";;;")
            temp_path = Path(f.name)
        
        try:
            error = ErrorReportBuilder.create_syntax_error(
                title="不正マーカー",
                message="マーカーが正しくありません",
                file_path=temp_path,
                line_number=3,
                problem_text=";;;不正なマーカー"
            )
            
            # コンテキスト行が自動取得されていることを確認
            assert len(error.context_lines) > 0
            assert any("→│" in line for line in error.context_lines)  # 問題行マーカー
            assert any("タイトル" in line for line in error.context_lines)  # 周辺行
        
        finally:
            temp_path.unlink()  # 一時ファイルを削除
    
    def test_create_enhanced_syntax_error(self):
        """拡張記法エラー作成"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(";;;見出し1\n")
            f.write("内容\n")
            f.write(";;;見だし2\n")  # スペルミス
            temp_path = Path(f.name)
        
        try:
            error = ErrorReportBuilder.create_enhanced_syntax_error(
                title="スペルミス",
                message="キーワードにスペルミスがあります",
                file_path=temp_path,
                line_number=3,
                problem_text=";;;見だし2",
                error_type="invalid_keyword"
            )
            
            # 自動修正提案が含まれていることを確認
            assert len(error.fix_suggestions) > 0
            # スペルミス修正提案があることを確認
            suggestions_text = " ".join([s.description for s in error.fix_suggestions])
            assert "見出し" in suggestions_text
        
        finally:
            temp_path.unlink()
    
    def test_smart_suggestions_generation(self):
        """スマート修正提案の生成テスト"""
        # 未閉じブロックの提案
        suggestions = ErrorReportBuilder._generate_smart_suggestions(
            "unclosed_block", ";;;見出し1"
        )
        assert len(suggestions) > 0
        assert any(";;; を追加" in s.description for s in suggestions)
        
        # 空ブロックの提案
        suggestions = ErrorReportBuilder._generate_smart_suggestions(
            "empty_block", ";;;"
        )
        assert len(suggestions) >= 2  # 追加と削除の提案
        assert any("削除" in s.description for s in suggestions)
        assert any("追加" in s.description for s in suggestions)
    
    def test_context_lines_extraction(self):
        """コンテキスト行抽出のテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            lines = [
                "1行目",
                "2行目", 
                "3行目 - 問題行",
                "4行目",
                "5行目"
            ]
            f.write("\n".join(lines))
            temp_path = Path(f.name)
        
        try:
            context = ErrorReportBuilder._get_context_lines(temp_path, 3, context_count=2)
            
            # 期待される行数（前後2行+問題行）
            assert len(context) == 5
            
            # 行番号の確認
            assert "1  │ 1行目" in context[0]
            assert "3 →│ 3行目 - 問題行" in context[2]  # 問題行がマーク
            assert "5  │ 5行目" in context[4]
        
        finally:
            temp_path.unlink()


class TestErrorIntegration:
    """エラーレポート統合テスト"""
    
    def test_full_error_workflow(self):
        """完全なエラーワークフローのテスト"""
        # サンプルファイルでエラーレポートを作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(";;;見出し1\n")
            f.write("正常な内容\n")
            f.write(";;;見だし2\n")  # スペルミス
            f.write("不完全な内容")     # 閉じマーカーなし
            temp_path = Path(f.name)
        
        try:
            report = ErrorReport(temp_path)
            
            # 複数種類のエラーを追加
            error1 = ErrorReportBuilder.create_enhanced_syntax_error(
                title="スペルミス",
                message="キーワードが正しくありません",
                file_path=temp_path,
                line_number=3,
                problem_text=";;;見だし2",
                error_type="invalid_keyword"
            )
            report.add_error(error1)
            
            error2 = ErrorReportBuilder.create_enhanced_syntax_error(
                title="未閉じブロック",
                message="ブロックが閉じられていません",
                file_path=temp_path,
                line_number=4,
                problem_text="不完全な内容",
                error_type="unclosed_block"
            )
            report.add_error(error2)
            
            # レポート出力のテスト
            console_output = report.to_console_output()
            
            # レポートの各要素が含まれていることを確認
            assert temp_path.name in console_output
            assert "【問題 1】" in console_output
            assert "【問題 2】" in console_output
            assert "🔧 次のステップ:" in console_output
            assert "スペルミス" in console_output
            assert "未閉じブロック" in console_output
        
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])