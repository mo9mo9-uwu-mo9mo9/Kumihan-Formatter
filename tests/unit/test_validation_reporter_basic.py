"""ValidationReporter の基本出力テスト"""

import json
from pathlib import Path
from kumihan_formatter.core.validation.validation_reporter import ValidationReporter
from kumihan_formatter.core.validation.validation_issue import ValidationIssue


def _make_issues():
    return [
        ValidationIssue("error", "syntax", "未対応の終了マーカー", 10, 1, "開始行(#...#)を追加"),
        ValidationIssue("warning", "style", "タブ文字が含まれます", 2, 5, "スペースに置換"),
        ValidationIssue("info", "structure", "見出しが不足しています", None, None, None),
    ]


def test_text_report_and_summary(capsys):
    rep = ValidationReporter()
    issues = _make_issues()
    txt = rep.generate_report(issues, "text")
    assert "error (" in txt and "warning (" in txt and "info (" in txt

    # summary print
    rep.print_summary(issues)
    out = capsys.readouterr().out
    assert "Validation complete:" in out


def test_json_and_html_report(tmp_path: Path):
    rep = ValidationReporter()
    issues = _make_issues()

    js = rep.generate_report(issues, "json")
    data = json.loads(js)
    assert data["summary"]["total"] == 3
    assert len(data["issues"]) == 3

    html = rep.generate_report([], "html")
    assert "No validation issues found" in html

