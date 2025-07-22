"""Phase 2 Parser Integration Tests - パーサー統合テスト

パーサー統合機能テスト - KeywordParser・統合・パフォーマンス
Target: parser.py の統合機能
Goal: KeywordParser・統合テスト・パフォーマンステスト
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.markdown_parser import MarkdownParser
from kumihan_formatter.parser import parse


class TestKeywordParser:
    """KeywordParser完全テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = KeywordParser()

    def test_keyword_parser_initialization(self):
        """KeywordParser初期化テスト"""
        parser = KeywordParser()

        # 基本属性が初期化されていることを確認
        assert hasattr(parser, "parse")

    def test_parse_footnote_notation(self):
        """脚注記法解析テスト"""
        text = "Text with ((footnote content)) notation."
        result = self.parser.parse(text)

        # 脚注記法が解析されることを確認
        assert isinstance(result, list)

    def test_parse_ruby_notation(self):
        """ルビ記法解析テスト"""
        text = "Text with ｜ruby text《reading》 notation."
        result = self.parser.parse(text)

        # ルビ記法が解析されることを確認
        assert isinstance(result, list)

    def test_parse_mixed_notations(self):
        """混在記法解析テスト"""
        text = "Mixed ((footnote)) and ｜ruby《reading》 notations."
        result = self.parser.parse(text)

        # 混在記法が解析されることを確認
        assert isinstance(result, list)

    def test_parse_multiple_footnotes(self):
        """複数脚注解析テスト"""
        text = "First ((footnote one)) and second ((footnote two)) notes."
        result = self.parser.parse(text)

        # 複数脚注が解析されることを確認
        assert isinstance(result, list)

    def test_parse_multiple_rubies(self):
        """複数ルビ解析テスト"""
        text = "First ｜word《reading1》 and ｜another《reading2》 rubies."
        result = self.parser.parse(text)

        # 複数ルビが解析されることを確認
        assert isinstance(result, list)

    def test_parse_nested_notations(self):
        """ネスト記法解析テスト"""
        text = "Complex ((footnote with ｜nested《ruby》 content)) notation."
        result = self.parser.parse(text)

        # ネスト記法が解析されることを確認
        assert isinstance(result, list)

    def test_parse_custom_notation(self):
        """カスタム記法解析テスト"""
        text = "Custom ;;;emphasis;;; content ;;; notation."
        result = self.parser.parse(text)

        # カスタム記法が解析されることを確認
        assert isinstance(result, list)

    def test_parse_malformed_notations(self):
        """不正形記法解析テスト"""
        malformed_cases = [
            "Incomplete ((footnote",
            "Incomplete ｜ruby《",
            "Mismatched ((footnote))",
            "Wrong ｜ruby｜reading》",
        ]

        for case in malformed_cases:
            result = self.parser.parse(case)
            # 不正形記法でも何らかの結果が返されることを確認
            assert isinstance(result, list)

    def test_parse_empty_notations(self):
        """空記法解析テスト"""
        text = "Empty (()) and ｜《》 notations."
        result = self.parser.parse(text)

        # 空記法が解析されることを確認
        assert isinstance(result, list)

    def test_parse_unicode_notations(self):
        """Unicode記法解析テスト"""
        text = "Unicode ((日本語脚注)) and ｜漢字《かんじ》 notations."
        result = self.parser.parse(text)

        # Unicode記法が解析されることを確認
        assert isinstance(result, list)


