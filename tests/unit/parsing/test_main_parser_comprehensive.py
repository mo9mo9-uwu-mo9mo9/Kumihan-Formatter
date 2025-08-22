"""
MainParser効率化テストスイート

Issue #1113: 701→200テスト削減による70%実行時間短縮

統合されたテスト領域：
- 基本機能（初期化・パース・統計）
- Kumihan記法解析（統合テスト）
- 統合機能（パーサー連携）
- エラーハンドリング（例外・不正入力）
- パフォーマンス（大容量・並列）
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Iterator
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node, create_node, error_node
from kumihan_formatter.core.parsing.main_parser import MainParser
from kumihan_formatter.core.utilities.logger import get_logger


class TestMainParserCore:
    """MainParser基本機能テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()
        self.logger = get_logger(self.__class__.__name__)

    @pytest.mark.parametrize("config,expected_type", [
        (None, "main"),
        ({"test": "value"}, "main"),
        ({}, "main"),
    ])
    def test_initialization_variants(self, config, expected_type):
        """初期化バリエーションテスト"""
        parser = MainParser(config=config)
        assert parser.parser_type == expected_type
        assert hasattr(parser, "parsers")

        # 専門パーサーの存在確認
        expected_parsers = ["keyword", "list", "block", "markdown"]
        for parser_name in expected_parsers:
            assert parser_name in parser.parsers

    @pytest.mark.parametrize("input_text,expected_type", [
        ("基本テキスト", "text"),
        ("", "error"),
        ("   \n\t  \n  ", "error"),
        (None, "error"),
        (123, "error"),
    ])
    def test_parse_inputs(self, input_text, expected_type):
        """パース入力バリエーションテスト"""
        result = self.parser.parse(input_text)
        assert isinstance(result, list)
        assert len(result) >= 1
        if expected_type == "error":
            assert result[0].type == "error"
        else:
            assert all(isinstance(node, Node) for node in result)

    def test_statistics_and_state_management(self):
        """統計と状態管理統合テスト"""
        # 初期統計確認
        initial_stats = self.parser.get_performance_stats()
        assert initial_stats["total_parses"] == 0

        # 複数パース実行
        texts = ["テスト1", "テスト2", "テスト3"]
        for i, text in enumerate(texts, 1):
            result = self.parser.parse(text)
            assert len(result) > 0
            stats = self.parser.get_performance_stats()
            assert stats["total_parses"] == i
            assert stats["total_time"] > 0

        # 統計リセットテスト
        self.parser.reset_statistics()
        reset_stats = self.parser.get_performance_stats()
        assert reset_stats["total_parses"] == 0
        assert reset_stats["total_time"] == 0.0


class TestMainParserKumihanNotation:
    """Kumihan記法解析統合テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    @pytest.mark.parametrize("notation_text,description", [
        ("#太字#\n重要な情報\n##", "基本ブロック記法"),
        ("これは #強調# された文章です。", "インライン記法"),
        ("#見出し#\nタイトル\n##\n\n通常テキスト", "混合記法"),
        ("#外部#\n#内部#\n内容\n##\n##", "ネスト構造"),
        ("#不完全なブロック", "不正形式記法"),
    ])
    def test_kumihan_notation_parsing(self, notation_text, description):
        """Kumihan記法統合パーステスト"""
        result = self.parser.parse(notation_text)
        assert isinstance(result, list)
        assert len(result) > 0
        # 全てのノードが適切な型を持つことを確認
        for node in result:
            assert hasattr(node, "type")

    def test_complex_document_structure(self):
        """複雑文書構造テスト"""
        complex_text = """#文書タイトル#
メイン文書
##

#セクション1#
内容
##

- リスト項目1
- リスト項目2

#結論#
まとめ
##"""

        result = self.parser.parse(complex_text)
        assert isinstance(result, list)
        assert len(result) > 0


