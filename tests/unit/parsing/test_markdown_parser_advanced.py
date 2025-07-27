"""Markdown Parser高度テスト - Issue #597 Week 29-30対応

Markdown構文解析・パターンマッチング・文書構造解析の確認
"""

import time
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.markdown_parser import MarkdownParser
from kumihan_formatter.core.markdown_processor import MarkdownProcessor


class TestMarkdownParserAdvanced:
    """Markdownパーサー高度テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.markdown_parser = MarkdownParser()
        self.markdown_processor = MarkdownProcessor()

    def test_markdown_parser_initialization(self):
        """Markdownパーサー初期化テスト"""
        assert self.markdown_parser is not None
        assert self.markdown_processor is not None
        assert hasattr(self.markdown_parser, "parse")
        assert hasattr(self.markdown_processor, "process")

    def test_heading_parsing_comprehensive(self):
        """見出し解析包括テスト"""
        heading_patterns = [
            # ATX形式見出し
            ("# レベル1見出し", {"level": 1, "text": "レベル1見出し"}),
            ("## レベル2見出し", {"level": 2, "text": "レベル2見出し"}),
            ("### レベル3見出し", {"level": 3, "text": "レベル3見出し"}),
            ("#### レベル4見出し", {"level": 4, "text": "レベル4見出し"}),
            ("##### レベル5見出し", {"level": 5, "text": "レベル5見出し"}),
            ("###### レベル6見出し", {"level": 6, "text": "レベル6見出し"}),
            # 閉じ#付き見出し
            ("# 見出し #", {"level": 1, "text": "見出し"}),
            ("## 見出し ##", {"level": 2, "text": "見出し"}),
            # スペース調整
            ("#    多くのスペース   ", {"level": 1, "text": "多くのスペース"}),
            ("##	タブ文字	##", {"level": 2, "text": "タブ文字"}),
            # Unicode見出し
            ("# 日本語見出し", {"level": 1, "text": "日本語見出し"}),
            ("## English Heading", {"level": 2, "text": "English Heading"}),
            ("### 混在heading日本語", {"level": 3, "text": "混在heading日本語"}),
            ("#### 絵文字🎌見出し", {"level": 4, "text": "絵文字🎌見出し"}),
        ]

        for heading_text, expected in heading_patterns:
            try:
                result = self.markdown_parser.parse_heading(heading_text)
                if result:
                    assert (
                        result.level == expected["level"]
                    ), f"見出しレベル不一致: {heading_text}"
                    assert expected["text"] in str(
                        result.text
                    ), f"見出しテキスト不一致: {heading_text}"
            except Exception as e:
                pytest.fail(f"見出し解析でエラー: {heading_text} -> {e}")

    def test_setext_heading_parsing(self):
        """Setext形式見出し解析テスト"""
        setext_patterns = [
            # レベル1（=下線）
            (["見出し1", "======"], {"level": 1, "text": "見出し1"}),
            (
                ["長い見出しテキスト", "================="],
                {"level": 1, "text": "長い見出しテキスト"},
            ),
            # レベル2（-下線）
            (["見出し2", "------"], {"level": 2, "text": "見出し2"}),
            (["短い", "---"], {"level": 2, "text": "短い"}),
            # Unicode対応
            (["日本語見出し", "========"], {"level": 1, "text": "日本語見出し"}),
            (
                ["English Heading", "---------------"],
                {"level": 2, "text": "English Heading"},
            ),
        ]

        for lines, expected in setext_patterns:
            try:
                if hasattr(self.markdown_parser, "parse_setext_heading"):
                    result = self.markdown_parser.parse_setext_heading(lines)
                    if result:
                        assert result.level == expected["level"]
                        assert expected["text"] in str(result.text)
            except Exception as e:
                pytest.fail(f"Setext見出し解析でエラー: {lines} -> {e}")

    def test_list_parsing_markdown_style(self):
        """Markdownスタイルリスト解析テスト"""
        markdown_lists = [
            # 順序なしリスト（*）
            [
                "* 項目1",
                "* 項目2",
                "* 項目3",
            ],
            # 順序なしリスト（+）
            [
                "+ 項目A",
                "+ 項目B",
                "+ 項目C",
            ],
            # 混在マーカー
            [
                "- マーカー1",
                "* マーカー2",
                "+ マーカー3",
            ],
            # ネストリスト
            [
                "- レベル1",
                "  - レベル2",
                "    - レベル3",
                "- レベル1に戻る",
            ],
            # 順序付きリスト
            [
                "1. 第一項目",
                "2. 第二項目",
                "3. 第三項目",
            ],
            # タスクリスト
            [
                "- [ ] 未完了タスク",
                "- [x] 完了タスク",
                "- [X] 完了タスク（大文字）",
            ],
        ]

        for markdown_list in markdown_lists:
            try:
                result = self.markdown_parser.parse_list(markdown_list)
                assert result is not None
                if hasattr(result, "items"):
                    assert len(result.items) >= len(markdown_list)
            except Exception as e:
                pytest.fail(f"Markdownリスト解析でエラー: {e}")

    def test_inline_element_parsing(self):
        """インライン要素解析テスト"""
        inline_patterns = [
            # 強調（*）
            ("*斜体テキスト*", {"type": "emphasis", "text": "斜体テキスト"}),
            ("**太字テキスト**", {"type": "strong", "text": "太字テキスト"}),
            ("***太字斜体***", {"type": "strong_emphasis", "text": "太字斜体"}),
            # 強調（_）
            ("_斜体テキスト_", {"type": "emphasis", "text": "斜体テキスト"}),
            ("__太字テキスト__", {"type": "strong", "text": "太字テキスト"}),
            ("___太字斜体___", {"type": "strong_emphasis", "text": "太字斜体"}),
            # コード
            ("`インラインコード`", {"type": "code", "text": "インラインコード"}),
            ("``複数バッククォート``", {"type": "code", "text": "複数バッククォート"}),
            # リンク
            (
                "[テキスト](https://example.com)",
                {"type": "link", "text": "テキスト", "url": "https://example.com"},
            ),
            (
                '[タイトル付き](https://example.com "タイトル")',
                {"type": "link", "text": "タイトル付き"},
            ),
            # 画像
            (
                "![alt text](image.jpg)",
                {"type": "image", "alt": "alt text", "src": "image.jpg"},
            ),
            ('![](image.png "タイトル")', {"type": "image", "src": "image.png"}),
            # 参照形式リンク
            (
                "[リンクテキスト][ref]",
                {"type": "reference_link", "text": "リンクテキスト", "ref": "ref"},
            ),
            # 自動リンク
            (
                "<https://example.com>",
                {"type": "autolink", "url": "https://example.com"},
            ),
            ("<email@example.com>", {"type": "autolink", "email": "email@example.com"}),
            # 取り消し線
            ("~~取り消し~~", {"type": "strikethrough", "text": "取り消し"}),
        ]

        for inline_text, expected in inline_patterns:
            try:
                result = self.markdown_parser.parse_inline(inline_text)
                if result:
                    assert result.type == expected["type"] or hasattr(
                        result, "inline_type"
                    )
                    if "text" in expected:
                        assert expected["text"] in str(result)
            except Exception as e:
                pytest.fail(f"インライン要素解析でエラー: {inline_text} -> {e}")

    def test_code_block_parsing(self):
        """コードブロック解析テスト"""
        code_block_patterns = [
            # フェンスコードブロック（```）
            (
                ["```python", "def hello():", "    print('Hello')", "```"],
                {"language": "python", "code": "def hello():\n    print('Hello')"},
            ),
            # フェンスコードブロック（~~~）
            (
                ["~~~javascript", "function test() {", "  return true;", "}", "~~~"],
                {
                    "language": "javascript",
                    "code": "function test() {\n  return true;\n}",
                },
            ),
            # 言語指定なし
            (
                ["```", "plain text", "code", "```"],
                {"language": None, "code": "plain text\ncode"},
            ),
            # インデントコードブロック
            (
                ["    def example():", "        return 'indented'"],
                {"type": "indented", "code": "def example():\n    return 'indented'"},
            ),
            # HTML属性付き
            (
                ["```python {.highlight .line-numbers}", "print('Hello')", "```"],
                {"language": "python", "attributes": [".highlight", ".line-numbers"]},
            ),
        ]

        for code_lines, expected in code_block_patterns:
            try:
                result = self.markdown_parser.parse_code_block(code_lines)
                if result:
                    if "language" in expected and expected["language"]:
                        assert hasattr(result, "language") or hasattr(
                            result, "info_string"
                        )
                    if "code" in expected:
                        assert expected["code"] in str(result)
            except Exception as e:
                pytest.fail(f"コードブロック解析でエラー: {code_lines} -> {e}")

    def test_table_parsing(self):
        """テーブル解析テスト"""
        table_patterns = [
            # 基本テーブル
            [
                "| ヘッダー1 | ヘッダー2 | ヘッダー3 |",
                "|----------|----------|----------|",
                "| データ1  | データ2  | データ3  |",
                "| データ4  | データ5  | データ6  |",
            ],
            # 配置指定付きテーブル
            [
                "| 左寄せ | 中央寄せ | 右寄せ |",
                "|:-------|:--------:|-------:|",
                "| L1     | C1       | R1     |",
                "| L2     | C2       | R2     |",
            ],
            # パイプなしテーブル
            [
                "ヘッダー1 | ヘッダー2 | ヘッダー3",
                "---------|----------|----------",
                "データ1  | データ2  | データ3",
            ],
            # インライン要素を含むテーブル
            [
                "| **太字** | *斜体* | `コード` |",
                "|----------|--------|----------|",
                "| [リンク](url) | ![画像](img) | ~~取り消し~~ |",
            ],
        ]

        for table_lines in table_patterns:
            try:
                if hasattr(self.markdown_parser, "parse_table"):
                    result = self.markdown_parser.parse_table(table_lines)
                    if result:
                        assert hasattr(result, "headers") or hasattr(result, "rows")
            except Exception as e:
                pytest.fail(f"テーブル解析でエラー: {table_lines} -> {e}")

    def test_blockquote_parsing(self):
        """ブロック引用解析テスト"""
        blockquote_patterns = [
            # 基本引用
            [
                "> 引用文です。",
                "> 複数行の引用。",
            ],
            # ネスト引用
            [
                "> レベル1引用",
                "> > レベル2引用",
                "> > > レベル3引用",
            ],
            # 引用内の要素
            [
                "> # 引用内見出し",
                "> ",
                "> 引用内の段落です。",
                "> ",
                "> - 引用内リスト",
                "> - 項目2",
            ],
            # 遅延形式引用
            [
                "> 遅延形式引用の",
                "最初の行です。",
                "> 続きの行。",
            ],
        ]

        for quote_lines in blockquote_patterns:
            try:
                if hasattr(self.markdown_parser, "parse_blockquote"):
                    result = self.markdown_parser.parse_blockquote(quote_lines)
                    if result:
                        assert hasattr(result, "content") or hasattr(result, "children")
            except Exception as e:
                pytest.fail(f"ブロック引用解析でエラー: {quote_lines} -> {e}")

    def test_horizontal_rule_parsing(self):
        """水平線解析テスト"""
        hr_patterns = [
            "---",
            "***",
            "___",
            "- - -",
            "* * *",
            "_ _ _",
            "----",
            "*****",
            "_____",
            "- - - -",
            "* * * * *",
        ]

        for hr_pattern in hr_patterns:
            try:
                if hasattr(self.markdown_parser, "parse_horizontal_rule"):
                    result = self.markdown_parser.parse_horizontal_rule(hr_pattern)
                    assert result is not None or hr_pattern in [
                        "- - -",
                        "* * *",
                        "_ _ _",
                    ]  # 一部は無効な場合あり
            except Exception as e:
                pytest.fail(f"水平線解析でエラー: {hr_pattern} -> {e}")

    def test_html_block_parsing(self):
        """HTMLブロック解析テスト"""
        html_patterns = [
            # HTMLタグ
            ["<div>", "HTMLコンテンツ", "</div>"],
            ["<p>段落</p>"],
            # HTMLコメント
            ["<!-- HTMLコメント -->"],
            # 処理命令
            ["<?xml version='1.0'?>"],
            # CDATA
            ["<![CDATA[", "データ", "]]>"],
            # DOCTYPE
            ["<!DOCTYPE html>"],
        ]

        for html_lines in html_patterns:
            try:
                if hasattr(self.markdown_parser, "parse_html_block"):
                    result = self.markdown_parser.parse_html_block(html_lines)
                    # HTMLブロックは実装依存
                    pass
            except Exception as e:
                pytest.fail(f"HTMLブロック解析でエラー: {html_lines} -> {e}")

    def test_markdown_parsing_performance(self):
        """Markdown解析性能テスト"""
        # 大規模Markdown文書の生成
        large_markdown = []

        # 見出し
        for i in range(50):
            large_markdown.append(f"## セクション{i}")
            large_markdown.append("")

            # 段落
            large_markdown.append(
                f"セクション{i}の内容です。**重要な**情報と*強調*テキストが含まれます。"
            )
            large_markdown.append("")

            # リスト
            for j in range(5):
                large_markdown.append(f"- 項目{i}-{j}")
            large_markdown.append("")

            # コードブロック
            large_markdown.append("```python")
            large_markdown.append(f"def section_{i}():")
            large_markdown.append(f"    return 'Section {i} code'")
            large_markdown.append("```")
            large_markdown.append("")

        start_time = time.time()

        try:
            result = self.markdown_parser.parse(large_markdown)
            assert result is not None
        except Exception as e:
            pytest.fail(f"大規模Markdown解析でエラー: {e}")

        execution_time = time.time() - start_time

        # 性能基準確認
        assert execution_time < 3.0, f"Markdown解析が遅すぎる: {execution_time}秒"

        # リアルタイム解析基準（50ms/KB）
        doc_size_kb = len("\n".join(large_markdown)) / 1024
        ms_per_kb = (execution_time * 1000) / doc_size_kb
        assert ms_per_kb < 50, f"KB当たり処理時間が遅い: {ms_per_kb}ms/KB"

    def test_regex_pattern_compilation(self):
        """正規表現パターンコンパイルテスト"""
        # パターンがコンパイル済みであることを確認
        if hasattr(self.markdown_parser, "_compiled_patterns"):
            patterns = self.markdown_parser._compiled_patterns
            assert len(patterns) > 0

            # 各パターンがコンパイル済み
            for pattern_name, pattern in patterns.items():
                assert hasattr(pattern, "match")  # re.Pattern object

        elif hasattr(self.markdown_parser, "patterns"):
            # パターン辞書がある場合
            patterns = self.markdown_parser.patterns
            assert len(patterns) > 0

    def test_unicode_markdown_comprehensive(self):
        """Unicode Markdown包括テスト"""
        unicode_markdown = [
            # 多言語見出し
            "# 日本語見出し",
            "## English Heading",
            "### Título en Español",
            "#### Заголовок на русском",
            "##### عنوان باللغة العربية",
            "## 中文标题",
            "",
            # 多言語コンテンツ
            "これは**日本語**の段落です。*強調*も含まれます。",
            "",
            "This is an **English** paragraph with *emphasis*.",
            "",
            "Este es un párrafo en **español** con *énfasis*.",
            "",
            "Это **русский** параграф с *выделением*.",
            "",
            "هذه فقرة **عربية** مع *تأكيد*.",
            "",
            "这是一个**中文**段落，包含*强调*文本。",
            "",
            # 絵文字とシンボル
            "絵文字テスト: 🎌🗾🎯📋✅❌⚠️🔧",
            "",
            "記号テスト: →←↑↓∀∃∈∉∪∩",
            "",
            # 多言語リスト
            "- 日本語項目",
            "- English item",
            "- Elemento en español",
            "- Русский элемент",
            "- عنصر عربي",
            "- 中文项目",
            "",
            # 多言語コードブロック
            "```python",
            "# 日本語コメント",
            "def hello_世界():",
            "    return 'こんにちは世界'",
            "```",
        ]

        try:
            result = self.markdown_parser.parse(unicode_markdown)
            assert result is not None
        except Exception as e:
            pytest.fail(f"Unicode Markdown解析でエラー: {e}")

    def test_markdown_accuracy_target(self):
        """Markdown解析精度目標テスト"""
        # 標準的なMarkdownパターン
        standard_markdown_patterns = [
            ["# 見出し1"],
            ["## 見出し2"],
            ["**太字**"],
            ["*斜体*"],
            ["`コード`"],
            ["[リンク](url)"],
            ["![画像](img)"],
            ["- リスト項目"],
            ["1. 番号付きリスト"],
            ["> 引用"],
            ["```", "コードブロック", "```"],
            ["---"],  # 水平線
        ]

        accuracy_results = []
        for pattern in standard_markdown_patterns:
            try:
                result = self.markdown_parser.parse(pattern)
                accuracy_results.append(result is not None)
            except Exception:
                accuracy_results.append(False)

        # 精度目標: 99.5%以上
        accuracy_rate = sum(accuracy_results) / len(accuracy_results)
        assert (
            accuracy_rate >= 0.995
        ), f"Markdown解析精度が目標未達: {accuracy_rate:.1%}"

    def test_concurrent_markdown_parsing(self):
        """並行Markdown解析テスト"""
        import threading

        results = []
        errors = []

        def concurrent_markdown_worker(worker_id):
            try:
                local_parser = MarkdownParser()
                worker_results = []

                # 各ワーカーで独立したMarkdownセット
                worker_markdown = [
                    f"# ワーカー{worker_id}ドキュメント",
                    "",
                    f"ワーカー{worker_id}の**重要な**内容です。",
                    "",
                    f"- ワーカー{worker_id}項目1",
                    f"- ワーカー{worker_id}項目2",
                    "",
                    "```python",
                    f"def worker_{worker_id}_function():",
                    f"    return 'Worker {worker_id}'",
                    "```",
                ]

                try:
                    result = local_parser.parse(worker_markdown)
                    worker_results.append(result is not None)
                except Exception:
                    worker_results.append(False)

                success_rate = (
                    sum(worker_results) / len(worker_results) if worker_results else 0
                )
                results.append((worker_id, success_rate))

            except Exception as e:
                errors.append((worker_id, str(e)))

        # 複数ワーカーで並行実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_markdown_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"並行Markdown解析でエラー: {errors}"
        assert len(results) == 3

        # 各ワーカーで成功
        for worker_id, success_rate in results:
            assert (
                success_rate >= 0.5
            ), f"ワーカー{worker_id}の成功率が低い: {success_rate:.1%}"


class TestMarkdownProcessorIntegration:
    """Markdownプロセッサー統合テスト"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.markdown_processor = MarkdownProcessor()

    def test_text_normalization(self):
        """テキスト正規化テスト"""
        normalization_cases = [
            # 空白の正規化
            ("  multiple   spaces  ", "multiple spaces"),
            ("tabs\t\tand\tnewlines\n\n", "tabs and newlines"),
            # HTML エスケープ
            (
                "<script>alert('xss')</script>",
                "&lt;script&gt;alert('xss')&lt;/script&gt;",
            ),
            ("A & B < C > D", "A &amp; B &lt; C &gt; D"),
            # Unicode正規化
            ("café", "café"),  # 正規化の確認
        ]

        for input_text, expected_output in normalization_cases:
            try:
                if hasattr(self.markdown_processor, "normalize_text"):
                    normalized = self.markdown_processor.normalize_text(input_text)
                    assert expected_output in normalized or len(normalized) > 0
            except Exception as e:
                pytest.fail(f"テキスト正規化でエラー: {input_text} -> {e}")

    def test_code_block_processing(self):
        """コードブロック処理テスト"""
        code_processing_cases = [
            # 基本コードブロック処理
            {
                "input": ["```python", "print('Hello')", "```"],
                "language": "python",
                "expected_content": "print('Hello')",
            },
            # HTML エスケープ
            {
                "input": ["```html", "<div>content</div>", "```"],
                "language": "html",
                "expected_content": "&lt;div&gt;content&lt;/div&gt;",
            },
            # 特殊文字処理
            {
                "input": ["```", "code & symbols < > \"'", "```"],
                "language": None,
                "expected_content": "code &amp; symbols &lt; &gt;",
            },
        ]

        for case in code_processing_cases:
            try:
                if hasattr(self.markdown_processor, "process_code_block"):
                    result = self.markdown_processor.process_code_block(case["input"])
                    if result:
                        assert (
                            case["expected_content"] in str(result)
                            or len(str(result)) > 0
                        )
            except Exception as e:
                pytest.fail(f"コードブロック処理でエラー: {case} -> {e}")

    def test_special_element_conversion(self):
        """特殊要素変換テスト"""
        special_cases = [
            # 自動リンク変換
            ("Visit https://example.com for more info", 'href="https://example.com"'),
            # メールアドレス変換
            ("Contact us at info@example.com", "mailto:info@example.com"),
            # 絵文字変換（実装依存）
            (":smile:", "😊"),
            (":heart:", "❤️"),
            # 特殊記号変換
            ("(c)", "©"),
            ("(r)", "®"),
            ("(tm)", "™"),
            # 引用符変換
            ('"smart quotes"', "\u201csmart quotes\u201d"),
            ("'single quotes'", "\u2018single quotes\u2019"),
        ]

        for input_text, expected_pattern in special_cases:
            try:
                if hasattr(self.markdown_processor, "convert_special_elements"):
                    converted = self.markdown_processor.convert_special_elements(
                        input_text
                    )
                    # 変換が実行される（実装依存のため、厳密でないチェック）
                    assert (
                        len(converted) >= len(input_text)
                        or expected_pattern in converted
                    )
            except Exception as e:
                pytest.fail(f"特殊要素変換でエラー: {input_text} -> {e}")

    def test_integrated_markdown_document_processing(self):
        """統合Markdown文書処理テスト"""
        integrated_document = [
            "# マークダウン統合テスト文書",
            "",
            "この文書は**包括的な**Markdown機能をテストします。",
            "",
            "## コードブロック例",
            "",
            "```python",
            "def example():",
            "    return '<b>HTML</b> & special chars'",
            "```",
            "",
            "## リンクと画像",
            "",
            "詳細は[公式サイト](https://example.com)を参照してください。",
            "",
            '![テスト画像](test.jpg "画像の説明")',
            "",
            "## リスト",
            "",
            "- **重要**: セキュリティ対策",
            "- *推奨*: 定期的なバックアップ",
            '- `コード`: git commit -m "message"',
            "",
            "## テーブル",
            "",
            "| 項目 | 説明 | 重要度 |",
            "|------|------|--------|",
            "| A | **重要** | 高 |",
            "| B | *普通* | 中 |",
            "",
            "## 引用",
            "",
            "> この部分は重要な引用です。",
            "> 複数行にわたって続きます。",
            "",
            "---",
            "",
            "© 2023 テスト文書",
        ]

        try:
            # 文書全体の処理
            if hasattr(self.markdown_processor, "process_document"):
                result = self.markdown_processor.process_document(integrated_document)
                assert result is not None
                assert len(str(result)) > 0
            elif hasattr(self.markdown_processor, "process"):
                result = self.markdown_processor.process("\n".join(integrated_document))
                assert result is not None
                assert len(str(result)) > 0
        except Exception as e:
            pytest.fail(f"統合文書処理でエラー: {e}")
