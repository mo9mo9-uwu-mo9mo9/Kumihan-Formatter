"""簡素化された設定管理のテスト"""

from kumihan_formatter.simple_config import SimpleConfig, create_simple_config


def test_simple_config():
    """簡素化された設定のテスト"""
    config = SimpleConfig()
    
    # CSS変数の確認
    css_vars = config.get_css_variables()
    assert "font_family" in css_vars
    assert "background_color" in css_vars
    assert "container_background" in css_vars
    assert "text_color" in css_vars
    assert "line_height" in css_vars
    assert "max_width" in css_vars
    
    # テーマ名の確認
    assert config.get_theme_name() == "デフォルト"


def test_create_simple_config():
    """設定作成関数のテスト"""
    config = create_simple_config()
    assert isinstance(config, SimpleConfig)
    
    # CSS変数が正しく設定されているか
    css_vars = config.get_css_variables()
    assert css_vars["background_color"] == "#f9f9f9"
    assert css_vars["text_color"] == "#333"


def test_css_variables_immutable():
    """CSS変数の不変性テスト"""
    config = SimpleConfig()
    
    # 元の値を取得
    css_vars1 = config.get_css_variables()
    css_vars2 = config.get_css_variables()
    
    # 別のオブジェクトであることを確認
    assert css_vars1 is not css_vars2
    
    # 値を変更しても元の設定に影響しないことを確認
    css_vars1["background_color"] = "#000000"
    css_vars3 = config.get_css_variables()
    assert css_vars3["background_color"] == "#f9f9f9"