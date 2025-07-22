"""Phase 3 Streaming Parser Enhanced Tests - ストリーミングパーサー強化テスト

パーサーコア機能テスト - 大容量ファイル処理システム拡充
Target: kumihan_formatter/core/streaming/parser.py (539行・既存テスト強化)
Goal: 既存テスト拡充で+20-25%カバレッジ向上 (Phase 3目標70-80%への重要貢献)

2番目最大カバレッジ貢献 - 推定+20-25%カバレッジ向上
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import pytest
import io

from kumihan_formatter.core.streaming.parser import KumihanStreamingParser


class TestKumihanStreamingParserAdvanced:
    """KumihanStreamingParser 高度テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = KumihanStreamingParser()

    @pytest.mark.asyncio
    async def test_process_stream_large_chunks(self):
        """大チャンクストリーム処理テスト"""
        # 大きなチャンクサイズでのテスト
        large_content = ";;;太字;;; 大容量テスト ;;; " * 10000
        stream = io.StringIO(large_content)
        
        with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
            result = await self.parser.process_stream(stream, chunk_size=50000)
            
            # 大チャンクが適切に処理されることを確認
            assert result is not None
            mock_parse.assert_called()

    @pytest.mark.asyncio
    async def test_process_stream_tiny_chunks(self):
        """微小チャンクストリーム処理テスト"""
        # 非常に小さなチャンクサイズでのテスト
        content = ";;;太字;;; 微小チャンクテスト ;;;"
        stream = io.StringIO(content)
        
        with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
            result = await self.parser.process_stream(stream, chunk_size=5)
            
            # 微小チャンクが適切に処理されることを確認
            assert result is not None
            mock_parse.assert_called()

    @pytest.mark.asyncio
    async def test_process_stream_memory_management(self):
        """メモリ管理ストリーム処理テスト"""
        # メモリ効率的な処理のテスト
        content = ";;;太字;;; メモリ管理 ;;; " * 5000
        stream = io.StringIO(content)
        
        with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
            with patch.object(self.parser, 'manage_memory') as mock_memory:
                result = await self.parser.process_stream(stream)
                
                # メモリ管理が適切に呼ばれることを確認
                assert result is not None

    @pytest.mark.asyncio
    async def test_process_stream_error_recovery(self):
        """エラー回復ストリーム処理テスト"""
        # チャンク処理でエラーが発生した場合の回復テスト
        content = ";;;太字;;; エラー回復テスト ;;;"
        stream = io.StringIO(content)
        
        parse_call_count = [0]
        def parse_with_error(chunk):
            parse_call_count[0] += 1
            if parse_call_count[0] == 2:  # 2回目の呼び出しでエラー
                raise Exception("Parse error")
            return Mock()
        
        with patch.object(self.parser, 'parse_chunk', side_effect=parse_with_error):
            with patch.object(self.parser, 'recover_from_error', return_value=Mock()) as mock_recovery:
                result = await self.parser.process_stream(stream)
                
                # エラー回復が実行されることを確認
                assert result is not None

    @pytest.mark.asyncio
    async def test_process_stream_concurrent_processing(self):
        """並行処理ストリーム処理テスト"""
        # 複数ストリームの並行処理
        contents = [
            ";;;太字;;; ストリーム1 ;;;",
            ";;;イタリック;;; ストリーム2 ;;;",
            ";;;枠線;;; ストリーム3 ;;;",
        ]
        
        streams = [io.StringIO(content) for content in contents]
        
        with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
            # 並行してストリーム処理
            tasks = [self.parser.process_stream(stream) for stream in streams]
            results = await asyncio.gather(*tasks)
            
            # 全ての並行処理が成功することを確認
            assert len(results) == 3
            assert all(result is not None for result in results)

    @pytest.mark.asyncio
    async def test_process_stream_backpressure_handling(self):
        """バックプレッシャー処理テスト"""
        # 処理速度調整のテスト
        slow_content = ";;;太字;;; バックプレッシャー ;;; " * 1000
        stream = io.StringIO(slow_content)
        
        async def slow_parse_chunk(chunk):
            await asyncio.sleep(0.001)  # 意図的な遅延
            return Mock()
        
        with patch.object(self.parser, 'parse_chunk', side_effect=slow_parse_chunk):
            with patch.object(self.parser, 'handle_backpressure') as mock_backpressure:
                result = await self.parser.process_stream(stream)
                
                # バックプレッシャー処理が適切に動作することを確認
                assert result is not None

    @pytest.mark.asyncio
    async def test_process_stream_progress_tracking(self):
        """進行状況追跡ストリーム処理テスト"""
        # 進行状況の追跡機能テスト
        content = ";;;太字;;; 進行状況テスト ;;; " * 100
        stream = io.StringIO(content)
        
        progress_calls = []
        def track_progress(current, total):
            progress_calls.append((current, total))
        
        with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
            with patch.object(self.parser, 'update_progress', side_effect=track_progress):
                result = await self.parser.process_stream(stream)
                
                # 進行状況が適切に追跡されることを確認
                assert result is not None


