"""FileIOHandler の基本I/Oテスト"""

from pathlib import Path
from kumihan_formatter.core.utilities.file_io_handler import FileIOHandler


def test_file_io_roundtrip(tmp_path: Path):
    io = FileIOHandler()
    f = tmp_path / "a" / "b" / "test.txt"

    ok = io.write_file(f, "hello\nworld")
    assert ok is True
    assert io.file_exists(f) is True
    assert (io.get_file_size(f) or 0) > 0

    text = io.read_file(f)
    assert text and "hello" in text

    lines_ok = io.write_lines(f, ["x\n", "y\n"])  # 上書き
    assert lines_ok is True
    lines = io.read_lines(f)
    assert lines and lines[0].strip() == "x"

    # copy / move / delete
    dst = tmp_path / "copy.txt"
    assert io.copy_file(f, dst) is True
    moved = tmp_path / "moved.txt"
    assert io.move_file(dst, moved) is True
    assert io.delete_file(moved) is True

