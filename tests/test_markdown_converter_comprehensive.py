"""
markdown_converter.py の包括的テスト

Issue #591 Critical Tier Testing対応
- 80%以上のテストカバレッジ
- 100%エッジケーステスト
- 統合テスト・回帰テスト
"""

from pathlib import Path
from unittest import mock
from unittest.mock import mock_open, patch

import pytest

from kumihan_formatter.core.markdown_converter import (
    SimpleMarkdownConverter,
    convert_markdown_file,
    convert_markdown_text,
)
from kumihan_formatter.core.markdown_parser import MarkdownParser
from kumihan_formatter.core.markdown_processor import MarkdownProcessor
from kumihan_formatter.core.markdown_renderer import MarkdownRenderer


class TestSimpleMarkdownConverter:
    """SimpleMarkdownConverterのテスト"""

    @pytest.fixture
    def converter(self):
        """コンバーターのフィクスチャ"""
        return SimpleMarkdownConverter()

    def test_init_components(self, converter):
        """初期化時にコンポーネントが正しく作成されることを確認"""
        assert isinstance(converter.parser, MarkdownParser)
        assert isinstance(converter.processor, MarkdownProcessor)
        assert isinstance(converter.renderer, MarkdownRenderer)
        assert converter.patterns is not None

    def test_convert_text_basic(self, converter):
        """基本的なテキスト変換のテスト"""
        markdown_text = "# Test Heading\n\nThis is a paragraph."
        result = converter.convert_text(markdown_text)

        # 見出しが変換されていることを確認
        assert "<h1" in result
        assert "Test Heading" in result
        # 段落が作成されていることを確認
        assert "<p>" in result
        assert "paragraph" in result

    def test_convert_text_with_code_blocks(self, converter):
        """コードブロック付きテキスト変換のテスト"""
        markdown_text = """
# Code Example

```python
def hello():
    print("Hello, World!")
```

Some text after code.
"""
        result = converter.convert_text(markdown_text)

        # コードブロックが変換されていることを確認
        assert "<pre><code>" in result
        assert "def hello():" in result
        assert "print" in result

    def test_convert_text_with_lists(self, converter):
        """リスト付きテキスト変換のテスト"""
        markdown_text = """
# Lists

- Item 1
- Item 2
- Item 3

1. Numbered item 1
2. Numbered item 2
"""
        result = converter.convert_text(markdown_text)

        # リストが変換されていることを確認（具体的なHTMLは実装依存）
        assert "Item 1" in result
        assert "Numbered item 1" in result

    def test_convert_text_with_inline_elements(self, converter):
        """インライン要素付きテキスト変換のテスト"""
        markdown_text = """
This text has **bold** and *italic* elements.
There's also `inline code` and [a link](https://example.com).
"""
        result = converter.convert_text(markdown_text)

        # インライン要素が処理されていることを確認
        assert "bold" in result
        assert "italic" in result
        assert "inline code" in result
        assert "example.com" in result

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="# Test Document\n\nContent here.",
    )
    @patch("pathlib.Path.exists", return_value=True)
    def test_convert_file_success(self, mock_exists, mock_file, converter):
        """ファイル変換成功のテスト"""
        test_file = Path("test.md")
        result = converter.convert_file(test_file, "Custom Title")

        # HTMLが生成されていることを確認
        assert "<html" in result
        assert "Custom Title" in result
        assert "Test Document" in result
        assert "Content here" in result

    @patch("pathlib.Path.exists", return_value=False)
    def test_convert_file_not_found(self, mock_exists, converter):
        """存在しないファイルの変換テスト"""
        test_file = Path("nonexistent.md")

        with pytest.raises(FileNotFoundError) as exc_info:
            converter.convert_file(test_file)

        assert "ファイルが見つかりません" in str(exc_info.value)

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists", return_value=True)
    def test_convert_file_unicode_decode_error(self, mock_exists, mock_file, converter):
        """UTF-8デコードエラーでShift_JISフォールバックのテスト"""

        # UTF-8で失敗、Shift_JISで成功するケースをモック
        def open_side_effect(file, mode, encoding=None):
            if encoding == "utf-8":
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")
            elif encoding == "shift_jis":
                return mock_open(read_data="# テスト文書\n\n内容").return_value
            return mock_open().return_value

        mock_file.side_effect = open_side_effect

        test_file = Path("japanese.md")
        result = converter.convert_file(test_file)

        # フォールバックが機能していることを確認
        assert "テスト文書" in result

    @patch("builtins.open", new_callable=mock_open, read_data="Content without title")
    @patch("pathlib.Path.exists", return_value=True)
    def test_convert_file_no_title_provided(self, mock_exists, mock_file, converter):
        """タイトル未指定でファイル変換のテスト"""
        test_file = Path("document.md")
        result = converter.convert_file(test_file)

        # ファイル名がタイトルとして使用されることを確認
        assert "document" in result

    def test_extract_title_from_content(self, converter):
        """コンテンツからタイトル抽出のテスト"""
        content_with_h1 = "# Main Title\n\nSome content"
        title = converter._extract_title_from_content(content_with_h1)
        assert title == "Main Title"

    def test_extract_title_from_content_no_h1(self, converter):
        """H1見出しがないコンテンツのタイトル抽出テスト"""
        content_without_h1 = "## Sub Title\n\nSome content"
        title = converter._extract_title_from_content(content_without_h1)
        assert title is None

    def test_generate_heading_id(self, converter):
        """見出しID生成のテスト"""
        heading_text = "Test Heading with Spaces"
        heading_id = converter._generate_heading_id(heading_text)
        assert isinstance(heading_id, str)
        # 具体的なID形式は実装依存

    def test_create_full_html(self, converter):
        """完全HTML作成のテスト"""
        title = "Test Title"
        content = "<h1>Test</h1><p>Content</p>"
        source_filename = "test.md"

        html = converter._create_full_html(title, content, source_filename)

        # HTML構造の確認
        assert "<html" in html
        assert "<head>" in html
        assert "<title>" in html
        assert "Test Title" in html
        assert "<body>" in html
        assert content in html

    def test_component_method_delegation(self, converter):
        """コンポーネントメソッドの委譲テスト"""
        # パーサーメソッドの委譲
        test_text = "# Heading\n\nParagraph"
        headings_result = converter._convert_headings(test_text)
        assert isinstance(headings_result, str)

        # プロセッサーメソッドの委譲
        code_text = "```\ncode here\n```"
        code_result = converter._convert_code_blocks(code_text)
        assert isinstance(code_result, str)

        # レンダラーメソッドの委譲
        paragraph_text = "Some text\n\nAnother paragraph"
        paragraph_result = converter._convert_paragraphs(paragraph_text)
        assert isinstance(paragraph_result, str)


