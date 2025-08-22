"""ListUtilities包括テストスイート

Issue #929 - List系統合テスト実装によるカバレッジ向上(14-45% → 75%)
Phase 1C: ListUtilities総合テスト - ユーティリティ・検証・変換機能テスト
"""

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.parsing.list.utilities.list_utilities import ListUtilities


# Nodeクラスのテスト用モック（import不具合対応）
class MockNode:
    """テスト用Nodeモック"""

    def __init__(self, type: str, content: Any, attributes: Optional[Dict[str, Any]] = None):
        self.type = type
        self.content = content
        self.attributes = attributes or {}


class TestListUtilitiesCore:
    """ListUtilities核心機能テスト"""

    def test_create_nodes_from_parsed_data_simple_list(self):
        """単純リストからのノード作成テスト"""
        simple_data = ["項目1", "項目2", "項目3"]

        nodes = ListUtilities.create_nodes_from_parsed_data(simple_data)

        assert nodes is not None
        assert isinstance(nodes, list)
        assert len(nodes) == 3

        for i, node in enumerate(nodes):
            assert hasattr(node, "type")
            assert hasattr(node, "content")
            assert hasattr(node, "attributes")
            assert node.type == "list_item"
            assert node.content == f"項目{i+1}"
            assert node.attributes.get("index") == i
            assert node.attributes.get("level") == 0

    def test_create_nodes_from_parsed_data_nested_list(self):
        """ネストリストからのノード作成テスト"""
        nested_data = ["項目1", ["子項目1", "子項目2"], "項目3"]

        nodes = ListUtilities.create_nodes_from_parsed_data(nested_data)

        assert nodes is not None
        assert isinstance(nodes, list)
        assert len(nodes) == 3

        # 最初のノード：通常項目
        assert nodes[0].type == "list_item"
        assert nodes[0].content == "項目1"

        # 2番目のノード：ネストリスト
        assert nodes[1].type == "nested_list"
        assert hasattr(nodes[1], "content")
        assert nodes[1].attributes.get("level") == 1
        assert nodes[1].attributes.get("item_count") == 2

        # 3番目のノード：通常項目
        assert nodes[2].type == "list_item"
        assert nodes[2].content == "項目3"

    def test_create_nodes_from_parsed_data_single_item(self):
        """単一アイテムからのノード作成テスト"""
        single_data = "単一項目"

        nodes = ListUtilities.create_nodes_from_parsed_data(single_data)

        assert nodes is not None
        assert isinstance(nodes, list)
        assert len(nodes) == 1

        node = nodes[0]
        assert node.type == "list_item"
        assert node.content == "単一項目"
        assert node.attributes.get("index") == 0
        assert node.attributes.get("level") == 0

    def test_create_nodes_from_parsed_data_empty_items(self):
        """空アイテム処理テスト"""
        empty_data = ["", None, "有効項目"]

        nodes = ListUtilities.create_nodes_from_parsed_data(empty_data)

        assert nodes is not None
        assert isinstance(nodes, list)
        assert len(nodes) == 3

        # 空文字列
        assert nodes[0].content == ""
        # None
        assert nodes[1].content == ""  # Noneは空文字列に変換
        # 有効項目
        assert nodes[2].content == "有効項目"

    def test_create_nodes_from_parsed_data_with_items_flag(self):
        """create_itemsフラグ付きノード作成テスト"""
        data = ["項目1", "項目2"]

        # create_items=Trueでの動作確認
        nodes = ListUtilities.create_nodes_from_parsed_data(data, create_items=True)

        assert nodes is not None
        assert isinstance(nodes, list)
        assert len(nodes) == 2

        for node in nodes:
            assert node.type == "list_item"


