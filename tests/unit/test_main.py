"""
__main__.py テスト
"""

import pytest


class TestMainModule:
    """__main__.py モジュールテスト"""

    def test_main_module_import(self):
        """__main__.py のimport動作テスト"""
        import kumihan_formatter.__main__ as main_module

        # importが成功することを確認
        assert hasattr(main_module, "main")

    def test_main_module_execution(self):
        """__main__.py の直接実行テスト"""
        import unittest.mock as mock

        # unified_api.mainをmockして、importのテスト（cliは存在しないため）
        with mock.patch("kumihan_formatter.unified_api.main"):
            from kumihan_formatter.__main__ import main

            # main関数が正しくimportされることを確認
            assert callable(main)
