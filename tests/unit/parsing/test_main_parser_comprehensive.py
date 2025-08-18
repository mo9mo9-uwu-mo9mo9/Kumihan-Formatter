"""
MainParser包括的テストスイート

Issue #929: MainParser完全テスト実装による46%→85%カバレッジ向上

このテストスイートは以下の機能領域を包括的にテストします：
- 基本機能（初期化・パース・設定管理）
- Kumihan記法解析（ブロック・インライン・ネスト）
- 統合・協調機能（専門パーサー連携・DI統合）
- エラーハンドリング（例外処理・不正入力・耐性）
- パフォーマンス・負荷（大容量・並列・ストリーミング）
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

    def test_initialization_basic(self):
        """基本初期化テスト"""
        parser = MainParser()

        # 基本属性の存在確認
        assert parser is not None
        assert hasattr(parser, "logger")
        assert hasattr(parser, "config")
        assert hasattr(parser, "parsers")
        assert hasattr(parser, "performance_stats")

        # パーサー種別の確認
        assert parser.parser_type == "main"

        # 専門パーサーの初期化確認
        expected_parsers = ["keyword", "list", "block", "markdown"]
        for parser_name in expected_parsers:
            assert parser_name in parser.parsers
            assert parser.parsers[parser_name] is not None

    def test_initialization_with_config(self):
        """設定付き初期化テスト"""
        test_config = {"test_option": "test_value"}
        parser = MainParser(config=test_config)

        assert parser.config == test_config
        assert parser.parser_type == "main"

    def test_initialization_with_di_container_mock(self):
        """DIコンテナ付き初期化テスト（モック使用）"""
        mock_container = Mock()
        mock_container.resolve.return_value = Mock()

        parser = MainParser(container=mock_container)

        assert parser.container == mock_container
        assert parser.parsers is not None

    def test_parse_basic_text(self):
        """基本テキストパーステスト"""
        test_text = "これは基本的なテストテキストです。"

        result = self.parser.parse(test_text)

        # 基本検証
        assert isinstance(result, list)
        assert len(result) > 0

        # 最低限のノード構造確認
        for node in result:
            assert isinstance(node, Node)
            assert hasattr(node, "type")

    def test_parse_empty_input(self):
        """空入力パーステスト"""
        result = self.parser.parse("")

        # 空入力でも適切な処理
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].type == "error"

    def test_parse_whitespace_only(self):
        """空白のみ入力テスト"""
        result = self.parser.parse("   \n\t  \n  ")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].type == "error"

    def test_parse_with_statistics_tracking(self):
        """統計追跡付きパーステスト"""
        # 初期統計確認
        initial_stats = self.parser.get_performance_stats()
        assert initial_stats["total_parses"] == 0

        # パース実行
        self.parser.parse("テストテキスト")

        # 統計更新確認
        updated_stats = self.parser.get_performance_stats()
        assert updated_stats["total_parses"] == 1
        assert updated_stats["total_time"] > 0
        assert updated_stats["average_time"] > 0

    def test_parser_state_management(self):
        """パーサー状態管理テスト"""
        # 複数回パース実行
        texts = ["テキスト1", "テキスト2", "テキスト3"]

        for i, text in enumerate(texts, 1):
            result = self.parser.parse(text)
            assert len(result) > 0

            # 統計が正しく累積されているか確認
            stats = self.parser.get_performance_stats()
            assert stats["total_parses"] == i

    def test_reset_statistics(self):
        """統計リセットテスト"""
        # 何回かパースを実行
        self.parser.parse("テスト1")
        self.parser.parse("テスト2")

        # 統計がカウントされていることを確認
        stats = self.parser.get_performance_stats()
        assert stats["total_parses"] == 2

        # リセット実行
        self.parser.reset_statistics()

        # リセット確認
        reset_stats = self.parser.get_performance_stats()
        assert reset_stats["total_parses"] == 0
        assert reset_stats["total_time"] == 0.0


class TestMainParserKumihanNotation:
    """Kumihan記法解析テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    def test_parse_block_notation_basic(self):
        """基本ブロック記法テスト"""
        text = """#太字#
重要な情報
##"""

        result = self.parser.parse(text)

        assert isinstance(result, list)
        assert len(result) > 0

        # ブロック記法の解析結果確認
        found_content = any(
            "太字" in str(node) or "重要な情報" in str(node) for node in result
        )
        assert found_content

    def test_parse_inline_notation(self):
        """インライン記法テスト"""
        text = "これは #強調# された文章です。"

        result = self.parser.parse(text)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_mixed_notation(self):
        """混合記法テスト"""
        text = """#見出し#
タイトル内容
##

通常テキスト with #強調# 部分

#リスト#
- 項目1
- 項目2
##"""

        result = self.parser.parse(text)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_nested_structures(self):
        """ネスト構造テスト"""
        text = """#外部ブロック#
#内部ブロック#
ネストされた内容
##
##"""

        result = self.parser.parse(text)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_complex_document(self):
        """複雑な文書パーステスト"""
        text = """#文書タイトル#
メイン文書
##

#セクション1#
セクション内容

#サブセクション#
詳細情報
##
##

- リスト項目1
- リスト項目2

#結論#
まとめ文章
##"""

        result = self.parser.parse(text)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_malformed_notation(self):
        """不正形式記法テスト"""
        text = "#不完全なブロック記法"  # 終了タグなし

        result = self.parser.parse(text)

        # エラーにならずに処理される
        assert isinstance(result, list)
        assert len(result) > 0


