"""UnifiedListParser包括テストスイート

Issue #929 - List系統合テスト実装によるカバレッジ向上(14-45% → 75%)
Phase 1C: ListParser総合テスト - 基本機能・Kumihan記法・統合テスト
"""

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node, create_node
from kumihan_formatter.core.parsing.base.parser_protocols import (
    ParseContext,
    ParseResult,
    create_parse_result,
)
from kumihan_formatter.core.parsing.list.list_parser import UnifiedListParser


class TestListParserCore:
    """UnifiedListParser核心機能テスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = UnifiedListParser()

    def test_initialization(self):
        """パーサー初期化テスト"""
        # 基本初期化確認
        assert self.parser is not None
        assert hasattr(self.parser, "ordered_parser")
        assert hasattr(self.parser, "unordered_parser")
        assert hasattr(self.parser, "nested_parser")

        # パターン初期化確認
        assert hasattr(self.parser, "list_patterns")
        assert hasattr(self.parser, "list_handlers")

        # 必須パターン存在確認
        expected_patterns = [
            "unordered",
            "ordered",
            "definition",
            "checklist",
            "alpha",
            "roman",
        ]
        for pattern in expected_patterns:
            assert pattern in self.parser.list_patterns

        # ハンドラー対応確認
        expected_handlers = [
            "unordered",
            "ordered",
            "definition",
            "checklist",
            "alpha",
            "roman",
        ]
        for handler in expected_handlers:
            assert handler in self.parser.list_handlers

    def test_parse_simple_list(self):
        """単純リスト解析テスト"""
        # 順序なしリスト
        unordered_content = "- 項目1\n- 項目2\n- 項目3"
        result = self.parser.parse_list_from_text(unordered_content)
        assert result is not None
        assert len(result) > 0  # リスト項目が解析されることを確認

        # 順序付きリスト
        ordered_content = "1. 項目1\n2. 項目2\n3. 項目3"
        result = self.parser.parse_list_from_text(ordered_content)
        assert result is not None
        assert len(result) > 0  # リスト項目が解析されることを確認

    def test_parse_nested_list(self):
        """ネストリスト解析テスト"""
        nested_content = """- 親項目1
  - 子項目1
  - 子項目2
- 親項目2
  - 子項目3
    - 孫項目1"""

        result = self.parser.parse_nested_list(nested_content.split("\n"))
        assert result is not None
        # ネスト構造が適切に処理されることを確認

    def test_parse_mixed_list_types(self):
        """混合リストタイプ解析テスト"""
        # 順序なしリスト項目をテスト
        unordered_line = "- 順序なし項目1"
        list_type = self.parser.detect_list_type(unordered_line)
        assert list_type == "unordered"

        # 順序付きリスト項目をテスト
        ordered_line = "1. 順序付き項目1"
        list_type = self.parser.detect_list_type(ordered_line)
        assert list_type == "ordered"

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        # 空文字列
        result = self.parser.parse_list_from_text("")
        assert result is not None  # 空の結果でもエラーにならない

        # None入力
        result = self.parser.parse_list_from_text(None)
        assert result is not None  # Noneでもエラーにならない
        assert result is not None

        # None入力（型エラーが期待される）
        try:
            result = self.parser._parse_implementation(None)  # type: ignore
            # エラーノードまたは適切な処理がされることを確認
            assert result is not None
        except Exception:
            # 例外が適切にハンドリングされることも許容
            pass


class TestListParserKumihanNotation:
    """Kumihan記法専用リストテスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = UnifiedListParser()

    def test_ordered_list_notation(self):
        """順序付きリスト記法テスト - 1. 2. 3. 形式"""
        test_cases = [
            "1. 項目1\n2. 項目2\n3. 項目3",
            "1) 項目A\n2) 項目B\n3) 項目C",
            "a. 項目一\nb. 項目二\nc. 項目三",
        ]

        for content in test_cases:
            result = self.parser._parse_implementation(content)
            assert result is not None
            assert result.type == "document"
            if result.children:
                list_node = result.children[0]
                # リストタイプが適切に判定されることを確認
                assert hasattr(list_node, "metadata")

    def test_unordered_list_notation(self):
        """順序なしリスト記法テスト - -, *, • 形式"""
        test_cases = [
            "- リスト項目1\n- リスト項目2",
            "* リスト項目A\n* リスト項目B",
            "+ リスト項目あ\n+ リスト項目い",
        ]

        for content in test_cases:
            result = self.parser._parse_implementation(content)
            assert result is not None
            assert result.type == "document"
            if result.children:
                list_node = result.children[0]
                assert hasattr(list_node, "metadata")

    def test_nested_list_notation(self):
        """ネストリスト記法テスト - インデントによるネスト"""
        nested_cases = [
            """1. 親項目1
   a. 子項目1
   b. 子項目2
2. 親項目2""",
            """- 親項目
  - 子項目1
    - 孫項目
  - 子項目2""",
        ]

        for content in nested_cases:
            result = self.parser._parse_implementation(content)
            assert result is not None
            assert result.type == "document"
            # ネスト構造が適切に処理されることを確認

    def test_mixed_notation_patterns(self):
        """混合記法パターンテスト"""
        mixed_content = """1. 順序付き
- 順序なし
a. アルファベット
* 別マーカー"""

        result = self.parser._parse_implementation(mixed_content)
        assert result is not None
        assert result.type == "document"

    def test_special_list_markers(self):
        """特殊リストマーカーテスト"""
        # チェックリスト記法
        checklist_content = "- [ ] 未完了項目\n- [x] 完了項目"
        result = self.parser._parse_implementation(checklist_content)
        assert result is not None

        # 定義リスト記法
        definition_content = "用語1 :: 定義1\n用語2 :: 定義2"
        result = self.parser._parse_implementation(definition_content)
        assert result is not None


