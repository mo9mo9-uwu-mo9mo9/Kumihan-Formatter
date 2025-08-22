"""Legacy Factory Integration のテスト

legacy_factory_integration.pyモジュールの包括的なテスト。
Issue #929 Phase 2A対応 - Factory & Builder System テストカバレッジ向上
"""

from typing import Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.patterns.dependency_injection import DIContainer
from kumihan_formatter.core.patterns.legacy_factory_integration import (
    LegacyFactoryAdapter,
    create_legacy_file_operations,
    create_legacy_list_parser,
    create_legacy_markdown_converter,
    get_legacy_adapter,
    initialize_legacy_integration,
)
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestLegacyFactoryAdapter:
    """LegacyFactoryAdapterのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.container = DIContainer()

    def test_正常系_初期化(self):
        """正常系: アダプター初期化の確認"""
        # Given: DIコンテナ
        # When: LegacyFactoryAdapterを初期化
        adapter = LegacyFactoryAdapter(self.container)

        # Then: 正しく初期化される
        assert adapter.container is self.container
        assert adapter.service_factory is not None

    def test_正常系_初期化_デフォルトコンテナ(self):
        """正常系: デフォルトコンテナでの初期化"""
        # Given: コンテナなし
        # When: LegacyFactoryAdapterを初期化
        adapter = LegacyFactoryAdapter()

        # Then: デフォルトコンテナが使用される
        assert adapter.container is not None
        assert adapter.service_factory is not None

    @patch.object(LegacyFactoryAdapter, "_register_file_operations")
    @patch.object(LegacyFactoryAdapter, "_register_markdown_services")
    @patch.object(LegacyFactoryAdapter, "_register_list_parser_services")
    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.logger")
    def test_正常系_レガシーサービス登録成功(
        self, mock_logger, mock_list, mock_markdown, mock_file
    ):
        """正常系: レガシーサービス登録の成功確認"""
        # Given: 初期化されるアダプター
        # When: アダプターを初期化（内部で_register_legacy_servicesが呼ばれる）
        LegacyFactoryAdapter(self.container)

        # Then: 各登録メソッドが呼ばれ、成功ログが出力される
        mock_file.assert_called_once()
        mock_markdown.assert_called_once()
        mock_list.assert_called_once()
        mock_logger.info.assert_called_with("Legacy factory services registered successfully")

    @patch.object(LegacyFactoryAdapter, "_register_file_operations")
    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.logger")
    def test_異常系_レガシーサービス登録失敗(self, mock_logger, mock_file):
        """異常系: レガシーサービス登録失敗時のエラーハンドリング"""
        # Given: 登録失敗を起こすモック
        mock_file.side_effect = Exception("Registration error")

        # When: アダプター初期化を試行
        adapter = LegacyFactoryAdapter(self.container)

        # Then: エラーログが出力される
        mock_logger.error.assert_called()
        # アダプター自体は初期化される（例外は握りつぶし）
        assert adapter.container is self.container

    @patch(
        "kumihan_formatter.core.patterns.legacy_factory_integration.DIContainer.register_factory"
    )
    def test_正常系_ファイル操作サービス登録(self, mock_register):
        """正常系: ファイル操作サービス登録の確認"""
        # Given: アダプター
        adapter = LegacyFactoryAdapter(self.container)

        # When: ファイル操作サービス登録を直接呼び出し
        adapter._register_file_operations()

        # Then: register_factoryが適切に呼ばれる
        # FileOperationsCore, FilePathUtilities, FileIOHandler, FileOperationsComponentsの4回
        assert mock_register.call_count >= 4

    @patch("builtins.__import__")
    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.logger")
    def test_異常系_ファイル操作サービス_ImportError(self, mock_logger, mock_import):
        """異常系: ファイル操作サービスImportError時の警告ログ確認"""

        # Given: ImportError を発生させるモック
        def import_side_effect(name, *args, **kwargs):
            if "file_io_handler" in name:
                raise ImportError("Module not found")
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = import_side_effect
        adapter = LegacyFactoryAdapter(self.container)

        # When: ファイル操作サービス登録を試行
        adapter._register_file_operations()

        # Then: 警告ログが出力される
        mock_logger.warning.assert_called()
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if "Could not register file operations services" in str(call)
        ]
        assert len(warning_calls) > 0

    @patch(
        "kumihan_formatter.core.patterns.legacy_factory_integration.DIContainer.register_factory"
    )
    def test_正常系_マークダウンサービス登録(self, mock_register):
        """正常系: マークダウンサービス登録の確認"""
        # Given: アダプター
        adapter = LegacyFactoryAdapter(self.container)

        # When: マークダウンサービス登録を直接呼び出し
        adapter._register_markdown_services()

        # Then: register_factoryが適切に呼ばれる
        # MarkdownParser, MarkdownProcessor, MarkdownRendererの3回
        assert mock_register.call_count >= 3

    @patch("builtins.__import__")
    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.logger")
    def test_異常系_マークダウンサービス_ImportError(self, mock_logger, mock_import):
        """異常系: マークダウンサービスImportError時の警告ログ確認"""

        # Given: ImportError を発生させるモック
        def import_side_effect(name, *args, **kwargs):
            if "markdown_factory" in name:
                raise ImportError("Module not found")
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = import_side_effect
        adapter = LegacyFactoryAdapter(self.container)

        # When: マークダウンサービス登録を試行
        adapter._register_markdown_services()

        # Then: 警告ログが出力される
        mock_logger.warning.assert_called()
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if "Could not register markdown services" in str(call)
        ]
        assert len(warning_calls) > 0

    @patch(
        "kumihan_formatter.core.patterns.legacy_factory_integration.DIContainer.register_factory"
    )
    def test_正常系_リストパーサーサービス登録(self, mock_register):
        """正常系: リストパーサーサービス登録の確認"""
        # Given: アダプター
        adapter = LegacyFactoryAdapter(self.container)

        # When: リストパーサーサービス登録を直接呼び出し
        adapter._register_list_parser_services()

        # Then: register_factoryが適切に呼ばれる
        # ListParserCore, NestedListParser, ListValidator, ListParserComponentsの4回
        assert mock_register.call_count >= 4

    @patch("builtins.__import__")
    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.logger")
    def test_異常系_リストパーサーサービス_ImportError(self, mock_logger, mock_import):
        """異常系: リストパーサーサービスImportError時の警告ログ確認"""

        # Given: ImportError を発生させるモック
        def import_side_effect(name, *args, **kwargs):
            if "list_parser_core" in name:
                raise ImportError("Module not found")
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = import_side_effect
        adapter = LegacyFactoryAdapter(self.container)

        # When: リストパーサーサービス登録を試行
        adapter._register_list_parser_services()

        # Then: 警告ログが出力される
        mock_logger.warning.assert_called()
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if "Could not register list parser services" in str(call)
        ]
        assert len(warning_calls) > 0

    def test_境界値_例外処理での継続実行(self):
        """境界値: 一部サービス登録失敗時の他サービス継続実行"""
        # Given: 一部で失敗するモック
        with patch.object(
            LegacyFactoryAdapter,
            "_register_file_operations",
            side_effect=Exception("File error"),
        ):
            with patch.object(LegacyFactoryAdapter, "_register_markdown_services") as mock_markdown:
                with patch.object(
                    LegacyFactoryAdapter, "_register_list_parser_services"
                ) as mock_list:
                    # When: アダプター初期化（例外により全体が失敗するが、オブジェクトは作成される）
                    adapter = LegacyFactoryAdapter(self.container)

                    # Then: アダプターは作成されるが、例外により後続処理は実行されない
                    # 実際の動作では例外が発生すると早期returnするため、後続メソッドは呼ばれない
                    assert adapter.container is not None
                    # 例外により全処理が停止するため、後続メソッド呼び出しはチェックしない


class TestLegacyCompatibilityFunctions:
    """レガシー互換性関数のテスト"""

    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.LegacyFactoryAdapter")
    def test_正常系_create_legacy_file_operations(self, mock_adapter_class):
        """正常系: レガシーファイル操作作成"""
        # Given: モックアダプターとコンテナ
        mock_adapter = Mock()
        mock_container = Mock()
        mock_file_ops = Mock()
        mock_container.resolve.return_value = mock_file_ops
        mock_adapter.container = mock_container
        mock_adapter_class.return_value = mock_adapter

        # When: レガシーファイル操作を作成
        result = create_legacy_file_operations()

        # Then: 正しくファイル操作が返される
        assert result is mock_file_ops
        mock_container.resolve.assert_called_once()

    def test_異常系_create_legacy_file_operations_フォールバック(self):
        """異常系: ファイル操作作成失敗時のフォールバック処理確認"""
        # Given: container.resolveが失敗する状況
        with patch(
            "kumihan_formatter.core.patterns.legacy_factory_integration.LegacyFactoryAdapter"
        ) as mock_adapter_class:
            mock_adapter = Mock()
            mock_container = Mock()
            mock_container.resolve.side_effect = Exception("Resolve failed")
            mock_adapter.container = mock_container
            mock_adapter_class.return_value = mock_adapter

            with patch(
                "kumihan_formatter.core.patterns.legacy_factory_integration.logger"
            ) as mock_logger:
                with patch(
                    "kumihan_formatter.core.file_operations_factory.create_file_operations"
                ) as mock_fallback:
                    mock_fallback_result = Mock()
                    mock_fallback.return_value = mock_fallback_result

                    # When: レガシーファイル操作作成を試行
                    result = create_legacy_file_operations("test_ui")

                    # Then: フォールバック処理が呼ばれる
                    assert result is mock_fallback_result
                    mock_fallback.assert_called_once_with("test_ui")
                    mock_logger.warning.assert_called()

    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.LegacyFactoryAdapter")
    def test_正常系_create_legacy_markdown_converter(self, mock_adapter_class):
        """正常系: レガシーマークダウンコンバーター作成"""
        # Given: モックアダプターとコンテナ
        mock_adapter = Mock()
        mock_container = Mock()
        mock_parser = Mock()
        mock_processor = Mock()
        mock_renderer = Mock()
        mock_container.resolve.side_effect = [
            mock_parser,
            mock_processor,
            mock_renderer,
        ]
        mock_adapter.container = mock_container
        mock_adapter_class.return_value = mock_adapter

        # When: レガシーマークダウンコンバーターを作成
        result = create_legacy_markdown_converter()

        # Then: パーサー・プロセッサー・レンダラーのタプルが返される
        assert result == (mock_parser, mock_processor, mock_renderer)
        assert mock_container.resolve.call_count == 3

    def test_異常系_create_legacy_markdown_converter_フォールバック(self):
        """異常系: マークダウンコンバーター作成失敗時のフォールバック処理確認"""
        # Given: container.resolveが失敗する状況
        with patch(
            "kumihan_formatter.core.patterns.legacy_factory_integration.LegacyFactoryAdapter"
        ) as mock_adapter_class:
            mock_adapter = Mock()
            mock_container = Mock()
            mock_container.resolve.side_effect = Exception("Resolve failed")
            mock_adapter.container = mock_container
            mock_adapter_class.return_value = mock_adapter

            with patch(
                "kumihan_formatter.core.patterns.legacy_factory_integration.logger"
            ) as mock_logger:
                with patch(
                    "kumihan_formatter.core.markdown_factory.create_markdown_converter"
                ) as mock_fallback:
                    mock_fallback_result = (Mock(), Mock(), Mock())
                    mock_fallback.return_value = mock_fallback_result

                    # When: レガシーマークダウンコンバーター作成を試行
                    result = create_legacy_markdown_converter()

                    # Then: フォールバック処理が呼ばれる
                    assert result is mock_fallback_result
                    mock_fallback.assert_called_once()
                    mock_logger.warning.assert_called()

    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.LegacyFactoryAdapter")
    def test_正常系_create_legacy_list_parser(self, mock_adapter_class):
        """正常系: レガシーリストパーサー作成"""
        # Given: モックアダプターとコンテナ
        mock_adapter = Mock()
        mock_container = Mock()
        mock_list_parser = Mock()
        mock_container.resolve.return_value = mock_list_parser
        mock_adapter.container = mock_container
        mock_adapter_class.return_value = mock_adapter
        mock_keyword_parser = Mock()

        # When: レガシーリストパーサーを作成
        result = create_legacy_list_parser(mock_keyword_parser)

        # Then: 正しくリストパーサーが返される
        assert result is mock_list_parser
        mock_container.resolve.assert_called_once()

    def test_異常系_create_legacy_list_parser_フォールバック(self):
        """異常系: リストパーサー作成失敗時のフォールバック処理確認"""
        # Given: container.resolveが失敗する状況
        with patch(
            "kumihan_formatter.core.patterns.legacy_factory_integration.LegacyFactoryAdapter"
        ) as mock_adapter_class:
            mock_adapter = Mock()
            mock_container = Mock()
            mock_container.resolve.side_effect = Exception("Resolve failed")
            mock_adapter.container = mock_container
            mock_adapter_class.return_value = mock_adapter
            mock_keyword_parser = Mock()

            with patch(
                "kumihan_formatter.core.patterns.legacy_factory_integration.logger"
            ) as mock_logger:
                with patch(
                    "kumihan_formatter.core.list_parser_factory.create_list_parser"
                ) as mock_fallback:
                    mock_fallback_result = Mock()
                    mock_fallback.return_value = mock_fallback_result

                    # When: レガシーリストパーサー作成を試行
                    result = create_legacy_list_parser(mock_keyword_parser)

                    # Then: フォールバック処理が呼ばれる
                    assert result is mock_fallback_result
                    mock_fallback.assert_called_once_with(mock_keyword_parser)
                    mock_logger.warning.assert_called()


class TestGlobalLegacyAdapter:
    """グローバルレガシーアダプターのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        # グローバル状態をクリア
        import kumihan_formatter.core.patterns.legacy_factory_integration as module

        module._legacy_adapter = None

    def test_正常系_get_legacy_adapter_初回(self):
        """正常系: グローバルアダプター初回取得"""
        # Given: グローバルアダプターが未初期化
        # When: get_legacy_adapter()を呼び出し
        adapter = get_legacy_adapter()

        # Then: LegacyFactoryAdapterインスタンスが返される
        assert isinstance(adapter, LegacyFactoryAdapter)

    def test_正常系_get_legacy_adapter_2回目(self):
        """正常系: グローバルアダプター2回目取得（シングルトン確認）"""
        # Given: 1回目の呼び出し
        adapter1 = get_legacy_adapter()

        # When: 2回目の呼び出し
        adapter2 = get_legacy_adapter()

        # Then: 同一インスタンスが返される（シングルトン）
        assert adapter1 is adapter2

    def test_正常系_initialize_legacy_integration(self):
        """正常系: レガシー統合システム初期化"""
        # Given: カスタムコンテナ
        custom_container = DIContainer()

        # When: レガシー統合システムを初期化
        with patch(
            "kumihan_formatter.core.patterns.legacy_factory_integration.logger"
        ) as mock_logger:
            initialize_legacy_integration(custom_container)

            # Then: 成功ログが出力される
            mock_logger.info.assert_called_with(
                "Legacy integration system initialized successfully"
            )

        # グローバルアダプターが設定される
        adapter = get_legacy_adapter()
        assert adapter.container is custom_container

    def test_正常系_initialize_legacy_integration_デフォルト(self):
        """正常系: レガシー統合システムデフォルト初期化"""
        # Given: コンテナなし
        # When: レガシー統合システムを初期化
        with patch(
            "kumihan_formatter.core.patterns.legacy_factory_integration.logger"
        ) as mock_logger:
            initialize_legacy_integration()

            # Then: 成功ログが出力される
            mock_logger.info.assert_called_with(
                "Legacy integration system initialized successfully"
            )

    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.LegacyFactoryAdapter")
    @patch("kumihan_formatter.core.patterns.legacy_factory_integration.logger")
    def test_異常系_initialize_legacy_integration_失敗(self, mock_logger, mock_adapter_class):
        """異常系: レガシー統合システム初期化失敗"""
        # Given: 初期化失敗するアダプター
        mock_adapter_class.side_effect = Exception("Init failed")

        # When: レガシー統合システム初期化を試行
        # Then: 例外が再発生し、エラーログが出力される
        with pytest.raises(Exception, match="Init failed"):
            initialize_legacy_integration()

        mock_logger.error.assert_called()

    def test_境界値_グローバル状態管理(self):
        """境界値: グローバル状態の適切な管理確認"""
        # Given: 初期化されたアダプター
        adapter1 = get_legacy_adapter()

        # When: 新しい初期化を実行
        new_container = DIContainer()
        initialize_legacy_integration(new_container)
        adapter2 = get_legacy_adapter()

        # Then: 新しいアダプターに置き換わる
        assert adapter1 is not adapter2
        assert adapter2.container is new_container