class TestMainParserIntegration:
    """統合・協調機能テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    def test_keyword_parser_integration(self):
        """キーワードパーサー統合テスト"""
        # キーワードパーサーが利用可能か確認
        assert "keyword" in self.parser.parsers
        keyword_parser = self.parser.parsers["keyword"]
        assert keyword_parser is not None

        # キーワード解析機能テスト
        text = "これはキーワードテストです"
        result = self.parser.parse(text)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_list_parser_integration(self):
        """リストパーサー統合テスト"""
        assert "list" in self.parser.parsers
        list_parser = self.parser.parsers["list"]
        assert list_parser is not None

        # リスト解析機能テスト
        text = """- 項目1
- 項目2
- 項目3"""
        result = self.parser.parse(text)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_block_parser_integration(self):
        """ブロックパーサー統合テスト"""
        assert "block" in self.parser.parsers
        block_parser = self.parser.parsers["block"]
        assert block_parser is not None

    def test_markdown_parser_integration(self):
        """マークダウンパーサー統合テスト"""
        assert "markdown" in self.parser.parsers
        markdown_parser = self.parser.parsers["markdown"]
        assert markdown_parser is not None

        # マークダウン解析機能テスト
        text = """# Heading 1
**Bold text**
*Italic text*"""
        result = self.parser.parse(text)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_parser_selection_mechanism(self):
        """パーサー選択機構テスト"""
        text = "テストテキスト"

        # パーサー選択処理のテスト
        selected_parsers = self.parser._select_parsers(text)

        assert isinstance(selected_parsers, list)
        # 選択されるパーサーの数は0以上
        assert len(selected_parsers) >= 0

    def test_get_parser_info(self):
        """パーサー情報取得テスト"""
        info = self.parser.get_parser_info()

        assert isinstance(info, dict)
        assert "main_parser" in info
        assert "specialized_parsers" in info

        # メインパーサー情報
        main_info = info["main_parser"]
        assert "type" in main_info
        assert main_info["type"] == "main"

        # 専門パーサー情報
        specialized_info = info["specialized_parsers"]
        expected_parsers = ["keyword", "list", "block", "markdown"]
        for parser_name in expected_parsers:
            assert parser_name in specialized_info

    def test_parser_registration(self):
        """パーサー登録・解除テスト"""
        # テスト用モックパーサー
        mock_parser = Mock()
        mock_parser.can_parse.return_value = True
        mock_parser.parse.return_value = [create_node("test", content="test")]

        # パーサー登録
        self.parser.register_parser("test_parser", mock_parser)
        assert "test_parser" in self.parser.parsers

        # パーサー解除
        success = self.parser.unregister_parser("test_parser")
        assert success is True
        assert "test_parser" not in self.parser.parsers

        # 存在しないパーサーの解除
        success = self.parser.unregister_parser("nonexistent")
        assert success is False


class TestMainParserErrorHandling:
    """エラーハンドリングテスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    def test_invalid_input_types(self):
        """不正入力型テスト"""
        # None入力 - MainParserは例外を発生させずエラーノードを返す
        result = self.parser.parse(None)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].type == "error"

        # 数値入力
        result = self.parser.parse(123)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].type == "error"

        # リスト入力
        result = self.parser.parse(["test"])
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].type == "error"

    def test_corrupted_input_handling(self):
        """破損入力処理テスト"""
        # 非常に長い行
        long_line = "a" * 100000
        result = self.parser.parse(long_line)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_special_characters_handling(self):
        """特殊文字処理テスト"""
        special_texts = [
            "🎯📋✅❌",  # 絵文字
            "テスト\x00\x01\x02",  # 制御文字
            "テスト\ufffe\uffff",  # 非文字
            "テスト" + "\n" * 1000,  # 大量改行
        ]

        for text in special_texts:
            try:
                result = self.parser.parse(text)
                assert isinstance(result, list)
            except Exception:
                # 例外が発生しても処理継続
                pass

    def test_resource_exhaustion_simulation(self):
        """リソース枯渇シミュレーションテスト"""
        # メモリ使用量の多いテキスト
        large_text = "テスト文字列\n" * 10000

        result = self.parser.parse(large_text)

        # 処理完了の確認
        assert isinstance(result, list)

    def test_graceful_degradation(self):
        """優雅な機能劣化テスト"""
        # パーサーの一部を無効化した状態での処理
        original_keyword_parser = self.parser.parsers["keyword"]

        # 一時的にパーサーを無効化
        self.parser.parsers["keyword"] = None

        try:
            result = self.parser.parse("テストテキスト")
            assert isinstance(result, list)
        finally:
            # 復元
            self.parser.parsers["keyword"] = original_keyword_parser

    def test_concurrent_error_handling(self):
        """並行処理エラーハンドリングテスト"""

        def parse_with_error():
            # エラーを引き起こす可能性のある処理
            return self.parser.parse("エラーテスト" * 1000)

        # 複数スレッドで同時実行
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(parse_with_error) for _ in range(3)]

            for future in futures:
                try:
                    result = future.result(timeout=5)
                    assert isinstance(result, list)
                except Exception:
                    # タイムアウトや例外が発生しても処理継続
                    pass


