"""Tokenトラッカの基本テスト"""

from pathlib import Path
from kumihan_formatter.core.utilities import token_tracker as tt


def test_estimate_tokens_basic():
    assert tt.estimate_tokens("") == 0
    assert tt.estimate_tokens("a") >= 1
    assert tt.estimate_tokens("hello world") >= 1


def test_logging_and_report_generation(tmp_path: Path, monkeypatch):
    # tmp/配下への書き込みをテスト用ディレクトリに向ける
    test_tmp = tmp_path / "tmp"
    test_tmp.mkdir(parents=True, exist_ok=True)

    # Path("tmp/...") の解決をテスト専用に切り替える
    # monkeypatch を使って token_tracker 内の Path を置き換えるのは難しいため
    # 作業ディレクトリを一時的に変更する
    monkeypatch.chdir(tmp_path)

    tt.log_task_usage("taskA", "prompt text", "response text")
    tt.log_task_usage("taskB", "p" * 20, "r" * 30)

    data = tt.load_usage_data()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert all("actual_total" in row for row in data)

    report_path = tt.generate_report()
    assert report_path
    p = Path(report_path)
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert "Token使用量レポート" in content

