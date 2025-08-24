"""
パーサー設定・並列処理設定テスト (Issue #1143)

Critical Priority: テストカバレッジ危機的不足（0.6%）対策  
Phase 1: パーサー設定系クラステスト追加
"""

import pytest
import os
from unittest.mock import patch, Mock

from kumihan_formatter.parser import ParallelProcessingConfig, ParallelProcessingError, ChunkProcessingError, MemoryMonitoringError


class TestParallelProcessingConfig:
    """並列処理設定クラステスト"""

    @pytest.mark.unit
    def test_default_initialization(self):
        """デフォルト初期化テスト"""
        config = ParallelProcessingConfig()
        
        # デフォルト値確認
        assert config.parallel_threshold_lines > 0
        assert config.parallel_threshold_size > 0
        assert config.memory_critical_threshold_mb > 0

    @pytest.mark.unit
    def test_custom_initialization(self):
        """カスタム初期化後のカスタマイズテスト"""
        config = ParallelProcessingConfig()
        
        # 作成後に設定を変更
        config.parallel_threshold_lines = 1000
        config.parallel_threshold_size = 50000
        config.memory_critical_threshold_mb = 256
        
        assert config.parallel_threshold_lines == 1000
        assert config.parallel_threshold_size == 50000
        assert config.memory_critical_threshold_mb == 256

    @pytest.mark.unit
    def test_from_environment_with_env_vars(self):
        """環境変数からの設定読み込みテスト"""
        with patch.dict(os.environ, {
            'KUMIHAN_PARALLEL_THRESHOLD_LINES': '500',
            'KUMIHAN_PARALLEL_THRESHOLD_SIZE': '25000',
            'KUMIHAN_MEMORY_LIMIT_MB': '128'
        }):
            config = ParallelProcessingConfig.from_environment()
            
            assert config.parallel_threshold_lines == 500
            assert config.parallel_threshold_size == 25000
            assert config.memory_critical_threshold_mb == 128

    @pytest.mark.unit
    def test_from_environment_without_env_vars(self):
        """環境変数なしでのデフォルト設定テスト"""
        # 環境変数をクリア
        env_vars = [
            'KUMIHAN_PARALLEL_THRESHOLD_LINES',
            'KUMIHAN_PARALLEL_THRESHOLD_SIZE', 
            'KUMIHAN_MEMORY_LIMIT_MB'
        ]
        
        with patch.dict(os.environ, {}, clear=False):
            for var in env_vars:
                os.environ.pop(var, None)
            
            config = ParallelProcessingConfig.from_environment()
            
            # デフォルト値が使用されることを確認
            assert config.parallel_threshold_lines > 0
            assert config.parallel_threshold_size > 0
            assert config.memory_critical_threshold_mb > 0

    @pytest.mark.unit
    def test_from_environment_invalid_values(self):
        """環境変数の無効な値処理テスト"""
        with patch.dict(os.environ, {
            'KUMIHAN_PARALLEL_THRESHOLD_LINES': 'invalid',
            'KUMIHAN_PARALLEL_THRESHOLD_SIZE': 'not_a_number',
            'KUMIHAN_MEMORY_LIMIT_MB': 'bad_value'
        }):
            # 無効な値でもクラッシュしないことを確認
            config = ParallelProcessingConfig.from_environment()
            assert config is not None

    @pytest.mark.unit
    def test_validate_valid_config(self):
        """有効な設定の検証テスト"""
        config = ParallelProcessingConfig()
        config.parallel_threshold_lines = 100
        config.parallel_threshold_size = 5000
        config.memory_warning_threshold_mb = 50  # criticalより小さく設定
        config.memory_critical_threshold_mb = 64
        
        assert config.validate() is True

    @pytest.mark.unit
    def test_validate_invalid_config(self):
        """無効な設定の検証テスト"""
        config = ParallelProcessingConfig()
        # 負の値での設定
        config.parallel_threshold_lines = -1
        config.parallel_threshold_size = -1
        config.memory_critical_threshold_mb = -1
        
        assert config.validate() is False

    @pytest.mark.unit 
    def test_validate_zero_values(self):
        """ゼロ値設定の検証テスト"""
        config = ParallelProcessingConfig()
        config.parallel_threshold_lines = 0
        config.parallel_threshold_size = 0
        config.memory_critical_threshold_mb = 0
        
        # ゼロ値は無効とみなされるべき
        assert config.validate() is False

    @pytest.mark.unit
    def test_config_attributes_access(self):
        """設定属性アクセステスト"""
        config = ParallelProcessingConfig()
        config.parallel_threshold_lines = 200
        config.parallel_threshold_size = 10000
        config.memory_critical_threshold_mb = 128
        
        # 属性値が正しく設定・取得できることを確認
        assert config.parallel_threshold_lines == 200
        assert config.parallel_threshold_size == 10000
        assert config.memory_critical_threshold_mb == 128


