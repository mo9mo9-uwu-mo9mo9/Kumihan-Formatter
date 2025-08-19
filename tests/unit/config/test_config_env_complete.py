"""config_manager_env.py の包括的テスト

Issue #929 Phase 3C: ConfigEnvironmentHandler テスト
15テストケースで環境変数管理機能の70%カバレッジ達成
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from kumihan_formatter.config.config_manager_env import ConfigEnvironmentHandler
from kumihan_formatter.config.base_config import BaseConfig
from kumihan_formatter.config.extended_config import ExtendedConfig


class TestConfigEnvironmentHandlerInitialization:
    """ConfigEnvironmentHandler初期化のテスト"""

    def test_正常系_初期化_デフォルトプレフィックス(self):
        """デフォルトのenv_prefixで初期化されることを確認"""
        # Given: デフォルト初期化パラメーター
        # When: ConfigEnvironmentHandlerを初期化
        handler = ConfigEnvironmentHandler()

        # Then: デフォルトのプレフィックスが設定される
        assert handler.env_prefix == "KUMIHAN_"

    def test_正常系_初期化_カスタムプレフィックス(self):
        """カスタムのenv_prefixで初期化されることを確認"""
        # Given: カスタムプレフィックス
        custom_prefix = "CUSTOM_"

        # When: カスタムプレフィックスで初期化
        handler = ConfigEnvironmentHandler(env_prefix=custom_prefix)

        # Then: カスタムプレフィックスが設定される
        assert handler.env_prefix == custom_prefix

    def test_正常系_初期化_属性確認(self):
        """初期化後の属性が正しく設定されることを確認"""
        # Given: 任意のプレフィックス
        prefix = "TEST_"

        # When: ハンドラーを初期化
        handler = ConfigEnvironmentHandler(env_prefix=prefix)

        # Then: 属性が適切に設定される
        assert hasattr(handler, 'env_prefix')
        assert handler.env_prefix == prefix
        assert hasattr(handler, 'load_from_env')
        assert hasattr(handler, '_extract_env_config')
        assert hasattr(handler, '_extract_css_vars')


class TestConfigEnvironmentHandlerLoadFromEnv:
    """load_from_env メソッドのテスト"""

    @patch.dict('os.environ', {'KUMIHAN_CSS_BACKGROUND': '#ffffff', 'KUMIHAN_THEME': 'light'})
    def test_正常系_load_from_env_merge_config持つ設定(self):
        """merge_configメソッドを持つ設定オブジェクトのテスト"""
        # Given: merge_configメソッドを持つ設定オブジェクト
        config = Mock()
        config.merge_config = Mock()
        handler = ConfigEnvironmentHandler()

        # When: 環境変数から設定を読み込み
        handler.load_from_env(config)

        # Then: merge_configが呼び出される
        config.merge_config.assert_called_once()
        call_args = config.merge_config.call_args[0][0]
        assert 'css' in call_args
        assert 'theme' in call_args
        assert call_args['css']['background'] == '#ffffff'
        assert call_args['theme'] == 'light'

    @patch.dict('os.environ', {'KUMIHAN_CSS_COLOR': '#000000'})
    def test_正常系_load_from_env_merge_config持たない設定(self):
        """merge_configメソッドを持たない設定オブジェクトのテスト"""
        # Given: merge_configメソッドを持たない設定オブジェクト
        config = Mock()
        config.set = Mock()
        # merge_configメソッドが存在しないことを明示的に設定
        del config.merge_config
        handler = ConfigEnvironmentHandler()

        # When: 環境変数から設定を読み込み
        handler.load_from_env(config)

        # Then: setメソッドが各設定項目で呼び出される
        config.set.assert_called()
        calls = config.set.call_args_list
        assert len(calls) == 1
        assert calls[0][0] == ('css', {'color': '#000000'})

    @patch.dict('os.environ', {}, clear=True)
    def test_境界値_load_from_env_空環境変数(self):
        """環境変数が空の場合のテスト"""
        # Given: 空の環境変数
        config = Mock()
        config.merge_config = Mock()
        handler = ConfigEnvironmentHandler()

        # When: 環境変数から設定を読み込み
        handler.load_from_env(config)

        # Then: env_configが空のため何もメソッドが呼び出されない
        config.merge_config.assert_not_called()

    @patch.dict('os.environ', {'KUMIHAN_CSS_BACKGROUND_COLOR': '#ff0000', 'KUMIHAN_THEME': 'dark'})
    def test_正常系_load_from_env_CSS_テーマ混在(self):
        """CSS・テーマ環境変数が混在した場合のテスト"""
        # Given: CSS・テーマ環境変数が設定された状態
        config = Mock()
        config.set = Mock()
        # merge_configメソッドが存在しないことを明示的に設定
        del config.merge_config
        handler = ConfigEnvironmentHandler()

        # When: 環境変数から設定読み込み
        handler.load_from_env(config)

        # Then: CSS・テーマが適切に設定される
        calls = config.set.call_args_list
        assert len(calls) == 2
        # CSS設定の確認
        css_call = next(call for call in calls if call[0][0] == 'css')
        assert css_call[0][1] == {'background_color': '#ff0000'}
        # テーマ設定の確認
        theme_call = next(call for call in calls if call[0][0] == 'theme')
        assert theme_call[0][1] == 'dark'


class TestConfigEnvironmentHandlerExtractEnvConfig:
    """_extract_env_config メソッドのテスト"""

    @patch.dict('os.environ', {'KUMIHAN_CSS_COLOR': '#123456'})
    def test_正常系_extract_env_config_CSS変数のみ(self):
        """CSS変数のみが存在する場合のテスト"""
        # Given: CSS変数のみ設定された環境
        handler = ConfigEnvironmentHandler()

        # When: 環境変数設定を抽出
        result = handler._extract_env_config()

        # Then: CSS設定のみが返される
        assert 'css' in result
        assert result['css']['color'] == '#123456'
        assert 'theme' not in result

    @patch.dict('os.environ', {'KUMIHAN_THEME': 'custom'})
    def test_正常系_extract_env_config_テーマ変数のみ(self):
        """テーマ変数のみが存在する場合のテスト"""
        # Given: テーマ変数のみ設定された環境
        handler = ConfigEnvironmentHandler()

        # When: 環境変数設定を抽出
        result = handler._extract_env_config()

        # Then: テーマ設定のみが返される
        assert 'theme' in result
        assert result['theme'] == 'custom'
        assert 'css' not in result

    @patch.dict('os.environ', {'KUMIHAN_CSS_FONT_SIZE': '16px', 'KUMIHAN_THEME': 'dark'})
    def test_正常系_extract_env_config_CSS_テーマ混在(self):
        """CSS・テーマ変数が混在する場合のテスト"""
        # Given: CSS・テーマ変数が混在した環境
        handler = ConfigEnvironmentHandler()

        # When: 環境変数設定を抽出
        result = handler._extract_env_config()

        # Then: 両方の設定が返される
        assert 'css' in result
        assert 'theme' in result
        assert result['css']['font_size'] == '16px'
        assert result['theme'] == 'dark'

    @patch.dict('os.environ', {}, clear=True)
    def test_境界値_extract_env_config_変数なし(self):
        """関連環境変数が存在しない場合のテスト"""
        # Given: 関連環境変数が存在しない環境
        handler = ConfigEnvironmentHandler()

        # When: 環境変数設定を抽出
        result = handler._extract_env_config()

        # Then: 空辞書が返される
        assert result == {}


class TestConfigEnvironmentHandlerExtractCssVars:
    """_extract_css_vars メソッドのテスト"""

    @patch.dict('os.environ', {'KUMIHAN_CSS_MARGIN': '10px'})
    def test_正常系_extract_css_vars_プレフィックス抽出(self):
        """CSS環境変数のプレフィックスが適切に除去されることを確認"""
        # Given: CSS環境変数が設定された状態
        handler = ConfigEnvironmentHandler()

        # When: CSS変数を抽出
        result = handler._extract_css_vars()

        # Then: プレフィックスが除去され、小文字化される
        assert 'margin' in result
        assert result['margin'] == '10px'

    @patch.dict('os.environ', {
        'KUMIHAN_CSS_FONT_SIZE': '14px',
        'KUMIHAN_CSS_LINE_HEIGHT': '1.5',
        'KUMIHAN_CSS_PADDING': '8px'
    })
    def test_正常系_extract_css_vars_複数CSS変数(self):
        """複数のCSS変数が存在する場合のテスト"""
        # Given: 複数のCSS環境変数が設定された状態
        handler = ConfigEnvironmentHandler()

        # When: CSS変数を抽出
        result = handler._extract_css_vars()

        # Then: 全てのCSS変数が抽出される
        assert len(result) == 3
        assert result['font_size'] == '14px'
        assert result['line_height'] == '1.5'
        assert result['padding'] == '8px'

    @patch.dict('os.environ', {'KUMIHAN_CSS_BACKGROUND_COLOR': '#FFFFFF'})
    def test_正常系_extract_css_vars_大文字小文字変換(self):
        """大文字の環境変数が小文字に変換されることを確認"""
        # Given: 大文字を含むCSS環境変数
        handler = ConfigEnvironmentHandler()

        # When: CSS変数を抽出
        result = handler._extract_css_vars()

        # Then: 変数名が小文字に変換される
        assert 'background_color' in result
        assert result['background_color'] == '#FFFFFF'

    @patch.dict('os.environ', {'OTHER_VAR': 'value', 'KUMIHAN_THEME': 'dark'})
    def test_境界値_extract_css_vars_CSS変数なし(self):
        """CSS変数が存在しない場合のテスト"""
        # Given: CSS以外の環境変数のみ設定された状態
        handler = ConfigEnvironmentHandler()

        # When: CSS変数を抽出
        result = handler._extract_css_vars()

        # Then: 空辞書が返される
        assert result == {}