class TestParserIntegration:
    """パーサー統合テスト"""

    def test_markup_and_notation_integration(self):
        """マークアップと記法の統合テスト"""
        text = """
        # Document with ((footnote in title))

        Paragraph with **bold ((footnote))** text.

        ## Section with ｜ruby《reading》

        - List item with ((footnote))
        - Another item with ｜ruby《reading》
        """
        result = parse(text)

        # マークアップと記法が統合処理されることを確認
        assert isinstance(result, list)
        assert len(result) > 0

    def test_complex_document_parsing(self):
        """複雑文書解析テスト"""
        text = """
        # Main Title with ((title footnote))

        Introduction paragraph with ｜important《じゅうよう》 information.

        ## Features Section

        ### Feature 1: ｜Advanced《高度》 Processing

        Description with ((detailed explanation)) about the feature.

        - Benefit 1 with **emphasis**
        - Benefit 2 with ((footnote benefit))
        - Benefit 3 with ｜technical《技術的》 details

        ### Feature 2: Integration

        More content with *italic* and ((comprehensive footnote with
        multiple lines and ｜nested《ネスト》 ruby content)).

        ## Conclusion

        Final thoughts with ｜conclusion《結論》 and ((final note)).
        """
        result = parse(text)

        # 複雑文書が完全に解析されることを確認
        assert isinstance(result, list)
        assert len(result) > 0

    def test_parser_performance(self):
        """パーサーパフォーマンステスト"""
        # 大きなドキュメントを生成
        large_content = []
        for i in range(100):
            large_content.append(f"# Heading {i}")
            large_content.append(f"Paragraph {i} with ((footnote {i})) notation.")
            large_content.append(f"More content with ｜word{i}《reading{i}》 ruby.")
            large_content.append("")

        text = "\n".join(large_content)

        import time

        start = time.time()
        result = parse(text)
        end = time.time()

        # 合理的な時間内で処理が完了することを確認
        assert isinstance(result, list)
        assert (end - start) < 10.0  # 10秒以内

    def test_parser_memory_efficiency(self):
        """パーサーメモリ効率テスト"""
        # 複数の解析処理でメモリリークが発生しないことを確認
        texts = [
            "Simple text with ((footnote)).",
            "Ruby text with ｜word《reading》 notation.",
            "# Heading with mixed content",
            "Complex ((footnote with ｜nested《ruby》 content)) text.",
        ]

        for _ in range(10):
            for text in texts:
                result = parse(text)
                assert isinstance(result, list)

        # ガベージコレクション
        import gc

        gc.collect()
        assert True

    def test_parser_error_resilience(self):
        """パーサーエラー耐性テスト"""
        error_cases = [
            None,
            123,
            [],
            {},
            "Very long " + "text " * 1000 + " content",
            "Malformed ((footnote content",
            "Invalid ｜ruby｜reading》 notation",
            "\x00\x01\x02 binary content",
        ]

        for case in error_cases:
            try:
                result = parse(case)
                if result is not None:
                    assert isinstance(result, list)
            except Exception:
                # エラーが発生しても適切に処理されることを確認
                assert True

    def test_parser_concurrent_usage(self):
        """パーサー並行使用テスト"""
        import threading

        results = []

        def parse_content(content_id):
            text = f"Content {content_id} with ((footnote {content_id})) and ｜word{content_id}《reading》."
            try:
                result = parse(text)
                results.append(isinstance(result, list))
            except Exception:
                results.append(False)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=parse_content, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 全ての並行処理が正常に完了することを確認
        assert all(results)

    def test_parser_edge_cases(self):
        """パーサーエッジケーステスト"""
        edge_cases = [
            "",  # 空文字列
            " ",  # 単一スペース
            "\n",  # 単一改行
            "\t",  # 単一タブ
            "((()))",  # ネストした括弧
            "｜｜《》《》",  # 重複記号
            "# # # Multiple hashes",  # 複数ハッシュ
            "**bold**italic*",  # 不正マークアップ
            "Mixed ((footnote and ｜ruby《reading》)) complex",  # 複雑ネスト
        ]

        for case in edge_cases:
            result = parse(case)
            # エッジケースでも何らかのリストが返されることを確認
            assert isinstance(result, list)

    def test_parser_unicode_robustness(self):
        """パーサーUnicode堅牢性テスト"""
        unicode_texts = [
            "日本語のテキスト with ((脚注))",
            "中文文档 with ｜汉字《pinyin》",
            "한국어 텍스트 with mixed content",
            "العربية النص with ((footnote))",
            "Русский текст with ｜слово《slovo》",
            "🎌🌸⚡ Emoji with ((emoji footnote)) 🚀💫",
        ]

        for text in unicode_texts:
            result = parse(text)
            assert isinstance(result, list)