"""AST Factory functions comprehensive tests

This module provides comprehensive testing for factory functions
in the factories module, covering all node creation patterns
and NodeBuilder integration.
"""

from typing import Any

import pytest

from kumihan_formatter.core.ast_nodes.factories import (
    create_node,
    details,
    div_box,
    emphasis,
    error_node,
    heading,
    highlight,
    image_node,
    list_item,
    ordered_list,
    paragraph,
    strong,
    toc_marker,
    unordered_list,
)
from kumihan_formatter.core.ast_nodes.node import Node
from kumihan_formatter.core.ast_nodes.node_builder import NodeBuilder
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestCreateNode:
    """汎用ノード作成テスト"""

    def test_正常系_基本作成(self):
        """正常系: create_node基本動作確認"""
        node = create_node("div", "test content")

        assert node.type == "div"
        assert node.content == "test content"
        assert isinstance(node.attributes, dict)

    def test_正常系_metadata設定(self):
        """正常系: metadataパラメーター確認"""
        metadata = {"class": "highlight", "data-value": "test"}
        node = create_node("span", "content", metadata=metadata)

        assert node.get_attribute("class") == "highlight"
        assert node.get_attribute("data-value") == "test"

    def test_正常系_kwargs属性設定(self):
        """正常系: **kwargs属性設定確認"""
        node = create_node(
            "p",
            "paragraph",
            id="test-id",
            style="color: red",
            custom_attr="custom_value",
        )

        assert node.get_attribute("id") == "test-id"
        assert node.get_attribute("style") == "color: red"
        assert node.get_attribute("custom_attr") == "custom_value"

    def test_正常系_metadata_kwargs併用(self):
        """正常系: metadataとkwargsの併用"""
        metadata = {"class": "box"}
        node = create_node(
            "div",
            "content",
            metadata=metadata,
            id="combined-test",
            data_source="kwargs",
        )

        # metadataからの属性
        assert node.get_attribute("class") == "box"
        # kwargsからの属性
        assert node.get_attribute("id") == "combined-test"
        assert node.get_attribute("data_source") == "kwargs"

    def test_境界値_空コンテンツ(self):
        """境界値: 空コンテンツでの作成"""
        node = create_node("div")

        assert node.type == "div"
        assert node.content == ""
        assert isinstance(node.attributes, dict)


class TestBasicFactories:
    """基本ファクトリー関数テスト"""

    def test_正常系_paragraph作成(self):
        """正常系: paragraph()確認"""
        # 文字列コンテンツ
        p1 = paragraph("Simple paragraph")
        assert p1.type == "paragraph"
        assert p1.content == "Simple paragraph"

        # 属性付き
        attrs = {"class": "intro", "id": "p1"}
        p2 = paragraph("Paragraph with attributes", attributes=attrs)
        assert p2.get_attribute("class") == "intro"
        assert p2.get_attribute("id") == "p1"

        # リストコンテンツ
        p3 = paragraph(["Text with ", strong("bold"), " formatting"])
        assert isinstance(p3.content, list)
        assert len(p3.content) == 3

    def test_正常系_heading作成(self):
        """正常系: heading()全レベル確認"""
        for level in range(1, 6):  # h1-h5
            h = heading(level, f"Heading Level {level}")

            assert h.type == f"h{level}"
            assert h.content == f"Heading Level {level}"
            assert h.is_heading()
            assert h.get_heading_level() == level

        # 属性付き見出し
        h_with_attrs = heading(2, "Title", attributes={"id": "title"})
        assert h_with_attrs.type == "h2"
        assert h_with_attrs.get_attribute("id") == "title"

    def test_正常系_strong_emphasis作成(self):
        """正常系: strong()/emphasis()確認"""
        # strong要素
        strong_node = strong("Bold text")
        assert strong_node.type == "strong"
        assert strong_node.content == "Bold text"
        assert strong_node.is_inline_element()

        # emphasis要素
        em_node = emphasis("Italic text")
        assert em_node.type == "em"
        assert em_node.content == "Italic text"
        assert em_node.is_inline_element()

        # リストコンテンツ
        strong_list = strong(["Bold ", emphasis("and italic")])
        assert isinstance(strong_list.content, list)
        assert len(strong_list.content) == 2

    def test_境界値_heading_レベル境界(self):
        """境界値: heading()のレベル境界値"""
        # 有効範囲
        h1 = heading(1, "H1")
        h5 = heading(5, "H5")

        assert h1.type == "h1"
        assert h5.type == "h5"

        # 範囲外レベル（ファクトリーは作成するが、分類では適切に処理される）
        h0 = heading(0, "H0")  # h0として作成される
        h6 = heading(6, "H6")  # h6として作成される

        assert h0.type == "h0"
        assert h6.type == "h6"
        # 分類メソッドでは正しく処理される
        assert not h0.is_heading()
        assert not h6.is_heading()


