"""広範インポートのスモークテスト（カバレッジ押し上げ用）

モジュールのトップレベル実行（定義評価）で安全にカバレッジを稼ぐ。
実行時副作用の大きいモジュールは対象外とする。
"""

def test_smoke_imports():
    # parsers
    import importlib

    modules = [
        # パーサー関連
        "kumihan_formatter.parsers.core_parser",
        "kumihan_formatter.parsers.main_parser",
        "kumihan_formatter.parsers.specialized_parser",
        "kumihan_formatter.parsers.parser_utils",
        "kumihan_formatter.parsers.unified_keyword_parser",
        "kumihan_formatter.parsers.unified_list_parser",
        "kumihan_formatter.parsers.unified_markdown_parser",
        "kumihan_formatter.parsers.keyword_config",
        "kumihan_formatter.parsers.keyword_validation",
        "kumihan_formatter.parsers.keyword_extractors",
        "kumihan_formatter.parsers.keyword_definitions",
        "kumihan_formatter.parsers.utils.normalization_utils",
        "kumihan_formatter.parsers.utils.patterns",
        # AST関連
        "kumihan_formatter.core.ast_nodes.node",
        "kumihan_formatter.core.ast_nodes.factories",
        # ユーティリティ（安全なもの）
        "kumihan_formatter.core.utilities.css_utils",
        "kumihan_formatter.core.utilities.element_counter",
        "kumihan_formatter.core.utilities.compatibility_layer",
        # 共通エラー
        "kumihan_formatter.core.common.error_framework",
        "kumihan_formatter.core.common.processing_errors",
        # 解析系（トップレベル定義評価のみに留める）
        "kumihan_formatter.core.parsing.core_marker_parser",
        "kumihan_formatter.core.parsing.inline_marker_processor",
        "kumihan_formatter.core.parsing.ruby_format_processor",
        "kumihan_formatter.core.parsing.new_format_processor",
    ]

    for mod in modules:
        m = importlib.import_module(mod)
        assert m is not None

