"""SampleCommand の dry-run 実行テスト（安全に網羅率を稼ぐ）"""

from pathlib import Path
from kumihan_formatter.commands.sample_command import SampleCommand


def test_sample_command_dry_run(tmp_path: Path):
    cmd = SampleCommand()
    out_dir = tmp_path / "sample_out"
    # dry-run で安全に実行。既存ディレクトリが無くても通る。
    result = cmd.execute(str(out_dir), use_source_toggle=False, dry_run=True, force=False)
    # dry-run では実ファイルは生成しないが、戻り値は指定ディレクトリ
    assert Path(result).name == "sample_out"
