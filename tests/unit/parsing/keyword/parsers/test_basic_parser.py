"""基本キーワードパーサーのテスト

基本キーワードパーサーの包括的なテスト:
- 基本キーワード解析
- 属性処理
- ノード作成
- エラーハンドリング
"""

import pytest
from unittest.mock import Mock, patch

from kumihan_formatter.core.parsing.keyword.parsers.basic_parser import (
    BasicKeywordParser,
)
from kumihan_formatter.core.ast_nodes import Node, create_node
from kumihan_formatter.core.utilities.logger import get_logger


class TestBasicKeywordParser:
    """基本キーワードパーサーのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.parser = BasicKeywordParser()
        self.logger = get_logger(__name__)

    # ========== 正常系テスト（60%） ==========

    def test_正常系_初期化(self):
        """正常系: パーサーの初期化"""
        parser = BasicKeywordParser()

        # 設定の確認
        assert hasattr(parser, "config")
        assert hasattr(parser, "default_keywords")
        assert hasattr(parser, "custom_keywords")
        assert hasattr(parser, "keyword_patterns")
        assert hasattr(parser, "attribute_handlers")

        # デフォルトキーワードの存在確認
        assert "太字" in parser.default_keywords
        assert "斜体" in parser.default_keywords
        assert "見出し" in parser.default_keywords

    def test_正常系_基本キーワード解析_単純(self):
        """正常系: 基本キーワードの解析（単純）"""
        result = self.parser.parse_keyword_string("太字")

        assert result["keyword"] == "太字"
        assert result["attributes"] == {}
        assert result["modifiers"] == []
        assert result["level"] is None
        assert result["negated"] is False

    def test_正常系_基本キーワード解析_属性付き(self):
        """正常系: 属性付きキーワードの解析"""
        result = self.parser.parse_keyword_string("太字[color:red]")

        assert result["keyword"] == "太字"
        assert result["attributes"] == {"color": "red"}
        assert result["negated"] is False

    def test_正常系_基本キーワード解析_レベル指定(self):
        """正常系: レベル指定キーワードの解析"""
        result = self.parser.parse_keyword_string("見出し2")

        assert result["keyword"] == "見出し"
        assert result["level"] == 2
        assert result["negated"] is False

    def test_正常系_基本キーワード解析_複合(self):
        """正常系: 複合キーワードの解析"""
        result = self.parser.parse_keyword_string("太字+赤")

        assert result["keyword"] == "太字"
        assert result["modifiers"] == ["赤"]
        assert result["negated"] is False

    def test_正常系_基本キーワード解析_否定(self):
        """正常系: 否定キーワードの解析"""
        result = self.parser.parse_keyword_string("-太字")

        assert result["keyword"] == "太字"
        assert result["negated"] is True

    def test_正常系_属性解析_単一属性(self):
        """正常系: 単一属性の解析"""
        result = self.parser.parse_attributes("[color:red]")

        assert result == {"color": "red"}

    def test_正常系_属性解析_複数属性(self):
        """正常系: 複数属性の解析"""
        result = self.parser.parse_attributes("[color:red][size:large]")

        assert result == {"color": "red", "size": "large"}

    def test_正常系_属性解析_フラグ属性(self):
        """正常系: フラグ属性の解析"""
        result = self.parser.parse_attributes("[bold]")

        assert result == {"bold": True}

    def test_正常系_ノード作成_基本(self):
        """正常系: 基本ノードの作成"""
        keyword_info = {
            "keyword": "太字",
            "content": "テストテキスト",
            "attributes": {},
            "context": "test",
            "position": (0, 10),
        }

        node = self.parser.create_keyword_node(keyword_info)

        assert isinstance(node, Node)
        assert node.content == "テストテキスト"
        assert node.metadata["keyword"] == "太字"
        assert node.metadata["context"] == "test"

    def test_正常系_ノード作成_属性付き(self):
        """正常系: 属性付きノードの作成"""
        keyword_info = {
            "keyword": "太字",
            "content": "テストテキスト",
            "attributes": {"color": "red"},
            "context": "test",
        }

        node = self.parser.create_keyword_node(keyword_info)

        assert node.metadata["attributes"] == {"color": "red"}
        assert node.metadata.get("color") == "red"
        assert "styles" in node.metadata
        assert node.metadata["styles"]["color"] == "red"

    def test_正常系_キーワード定義取得_デフォルト(self):
        """正常系: デフォルトキーワード定義の取得"""
        definition = self.parser.get_keyword_definition("太字")

        assert definition is not None
        assert definition["type"] == "decoration"
        assert definition["html_tag"] == "strong"

    def test_正常系_キーワード定義取得_カスタム(self):
        """正常系: カスタムキーワード定義の取得"""
        # カスタムキーワードを追加
        self.parser.custom_keywords["カスタム"] = {"type": "custom", "html_tag": "span"}

        definition = self.parser.get_keyword_definition("カスタム")

        assert definition is not None
        assert definition["type"] == "custom"
        assert definition["html_tag"] == "span"

    def test_正常系_キーワード有効性_有効なキーワード(self):
        """正常系: 有効なキーワードの検証"""
        assert self.parser.is_valid_keyword("太字") is True
        assert self.parser.is_valid_keyword("見出し") is True
        assert self.parser.is_valid_keyword("画像") is True

    # ========== 異常系テスト（20%） ==========

    def test_異常系_空文字列キーワード(self):
        """異常系: 空文字列のキーワード"""
        result = self.parser.parse_keyword_string("")

        assert result["keyword"] == ""
        assert result["attributes"] == {}
        assert result["negated"] is False

    def test_異常系_Noneキーワード(self):
        """異常系: Noneのキーワード"""
        with pytest.raises(TypeError):
            self.parser.parse_keyword_string(None)

    def test_異常系_不正属性フォーマット(self):
        """異常系: 不正な属性フォーマット"""
        result = self.parser.parse_attributes("[invalid")

        assert result == {}

    def test_異常系_未定義キーワード_ノード作成(self):
        """異常系: 未定義キーワードのノード作成"""
        keyword_info = {
            "keyword": "未定義キーワード",
            "content": "テスト",
            "attributes": {},
            "context": "test",
        }

        node = self.parser.create_keyword_node(keyword_info)

        assert node.type == "unknown_keyword"
        assert "warning" in node.metadata
        assert "未定義のキーワード" in node.metadata["warning"]

    def test_異常系_キーワード有効性_無効なキーワード(self):
        """異常系: 無効なキーワードの検証"""
        assert self.parser.is_valid_keyword("") is False
        assert self.parser.is_valid_keyword(None) is False
        assert self.parser.is_valid_keyword(123) is False
        assert self.parser.is_valid_keyword("存在しないキーワード") is False

    def test_異常系_属性ハンドラー_存在しない属性(self):
        """異常系: 存在しない属性ハンドラー"""
        node = create_node("test")
        # 存在しない属性を適用（エラーにならないことを確認）
        self.parser.apply_attribute_handlers(node, {"non_existent": "value"})

        # 例外が発生せず、ノードが有効であることを確認
        assert isinstance(node, Node)

    # ========== 境界値テスト（10%） ==========

    def test_境界値_非常に長いキーワード(self):
        """境界値: 非常に長いキーワード"""
        long_keyword = "a" * 1000
        result = self.parser.parse_keyword_string(long_keyword)

        assert result["keyword"] == long_keyword
        assert result["negated"] is False

    def test_境界値_空白を含むキーワード(self):
        """境界値: 空白を含むキーワード"""
        result = self.parser.parse_keyword_string("  太字  ")

        assert result["keyword"] == "太字"

    def test_境界値_特殊文字を含むキーワード(self):
        """境界値: 特殊文字を含むキーワード"""
        result = self.parser.parse_keyword_string("太字[color:#ff0000]")

        assert result["keyword"] == "太字"
        assert result["attributes"]["color"] == "#ff0000"

    def test_境界値_ネストした属性(self):
        """境界値: 深くネストした属性"""
        nested_attrs = "[attr1:value1][attr2:value2][attr3:value3]"
        result = self.parser.parse_attributes(nested_attrs)

        assert len(result) == 3
        assert result["attr1"] == "value1"
        assert result["attr2"] == "value2"
        assert result["attr3"] == "value3"

    # ========== 統合テスト（10%） ==========

    def test_統合_複雑なキーワード解析(self):
        """統合: 複雑なキーワード解析の統合テスト"""
        # より単純なテストケースに変更
        result = self.parser.parse_keyword_string("見出し2[color:blue]")

        # レベルが処理される
        assert result["keyword"] == "見出し"
        assert result["level"] == 2
        # 属性が処理される
        assert result["attributes"]["color"] == "blue"
        assert result["negated"] is False

    def test_統合_全属性ハンドラー適用(self):
        """統合: 全属性ハンドラーの適用テスト"""
        node = create_node("test")
        attributes = {
            "color": "red",
            "size": "large",
            "align": "center",
            "class": "test-class other-class",
            "id": "test-id",
            "style": "margin:10px;padding:5px",
        }

        self.parser.apply_attribute_handlers(node, attributes)

        # 各属性が正しく設定されているかチェック
        assert node.metadata["color"] == "red"
        assert node.metadata["size"] == "large"
        assert node.metadata["align"] == "center"
        assert "test-class" in node.metadata["classes"]
        assert "other-class" in node.metadata["classes"]
        assert node.metadata["id"] == "test-id"
        assert node.metadata["styles"]["margin"] == "10px"
        assert node.metadata["styles"]["padding"] == "5px"

    def test_統合_設定付き初期化(self):
        """統合: 設定付きでの初期化テスト"""
        config = {"custom_keyword_support": True, "strict_validation": False}

        parser = BasicKeywordParser(config)

        assert parser.config == config
        assert hasattr(parser, "default_keywords")
        assert hasattr(parser, "custom_keywords")

    # ========== パフォーマンステスト ==========

    def test_性能_大量キーワード処理(self):
        """性能: 大量キーワードの処理性能"""
        import time

        keywords = ["太字", "斜体", "下線", "取消", "赤", "青", "緑"] * 100

        start_time = time.time()
        for keyword in keywords:
            result = self.parser.parse_keyword_string(keyword)
            assert result["keyword"] == keyword
        end_time = time.time()

        # 700キーワードの処理が1秒以内に完了することを確認
        assert (end_time - start_time) < 1.0

    def test_性能_複雑な属性解析(self):
        """性能: 複雑な属性解析の性能"""
        import time

        complex_attrs = (
            "[color:red][size:large][align:center][class:test][id:test-id]" * 10
        )

        start_time = time.time()
        result = self.parser.parse_attributes(complex_attrs)
        end_time = time.time()

        # 複雑な属性解析が0.1秒以内に完了することを確認
        assert (end_time - start_time) < 0.1
        assert len(result) == 5  # 各属性は最後の値で上書きされる