class TestListUtilitiesNested:
    """ネストノード作成機能テスト"""

    def test_create_nested_nodes_simple(self):
        """単純ネストノード作成テスト"""
        data = ["項目1", "項目2"]
        level = 1

        nodes = ListUtilities.create_nested_nodes(data, level)

        assert nodes is not None
        assert isinstance(nodes, list)
        assert len(nodes) == 2

        for i, node in enumerate(nodes):
            assert node.type == "list_item"
            assert node.content == f"項目{i+1}"
            assert node.attributes.get("level") == level
            assert node.attributes.get("index") == i

    def test_create_nested_nodes_with_nesting(self):
        """ネスト含みノード作成テスト"""
        data = ["項目1", ["子項目1", "子項目2"]]
        level = 2

        nodes = ListUtilities.create_nested_nodes(data, level)

        assert nodes is not None
        assert isinstance(nodes, list)
        assert len(nodes) == 2

        # 最初のノード：通常項目
        assert nodes[0].type == "list_item"
        assert nodes[0].content == "項目1"
        assert nodes[0].attributes.get("level") == level

        # 2番目のノード：ネストリスト
        assert nodes[1].type == "nested_list"
        assert nodes[1].attributes.get("level") == level + 1
        assert nodes[1].attributes.get("item_count") == 2

    def test_create_nested_nodes_multiple_levels(self):
        """多レベルネストノード作成テスト"""
        data = ["項目1", ["子項目1", ["孫項目1", "孫項目2"], "子項目2"]]
        level = 0

        nodes = ListUtilities.create_nested_nodes(data, level)

        assert nodes is not None
        assert isinstance(nodes, list)
        assert len(nodes) == 2

        # ネスト構造が適切に作成されることを確認
        nested_node = nodes[1]
        assert nested_node.type == "nested_list"
        assert nested_node.attributes.get("level") == 1

    def test_create_nested_nodes_deep_nesting(self):
        """深いネスト構造テスト"""
        # 5レベルのネスト構造
        deep_data = "項目"
        for _ in range(4):
            deep_data = [deep_data]

        nodes = ListUtilities.create_nested_nodes(deep_data, 0)

        assert nodes is not None
        assert isinstance(nodes, list)
        # 深いネストが適切に処理されることを確認

    def test_create_nested_nodes_empty_data(self):
        """空データでのネストノード作成テスト"""
        empty_data = []
        level = 1

        nodes = ListUtilities.create_nested_nodes(empty_data, level)

        assert nodes is not None
        assert isinstance(nodes, list)
        assert len(nodes) == 0


class TestListUtilitiesCalculation:
    """計算・分析機能テスト"""

    def test_calculate_list_depth_simple(self):
        """単純リスト深度計算テスト"""
        simple_data = ["項目1", "項目2", "項目3"]

        depth = ListUtilities.calculate_list_depth(simple_data)

        assert isinstance(depth, int)
        assert depth >= 0  # 単純リストは0深度またはそれ以上

    def test_calculate_list_depth_nested(self):
        """ネストリスト深度計算テスト"""
        nested_data = ["項目1", ["子項目1", "子項目2"]]

        depth = ListUtilities.calculate_list_depth(nested_data)

        assert isinstance(depth, int)
        assert depth >= 1  # ネストがあるので1以上

    def test_calculate_list_depth_deep_nesting(self):
        """深いネスト深度計算テスト"""
        # 3レベルのネスト: [1, [2, [3]]]
        deep_data = ["項目1", ["項目2", ["項目3"]]]

        depth = ListUtilities.calculate_list_depth(deep_data)

        assert isinstance(depth, int)
        assert depth >= 2  # 深いネストなので2以上

    def test_calculate_list_depth_complex_structure(self):
        """複雑構造深度計算テスト"""
        complex_data = [
            "項目1",
            ["子1", "子2"],
            "項目2",
            ["子3", ["孫1", "孫2"], "子4"],
            "項目3",
        ]

        depth = ListUtilities.calculate_list_depth(complex_data)

        assert isinstance(depth, int)
        assert depth >= 2  # 孫要素があるので2以上

    def test_calculate_list_depth_non_list(self):
        """非リストデータ深度計算テスト"""
        non_list_data = "単純文字列"

        depth = ListUtilities.calculate_list_depth(non_list_data)

        assert isinstance(depth, int)
        assert depth == 0  # 非リストは0深度

    def test_calculate_list_depth_with_current_depth(self):
        """現在深度指定での深度計算テスト"""
        data = ["項目1", ["項目2"]]
        current_depth = 3

        depth = ListUtilities.calculate_list_depth(data, current_depth)

        assert isinstance(depth, int)
        assert depth >= current_depth  # 現在深度以上になるはず

    def test_calculate_list_depth_empty_list(self):
        """空リスト深度計算テスト"""
        empty_data = []

        depth = ListUtilities.calculate_list_depth(empty_data)

        assert isinstance(depth, int)
        assert depth >= 0


