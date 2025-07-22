"""Phase 2 Parser Core Tests Part 2 - パーサーコアテスト（後半）

MarkdownParserテスト - パターンマッチング機能
Target: MarkdownParser完全テスト
Goal: パターン解析・マークダウン構文テスト
"""

from kumihan_formatter.core.markdown_parser import MarkdownParser


class TestMarkdownParser:
    """MarkdownParser完全テスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.parser = MarkdownParser()

    def test_markdown_parser_initialization(self) -> None:
        """MarkdownParser初期化テスト"""
        parser = MarkdownParser()

        # パターンが初期化されていることを確認
        assert hasattr(parser, "patterns")
        assert isinstance(parser.patterns, dict)
        assert len(parser.patterns) > 0

    def test_parse_heading_patterns(self) -> None:
        """見出しパターンテスト"""
        parser = MarkdownParser()

        # H1パターンのテスト
        h1_pattern = parser.patterns["h1"]
        match = h1_pattern.search("# Test Heading")
        assert match is not None
        assert match.group(1) == "Test Heading"

        # H2パターンのテスト
        h2_pattern = parser.patterns["h2"]
        match = h2_pattern.search("## Another Heading")
        assert match is not None
        assert match.group(1) == "Another Heading"

    def test_inline_patterns(self) -> None:
        """インラインパターンテスト"""
        parser = MarkdownParser()

        # strongパターンのテスト
        strong_pattern = parser.patterns["strong"]
        match = strong_pattern.search("This is **bold** text")
        assert match is not None
        assert match.group(1) == "bold"

        # emパターンのテスト
        em_pattern = parser.patterns["em"]
        match = em_pattern.search("This is *italic* text")
        assert match is not None
        assert match.group(1) == "italic"

    def test_link_patterns(self) -> None:
        """リンクパターンテスト"""
        parser = MarkdownParser()

        # linkパターンのテスト
        link_pattern = parser.patterns["link"]
        match = link_pattern.search("[Example](http://example.com)")
        assert match is not None
        assert match.group(1) == "Example"
        assert match.group(2) == "http://example.com"

    def test_list_patterns(self) -> None:
        """リストパターンテスト"""
        parser = MarkdownParser()

        # ol_itemパターンのテスト
        ol_pattern = parser.patterns["ol_item"]
        match = ol_pattern.search("1. First item")
        assert match is not None
        assert match.group(1) == "First item"

        # ul_itemパターンのテスト
        ul_pattern = parser.patterns["ul_item"]
        match = ul_pattern.search("- Bullet item")
        assert match is not None
        assert match.group(1) == "Bullet item"

    def test_code_patterns(self) -> None:
        """コードパターンテスト"""
        parser = MarkdownParser()

        # codeパターンのテスト
        code_pattern = parser.patterns["code"]
        match = code_pattern.search("This is `inline code` example")
        assert match is not None
        assert match.group(1) == "inline code"

    def test_pattern_compilation_completeness(self) -> None:
        """パターンコンパイル完全性テスト"""
        parser = MarkdownParser()

        # 期待するパターンキーがすべて存在することを確認
        expected_keys = [
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

        for key in expected_keys:
            assert key in parser.patterns
            assert parser.patterns[key] is not None
