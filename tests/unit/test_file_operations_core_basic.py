"""FileOperationsCore の基本テスト"""

from pathlib import Path
from kumihan_formatter.core.utilities.file_operations_core import FileOperationsCore


def test_copy_directory_with_exclusions(tmp_path: Path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    (src / "keep").mkdir(parents=True)
    (src / "ignore").mkdir(parents=True)
    (src / "keep" / "a.txt").write_text("ok", encoding="utf-8")
    (src / "ignore" / "b.txt").write_text("no", encoding="utf-8")

    copied, excluded = FileOperationsCore.copy_directory_with_exclusions(
        src, dst, ["ignore/"]
    )
    assert copied == 1
    assert excluded == 1
    assert (dst / "keep" / "a.txt").exists()
    assert not (dst / "ignore" / "b.txt").exists()


def test_find_preview_file(tmp_path: Path):
    p = FileOperationsCore.find_preview_file(tmp_path)
    assert p is None
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    p2 = FileOperationsCore.find_preview_file(tmp_path)
    assert p2 and p2.name == "index.html"


def test_check_large_file_warning(tmp_path: Path):
    f = tmp_path / "small.bin"
    f.write_bytes(b"x" * 10)
    foc = FileOperationsCore()
    # 0MBの閾値で強制的に警告経路を通す（戻り値はTrue）
    assert foc.check_large_file_warning(f, max_size_mb=0.0) is True

