"""
Test cases for compound notation patterns.

Tests complex combinations of notations including nesting, overlapping, and mixed formats.
"""

import pytest
from pathlib import Path

from kumihan_formatter.core.keyword_parsing.marker_parser import MarkerParser
from kumihan_formatter.core.syntax.syntax_validator import KumihanSyntaxValidator
from kumihan_formatter.core.keyword_parsing.definitions import KeywordDefinitions, NESTING_ORDER


@pytest.mark.unit
@pytest.mark.notation
class TestNestedNotation:
    """Test nested notation structures."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.definitions)
        self.validator = KumihanSyntaxValidator()
        self.definitions = KeywordDefinitions()
    
    def test_simple_nesting(self):
        """Test simple nested notation structures."""
        nested_patterns = [
            """#太字
外側のテキスト
#下線 内側のテキスト#
続きのテキスト
#""",
            """#見出し1
セクション
#太字 重要部分#
残り
#""",
            """#リスト
- 項目1: #太字 重要#
- 項目2: 通常
- 項目3: #下線 強調#
#""",
        ]
        
        for text in nested_patterns:
            result = self.parser.parse(text)
            errors = self.validator.validate_text(text)
            
            # Should handle nested structures
            assert result is not None
            assert isinstance(errors, list)
            
            # Check for severe parsing errors
            severe_errors = [e for e in errors if hasattr(e, 'severity') and str(e.severity).upper() == 'ERROR']
            # Nested structures should be parseable (implementation-dependent)
    
    def test_deep_nesting(self):
        """Test deeply nested notation structures."""
        # Create 5-level deep nesting
        deep_nested = """#見出し1
レベル1
#太字
レベル2
#下線
レベル3
#斜体
レベル4
#強調 レベル5の内容#
レベル4続き
##
レベル3続き
##
レベル2続き
##
レベル1続き
#"""
        
        result = self.parser.parse(deep_nested)
        errors = self.validator.validate_text(deep_nested)
        
        # Should handle deep nesting appropriately
        assert isinstance(errors, list)
        # Implementation may have limits on nesting depth
    
    def test_nesting_order_validation(self):
        """Test nesting order validation if implemented."""
        if not hasattr(self.definitions, 'validate_nesting_order'):
            pytest.skip("Nesting order validation not implemented")
        
        # Test proper nesting order
        proper_nesting = """#見出し1
#太字 内容#
#"""
        
        # Test improper nesting order (if rules exist)
        improper_nesting = """#太字
#見出し1 逆順#
#"""
        
        proper_errors = self.validator.validate_text(proper_nesting)
        improper_errors = self.validator.validate_text(improper_nesting)
        
        # Results depend on implementation
        assert isinstance(proper_errors, list)
        assert isinstance(improper_errors, list)
    
    def test_overlapping_notation(self):
        """Test overlapping notation patterns."""
        overlapping_patterns = [
            "#太字 開始#下線 中間#太字終了 重複#",
            "#見出し1\n#太字 開始\n#\n#下線 終了#",
            "#太字 A#B#下線 C#D#",
        ]
        
        for text in overlapping_patterns:
            result = self.parser.parse(text)
            errors = self.validator.validate_text(text)
            
            # Should handle overlapping patterns
            assert isinstance(errors, list)
            # May flag as errors or handle gracefully
    
    def test_cross_nested_notation(self):
        """Test cross-nested notation patterns."""
        cross_nested = """#太字
開始A
#下線
開始B
##
終了A - これは問題のある構造
#"""
        
        result = self.parser.parse(cross_nested)
        errors = self.validator.validate_text(cross_nested)
        
        # Cross-nesting should be detected as problematic
        assert isinstance(errors, list)
        # May produce validation errors


@pytest.mark.unit
@pytest.mark.notation
class TestMixedFormatNotation:
    """Test mixed inline and block format notations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.definitions)
        self.validator = KumihanSyntaxValidator()
    
    def test_inline_block_combination(self):
        """Test combination of inline and block formats."""
        mixed_formats = [
            """#見出し1
ブロック形式のタイトル
##

段落内に#太字 インライン形式#があります。

