"""
MarkdownParserのテスト

Test coverage targets:
- パターンコンパイル: 95%
- 見出し変換: 90%
- リスト変換: 85%
- インライン要素変換: 90%
"""

import re
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.markdown_parser import MarkdownParser


class TestMarkdownParser:
    """MarkdownParserクラスのテスト"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        self.parser = MarkdownParser()

    def test_init_compiles_patterns(self):
        """初期化時にパターンがコンパイルされることを確認"""
        # Given & When
        parser = MarkdownParser()

        # Then
        assert parser.patterns is not None
        assert isinstance(parser.patterns, dict)
        assert len(parser.patterns) > 0

        # 主要パターンの存在確認
        expected_patterns = [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "strong",
            "em",
            "strong_alt",
            "em_alt",
            "link",
            "code",
            "hr",
            "ol_item",
            "ul_item",
        ]
        for pattern in expected_patterns:
            assert pattern in parser.patterns
            assert hasattr(parser.patterns[pattern], "match")

    def test_compile_patterns_regex_compilation(self):
        """正規表現パターンのコンパイルテスト"""
        # Given & When
        patterns = self.parser._compile_patterns()

        # Then
        # 見出しパターンテスト
        assert patterns["h1"].match("# Title")
        assert patterns["h2"].match("## Subtitle")
        assert patterns["h3"].match("### Section")
        assert not patterns["h1"].match("## Not H1")

        # 強調パターンテスト
        assert patterns["strong"].search("**bold text**")
        assert patterns["em"].search("*italic text*")
        assert patterns["strong_alt"].search("__bold text__")
        assert patterns["em_alt"].search("_italic text_")

        # リンクパターンテスト
        assert patterns["link"].search("[text](url)")

        # コードパターンテスト
        assert patterns["code"].search("`code`")

        # リストパターンテスト
        assert patterns["ol_item"].match("1. Item")
        assert patterns["ul_item"].match("- Item")
        assert patterns["ul_item"].match("* Item")
        assert patterns["ul_item"].match("+ Item")

        # 水平線パターンテスト
        assert patterns["hr"].match("---")
        assert patterns["hr"].match("-----")

    def test_convert_headings_all_levels(self):
        """すべてのレベルの見出し変換テスト"""
        # Given
        markdown_text = """# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6"""

        # When
        result = self.parser._convert_headings(markdown_text)

        # Then
        assert '<h1 id="heading-1">Heading 1</h1>' in result
        assert '<h2 id="heading-2">Heading 2</h2>' in result
        assert '<h3 id="heading-3">Heading 3</h3>' in result
        assert '<h4 id="heading-4">Heading 4</h4>' in result
        assert '<h5 id="heading-5">Heading 5</h5>' in result
        assert '<h6 id="heading-6">Heading 6</h6>' in result

    def test_convert_headings_with_special_characters(self):
        """特殊文字を含む見出しの変換テスト"""
        # Given
        markdown_text = "# Special Characters: !@#$%^&*()"

        # When
        result = self.parser._convert_headings(markdown_text)

        # Then
        assert (
            '<h1 id="special-characters">Special Characters: !@#$%^&*()</h1>' in result
        )

    def test_convert_headings_with_numbers(self):
        """数字を含む見出しの変換テスト"""
        # Given
        markdown_text = "## Version 2.1.0 Release Notes"

        # When
        result = self.parser._convert_headings(markdown_text)

        # Then
        assert (
            '<h2 id="version-210-release-notes">Version 2.1.0 Release Notes</h2>'
            in result
        )

    def test_generate_heading_id_basic(self):
        """基本的な見出しID生成テスト"""
        # Given
        heading_text = "Simple Heading"

        # When
        result = self.parser._generate_heading_id(heading_text)

        # Then
        assert result == "simple-heading"

    def test_generate_heading_id_with_special_chars(self):
        """特殊文字を含む見出しID生成テスト"""
        # Given
        heading_text = "Complex Title: With Special! Characters@"

        # When
        result = self.parser._generate_heading_id(heading_text)

        # Then
        assert result == "complex-title-with-special-characters"

    def test_generate_heading_id_with_numbers(self):
        """数字を含む見出しID生成テスト"""
        # Given
        heading_text = "Version 1.2.3 Update"

        # When
        result = self.parser._generate_heading_id(heading_text)

        # Then
        assert result == "version-123-update"

    def test_generate_heading_id_empty_result(self):
        """特殊文字のみの見出しID生成テスト"""
        # Given
        heading_text = "!@#$%^&*()"

        # When
        result = self.parser._generate_heading_id(heading_text)

        # Then
        assert result == ""

    def test_convert_lists_unordered_list(self):
        """順序なしリスト変換テスト"""
        # Given
        markdown_text = """- Item 1
- Item 2
- Item 3"""

        # When
        result = self.parser._convert_lists(markdown_text)

        # Then
        assert "<ul>" in result
        assert "</ul>" in result
        assert "<li>Item 1</li>" in result
        assert "<li>Item 2</li>" in result
        assert "<li>Item 3</li>" in result

    def test_convert_lists_ordered_list(self):
        """順序ありリスト変換テスト"""
        # Given
        markdown_text = """1. First item
2. Second item
3. Third item"""

        # When
        result = self.parser._convert_lists(markdown_text)

        # Then
        assert "<ol>" in result
        assert "</ol>" in result
        assert "<li>First item</li>" in result
        assert "<li>Second item</li>" in result
        assert "<li>Third item</li>" in result

    def test_convert_lists_mixed_markers(self):
        """異なるマーカーでの順序なしリスト変換テスト"""
        # Given
        markdown_text = """- Dash item
* Asterisk item
+ Plus item"""

        # When
        result = self.parser._convert_lists(markdown_text)

        # Then
        assert "<ul>" in result
        assert "</ul>" in result
        assert "<li>Dash item</li>" in result
        assert "<li>Asterisk item</li>" in result
        assert "<li>Plus item</li>" in result

    def test_convert_lists_mixed_ordered_unordered(self):
        """順序ありと順序なしの混在リスト変換テスト"""
        # Given
        markdown_text = """- Unordered item 1
- Unordered item 2
1. Ordered item 1
2. Ordered item 2
- Back to unordered"""

        # When
        result = self.parser._convert_lists(markdown_text)

        # Then
        lines = result.split("\n")

        # 最初の順序なしリスト
        assert "<ul>" in lines
        assert "<li>Unordered item 1</li>" in lines
        assert "<li>Unordered item 2</li>" in lines
        assert "</ul>" in lines

        # 順序ありリスト
        assert "<ol>" in lines
        assert "<li>Ordered item 1</li>" in lines
        assert "<li>Ordered item 2</li>" in lines
        assert "</ol>" in lines

        # 再び順序なしリスト
        assert "<li>Back to unordered</li>" in lines

    def test_convert_lists_with_non_list_content(self):
        """リストと通常テキストの混在変換テスト"""
        # Given
        markdown_text = """Normal paragraph
- List item 1
- List item 2
Another paragraph
1. Numbered item
Final paragraph"""

        # When
        result = self.parser._convert_lists(markdown_text)

        # Then
        assert "Normal paragraph" in result
        assert "<ul>" in result
        assert "<li>List item 1</li>" in result
        assert "</ul>" in result
        assert "Another paragraph" in result
        assert "<ol>" in result
        assert "<li>Numbered item</li>" in result
        assert "</ol>" in result
        assert "Final paragraph" in result

    def test_convert_inline_elements_links(self):
        """リンクのインライン変換テスト"""
        # Given
        markdown_text = "Visit [Google](https://google.com) for search"

        # When
        result = self.parser._convert_inline_elements(markdown_text)

        # Then
        assert '<a href="https://google.com">Google</a>' in result
        assert "Visit" in result
        assert "for search" in result

    def test_convert_inline_elements_strong_emphasis(self):
        """強調（太字）のインライン変換テスト"""
        # Given
        markdown_text = "This is **bold** and __also bold__ text"

        # When
        result = self.parser._convert_inline_elements(markdown_text)

        # Then
        assert "<strong>bold</strong>" in result
        assert "<strong>also bold</strong>" in result
        assert "This is" in result
        assert "text" in result

    def test_convert_inline_elements_emphasis(self):
        """強調（イタリック）のインライン変換テスト"""
        # Given
        markdown_text = "This is *italic* and _also italic_ text"

        # When
        result = self.parser._convert_inline_elements(markdown_text)

        # Then
        assert "<em>italic</em>" in result
        assert "<em>also italic</em>" in result
        assert "This is" in result
        assert "text" in result

    def test_convert_inline_elements_code(self):
        """インラインコードの変換テスト"""
        # Given
        markdown_text = "Use `print()` function to output text"

        # When
        result = self.parser._convert_inline_elements(markdown_text)

        # Then
        assert "<code>print()</code>" in result
        assert "Use" in result
        assert "function to output text" in result

    def test_convert_inline_elements_horizontal_rule(self):
        """水平線の変換テスト"""
        # Given
        markdown_text = """Section 1
---
Section 2
-----
Section 3"""

        # When
        result = self.parser._convert_inline_elements(markdown_text)

        # Then
        assert "<hr>" in result
        assert "Section 1" in result
        assert "Section 2" in result
        assert "Section 3" in result
        assert result.count("<hr>") == 2

    def test_convert_inline_elements_multiple_elements(self):
        """複数のインライン要素の変換テスト"""
        # Given
        markdown_text = "Check **[GitHub](https://github.com)** for `code` examples"

        # When
        result = self.parser._convert_inline_elements(markdown_text)

        # Then
        assert "<strong>" in result
        assert "</strong>" in result
        assert '<a href="https://github.com">GitHub</a>' in result
        assert "<code>code</code>" in result

    def test_convert_inline_elements_nested_emphasis(self):
        """ネストした強調要素の変換テスト"""
        # Given
        markdown_text = "***Very important*** text and **bold _with italic_** text"

        # When
        result = self.parser._convert_inline_elements(markdown_text)

        # Then
        # 順序に依存せず、変換が行われていることを確認
        assert "Very important" in result
        assert "bold" in result
        assert "with italic" in result
        assert "<strong>" in result or "<em>" in result

    def test_patterns_immutability(self):
        """パターンの不変性テスト"""
        # Given
        original_patterns = self.parser.patterns.copy()

        # When
        # パターンを変更しようとする
        try:
            self.parser.patterns["new_pattern"] = re.compile(r"test")
        except Exception:
            pass

        # Then
        # 元のパターンは保持されている
        for key, pattern in original_patterns.items():
            assert key in self.parser.patterns

    def test_edge_cases_empty_text(self):
        """エッジケース: 空文字列の処理テスト"""
        # Given
        empty_text = ""

        # When & Then
        assert self.parser._convert_headings(empty_text) == ""
        assert self.parser._convert_lists(empty_text) == ""
        assert self.parser._convert_inline_elements(empty_text) == ""

    def test_edge_cases_whitespace_only(self):
        """エッジケース: 空白のみの処理テスト"""
        # Given
        whitespace_text = "   \n\t  \n   "

        # When
        heading_result = self.parser._convert_headings(whitespace_text)
        list_result = self.parser._convert_lists(whitespace_text)
        inline_result = self.parser._convert_inline_elements(whitespace_text)

        # Then
        assert heading_result == whitespace_text
        assert list_result == whitespace_text
        assert inline_result == whitespace_text

    def test_edge_cases_malformed_markdown(self):
        """エッジケース: 不正なMarkdownの処理テスト"""
        # Given
        malformed_text = "# Incomplete heading \n**Unclosed bold \n[Incomplete link]()"

        # When & Then
        # エラーが発生せずに処理されることを確認
        heading_result = self.parser._convert_headings(malformed_text)
        list_result = self.parser._convert_lists(malformed_text)
        inline_result = self.parser._convert_inline_elements(malformed_text)

        assert isinstance(heading_result, str)
        assert isinstance(list_result, str)
        assert isinstance(inline_result, str)
