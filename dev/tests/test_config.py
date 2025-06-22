"""設定管理のテスト"""

import tempfile
from pathlib import Path

import pytest

from kumihan_formatter.config import Config, load_config


def test_default_config():
    """デフォルト設定のテスト"""
    config = Config()
    
    # デフォルトマーカーの確認
    markers = config.get_markers()
    assert "太字" in markers
    assert markers["太字"]["tag"] == "strong"
    
    # デフォルトテーマの確認
    assert config.get_theme_name() == "デフォルト"
    
    # CSS変数の確認
    css_vars = config.get_css_variables()
    assert "font_family" in css_vars
    assert "background_color" in css_vars


def test_yaml_config_loading():
    """YAML設定ファイルの読み込みテスト"""
    yaml_content = """
markers:
  カスタム1:
    tag: div
    class: custom-style
  カスタム2:
    tag: span
    class: highlight

theme: dark
font_family: "Noto Sans JP"

css:
  max_width: "900px"
  background_color: "#000000"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(yaml_content)
        config_path = f.name
    
    try:
        config = Config(config_path)
        
        # カスタムマーカーの確認
        markers = config.get_markers()
        assert "カスタム1" in markers
        assert markers["カスタム1"]["tag"] == "div"
        assert markers["カスタム1"]["class"] == "custom-style"
        
        # テーマの確認
        assert config.get_theme_name() == "ダーク"
        
        # CSS変数の確認
        css_vars = config.get_css_variables()
        assert css_vars["font_family"] == "Noto Sans JP"
        assert css_vars["max_width"] == "900px"
        assert css_vars["background_color"] == "#1a1a1a"  # ダークテーマの背景色
        
    finally:
        Path(config_path).unlink()


def test_json_config_loading():
    """JSON設定ファイルの読み込みテスト"""
    json_content = """{
    "markers": {
        "警告": {
            "tag": "div",
            "class": "warning"
        }
    },
    "theme": "sepia",
    "font_family": "Arial"
}"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        f.write(json_content)
        config_path = f.name
    
    try:
        config = Config(config_path)
        
        # カスタムマーカーの確認
        markers = config.get_markers()
        assert "警告" in markers
        assert markers["警告"]["tag"] == "div"
        assert markers["警告"]["class"] == "warning"
        
        # テーマの確認
        assert config.get_theme_name() == "セピア"
        
        # CSS変数の確認
        css_vars = config.get_css_variables()
        assert css_vars["font_family"] == "Arial"
        
    finally:
        Path(config_path).unlink()


def test_invalid_config_file():
    """無効な設定ファイルのテスト"""
    # 存在しないファイル
    config = Config("non_existent_file.yaml")
    assert config.get_theme_name() == "デフォルト"
    
    # 無効なYAML
    invalid_yaml = "invalid: yaml: content: ["
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(invalid_yaml)
        config_path = f.name
    
    try:
        config = Config(config_path)
        # エラーが発生してもデフォルト設定で動作することを確認
        assert config.get_theme_name() == "デフォルト"
    finally:
        Path(config_path).unlink()


def test_config_validation():
    """設定の妥当性チェックのテスト"""
    config = Config()
    
    # デフォルト設定は有効
    assert config.validate_config() == True
    
    # 無効な設定
    config.config["markers"] = {"invalid": "not_a_dict"}
    assert config.validate_config() == False


def test_load_config_function():
    """load_config関数のテスト"""
    # 設定なしの場合
    config = load_config()
    assert config.get_theme_name() == "デフォルト"
    
    # 存在しない設定ファイル
    config = load_config("non_existent.yaml")
    assert config.get_theme_name() == "デフォルト"


def test_custom_themes():
    """カスタムテーマのテスト"""
    yaml_content = """
themes:
  custom_dark:
    name: "カスタムダーク"
    css:
      background_color: "#111111"
      text_color: "#ffffff"

theme: custom_dark
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(yaml_content)
        config_path = f.name
    
    try:
        config = Config(config_path)
        
        # カスタムテーマの確認
        assert config.get_theme_name() == "カスタムダーク"
        
        # CSS変数の確認
        css_vars = config.get_css_variables()
        assert css_vars["background_color"] == "#111111"
        assert css_vars["text_color"] == "#ffffff"
        
    finally:
        Path(config_path).unlink()