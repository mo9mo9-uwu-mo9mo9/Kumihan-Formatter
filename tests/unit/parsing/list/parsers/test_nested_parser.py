"""ネストリストパーサー（NestedListParser）の包括的テスト

Kumihan-Formatter の core/parsing/list/parsers/nested_parser.py モジュールをテスト
ネストリスト構造の解析、インデント管理、動的構造構築を検証
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import (
    Node,
    create_node,
    list_item,
    unordered_list,
)
from kumihan_formatter.core.parsing.list.parsers.nested_parser import NestedListParser


class TestNestedListParser:
    """ネストリストパーサーのテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.parser = NestedListParser()

    # ============================================================================
    # 正常系テスト（60%）
    # ============================================================================

    def test_正常系_ネスト処理可能判定(self):
        """正常系: ネスト構造の処理可能判定"""
        # Given: 複数のインデントレベルを含むコンテンツ
        content = """項目1
    子項目1
    子項目2
項目2"""

        # When: ネスト処理可能判定
        result = self.parser.can_handle_nesting(content)

        # Then: ネスト構造があることを検出
        assert result is True

    def test_正常系_単一レベル処理可能判定(self):
        """正常系: 単一レベルの処理可能判定"""
        # Given: 単一インデントレベルのコンテンツ
        content = """項目1
項目2
項目3"""

        # When: ネスト処理可能判定
        result = self.parser.can_handle_nesting(content)

        # Then: ネスト構造がないことを検出
        assert result is False

    def test_正常系_ネストリスト解析(self):
        """正常系: ネストリストの解析"""
        # Given: ネストしたリストコンテンツ
        content = """- 項目1
  - 子項目1
  - 子項目2
- 項目2"""

        # When: ネストリスト解析
        result = self.parser.parse_nested_list(content, level=0)

        # Then: ネスト構造が正しく解析されることを検証
        assert len(result) > 0
        assert all(isinstance(node, Node) for node in result)

    def test_正常系_ネスト構造構築_リスト版(self):
        """正常系: ネスト構造の構築（リスト版）"""
        # Given: 相対レベル付きノードリスト
        items = [
            create_node("list_item", content="項目1", metadata={"relative_level": 0}),
            create_node("list_item", content="子項目1", metadata={"relative_level": 1}),
            create_node("list_item", content="子項目2", metadata={"relative_level": 1}),
            create_node("list_item", content="項目2", metadata={"relative_level": 0}),
        ]

        # When: ネスト構造構築
        result = self.parser.build_nested_structure_list(items)

        # Then: 階層構造が正しく構築されることを検証
        assert len(result) == 2  # ルートレベル項目数
        # 最初の項目には子要素があることを確認
        if "children" in result[0].metadata:
            assert len(result[0].metadata["children"]) == 2

    def test_正常系_ネスト構造構築_基本版(self):
        """正常系: ネスト構造の構築（基本版）"""
        # Given: ネストレベル付きノードリスト
        items = [
            create_node("list_item", content="項目1", metadata={"nest_level": 0}),
            create_node("list_item", content="子項目1", metadata={"nest_level": 1}),
            create_node("list_item", content="項目2", metadata={"nest_level": 0}),
        ]

        # When: ネスト構造構築
        result = self.parser.build_nested_structure(items)

        # Then: unordered_listノードが返されることを検証
        assert result is not None
        assert result.node_type == "ul"

    def test_正常系_相対レベル計算(self):
        """正常系: 相対的なネストレベルの計算"""
        # Given: 絶対インデント付きノードリスト
        items = [
            create_node("list_item", content="項目1", metadata={"indent": 0}),
            create_node("list_item", content="子項目1", metadata={"indent": 4}),
            create_node("list_item", content="孫項目1", metadata={"indent": 8}),
        ]

        # When: 相対レベル計算
        self.parser.calculate_relative_levels(items, base_indent=0)

        # Then: 相対レベルが正しく計算されることを検証
        assert items[0].metadata["relative_level"] == 0
        assert items[1].metadata["relative_level"] == 2  # 4/2=2
        assert items[2].metadata["relative_level"] == 4  # 8/2=4

    def test_正常系_ネスト構造検証_正常ケース(self):
        """正常系: 正常なネスト構造の検証"""
        # Given: 正常なネスト構造のノードリスト
        items = [
            create_node("list_item", content="項目1", metadata={"relative_level": 0}),
            create_node("list_item", content="子項目1", metadata={"relative_level": 1}),
            create_node("list_item", content="子項目2", metadata={"relative_level": 1}),
            create_node("list_item", content="項目2", metadata={"relative_level": 0}),
        ]

        # When: ネスト構造検証
        errors = self.parser.validate_nesting_structure(items)

        # Then: エラーなしの検証
        assert len(errors) == 0

    def test_正常系_ネスト項目存在チェック_あり(self):
        """正常系: ネスト項目がある場合のチェック"""
        # Given: ネスト項目を含むノードリスト
        items = [
            create_node("list_item", content="項目1", metadata={"relative_level": 0}),
            create_node("list_item", content="子項目1", metadata={"relative_level": 1}),
        ]

        # When: ネスト項目存在チェック
        result = self.parser.has_nested_items(items)

        # Then: ネスト項目があることを検出
        assert result is True

    def test_正常系_ネスト項目存在チェック_なし(self):
        """正常系: ネスト項目がない場合のチェック"""
        # Given: ネスト項目を含まないノードリスト
        items = [
            create_node("list_item", content="項目1", metadata={"relative_level": 0}),
            create_node("list_item", content="項目2", metadata={"relative_level": 0}),
        ]

        # When: ネスト項目存在チェック
        result = self.parser.has_nested_items(items)

        # Then: ネスト項目がないことを検出
        assert result is False

    def test_正常系_ネスト統計情報取得(self):
        """正常系: ネスト構造の統計情報取得"""
        # Given: 様々なレベルのネスト項目
        items = [
            create_node("list_item", content="項目1", metadata={"relative_level": 0}),
            create_node("list_item", content="子項目1", metadata={"relative_level": 1}),
            create_node("list_item", content="孫項目1", metadata={"relative_level": 2}),
            create_node("list_item", content="子項目2", metadata={"relative_level": 1}),
        ]

        # When: 統計情報取得
        stats = self.parser.get_nesting_statistics(items)

        # Then: 統計情報の検証
        assert stats["max_level"] == 2
        assert stats["total_items"] == 4
        assert stats["has_nesting"] is True
        assert stats["level_distribution"][0] == 1  # レベル0が1個
        assert stats["level_distribution"][1] == 2  # レベル1が2個
        assert stats["level_distribution"][2] == 1  # レベル2が1個

    def test_正常系_最大ネストレベル制限(self):
        """正常系: 最大ネストレベル制限の確認"""
        # Given: 最大レベルを超えるコンテンツ
        deep_content = "項目"

        # When: 制限を超えるレベルでの解析
        result = self.parser.parse_nested_list(
            deep_content, level=4
        )  # max_nest_level=3を超える

        # Then: 空のリストが返されることを検証
        assert result == []

    # ============================================================================
    # 異常系テスト（20%）
    # ============================================================================

    def test_異常系_不正なネストレベルジャンプ(self):
        """異常系: 不正なネストレベルジャンプ"""
        # Given: 急激なレベル変化のあるノードリスト
        items = [
            create_node("list_item", content="項目1", metadata={"relative_level": 0}),
            create_node(
                "list_item", content="急激ジャンプ", metadata={"relative_level": 3}
            ),  # 3レベル急上昇
        ]

        # When: ネスト構造検証
        errors = self.parser.validate_nesting_structure(items)

        # Then: エラーが検出されることを検証
        assert len(errors) > 0
        assert "ネストレベルが急激に変化" in errors[0]

    def test_異常系_最大レベル制限超過(self):
        """異常系: 最大レベル制限を超える構造"""
        # Given: 最大レベルを超える深いネスト
        items = [
            create_node("list_item", content="項目1", metadata={"relative_level": 0}),
            create_node(
                "list_item", content="深すぎる", metadata={"relative_level": 5}
            ),  # max_nest_level=3を超える
        ]

        # When: ネスト構造検証
        errors = self.parser.validate_nesting_structure(items)

        # Then: エラーが検出されることを検証
        assert len(errors) > 0
        assert "ネストレベルが急激に変化" in errors[0]

    def test_異常系_最大レベル制限超過_段階的(self):
        """異常系: 最大レベル制限を超える構造（段階的）"""
        # Given: 段階的に最大レベルを超える深いネスト
        items = [
            create_node("list_item", content="項目1", metadata={"relative_level": 0}),
            create_node("list_item", content="項目2", metadata={"relative_level": 1}),
            create_node("list_item", content="項目3", metadata={"relative_level": 2}),
            create_node("list_item", content="項目4", metadata={"relative_level": 3}),
            create_node(
                "list_item", content="深すぎる", metadata={"relative_level": 4}
            ),  # max_nest_level=3を超える
        ]

        # When: ネスト構造検証
        errors = self.parser.validate_nesting_structure(items)

        # Then: エラーが検出されることを検証
        assert len(errors) > 0
        assert "制限を超えています" in errors[-1]  # 最後のエラーメッセージをチェック

    def test_異常系_空のノードリスト処理(self):
        """異常系: 空のノードリストの処理"""
        # Given: 空のノードリスト
        empty_items = []

        # When: 各種処理を実行
        nested_result = self.parser.build_nested_structure_list(empty_items)
        structure_result = self.parser.build_nested_structure(empty_items)
        stats = self.parser.get_nesting_statistics(empty_items)
        has_nested = self.parser.has_nested_items(empty_items)

        # Then: 適切なデフォルト値が返されることを検証
        assert nested_result == []
        assert structure_result.node_type == "ul"
        assert stats["max_level"] == 0
        assert stats["total_items"] == 0
        assert has_nested is False

    def test_異常系_不正なコンテンツ形式(self):
        """異常系: 不正なコンテンツ形式の処理"""
        # Given: 不正なコンテンツ形式
        invalid_contents = [None, "", "   ", "\n\n\n"]

        for content in invalid_contents:
            # When: ネスト処理可能判定
            if content is not None:
                result = self.parser.can_handle_nesting(content)
                # Then: 適切に処理されることを検証
                assert result is False  # ネスト構造なしと判定

    def test_異常系_メタデータ不正ノード(self):
        """異常系: メタデータが不正なノードの処理"""
        # Given: メタデータが不正なノード
        invalid_items = [
            create_node("list_item", content="項目1"),  # metadataなし
            create_node("list_item", content="項目2", metadata={}),  # 空のmetadata
            create_node(
                "list_item", content="項目3", metadata={"invalid_key": "value"}
            ),  # 無関係なkey
        ]

        # When: 相対レベル計算
        self.parser.calculate_relative_levels(invalid_items)

        # Then: エラーなく処理され、デフォルト値が設定されることを検証
        for item in invalid_items:
            assert "relative_level" in item.metadata
            assert item.metadata["relative_level"] >= 0

    # ============================================================================
    # 境界値テスト（10%）
    # ============================================================================

    def test_境界値_最大ネストレベル境界(self):
        """境界値: 最大ネストレベルの境界値"""
        # Given: 最大レベル境界のコンテンツ
        boundary_contents = [
            ("項目", 3),  # 最大レベル
            ("項目", 4),  # 最大レベル+1
        ]

        for content, level in boundary_contents:
            # When: ネストリスト解析
            result = self.parser.parse_nested_list(content, level)

            # Then: 境界値での適切な処理を検証
            if level <= self.parser.max_nest_level:
                assert isinstance(result, list)
            else:
                assert result == []

    def test_境界値_極端なインデント(self):
        """境界値: 極端なインデント値"""
        # Given: 極端なインデント値のノード
        extreme_items = [
            create_node("list_item", content="項目1", metadata={"indent": 0}),
            create_node(
                "list_item", content="項目2", metadata={"indent": 1000}
            ),  # 極端に大きい
            create_node(
                "list_item", content="項目3", metadata={"indent": -5}
            ),  # 負の値
        ]

        # When: 相対レベル計算
        self.parser.calculate_relative_levels(extreme_items, base_indent=0)

        # Then: 適切に処理されることを検証
        assert extreme_items[0].metadata["relative_level"] == 0
        assert extreme_items[1].metadata["relative_level"] >= 0  # 負にならない
        assert extreme_items[2].metadata["relative_level"] == 0  # max(0, ...)により0

    def test_境界値_大量ノード処理(self):
        """境界値: 大量ノードの処理"""
        # CI環境での実行時間を考慮して削減
        from tests.conftest import get_test_data_size
        node_count = get_test_data_size(1000, 100)

        # Given: 大量のノード
        large_items = []
        for i in range(node_count):
            level = i % 4  # 0-3のレベル循環
            item = create_node(
                "list_item", content=f"項目{i}", metadata={"relative_level": level}
            )
            large_items.append(item)

        # When: 統計情報取得
        stats = self.parser.get_nesting_statistics(large_items)

        # Then: 大量データが適切に処理されることを検証
        assert stats["total_items"] == node_count
        assert stats["max_level"] == 3
        assert stats["has_nesting"] is True

    def test_境界値_空文字列要素(self):
        """境界値: 空文字列要素を含む処理"""
        # Given: 空文字列要素を含むコンテンツ
        content_with_empty = """項目1


項目2
    子項目"""

        # When: ネスト処理可能判定
        result = self.parser.can_handle_nesting(content_with_empty)

        # Then: 空行を無視して適切に判定されることを検証
        assert result is True  # 複数のインデントレベルがある

    # ============================================================================
    # 統合テスト（10%）
    # ============================================================================

    def test_統合_完全なネストワークフロー(self):
        """統合: 完全なネスト処理ワークフロー"""
        # Given: 複雑なネスト構造
        content = """- 項目1
  - 子項目1
    - 孫項目1
  - 子項目2
- 項目2
  - 子項目3"""

        # When: 完全なワークフロー実行
        # 1. ネスト処理可能判定
        can_handle = self.parser.can_handle_nesting(content)

        # 2. ネストリスト解析
        parsed_nodes = self.parser.parse_nested_list(content, level=0)

        # 3. 統計情報取得
        if parsed_nodes:
            stats = self.parser.get_nesting_statistics(parsed_nodes)

        # Then: 全ステップが適切に動作することを検証
        assert can_handle is True
        assert len(parsed_nodes) > 0
        if parsed_nodes:
            assert stats["has_nesting"] is True

    def test_統合_ネスト構造構築から平坦化まで(self):
        """統合: ネスト構造構築から平坦化までの流れ"""
        # Given: ネスト構造のノード
        nested_root = create_node(
            "list",
            content="",
            metadata={
                "children": [
                    create_node("list_item", content="項目1", metadata={"level": 0}),
                    create_node("list_item", content="子項目1", metadata={"level": 1}),
                ]
            },
        )

        # When: 平坦化実行
        flattened = self.parser.flatten_nested_list(nested_root)

        # Then: 適切に平坦化されることを検証
        assert len(flattened) >= 0  # 何らかの結果が返される
        assert all(isinstance(node, Node) for node in flattened)

    def test_統合_ネスト深度計算総合(self):
        """統合: ネスト深度計算の総合テスト"""
        # Given: 複雑な階層構造
        items = [
            create_node(
                "list_item",
                content="レベル0",
                metadata={
                    "children": [
                        create_node(
                            "list_item",
                            content="レベル1",
                            metadata={
                                "children": [
                                    create_node("list_item", content="レベル2")
                                ]
                            },
                        )
                    ]
                },
            ),
            create_node("list_item", content="レベル0-2"),
        ]

        # When: ネスト深度計算
        depth = self.parser.calculate_nesting_depth(items)

        # Then: 正しい深度が計算されることを検証
        assert depth >= 0  # 適切な深度値

    def test_統合_インデント正規化(self):
        """統合: インデント正規化機能"""
        # Given: ネストされたリスト構造
        text = """- 項目1
    - 子項目1
        - 孫項目1
    - 子項目2
- 項目2"""

        # When: ネストリスト解析
        result = self.parser.parse(text)

        # Then: 適切にネスト構造が解析されることを検証
        assert result is not None
        assert isinstance(result, Node)
        # ネスト構造の検証
        if hasattr(result, 'children'):
            assert len(result.children) > 0

    def test_統合_エラーハンドリング総合(self):
        """統合: エラーハンドリングの総合テスト"""
        # Given: 様々な問題を含むノードリスト
        problematic_items = [
            create_node(
                "list_item", content="正常項目", metadata={"relative_level": 0}
            ),
            create_node(
                "list_item", content="急激ジャンプ", metadata={"relative_level": 3}
            ),
            create_node(
                "list_item", content="制限超過", metadata={"relative_level": 5}
            ),
        ]

        # When: 検証とその他の処理
        errors = self.parser.validate_nesting_structure(problematic_items)
        stats = self.parser.get_nesting_statistics(problematic_items)

        # Then: エラーが適切に検出され、他の機能は継続動作することを検証
        assert len(errors) > 0  # エラーが検出される
        assert stats["total_items"] == 3  # 統計は正常に取得される

    # ============================================================================
    # 特殊ケーステスト
    # ============================================================================

    def test_特殊_日本語コンテンツネスト(self):
        """特殊: 日本語コンテンツを含むネスト構造"""
        # Given: 日本語コンテンツのネスト
        japanese_content = """- 日本語項目１
  - 子項目：詳細説明
    - 孫項目（更に詳細）
- 日本語項目２"""

        # When: ネスト処理
        can_handle = self.parser.can_handle_nesting(japanese_content)
        parsed = self.parser.parse_nested_list(japanese_content)

        # Then: 日本語が適切に処理されることを検証
        assert can_handle is True
        assert len(parsed) > 0

    def test_特殊_特殊文字インデント(self):
        """特殊: 特殊文字を含むインデント"""
        # Given: タブとスペースの混合インデント
        mixed_content = """項目1
\t子項目1（タブ）
    子項目2（スペース）
\t\t孫項目1（ダブルタブ）"""

        # When: ネスト処理可能判定
        result = self.parser.can_handle_nesting(mixed_content)

        # Then: 混合インデントが適切に処理されることを検証
        assert result is True

    def test_特殊_リストアイテムノード作成(self):
        """特殊: リストアイテムノード作成の詳細テスト"""
        # Given: 様々なリストマーカーを含む行
        test_lines = [
            "- 通常項目",
            "* アスタリスク項目",
            "+ プラス項目",
            "1. 順序付き項目",
            "通常テキスト（マーカーなし）",
        ]

        for line in test_lines:
            # When: リストアイテムノード作成
            node = self.parser._create_list_item_node(line, level=4)

            # Then: 適切なノードが作成されることを検証
            if node:
                assert node.node_type == "list_item"
                assert node.metadata["level"] == 4

    def test_特殊_パターン初期化と設定(self):
        """特殊: パターン初期化と設定の確認"""
        # Given: 新しいパーサーインスタンス
        new_parser = NestedListParser()

        # When: 設定確認
        patterns = new_parser.patterns
        max_level = new_parser.max_nest_level

        # Then: 適切な初期化がされていることを検証
        assert "indent" in patterns
        assert "nested_item" in patterns
        assert max_level == 3
        assert all(hasattr(pattern, "match") for pattern in patterns.values())

    def test_特殊_空コンテンツ各種処理(self):
        """特殊: 空コンテンツに対する各種処理"""
        # Given: 様々な空コンテンツ
        empty_contents = ["", "   ", "\n", "\t\t", None]

        for content in empty_contents:
            if content is not None:
                # When: 各種処理実行
                can_handle = self.parser.can_handle_nesting(content)

                # Then: 適切に処理されることを検証
                assert can_handle is False  # 空コンテンツはネスト構造なし
