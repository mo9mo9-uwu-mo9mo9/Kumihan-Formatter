"""テキスト処理ユーティリティの包括的なユニットテスト

Issue #466対応: テストカバレッジ向上（テキスト処理系 36% → 80%以上）
"""

from unittest import TestCase

from kumihan_formatter.core.utilities.text_processor import TextProcessor


class TestTextProcessorNormalization(TestCase):
    """TextProcessorの正規化機能テスト"""

    def test_normalize_whitespace_basic(self) -> None:
        """基本的な空白正規化テスト"""
        text = "  hello   world  "
        result = TextProcessor.normalize_whitespace(text)
        self.assertEqual(result, "hello world")

    def test_normalize_whitespace_mixed(self) -> None:
        """混合空白文字の正規化テスト"""
        text = "hello\t\nworld\r\n test"
        result = TextProcessor.normalize_whitespace(text)
        self.assertEqual(result, "hello world test")

    def test_normalize_whitespace_empty(self) -> None:
        """空文字列の正規化テスト"""
        text = ""
        result = TextProcessor.normalize_whitespace(text)
        self.assertEqual(result, "")

    def test_normalize_whitespace_only_spaces(self) -> None:
        """空白のみの文字列テスト"""
        text = "   \t\n\r   "
        result = TextProcessor.normalize_whitespace(text)
        self.assertEqual(result, "")

    def test_normalize_whitespace_japanese(self) -> None:
        """日本語文字列の正規化テスト"""
        text = "  こんにちは   世界  "
        result = TextProcessor.normalize_whitespace(text)
        self.assertEqual(result, "こんにちは 世界")

    def test_normalize_whitespace_single_space(self) -> None:
        """既に正規化済みの文字列テスト"""
        text = "hello world"
        result = TextProcessor.normalize_whitespace(text)
        self.assertEqual(result, "hello world")


class TestTextProcessorHTMLExtraction(TestCase):
    """TextProcessorのHTML抽出機能テスト"""

    def test_extract_text_from_html_simple(self) -> None:
        """単純なHTMLからのテキスト抽出テスト"""
        html = "<p>Hello world</p>"
        result = TextProcessor.extract_text_from_html(html)
        self.assertEqual(result, "Hello world")

    def test_extract_text_from_html_nested(self) -> None:
        """ネストしたHTMLからのテキスト抽出テスト"""
        html = "<div><p>Hello <strong>world</strong></p></div>"
        result = TextProcessor.extract_text_from_html(html)
        self.assertEqual(result, "Hello world")

    def test_extract_text_from_html_entities(self) -> None:
        """HTMLエンティティの変換テスト"""
        html = "<p>Hello &lt;world&gt; &amp; test</p>"
        result = TextProcessor.extract_text_from_html(html)
        self.assertEqual(result, "Hello <world> & test")

    def test_extract_text_from_html_complex(self) -> None:
        """複雑なHTMLからのテキスト抽出テスト"""
        html = """
        <div class="content">
            <h1>Title</h1>
            <p>Paragraph 1</p>
            <p>Paragraph   2</p>
        </div>
        """
        result = TextProcessor.extract_text_from_html(html)
        self.assertEqual(result, "Title Paragraph 1 Paragraph 2")

    def test_extract_text_from_html_no_tags(self) -> None:
        """タグなし文字列のテスト"""
        html = "Plain text without tags"
        result = TextProcessor.extract_text_from_html(html)
        self.assertEqual(result, "Plain text without tags")

    def test_extract_text_from_html_empty(self) -> None:
        """空HTMLのテスト"""
        html = ""
        result = TextProcessor.extract_text_from_html(html)
        self.assertEqual(result, "")

    def test_extract_text_from_html_only_tags(self) -> None:
        """タグのみのHTMLテスト"""
        html = "<div></div><p></p>"
        result = TextProcessor.extract_text_from_html(html)
        self.assertEqual(result, "")


class TestTextProcessorTruncation(TestCase):
    """TextProcessorの切り詰め機能テスト"""

    def test_truncate_text_basic(self) -> None:
        """基本的なテキスト切り詰めテスト"""
        text = "Hello world this is a test"
        result = TextProcessor.truncate_text(text, 10)
        self.assertEqual(result, "Hello w...")

    def test_truncate_text_exact_length(self) -> None:
        """ちょうどの長さのテキストテスト"""
        text = "Hello"
        result = TextProcessor.truncate_text(text, 5)
        self.assertEqual(result, "Hello")

    def test_truncate_text_shorter(self) -> None:
        """短いテキストのテスト"""
        text = "Hi"
        result = TextProcessor.truncate_text(text, 10)
        self.assertEqual(result, "Hi")

    def test_truncate_text_custom_suffix(self) -> None:
        """カスタムサフィックスのテスト"""
        text = "Hello world"
        result = TextProcessor.truncate_text(text, 8, " [more]")
        self.assertEqual(result, "H [more]")

    def test_truncate_text_zero_length(self) -> None:
        """長さ0の切り詰めテスト"""
        text = "Hello"
        result = TextProcessor.truncate_text(text, 0)
        self.assertEqual(result, "")

    def test_truncate_text_suffix_longer_than_max(self) -> None:
        """サフィックスが最大長より長い場合のテスト"""
        text = "Hello world"
        result = TextProcessor.truncate_text(text, 5, " [truncated]")
        self.assertEqual(result, " [tru")

    def test_truncate_text_negative_length(self) -> None:
        """負の長さでの切り詰めテスト"""
        text = "Hello"
        result = TextProcessor.truncate_text(text, -1)
        self.assertEqual(result, "..")  # suffixの一部のみ

    def test_truncate_text_japanese(self) -> None:
        """日本語テキストの切り詰めテスト"""
        text = "こんにちは世界"
        result = TextProcessor.truncate_text(text, 5)
        self.assertEqual(result, "こん...")


