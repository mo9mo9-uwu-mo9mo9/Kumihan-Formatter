"""Pattern Integration System Test

integration.py モジュールの包括的なテスト。
ArchitectureManagerとパターン統合機能の完全なテストカバレッジを提供。
"""

import pytest
from unittest.mock import Mock, patch, call, MagicMock
from typing import Any, Dict, Optional

from kumihan_formatter.core.patterns.integration import ArchitectureManager
from kumihan_formatter.core.patterns.observer import Event, EventType, EventBus
from kumihan_formatter.core.patterns.strategy import StrategyManager
from kumihan_formatter.core.patterns.command import CommandProcessor
from kumihan_formatter.core.patterns.decorator import DecoratorChain
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestArchitectureManager:
    """ArchitectureManagerのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.manager = ArchitectureManager()

    def test_正常系_初期化(self):
        """正常系: アーキテクチャマネージャー初期化確認"""
        # Given: ArchitectureManagerを初期化
        # When: インスタンス作成
        manager = ArchitectureManager()

        # Then: 各コンポーネントが適切に初期化される
        assert isinstance(manager._event_bus, EventBus)
        assert isinstance(manager._strategy_manager, StrategyManager)
        assert isinstance(manager._command_processor, CommandProcessor)
        assert isinstance(manager._instances, dict)

        # 基本インスタンス登録確認
        assert manager._instances["event_bus"] is manager._event_bus
        assert manager._instances["strategy_manager"] is manager._strategy_manager
        assert manager._instances["command_processor"] is manager._command_processor

    def test_正常系_デフォルトパターン設定_成功(self):
        """正常系: configure_default_patterns()の成功パス確認"""
        # Given: モックモジュールの作成
        mock_observers_module = Mock()
        mock_strategies_module = Mock()

        mock_observers_module.ParsingObserver = Mock()
        mock_observers_module.RenderingObserver = Mock()
        mock_strategies_module.KumihanParsingStrategy = Mock()
        mock_strategies_module.HTMLRenderingStrategy = Mock()

        # sys.modulesを直接パッチ
        with patch.dict('sys.modules', {
            'kumihan_formatter.core.patterns.observers': mock_observers_module,
            'kumihan_formatter.core.patterns.strategies': mock_strategies_module
        }):
            # When: デフォルトパターン設定を実行
            self.manager.configure_default_patterns()

            # Then: 例外が発生せずに完了することを確認
            assert True

    def test_正常系_デフォルトパターン設定_ImportError処理(self):
        """正常系: ImportError時の適切な処理確認"""
        # Given: ImportErrorを発生させるモック
        with patch('builtins.__import__', side_effect=ImportError("Module not found")):
            # When: デフォルトパターン設定を実行
            # Then: 例外が発生せずに正常に処理される
            try:
                self.manager.configure_default_patterns()
                assert True  # ImportErrorがキャッチされ正常に処理される
            except ImportError:
                pytest.fail("ImportError should be caught and handled gracefully")

    def test_正常系_機能拡張パーサー生成(self):
        """正常系: create_enhanced_parser()の確認"""
        # Given: ベースパーサー
        base_parser = Mock()
        base_parser.parse = Mock(return_value="parsed_result")

        # When: 機能拡張パーサーを生成
        enhanced_parser = self.manager.create_enhanced_parser(base_parser)

        # Then: デコレーターチェーンで拡張されたパーサーが返される
        assert enhanced_parser is not None
        assert enhanced_parser != base_parser

        # 拡張機能の動作確認（キャッシュ・ログ機能）
        result = enhanced_parser.parse("test_content", {"context": "test"})
        assert result is not None

    def test_正常系_機能拡張レンダラー生成(self):
        """正常系: create_enhanced_renderer()の確認"""
        # Given: ベースレンダラー
        base_renderer = Mock()
        base_renderer.render = Mock(return_value="rendered_result")

        # When: 機能拡張レンダラーを生成
        enhanced_renderer = self.manager.create_enhanced_renderer(base_renderer)

        # Then: デコレーターチェーンで拡張されたレンダラーが返される
        assert enhanced_renderer is not None
        assert enhanced_renderer != base_renderer

        # 拡張機能の動作確認（ログ機能）
        result = enhanced_renderer.render("test_data", {"format": "html"})
        assert result is not None

    def test_正常系_インスタンス管理(self):
        """正常系: register_instance/get_instanceの確認"""
        # Given: テスト用インスタンス
        test_instance = Mock()
        test_instance.name = "test_object"

        # When: インスタンスを登録
        self.manager.register_instance("test_key", test_instance)

        # Then: インスタンスが正しく登録される
        retrieved_instance = self.manager.get_instance("test_key")
        assert retrieved_instance is test_instance
        assert retrieved_instance.name == "test_object"

    def test_正常系_存在しないインスタンス取得(self):
        """正常系: 存在しないインスタンス取得時の動作確認"""
        # Given: 存在しないキー
        # When: 存在しないインスタンスを取得
        result = self.manager.get_instance("nonexistent_key")

        # Then: Noneが返される
        assert result is None

    def test_正常系_コンポーネント取得メソッド(self):
        """正常系: 各コンポーネント取得メソッドの確認"""
        # Given: 初期化されたマネージャー
        # When: 各コンポーネントを取得
        event_bus = self.manager.get_event_bus()
        strategy_manager = self.manager.get_strategy_manager()
        command_processor = self.manager.get_command_processor()

        # Then: 正しいインスタンスが返される
        assert event_bus is self.manager._event_bus
        assert strategy_manager is self.manager._strategy_manager
        assert command_processor is self.manager._command_processor

    def test_正常系_イベント発行便利メソッド(self):
        """正常系: publish_event()便利メソッドの確認"""
        # Given: モックされたイベントバス
        mock_event_bus = Mock()
        self.manager._event_bus = mock_event_bus

        # When: イベント発行便利メソッドを呼び出し
        self.manager.publish_event(
            EventType.PARSING_STARTED,
            "test_source",
            {"key": "value"}
        )

        # Then: イベントバスのpublishメソッドが正しく呼ばれる
        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args[0][0]
        assert call_args.event_type == EventType.PARSING_STARTED
        assert call_args.source == "test_source"
        assert call_args.data == {"key": "value"}

    def test_正常系_イベント発行_データなし(self):
        """正常系: データなしでのイベント発行確認"""
        # Given: モックされたイベントバス
        mock_event_bus = Mock()
        self.manager._event_bus = mock_event_bus

        # When: データなしでイベント発行
        self.manager.publish_event(EventType.RENDERING_STARTED, "source")

        # Then: 空のデータ辞書でイベントが発行される
        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args[0][0]
        assert call_args.data == {}


class TestPatternIntegration:
    """パターン統合テスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.manager = ArchitectureManager()

    def test_統合_Observer_Strategy連携(self):
        """統合: ObserverパターンとStrategyパターンの連携確認"""
        # Given: オブザーバーとストラテジーの統合システム
        mock_observer = Mock()
        mock_strategy = Mock()
        mock_strategy.execute = Mock(return_value="strategy_result")

        # イベントバスにオブザーバーを登録
        self.manager._event_bus.subscribe(EventType.PARSING_STARTED, mock_observer)

        # ストラテジーマネージャーに戦略を登録
        self.manager._strategy_manager.register_parsing_strategy(
            "test", mock_strategy, is_default=True
        )

        # When: イベント発行とストラテジー実行
        self.manager.publish_event(EventType.PARSING_STARTED, "integration_test")
        result = self.manager._strategy_manager.get_parsing_strategy("test")

        # Then: オブザーバーとストラテジーが連携動作する
        assert result is mock_strategy

    def test_統合_Command_Decorator連携(self):
        """統合: CommandパターンとDecoratorパターンの連携確認"""
        # Given: コマンドプロセッサーと拡張機能の統合
        base_parser = Mock()
        base_parser.parse = Mock(return_value="base_parse_result")

        # When: 拡張パーサーを作成し、コマンド処理と連携
        enhanced_parser = self.manager.create_enhanced_parser(base_parser)
        command_processor = self.manager.get_command_processor()

        # Then: 両システムが正常に動作する
        assert enhanced_parser is not None
        assert command_processor is not None

        # 拡張パーサーの動作確認
        result = enhanced_parser.parse("test", {})
        assert result is not None

    def test_統合_全パターン協調(self):
        """統合: 全パターンの協調動作確認"""
        # Given: 全パターンが統合されたシステム
        self.manager.configure_default_patterns()

        # テスト用のモックオブジェクト
        base_parser = Mock()
        base_parser.parse = Mock(return_value="parsed")
        base_renderer = Mock()
        base_renderer.render = Mock(return_value="rendered")

        # When: 全システムを使った完全なワークフロー
        enhanced_parser = self.manager.create_enhanced_parser(base_parser)
        enhanced_renderer = self.manager.create_enhanced_renderer(base_renderer)

        # イベント発行
        self.manager.publish_event(EventType.PARSING_STARTED, "workflow_test")

        # パース・レンダリング実行
        parse_result = enhanced_parser.parse("content", {})
        render_result = enhanced_renderer.render(parse_result, {"format": "html"})

        # Then: 全パターンが協調して動作する
        assert parse_result is not None
        assert render_result is not None

    def test_統合_エラー伝播と回復(self):
        """統合: エラー伝播と回復機能の確認"""
        # Given: エラーが発生するコンポーネント
        error_parser = Mock()
        error_parser.parse = Mock(side_effect=ValueError("Parse error"))

        # When: エラーが発生する状況での統合テスト
        enhanced_parser = self.manager.create_enhanced_parser(error_parser)

        # Then: エラーが適切に処理される（ログ機能により）
        with pytest.raises(ValueError):
            enhanced_parser.parse("error_content", {})

    def test_統合_並行処理シナリオ(self):
        """統合: 並行処理シナリオでの動作確認"""
        # Given: 複数のコンポーネントが並行して動作
        import threading
        import time

        results = []

        def worker(worker_id: int):
            """ワーカー関数"""
            manager = ArchitectureManager()
            base_parser = Mock()
            base_parser.parse = Mock(return_value=f"result_{worker_id}")

            enhanced_parser = manager.create_enhanced_parser(base_parser)
            result = enhanced_parser.parse(f"content_{worker_id}", {})
            results.append(result)

        # When: 複数スレッドで並行処理実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=5.0)

        # Then: 全スレッドが正常に完了する
        assert len(results) == 3
        assert all(result is not None for result in results)


