"""config_manager_utils.py の包括的テスト

Issue #929 Phase 3C: ユーティリティ関数テスト
15テストケースで設定ユーティリティ機能の70%カバレッジ達成
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.config.base_config import BaseConfig
from kumihan_formatter.config.config_manager_utils import (
    create_config_instance,
    load_config_file,
    merge_config_data,
)
from kumihan_formatter.config.extended_config import ExtendedConfig


class TestCreateConfigInstance:
    """create_config_instance 関数のテスト"""

    @patch("kumihan_formatter.config.config_manager_utils.ExtendedConfig")
    def test_正常系_create_config_instance_extendedタイプ作成(
        self, mock_extended_config
    ):
        """extendedタイプの設定インスタンスが作成されることを確認"""
        # Given: extendedタイプとパス指定
        mock_instance = Mock()
        mock_extended_config.return_value = mock_instance
        config_type = "extended"
        config_path = None

        # When: 設定インスタンスを作成
        result = create_config_instance(config_type, config_path)

        # Then: ExtendedConfigインスタンスが作成される
        mock_extended_config.assert_called_once()
        assert result == mock_instance

    @patch("kumihan_formatter.config.config_manager_utils.BaseConfig")
    def test_正常系_create_config_instance_baseタイプ作成(self, mock_base_config):
        """baseタイプの設定インスタンスが作成されることを確認"""
        # Given: baseタイプとパス指定
        mock_instance = Mock()
        mock_base_config.return_value = mock_instance
        config_type = "base"
        config_path = None

        # When: 設定インスタンスを作成
        result = create_config_instance(config_type, config_path)

        # Then: BaseConfigインスタンスが作成される
        mock_base_config.assert_called_once()
        assert result == mock_instance

    @patch("kumihan_formatter.config.config_manager_utils.Path")
    @patch("kumihan_formatter.config.config_manager_utils.BaseConfig")
    def test_正常系_create_config_instance_ファイルパス成功(
        self, mock_base_config, mock_path
    ):
        """ファイルパスからの設定読み込みが成功することを確認"""
        # Given: 存在するファイルパス
        config_path = "/path/to/config.json"
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_instance = Mock()
        mock_base_config.from_file.return_value = mock_instance

        # When: ファイルから設定インスタンスを作成
        result = create_config_instance("base", config_path)

        # Then: from_fileが呼び出される
        mock_base_config.from_file.assert_called_once_with(config_path)
        assert result == mock_instance

    @patch("kumihan_formatter.config.config_manager_utils.Path")
    @patch("kumihan_formatter.config.config_manager_utils.BaseConfig")
    def test_異常系_create_config_instance_ファイル読み込み失敗(
        self, mock_base_config, mock_path
    ):
        """ファイル読み込み失敗時のフォールバック処理を確認"""
        # Given: 存在するが読み込みに失敗するファイル
        config_path = "/path/to/invalid.json"
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        default_instance = Mock()
        mock_base_config.from_file.side_effect = Exception("読み込みエラー")
        mock_base_config.return_value = default_instance

        # When: 失敗するファイルから設定インスタンスを作成
        result = create_config_instance("base", config_path)

        # Then: デフォルトインスタンスが返される
        mock_base_config.assert_called_once()
        assert result == default_instance

    @patch("kumihan_formatter.config.config_manager_utils.Path")
    @patch("kumihan_formatter.config.config_manager_utils.BaseConfig")
    def test_境界値_create_config_instance_ファイル存在しない(
        self, mock_base_config, mock_path
    ):
        """存在しないファイルパス指定時のテスト"""
        # Given: 存在しないファイルパス
        config_path = "/path/to/nonexistent.json"
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        default_instance = Mock()
        mock_base_config.return_value = default_instance

        # When: 存在しないファイルで設定インスタンスを作成
        result = create_config_instance("base", config_path)

        # Then: from_fileは呼ばれずデフォルトインスタンスが返される
        mock_base_config.from_file.assert_not_called()
        mock_base_config.assert_called_once()
        assert result == default_instance

    @patch("kumihan_formatter.config.config_manager_utils.BaseConfig")
    def test_境界値_create_config_instance_パスなし(self, mock_base_config):
        """config_pathがNoneの場合のテスト"""
        # Given: config_pathがNone
        config_path = None
        default_instance = Mock()
        mock_base_config.return_value = default_instance

        # When: パスなしで設定インスタンスを作成
        result = create_config_instance("base", config_path)

        # Then: デフォルトインスタンスが返される
        mock_base_config.assert_called_once()
        assert result == default_instance


class TestMergeConfigData:
    """merge_config_data 関数のテスト"""

    def test_正常系_merge_config_data_merge_config持つ設定(self):
        """merge_configメソッドを持つ設定オブジェクトのテスト"""
        # Given: merge_configメソッドを持つ設定オブジェクト
        config = Mock()
        config.merge_config = Mock()
        other_config = {"key1": "value1", "key2": "value2"}

        # When: 設定データをマージ
        merge_config_data(config, other_config)

        # Then: merge_configが呼び出される
        config.merge_config.assert_called_once_with(other_config)

    def test_正常系_merge_config_data_merge_config持たない設定(self):
        """merge_configメソッドを持たない設定オブジェクトのテスト"""
        # Given: merge_configメソッドを持たない設定オブジェクト
        config = Mock()
        config.set = Mock()
        # merge_configメソッドが存在しないことを明示的に設定
        del config.merge_config
        other_config = {"key1": "value1", "key2": "value2"}

        # When: 設定データをマージ
        merge_config_data(config, other_config)

        # Then: setメソッドが各項目で呼び出される
        expected_calls = [(("key1", "value1"),), (("key2", "value2"),)]
        config.set.assert_has_calls(expected_calls, any_order=True)

    def test_境界値_merge_config_data_空辞書(self):
        """空の辞書をマージする場合のテスト"""
        # Given: 空の辞書
        config = Mock()
        config.merge_config = Mock()
        other_config = {}

        # When: 空辞書をマージ
        merge_config_data(config, other_config)

        # Then: merge_configが空辞書で呼び出される
        config.merge_config.assert_called_once_with({})

    def test_正常系_merge_config_data_複雑構造(self):
        """ネストした辞書構造のマージテスト"""
        # Given: ネストした辞書構造
        config = Mock()
        config.set = Mock()
        # merge_configメソッドが存在しないことを明示的に設定
        del config.merge_config
        other_config = {
            "css": {"color": "#000000", "background": "#ffffff"},
            "theme": "dark",
            "features": ["feature1", "feature2"],
        }

        # When: 複雑な構造をマージ
        merge_config_data(config, other_config)

        # Then: 各トップレベルキーでsetが呼び出される
        assert config.set.call_count == 3
        calls = config.set.call_args_list
        call_keys = [call[0][0] for call in calls]
        assert "css" in call_keys
        assert "theme" in call_keys
        assert "features" in call_keys

    def test_正常系_merge_config_data_既存値上書き(self):
        """既存値の上書き処理のテスト"""
        # Given: merge_configを持つ設定オブジェクトと上書き用データ
        config = Mock()
        config.merge_config = Mock()
        other_config = {"existing_key": "new_value"}

        # When: 既存キーの値を上書き
        merge_config_data(config, other_config)

        # Then: merge_configが適切に呼び出される
        config.merge_config.assert_called_once_with(other_config)


class TestLoadConfigFile:
    """load_config_file 関数のテスト"""

    @patch("kumihan_formatter.config.config_manager_utils.create_config_instance")
    def test_正常系_load_config_file_読み込み成功(self, mock_create_config):
        """設定ファイルの読み込みが成功することを確認"""
        # Given: 設定ファイルパスと既存設定
        config_type = "extended"
        config_path = "/path/to/config.json"
        existing_config = Mock()
        existing_config.to_dict.return_value = {"existing": "data"}

        new_config = Mock()
        new_config.merge_config = Mock()
        mock_create_config.return_value = new_config

        # When: 設定ファイルを読み込み
        result = load_config_file(config_type, config_path, existing_config)

        # Then: 新しい設定インスタンスが返される
        mock_create_config.assert_called_once_with(config_type, config_path)
        new_config.merge_config.assert_called_once_with({"existing": "data"})
        assert result == new_config

    @patch("kumihan_formatter.config.config_manager_utils.create_config_instance")
    def test_正常系_load_config_file_既存設定統合(self, mock_create_config):
        """既存設定が新しい設定に統合されることを確認"""
        # Given: merge_config・to_dict両方を持つ設定
        config_type = "base"
        config_path = "/path/to/config.json"
        existing_config = Mock()
        existing_config.to_dict.return_value = {
            "theme": "light",
            "css": {"color": "#000"},
        }

        new_config = Mock()
        new_config.merge_config = Mock()
        mock_create_config.return_value = new_config

        # When: 既存設定を統合
        result = load_config_file(config_type, config_path, existing_config)

        # Then: 既存設定がマージされる
        expected_data = {"theme": "light", "css": {"color": "#000"}}
        new_config.merge_config.assert_called_once_with(expected_data)
        assert result == new_config

    @patch("kumihan_formatter.config.config_manager_utils.create_config_instance")
    def test_正常系_load_config_file_merge_config_to_dict両方(self, mock_create_config):
        """merge_config・to_dict両方のメソッドが存在する場合のテスト"""
        # Given: 両方のメソッドを持つ設定オブジェクト
        config_type = "extended"
        config_path = "/path/to/config.json"
        existing_config = Mock()
        existing_config.to_dict.return_value = {"data": "value"}

        new_config = Mock()
        new_config.merge_config = Mock()
        mock_create_config.return_value = new_config

        # When: 設定をロード
        result = load_config_file(config_type, config_path, existing_config)

        # Then: 正常にマージされる
        new_config.merge_config.assert_called_once()
        existing_config.to_dict.assert_called_once()
        assert result == new_config

    @patch("kumihan_formatter.config.config_manager_utils.create_config_instance")
    def test_境界値_load_config_file_メソッド欠落(self, mock_create_config):
        """merge_config または to_dict が欠落している場合のテスト"""
        # Given: to_dictメソッドを持たない既存設定
        config_type = "base"
        config_path = "/path/to/config.json"
        existing_config = Mock()
        # to_dictメソッドが存在しない
        del existing_config.to_dict

        new_config = Mock()
        # merge_configメソッドが存在しない
        del new_config.merge_config
        mock_create_config.return_value = new_config

        # When: メソッドが欠落した状態で設定をロード
        result = load_config_file(config_type, config_path, existing_config)

        # Then: 新しい設定がそのまま返される（マージはスキップ）
        assert result == new_config
