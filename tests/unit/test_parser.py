"""パーサー機能の包括的なユニットテスト

Issue #466対応: テストカバレッジ向上（パーサー系 74% → 80%以上）
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.parser import Parser, parse


class TestParserInitialization(TestCase):
    """パーサーの初期化テスト"""

    def test_parser_init_default(self) -> None:
        """デフォルト設定でのパーサー初期化テスト"""
        parser = Parser()

        self.assertIsNone(parser.config)
        self.assertEqual(parser.lines, [])
        self.assertEqual(parser.current, 0)
        self.assertEqual(parser.errors, [])
        self.assertIsNotNone(parser.keyword_parser)
        self.assertIsNotNone(parser.list_parser)
        self.assertIsNotNone(parser.block_parser)

    def test_parser_init_with_config(self) -> None:
        """設定付きでのパーサー初期化テスト"""
        config = {"test": "value"}
        parser = Parser(config)

        # configは無視されることを確認
        self.assertIsNone(parser.config)

    def test_parser_specialized_parsers_initialization(self) -> None:
        """特化パーサーの初期化テスト"""
        with patch("kumihan_formatter.parser.KeywordParser") as mock_keyword:
            with patch("kumihan_formatter.parser.ListParser") as mock_list:
                with patch("kumihan_formatter.parser.BlockParser") as mock_block:
                    mock_keyword_instance = MagicMock()
                    mock_keyword.return_value = mock_keyword_instance

                    parser = Parser()

                    mock_keyword.assert_called_once()
                    mock_list.assert_called_once_with(mock_keyword_instance)
                    mock_block.assert_called_once_with(mock_keyword_instance)


class TestParserBasicParsing(TestCase):
    """パーサーの基本解析機能テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.parser = Parser()

    def test_parse_empty_text(self) -> None:
        """空テキストの解析テスト"""
        result = self.parser.parse("")

        self.assertEqual(result, [])
        self.assertEqual(len(self.parser.get_errors()), 0)

    def test_parse_simple_text(self) -> None:
        """単純テキストの解析テスト"""
        text = "これはテストです"

        # モックを設定してparagraphが返されることをテスト
        with patch.object(self.parser.block_parser, "parse_paragraph") as mock_parse:
            mock_node = Node("paragraph", {"content": text})
            mock_parse.return_value = (mock_node, 1)

            result = self.parser.parse(text)

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].type, "paragraph")
            mock_parse.assert_called_once()

    def test_parse_multiline_text(self) -> None:
        """複数行テキストの解析テスト"""
        text = "行1\n行2\n行3"

        with patch.object(self.parser.block_parser, "parse_paragraph") as mock_parse:
            # 各行がparagraphとして処理されることをシミュレート
            def side_effect(lines, current):
                content = lines[current] if current < len(lines) else ""
                return (Node("paragraph", {"content": content}), current + 1)

            mock_parse.side_effect = side_effect

            result = self.parser.parse(text)

            self.assertEqual(len(result), 3)
            self.assertEqual(mock_parse.call_count, 3)

    def test_parse_with_empty_lines(self) -> None:
        """空行を含むテキストの解析テスト"""
        text = "行1\n\n行3"

        with patch.object(self.parser.block_parser, "skip_empty_lines") as mock_skip:
            with patch.object(
                self.parser.block_parser, "parse_paragraph"
            ) as mock_parse:
                # skip_empty_linesが適切に呼ばれることを確認
                mock_skip.side_effect = lambda lines, current: current
                mock_parse.return_value = (Node("paragraph", {"content": "test"}), 1)

                self.parser.parse(text)

                # skip_empty_linesが呼ばれることを確認
                self.assertTrue(mock_skip.called)

    def test_parse_comment_lines(self) -> None:
        """コメント行の解析テスト"""
        text = "# これはコメント\n実際のテキスト"

        with patch.object(self.parser.block_parser, "parse_paragraph") as mock_parse:
            mock_parse.return_value = (
                Node("paragraph", {"content": "実際のテキスト"}),
                2,
            )

            result = self.parser.parse(text)

            # コメント行はスキップされ、実際のテキストのみ処理される
            self.assertEqual(len(result), 1)


