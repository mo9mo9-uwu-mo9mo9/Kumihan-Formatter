"""
SimpleKumihanParser テスト
"""

import pytest
from kumihan_formatter.simple_parser import SimpleKumihanParser


class TestSimpleKumihanParser:
    """SimpleKumihanParser テストクラス"""
    
    def setup_method(self):
        self.parser = SimpleKumihanParser()
    
    def test_parse_basic_kumihan_block(self):
        """基本的なKumihanブロックの解析テスト"""
        text = "# 重要 #これは重要な情報です##"
        result = self.parser.parse(text)
        
        assert result["status"] == "success"
        assert result["total_elements"] >= 1
        
        elements = result["elements"]
        kumihan_block = next((e for e in elements if e["type"] == "kumihan_block"), None)
        assert kumihan_block is not None
        assert kumihan_block["content"] == "これは重要な情報です"
        assert kumihan_block["attributes"]["decoration"] == "重要"
    
    def test_parse_heading(self):
        """見出しの解析テスト"""
        text = "## 見出しレベル2"
        result = self.parser.parse(text)
        
        assert result["status"] == "success"
        elements = result["elements"]
        
        heading = next((e for e in elements if e["type"] == "heading_2"), None)
        assert heading is not None
        assert heading["content"] == "見出しレベル2"
        assert heading["attributes"]["level"] == "2"
    
    def test_parse_list_items(self):
        """リストアイテムの解析テスト"""
        text = """- リスト項目1
- リスト項目2"""
        result = self.parser.parse(text)
        
        assert result["status"] == "success"
        elements = result["elements"]
        
        list_items = [e for e in elements if e["type"] == "list_item"]
        assert len(list_items) == 2
        assert list_items[0]["content"] == "リスト項目1"
        assert list_items[0]["attributes"]["list_type"] == "unordered"
    
    def test_parse_numbered_list(self):
        """番号付きリストの解析テスト"""
        text = """1. 番号付き項目1
2. 番号付き項目2"""
        result = self.parser.parse(text)
        
        assert result["status"] == "success"
        elements = result["elements"]
        
        list_items = [e for e in elements if e["type"] == "list_item"]
        numbered_items = [e for e in list_items if e["attributes"]["list_type"] == "ordered"]
        assert len(numbered_items) == 2
    
    def test_parse_paragraph(self):
        """段落の解析テスト"""
        text = "これは通常の段落です。"
        result = self.parser.parse(text)
        
        assert result["status"] == "success"
        elements = result["elements"]
        
        paragraph = next((e for e in elements if e["type"] == "paragraph"), None)
        assert paragraph is not None
        assert "これは通常の段落です。" in paragraph["content"]
    
    def test_inline_formatting(self):
        """インライン装飾のテスト"""
        text = "これは**太字**と*イタリック*の例です。"
        result = self.parser._process_inline_formatting(text)
        
        assert "<strong>太字</strong>" in result
        assert "<em>イタリック</em>" in result
    
    def test_validate_syntax(self):
        """構文検証のテスト"""
        # 正常なKumihan記法
        valid_text = "# 重要 #内容##"
        errors = self.parser.validate(valid_text)
        assert len(errors) == 0
        
        # 空の装飾名
        invalid_text1 = "#  #内容##"
        errors1 = self.parser.validate(invalid_text1)
        assert len(errors1) > 0
        
        # 空の内容（スペースのみ）
        invalid_text2 = "# 重要 #  ##"
        errors2 = self.parser.validate(invalid_text2)
        assert len(errors2) > 0
    
    def test_empty_input(self):
        """空の入力のテスト"""
        result = self.parser.parse("")
        assert result["status"] == "success"
        assert result["total_elements"] == 0
    
    def test_complex_document(self, sample_text):
        """複雑な文書の解析テスト"""
        result = self.parser.parse(sample_text)
        
        assert result["status"] == "success"
        assert result["total_elements"] > 5
        
        elements = result["elements"]
        types = [e["type"] for e in elements]
        
        # 様々な要素タイプが含まれていることを確認
        assert "kumihan_block" in types
        assert "heading_2" in types
        assert "paragraph" in types
        assert "list_item" in types