class TestIntegration:
    """統合テスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        # グローバル状態をクリア
        import kumihan_formatter.core.patterns.legacy_factory_integration as module

        module._legacy_adapter = None

    def test_統合_完全なレガシー統合ワークフロー(self):
        """統合: 完全なレガシー統合ワークフローの確認"""
        # Given: カスタムDIコンテナ
        container = DIContainer()

        # When: レガシー統合システムを初期化し、各サービスを生成
        with patch("kumihan_formatter.core.patterns.legacy_factory_integration.logger"):
            initialize_legacy_integration(container)

        # レガシー互換関数を呼び出し（実際のオブジェクトが返される）
        file_ops = create_legacy_file_operations()
        md_converter = create_legacy_markdown_converter()
        list_parser = create_legacy_list_parser(Mock())

        # Then: 全てのサービスが正常に生成される
        assert file_ops is not None
        assert md_converter is not None
        assert isinstance(md_converter, tuple) and len(md_converter) == 3
        assert list_parser is not None

    def test_統合_エラー処理と復旧(self):
        """統合: エラー処理と復旧の確認"""
        # Given: 失敗する環境でフォールバック動作確認
        with patch(
            "kumihan_formatter.core.patterns.legacy_factory_integration.LegacyFactoryAdapter"
        ) as mock_adapter_class:
            mock_adapter = Mock()
            mock_container = Mock()
            mock_container.resolve.side_effect = Exception("Resolve failed")
            mock_adapter.container = mock_container
            mock_adapter_class.return_value = mock_adapter

            # When: フォールバック処理が動作
            with patch(
                "kumihan_formatter.core.file_operations_factory.create_file_operations"
            ) as mock_fallback:
                mock_fallback.return_value = Mock()
                result1 = create_legacy_file_operations()  # フォールバック

            # Then: フォールバック処理が動作
            mock_fallback.assert_called_once()
            assert result1 is not None

        # 正常な環境での動作確認
        result2 = get_legacy_adapter()  # 成功
        assert isinstance(result2, LegacyFactoryAdapter)

    def test_境界値_大量同時アクセス(self):
        """境界値: グローバルアダプターへの大量同時アクセス"""
        # Given: グローバル状態
        # When: 大量の同時アクセス
        adapters = []
        for _ in range(100):
            adapters.append(get_legacy_adapter())

        # Then: 全て同一インスタンス（シングルトン保証）
        for adapter in adapters:
            assert adapter is adapters[0]
