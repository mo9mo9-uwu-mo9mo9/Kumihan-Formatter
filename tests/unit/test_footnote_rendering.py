"""Unit tests for Kumihan-Formatter footnote rendering system."""

import pytest
from kumihan_formatter.core.rendering.html_formatter import (
    HTMLFormatter,
    FootnoteManager,
)
from kumihan_formatter.core.utilities.logger import get_logger


# mypy: ignore-errors
# Test with mocking type issues - strategic ignore for rapid error reduction


class TestFootnoteRendering:
    """脚注レンダリング処理テスト"""

    def setup_method(self):
        """各テストメソッドの前にセットアップを実行"""
        self.html_formatter = HTMLFormatter()
        self.logger = get_logger(__name__)

    def test_basic_footnote_handling(self):
        """基本的な脚注処理のテスト"""
        content = "これは基本的な脚注です"
        result = self.html_formatter._handle_footnote(content, {})

        assert '<sup><a href="#footnote-1"' in result
        assert 'class="footnote-ref"' in result
        assert "[1]</a></sup>" in result

    def test_footnote_with_html_content(self):
        """HTMLタグを含む脚注のテスト"""
        content = "HTMLタグを含む<strong>脚注</strong>"
        result = self.html_formatter._handle_footnote(content, {})

        assert '<sup><a href="#footnote-1"' in result
        assert 'class="footnote-ref"' in result
        assert "[1]</a></sup>" in result

    def test_multiple_footnotes_numbering(self):
        """複数脚注の番号管理テスト"""
        # 新しいHTMLFormatterインスタンスで番号リセット
        formatter = HTMLFormatter()

        content1 = "最初の脚注"
        content2 = "二番目の脚注"

        result1 = formatter._handle_footnote(content1, {})
        result2 = formatter._handle_footnote(content2, {})

        assert "[1]</a></sup>" in result1
        assert "[2]</a></sup>" in result2

    def test_footnote_special_handler_processing(self):
        """special_handlerキーワード処理のテスト"""
        content = "特殊ハンドラーテスト"
        result = self.html_formatter.handle_special_element("脚注", content, {})

        assert '<sup><a href="#footnote-' in result
        assert 'class="footnote-ref"' in result

    def test_footnote_error_fallback(self):
        """脚注エラー時のフォールバック処理テスト"""
        # 空のコンテンツでも正常に処理される
        result = self.html_formatter._handle_footnote("", {})
        assert '<sup><a href="#footnote-' in result
        assert 'class="footnote-ref"' in result


