"""AST Node core functionality tests

This module provides comprehensive testing for the Node class,
covering initialization, attributes, children, classification,
and content operations.
"""

from typing import Any

import pytest

from kumihan_formatter.core.ast_nodes.node import Node
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestNodeInitialization:
    """Nodeクラス初期化テスト"""

    def test_正常系_基本初期化(self):
        """正常系: Node基本初期化確認"""
        node = Node(type="p", content="test content")

        assert node.type == "p"
        assert node.content == "test content"
        assert node.attributes == {}
        assert node.children == []

    def test_正常系_post_init動作(self):
        """正常系: __post_init__の適切な動作確認"""
        # attributes=Noneで初期化
        node = Node(type="div", content="", attributes=None, children=None)

        # __post_init__により空の辞書・リストに初期化される
        assert node.attributes == {}
        assert node.children == []

    def test_境界値_None値初期化(self):
        """境界値: attributes/children=Noneでの初期化"""
        node = Node(type="span", content="", attributes=None, children=None)

        # None値が適切に初期化される
        assert isinstance(node.attributes, dict)
        assert isinstance(node.children, list)
        assert len(node.attributes) == 0
        assert len(node.children) == 0

    def test_正常系_完全初期化(self):
        """正常系: 全パラメーター指定での初期化"""
        attributes = {"class": "test", "id": "test-id"}
        child_node = Node(type="em", content="child")
        children = [child_node]

        node = Node(
            type="div",
            content="parent content",
            attributes=attributes,
            children=children,
        )

        assert node.type == "div"
        assert node.content == "parent content"
        assert node.attributes == attributes
        assert node.children == children
        assert node.children[0].type == "em"


class TestNodeAttributes:
    """ノード属性操作テスト"""

    def test_正常系_属性追加取得(self):
        """正常系: add_attribute/get_attribute確認"""
        node = Node(type="p", content="")

        # 属性追加
        node.add_attribute("class", "highlight")
        node.add_attribute("data-value", "test")

        # 属性取得
        assert node.get_attribute("class") == "highlight"
        assert node.get_attribute("data-value") == "test"
        assert node.get_attribute("nonexistent") is None
        assert node.get_attribute("nonexistent", "default") == "default"

    def test_正常系_属性存在判定(self):
        """正常系: has_attribute確認"""
        node = Node(type="div", content="")

        # 属性なし
        assert not node.has_attribute("class")

        # 属性追加後
        node.add_attribute("class", "box")
        assert node.has_attribute("class")
        assert not node.has_attribute("id")

    def test_正常系_属性削除(self):
        """正常系: remove_attribute確認"""
        node = Node(type="span", content="")

        # 属性追加
        node.add_attribute("style", "color: red")
        node.add_attribute("class", "error")
        assert node.has_attribute("style")
        assert node.has_attribute("class")

        # 属性削除
        node.remove_attribute("style")
        assert not node.has_attribute("style")
        assert node.has_attribute("class")

        # 存在しない属性の削除（エラーなし）
        node.remove_attribute("nonexistent")  # エラーが発生しない

    def test_正常系_metadata互換性(self):
        """正常系: metadataプロパティ互換性確認"""
        node = Node(type="h1", content="Title")

        # metadataプロパティ経由でのアクセス
        metadata = node.metadata
        assert isinstance(metadata, dict)

        # 属性追加してmetadata経由で確認
        node.add_attribute("level", 1)
        assert node.metadata["level"] == 1

        # metadataとattributesは同じオブジェクト
        assert node.metadata is node.attributes

    def test_境界値_attributes_None状態(self):
        """境界値: attributes=None状態での操作"""
        node = Node(type="p", content="", attributes=None)
        # __post_init__で初期化されているため、以下が安全に動作

        node.add_attribute("test", "value")
        assert node.get_attribute("test") == "value"
        assert node.has_attribute("test")


class TestNodeChildren:
    """子ノード操作テスト"""

    def test_正常系_子ノード追加削除(self):
        """正常系: add_child/remove_child確認"""
        parent = Node(type="div", content="")
        child1 = Node(type="p", content="paragraph 1")
        child2 = Node(type="p", content="paragraph 2")

        # 子ノード追加
        parent.add_child(child1)
        parent.add_child(child2)

        assert len(parent.children) == 2
        assert parent.children[0] == child1
        assert parent.children[1] == child2

        # 子ノード削除
        parent.remove_child(child1)
        assert len(parent.children) == 1
        assert parent.children[0] == child2

    def test_境界値_存在しない子削除(self):
        """境界値: 存在しない子ノード削除時の処理"""
        parent = Node(type="ul", content="")
        child = Node(type="li", content="item")
        other_child = Node(type="li", content="other item")

        parent.add_child(child)

        # 存在しない子の削除（エラーなし）
        parent.remove_child(other_child)  # エラーが発生しない
        assert len(parent.children) == 1
        assert parent.children[0] == child

    def test_境界値_children_None状態(self):
        """境界値: children=None状態での操作"""
        node = Node(type="div", content="", children=None)
        child = Node(type="span", content="child")

        # __post_init__で初期化されているため、安全に操作可能
        node.add_child(child)
        assert len(node.children) == 1
        assert node.children[0] == child