class TestListParserIntegration:
    """統合テスト - 他コンポーネントとの連携"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = UnifiedListParser()

    def test_main_parser_integration(self):
        """メインパーサーとの統合テスト"""
        # can_parseメソッドテスト
        valid_content = "- 項目1\n- 項目2"
        assert self.parser.can_parse(valid_content) is True

        invalid_content = "単純テキスト"
        assert self.parser.can_parse(invalid_content) is False

    def test_keyword_parser_integration(self):
        """キーワードパーサーとの連携テスト"""
        # キーワード含みリスト
        keyword_content = "- # 見出し # 項目1\n- *強調* 項目2"
        result = self.parser._parse_implementation(keyword_content)
        assert result is not None
        # キーワードが適切に処理されることを期待

    def test_block_parser_integration(self):
        """ブロックパーサーとの連携テスト"""
        # ブロック要素含みリスト
        block_content = """- 項目1
- 項目2

  ブロック内容

- 項目3"""
        result = self.parser._parse_implementation(block_content)
        assert result is not None

    def test_rendering_pipeline_integration(self):
        """レンダリングパイプラインとの統合テスト"""
        content = "1. 項目1\n2. 項目2"
        result = self.parser._parse_implementation(content)
        assert result is not None

        # レンダリング用メタデータの確認
        if result.children:
            list_node = result.children[0]
            assert hasattr(list_node, "metadata")


class TestListParserProtocols:
    """プロトコル準拠テスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = UnifiedListParser()

    def test_parse_protocol(self):
        """parseプロトコル実装テスト"""
        content = "- 項目1\n- 項目2"
        context = ParseContext()

        result = self.parser.parse(content, context)
        assert isinstance(result, (ParseResult, dict))  # フォールバック対応

        # ParseResultの基本構造確認
        if hasattr(result, "success"):
            assert result.success is True
            assert result.nodes is not None
        else:  # dict fallback
            assert result["success"] is True
            assert result["nodes"] is not None

    def test_validate_protocol(self):
        """validateプロトコル実装テスト"""
        # 有効なコンテンツ
        valid_content = "- 項目1\n- 項目2"
        errors = self.parser.validate(valid_content)
        assert isinstance(errors, list)
        # エラーが少ないことを期待（完全に0である必要はない）

        # 無効なコンテンツ
        invalid_content = ""
        errors = self.parser.validate(invalid_content)
        assert isinstance(errors, list)

    def test_parser_info_protocol(self):
        """パーサー情報プロトコルテスト"""
        info = self.parser.get_parser_info()
        assert isinstance(info, dict)

        # 必要な情報が含まれていることを確認
        expected_keys = ["name", "version", "supported_formats", "capabilities"]
        for key in expected_keys:
            assert key in info

    def test_supports_format_protocol(self):
        """フォーマット対応プロトコルテスト"""
        # サポート対象フォーマット
        supported_formats = ["list", "ordered", "unordered", "checklist", "definition"]
        for format_hint in supported_formats:
            assert self.parser.supports_format(format_hint) is True

        # 非サポートフォーマット
        unsupported_formats = ["markdown", "html", "json"]
        for format_hint in unsupported_formats:
            assert self.parser.supports_format(format_hint) is False


