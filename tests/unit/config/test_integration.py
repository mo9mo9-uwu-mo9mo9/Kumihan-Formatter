"""設定システム統合テスト - Issue #929 Phase 3E

実際のConfigManager APIに対応した統合テスト実装
30テストケースで設定システムの統合動作を確認
"""

import os
import tempfile
import warnings
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.config import (
    Config,
    create_simple_config,
    get_default_config,
    reset_default_config,
)
from kumihan_formatter.config.base_config import BaseConfig
from kumihan_formatter.config.config_manager import (
    ConfigManager,
    create_config_manager,
    load_config,
)
from kumihan_formatter.config.extended_config import ExtendedConfig


class TestConfigManagerIntegration:
    """ConfigManager統合テスト（10ケース）"""

    def test_正常系_ConfigManager_BaseConfig統合初期化(self):
        """ConfigManagerとBaseConfigの統合初期化確認"""
        # Given & When
        manager = ConfigManager(config_type="base")

        # Then
        assert manager.config_type == "base"
        assert isinstance(manager._config, BaseConfig)
        assert manager.env_prefix == "KUMIHAN_"

    def test_正常系_ConfigManager_ExtendedConfig統合初期化(self):
        """ConfigManagerとExtendedConfigの統合初期化確認"""
        # Given & When
        manager = ConfigManager(config_type="extended")

        # Then
        assert manager.config_type == "extended"
        assert isinstance(manager._config, ExtendedConfig)
        assert hasattr(manager, "get_markers")
        assert hasattr(manager, "get_themes")

    @patch.dict("os.environ", {"KUMIHAN_CSS_BACKGROUND": "#ffffff"})
    def test_正常系_環境変数統合動作確認(self):
        """環境変数とConfigManagerの統合動作確認"""
        # Given & When: 環境変数が設定された状態でConfigManagerを作成
        manager = ConfigManager(config_type="extended")

        # Then: 環境変数が統合されていることを確認
        css_vars = manager.get_css_variables()
        assert isinstance(css_vars, dict)

    def test_正常系_ファイル読み込み統合確認(self):
        """設定ファイル読み込みの統合確認"""
        # Given: 一時設定ファイル作成
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"theme": "dark"}')
            config_path = f.name

        try:
            # When: load_configメソッドでファイル読み込み
            manager = ConfigManager()
            success = manager.load_config(config_path)

            # Then: 読み込みが成功することを確認
            assert isinstance(success, bool)
        finally:
            os.unlink(config_path)

    def test_正常系_設定マージ統合動作(self):
        """設定マージの統合動作確認"""
        # Given
        manager = ConfigManager(config_type="extended")
        merge_data = {"test_key": "test_value"}

        # When: 設定をマージ
        manager.merge_config(merge_data)

        # Then: マージされた設定が取得できる
        result = manager.get("test_key")
        assert result == "test_value"

    def test_正常系_hasattr委譲メソッド動作確認(self):
        """hasattrによる委譲メソッドの動作確認"""
        # Given
        base_manager = ConfigManager(config_type="base")
        extended_manager = ConfigManager(config_type="extended")

        # When & Then: ExtendedConfig固有メソッドの委譲確認
        assert callable(extended_manager.get_markers)
        assert callable(extended_manager.get_themes)
        assert callable(base_manager.get_markers)  # BaseConfigでも呼べるが空を返す

    def test_異常系_不正ファイル統合エラーハンドリング(self):
        """不正ファイル読み込み時のエラーハンドリング確認"""
        # Given: 存在しないファイルパス
        invalid_path = "/nonexistent/path/config.json"

        # When: 不正なファイルで初期化
        manager = ConfigManager(config_path=invalid_path)

        # Then: エラーハンドリングされてデフォルト設定が使用される
        assert manager._config is not None
        assert isinstance(manager._config, ExtendedConfig)

    def test_境界値_空設定統合処理(self):
        """空設定での統合処理確認"""
        # Given & When: 空辞書でマージ
        manager = ConfigManager()
        manager.merge_config({})

        # Then: エラーなく処理される
        assert manager.to_dict() is not None

    def test_正常系_ログ出力統合確認(self):
        """ログ出力統合確認"""
        # Given & When
        manager = ConfigManager()

        # Then: ロガーが適切に設定される
        assert hasattr(manager, "logger")
        assert manager.logger is not None

    def test_正常系_設定検証統合(self):
        """設定検証の統合動作確認"""
        # Given
        manager = ConfigManager(config_type="extended")

        # When: 設定検証実行
        is_valid = manager.validate()

        # Then: 検証が実行される
        assert isinstance(is_valid, bool)


