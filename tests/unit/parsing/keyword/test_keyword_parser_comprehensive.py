"""
KeywordParser包括的テストスイート - Issue #929対応

カバレッジ向上目標: 35% → 60%
統一プロトコル対応、Kumihan記法、国際化、エラーハンドリングの完全テスト
"""

from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes.node import Node
from kumihan_formatter.core.parsing.keyword.definitions import KeywordDefinitions
from kumihan_formatter.core.parsing.keyword.keyword_parser import KeywordParser
from kumihan_formatter.core.parsing.keyword.parse_result import ParseResult


class TestKeywordParserCore:
    """KeywordParserコア機能テスト"""

    def test_初期化_デフォルト定義(self):
        """KeywordParserが適切に初期化されることを確認"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        assert parser.definitions is definitions
        assert hasattr(parser, "_is_valid_keyword")

    def test_初期化_None定義(self):
        """definitions=Noneでの初期化テスト"""
        parser = KeywordParser(None)

        assert parser.definitions is None

    def test_初期化_カスタム定義(self):
        """カスタム定義での初期化テスト"""
        mock_definitions = Mock()
        parser = KeywordParser(mock_definitions)

        assert parser.definitions is mock_definitions

    def test_parse_marker_keywords_基本キーワード(self):
        """基本キーワード解析テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        keywords, attributes, errors = parser.parse_marker_keywords("太字")

        assert keywords == ["太字"]
        assert attributes == {}
        assert errors == []

    def test_parse_marker_keywords_複合キーワード(self):
        """複合キーワード解析テスト（+記号）"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        keywords, attributes, errors = parser.parse_marker_keywords("太字+下線")

        assert "太字" in keywords
        assert "下線" in keywords
        assert len(keywords) == 2

    def test_parse_marker_keywords_複合キーワード_全角プラス(self):
        """複合キーワード解析テスト（＋記号）"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        keywords, attributes, errors = parser.parse_marker_keywords("太字＋イタリック")

        assert "太字" in keywords
        assert "イタリック" in keywords

    def test_parse_marker_keywords_ルビ記法(self):
        """ルビ記法の解析テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        keywords, attributes, errors = parser.parse_marker_keywords("ルビ 漢字(かんじ)")

        assert keywords == []
        assert "ruby" in attributes
        assert attributes["ruby"]["base_text"] == "漢字"
        assert attributes["ruby"]["ruby_text"] == "かんじ"

    def test_parse_marker_keywords_ルビ記法_全角括弧(self):
        """ルビ記法の解析テスト（全角括弧）"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        keywords, attributes, errors = parser.parse_marker_keywords("ルビ 日本語（にほんご）")

        assert "ruby" in attributes
        assert attributes["ruby"]["base_text"] == "日本語"
        assert attributes["ruby"]["ruby_text"] == "にほんご"


