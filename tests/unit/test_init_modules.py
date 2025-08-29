"""
__init__.py ファイル群のテスト
"""

import pytest


class TestParsersInit:
    """parsers/__init__.py テスト"""

    def test_parsers_init_import(self):
        """parsers/__init__.py のimportテスト"""
        from kumihan_formatter.parsers import UnifiedListParser

        assert UnifiedListParser is not None
        assert hasattr(UnifiedListParser, "__init__")

    def test_parsers_init_all(self):
        """parsers/__init__.py の__all__テスト"""
        import kumihan_formatter.parsers as parsers_module

        assert hasattr(parsers_module, "__all__")
        assert "UnifiedListParser" in parsers_module.__all__


class TestCoreInit:
    """core/__init__.py テスト"""

    def test_core_init_import(self):
        """core/__init__.py のimportテスト"""
        import kumihan_formatter.core

        # モジュール自体のimportが成功することを確認
        assert kumihan_formatter.core is not None