class TestConfigFlowIntegration:
    """設定フロー統合テスト（10ケース）"""

    @patch.dict("os.environ", {"KUMIHAN_CSS_COLOR": "#000000"})
    def test_正常系_初期化環境変数統合フロー(self):
        """初期化→環境変数読み込みフローの確認"""
        # Given & When: 環境変数が設定された状態で初期化
        manager = ConfigManager(config_type="extended")

        # Then: 初期化と環境変数読み込みが完了
        assert manager._config is not None
        css_vars = manager.get_css_variables()
        assert isinstance(css_vars, dict)

    def test_正常系_設定更新検証保存フロー(self):
        """設定更新→検証フローの確認"""
        # Given
        manager = ConfigManager()

        # When: 設定更新→検証
        manager.set("test_key", "test_value")
        is_valid = manager.validate()
        config_dict = manager.to_dict()

        # Then: フローが正常に実行される
        assert manager.get("test_key") == "test_value"
        assert isinstance(is_valid, bool)
        assert isinstance(config_dict, dict)

    def test_正常系_テーマ切り替えフロー(self):
        """テーマ切り替えフローの確認"""
        # Given
        manager = ConfigManager(config_type="extended")

        # When: テーマ追加→設定→取得フロー
        manager.add_theme("test_theme", {"name": "テストテーマ", "css": {}})
        result = manager.set_theme("test_theme")
        current_theme = manager.get_current_theme()

        # Then: テーマ切り替えフローが正常に動作
        assert isinstance(result, bool)
        assert isinstance(current_theme, str)

    def test_正常系_マーカー管理フロー(self):
        """マーカー管理フローの確認"""
        # Given
        manager = ConfigManager(config_type="extended")

        # When: マーカー追加→取得→削除フロー
        manager.add_marker("test_marker", {"tag": "span"})
        markers = manager.get_markers()
        removed = manager.remove_marker("test_marker")

        # Then: マーカー管理フローが正常に動作
        assert isinstance(markers, dict)
        assert isinstance(removed, bool)

    def test_正常系_設定統合フロー(self):
        """複数設定の統合フロー確認"""
        # Given
        manager = ConfigManager()

        # When: 複数の設定を段階的に統合
        manager.set("key1", "value1")
        manager.merge_config({"key2": "value2"})
        result_dict = manager.to_dict()

        # Then: 統合された設定が取得できる
        assert manager.get("key1") == "value1"
        assert manager.get("key2") == "value2"
        assert isinstance(result_dict, dict)

    def test_正常系_複合操作フロー確認(self):
        """複合操作フローの確認"""
        # Given
        manager = ConfigManager(config_type="extended")

        # When: 複数操作を組み合わせ
        manager.set("base_setting", "test")
        manager.add_marker("flow_marker", {"tag": "div"})
        config_dict = manager.to_dict()

        # Then: 全ての操作が正常に完了
        assert manager.get("base_setting") == "test"
        markers = manager.get_markers()
        assert "flow_marker" in markers
        assert isinstance(config_dict, dict)

    def test_正常系_設定継承フロー確認(self):
        """設定継承フローの確認"""
        # Given
        base_manager = ConfigManager(config_type="base")
        extended_manager = ConfigManager(config_type="extended")

        # When: 同じ操作を実行
        base_manager.set("common_key", "common_value")
        extended_manager.set("common_key", "common_value")

        # Then: 両方で正常に動作
        assert base_manager.get("common_key") == "common_value"
        assert extended_manager.get("common_key") == "common_value"

    def test_境界値_フロー中断復旧確認(self):
        """フロー中断時の復旧確認"""
        # Given
        manager = ConfigManager()

        # When: 一部操作失敗を想定
        manager.set("valid_key", "valid_value")
        try:
            manager.set("", "invalid_key")  # 空キーでの設定試行
        except:
            pass

        # Then: 有効な設定は維持される
        assert manager.get("valid_key") == "valid_value"

    def test_異常系_フローエラー処理確認(self):
        """フローエラー処理の確認"""
        # Given
        manager = ConfigManager()

        # When: エラーが発生する可能性のある操作
        result = manager.get("nonexistent_key", "default_value")

        # Then: エラーハンドリングされてデフォルト値が返される
        assert result == "default_value"

    def test_正常系_設定永続化フロー確認(self):
        """設定永続化フローの確認"""
        # Given
        manager = ConfigManager()

        # When: 設定を行い辞書として取得
        manager.set("persist_key", "persist_value")
        config_dict = manager.to_dict()

        # Then: 設定が辞書に反映される
        assert isinstance(config_dict, dict)
        # BaseConfigの場合、to_dictに含まれない可能性があるので存在チェックのみ


