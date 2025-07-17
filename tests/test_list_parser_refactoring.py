"""
list_parser.py分割のためのテスト

TDD: 分割後の新しいモジュール構造のテスト
Issue #492 Phase 5A - list_parser.py分割
"""

from unittest.mock import Mock

import pytest


class TestListParserCore:
    """リストパーサーコアのテスト"""

    def test_list_parser_core_import(self):
        """RED: リストパーサーコアモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_parser_core import ListParserCore

    def test_list_parser_core_initialization(self):
        """RED: リストパーサーコア初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_parser_core import ListParserCore

            mock_keyword_parser = Mock()
            parser = ListParserCore(mock_keyword_parser)

    def test_parse_unordered_list_method(self):
        """RED: 順序なしリスト解析メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_parser_core import ListParserCore

            mock_keyword_parser = Mock()
            parser = ListParserCore(mock_keyword_parser)
            result = parser.parse_unordered_list(["- item1", "- item2"], 0)

    def test_parse_ordered_list_method(self):
        """RED: 順序付きリスト解析メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_parser_core import ListParserCore

            mock_keyword_parser = Mock()
            parser = ListParserCore(mock_keyword_parser)
            result = parser.parse_ordered_list(["1. item1", "2. item2"], 0)

    def test_is_list_line_method(self):
        """RED: リスト行判定メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_parser_core import ListParserCore

            mock_keyword_parser = Mock()
            parser = ListParserCore(mock_keyword_parser)
            result = parser.is_list_line("- item")

    def test_contains_list_method(self):
        """RED: リスト含有判定メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_parser_core import ListParserCore

            mock_keyword_parser = Mock()
            parser = ListParserCore(mock_keyword_parser)
            result = parser.contains_list("some text\\n- item")

    def test_extract_list_items_method(self):
        """RED: リスト項目抽出メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_parser_core import ListParserCore

            mock_keyword_parser = Mock()
            parser = ListParserCore(mock_keyword_parser)
            result = parser.extract_list_items("- item1\\n- item2")


class TestNestedListParser:
    """ネストリストパーサーのテスト"""

    def test_nested_list_parser_import(self):
        """RED: ネストリストパーサーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.nested_list_parser import NestedListParser

    def test_nested_list_parser_initialization(self):
        """RED: ネストリストパーサー初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.nested_list_parser import NestedListParser

            mock_list_parser = Mock()
            parser = NestedListParser(mock_list_parser)

    def test_parse_nested_lists_method(self):
        """RED: ネストリスト解析メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.nested_list_parser import NestedListParser

            mock_list_parser = Mock()
            parser = NestedListParser(mock_list_parser)
            result = parser.parse_nested_lists(["- item1", "  - subitem"], 0)

    def test_calculate_indent_level_method(self):
        """RED: インデントレベル計算メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.nested_list_parser import NestedListParser

            mock_list_parser = Mock()
            parser = NestedListParser(mock_list_parser)
            result = parser._calculate_indent_level("  - item")

    def test_group_by_indent_level_method(self):
        """RED: インデントレベル別グループ化メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.nested_list_parser import NestedListParser

            mock_list_parser = Mock()
            parser = NestedListParser(mock_list_parser)
            result = parser._group_by_indent_level(["- item1", "  - subitem"])


class TestListValidator:
    """リストバリデーターのテスト"""

    def test_list_validator_import(self):
        """RED: リストバリデーターモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_validator import ListValidator

    def test_list_validator_initialization(self):
        """RED: リストバリデーター初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_validator import ListValidator

            mock_list_parser = Mock()
            validator = ListValidator(mock_list_parser)

    def test_validate_list_structure_method(self):
        """RED: リスト構造バリデーションメソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_validator import ListValidator

            mock_list_parser = Mock()
            validator = ListValidator(mock_list_parser)
            result = validator.validate_list_structure(["- item1", "1. item2"])

    def test_validate_keyword_list_item_method(self):
        """RED: キーワードリスト項目バリデーションメソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_validator import ListValidator

            mock_list_parser = Mock()
            validator = ListValidator(mock_list_parser)
            result = validator._validate_keyword_list_item("- ;;;keyword;;; text", 1)


