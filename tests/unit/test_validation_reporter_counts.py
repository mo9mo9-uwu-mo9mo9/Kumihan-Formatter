"""SyntaxReporter の集計系ユーティリティのテスト"""

from pathlib import Path
from kumihan_formatter.core.syntax.syntax_reporter import SyntaxReporter


def test_get_error_counts_and_exit_code(tmp_path: Path):
    # エラーなし
    f_ok = tmp_path / "ok.txt"
    f_ok.write_text("通常の本文\n", encoding="utf-8")
    results_ok = SyntaxReporter.check_files([f_ok])
    counts_ok = SyntaxReporter.get_error_counts(results_ok)
    assert counts_ok["TOTAL"] >= 0
    assert SyntaxReporter.should_exit_with_error(results_ok) is False

    # 明確なエラー（unmatched end）
    f_ng = tmp_path / "ng.txt"
    f_ng.write_text("##\n", encoding="utf-8")
    results_ng = SyntaxReporter.check_files([f_ng])
    counts_ng = SyntaxReporter.get_error_counts(results_ng)
    assert counts_ng["ERROR"] >= 1
    assert SyntaxReporter.should_exit_with_error(results_ng) is True
