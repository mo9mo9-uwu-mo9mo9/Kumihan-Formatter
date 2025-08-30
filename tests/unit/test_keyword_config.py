"""
キーワード設定関連のユニットテスト

このテストファイルは、kumihan_formatter.parsers.keyword_config と
kumihan_formatter.parsers.keyword_definitions の基本機能をテストします。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, Set

# インポートエラー回避のため、try-except でインポート
try:
    from kumihan_formatter.parsers.keyword_config import KeywordParserConfig

    KEYWORD_CONFIG_AVAILABLE = True
except ImportError:
    KeywordParserConfig = None
    KEYWORD_CONFIG_AVAILABLE = False


@pytest.mark.skipif(
    not KEYWORD_CONFIG_AVAILABLE, reason="KeywordParserConfig not available"
)
class TestKeywordParserConfig:
    """KeywordParserConfigクラスのテスト"""

    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_definitions")
    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_patterns")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordCache")
    @patch("kumihan_formatter.parsers.keyword_config.BasicKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AdvancedKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.CustomKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AttributeProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordExtractor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordInfoProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordValidatorCollection")
    def test_initialization(
        self,
        mock_validator,
        mock_info_proc,
        mock_extractor,
        mock_attr_proc,
        mock_custom_handler,
        mock_adv_handler,
        mock_basic_handler,
        mock_cache,
        mock_patterns,
        mock_definitions,
    ):
        """初期化テスト"""
        # モックの設定
        mock_definitions.return_value = {
            "basic": {"keyword1", "keyword2"},
            "advanced": {"adv_keyword1"},
            "all": {"keyword1", "keyword2", "adv_keyword1"},
        }

        mock_basic_handler_instance = Mock()
        mock_basic_handler_instance.handlers = {"basic_handler": "value"}
        mock_basic_handler.return_value = mock_basic_handler_instance

        mock_adv_handler_instance = Mock()
        mock_adv_handler_instance.handlers = {"adv_handler": "value"}
        mock_adv_handler.return_value = mock_adv_handler_instance

        mock_custom_handler_instance = Mock()
        mock_custom_handler_instance.custom_handlers = {"custom_handler": "value"}
        mock_custom_handler.return_value = mock_custom_handler_instance

        # テスト実行
        config = KeywordParserConfig()

        # 初期化の確認
        assert hasattr(config, "logger")
        assert hasattr(config, "keyword_definitions")
        assert hasattr(config, "basic_keywords")
        assert hasattr(config, "advanced_keywords")
        assert hasattr(config, "all_keywords")

        # セットアップ関数が呼ばれることを確認
        mock_definitions.assert_called_once()
        mock_patterns.assert_called_once()

    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_definitions")
    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_patterns")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordCache")
    @patch("kumihan_formatter.parsers.keyword_config.BasicKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AdvancedKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.CustomKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AttributeProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordExtractor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordInfoProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordValidatorCollection")
    def test_get_handlers(self, *mocks):
        """get_handlersメソッドのテスト"""
        # モックの設定
        setup_keyword_definitions_mock = mocks[9]  # 逆順なので注意
        setup_keyword_definitions_mock.return_value = {
            "basic": {"test"},
            "advanced": {"test"},
            "all": {"test"},
        }

        # ハンドラーのモック設定
        basic_handler_mock = mocks[6]
        adv_handler_mock = mocks[5]
        custom_handler_mock = mocks[4]

        basic_instance = Mock()
        basic_instance.handlers = {"basic": "handler1"}
        basic_handler_mock.return_value = basic_instance

        adv_instance = Mock()
        adv_instance.handlers = {"advanced": "handler2"}
        adv_handler_mock.return_value = adv_instance

        custom_instance = Mock()
        custom_instance.custom_handlers = {"custom": "handler3"}
        custom_handler_mock.return_value = custom_instance

        config = KeywordParserConfig()
        handlers = config.get_handlers()

        assert isinstance(handlers, dict)
        assert "basic" in handlers
        assert "advanced" in handlers
        assert "custom" in handlers

    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_definitions")
    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_patterns")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordCache")
    @patch("kumihan_formatter.parsers.keyword_config.BasicKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AdvancedKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.CustomKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AttributeProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordExtractor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordInfoProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordValidatorCollection")
    def test_get_basic_keywords(self, *mocks):
        """get_basic_keywordsメソッドのテスト"""
        setup_keyword_definitions_mock = mocks[9]
        basic_keywords = {"bold", "italic", "underline"}
        setup_keyword_definitions_mock.return_value = {
            "basic": basic_keywords,
            "advanced": {"advanced1"},
            "all": basic_keywords | {"advanced1"},
        }

        config = KeywordParserConfig()
        result = config.get_basic_keywords()

        assert result == basic_keywords
        assert isinstance(result, set)

    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_definitions")
    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_patterns")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordCache")
    @patch("kumihan_formatter.parsers.keyword_config.BasicKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AdvancedKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.CustomKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AttributeProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordExtractor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordInfoProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordValidatorCollection")
    def test_get_advanced_keywords(self, *mocks):
        """get_advanced_keywordsメソッドのテスト"""
        setup_keyword_definitions_mock = mocks[9]
        advanced_keywords = {"ruby", "link", "image"}
        setup_keyword_definitions_mock.return_value = {
            "basic": {"basic1"},
            "advanced": advanced_keywords,
            "all": {"basic1"} | advanced_keywords,
        }

        config = KeywordParserConfig()
        result = config.get_advanced_keywords()

        assert result == advanced_keywords
        assert isinstance(result, set)

    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_definitions")
    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_patterns")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordCache")
    @patch("kumihan_formatter.parsers.keyword_config.BasicKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AdvancedKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.CustomKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AttributeProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordExtractor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordInfoProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordValidatorCollection")
    def test_get_all_keywords(self, *mocks):
        """get_all_keywordsメソッドのテスト"""
        setup_keyword_definitions_mock = mocks[9]
        basic_keywords = {"bold", "italic"}
        advanced_keywords = {"ruby", "link"}
        all_keywords = basic_keywords | advanced_keywords

        setup_keyword_definitions_mock.return_value = {
            "basic": basic_keywords,
            "advanced": advanced_keywords,
            "all": all_keywords,
        }

        config = KeywordParserConfig()
        result = config.get_all_keywords()

        assert result == all_keywords
        assert isinstance(result, set)
        assert len(result) == 4


class TestKeywordDefinitions:
    """KeywordDefinitionsクラスのテスト"""

    def test_default_block_keywords_import(self):
        """DEFAULT_BLOCK_KEYWORDSのインポートテスト"""
        from kumihan_formatter.parsers.keyword_definitions import DEFAULT_BLOCK_KEYWORDS

        assert DEFAULT_BLOCK_KEYWORDS is not None
        assert isinstance(DEFAULT_BLOCK_KEYWORDS, (set, list, tuple))

    def test_keyword_definitions_import(self):
        """KeywordDefinitionsクラスのインポートテスト"""
        from kumihan_formatter.parsers.keyword_definitions import KeywordDefinitions

        assert KeywordDefinitions is not None
        # インスタンス化可能であることを確認
        instance = KeywordDefinitions()
        assert instance is not None


@pytest.mark.skipif(
    not KEYWORD_CONFIG_AVAILABLE, reason="KeywordParserConfig not available"
)
class TestKeywordConfigIntegration:
    """キーワード設定の統合テスト"""

    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_definitions")
    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_patterns")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordCache")
    @patch("kumihan_formatter.parsers.keyword_config.BasicKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AdvancedKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.CustomKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AttributeProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordExtractor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordInfoProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordValidatorCollection")
    def test_keyword_setup_integration(self, *mocks):
        """キーワードセットアップの統合テスト"""
        setup_keyword_definitions_mock = mocks[9]
        setup_keyword_patterns_mock = mocks[8]

        # 実際のキーワード定義に近い構造を模擬
        keyword_definitions = {
            "basic": {"太字", "斜体", "下線", "取消線"},
            "advanced": {"ルビ", "リンク", "画像", "コード"},
            "all": {
                "太字",
                "斜体",
                "下線",
                "取消線",
                "ルビ",
                "リンク",
                "画像",
                "コード",
            },
        }

        setup_keyword_definitions_mock.return_value = keyword_definitions
        setup_keyword_patterns_mock.return_value = {"pattern": "test"}

        config = KeywordParserConfig()

        # 各種ゲッターメソッドのテスト
        basic = config.get_basic_keywords()
        advanced = config.get_advanced_keywords()
        all_keywords = config.get_all_keywords()

        assert len(basic) == 4
        assert len(advanced) == 4
        assert len(all_keywords) == 8
        assert basic.isdisjoint(advanced) or len(basic & advanced) == 0  # 重複なし

    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_definitions")
    @patch("kumihan_formatter.parsers.keyword_config.setup_keyword_patterns")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordCache")
    @patch("kumihan_formatter.parsers.keyword_config.BasicKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AdvancedKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.CustomKeywordHandler")
    @patch("kumihan_formatter.parsers.keyword_config.AttributeProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordExtractor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordInfoProcessor")
    @patch("kumihan_formatter.parsers.keyword_config.KeywordValidatorCollection")
    def test_modular_components_setup(self, *mocks):
        """モジュラーコンポーネントのセットアップテスト"""
        setup_keyword_definitions_mock = mocks[9]
        setup_keyword_definitions_mock.return_value = {
            "basic": set(),
            "advanced": set(),
            "all": set(),
        }

        # 各コンポーネントのモック設定
        cache_mock = mocks[7]
        basic_handler_mock = mocks[6]
        advanced_handler_mock = mocks[5]
        custom_handler_mock = mocks[4]
        attr_processor_mock = mocks[3]
        extractor_mock = mocks[2]
        info_processor_mock = mocks[1]
        validator_mock = mocks[0]

        # インスタンス化
        config = KeywordParserConfig()

        # 全コンポーネントが初期化されることを確認
        cache_mock.assert_called_once()
        basic_handler_mock.assert_called_once()
        advanced_handler_mock.assert_called_once()
        custom_handler_mock.assert_called_once()
        attr_processor_mock.assert_called_once()
        extractor_mock.assert_called_once()
        info_processor_mock.assert_called_once()
        validator_mock.assert_called_once()

        # 属性が設定されることを確認
        assert hasattr(config, "cache")
        assert hasattr(config, "basic_handler")
        assert hasattr(config, "advanced_handler")
        assert hasattr(config, "custom_handler")
        assert hasattr(config, "attribute_processor")
        assert hasattr(config, "keyword_extractor")
        assert hasattr(config, "info_processor")
        assert hasattr(config, "validator_collection")
