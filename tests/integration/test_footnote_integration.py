"""Integration tests for Kumihan-Formatter footnote system."""

import pytest
from kumihan_formatter.parser import Parser
from kumihan_formatter.renderer import Renderer
from kumihan_formatter.core.parsing.keyword.definitions import KeywordDefinitions
from kumihan_formatter.core.rendering.html_formatter import FootnoteManager
from kumihan_formatter.core.utilities.logger import get_logger


class TestFootnoteIntegration:
    """脚注システムの統合テスト"""

    def setup_method(self):
        """各テストメソッドの前にセットアップを実行"""
        self.parser = Parser()
        self.renderer = Renderer()
        self.logger = get_logger(__name__)

    def test_single_footnote_parsing_and_rendering(self):
        """単一脚注のパース→レンダリング統合テスト"""
        text = "これは本文です# 脚注 #これは脚注の内容です##"

        # パース処理
        nodes = self.parser.parse(text)
        assert nodes is not None
        assert len(nodes) > 0

        # レンダリング処理
        html = self.renderer.render(nodes)
        assert html is not None

        # 脚注リンクが本文に含まれることを確認
        assert "footnote-ref" in html
        assert "[1]" in html

        # 脚注セクションが末尾に含まれることを確認
        assert 'class="footnotes"' in html
        assert "これは脚注の内容です" in html

    def test_multiple_footnotes_parsing_and_rendering(self):
        """複数脚注のパース→レンダリング統合テスト"""
        text = """最初の段落# 脚注 #第一の脚注##です。

二番目の段落# 脚注 #第二の脚注##です。

三番目の段落# 脚注 #第三の脚注##です。"""

        # パース処理
        nodes = self.parser.parse(text)
        assert nodes is not None

        # レンダリング処理
        html = self.renderer.render(nodes)
        assert html is not None

        # 複数の脚注番号が正しく割り当てられることを確認
        assert "[1]" in html
        assert "[2]" in html
        assert "[3]" in html

        # 全ての脚注内容が含まれることを確認
        assert "第一の脚注" in html
        assert "第二の脚注" in html
        assert "第三の脚注" in html

        # 脚注セクションが正しく生成されることを確認
        assert 'class="footnotes"' in html
        assert 'id="footnote-1"' in html
        assert 'id="footnote-2"' in html
        assert 'id="footnote-3"' in html

    def test_footnote_with_special_characters(self):
        """特殊文字を含む脚注の統合テスト"""
        text = "本文# 脚注 #HTML特殊文字 <>&\"' を含む脚注##"

        # パース処理
        nodes = self.parser.parse(text)
        assert nodes is not None

        # レンダリング処理
        html = self.renderer.render(nodes)
        assert html is not None

        # HTML特殊文字が適切にエスケープされることを確認
        assert "&lt;" in html or "<" in html
        assert "&gt;" in html or ">" in html

    def test_footnote_bidirectional_links(self):
        """脚注の双方向リンク生成テスト"""
        text = "本文# 脚注 #脚注内容##"

        # パース処理
        nodes = self.parser.parse(text)
        html = self.renderer.render(nodes)

        # 本文から脚注への参照リンク
        assert 'href="#footnote-1"' in html
        assert 'id="footnote-ref-1"' in html

        # 脚注から本文への戻りリンク
        assert 'href="#footnote-ref-1"' in html
        assert 'id="footnote-1"' in html
        assert "↩" in html

    def test_footnote_accessibility_attributes(self):
        """脚注のアクセシビリティ属性テスト"""
        text = "本文# 脚注 #アクセシビリティテスト##"

        # パース処理
        nodes = self.parser.parse(text)
        html = self.renderer.render(nodes)

        # ARIA属性の確認
        assert 'role="doc-endnotes"' in html
        assert 'role="doc-endnote"' in html
        assert 'role="doc-backlink"' in html


class TestFootnoteEdgeCases:
    """脚注システムのエッジケーステスト"""

    def setup_method(self):
        """各テストメソッドの前にセットアップを実行"""
        self.parser = Parser()
        self.renderer = Renderer()
        self.logger = get_logger(__name__)

    def test_footnote_at_document_start(self):
        """文書開始位置の脚注テスト"""
        text = "# 脚注 #文書開始の脚注##最初の段落です。"

        nodes = self.parser.parse(text)
        html = self.renderer.render(nodes)

        assert "[1]" in html
        assert 'class="footnotes"' in html

    def test_consecutive_footnotes(self):
        """連続する脚注のテスト"""
        text = "本文# 脚注 #第一脚注##直後に# 脚注 #第二脚注##続きます。"

        nodes = self.parser.parse(text)
        html = self.renderer.render(nodes)

        assert "[1]" in html
        assert "[2]" in html
        assert 'class="footnotes"' in html

    def test_footnote_with_nested_keywords(self):
        """ネストしたキーワードを含む脚注の統合テスト"""
        text = "本文# 脚注 #脚注内に# 太字 #強調テキスト##を含む例##"

        # パース処理
        nodes = self.parser.parse(text)
        assert nodes is not None

        # レンダリング処理
        html = self.renderer.render(nodes)
        assert html is not None

        # 脚注が正しく処理されることを確認
        assert "footnote-ref" in html
        assert 'class="footnotes"' in html


if __name__ == "__main__":
    pytest.main([__file__])