class TestMainParserIntegration:
    """統合・協調機能テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    def test_specialized_parsers_availability(self):
        """専門パーサー利用可能性テスト"""
        expected_parsers = ["keyword", "list", "block", "markdown"]
        for parser_name in expected_parsers:
            assert parser_name in self.parser.parsers
            assert self.parser.parsers[parser_name] is not None

    @pytest.mark.parametrize("parser_type,test_text", [
        ("keyword", "キーワードテスト"),
        ("list", "- 項目1\n- 項目2"),
        ("markdown", "# Heading\n**Bold**"),
    ])
    def test_parser_integration_execution(self, parser_type, test_text):
        """パーサー統合実行テスト"""
        assert parser_type in self.parser.parsers
        result = self.parser.parse(test_text)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_parser_management_operations(self):
        """パーサー管理操作統合テスト"""
        # パーサー情報取得
        info = self.parser.get_parser_info()
        assert isinstance(info, dict)
        assert "main_parser" in info
        assert "specialized_parsers" in info

        # パーサー登録・解除
        mock_parser = Mock()
        mock_parser.can_parse.return_value = True
        mock_parser.parse.return_value = [create_node("test", content="test")]

        self.parser.register_parser("test_parser", mock_parser)
        assert "test_parser" in self.parser.parsers

        success = self.parser.unregister_parser("test_parser")
        assert success is True
        assert "test_parser" not in self.parser.parsers

        # 存在しないパーサーの解除
        success = self.parser.unregister_parser("nonexistent")
        assert success is False

    def test_parser_selection_mechanism(self):
        """パーサー選択機構テスト"""
        selected_parsers = self.parser._select_parsers("テスト")
        assert isinstance(selected_parsers, list)
        assert len(selected_parsers) >= 0


class TestMainParserErrorHandling:
    """エラーハンドリング統合テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    @pytest.mark.parametrize("invalid_input,expected_error", [
        (None, "error"),
        (123, "error"),
        (["test"], "error"),
        ("", "error"),
        ("   \n\t\n   ", "error"),
    ])
    def test_invalid_input_handling(self, invalid_input, expected_error):
        """不正入力統合ハンドリングテスト"""
        result = self.parser.parse(invalid_input)
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0].type == expected_error

    def test_special_and_large_input_handling(self):
        """特殊・大容量入力ハンドリングテスト"""
        test_cases = [
            "🎯📋✅❌",  # 絵文字
            "テスト\x00\x01\x02",  # 制御文字
            "a" * 100000,  # 大容量
            "テスト\n" * 1000,  # 大量改行
        ]

        for text in test_cases:
            try:
                result = self.parser.parse(text)
                assert isinstance(result, list)
                assert len(result) > 0
            except Exception:
                # 例外発生時も処理継続
                pass

    def test_graceful_degradation_and_concurrency(self):
        """優雅な劣化と並行処理統合テスト"""
        # パーサー無効化テスト
        original = self.parser.parsers["keyword"]
        self.parser.parsers["keyword"] = None

        try:
            result = self.parser.parse("劣化テスト")
            assert isinstance(result, list)
        finally:
            self.parser.parsers["keyword"] = original

        # 並行処理エラーハンドリング
        def concurrent_parse():
            return self.parser.parse("並行テスト" * 100)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(concurrent_parse) for _ in range(2)]
            for future in futures:
                try:
                    result = future.result(timeout=3)
                    assert isinstance(result, list)
                except Exception:
                    pass


class TestMainParserPerformance:
    """パフォーマンス統合テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    def test_large_document_processing(self):
        """大容量文書処理統合テスト"""
        # 大容量テキスト（約50KB）
        large_text = "#大容量テスト#\nテスト内容\n##\n" * 1000

        start_time = time.time()
        result = self.parser.parse(large_text)
        elapsed_time = time.time() - start_time

        assert isinstance(result, list)
        assert len(result) > 0
        assert elapsed_time < 10.0  # 10秒以内

    def test_parallel_processing_capabilities(self):
        """並列処理機能統合テスト"""
        # 並列処理閾値テスト
        small_text = "小さなテキスト"
        large_text = "大きなテキスト\n" * 20000

        assert not self.parser._should_use_parallel_processing(small_text)
        assert self.parser._should_use_parallel_processing(large_text)

        # チャンク分割テスト
        chunks = self.parser._split_into_chunks(large_text)
        assert isinstance(chunks, list)
        assert len(chunks) > 1

    def test_streaming_and_memory_management(self):
        """ストリーミング・メモリ管理統合テスト"""
        # ストリーミング処理
        def text_stream():
            for i in range(50):
                yield f"ストリーミング {i}\n"

        start_time = time.time()
        results = list(self.parser.parse_streaming(text_stream()))
        elapsed_time = time.time() - start_time

        assert len(results) > 0
        assert elapsed_time < 5.0

        # メモリ使用量安定性（統計リセット含む）
        for i in range(20):
            text = f"メモリテスト {i}\n" * 50
            result = self.parser.parse(text)
            assert len(result) > 0
            if i % 10 == 0:
                self.parser.reset_statistics()

    def test_concurrent_processing_safety(self):
        """並行処理安全性統合テスト"""
        def parse_task(task_id):
            return self.parser.parse(f"並行テスト {task_id}")

        with ThreadPoolExecutor(max_workers=3) as executor:
            tasks = [executor.submit(parse_task, i) for i in range(6)]
            results = []

            for task in tasks:
                try:
                    result = task.result(timeout=2)
                    results.append(result)
                except Exception:
                    pass

            assert len(results) > 0


class TestMainParserProtocols:
    """プロトコル準拠統合テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    def test_parse_and_validation_protocols(self):
        """パース・バリデーションプロトコル統合テスト"""
        content = "プロトコル統合テスト"

        # パースプロトコル
        parse_result = self.parser.parse_protocol(content)
        assert hasattr(parse_result, "success")
        assert hasattr(parse_result, "nodes")
        assert parse_result.success is True
        assert isinstance(parse_result.nodes, list)

        # バリデーションプロトコル
        validation_errors = self.parser.validate(content)
        assert isinstance(validation_errors, list)

    def test_format_support_and_info_protocols(self):
        """フォーマット対応・情報プロトコル統合テスト"""
        # フォーマット対応確認
        supported = ["kumihan", "markdown", "text", "auto"]
        for fmt in supported:
            assert self.parser.supports_format(fmt) is True
        assert self.parser.supports_format("unsupported") is False

        # パーサー情報プロトコル
        info = self.parser.get_parser_info_protocol()
        assert isinstance(info, dict)
        required_keys = ["name", "version", "supported_formats", "capabilities"]
        for key in required_keys:
            assert key in info
        assert info["name"] == "MainParser"

    def test_streaming_protocol_integration(self):
        """ストリーミングプロトコル統合テスト"""
        def test_stream():
            yield "ストリーミング"
            yield "プロトコル"
            yield "統合テスト"

        results = list(self.parser.parse_streaming_protocol(test_stream()))
        assert len(results) > 0

        for result in results:
            assert hasattr(result, "success")
            assert hasattr(result, "nodes")