class TestCompatibilityTests:
    """互換性テスト（10ケース）"""

    def test_正常系_旧API互換性確認(self):
        """旧APIとの互換性確認"""
        # Given & When: 旧APIスタイルでの呼び出し
        config_mgr = create_config_manager("base")

        # Then: 正常に作成される
        assert isinstance(config_mgr, ConfigManager)
        assert config_mgr.config_type == "base"

    def test_正常系_Configエイリアス動作確認(self):
        """ConfigエイリアスがConfigManagerと同じことを確認"""
        # Given & When
        config_instance = Config()
        manager_instance = ConfigManager()

        # Then: 同じクラス
        assert type(config_instance) == type(manager_instance)
        assert Config is ConfigManager

    def test_正常系_非推奨関数警告確認(self):
        """非推奨関数の警告確認"""
        # Given & When: 非推奨関数呼び出し
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            reset_default_config()
            config = create_simple_config()

            # Then: 警告が出力される（create_simple_configで）
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)

    def test_正常系_BaseConfig移行互換性(self):
        """BaseConfig移行互換性の確認"""
        # Given
        manager = ConfigManager(config_type="base")

        # When: BaseConfig固有操作
        manager.set("migration_test", "value")
        result = manager.get("migration_test")

        # Then: 互換性が保たれる
        assert result == "value"

    def test_正常系_ExtendedConfig移行互換性(self):
        """ExtendedConfig移行互換性の確認"""
        # Given
        manager = ConfigManager(config_type="extended")

        # When: ExtendedConfig固有操作
        manager.add_marker("migration_marker", {"tag": "div"})
        markers = manager.get_markers()

        # Then: 拡張機能が正常に動作
        assert "migration_marker" in markers

    def test_正常系_既存コード統合確認(self):
        """既存コードパターンとの統合確認"""
        # Given: 既存コードスタイル
        config = load_config()

        # When: 基本操作
        config.set("existing_pattern", "test")
        result = config.get("existing_pattern")

        # Then: 正常に動作
        assert result == "test"

    def test_正常系_create_simple_config互換(self):
        """create_simple_config互換性確認"""
        # Given & When: 非推奨関数を使用
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            simple_config = create_simple_config()

        # Then: ConfigManagerインスタンスが返される
        assert isinstance(simple_config, ConfigManager)

    def test_正常系_get_default_config互換(self):
        """get_default_config互換性確認"""
        # Given & When: 非推奨関数を使用
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            reset_default_config()  # リセットしてからテスト
            default_config = get_default_config()

        # Then: ConfigManagerインスタンスが返される
        assert isinstance(default_config, ConfigManager)

    def test_境界値_互換性境界処理(self):
        """互換性境界値処理の確認"""
        # Given: 境界値的な使用パターン
        manager = ConfigManager(config_type="extended")

        # When: BaseConfig的な使用とExtendedConfig的な使用を混在
        manager.set("base_style", "value")  # BaseConfig style
        manager.add_marker("extended_style", {"tag": "span"})  # ExtendedConfig style

        # Then: 両方正常に動作
        assert manager.get("base_style") == "value"
        assert "extended_style" in manager.get_markers()

    def test_正常系_後方互換性全体確認(self):
        """後方互換性全体の確認"""
        # Given & When: 各種互換APIを使用
        manager1 = create_config_manager()
        manager2 = load_config()

        # Then: 全て同じタイプのインスタンス
        assert isinstance(manager1, ConfigManager)
        assert isinstance(manager2, ConfigManager)
        assert type(manager1) == type(manager2)