class TestNodeClassification:
    """ノード分類・判定テスト"""

    def test_正常系_ブロック要素判定(self):
        """正常系: is_block_element()全パターン確認"""
        # ブロック要素
        block_types = [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "p",
            "div",
            "ul",
            "ol",
            "li",
            "blockquote",
            "pre",
            "details",
        ]

        for block_type in block_types:
            node = Node(type=block_type, content="")
            assert node.is_block_element(), f"{block_type} should be block element"

        # 非ブロック要素
        inline_node = Node(type="span", content="")
        assert not inline_node.is_block_element()

    def test_正常系_インライン要素判定(self):
        """正常系: is_inline_element()全パターン確認"""
        # インライン要素
        inline_types = ["strong", "em", "code", "span", "a"]

        for inline_type in inline_types:
            node = Node(type=inline_type, content="")
            assert node.is_inline_element(), f"{inline_type} should be inline element"

        # 非インライン要素
        block_node = Node(type="div", content="")
        assert not block_node.is_inline_element()

    def test_正常系_リスト要素判定(self):
        """正常系: is_list_element()確認"""
        # リスト要素
        list_types = ["ul", "ol", "li"]

        for list_type in list_types:
            node = Node(type=list_type, content="")
            assert node.is_list_element(), f"{list_type} should be list element"

        # 非リスト要素
        non_list_node = Node(type="p", content="")
        assert not non_list_node.is_list_element()

    def test_正常系_見出し判定(self):
        """正常系: is_heading()とget_heading_level()確認"""
        # 見出し要素
        for level in range(1, 6):  # h1-h5
            node = Node(type=f"h{level}", content="")
            assert node.is_heading(), f"h{level} should be heading"
            assert node.get_heading_level() == level

        # 非見出し要素
        non_heading = Node(type="p", content="")
        assert not non_heading.is_heading()
        assert non_heading.get_heading_level() is None

    def test_境界値_見出しレベル判定(self):
        """境界値: 見出しレベル判定の境界ケース"""
        # 不正な見出し形式
        invalid_headings = ["h0", "h6", "h10", "heading", "h"]

        for invalid_type in invalid_headings:
            node = Node(type=invalid_type, content="")
            assert not node.is_heading(), f"{invalid_type} should not be heading"
            assert node.get_heading_level() is None


class TestNodeContent:
    """ノードコンテンツ操作テスト"""

    def test_正常系_テキスト存在判定(self):
        """正常系: contains_text()各種パターン確認"""
        # 文字列コンテンツ
        text_node = Node(type="p", content="Hello World")
        assert text_node.contains_text()

        # 空文字列
        empty_node = Node(type="p", content="")
        assert not empty_node.contains_text()

        # 空白のみ
        whitespace_node = Node(type="p", content="   \n\t   ")
        assert not whitespace_node.contains_text()

        # リストコンテンツ（文字列あり）
        list_with_text = Node(type="div", content=["Hello", " ", "World"])
        assert list_with_text.contains_text()

        # リストコンテンツ（ノードあり）
        child_node = Node(type="span", content="text")
        list_with_node = Node(type="div", content=[child_node])
        assert list_with_node.contains_text()

    def test_正常系_テキスト抽出(self):
        """正常系: get_text_content()確認"""
        # 文字列コンテンツ
        text_node = Node(type="p", content="Simple text")
        assert text_node.get_text_content() == "Simple text"

        # リストコンテンツ（混合）
        child_node = Node(type="em", content="emphasized")
        mixed_content = Node(type="p", content=["Hello ", child_node, " world"])
        # " ".join()により各要素間にスペースが挿入される
        assert mixed_content.get_text_content() == "Hello  emphasized  world"

        # 空コンテンツ
        empty_node = Node(type="div", content="")
        assert empty_node.get_text_content() == ""

    def test_正常系_子数カウント(self):
        """正常系: count_children()確認"""
        # リストコンテンツ
        list_content = Node(type="ul", content=["item1", "item2", "item3"])
        assert list_content.count_children() == 3

        # 文字列コンテンツ
        text_content = Node(type="p", content="single text")
        assert text_content.count_children() == 0

        # 空リスト
        empty_list = Node(type="div", content=[])
        assert empty_list.count_children() == 0

    def test_正常系_タイプ別子検索(self):
        """正常系: find_children_by_type()確認"""
        # 混合コンテンツ
        child1 = Node(type="p", content="paragraph")
        child2 = Node(type="span", content="span")
        child3 = Node(type="p", content="another paragraph")

        parent = Node(type="div", content=[child1, "text", child2, child3])

        # p要素の検索
        p_children = parent.find_children_by_type("p")
        assert len(p_children) == 2
        assert p_children[0] == child1
        assert p_children[1] == child3

        # span要素の検索
        span_children = parent.find_children_by_type("span")
        assert len(span_children) == 1
        assert span_children[0] == child2

        # 存在しない要素の検索
        div_children = parent.find_children_by_type("div")
        assert len(div_children) == 0

    def test_正常系_ノード走査(self):
        """正常系: walk()ジェネレーター確認"""
        # ネストした構造の作成
        grandchild = Node(type="em", content="emphasis")
        child = Node(type="p", content=[grandchild])
        parent = Node(type="div", content=[child])

        # 走査結果の収集
        nodes = list(parent.walk())

        # 親、子、孫の順で走査される
        assert len(nodes) == 3
        assert nodes[0] == parent
        assert nodes[1] == child
        assert nodes[2] == grandchild

    def test_境界値_walk_単一ノード(self):
        """境界値: walk()での単一ノード走査"""
        single_node = Node(type="span", content="single")
        nodes = list(single_node.walk())

        assert len(nodes) == 1
        assert nodes[0] == single_node

    def test_境界値_find_children_非リストコンテンツ(self):
        """境界値: find_children_by_type()での非リストコンテンツ"""
        text_node = Node(type="p", content="plain text")
        children = text_node.find_children_by_type("span")

        assert len(children) == 0
