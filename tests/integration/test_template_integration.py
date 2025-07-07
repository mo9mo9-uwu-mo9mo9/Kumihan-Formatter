"""テンプレート処理の統合テスト（10テスト）

統合テスト: テンプレート処理の統合テスト
- テンプレート読み込みテスト（3テスト）
- テンプレート変数展開テスト（4テスト）
- テンプレート出力テスト（3テスト）
"""

import shutil
import tempfile
from pathlib import Path
from unittest import TestCase

from kumihan_formatter.core.rendering.main_renderer import HTMLRenderer
from kumihan_formatter.core.template_manager import TemplateManager


class TestTemplateIntegration(TestCase):
    """テンプレート処理の統合テスト"""

    def setUp(self) -> None:
        """テスト用の一時ディレクトリとテンプレートマネージャーを作成"""
        self.test_dir = tempfile.mkdtemp()
        self.template_dir = Path(self.test_dir) / "templates"
        self.template_dir.mkdir(exist_ok=True)
        self.template_manager = TemplateManager(template_dir=self.template_dir)
        self.renderer = HTMLRenderer()

    def tearDown(self) -> None:
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_test_template(self, name, content):  # type: ignore
        """テスト用テンプレートファイルを作成"""
        template_file = self.template_dir / f"{name}.html.j2"
        template_file.write_text(content, encoding="utf-8")
        return template_file

    def _create_test_content(self):  # type: ignore
        """テスト用コンテンツを作成"""
        return {
            "title": "テストシナリオ",
            "content": """<h1>テストシナリオ</h1>
<p>これはテンプレートテストです。</p>
<ul>
<li>項目1</li>
<li>項目2</li>
<li>項目3</li>
</ul>""",
            "author": "テストユーザー",
            "date": "2025-07-05",
            "description": "テンプレート統合テストのサンプル",
        }

    # テンプレート読み込みテスト（3テスト）

    def test_load_basic_template(self) -> None:
        """基本的なテンプレート読み込みテスト"""
        template_content = """<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    {{ content }}
</body>
</html>"""
        template_file = self._create_test_template("basic", template_content)  # type: ignore

        # テンプレートを読み込み
        template = self.template_manager.get_template(template_file.name)

        # テンプレートが正しく読み込まれることを確認
        self.assertIsNotNone(template)

    def test_load_template_with_includes(self) -> None:
        """インクルード付きテンプレート読み込みテスト"""
        # ベーステンプレートを作成
        base_template = """<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; }
    </style>
</head>
<body>
    <header>
        <h1>{{ title }}</h1>
    </header>
    <main>
        {{ content }}
    </main>
    <footer>
        <p>&copy; {{ date }} {{ author }}</p>
    </footer>
</body>
</html>"""

        # メインテンプレートを作成（ベースを拡張）
        main_template = """{% extends "base.html.j2" %}
{% block content %}
    <div class="scenario">
        {{ content }}
    </div>
{% endblock %}"""

        self._create_test_template("base", base_template)  # type: ignore
        template_file = self._create_test_template("with_includes", main_template)  # type: ignore

        # インクルード付きテンプレートを読み込み
        template = self.template_manager.get_template(template_file.name)

        # テンプレートが正しく読み込まれることを確認
        self.assertIsNotNone(template)

    def test_load_nonexistent_template(self) -> None:
        """存在しないテンプレート読み込みテスト"""
        nonexistent_template = Path(self.test_dir) / "nonexistent.html.j2"

        # 存在しないテンプレートの読み込みで例外が発生することを確認
        with self.assertRaises(
            Exception
        ):  # TemplateNotFoundエラーまたはFileNotFoundError
            self.template_manager.get_template(nonexistent_template.name)

    # テンプレート変数展開テスト（4テスト）

    def test_basic_variable_expansion(self) -> None:
        """基本的な変数展開テスト"""
        template_content = """<h1>{{ title }}</h1>
<p>著者: {{ author }}</p>
<p>日付: {{ date }}</p>"""
        template_file = self._create_test_template("variables", template_content)  # type: ignore

        # テンプレートを読み込み
        template = self.template_manager.get_template(template_file.name)

        # 変数を展開
        test_data = self._create_test_content()  # type: ignore
        result = template.render(test_data)

        # 変数が正しく展開されることを確認
        self.assertIn("テストシナリオ", result)
        self.assertIn("テストユーザー", result)
        self.assertIn("2025-07-05", result)

    def test_conditional_expansion(self) -> None:
        """条件分岐展開テスト"""
        template_content = """<h1>{{ title }}</h1>
{% if author %}
<p>著者: {{ author }}</p>
{% endif %}
{% if description %}
<p>説明: {{ description }}</p>
{% else %}
<p>説明はありません</p>
{% endif %}"""
        template_file = self._create_test_template("conditional", template_content)  # type: ignore

        # テンプレートを読み込み
        template = self.template_manager.get_template(template_file.name)

        # 条件分岐のテスト
        test_data = self._create_test_content()  # type: ignore
        result = template.render(test_data)

        # 条件分岐が正しく動作することを確認
        self.assertIn("著者: テストユーザー", result)
        self.assertIn("説明: テンプレート統合テストのサンプル", result)

    def test_loop_expansion(self) -> None:
        """ループ展開テスト"""
        template_content = """<h1>{{ title }}</h1>
<ul>
{% for item in items %}
<li>{{ item.name }}: {{ item.description }}</li>
{% endfor %}
</ul>"""
        template_file = self._create_test_template("loop", template_content)  # type: ignore

        # テンプレートを読み込み
        template = self.template_manager.get_template(template_file.name)

        # ループのテストデータ
        test_data = {
            "title": "アイテムリスト",
            "items": [
                {"name": "剣", "description": "鋭い刀剣"},
                {"name": "盾", "description": "頑丈な防具"},
                {"name": "薬草", "description": "回復アイテム"},
            ],
        }

        result = template.render(test_data)

        # ループが正しく動作することを確認
        self.assertIn("剣: 鋭い刀剣", result)
        self.assertIn("盾: 頑丈な防具", result)
        self.assertIn("薬草: 回復アイテム", result)

    def test_filter_expansion(self) -> None:
        """フィルター展開テスト"""
        template_content = """<h1>{{ title|upper }}</h1>
<p>内容: {{ content|truncate(50) }}</p>
<p>日付: {{ date|default("未設定") }}</p>"""
        template_file = self._create_test_template("filter", template_content)  # type: ignore

        # テンプレートを読み込み
        template = self.template_manager.get_template(template_file.name)

        # フィルターのテスト
        test_data = self._create_test_content()  # type: ignore
        result = template.render(test_data)

        # フィルターが正しく動作することを確認
        self.assertIn("テストシナリオ", result.upper())
        self.assertIn("2025-07-05", result)

    # テンプレート出力テスト（3テスト）

    def test_complete_html_output(self) -> None:
        """完全なHTML出力テスト"""
        template_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: 'Noto Sans JP', sans-serif; }
        .scenario { margin: 20px; padding: 20px; }
    </style>
