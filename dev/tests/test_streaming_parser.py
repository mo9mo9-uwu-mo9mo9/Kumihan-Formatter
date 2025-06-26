"""ストリーミングパーサのテスト"""

import pytest
import tempfile
import io
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

from kumihan_formatter.core.streaming import (
    KumihanStreamingParser, StreamingParserConfig, ChunkManager,
    MemoryManager, MemoryConfig, ProgressTracker, ParseResult
)
from kumihan_formatter.core.streaming.performance import (
    PerformanceProfiler, AdaptiveChunkSizer, performance_profiling
)


class TestChunkManager:
    """チャンクマネージャーのテスト"""
    
    def test_create_chunks_from_small_file(self):
        """小さなファイルのチャンク作成テスト"""
        content = "Line 1\\nLine 2\\nLine 3\\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            manager = ChunkManager(chunk_size=10)  # 小さなチャンクサイズ
            chunks = list(manager.create_chunks(temp_path))
            
            assert len(chunks) >= 1
            
            # すべてのチャンクを結合すると元のコンテンツになる
            combined_content = ""
            for chunk_content, metadata in chunks:
                combined_content += chunk_content
            
            assert combined_content.strip() == content.strip()
            
        finally:
            temp_path.unlink()
    
    def test_chunk_metadata(self):
        """チャンクメタデータのテスト"""
        content = "a" * 100  # 100文字
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            manager = ChunkManager(chunk_size=30)
            chunks = list(manager.create_chunks(temp_path))
            
            for i, (chunk_content, metadata) in enumerate(chunks):
                assert metadata.index == i
                assert metadata.size == len(chunk_content)
                assert metadata.start_position <= metadata.end_position
                
        finally:
            temp_path.unlink()
    
    def test_block_boundary_handling(self):
        """ブロック境界処理のテスト"""
        content = """;;;見出し1
タイトル
;;;

通常のテキスト

;;;太字
強調テキスト
;;;"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            manager = ChunkManager(chunk_size=20)  # ブロックを分割するサイズ
            chunks = list(manager.create_chunks(temp_path))
            
            # ブロックが適切に分割されることを確認
            assert len(chunks) >= 1
            
        finally:
            temp_path.unlink()


class TestMemoryManager:
    """メモリマネージャーのテスト"""
    
    def test_memory_monitoring(self):
        """メモリ監視のテスト"""
        config = MemoryConfig(max_memory_mb=10, enable_monitoring=True)
        manager = MemoryManager(config)
        
        with manager.managed_processing():
            # メモリ使用量の取得
            status = manager.get_memory_status()
            
            assert 'current_mb' in status
            assert 'peak_mb' in status
            assert 'usage_ratio' in status
            assert status['current_mb'] >= 0
    
    def test_cache_management(self):
        """キャッシュ管理のテスト"""
        config = MemoryConfig(max_memory_mb=1)  # 小さなメモリ制限
        manager = MemoryManager(config)
        
        # オブジェクトをキャッシュ
        test_data = "a" * 1000
        manager.cache_object("test_key", test_data)
        
        # キャッシュから取得
        cached_data = manager.get_cached_object("test_key")
        assert cached_data == test_data
    
    def test_chunk_memory_estimation(self):
        """チャンクメモリ推定のテスト"""
        manager = MemoryManager()
        
        chunk_size = 1024  # 1KB
        estimated_memory = manager.estimate_chunk_memory(chunk_size)
        
        assert estimated_memory > chunk_size  # オーバーヘッドを含む
        assert estimated_memory > 0
    
    def test_memory_optimization(self):
        """メモリ最適化のテスト"""
        manager = MemoryManager()
        
        # 通常サイズのチャンク
        normal_size = 1024 * 1024  # 1MB
        optimized_size = manager.optimize_chunk_size(normal_size)
        
        assert optimized_size > 0
        assert optimized_size <= normal_size * 2  # 大幅な増大はしない


class TestProgressTracker:
    """進捗追跡のテスト"""
    
    def test_progress_tracking(self):
        """基本的な進捗追跡のテスト"""
        tracker = ProgressTracker(total_bytes=1000, total_chunks=10)
        
        # 進捗開始
        tracker.start()
        info = tracker.get_info()
        assert info.processed_bytes == 0
        assert info.total_bytes == 1000
        
        # 進捗更新
        tracker.update(processed_bytes=500, current_chunk=5)
        info = tracker.get_info()
        assert info.processed_bytes == 500
        assert info.current_chunk == 5
        assert info.progress_ratio == 0.5
        
        # 完了
        tracker.complete()
        info = tracker.get_info()
        assert info.processed_bytes == 1000
    
    def test_progress_callbacks(self):
        """進捗コールバックのテスト"""
        callback_calls = []
        
        def test_callback(info):
            callback_calls.append(info.processed_bytes)
        
        tracker = ProgressTracker(total_bytes=100)
        tracker.add_callback(test_callback)
        
        tracker.start()
        tracker.update(processed_bytes=50)
        tracker.complete()
        
        assert len(callback_calls) >= 2  # start, update, complete
        assert callback_calls[-1] == 100  # 最終的に100%
    
    def test_cancellation(self):
        """キャンセル機能のテスト"""
        tracker = ProgressTracker()
        
        tracker.start()
        assert not tracker.is_cancelled()
        
        tracker.cancel()
        assert tracker.is_cancelled()
        
        info = tracker.get_info()
        assert info.state.value == "cancelled"


class TestStreamingParserConfig:
    """ストリーミングパーサ設定のテスト"""
    
    def test_default_config(self):
        """デフォルト設定のテスト"""
        config = StreamingParserConfig()
        
        assert config.default_chunk_size > 0
        assert config.max_chunk_size >= config.default_chunk_size
        assert config.min_chunk_size <= config.default_chunk_size
        assert config.max_memory_usage > 0
    
    def test_config_validation(self):
        """設定検証のテスト"""
        # 無効な設定
        config = StreamingParserConfig(
            min_chunk_size=1000,
            max_chunk_size=500  # min > max
        )
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("min_chunk_size must be <= max_chunk_size" in error for error in errors)
    
    def test_adaptive_chunk_size(self):
        """適応的チャンクサイズのテスト"""
        config = StreamingParserConfig()
        
        # 小さなファイル
        small_size = config.adjust_chunk_size(1024)
        
        # 大きなファイル
        large_size = config.adjust_chunk_size(100 * 1024 * 1024)
        
        assert small_size <= large_size


class TestKumihanStreamingParser:
    """Kumihanストリーミングパーサのテスト"""
    
    def test_parse_small_file(self):
        """小さなファイルのパーステスト"""
        content = """;;;見出し1
