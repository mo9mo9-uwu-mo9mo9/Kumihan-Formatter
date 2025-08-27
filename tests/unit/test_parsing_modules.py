"""
パーシングモジュールの単体テスト

分離されたパーシングモジュール群の動作確認
- キーワード解析 (keyword parser)
- ブロック解析 (block parser)
- リスト解析 (list parser)
- マークダウン解析 (markdown parser)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from kumihan_formatter.core.parsing.keyword.parsers.basic_parser import BasicKeywordParser
from kumihan_formatter.core.parsing.keyword.definitions import DEFAULT_BLOCK_KEYWORDS, KeywordDefinitions
from kumihan_formatter.core.parsing.keyword.keyword_registry import KeywordRegistry, KeywordType
from kumihan_formatter.core.parsing.keyword.validator import KeywordValidator

from kumihan_formatter.core.parsing.base.parser_base import UnifiedParserBase
from kumihan_formatter.core.parsing.base.parser_protocols import ParseContext, ParseResult

from kumihan_formatter.core.ast_nodes import Node, create_node


class TestBasicKeywordParser:
    """基本キーワード解析のテスト"""

    def test_basic_keyword_parser_initialization(self):
        """BasicKeywordParser 初期化テスト"""
        parser = BasicKeywordParser()
        assert parser is not None
        assert hasattr(parser, 'default_keywords')
        assert hasattr(parser, 'custom_keywords')

    def test_default_keywords_loaded(self):
        """デフォルトキーワードの読み込みテスト"""
        parser = BasicKeywordParser()
        
        # 基本装飾キーワード
        assert "太字" in parser.default_keywords
        assert "斜体" in parser.default_keywords
        assert "下線" in parser.default_keywords
        
        # 色・スタイルキーワード
        assert "赤" in parser.default_keywords
        assert "青" in parser.default_keywords
        
        # ブロックキーワード
        assert "重要" in parser.default_keywords
        assert "注意" in parser.default_keywords

    def test_parse_keyword_string_simple(self):
        """単純なキーワード文字列解析テスト"""
        parser = BasicKeywordParser()
        result = parser.parse_keyword_string("太字")
        
        assert result["keyword"] == "太字"
        assert result["negated"] is False
        assert result["level"] is None
        assert isinstance(result["attributes"], dict)

    def test_parse_keyword_string_with_attributes(self):
        """属性付きキーワード解析テスト"""
        parser = BasicKeywordParser()
        result = parser.parse_keyword_string("太字[color:red]")
        
        assert result["keyword"] == "太字"
        assert "color" in result["attributes"]
        assert result["attributes"]["color"] == "red"

    def test_parse_keyword_string_with_level(self):
        """レベル指定キーワード解析テスト"""
        parser = BasicKeywordParser()
        result = parser.parse_keyword_string("見出し1")
        
        assert result["keyword"] == "見出し"
        assert result["level"] == 1

    def test_parse_keyword_string_negated(self):
        """否定キーワード解析テスト"""
        parser = BasicKeywordParser()
        result = parser.parse_keyword_string("-太字")
        
        assert result["keyword"] == "太字"
        assert result["negated"] is True

    def test_parse_attributes_multiple(self):
        """複数属性の解析テスト"""
        parser = BasicKeywordParser()
        result = parser.parse_attributes("[color:red][size:large]")
        
        assert "color" in result
        assert "size" in result
        assert result["color"] == "red"
        assert result["size"] == "large"

    def test_create_keyword_node_known(self):
        """既知キーワードからのノード作成テスト"""
        parser = BasicKeywordParser()
        keyword_info = {
            "keyword": "太字",
            "content": "テストコンテンツ",
            "attributes": {},
            "context": "test"
        }
        
        node = parser.create_keyword_node(keyword_info)
        assert isinstance(node, Node)
        assert node.metadata["keyword"] == "太字"

    def test_create_keyword_node_unknown(self):
        """未知キーワードからのノード作成テスト"""
        parser = BasicKeywordParser()
        keyword_info = {
            "keyword": "未知キーワード",
            "content": "テストコンテンツ",
            "attributes": {},
            "context": "test"
        }
        
        node = parser.create_keyword_node(keyword_info)
        assert isinstance(node, Node)
        assert node.node_type == "unknown_keyword"
        assert "warning" in node.metadata

    def test_is_valid_keyword(self):
        """キーワード有効性チェックテスト"""
        parser = BasicKeywordParser()
        
        assert parser.is_valid_keyword("太字") is True
        assert parser.is_valid_keyword("斜体") is True
        assert parser.is_valid_keyword("未知キーワード") is False
        assert parser.is_valid_keyword("") is False
        assert parser.is_valid_keyword(None) is False

    def test_attribute_handlers(self):
        """属性ハンドラーのテスト"""
        parser = BasicKeywordParser()
        node = create_node("test")
        
        # 色属性ハンドラー
        parser._handle_color_attribute(node, "red")
        assert node.metadata["color"] == "red"
        assert "styles" in node.metadata
        
        # サイズ属性ハンドラー
        parser._handle_size_attribute(node, "large")
        assert node.metadata["size"] == "large"
        
        # クラス属性ハンドラー
        parser._handle_class_attribute(node, "important highlight")
        assert "classes" in node.metadata
        assert "important" in node.metadata["classes"]
        assert "highlight" in node.metadata["classes"]


class TestKeywordRegistry:
    """キーワードレジストリのテスト"""

    def test_keyword_registry_initialization(self):
        """KeywordRegistry 初期化テスト"""
        registry = KeywordRegistry()
        assert registry is not None

    def test_keyword_type_enum(self):
        """KeywordType 列挙型のテスト"""
        assert hasattr(KeywordType, 'DECORATION')
        assert hasattr(KeywordType, 'LAYOUT')
        assert hasattr(KeywordType, 'STRUCTURE')
        assert hasattr(KeywordType, 'CONTENT')


class TestKeywordValidator:
    """キーワードバリデーターのテスト"""

    def test_keyword_validator_initialization(self):
        """KeywordValidator 初期化テスト"""
        definitions = KeywordDefinitions()
        validator = KeywordValidator(definitions)
        assert validator is not None
        assert validator.definitions is not None


class TestDefaultBlockKeywords:
    """デフォルトブロックキーワードのテスト"""

    def test_default_block_keywords_exists(self):
        """DEFAULT_BLOCK_KEYWORDS 定数の存在テスト"""
        assert DEFAULT_BLOCK_KEYWORDS is not None
        assert isinstance(DEFAULT_BLOCK_KEYWORDS, dict)

    def test_default_block_keywords_content(self):
        """デフォルトブロックキーワードの内容テスト"""
        keywords = DEFAULT_BLOCK_KEYWORDS
        
        # 基本的なブロックキーワードが存在することを確認
        assert len(keywords) > 0
        
        # キーワード構造の確認（サンプル）
        for keyword, definition in keywords.items():
            assert isinstance(keyword, str)
            assert isinstance(definition, dict)
            if "type" in definition:
                assert isinstance(definition["type"], str)


class TestUnifiedParserBase:
    """統合基本パーサークラスのテスト"""

    def test_unified_parser_base_initialization(self):
        """UnifiedParserBase 初期化テスト"""
        parser = UnifiedParserBase()
        assert parser is not None

    def test_unified_parser_base_parse_method_exists(self):
        """UnifiedParserBase parse メソッド存在テスト"""
        parser = UnifiedParserBase()
        assert hasattr(parser, 'parse')


class TestParseProtocols:
    """パース プロトコルのテスト"""

    def test_parse_context_protocol(self):
        """ParseContext プロトコルのテスト"""
        # プロトコルの存在確認
        assert ParseContext is not None

    def test_parse_result_protocol(self):
        """ParseResult プロトコルのテスト"""
        # プロトコルの存在確認
        assert ParseResult is not None


class TestNodeCreation:
    """ノード作成のテスト"""

    def test_create_node_function(self):
        """create_node 関数のテスト"""
        node = create_node("test_type", content="テスト内容")
        assert isinstance(node, Node)
        assert node.node_type == "test_type"
        assert node.content == "テスト内容"

    def test_create_node_with_metadata(self):
        """メタデータ付きノード作成テスト"""
        node = create_node("test_type", content="テスト内容")
        node.metadata["test_key"] = "test_value"
        
        assert node.metadata["test_key"] == "test_value"


class TestParsingIntegration:
    """パーシング統合テスト"""

    def test_keyword_parser_integration(self):
        """キーワードパーサー統合テスト"""
        parser = BasicKeywordParser()
        
        # 複雑なキーワード文字列の解析
        result = parser.parse_keyword_string("太字+赤[size:large]")
        assert result["keyword"] == "太字"
        assert "modifiers" in result or "attributes" in result

    def test_multiple_parser_compatibility(self):
        """複数パーサーの互換性テスト"""
        keyword_parser = BasicKeywordParser()
        base_parser = UnifiedParserBase()
        
        # 両方のパーサーが正常に初期化されることを確認
        assert keyword_parser is not None
        assert base_parser is not None

    def test_node_metadata_consistency(self):
        """ノードメタデータの一貫性テスト"""
        parser = BasicKeywordParser()
        keyword_info = {
            "keyword": "重要",
            "content": "重要なメッセージ",
            "attributes": {"color": "red"},
            "context": "block",
            "position": (0, 10)
        }
        
        node = parser.create_keyword_node(keyword_info)
        
        # メタデータの一貫性チェック
        assert node.metadata["keyword"] == "重要"
        assert node.metadata["context"] == "block"
        assert "position" in node.metadata
        assert "attributes" in node.metadata

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        parser = BasicKeywordParser()
        
        # 不正な入力でのエラーハンドリング
        result = parser.parse_keyword_string("")
        assert result["keyword"] == ""
        
        # None 入力
        assert parser.is_valid_keyword(None) is False
        
        # 数値入力
        assert parser.is_valid_keyword(123) is False

    def test_performance_basic(self):
        """基本パフォーマンステスト"""
        parser = BasicKeywordParser()
        
        # 大量のキーワード処理テスト
        keywords = ["太字", "斜体", "下線", "赤", "青", "緑"] * 100
        
        for keyword in keywords:
            result = parser.parse_keyword_string(keyword)
            assert result["keyword"] == keyword

    def test_memory_usage(self):
        """メモリ使用量テスト"""
        parser = BasicKeywordParser()
        
        # 多数のノード作成
        nodes = []
        for i in range(100):
            keyword_info = {
                "keyword": "太字",
                "content": f"テスト内容{i}",
                "attributes": {},
                "context": "test"
            }
            node = parser.create_keyword_node(keyword_info)
            nodes.append(node)
        
        # ノードが正しく作成されていることを確認
        assert len(nodes) == 100
        assert all(isinstance(node, Node) for node in nodes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])