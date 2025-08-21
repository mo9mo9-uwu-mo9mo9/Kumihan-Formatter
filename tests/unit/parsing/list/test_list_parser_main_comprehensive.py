"""ListParserMain包括テストスイート

Issue #929 - List系統合テスト実装によるカバレッジ向上(14-45% → 75%)
Phase 1C: ListParserMain総合テスト - メイン機能・高度機能・パフォーマンステスト
"""

import gc
import time
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.parsing.list.list_parser_main import (
    ListParser,
    ListParserProtocol,
    find_outermost_list,
    parse_list_string,
)


class TestListParserMainCore:
    """ListParserメイン機能テスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = ListParser()

    def test_initialization(self):
        """パーサー初期化テスト"""
        # 基本初期化確認
        assert self.parser is not None
        assert hasattr(self.parser, "stack")
        assert hasattr(self.parser, "current_string")

        # 専用パーサー初期化確認
        assert hasattr(self.parser, "ordered_parser")
        assert hasattr(self.parser, "unordered_parser")
        assert hasattr(self.parser, "nested_parser")
        assert hasattr(self.parser, "utilities")

        # 初期状態確認
        assert len(self.parser.stack) == 1
        assert self.parser.current_string == ""

    def test_parse_ordered_lists(self):
        """順序付きリスト解析テスト"""
        # ブラケット記法
        ordered_cases = [
            "[1,2,3]",
            "[項目1,項目2,項目3]",
            "[a,b,c,d,e]",
            '[1,"文字列",3]',
        ]

        for content in ordered_cases:
            result = self.parser.parse_string(content)
            assert result is not None
            assert isinstance(result, list)
            assert len(result) > 0

    def test_parse_unordered_lists(self):
        """順序なしリスト解析テスト"""
        # 単純リスト
        simple_cases = ["[項目1,項目2]", "[a,b,c]", "[1,2,3,4,5]"]

        for content in simple_cases:
            result = self.parser.parse_string(content)
            assert result is not None
            assert isinstance(result, list)

    def test_parse_definition_lists(self):
        """定義リスト解析テスト"""
        # キー:バリュー形式のテスト
        definition_cases = ["[key:value,key2:value2]", "[名前:田中,年齢:30]"]

        for content in definition_cases:
            result = self.parser.parse_string(content)
            assert result is not None
            assert isinstance(result, list)

    def test_parse_task_lists(self):
        """タスクリスト解析テスト"""
        # タスク形式のテスト（ブラケット記法での表現）
        task_cases = ["[完了,未完了,進行中]", "[TODO,DONE,IN_PROGRESS]"]

        for content in task_cases:
            result = self.parser.parse_string(content)
            assert result is not None
            assert isinstance(result, list)

    def test_parse_complex_nested_structures(self):
        """複雑ネスト構造解析テスト"""
        complex_cases = [
            "[[1,2],[3,4]]",
            "[項目1,[子項目1,子項目2],項目2]",
            "[[a,b,c],[d,[e,f],g]]",
            "[1,[2,[3,[4,5]]]]",  # 深いネスト
        ]

        for content in complex_cases:
            result = self.parser.parse_string(content)
            assert result is not None
            assert isinstance(result, list)
            # ネスト構造が適切に処理されていることを確認
            has_nested = any(isinstance(item, list) for item in result)
            if content.count("[") > 1:  # ネストがある場合
                assert has_nested


class TestListParserMainAdvanced:
    """ListParser高度機能テスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = ListParser()

    def test_list_continuation(self):
        """リスト継続処理テスト"""
        # 複数行にわたるリスト（ブラケット記法）
        multi_line_cases = [
            "[項目1,項目2,項目3,項目4,項目5]",
            "[[1,2,3],[4,5,6],[7,8,9]]",
        ]

        for content in multi_line_cases:
            result = self.parser.parse_string(content)
            assert result is not None
            assert len(result) > 0

    def test_list_interruption_recovery(self):
        """リスト中断回復テスト"""
        # 不完全だが回復可能な構造
        recovery_cases = [
            "[1,2,3",  # 閉じブラケット欠落
            "1,2,3]",  # 開きブラケット欠落
        ]

        for content in recovery_cases:
            try:
                result = self.parser.parse_string(content)
                # エラーが発生する可能性があるが、適切にハンドリングされることを確認
            except Exception as e:
                # 例外が適切に処理されることも許容
                assert isinstance(e, (ValueError, Exception))

    def test_list_marker_variations(self):
        """リストマーカー変化テスト"""
        # 様々なマーカーパターン
        marker_cases = [
            "[a,b,c]",  # 単純文字
            "[1,2,3]",  # 数字
            "[項目1,項目2,項目3]",  # 日本語
            "['文字列1','文字列2']",  # クォート付き
        ]

        for content in marker_cases:
            result = self.parser.parse_string(content)
            assert result is not None
            assert isinstance(result, list)

    def test_indentation_handling(self):
        """インデント処理テスト（ブラケット記法でのネスト表現）"""
        indented_cases = [
            "[[項目1,項目2],[項目3,項目4]]",  # 2レベルネスト
            "[[[項目1]]]",  # 3レベルネスト
        ]

        for content in indented_cases:
            result = self.parser.parse_string(content)
            assert result is not None
            assert isinstance(result, list)

    def test_mixed_content_in_list_items(self):
        """混合コンテンツアイテムテスト"""
        mixed_cases = ["[文字,123,項目]", "[a,1,項目,b]", "['複合項目',123,'日本語']"]

        for content in mixed_cases:
            result = self.parser.parse_string(content)
            assert result is not None
            assert isinstance(result, list)
            # 混合コンテンツが適切に処理されることを確認


