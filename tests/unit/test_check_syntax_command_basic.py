"""CheckSyntaxCommand の基本動作テスト"""

from pathlib import Path
from kumihan_formatter.commands.check_syntax import CheckSyntaxCommand


def test_check_syntax_execute_text_and_json(tmp_path: Path, capsys):
    # OKファイル
    ok = tmp_path / "ok.txt"
    ok.write_text("通常の本文\n", encoding="utf-8")

    # NGファイル（unmatched end）
    ng = tmp_path / "ng.txt"
    ng.write_text("##\n", encoding="utf-8")

    cmd = CheckSyntaxCommand()
    # text出力
    res_text = cmd.execute([str(ok), str(ng)], recursive=False, show_suggestions=True, format_output="text")
    assert isinstance(res_text, dict)
    assert res_text["error_count"] >= 1

    # json出力
    res_json = cmd.execute([str(ng)], recursive=False, show_suggestions=False, format_output="json")
    assert isinstance(res_json, dict)
    assert res_json["error_count"] >= 1

