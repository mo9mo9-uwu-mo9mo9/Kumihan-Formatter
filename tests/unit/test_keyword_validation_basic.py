"""KeywordValidator の基本動作テスト"""

from kumihan_formatter.parsers.keyword_config import KeywordParserConfig
from kumihan_formatter.parsers.keyword_validation import KeywordValidator


def test_validate_empty_content_is_ok():
    cfg = KeywordParserConfig()
    v = KeywordValidator(cfg)
    assert v.validate("") == []


def test_validate_keyword_cache_and_custom():
    cfg = KeywordParserConfig()
    v = KeywordValidator(cfg)

    # 既定のカスタムハンドラに登録済みのキーワード
    assert v.validate_keyword("custom") is True
    # 未登録
    assert v.validate_keyword("unknown") is False

    # キャッシュにより2回目も安定
    assert v.validate_keyword("custom") is True


def test_validate_invalid_keyword_characters():
    cfg = KeywordParserConfig()
    v = KeywordValidator(cfg)

    # 先頭が数値や記号を含むキーワードはエラーになる想定
    errors = v.validate("# 123invalid *bad* # content ##")
    assert errors  # 何らかのエラーが検出される
