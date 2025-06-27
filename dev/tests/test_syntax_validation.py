"""記法検証機能のテスト"""

import pytest
from pathlib import Path
import tempfile
import os
import sys

# テストで syntax_validator を import するため、パスを追加
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from syntax_validator import SyntaxValidator, ValidationError


class TestSyntaxValidation:
    """記法検証のテストクラス"""
    
    def test_valid_syntax_no_errors(self, tmp_path):
        """正しい記法のファイルでエラーが発生しないことを確認"""
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
        test_file = tmp_path / "valid.txt"
        test_file.write_text(valid_content, encoding="utf-8")
        
        validator = SyntaxValidator()
        errors = validator.validate_file(test_file)
        
        assert len(errors) == 0
    
    def test_standalone_marker_error(self, tmp_path):
        """単独の;;;マーカーがエラーとして検出されることを確認"""
        invalid_content = """;;;見出し1
タイトル
;;;

これは段落です。
;;;

;;;太字
テキスト
;;;
"""
        test_file = tmp_path / "standalone.txt"
        test_file.write_text(invalid_content, encoding="utf-8")
        
        validator = SyntaxValidator()
        errors = validator.validate_file(test_file)
        
        # 6行目に単独の;;;があるのでエラーが1つあるはず
        assert len(errors) >= 1
        assert any(error.line_number == 6 for error in errors)
    
    def test_unsupported_markdown_syntax(self, tmp_path):
        """非サポートのMarkdown記法を検出"""
        invalid_content = """# これは非サポート記法です

**太字** は使えません

;;;見出し1
正しい記法
;;;
"""
        test_file = tmp_path / "invalid.txt"
        test_file.write_text(invalid_content, encoding="utf-8")
        
        validator = SyntaxValidator()
        errors = validator.validate_file(test_file)
        
        # 2つのエラーが検出されることを確認
        assert len(errors) == 2
        
        error_types = [e.error_type for e in errors]
        assert "UNSUPPORTED_SYNTAX" in error_types
        
        # 行番号が正しく記録されることを確認
        line_numbers = [e.line_number for e in errors]
        assert 1 in line_numbers  # # 記法
        assert 3 in line_numbers  # **太字** 記法
    
    def test_malformed_blocks(self, tmp_path):
        """不完全なブロック記法を検出"""
        # 最初のブロックに閉じマーカーがない
        malformed_content = """;;;見出し1
タイトル
閉じマーカーがありません
"""
        test_file = tmp_path / "malformed.txt"
        test_file.write_text(malformed_content, encoding="utf-8")
        
        validator = SyntaxValidator()
        errors = validator.validate_file(test_file)
        
        # ブロック内の # 記法は検証対象外となるため、
        # 閉じマーカーがないことだけが検出される
        assert len(errors) == 1
        assert errors[0].error_type == "MALFORMED_BLOCK"
        assert errors[0].line_number == 1
    
    def test_invalid_color_attribute(self, tmp_path):
        """color属性の誤使用を検出"""
        invalid_content = """- ;;;ハイライト color=#ff0000+太字;;; 間違った記法
"""
        test_file = tmp_path / "invalid_color.txt"
        test_file.write_text(invalid_content, encoding="utf-8")
        
        validator = SyntaxValidator()
        errors = validator.validate_file(test_file)
        
        assert len(errors) == 1
        assert errors[0].error_type == "INVALID_MARKER"
        assert "color属性の後に + は使用できません" in errors[0].message
    
    def test_toc_marker_usage(self, tmp_path):
        """目次マーカーの手動使用を検出"""
        invalid_content = """;;;目次;;;

;;;見出し1
テスト
;;;
"""
        test_file = tmp_path / "invalid_toc.txt"
        test_file.write_text(invalid_content, encoding="utf-8")
        
        validator = SyntaxValidator()
        errors = validator.validate_file(test_file)
        
        assert len(errors) == 1
        assert errors[0].error_type == "INVALID_MARKER"
        assert ";;;目次;;; は自動生成専用です" in errors[0].message
    
    def test_file_not_found_error(self):
        """存在しないファイルのエラーハンドリング"""
        validator = SyntaxValidator()
        errors = validator.validate_file(Path("nonexistent.txt"))
        
        assert len(errors) == 1
        assert errors[0].error_type == "FILE_ERROR"
        assert "ファイル読み込みエラー" in errors[0].message


class TestSampleFilesValidation:
    """サンプルファイル専用の記法検証テスト"""
    
    def test_examples_directory_syntax(self):
        """examples/ ディレクトリの全ファイルの記法検証"""
        examples_dir = Path(__file__).parent.parent.parent / "examples"
        
        if not examples_dir.exists():
            pytest.skip("examples/ ディレクトリが見つかりません")
        
        validator = SyntaxValidator()
        all_errors = []
        
        for txt_file in examples_dir.glob("*.txt"):
            errors = validator.validate_file(txt_file)
            all_errors.extend(errors)
            
            # ファイルごとのエラー詳細を出力
            if errors:
                print(f"\n[エラー] {txt_file.name}: {len(errors)} エラー")
                for error in errors:
                    print(f"   Line {error.line_number}: {error.message}")
                    if error.suggestion:
                        print(f"      [ヒント] {error.suggestion}")
        
        # 全サンプルファイルでエラーがないことを確認
        assert len(all_errors) == 0, f"サンプルファイルに {len(all_errors)} 個のエラーがあります"
    
    def test_sample_content_module_syntax(self):
        """sample_content.py 内のサンプルテキストの記法検証"""
        try:
            from kumihan_formatter.sample_content import SHOWCASE_SAMPLE
        except ImportError:
            pytest.skip("sample_content モジュールが見つかりません")
        
        # 一時ファイルにサンプルコンテンツを保存
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(SHOWCASE_SAMPLE)
            temp_path = Path(f.name)
        
        try:
            validator = SyntaxValidator()
            errors = validator.validate_file(temp_path)
            
            if errors:
                print(f"\n[エラー] SHOWCASE_SAMPLE: {len(errors)} エラー")
                for error in errors:
                    print(f"   Line {error.line_number}: {error.message}")
                    if error.suggestion:
                        print(f"      [ヒント] {error.suggestion}")
            
            assert len(errors) == 0, f"SHOWCASE_SAMPLE に {len(errors)} 個のエラーがあります"
        
        finally:
            # 一時ファイルを削除
            os.unlink(temp_path)


if __name__ == "__main__":
    # テスト実行時のカスタムオプション
    pytest.main([__file__, "-v", "--tb=short"])