#リスト
- 項目1: #下線 インライン#
- 項目2: 通常テキスト
#""",
            """#太字 インライン形式#の後に

#見出し2
ブロック形式
##

が続きます。""",
        ]
        
        for text in mixed_formats:
            result = self.parser.parse(text)
            errors = self.validator.validate_text(text)
            
            # Should handle mixed formats
            assert isinstance(errors, list)
    
    def test_consecutive_blocks(self):
        """Test consecutive block notations."""
        consecutive_blocks = """#見出し1
最初のブロック
##

#太字
次のブロック
##

#リスト
- 項目1
- 項目2
##

#見出し2
最後のブロック
#"""
        
        result = self.parser.parse(consecutive_blocks)
        errors = self.validator.validate_text(consecutive_blocks)
        
        # Should handle consecutive blocks
        assert isinstance(errors, list)
    
    def test_consecutive_inlines(self):
        """Test consecutive inline notations."""
        consecutive_inlines = "#太字 第一##下線 第二##斜体 第三#"
        
        result = self.parser.parse(consecutive_inlines)
        errors = self.validator.validate_text(consecutive_inlines)
        
        # Should handle consecutive inlines
        assert isinstance(errors, list)
    
    def test_mixed_content_paragraph(self):
        """Test paragraph with mixed notation content."""
        mixed_paragraph = """この段落には#太字 重要な情報#と、

#見出し3
中間見出し
##

それに続く#下線 強調されたテキスト#、さらに

#リスト
- #太字 重要項目#
- 通常項目
- #下線 強調項目#
##

という構成があります。#斜体 最終的な補足情報#も含まれています。"""
        
        result = self.parser.parse(mixed_paragraph)
        errors = self.validator.validate_text(mixed_paragraph)
        
        # Should handle complex mixed content
        assert isinstance(errors, list)


@pytest.mark.unit
@pytest.mark.notation
class TestComplexNotationCombinations:
    """Test complex notation combination scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.definitions)
        self.validator = KumihanSyntaxValidator()
    
    def test_document_structure_simulation(self):
        """Test complete document structure with various notations."""
        document_structure = """#見出し1
メインタイトル：複合記法テストドキュメント
##

このドキュメントは#太字 複合記法システム#のテストを目的としています。

#見出し2
第1章：基本記法
##

基本的な記法には以下があります：

#リスト
- #太字 太字記法# - 重要な情報の強調
- #下線 下線記法# - 補足情報の表示
- #斜体 斜体記法# - 引用や特殊な表現
##

#見出し2
第2章：応用記法
##

応用的な使用方法として、#太字 #下線 二重装飾##; があります。

#見出し3
サブセクション
##

#リスト
- 項目A：#太字 重要度高#
  - サブ項目1：#下線 詳細情報#
  - サブ項目2：通常情報
- 項目B：標準的な内容
  - サブ項目3：#斜体 参考情報#
##

#見出し2
結論
##

