#!/usr/bin/env python3
"""
Kumihan Formatter プレイグラウンド機能テスト
Issue #580 - ドキュメント改善 Phase 2

プレイグラウンド機能の動作確認テスト
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# プレイグラウンドモジュールのインポート（動的）
playground_dir = PROJECT_ROOT / "docs" / "playground"
sys.path.insert(0, str(playground_dir))

# FastAPIテスト用
try:
    from fastapi.testclient import TestClient

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class TestPlaygroundFunctionality(unittest.TestCase):
    """プレイグラウンド機能の基本テスト"""

    def setUp(self):
        """テスト前準備"""
        self.playground_dir = PROJECT_ROOT / "docs" / "playground"
        self.server_file = self.playground_dir / "server.py"
        self.start_script = self.playground_dir / "start_playground.py"

    def test_playground_files_exist(self):
        """プレイグラウンドファイルの存在確認"""
        # 必須ファイルの存在確認
        required_files = [
            "server.py",
            "start_playground.py",
            "README.md",
            "templates/playground.html",
            "static/playground.css",
            "static/playground.js",
        ]

        for file_path in required_files:
            full_path = self.playground_dir / file_path
            self.assertTrue(
                full_path.exists(), f"Required playground file missing: {file_path}"
            )

    def test_server_file_structure(self):
        """サーバーファイルの構造確認"""
        self.assertTrue(self.server_file.exists())

        # ファイル内容の基本確認
        content = self.server_file.read_text(encoding="utf-8")

        # 必須要素の存在確認
        required_elements = [
            "from fastapi import FastAPI",
            "app = FastAPI",
            "/api/convert",
            "/api/metrics/session",
            "/api/metrics/summary",
            'if __name__ == "__main__":',
        ]

        for element in required_elements:
            self.assertIn(
                element, content, f"Required element not found in server.py: {element}"
            )

    def test_start_script_structure(self):
        """起動スクリプトの構造確認"""
        self.assertTrue(self.start_script.exists())

        content = self.start_script.read_text(encoding="utf-8")

        # 必須要素の存在確認
        required_elements = [
            "def main():",
            "fastapi",
            "uvicorn",
            "subprocess",
            "webbrowser",
        ]

        for element in required_elements:
            self.assertIn(
                element,
                content,
                f"Required element not found in start_playground.py: {element}",
            )

    def test_html_template_structure(self):
        """HTMLテンプレートの構造確認"""
        template_file = self.playground_dir / "templates" / "playground.html"
        self.assertTrue(template_file.exists())

        content = template_file.read_text(encoding="utf-8")

        # 必須HTML要素の確認
        required_elements = [
            "<!DOCTYPE html>",
            "kumihan-input",
            "preview-content",
            "mermaid",
            "metrics-dashboard",
            "playground.js",
            "playground.css",
        ]

        for element in required_elements:
            self.assertIn(
                element, content, f"Required HTML element not found: {element}"
            )

    def test_css_structure(self):
        """CSSファイルの構造確認"""
        css_file = self.playground_dir / "static" / "playground.css"
        self.assertTrue(css_file.exists())

        content = css_file.read_text(encoding="utf-8")

        # 必須CSSクラスの確認
        required_classes = [
            ".playground-container",
            ".input-panel",
            ".preview-panel",
            ".mermaid-container",
            ".metrics-dashboard",
            "@media (max-width: 768px)",  # レスポンシブ対応
        ]

        for css_class in required_classes:
            self.assertIn(
                css_class, content, f"Required CSS class not found: {css_class}"
            )

    def test_javascript_structure(self):
        """JavaScriptファイルの構造確認"""
        js_file = self.playground_dir / "static" / "playground.js"
        self.assertTrue(js_file.exists())

        content = js_file.read_text(encoding="utf-8")

        # 必須JavaScript要素の確認
        required_elements = [
            "class KumihanPlayground",
            "convertText",
            "handleInput",
            "sendGAEvent",
            "debounce",
            "mermaid",
            "fetch('/api/convert'",
        ]

        for element in required_elements:
            self.assertIn(
                element, content, f"Required JavaScript element not found: {element}"
            )

    def test_file_line_limits(self):
        """ファイル行数制限（300行）の確認"""
        files_to_check = [
            "server.py",
            "start_playground.py",
            "templates/playground.html",
            "static/playground.css",
            "static/playground.js",
            "static/base.css",
            "static/components.css",
            "static/responsive.css",
            "static/playground-core.js",
            "static/playground-features.js",
            "static/playground-metrics.js",
        ]

        for file_path in files_to_check:
            full_path = self.playground_dir / file_path
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8") as f:
                    line_count = len(f.readlines())

                self.assertLessEqual(
                    line_count,
                    300,
                    f"File {file_path} exceeds 300 line limit: {line_count} lines",
                )

    def test_readme_completeness(self):
        """READMEファイルの完全性確認"""
        readme_file = self.playground_dir / "README.md"
        self.assertTrue(readme_file.exists())

        content = readme_file.read_text(encoding="utf-8")

        # 必須セクションの確認
        required_sections = [
            "# 🎮 Kumihan Formatter Playground",
            "## 🌟 概要",
            "## 🚀 クイックスタート",
            "## 🎯 使用方法",
            "## 📊 DX指標について",
            "## 🎨 技術構成",
            "## 🔧 開発者向け情報",
        ]

        for section in required_sections:
            self.assertIn(
                section, content, f"Required README section not found: {section}"
            )


class TestPlaygroundIntegration(unittest.TestCase):
    """プレイグラウンド統合テスト（FastAPI依存）"""

    def setUp(self):
        """テスト前準備"""
        self.playground_dir = PROJECT_ROOT / "docs" / "playground"

    @unittest.skipUnless(FASTAPI_AVAILABLE, "FastAPI not available")
    def test_api_endpoints_exist(self):
        """APIエンドポイントの存在確認"""
        # 動的インポートでサーバーモジュールを読み込み
        try:
            sys.path.insert(0, str(self.playground_dir))
            import server

            # FastAPI appインスタンス確認
            self.assertTrue(hasattr(server, "app"))

            # TestClient作成
            client = TestClient(server.app)

            # ヘルスチェックエンドポイント
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)

            # メトリクスサマリーエンドポイント
            response = client.get("/api/metrics/summary")
            self.assertEqual(response.status_code, 200)

        except ImportError as e:
            self.skipTest(f"Server module import failed: {e}")

    def test_conversion_api_structure(self):
        """変換API構造の確認"""
        server_file = self.playground_dir / "server.py"
        content = server_file.read_text(encoding="utf-8")

        # 変換API関連の必須要素
        required_elements = [
            '@app.post("/api/convert")',
            'kumihan_text = data.get("text"',
            "parser.parse",
            "renderer.render",
            "processing_time",
        ]

        for element in required_elements:
            self.assertIn(
                element,
                content,
                f"Required conversion API element not found: {element}",
            )


class TestDXMetricsFeature(unittest.TestCase):
    """DX指標機能のテスト"""

    def test_metrics_data_structure(self):
        """メトリクスデータ構造の確認"""
        server_file = PROJECT_ROOT / "docs" / "playground" / "server.py"
        content = server_file.read_text(encoding="utf-8")

        # DX指標関連の必須要素
        required_elements = [
            "dx_metrics = {",
            '"sessions":',
            '"conversions":',
            '"errors":',
            '"performance":',
        ]

        for element in required_elements:
            self.assertIn(
                element, content, f"Required DX metrics element not found: {element}"
            )

    def test_ga4_integration(self):
        """Google Analytics 4統合の確認"""
        template_file = (
            PROJECT_ROOT / "docs" / "playground" / "templates" / "playground.html"
        )
        content = template_file.read_text(encoding="utf-8")

        # GA4統合関連要素
        ga4_elements = ["gtag/js", "gtag('js'", "gtag('config'"]

        for element in ga4_elements:
            self.assertIn(
                element, content, f"Required GA4 element not found: {element}"
            )


class TestMermaidIntegration(unittest.TestCase):
    """Mermaid図表統合のテスト"""

    def test_mermaid_integration(self):
        """Mermaid統合の確認"""
        template_file = (
            PROJECT_ROOT / "docs" / "playground" / "templates" / "playground.html"
        )
        content = template_file.read_text(encoding="utf-8")

        # Mermaid関連要素
        mermaid_elements = ["mermaid@", "mermaid-container", "mermaid-content"]

        for element in mermaid_elements:
            self.assertIn(
                element, content, f"Required Mermaid element not found: {element}"
            )

    def test_mermaid_javascript_logic(self):
        """MermaidJavaScript機能の確認"""
        js_file = PROJECT_ROOT / "docs" / "playground" / "static" / "playground.js"
        content = js_file.read_text(encoding="utf-8")

        # Mermaid JavaScript機能
        required_functions = [
            "checkForMermaidContent",
            "generateMermaidDiagram",
            "mermaidKeywords",
            "mermaid.init",
        ]

        for func in required_functions:
            self.assertIn(
                func, content, f"Required Mermaid JS function not found: {func}"
            )


if __name__ == "__main__":
    # テスト実行設定
    unittest.main(verbosity=2, exit=False)

    print("\n" + "=" * 50)
    print("🎮 Playground Functionality Tests Completed!")
    print("Issue #580 - ドキュメント改善 Phase 2")
    print("=" * 50)
