"""Unit tests for Kumihan-Formatter footnote keyword system."""

import pytest

from kumihan_formatter.core.parsing.keyword.definitions import KeywordDefinitions
from kumihan_formatter.core.utilities.logger import get_logger


class TestFootnoteKeywordParsing:
    """新記法脚注キーワードのパース処理テスト"""

    def setup_method(self):
        """各テストメソッドの前にセットアップを実行"""
        self.keyword_definitions = KeywordDefinitions()
        self.logger = get_logger(__name__)

    def test_footnote_keyword_exists(self):
        """脚注キーワードが定義されていることを確認"""
        assert self.keyword_definitions.is_valid_keyword("脚注")

    def test_footnote_keyword_info(self):
        """脚注キーワードの定義情報を確認"""
        info = self.keyword_definitions.get_keyword_info("脚注")
        assert info is not None
        assert info["tag"] == "span"
        assert info["class"] == "footnote"
        assert info["special_handler"] == "footnote"

    def test_footnote_keyword_tag(self):
        """脚注キーワードのHTMLタグを確認"""
        tag = self.keyword_definitions.get_tag_for_keyword("脚注")
        assert tag == "span"

    def test_footnote_keyword_normalization(self):
        """脚注キーワードの正規化処理を確認"""
        normalized = self.keyword_definitions.normalize_keyword("  脚注  ")
        assert normalized == "脚注"

    def test_footnote_keyword_in_all_keywords(self):
        """全キーワードリストに脚注が含まれることを確認"""
        all_keywords = self.keyword_definitions.get_all_keywords()
        assert "脚注" in all_keywords

    def test_footnote_special_handler_detection(self):
        """脚注のspecial_handler指定を確認"""
        info = self.keyword_definitions.get_keyword_info("脚注")
        assert info is not None
        assert "special_handler" in info
        assert info["special_handler"] == "footnote"


if __name__ == "__main__":
    pytest.main([__file__])