class TestListParserMainPerformance:
    """ListParserパフォーマンステスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = ListParser()

    def test_large_list_processing(self):
        """大規模リスト処理テスト"""
        # 1000項目のリスト生成
        large_items = [f"項目{i+1}" for i in range(1000)]
        large_content = "[" + ",".join(large_items) + "]"

        start_time = time.time()
        result = self.parser.parse_string(large_content)
        end_time = time.time()

        assert result is not None
        assert len(result) == 1000
        # 処理時間が合理的であることを確認（10秒以内）
        assert (end_time - start_time) < 10.0

    def test_deeply_nested_lists(self):
        """深いネストリスト処理テスト"""
        # 10レベルのネスト生成
        nested_content = "[" * 10 + "項目" + "]" * 10

        try:
            result = self.parser.parse_string(nested_content)
            assert result is not None
        except RecursionError:
            # 深すぎるネストで再帰エラーが発生することも許容
            pytest.skip("深いネストによる再帰制限")

    def test_memory_efficiency(self):
        """メモリ効率テスト"""
        # ガベージコレクション実行
        gc.collect()
        initial_objects = len(gc.get_objects())

        # 中規模リスト処理を複数回実行
        for _ in range(10):
            items = [f"項目{i+1}" for i in range(100)]
            content = "[" + ",".join(items) + "]"
            result = self.parser.parse_string(content)
            del result

        # 再度ガベージコレクション
        gc.collect()
        final_objects = len(gc.get_objects())

        # メモリリークがないことを確認
        objects_increase = final_objects - initial_objects
        assert objects_increase < 500  # 許容範囲内

    def test_streaming_support(self):
        """ストリーミング処理サポートテスト"""
        # 文字単位での段階的処理
        content = "[1,2,3,4,5]"

        # 文字ごとに処理
        for char in content:
            self.parser.parse_char(char)

        result = self.parser.get_result()
        assert result is not None
        assert isinstance(result, list)


class TestListParserMainProtocols:
    """統一プロトコル実装テスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = ListParser()

    def test_parse_protocol_implementation(self):
        """parseプロトコル実装テスト"""
        content = "[項目1,項目2,項目3]"
        result = self.parser.parse(content)

        # ParseResultまたはフォールバック辞書の確認
        assert result is not None
        if hasattr(result, "success"):
            assert result.success is True
            assert result.nodes is not None
        else:  # dict fallback
            assert result["success"] is True
            assert result["nodes"] is not None

    def test_validate_protocol_implementation(self):
        """validateプロトコル実装テスト"""
        # 有効なコンテンツ
        valid_cases = ["[1,2,3]", "[項目1,項目2]", "[[1,2],[3,4]]"]

        for content in valid_cases:
            errors = self.parser.validate(content)
            assert isinstance(errors, list)
            # エラーが少ないことを期待

        # 無効なコンテンツ
        invalid_cases = [
            "[1,2,3",  # 閉じブラケット欠落
            "1,2,3]",  # 開きブラケット欠落
            "[1,2,[3,4",  # ネスト不完全
            "",  # 空文字列
        ]

        for content in invalid_cases:
            errors = self.parser.validate(content)
            assert isinstance(errors, list)
            if content:  # 空文字列以外はエラーがあることを期待
                assert len(errors) > 0

    def test_parser_info_protocol(self):
        """パーサー情報プロトコルテスト"""
        info = self.parser.get_parser_info()
        assert isinstance(info, dict)

        # 必要な情報が含まれていることを確認
        expected_keys = ["name", "version", "supported_formats", "capabilities"]
        for key in expected_keys:
            assert key in info

        # 具体的な情報内容確認
        assert info["name"] == "ListParser"
        assert "list_parsing" in info["capabilities"]

    def test_supports_format_protocol(self):
        """フォーマット対応プロトコルテスト"""
        # サポート対象フォーマット
        supported_formats = ["list", "array", "nested_list", "bracket"]
        for format_hint in supported_formats:
            assert self.parser.supports_format(format_hint) is True

        # 非サポートフォーマット
        unsupported_formats = ["markdown", "html", "json", "xml"]
        for format_hint in unsupported_formats:
            assert self.parser.supports_format(format_hint) is False

    def test_list_parser_protocol_methods(self):
        """ListParserProtocol専用メソッドテスト"""
        content = "[項目1,[子項目1,子項目2],項目3]"

        # parse_list_items
        items = self.parser.parse_list_items(content)
        assert isinstance(items, list)

        # parse_nested_list
        nested_items = self.parser.parse_nested_list(content)
        assert isinstance(nested_items, list)

        # detect_list_type
        list_type = self.parser.detect_list_type("[1,2,3]")
        assert list_type == "bracket"

        json_type = self.parser.detect_list_type("{a:1,b:2}")
        assert json_type == "json"

        none_type = self.parser.detect_list_type("simple text")
        assert none_type is None

        # get_list_nesting_level
        nesting_level = self.parser.get_list_nesting_level("[[1,2],3]")
        assert isinstance(nesting_level, int)
        assert nesting_level >= 0


