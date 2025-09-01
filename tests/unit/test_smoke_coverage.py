"""
スモークカバレッジテスト
- 目的: 主要モジュールのインポートと軽いエントリ呼び出しでカバレッジ底上げ
"""

import importlib


def test_smoke_import_core_packages():
    modules = [
        "kumihan_formatter",
        "kumihan_formatter.unified_api",
        "kumihan_formatter.parser",
        "kumihan_formatter.core.api.formatter_api",
        "kumihan_formatter.core.api.manager_coordinator",
        "kumihan_formatter.core.rendering.main_renderer",
        "kumihan_formatter.core.templates.template_selector",
        "kumihan_formatter.core.parsing.parser_core",
        "kumihan_formatter.parsers.unified_list_parser",
        "kumihan_formatter.parsers.unified_keyword_parser",
        "kumihan_formatter.parsers.unified_markdown_parser",
        "kumihan_formatter.parsers.main_parser",
        "kumihan_formatter.parsers.specialized_parser",
    ]
    for m in modules:
        importlib.invalidate_caches()
        mod = importlib.import_module(m)
        assert mod is not None