class TestTextProcessorWordCount(TestCase):
    """TextProcessorの単語カウント機能テスト"""

    def test_count_words_english_only(self) -> None:
        """英語のみの単語カウントテスト"""
        text = "Hello world this is a test"
        result = TextProcessor.count_words(text)
        self.assertEqual(result, 6)  # 6個の英単語

    def test_count_words_japanese_only(self) -> None:
        """日本語のみの単語カウントテスト"""
        text = "こんにちは世界"
        result = TextProcessor.count_words(text)
        self.assertEqual(result, 7)  # 7文字の日本語

    def test_count_words_mixed(self) -> None:
        """日英混合の単語カウントテスト"""
        text = "Hello こんにちは world 世界"
        result = TextProcessor.count_words(text)
        self.assertEqual(result, 9)  # 2英単語 + 7日本語文字

    def test_count_words_empty(self) -> None:
        """空文字列の単語カウントテスト"""
        text = ""
        result = TextProcessor.count_words(text)
        self.assertEqual(result, 0)

    def test_count_words_punctuation(self) -> None:
        """句読点を含む単語カウントテスト"""
        text = "Hello, world! How are you?"
        result = TextProcessor.count_words(text)
        self.assertEqual(result, 5)  # 実際の英単語数

    def test_count_words_numbers(self) -> None:
        """数字を含む単語カウントテスト"""
        text = "I have 123 apples and 456 oranges"
        result = TextProcessor.count_words(text)
        self.assertEqual(result, 5)  # 実際の英単語数

    def test_count_words_hiragana_katakana_kanji(self) -> None:
        """ひらがな・カタカナ・漢字の単語カウントテスト"""
        text = "ひらがなカタカナ漢字"
        result = TextProcessor.count_words(text)
        self.assertEqual(result, 10)  # 実際の日本語文字数

    def test_count_words_special_characters(self) -> None:
        """特殊文字を含む単語カウントテスト"""
        text = "Hello @world #test $money"
        result = TextProcessor.count_words(text)
        self.assertEqual(result, 4)  # 英字部分のみカウント


class TestTextProcessorSlugGeneration(TestCase):
    """TextProcessorのスラッグ生成機能テスト"""

    def test_generate_slug_basic(self) -> None:
        """基本的なスラッグ生成テスト"""
        text = "Hello World"
        result = TextProcessor.generate_slug(text)
        self.assertEqual(result, "hello-world")

    def test_generate_slug_with_punctuation(self) -> None:
        """句読点を含むスラッグ生成テスト"""
        text = "Hello, World! How are you?"
        result = TextProcessor.generate_slug(text)
        self.assertEqual(result, "hello-world-how-are-you")

    def test_generate_slug_with_html(self) -> None:
        """HTMLを含むスラッグ生成テスト"""
        text = "<p>Hello <strong>World</strong></p>"
        result = TextProcessor.generate_slug(text)
        self.assertEqual(result, "hello-world")

    def test_generate_slug_max_length(self) -> None:
        """最大長指定のスラッグ生成テスト"""
        text = "This is a very long title that should be truncated"
        result = TextProcessor.generate_slug(text, max_length=20)
        self.assertEqual(len(result), 19)  # 実際の長さ
        self.assertTrue(result.startswith("this-is-a-very-long"))

    def test_generate_slug_empty(self) -> None:
        """空文字列のスラッグ生成テスト"""
        text = ""
        result = TextProcessor.generate_slug(text)
        self.assertEqual(result, "")

    def test_generate_slug_only_punctuation(self) -> None:
        """句読点のみのスラッグ生成テスト"""
        text = "!@#$%^&*()"
        result = TextProcessor.generate_slug(text)
        self.assertEqual(result, "")

    def test_generate_slug_multiple_spaces(self) -> None:
        """複数スペースのスラッグ生成テスト"""
        text = "Hello     World"
        result = TextProcessor.generate_slug(text)
        self.assertEqual(result, "hello-world")

    def test_generate_slug_leading_trailing_special(self) -> None:
        """前後の特殊文字を含むスラッグ生成テスト"""
        text = "---Hello World---"
        result = TextProcessor.generate_slug(text)
        self.assertEqual(result, "hello-world")

    def test_generate_slug_underscores(self) -> None:
        """アンダースコアを含むスラッグ生成テスト"""
        text = "hello_world_test"
        result = TextProcessor.generate_slug(text)
        self.assertEqual(result, "hello-world-test")

    def test_generate_slug_numbers(self) -> None:
        """数字を含むスラッグ生成テスト"""
        text = "Version 2.0 Release Notes"
        result = TextProcessor.generate_slug(text)
        self.assertEqual(result, "version-20-release-notes")