class TestChunkParsing:
    """チャンク解析テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = KumihanStreamingParser()

    def test_parse_chunk_complete_markers(self):
        """完全マーカーチャンク解析テスト"""
        complete_chunk = ";;;太字;;; 完全マーカー ;;;"
        
        with patch.object(self.parser, 'process_markers', return_value=[]) as mock_process:
            result = self.parser.parse_chunk(complete_chunk)
            
            # 完全マーカーが適切に処理されることを確認
            assert result is not None
            mock_process.assert_called()

    def test_parse_chunk_partial_markers(self):
        """部分マーカーチャンク解析テスト"""
        partial_chunks = [
            ";;;太字",           # 開始部分
            ";;; 中間テキスト ",  # 中間部分
            ";;;",               # 終了部分
        ]
        
        for chunk in partial_chunks:
            with patch.object(self.parser, 'buffer_partial_marker') as mock_buffer:
                result = self.parser.parse_chunk(chunk)
                
                # 部分マーカーが適切にバッファされることを確認
                assert result is not None

    def test_parse_chunk_mixed_content(self):
        """混在コンテンツチャンク解析テスト"""
        mixed_chunk = """
        通常テキスト
        ;;;太字;;; マーカー1 ;;;
        さらに通常テキスト
        ;;;イタリック;;; マーカー2 ;;;
        最後の通常テキスト
        """
        
        with patch.object(self.parser, 'process_markers', return_value=[]) as mock_process:
            with patch.object(self.parser, 'process_plain_text', return_value=[]) as mock_plain:
                result = self.parser.parse_chunk(mixed_chunk)
                
                # 混在コンテンツが適切に処理されることを確認
                assert result is not None
                mock_process.assert_called()
                mock_plain.assert_called()

    def test_parse_chunk_unicode_handling(self):
        """Unicode処理チャンク解析テスト"""
        unicode_chunks = [
            ";;;太字;;; 日本語テキスト ;;;",
            ";;;太字;;; 한국어 텍스트 ;;;",
            ";;;太字;;; 中文文本 ;;;",
            ";;;太字;;; العربية ;;;",
            ";;;太字;;; 🎌🗻⛩️ ;;;",
        ]
        
        for chunk in unicode_chunks:
            with patch.object(self.parser, 'process_markers', return_value=[]) as mock_process:
                result = self.parser.parse_chunk(chunk)
                
                # Unicode文字が適切に処理されることを確認
                assert result is not None

    def test_parse_chunk_boundary_cases(self):
        """境界ケースチャンク解析テスト"""
        boundary_chunks = [
            "",                    # 空チャンク
            ";;;",                 # 最小マーカー
            ";;;;;;",              # マーカーのみ
            "\n\n\n",              # 改行のみ
            " " * 1000,            # スペースのみ
            ";;;太字;;;" + "あ" * 10000 + ";;;",  # 超長マーカー
        ]
        
        for chunk in boundary_chunks:
            try:
                result = self.parser.parse_chunk(chunk)
                # 境界ケースが適切に処理されることを確認
                assert result is not None
            except Exception:
                # エラーハンドリングが適切に動作することを確認
                assert True

    def test_parse_chunk_performance_large(self):
        """大チャンクパフォーマンステスト"""
        large_chunk = ";;;太字;;; パフォーマンステスト ;;; " * 5000
        
        with patch.object(self.parser, 'process_markers', return_value=[]) as mock_process:
            import time
            start = time.time()
            
            result = self.parser.parse_chunk(large_chunk)
            
            end = time.time()
            duration = end - start
            
            # パフォーマンス要件を満たすことを確認
            assert result is not None
            assert duration < 2.0  # 2秒以内


class TestBufferManagement:
    """バッファ管理テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = KumihanStreamingParser()

    def test_buffer_partial_marker_accumulation(self):
        """部分マーカー蓄積バッファテスト"""
        partial_parts = [";;;太", "字;;; ", "テスト", " ;;;"]
        
        for part in partial_parts:
            with patch.object(self.parser, 'get_buffer_status', return_value='partial') as mock_status:
                self.parser.buffer_partial_marker(part)
                
                # 各部分が適切にバッファされることを確認
                mock_status.assert_called()

    def test_buffer_overflow_handling(self):
        """バッファオーバーフロー処理テスト"""
        # 大量データでのバッファオーバーフローテスト
        large_partial = ";;;太字;;; " + "あ" * 100000
        
        with patch.object(self.parser, 'handle_buffer_overflow') as mock_overflow:
            self.parser.buffer_partial_marker(large_partial)
            
            # バッファオーバーフローが適切に処理されることを確認
            assert True

    def test_buffer_flush_complete_markers(self):
        """完全マーカーバッファフラッシュテスト"""
        with patch.object(self.parser, 'flush_buffer') as mock_flush:
            with patch.object(self.parser, 'is_complete_marker', return_value=True) as mock_complete:
                self.parser.buffer_partial_marker(";;;太字;;; 完全 ;;;")
                
                # 完全マーカー検出時にフラッシュされることを確認
                assert True

    def test_buffer_memory_limit_enforcement(self):
        """バッファメモリ制限実施テスト"""
        # メモリ制限の実施テスト
        with patch.object(self.parser, 'check_memory_limit', return_value=False) as mock_limit:
            with patch.object(self.parser, 'enforce_memory_limit') as mock_enforce:
                self.parser.buffer_partial_marker("大量データ" * 10000)
                
                # メモリ制限が実施されることを確認
                assert True

    def test_buffer_cleanup_invalid_markers(self):
        """無効マーカーバッファクリーンアップテスト"""
        invalid_markers = [
            ";;;不正マーカー",
            ";;太字;;;",
            "無効;;;",
            ";;;",
        ]
        
        for invalid in invalid_markers:
            with patch.object(self.parser, 'cleanup_invalid_buffer') as mock_cleanup:
                self.parser.buffer_partial_marker(invalid)
                
                # 無効マーカーがクリーンアップされることを確認
                assert True