class TestParallelProcessingExceptions:
    """並列処理例外クラステスト"""

    @pytest.mark.unit
    def test_parallel_processing_error_creation(self):
        """ParallelProcessingError作成テスト"""
        error_msg = "Test parallel processing error"
        error = ParallelProcessingError(error_msg)
        
        assert str(error) == error_msg
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_chunk_processing_error_creation(self):
        """ChunkProcessingError作成テスト"""
        error_msg = "Test chunk processing error"
        error = ChunkProcessingError(error_msg)
        
        assert str(error) == error_msg
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_memory_monitoring_error_creation(self):
        """MemoryMonitoringError作成テスト"""
        error_msg = "Test memory monitoring error"
        error = MemoryMonitoringError(error_msg)
        
        assert str(error) == error_msg
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_exception_inheritance(self):
        """例外継承関係テスト"""
        # すべての例外がExceptionから継承されていることを確認
        assert issubclass(ParallelProcessingError, Exception)
        assert issubclass(ChunkProcessingError, Exception)
        assert issubclass(MemoryMonitoringError, Exception)

    @pytest.mark.unit
    def test_exception_with_none_message(self):
        """Noneメッセージでの例外作成テスト"""
        error = ParallelProcessingError(None)
        assert error is not None

    @pytest.mark.unit
    def test_exception_with_empty_message(self):
        """空メッセージでの例外作成テスト"""
        error = ChunkProcessingError("")
        assert str(error) == ""

    @pytest.mark.unit
    def test_exception_with_multiline_message(self):
        """複数行メッセージでの例外作成テスト"""
        multiline_msg = """Line 1 of error
        Line 2 of error
        Line 3 of error"""
        error = MemoryMonitoringError(multiline_msg)
        assert "Line 1" in str(error)
        assert "Line 2" in str(error)
        assert "Line 3" in str(error)


