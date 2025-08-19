"""AST utilities comprehensive tests

This module provides comprehensive testing for AST utility functions
in the utilities module, covering all scenarios and edge cases.
"""

import pytest
from typing import Any
from unittest.mock import Mock

from kumihan_formatter.core.ast_nodes.node import Node
from kumihan_formatter.core.ast_nodes.utilities import (
    flatten_text_nodes,
    count_nodes_by_type,
    find_all_headings,
    validate_ast
)
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestFlattenTextNodes:
    """flatten_text_nodes関数テスト"""

    def test_正常系_連続テキスト統合(self) -> None:
        """正常系: 連続するテキストノードの統合確認"""
        content = ["Hello", " ", "World", "!"]
        result = flatten_text_nodes(content)

        assert result == ["Hello World!"]

    def test_正常系_混在要素処理(self) -> None:
        """正常系: テキスト・Nodeの混在リスト処理確認"""
        node = Node(type="strong", content="bold")
        content = ["Start ", node, " middle ", "end"]
        result = flatten_text_nodes(content)

        assert len(result) == 3
        assert result[0] == "Start "
        assert result[1] == node
        assert result[2] == " middle end"

    def test_正常系_ノードで開始(self) -> None:
        """正常系: ノードで開始するリストの処理確認"""
        node = Node(type="em", content="italic")
        content = [node, " after"]
        result = flatten_text_nodes(content)

        assert len(result) == 2
        assert result[0] == node
        assert result[1] == " after"

    def test_正常系_ノードで終了(self) -> None:
        """正常系: ノードで終了するリストの処理確認"""
        node = Node(type="code", content="code")
        content = ["before ", node]
        result = flatten_text_nodes(content)

        assert len(result) == 2
        assert result[0] == "before "
        assert result[1] == node

    def test_境界値_空リスト処理(self) -> None:
        """境界値: 空リスト・None要素での処理確認"""
        # 空リスト
        assert flatten_text_nodes([]) == []

        # None要素を含むリスト（Noneは文字列ではないため、そのまま残る）
        content_with_none = ["text", None, "more"]
        result = flatten_text_nodes(content_with_none)
        assert len(result) == 3
        assert result[0] == "text"
        assert result[1] is None
        assert result[2] == "more"

    def test_境界値_テキストのみ(self) -> None:
        """境界値: テキストのみのリスト処理確認"""
        content = ["a", "b", "c", "d"]
        result = flatten_text_nodes(content)

        assert result == ["abcd"]

    def test_境界値_ノードのみ(self) -> None:
        """境界値: ノードのみのリスト処理確認"""
        node1 = Node(type="span", content="span1")
        node2 = Node(type="div", content="div1")
        content = [node1, node2]
        result = flatten_text_nodes(content)

        assert len(result) == 2
        assert result[0] == node1
        assert result[1] == node2

    def test_境界値_空文字列含有(self) -> None:
        """境界値: 空文字列を含む処理確認"""
        content = ["start", "", "middle", "", "end"]
        result = flatten_text_nodes(content)

        assert result == ["startmiddleend"]

    def test_境界値_None入力(self) -> None:
        """境界値: None入力時の処理確認"""
        # 関数内でnot contentチェックしているため、Noneは早期リターンされる
        # type: ignore[arg-type] を使用して型チェッカーエラーを抑制
        result = flatten_text_nodes(None)  # type: ignore[arg-type]
        assert result is None


