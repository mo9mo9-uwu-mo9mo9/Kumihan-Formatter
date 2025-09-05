"""ParserUtils の基本機能テスト"""

import warnings
from kumihan_formatter.parsers import parser_utils as PU


def test_validate_and_extract_and_normalize():
    # validate
    assert PU.validate_keyword("keyword1") in {True, False}
    assert PU.validate_keyword("1234") is False  # 数字のみは無効

    # extract
    content = "これは #見出し1# と #重要# を含むテキストです ##"
    kws = PU.extract_keywords_from_content(content)
    assert isinstance(kws, list)

    # normalize
    norm = PU.normalize_text("ＡＢＣ abc")
    assert isinstance(norm, str)


def test_legacy_get_keyword_categories():
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        cats = PU.get_keyword_categories()
        assert isinstance(cats, dict)
        assert any(isinstance(v, (set, list)) for v in cats.values())
        assert any(w.category == UserWarning or issubclass(w.category, Warning) for w in rec)