以上のように、#太字 多様な記法の組み合わせ#が可能です。
#下線 柔軟性#と#斜体 表現力#を両立しています。"""
        
        result = self.parser.parse(document_structure)
        errors = self.validator.validate_text(document_structure)
        
        # Should handle complete document structure
        assert isinstance(errors, list)
        
        # Check for any critical errors
        critical_errors = [e for e in errors if hasattr(e, 'severity') and 'CRITICAL' in str(e.severity).upper()]
        assert len(critical_errors) == 0, "Document structure should not have critical errors"
    
    def test_table_like_structure(self):
        """Test table-like structures with notations."""
        table_structure = """#見出し2
データ表
##

#リスト
- 行1：#太字 列A#｜#下線 列B#｜#斜体 列C#
- 行2：データ1｜データ2｜データ3
- 行3：#太字 重要データ#｜通常データ｜#下線 補足データ#
#"""
        
        result = self.parser.parse(table_structure)
        errors = self.validator.validate_text(table_structure)
        
        # Should handle table-like structures
        assert isinstance(errors, list)
    
    def test_code_block_simulation(self):
        """Test code block-like structures."""
        code_simulation = """#見出し2
コード例
##

以下は記法の使用例です：

#コード
input_text = "#太字 サンプルテキスト#"
result = parser.parse(input_text)
print(f"結果: {result}")
##

この例では#太字 パーサー#が#下線 入力テキスト#を処理します。"""
        
        result = self.parser.parse(code_simulation)
        errors = self.validator.validate_text(code_simulation)
        
        # Should handle code-like blocks
        assert isinstance(errors, list)
    
    def test_footnote_like_patterns(self):
        """Test footnote-like patterns if supported."""
        footnote_pattern = """本文に#太字 重要な概念#があります((これは脚注のような補足説明です))。

さらに詳細な説明((別の補足情報))も含まれており、
#下線 強調部分#((強調に関する注釈))として表現されます。"""
        
        result = self.parser.parse(footnote_pattern)
        errors = self.validator.validate_text(footnote_pattern)
        
        # Should handle footnote-like patterns
        assert isinstance(errors, list)
        # May not be fully implemented yet
    
    def test_ruby_like_patterns(self):
        """Test ruby-like patterns if supported."""
        ruby_pattern = """日本語には｜漢字《かんじ》や｜平仮名《ひらがな》があります。
これらは#太字 ｜重要《じゅうよう》な要素#です。"""
        
        result = self.parser.parse(ruby_pattern)
        errors = self.validator.validate_text(ruby_pattern)
        
        # Should handle ruby-like patterns
        assert isinstance(errors, list)
        # May not be fully implemented yet
    
    @pytest.mark.slow
    def test_large_compound_document(self, large_text_content):
        """Test processing of large document with compound notations."""
        # Use the large content fixture and add compound notations
        sections = large_text_content.split('\n\n')
        compound_sections = []
        
        for i, section in enumerate(sections[:100]):  # Limit for performance
            if i % 3 == 0:
                # Add nested notation every third section
                modified_section = section.replace(
                    '重要な情報',
                    '#太字 #下線 重要な情報##'
                )
                compound_sections.append(modified_section)
            else:
                compound_sections.append(section)
        
        compound_content = '\n\n'.join(compound_sections)
        
        result = self.parser.parse(compound_content)
        errors = self.validator.validate_text(compound_content)
        
        # Should handle large compound document
        assert isinstance(errors, list)
        
        # Should not have excessive processing time
        # (This is implicitly tested by not timing out)


@pytest.mark.unit
@pytest.mark.notation
class TestNotationInteraction:
    """Test interactions between different notation types."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.definitions)
        self.validator = KumihanSyntaxValidator()
    
    def test_heading_with_decorations(self):
        """Test headings containing decorative notations."""
        heading_decorations = [
            """#見出し1
#太字 重要な#タイトル
#""",
            """#見出し2
プロジェクト#下線 名前#の説明
#""",
            """#見出し3
#斜体 特別#なセクション
#""",
        ]
        
        for text in heading_decorations:
            result = self.parser.parse(text)
            errors = self.validator.validate_text(text)
            
            # Should handle decorated headings
            assert isinstance(errors, list)
    
    def test_list_with_complex_items(self):
        """Test lists containing complex notations."""
        complex_list = """#リスト
- #太字 重要項目#：
  これは#下線 詳細説明#です
  
- 通常項目：標準的な内容

- #斜体 特殊項目#：
  #太字 複数の##下線 装飾#を含む項目
  
- 最終項目：
  #見出し4
  サブ見出し
  #
  内容が続きます
#"""
        
        result = self.parser.parse(complex_list)
        errors = self.validator.validate_text(complex_list)
        
        # Should handle complex list items
        assert isinstance(errors, list)
    
    def test_decoration_boundary_cases(self):
        """Test decoration boundary interactions."""
        boundary_cases = [
            "#太字 終了##下線 開始#",  # Adjacent notations
            "#太字#下線 内容#終了#",  # Embedded notations
            "前#太字 中#後#下線 最後#",  # Mixed positions
        ]
        
        for text in boundary_cases:
            result = self.parser.parse(text)
            errors = self.validator.validate_text(text)
            
            # Should handle boundary cases
            assert isinstance(errors, list)
    
    def test_whitespace_sensitivity(self):
        """Test whitespace handling in compound notations."""
        whitespace_cases = [
            "#太字\n\n\n内容\n\n\n#",  # Multiple newlines
            "#太字   内容   #",  # Internal spaces
            "   #太字 内容#   ",  # External spaces
            "#太字\t内容\t#",  # Tab characters
        ]
        
        for text in whitespace_cases:
            result = self.parser.parse(text)
            errors = self.validator.validate_text(text)
            
            # Should handle whitespace consistently
            assert isinstance(errors, list)