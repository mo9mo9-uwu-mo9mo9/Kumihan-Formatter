"""observers.py具体実装の包括的テスト

Issue #929 Phase 2A: Event & Observer System Tests
ParsingObserver・RenderingObserver具体実装テスト
"""

import logging
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.patterns.observer import Event, EventType, Observer
from kumihan_formatter.core.patterns.observers import ParsingObserver, RenderingObserver


class TestParsingObserver:
    """ParsingObserverのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.parsing_observer = ParsingObserver()

    def test_正常系_初期化(self):
        """正常系: パーシングオブザーバー初期化確認"""
        # Given: ParsingObserverクラス
        # When: ParsingObserverを初期化
        observer = ParsingObserver()

        # Then: 正しく初期化される
        assert hasattr(observer, "handle_event")
        assert hasattr(observer, "get_supported_events")
        assert hasattr(observer, "logger")
        assert isinstance(observer.logger, logging.Logger)

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_ロガー設定(self, mock_get_logger):
        """正常系: ロガー設定確認"""
        # Given: モックロガー
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # When: ParsingObserverを初期化
        observer = ParsingObserver()

        # Then: ロガーが適切に設定される
        mock_get_logger.assert_called_once_with(
            "kumihan_formatter.core.patterns.observers"
        )
        assert observer.logger is mock_logger

    def test_正常系_対応イベント種別取得(self):
        """正常系: get_supported_events()の確認"""
        # Given: ParsingObserver
        # When: 対応イベント種別を取得
        supported_events = self.parsing_observer.get_supported_events()

        # Then: パーシング関連の全イベント種別が返される
        expected_events = [
            EventType.PARSING_STARTED,
            EventType.PARSING_COMPLETED,
            EventType.PARSING_ERROR,
        ]
        assert supported_events == expected_events
        assert len(supported_events) == 3

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_パーシング開始イベント処理(self, mock_get_logger):
        """正常系: PARSING_STARTEDイベント処理確認"""
        # Given: モックロガーとイベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = ParsingObserver()

        event = Event(
            event_type=EventType.PARSING_STARTED,
            source="test_parser",
            data={"content_length": 1500},
        )

        # When: パーシング開始イベントを処理
        observer.handle_event(event)

        # Then: 適切なログが出力される
        mock_logger.info.assert_called_once_with("Parsing started: 1500 characters")

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_パーシング開始イベント処理_データなし(self, mock_get_logger):
        """正常系: PARSING_STARTEDイベント処理（データなし）確認"""
        # Given: モックロガーとデータなしイベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = ParsingObserver()

        event = Event(
            event_type=EventType.PARSING_STARTED,
            source="test_parser",
            data={},  # content_lengthなし
        )

        # When: パーシング開始イベントを処理
        observer.handle_event(event)

        # Then: デフォルト値でログが出力される
        mock_logger.info.assert_called_once_with("Parsing started: 0 characters")

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_パーシング完了イベント処理(self, mock_get_logger):
        """正常系: PARSING_COMPLETEDイベント処理確認"""
        # Given: モックロガーとイベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = ParsingObserver()

        event = Event(
            event_type=EventType.PARSING_COMPLETED,
            source="test_parser",
            data={"duration": 0.125},
        )

        # When: パーシング完了イベントを処理
        observer.handle_event(event)

        # Then: 適切なログが出力される
        mock_logger.info.assert_called_once_with("Parsing completed in 0.125s")

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_パーシング完了イベント処理_データなし(self, mock_get_logger):
        """正常系: PARSING_COMPLETEDイベント処理（データなし）確認"""
        # Given: モックロガーとデータなしイベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = ParsingObserver()

        event = Event(
            event_type=EventType.PARSING_COMPLETED,
            source="test_parser",
            data={},  # durationなし
        )

        # When: パーシング完了イベントを処理
        observer.handle_event(event)

        # Then: デフォルト値でログが出力される（実際は0.000sと表示）
        mock_logger.info.assert_called_once_with("Parsing completed in 0.000s")

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_パーシングエラーイベント処理(self, mock_get_logger):
        """正常系: PARSING_ERRORイベント処理確認"""
        # Given: モックロガーとエラーイベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = ParsingObserver()

        event = Event(
            event_type=EventType.PARSING_ERROR,
            source="test_parser",
            data={"error": "Invalid syntax at line 10"},
        )

        # When: パーシングエラーイベントを処理
        observer.handle_event(event)

        # Then: エラーログが出力される
        mock_logger.error.assert_called_once_with(
            "Parsing failed: Invalid syntax at line 10"
        )

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_パーシングエラーイベント処理_データなし(self, mock_get_logger):
        """正常系: PARSING_ERRORイベント処理（データなし）確認"""
        # Given: モックロガーとデータなしエラーイベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = ParsingObserver()

        event = Event(
            event_type=EventType.PARSING_ERROR,
            source="test_parser",
            data={},  # errorなし
        )

        # When: パーシングエラーイベントを処理
        observer.handle_event(event)

        # Then: デフォルトエラーメッセージでログが出力される
        mock_logger.error.assert_called_once_with("Parsing failed: Unknown error")

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_非対応イベント処理(self, mock_get_logger):
        """正常系: 非対応イベント処理確認"""
        # Given: モックロガーと非対応イベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = ParsingObserver()

        event = Event(
            event_type=EventType.RENDERING_STARTED,  # パーシングオブザーバーの非対応イベント
            source="test_renderer",
            data={"format": "html"},
        )

        # When: 非対応イベントを処理
        observer.handle_event(event)

        # Then: ログが出力されない
        mock_logger.info.assert_not_called()
        mock_logger.error.assert_not_called()


class TestRenderingObserver:
    """RenderingObserverのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.rendering_observer = RenderingObserver()

    def test_正常系_初期化(self):
        """正常系: レンダリングオブザーバー初期化確認"""
        # Given: RenderingObserverクラス
        # When: RenderingObserverを初期化
        observer = RenderingObserver()

        # Then: 正しく初期化される
        assert hasattr(observer, "handle_event")
        assert hasattr(observer, "get_supported_events")
        assert hasattr(observer, "logger")
        assert isinstance(observer.logger, logging.Logger)

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_ロガー設定(self, mock_get_logger):
        """正常系: ロガー設定確認"""
        # Given: モックロガー
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # When: RenderingObserverを初期化
        observer = RenderingObserver()

        # Then: ロガーが適切に設定される
        mock_get_logger.assert_called_once_with(
            "kumihan_formatter.core.patterns.observers"
        )
        assert observer.logger is mock_logger

    def test_正常系_対応イベント種別取得(self):
        """正常系: get_supported_events()の確認"""
        # Given: RenderingObserver
        # When: 対応イベント種別を取得
        supported_events = self.rendering_observer.get_supported_events()

        # Then: レンダリング関連の全イベント種別が返される
        expected_events = [
            EventType.RENDERING_STARTED,
            EventType.RENDERING_COMPLETED,
            EventType.RENDERING_ERROR,
        ]
        assert supported_events == expected_events
        assert len(supported_events) == 3

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_レンダリング開始イベント処理(self, mock_get_logger):
        """正常系: RENDERING_STARTEDイベント処理確認"""
        # Given: モックロガーとイベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = RenderingObserver()

        event = Event(
            event_type=EventType.RENDERING_STARTED,
            source="test_renderer",
            data={"format": "html"},
        )

        # When: レンダリング開始イベントを処理
        observer.handle_event(event)

        # Then: 適切なログが出力される
        mock_logger.info.assert_called_once_with("Rendering started: format=html")

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_レンダリング開始イベント処理_データなし(self, mock_get_logger):
        """正常系: RENDERING_STARTEDイベント処理（データなし）確認"""
        # Given: モックロガーとデータなしイベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = RenderingObserver()

        event = Event(
            event_type=EventType.RENDERING_STARTED,
            source="test_renderer",
            data={},  # formatなし
        )

        # When: レンダリング開始イベントを処理
        observer.handle_event(event)

        # Then: デフォルト値でログが出力される
        mock_logger.info.assert_called_once_with("Rendering started: format=unknown")

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_レンダリング完了イベント処理(self, mock_get_logger):
        """正常系: RENDERING_COMPLETEDイベント処理確認"""
        # Given: モックロガーとイベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = RenderingObserver()

        event = Event(
            event_type=EventType.RENDERING_COMPLETED,
            source="test_renderer",
            data={"output_size": 2048},
        )

        # When: レンダリング完了イベントを処理
        observer.handle_event(event)

        # Then: 適切なログが出力される
        mock_logger.info.assert_called_once_with("Rendering completed: 2048 bytes")

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_レンダリング完了イベント処理_データなし(self, mock_get_logger):
        """正常系: RENDERING_COMPLETEDイベント処理（データなし）確認"""
        # Given: モックロガーとデータなしイベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = RenderingObserver()

        event = Event(
            event_type=EventType.RENDERING_COMPLETED,
            source="test_renderer",
            data={},  # output_sizeなし
        )

        # When: レンダリング完了イベントを処理
        observer.handle_event(event)

        # Then: デフォルト値でログが出力される
        mock_logger.info.assert_called_once_with("Rendering completed: 0 bytes")

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_レンダリングエラーイベント処理(self, mock_get_logger):
        """正常系: RENDERING_ERRORイベント処理確認"""
        # Given: モックロガーとエラーイベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = RenderingObserver()

        event = Event(
            event_type=EventType.RENDERING_ERROR,
            source="test_renderer",
            data={"error": "Template not found: main.html"},
        )

        # When: レンダリングエラーイベントを処理
        observer.handle_event(event)

        # Then: エラーログが出力される
        mock_logger.error.assert_called_once_with(
            "Rendering failed: Template not found: main.html"
        )

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_レンダリングエラーイベント処理_データなし(self, mock_get_logger):
        """正常系: RENDERING_ERRORイベント処理（データなし）確認"""
        # Given: モックロガーとデータなしエラーイベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = RenderingObserver()

        event = Event(
            event_type=EventType.RENDERING_ERROR,
            source="test_renderer",
            data={},  # errorなし
        )

        # When: レンダリングエラーイベントを処理
        observer.handle_event(event)

        # Then: デフォルトエラーメッセージでログが出力される
        mock_logger.error.assert_called_once_with("Rendering failed: Unknown error")

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_正常系_非対応イベント処理(self, mock_get_logger):
        """正常系: 非対応イベント処理確認"""
        # Given: モックロガーと非対応イベント
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        observer = RenderingObserver()

        event = Event(
            event_type=EventType.PARSING_STARTED,  # レンダリングオブザーバーの非対応イベント
            source="test_parser",
            data={"content_length": 100},
        )

        # When: 非対応イベントを処理
        observer.handle_event(event)

        # Then: ログが出力されない
        mock_logger.info.assert_not_called()
        mock_logger.error.assert_not_called()


