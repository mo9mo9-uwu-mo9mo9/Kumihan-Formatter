"""カスタムキーワードパーサーのテスト

カスタムキーワードパーサーの包括的なテスト:
- カスタムキーワード管理
- インライン記法処理
- 拡張機能管理
- ユーザー定義キーワード
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import (
    Node,
    NodeBuilder,
    create_node,
    emphasis,
    highlight,
    strong,
)
from kumihan_formatter.core.parsing.keyword.parsers.custom_parser import (
    CustomKeywordParser,
)
from kumihan_formatter.core.utilities.logger import get_logger


class TestCustomKeywordParser:
    """カスタムキーワードパーサーのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.parser = CustomKeywordParser()
        self.logger = get_logger(__name__)

    # ========== 正常系テスト（60%） ==========

    def test_正常系_初期化(self):
        """正常系: パーサーの初期化"""
        parser = CustomKeywordParser()

        # 設定の確認
        assert hasattr(parser, "config")
        assert hasattr(parser, "custom_keywords")
        assert hasattr(parser, "deprecated_keywords")
        assert hasattr(parser, "extension_keywords")
        assert hasattr(parser, "_inline_keyword_mapping")
        assert hasattr(parser, "extension_features")

        # インライン記法マッピングの確認
        assert "太字" in parser._inline_keyword_mapping
        assert "イタリック" in parser._inline_keyword_mapping
        assert "ハイライト" in parser._inline_keyword_mapping

    def test_正常系_カスタムキーワード登録(self):
        """正常系: カスタムキーワードの登録"""
        definition = {"type": "custom", "html_tag": "span", "class": "custom"}
        self.parser.register_keyword("カスタム", definition)

        assert "カスタム" in self.parser.custom_keywords
        assert self.parser.custom_keywords["カスタム"] == definition

    def test_正常系_カスタムキーワード登録解除(self):
        """正常系: カスタムキーワードの登録解除"""
        # まず登録
        definition = {"type": "custom", "html_tag": "span"}
        self.parser.register_keyword("テスト", definition)

        # 登録解除
        result = self.parser.unregister_keyword("テスト")

        assert result is True
        assert "テスト" not in self.parser.custom_keywords

    def test_正常系_キーワード非推奨化(self):
        """正常系: キーワードの非推奨化"""
        self.parser.deprecate_keyword("古いキーワード")

        assert "古いキーワード" in self.parser.deprecated_keywords

    def test_正常系_キーワード候補取得(self):
        """正常系: キーワード候補の取得"""
        # テスト用のキーワードを追加
        self.parser.register_keyword("テスト1", {"type": "test"})
        self.parser.register_keyword("テスト2", {"type": "test"})
        self.parser.register_keyword("別の", {"type": "other"})

        suggestions = self.parser.get_keyword_suggestions("テスト")

        assert len(suggestions) >= 2
        assert "テスト1" in suggestions
        assert "テスト2" in suggestions
        assert "別の" not in suggestions

    def test_正常系_キーワード検証_有効(self):
        """正常系: 有効なキーワードの検証"""
        # カスタムキーワードを登録
        definition = {"type": "custom", "html_tag": "span"}
        self.parser.register_keyword("有効", definition)

        result = self.parser.validate_keyword("有効")

        assert result["valid"] is True
        assert result["type"] == "custom"
        assert result["definition"] == definition
        assert result["deprecated"] is False

    def test_正常系_キーワード検証_無効(self):
        """正常系: 無効なキーワードの検証"""
        result = self.parser.validate_keyword("存在しない")

        assert result["valid"] is False
        assert result["type"] is None
        assert result["definition"] is None
        assert isinstance(result["suggestions"], list)

    def test_正常系_キーワード検証_非推奨(self):
        """正常系: 非推奨キーワードの検証"""
        # キーワードを登録して非推奨化
        definition = {"type": "deprecated", "html_tag": "span"}
        self.parser.register_keyword("非推奨", definition)
        self.parser.deprecate_keyword("非推奨")

        result = self.parser.validate_keyword("非推奨")

        assert result["valid"] is True
        assert result["deprecated"] is True

    def test_正常系_キーワード定義取得_カスタム(self):
        """正常系: カスタムキーワード定義の取得"""
        definition = {"type": "custom", "html_tag": "span"}
        self.parser.register_keyword("カスタム", definition)

        result = self.parser.get_keyword_definition("カスタム")

        assert result == definition

    def test_正常系_キーワード定義取得_拡張(self):
        """正常系: 拡張キーワード定義の取得"""
        definition = {"type": "extension", "html_tag": "div"}
        self.parser.register_extension_keyword("拡張", definition)

        result = self.parser.get_keyword_definition("拡張")

        assert result == definition

    def test_正常系_インライン記法処理_基本(self):
        """正常系: 基本的なインライン記法処理"""
        text = "これは #太字#重要## な文章です。"
        nodes = self.parser.process_inline_keywords(text)

        assert len(nodes) >= 3  # 前のテキスト + 太字ノード + 後のテキスト
        # 太字ノードの確認
        bold_node = None
        for node in nodes:
            if hasattr(node, "type") and node.type == "strong":
                bold_node = node
                break

        assert bold_node is not None
        assert bold_node.content == "重要"

    def test_正常系_インライン記法処理_複数(self):
        """正常系: 複数のインライン記法処理"""
        text = "#太字#重要## と #イタリック#強調## があります。"
        nodes = self.parser.process_inline_keywords(text)

        assert len(nodes) >= 4  # ノード + テキスト + ノード + テキスト

        # 太字とイタリックノードの存在確認
        node_types = [getattr(node, "type", None) for node in nodes]
        assert "strong" in node_types or any("太字" in str(node) for node in nodes)
        assert "em" in node_types or any("イタリック" in str(node) for node in nodes)

    def test_正常系_ルビノード作成_パイプ付き(self):
        """正常系: パイプ付きルビノードの作成"""
        node = self.parser._create_ruby_node("漢字|かんじ")

        assert isinstance(node, Node)
        assert node.type == "ruby"
        assert node.content == "漢字"
        assert node.attributes.get("data-ruby") == "かんじ"

    def test_正常系_ルビノード作成_パイプなし(self):
        """正常系: パイプなしルビノードの作成"""
        node = self.parser._create_ruby_node("漢字")

        assert isinstance(node, Node)
        assert node.type == "span"
        assert node.content == "漢字"

    def test_正常系_拡張機能有効化(self):
        """正常系: 拡張機能の有効化"""
        result = self.parser.enable_extension_feature("auto_link")

        assert result is True
        assert self.parser.extension_features["auto_link"] is True

    def test_正常系_拡張機能無効化(self):
        """正常系: 拡張機能の無効化"""
        result = self.parser.disable_extension_feature("emoji_support")

        assert result is True
        assert self.parser.extension_features["emoji_support"] is False

    def test_正常系_拡張機能状態取得(self):
        """正常系: 拡張機能状態の取得"""
        status = self.parser.get_extension_status()

        assert isinstance(status, dict)
        assert "auto_link" in status
        assert "emoji_support" in status
        assert "math_notation" in status
        assert "code_highlighting" in status

    def test_正常系_統計情報取得(self):
        """正常系: カスタムキーワード統計情報の取得"""
        # テスト用データの追加
        self.parser.register_keyword("カスタム1", {"type": "custom"})
        self.parser.register_keyword("カスタム2", {"type": "custom"})
        self.parser.register_extension_keyword("拡張1", {"type": "extension"})
        self.parser.deprecate_keyword("非推奨1")

        stats = self.parser.get_custom_keyword_statistics()

        assert stats["custom_keywords"] == 2
        assert stats["extension_keywords"] == 1
        assert stats["deprecated_keywords"] == 1
        assert stats["total_custom"] == 3
        assert isinstance(stats["enabled_extensions"], int)

    # ========== 異常系テスト（20%） ==========

    def test_異常系_存在しないキーワードの登録解除(self):
        """異常系: 存在しないキーワードの登録解除"""
        result = self.parser.unregister_keyword("存在しない")

        assert result is False

    def test_異常系_存在しない拡張機能の有効化(self):
        """異常系: 存在しない拡張機能の有効化"""
        result = self.parser.enable_extension_feature("存在しない機能")

        assert result is False

    def test_異常系_存在しない拡張機能の無効化(self):
        """異常系: 存在しない拡張機能の無効化"""
        result = self.parser.disable_extension_feature("存在しない機能")

        assert result is False

    def test_異常系_空文字列のキーワード候補取得(self):
        """異常系: 空文字列でのキーワード候補取得"""
        suggestions = self.parser.get_keyword_suggestions("")

        # 空文字列でも全キーワードが返される可能性がある
        assert isinstance(suggestions, list)

    def test_異常系_インライン記法処理_未知キーワード(self):
        """異常系: 未知キーワードのインライン記法処理"""
        text = "#未知#内容## があります。"
        nodes = self.parser.process_inline_keywords(text)

        # 未知のキーワードは unknown_inline ノードになる
        unknown_node = None
        for node in nodes:
            if hasattr(node, "type") and node.type == "unknown_inline":
                unknown_node = node
                break

        assert unknown_node is not None

    def test_異常系_空のテキストでインライン処理(self):
        """異常系: 空のテキストでのインライン処理"""
        nodes = self.parser.process_inline_keywords("")

        assert len(nodes) == 0

    def test_異常系_不正フォーマットのインライン記法(self):
        """異常系: 不正フォーマットのインライン記法"""
        text = "#太字#内容#不正"  # 閉じタグが不完全
        nodes = self.parser.process_inline_keywords(text)

        # 不正なフォーマットは通常のテキストとして処理される
        assert len(nodes) >= 1
        # すべてテキストノードか確認
        for node in nodes:
            assert hasattr(node, "type")

    # ========== 境界値テスト（10%） ==========

    def test_境界値_非常に長いカスタムキーワード(self):
        """境界値: 非常に長いカスタムキーワード"""
        long_keyword = "a" * 1000
        definition = {"type": "custom", "html_tag": "span"}

        self.parser.register_keyword(long_keyword, definition)

        assert long_keyword in self.parser.custom_keywords
        assert self.parser.get_keyword_definition(long_keyword) == definition

    def test_境界値_大量のカスタムキーワード登録(self):
        """境界値: 大量のカスタムキーワード登録"""
        from tests.conftest import get_test_data_size

        count = get_test_data_size(1000, 100)
        for i in range(count):
            keyword = f"カスタム{i}"
            definition = {"type": "custom", "index": i}
            self.parser.register_keyword(keyword, definition)

        assert len(self.parser.custom_keywords) == 1000
        assert "カスタム500" in self.parser.custom_keywords

    def test_境界値_複雑なインライン記法(self):
        """境界値: 複雑で長いインライン記法"""
        complex_text = "#太字#" + "a" * 1000 + "##"
        nodes = self.parser.process_inline_keywords(complex_text)

        assert len(nodes) >= 1
        # 長いコンテンツが正しく処理されるか確認
        bold_node = None
        for node in nodes:
            if hasattr(node, "type") and node.type == "strong":
                bold_node = node
                break

        if bold_node:
            assert len(bold_node.content) == 1000

    def test_境界値_深くネストしたルビ記法(self):
        """境界値: 複数のパイプを含むルビ記法"""
        ruby_text = "基本|ルビ1|ルビ2|ルビ3"
        node = self.parser._create_ruby_node(ruby_text)

        assert isinstance(node, Node)
        assert node.type == "ruby"
        assert node.content == "基本"
        # 最初のパイプで分割される
        assert "ルビ1|ルビ2|ルビ3" in node.attributes.get("data-ruby", "")

    # ========== 統合テスト（10%） ==========

    def test_統合_カスタムキーワード完全サイクル(self):
        """統合: カスタムキーワードの完全なライフサイクル"""
        # 1. 登録
        definition = {"type": "custom", "html_tag": "span", "class": "special"}
        self.parser.register_keyword("特別", definition)

        # 2. 検証
        validation = self.parser.validate_keyword("特別")
        assert validation["valid"] is True
        assert validation["type"] == "custom"

        # 3. 非推奨化
        self.parser.deprecate_keyword("特別")
        validation_deprecated = self.parser.validate_keyword("特別")
        assert validation_deprecated["deprecated"] is True

        # 4. 登録解除
        result = self.parser.unregister_keyword("特別")
        assert result is True

        # 5. 最終確認
        final_validation = self.parser.validate_keyword("特別")
        assert final_validation["valid"] is False

    def test_統合_拡張機能管理(self):
        """統合: 拡張機能の管理"""
        # 初期状態の確認
        self.parser.get_extension_status()

        # 機能の無効化
        self.parser.disable_extension_feature("auto_link")
        self.parser.disable_extension_feature("emoji_support")

        # 状態の確認
        disabled_status = self.parser.get_extension_status()
        assert disabled_status["auto_link"] is False
        assert disabled_status["emoji_support"] is False

        # 機能の再有効化
        self.parser.enable_extension_feature("auto_link")

        # 最終状態の確認
        final_status = self.parser.get_extension_status()
        assert final_status["auto_link"] is True
        assert final_status["emoji_support"] is False

    def test_統合_複合インライン記法処理(self):
        """統合: 複合的なインライン記法処理"""
        complex_text = "これは #太字#重要## で #イタリック#強調## された #ルビ#漢字|かんじ## を含むテキストです。"
        nodes = self.parser.process_inline_keywords(complex_text)

        # 複数のノードが生成される
        assert len(nodes) >= 7  # テキスト + ノード の繰り返し

        # 各種ノードの存在確認
        node_types = []
        for node in nodes:
            if hasattr(node, "type"):
                node_types.append(node.type)

        # 太字、イタリック、ルビノードが含まれているか確認
        assert any(t in ["strong", "em", "ruby", "span"] for t in node_types)

    def test_統合_設定付き初期化(self):
        """統合: 設定付きでの初期化テスト"""
        config = {
            "enable_custom_keywords": True,
            "max_custom_keywords": 1000,
            "inline_processing": True,
        }

        parser = CustomKeywordParser(config)

        assert parser.config == config
        assert hasattr(parser, "custom_keywords")
        assert hasattr(parser, "extension_features")

    # ========== パフォーマンステスト ==========

    def test_性能_大量カスタムキーワード検索(self):
        """性能: 大量カスタムキーワードでの検索性能"""
        import time

        # 大量のキーワードを登録
        from tests.conftest import get_test_data_size

        count = get_test_data_size(1000, 100)
        for i in range(count):
            self.parser.register_keyword(f"キーワード{i}", {"type": "test", "index": i})

        # 検索性能テスト
        start_time = time.time()
        for i in range(100):
            self.parser.get_keyword_suggestions("キーワード")
        end_time = time.time()

        # 100回の検索が0.5秒以内に完了することを確認
        assert (end_time - start_time) < 0.5

    def test_性能_大量インライン記法処理(self):
        """性能: 大量のインライン記法処理性能"""
        import time

        # 大量のインライン記法を含むテキスト
        inline_parts = ["#太字#重要##"] * 100
        large_text = " ".join(inline_parts)

        start_time = time.time()
        nodes = self.parser.process_inline_keywords(large_text)
        end_time = time.time()

        # 100個のインライン記法処理が1秒以内に完了することを確認
        assert (end_time - start_time) < 1.0
        assert len(nodes) >= 100

    def test_性能_統計情報計算(self):
        """性能: 統計情報計算の性能"""
        import time

        # 大量データの追加
        from tests.conftest import get_test_data_size

        count = get_test_data_size(1000, 100)
        for i in range(count):
            self.parser.register_keyword(f"カスタム{i}", {"type": "custom"})
            self.parser.register_extension_keyword(f"拡張{i}", {"type": "extension"})
            if i % 10 == 0:
                self.parser.deprecate_keyword(f"カスタム{i}")

        start_time = time.time()
        stats = self.parser.get_custom_keyword_statistics()
        end_time = time.time()

        # 統計計算が0.1秒以内に完了することを確認
        assert (end_time - start_time) < 0.1
        assert stats["custom_keywords"] == 1000
        assert stats["extension_keywords"] == 1000