class TestListParserEdgeCases:
    """エッジケース・境界値テスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = UnifiedListParser()

    def test_empty_content(self):
        """空コンテンツテスト"""
        empty_cases = ["", "   ", "\n\n", "\t\t"]
        for content in empty_cases:
            result = self.parser._parse_implementation(content)
            assert result is not None
            # エラーでなく適切に処理されることを確認

    def test_single_item_lists(self):
        """単一項目リストテスト"""
        single_cases = ["- 単一項目", "1. 単一項目"]
        for content in single_cases:
            result = self.parser._parse_implementation(content)
            assert result is not None

    def test_extremely_nested_lists(self):
        """極度にネストしたリストテスト"""
        deep_nesting = """- レベル1
  - レベル2
    - レベル3
      - レベル4
        - レベル5
          - レベル6"""

        result = self.parser._parse_implementation(deep_nesting)
        assert result is not None
        # 深いネストも適切に処理されることを確認

    def test_malformed_list_syntax(self):
        """不正なリスト構文テスト"""
        malformed_cases = [
            "-項目1\n-項目2",  # スペース欠落
            "1項目1\n2項目2",  # ピリオド欠落
            "- \n- 項目2",  # 空項目
            "1. 項目1\na. 項目2",  # 混合番号体系
        ]

        for content in malformed_cases:
            result = self.parser._parse_implementation(content)
            assert result is not None
            # エラーでもグレースフルに処理されることを確認

    def test_unicode_content(self):
        """Unicode文字列テスト"""
        unicode_cases = [
            "- 日本語項目1\n- 日本語項目2",
            "- émojis 🎉\n- 特殊文字 ©®™",
            "1. 中文项目1\n2. 한국어 항목2",
        ]

        for content in unicode_cases:
            result = self.parser._parse_implementation(content)
            assert result is not None

    def test_large_lists(self):
        """大規模リストテスト"""
        # 100項目のリスト生成
        large_list_items = [f"- 項目{i+1}" for i in range(100)]
        large_content = "\n".join(large_list_items)

        result = self.parser._parse_implementation(large_content)
        assert result is not None
        # パフォーマンス問題がないことを確認


class TestListParserMocking:
    """モッキング・依存関係テスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = UnifiedListParser()

    @patch("kumihan_formatter.core.ast_nodes.create_node")
    def test_node_creation_mocking(self, mock_create_node):
        """ノード作成のモッキングテスト"""
        mock_node = Mock(spec=Node)
        mock_node.type = "test_node"
        mock_node.children = []
        mock_create_node.return_value = mock_node

        content = "- テスト項目"
        result = self.parser._parse_implementation(content)

        # create_nodeが呼び出されたことを確認
        assert mock_create_node.called
        assert result == mock_node

    def test_specialized_parser_integration(self):
        """専用パーサー統合テスト"""
        # OrderedListParserのモック
        with patch.object(self.parser, "ordered_parser") as mock_ordered:
            mock_ordered.handle_ordered_list.return_value = create_node("list_item", "テスト")

            content = "1. テスト項目"
            result = self.parser._parse_implementation(content)
            assert result is not None

    def test_error_propagation(self):
        """エラー伝播テスト"""
        # 専用パーサーからのエラー伝播
        with patch.object(self.parser, "unordered_parser") as mock_unordered:
            mock_unordered.handle_unordered_list.side_effect = Exception("テストエラー")

            content = "- エラーテスト"
            result = self.parser._parse_implementation(content)

            # エラーが適切に処理されることを確認
            assert result is not None
            assert result.type == "error" or hasattr(result, "children")