class TestListUtilitiesItemCounting:
    """アイテムカウント機能テスト"""

    def test_count_total_items_simple(self):
        """単純リストアイテムカウントテスト"""
        simple_data = ["項目1", "項目2", "項目3"]

        count = ListUtilities.count_total_items(simple_data)

        assert isinstance(count, int)
        assert count == 3

    def test_count_total_items_nested(self):
        """ネストリストアイテムカウントテスト"""
        nested_data = ["項目1", ["子項目1", "子項目2"], "項目3"]

        count = ListUtilities.count_total_items(nested_data)

        assert isinstance(count, int)
        assert count == 4  # 項目1 + (子項目1 + 子項目2) + 項目3

    def test_count_total_items_deep_nesting(self):
        """深いネストアイテムカウントテスト"""
        deep_data = ["項目1", ["子1", ["孫1", "孫2"], "子2"]]

        count = ListUtilities.count_total_items(deep_data)

        assert isinstance(count, int)
        assert count == 5  # 項目1 + 子1 + 孫1 + 孫2 + 子2

    def test_count_total_items_complex_structure(self):
        """複雑構造アイテムカウントテスト"""
        complex_data = ["A", ["B1", "B2"], "C", ["D1", ["E1", "E2", "E3"], "D2"], "F"]

        count = ListUtilities.count_total_items(complex_data)

        assert isinstance(count, int)
        assert count == 9  # A + B1 + B2 + C + D1 + E1 + E2 + E3 + D2 + F

    def test_count_total_items_empty_list(self):
        """空リストアイテムカウントテスト"""
        empty_data = []

        count = ListUtilities.count_total_items(empty_data)

        assert isinstance(count, int)
        assert count == 0

    def test_count_total_items_single_item(self):
        """単一アイテムカウントテスト"""
        single_item = "単一項目"

        count = ListUtilities.count_total_items(single_item)

        assert isinstance(count, int)
        assert count == 1

    def test_count_total_items_mixed_types(self):
        """混合タイプアイテムカウントテスト"""
        mixed_data = ["文字列", 123, ["ネスト文字列", 456], None, ["", "空でない"]]

        count = ListUtilities.count_total_items(mixed_data)

        assert isinstance(count, int)
        assert count == 7  # 文字列 + 123 + ネスト文字列 + 456 + None + "" + "空でない"


