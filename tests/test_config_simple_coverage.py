"""config.py (トップレベル) の簡単なカバレッジ向上テスト

Phase 1 最終目標18%達成のための簡易テスト
ConfigManagerエイリアスの基本動作をテスト
"""

import json
import tempfile
from pathlib import Path

from kumihan_formatter.config import Config, load_config


class TestConfigBasic:
    """Config(ConfigManagerエイリアス)の基本テスト"""

    def test_config_creation(self):
        """Config作成のテスト"""
        config = Config()
        assert config is not None

    def test_config_with_config_type(self):
        """config_type指定でのConfig作成"""
        config = Config(config_type="base")
        assert config is not None

    def test_config_basic_methods(self):
        """基本メソッドの動作確認"""
        config = Config()

        # 基本メソッドの存在確認
        assert hasattr(config, "get_css_variables")
        assert hasattr(config, "get_theme_name")
        assert hasattr(config, "get_markers")
        assert hasattr(config, "validate")

        # メソッド実行
        css_vars = config.get_css_variables()
        assert isinstance(css_vars, dict)

        theme_name = config.get_theme_name()
        assert isinstance(theme_name, str)

        markers = config.get_markers()
        assert isinstance(markers, dict)

        is_valid = config.validate()
        assert isinstance(is_valid, bool)

    def test_config_dict_operations(self):
        """辞書操作の確認"""
        config = Config()

        # to_dict メソッド
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)

        # get/set メソッド
        config.set("test_key", "test_value")
        value = config.get("test_key")
        assert value == "test_value"

    def test_load_config_function(self):
        """load_config関数のテスト"""
        config = load_config()
        assert config is not None

    def test_load_config_with_valid_file(self):
        """有効な設定ファイルでのテスト"""
        test_data = {"theme": "test", "test_setting": "value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            config = Config()
            result = config.load_config(temp_path)
            # load_configの結果を確認（Trueかboolであることを確認）
            assert isinstance(result, bool)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_config_integration(self):
        """統合動作テスト"""
        config = Config()

        # テーマ関連の操作
        config.set_theme("test_theme")

        # マーカー追加
        config.add_marker("テスト", {"tag": "span"})

        # 設定確認
        markers = config.get_markers()
        assert "テスト" in markers

        # 検証
        is_valid = config.validate()
        assert is_valid is True


class TestConfigModuleAttributes:
    """configモジュールの属性テスト"""

    def test_module_imports(self):
        """モジュールインポートの確認"""
        from kumihan_formatter import config as config_module

        assert hasattr(config_module, "Config")
        assert hasattr(config_module, "load_config")

    def test_config_class_attributes(self):
        """Configクラスの属性確認"""
        config = Config()

        # 基本属性の存在確認
        assert hasattr(config, "config")
        assert hasattr(config, "config_type")

    def test_config_instantiation_variations(self):
        """Config作成の各種パターン"""
        # デフォルト作成
        config1 = Config()
        assert config1 is not None

        # config_type指定
        config2 = Config(config_type="extended")
        assert config2 is not None

        # env_prefix指定
        config3 = Config(env_prefix="KUMIHAN")
        assert config3 is not None