class TestCountNodesByType:
    """count_nodes_by_type関数テスト"""

    def test_正常系_タイプ別カウント(self):
        """正常系: 各種ノードタイプのカウント確認"""
        nodes = [
            Node(type="p", content="para1"),
            Node(type="h1", content="heading"),
            Node(type="p", content="para2"),
            Node(type="div", content="division"),
            Node(type="span", content="span1")
        ]
        result = count_nodes_by_type(nodes)

        assert result["p"] == 2
        assert result["h1"] == 1
        assert result["div"] == 1
        assert result["span"] == 1
        assert len(result) == 4

    def test_正常系_同一タイプ複数(self):
        """正常系: 同一タイプ複数ノードのカウント確認"""
        nodes = [
            Node(type="li", content="item1"),
            Node(type="li", content="item2"),
            Node(type="li", content="item3"),
            Node(type="li", content="item4")
        ]
        result = count_nodes_by_type(nodes)

        assert result["li"] == 4
        assert len(result) == 1

    def test_境界値_空リスト(self):
        """境界値: 空リスト・Node以外混在での処理確認"""
        # 空リスト
        assert count_nodes_by_type([]) == {}

        # Node以外の要素（関数内でisinstance(node, Node)チェックで除外）
        mixed_list = [
            "not a node",
            42,
            None,
            {"type": "fake"}
        ]
        result = count_nodes_by_type(mixed_list)
        assert result == {}

    def test_境界値_非Node要素混在(self):
        """境界値: 非Node要素が混在したリストの処理確認"""
        nodes = [
            Node(type="p", content="paragraph"),
            "string element",
            Node(type="div", content="division"),
            123,
            Node(type="p", content="another para")
        ]
        result = count_nodes_by_type(nodes)

        # 非Node要素は無視され、Nodeのみカウント
        assert result["p"] == 2
        assert result["div"] == 1
        assert len(result) == 2

    def test_正常系_空タイプ処理(self):
        """正常系: 空のタイプを持つノードの処理確認"""
        nodes = [
            Node(type="", content="empty type"),
            Node(type="p", content="normal")
        ]
        result = count_nodes_by_type(nodes)

        # 空タイプも正常にカウント
        assert result[""] == 1
        assert result["p"] == 1


class TestFindAllHeadings:
    """find_all_headings関数テスト"""

    def test_正常系_見出し検索(self):
        """正常系: 各レベル見出しの検索確認"""
        nodes = [
            Node(type="h1", content="Main Title"),
            Node(type="p", content="paragraph"),
            Node(type="h2", content="Subtitle"),
            Node(type="div", content="division"),
            Node(type="h3", content="Sub-subtitle")
        ]
        result = find_all_headings(nodes)

        assert len(result) == 3
        assert result[0].type == "h1"
        assert result[0].content == "Main Title"
        assert result[1].type == "h2"
        assert result[1].content == "Subtitle"
        assert result[2].type == "h3"
        assert result[2].content == "Sub-subtitle"

    def test_正常系_再帰的検索(self):
        """正常系: ネストしたノード内の見出し検索確認"""
        nested_heading = Node(type="h2", content="Nested heading")
        container = Node(type="div", content=[
            "Some text",
            nested_heading,
            "More text"
        ])

        nodes = [
            Node(type="h1", content="Top level"),
            container,
            Node(type="p", content="paragraph")
        ]
        result = find_all_headings(nodes)

        assert len(result) == 2
        assert result[0].type == "h1"
        assert result[0].content == "Top level"
        assert result[1].type == "h2"
        assert result[1].content == "Nested heading"

    def test_正常系_複合構造検索(self):
        """正常系: 複雑なAST構造での見出し検索確認"""
        # 深いネスト構造を作成
        deep_heading = Node(type="h4", content="Deep heading")
        level3_container = Node(type="section", content=[deep_heading])
        level2_container = Node(type="article", content=[
            Node(type="h3", content="Level 3 heading"),
            level3_container
        ])
        level1_container = Node(type="div", content=[
            Node(type="h2", content="Level 2 heading"),
            level2_container
        ])

        nodes = [
            Node(type="h1", content="Root heading"),
            level1_container
        ]

        result = find_all_headings(nodes)

        assert len(result) == 4
        assert result[0].content == "Root heading"
        assert result[1].content == "Level 2 heading"
        assert result[2].content == "Level 3 heading"
        assert result[3].content == "Deep heading"

    def test_境界値_見出しなし(self):
        """境界値: 見出しが存在しない場合の処理確認"""
        nodes = [
            Node(type="p", content="paragraph"),
            Node(type="div", content="division"),
            Node(type="span", content="span")
        ]
        result = find_all_headings(nodes)

        assert result == []

    def test_境界値_空リスト(self):
        """境界値: 空リストでの検索確認"""
        result = find_all_headings([])
        assert result == []

    def test_境界値_非Node要素混在(self):
        """境界値: 非Node要素が混在した場合の処理確認"""
        nodes = [
            "not a node",
            Node(type="h1", content="Real heading"),
            42,
            {"fake": "node"}
        ]
        result = find_all_headings(nodes)

        assert len(result) == 1
        assert result[0].content == "Real heading"

    def test_正常系_文字列コンテンツノード(self):
        """正常系: 文字列コンテンツを持つノード内検索"""
        node_with_string = Node(type="div", content="string content")
        nodes = [
            Node(type="h1", content="heading"),
            node_with_string
        ]
        result = find_all_headings(nodes)

        # 文字列コンテンツのノードは再帰検索されない
        assert len(result) == 1
        assert result[0].content == "heading"