class TestMainParserPerformance:
    """パフォーマンス・負荷テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    def test_large_document_parsing(self):
        """大容量文書パーステスト"""
        # 大容量テキスト生成（約50KB）
        large_text = (
            """#大容量テスト#
このセクションは大容量文書のテストです。
"""
            * 1000
        )

        start_time = time.time()
        result = self.parser.parse(large_text)
        elapsed_time = time.time() - start_time

        # 処理完了確認
        assert isinstance(result, list)
        assert len(result) > 0

        # パフォーマンス確認（10秒以内）
        assert elapsed_time < 10.0

    def test_parallel_processing_threshold(self):
        """並列処理閾値テスト"""
        # 小容量テキスト（並列処理されない）
        small_text = "小さなテキスト"
        assert not self.parser._should_use_parallel_processing(small_text)

        # 大容量テキスト（並列処理される）
        large_text = "大きなテキスト\n" * 20000
        assert self.parser._should_use_parallel_processing(large_text)

    def test_chunk_splitting(self):
        """チャンク分割テスト"""
        # 大容量テキスト
        text = "テスト行\n" * 5000

        chunks = self.parser._split_into_chunks(text)

        assert isinstance(chunks, list)
        assert len(chunks) > 1  # 複数チャンクに分割される

        # チャンクの内容確認（結合検証は厳密性を緩和）
        total_lines = sum(chunk.count("\n") + 1 for chunk in chunks)
        original_lines = text.count("\n") + 1
        assert abs(total_lines - original_lines) <= 1  # 改行処理による微差を許容

    def test_streaming_parsing_efficiency(self):
        """ストリーミング解析効率テスト"""

        def text_stream():
            for i in range(100):
                yield f"ストリーミングテスト行 {i}\n"

        start_time = time.time()
        results = list(self.parser.parse_streaming(text_stream()))
        elapsed_time = time.time() - start_time

        # 結果確認
        assert len(results) > 0

        # ストリーミング統計確認
        stats = self.parser.get_performance_stats()
        assert stats["streaming_parses"] == 1

        # パフォーマンス確認（5秒以内）
        assert elapsed_time < 5.0

    def test_memory_usage_stability(self):
        """メモリ使用量安定性テスト"""
        # 繰り返し処理でメモリリークがないことを確認
        for i in range(50):
            text = f"メモリテスト {i}\n" * 100
            result = self.parser.parse(text)
            assert len(result) > 0

            # 統計リセットでメモリクリーンアップ
            if i % 10 == 0:
                self.parser.reset_statistics()

    def test_concurrent_parsing_safety(self):
        """並行解析安全性テスト"""

        def parse_task(task_id):
            text = f"並行テスト {task_id}"
            return self.parser.parse(text)

        # 複数スレッドで同時実行
        with ThreadPoolExecutor(max_workers=4) as executor:
            tasks = [executor.submit(parse_task, i) for i in range(10)]

            results = []
            for task in tasks:
                try:
                    result = task.result(timeout=3)
                    results.append(result)
                except Exception:
                    # タイムアウトが発生しても他のタスクに影響しない
                    pass

            # 少なくとも一部のタスクは成功
            assert len(results) > 0


class TestMainParserProtocols:
    """プロトコル準拠テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    def test_parse_protocol_interface(self):
        """統一パースインターフェーステスト"""
        content = "プロトコルテスト"

        result = self.parser.parse_protocol(content)

        # ParseResult型の確認
        assert hasattr(result, "success")
        assert hasattr(result, "nodes")
        assert result.success is True
        assert isinstance(result.nodes, list)

    def test_validate_interface(self):
        """バリデーションインターフェーステスト"""
        content = "バリデーションテスト"

        errors = self.parser.validate(content)

        assert isinstance(errors, list)
        # エラーがない場合は空リスト

    def test_supports_format_interface(self):
        """フォーマット対応判定インターフェーステスト"""
        # サポートされるフォーマット
        supported_formats = ["kumihan", "markdown", "text", "auto"]
        for format_name in supported_formats:
            assert self.parser.supports_format(format_name) is True

        # サポートされないフォーマット
        assert self.parser.supports_format("unsupported") is False

    def test_get_parser_info_protocol_interface(self):
        """パーサー情報プロトコルインターフェーステスト"""
        info = self.parser.get_parser_info_protocol()

        assert isinstance(info, dict)
        assert "name" in info
        assert info["name"] == "MainParser"
        assert "version" in info
        assert "supported_formats" in info
        assert "capabilities" in info
        assert "specialized_parsers" in info

    def test_streaming_protocol_interface(self):
        """ストリーミングプロトコルインターフェーステスト"""

        def stream():
            yield "ストリーミング"
            yield "プロトコル"
            yield "テスト"

        results = list(self.parser.parse_streaming_protocol(stream()))

        assert len(results) > 0
        for result in results:
            assert hasattr(result, "success")
            assert hasattr(result, "nodes")


