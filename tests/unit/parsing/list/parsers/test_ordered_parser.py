"""順序付きリストパーサー（OrderedListParser）の包括的テスト

Kumihan-Formatter の core/parsing/list/parsers/ordered_parser.py モジュールをテスト
順序付きリスト、アルファベットリスト、ローマ数字リストの解析機能を検証
"""

import pytest
from unittest.mock import Mock, patch

from kumihan_formatter.core.parsing.list.parsers.ordered_parser import OrderedListParser
from kumihan_formatter.core.ast_nodes import Node, create_node


class TestOrderedListParser:
    """順序付きリストパーサーのテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.parser = OrderedListParser()

    # ============================================================================
    # 正常系テスト（60%）
    # ============================================================================

    def test_正常系_順序付きリスト解析(self):
        """正常系: 順序付きリストの解析"""
        # Given: 順序付きリストの行
        line = "1. 最初の項目"

        # When: パース実行
        result = self.parser.handle_ordered_list(line)

        # Then: リスト項目ノードの検証
        assert result is not None
        assert result.node_type == "list_item"
        assert result.content == "最初の項目"
        assert result.metadata["type"] == "ordered"
        assert result.metadata["number"] == 1

    def test_正常系_複数項目の順序付きリスト(self):
        """正常系: 複数項目の順序付きリスト"""
        # Given: 複数の順序付きリスト項目
        lines = [
            "1. 項目1",
            "2. 項目2", 
            "3. 項目3"
        ]

        # When: 各行をパース
        results = []
        for line in lines:
            result = self.parser.handle_ordered_list(line)
            if result:
                results.append(result)

        # Then: 全項目の検証
        assert len(results) == 3
        assert all(node.metadata["type"] == "ordered" for node in results)
        assert [node.metadata["number"] for node in results] == [1, 2, 3]
        assert [node.content for node in results] == ["項目1", "項目2", "項目3"]

    def test_正常系_アルファベットリスト解析(self):
        """正常系: アルファベットリストの解析"""
        # Given: アルファベットリストの行
        line = "a. アルファベット項目"

        # When: パース実行
        result = self.parser.handle_alpha_list(line)

        # Then: アルファベットリスト項目の検証
        assert result is not None
        assert result.node_type == "list_item"
        assert result.content == "アルファベット項目"
        assert result.metadata["type"] == "alpha"
        assert result.metadata["letter"] == "a"

    def test_正常系_ローマ数字リスト解析(self):
        """正常系: ローマ数字リストの解析"""
        # Given: ローマ数字リストの行
        line = "i. ローマ数字項目"

        # When: パース実行
        result = self.parser.handle_roman_list(line)

        # Then: ローマ数字リスト項目の検証
        assert result is not None
        assert result.node_type == "list_item"
        assert result.content == "ローマ数字項目"
        assert result.metadata["type"] == "roman"
        assert result.metadata["roman"] == "i"

    def test_正常系_インデント付きリスト(self):
        """正常系: インデント付きリストの解析"""
        # Given: インデント付きの順序付きリスト
        line = "    1. インデント項目"

        # When: パース実行
        result = self.parser.handle_ordered_list(line)

        # Then: インデント情報を含む検証
        assert result is not None
        assert result.metadata["indent"] == 4
        assert result.content == "インデント項目"

    def test_正常系_コンテンツ抽出(self):
        """正常系: リスト項目からのコンテンツ抽出"""
        # Given: 各種リスト行
        test_cases = [
            ("1. 順序付き項目", "ordered", "順序付き項目"),
            ("a. アルファベット項目", "alpha", "アルファベット項目"),
            ("i. ローマ数字項目", "roman", "ローマ数字項目"),
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
            ("1. 順序付き", "ordered", True),
            ("a. アルファベット", "alpha", True),
            ("i. ローマ数字", "roman", True),
            ("- 非順序", "ordered", False),
            ("通常テキスト", "ordered", False),
        ]

        for line, list_type, expected in test_cases:
            # When: 処理可能判定
            result = self.parser.can_handle(line, list_type)

            # Then: 判定結果の検証
            assert bool(result) == expected

    def test_正常系_連番検証_正常ケース(self):
        """正常系: 正常な連番の検証"""
        # Given: 正常な連番の順序付きリスト項目
        items = [
            create_node("list_item", content="項目1", 
                       metadata={"type": "ordered", "number": 1, "indent": 0}),
            create_node("list_item", content="項目2",
                       metadata={"type": "ordered", "number": 2, "indent": 0}),
            create_node("list_item", content="項目3",
                       metadata={"type": "ordered", "number": 3, "indent": 0}),
        ]

        # When: 連番検証
        errors = self.parser.validate_ordered_sequence(items)

        # Then: エラーなしの検証
        assert len(errors) == 0

    def test_正常系_サポートタイプ取得(self):
        """正常系: サポートするリストタイプの取得"""
        # When: サポートタイプ取得
        supported_types = self.parser.get_supported_types()

        # Then: 期待されるタイプが含まれることを検証
        expected_types = ["ordered", "alpha", "roman"]
        assert all(t in supported_types for t in expected_types)

    # ============================================================================
    # 異常系テスト（20%）
    # ============================================================================

    def test_異常系_不正な順序番号(self):
        """異常系: 不正な順序番号の処理"""
        # Given: 不正な連番の順序付きリスト項目
        items = [
            create_node("list_item", content="項目1",
                       metadata={"type": "ordered", "number": 1, "indent": 0}),
            create_node("list_item", content="項目3",  # 2をスキップ
                       metadata={"type": "ordered", "number": 3, "indent": 0}),
        ]

        # When: 連番検証
        errors = self.parser.validate_ordered_sequence(items)

        # Then: エラーが検出されることを検証
        assert len(errors) > 0
        assert "期待される番号2" in errors[0]

    def test_異常系_不正フォーマット(self):
        """異常系: 不正フォーマットの処理"""
        # Given: 不正フォーマットの行
        invalid_lines = [
            "1 項目（ドットなし）",
            "a 項目（ドットなし）",
            "項目のみ",
            "",
            "1.    "  # 空のコンテンツ
        ]

        for line in invalid_lines:
            # When: パース実行
            result = self.parser.handle_ordered_list(line)

            # Then: フォールバック処理の検証
            assert result is not None
            # 不正フォーマットの場合はフォールバックノードが返される
            # 実装によってはcontentが元の行と異なる場合がある

    def test_異常系_サポート外リストタイプ(self):
        """異常系: サポート外のリストタイプ"""
        # Given: サポート外のリストタイプ
        line = "1. 項目"
        unsupported_type = "unsupported"

        # When: 処理可能判定
        result = self.parser.can_handle(line, unsupported_type)

        # Then: 処理不可と判定されることを検証
        assert result == False

    def test_異常系_空文字列処理(self):
        """異常系: 空文字列の処理"""
        # Given: 空文字列
        empty_inputs = ["", "   ", "\n", "\t"]

        for empty_input in empty_inputs:
            # When: コンテンツ抽出
            content = self.parser.extract_item_content(empty_input, "ordered")

            # Then: 空文字列が返されることを検証
            assert content == ""

    # ============================================================================
    # 境界値テスト（10%）
    # ============================================================================

    def test_境界値_大きな番号(self):
        """境界値: 大きな番号の順序付きリスト"""
        # Given: 大きな番号の順序付きリスト
        line = "999. 大きな番号の項目"

        # When: パース実行
        result = self.parser.handle_ordered_list(line)

        # Then: 正常に処理されることを検証
        assert result is not None
        assert result.metadata["number"] == 999
        assert result.content == "大きな番号の項目"

    def test_境界値_最大インデント(self):
        """境界値: 最大インデントレベル"""
        # Given: 非常に深いインデントの項目
        deep_indent = " " * 20
        line = f"{deep_indent}1. 深いインデント項目"

        # When: パース実行
        result = self.parser.handle_ordered_list(line)

        # Then: インデントが正しく処理されることを検証
        assert result is not None
        assert result.metadata["indent"] == 20

    def test_境界値_長いコンテンツ(self):
        """境界値: 非常に長いコンテンツ"""
        # Given: 非常に長いコンテンツ
        long_content = "非常に長い" * 100 + "コンテンツ"
        line = f"1. {long_content}"

        # When: パース実行
        result = self.parser.handle_ordered_list(line)

        # Then: 長いコンテンツが正常に処理されることを検証
        assert result is not None
        assert result.content == long_content

    def test_境界値_アルファベット端境界(self):
        """境界値: アルファベットの端境界（a, z）"""
        # Given: アルファベットの端境界
        test_cases = [
            "a. 最初のアルファベット",
            "z. 最後のアルファベット",
            "A. 大文字最初",
            "Z. 大文字最後"
        ]

        for line in test_cases:
            # When: パース実行
            result = self.parser.handle_alpha_list(line)

            # Then: 正常に処理されることを検証
            assert result is not None
            assert result.metadata["type"] == "alpha"

    def test_境界値_ローマ数字境界(self):
        """境界値: ローマ数字の境界値"""
        # Given: ローマ数字の境界値
        test_cases = [
            "i. 最小ローマ数字",
            "x. 最大ローマ数字",
            "iv. 中間ローマ数字",
            "ix. 複雑ローマ数字"
        ]

        for line in test_cases:
            # When: パース実行
            result = self.parser.handle_roman_list(line)

            # Then: 正常に処理されることを検証
            assert result is not None
            assert result.metadata["type"] == "roman"

    # ============================================================================
    # 統合テスト（10%）
    # ============================================================================

    def test_統合_混合リストタイプ連番検証(self):
        """統合: 混合リストタイプでの連番検証"""
        # Given: 異なるタイプの混合リスト
        items = [
            create_node("list_item", content="順序1",
                       metadata={"type": "ordered", "number": 1, "indent": 0}),
            create_node("list_item", content="アルファa",
                       metadata={"type": "alpha", "letter": "a", "indent": 4}),
            create_node("list_item", content="順序2",
                       metadata={"type": "ordered", "number": 2, "indent": 0}),
        ]

        # When: 連番検証（順序付きリストのみ対象）
        errors = self.parser.validate_ordered_sequence(items)

        # Then: 順序付きリストの連番のみチェックされることを検証
        assert len(errors) == 0  # 1→2の連番は正常

    def test_統合_複数レベルネスト検証(self):
        """統合: 複数レベルのネスト構造での連番検証"""
        # Given: 複数レベルのネスト構造
        items = [
            create_node("list_item", content="レベル0-1",
                       metadata={"type": "ordered", "number": 1, "indent": 0}),
            create_node("list_item", content="レベル1-1",
                       metadata={"type": "ordered", "number": 1, "indent": 4}),
            create_node("list_item", content="レベル1-2",
                       metadata={"type": "ordered", "number": 2, "indent": 4}),
            create_node("list_item", content="レベル0-2",
                       metadata={"type": "ordered", "number": 2, "indent": 0}),
        ]

        # When: 連番検証
        errors = self.parser.validate_ordered_sequence(items)

        # Then: 各レベルで独立した連番が正しく検証されることを確認
        assert len(errors) == 0

    def test_統合_全機能組み合わせ(self):
        """統合: 全機能の組み合わせテスト"""
        # Given: 様々な機能を組み合わせた入力
        lines = [
            "1. 順序付き項目1",
            "    a. ネストアルファベット",
            "    b. ネストアルファベット2",
            "2. 順序付き項目2",
            "    i. ネストローマ数字",
            "    ii. ネストローマ数字2"
        ]

        results = []
        for line in lines:
            if self.parser.can_handle(line, "ordered"):
                result = self.parser.handle_ordered_list(line)
            elif self.parser.can_handle(line, "alpha"):
                result = self.parser.handle_alpha_list(line)
            elif self.parser.can_handle(line, "roman"):
                result = self.parser.handle_roman_list(line)
            else:
                result = None
            
            if result:
                results.append(result)

        # Then: 全項目が適切に解析されることを検証
        assert len(results) == 6
        assert all(result.node_type == "list_item" for result in results)

    def test_統合_エラーハンドリング連携(self):
        """統合: エラーハンドリングとの連携"""
        # Given: 部分的に不正な連番を含むリスト
        items = [
            create_node("list_item", content="項目1",
                       metadata={"type": "ordered", "number": 1, "indent": 0}),
            create_node("list_item", content="項目3",  # 不正な順序
                       metadata={"type": "ordered", "number": 3, "indent": 0}),
            create_node("list_item", content="項目4",
                       metadata={"type": "ordered", "number": 4, "indent": 0}),
        ]

        # When: 連番検証と統計取得
        errors = self.parser.validate_ordered_sequence(items)
        supported_types = self.parser.get_supported_types()

        # Then: エラー検出と機能統合の検証
        assert len(errors) > 0  # エラーが検出される
        assert "ordered" in supported_types  # サポートタイプに含まれる

    # ============================================================================
    # 特殊ケーステスト
    # ============================================================================

    def test_特殊_日本語コンテンツ(self):
        """特殊: 日本語コンテンツの処理"""
        # Given: 日本語を含むリスト項目
        test_cases = [
            "1. これは日本語の項目です",
            "a. ひらがなとカタカナと漢字",
            "i. 特殊文字：「」、。・"
        ]

        for line in test_cases:
            # When: パース実行
            if self.parser.can_handle(line, "ordered"):
                result = self.parser.handle_ordered_list(line)
            elif self.parser.can_handle(line, "alpha"):
                result = self.parser.handle_alpha_list(line)
            elif self.parser.can_handle(line, "roman"):
                result = self.parser.handle_roman_list(line)

            # Then: 日本語が正しく処理されることを検証
            assert result is not None
            assert "日本語" in result.content or "ひらがな" in result.content or "特殊文字" in result.content

    def test_特殊_特殊文字とマークアップ(self):
        """特殊: 特殊文字とマークアップの処理"""
        # Given: 特殊文字やマークアップを含む項目
        line = "1. **太字**と*イタリック*と`コード`を含む項目"

        # When: パース実行
        result = self.parser.handle_ordered_list(line)

        # Then: マークアップが含まれたまま処理されることを検証
        assert result is not None
        assert "**太字**" in result.content
        assert "*イタリック*" in result.content
        assert "`コード`" in result.content

    def test_特殊_パターン初期化(self):
        """特殊: パターン初期化の動作確認"""
        # Given: 新しいパーサーインスタンス
        new_parser = OrderedListParser()

        # When: パターン確認
        patterns = new_parser.patterns

        # Then: 期待されるパターンが設定されていることを検証
        assert "ordered" in patterns
        assert "alpha" in patterns  
        assert "roman" in patterns
        assert all(hasattr(pattern, 'match') for pattern in patterns.values())