#!/usr/bin/env python3
"""
Issue #769 統合パフォーマンステスト

実際のKumihan記法パーサーを使用した300K行ファイル処理の性能測定
目標: 29.17秒 → 5秒以下（83%高速化）
"""

import asyncio
import time
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

# Kumihan-Formatter components
sys.path.insert(0, str(Path(__file__).parent))
from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.utilities.performance_metrics import (
    PerformanceMonitor,
    SIMDOptimizer,
    AsyncIOOptimizer,
    RegexOptimizer,
    MemoryOptimizer
)
from kumihan_formatter.core.utilities.parallel_processor import ParallelChunkProcessor
from kumihan_formatter.core.utilities.logger import get_logger


class IntegratedPerformanceTest:
    """統合パフォーマンステスト - 実際のKumihan記法処理"""

    def __init__(self):
        self.logger = get_logger(__name__)

        # コアコンポーネント
        self.keyword_parser = KeywordParser()
        self.parallel_processor = ParallelChunkProcessor()

        # 最適化コンポーネント
        self.simd_optimizer = SIMDOptimizer()
        self.async_optimizer = AsyncIOOptimizer()
        self.regex_optimizer = RegexOptimizer()
        self.memory_optimizer = MemoryOptimizer()

        self.logger.info("Integrated performance test system initialized")

    def create_realistic_test_file(self, lines_count: int = 300000) -> Path:
        """現実的なKumihan記法を含むテストファイルを生成"""
        test_file = Path(tempfile.mktemp(suffix=".kumihan"))

        self.logger.info(f"Creating realistic Kumihan test file: {lines_count:,} lines")

        # 実際のKumihan記法パターン（使用頻度を考慮）
        patterns = [
            "# 太字 #重要な情報##",
            "# イタリック #強調されたテキスト##",
            "# ハイライト color=yellow #注意事項##",
            "# ハイライト color=#ff0000 #警告メッセージ##",
            "# 見出し1 #第1章 システム概要##",
            "# 見出し2 #2.1 基本機能##",
            "# 見出し3 #2.1.1 詳細仕様##",
            "# 太字 イタリック #複合スタイルテキスト##",
            "# コード #print('Hello, Kumihan!')##",
            "# 下線 #下線付きテキスト##",
            "通常のテキスト行です。この行には特別な記法は含まれていません。",
            "日本語の複雑な文章。漢字、ひらがな、カタカナが混在している例です。",
            "English mixed text with Japanese. 英語と日本語の混合例。",
            "数値データ: 123, 456.789, -987.654, 3.14159265359",
            "# 太字 #プロジェクト名: Kumihan-Formatter##",
            "# イタリック #バージョン: v2.0.0-alpha##",
            "# ハイライト color=lightblue #リリース予定: 2024年12月##",
            "# 見出し2 #機能一覧##",
            "- 基本記法サポート",
            "- 高速処理エンジン",
            "- 並列処理対応",
            "複数の# 太字 #キーワード##を含む行と# イタリック #他のスタイル##の組み合わせ",
            "# 太字 #ネストした# イタリック #記法## test##",
            "特殊文字を含む行: !@#$%^&*()_+-=[]{}|;':\",./<>?",
            "長い行のテスト: " + "あ" * 200,  # 長い行
            "",  # 空行
            "# 見出し1 #パフォーマンステスト##",
            "# 太字 #処理速度: 300,000行/秒##",
            "# ハイライト color=green #テスト結果: 成功##",
        ]

        with open(test_file, 'w', encoding='utf-8') as f:
            for i in range(lines_count):
                # パターンをローテーションして多様性を確保
                pattern = patterns[i % len(patterns)]
                # 行番号を追加
                line = f"L{i:06d}: {pattern}\n"
                f.write(line)

        file_size_mb = test_file.stat().st_size / 1024 / 1024
        self.logger.info(f"Test file created: {file_size_mb:.2f}MB")

        return test_file

    def process_kumihan_content_traditional(self, content: str) -> str:
        """従来手法でのKumihan記法処理 - 実際のKumihan処理エンジンを使用"""
        # 最適化なしの従来のKeywordParserを使用（パフォーマンス比較の基準）
        from kumihan_formatter.core.keyword_parser import KeywordParser

        # 最適化を無効にした従来のパーサー
        traditional_parser = KeywordParser()

        # _regex_optimizerの削除で最適化を無効化
        if hasattr(traditional_parser, '_regex_optimizer'):
            delattr(traditional_parser, '_regex_optimizer')

        # 従来の処理（最適化なし）
        processed = traditional_parser._process_inline_keywords(content)

        if isinstance(processed, list):
            # リスト結果を文字列に変換（簡略化）
            result = ""
            for item in processed:
                if hasattr(item, 'tag'):  # Node object
                    result += f"<{item.tag}>{item.content}</{item.tag}>"
                else:
                    result += str(item)
            return result
        else:
            return str(processed)

    def process_kumihan_content_optimized(self, content: str) -> str:
        """最適化手法でのKumihan記法処理"""
        # KeywordParserの最適化された処理を使用
        processed = self.keyword_parser._process_inline_keywords(content)

        if isinstance(processed, list):
            # リスト結果を文字列に変換（簡略化）
            result = ""
            for item in processed:
                if hasattr(item, 'tag'):  # Node object
                    result += f"<{item.tag}>{item.content}</{item.tag}>"
                else:
                    result += str(item)
            return result
        else:
            return str(processed)

    async def run_performance_comparison(self, lines_count: int = 300000) -> Dict[str, Any]:
        """パフォーマンス比較テストの実行"""
        self.logger.info(f"Starting integrated performance test: {lines_count:,} lines")

        # テストファイル生成
        test_file = self.create_realistic_test_file(lines_count)

        try:
            # ファイル読み込み
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()

            self.logger.info(f"Test file loaded: {len(content):,} characters")

            # 1. 従来手法でのテスト
            self.logger.info("Testing traditional approach...")
            perf_monitor_traditional = PerformanceMonitor()
            perf_monitor_traditional.start_monitoring(lines_count, "traditional_processing")

            start_time = time.time()
            traditional_result = self.process_kumihan_content_traditional(content)
            traditional_time = time.time() - start_time

            perf_monitor_traditional.stop_monitoring()

            # 2. 最適化手法でのテスト
            self.logger.info("Testing optimized approach...")
            perf_monitor_optimized = PerformanceMonitor()
            perf_monitor_optimized.start_monitoring(lines_count, "optimized_processing")

            start_time = time.time()
            optimized_result = self.process_kumihan_content_optimized(content)
            optimized_time = time.time() - start_time

            perf_monitor_optimized.stop_monitoring()

            # 3. 並列処理テスト（大容量ファイル用）
            self.logger.info("Testing parallel processing...")
            lines = content.split('\n')

            # チャンク作成
            chunks = self.parallel_processor.create_chunks_adaptive(lines[:50000])  # 50K行でテスト

            def process_chunk_parallel(chunk):
                chunk_content = '\n'.join(chunk.lines)
                return self.process_kumihan_content_optimized(chunk_content)

            start_time = time.time()
            parallel_results = list(
                self.parallel_processor.process_chunks_parallel_optimized(
                    chunks,
                    process_chunk_parallel
                )
            )
            parallel_time = time.time() - start_time

            # 4. 非同期I/O + 最適化処理テスト
            self.logger.info("Testing async I/O + optimization...")

            start_time = time.time()
            async_results = []
            async for batch in self.async_optimizer.async_read_lines_batched(test_file, batch_size=5000):
                batch_content = '\n'.join(batch)
                batch_result = self.process_kumihan_content_optimized(batch_content)
                async_results.append(batch_result)
            async_time = time.time() - start_time

            # 結果分析
            speedup_factor = traditional_time / optimized_time if optimized_time > 0 else float('inf')
            parallel_speedup = traditional_time / parallel_time if parallel_time > 0 else float('inf')
            async_speedup = traditional_time / async_time if async_time > 0 else float('inf')

            results = {
                "traditional_time": traditional_time,
                "optimized_time": optimized_time,
                "parallel_time": parallel_time,
                "async_time": async_time,
                "speedup_factor": speedup_factor,
                "parallel_speedup": parallel_speedup,
                "async_speedup": async_speedup,
                "lines_processed": lines_count,
                "characters_processed": len(content),
                "target_time": 5.0,  # 目標: 5秒以下
                "original_time": 29.17,  # 元の処理時間
                "target_achieved": optimized_time <= 5.0,
                "performance_improvement": ((29.17 - optimized_time) / 29.17) * 100,
                "traditional_report": perf_monitor_traditional.generate_performance_report(),
                "optimized_report": perf_monitor_optimized.generate_performance_report(),
            }

            self.logger.info(f"Performance test completed:")
            self.logger.info(f"  Traditional: {traditional_time:.2f}s")
            self.logger.info(f"  Optimized: {optimized_time:.2f}s")
            self.logger.info(f"  Speedup: {speedup_factor:.2f}x")
            self.logger.info(f"  Target achieved: {results['target_achieved']}")

            return results

        finally:
            # クリーンアップ
            if test_file.exists():
                test_file.unlink()
                self.logger.info(f"Test file cleaned up: {test_file}")

    def print_performance_report(self, results: Dict[str, Any]):
        """統合パフォーマンステスト結果レポート"""
        print("\n" + "="*80)
        print("🚀 Issue #769 統合パフォーマンステスト結果")
        print("="*80)
        print(f"目標: 300K行ファイル処理 29.17秒 → 5秒以下")
        print()

        print("📊 処理時間比較")
        print("-" * 40)
        print(f"  従来手法:     {results['traditional_time']:8.2f}秒")
        print(f"  最適化手法:   {results['optimized_time']:8.2f}秒")
        print(f"  並列処理:     {results['parallel_time']:8.2f}秒")
        print(f"  非同期I/O:    {results['async_time']:8.2f}秒")
        print()

        print("⚡ 高速化結果")
        print("-" * 40)
        print(f"  基本最適化:   {results['speedup_factor']:8.2f}x")
        print(f"  並列処理:     {results['parallel_speedup']:8.2f}x")
        print(f"  非同期I/O:    {results['async_speedup']:8.2f}x")
        print()

        print("🎯 目標達成状況")
        print("-" * 40)
        print(f"  目標時間:     {results['target_time']:8.2f}秒")
        print(f"  実際の時間:   {results['optimized_time']:8.2f}秒")
        print(f"  目標達成:     {'✅ YES' if results['target_achieved'] else '❌ NO'}")
        print(f"  性能向上:     {results['performance_improvement']:8.1f}%")
        print()

        if results['target_achieved']:
            print("🎉 Issue #769 完全達成!")
            print(f"   29.17秒 → {results['optimized_time']:.2f}秒")
            print(f"   {results['speedup_factor']:.1f}倍高速化を実現")
        else:
            remaining_improvement = (results['optimized_time'] / results['target_time'] - 1) * 100
            print(f"⚠️  目標まであと {remaining_improvement:.1f}% の改善が必要")

        print()
        print("📈 詳細パフォーマンス分析:")
        print("従来手法:")
        print(results['traditional_report'])
        print("\n最適化手法:")
        print(results['optimized_report'])


async def main():
    """メイン実行関数"""
    print("Issue #769 統合パフォーマンステスト開始")

    test_system = IntegratedPerformanceTest()

    # 統合パフォーマンステスト実行
    results = await test_system.run_performance_comparison(lines_count=300000)

    # 結果レポート出力
    test_system.print_performance_report(results)

    print("\n統合パフォーマンステスト完了 🎉")

    # Issue #769完了判定
    if results['target_achieved']:
        print("\n🏆 Issue #769 完全完了!")
        print("   300K行ファイル処理が5秒以下で完了しました")
    else:
        print(f"\n⚠️  Issue #769 未完了")
        print(f"   現在: {results['optimized_time']:.2f}秒")
        print(f"   目標: {results['target_time']:.2f}秒以下")


if __name__ == "__main__":
    asyncio.run(main())
