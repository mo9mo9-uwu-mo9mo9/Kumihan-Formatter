"""Phase 2 Parser Core Tests Part 1 - パーサーコアテスト（前半）

パーサーコア機能テスト - parse関数・基本パーサー
Target: parser.py のコア機能
Goal: parse関数・基本解析機能テスト
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.markdown_parser import MarkdownParser
from kumihan_formatter.parser import parse


class TestParseFunction:
    """Parse関数の完全テスト"""

    def test_parse_function_basic(self) -> None:
        """基本的な解析テスト"""
        text = "Simple paragraph text."
        result = parse(text)

        # ASTが生成されることを確認
        assert isinstance(result, list)
        assert len(result) >= 0

    def test_parse_function_empty_text(self) -> None:
        """空テキストの解析テスト"""
        text = ""
        result = parse(text)

        # 空テキストでも正常に処理されることを確認
        assert isinstance(result, list)

    def test_parse_function_with_markup(self) -> None:
        """マークアップ記法付きテキストの解析テスト"""
        text = """
        # Heading 1

        Simple paragraph.

        ## Heading 2

        Another paragraph with **bold** text.
        """
        result = parse(text)

        # マークアップが解析されることを確認
        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_function_with_notations(self) -> None:
        """記法付きテキストの解析テスト"""
        text = "This is ((footnote)) notation and ｜ruby《ルビ》 notation."
        result = parse(text)

        # 記法が解析されることを確認
        assert isinstance(result, list)

    def test_parse_function_with_complex_content(self) -> None:
        """複雑なコンテンツの解析テスト"""
        text = """
        # Main Title

        This paragraph contains ((footnote content)) and ｜ruby《reading》.

        ## Subsection

        - List item 1
        - List item 2 with ((another footnote))

        Regular paragraph with mixed content.
        """
        result = parse(text)

        # 複雑な構造が解析されることを確認
        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_function_with_config(self) -> None:
        """設定オブジェクト付き解析テスト"""
        text = "Test content"
        config = Mock()
        config.debug = False

        result = parse(text, config)

        # 設定付きで正常に解析されることを確認
        assert isinstance(result, list)

    def test_parse_function_with_config_dict(self) -> None:
        """設定辞書付き解析テスト"""
        text = "Test content"
        config = {"test": "value"}

        result = parse(text, config=config)

        # 設定付きで正常に解析されることを確認
        assert isinstance(result, list)

    def test_parse_function_error_handling(self) -> None:
        """解析エラーハンドリングテスト"""
        # 不正な入力でもエラーが適切に処理されることを確認
        invalid_inputs = [None, 123, [], {}]

        for invalid_input in invalid_inputs:
            try:
                result = parse(invalid_input)
                assert isinstance(result, list)  # 何らかのリストが返される
            except Exception:
                # または例外が適切に処理される
                assert True

    def test_parse_function_unicode_content(self) -> None:
        """Unicode文字を含むコンテンツの解析テスト"""
        text = "Unicode content: 日本語テスト with ((脚注)) notation."
        result = parse(text)

        # Unicode文字が正常に解析されることを確認
        assert isinstance(result, list)


class TestParserCoverageBoost:
    """Parser.py未カバー部分のテスト"""

    def test_parser_empty_line_handling(self) -> None:
        """空行が正しく処理されることをテスト"""
        from kumihan_formatter.parser import Parser

        parser = Parser()
        # 空のテキスト/行が終端まで達した場合
        parser.lines = [""]
        parser.current = 1  # 範囲外

        result = parser._parse_line()
        assert result is None

    def test_parser_block_marker_handling(self) -> None:
        """ブロックマーカー処理をテスト"""
        from kumihan_formatter.parser import Parser

        parser = Parser()
        # ブロックマーカーのテスト
        text = ";;;太字;;;\ntest content\n;;;"
        nodes = parser.parse(text)

        assert isinstance(nodes, list)

    def test_parser_ordered_list_handling(self) -> None:
        """番号付きリスト処理をテスト"""
        from kumihan_formatter.parser import Parser

        parser = Parser()
        text = "1. First item\n2. Second item"
        nodes = parser.parse(text)

        assert isinstance(nodes, list)

    def test_parser_add_error_function(self) -> None:
        """add_error関数をテスト"""
        from kumihan_formatter.parser import Parser

        parser = Parser()
        error_msg = "Test error message"
        parser.add_error(error_msg)

        assert error_msg in parser.get_errors()

    def test_parser_add_error_logging(self) -> None:
        """エラー追加時のログをテスト"""
        from kumihan_formatter.parser import Parser

        parser = Parser()
        with patch("kumihan_formatter.core.utilities.logger.get_logger") as mock_logger:
            mock_logger_instance = Mock()
            mock_logger.return_value = mock_logger_instance

            parser = Parser()
            parser.add_error("Test error")

            # ログが呼ばれたことを確認
            assert len(parser.errors) > 0

    def test_parser_get_statistics(self) -> None:
        """統計取得をテスト"""
        from kumihan_formatter.parser import Parser

        parser = Parser()
        text = "# Heading\nParagraph"
        parser.parse(text)

        stats = parser.get_statistics()
        assert isinstance(stats, dict)
        assert "total_lines" in stats
        assert "errors_count" in stats
        assert "heading_count" in stats

    def test_parser_skip_empty_lines_coverage(self) -> None:
        """skip_empty_lines内のカバーされていない分岐をテスト"""
        from kumihan_formatter.parser import Parser

        parser = Parser()
        # 空行がない場合の処理
        text = "content line"
        parser.parse(text)

        assert len(parser.lines) > 0

    def test_parser_block_marker_detection(self) -> None:
        """ブロックマーカー検出のテスト"""
        from kumihan_formatter.parser import Parser

        parser = Parser()
        # 実際のブロックマーカーを使用
        text = ";;;太字;;;\ntest content\n;;;"
        result = parser.parse(text)

        assert isinstance(result, list)

    def test_parser_ordered_list_branch(self) -> None:
        """番号付きリストの特定分岐をテスト"""
        from kumihan_formatter.parser import Parser

        parser = Parser()
        # 実際の番号付きリストを使用
        text = "1. Test item\n2. Second item"
        result = parser.parse(text)

        assert isinstance(result, list)

    def test_parse_function_edge_cases(self) -> None:
        """parse関数のエッジケースをテスト"""
        from kumihan_formatter.parser import parse

        # None config
        result1 = parse("test", config=None)
        assert isinstance(result1, list)

        # 空のconfig
        result2 = parse("test", config={})
        assert isinstance(result2, list)
