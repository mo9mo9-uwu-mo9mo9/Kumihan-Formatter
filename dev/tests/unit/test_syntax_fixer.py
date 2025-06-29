#!/usr/bin/env python3
"""
Syntax Fixer テストスイート
"""

import pytest
import tempfile
from pathlib import Path
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dev.tools.syntax_fixer import SyntaxFixer, FixResult


class TestSyntaxFixer:
    """SyntaxFixer クラスのテスト"""
    
    def test_fix_malformed_heading_blocks(self):
        """見出しブロックの修正テスト"""
        content = """;;;見出し1
テストタイトル

;;;見出し2
サブタイトル"""
        
        fixer = SyntaxFixer()
        fixed_content, changes = fixer._fix_malformed_blocks(content)
        
        expected = """;;;見出し1
テストタイトル
;;;

;;;見出し2
サブタイトル
;;;"""
        
        assert fixed_content == expected
        assert len(changes) == 2
        assert "見出しブロックに閉じマーカーを追加" in changes[0]
    
    def test_cleanup_empty_markers(self):
        """空マーカーのクリーンアップテスト"""
        content = """;;;見出し1
テスト
;;;

;;;
;;;太字
内容
;;;"""
        
        fixer = SyntaxFixer()
        fixed_content, changes = fixer._cleanup_empty_markers(content)
        
        # 不要な空マーカーが削除されることを確認
        assert ";;;\n;;;太字" not in fixed_content
        assert len(changes) > 0
    
    def test_consecutive_marker_combination(self):
        """連続マーカーの統合テスト"""
        content = """;;;ハイライト color=#e6f3ff
;;;太字
内容
;;;"""
        
        fixer = SyntaxFixer()
        fixed_content, changes = fixer._fix_consecutive_markers(content)
        
        # 連続マーカーが統合されることを確認
        expected = """;;;ハイライト+太字 color=#e6f3ff
内容
;;;"""
        
        assert fixed_content == expected
        assert len(changes) == 1
        assert "連続マーカーを統合" in changes[0]
    
    def test_combine_markers(self):
        """マーカー統合ロジックテスト"""
        fixer = SyntaxFixer()
        
        # 基本的な統合
        markers = [";;;太字", ";;;イタリック"]
        result = fixer._combine_markers(markers)
        assert result == ";;;太字+イタリック"
        
        # color属性付き統合
        markers = [";;;ハイライト color=#ff0000", ";;;太字"]
        result = fixer._combine_markers(markers)
        assert result == ";;;ハイライト+太字 color=#ff0000"
    
    def test_fix_file_integration(self):
        """ファイル修正の統合テスト"""
        test_content = """;;;見出し1
テスト

;;;
;;;ハイライト color=#e6f3ff
;;;
;;;太字
基本情報
;;;

;;;見出し2
終了"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            fixer = SyntaxFixer()
            result = fixer.fix_file(temp_path, preview_only=True)
            
            # 修正が検出されることを確認
            assert result.errors_fixed > 0
            assert result.original_content != result.fixed_content
            assert len(result.changes_made) > 0
            
            # 実際のファイル修正テスト
            result_applied = fixer.fix_file(temp_path, preview_only=False)
            
            # ファイルが実際に修正されることを確認
            with open(temp_path, 'r', encoding='utf-8') as f:
                fixed_file_content = f.read()
            
            assert fixed_file_content == result_applied.fixed_content
            
        finally:
            temp_path.unlink()  # 一時ファイルを削除
    
    def test_validation_errors(self):
        """検証エラーのテスト"""
        content = """# Markdown見出し
**太字テキスト**
;;;目次;;;"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            fixer = SyntaxFixer()
            errors = fixer.validate_file(temp_path)
            
            # 非サポート記法エラーが検出されることを確認
            assert len(errors) > 0
            error_types = [error.error_type for error in errors]
            assert "UNSUPPORTED_SYNTAX" in error_types
            assert "INVALID_MARKER" in error_types
            
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])