class TestParserLineTypeParsing(TestCase):
    """パーサーの行タイプ解析テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.parser = Parser()

    def test_parse_block_marker(self) -> None:
        """ブロックマーカーの解析テスト"""
        text = ";;;code;;;\nコード内容\n;;;"

        with patch.object(
            self.parser.block_parser, "is_opening_marker"
        ) as mock_is_marker:
            with patch.object(
                self.parser.block_parser, "parse_block_marker"
            ) as mock_parse_block:
                mock_is_marker.return_value = True
                mock_node = Node("code_block", {"content": "コード内容"})
                mock_parse_block.return_value = (mock_node, 3)

                result = self.parser.parse(text)

                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].type, "code_block")
                mock_parse_block.assert_called_once()

    def test_parse_unordered_list(self) -> None:
        """順序なしリストの解析テスト"""
        text = "- 項目1\n- 項目2"

        with patch.object(self.parser.list_parser, "is_list_line") as mock_is_list:
            with patch.object(
                self.parser.list_parser, "parse_unordered_list"
            ) as mock_parse_ul:
                mock_is_list.return_value = "ul"
                mock_node = Node("ul", {"items": ["項目1", "項目2"]})
                mock_parse_ul.return_value = (mock_node, 2)

                result = self.parser.parse(text)

                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].type, "ul")
                mock_parse_ul.assert_called_once()

    def test_parse_ordered_list(self) -> None:
        """順序ありリストの解析テスト"""
        text = "1. 項目1\n2. 項目2"

        with patch.object(self.parser.list_parser, "is_list_line") as mock_is_list:
            with patch.object(
                self.parser.list_parser, "parse_ordered_list"
            ) as mock_parse_ol:
                mock_is_list.return_value = "ol"
                mock_node = Node("ol", {"items": ["項目1", "項目2"]})
                mock_parse_ol.return_value = (mock_node, 2)

                result = self.parser.parse(text)

                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].type, "ol")
                mock_parse_ol.assert_called_once()

    def test_parse_paragraph_fallback(self) -> None:
        """段落のフォールバック解析テスト"""
        text = "通常の段落テキスト"

        with patch.object(
            self.parser.block_parser, "is_opening_marker"
        ) as mock_is_marker:
            with patch.object(self.parser.list_parser, "is_list_line") as mock_is_list:
                with patch.object(
                    self.parser.block_parser, "parse_paragraph"
                ) as mock_parse_para:
                    mock_is_marker.return_value = False
                    mock_is_list.return_value = None
                    mock_node = Node("paragraph", {"content": text})
                    mock_parse_para.return_value = (mock_node, 1)

                    result = self.parser.parse(text)

                    self.assertEqual(len(result), 1)
                    self.assertEqual(result[0].type, "paragraph")
                    mock_parse_para.assert_called_once()


class TestParserErrorHandling(TestCase):
    """パーサーのエラーハンドリングテスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.parser = Parser()

    def test_get_errors_empty(self) -> None:
        """エラーなしの場合のテスト"""
        errors = self.parser.get_errors()
        self.assertEqual(errors, [])

    def test_add_error(self) -> None:
        """エラー追加のテスト"""
        error_message = "テストエラー"

        self.parser.add_error(error_message)

        errors = self.parser.get_errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], error_message)

    def test_add_multiple_errors(self) -> None:
        """複数エラー追加のテスト"""
        error1 = "エラー1"
        error2 = "エラー2"

        self.parser.add_error(error1)
        self.parser.add_error(error2)

        errors = self.parser.get_errors()
        self.assertEqual(len(errors), 2)
        self.assertIn(error1, errors)
        self.assertIn(error2, errors)

    def test_parse_line_out_of_bounds(self) -> None:
        """範囲外の行解析テスト"""
        self.parser.lines = ["テスト"]
        self.parser.current = 10  # 範囲外のインデックス

        result = self.parser._parse_line()

        self.assertIsNone(result)


class TestParserStatistics(TestCase):
    """パーサーの統計情報テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.parser = Parser()

    def test_get_statistics_empty(self) -> None:
        """空の統計情報テスト"""
        stats = self.parser.get_statistics()

        self.assertIn("total_lines", stats)
        self.assertIn("errors_count", stats)
        self.assertIn("heading_count", stats)
        self.assertEqual(stats["total_lines"], 0)
        self.assertEqual(stats["errors_count"], 0)

    def test_get_statistics_after_parse(self) -> None:
        """解析後の統計情報テスト"""
        text = "行1\n行2\n行3"

        with patch.object(self.parser.block_parser, "parse_paragraph") as mock_parse:
            mock_parse.return_value = (Node("paragraph", {"content": "test"}), 1)

            self.parser.parse(text)

            stats = self.parser.get_statistics()
            self.assertEqual(stats["total_lines"], 3)

    def test_get_statistics_with_errors(self) -> None:
        """エラー含む統計情報テスト"""
        self.parser.add_error("テストエラー1")
        self.parser.add_error("テストエラー2")

        stats = self.parser.get_statistics()
        self.assertEqual(stats["errors_count"], 2)


class TestParserIntegration(TestCase):
    """パーサーの統合テスト"""

    def test_parse_mixed_content(self) -> None:
        """混合コンテンツの解析テスト"""
        text = """# コメント
通常の段落

- リスト項目1
- リスト項目2