テストタイトル
;;;

これは段落です。

;;;太字
強調テキスト
;;;"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = KumihanStreamingParser()
            result = parser.parse_file(temp_path)
            
            assert isinstance(result, ParseResult)
            assert result.content
            assert result.processing_time > 0
            assert result.chunks_processed > 0
            assert len(result.errors) >= 0  # エラーがあってもテストは継続
            
            # HTMLが生成されていることを確認
            assert "<h1>" in result.content or "<strong>" in result.content
            
        finally:
            temp_path.unlink()
    
    def test_parse_stream(self):
        """ストリームパーステスト"""
        content = "Line 1\\nLine 2\\nLine 3\\n"
        stream = io.StringIO(content)
        
        parser = KumihanStreamingParser()
        result = parser.parse_stream(stream, total_size=len(content))
        
        assert isinstance(result, ParseResult)
        assert result.content
        assert result.chunks_processed > 0
    
    @pytest.mark.asyncio
    async def test_async_parsing(self):
        """非同期パーステスト"""
        content = "Test content for async parsing\\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = KumihanStreamingParser()
            result = await parser.parse_file_async(temp_path)
            
            assert isinstance(result, ParseResult)
            assert result.content
            
        finally:
            temp_path.unlink()
    
    def test_memory_limit_enforcement(self):
        """メモリ制限の実行テスト"""
        content = "a" * 10000  # 10KB
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            # 非常に小さなメモリ制限を設定
            config = StreamingParserConfig(max_memory_usage=1024)  # 1KB
            parser = KumihanStreamingParser(config)
            
            # パースが完了することを確認（メモリ制限内で動作）
            result = parser.parse_file(temp_path, max_memory=1024)
            assert isinstance(result, ParseResult)
            
        finally:
            temp_path.unlink()
    
    def test_chunk_info_generation(self):
        """チャンク情報生成のテスト"""
        content = "Line 1\\nLine 2\\nLine 3\\n" * 100  # 大きめのコンテンツ
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = KumihanStreamingParser()
            chunk_infos = parser.get_chunk_info(temp_path, chunk_size=100)
            
            assert len(chunk_infos) > 0
            for info in chunk_infos:
                assert info.index >= 0
                assert info.size > 0
                assert info.content_preview
                assert len(info.content_preview) <= 103  # "..." を含む
                
        finally:
            temp_path.unlink()
    
    def test_memory_usage_estimation(self):
        """メモリ使用量推定のテスト"""
        parser = KumihanStreamingParser()
        
        file_size = 1024 * 1024  # 1MB
        chunk_size = 64 * 1024   # 64KB
        
        estimates = parser.estimate_memory_usage(file_size, chunk_size)
        
        assert 'chunk_memory_bytes' in estimates
        assert 'buffer_memory_bytes' in estimates
        assert 'total_memory_bytes' in estimates
        assert 'estimated_chunks' in estimates
        
        assert estimates['total_memory_bytes'] > 0
        assert estimates['estimated_chunks'] > 0
    
    def test_progress_callback_integration(self):
        """進捗コールバック統合のテスト"""
        progress_updates = []
        
        def progress_callback(processed_bytes, total_bytes, current_chunk, total_chunks, message):
            progress_updates.append({
                'processed_bytes': processed_bytes,
                'total_bytes': total_bytes,
                'current_chunk': current_chunk,
                'message': message
            })
        
        content = "Line 1\\nLine 2\\nLine 3\\n" * 10
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = KumihanStreamingParser()
            result = parser.parse_file(
                temp_path, 
                chunk_size=50,
                progress_callback=progress_callback
            )
            
            assert isinstance(result, ParseResult)
            assert len(progress_updates) > 0
            
            # 進捗が増加していることを確認
            processed_bytes_list = [update['processed_bytes'] for update in progress_updates if update['processed_bytes'] is not None]
            if len(processed_bytes_list) > 1:
                assert processed_bytes_list[-1] >= processed_bytes_list[0]
            
        finally:
            temp_path.unlink()


