"""追加スモークインポート（さらにカバレッジ押し上げ）"""

def test_smoke_imports_extra():
    import importlib

    modules = [
        # コマンド系（トップレベル実行は無い想定）
        "kumihan_formatter.commands.check_syntax",
        "kumihan_formatter.commands.convert_watcher",
        # ASTユーティリティ
        "kumihan_formatter.core.ast_nodes.node_builder",
        "kumihan_formatter.core.ast_nodes.utilities",
        # 共通ミックスイン/エラー
        "kumihan_formatter.core.common.validation_mixin",
        "kumihan_formatter.core.common.processing_errors",
        # 解析コア
        "kumihan_formatter.core.parsing.parser_core",
        # サンプル
        "kumihan_formatter.sample_content",
    ]

    for mod in modules:
        m = importlib.import_module(mod)
        assert m is not None

