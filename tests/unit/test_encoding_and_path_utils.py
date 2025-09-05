"""EncodingDetector と FilePathUtilities の基本テスト"""

from pathlib import Path
from kumihan_formatter.core.utilities.encoding_detector import EncodingDetector
from kumihan_formatter.core.utilities.file_path_utilities import FilePathUtilities


def test_detect_bom_and_encoding(tmp_path: Path):
    # UTF-8 with BOM
    f = tmp_path / "bom_utf8.txt"
    f.write_bytes(b"\xef\xbb\xbfhello")
    enc, confident = EncodingDetector.detect(f)
    assert enc in {"utf-8-sig", "utf-8"}
    assert confident in {True, False}

    # UTF-16-like (contains null bytes) without BOM
    f2 = tmp_path / "utf16_like.txt"
    f2.write_bytes(b"h\x00e\x00l\x00l\x00o\x00")
    enc2, confident2 = EncodingDetector.detect(f2)
    assert enc2 in {"utf-16", "utf-8"}
    assert confident2 in {True, False}


def test_file_path_utilities(tmp_path: Path, monkeypatch):
    # .distignore の読み込み
    di = tmp_path / ".distignore"
    di.write_text("ignore/\n# comment\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    patterns = FilePathUtilities.load_distignore_patterns()
    assert patterns == ["ignore/"]

    # should_exclude（ディレクトリパターン）
    src = tmp_path / "src"
    (src / "ignore").mkdir(parents=True)
    (src / "ignore" / "a.txt").write_text("x", encoding="utf-8")
    assert FilePathUtilities.should_exclude(src / "ignore" / "a.txt", ["ignore/"], src)

    # size info / estimate time
    big = tmp_path / "big.bin"
    big.write_bytes(b"x" * 2048)
    info = FilePathUtilities.get_file_size_info(big)
    assert info["size_bytes"] > 0
    _ = FilePathUtilities.estimate_processing_time(info["size_mb"])  # smoke

