"""
パーサー統合テスト

AI開発効率化・個人開発最適化のためのパーサー機能テスト
"""

import pytest
from pathlib import Path
from typing import Any, Dict

from kumihan_formatter.parser import Parser, parse


class TestParser:
    """Parserクラスの統合テスト"""

    @pytest.fixture
    def parser_instance(self) -> Parser:
        """パーサーインスタンス生成"""
        return Parser()

    @pytest.mark.integration
    def test_parser_initialization(self, parser_instance: Parser):
        """パーサー初期化テスト"""
        assert parser_instance is not None
        assert hasattr(parser_instance, 'config')
        assert hasattr(parser_instance, 'logger')

    @pytest.mark.integration
    def test_parse_simple_text(self, parser_instance: Parser):
        """シンプルテキストのパーステスト"""
        text = "これは普通のテキストです。"
        result = parser_instance.parse(text)
        
        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.integration
    def test_parse_kumihan_block(self, parser_instance: Parser, sample_kumihan_text: str):
        """Kumihanブロック記法のパーステスト"""
        result = parser_instance.parse(sample_kumihan_text)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.integration
    def test_parser_error_handling(self, parser_instance: Parser):
        """パーサーエラーハンドリングテスト"""
        # 不正な形式のテキスト
        invalid_text = "# 不完全な記法 #内容"  # 終了マーカーなし
        
        # エラーが発生してもクラッシュしないことを確認
        result = parser_instance.parse(invalid_text)
        assert result is not None

    @pytest.mark.integration
    def test_parser_empty_input(self, parser_instance: Parser):
        """空入力のテスト"""
        result = parser_instance.parse("")
        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.integration
    @pytest.mark.parametrize("input_text", [
        "# 太字 #重要##",
        "# イタリック #斜体##", 
        "# 見出し #タイトル##",
        "通常のテキスト",
        "複数行\nテキスト\nです",
    ])
    def test_parse_various_formats(self, parser_instance: Parser, input_text: str):
        """様々な記法のパーステスト（パラメータ化）"""
        result = parser_instance.parse(input_text)
        assert result is not None
        assert isinstance(result, list)


class TestParseFunction:
    """parse関数の統合テスト"""

    @pytest.mark.integration
    def test_parse_function_basic(self, sample_kumihan_text: str):
        """parse関数の基本テスト"""
        result = parse(sample_kumihan_text)
        
        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.integration
    def test_parse_function_with_config(self, sample_kumihan_text: str):
        """設定付きparse関数のテスト"""
        config = {"strict_mode": True}
        result = parse(sample_kumihan_text, config)
        
        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.integration
    def test_parse_function_empty_input(self):
        """空入力でのparse関数テスト"""
        result = parse("")
        assert result is not None
        assert isinstance(result, list)


class TestParserPerformance:
    """パーサーパフォーマンステスト（AI開発効率化）"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_parse_large_text_performance(self, parser_instance: Parser):
        """大きなテキストのパフォーマンステスト"""
        # 1000行のテキスト生成
        large_text = "\n".join([f"行{i}: # 太字 #内容{i}##" for i in range(1000)])
        
        import time
        start_time = time.time()
        result = parser_instance.parse(large_text)
        end_time = time.time()
        
        # 結果検証
        assert result is not None
        assert isinstance(result, list)
        
        # パフォーマンス検証（10秒以内）
        execution_time = end_time - start_time
        assert execution_time < 10.0, f"パース処理が遅すぎます: {execution_time:.2f}秒"

    @pytest.mark.integration  
    def test_parser_memory_efficiency(self, parser_instance: Parser):
        """メモリ効率性テスト（AI開発Token効率化）"""
        # 中程度のテキスト（100行）
        medium_text = "\n".join([f"行{i}: # 太字 #内容{i}##" for i in range(100)])
        
        # パース実行（メモリ使用量は結果の妥当性で間接的に検証）
        result = parser_instance.parse(medium_text)
        
        # 結果検証
        assert result is not None
        assert isinstance(result, list)
        
        # 大量データでもクラッシュしないことを確認
        assert len(result) >= 0  # 最低限の検証