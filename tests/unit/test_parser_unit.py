"""
Parserクラスのユニットテスト

Critical Tier対応: コア機能の基本動作確認
Issue #620: テストカバレッジ改善
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.parser import Parser, parse


class TestParser:
    """Parserクラスのテスト"""

    def setup_method(self):
        """各テストの前にセットアップ"""
        self.parser = Parser()

    def test_parser_initialization(self):
        """パーサーの初期化テスト"""
        parser = Parser()

        # 基本属性の確認
        assert parser.config is None
        assert parser.lines == []
        assert parser.current == 0
        assert parser.errors == []
        assert parser.logger is not None

        # 特化パーサーの初期化確認
        assert parser.keyword_parser is not None
        assert parser.list_parser is not None
        assert parser.block_parser is not None

    def test_parser_initialization_with_config(self):
        """設定ありでのパーサー初期化テスト"""
        config = {"test": "value"}
        parser = Parser(config)

        # configは無視される（仕様通り）
        assert parser.config is None

    @patch("kumihan_formatter.parser.get_logger")
    def test_parser_initialization_logging(self, mock_get_logger):
        """ログ出力を含む初期化テスト"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        parser = Parser()

        mock_get_logger.assert_called_once_with("kumihan_formatter.parser")
        mock_logger.debug.assert_called_once_with(
            "Parser initialized with specialized parsers"
        )

    def test_parse_empty_text(self):
        """空文字列のパーステスト"""
        result = self.parser.parse("")

        assert result == []
        assert self.parser.lines == [""]
        assert self.parser.current == 1
        assert self.parser.errors == []

    def test_parse_simple_text(self):
        """シンプルなテキストのパーステスト"""
        text = "Hello World"

        # block_parserのparse_paragraphをモック
        mock_node = Mock(spec=Node)
        mock_node.type = "paragraph"

        with patch.object(self.parser.block_parser, "skip_empty_lines", return_value=0):
            with patch.object(
                self.parser.block_parser, "parse_paragraph", return_value=(mock_node, 1)
            ):
                result = self.parser.parse(text)

        assert len(result) == 1
        assert result[0] == mock_node
        assert self.parser.lines == ["Hello World"]

    def test_parse_multiple_lines(self):
        """複数行テキストのパーステスト"""
        text = "Line 1\nLine 2\nLine 3"

        mock_node = Mock(spec=Node)
        mock_node.type = "paragraph"

        # currentを返して次の行に進むside_effectを使用
        with patch.object(
            self.parser.block_parser,
            "skip_empty_lines",
            side_effect=lambda lines, current: current,
        ):
            with patch.object(
                self.parser.block_parser,
                "parse_paragraph",
                side_effect=[(mock_node, 1), (mock_node, 2), (mock_node, 3)],
            ):
                result = self.parser.parse(text)

        assert len(result) == 3
        assert self.parser.lines == ["Line 1", "Line 2", "Line 3"]

    def test_parse_with_comments(self):
        """コメント行を含むテキストのパーステスト"""
        text = "# Comment\nActual content"

        mock_node = Mock(spec=Node)
        mock_node.type = "paragraph"

        with patch.object(
            self.parser.block_parser, "skip_empty_lines", side_effect=[0, 1]
        ):
            with patch.object(
                self.parser.block_parser, "parse_paragraph", return_value=(mock_node, 2)
            ):
                result = self.parser.parse(text)

        # コメント行はスキップされ、実際のコンテンツのみパース
        assert len(result) == 1
        assert result[0] == mock_node

    def test_parse_with_block_markers(self):
        """ブロックマーカーを含むテキストのパーステスト"""
        text = ";;;bold;;; content ;;;"

        mock_node = Mock(spec=Node)
        mock_node.type = "block"

        with patch.object(self.parser.block_parser, "skip_empty_lines", return_value=0):
            with patch.object(
                self.parser.block_parser, "is_opening_marker", return_value=True
            ):
                with patch.object(
                    self.parser.block_parser,
                    "parse_block_marker",
                    return_value=(mock_node, 1),
                ):
                    result = self.parser.parse(text)

        assert len(result) == 1
        assert result[0] == mock_node

    def test_parse_with_unordered_list(self):
        """順序なしリストのパーステスト"""
        text = "- Item 1\n- Item 2"

        mock_node = Mock(spec=Node)
        mock_node.type = "ul"

        with patch.object(self.parser.block_parser, "skip_empty_lines", return_value=0):
            with patch.object(
                self.parser.block_parser, "is_opening_marker", return_value=False
            ):
                with patch.object(
                    self.parser.list_parser, "is_list_line", return_value="ul"
                ):
                    with patch.object(
                        self.parser.list_parser,
                        "parse_unordered_list",
                        return_value=(mock_node, 2),
                    ):
                        result = self.parser.parse(text)

        assert len(result) == 1
        assert result[0] == mock_node

    def test_parse_with_ordered_list(self):
        """順序ありリストのパーステスト"""
        text = "1. Item 1\n2. Item 2"

        mock_node = Mock(spec=Node)
        mock_node.type = "ol"

        with patch.object(self.parser.block_parser, "skip_empty_lines", return_value=0):
            with patch.object(
                self.parser.block_parser, "is_opening_marker", return_value=False
            ):
                with patch.object(
                    self.parser.list_parser, "is_list_line", return_value="ol"
                ):
                    with patch.object(
                        self.parser.list_parser,
                        "parse_ordered_list",
                        return_value=(mock_node, 2),
                    ):
                        result = self.parser.parse(text)

        assert len(result) == 1
        assert result[0] == mock_node

    def test_parse_line_beyond_bounds(self):
        """範囲外アクセス時の動作テスト"""
        self.parser.lines = ["test"]
        self.parser.current = 1  # 範囲外

        result = self.parser._parse_line()

        assert result is None

    def test_parse_line_empty_lines_skipped(self):
        """空行スキップの動作テスト"""
        self.parser.lines = ["", "", "content"]
        self.parser.current = 0

        mock_node = Mock(spec=Node)

        with patch.object(self.parser.block_parser, "skip_empty_lines", return_value=3):
            result = self.parser._parse_line()

        assert result is None
        assert self.parser.current == 3

    def test_get_errors(self):
        """エラー取得テスト"""
        self.parser.errors = ["Error 1", "Error 2"]

        result = self.parser.get_errors()

        assert result == ["Error 1", "Error 2"]

    @patch("kumihan_formatter.parser.get_logger")
    def test_add_error(self, mock_get_logger):
        """エラー追加テスト"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        parser = Parser()
        parser.add_error("Test error")

        assert "Test error" in parser.errors
        mock_logger.warning.assert_called_with("Parse error: Test error")

    def test_get_statistics(self):
        """統計情報取得テスト"""
        self.parser.lines = ["line1", "line2", "line3"]
        self.parser.errors = ["error1"]
        self.parser.block_parser.heading_counter = 2

        stats = self.parser.get_statistics()

        assert stats["total_lines"] == 3
        assert stats["errors_count"] == 1
        assert stats["heading_count"] == 2


class TestParseFunction:
    """parse関数のテスト"""

    @patch("kumihan_formatter.parser.Parser")
    def test_parse_function_creates_parser(self, mock_parser_class):
        """parse関数がParserインスタンスを作成することを確認"""
        mock_parser = Mock()
        mock_parser.parse.return_value = [Mock(spec=Node)]
        mock_parser_class.return_value = mock_parser

        result = parse("test text")

        mock_parser_class.assert_called_once_with(None)
        mock_parser.parse.assert_called_once_with("test text")
        assert len(result) == 1

    @patch("kumihan_formatter.parser.Parser")
    def test_parse_function_with_config(self, mock_parser_class):
        """設定ありでのparse関数テスト"""
        mock_parser = Mock()
        mock_parser.parse.return_value = []
        mock_parser_class.return_value = mock_parser

        config = {"test": "config"}
        result = parse("test", config)

        mock_parser_class.assert_called_once_with(config)
        assert result == []


class TestParserIntegration:
    """Parser統合テスト（モックを使わない基本動作確認）"""

    def test_parser_basic_functionality(self):
        """パーサーの基本機能テスト"""
        parser = Parser()

        # 最低限の動作確認
        assert parser is not None
        assert hasattr(parser, "parse")
        assert hasattr(parser, "get_errors")
        assert hasattr(parser, "get_statistics")

    def test_parse_function_basic_functionality(self):
        """parse関数の基本機能テスト"""
        # 最低限の動作確認
        result = parse("")
        assert isinstance(result, list)