class TestSpecialFactories:
    """特殊ファクトリー関数テスト"""

    def test_正常系_div_box作成(self):
        """正常系: div_box()確認"""
        box = div_box("Box content")

        assert box.type == "div"
        assert box.content == "Box content"
        assert box.get_attribute("class") == "box"
        assert box.is_block_element()

    def test_正常系_highlight作成(self):
        """正常系: highlight()色指定確認"""
        # 色指定なし
        highlight1 = highlight("Highlighted text")
        assert highlight1.type == "div"
        assert highlight1.content == "Highlighted text"
        assert highlight1.get_attribute("class") == "highlight"
        assert not highlight1.has_attribute("style")

        # 色指定あり
        highlight2 = highlight("Yellow highlight", color="yellow")
        assert highlight2.get_attribute("class") == "highlight"
        assert highlight2.get_attribute("style") == "background-color:yellow"

        # カスタム色
        highlight3 = highlight("Custom color", color="#ff6b6b")
        assert highlight3.get_attribute("style") == "background-color:#ff6b6b"

    def test_正常系_リスト作成(self):
        """正常系: unordered_list/ordered_list/list_item確認"""
        # リスト項目作成
        item1 = list_item("First item")
        item2 = list_item("Second item")
        item3 = list_item(["Item with ", strong("formatting")])

        assert item1.type == "li"
        assert item1.content == "First item"
        assert item1.is_list_element()

        # 順序なしリスト
        ul = unordered_list([item1, item2, item3])
        assert ul.type == "ul"
        assert ul.is_list_element()
        assert isinstance(ul.content, list)
        assert len(ul.content) == 3
        assert ul.content[0] == item1

        # 順序ありリスト
        ol = ordered_list([item1, item2])
        assert ol.type == "ol"
        assert ol.is_list_element()
        assert len(ol.content) == 2

    def test_正常系_details作成(self):
        """正常系: details()確認"""
        details_node = details("Summary text", "Detailed content")

        assert details_node.type == "details"
        assert details_node.content == "Detailed content"
        assert details_node.get_attribute("summary") == "Summary text"
        assert details_node.is_block_element()

        # リストコンテンツ
        details_list = details("Complex", ["Content with ", emphasis("formatting")])
        assert isinstance(details_list.content, list)

    def test_境界値_リスト_空項目(self):
        """境界値: 空のリスト項目"""
        empty_item = list_item("")
        empty_ul = unordered_list([])
        empty_ol = ordered_list([])

        assert empty_item.content == ""
        assert len(empty_ul.content) == 0
        assert len(empty_ol.content) == 0


class TestUtilityFactories:
    """ユーティリティファクトリーテスト"""

    def test_正常系_error_node作成(self):
        """正常系: error_node()確認"""
        # 基本エラーノード
        error1 = error_node("Parse error occurred")
        assert error1.type == "error"
        assert error1.content == "Parse error occurred"
        assert not error1.has_attribute("line")

        # 行番号付きエラーノード
        error2 = error_node("Syntax error", line_number=42)
        assert error2.content == "Syntax error"
        assert error2.get_attribute("line") == 42

    def test_正常系_image_node作成(self):
        """正常系: image_node()確認"""
        # ファイル名のみ
        img1 = image_node("photo.jpg")
        assert img1.type == "image"
        assert img1.content == "photo.jpg"
        assert not img1.has_attribute("alt")

        # alt属性付き
        img2 = image_node("diagram.png", alt_text="System diagram")
        assert img2.content == "diagram.png"
        assert img2.get_attribute("alt") == "System diagram"

    def test_正常系_toc_marker作成(self):
        """正常系: toc_marker()廃止予定機能確認"""
        # Issue #799: 廃止予定機能のテスト
        toc = toc_marker()

        assert toc.type == "toc"
        assert toc.content == "<!-- TOC Auto-Generated -->"

        # 廃止予定であることを警告として記録
        logger.warning("toc_marker() is deprecated as per Issue #799")

    def test_境界値_error_node_行番号None(self):
        """境界値: error_node()での行番号None指定"""
        error = error_node("Error message", line_number=None)

        assert error.content == "Error message"
        assert not error.has_attribute("line")

    def test_境界値_image_node_空alt(self):
        """境界値: image_node()での空alt属性"""
        img = image_node("test.jpg", alt_text="")

        assert img.content == "test.jpg"
        # 空文字列のalt_textは`if alt_text:`で False となるため属性は設定されない
        assert not img.has_attribute("alt")


