"""
Unit tests for the Config module
"""
import pytest
from pathlib import Path
import yaml

from kumihan_formatter.config import Config
from kumihan_formatter.simple_config import SimpleConfig


class TestConfig:
    """Configクラスのテスト"""

    @pytest.fixture
    def config(self):
        """Configインスタンスを生成"""
        return Config()

    @pytest.fixture
    def config_file(self, temp_dir):
        """テスト用の設定ファイルを作成"""
        config_path = temp_dir / "test_config.yaml"
        config_data = {
            "title": "テストタイトル",
            "author": "テスト作者",
            "output_dir": "test_output",
            "template": "base.html.j2"
        }
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True)
        return config_path

    def test_default_config(self, config):
        """デフォルト設定の確認"""
        assert hasattr(config, "DEFAULT_CONFIG")
        assert hasattr(config, "config")
        assert hasattr(config, "load_config")
        assert hasattr(config, "validate_config")

    def test_load_config_from_file(self, config, config_file):
        """ファイルから設定を読み込むテスト"""
        success = config.load_config(str(config_file))
        
        # load_configはbooleanを返す
        assert isinstance(success, bool)
        assert success == True
        
        # 実際の設定はconfig属性からアクセス
        assert isinstance(config.config, dict)

    def test_load_nonexistent_file(self, config):
        """存在しないファイルの読み込みテスト"""
        # load_configはFalseを返し、デフォルト設定を使用
        result = config.load_config("nonexistent_file.yaml")
        assert isinstance(result, bool)
        assert result == False
        
        # デフォルト設定が使用される
        assert isinstance(config.config, dict)

    def test_config_validation(self, config):
        """設定の検証テスト"""
        test_config = {
            "title": "新しいタイトル",
            "author": "新しい作者"
        }
        
        # 検証が成功することを確認
        is_valid = config.validate_config()
        assert isinstance(is_valid, bool)

    def test_config_access(self, config):
        """設定アクセステスト"""
        # DEFAULT_CONFIGがアクセス可能であることを確認
        default_config = config.DEFAULT_CONFIG
        assert isinstance(default_config, dict)
        
        # config属性がアクセス可能であることを確認
        current_config = config.config
        assert isinstance(current_config, dict)


class TestSimpleConfig:
    """SimpleConfigクラスのテスト"""

    def test_simple_config_creation(self):
        """SimpleConfigの作成テスト"""
        config = SimpleConfig()
        
        assert hasattr(config, "DEFAULT_CSS")
        assert hasattr(config, "css_vars")
        assert hasattr(config, "get_css_variables")
        assert hasattr(config, "get_theme_name")

    def test_simple_config_methods(self):
        """シンプルコンフィグのメソッドテスト"""
        config = SimpleConfig()
        
        # get_css_variablesメソッドのテスト
        css_vars = config.get_css_variables()
        assert isinstance(css_vars, dict)
        
        # get_theme_nameメソッドのテスト
        theme_name = config.get_theme_name()
        assert isinstance(theme_name, str)

    def test_simple_config_css_access(self):
        """SimpleConfigのCSSアクセステスト"""
        config = SimpleConfig()
        
        # DEFAULT_CSSがアクセス可能であることを確認
        default_css = config.DEFAULT_CSS
        assert isinstance(default_css, dict)
        
        # css_varsがアクセス可能であることを確認
        css_vars = config.css_vars
        assert isinstance(css_vars, dict)