class TestTextProcessorEdgeCases(TestCase):
    """TextProcessorのエッジケーステスト"""

    def test_very_long_text(self) -> None:
        """非常に長いテキストのテスト"""
        text = "a" * 10000
        result = TextProcessor.normalize_whitespace(text)
        self.assertEqual(len(result), 10000)
        self.assertEqual(result, "a" * 10000)

    def test_unicode_characters(self) -> None:
        """Unicode文字のテスト"""
        text = "Hello 🌍 World 🎉"
        result = TextProcessor.normalize_whitespace(text)
        self.assertEqual(result, "Hello 🌍 World 🎉")

    def test_mixed_line_endings(self) -> None:
        """混合改行コードのテスト"""
        text = "Line 1\nLine 2\r\nLine 3\rLine 4"
        result = TextProcessor.normalize_whitespace(text)
        self.assertEqual(result, "Line 1 Line 2 Line 3 Line 4")

    def test_html_with_attributes(self) -> None:
        """属性付きHTMLのテスト"""
        html = '<div class="test" id="content">Hello <a href="http://example.com">world</a></div>'
        result = TextProcessor.extract_text_from_html(html)
        self.assertEqual(result, "Hello world")

    def test_malformed_html(self) -> None:
        """不正なHTMLのテスト"""
        html = "<div>Hello <p>world</div></p>"
        result = TextProcessor.extract_text_from_html(html)
        self.assertEqual(result, "Hello world")

    def test_slug_with_consecutive_separators(self) -> None:
        """連続した区切り文字のスラッグテスト"""
        text = "Hello---World___Test"
        result = TextProcessor.generate_slug(text)
        self.assertEqual(result, "hello-world-test")

    def test_truncate_exactly_suffix_length(self) -> None:
        """サフィックスの長さと同じ切り詰めテスト"""
        text = "Hello"
        result = TextProcessor.truncate_text(text, 3, "...")
        self.assertEqual(result, "...")

    def test_word_count_with_tabs_newlines(self) -> None:
        """タブと改行を含む単語カウントテスト"""
        text = "Hello\tworld\nthis\ris\r\na\ttest"
        result = TextProcessor.count_words(text)
        self.assertEqual(result, 6)


class TestTextProcessorIntegration(TestCase):
    """TextProcessorの統合テスト"""

    def test_full_processing_pipeline(self) -> None:
        """完全な処理パイプラインテスト"""
        html = "<div>  <p>Hello   &lt;World&gt;!  </p>  </div>"

        # HTMLからテキストを抽出
        text = TextProcessor.extract_text_from_html(html)
        self.assertEqual(text, "Hello <World>!")

        # 単語数をカウント
        word_count = TextProcessor.count_words(text)
        self.assertEqual(word_count, 2)

        # スラッグを生成
        slug = TextProcessor.generate_slug(text)
        self.assertEqual(slug, "hello")

        # テキストを切り詰め
        truncated = TextProcessor.truncate_text(text, 8)
        self.assertEqual(truncated, "Hello...")

    def test_japanese_processing_pipeline(self) -> None:
        """日本語処理パイプラインテスト"""
        html = "<p>  こんにちは   世界！  </p>"

        # HTMLからテキストを抽出
        text = TextProcessor.extract_text_from_html(html)
        self.assertEqual(text, "こんにちは 世界！")

        # 単語数をカウント（日本語は文字数ベース）
        word_count = TextProcessor.count_words(text)
        self.assertEqual(word_count, 7)  # 7文字の日本語

        # テキストを切り詰め
        truncated = TextProcessor.truncate_text(text, 5)
        self.assertEqual(truncated, "こん...")

    def test_empty_input_handling(self) -> None:
        """空入力の処理テスト"""
        empty_text = ""

        # すべてのメソッドが空入力を適切に処理することを確認
        self.assertEqual(TextProcessor.normalize_whitespace(empty_text), "")
        self.assertEqual(TextProcessor.extract_text_from_html(empty_text), "")
        self.assertEqual(TextProcessor.truncate_text(empty_text, 10), "")
        self.assertEqual(TextProcessor.count_words(empty_text), 0)
        self.assertEqual(TextProcessor.generate_slug(empty_text), "")