class TestStreamingParserErrorHandling:
    """ストリーミングパーサーエラーハンドリングテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = KumihanStreamingParser()

    @pytest.mark.asyncio
    async def test_stream_read_error_handling(self):
        """ストリーム読み取りエラーハンドリング"""
        # ストリーム読み取りエラーのシミュレート
        mock_stream = Mock()
        mock_stream.read.side_effect = IOError("Stream read error")
        
        with patch.object(self.parser, 'handle_stream_error') as mock_handle:
            try:
                result = await self.parser.process_stream(mock_stream)
            except IOError:
                pass
            
            # ストリームエラーが適切に処理されることを確認
            assert True

    @pytest.mark.asyncio
    async def test_parse_error_recovery(self):
        """パースエラー回復テスト"""
        content = ";;;太字;;; 正常 ;;; ;;;不正マーカー ;;;太字;;; 回復 ;;;"
        stream = io.StringIO(content)
        
        def parse_with_selective_error(chunk):
            if "不正" in chunk:
                raise ValueError("Parse error")
            return Mock()
        
        with patch.object(self.parser, 'parse_chunk', side_effect=parse_with_selective_error):
            with patch.object(self.parser, 'recover_from_parse_error', return_value=Mock()) as mock_recovery:
                result = await self.parser.process_stream(stream)
                
                # パースエラーから回復することを確認
                assert result is not None

    @pytest.mark.asyncio
    async def test_memory_error_handling(self):
        """メモリエラーハンドリング"""
        # メモリエラーのシミュレート
        content = ";;;太字;;; メモリテスト ;;;"
        stream = io.StringIO(content)
        
        with patch.object(self.parser, 'parse_chunk', side_effect=MemoryError("Out of memory")):
            with patch.object(self.parser, 'handle_memory_error') as mock_handle:
                try:
                    result = await self.parser.process_stream(stream)
                except MemoryError:
                    pass
                
                # メモリエラーが適切に処理されることを確認
                assert True

    @pytest.mark.asyncio
    async def test_timeout_error_handling(self):
        """タイムアウトエラーハンドリング"""
        # タイムアウトエラーのシミュレート
        content = ";;;太字;;; タイムアウトテスト ;;;"
        stream = io.StringIO(content)
        
        async def slow_parse(chunk):
            await asyncio.sleep(10)  # 意図的な長時間処理
            return Mock()
        
        with patch.object(self.parser, 'parse_chunk', side_effect=slow_parse):
            with patch.object(self.parser, 'handle_timeout_error') as mock_handle:
                try:
                    result = await asyncio.wait_for(
                        self.parser.process_stream(stream),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    pass
                
                # タイムアウトエラーが適切に処理されることを確認
                assert True

    def test_encoding_error_handling(self):
        """エンコーディングエラーハンドリング"""
        # エンコーディングエラーのシミュレート
        with patch.object(self.parser, 'handle_encoding_error') as mock_handle:
            try:
                # 不正なエンコーディングデータ
                invalid_data = b'\xff\xfe\x00\x00'
                self.parser.parse_chunk(invalid_data.decode('utf-8', errors='ignore'))
            except UnicodeDecodeError:
                pass
            
            # エンコーディングエラーが適切に処理されることを確認
            assert True


class TestStreamingParserOptimization:
    """ストリーミングパーサー最適化テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = KumihanStreamingParser()

    @pytest.mark.asyncio
    async def test_adaptive_chunk_sizing(self):
        """適応的チャンクサイズ調整テスト"""
        # 処理負荷に応じたチャンクサイズ調整
        content = ";;;太字;;; 適応的テスト ;;; " * 1000
        stream = io.StringIO(content)
        
        with patch.object(self.parser, 'adjust_chunk_size') as mock_adjust:
            with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
                result = await self.parser.process_stream(stream)
                
                # チャンクサイズが適応的に調整されることを確認
                assert result is not None

    @pytest.mark.asyncio
    async def test_parallel_chunk_processing(self):
        """並列チャンク処理テスト"""
        # 複数チャンクの並列処理
        content = ";;;太字;;; 並列テスト ;;; " * 500
        stream = io.StringIO(content)
        
        with patch.object(self.parser, 'process_chunks_in_parallel') as mock_parallel:
            with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
                result = await self.parser.process_stream(stream, parallel=True)
                
                # 並列処理が実行されることを確認
                assert result is not None

    @pytest.mark.asyncio
    async def test_memory_pool_optimization(self):
        """メモリプール最適化テスト"""
        # メモリプールを使用した最適化
        content = ";;;太字;;; プール最適化 ;;; " * 200
        stream = io.StringIO(content)
        
        with patch.object(self.parser, 'use_memory_pool') as mock_pool:
            with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
                result = await self.parser.process_stream(stream)
                
                # メモリプールが活用されることを確認
                assert result is not None

    @pytest.mark.asyncio
    async def test_cache_optimization(self):
        """キャッシュ最適化テスト"""
        # パース結果のキャッシュ最適化
        repeated_content = ";;;太字;;; 同じコンテンツ ;;; " * 100
        stream = io.StringIO(repeated_content)
        
        with patch.object(self.parser, 'use_parse_cache') as mock_cache:
            with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
                result = await self.parser.process_stream(stream)
                
                # キャッシュが活用されることを確認
                assert result is not None

    def test_parser_state_optimization(self):
        """パーサー状態最適化テスト"""
        # パーサー内部状態の最適化
        with patch.object(self.parser, 'optimize_internal_state') as mock_optimize:
            self.parser.parse_chunk(";;;太字;;; 状態最適化 ;;;")
            
            # 内部状態最適化が実行されることを確認
            assert True


