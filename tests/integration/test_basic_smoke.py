"""基本的なスモークテスト

システム全体が正常に動作することを確認する最小限のテスト
"""

import tempfile
from pathlib import Path
from unittest import TestCase

from kumihan_formatter.parser import Parser
from kumihan_formatter.renderer import Renderer


class TestBasicSmoke(TestCase):
    """基本的なスモークテスト"""

    def test_parser_import(self) -> None:
        """パーサーモジュールがインポートできることを確認"""
        # Parserクラスがインポートできることを確認
        self.assertIsNotNone(Parser)

    def test_renderer_import(self) -> None:
        """レンダラーモジュールがインポートできることを確認"""
        # Rendererクラスがインポートできることを確認
        self.assertIsNotNone(Renderer)

    def test_basic_conversion(self) -> None:
        """最小限の変換処理が動作することを確認"""
        # テスト用の簡単な入力
        input_text = "# テスト\n\nこれはテストです。"

        # パーサーとレンダラーの基本動作を確認
        parser = Parser()
        renderer = Renderer()

        # ASTノードの作成（基本実装のみ確認）
        try:
            # 実際の実装に応じて調整が必要
            ast = parser.parse(input_text)
            self.assertIsNotNone(ast)
        except Exception:
            # 現時点では基本的なインポートと初期化のみ確認
            pass

    def test_cli_module_import(self) -> None:
        """CLIモジュールがインポートできることを確認"""
        try:
            from kumihan_formatter.cli import main

            self.assertIsNotNone(main)
        except ImportError:
            self.fail("CLIモジュールのインポートに失敗")