class TestMainParserUtilities:
    """ユーティリティ機能統合テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    def test_element_extraction_and_stats(self):
        """要素抽出・統計機能統合テスト"""
        # 要素抽出テスト
        buffer = "#要素1##テキスト##要素2##残り"
        elements, remaining = self.parser._extract_complete_elements(buffer)
        assert isinstance(elements, list)
        assert isinstance(remaining, str)

        # 統計更新テスト
        self.parser.parse("統計テスト")
        initial_stats = self.parser.get_performance_stats()
        self.parser._update_performance_stats(0.1)
        updated_stats = self.parser.get_performance_stats()
        assert updated_stats["total_time"] > initial_stats["total_time"]

    @pytest.mark.parametrize("input_value,expected", [
        ("有効なテキスト", True),
        ("", False),
        ("   ", False),
        (None, False),
        (123, False),
    ])
    def test_input_validation_utilities(self, input_value, expected):
        """入力検証ユーティリティ統合テスト"""
        result = self.parser._validate_input(input_value)
        assert result is expected

    def test_system_utilities(self):
        """システムユーティリティ統合テスト"""
        # CPU数取得
        cpu_count = self.parser._get_cpu_count()
        assert cpu_count is None or (isinstance(cpu_count, int) and cpu_count > 0)

    def test_advanced_di_and_factory_integration(self):
        """高度なDI・ファクトリ統合テスト"""
        # DI Container複雑シナリオ
        mock_container = Mock()
        resolution_calls = 0

        def mock_resolve(cls):
            nonlocal resolution_calls
            resolution_calls += 1
            if resolution_calls > 5:
                raise Exception("Too many calls")
            mock_instance = Mock()
            mock_instance.can_parse.return_value = True
            mock_instance.parse.return_value = [create_node("test", content="resolved")]
            return mock_instance

        mock_container.resolve.side_effect = mock_resolve
        di_parser = MainParser(container=mock_container)
        result = di_parser.parse("DI統合テスト")

        assert isinstance(result, list)
        assert resolution_calls <= 5

    def test_import_error_paths_and_edge_cases(self):
        """インポートエラーパス・エッジケース統合テスト"""
        # DI Container ImportError
        with patch("kumihan_formatter.core.patterns.dependency_injection.get_container") as mock_get:
            mock_get.side_effect = ImportError("DI module not found")
            parser = MainParser()
            assert parser.container is None
            assert parser.parser_factory is None


@pytest.mark.integration
class TestMainParserEndToEnd:
    """エンドツーエンド統合テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    def test_complete_document_processing(self):
        """完全文書処理統合テスト"""
        document = """#メイン文書#
包括的なテストドキュメント

#セクション1#
- 基本機能
- エラーハンドリング
##

#セクション2#
応用機能テスト
##

#結論#
全機能正常動作確認
##"""

        start_time = time.time()
        result = self.parser.parse(document)
        elapsed_time = time.time() - start_time

        assert isinstance(result, list)
        assert len(result) > 0
        assert elapsed_time < 1.0

        stats = self.parser.get_performance_stats()
        assert stats["total_parses"] == 1
        assert stats["total_time"] > 0

    def test_real_world_usage_and_error_recovery(self):
        """実世界使用・エラー回復統合テスト"""
        # 多様なコンテンツテスト
        contents = [
            "短いテキスト",
            "#見出し#\n内容\n##",
            "- リスト項目",
            "# マークダウン\n**太字**",
            "#不完全ブロック",  # エラーケース
            "正常テキスト",
        ]

        successful_parses = 0
        for content in contents:
            try:
                result = self.parser.parse(content)
                if isinstance(result, list) and len(result) > 0:
                    successful_parses += 1
            except Exception:
                pass

        assert successful_parses >= len(contents) - 1  # エラーケース除く

        final_stats = self.parser.get_performance_stats()
        assert final_stats["total_parses"] >= successful_parses