class TestModuleFunctions:
    """モジュールレベル関数のテスト"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """テンポラリディレクトリのフィクスチャ"""
        return tmp_path

    def test_convert_markdown_file_success(self, temp_dir):
        """convert_markdown_file成功のテスト"""
        # 入力ファイル作成
        input_file = temp_dir / "input.md"
        input_file.write_text("# Test Document\n\nThis is a test.", encoding="utf-8")

        # 出力ファイルパス
        output_file = temp_dir / "output.html"

        # 変換実行
        result = convert_markdown_file(input_file, output_file, "Custom Title")

        # 成功することを確認
        assert result is True
        assert output_file.exists()

        # 出力内容の確認
        html_content = output_file.read_text(encoding="utf-8")
        assert "Custom Title" in html_content
        assert "Test Document" in html_content

    def test_convert_markdown_file_nested_output_dir(self, temp_dir):
        """ネストした出力ディレクトリでの変換テスト"""
        input_file = temp_dir / "input.md"
        input_file.write_text("# Test\n\nContent")

        # ネストした出力パス
        output_file = temp_dir / "nested" / "deep" / "output.html"

        result = convert_markdown_file(input_file, output_file)

        assert result is True
        assert output_file.exists()
        assert output_file.parent.exists()

    def test_convert_markdown_file_failure(self, temp_dir):
        """convert_markdown_file失敗のテスト"""
        # 存在しない入力ファイル
        input_file = temp_dir / "nonexistent.md"
        output_file = temp_dir / "output.html"

        result = convert_markdown_file(input_file, output_file)

        # 失敗することを確認
        assert result is False
        assert not output_file.exists()

    @patch("builtins.print")  # エラーメッセージの出力をキャプチャ
    def test_convert_markdown_file_exception_handling(self, mock_print, temp_dir):
        """convert_markdown_file例外処理のテスト"""
        input_file = temp_dir / "input.md"
        input_file.write_text("# Test")

        # 書き込み不可能な出力パス（権限エラーをシミュレート）
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            output_file = temp_dir / "output.html"
            result = convert_markdown_file(input_file, output_file)

            assert result is False
            mock_print.assert_called_once()
            assert "変換エラー" in mock_print.call_args[0][0]

    def test_convert_markdown_text_basic(self):
        """convert_markdown_text基本テスト"""
        markdown_text = "# Title\n\nParagraph content"
        title = "Custom Title"

        result = convert_markdown_text(markdown_text, title)

        # HTML構造の確認
        assert "<html" in result
        assert "Custom Title" in result
        assert "Title" in result
        assert "Paragraph content" in result

    def test_convert_markdown_text_default_title(self):
        """convert_markdown_textデフォルトタイトルのテスト"""
        markdown_text = "Content only"

        result = convert_markdown_text(markdown_text)

        # デフォルトタイトルが使用されることを確認
        assert "文書" in result
        assert "テキスト" in result  # source_filenameのデフォルト値

    def test_convert_markdown_text_empty_input(self):
        """convert_markdown_text空入力のテスト"""
        result = convert_markdown_text("")

        # 空でもHTMLが生成されることを確認
        assert "<html" in result
        assert "<body>" in result


class TestMarkdownConverterEdgeCases:
    """エッジケーステスト - 100%カバレッジ"""

    @pytest.fixture
    def converter(self):
        return SimpleMarkdownConverter()

    def test_convert_text_empty_string(self, converter):
        """空文字列の変換テスト"""
        result = converter.convert_text("")
        assert isinstance(result, str)

    def test_convert_text_whitespace_only(self, converter):
        """空白のみのテキスト変換テスト"""
        result = converter.convert_text("   \n\n   \t   ")
        assert isinstance(result, str)

    def test_convert_text_special_characters(self, converter):
        """特殊文字を含むテキスト変換テスト"""
        special_text = "Text with <tags> & entities \"quotes\" 'apostrophes'"
        result = converter.convert_text(special_text)
        assert isinstance(result, str)

    def test_convert_text_unicode_characters(self, converter):
        """Unicode文字を含むテキスト変換テスト"""
        unicode_text = "日本語テキスト with émojis 🚀 and symbols ★★★"
        result = converter.convert_text(unicode_text)
        assert isinstance(result, str)
        assert "日本語" in result

    def test_convert_text_very_long_input(self, converter):
        """非常に長い入力のテスト"""
        long_text = "# Long Document\n\n" + "Long paragraph content. " * 1000
        result = converter.convert_text(long_text)
        assert isinstance(result, str)
        assert "Long Document" in result

    def test_convert_text_nested_markdown_elements(self, converter):
        """ネストしたMarkdown要素のテスト"""
        nested_text = """