class TestParallelProcessingConfigEdgeCases:
    """並列処理設定エッジケーステスト"""

    @pytest.mark.unit
    def test_extreme_large_values(self):
        """極端に大きな値での設定テスト"""
        config = ParallelProcessingConfig()
        config.parallel_threshold_lines = 1000000
        config.parallel_threshold_size = 100000000
        config.memory_critical_threshold_mb = 10000
        
        # 大きな値でも正常に設定されることを確認
        assert config.parallel_threshold_lines == 1000000
        assert config.parallel_threshold_size == 100000000
        assert config.memory_critical_threshold_mb == 10000
        assert config.validate() is True

    @pytest.mark.unit
    def test_minimum_valid_values(self):
        """最小有効値でのテスト"""
        config = ParallelProcessingConfig()
        config.parallel_threshold_lines = 1
        config.parallel_threshold_size = 1
        config.min_chunk_size = 1
        config.max_chunk_size = 2  # min_chunk_sizeより大きく設定
        config.memory_warning_threshold_mb = 1
        config.memory_critical_threshold_mb = 2  # warningより大きく設定
        config.processing_timeout_seconds = 1
        
        assert config.validate() is True

    @pytest.mark.unit
    def test_config_modification_after_creation(self):
        """作成後の設定変更テスト"""
        config = ParallelProcessingConfig()
        original_lines = config.parallel_threshold_lines
        
        # 設定を変更
        config.parallel_threshold_lines = 999
        assert config.parallel_threshold_lines == 999
        assert config.parallel_threshold_lines != original_lines

    @pytest.mark.unit
    def test_config_equality_comparison(self):
        """設定の等価比較テスト"""
        config1 = ParallelProcessingConfig()
        config1.parallel_threshold_lines = 100
        config1.parallel_threshold_size = 5000
        config1.memory_critical_threshold_mb = 64
        
        config2 = ParallelProcessingConfig()
        config2.parallel_threshold_lines = 100
        config2.parallel_threshold_size = 5000
        config2.memory_critical_threshold_mb = 64
        
        config3 = ParallelProcessingConfig()
        config3.parallel_threshold_lines = 200
        config3.parallel_threshold_size = 5000
        config3.memory_critical_threshold_mb = 64
        
        # 実装依存だが、基本的な値比較をテスト
        assert config1.parallel_threshold_lines == config2.parallel_threshold_lines
        assert config1.parallel_threshold_lines != config3.parallel_threshold_lines

    @pytest.mark.unit
    def test_config_copy_semantics(self):
        """設定コピー動作テスト"""
        config1 = ParallelProcessingConfig()
        config1.parallel_threshold_lines = 150
        
        # 新しいインスタンス作成
        config2 = ParallelProcessingConfig()
        config2.parallel_threshold_lines = config1.parallel_threshold_lines
        config2.parallel_threshold_size = config1.parallel_threshold_size
        config2.memory_critical_threshold_mb = config1.memory_critical_threshold_mb
        
        # 値が同じことを確認
        assert config1.parallel_threshold_lines == config2.parallel_threshold_lines
        assert config1.parallel_threshold_size == config2.parallel_threshold_size
        assert config1.memory_critical_threshold_mb == config2.memory_critical_threshold_mb
        
        # 別インスタンスであることを確認
        assert config1 is not config2


class TestParallelProcessingConfigIntegration:
    """並列処理設定統合テスト"""

    @pytest.mark.unit
    def test_config_with_parser_integration(self):
        """パーサーとの統合テスト"""
        from kumihan_formatter.parser import Parser
        
        config = ParallelProcessingConfig()
        config.parallel_threshold_lines = 50
        config.parallel_threshold_size = 2000
        config.memory_warning_threshold_mb = 30  # criticalより小さく設定
        config.memory_critical_threshold_mb = 32
        
        # validate()が成功することを確認
        assert config.validate() is True
        
        parser = Parser(parallel_config=config)
        
        # オブジェクトの参照が同じであることを確認
        assert parser.parallel_config is config
        assert parser.parallel_threshold_lines == 50
        assert parser.parallel_threshold_size == 2000

    @pytest.mark.unit 
    def test_invalid_config_with_parser(self):
        """無効な設定でのパーサー動作テスト"""
        from kumihan_formatter.parser import Parser
        
        # 無効な設定を作成
        invalid_config = ParallelProcessingConfig()
        invalid_config.parallel_threshold_lines = -1
        invalid_config.parallel_threshold_size = -1
        invalid_config.memory_critical_threshold_mb = -1
        
        # パーサーが適切にフォールバックすることを確認
        parser = Parser(parallel_config=invalid_config)
        assert parser is not None
        assert parser.parallel_config is not None

    @pytest.mark.unit
    def test_config_validation_with_warnings(self):
        """設定検証時の警告処理テスト"""
        config = ParallelProcessingConfig()
        
        # validateメソッドがFalseを返すように設定
        with patch.object(config, 'validate', return_value=False):
            from kumihan_formatter.parser import Parser
            
            # 警告が発生してもパーサーが正常に作成されることを確認
            parser = Parser(parallel_config=config)
            assert parser is not None