class TestKeywordParserKumihanNotation:
    """Kumihan記法固有テスト"""

    def test_装飾キーワード_基本装飾(self):
        """基本装飾キーワードのテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        decoration_keywords = ["太字", "下線", "イタリック", "取り消し線"]

        for keyword in decoration_keywords:
            keywords, attributes, errors = parser.parse_marker_keywords(keyword)
            assert keyword in keywords
            assert len(errors) == 0

    def test_レイアウトキーワード_中央寄せ等(self):
        """レイアウト系キーワードのテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        layout_keywords = ["中央寄せ", "注意", "情報"]

        for keyword in layout_keywords:
            keywords, attributes, errors = parser.parse_marker_keywords(keyword)
            assert keyword in keywords

    def test_構造キーワード_見出し(self):
        """構造系キーワード（見出し）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        heading_keywords = ["見出し1", "見出し2", "見出し3", "見出し4", "見出し5"]

        for keyword in heading_keywords:
            keywords, attributes, errors = parser.parse_marker_keywords(keyword)
            assert keyword in keywords

    def test_コンテンツキーワード_コードと引用(self):
        """コンテンツ系キーワードのテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        content_keywords = ["コード", "引用", "コードブロック"]

        for keyword in content_keywords:
            keywords, attributes, errors = parser.parse_marker_keywords(keyword)
            assert keyword in keywords

    def test_複合記法パターン_装飾組み合わせ(self):
        """複合記法パターンのテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        keywords, attributes, errors = parser.parse_marker_keywords("太字+イタリック+下線")

        assert "太字" in keywords
        assert "イタリック" in keywords
        assert "下線" in keywords
        assert len(keywords) == 3


class TestKeywordParserValidation:
    """バリデーション機能テスト"""

    def test_空文字列入力(self):
        """空文字列入力のハンドリング"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        keywords, attributes, errors = parser.parse_marker_keywords("")

        assert keywords == []
        assert attributes == {}
        assert errors == []

    def test_無効な型入力(self):
        """無効な型入力のハンドリング"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        keywords, attributes, errors = parser.parse_marker_keywords(123)

        assert keywords == []
        assert attributes == {}
        assert len(errors) > 0
        assert "Invalid marker content type" in errors[0]

    def test_None入力(self):
        """None入力のハンドリング"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        keywords, attributes, errors = parser.parse_marker_keywords(None)

        assert keywords == []
        assert errors == ["Invalid marker content type"]

    def test_未定義キーワード_definitions無し(self):
        """未定義キーワードのハンドリング（definitions=None）"""
        parser = KeywordParser(None)

        keywords, attributes, errors = parser.parse_marker_keywords("不明キーワード")

        # definitions=Noneの場合、is_validは常にTrueを返す
        assert "不明キーワード" in keywords

    def test_未定義キーワード_definitionsあり(self):
        """未定義キーワードのハンドリング（definitionsあり）"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        keywords, attributes, errors = parser.parse_marker_keywords("存在しないキーワード")

        # 未定義キーワードは除外される
        assert keywords == []


class TestKeywordParserProtocol:
    """統一プロトコル実装テスト"""

    def test_parse_統一インターフェース_基本(self):
        """統一parseインターフェースのテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser.parse("太字")

        assert hasattr(result, "success")
        assert result.success is True
        assert len(result.nodes) == 1
        assert result.nodes[0].type == "keyword"
        assert result.nodes[0].content == "太字"

    def test_parse_統一インターフェース_複合キーワード(self):
        """統一parseインターフェース（複合キーワード）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser.parse("太字+下線")

        assert result.success is True
        assert len(result.nodes) == 2
        assert any(node.content == "太字" for node in result.nodes)
        assert any(node.content == "下線" for node in result.nodes)

    def test_parse_統一インターフェース_エラー(self):
        """統一parseインターフェース（エラーケース）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        # 例外を発生させる
        with patch.object(parser, "parse_marker_keywords", side_effect=Exception("Test error")):
            result = parser.parse("テスト")

            assert result.success is False
            assert len(result.errors) > 0
            assert "Keyword parsing failed" in result.errors[0]

    def test_validate_基本バリデーション(self):
        """validateメソッドのテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        errors = parser.validate("太字")

        assert errors == []

    def test_validate_無効入力(self):
        """validateメソッド（無効入力）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        errors = parser.validate(123)  # type: ignore

        assert len(errors) > 0
        assert "Content must be a string" in errors[0]

    def test_validate_空コンテンツ(self):
        """validateメソッド（空コンテンツ）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        errors = parser.validate("")

        assert len(errors) > 0
        assert "Empty content provided" in errors[0]

    def test_validate_複合キーワード(self):
        """validateメソッド（複合キーワード）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        errors = parser.validate("太字+下線")

        assert errors == []

    def test_get_parser_info(self):
        """get_parser_infoメソッドのテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        info = parser.get_parser_info()

        assert info["name"] == "KeywordParser"
        assert info["version"] == "2.0"
        assert "kumihan" in info["supported_formats"]
        assert "keyword_parsing" in info["capabilities"]

    def test_supports_format(self):
        """supports_formatメソッドのテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        assert parser.supports_format("kumihan") is True
        assert parser.supports_format("keyword") is True
        assert parser.supports_format("markdown") is False


class TestKeywordParserMethods:
    """KeywordParserProtocol固有メソッドテスト"""

    def test_parse_keywords_基本(self):
        """parse_keywordsメソッドのテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser.parse_keywords("太字")

        assert result == ["太字"]

    def test_parse_keywords_複合(self):
        """parse_keywordsメソッド（複合キーワード）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser.parse_keywords("太字+下線")

        assert "太字" in result
        assert "下線" in result

    def test_parse_keywords_空文字列(self):
        """parse_keywordsメソッド（空文字列）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser.parse_keywords("")

        assert result == []

    def test_validate_keyword_有効(self):
        """validate_keywordメソッド（有効キーワード）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser.validate_keyword("太字")

        assert result is True

    def test_validate_keyword_無効(self):
        """validate_keywordメソッド（無効キーワード）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser.validate_keyword("不明キーワード")

        assert result is False


class TestKeywordParserSanitization:
    """サニタイゼーション機能テスト"""

    def test_sanitize_color_attribute_hex色(self):
        """color属性サニタイゼーション（hex色）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser._sanitize_color_attribute("#ff0000")

        assert result == "#ff0000"

    def test_sanitize_color_attribute_短縮hex色(self):
        """color属性サニタイゼーション（短縮hex色）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser._sanitize_color_attribute("#f00")

        assert result == "#f00"

    def test_sanitize_color_attribute_名前色(self):
        """color属性サニタイゼーション（名前付き色）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser._sanitize_color_attribute("red")

        assert result == "red"

    def test_sanitize_color_attribute_無効値(self):
        """color属性サニタイゼーション（無効値）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser._sanitize_color_attribute("invalid-color")

        assert result == "#000000"

    def test_sanitize_color_attribute_非文字列(self):
        """color属性サニタイゼーション（非文字列）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser._sanitize_color_attribute(123)

        assert result == ""