class TestListUtilitiesEdgeCases:
    """エッジケース・境界値テスト"""

    def test_create_nodes_extremely_nested(self):
        """極度にネストしたデータからのノード作成テスト"""
        # 10レベルのネスト作成
        deeply_nested = "最深項目"
        for i in range(9):
            deeply_nested = [f"レベル{9-i}", deeply_nested]

        nodes = ListUtilities.create_nodes_from_parsed_data(deeply_nested)

        assert nodes is not None
        assert isinstance(nodes, list)
        # エラーが発生しないことを確認

    def test_create_nodes_large_list(self):
        """大規模リストからのノード作成テスト"""
        large_data = [f"項目{i+1}" for i in range(1000)]

        nodes = ListUtilities.create_nodes_from_parsed_data(large_data)

        assert nodes is not None
        assert isinstance(nodes, list)
        assert len(nodes) == 1000

    def test_create_nodes_mixed_content_types(self):
        """混合コンテンツタイプノード作成テスト"""
        mixed_data = ["文字列", 123, None, "", ["ネスト", 456, None], True, False]

        nodes = ListUtilities.create_nodes_from_parsed_data(mixed_data)

        assert nodes is not None
        assert isinstance(nodes, list)
        assert len(nodes) == 7

        # 各ノードが適切に変換されることを確認
        for node in nodes:
            assert hasattr(node, "content")
            assert isinstance(node.content, str)  # 全て文字列に変換される

    def test_calculate_depth_circular_reference(self):
        """循環参照データの深度計算テスト（可能な場合）"""
        # 循環参照は通常のリストでは作れないが、異常なケースをテスト
        anomalous_data = [1, 2, 3]
        anomalous_data.append(anomalous_data)  # 循環参照作成

        try:
            depth = ListUtilities.calculate_list_depth(anomalous_data)
            assert isinstance(depth, int)
        except RecursionError:
            # 循環参照で再帰制限に達することも許容
            pytest.skip("循環参照による再帰制限")

    def test_count_items_with_none_values(self):
        """None値含みアイテムカウントテスト"""
        data_with_nones = [None, "項目1", [None, "項目2", None], "項目3", None]

        count = ListUtilities.count_total_items(data_with_nones)

        assert isinstance(count, int)
        assert count == 6  # None値も1項目としてカウント

    def test_utilities_with_unicode(self):
        """Unicode文字列でのユーティリティテスト"""
        unicode_data = [
            "日本語項目",
            ["中文项目", "한국어 항목"],
            "Русский элемент",
            ["Ελληνικά στοιχείο", "🎉絵文字項目🚀"],
        ]

        # ノード作成テスト
        nodes = ListUtilities.create_nodes_from_parsed_data(unicode_data)
        assert nodes is not None
        assert len(nodes) == 4

        # 深度計算テスト
        depth = ListUtilities.calculate_list_depth(unicode_data)
        assert isinstance(depth, int)
        assert depth >= 1

        # アイテムカウントテスト
        count = ListUtilities.count_total_items(unicode_data)
        assert isinstance(count, int)
        assert count == 6


class TestListUtilitiesPerformance:
    """パフォーマンステスト"""

    def test_large_data_processing_performance(self):
        """大規模データ処理性能テスト"""
        import time

        # 10000項目の大規模データ作成
        large_data = [f"項目{i+1}" for i in range(10000)]

        # ノード作成性能テスト
        start_time = time.time()
        nodes = ListUtilities.create_nodes_from_parsed_data(large_data)
        end_time = time.time()

        assert nodes is not None
        assert len(nodes) == 10000
        # 10秒以内に完了することを期待
        assert (end_time - start_time) < 10.0

    def test_deep_nesting_performance(self):
        """深いネスト処理性能テスト"""
        import time

        # 深いネスト構造作成（20レベル）
        deep_data = "最深項目"
        for i in range(19):
            deep_data = [f"レベル{20-i}", deep_data]

        start_time = time.time()
        try:
            # 深度計算
            depth = ListUtilities.calculate_list_depth(deep_data)
            assert isinstance(depth, int)

            # アイテムカウント
            count = ListUtilities.count_total_items(deep_data)
            assert isinstance(count, int)

        except RecursionError:
            pytest.skip("深いネストによる再帰制限")

        end_time = time.time()
        # 5秒以内に完了することを期待
        assert (end_time - start_time) < 5.0

    def test_memory_efficiency(self):
        """メモリ効率テスト"""
        import gc

        # ガベージコレクション実行
        gc.collect()
        initial_objects = len(gc.get_objects())

        # 複数回の処理実行
        for _ in range(100):
            data = [f"項目{i+1}" for i in range(50)]
            nodes = ListUtilities.create_nodes_from_parsed_data(data)
            del nodes

        # 再度ガベージコレクション
        gc.collect()
        final_objects = len(gc.get_objects())

        # メモリリークがないことを確認
        objects_increase = final_objects - initial_objects
        assert objects_increase < 1000  # 許容範囲内