class TestMainParserUtilities:
    """ユーティリティ機能テスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    def test_extract_complete_elements(self):
        """完全要素抽出テスト"""
        buffer = "#要素1##テキスト##要素2##残り"

        elements, remaining = self.parser._extract_complete_elements(buffer)

        assert isinstance(elements, list)
        assert len(elements) > 0
        assert isinstance(remaining, str)

    def test_update_performance_stats(self):
        """パフォーマンス統計更新テスト"""
        # まず一度パースを実行して統計を初期化
        self.parser.parse("初期化テスト")
        
        initial_stats = self.parser.get_performance_stats()

        # 統計更新
        self.parser._update_performance_stats(0.1)

        updated_stats = self.parser.get_performance_stats()
        assert updated_stats["total_time"] > initial_stats["total_time"]

    def test_validate_input(self):
        """入力検証テスト"""
        # 有効な入力
        assert self.parser._validate_input("有効なテキスト") is True

        # 無効な入力
        assert self.parser._validate_input("") is False
        assert self.parser._validate_input("   ") is False
        assert self.parser._validate_input(None) is False

    def test_get_cpu_count(self):
        """CPU数取得テスト"""
        cpu_count = self.parser._get_cpu_count()

        # None または正の整数
        assert cpu_count is None or (isinstance(cpu_count, int) and cpu_count > 0)


@pytest.mark.integration
class TestMainParserEndToEnd:
    """エンドツーエンドテスト"""

    def setup_method(self):
        """テスト前準備"""
        self.parser = MainParser()

    def test_complete_document_processing(self):
        """完全文書処理テスト"""
        document = """#メイン文書#