# Main Heading

## Sub Heading

- List item with **bold** text
- Another item with `inline code`
  - Nested list item
  - Another nested with *italic*

```python
# Code block with comments
def function():
    return "value"
```

Final paragraph with [link](http://example.com).
"""
        result = converter.convert_text(nested_text)
        assert isinstance(result, str)
        assert "Main Heading" in result
        assert "bold" in result
        assert "inline code" in result

    def test_convert_text_malformed_markdown(self, converter):
        """不正な形式のMarkdownのテスト"""
        malformed_text = """
# Unclosed emphasis *text without closing
## Unmatched code `block without closing
[Invalid link](without closing paren
**Unclosed bold text
```
Unclosed code block
"""
        result = converter.convert_text(malformed_text)
        assert isinstance(result, str)

    def test_patterns_property_access(self, converter):
        """patternsプロパティのアクセステスト"""
        patterns = converter.patterns
        assert patterns is not None
        assert isinstance(patterns, dict)

    @patch("builtins.open")
    @patch("pathlib.Path.exists", return_value=True)
    def test_convert_file_with_encoding_fallback_failure(
        self, mock_exists, mock_open, converter
    ):
        """エンコーディングフォールバックも失敗するケースのテスト"""
        # UTF-8とShift_JIS両方で失敗するケース
        mock_open.side_effect = UnicodeDecodeError("encoding", b"", 0, 1, "error")

        test_file = Path("problematic.md")

        with pytest.raises(UnicodeDecodeError):
            converter.convert_file(test_file)

    def test_extract_title_multiline_content(self, converter):
        """複数行にわたるコンテンツからのタイトル抽出テスト"""
        multiline_content = """
Some preamble text
that doesn't contain headings

# The Actual Title

More content after the title
## Sub heading
"""
        title = converter._extract_title_from_content(multiline_content)
        assert title == "The Actual Title"

    def test_extract_title_multiple_h1(self, converter):
        """複数のH1見出しがある場合のタイトル抽出テスト"""
        multiple_h1_content = """
# First Title

Content here

# Second Title

More content
"""
        title = converter._extract_title_from_content(multiple_h1_content)
        # 最初のH1が抽出されることを確認
        assert title == "First Title"


class TestMarkdownConverterIntegration:
    """統合テスト"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path

    @pytest.mark.integration
    def test_full_markdown_conversion_workflow(self, temp_dir):
        """完全なMarkdown変換ワークフローの統合テスト"""
        # 複雑なMarkdownファイル作成
        complex_markdown = """
# プロジェクト文書

## 概要

これは**重要な**プロジェクト文書です。

### 機能リスト

1. *基本機能*
2. `高度な機能`
3. [外部連携](https://example.com)

### コード例

```python
def main():
    print("Hello, World!")
    return 0
```

## 補足

- 注意事項1
- 注意事項2
  - サブ項目A
  - サブ項目B

---

最終更新: 2024年
"""

        input_file = temp_dir / "complex.md"
        input_file.write_text(complex_markdown, encoding="utf-8")

        output_file = temp_dir / "complex.html"

        # ファイル変換実行
        result = convert_markdown_file(input_file, output_file)
        assert result is True

        # 出力の確認
        html_content = output_file.read_text(encoding="utf-8")

        # 各要素が適切に変換されていることを確認
        assert "プロジェクト文書" in html_content
        assert "<h1" in html_content
        assert "<h2" in html_content
        assert "<h3" in html_content
        assert "重要な" in html_content
        assert "基本機能" in html_content
        assert "example.com" in html_content
        assert "<pre><code>" in html_content
        assert "Hello, World!" in html_content

    @pytest.mark.integration
    def test_component_integration(self):
        """コンポーネント間の統合テスト"""
        converter = SimpleMarkdownConverter()

        # 各コンポーネントが正しく連携していることを確認
        test_markdown = """
# Test Title

Normal paragraph with **bold** text.

```
code block content
```

- List item 1
- List item 2

Final paragraph.
"""

        # step-by-step変換をシミュレート
        # 1. テキスト正規化
        normalized = converter.processor.normalize_text(test_markdown)
        assert isinstance(normalized, str)

        # 2. 完全変換
        html_result = converter.convert_text(test_markdown)

        # 各コンポーネントの出力が統合されていることを確認
        assert "Test Title" in html_result
        assert "bold" in html_result
        assert "code block content" in html_result
        assert "List item" in html_result

    @pytest.mark.integration
    def test_backward_compatibility_integration(self, temp_dir):
        """後方互換性の統合テスト"""
        # SimpleMarkdownConverterの全メソッドが期待通りに動作することを確認
        converter = SimpleMarkdownConverter()

        # ファイル変換（Windows互換性のためUTF-8エンコーディング明示）
        input_file = temp_dir / "compat_test.md"
        input_file.write_text("# 互換性テスト\n\n内容です。", encoding="utf-8")

        html_output = converter.convert_file(input_file)
        assert "互換性テスト" in html_output

        # テキスト変換
        text_output = converter.convert_text("# テキスト\n\n内容")
        assert "テキスト" in text_output

        # モジュール関数
        module_output = convert_markdown_text("# モジュール\n\n内容")
        assert "モジュール" in module_output


class TestMarkdownConverterRegression:
    """回帰テスト"""

    def test_converter_class_attributes_regression(self):
        """コンバータークラス属性の回帰テスト"""
        converter = SimpleMarkdownConverter()

        # 必要な属性が存在することを確認
        required_attributes = ["parser", "processor", "renderer", "patterns"]
        for attr in required_attributes:
            assert hasattr(converter, attr), f"属性 {attr} が見つからない"

    def test_module_function_signatures_regression(self):
        """モジュール関数シグネチャの回帰テスト"""
        import inspect

        # convert_markdown_file のシグネチャ確認
        file_sig = inspect.signature(convert_markdown_file)
        file_params = list(file_sig.parameters.keys())
        expected_file_params = ["input_file", "output_file", "title"]
        assert file_params == expected_file_params

        # convert_markdown_text のシグネチャ確認
        text_sig = inspect.signature(convert_markdown_text)
        text_params = list(text_sig.parameters.keys())
        expected_text_params = ["markdown_text", "title"]
        assert text_params == expected_text_params

    def test_docstring_regression(self):
        """ドキュメント文字列の回帰テスト"""
        from kumihan_formatter.core import markdown_converter

        # モジュールdocstring確認
        assert markdown_converter.__doc__ is not None
        docstring = markdown_converter.__doc__
        assert "マークダウン変換器 統合モジュール" in docstring
        assert "分割された各コンポーネントを統合" in docstring
        assert "Issue #492 Phase 5A" in docstring

    def test_class_method_availability_regression(self):
        """クラスメソッド可用性の回帰テスト"""
        converter = SimpleMarkdownConverter()

        # 主要メソッドが利用可能であることを確認
        required_methods = [
            "convert_file",
            "convert_text",
            "_extract_title_from_content",
            "_convert_code_blocks",
            "_convert_headings",
            "_generate_heading_id",
            "_convert_lists",
            "_convert_inline_elements",
            "_convert_paragraphs",
            "_create_full_html",
        ]

        for method_name in required_methods:
            assert hasattr(
                converter, method_name
            ), f"メソッド {method_name} が見つからない"
            assert callable(
                getattr(converter, method_name)
            ), f"メソッド {method_name} が呼び出し可能でない"

    @pytest.mark.performance
    def test_performance_regression(self, tmp_path):
        """パフォーマンス回帰テスト"""
        import time

        # 大きなMarkdownファイルの変換時間測定
        large_markdown = """# Large Document\n\n""" + "Paragraph content. " * 1000
        large_markdown += (
            "\n\n## Code Section\n\n```python\n" + "print('line')\n" * 100 + "```"
        )

        input_file = tmp_path / "large.md"
        input_file.write_text(large_markdown)
        output_file = tmp_path / "large.html"

        start_time = time.time()
        result = convert_markdown_file(input_file, output_file)
        elapsed_time = time.time() - start_time

        # 変換成功と性能要件の確認
        assert result is True
        assert elapsed_time < 5.0, f"変換が遅すぎます: {elapsed_time:.3f}秒"

    def test_encoding_handling_regression(self, tmp_path):
        """エンコーディング処理の回帰テスト"""
        # UTF-8ファイル
        utf8_content = "# UTF-8 テスト\n\n日本語内容です。🚀"
        utf8_file = tmp_path / "utf8.md"
        utf8_file.write_text(utf8_content, encoding="utf-8")

        converter = SimpleMarkdownConverter()
        result = converter.convert_file(utf8_file)

        # UTF-8が正しく処理されることを確認
        assert "UTF-8 テスト" in result
        assert "日本語内容" in result
        assert "🚀" in result

    def test_error_handling_consistency_regression(self):
        """エラーハンドリング一貫性の回帰テスト"""
        converter = SimpleMarkdownConverter()

        # 存在しないファイルの処理
        with pytest.raises(FileNotFoundError):
            converter.convert_file(Path("does_not_exist.md"))

        # 空入力の処理（エラーにならない）
        result = converter.convert_text("")
        assert isinstance(result, str)

        # None入力の処理（型エラーになるべき）
        with pytest.raises(AttributeError):
            converter.convert_text(None)
