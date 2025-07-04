"""基本的なインポートテスト"""


def test_import_kumihan_formatter():
    """kumihan_formatterパッケージのインポートテスト"""
    import kumihan_formatter

    assert kumihan_formatter is not None


def test_import_parser():
    """parserモジュールのインポートテスト"""
    from kumihan_formatter import parser

    assert parser is not None


def test_import_renderer():
    """rendererモジュールのインポートテスト"""
    from kumihan_formatter import renderer

    assert renderer is not None


def test_import_config():
    """configモジュールのインポートテスト"""
    from kumihan_formatter import config

    assert config is not None