class TestValidateAST:
    """validate_ast関数テスト"""

    def test_正常系_有効AST(self):
        """正常系: 有効なAST構造の検証確認"""
        nodes = [
            Node(type="h1", content="Title"),
            Node(type="p", content="Paragraph"),
            Node(type="div", content=["Mixed", "content"])
        ]
        issues = validate_ast(nodes)

        assert issues == []

    def test_異常系_非Node要素(self):
        """異常系: 非Node要素を含むリストの検証確認"""
        nodes = [
            Node(type="p", content="Valid node"),
            "string element",
            42,
            None,
            {"fake": "node"}
        ]
        issues = validate_ast(nodes)

        assert len(issues) == 4
        assert "Item 1 is not a Node instance" in issues[0]
        assert "Item 2 is not a Node instance" in issues[1]
        assert "Item 3 is not a Node instance" in issues[2]
        assert "Item 4 is not a Node instance" in issues[3]

    def test_異常系_空タイプ(self):
        """異常系: 空のタイプを持つノードの検証確認"""
        nodes = [
            Node(type="", content="Empty type"),
            Node(type="p", content="Normal")
        ]
        issues = validate_ast(nodes)

        assert len(issues) == 1
        assert "Node 0 has empty type" in issues[0]

    def test_異常系_Noneコンテンツ(self):
        """異常系: Noneコンテンツを持つノードの検証確認"""
        nodes = [
            Node(type="div", content=None),
            Node(type="p", content="Normal")
        ]
        issues = validate_ast(nodes)

        assert len(issues) == 1
        assert "Node 0 (div) has None content" in issues[0]

    def test_異常系_不正見出しレベル(self):
        """異常系: 不正な見出しレベルの検証確認"""
        # 既存のvalidate_astがh0, h6を不正と判定するかテストするため、
        # 実際にh6ノードで確認（仕様上h6は不正）
        valid_heading = Node(type="h1", content="Valid heading")
        # h0は範囲外だが、is_heading()でFalseになるため、見出しレベルチェックされない

        # 実際の実装確認のため、見出しレベル6を持つカスタムノードを作成
        class CustomNode(Node):
            def is_heading(self):
                return self.type in {'h1', 'h6'}  # h6も見出しとして認識

            def get_heading_level(self):
                if self.type == 'h1':
                    return 1
                elif self.type == 'h6':
                    return 6  # 不正レベル
                return super().get_heading_level()

        custom_valid = CustomNode(type="h1", content="Valid")
        custom_invalid = CustomNode(type="h6", content="Invalid")

        nodes = [custom_valid, custom_invalid]
        issues = validate_ast(nodes)

        # h6の不正レベルのみエラーになる
        assert len(issues) == 1
        assert "has invalid heading level: 6" in issues[0]

    def test_境界値_複合エラー(self):
        """境界値: 複数の問題を含むASTの検証確認"""
        nodes = [
            "not a node",  # 非Node要素
            Node(type="", content="Empty type"),  # 空タイプ
            Node(type="div", content=None),  # Noneコンテンツ
            Node(type="p", content="Valid")  # 正常
        ]
        issues = validate_ast(nodes)

        assert len(issues) == 3
        assert any("not a Node instance" in issue for issue in issues)
        assert any("empty type" in issue for issue in issues)
        assert any("None content" in issue for issue in issues)

    def test_境界値_空リスト(self):
        """境界値: 空リストの検証確認"""
        issues = validate_ast([])
        assert issues == []

    def test_正常系_有効見出しレベル(self):
        """正常系: 有効な見出しレベルの検証確認"""
        nodes = [
            Node(type="h1", content="H1"),
            Node(type="h2", content="H2"),
            Node(type="h3", content="H3"),
            Node(type="h4", content="H4"),
            Node(type="h5", content="H5")
        ]
        issues = validate_ast(nodes)

        # 有効な見出しレベル（1-5）は全てエラーなし
        assert issues == []