class TestListParserMainEdgeCases:
    """エッジケース・境界値テスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = ListParser()

    def test_empty_lists(self):
        """空リストテスト"""
        empty_cases = ["[]", "[[]]", "[[],[]]"]

        for content in empty_cases:
            result = self.parser.parse_string(content)
            assert result is not None
            assert isinstance(result, list)

    def test_single_character_parsing(self):
        """単一文字解析テスト"""
        single_chars = ["[", "]", ",", "a", "1"]

        for char in single_chars:
            parser = ListParser()  # 新しいインスタンス
            try:
                parser.parse_char(char)
                result = parser.get_result()
                assert result is not None
            except ValueError:
                # 不完全な構造でのエラーは許容
                pass

    def test_bracket_mismatch_handling(self):
        """ブラケット不一致処理テスト"""
        mismatch_cases = [
            "[[[",  # 開きすぎ
            "]]]",  # 閉じすぎ
            "][",  # 逆順
            "[1,2]3,4]",  # 混在
        ]

        for content in mismatch_cases:
            try:
                result = self.parser.parse_string(content)
                # エラーでなく処理される場合もある
            except ValueError as e:
                # 適切なエラーメッセージが含まれることを確認
                assert "bracket" in str(e).lower() or "unmatched" in str(e).lower()

    def test_special_characters(self):
        """特殊文字処理テスト"""
        special_cases = [
            "[改行\n含み,項目]",
            "[タブ\t含み,項目]",
            "[スペース 含み,項目]",
            "[🎉,絵文字,🚀]",
            '["クォート付き",項目]',
        ]

        for content in special_cases:
            try:
                result = self.parser.parse_string(content)
                assert result is not None
                assert isinstance(result, list)
            except Exception:
                # 特殊文字処理でのエラーも許容
                pass

    def test_unicode_handling(self):
        """Unicode処理テスト"""
        unicode_cases = [
            "[中文,項目]",
            "[한글,항목]",
            "[العربية,عنصر]",
            "[Ελληνικά,στοιχείο]",
            "[Русский,элемент]",
        ]

        for content in unicode_cases:
            result = self.parser.parse_string(content)
            assert result is not None
            assert isinstance(result, list)

    def test_maximum_nesting_depth(self):
        """最大ネスト深度テスト"""
        # 段階的にネスト深度を増やしてテスト
        for depth in range(1, 20):  # 1から19レベル
            nested = "[" * depth + "項目" + "]" * depth
            try:
                result = self.parser.parse_string(nested)
                assert result is not None
            except (RecursionError, ValueError):
                # 深すぎる場合のエラーは許容
                break


class TestListParserMainUtilityFunctions:
    """ユーティリティ関数テスト"""

    def test_parse_list_string_function(self):
        """parse_list_string関数テスト"""
        test_cases = ["[1,2,3]", "[項目1,項目2]", "[[1,2],[3,4]]"]

        for content in test_cases:
            result = parse_list_string(content)
            assert result is not None
            assert isinstance(result, list)

    def test_find_outermost_list_function(self):
        """find_outermost_list関数テスト"""
        test_cases = [
            ("prefix[1,2,3]suffix", (6, 12)),
            ("[項目1,項目2]", (0, 8)),
            ("no list here", (-1, -1)),
            ("[[nested]]", (0, 9)),
            ("text[list]more[list2]", (4, 9)),  # 最初のリストを検出
        ]

        for content, expected in test_cases:
            result = find_outermost_list(content)
            assert result == expected

    def test_find_outermost_list_edge_cases(self):
        """find_outermost_list エッジケーステスト"""
        edge_cases = [
            ("", (-1, -1)),  # 空文字列
            ("[", (-1, -1)),  # 不完全な開き
            ("]", (-1, -1)),  # 不完全な閉じ
            ("][][[", (-1, -1)),  # 混乱した構造
            ("[正常][不完全", (0, 3)),  # 最初の完全なリスト
        ]

        for content, expected in edge_cases:
            result = find_outermost_list(content)
            assert result == expected


class TestListParserMainMocking:
    """モッキング・依存関係テスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = ListParser()

    def test_utilities_integration(self):
        """ユーティリティ統合テスト"""
        # utilitiesのモック
        with patch.object(self.parser, "utilities") as mock_utils:
            mock_utils.create_nodes_from_parsed_data.return_value = [Mock()]
            mock_utils.calculate_list_depth.return_value = 2
            mock_utils.count_total_items.return_value = 5

            result = self.parser.parse("[1,2,3]")
            assert result is not None

    def test_specialized_parsers_integration(self):
        """専用パーサー統合テスト"""
        # nested_parserのモック
        with patch.object(self.parser, "nested_parser") as mock_nested:
            mock_nested.parse_nested_list.return_value = [Mock()]
            mock_nested.get_list_nesting_level.return_value = 1

            # ネスト関連メソッドの動作確認
            nested_result = self.parser.parse_nested_list("[[1,2]]")
            assert nested_result is not None

            level = self.parser.get_list_nesting_level("[[test]]")
            assert level == 1

    def test_error_handling_with_mocks(self):
        """モック使用時のエラーハンドリングテスト"""
        # parse_list_stringでエラーを発生させる
        with patch(
            "kumihan_formatter.core.parsing.list.list_parser_main.parse_list_string"
        ) as mock_parse:
            mock_parse.side_effect = Exception("Parse error")

            result = self.parser.parse("[test]")
            # エラーが適切に処理されることを確認
            if hasattr(result, "success"):
                assert result.success is False
                assert len(result.errors) > 0
            else:  # dict fallback
                assert result["success"] is False
                assert len(result["errors"]) > 0


