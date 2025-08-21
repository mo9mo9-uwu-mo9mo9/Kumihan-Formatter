"""非順序リストパーサー（UnorderedListParser）の包括的テスト

Kumihan-Formatter の core/parsing/list/parsers/unordered_parser.py モジュールをテスト
非順序リスト、チェックリスト、定義リストの解析機能を検証
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node, create_node
from kumihan_formatter.core.parsing.list.parsers.unordered_parser import (
    UnorderedListParser,
)


class TestUnorderedListParser:
    """非順序リストパーサーのテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.parser = UnorderedListParser()

    # ============================================================================
    # 正常系テスト（60%）
    # ============================================================================

    def test_正常系_非順序リスト解析_ハイフン(self):
        """正常系: ハイフンマーカーの非順序リスト解析"""
        # Given: ハイフンマーカーの非順序リスト
        line = "- 非順序項目"

        # When: パース実行
        result = self.parser.handle_unordered_list(line)

        # Then: 非順序リスト項目の検証
        assert result is not None
        assert result.node_type == "list_item"
        assert result.content == "非順序項目"
        assert result.metadata["type"] == "unordered"
        assert result.metadata["marker"] == "-"

    def test_正常系_非順序リスト解析_アスタリスク(self):
        """正常系: アスタリスクマーカーの非順序リスト解析"""
        # Given: アスタリスクマーカーの非順序リスト
        line = "* アスタリスク項目"

        # When: パース実行
        result = self.parser.handle_unordered_list(line)

        # Then: アスタリスクマーカーの検証
        assert result is not None
        assert result.metadata["marker"] == "*"
        assert result.content == "アスタリスク項目"

    def test_正常系_非順序リスト解析_プラス(self):
        """正常系: プラスマーカーの非順序リスト解析"""
        # Given: プラスマーカーの非順序リスト
        line = "+ プラス項目"

        # When: パース実行
        result = self.parser.handle_unordered_list(line)

        # Then: プラスマーカーの検証
        assert result is not None
        assert result.metadata["marker"] == "+"
        assert result.content == "プラス項目"

    def test_正常系_チェックリスト解析_未チェック(self):
        """正常系: 未チェックのチェックリスト解析"""
        # Given: 未チェックのチェックリスト
        line = "- [ ] 未完了タスク"

        # When: パース実行
        result = self.parser.handle_checklist(line)

        # Then: 未チェックチェックリストの検証
        assert result is not None
        assert result.node_type == "checklist_item"
        assert result.content == "未完了タスク"
        assert result.metadata["type"] == "checklist"
        assert result.metadata["checked"] is False

    def test_正常系_チェックリスト解析_チェック済み(self):
        """正常系: チェック済みのチェックリスト解析"""
        # Given: チェック済みのチェックリスト
        line = "- [x] 完了タスク"

        # When: パース実行
        result = self.parser.handle_checklist(line)

        # Then: チェック済みチェックリストの検証
        assert result is not None
        assert result.metadata["checked"] is True
        assert result.content == "完了タスク"

    def test_正常系_定義リスト解析(self):
        """正常系: 定義リストの解析"""
        # Given: 定義リスト
        line = "用語 :: 用語の定義説明"

        # When: パース実行
        result = self.parser.handle_definition_list(line)

        # Then: 定義リストの検証
        assert result is not None
        assert result.node_type == "definition_item"
        assert result.content == "用語の定義説明"
        assert result.metadata["type"] == "definition"
        assert result.metadata["term"] == "用語"

    def test_正常系_インデント付きリスト(self):
        """正常系: インデント付きリストの解析"""
        # Given: インデント付きの非順序リスト
        line = "    - インデント項目"

        # When: パース実行
        result = self.parser.handle_unordered_list(line)

        # Then: インデント情報を含む検証
        assert result is not None
        assert result.metadata["indent"] == 4
        assert result.content == "インデント項目"

    def test_正常系_コンテンツ抽出(self):
        """正常系: リスト項目からのコンテンツ抽出"""
        # Given: 各種リスト行
        test_cases = [
            ("- 非順序項目", "unordered", "非順序項目"),
            ("- [x] チェック項目", "checklist", "チェック項目"),
            ("用語 :: 定義", "definition", "定義"),
        ]

        for line, list_type, expected_content in test_cases:
            # When: コンテンツ抽出
            content = self.parser.extract_item_content(line, list_type)

            # Then: 抽出されたコンテンツの検証
            assert content == expected_content

    def test_正常系_パターンマッチング能力判定(self):
        """正常系: 処理可能判定機能"""
        # Given: 各種リスト行とタイプ
        test_cases = [
            ("- 非順序", "unordered", True),
            ("- [x] チェック", "checklist", True),
            ("用語 :: 定義", "definition", True),
            ("1. 順序", "unordered", False),
            ("通常テキスト", "unordered", False),
        ]

        for line, list_type, expected in test_cases:
            # When: 処理可能判定
            result = self.parser.can_handle(line, list_type)

            # Then: 判定結果の検証
            assert result == expected

    def test_正常系_チェックリスト状況抽出(self):
        """正常系: チェックリストの完了状況抽出"""
        # Given: チェックリストノード（メタデータで子要素を模擬）
        checklist_node = create_node(
            "list",
            content="",
            metadata={
                "type": "checklist",
                "children": [
                    create_node(
                        "checklist_item", content="完了", metadata={"checked": True}
                    ),
                    create_node(
                        "checklist_item", content="未完了", metadata={"checked": False}
                    ),
                    create_node(
                        "checklist_item", content="完了2", metadata={"checked": True}
                    ),
                ],
            },
        )

        # When: 完了状況抽出
        status = self.parser.extract_checklist_status(checklist_node)

        # Then: 状況統計の検証
        assert status["total_items"] == 3
        assert status["checked_items"] == 2
        assert status["unchecked_items"] == 1
        assert abs(status["completion_rate"] - 66.67) < 0.1

    def test_正常系_マーカー一貫性検証_正常ケース(self):
        """正常系: 正常なマーカー一貫性の検証"""
        # Given: 一貫したマーカーの非順序リスト項目
        items = [
            create_node(
                "list_item",
                content="項目1",
                metadata={"type": "unordered", "marker": "-", "indent": 0},
            ),
            create_node(
                "list_item",
                content="項目2",
                metadata={"type": "unordered", "marker": "-", "indent": 0},
            ),
            create_node(
                "list_item",
                content="項目3",
                metadata={"type": "unordered", "marker": "-", "indent": 0},
            ),
        ]

        # When: マーカー一貫性検証
        errors = self.parser.validate_marker_consistency(items)

        # Then: エラーなしの検証
        assert len(errors) == 0

    def test_正常系_サポートタイプ取得(self):
        """正常系: サポートするリストタイプの取得"""
        # When: サポートタイプ取得
        supported_types = self.parser.get_supported_types()

        # Then: 期待されるタイプが含まれることを検証
        expected_types = ["unordered", "checklist", "definition"]
        assert all(t in supported_types for t in expected_types)

    # ============================================================================
    # 異常系テスト（20%）
    # ============================================================================

    def test_異常系_不正マーカー一貫性(self):
        """異常系: 不正なマーカー一貫性の処理"""
        # Given: 一貫しないマーカーの非順序リスト項目
        items = [
            create_node(
                "list_item",
                content="項目1",
                metadata={"type": "unordered", "marker": "-", "indent": 0},
            ),
            create_node(
                "list_item",
                content="項目2",
                metadata={"type": "unordered", "marker": "*", "indent": 0},
            ),  # 異なるマーカー
        ]

        # When: マーカー一貫性検証
        errors = self.parser.validate_marker_consistency(items)

        # Then: エラーが検出されることを検証
        assert len(errors) > 0
        assert "マーカーが不一致" in errors[0]

    def test_異常系_不正フォーマット(self):
        """異常系: 不正フォーマットの処理"""
        # Given: 不正フォーマットの行
        invalid_lines = [
            "項目のみ（マーカーなし）",
            "- ",  # 空のコンテンツ
            "",
            "   ",  # 空白のみ
            "- [ 不完全なチェックボックス",
        ]

        for line in invalid_lines:
            # When: パース実行
            result = self.parser.handle_unordered_list(line)

            # Then: フォールバック処理の検証
            assert result is not None
            # 不正フォーマットの場合はフォールバックノードが返される
            if line.strip():
                assert result.content == line.strip()

    def test_異常系_サポート外リストタイプ(self):
        """異常系: サポート外のリストタイプ"""
        # Given: サポート外のリストタイプ
        line = "- 項目"
        unsupported_type = "unsupported"

        # When: 処理可能判定
        result = self.parser.can_handle(line, unsupported_type)

        # Then: 処理不可と判定されることを検証
        assert result == False

    def test_異常系_空のチェックリスト状況(self):
        """異常系: 空のチェックリストの状況抽出"""
        # Given: 空のリストノード
        empty_node = create_node("list", content="", metadata={"type": "checklist"})

        # When: 完了状況抽出
        status = self.parser.extract_checklist_status(empty_node)

        # Then: 空の状況が返されることを検証
        assert status["error"] == "Not a checklist"

    def test_異常系_チェックリスト以外の状況抽出(self):
        """異常系: チェックリスト以外のノードの状況抽出"""
        # Given: チェックリスト以外のノード
        non_checklist_node = create_node(
            "list", content="", metadata={"type": "unordered"}
        )

        # When: 完了状況抽出
        status = self.parser.extract_checklist_status(non_checklist_node)

        # Then: エラーが返されることを検証
        assert status["error"] == "Not a checklist"

    # ============================================================================
    # 境界値テスト（10%）
    # ============================================================================

    def test_境界値_最大インデント(self):
        """境界値: 最大インデントレベル"""
        # Given: 非常に深いインデントの項目
        deep_indent = " " * 20
        line = f"{deep_indent}- 深いインデント項目"

        # When: パース実行
        result = self.parser.handle_unordered_list(line)

        # Then: インデントが正しく処理されることを検証
        assert result is not None
        assert result.metadata["indent"] == 20

    def test_境界値_長いコンテンツ(self):
        """境界値: 非常に長いコンテンツ"""
        # Given: 非常に長いコンテンツ
        long_content = "非常に長い" * 100 + "コンテンツ"
        line = f"- {long_content}"

        # When: パース実行
        result = self.parser.handle_unordered_list(line)

        # Then: 長いコンテンツが正常に処理されることを検証
        assert result is not None
        assert result.content == long_content

    def test_境界値_長い定義リスト(self):
        """境界値: 非常に長い用語と定義"""
        # Given: 長い用語と定義
        long_term = "非常に長い用語" * 20
        long_definition = "非常に長い定義" * 50
        line = f"{long_term} :: {long_definition}"

        # When: パース実行
        result = self.parser.handle_definition_list(line)

        # Then: 長い用語と定義が正常に処理されることを検証
        assert result is not None
        assert result.metadata["term"] == long_term
        assert result.content == long_definition

    def test_境界値_特殊文字マーカー組み合わせ(self):
        """境界値: 特殊文字を含むマーカーの組み合わせ"""
        # Given: 各種マーカーの組み合わせ
        test_cases = ["- ハイフン項目", "* アスタリスク項目", "+ プラス項目"]

        for line in test_cases:
            # When: パース実行
            result = self.parser.handle_unordered_list(line)

            # Then: 全マーカーが正常に処理されることを検証
            assert result is not None
            assert result.metadata["marker"] in ["-", "*", "+"]

    def test_境界値_チェックボックス変形(self):
        """境界値: チェックボックスの各種状態"""
        # Given: チェックボックスの各種状態
        test_cases = [
            ("- [ ] 未チェック", False),
            ("- [x] チェック済み", True),
            ("- [X] 大文字チェック", True),
            ("* [ ] アスタリスク未チェック", False),
            ("+ [x] プラスチェック済み", True),
        ]

        for line, expected_checked in test_cases:
            # When: パース実行
            result = self.parser.handle_checklist(line)

            # Then: チェック状態が正しく認識されることを検証
            assert result is not None
            assert result.metadata["checked"] == expected_checked

    # ============================================================================
    # 統合テスト（10%）
    # ============================================================================

    def test_統合_混合リストタイプ処理(self):
        """統合: 混合リストタイプの処理"""
        # Given: 異なるタイプの混合リスト
        lines = [
            "- 非順序項目",
            "- [x] チェック済み項目",
            "用語 :: 定義",
            "- [ ] 未チェック項目",
        ]

        results = []
        for line in lines:
            if self.parser.can_handle(line, "unordered"):
                result = self.parser.handle_unordered_list(line)
            elif self.parser.can_handle(line, "checklist"):
                result = self.parser.handle_checklist(line)
            elif self.parser.can_handle(line, "definition"):
                result = self.parser.handle_definition_list(line)
            else:
                result = None

            if result:
                results.append(result)

        # Then: 全項目が適切なタイプで解析されることを検証
        assert len(results) == 4
        types = [result.node_type for result in results]
        assert "list_item" in types
        assert "checklist_item" in types
        assert "definition_item" in types

    def test_統合_チェックリスト完了率計算(self):
        """統合: チェックリストの完了率計算の詳細テスト"""
        # Given: 様々な状態のチェックリスト
        checklist_items = [
            create_node("checklist_item", content="完了1", metadata={"checked": True}),
            create_node(
                "checklist_item", content="未完了1", metadata={"checked": False}
            ),
            create_node("checklist_item", content="完了2", metadata={"checked": True}),
            create_node(
                "checklist_item", content="未完了2", metadata={"checked": False}
            ),
            create_node("checklist_item", content="完了3", metadata={"checked": True}),
        ]

        # ネストチェックリストを模擬
        checklist_node = create_node(
            "list",
            content="",
            metadata={"type": "checklist", "children": checklist_items},
        )

        # When: 完了状況抽出
        status = self.parser.extract_checklist_status(checklist_node)

        # Then: 詳細な統計の検証
        assert status["total_items"] == 5
        assert status["checked_items"] == 3
        assert status["unchecked_items"] == 2
        assert status["completion_rate"] == 60.0
        assert status["completed"] is False  # 全完了ではない

    def test_統合_マーカー正規化機能(self):
        """統合: マーカー正規化機能のテスト"""
        # Given: 異なるマーカーを含む行リスト
        lines = ["- ハイフン項目", "* アスタリスク項目", "+ プラス項目", "通常テキスト"]

        # When: マーカー正規化（全てハイフンに統一）
        normalized_lines = self.parser.normalize_marker(lines, "-")

        # Then: マーカーが統一されることを検証
        assert "- ハイフン項目" in normalized_lines
        assert "- アスタリスク項目" in normalized_lines
        assert "- プラス項目" in normalized_lines
        assert "通常テキスト" in normalized_lines  # 非リスト項目は変更されない

    def test_統合_チェックリスト切り替え機能(self):
        """統合: チェックリスト項目の切り替え機能"""
        # Given: チェックリスト項目
        checklist_item = create_node(
            "checklist_item", content="タスク", metadata={"checked": False}
        )

        # When: チェック状態切り替え
        toggled_item = self.parser.toggle_checklist_item(checklist_item)

        # Then: チェック状態が切り替わることを検証
        assert toggled_item.metadata["checked"] is True

        # When: 再度切り替え
        toggled_again = self.parser.toggle_checklist_item(toggled_item)

        # Then: 元の状態に戻ることを検証
        assert toggled_again.metadata["checked"] is False

    def test_統合_チェックリストから通常リスト変換(self):
        """統合: チェックリストから通常リストへの変換"""
        # Given: チェックリスト項目
        checklist_item = create_node(
            "checklist_item",
            content="タスク",
            metadata={"checked": True, "type": "checklist"},
        )

        # When: 通常リストに変換
        bullet_item = self.parser.convert_to_bullet_list(checklist_item, "*")

        # Then: 通常リスト項目への変換確認
        assert bullet_item.node_type == "list_item"
        assert bullet_item.metadata["marker"] == "*"
        assert bullet_item.metadata["marker_type"] == "bullet"
        assert "checked" not in bullet_item.metadata

    # ============================================================================
    # 特殊ケーステスト
    # ============================================================================

    def test_特殊_日本語コンテンツ(self):
        """特殊: 日本語コンテンツの処理"""
        # Given: 日本語を含むリスト項目
        test_cases = [
            "- これは日本語の項目です",
            "- [x] 完了した日本語タスク",
            "専門用語 :: 日本語での詳細な説明文",
        ]

        for line in test_cases:
            # When: 適切なハンドラーでパース実行
            if self.parser.can_handle(line, "unordered"):
                result = self.parser.handle_unordered_list(line)
            elif self.parser.can_handle(line, "checklist"):
                result = self.parser.handle_checklist(line)
            elif self.parser.can_handle(line, "definition"):
                result = self.parser.handle_definition_list(line)

            # Then: 日本語が正しく処理されることを検証
            assert result is not None
            assert (
                "日本語" in result.content
                or "完了" in result.content
                or "説明" in result.content
            )

    def test_特殊_特殊文字とマークアップ(self):
        """特殊: 特殊文字とマークアップの処理"""
        # Given: 特殊文字やマークアップを含む項目
        line = "- **太字**と*イタリック*と`コード`を含む項目"

        # When: パース実行
        result = self.parser.handle_unordered_list(line)

        # Then: マークアップが含まれたまま処理されることを検証
        assert result is not None
        assert "**太字**" in result.content
        assert "*イタリック*" in result.content
        assert "`コード`" in result.content

    def test_特殊_行からマーカー抽出(self):
        """特殊: 行からのマーカー抽出機能"""
        # Given: 各種マーカーを含む行
        test_cases = [
            ("- 項目", "-"),
            ("* 項目", "*"),
            ("+ 項目", "+"),
            ("- [x] チェック項目", "-"),
            ("通常テキスト", None),
            ("", None),
        ]

        for line, expected_marker in test_cases:
            # When: マーカー抽出
            marker = self.parser.get_marker_from_line(line)

            # Then: 期待されるマーカーが抽出されることを検証
            assert marker == expected_marker

    def test_特殊_パターン初期化(self):
        """特殊: パターン初期化の動作確認"""
        # Given: 新しいパーサーインスタンス
        new_parser = UnorderedListParser()

        # When: パターン確認
        patterns = new_parser.patterns

        # Then: 期待されるパターンが設定されていることを検証
        assert "unordered" in patterns
        assert "checklist" in patterns
        assert "definition" in patterns
        assert all(hasattr(pattern, "match") for pattern in patterns.values())

    def test_特殊_複雑な定義リスト(self):
        """特殊: 複雑な定義リストの処理"""
        # Given: 複雑な定義リスト（用語にスペースや特殊文字を含む）
        test_cases = [
            "複雑な 用語 :: 複雑な定義の説明",
            "API キー :: プログラムで使用する認証情報",
            "正規表現(regex) :: パターンマッチングの仕組み",
        ]

        for line in test_cases:
            # When: パース実行
            result = self.parser.handle_definition_list(line)

            # Then: 複雑な用語が正しく処理されることを検証
            assert result is not None
            assert result.node_type == "definition_item"
            assert "::" not in result.content  # 定義部分のみ
            assert "::" not in result.metadata["term"]  # 用語部分のみ