class TestFootnoteManager:
    """FootnoteManagerクラステスト"""

    def setup_method(self):
        """各テストメソッドの前にセットアップを実行"""
        self.footnote_manager = FootnoteManager()
        self.logger = get_logger(__name__)

    def test_footnote_registration(self):
        """FootnoteManagerでの脚注登録テスト"""
        footnotes = [
            {"content": "第一の脚注", "number": None},
            {"content": "第二の脚注", "number": None},
        ]

        processed = self.footnote_manager.register_footnotes(footnotes)

        assert len(processed) == 2
        assert processed[0]["global_number"] == 1
        assert processed[1]["global_number"] == 2

    def test_footnote_storage_retrieval(self):
        """脚注ストレージからの取得テスト"""
        footnotes = [{"content": "保存テスト脚注", "number": None}]
        self.footnote_manager.register_footnotes(footnotes)

        all_footnotes = self.footnote_manager.get_all_footnotes()
        assert len(all_footnotes) == 1
        assert all_footnotes[0]["content"] == "保存テスト脚注"
        assert all_footnotes[0]["global_number"] == 1

    def test_footnote_counter_reset(self):
        """脚注カウンターリセットテスト"""
        footnotes = [{"content": "リセット前脚注", "number": None}]
        self.footnote_manager.register_footnotes(footnotes)

        # カウンターリセット
        self.footnote_manager.reset_counter()

        new_footnotes = [{"content": "リセット後脚注", "number": None}]
        processed = self.footnote_manager.register_footnotes(new_footnotes)

        assert processed[0]["global_number"] == 1
        assert len(self.footnote_manager.get_all_footnotes()) == 1

    def test_footnote_html_generation(self):
        """脚注HTML生成テスト"""
        footnotes = [{"content": "テスト脚注", "global_number": 1}]

        html = self.footnote_manager.generate_footnote_html(footnotes)

        assert '<div class="footnotes">' in html
        assert "<ol>" in html
        assert 'id="footnote-1"' in html
        assert "テスト脚注" in html
        assert 'href="#footnote-ref-1"' in html
        assert "↩</a>" in html

    def test_footnote_data_validation(self):
        """脚注データ検証テスト"""
        # 有効なデータ
        valid_footnotes = [{"content": "有効な脚注"}]
        is_valid, errors = self.footnote_manager.validate_footnote_data(valid_footnotes)
        assert is_valid
        assert len(errors) == 0

        # 無効なデータ
        invalid_footnotes = [{"content": ""}]  # 空のコンテンツ
        is_valid, errors = self.footnote_manager.validate_footnote_data(
            invalid_footnotes
        )
        assert not is_valid
        assert len(errors) > 0

    def test_safe_footnote_html_generation(self):
        """安全な脚注HTML生成テスト"""
        footnotes = [{"content": "安全なテスト脚注", "global_number": 1}]

        html, errors = self.footnote_manager.safe_generate_footnote_html(footnotes)

        assert len(errors) == 0
        assert html
        assert 'role="doc-endnotes"' in html
        assert 'role="doc-endnote"' in html
        assert 'role="doc-backlink"' in html

    def test_multiple_footnotes_html_output(self):
        """複数脚注のHTML出力テスト"""
        footnotes = [
            {"content": "第一脚注", "global_number": 1},
            {"content": "第二脚注", "global_number": 2},
            {"content": "第三脚注", "global_number": 3},
        ]

        html = self.footnote_manager.generate_footnote_html(footnotes)

        assert 'id="footnote-1"' in html
        assert 'id="footnote-2"' in html
        assert 'id="footnote-3"' in html
        assert "第一脚注" in html
        assert "第二脚注" in html
        assert "第三脚注" in html


class TestFootnoteErrorHandling:
    """脚注エラーハンドリングテスト"""

    def setup_method(self):
        """各テストメソッドの前にセットアップを実行"""
        self.html_formatter = HTMLFormatter()
        self.footnote_manager = FootnoteManager()
        self.logger = get_logger(__name__)

    def test_empty_footnote_content(self):
        """空の脚注コンテンツのエラーハンドリング"""
        result = self.html_formatter._handle_footnote("", {})
        # 空のコンテンツでも正常に脚注リンクが生成される
        assert '<sup><a href="#footnote-' in result
        assert 'class="footnote-ref"' in result

    def test_invalid_footnote_data_structure(self):
        """無効な脚注データ構造のエラーハンドリング"""
        invalid_data = "文字列（辞書ではない）"
        is_valid, errors = self.footnote_manager.validate_footnote_data([invalid_data])

        assert not is_valid
        assert len(errors) > 0
        assert "辞書形式" in errors[0]

    def test_footnote_content_too_long(self):
        """脚注コンテンツが長すぎる場合のエラーハンドリング"""
        long_content = "a" * 2001  # 2000文字を超える
        footnotes = [{"content": long_content}]

        is_valid, errors = self.footnote_manager.validate_footnote_data(footnotes)
        assert not is_valid
        assert any("長すぎます" in error for error in errors)

    def test_missing_required_fields(self):
        """必須フィールドが不足している場合のエラーハンドリング"""
        footnotes = [{}]  # contentフィールドなし

        is_valid, errors = self.footnote_manager.validate_footnote_data(footnotes)
        assert not is_valid
        assert any("content" in error for error in errors)

    def test_footnote_validation_with_invalid_number(self):
        """無効な番号を持つ脚注の検証テスト"""
        footnotes = [{"content": "テスト", "number": -1}]  # 無効な番号

        is_valid, errors = self.footnote_manager.validate_footnote_data(footnotes)
        assert not is_valid
        assert any("1以上の整数" in error for error in errors)

    def test_safe_html_generation_with_errors(self):
        """エラーがある場合の安全なHTML生成テスト"""
        invalid_footnotes = [{"content": ""}]  # 無効なデータ

        html, errors = self.footnote_manager.safe_generate_footnote_html(
            invalid_footnotes
        )

        assert html == ""  # エラー時は空文字列
        assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__])