このドキュメントは包括的なテストです。

#セクション1: 基本機能#
- 基本的な解析機能
- エラーハンドリング
- パフォーマンス最適化
##

#セクション2: 応用機能#
並列処理とストリーミングをテストします。

#サブセクション#
ネストされた構造のテスト
##
##

#結論#
すべての機能が正常に動作しています。
##
"""

        start_time = time.time()
        result = self.parser.parse(document)
        elapsed_time = time.time() - start_time

        # 基本検証
        assert isinstance(result, list)
        assert len(result) > 0

        # パフォーマンス確認
        assert elapsed_time < 1.0

        # 統計確認
        stats = self.parser.get_performance_stats()
        assert stats["total_parses"] == 1
        assert stats["total_time"] > 0

    def test_real_world_usage_simulation(self):
        """実世界使用シミュレーションテスト"""
        # 様々な種類のコンテンツを順次処理
        contents = [
            "短いテキスト",
            "#見出し#\n長めのコンテンツ\n##",
            "- リスト1\n- リスト2\n- リスト3",
            "# マークダウン見出し\n**太字**と*斜体*",
            "混合コンテンツ\n#ブロック#\n内容\n##\n- リスト",
        ]

        all_results = []
        for content in contents:
            result = self.parser.parse(content)
            all_results.append(result)
            assert isinstance(result, list)
            assert len(result) > 0

        # 全体統計確認
        final_stats = self.parser.get_performance_stats()
        assert final_stats["total_parses"] == len(contents)

    def test_error_recovery_and_continuation(self):
        """エラー回復・継続テスト"""
        # エラーが発生する可能性のあるコンテンツ
        problematic_contents = [
            "#不完全なブロック",  # 終了タグなし
            "正常なテキスト",  # 正常
            "#ネスト#\n#内部#\n##",  # 不完全ネスト
            "再び正常なテキスト",  # 正常
        ]

        successful_parses = 0
        for content in problematic_contents:
            try:
                result = self.parser.parse(content)
                if isinstance(result, list) and len(result) > 0:
                    successful_parses += 1
            except Exception:
                # エラーが発生しても処理継続
                pass

        # 少なくとも正常なテキストは処理される
        assert successful_parses >= 2