class TestObserversIntegration:
    """オブザーバー統合テスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.parsing_observer = ParsingObserver()
        self.rendering_observer = RenderingObserver()

    def test_統合_複数オブザーバー連携(self):
        """統合: 複数オブザーバーの連携動作確認"""
        # Given: 複数のオブザーバー
        parsing_observer = ParsingObserver()
        rendering_observer = RenderingObserver()

        # Then: 各オブザーバーが独立して動作する
        assert hasattr(parsing_observer, "handle_event")
        assert hasattr(rendering_observer, "handle_event")

        # 対応イベント種別が異なる
        parsing_events = set(parsing_observer.get_supported_events())
        rendering_events = set(rendering_observer.get_supported_events())
        assert parsing_events.isdisjoint(rendering_events)  # 重複なし

    @patch("kumihan_formatter.core.patterns.observers.logging.getLogger")
    def test_統合_ログ出力確認(self, mock_get_logger):
        """統合: 各種ログ出力の確認"""
        # Given: 統一されたモックロガー
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # 両方のオブザーバーを初期化
        parsing_observer = ParsingObserver()
        rendering_observer = RenderingObserver()

        # When: 各種イベントを処理
        parsing_event = Event(
            event_type=EventType.PARSING_STARTED,
            source="parser",
            data={"content_length": 500},
        )
        rendering_event = Event(
            event_type=EventType.RENDERING_COMPLETED,
            source="renderer",
            data={"output_size": 1024},
        )

        parsing_observer.handle_event(parsing_event)
        rendering_observer.handle_event(rendering_event)

        # Then: 両方のログが出力される
        expected_calls = [
            (("Parsing started: 500 characters",), {}),
            (("Rendering completed: 1024 bytes",), {}),
        ]
        # ログ呼び出しの確認
        call_args_list = [call.args[0] for call in mock_logger.info.call_args_list]
        assert "Parsing started: 500 characters" in call_args_list
        assert "Rendering completed: 1024 bytes" in call_args_list
        assert mock_logger.info.call_count == 2

    def test_統合_Observerプロトコル準拠(self):
        """統合: Observer protocolの正確な実装確認"""
        # Given: 具体的なオブザーバー実装
        observers = [ParsingObserver(), RenderingObserver()]

        # Then: 全てのオブザーバーがObserverプロトコルを満たす
        for observer in observers:
            # 必要なメソッドが存在する
            assert hasattr(observer, "handle_event")
            assert hasattr(observer, "get_supported_events")
            assert callable(observer.handle_event)
            assert callable(observer.get_supported_events)

            # get_supported_events()がEventTypeのリストを返す
            supported_events = observer.get_supported_events()
            assert isinstance(supported_events, list)
            for event_type in supported_events:
                assert isinstance(event_type, EventType)

    def test_境界値_大量イベント処理(self):
        """境界値: 大量イベントの処理性能確認"""
        with patch(
            "kumihan_formatter.core.patterns.observers.logging.getLogger"
        ) as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            parsing_observer = ParsingObserver()
            rendering_observer = RenderingObserver()

            # When: 大量のイベントを処理
            for i in range(100):
                parsing_event = Event(
                    event_type=EventType.PARSING_STARTED,
                    source=f"parser_{i}",
                    data={"content_length": i},
                )
                rendering_event = Event(
                    event_type=EventType.RENDERING_COMPLETED,
                    source=f"renderer_{i}",
                    data={"output_size": i * 10},
                )

                parsing_observer.handle_event(parsing_event)
                rendering_observer.handle_event(rendering_event)

            # Then: 全てのイベントが処理される
            assert mock_logger.info.call_count == 200  # 100 * 2種類

    def test_異常系_例外イベントデータ(self):
        """異常系: 異常なイベントデータの処理確認"""
        with patch(
            "kumihan_formatter.core.patterns.observers.logging.getLogger"
        ) as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            parsing_observer = ParsingObserver()

            # Given: 異常なデータ型のイベント
            abnormal_events = [
                Event(
                    event_type=EventType.PARSING_STARTED,
                    source="test",
                    data={"content_length": "invalid_string"},  # 数値でない
                ),
                Event(
                    event_type=EventType.PARSING_COMPLETED,
                    source="test",
                    data={"duration": None},  # None値
                ),
                Event(
                    event_type=EventType.PARSING_ERROR,
                    source="test",
                    data={"error": 12345},  # 文字列でない
                ),
            ]

            # When: 異常なイベントを処理
            for event in abnormal_events:
                # Then: フォーマットエラーは発生しうるがプログラムは継続
                try:
                    parsing_observer.handle_event(event)
                except (TypeError, ValueError, AttributeError):
                    # フォーマットエラーは予期される
                    pass
                except Exception as e:
                    pytest.fail(f"Unexpected exception raised: {e}")

            # ログが出力される（フォーマットエラーで出力されない場合もある）
            # 少なくとも1回は何らかのログメソッドが呼ばれることを確認
            total_calls = (
                mock_logger.info.call_count +
                mock_logger.error.call_count +
                mock_logger.warning.call_count +
                mock_logger.debug.call_count
            )
            assert total_calls >= 1  # 何らかのログが出力される