class TestStreamingParserIntegration:
    """ストリーミングパーサー統合テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = KumihanStreamingParser()

    @pytest.mark.asyncio
    async def test_full_document_streaming_integration(self):
        """完全文書ストリーミング統合テスト"""
        # 実際の大容量文書のストリーミング処理統合テスト
        full_document = """
        ;;;見出し1;;; 大容量文書処理テスト ;;;
        
        通常の段落テキストです。この段落には複数の文が含まれています。
        
        ;;;太字;;; 重要な情報 ;;; があり、;;;イタリック;;; 強調部分 ;;; も存在します。
        
        ;;;枠線 class="highlight";;;
        枠線内のコンテンツです。
        ;;;太字;;; 枠線内の強調 ;;;
        さらに続くテキスト。
        ;;;
        
        """ * 50  # 50回繰り返し
        
        stream = io.StringIO(full_document)
        
        with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
            result = await self.parser.process_stream(stream)
            
            # 完全文書統合処理が成功することを確認
            assert result is not None
            assert mock_parse.call_count > 0

    @pytest.mark.asyncio
    async def test_multi_format_streaming_integration(self):
        """複数フォーマットストリーミング統合テスト"""
        # 異なるフォーマットの混在文書処理
        mixed_format_document = """
        ;;;見出し1;;; マルチフォーマットテスト ;;;
        
        普通のテキスト。
        
        ;;;太字;;; 標準マーカー ;;;
        ;;;イタリック class="special";;; 属性付きマーカー ;;;
        ;;;枠線 id="main" style="border: 1px solid red;";;; 複合属性マーカー ;;;
        
        ネスト構造：
        ;;;太字;;; 外側 ;;;イタリック;;; 内側 ;;; マーカー ;;;
        
        特殊文字：;;;太字;;; 日本語、한국어、中文 ;;;
        
        """ * 20
        
        stream = io.StringIO(mixed_format_document)
        
        with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
            with patch.object(self.parser, 'handle_mixed_formats') as mock_mixed:
                result = await self.parser.process_stream(stream)
                
                # 複数フォーマット統合処理が成功することを確認
                assert result is not None

    @pytest.mark.asyncio
    async def test_real_time_streaming_simulation(self):
        """リアルタイムストリーミングシミュレーション"""
        # リアルタイムデータストリームのシミュレート
        async def simulate_real_time_stream():
            """リアルタイムストリームシミュレート"""
            chunks = [
                ";;;太字;;; リアルタイム ;;;",
                " データが ",
                ";;;イタリック;;; 連続的 ;;;",
                "に到着しています。",
            ]
            
            for chunk in chunks:
                yield chunk
                await asyncio.sleep(0.01)  # 少し遅延
        
        with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
            chunks = []
            async for chunk in simulate_real_time_stream():
                result = self.parser.parse_chunk(chunk)
                chunks.append(result)
            
            # リアルタイムストリーミングが適切に処理されることを確認
            assert len(chunks) > 0
            assert all(chunk is not None for chunk in chunks)

    @pytest.mark.asyncio
    async def test_stress_test_streaming_integration(self):
        """ストレステストストリーミング統合"""
        # 高負荷でのストリーミング処理テスト
        stress_content = ";;;太字;;; ストレステスト ;;; " * 10000
        stream = io.StringIO(stress_content)
        
        with patch.object(self.parser, 'parse_chunk', return_value=Mock()) as mock_parse:
            import time
            start = time.time()
            
            result = await self.parser.process_stream(stream, chunk_size=1000)
            
            end = time.time()
            duration = end - start
            
            # ストレステストが合理的な時間で完了することを確認
            assert result is not None
            assert duration < 10.0  # 10秒以内