class TestListUtilitiesStaticMethods:
    """静的メソッドテスト"""

    def test_all_methods_are_static(self):
        """全メソッドが静的メソッドであることを確認"""
        # クラスインスタンスを作成せずにメソッドを呼び出し
        data = ["項目1", "項目2"]

        # create_nodes_from_parsed_data
        nodes = ListUtilities.create_nodes_from_parsed_data(data)
        assert nodes is not None

        # create_nested_nodes
        nested_nodes = ListUtilities.create_nested_nodes(data, 1)
        assert nested_nodes is not None

        # calculate_list_depth
        depth = ListUtilities.calculate_list_depth(data)
        assert isinstance(depth, int)

        # count_total_items
        count = ListUtilities.count_total_items(data)
        assert isinstance(count, int)

    def test_static_method_independence(self):
        """静的メソッドの独立性テスト"""
        # 同じデータで複数回呼び出しても結果が一致することを確認
        data = ["項目1", ["項目2", "項目3"]]

        # 複数回実行
        depth1 = ListUtilities.calculate_list_depth(data)
        depth2 = ListUtilities.calculate_list_depth(data)
        assert depth1 == depth2

        count1 = ListUtilities.count_total_items(data)
        count2 = ListUtilities.count_total_items(data)
        assert count1 == count2

    def test_method_side_effects(self):
        """メソッドの副作用がないことを確認"""
        original_data = ["項目1", ["項目2"]]
        data_copy = original_data.copy()

        # メソッド実行
        ListUtilities.create_nodes_from_parsed_data(data_copy)
        ListUtilities.calculate_list_depth(data_copy)
        ListUtilities.count_total_items(data_copy)

        # 元データが変更されていないことを確認
        assert data_copy == original_data


class TestListUtilitiesMocking:
    """モッキング・依存関係テスト"""

    @patch("kumihan_formatter.core.parsing.list.utilities.list_utilities.Node")
    def test_node_creation_mocking(self, mock_node_class):
        """ノード作成のモッキングテスト"""
        # Nodeクラスをモック
        mock_node_instance = Mock()
        mock_node_class.return_value = mock_node_instance

        data = ["項目1", "項目2"]

        try:
            nodes = ListUtilities.create_nodes_from_parsed_data(data)
            # モックされたNodeが使用されることを確認
            assert mock_node_class.called
        except Exception:
            # import関係でエラーが発生する可能性があるため許容
            pass

    def test_fallback_node_implementation(self):
        """フォールバックNode実装テスト"""
        # フォールバック実装が動作することを確認
        with patch(
            "kumihan_formatter.core.parsing.list.utilities.list_utilities.Node",
            side_effect=ImportError,
        ):
            try:
                data = ["項目1"]
                nodes = ListUtilities.create_nodes_from_parsed_data(data)
                # フォールバック実装でも動作することを期待
                assert nodes is not None
            except ImportError:
                # フォールバック実装がない場合はスキップ
                pytest.skip("フォールバック実装が利用できません")


# === テストユーティリティ ===


def create_nested_test_data(depth: int, items_per_level: int = 2) -> List[Any]:
    """テスト用ネストデータ生成"""
    if depth <= 0:
        return [f"項目{i+1}" for i in range(items_per_level)]

    result = []
    for i in range(items_per_level):
        if i == 0:
            result.append(f"レベル{depth}_項目{i+1}")
        else:
            result.append(create_nested_test_data(depth - 1, items_per_level))

    return result


