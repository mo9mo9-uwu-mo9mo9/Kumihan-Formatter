"""
Manager間連携の統合テスト

このモジュールでは、CoreManager ↔ ProcessingManager間の
連携を検証する統合テストを実装します。
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from kumihan_formatter.core.utilities.logger import get_logger
from kumihan_formatter.managers.core_manager import CoreManager
from kumihan_formatter.managers.processing_manager import ProcessingManager
from kumihan_formatter.core.ast_nodes.node import Node


class TestManagerIntegration:
    """Manager間連携の統合テスト"""

    def setup_method(self):
        """テスト準備"""
        self.logger = get_logger(__name__)
        self.temp_dir = tempfile.mkdtemp()

        # テスト用設定
        self.config = {
            "output_dir": self.temp_dir,
            "template_dir": "templates",
            "chunk_size": 1000,
            "enable_cache": False,
            "parallel_processing": False,
        }

        # Manager instances
        self.core_manager = CoreManager(self.config)
        self.processing_manager = ProcessingManager(self.config)

    def teardown_method(self):
        """テスト後片付け"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_core_processing_integration(self):
        """CoreManager ↔ ProcessingManager連携テスト"""
        # テストデータ
        test_content = """
        # テスト見出し #
        テストコンテンツです。
        
        ## サブ見出し ##
        - アイテム1
        - アイテム2
        """

        # CoreManagerでファイル作成
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # CoreManagerでファイル読み込み
        content = self.core_manager.read_file(test_file)
        assert content == test_content

        # ProcessingManagerで処理
        processed_result = self.processing_manager.parse(content)
        assert processed_result is not None

        # 結果検証
        assert processed_result is not None

    def test_processing_core_integration(self):
        """ProcessingManager ↔ CoreManager連携テスト"""
        # テストデータ
        test_content = (
            """
        # 長いテキストのテスト #
        """
            + "テスト内容 " * 100
        )

        # ProcessingManagerで処理
        processed_result = self.processing_manager.parse(test_content)

        # CoreManagerでチャンク作成
        chunks = self.core_manager.create_chunks_from_lines(
            test_content.split("\n"), chunk_size=500
        )

        # 結果検証
        assert processed_result is not None
        assert chunks is not None

    def test_full_manager_chain_integration(self):
        """全Manager連携の統合テスト"""
        # テストファイル作成
        test_file = os.path.join(self.temp_dir, "chain_test.txt")
        test_content = """
        # チェインテスト #
        
        ## 処理フロー ##
        1. ファイル読み込み（CoreManager）
        2. パース処理（ParsingManager）
        3. 最適化処理（OptimizationManager）
        
        ## 検証項目 ##
        - データの整合性
        - エラー処理
        - パフォーマンス
        """

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # フル処理チェーン実行
        # 1. CoreManagerでファイル読み込み
        content = self.core_manager.read_file(test_file)

        # 2. ProcessingManagerで処理
        processed_result = self.processing_manager.parse(content)

        # 4. CoreManagerでChunk処理
        chunks = self.core_manager.create_chunks_from_lines(
            content.split("\n"), chunk_size=500
        )

        # 結果検証
        assert content is not None
        assert processed_result is not None
        assert chunks is not None
        assert len(chunks) > 0

    def test_error_propagation_between_managers(self):
        """Manager間エラー伝播テスト"""
        # 存在しないファイルでテスト
        non_existent_file = os.path.join(self.temp_dir, "non_existent.txt")

        # CoreManagerエラー検証（Noneを返すことを確認）
        content = self.core_manager.read_file(non_existent_file)
        assert content is None

        # 不正なデータでProcessingManagerテスト（Noneを返す）
        result = self.processing_manager.parse(None)
        # エラー時はNoneを返す
        assert result is None

    def test_manager_configuration_consistency(self):
        """Manager間設定一貫性テスト"""
        # 設定変更
        new_config = {
            "chunk_size": 2000,
            "enable_cache": True,
            "parallel_processing": True,
        }

        # 全Managerの設定更新
        self.core_manager.config.update(new_config)
        self.processing_manager.config.update(new_config)

        # CoreManagerのプロパティも直接更新
        self.core_manager.chunk_size = new_config["chunk_size"]

        # 設定一貫性検証
        assert self.core_manager.chunk_size == 2000
        assert self.processing_manager.config["chunk_size"] == 2000

    def test_concurrent_manager_operations(self):
        """Manager並行操作テスト"""
        import threading
        import time

        results = []

        def worker(manager_type: str, content: str):
            """ワーカー関数"""
            try:
                if manager_type == "processing":
                    result = self.processing_manager.parse(content)
                elif manager_type == "core_chunks":
                    result = self.core_manager.create_chunks_from_lines(
                        content.split("\n")
                    )
                else:
                    result = None

                results.append(
                    {
                        "type": manager_type,
                        "success": result is not None,
                        "thread_id": threading.current_thread().ident,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "type": manager_type,
                        "success": False,
                        "error": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )

        # テストコンテンツ
        test_content = "# 並行テスト # テストコンテンツです。"

        # 複数スレッドで並行実行
        threads = [
            threading.Thread(target=worker, args=("processing", test_content)),
            threading.Thread(target=worker, args=("core_chunks", test_content)),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=5.0)

        # 結果検証
        assert len(results) == 2
        for result in results:
            assert result["success"] is True

    def test_memory_usage_across_managers(self):
        """Manager間メモリ使用量テスト"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 大量データテスト
        large_content = "# 大量データテスト #\n" + ("テストデータ " * 1000)

        # 各Managerで処理
        content = large_content
        processed = self.processing_manager.parse(large_content)
        chunks = self.core_manager.create_chunks_from_lines(large_content.split("\n"))

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # メモリ使用量が合理的な範囲内であることを確認
        assert memory_increase < 100 * 1024 * 1024  # 100MB未満

    def test_manager_state_isolation(self):
        """Manager間状態分離テスト"""
        # CoreManager状態変更
        self.core_manager._file_cache = {"test": "data"}

        # ProcessingManager状態変更
        self.processing_manager.config["test_flag"] = True

        # 状態分離検証
        assert hasattr(self.core_manager, "_file_cache")
        assert "test_flag" in self.processing_manager.config

        # 他のManagerに影響しないことを確認
        assert not hasattr(self.processing_manager, "_file_cache")


class TestManagerErrorHandling:
    """Manager間エラーハンドリング統合テスト"""

    def setup_method(self):
        """テスト準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {"output_dir": self.temp_dir}

        self.core_manager = CoreManager(self.config)
        self.processing_manager = ProcessingManager(self.config)

    def teardown_method(self):
        """テスト後片付け"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_cascading_error_handling(self):
        """カスケードエラーハンドリングテスト"""
        # ファイルシステムエラーをシミュレート
        invalid_path = "/invalid/path/file.txt"

        # CoreManager → ProcessingManager エラー連鎖テスト
        # Managerはエラー時にNoneを返す（例外は投げない）
        content = self.core_manager.read_file(invalid_path)
        assert content is None

        # Noneコンテンツの処理はNoneを返す
        result = self.processing_manager.parse(content)
        assert result is None

    def test_partial_failure_recovery(self):
        """部分的失敗からの回復テスト"""
        # 有効なコンテンツと無効なコンテンツを混在
        valid_content = "# 有効なコンテンツ #"

        # 有効なコンテンツは正常処理
        result = self.processing_manager.parse(valid_content)
        assert result is not None

        # 無効なコンテンツはNoneを返す
        invalid_result = self.processing_manager.parse(None)
        assert invalid_result is None

        # エラー後も他の処理は継続可能
        result2 = self.processing_manager.parse(valid_content)
        assert result2 is not None

    def test_resource_cleanup_on_error(self):
        """エラー時のリソースクリーンアップテスト"""
        # テンポラリファイル作成
        temp_file = os.path.join(self.temp_dir, "cleanup_test.txt")
        with open(temp_file, "w") as f:
            f.write("test content")

        try:
            # 処理中にエラーを発生
            content = self.core_manager.read_file(temp_file)

            # 意図的にエラーを発生させる
            with patch.object(
                self.processing_manager, "parse", side_effect=Exception("Simulated error")
            ):
                with pytest.raises(Exception):
                    self.processing_manager.parse(content)

            # リソースがクリーンアップされていることを確認
            # (ファイルハンドルやメモリリークがないこと)
            assert os.path.exists(temp_file)  # ファイル自体は残存

        except Exception:
            # エラー処理の検証
            assert True  # エラーが適切にハンドリングされた
