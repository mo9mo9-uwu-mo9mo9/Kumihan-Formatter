"""
__init__.py ファイル群のテスト
"""

import pytest


class TestParsersInit:
    """parsers/__init__.py テスト"""

    def test_parsers_init_import(self):
        """parsers/__init__.py は再エクスポートしない（Phase 2）"""
        import importlib
        import sys
        import types
        import pytest

        # 直接モジュールからのimportは成功する
        from kumihan_formatter.parsers.unified_list_parser import UnifiedListParser  # noqa: F401

        # トップレベルからの再エクスポートは不可（ImportError想定）
        with pytest.raises(ImportError):
            from kumihan_formatter import parsers as _p  # noqa: F401
            from kumihan_formatter.parsers import UnifiedListParser as _u  # type: ignore # noqa: F401

    def test_parsers_init_all(self):
        """parsers/__init__.py の__all__テスト"""
        import kumihan_formatter.parsers as parsers_module

        assert hasattr(parsers_module, "__all__")
        assert "UnifiedListParser" not in parsers_module.__all__


class TestCoreInit:
    """core/__init__.py テスト"""

    def test_core_init_import(self):
        """core/__init__.py のimportテスト"""
        import kumihan_formatter.core

        # モジュール自体のimportが成功することを確認
        assert kumihan_formatter.core is not None
