"""KeywordExtractor の基本動作テスト"""

from kumihan_formatter.parsers.keyword_extractors import KeywordExtractor


def test_extract_inline_format():
    ex = KeywordExtractor()
    info = ex.extract_keyword_info("# bold italic # Content text ##")

    assert info is not None
    assert info["format"] == "inline"
    assert info["content"] == "Content text"
    assert "bold" in info["keywords"]
    assert "italic" in info["keywords"]


def test_extract_multiline_format():
    ex = KeywordExtractor()
    text = "# bold #\nfirst line\nsecond line\n##\ntrailing"
    info = ex.extract_keyword_info(text)

    assert info is not None
    assert info["format"] == "multiline"
    assert info["content"] == "first line\nsecond line"
    assert info["keywords"] == ["bold"]