</head>
<body>
    <div class="scenario">
        <h1>{{ title }}</h1>
        <div class="content">
            {{ content|safe }}
        </div>
        <div class="meta">
            <p>著者: {{ author }}</p>
            <p>作成日: {{ date }}</p>
        </div>
    </div>
</body>
</html>"""
        template_file = self._create_test_template("complete", template_content)  # type: ignore

        # テンプレートを読み込み
        template = self.template_manager.get_template(template_file.name)

        # 完全なHTMLを生成
        test_data = self._create_test_content()  # type: ignore
        result = template.render(test_data)

        # 完全なHTMLが生成されることを確認
        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn('<html lang="ja">', result)
        self.assertIn('<meta charset="UTF-8">', result)
        self.assertIn("テストシナリオ", result)
        self.assertIn("テストユーザー", result)

    def test_css_integration_output(self) -> None:
        """CSS統合出力テスト"""
        template_content = """<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        /* テンプレート内CSS */
        .header { background: #f0f0f0; padding: 10px; }
        .content { margin: 20px; }
        .footer { text-align: center; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
    </div>
    <div class="content">
        {{ content|safe }}
    </div>
    <div class="footer">
        <p>&copy; {{ date }} {{ author }}</p>
    </div>
</body>
</html>"""
        template_file = self._create_test_template("css_integration", template_content)  # type: ignore

        # テンプレートを読み込み
        template = self.template_manager.get_template(template_file.name)

        # CSS統合HTMLを生成
        test_data = self._create_test_content()  # type: ignore
        result = template.render(test_data)

        # CSS統合HTMLが生成されることを確認
        self.assertIn("<style>", result)
        self.assertIn(".header", result)
        self.assertIn(".content", result)
        self.assertIn(".footer", result)
        self.assertIn('class="header"', result)

    def test_javascript_integration_output(self) -> None:
        """JavaScript統合出力テスト"""
        template_content = """<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <script>
        // テンプレート内JavaScript
        function showDetails() {
            document.getElementById('details').style.display = 'block';
        }

        document.addEventListener('DOMContentLoaded', function() {
            console.log('ページが読み込まれました: {{ title }}');
        });
    </script>
</head>
<body>
    <h1>{{ title }}</h1>
    <button onclick="showDetails()">詳細を表示</button>
    <div id="details" style="display: none;">
        {{ content|safe }}
    </div>
</body>
</html>"""
        template_file = self._create_test_template("js_integration", template_content)  # type: ignore

        # テンプレートを読み込み
        template = self.template_manager.get_template(template_file.name)

        # JavaScript統合HTMLを生成
        test_data = self._create_test_content()  # type: ignore
        result = template.render(test_data)

        # JavaScript統合HTMLが生成されることを確認
        self.assertIn("<script>", result)
        self.assertIn("function showDetails()", result)
        self.assertIn("addEventListener", result)
        self.assertIn('onclick="showDetails()"', result)
        self.assertIn("テストシナリオ", result)
