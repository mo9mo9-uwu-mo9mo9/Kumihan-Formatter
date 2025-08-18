"""高度キーワードパーサーのテスト

高度キーワードパーサーの包括的なテスト:
- 複合キーワード分割
- ルビ記法処理
- ネスト構造処理
- 高度な属性解析
"""

import pytest
from unittest.mock import Mock, patch

from kumihan_formatter.core.parsing.keyword.parsers.advanced_parser import (
    AdvancedKeywordParser,
)
from kumihan_formatter.core.ast_nodes import Node, NodeBuilder, create_node, error_node
from kumihan_formatter.core.utilities.logger import get_logger


class TestAdvancedKeywordParser:
    """高度キーワードパーサーのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.parser = AdvancedKeywordParser()
        self.logger = get_logger(__name__)

    # ========== 正常系テスト（60%） ==========

    def test_正常系_初期化(self):
        """正常系: パーサーの初期化"""
        parser = AdvancedKeywordParser()

        # 設定の確認
        assert hasattr(parser, "config")
        assert hasattr(parser, "advanced_patterns")
        assert hasattr(parser, "NESTING_ORDER")
        assert hasattr(parser, "DEFAULT_BLOCK_KEYWORDS")

        # パターンの確認
        assert "ruby" in parser.advanced_patterns
        assert "compound_separators" in parser.advanced_patterns
        assert "nested_block" in parser.advanced_patterns

    def test_正常系_複合キーワード分割_基本(self):
        """正常系: 基本的な複合キーワード分割"""
        keywords = self.parser.split_compound_keywords("太字+イタリック")

        assert len(keywords) == 2
        assert "太字" in keywords
        assert "イタリック" in keywords

    def test_正常系_複合キーワード分割_全角記号(self):
        """正常系: 全角記号を使った複合キーワード分割"""
        keywords = self.parser.split_compound_keywords("太字＋イタリック")

        assert len(keywords) == 2
        assert "太字" in keywords
        assert "イタリック" in keywords

    def test_正常系_複合キーワード分割_単一キーワード(self):
        """正常系: 単一キーワードの処理"""
        keywords = self.parser.split_compound_keywords("太字")

        assert len(keywords) == 1
        assert keywords[0] == "太字"

    def test_正常系_ルビ記法解析_基本(self):
        """正常系: 基本的なルビ記法の解析"""
        result = self.parser.parse_ruby_content("漢字|かんじ")

        assert result is not None
        assert result["base"] == "漢字"
        assert result["ruby"] == "かんじ"

    def test_正常系_ルビ記法解析_単純ルビ(self):
        """正常系: 単純なルビ記法の解析"""
        result = self.parser.parse_ruby_content("漢字")

        assert result is not None
        assert result["base"] == "漢字"
        assert result["ruby"] == ""

    def test_正常系_ルビノード作成(self):
        """正常系: ルビノードの作成"""
        node = self.parser.create_ruby_node("漢字|かんじ")

        assert isinstance(node, Node)
        assert node.type == "ruby"
        assert node.content == "漢字"
        assert node.attributes.get("data-ruby") == "かんじ"

    def test_正常系_マーカーキーワード解析_単一(self):
        """正常系: 単一キーワードのマーカー解析"""
        keywords, attributes, errors = self.parser.parse_marker_keywords("太字")

        assert len(keywords) == 1
        assert keywords[0] == "太字"
        assert len(attributes) == 0
        assert len(errors) == 0

    def test_正常系_マーカーキーワード解析_複合(self):
        """正常系: 複合キーワードのマーカー解析"""
        keywords, attributes, errors = self.parser.parse_marker_keywords(
            "太字+イタリック"
        )

        assert len(keywords) == 2
        assert "太字" in keywords
        assert "イタリック" in keywords
        assert len(errors) == 0

    def test_正常系_マーカーキーワード解析_ルビ(self):
        """正常系: ルビ記法のマーカー解析"""
        keywords, attributes, errors = self.parser.parse_marker_keywords(
            "ルビ 漢字|かんじ"
        )

        assert len(keywords) == 0
        assert "ruby" in attributes
        assert attributes["ruby"]["base"] == "漢字"
        assert attributes["ruby"]["ruby"] == "かんじ"
        assert len(errors) == 0

    def test_正常系_ネスト順序ソート(self):
        """正常系: ネスト順序でのキーワードソート"""
        keywords = ["太字", "見出し1", "イタリック"]
        sorted_keywords = self.parser.sort_keywords_by_nesting_order(keywords)

        # ネスト順序に従ってソートされているか確認
        assert len(sorted_keywords) == 3
        # 見出し1(h1)は太字(strong)より前にくる
        h1_index = sorted_keywords.index("見出し1")
        bold_index = sorted_keywords.index("太字")
        assert h1_index < bold_index

    def test_正常系_複合ブロック作成_単一キーワード(self):
        """正常系: 単一キーワードでの複合ブロック作成"""
        node = self.parser.create_compound_block(["太字"], "テスト内容", {})

        assert isinstance(node, Node)
        assert node.type == "strong"

    def test_正常系_複合ブロック作成_複数キーワード(self):
        """正常系: 複数キーワードでの複合ブロック作成"""
        node = self.parser.create_compound_block(
            ["太字", "イタリック"], "テスト内容", {}
        )

        assert isinstance(node, Node)
        # ネスト構造になっているか確認
        assert node.type == "strong" or node.type == "em"

    def test_正常系_色値正規化(self):
        """正常系: 色値の正規化"""
        # 16進数形式は変更されない
        assert self.parser.normalize_color_value("#ff0000") == "#ff0000"
        # その他の形式はそのまま
        assert self.parser.normalize_color_value("red") == "red"
        assert self.parser.normalize_color_value("rgb(255,0,0)") == "rgb(255,0,0)"

    def test_正常系_マーカー記法正規化(self):
        """正常系: マーカー記法の正規化"""
        # 全角記号の半角化
        assert self.parser.normalize_marker_syntax("太字＋赤") == "太字+赤"
        assert self.parser.normalize_marker_syntax("太字－青") == "太字-青"
        # 空白の除去
        assert self.parser.normalize_marker_syntax("  太字  ") == "太字"

    def test_正常系_ネストキーワード抽出(self):
        """正常系: ネストしたキーワード構造の抽出"""
        text = "通常のテキスト #太字#重要な内容## 続きのテキスト"
        nested = self.parser.extract_nested_keywords(text)

        assert len(nested) == 1
        assert nested[0]["keywords"] == ["太字"]
        assert nested[0]["content"] == "重要な内容"
        assert "position" in nested[0]
        assert "original" in nested[0]

    # ========== 異常系テスト（20%） ==========

    def test_異常系_空文字列マーカー解析(self):
        """異常系: 空文字列のマーカー解析"""
        keywords, attributes, errors = self.parser.parse_marker_keywords("")

        assert len(keywords) == 0
        assert len(attributes) == 0
        assert len(errors) == 0

    def test_異常系_無効な型のマーカー解析(self):
        """異常系: 無効な型のマーカー解析"""
        keywords, attributes, errors = self.parser.parse_marker_keywords(123)

        assert len(keywords) == 0
        assert len(attributes) == 0
        assert len(errors) == 1
        assert "Invalid marker content type" in errors[0]

    def test_異常系_不正な複合キーワード分割(self):
        """異常系: 不正な複合キーワード分割"""
        keywords = self.parser.split_compound_keywords(None)

        assert len(keywords) == 0

    def test_異常系_空のルビ記法解析(self):
        """異常系: 空のルビ記法解析"""
        result = self.parser.parse_ruby_content("")

        assert result is None

    def test_異常系_複合ブロック作成_空キーワード(self):
        """異常系: 空のキーワードでの複合ブロック作成"""
        node = self.parser.create_compound_block([], "テスト内容", {})

        assert node.type == "error"
        assert "キーワードが指定されていません" in str(node)

    def test_異常系_複合ブロック作成_不明キーワード(self):
        """異常系: 不明なキーワードでの複合ブロック作成"""
        node = self.parser.create_compound_block(["不明なキーワード"], "テスト内容", {})

        assert node.type == "error"
        assert "不明なキーワード" in str(node)

    def test_異常系_マーカー解析例外処理(self):
        """異常系: マーカー解析での例外処理"""
        # モックを使って例外を発生させる
        with patch.object(
            self.parser,
            "split_compound_keywords",
            side_effect=Exception("テストエラー"),
        ):
            keywords, attributes, errors = self.parser.parse_marker_keywords(
                "太字+イタリック"
            )

            assert len(errors) == 1
            assert "マーカー解析エラー" in errors[0]

    # ========== 境界値テスト（10%） ==========

    def test_境界値_非常に長いルビ記法(self):
        """境界値: 非常に長いルビ記法"""
        long_base = "a" * 1000
        long_ruby = "b" * 1000
        ruby_text = f"{long_base}|{long_ruby}"

        result = self.parser.parse_ruby_content(ruby_text)

        assert result is not None
        assert result["base"] == long_base
        assert result["ruby"] == long_ruby

    def test_境界値_複数パイプのルビ記法(self):
        """境界値: 複数のパイプを含むルビ記法"""
        result = self.parser.parse_ruby_content("漢字|かん|じ")

        assert result is not None
        assert result["base"] == "漢字"
        assert result["ruby"] == "かん|じ"  # 最初のパイプで分割

    def test_境界値_大量の複合キーワード(self):
        """境界値: 大量の複合キーワード"""
        many_keywords = "+".join(["太字"] * 100)
        keywords = self.parser.split_compound_keywords(many_keywords)

        # 有効なキーワードのみが含まれる
        assert len(keywords) == 100
        assert all(kw == "太字" for kw in keywords)

    def test_境界値_深いネスト構造(self):
        """境界値: 深いネスト構造"""
        deep_keywords = ["見出し1", "見出し2", "見出し3", "太字", "イタリック"]
        sorted_keywords = self.parser.sort_keywords_by_nesting_order(deep_keywords)

        assert len(sorted_keywords) == 5
        # ネスト順序が正しいか確認
        assert sorted_keywords.index("見出し1") < sorted_keywords.index("太字")
        assert sorted_keywords.index("太字") < sorted_keywords.index("イタリック")

    # ========== 統合テスト（10%） ==========

    def test_統合_複雑なマーカー解析(self):
        """統合: 複雑なマーカー解析の統合テスト"""
        complex_marker = "太字+イタリック+ハイライト"
        keywords, attributes, errors = self.parser.parse_marker_keywords(complex_marker)

        assert len(keywords) == 3
        assert "太字" in keywords
        assert "イタリック" in keywords
        assert "ハイライト" in keywords
        assert len(errors) == 0

    def test_統合_ルビ付き複合ブロック(self):
        """統合: ルビ記法を含む複合ブロック"""
        # ルビ記法の処理
        ruby_node = self.parser.create_ruby_node("漢字|かんじ")

        assert isinstance(ruby_node, Node)
        assert ruby_node.type == "ruby"
        assert ruby_node.content == "漢字"

    def test_統合_属性付き複合ブロック(self):
        """統合: 属性付きの複合ブロック作成"""
        attributes = {"color": "blue", "size": "large"}
        node = self.parser.create_compound_block(["ハイライト"], "テスト", attributes)

        assert isinstance(node, Node)
        # ハイライトの色属性が適用されているか確認
        if "color" in attributes:
            # スタイルが適用されているはず
            assert "style" in node.attributes or "styles" in node.metadata

    def test_統合_設定付き初期化(self):
        """統合: 設定付きでの初期化テスト"""
        config = {
            "enable_ruby": True,
            "compound_separator": "+",
            "strict_nesting": False,
        }

        parser = AdvancedKeywordParser(config)

        assert parser.config == config
        assert hasattr(parser, "advanced_patterns")
        assert hasattr(parser, "NESTING_ORDER")

    def test_統合_ブロックコンテンツ解析(self):
        """統合: ブロックコンテンツの解析"""
        content = "テスト内容"
        result = self.parser.parse_block_content(content)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == content

    # ========== パフォーマンステスト ==========

    def test_性能_大量複合キーワード分割(self):
        """性能: 大量の複合キーワード分割性能"""
        import time

        # 100個のキーワードを結合
        large_compound = "+".join(["太字"] * 100)

        start_time = time.time()
        keywords = self.parser.split_compound_keywords(large_compound)
        end_time = time.time()

        # 100個のキーワード分割が0.1秒以内に完了することを確認
        assert (end_time - start_time) < 0.1
        assert len(keywords) == 100

    def test_性能_複雑なネスト処理(self):
        """性能: 複雑なネスト処理の性能"""
        import time

        keywords = ["見出し1", "見出し2", "太字", "イタリック", "ハイライト"] * 10

        start_time = time.time()
        sorted_keywords = self.parser.sort_keywords_by_nesting_order(keywords)
        end_time = time.time()

        # 50個のキーワードソートが0.1秒以内に完了することを確認
        assert (end_time - start_time) < 0.1
        assert len(sorted_keywords) == 50

    def test_性能_ルビ記法大量処理(self):
        """性能: ルビ記法の大量処理性能"""
        import time

        ruby_texts = ["漢字|かんじ"] * 1000

        start_time = time.time()
        for ruby_text in ruby_texts:
            result = self.parser.parse_ruby_content(ruby_text)
            assert result is not None
        end_time = time.time()

        # 1000個のルビ解析が0.5秒以内に完了することを確認
        assert (end_time - start_time) < 0.5