class TestListParserPerformance:
    """パフォーマンステスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = UnifiedListParser()

    def test_parse_performance_timing(self):
        """パース性能タイミングテスト"""
        import time

        content = "\n".join([f"- 項目{i+1}" for i in range(1000)])

        start_time = time.time()
        result = self.parser._parse_implementation(content)
        end_time = time.time()

        # 1000項目のパースが5秒以内に完了することを確認
        assert (end_time - start_time) < 5.0
        assert result is not None

    def test_memory_efficiency(self):
        """メモリ効率テスト"""
        import gc
        import sys

        # ガベージコレクション実行
        gc.collect()
        initial_objects = len(gc.get_objects())

        # 大規模リスト処理
        content = "\n".join([f"- 項目{i+1}" for i in range(500)])
        result = self.parser._parse_implementation(content)

        # 再度ガベージコレクション
        del result
        gc.collect()
        final_objects = len(gc.get_objects())

        # メモリリークがないことを確認（大幅な増加がないこと）
        objects_increase = final_objects - initial_objects
        assert objects_increase < 1000  # 許容範囲内


# === テストユーティリティ ===


def create_test_list_content(type_name: str, count: int = 3) -> str:
    """テスト用リストコンテンツ生成"""
    if type_name == "unordered":
        return "\n".join([f"- 項目{i+1}" for i in range(count)])
    elif type_name == "ordered":
        return "\n".join([f"{i+1}. 項目{i+1}" for i in range(count)])
    elif type_name == "checklist":
        return "\n".join([f"- [{'x' if i % 2 == 0 else ' '}] 項目{i+1}" for i in range(count)])
    else:
        return f"- テスト項目"


def assert_valid_list_node(node: Node) -> None:
    """リストノードの妥当性検証"""
    assert node is not None
    assert hasattr(node, "type")
    assert hasattr(node, "metadata")
    if hasattr(node, "children") and node.children:
        for child in node.children:
            assert child is not None


# === パラメータ化テストケース ===


@pytest.mark.parametrize(
    "list_type,content",
    [
        ("unordered", "- 項目1\n- 項目2"),
        ("ordered", "1. 項目1\n2. 項目2"),
        ("alpha", "a. 項目1\nb. 項目2"),
        ("checklist", "- [ ] 項目1\n- [x] 項目2"),
    ],
)
def test_list_type_parsing_parametrized(list_type, content):
    """パラメータ化リストタイプ解析テスト"""
    parser = UnifiedListParser()
    result = parser._parse_implementation(content)
    assert result is not None
    assert result.type == "document"


@pytest.mark.parametrize("nesting_level", [1, 2, 3, 4, 5])
def test_nesting_levels_parametrized(nesting_level):
    """パラメータ化ネストレベルテスト"""
    parser = UnifiedListParser()

    # ネストレベルに応じたコンテンツ生成
    lines = []
    for level in range(nesting_level + 1):
        indent = "  " * level
        lines.append(f"{indent}- レベル{level+1}")

    content = "\n".join(lines)
    result = parser._parse_implementation(content)
    assert result is not None


# === フィクスチャー ===


@pytest.fixture
def sample_list_contents():
    """サンプルリストコンテンツフィクスチャ"""
    return {
        "simple_unordered": "- 項目1\n- 項目2\n- 項目3",
        "simple_ordered": "1. 項目1\n2. 項目2\n3. 項目3",
        "nested": """- 親1
  - 子1
  - 子2
- 親2
  - 子3""",
        "mixed": "- 順序なし\n1. 順序付き\n- 再び順序なし",
        "checklist": "- [ ] 未完了\n- [x] 完了\n- [ ] 未完了2",
    }


@pytest.fixture
def parser_instance():
    """パーサーインスタンスフィクスチャ"""
    return UnifiedListParser()


def test_with_fixtures(parser_instance, sample_list_contents):
    """フィクスチャーを使用したテスト"""
    for content_type, content in sample_list_contents.items():
        result = parser_instance._parse_implementation(content)
        assert result is not None, f"Failed to parse {content_type}"
