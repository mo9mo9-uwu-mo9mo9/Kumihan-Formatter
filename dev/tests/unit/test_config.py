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
        assert hasattr(config, "output_dir")
        assert hasattr(config, "template")
        assert config.output_dir is not None
        assert config.template is not None

    def test_load_config_from_file(self, config, config_file):
        """ファイルから設定を読み込むテスト"""
        config.load(str(config_file))
        
        assert config.title == "テストタイトル"
        assert config.author == "テスト作者"
        assert config.output_dir == "test_output"
        assert config.template == "base.html.j2"

    def test_load_nonexistent_file(self, config):
        """存在しないファイルの読み込みテスト"""
        # エラーが発生するか、デフォルト設定が維持される
        try:
            config.load("nonexistent_file.yaml")
            # デフォルト設定が維持される場合
            assert config.output_dir is not None
        except FileNotFoundError:
            # エラーが発生する場合
            pass

    def test_config_update(self, config):
        """設定の更新テスト"""
        config.update({"title": "新しいタイトル", "author": "新しい作者"})
        
        assert config.title == "新しいタイトル"
        assert config.author == "新しい作者"

    def test_config_to_dict(self, config):
        """設定の辞書変換テスト"""
        config.title = "テスト"
        config.author = "作者"
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict.get("title") == "テスト"
        assert config_dict.get("author") == "作者"


class TestSimpleConfig:
    """SimpleConfigクラスのテスト"""

    def test_simple_config_creation(self):
        """SimpleConfigの作成テスト"""
        config = SimpleConfig()
        
        assert hasattr(config, "output_dir")
        assert hasattr(config, "template")
        assert config.output_dir == "output"
        assert config.template == "base.html.j2"

    def test_simple_config_with_params(self):
        """パラメータ付きSimpleConfigの作成テスト"""
        config = SimpleConfig(
            output_dir="custom_output",
            template="custom.html.j2",
            title="カスタムタイトル"
        )
        
        assert config.output_dir == "custom_output"
        assert config.template == "custom.html.j2"
        assert config.title == "カスタムタイトル"

    def test_simple_config_attribute_access(self):
        """SimpleConfigの属性アクセステスト"""
        config = SimpleConfig()
        config.custom_attr = "カスタム値"
        
        assert config.custom_attr == "カスタム値"
        assert hasattr(config, "custom_attr")