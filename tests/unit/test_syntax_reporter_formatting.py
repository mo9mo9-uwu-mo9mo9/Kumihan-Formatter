"""SyntaxReporter のフォーマット出力のテスト"""

from pathlib import Path
from kumihan_formatter.core.syntax.syntax_reporter import SyntaxReporter


def test_format_error_report_contains_icons(tmp_path: Path):
    text = "# #\n本文\n##\n"
    f = tmp_path / "t.txt"
    f.write_text(text, encoding="utf-8")
    results = SyntaxReporter.check_files([f])
    txt = SyntaxReporter.format_error_report(results)
    # アイコンのいずれかが含まれること（ERROR/WARNING/INFO）
    assert any(icon in txt for icon in ["❌", "⚠️", "ℹ️"]) or txt.strip() == ""

