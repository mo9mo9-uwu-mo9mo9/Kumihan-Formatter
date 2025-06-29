"""目次（TOC）機能のテストケース"""

import pytest
from kumihan_formatter.parser import parse
from kumihan_formatter.renderer import render


class TestTOCFeature:
    """目次機能のテストクラス"""
    
    def test_toc_marker_parsing(self):
        """目次マーカーのパーステスト"""
        text = ";;;目次;;;"
        ast = parse(text)
        
        assert len(ast) == 1
        assert ast[0].type == "toc"
        assert ast[0].content == ""
    
    def test_heading_id_assignment(self):
        """見出しへのID自動付与テスト"""
        text = """;;;見出し1
タイトル
;;;

;;;見出し2
サブタイトル
;;;

通常のテキスト

;;;見出し3
セクション
;;;"""
        
        ast = parse(text)
        heading_nodes = [node for node in ast if node.type.startswith("h")]
        
        assert len(heading_nodes) == 3
        assert heading_nodes[0].attributes.get("id") == "heading-1"
        assert heading_nodes[1].attributes.get("id") == "heading-2"
        assert heading_nodes[2].attributes.get("id") == "heading-3"
    
    def test_compound_heading_id(self):
        """複合見出しへのID付与テスト"""
        text = """;;;見出し2+太字
重要なセクション
;;;"""
        
        ast = parse(text)
        # 複合ブロックの場合、最外側のノードを確認
        assert ast[0].type == "h2"
        assert ast[0].attributes.get("id") == "heading-1"
    
    def test_toc_generation(self):
        """目次HTML生成テスト"""
        text = """;;;目次;;;

;;;見出し1
第1章
;;;

本文テキスト

;;;見出し2
セクション1.1
;;;

;;;見出し2
セクション1.2
;;;

;;;見出し3
サブセクション
;;;"""
        
        ast = parse(text)
        html = render(ast)
        
        # 目次が生成されていることを確認
        assert '<aside class="toc-sidebar' in html
        assert '<nav class="toc-content">' in html
        assert '<ul class="toc-list">' in html
        
        # 見出しへのリンクを確認
        assert '<a href="#heading-1">第1章</a>' in html
        assert '<a href="#heading-2">セクション1.1</a>' in html
        assert '<a href="#heading-3">セクション1.2</a>' in html
        assert '<a href="#heading-4">サブセクション</a>' in html
        
        # 見出し要素にIDが付与されていることを確認
        assert '<h1 id="heading-1">第1章</h1>' in html
        assert '<h2 id="heading-2">セクション1.1</h2>' in html
    
    def test_no_toc_marker(self):
        """目次マーカーがない場合のテスト"""
        text = """;;;見出し1
タイトル
;;;

本文"""
        
        ast = parse(text)
        html = render(ast)
        
        # 目次が生成されていないことを確認
        assert '<aside class="toc-sidebar' not in html
        assert 'layout-wrapper' not in html
        
        # 通常のコンテナレイアウトを確認
        assert '<div class="container">' in html
    
    def test_toc_with_nested_headings(self):
        """ネストされた見出しの目次テスト"""
        text = """;;;目次;;;

;;;見出し1
大見出し
;;;

;;;見出し2
中見出し1
;;;

;;;見出し3
小見出し1
;;;

;;;見出し3
小見出し2
;;;

;;;見出し2
中見出し2
;;;"""
        
        ast = parse(text)
        html = render(ast)
        
        # ネストされたリスト構造を確認
        assert '<ul class="toc-list">' in html
        assert html.count('<ul>') >= 2  # ネストされたul要素
    
    def test_toc_javascript_toggle(self):
        """JavaScriptトグル機能の存在確認"""
        text = """;;;目次;;;

;;;見出し1
テスト
;;;"""
        
        ast = parse(text)
        html = render(ast)
        
        # JavaScriptコードの存在を確認
        assert 'toc-toggle' in html
        assert 'localStorage' in html
        assert 'updateActiveLink' in html
        assert 'scroll-behavior: smooth' in html
    
    def test_empty_toc(self):
        """見出しがない場合の目次テスト"""
        text = """;;;目次;;;

これは通常のテキストです。
見出しはありません。"""
        
        ast = parse(text)
        html = render(ast)
        
        # 目次コンテナは存在するが、リストは空
        assert '<aside class="toc-sidebar' in html
        # 目次リストが空でないことを確認（少なくともulタグは存在）
        assert '<ul class="toc-list">' in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])