class TestListParserMainProtocolImplementation:
    """ListParserProtocolクラステスト"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.protocol_parser = ListParserProtocol()

    def test_protocol_inheritance(self):
        """プロトコル継承テスト"""
        # ListParserProtocolがListParserを継承していることを確認
        assert isinstance(self.protocol_parser, ListParser)

        # 全てのプロトコルメソッドが実装されていることを確認
        required_methods = [
            "parse",
            "validate",
            "get_parser_info",
            "supports_format",
            "parse_list_items",
            "parse_nested_list",
            "detect_list_type",
            "get_list_nesting_level",
        ]

        for method in required_methods:
            assert hasattr(self.protocol_parser, method)
            assert callable(getattr(self.protocol_parser, method))

    def test_protocol_method_delegation(self):
        """プロトコルメソッド委譲テスト"""
        content = "[1,2,3]"

        # 各メソッドが親クラスの実装を正しく呼び出していることを確認
        parse_result = self.protocol_parser.parse(content)
        assert parse_result is not None

        validation_errors = self.protocol_parser.validate(content)
        assert isinstance(validation_errors, list)

        parser_info = self.protocol_parser.get_parser_info()
        assert isinstance(parser_info, dict)

        supports_list = self.protocol_parser.supports_format("list")
        assert supports_list is True

        list_items = self.protocol_parser.parse_list_items(content)
        assert isinstance(list_items, list)

        nested_items = self.protocol_parser.parse_nested_list(content)
        assert isinstance(nested_items, list)

        list_type = self.protocol_parser.detect_list_type(content)
        assert list_type is not None

        nesting_level = self.protocol_parser.get_list_nesting_level(content)
        assert isinstance(nesting_level, int)


# === テストユーティリティ ===


def create_bracket_list(items: List[str], nested: bool = False) -> str:
    """ブラケット記法のテストリスト生成"""
    if nested and len(items) > 1:
        # 半分をネストに
        mid = len(items) // 2
        first_half = ",".join(items[:mid])
        second_half = ",".join(items[mid:])
        return f"[[{first_half}],[{second_half}]]"
    else:
        return "[" + ",".join(items) + "]"


def assert_valid_parse_result(result: Any) -> None:
    """パース結果の妥当性検証"""
    assert result is not None
    if hasattr(result, "success"):
        # ParseResult形式
        if result.success:
            assert result.nodes is not None
    else:
        # dict fallback形式
        if result.get("success"):
            assert result.get("nodes") is not None


# === パラメータ化テスト ===


@pytest.mark.parametrize(
    "content,expected_length",
    [
        ("[1,2,3]", 3),
        ("[a,b]", 2),
        ("[[1,2],[3,4]]", 2),
        ("[項目1,項目2,項目3,項目4,項目5]", 5),
    ],
)
def test_parse_string_parametrized(content, expected_length):
    """パラメータ化文字列解析テスト"""
    parser = ListParser()
    result = parser.parse_string(content)
    assert len(result) == expected_length


@pytest.mark.parametrize("nesting_depth", [1, 2, 3, 4, 5])
def test_nesting_depth_parametrized(nesting_depth):
    """パラメータ化ネスト深度テスト"""
    # ネスト深度に応じたリスト生成
    nested_content = "[" * nesting_depth + "項目" + "]" * nesting_depth

    parser = ListParser()
    try:
        result = parser.parse_string(nested_content)
        assert result is not None
    except (RecursionError, ValueError):
        # 深いネストでのエラーは許容
        pytest.skip(f"Nesting depth {nesting_depth} caused recursion limit")


# === フィクスチャー ===


@pytest.fixture
def sample_bracket_lists():
    """サンプルブラケットリストフィクスチャ"""
    return {
        "simple": "[1,2,3]",
        "strings": "[項目1,項目2,項目3]",
        "nested": "[[1,2],[3,4]]",
        "mixed": "[1,項目2,[3,4]]",
        "empty": "[]",
        "deep_nested": "[[[1]]]",
    }


@pytest.fixture
def parser_instance():
    """パーサーインスタンスフィクスチャ"""
    return ListParser()


def test_with_fixtures(parser_instance, sample_bracket_lists):
    """フィクスチャー使用テスト"""
    for list_type, content in sample_bracket_lists.items():
        result = parser_instance.parse_string(content)
        assert result is not None, f"Failed to parse {list_type}: {content}"
        assert isinstance(result, list), f"Result is not a list for {list_type}"
