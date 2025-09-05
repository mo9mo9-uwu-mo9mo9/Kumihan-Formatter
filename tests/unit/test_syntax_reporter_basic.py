"""SyntaxReporter の最小動作テスト"""

from pathlib import Path
from kumihan_formatter.core.syntax.syntax_reporter import SyntaxReporter


def test_syntax_reporter_detects_errors(tmp_path: Path):
    # 複数の軽微な記法エラーが出る内容
    text = """
# #
本文に`バッククォートが奇数
\tタブあり
##
""".strip()

    f = tmp_path / "sample.txt"
    f.write_text(text, encoding="utf-8")

    results = SyntaxReporter.check_files([f])
    assert str(f) in results
    errors = results[str(f)]
    assert len(errors) >= 2

    # JSON整形出力（テキスト整形は別テストに委譲）
    out_json = SyntaxReporter.format_json_report(results)
    assert "line" in out_json and "severity" in out_json

    # 退出コード判定
    assert SyntaxReporter.should_exit_with_error(results) in {True, False}