class TestUtilitiesIntegration:
    """ユーティリティ統合テスト"""

    def test_統合_完全ASTワークフロー(self):
        """統合: AST作成→検証→操作の完全フロー確認"""
        # 1. AST構造作成
        heading = Node(type="h1", content="Document Title")
        paragraph = Node(type="p", content=["Text with ", Node(type="strong", content="formatting")])
        container = Node(type="div", content=[heading, paragraph])

        ast_nodes = [container]

        # 2. AST検証
        issues = validate_ast(ast_nodes)
        assert issues == []

        # 3. 見出し検索
        headings = find_all_headings(ast_nodes)
        assert len(headings) == 1
        assert headings[0].content == "Document Title"

        # 4. ノードタイプカウント（walk()で全ノードを収集）
        all_nodes = list(container.walk())
        counts = count_nodes_by_type(all_nodes)
        assert counts["div"] == 1
        assert counts["h1"] == 1
        assert counts["p"] == 1
        assert counts["strong"] == 1

        # 5. テキストノード統合
        flattened = flatten_text_nodes(paragraph.content)
        assert len(flattened) == 2
        assert flattened[0] == "Text with "
        assert isinstance(flattened[1], Node)

    def test_統合_大量データ処理(self):
        """統合: 大量ノードでの各種ユーティリティ動作確認"""
        # 100個のノードを含む大量データ作成
        nodes = []
        for i in range(100):
            if i % 10 == 0:
                nodes.append(Node(type="h2", content=f"Heading {i//10 + 1}"))
            else:
                nodes.append(Node(type="p", content=f"Paragraph {i}"))

        # 検証
        issues = validate_ast(nodes)
        assert issues == []

        # タイプカウント
        counts = count_nodes_by_type(nodes)
        assert counts["h2"] == 10  # 0, 10, 20, ..., 90
        assert counts["p"] == 90

        # 見出し検索
        headings = find_all_headings(nodes)
        assert len(headings) == 10

        # テキストノード統合（大量文字列データ）
        large_content = [f"Part {i} " for i in range(50)]
        flattened = flatten_text_nodes(large_content)
        assert len(flattened) == 1
        assert "Part 0" in flattened[0] and "Part 49" in flattened[0]

    def test_統合_エラー処理相互作用(self):
        """統合: 各ユーティリティ間でのエラー処理確認"""
        # 意図的に問題のあるAST構造
        problematic_nodes = [
            "not a node",
            Node(type="", content="empty type"),
            Node(type="h1", content="valid heading"),
            Node(type="div", content=None)
        ]

        # 検証は問題を検出
        issues = validate_ast(problematic_nodes)
        assert len(issues) >= 3

        # 他の関数は堅牢に動作
        counts = count_nodes_by_type(problematic_nodes)
        assert counts.get("", 0) == 1  # 空タイプもカウント
        assert counts.get("h1", 0) == 1
        assert counts.get("div", 0) == 1

        headings = find_all_headings(problematic_nodes)
        assert len(headings) == 1  # 有効な見出しのみ検索

        # テキスト統合は型安全
        mixed_content = ["text", None, "more text"]
        flattened = flatten_text_nodes(mixed_content)
        assert len(flattened) == 3  # Noneもそのまま保持

    def test_統合_空データ処理(self):
        """統合: 各種空データでの堅牢性確認"""
        # 空リストでの全関数テスト
        assert validate_ast([]) == []
        assert count_nodes_by_type([]) == {}
        assert find_all_headings([]) == []
        assert flatten_text_nodes([]) == []

        # None入力での処理
        assert flatten_text_nodes(None) is None

        # 空コンテンツノードでの処理
        empty_node = Node(type="div", content="")
        assert validate_ast([empty_node]) == []  # 空コンテンツは有効
        assert count_nodes_by_type([empty_node])["div"] == 1
        assert find_all_headings([empty_node]) == []

    def test_統合_パフォーマンス指標(self):
        """統合: パフォーマンス関連の基本指標確認"""
        # 中規模データでの処理時間測定（基本的な動作確認）
        import time

        # テストデータ作成
        nodes = []
        for i in range(50):
            content = [f"Text part {j}" for j in range(5)]  # 各ノードに5個のテキスト要素
            nodes.append(Node(type="p", content=content))

        start_time = time.time()

        # 全ユーティリティ実行
        validate_ast(nodes)
        count_nodes_by_type(nodes)
        find_all_headings(nodes)

        for node in nodes:
            flatten_text_nodes(node.content)

        end_time = time.time()
        execution_time = end_time - start_time

        # 1秒以内で完了することを確認（基本的なパフォーマンステスト）
        assert execution_time < 1.0, f"Processing took too long: {execution_time:.3f}s"

        logger.info(f"Performance test completed in {execution_time:.3f} seconds")
