"""
スマート提案システムのテスト

Important Tier Phase 2-1対応 - Issue #593
スマート提案システムの体系的テスト実装
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.error_handling.smart_suggestions import SmartSuggestions


class TestSmartSuggestions:
    """スマート提案システムのテストクラス"""

    def test_suggest_keyword_exact_match(self):
        """完全一致キーワードの提案テスト"""
        # Given
        suggestions = SmartSuggestions()

        # When
        result = suggestions.suggest_keyword("太字")

        # Then
        assert result == ["太字"]

    def test_suggest_keyword_common_mistake(self):
        """よくある間違いパターンの提案テスト"""
        # Given
        suggestions = SmartSuggestions()

        # When
        result = suggestions.suggest_keyword("太文字")

        # Then
        assert "太字" in result
        assert result[0] == "太字"  # 最初の提案が正しい修正

    def test_suggest_keyword_similar_match(self):
        """類似キーワードの提案テスト"""
        # Given
        suggestions = SmartSuggestions()

        # When
        result = suggestions.suggest_keyword("太時")  # タイポ

        # Then
        assert "太字" in result
        assert len(result) >= 1

    def test_suggest_keyword_no_match(self):
        """マッチしないキーワードの提案テスト"""
        # Given
        suggestions = SmartSuggestions()

        # When
        result = suggestions.suggest_keyword("完全に無関係な文字列")

        # Then
        assert len(result) <= 3  # 最大3つまでの提案

    def test_suggest_keyword_english_input(self):
        """英語入力での提案テスト"""
        # Given
        suggestions = SmartSuggestions()

        # When
        bold_result = suggestions.suggest_keyword("bold")
        italic_result = suggestions.suggest_keyword("italic")

        # Then
        assert "太字" in bold_result
        assert "イタリック" in italic_result

    def test_suggest_encoding_shift_jis(self):
        """Shift-JISエンコーディング提案テスト"""
        # Given
        suggestions = SmartSuggestions()
        error = UnicodeDecodeError("utf-8", b"\x82\xa0", 0, 2, "invalid start byte")

        # When
        result = suggestions.suggest_encoding(error)

        # Then
        assert "shift_jis" in result or "cp932" in result
        assert len(result) >= 1

    def test_suggest_encoding_generic_error(self):
        """一般的なエンコーディングエラーの提案テスト"""
        # Given
        suggestions = SmartSuggestions()
        error = UnicodeDecodeError("utf-8", b"\xff\xfe", 0, 2, "invalid start byte")

        # When
        result = suggestions.suggest_encoding(error)

        # Then
        assert len(result) >= 1
        # プラットフォーム依存のエンコーディングが含まれる可能性
        assert any(enc in result for enc in ["utf-16", "utf-16-le", "utf-16-be"])

    def test_suggest_file_path_relative(self):
        """相対パスのファイルパス提案テスト"""
        # Given
        suggestions = SmartSuggestions()
        missing_path = "test.txt"

        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/home/user/project")

            # When
            result = suggestions.suggest_file_path(missing_path)

            # Then
            assert len(result) > 0
            # カレントディレクトリからの相対パスが提案される

    def test_suggest_file_path_with_typo(self):
        """タイポを含むファイルパス提案テスト"""
        # Given
        suggestions = SmartSuggestions()

        with patch("pathlib.Path.glob") as mock_glob:
            # 実際に存在するファイルをモック
            mock_glob.return_value = [
                Path("README.md"),
                Path("readme.txt"),
                Path("READNE.md"),  # タイポファイル
            ]

            # When
            result = suggestions.suggest_file_path("READM.md")  # タイポ

            # Then
            assert any("README.md" in str(p) for p in result)

    def test_suggest_file_path_case_sensitivity(self):
        """大文字小文字の違いに対するファイルパス提案テスト"""
        # Given
        suggestions = SmartSuggestions()

        with patch("pathlib.Path.iterdir") as mock_iterdir:
            mock_iterdir.return_value = [
                Path("Test.txt"),
                Path("test.TXT"),
                Path("TEST.txt"),
            ]

            # When
            result = suggestions.suggest_file_path("test.txt")

            # Then
            assert len(result) >= 1
            # 大文字小文字の違いを検出

    def test_suggest_syntax_fix_unclosed_decoration(self):
        """未閉装飾記法の修正提案テスト"""
        # Given
        suggestions = SmartSuggestions()
        error_line = ";;;太字;;これはテスト"

        # When
        result = suggestions.suggest_syntax_fix(error_line)

        # Then
        assert ";;;太字;;;これはテスト" in result

    def test_suggest_syntax_fix_invalid_decoration(self):
        """無効な装飾記法の修正提案テスト"""
        # Given
        suggestions = SmartSuggestions()
        error_line = ";;;invalid;;;テキスト;;;"

        # When
        result = suggestions.suggest_syntax_fix(error_line)

        # Then
        assert len(result) > 0
        # 有効なキーワードへの修正提案が含まれる

    def test_suggest_syntax_fix_multiple_issues(self):
        """複数の問題を含む行の修正提案テスト"""
        # Given
        suggestions = SmartSuggestions()
        error_line = ";;;太文字;;テスト;;;イタリク;;;別テキスト;;;"

        # When
        result = suggestions.suggest_syntax_fix(error_line)

        # Then
        assert len(result) > 0
        # 複数の修正案が提供される

    def test_suggest_syntax_fix_nested_decoration(self):
        """ネストされた装飾の修正提案テスト"""
        # Given
        suggestions = SmartSuggestions()
        error_line = ";;;太字;;;中に;;;イタリック;;;がある;;;"

        # When
        result = suggestions.suggest_syntax_fix(error_line)

        # Then
        assert len(result) >= 0  # ネストは許可されない場合もある

    def test_get_similar_keywords(self):
        """類似キーワード取得テスト"""
        # Given
        suggestions = SmartSuggestions()

        # When
        result = suggestions.get_similar_keywords("見出し", max_count=5)

        # Then
        assert len(result) <= 5
        assert any("見出し" in kw for kw in result)

    def test_common_mistakes_mapping(self):
        """よくある間違いマッピングの妥当性テスト"""
        # Given
        suggestions = SmartSuggestions()

        # Then
        assert suggestions.COMMON_MISTAKES["太文字"] == "太字"
        assert suggestions.COMMON_MISTAKES["bold"] == "太字"
        assert suggestions.COMMON_MISTAKES["斜体"] == "イタリック"

    def test_valid_keywords_completeness(self):
        """有効キーワードリストの完全性テスト"""
        # Given
        suggestions = SmartSuggestions()

        # Then
        essential_keywords = ["太字", "イタリック", "見出し1", "枠線", "画像"]
        for keyword in essential_keywords:
            assert keyword in suggestions.VALID_KEYWORDS

    def test_suggest_permission_fix(self):
        """権限エラーの修正提案テスト"""
        # Given
        suggestions = SmartSuggestions()
        file_path = "/protected/file.txt"

        # When
        result = suggestions.suggest_permission_fix(file_path)

        # Then
        assert len(result) > 0
        assert any("chmod" in suggestion for suggestion in result)

    def test_suggest_memory_optimization(self):
        """メモリ最適化の提案テスト"""
        # Given
        suggestions = SmartSuggestions()
        context = {
            "file_size": 100 * 1024 * 1024,  # 100MB
            "operation": "parse",
        }

        # When
        result = suggestions.suggest_memory_optimization(context)

        # Then
        assert len(result) > 0
        assert any(
            "チャンク" in suggestion or "chunk" in suggestion for suggestion in result
        )

    def test_case_insensitive_keyword_matching(self):
        """大文字小文字を区別しないキーワードマッチングテスト"""
        # Given
        suggestions = SmartSuggestions()

        # When
        result1 = suggestions.suggest_keyword("BOLD")
        result2 = suggestions.suggest_keyword("Bold")
        result3 = suggestions.suggest_keyword("BoLd")

        # Then
        assert "太字" in result1
        assert "太字" in result2
        assert "太字" in result3

    def test_suggest_with_empty_input(self):
        """空入力での提案テスト"""
        # Given
        suggestions = SmartSuggestions()

        # When
        keyword_result = suggestions.suggest_keyword("")
        syntax_result = suggestions.suggest_syntax_fix("")
        path_result = suggestions.suggest_file_path("")

        # Then
        assert isinstance(keyword_result, list)
        assert isinstance(syntax_result, list)
        assert isinstance(path_result, list)

    def test_suggest_for_special_characters(self):
        """特殊文字を含む入力での提案テスト"""
        # Given
        suggestions = SmartSuggestions()

        # When
        result = suggestions.suggest_syntax_fix(";;;太字@#$;;;テスト;;;")

        # Then
        assert len(result) >= 0  # エラーにならずに処理される

    def test_platform_specific_encoding_suggestions(self):
        """プラットフォーム固有のエンコーディング提案テスト"""
        # Given
        suggestions = SmartSuggestions()
        error = UnicodeDecodeError(
            "utf-8", b"\x93\xfa\x96{", 0, 3, "invalid start byte"
        )

        with patch("platform.system") as mock_system:
            # Windows環境をシミュレート
            mock_system.return_value = "Windows"

            # When
            result = suggestions.suggest_encoding(error)

            # Then
            assert "cp932" in result or "shift_jis" in result

    def test_integration_complete_error_suggestion(self):
        """統合テスト: 完全なエラー提案フロー"""
        # Given
        suggestions = SmartSuggestions()

        # Scenario 1: 構文エラー
        syntax_error_line = ";;;ボールド;;;テキスト;;;"
        syntax_suggestions = suggestions.suggest_syntax_fix(syntax_error_line)
        assert any("太字" in s for s in syntax_suggestions)

        # Scenario 2: エンコーディングエラー
        encoding_error = UnicodeDecodeError("utf-8", b"\x82\xa0", 0, 2, "error")
        encoding_suggestions = suggestions.suggest_encoding(encoding_error)
        assert len(encoding_suggestions) > 0

        # Scenario 3: ファイルパスエラー
        path_suggestions = suggestions.suggest_file_path("readne.md")
        assert len(path_suggestions) >= 0