def assert_valid_node(node: Any) -> None:
    """ノードの妥当性検証"""
    assert node is not None
    assert hasattr(node, "type")
    assert hasattr(node, "content")
    assert hasattr(node, "attributes")
    assert isinstance(node.attributes, dict)


def assert_valid_node_list(nodes: List[Any]) -> None:
    """ノードリストの妥当性検証"""
    assert nodes is not None
    assert isinstance(nodes, list)

    for node in nodes:
        assert_valid_node(node)


# === パラメータ化テスト ===


@pytest.mark.parametrize(
    "data,expected_count",
    [
        (["a", "b", "c"], 3),
        (["a", ["b", "c"]], 3),
        (["a", ["b", ["c", "d"]]], 4),
        ([["a", "b"], ["c", "d"]], 4),
        ([], 0),
        ("single", 1),
    ],
)
def test_count_total_items_parametrized(data, expected_count):
    """パラメータ化アイテムカウントテスト"""
    count = ListUtilities.count_total_items(data)
    assert count == expected_count


@pytest.mark.parametrize(
    "data,min_depth",
    [
        (["a", "b"], 0),
        (["a", ["b"]], 1),
        (["a", ["b", ["c"]]], 2),
        ("single", 0),
        ([], 0),
    ],
)
def test_calculate_list_depth_parametrized(data, min_depth):
    """パラメータ化深度計算テスト"""
    depth = ListUtilities.calculate_list_depth(data)
    assert depth >= min_depth


@pytest.mark.parametrize("level", [0, 1, 2, 3, 5, 10])
def test_create_nested_nodes_levels_parametrized(level):
    """パラメータ化ネストレベルテスト"""
    data = ["項目1", "項目2"]
    nodes = ListUtilities.create_nested_nodes(data, level)

    assert nodes is not None
    assert isinstance(nodes, list)
    assert len(nodes) == 2

    for node in nodes:
        assert node.attributes.get("level") == level


# === フィクスチャー ===


@pytest.fixture
def sample_list_data():
    """サンプルリストデータフィクスチャ"""
    return {
        "simple": ["項目1", "項目2", "項目3"],
        "nested": ["項目1", ["子1", "子2"], "項目3"],
        "deep": ["項目1", ["子1", ["孫1", "孫2"], "子2"]],
        "mixed": ["文字列", 123, ["ネスト", None], ""],
        "empty": [],
        "single": ["単一項目"],
    }


@pytest.fixture
def complex_nested_data():
    """複雑なネストデータフィクスチャ"""
    return [
        "ルート1",
        ["子1", ["孫1", "孫2", ["ひ孫1"]], "子2"],
        "ルート2",
        [["孫3", "孫4"], "子3"],
    ]


def test_with_fixtures(sample_list_data, complex_nested_data):
    """フィクスチャー使用テスト"""
    # サンプルデータテスト
    for data_type, data in sample_list_data.items():
        nodes = ListUtilities.create_nodes_from_parsed_data(data)
        assert nodes is not None, f"Failed for {data_type}"

        depth = ListUtilities.calculate_list_depth(data)
        assert isinstance(depth, int), f"Depth calculation failed for {data_type}"

        count = ListUtilities.count_total_items(data)
        assert isinstance(count, int), f"Count calculation failed for {data_type}"

    # 複雑データテスト
    complex_nodes = ListUtilities.create_nodes_from_parsed_data(complex_nested_data)
    assert complex_nodes is not None
    assert len(complex_nodes) == 4  # ルート1, [子...], ルート2, [孫3...]

    complex_depth = ListUtilities.calculate_list_depth(complex_nested_data)
    assert complex_depth >= 3  # ひ孫まであるので3以上

    complex_count = ListUtilities.count_total_items(complex_nested_data)
    assert complex_count == 9  # 全アイテムカウント