class TestListParserFactory:
    """リストパーサーファクトリーのテスト"""

    def test_list_parser_factory_import(self):
        """RED: リストパーサーファクトリーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_parser_factory import create_list_parser

    def test_create_list_parser_function(self):
        """RED: リストパーサー作成関数テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_parser_factory import create_list_parser

            mock_keyword_parser = Mock()
            parser = create_list_parser(mock_keyword_parser)

    def test_create_nested_list_parser_function(self):
        """RED: ネストリストパーサー作成関数テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_parser_factory import (
                create_nested_list_parser,
            )

            mock_keyword_parser = Mock()
            parser = create_nested_list_parser(mock_keyword_parser)

    def test_create_list_validator_function(self):
        """RED: リストバリデーター作成関数テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.list_parser_factory import create_list_validator

            mock_keyword_parser = Mock()
            validator = create_list_validator(mock_keyword_parser)


class TestOriginalListParser:
    """元のlist_parserモジュールとの互換性テスト"""

    def test_original_list_parser_still_works(self):
        """元のlist_parserが正常動作することを確認"""
        from kumihan_formatter.core.list_parser import (
            ListParser,
            ListValidator,
            NestedListParser,
        )

        # 基本クラスが存在することを確認
        assert ListParser is not None
        assert NestedListParser is not None
        assert ListValidator is not None

    def test_list_parser_initialization(self):
        """元のListParser初期化テスト"""
        from unittest.mock import Mock

        from kumihan_formatter.core.list_parser import ListParser

        mock_keyword_parser = Mock()
        parser = ListParser(mock_keyword_parser)

        # 基本メソッドが存在することを確認
        assert hasattr(parser, "parse_unordered_list")
        assert hasattr(parser, "parse_ordered_list")
        assert hasattr(parser, "is_list_line")
        assert hasattr(parser, "contains_list")
        assert hasattr(parser, "extract_list_items")

    def test_nested_list_parser_initialization(self):
        """元のNestedListParser初期化テスト"""
        from unittest.mock import Mock

        from kumihan_formatter.core.list_parser import NestedListParser

        mock_list_parser = Mock()
        parser = NestedListParser(mock_list_parser)

        # メソッドが存在することを確認
        assert hasattr(parser, "parse_nested_lists")
        assert hasattr(parser, "_calculate_indent_level")
        assert hasattr(parser, "_group_by_indent_level")

    def test_list_validator_initialization(self):
        """元のListValidator初期化テスト"""
        from unittest.mock import Mock

        from kumihan_formatter.core.list_parser import ListValidator

        mock_list_parser = Mock()
        validator = ListValidator(mock_list_parser)

        # メソッドが存在することを確認
        assert hasattr(validator, "validate_list_structure")
        assert hasattr(validator, "_validate_keyword_list_item")

    def test_list_parser_basic_functionality(self):
        """リストパーサーの基本機能テスト"""
        from unittest.mock import Mock

        from kumihan_formatter.core.list_parser import ListParser

        mock_keyword_parser = Mock()
        parser = ListParser(mock_keyword_parser)

        # is_list_line メソッドの基本動作
        assert parser.is_list_line("- item") == "ul"
        assert parser.is_list_line("1. item") == "ol"
        assert parser.is_list_line("normal text") == ""

    def test_list_detection_functionality(self):
        """リスト検出機能のテスト"""
        from unittest.mock import Mock

        from kumihan_formatter.core.list_parser import ListParser

        mock_keyword_parser = Mock()
        parser = ListParser(mock_keyword_parser)

        # contains_list メソッドの基本動作
        assert parser.contains_list("normal text") == False
        assert parser.contains_list("- item1\\n- item2") == True

    def test_list_item_extraction_functionality(self):
        """リスト項目抽出機能のテスト"""
        from unittest.mock import Mock

        from kumihan_formatter.core.list_parser import ListParser

        mock_keyword_parser = Mock()
        parser = ListParser(mock_keyword_parser)

        # extract_list_items メソッドの基本動作
        items = parser.extract_list_items("- item1\\n- item2\\n1. item3")
        assert len(items) == 3
        assert "item1" in items
        assert "item2" in items
        assert "item3" in items
