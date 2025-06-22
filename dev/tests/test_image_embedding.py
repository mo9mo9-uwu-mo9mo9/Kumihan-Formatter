"""画像埋め込み機能のテスト"""

import tempfile
import shutil
from pathlib import Path
import pytest
from kumihan_formatter.parser import parse
from kumihan_formatter.renderer import render


class TestImageEmbedding:
    """画像埋め込み機能のテストクラス"""
    
    def test_simple_image_syntax(self):
        """単純な画像記法のテスト"""
        text = ";;;test.png;;;"
        ast = parse(text)
        
        assert len(ast) == 1
        assert ast[0].type == "image"
        assert ast[0].content == "test.png"
        assert ast[0].attributes.get("alt") == "test.png"
    
    def test_image_with_text(self):
        """画像とテキストの混在テスト"""
        text = """これは画像のテストです。

;;;sample.jpg;;;

画像の後のテキストです。"""
        ast = parse(text)
        
        assert len(ast) == 3
        assert ast[0].type == "p"
        assert ast[1].type == "image"
        assert ast[1].content == "sample.jpg"
        assert ast[2].type == "p"
    
    def test_multiple_images(self):
        """複数画像のテスト"""
        text = """;;;image1.png;;;

何かテキスト

;;;image2.jpeg;;;

;;;image3.gif;;;"""
        ast = parse(text)
        
        # 画像ノードを抽出
        image_nodes = [node for node in ast if node.type == "image"]
        assert len(image_nodes) == 3
        assert image_nodes[0].content == "image1.png"
        assert image_nodes[1].content == "image2.jpeg"
        assert image_nodes[2].content == "image3.gif"
    
    def test_image_extensions(self):
        """対応している画像拡張子のテスト"""
        extensions = ["png", "jpg", "jpeg", "gif", "webp", "svg"]
        
        for ext in extensions:
            text = f";;;test.{ext};;;"
            ast = parse(text)
            assert len(ast) == 1
            assert ast[0].type == "image"
            assert ast[0].content == f"test.{ext}"
    
    def test_invalid_image_syntax(self):
        """無効な画像記法のテスト"""
        # 拡張子が画像でない場合は通常のブロックとして扱われる
        text = ";;;test.txt;;;"
        ast = parse(text)
        
        # エラーノードになることを確認
        assert len(ast) == 1
        assert ast[0].type == "error"
    
    def test_image_rendering(self):
        """画像のHTMLレンダリングテスト"""
        text = ";;;photo.jpg;;;"
        ast = parse(text)
        html = render(ast)
        
        # HTMLにimgタグが含まれることを確認
        assert '<img src="images/photo.jpg" alt="photo.jpg" />' in html
    
    def test_image_with_special_characters(self):
        """特殊文字を含むファイル名のテスト"""
        # アンダースコア、ハイフンを含むファイル名
        text = ";;;test_image-001.png;;;"
        ast = parse(text)
        
        assert len(ast) == 1
        assert ast[0].type == "image"
        assert ast[0].content == "test_image-001.png"
    
    def test_image_path_security(self):
        """パストラバーサル攻撃の防止テスト"""
        # パス区切り文字を含む場合は画像として認識しない
        dangerous_patterns = [
            ";;;../../../etc/passwd;;;",
            ";;;images/../../secret.png;;;",
            ";;;C:\\Windows\\System32\\file.png;;;",
            ";;;/etc/passwd;;;"
        ]
        
        for pattern in dangerous_patterns:
            ast = parse(pattern)
            # 画像として認識されないことを確認
            image_nodes = [node for node in ast if node.type == "image"]
            assert len(image_nodes) == 0
    
    def test_mixed_content_rendering(self):
        """複合コンテンツのレンダリングテスト"""
        text = """# 画像埋め込みテスト

これはテストドキュメントです。

;;;枠線
重要な情報
;;;

;;;demo.png;;;

- リスト項目1
- リスト項目2

;;;highlight.jpg;;;

最後のテキスト"""
        
        ast = parse(text)
        html = render(ast)
        
        # 各要素が正しくレンダリングされることを確認
        assert '<img src="images/demo.png" alt="demo.png" />' in html
        assert '<img src="images/highlight.jpg" alt="highlight.jpg" />' in html
        assert '<div class="box">' in html
        assert '<ul>' in html
        assert '<li>' in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])