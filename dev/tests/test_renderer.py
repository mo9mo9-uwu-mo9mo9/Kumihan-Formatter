"""レンダラーのテスト"""

import pytest
from kumihan_formatter.renderer import render
from kumihan_formatter.parser import Node


def test_render_empty():
    """空のASTのレンダリング"""
    result = render([])
    assert "<html" in result  # DOCTYPE宣言があるため
    assert "<body>" in result


def test_render_paragraph():
    """段落のレンダリング"""
    ast = [
        Node(type="p", content=["これはテスト段落です。"])
    ]
    result = render(ast)
    assert "<p>これはテスト段落です。</p>" in result


def test_render_list():
    """リストのレンダリング"""
    ast = [
        Node(type="ul", content=[
            Node(type="li", content=["項目1"]),
            Node(type="li", content=["項目2"])
        ])
    ]
    result = render(ast)
    assert "<ul>" in result
    assert "<li>項目1</li>" in result
    assert "<li>項目2</li>" in result
    assert "</ul>" in result


def test_render_with_attributes():
    """属性付きノードのレンダリング"""
    ast = [
        Node(type="div", content=["テスト"], attributes={"class": "box"})
    ]
    result = render(ast)
    assert '<div class="box">テスト</div>' in result


def test_render_error():
    """エラーノードのレンダリング"""
    ast = [
        Node(type="error", content="エラー内容", attributes={"message": "テストエラー", "line": 5})
    ]
    result = render(ast)
    assert "background-color:#ffe6e6" in result
    assert "[ERROR: テストエラー]" in result
    assert "(行: 5)" in result


def test_render_numbered_list():
    """番号付きリストのレンダリング"""
    ast = [
        Node(type="ol", content=[
            Node(type="li", content=["項目1"]),
            Node(type="li", content=["項目2"]),
            Node(type="li", content=["項目3"])
        ])
    ]
    result = render(ast)
    assert "<ol>" in result
    assert "<li>項目1</li>" in result
    assert "<li>項目2</li>" in result
    assert "<li>項目3</li>" in result
    assert "</ol>" in result


def test_render_numbered_list_in_block():
    """ブロック内番号付きリストのレンダリング"""
    ast = [
        Node(type="div", 
             content=["1. ブロック内項目1\n2. ブロック内項目2"],
             attributes={"class": "box", "contains_list": True})
    ]
    result = render(ast)
    assert '<div class="box">' in result
    assert "<ol>" in result
    assert "<li>ブロック内項目1</li>" in result
    assert "<li>ブロック内項目2</li>" in result
    assert "</ol>" in result
    assert "</div>" in result


def test_render_mixed_lists_in_block():
    """ブロック内混在リストのレンダリング"""
    ast = [
        Node(type="div", 
             content=["- 箇条書き項目1\n- 箇条書き項目2\n\n1. 番号付き項目1\n2. 番号付き項目2"],
             attributes={"class": "box", "contains_list": True})
    ]
    result = render(ast)
    assert '<div class="box">' in result
    assert "<ul>" in result
    assert "<ol>" in result
    assert "<li>箇条書き項目1</li>" in result
    assert "<li>番号付き項目1</li>" in result
    assert "</div>" in result