class TestKeywordParserBackwardCompatibility:
    """後方互換性テスト"""

    def test_parse_text_後方互換(self):
        """parse_text後方互換メソッドのテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser.parse_text("太字")

        assert len(result) == 1
        assert result[0].content == "太字"

    def test_parse_text_エラーハンドリング(self):
        """parse_text後方互換メソッド（エラー）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        with patch.object(parser, "parse", side_effect=Exception("Test error")):
            result = parser.parse_text("テスト")

            assert result == []

    def test_is_valid_後方互換(self):
        """is_valid後方互換メソッドのテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser.is_valid("太字")

        assert result is True

    def test_is_valid_後方互換_無効(self):
        """is_valid後方互換メソッド（無効）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser.is_valid("不明キーワード")

        assert result is False  # 未定義キーワードは無効

    def test_is_valid_エラーハンドリング(self):
        """is_valid後方互換メソッド（エラー）のテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        with patch.object(parser, "validate", side_effect=Exception("Test error")):
            result = parser.is_valid("テスト")

            assert result is False


class TestKeywordParserRubyHandling:
    """ルビ処理専門テスト"""

    def test_parse_ruby_content_基本(self):
        """_parse_ruby_content基本テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser._parse_ruby_content("漢字(かんじ)")

        assert result["base_text"] == "漢字"
        assert result["ruby_text"] == "かんじ"

    def test_parse_ruby_content_全角括弧(self):
        """_parse_ruby_content全角括弧テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser._parse_ruby_content("日本語（にほんご）")

        assert result["base_text"] == "日本語"
        assert result["ruby_text"] == "にほんご"

    def test_parse_ruby_content_空文字列(self):
        """_parse_ruby_content空文字列テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser._parse_ruby_content("")

        assert result == {}

    def test_parse_ruby_content_無効フォーマット(self):
        """_parse_ruby_content無効フォーマットテスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser._parse_ruby_content("無効なフォーマット")

        assert result == {}

    def test_parse_ruby_content_非文字列(self):
        """_parse_ruby_content非文字列テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser._parse_ruby_content(123)

        assert result == {}


class TestKeywordParserErrorHandling:
    """エラーハンドリング専門テスト"""

    def test_split_compound_keywords_非文字列(self):
        """split_compound_keywords非文字列入力テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser.split_compound_keywords(123)

        assert result == []

    def test_split_compound_keywords_空文字列(self):
        """split_compound_keywords空文字列テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser.split_compound_keywords("")

        assert result == []

    def test_is_valid_keyword_空文字列(self):
        """_is_valid_keyword空文字列テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        result = parser._is_valid_keyword("")

        assert result is False

    def test_is_valid_keyword_None_definitions(self):
        """_is_valid_keyword definitions=Noneテスト"""
        parser = KeywordParser(None)

        result = parser._is_valid_keyword("任意のキーワード")

        assert result is True

    def test_validate_例外処理(self):
        """validateメソッドの例外処理テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        with patch.object(parser, "parse_marker_keywords", side_effect=Exception("Test error")):
            errors = parser.validate("テスト")

            assert len(errors) > 0
            assert "Validation error" in errors[0]


class TestKeywordParserPerformance:
    """パフォーマンステスト"""

    def test_大量キーワード処理(self):
        """大量キーワード処理のパフォーマンステスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        # 大量の複合キーワードを作成
        large_keyword = "+".join(["太字"] * 100)

        keywords, attributes, errors = parser.parse_marker_keywords(large_keyword)

        # 100個のキーワードが適切に処理されることを確認
        assert len(keywords) == 100
        assert all(kw == "太字" for kw in keywords)

    def test_複雑なルビ処理(self):
        """複雑なルビ処理のパフォーマンステスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        # 複雑なルビコンテンツ
        complex_ruby = "ルビ " + "複雑漢字(ふくざつかんじ)" * 50

        keywords, attributes, errors = parser.parse_marker_keywords(complex_ruby)

        assert "ruby" in attributes
        assert len(errors) == 0


class TestKeywordParserIntegration:
    """統合テスト"""

    def test_definitions統合(self):
        """KeywordDefinitionsとの統合テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        # カスタムキーワードを追加
        definitions.add_custom_keyword("カスタム", {"tag": "span", "class": "custom"})

        keywords, attributes, errors = parser.parse_marker_keywords("カスタム")

        assert "カスタム" in keywords

    def test_registry統合(self):
        """KeywordRegistryとの統合テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        # レジストリを取得してテスト
        registry = definitions.get_keyword_registry()

        assert registry is not None

    def test_完全なKumihan記法処理(self):
        """完全なKumihan記法処理の統合テスト"""
        definitions = KeywordDefinitions()
        parser = KeywordParser(definitions)

        # 複雑な記法をテスト
        content = "太字+下線+イタリック"

        result = parser.parse(content)

        assert result.success is True
        assert len(result.nodes) == 3
        assert result.metadata["keyword_count"] == 3