class TestFactoriesIntegration:
    """ファクトリー統合テスト"""

    def test_統合_複雑なノード構造作成(self):
        """統合: 複雑なASTツリー構築確認"""
        # ネストした複雑な構造を作成
        title = heading(1, "Document Title")
        intro = paragraph(["Introduction with ", strong("important"), " information."])

        # リスト構造
        list_items = [
            list_item("First point"),
            list_item(["Second point with ", emphasis("emphasis")]),
            list_item("Third point"),
        ]
        main_list = unordered_list(list_items)

        # 詳細セクション
        detail_content = [
            paragraph("Detailed explanation here."),
            highlight("Important note", color="yellow"),
        ]
        details_section = details("Click for details", detail_content)

        # すべての要素が正しく作成されている
        assert title.is_heading()
        assert intro.type == "paragraph"
        assert main_list.is_list_element()
        assert len(main_list.content) == 3
        assert details_section.is_block_element()

        # ネストした内容の確認
        assert isinstance(intro.content, list)
        assert intro.content[1].type == "strong"  # "important"部分

        # リスト項目の確認
        second_item = list_items[1]
        assert isinstance(second_item.content, list)
        assert second_item.content[1].type == "em"  # emphasis部分

    def test_統合_NodeBuilder連携(self):
        """統合: NodeBuilderとの連携確認"""
        # 手動でNodeBuilderを使用
        manual_node = (
            NodeBuilder("div")
            .content("Manual content")
            .css_class("manual")
            .id("manual-id")
            .build()
        )

        # ファクトリー関数を使用
        factory_node = div_box("Factory content")

        # 両方とも正常に作成される
        assert manual_node.type == "div"
        assert manual_node.content == "Manual content"
        assert manual_node.get_attribute("class") == "manual"
        assert manual_node.get_attribute("id") == "manual-id"

        assert factory_node.type == "div"
        assert factory_node.content == "Factory content"
        assert factory_node.get_attribute("class") == "box"

        # 両方ともNodeインスタンス
        assert isinstance(manual_node, Node)
        assert isinstance(factory_node, Node)

    def test_統合_ファクトリー間相互作用(self):
        """統合: 異なるファクトリー関数の組み合わせ"""
        # 段落内で複数のインライン要素を組み合わせ
        complex_paragraph = paragraph(
            [
                "This is a ",
                strong("very important"),
                " message with ",
                emphasis("emphasis"),
                " and formatting.",
            ]
        )

        # エラーノードを含む構造
        error_with_context = div_box(
            [
                error_node("Validation failed", line_number=15),
                paragraph("Please check the input and try again."),
            ]
        )

        # 画像を含むリスト項目
        image_item = list_item(
            ["See diagram: ", image_node("workflow.png", alt_text="Workflow diagram")]
        )

        # すべてが正常に作成される
        assert complex_paragraph.type == "paragraph"
        assert len(complex_paragraph.content) == 5

        assert error_with_context.get_attribute("class") == "box"
        assert isinstance(error_with_context.content, list)
        assert error_with_context.content[0].type == "error"

        assert image_item.type == "li"
        assert image_item.content[1].type == "image"

    def test_境界値_ファクトリー_型混在(self):
        """境界値: ファクトリー関数での型混在コンテンツ"""
        # 文字列とNodeを混在させたコンテンツ
        mixed_content = paragraph(
            ["Start ", strong("bold"), " middle ", 42, " end"]  # 数値
        )

        # ファクトリーは型チェックを行わず、そのまま格納
        assert len(mixed_content.content) == 5
        assert mixed_content.content[3] == 42

        # Nodeメソッドでの処理確認
        text_content = mixed_content.get_text_content()
        assert "bold" in text_content  # Nodeからのテキストは抽出される