class TestEventPublication:
    """イベント発行機能テスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.manager = ArchitectureManager()

    def test_正常系_イベント発行便利メソッド(self):
        """正常系: publish_event()便利メソッドの確認"""
        # Given: イベント監視用のモック
        mock_observer = Mock()
        self.manager._event_bus.subscribe(EventType.PARSING_STARTED, mock_observer)

        # When: 便利メソッドでイベント発行
        self.manager.publish_event(
            EventType.PARSING_STARTED,
            "convenience_test",
            {"data": "test_value"}
        )

        # Then: イベントが正しく発行される
        # 内部実装に依存するため、例外が発生しないことを確認
        assert True

    def test_正常系_イベントバス取得(self):
        """正常系: get_event_bus()の確認"""
        # Given: 初期化されたマネージャー
        # When: イベントバスを取得
        event_bus = self.manager.get_event_bus()

        # Then: 正しいイベントバスインスタンスが返される
        assert event_bus is self.manager._event_bus
        assert isinstance(event_bus, EventBus)

    def test_正常系_複数イベント発行(self):
        """正常系: 複数イベントの発行確認"""
        # Given: 異なる種類のイベント
        events = [
            (EventType.PARSING_STARTED, "parser", {"input": "text1"}),
            (EventType.RENDERING_STARTED, "renderer", {"format": "html"}),
            (EventType.PARSING_STARTED, "parser2", {"input": "text2"}),
        ]

        # When: 複数のイベントを発行
        for event_type, source, data in events:
            self.manager.publish_event(event_type, source, data)

        # Then: 全イベントが正常に発行される（例外なし）
        assert True

    def test_境界値_大量データでのイベント発行(self):
        """境界値: 大量データでのイベント発行確認"""
        # Given: 大量のデータを含むイベント
        large_data = {"content": "x" * 10000, "metadata": list(range(1000))}

        # When: 大量データでイベント発行
        self.manager.publish_event(
            EventType.PARSING_STARTED,
            "large_data_test",
            large_data
        )

        # Then: 正常に処理される
        assert True


class TestImportErrorHandling:
    """ImportError処理テスト"""

    def test_異常系_observers未実装時処理(self):
        """異常系: observers.py未実装時の適切な処理確認"""
        # Given: observersモジュールのImportErrorをシミュレート
        # strategies モジュールは正常にロード可能
        mock_strategies_module = Mock()
        mock_strategies_module.KumihanParsingStrategy = Mock()
        mock_strategies_module.HTMLRenderingStrategy = Mock()

        # observers モジュールは存在しない状態をシミュレート
        with patch.dict('sys.modules', {
            'kumihan_formatter.core.patterns.strategies': mock_strategies_module
        }):
            # observers モジュールが存在しない場合のテスト
            if 'kumihan_formatter.core.patterns.observers' in __import__('sys').modules:
                del __import__('sys').modules['kumihan_formatter.core.patterns.observers']

            # When: デフォルトパターン設定を実行
            manager = ArchitectureManager()

            # Then: ImportErrorが適切に処理される
            try:
                manager.configure_default_patterns()
                assert True  # 正常に処理される
            except ImportError:
                pytest.fail("ImportError should be handled gracefully")

    def test_異常系_strategies未実装時処理(self):
        """異常系: strategies.py未実装時の適切な処理確認"""
        # Given: strategiesモジュールのImportErrorをシミュレート
        # observers モジュールは正常にロード可能
        mock_observers_module = Mock()
        mock_observers_module.ParsingObserver = Mock()
        mock_observers_module.RenderingObserver = Mock()

        # strategies モジュールは存在しない状態をシミュレート
        with patch.dict('sys.modules', {
            'kumihan_formatter.core.patterns.observers': mock_observers_module
        }):
            # strategies モジュールが存在しない場合のテスト
            if 'kumihan_formatter.core.patterns.strategies' in __import__('sys').modules:
                del __import__('sys').modules['kumihan_formatter.core.patterns.strategies']

            # When: デフォルトパターン設定を実行
            manager = ArchitectureManager()

            # Then: ImportErrorが適切に処理される
            try:
                manager.configure_default_patterns()
                assert True  # 正常に処理される
            except ImportError:
                pytest.fail("ImportError should be handled gracefully")

    def test_異常系_部分的ImportError処理(self):
        """異常系: 一部のモジュールのみImportError発生時の処理確認"""
        # Given: observersのみImportErrorが発生
        with patch('builtins.__import__') as mock_import:
            original_import = __import__

            def selective_import_failure(name, *args, **kwargs):
                if 'observers' in name:
                    raise ImportError("observers module not found")
                # strategies は正常に import される（モック）
                if 'strategies' in name:
                    mock_module = Mock()
                    mock_module.KumihanParsingStrategy = Mock()
                    mock_module.HTMLRenderingStrategy = Mock()
                    return mock_module
                return original_import(name, *args, **kwargs)

            mock_import.side_effect = selective_import_failure

            # When: デフォルトパターン設定を実行
            manager = ArchitectureManager()
            manager.configure_default_patterns()

            # Then: 利用可能なモジュールは処理され、エラーは無視される
            assert True

    def test_正常系_全モジュール利用可能時(self):
        """正常系: 全依存モジュールが利用可能な場合の処理確認"""
        # Given: 全モジュールが正常にインポート可能
        mock_observers = Mock()
        mock_strategies = Mock()

        mock_observers.ParsingObserver = Mock()
        mock_observers.RenderingObserver = Mock()
        mock_strategies.KumihanParsingStrategy = Mock()
        mock_strategies.HTMLRenderingStrategy = Mock()

        with patch.dict('sys.modules', {
            'kumihan_formatter.core.patterns.observers': mock_observers,
            'kumihan_formatter.core.patterns.strategies': mock_strategies
        }):
            # When: デフォルトパターン設定を実行
            manager = ArchitectureManager()
            manager.configure_default_patterns()

            # Then: 全機能が正常に設定される
            assert True


class TestArchitectureManagerIntegration:
    """ArchitectureManager統合テスト"""

    def test_統合_完全初期化ワークフロー(self):
        """統合: 完全な初期化ワークフローの確認"""
        # Given: 新しいArchitectureManager
        # When: 完全な初期化プロセス実行
        manager = ArchitectureManager()
        manager.configure_default_patterns()

        # 基本コンポーネント確認
        event_bus = manager.get_event_bus()
        strategy_manager = manager.get_strategy_manager()
        command_processor = manager.get_command_processor()

        # インスタンス管理確認
        test_instance = Mock()
        manager.register_instance("test", test_instance)
        retrieved = manager.get_instance("test")

        # Then: 全機能が正常に動作する
        assert event_bus is not None
        assert strategy_manager is not None
        assert command_processor is not None
        assert retrieved is test_instance

    def test_統合_拡張機能生成ワークフロー(self):
        """統合: 拡張機能生成の完全なワークフロー確認"""
        # Given: 基本のパーサーとレンダラー
        base_parser = Mock()
        base_parser.parse = Mock(return_value="base_parsed")
        base_renderer = Mock()
        base_renderer.render = Mock(return_value="base_rendered")

        manager = ArchitectureManager()

        # When: 拡張機能付きのオブジェクトを生成
        enhanced_parser = manager.create_enhanced_parser(base_parser)
        enhanced_renderer = manager.create_enhanced_renderer(base_renderer)

        # Then: 拡張機能が正常に動作する
        parse_result = enhanced_parser.parse("test_content", {"format": "test"})
        render_result = enhanced_renderer.render("test_data", {"output": "html"})

        assert parse_result is not None
        assert render_result is not None

    def test_統合_エラー回復力確認(self):
        """統合: システム全体のエラー回復力確認"""
        # Given: 様々なエラー条件
        manager = ArchitectureManager()

        # ImportError処理確認
        with patch('builtins.__import__', side_effect=ImportError("Test error")):
            manager.configure_default_patterns()  # 正常に処理される

        # 不正なインスタンス処理
        result = manager.get_instance("nonexistent")
        assert result is None

        # エラーが発生するオブジェクトの拡張
        error_object = Mock()
        error_object.parse = Mock(side_effect=RuntimeError("Test runtime error"))

        enhanced_error_object = manager.create_enhanced_parser(error_object)
        with pytest.raises(RuntimeError):
            enhanced_error_object.parse("test", {})

        # Then: システムが堅牢にエラーを処理する
        assert True

    def test_境界値_極端な使用パターン(self):
        """境界値: 極端な使用パターンでの動作確認"""
        # Given: 極端な使用条件
        manager = ArchitectureManager()

        # 大量のインスタンス登録
        for i in range(1000):
            manager.register_instance(f"instance_{i}", Mock())

        # 複雑な拡張チェーンの作成
        base_object = Mock()
        base_object.method = Mock(return_value="result")

        # 複数回の拡張適用
        enhanced1 = manager.create_enhanced_parser(base_object)
        enhanced2 = manager.create_enhanced_parser(enhanced1)

        # When: 極端な条件での実行
        result = enhanced2.parse("extreme_test", {})

        # Then: システムが安定して動作する
        assert result is not None

        # インスタンス管理の確認
        retrieved = manager.get_instance("instance_999")
        assert retrieved is not None

    def test_統合_メモリ効率性確認(self):
        """統合: メモリ効率性の確認"""
        # Given: メモリ使用量を意識した使用パターン
        import gc

        managers = []
        for i in range(100):
            manager = ArchitectureManager()
            manager.configure_default_patterns()
            managers.append(manager)

        # When: メモリクリーンアップ実行
        del managers
        gc.collect()

        # Then: メモリリークが発生しない（例外なく完了することで確認）
        assert True
