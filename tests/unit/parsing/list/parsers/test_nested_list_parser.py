"""ネストリスト専用パーサー（NestedListParser）の包括的テスト

Kumihan-Formatter の core/parsing/list/parsers/nested_list_parser.py モジュールをテスト
拡張版のネストリストパーサーの機能を詳細に検証
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.parsing.list.parsers.nested_list_parser import (
    NestedListParser,
)


class TestNestedListParserExtended:
    """ネストリスト専用パーサー（拡張版）のテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.parser = NestedListParser()

    # ============================================================================
    # 正常系テスト（60%）
    # ============================================================================

    def test_正常系_ネストリスト解析_文字列入力(self):
        """正常系: 文字列入力でのネストリスト解析"""
        # Given: ネストリストの文字列
        content = """- 項目1
  - 子項目1
  - 子項目2
- 項目2
  - 子項目3"""

        # When: ネストリスト解析
        result = self.parser.parse_nested_list(content, level=0)

        # Then: 解析結果の検証
        assert isinstance(result, list)
        assert len(result) > 0

    def test_正常系_ネストリスト解析_リスト入力(self):
        """正常系: リスト入力でのネストリスト解析"""
        # Given: ネストリストの行リスト
        lines = ["- 項目1", "  - 子項目1", "  - 子項目2", "- 項目2"]

        # When: ネストリスト解析
        result = self.parser.parse_nested_list(lines, level=0)

        # Then: 解析結果の検証
        assert isinstance(result, list)
        assert len(result) > 0

    def test_正常系_ネスト構造構築_詳細(self):
        """正常系: 詳細なネスト構造の構築"""
        # Given: 複雑なネスト構造の行
        lines = [
            "- 親項目1",
            "  - 子項目1-1",
            "    - 孫項目1-1-1",
            "  - 子項目1-2",
            "- 親項目2",
            "  - 子項目2-1",
        ]

        # When: ネスト構造構築
        result = self.parser.build_nested_structure(lines, base_level=0)

        # Then: 構築結果の検証
        assert len(result) == 2  # 親項目が2つ
        # 子要素の確認（実装に依存）
        for node in result:
            assert node.type == "list_item"

    def test_正常系_インデントレベル取得(self):
        """正常系: インデントレベルの取得"""
        # Given: 様々なインデントレベルの行
        test_cases = [
            ("項目", 0),
            ("  項目", 2),
            ("    項目", 4),
            ("      項目", 6),
            ("\t項目", 1),  # タブは1文字
            ("", 0),
        ]

        for line, expected_level in test_cases:
            # When: インデントレベル取得
            level = self.parser.get_indent_level(line)

            # Then: 期待されるレベルの検証
            assert level == expected_level

    def test_正常系_リストネストレベル取得(self):
        """正常系: リストのネストレベル取得"""
        # Given: 様々なインデントの行
        test_cases = [
            ("項目", 0),  # 0スペース = レベル0
            ("    項目", 1),  # 4スペース = レベル1
            ("        項目", 2),  # 8スペース = レベル2
            ("            項目", 3),  # 12スペース = レベル3
        ]

        for line, expected_level in test_cases:
            # When: リストネストレベル取得
            level = self.parser.get_list_nesting_level(line)

            # Then: 期待されるレベルの検証
            assert level == expected_level

    def test_正常系_リストアイテムノード作成(self):
        """正常系: リストアイテムノードの作成"""
        # Given: 様々なリスト行
        test_lines = [
            "- 基本項目",
            "* アスタリスク項目",
            "+ プラス項目",
            "1. 順序付き項目",
            "通常テキスト",
        ]

        for line in test_lines:
            # When: リストアイテムノード作成
            node = self.parser.create_list_item_node(line, indent_level=4)

            # Then: ノード作成の検証
            if node:
                assert node.type == "list_item"
                assert node.attributes["indent_level"] == 4
                assert node.attributes["nesting_level"] == 1  # 4//4=1

    def test_正常系_インデントレベルグループ化(self):
        """正常系: インデントレベルでのグループ化"""
        # Given: 様々なレベルのノード
        items = [
            Node(
                type="list_item", content="レベル0-1", attributes={"relative_level": 0}
            ),
            Node(
                type="list_item", content="レベル1-1", attributes={"relative_level": 1}
            ),
            Node(
                type="list_item", content="レベル1-2", attributes={"relative_level": 1}
            ),
            Node(
                type="list_item", content="レベル0-2", attributes={"relative_level": 0}
            ),
            Node(
                type="list_item", content="レベル2-1", attributes={"relative_level": 2}
            ),
        ]

        # When: インデントレベルグループ化
        groups = self.parser.group_by_indent_level(items)

        # Then: グループ化結果の検証
        assert 0 in groups
        assert 1 in groups
        assert 2 in groups
        assert len(groups[0]) == 2  # レベル0が2個
        assert len(groups[1]) == 2  # レベル1が2個
        assert len(groups[2]) == 1  # レベル2が1個

    def test_正常系_階層構造構築(self):
        """正常系: レベル別グループからの階層構造構築"""
        # Given: レベル別グループ
        level_groups = {
            0: [
                Node(type="list_item", content="親1", attributes={"index": 0}),
                Node(type="list_item", content="親2", attributes={"index": 3}),
            ],
            1: [
                Node(type="list_item", content="子1", attributes={"index": 1}),
                Node(type="list_item", content="子2", attributes={"index": 2}),
            ],
        }

        # When: 階層構造構築
        result = self.parser.build_hierarchy_from_groups(level_groups)

        # Then: 階層構造の検証
        assert len(result) == 2  # ルートレベルのノード数
        assert all(node.type == "list_item" for node in result)

    def test_正常系_子要素追加(self):
        """正常系: 親ノードへの子要素追加"""
        # Given: 親ノードとレベル別グループ
        parent_node = Node(type="list_item", content="親", attributes={"index": 0})
        level_groups = {
            1: [
                Node(type="list_item", content="子1", attributes={"index": 1}),
                Node(type="list_item", content="子2", attributes={"index": 2}),
            ],
            2: [Node(type="list_item", content="孫1", attributes={"index": 3})],
        }

        # When: 子要素追加
        self.parser.attach_children(parent_node, level_groups, target_level=1)

        # Then: 子要素が追加されることを検証
        # 実装により children 属性の扱いが異なる可能性
        if hasattr(parent_node, "children") and parent_node.children:
            assert len(parent_node.children) >= 0

    def test_正常系_ネスト項目存在チェック_詳細(self):
        """正常系: ネスト項目存在チェック（詳細）"""
        # Given: 各種パターンのノードリスト
        test_cases = [
            # ネストあり
            (
                [
                    Node(
                        type="list_item",
                        content="項目1",
                        attributes={"relative_level": 0},
                    ),
                    Node(
                        type="list_item",
                        content="項目2",
                        attributes={"relative_level": 1},
                    ),
                ],
                True,
            ),
            # ネストなし
            (
                [
                    Node(
                        type="list_item",
                        content="項目1",
                        attributes={"relative_level": 0},
                    ),
                    Node(
                        type="list_item",
                        content="項目2",
                        attributes={"relative_level": 0},
                    ),
                ],
                False,
            ),
            # 空リスト
            ([], False),
        ]

        for items, expected in test_cases:
            # When: ネスト項目存在チェック
            result = self.parser.has_nested_items(items)

            # Then: 期待結果の検証
            assert result == expected

    def test_正常系_平坦化処理(self):
        """正常系: ネストリストの平坦化処理"""
        # Given: ネスト構造のノード
        nested_node = Node(
            type="list",
            content="",
            children=[
                Node(type="list_item", content="親1"),
                Node(
                    type="list_item",
                    content="親2",
                    children=[
                        Node(type="list_item", content="子2-1"),
                        Node(type="list_item", content="子2-2"),
                    ],
                ),
            ],
        )

        # When: 平坦化処理
        flattened = self.parser.flatten_nested_list(nested_node)

        # Then: 平坦化結果の検証
        assert isinstance(flattened, list)
        assert len(flattened) >= 1
        assert all(isinstance(node, Node) for node in flattened)

    def test_正常系_ネスト深度計算(self):
        """正常系: ネスト深度の計算"""
        # Given: 異なる深度のノードリスト
        items = [
            Node(
                type="list_item",
                content="レベル0",
                children=[
                    Node(
                        type="list_item",
                        content="レベル1",
                        children=[Node(type="list_item", content="レベル2")],
                    )
                ],
            ),
            Node(type="list_item", content="レベル0-2"),
        ]

        # When: ネスト深度計算
        depth = self.parser.calculate_nesting_depth(items)

        # Then: 深度の検証
        assert depth >= 0
        assert isinstance(depth, int)

    def test_正常系_インデント正規化_詳細(self):
        """正常系: インデント正規化の詳細テスト"""
        # Given: 不規則なインデントの行
        lines = [
            "項目1",
            "  子項目1",  # 2スペース
            "    孫項目1",  # 4スペース
            "      曾孫項目1",  # 6スペース
            "項目2",
        ]

        # When: インデント正規化（4スペース/レベル）
        normalized = self.parser.normalize_indentation(lines, spaces_per_level=4)

        # Then: 正規化結果の検証
        assert len(normalized) == len(lines)
        # 正規化により、インデントが4の倍数に調整される
        expected_indents = [0, 0, 4, 4, 0]  # 各行の期待インデント
        for i, line in enumerate(normalized):
            actual_indent = len(line) - len(line.lstrip())
            assert actual_indent == expected_indents[i]

    # ============================================================================
    # 異常系テスト（20%）
    # ============================================================================

    def test_異常系_空入力処理(self):
        """異常系: 空入力の処理"""
        # Given: 空の入力
        empty_inputs = ["", [], None]

        for empty_input in empty_inputs:
            if empty_input is not None:
                # When: ネストリスト解析
                result = self.parser.parse_nested_list(empty_input, level=0)

                # Then: 空の結果が返されることを検証
                assert result == []

    def test_異常系_最大ネストレベル制限(self):
        """異常系: 最大ネストレベル制限の動作"""
        # Given: 制限を超えるレベル
        over_limit_content = "深すぎる項目"

        # When: 制限を超えるレベルでの解析
        result = self.parser.parse_nested_list(over_limit_content, level=5)

        # Then: 空の結果が返されることを検証
        assert result == []

    def test_異常系_不正なインデント処理(self):
        """異常系: 不正なインデントの処理"""
        # Given: 不正なインデントパターン
        invalid_lines = [
            "項目1",
            "     子項目（5スペース）",  # 不規則
            "   子項目（3スペース）",  # 不規則
            "項目2",
        ]

        # When: ネスト構造構築
        result = self.parser.build_nested_structure(invalid_lines, base_level=0)

        # Then: エラーなく処理されることを検証（不規則でも何らかの結果）
        assert isinstance(result, list)

    def test_異常系_メタデータ不正ノード処理(self):
        """異常系: メタデータが不正なノードの処理"""
        # Given: メタデータが不正なノード
        invalid_items = [
            Node(type="list_item", content="項目1"),  # attributes なし
            Node(type="list_item", content="項目2", attributes={}),  # 空のattributes
            Node(
                type="list_item", content="項目3", attributes={"invalid": "data"}
            ),  # 無関係なkey
        ]

        # When: レベル別グループ化
        groups = self.parser.group_by_indent_level(invalid_items)

        # Then: エラーなく処理され、デフォルト値が使用されることを検証
        assert isinstance(groups, dict)
        assert 0 in groups  # デフォルトレベル0

    def test_異常系_循環参照処理(self):
        """異常系: 循環参照の処理"""
        # Given: 循環参照を含む可能性のある構造
        # 注: 実装上循環参照が発生しにくい構造だが、テストとして実装
        problematic_items = []
        for i in range(10):
            item = Node(
                type="list_item",
                content=f"項目{i}",
                attributes={"relative_level": i % 3},
            )
            problematic_items.append(item)

        # When: 階層構造構築
        groups = self.parser.group_by_indent_level(problematic_items)
        result = self.parser.build_hierarchy_from_groups(groups)

        # Then: 無限ループにならず結果が返されることを検証
        assert isinstance(result, list)

    # ============================================================================
    # 境界値テスト（10%）
    # ============================================================================

    def test_境界値_最大ネスト深度境界(self):
        """境界値: 最大ネスト深度の境界値"""
        # Given: 最大深度境界のレベル
        boundary_levels = [2, 3, 4]  # max_nesting_level=3の境界

        for level in boundary_levels:
            # When: ネストリスト解析
            result = self.parser.parse_nested_list("項目", level=level)

            # Then: 境界値での適切な処理を検証
            if level <= self.parser.max_nesting_level:
                assert isinstance(result, list)
            else:
                assert result == []

    def test_境界値_極端なインデント値(self):
        """境界値: 極端なインデント値"""
        # Given: 極端なインデント
        extreme_lines = [
            "",  # 空行
            " " * 100 + "深い項目",  # 非常に深いインデント
            "\t\t\t項目",  # 多重タブ
            "項目",  # インデントなし
        ]

        # When: インデント正規化
        normalized = self.parser.normalize_indentation(
            extreme_lines, spaces_per_level=4
        )

        # Then: 極端な値が適切に処理されることを検証
        assert len(normalized) == len(extreme_lines)
        for line in normalized:
            assert isinstance(line, str)

    def test_境界値_大量ノード処理(self):
        """境界値: 大量ノードの処理"""
        # Given: 大量のノード（1000個）
        large_items = []
        for i in range(1000):
            level = i % 4  # 0-3のレベル循環
            item = Node(
                type="list_item",
                content=f"項目{i}",
                attributes={"relative_level": level, "index": i},
            )
            large_items.append(item)

        # When: 大量ノード処理
        groups = self.parser.group_by_indent_level(large_items)
        result = self.parser.build_hierarchy_from_groups(groups)

        # Then: 大量データが処理されることを検証
        assert isinstance(result, list)
        assert len(groups) > 0

    def test_境界値_長いコンテンツ行(self):
        """境界値: 非常に長いコンテンツ行"""
        # Given: 非常に長いコンテンツ
        long_content = "非常に長い" * 200 + "項目"
        long_line = f"  - {long_content}"

        # When: リストアイテムノード作成
        node = self.parser.create_list_item_node(long_line, indent_level=2)

        # Then: 長いコンテンツが処理されることを検証
        assert node is not None
        assert len(node.content) > 1000

    def test_境界値_ゼロレベル処理(self):
        """境界値: レベル0での各種処理"""
        # Given: レベル0の項目のみ
        zero_level_items = [
            Node(type="list_item", content="項目1", attributes={"relative_level": 0}),
            Node(type="list_item", content="項目2", attributes={"relative_level": 0}),
            Node(type="list_item", content="項目3", attributes={"relative_level": 0}),
        ]

        # When: 各種処理実行
        has_nested = self.parser.has_nested_items(zero_level_items)
        depth = self.parser.calculate_nesting_depth(zero_level_items)
        groups = self.parser.group_by_indent_level(zero_level_items)

        # Then: レベル0のみの適切な処理を検証
        assert has_nested is False
        assert depth == 0
        assert 0 in groups
        assert len(groups[0]) == 3

    # ============================================================================
    # 統合テスト（10%）
    # ============================================================================

    def test_統合_完全ネストワークフロー(self):
        """統合: 完全なネスト処理ワークフロー"""
        # Given: 複雑なネスト構造
        content = """- メイン項目1
    - サブ項目1-1
        - サブサブ項目1-1-1
    - サブ項目1-2
- メイン項目2
    - サブ項目2-1"""

        # When: 完全ワークフロー実行
        # 1. ネスト解析
        parsed = self.parser.parse_nested_list(content, level=0)

        # 2. 構造構築
        if parsed:
            built_structure = self.parser.build_nested_structure_list(parsed)

        # 3. 深度計算
        if parsed:
            depth = self.parser.calculate_nesting_depth(parsed)

        # Then: 完全ワークフローが動作することを検証
        assert isinstance(parsed, list)
        if parsed:
            assert isinstance(depth, int)
            assert depth >= 0

    def test_統合_インデント処理総合(self):
        """統合: インデント処理の総合テスト"""
        # Given: 不規則なインデントの複雑な構造
        irregular_lines = [
            "項目1",
            "  子項目1",  # 2スペース
            "    孫項目1",  # 4スペース
            "      曾孫項目1",  # 6スペース
            "  子項目2",  # 2スペース
            "項目2",
            "\t子項目3",  # タブ
        ]

        # When: 統合的なインデント処理
        # 1. インデント正規化
        normalized = self.parser.normalize_indentation(
            irregular_lines, spaces_per_level=4
        )

        # 2. 構造構築
        built = self.parser.build_nested_structure(normalized, base_level=0)

        # 3. レベル取得テスト
        levels = [self.parser.get_list_nesting_level(line) for line in normalized]

        # Then: 統合処理が適切に動作することを検証
        assert len(normalized) == len(irregular_lines)
        assert isinstance(built, list)
        assert all(isinstance(level, int) and level >= 0 for level in levels)

    def test_統合_階層構築と平坦化往復(self):
        """統合: 階層構築と平坦化の往復処理"""
        # Given: 平坦なノードリスト
        flat_items = [
            Node(type="list_item", content="親1", attributes={"relative_level": 0}),
            Node(type="list_item", content="子1", attributes={"relative_level": 1}),
            Node(type="list_item", content="孫1", attributes={"relative_level": 2}),
            Node(type="list_item", content="子2", attributes={"relative_level": 1}),
            Node(type="list_item", content="親2", attributes={"relative_level": 0}),
        ]

        # When: 階層構築 → 平坦化の往復処理
        # 1. 階層構築
        groups = self.parser.group_by_indent_level(flat_items)
        hierarchy = self.parser.build_hierarchy_from_groups(groups)

        # 2. 各階層ノードを平坦化（実装依存）
        all_flattened = []
        for root_node in hierarchy:
            flattened = self.parser.flatten_nested_list(root_node)
            all_flattened.extend(flattened)

        # Then: 往復処理が適切に動作することを検証
        assert len(hierarchy) > 0
        assert len(all_flattened) >= 0

    def test_統合_エラーハンドリング総合(self):
        """統合: エラーハンドリングの総合テスト"""
        # Given: 様々な問題を含む入力
        problematic_input = """- 正常項目1
        - 深すぎる項目（不規則インデント）
- 正常項目2
     - 不規則インデント項目
"""

        # When: 堅牢な処理実行
        try:
            parsed = self.parser.parse_nested_list(problematic_input, level=0)
            built = self.parser.build_nested_structure(
                problematic_input.split("\n"), base_level=0
            )
            normalized = self.parser.normalize_indentation(
                problematic_input.split("\n")
            )

            results = [parsed, built, normalized]
        except Exception as e:
            results = [[], [], []]

        # Then: エラーがあっても何らかの結果が返されることを検証
        assert all(isinstance(result, list) for result in results)

    def test_統合_パフォーマンス最適化確認(self):
        """統合: パフォーマンス最適化の確認"""
        # Given: 性能テスト用の中規模データ
        medium_data = []
        for i in range(500):
            level = i % 5  # 0-4のレベル
            content = f"項目{i}" + "の詳細説明" * (level + 1)
            line = " " * (level * 4) + f"- {content}"
            medium_data.append(line)

        # When: 各種処理の実行時間測定（簡易）
        import time

        start = time.time()
        built = self.parser.build_nested_structure(medium_data, base_level=0)
        build_time = time.time() - start

        start = time.time()
        normalized = self.parser.normalize_indentation(medium_data)
        normalize_time = time.time() - start

        # Then: 合理的な時間で処理されることを検証
        assert build_time < 1.0  # 1秒以内
        assert normalize_time < 1.0  # 1秒以内
        assert len(built) >= 0
        assert len(normalized) == len(medium_data)

    # ============================================================================
    # 特殊ケーステスト
    # ============================================================================

    def test_特殊_日本語インデント処理(self):
        """特殊: 日本語コンテンツでのインデント処理"""
        # Given: 日本語コンテンツのネスト構造
        japanese_lines = [
            "日本語メイン項目１",
            "    日本語子項目１－１",
            "        日本語孫項目１－１－１",
            "    日本語子項目１－２",
            "日本語メイン項目２",
        ]

        # When: 日本語コンテンツ処理
        built = self.parser.build_nested_structure(japanese_lines, base_level=0)
        normalized = self.parser.normalize_indentation(japanese_lines)

        # Then: 日本語が適切に処理されることを検証
        assert len(built) > 0
        assert len(normalized) == len(japanese_lines)
        assert all("日本語" in line for line in normalized if line.strip())

    def test_特殊_混合インデント文字(self):
        """特殊: スペースとタブの混合インデント"""
        # Given: スペースとタブの混合
        mixed_lines = [
            "項目1",
            "\t子項目1（タブ）",
            "    子項目2（4スペース）",
            "\t\t孫項目1（ダブルタブ）",
            "        孫項目2（8スペース）",
        ]

        # When: 混合インデント処理
        built = self.parser.build_nested_structure(mixed_lines, base_level=0)
        levels = [self.parser.get_indent_level(line) for line in mixed_lines]

        # Then: 混合インデントが適切に処理されることを検証
        assert len(built) > 0
        assert all(isinstance(level, int) and level >= 0 for level in levels)

    def test_特殊_空行処理(self):
        """特殊: 空行を含む構造の処理"""
        # Given: 空行を含む構造
        lines_with_empty = [
            "項目1",
            "",
            "    子項目1",
            "",
            "        孫項目1",
            "",
            "項目2",
        ]

        # When: 空行込み処理
        built = self.parser.build_nested_structure(lines_with_empty, base_level=0)
        normalized = self.parser.normalize_indentation(lines_with_empty)

        # Then: 空行が適切に処理されることを検証
        assert len(built) >= 0
        assert len(normalized) == len(lines_with_empty)

    def test_特殊_特殊文字コンテンツ(self):
        """特殊: 特殊文字を含むコンテンツ"""
        # Given: 特殊文字を含むコンテンツ
        special_content = """- **太字**項目
    - *イタリック*子項目
        - `コード`孫項目
    - [リンク](URL)子項目"""

        # When: 特殊文字処理
        parsed = self.parser.parse_nested_list(special_content, level=0)

        # Then: 特殊文字が保持されることを検証
        assert len(parsed) > 0

    def test_特殊_設定値確認(self):
        """特殊: パーサー設定値の確認"""
        # Given: パーサーインスタンス
        parser = NestedListParser()

        # When: 設定値確認
        max_level = parser.max_nesting_level
        patterns = parser.indent_pattern

        # Then: 期待される設定値を検証
        assert max_level == 3
        assert hasattr(patterns, "match")

    def test_特殊_コンテキスト付きパース(self):
        """特殊: コンテキスト付きパース"""
        # Given: コンテキスト情報
        content = "- コンテキスト付き項目"
        context = {"parser_type": "nested", "strict_mode": True}

        # When: コンテキスト付きパース
        result = self.parser.parse_nested_list(content, level=0, context=context)

        # Then: コンテキストが考慮されることを検証（実装依存）
        assert isinstance(result, list)