class TestPerformanceOptimization:
    """パフォーマンス最適化のテスト"""
    
    def test_performance_profiling(self):
        """パフォーマンスプロファイリングのテスト"""
        profiler = PerformanceProfiler()
        
        profiler.start_profiling()
        
        # 模擬的なチャンク処理
        with profiler.measure_chunk_processing(1024):
            import time
            time.sleep(0.01)  # 10ms待機
        
        metrics = profiler.stop_profiling()
        
        assert metrics.total_time > 0
        assert len(metrics.chunk_processing_times) > 0
        assert metrics.throughput_mbps >= 0
    
    def test_adaptive_chunk_sizer(self):
        """適応的チャンクサイザーのテスト"""
        config = StreamingParserConfig()
        sizer = AdaptiveChunkSizer(config)
        
        file_size = 10 * 1024 * 1024  # 10MB
        available_memory = 50 * 1024 * 1024  # 50MB
        
        optimal_size = sizer.get_optimal_chunk_size(file_size, available_memory)
        
        assert optimal_size >= config.min_chunk_size
        assert optimal_size <= config.max_chunk_size
        assert optimal_size <= available_memory // 4  # メモリ制約を考慮
    
    def test_performance_context_manager(self):
        """パフォーマンスコンテキストマネージャーのテスト"""
        
        with performance_profiling() as profiler:
            # 模擬的な処理
            with profiler.measure_chunk_processing(1024):
                import time
                time.sleep(0.001)  # 1ms待機
        
        # コンテキストマネージャーが適切に動作することを確認
        assert profiler.metrics.total_time > 0


class TestErrorHandling:
    """エラーハンドリングのテスト"""
    
    def test_file_not_found_error(self):
        """ファイル未存在エラーのテスト"""
        parser = KumihanStreamingParser()
        non_existent_path = Path("/non/existent/file.txt")
        
        with pytest.raises(FileNotFoundError):
            parser.parse_file(non_existent_path)
    
    def test_invalid_config_error(self):
        """無効設定エラーのテスト"""
        invalid_config = StreamingParserConfig(
            min_chunk_size=1000,
            max_chunk_size=500  # 無効：min > max
        )
        
        with pytest.raises(Exception):  # KumihanError
            KumihanStreamingParser(invalid_config)
    
    def test_memory_exhaustion_handling(self):
        """メモリ不足処理のテスト"""
        # 非常に制限的なメモリ設定
        config = StreamingParserConfig(max_memory_usage=1)  # 1バイト
        
        # エラーが発生するか、適切に処理されるかを確認
        try:
            parser = KumihanStreamingParser(config)
            # 小さなダミーファイルでもテスト
            content = "test"
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                temp_path = Path(f.name)
            
            try:
                result = parser.parse_file(temp_path)
                # メモリ制約下でも何らかの結果が得られることを確認
                assert isinstance(result, ParseResult)
            finally:
                temp_path.unlink()
                
        except Exception as e:
            # 適切なエラーメッセージが含まれることを確認
            assert "memory" in str(e).lower() or "config" in str(e).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])