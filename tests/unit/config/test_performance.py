"""設定システムパフォーマンステスト - Issue #929 Phase 3E

実際のConfigManager APIに対応したパフォーマンステスト
10テストケースで設定システムの性能を確認
"""

import gc
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from kumihan_formatter.config.config_manager import ConfigManager
from kumihan_formatter.config.extended_config import ExtendedConfig


class TestConfigPerformance:
    """設定システムパフォーマンステスト（10ケース）"""

    def test_性能_大規模設定ファイル読み込み_1000項目以内1秒(self):
        """大規模設定ファイル読み込み性能テスト"""
        # Given: 1000項目の大規模設定ファイル作成
        large_config = {f"key_{i}": f"value_{i}" for i in range(1000)}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json

            json.dump(large_config, f)
            config_path = f.name

        try:
            # When: ファイル読み込み時間計測
            start_time = time.time()
            manager = ConfigManager(config_path=config_path)
            manager.load_config(config_path)
            end_time = time.time()

            # Then: 1秒以内で完了
            elapsed = end_time - start_time
            assert (
                elapsed < 1.0
            ), f"大規模ファイル読み込みが{elapsed:.3f}秒かかりました（目標: 1秒以内）"
        finally:
            os.unlink(config_path)

    def test_性能_大量マーカー管理_100個処理0_5秒以内(self):
        """大量マーカー管理の性能テスト"""
        # Given
        manager = ConfigManager(config_type="extended")

        # When: 100個のマーカー追加時間計測
        start_time = time.time()
        for i in range(100):
            manager.add_marker(f"marker_{i}", {"tag": "div", "class": f"marker-{i}"})
        end_time = time.time()

        # Then: 0.5秒以内で完了
        elapsed = end_time - start_time
        assert elapsed < 0.5, f"100個マーカー追加が{elapsed:.3f}秒かかりました（目標: 0.5秒以内）"

        # 取得性能も確認
        start_time = time.time()
        markers = manager.get_markers()
        end_time = time.time()

        elapsed = end_time - start_time
        assert len(markers) >= 100
        assert elapsed < 0.1, f"マーカー取得が{elapsed:.3f}秒かかりました（目標: 0.1秒以内）"

    def test_性能_大量テーマ管理_50個処理0_3秒以内(self):
        """大量テーマ管理の性能テスト"""
        # Given
        manager = ConfigManager(config_type="extended")

        # When: 50個のテーマ追加時間計測
        start_time = time.time()
        for i in range(50):
            manager.add_theme(
                f"theme_{i}",
                {
                    "name": f"テーマ{i}",
                    "css": {"background_color": f"#{i:06x}", "text_color": "#000000"},
                },
            )
        end_time = time.time()

        # Then: 0.3秒以内で完了
        elapsed = end_time - start_time
        assert elapsed < 0.3, f"50個テーマ追加が{elapsed:.3f}秒かかりました（目標: 0.3秒以内）"

        # テーマ取得性能も確認
        start_time = time.time()
        themes = manager.get_themes()
        end_time = time.time()

        elapsed = end_time - start_time
        assert len(themes) >= 50
        assert elapsed < 0.1, f"テーマ取得が{elapsed:.3f}秒かかりました（目標: 0.1秒以内）"

    def test_性能_繰り返し設定更新_1000回1秒以内(self):
        """繰り返し設定更新の性能テスト"""
        # Given
        manager = ConfigManager()

        # When: 1000回の設定更新時間計測
        start_time = time.time()
        for i in range(1000):
            manager.set(f"key_{i % 100}", f"value_{i}")  # 100キーを循環使用
        end_time = time.time()

        # Then: 1秒以内で完了
        elapsed = end_time - start_time
        assert elapsed < 1.0, f"1000回設定更新が{elapsed:.3f}秒かかりました（目標: 1秒以内）"

    def test_性能_深いネスト構造マージ_10階層0_2秒以内(self):
        """深いネスト構造マージの性能テスト"""

        # Given: 10階層のネスト構造作成
        def create_nested_dict(depth):
            if depth == 0:
                return f"value_depth_{depth}"
            return {f"level_{depth}": create_nested_dict(depth - 1)}

        nested_config = create_nested_dict(10)
        manager = ConfigManager()

        # When: ネスト構造マージ時間計測
        start_time = time.time()
        manager.merge_config(nested_config)
        end_time = time.time()

        # Then: 0.2秒以内で完了
        elapsed = end_time - start_time
        assert elapsed < 0.2, f"10階層ネストマージが{elapsed:.3f}秒かかりました（目標: 0.2秒以内）"

    @patch.dict("os.environ", {f"KUMIHAN_CSS_VAR_{i}": f"value_{i}" for i in range(100)})
    def test_性能_環境変数大量読み込み_100変数0_1秒以内(self):
        """環境変数大量読み込みの性能テスト"""
        # Given: 100個の環境変数（patch.dictで設定済み）

        # When: 環境変数読み込み時間計測
        start_time = time.time()
        manager = ConfigManager(config_type="extended")
        end_time = time.time()

        # Then: 0.1秒以内で完了
        elapsed = end_time - start_time
        assert (
            elapsed < 0.1
        ), f"100個環境変数読み込みが{elapsed:.3f}秒かかりました（目標: 0.1秒以内）"

    def test_性能_to_dict変換_大規模データ0_1秒以内(self):
        """to_dict変換の性能テスト"""
        # Given: 大規模データを持つConfigManager
        manager = ConfigManager(config_type="extended")

        # 大量データ設定
        for i in range(500):
            manager.set(f"data_{i}", {"nested": {"value": f"test_{i}"}})

        # When: to_dict変換時間計測
        start_time = time.time()
        config_dict = manager.to_dict()
        end_time = time.time()

        # Then: 0.1秒以内で完了
        elapsed = end_time - start_time
        assert (
            elapsed < 0.1
        ), f"大規模データto_dict変換が{elapsed:.3f}秒かかりました（目標: 0.1秒以内）"
        assert isinstance(config_dict, dict)

    def test_性能_validate実行_複雑設定0_05秒以内(self):
        """validate実行の性能テスト"""
        # Given: 複雑な設定を持つConfigManager
        manager = ConfigManager(config_type="extended")

        # 複雑な設定を追加
        for i in range(100):
            manager.add_marker(f"marker_{i}", {"tag": "div", "attributes": {"class": f"test-{i}"}})
            manager.add_theme(f"theme_{i}", {"name": f"テーマ{i}", "css": {"color": f"#{i:06x}"}})

        # When: validate実行時間計測
        start_time = time.time()
        is_valid = manager.validate()
        end_time = time.time()

        # Then: 0.05秒以内で完了
        elapsed = end_time - start_time
        assert (
            elapsed < 0.05
        ), f"複雑設定validate実行が{elapsed:.3f}秒かかりました（目標: 0.05秒以内）"
        assert isinstance(is_valid, bool)

    def test_性能_メモリ使用量_適正範囲内(self):
        """メモリ使用量の性能テスト"""
        # Given: メモリ使用量測定開始
        gc.collect()  # ガベージコレクション実行

        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # When: 大量データ操作
        manager = ConfigManager(config_type="extended")

        # 大量のマーカーとテーマを追加
        for i in range(200):
            manager.add_marker(f"memory_marker_{i}", {"tag": "div"})
            manager.add_theme(f"memory_theme_{i}", {"name": f"テーマ{i}", "css": {}})

        # 大量の設定値を追加
        for i in range(500):
            manager.set(f"memory_key_{i}", f"memory_value_{i}")

        gc.collect()  # ガベージコレクション実行
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Then: メモリ増加量が適正範囲内（50MB以下）
        memory_increase = final_memory - initial_memory
        assert (
            memory_increase < 50
        ), f"メモリ使用量が{memory_increase:.2f}MB増加しました（目標: 50MB以下）"

    def test_性能_並行アクセス_競合状態なし(self):
        """並行アクセス時の性能と安全性テスト"""
        # Given
        manager = ConfigManager(config_type="extended")
        errors = []
        results = {}

        def worker(worker_id):
            """ワーカー関数"""
            try:
                # 並行してマーカー追加
                manager.add_marker(f"concurrent_marker_{worker_id}", {"tag": "div"})

                # 並行して設定値更新
                manager.set(f"concurrent_key_{worker_id}", f"value_{worker_id}")

                # 並行して取得
                value = manager.get(f"concurrent_key_{worker_id}")
                results[worker_id] = value

            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")

        # When: 10個のワーカーで並行アクセス
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            for future in futures:
                future.result()  # 全ワーカーの完了を待機
        end_time = time.time()

        # Then: エラーなく完了し、性能も良好
        elapsed = end_time - start_time
        assert len(errors) == 0, f"並行アクセス中にエラー発生: {errors}"
        assert elapsed < 1.0, f"並行アクセスが{elapsed:.3f}秒かかりました（目標: 1秒以内）"
        assert len(results) == 10, f"期待される結果数: 10, 実際: {len(results)}"