;;;code;;;
コード内容
;;;"""

        parser = Parser()

        with patch.object(parser.block_parser, "is_opening_marker") as mock_is_marker:
            with patch.object(parser.list_parser, "is_list_line") as mock_is_list:
                with patch.object(
                    parser.block_parser, "parse_paragraph"
                ) as mock_parse_para:
                    with patch.object(
                        parser.list_parser, "parse_unordered_list"
                    ) as mock_parse_ul:
                        with patch.object(
                            parser.block_parser, "parse_block_marker"
                        ) as mock_parse_block:
                            # モックの設定
                            mock_is_marker.side_effect = lambda line: line.startswith(
                                ";;;"
                            )
                            mock_is_list.side_effect = lambda line: (
                                "ul" if line.startswith("-") else None
                            )
                            mock_parse_para.return_value = (Node("paragraph", {}), 1)
                            mock_parse_ul.return_value = (Node("ul", {}), 2)
                            mock_parse_block.return_value = (Node("code_block", {}), 3)

                            result = parser.parse(text)

                            # 結果の確認（コメント行は除外される）
                            self.assertGreater(len(result), 0)

    def test_parser_state_reset(self) -> None:
        """パーサー状態のリセットテスト"""
        parser = Parser()

        # 初回解析
        parser.parse("テスト1")
        first_lines = len(parser.lines)

        # 2回目解析
        parser.parse("テスト2\n別の行")
        second_lines = len(parser.lines)

        # 状態がリセットされることを確認
        self.assertEqual(parser.current, 0)
        self.assertEqual(second_lines, 2)
        self.assertNotEqual(first_lines, second_lines)


class TestParseFunction(TestCase):
    """parse関数のテスト"""

    def test_parse_function_basic(self) -> None:
        """parse関数の基本動作テスト"""
        text = "テストテキスト"

        with patch("kumihan_formatter.parser.Parser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse.return_value = [Node("paragraph", {"content": text})]
            mock_parser_class.return_value = mock_parser

            result = parse(text)

            mock_parser_class.assert_called_once_with(None)
            mock_parser.parse.assert_called_once_with(text)
            self.assertEqual(len(result), 1)

    def test_parse_function_with_config(self) -> None:
        """設定付きparse関数のテスト"""
        text = "テストテキスト"
        config = {"test": "value"}

        with patch("kumihan_formatter.parser.Parser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse.return_value = []
            mock_parser_class.return_value = mock_parser

            result = parse(text, config)

            mock_parser_class.assert_called_once_with(config)
            mock_parser.parse.assert_called_once_with(text)

    def test_parse_function_compatibility(self) -> None:
        """parse関数の互換性テスト"""
        # 実際のParserクラスを使用して互換性を確認
        text = "テストテキスト"

        with patch.object(Parser, "parse") as mock_parse:
            mock_parse.return_value = [Node("test", {})]

            result = parse(text)

            self.assertEqual(len(result), 1)
            mock_parse.assert_called_once_with(text)


class TestParserLogging(TestCase):
    """パーサーのログ機能テスト"""

    def test_parser_logging_initialization(self) -> None:
        """ログ初期化のテスト"""
        with patch("kumihan_formatter.parser.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            parser = Parser()

            mock_get_logger.assert_called_once_with("kumihan_formatter.parser")
            self.assertEqual(parser.logger, mock_logger)
            mock_logger.debug.assert_called_with(
                "Parser initialized with specialized parsers"
            )

    def test_parser_logging_during_parse(self) -> None:
        """解析中のログテスト"""
        parser = Parser()

        with patch.object(parser.logger, "info") as mock_info:
            with patch.object(parser.logger, "debug") as mock_debug:
                with patch.object(parser.block_parser, "parse_paragraph") as mock_parse:
                    mock_parse.return_value = (Node("paragraph", {}), 1)

                    parser.parse("テスト")

                    # ログが適切に出力されることを確認
                    mock_info.assert_called()
                    mock_debug.assert_called()

    def test_add_error_logging(self) -> None:
        """エラー追加時のログテスト"""
        parser = Parser()

        with patch.object(parser.logger, "warning") as mock_warning:
            error_message = "テストエラー"

            parser.add_error(error_message)

            mock_warning.assert_called_once_with(f"Parse error: {error_message}")


class TestParserEdgeCases(TestCase):
    """パーサーのエッジケーステスト"""

    def test_parse_very_long_line(self) -> None:
        """非常に長い行の解析テスト"""
        long_line = "a" * 1000
        parser = Parser()

        with patch.object(parser.block_parser, "parse_paragraph") as mock_parse:
            mock_parse.return_value = (Node("paragraph", {"content": long_line}), 1)

            result = parser.parse(long_line)

            self.assertEqual(len(result), 1)

    def test_parse_unicode_content(self) -> None:
        """Unicode文字の解析テスト"""
        unicode_text = "日本語テキスト 🎌 絵文字付き"
        parser = Parser()

        with patch.object(parser.block_parser, "parse_paragraph") as mock_parse:
            mock_parse.return_value = (Node("paragraph", {"content": unicode_text}), 1)

            result = parser.parse(unicode_text)

            self.assertEqual(len(result), 1)

    def test_parse_only_whitespace(self) -> None:
        """空白のみのテキスト解析テスト"""
        whitespace_text = "   \n\t\n   "
        parser = Parser()

        with patch.object(parser.block_parser, "skip_empty_lines") as mock_skip:
            mock_skip.return_value = len(whitespace_text.split("\n"))

            result = parser.parse(whitespace_text)

            # 空白のみの場合は何も返されない
            self.assertEqual(len(result), 0)
