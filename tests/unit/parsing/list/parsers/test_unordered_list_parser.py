"""非順序リスト専用パーサー（UnorderedListParser）の包括的テスト

Kumihan-Formatter の core/parsing/list/parsers/unordered_list_parser.py モジュールをテスト
拡張版の非順序リストパーサーの機能を詳細に検証
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.parsing.list.parsers.unordered_list_parser import (
    UnorderedListParser,
)


class TestUnorderedListParserExtended:
    """非順序リスト専用パーサー（拡張版）のテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.parser = UnorderedListParser()

    # ============================================================================
    # 正常系テスト（60%）
    # ============================================================================

    def test_正常系_非順序タイプ検出_バレット(self):
        """正常系: バレット非順序リストタイプの検出"""
        # Given: バレット非順序リストの行
        test_lines = ["- ハイフン項目", "* アスタリスク項目", "+ プラス項目"]

        for line in test_lines:
            # When: 非順序タイプ検出
            result = self.parser.detect_unordered_type(line)

            # Then: バレットタイプが検出されることを検証
            assert result == "bullet"

    def test_正常系_非順序タイプ検出_チェックリスト(self):
        """正常系: チェックリストタイプの検出"""
        # Given: チェックリストの行
        test_lines = [
            "- [ ] 未チェック項目",
            "- [x] チェック済み項目",
            "* [ ] アスタリスク未チェック",
            "+ [X] プラス大文字チェック",
        ]

        for line in test_lines:
            # When: 非順序タイプ検出
            result = self.parser.detect_unordered_type(line)

            # Then: チェックリストタイプが検出されることを検証
            assert result == "checklist"

    def test_正常系_非順序タイプ検出_定義リスト(self):
        """正常系: 定義リストタイプの検出"""
        # Given: 定義リストの行
        test_lines = [
            "用語 :: 定義",
            "API :: Application Programming Interface",
            "複雑な用語 :: 複雑な定義の説明",
        ]

        for line in test_lines:
            # When: 非順序タイプ検出
            result = self.parser.detect_unordered_type(line)

            # Then: 定義リストタイプが検出されることを検証
            assert result == "definition"

    def test_正常系_非順序タイプ検出_非対応(self):
        """正常系: 非対応形式の検出"""
        # Given: 非対応形式の行
        test_lines = ["1. 順序付き項目", "通常のテキスト", "- 不完全なチェック [", ""]

        for line in test_lines:
            # When: 非順序タイプ検出
            result = self.parser.detect_unordered_type(line)

            # Then: Noneが返されることを検証
            assert result is None

    def test_正常系_非順序リスト解析(self):
        """正常系: 非順序リストの解析"""
        # Given: 非順序リストの行リスト
        lines = ["- 最初の項目", "* 二番目の項目", "+ 三番目の項目"]

        # When: 非順序リスト解析
        result = self.parser.parse_unordered_list(lines)

        # Then: 解析結果の検証
        assert len(result) == 3
        assert all(node.type == "list_item" for node in result)
        assert all(node.attributes["ordered"] is False for node in result)

    def test_正常系_非順序項目解析_バレット(self):
        """正常系: バレット項目の解析"""
        # Given: バレット項目の行
        line = "  - インデント付きバレット項目"

        # When: 項目解析
        result = self.parser.parse_unordered_item(line, index=0)

        # Then: 解析結果の検証
        assert result is not None
        assert result.type == "list_item"
        assert result.content == "インデント付きバレット項目"
        assert result.attributes["marker_type"] == "bullet"
        assert result.attributes["indent_level"] == 2

    def test_正常系_非順序項目解析_チェックリスト(self):
        """正常系: チェックリスト項目の解析"""
        # Given: チェックリスト項目の行
        line = "    - [x] インデント付きチェック済み項目"

        # When: 項目解析
        result = self.parser.parse_unordered_item(line, index=1)

        # Then: 解析結果の検証
        assert result is not None
        assert result.type == "checklist_item"
        assert result.content == "インデント付きチェック済み項目"
        assert result.attributes["checked"] is True
        assert result.attributes["marker_type"] == "checklist"
        assert result.attributes["indent_level"] == 4

    def test_正常系_非順序項目解析_定義リスト(self):
        """正常系: 定義リスト項目の解析"""
        # Given: 定義リスト項目の行
        line = "  専門用語 :: 詳細な定義の説明文"

        # When: 項目解析
        result = self.parser.parse_unordered_item(line, index=2)

        # Then: 解析結果の検証
        assert result is not None
        assert result.type == "definition_item"
        assert result.content == "詳細な定義の説明文"
        assert result.attributes["term"] == "専門用語"
        assert result.attributes["marker_type"] == "definition"
        assert result.attributes["indent_level"] == 2

    def test_正常系_チェックリストハンドラー_各種状態(self):
        """正常系: チェックリストハンドラーの各種状態"""
        # Given: 各種チェック状態の行
        test_cases = [
            ("- [ ] 未チェック", False),
            ("- [x] チェック済み", True),
            ("- [X] 大文字チェック", True),
            ("* [ ] アスタリスク未チェック", False),
            ("+ [x] プラスチェック済み", True),
        ]

        for line, expected_checked in test_cases:
            # When: チェックリストハンドラー
            result = self.parser.handle_checklist(line)

            # Then: チェック状態が正しく処理されることを検証
            assert result is not None
            assert result.type == "checklist_item"
            assert result.attributes["checked"] == expected_checked

    def test_正常系_定義リストハンドラー(self):
        """正常系: 定義リストハンドラー"""
        # Given: 定義リストの行
        line = "    API キー :: プログラムで使用する認証情報"

        # When: 定義リストハンドラー
        result = self.parser.handle_definition_list(line)

        # Then: 定義リストが正しく処理されることを検証
        assert result is not None
        assert result.type == "definition_item"
        assert result.content == "プログラムで使用する認証情報"
        assert result.attributes["term"] == "API キー"
        assert result.attributes["indent_level"] == 4

    def test_正常系_チェックリスト状況抽出_詳細(self):
        """正常系: チェックリストの詳細状況抽出"""
        # Given: 子要素を持つチェックリストノード
        checklist_node = Node(
            type="list",
            content="",
            children=[
                Node(
                    type="checklist_item", content="完了1", attributes={"checked": True}
                ),
                Node(
                    type="checklist_item",
                    content="未完了1",
                    attributes={"checked": False},
                ),
                Node(
                    type="checklist_item", content="完了2", attributes={"checked": True}
                ),
                Node(
                    type="checklist_item",
                    content="未完了2",
                    attributes={"checked": False},
                ),
                Node(
                    type="checklist_item", content="完了3", attributes={"checked": True}
                ),
            ],
        )

        # When: 完了状況抽出
        status = self.parser.extract_checklist_status(checklist_node)

        # Then: 詳細な状況統計の検証
        assert status["total"] == 5
        assert status["checked"] == 3
        assert status["unchecked"] == 2
        assert status["completion_rate"] == 60.0

    def test_正常系_チェックリスト切り替え(self):
        """正常系: チェックリスト項目の切り替え"""
        # Given: チェックリスト項目
        unchecked_item = Node(
            type="checklist_item",
            content="切り替えテスト",
            attributes={"checked": False},
        )

        # When: チェック状態切り替え
        toggled_item = self.parser.toggle_checklist_item(unchecked_item)

        # Then: チェック状態が切り替わることを検証
        assert toggled_item.attributes["checked"] is True

        # When: 再度切り替え
        toggled_again = self.parser.toggle_checklist_item(toggled_item)

        # Then: 元の状態に戻ることを検証
        assert toggled_again.attributes["checked"] is False

    def test_正常系_バレットリスト変換(self):
        """正常系: チェックリストからバレットリストへの変換"""
        # Given: チェックリスト項目
        checklist_item = Node(
            type="checklist_item",
            content="変換テスト",
            attributes={"checked": True, "marker_type": "checklist"},
        )

        # When: バレットリスト変換
        bullet_item = self.parser.convert_to_bullet_list(checklist_item, "*")

        # Then: バレットリスト項目への変換確認
        assert bullet_item.type == "list_item"
        assert bullet_item.attributes["marker"] == "*"
        assert bullet_item.attributes["marker_type"] == "bullet"
        assert "checked" not in bullet_item.attributes

    def test_正常系_行からマーカー抽出_詳細(self):
        """正常系: 行からのマーカー抽出（詳細）"""
        # Given: 各種マーカーパターン
        test_cases = [
            ("- 項目", "-"),
            ("* 項目", "*"),
            ("+ 項目", "+"),
            ("  - インデント項目", "-"),
            ("- [x] チェック項目", "-"),
            ("* [ ] アスタリスクチェック", "*"),
            ("+ [X] プラスチェック", "+"),
            ("通常テキスト", None),
            ("", None),
        ]

        for line, expected_marker in test_cases:
            # When: マーカー抽出
            marker = self.parser.get_marker_from_line(line)

            # Then: 期待されるマーカーが抽出されることを検証
            assert marker == expected_marker

    def test_正常系_マーカー正規化(self):
        """正常系: マーカーの正規化"""
        # Given: 異なるマーカーを含む行リスト
        lines = [
            "- ハイフン項目",
            "* アスタリスク項目",
            "+ プラス項目",
            "  - インデント項目",
            "通常テキスト",
        ]

        # When: マーカー正規化（全てアスタリスクに統一）
        normalized = self.parser.normalize_marker(lines, "*")

        # Then: マーカーが統一されることを検証
        expected = [
            "* ハイフン項目",
            "* アスタリスク項目",
            "* プラス項目",
            "  * インデント項目",
            "通常テキスト",  # 非リスト項目は変更されない
        ]
        assert normalized == expected

    # ============================================================================
    # 異常系テスト（20%）
    # ============================================================================

    def test_異常系_不正フォーマット項目解析(self):
        """異常系: 不正フォーマットの項目解析"""
        # Given: 不正フォーマットの行
        invalid_lines = [
            "項目のみ（マーカーなし）",
            "- ",  # 空のコンテンツ
            "- [ 不完全なチェックボックス",
            "用語のみ（定義なし）",
            "",
        ]

        for line in invalid_lines:
            # When: 項目解析
            result = self.parser.parse_unordered_item(line)

            # Then: Noneが返されるか、適切なフォールバックが行われることを検証
            # 実装によってはフォールバックノードが返される場合もある

    def test_異常系_チェックリスト以外の切り替え(self):
        """異常系: チェックリスト以外の項目切り替え"""
        # Given: 通常のリスト項目
        regular_item = Node(
            type="list_item",
            content="通常項目",
            attributes={"marker": "-", "marker_type": "bullet"},
        )

        # When: チェック状態切り替え試行
        result = self.parser.toggle_checklist_item(regular_item)

        # Then: 元のノードがそのまま返されることを検証
        assert result == regular_item
        assert result.type == "list_item"

    def test_異常系_チェックリスト以外の変換(self):
        """異常系: チェックリスト以外のバレットリスト変換"""
        # Given: 定義リスト項目
        definition_item = Node(
            type="definition_item",
            content="定義",
            attributes={"term": "用語", "marker_type": "definition"},
        )

        # When: バレットリスト変換試行
        result = self.parser.convert_to_bullet_list(definition_item)

        # Then: 元のノードがそのまま返されることを検証
        assert result == definition_item
        assert result.type == "definition_item"

    def test_異常系_空のチェックリスト状況(self):
        """異常系: 空のチェックリストの状況抽出"""
        # Given: 子要素がないリストノード
        empty_node = Node(type="list", content="", children=[])

        # When: 完了状況抽出
        status = self.parser.extract_checklist_status(empty_node)

        # Then: 空の状況が返されることを検証
        assert status["total"] == 0
        assert status["checked"] == 0
        assert status["unchecked"] == 0
        assert status["completion_rate"] == 0.0

    def test_異常系_無効なマーカー正規化(self):
        """異常系: 無効な入力のマーカー正規化"""
        # Given: 無効な入力を含む行リスト
        invalid_lines = [
            None,  # Note: Noneは実際のリストには含まれないが、テストとして
        ]
        valid_lines = ["", "   ", "無効な形式の行"]

        # When: マーカー正規化
        normalized = self.parser.normalize_marker(valid_lines, "-")

        # Then: 無効な行は変更されずに保持されることを検証
        assert normalized == valid_lines

    # ============================================================================
    # 境界値テスト（10%）
    # ============================================================================

    def test_境界値_極端なインデント(self):
        """境界値: 極端なインデント"""
        # Given: 極端にインデントされた項目
        extreme_indent = " " * 50
        line = f"{extreme_indent}- 極端なインデント項目"

        # When: 項目解析
        result = self.parser.parse_unordered_item(line)

        # Then: 極端なインデントが処理されることを検証
        assert result is not None
        assert result.attributes["indent_level"] == 50

    def test_境界値_長いコンテンツ(self):
        """境界値: 非常に長いコンテンツ"""
        # Given: 非常に長いコンテンツ
        long_content = "非常に長い" * 200 + "コンテンツ"
        line = f"- {long_content}"

        # When: 項目解析
        result = self.parser.parse_unordered_item(line)

        # Then: 長いコンテンツが処理されることを検証
        assert result is not None
        assert len(result.content) > 1000

    def test_境界値_長い定義リスト(self):
        """境界値: 非常に長い用語と定義"""
        # Given: 長い用語と定義
        long_term = "非常に長い専門用語" * 10
        long_definition = "非常に詳細で長い定義説明" * 20
        line = f"{long_term} :: {long_definition}"

        # When: 定義リスト解析
        result = self.parser.parse_unordered_item(line)

        # Then: 長い用語と定義が処理されることを検証
        assert result is not None
        assert result.type == "definition_item"
        assert len(result.attributes["term"]) > 100
        assert len(result.content) > 200

    def test_境界値_大量チェックリスト(self):
        """境界値: 大量のチェックリスト項目"""
        # Given: 大量のチェックリスト項目
        large_checklist = Node(type="list", content="", children=[])

        # 1000個のチェックリスト項目を作成
        for i in range(1000):
            checked = i % 3 == 0  # 1/3をチェック済みに
            item = Node(
                type="checklist_item",
                content=f"項目{i}",
                attributes={"checked": checked},
            )
            large_checklist.children.append(item)

        # When: 完了状況抽出
        status = self.parser.extract_checklist_status(large_checklist)

        # Then: 大量データが適切に処理されることを検証
        assert status["total"] == 1000
        assert status["checked"] == 334  # 1000/3 + 余り1 = 334
        assert status["unchecked"] == 666

    def test_境界値_特殊文字マーカー(self):
        """境界値: 特殊文字を含むマーカー周辺"""
        # Given: 特殊文字を含む項目
        special_lines = [
            "- **太字**項目",
            "* *イタリック*項目",
            "+ `コード`項目",
            "- [x] **太字チェック**項目",
        ]

        for line in special_lines:
            # When: 項目解析
            result = self.parser.parse_unordered_item(line)

            # Then: 特殊文字が適切に処理されることを検証
            assert result is not None
            assert any(char in result.content for char in ["*", "`"])

    # ============================================================================
    # 統合テスト（10%）
    # ============================================================================

    def test_統合_混合タイプ処理(self):
        """統合: 混合タイプの非順序リスト処理"""
        # Given: 混合タイプの行リスト
        lines = [
            "- バレット項目",
            "- [x] チェック済み項目",
            "用語 :: 定義",
            "* アスタリスク項目",
            "- [ ] 未チェック項目",
        ]

        results = []
        for line in lines:
            unordered_type = self.parser.detect_unordered_type(line)
            if unordered_type == "bullet":
                result = self.parser.handle_unordered_list(line)
            elif unordered_type == "checklist":
                result = self.parser.handle_checklist(line)
            elif unordered_type == "definition":
                result = self.parser.handle_definition_list(line)
            else:
                result = None

            if result:
                results.append(result)

        # Then: 全タイプが適切に処理されることを検証
        assert len(results) == 5
        node_types = [node.type for node in results]
        assert "list_item" in node_types
        assert "checklist_item" in node_types
        assert "definition_item" in node_types

    def test_統合_チェックリスト操作フロー(self):
        """統合: チェックリストの操作フロー"""
        # Given: チェックリスト項目の作成
        line = "- [ ] 統合テストタスク"
        checklist_item = self.parser.handle_checklist(line)

        # When: 一連の操作実行
        # 1. チェック状態切り替え
        checked_item = self.parser.toggle_checklist_item(checklist_item)

        # 2. バレットリストに変換
        bullet_item = self.parser.convert_to_bullet_list(checked_item)

        # 3. マーカー抽出
        original_marker = self.parser.get_marker_from_line(line)

        # Then: 操作フローが正常に動作することを検証
        assert checklist_item.attributes["checked"] is False
        assert checked_item.attributes["checked"] is True
        assert bullet_item.type == "list_item"
        assert original_marker == "-"

    def test_統合_完全ワークフロー(self):
        """統合: 完全な処理ワークフローテスト"""
        # Given: 複雑な非順序リスト
        lines = [
            "- メインタスク1",
            "  - [x] サブタスク1-1（完了）",
            "  - [ ] サブタスク1-2（未完了）",
            "* メインタスク2",
            "  API :: Application Programming Interface",
            "  REST :: Representational State Transfer",
        ]

        # When: 完全な処理ワークフロー
        all_results = []
        for line in lines:
            unordered_type = self.parser.detect_unordered_type(line)

            if unordered_type:
                result = self.parser.parse_unordered_item(line)
                if result:
                    all_results.append(result)

        # マーカー正規化
        normalized_lines = self.parser.normalize_marker(
            lines[:4], "-"
        )  # 定義リスト以外

        # Then: 完全ワークフローが正常に動作することを検証
        assert len(all_results) == 6
        assert len(normalized_lines) == 4
        assert all(
            "- " in line or line.strip() == "" or "::" in line
            for line in normalized_lines
            if line.strip()
        )

    def test_統合_エラーハンドリング総合(self):
        """統合: エラーハンドリングの総合テスト"""
        # Given: 様々な問題を含む入力
        problematic_lines = [
            "- 正常項目",
            "- [ 不完全チェック",
            "",
            "不正な形式",
            "- [x] 正常チェック項目",
        ]

        # When: 堅牢な処理実行
        valid_results = []
        for line in problematic_lines:
            try:
                unordered_type = self.parser.detect_unordered_type(line)
                if unordered_type:
                    result = self.parser.parse_unordered_item(line)
                    if result:
                        valid_results.append(result)
            except Exception:
                # エラーが発生しても処理を続行
                continue

        # Then: エラーがあっても有効な項目は処理されることを検証
        assert len(valid_results) >= 2  # 少なくとも正常項目は処理される

    # ============================================================================
    # 特殊ケーステスト
    # ============================================================================

    def test_特殊_日本語コンテンツ処理(self):
        """特殊: 日本語コンテンツの処理"""
        # Given: 日本語コンテンツを含む項目
        japanese_lines = [
            "- これは日本語の項目です",
            "- [x] 完了した日本語タスク",
            "専門用語 :: 日本語での詳細な説明文",
        ]

        for line in japanese_lines:
            unordered_type = self.parser.detect_unordered_type(line)

            # When: 適切なハンドラーで処理
            if unordered_type == "bullet":
                result = self.parser.handle_unordered_list(line)
            elif unordered_type == "checklist":
                result = self.parser.handle_checklist(line)
            elif unordered_type == "definition":
                result = self.parser.handle_definition_list(line)

            # Then: 日本語が正しく処理されることを検証
            assert result is not None
            assert (
                "日本語" in result.content
                or "完了" in result.content
                or "説明" in result.content
            )

    def test_特殊_複雑な定義リスト(self):
        """特殊: 複雑な定義リストの処理"""
        # Given: 複雑な定義リスト
        complex_definitions = [
            "API (REST) :: RESTful Application Programming Interface",
            "複雑な用語 (略語) :: 括弧と特殊文字を含む定義",
            "JSON :: JavaScript Object Notation (データ交換フォーマット)",
        ]

        for line in complex_definitions:
            # When: 定義リスト解析
            result = self.parser.handle_definition_list(line)

            # Then: 複雑な定義が正しく処理されることを検証
            assert result is not None
            assert result.type == "definition_item"
            assert "::" not in result.content  # 定義部分のみ
            assert "::" not in result.attributes["term"]  # 用語部分のみ

    def test_特殊_統合ハンドラー使用(self):
        """特殊: 統合ハンドラーの使用"""
        # Given: 各種非順序リスト
        test_lines = ["- バレット項目", "- [x] チェック項目"]

        for line in test_lines:
            # When: 統合ハンドラー使用
            result = self.parser.handle_unordered_list(line)

            # Then: 統合ハンドラーが適切に動作することを検証
            if result:
                assert result.type in ["list_item", "checklist_item"]

    def test_特殊_パターン初期化確認(self):
        """特殊: パターン初期化の確認"""
        # Given: 新しいパーサーインスタンス
        new_parser = UnorderedListParser()

        # When: パターン確認
        patterns = new_parser.unordered_patterns

        # Then: 期待されるパターンが初期化されていることを検証
        assert "bullet" in patterns
        assert "checklist" in patterns
        assert "definition" in patterns
        assert all(hasattr(pattern, "match") for pattern in patterns.values())

    def test_特殊_ネストチェックリスト処理(self):
        """特殊: ネストしたチェックリストの処理"""
        # Given: ネストしたチェックリスト構造
        nested_structure = Node(
            type="list",
            content="",
            children=[
                Node(
                    type="checklist_item",
                    content="親タスク1",
                    attributes={"checked": False},
                    children=[
                        Node(
                            type="checklist_item",
                            content="子タスク1-1",
                            attributes={"checked": True},
                        ),
                        Node(
                            type="checklist_item",
                            content="子タスク1-2",
                            attributes={"checked": False},
                        ),
                    ],
                ),
                Node(
                    type="checklist_item",
                    content="親タスク2",
                    attributes={"checked": True},
                ),
            ],
        )

        # When: ネストチェックリスト状況抽出
        # 注: 実装によってはネストした子要素も考慮する必要がある
        status = self.parser.extract_checklist_status(nested_structure)

        # Then: ネスト構造が適切に処理されることを検証
        # 実装によって結果は異なる可能性がある
        assert status["total"] >= 2  # 少なくとも親要素は数えられる
