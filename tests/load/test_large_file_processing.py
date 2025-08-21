"""大型ファイル処理の負荷テスト

大規模データの処理能力とメモリ効率を検証する。
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Tuple

import pytest

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TestLargeFileProcessing:
    """大型ファイル処理テスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.temp_dir = Path(tempfile.mkdtemp())
        os.makedirs("tmp", exist_ok=True)
        self.output_dir = Path("tmp/load_test")
        self.output_dir.mkdir(exist_ok=True)

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        import shutil

        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")

    def generate_large_content(self, size_mb: int) -> str:
        """大型コンテンツを生成"""
        content_parts = []

        # 基本的な記法パターン
        patterns = [
            "# 見出し1 #セクション{}##",
            "## 見出し2 ##サブセクション{}###",
            "# 太字 #重要なテキスト{}##",
            "# イタリック #強調テキスト{}##",
            "- リストアイテム{}",
            "  - ネストされたアイテム{}",
            "通常のテキスト行{}。これはサンプルテキストです。",
            "# 枠線 #枠内のコンテンツ{}##",
        ]

        # 目標サイズに達するまでコンテンツを生成
        line_count = 0
        estimated_bytes = 0
        target_bytes = size_mb * 1024 * 1024

        while estimated_bytes < target_bytes:
            for pattern in patterns:
                line = pattern.format(line_count)
                content_parts.append(line)
                estimated_bytes += len(line.encode("utf-8"))
                line_count += 1

                if estimated_bytes >= target_bytes:
                    break

        return "\n".join(content_parts)

    def process_file(self, file_path: Path) -> Tuple[bool, float, int]:
        """ファイルを処理"""
        start_time = time.time()

        try:
            from kumihan_formatter.cli import main_cli

            # CLIコマンドを実行
            output_path = self.output_dir / f"{file_path.stem}_output.html"

            # 直接パーサーを使用
            from kumihan_formatter.core.parsing.main_parser import MainParser
            from kumihan_formatter.renderer import MainRenderer

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            parser = MainParser()
            parsed = parser.parse(content)

            renderer = MainRenderer()
            html = renderer.render(parsed)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

            elapsed = time.time() - start_time
            output_size = output_path.stat().st_size

            return True, elapsed, output_size

        except Exception as e:
            logger.error(f"ファイル処理エラー: {e}")
            elapsed = time.time() - start_time
            return False, elapsed, 0

    def test_小型ファイル処理_1MB(self) -> None:
        """1MBファイルの処理"""
        # テストファイル生成
        content = self.generate_large_content(1)
        test_file = self.temp_dir / "test_1mb.txt"
        test_file.write_text(content, encoding="utf-8")

        # 処理実行
        success, elapsed, output_size = self.process_file(test_file)

        # 検証
        assert success, "ファイル処理に失敗しました"
        assert elapsed < 5.0, f"処理時間が遅すぎます: {elapsed:.2f}秒"
        assert output_size > 0, "出力ファイルが空です"

        logger.info(f"1MBファイル処理: {elapsed:.2f}秒, 出力: {output_size/1024:.1f}KB")

    def test_中型ファイル処理_5MB(self) -> None:
        """5MBファイルの処理"""
        # テストファイル生成
        content = self.generate_large_content(5)
        test_file = self.temp_dir / "test_5mb.txt"
        test_file.write_text(content, encoding="utf-8")

        # 処理実行
        success, elapsed, output_size = self.process_file(test_file)

        # 検証
        assert success, "ファイル処理に失敗しました"
        assert elapsed < 30.0, f"処理時間が遅すぎます: {elapsed:.2f}秒"
        assert output_size > 0, "出力ファイルが空です"

        logger.info(
            f"5MBファイル処理: {elapsed:.2f}秒, 出力: {output_size/1024/1024:.1f}MB"
        )

    @pytest.mark.slow
    def test_大型ファイル処理_10MB(self) -> None:
        """10MBファイルの処理（遅いテスト）"""
        # テストファイル生成
        content = self.generate_large_content(10)
        test_file = self.temp_dir / "test_10mb.txt"
        test_file.write_text(content, encoding="utf-8")

        # 処理実行
        success, elapsed, output_size = self.process_file(test_file)

        # 検証
        assert success, "ファイル処理に失敗しました"
        assert elapsed < 60.0, f"処理時間が遅すぎます: {elapsed:.2f}秒"
        assert output_size > 0, "出力ファイルが空です"

        # メモリ効率の確認
        input_size = test_file.stat().st_size
        ratio = output_size / input_size

        logger.info(
            f"10MBファイル処理: {elapsed:.2f}秒, "
            f"入力: {input_size/1024/1024:.1f}MB, "
            f"出力: {output_size/1024/1024:.1f}MB, "
            f"比率: {ratio:.2f}"
        )

    def test_メモリ効率性(self) -> None:
        """メモリ効率性のテスト"""
        import tracemalloc

        # 5MBのファイルを準備
        content = self.generate_large_content(5)
        test_file = self.temp_dir / "test_memory.txt"
        test_file.write_text(content, encoding="utf-8")

        # メモリ追跡開始
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # 処理実行
        success, elapsed, output_size = self.process_file(test_file)

        # メモリ使用量確認
        snapshot2 = tracemalloc.take_snapshot()
        top_stats = snapshot2.compare_to(snapshot1, "lineno")

        # 最大メモリ使用量を計算
        total_memory = sum(stat.size for stat in snapshot2.statistics("lineno"))
        peak_memory = tracemalloc.get_traced_memory()[1]

        tracemalloc.stop()

        # 検証
        assert success, "ファイル処理に失敗しました"

        # メモリ使用量がファイルサイズの10倍を超えないこと
        file_size = test_file.stat().st_size
        assert peak_memory < file_size * 10, (
            f"メモリ使用量が多すぎます: "
            f"{peak_memory/1024/1024:.1f}MB "
            f"(ファイルサイズ: {file_size/1024/1024:.1f}MB)"
        )

        logger.info(
            f"メモリ効率: ピーク {peak_memory/1024/1024:.1f}MB, "
            f"ファイル {file_size/1024/1024:.1f}MB"
        )
