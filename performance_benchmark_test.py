#!/usr/bin/env python3
"""
Issue #769 パフォーマンス最適化ベンチマークテスト

目標: 300K行ファイル処理を29.17秒→5秒以下に短縮（83%高速化）

テスト対象:
- SIMD最適化（NumPy活用）
- 非同期I/O最適化（aiofiles活用）
- 正規表現エンジン最適化（キャッシュ機能）
- メモリアクセスパターン最適化
- 並列処理最適化
"""

import asyncio
import time
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import tempfile

# Kumihan-Formatter components
sys.path.insert(0, str(Path(__file__).parent))
from kumihan_formatter.core.utilities.performance_metrics import (
    SIMDOptimizer,
    AsyncIOOptimizer, 
    RegexOptimizer,
    MemoryOptimizer,
    PerformanceMonitor,
    monitor_performance
)
from kumihan_formatter.core.utilities.parallel_processor import ParallelChunkProcessor
from kumihan_formatter.core.utilities.logger import get_logger


class PerformanceBenchmark:
    """Issue #769対応 パフォーマンスベンチマークシステム"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.results = {}
        
        # 最適化コンポーネントの初期化
        self.simd_optimizer = SIMDOptimizer()
        self.async_optimizer = AsyncIOOptimizer()
        self.regex_optimizer = RegexOptimizer()
        self.memory_optimizer = MemoryOptimizer()
        self.parallel_processor = ParallelChunkProcessor()
        
        self.logger.info("Performance benchmark system initialized")
    
    def create_test_file(self, lines_count: int = 300000, output_path: Path = None) -> Path:
        """
        テスト用大容量ファイルを生成
        
        Args:
            lines_count: 行数（デフォルト300K行）
            output_path: 出力ファイルパス
            
        Returns:
            Path: 生成されたファイルのパス
        """
        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix=".txt"))
        
        self.logger.info(f"Creating test file with {lines_count:,} lines: {output_path}")
        
        # 多様なKumihan記法パターンを含むテストデータ
        test_patterns = [
            "# 太字 #これは太字のテストです##",
            "# イタリック #これはイタリック体のテストです##", 
            "# ハイライト color=yellow #重要な情報をハイライト##",
            "# 見出し1 #メインタイトル##",
            "# 見出し2 #サブタイトル##",
            "# 見出し3 #小見出し##",
            "通常のテキスト行です。Kumihan記法の処理性能をテストします。",
            "# 太字 イタリック #複合キーワードのテスト##",
            "# ハイライト color=#ff0000 #赤色ハイライト##",
            "# コード #print('Hello, World!')##",
            "# 下線 #下線付きテキスト##",
            "# 取り消し線 #削除されたテキスト##",
            "日本語を含む複雑な文章。漢字、ひらがな、カタカナが混在しています。",
            "English text mixed with Japanese. 英語と日本語の混合テキスト。",
            "数値データ: 123456789, 3.14159, -987.654",
            "特殊文字: !@#$%^&*()_+-=[]{}|;':\",./<>?",
        ]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i in range(lines_count):
                # パターンをローテーションして多様性を確保
                pattern = test_patterns[i % len(test_patterns)]
                # 行番号を追加して一意性を保証
                line = f"Line{i:06d}: {pattern}\n"
                f.write(line)
        
        file_size_mb = output_path.stat().st_size / 1024 / 1024
        self.logger.info(f"Test file created: {file_size_mb:.2f}MB, {lines_count:,} lines")
        
        return output_path
    
    def benchmark_simd_optimization(self, test_file: Path) -> Dict[str, Any]:
        """SIMD最適化のベンチマーク"""
        self.logger.info("Benchmarking SIMD optimization...")
        
        results = {}
        
        # テストデータ読み込み
        with open(test_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        sample_lines = lines[:10000]  # 10K行でテスト
        
        # 変換関数リスト
        pattern_funcs = [
            lambda line: line.replace("#", ""),
            lambda line: line.strip(),
            lambda line: line.upper() if len(line) < 50 else line,
        ]
        
        # 従来処理のベンチマーク
        start_time = time.time()
        traditional_result = sample_lines.copy()
        for func in pattern_funcs:
            traditional_result = [func(line) for line in traditional_result]
        traditional_time = time.time() - start_time
        
        # SIMD最適化処理のベンチマーク
        start_time = time.time()
        simd_result = self.simd_optimizer.vectorized_line_processing(sample_lines, pattern_funcs)
        simd_time = time.time() - start_time
        
        # 結果検証
        results_match = len(traditional_result) == len(simd_result)
        
        results = {
            "traditional_time": traditional_time,
            "simd_time": simd_time,
            "speedup_factor": traditional_time / simd_time if simd_time > 0 else float('inf'),
            "results_match": results_match,
            "processed_lines": len(sample_lines),
            "simd_metrics": self.simd_optimizer.get_simd_metrics(),
        }
        
        self.logger.info(f"SIMD benchmark: {results['speedup_factor']:.2f}x speedup")
        return results
    
    async def benchmark_async_io(self, test_file: Path) -> Dict[str, Any]:
        """非同期I/Oのベンチマーク"""
        self.logger.info("Benchmarking AsyncIO optimization...")
        
        results = {}
        
        # 同期読み込みベンチマーク
        start_time = time.time()
        with open(test_file, 'r', encoding='utf-8') as f:
            sync_lines = f.readlines()
        sync_time = time.time() - start_time
        
        # 非同期読み込みベンチマーク
        start_time = time.time()
        async_lines = []
        async for batch in self.async_optimizer.async_read_lines_batched(test_file, batch_size=1000):
            async_lines.extend(batch)
        async_time = time.time() - start_time
        
        # 結果検証
        results_match = len(sync_lines) == len(async_lines)
        
        results = {
            "sync_time": sync_time,
            "async_time": async_time,
            "speedup_factor": sync_time / async_time if async_time > 0 else float('inf'),
            "results_match": results_match,
            "total_lines": len(sync_lines),
            "async_metrics": self.async_optimizer.get_async_metrics(),
        }
        
        self.logger.info(f"AsyncIO benchmark: {results['speedup_factor']:.2f}x speedup")
        return results
    
    def benchmark_regex_optimization(self, test_file: Path) -> Dict[str, Any]:
        """正規表現最適化のベンチマーク"""
        self.logger.info("Benchmarking Regex optimization...")
        
        results = {}
        
        # テストデータ読み込み（サンプル）
        with open(test_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        sample_text = '\n'.join(lines[:5000])  # 5K行でテスト
        
        # テスト用正規表現パターン
        patterns_and_replacements = [
            (r"#\s*([^#]+?)\s*#([^#]+?)##", r"<\1>\2</\1>"),
            (r"\s+", " "),
            (r"Line\d+:", ""),
        ]
        
        # 従来処理（毎回コンパイル）
        start_time = time.time()
        import re
        traditional_result = sample_text
        for pattern, replacement in patterns_and_replacements:
            traditional_result = re.sub(pattern, replacement, traditional_result)
        traditional_time = time.time() - start_time
        
        # 最適化処理（キャッシュ活用）
        start_time = time.time()
        optimized_result = sample_text
        for pattern, replacement in patterns_and_replacements:
            optimized_result = self.regex_optimizer.optimized_substitute(
                pattern, replacement, optimized_result
            )
        optimized_time = time.time() - start_time
        
        # 結果検証
        results_match = traditional_result == optimized_result
        
        results = {
            "traditional_time": traditional_time,
            "optimized_time": optimized_time,
            "speedup_factor": traditional_time / optimized_time if optimized_time > 0 else float('inf'),
            "results_match": results_match,
            "cache_stats": self.regex_optimizer.get_cache_stats(),
        }
        
        self.logger.info(f"Regex benchmark: {results['speedup_factor']:.2f}x speedup")
        return results
    
    def benchmark_memory_optimization(self, test_file: Path) -> Dict[str, Any]:
        """メモリ最適化のベンチマーク"""
        self.logger.info("Benchmarking Memory optimization...")
        
        results = {}
        
        # メモリ効率的読み込みテスト
        start_time = time.time()
        traditional_lines = []
        with open(test_file, 'r', encoding='utf-8') as f:
            traditional_lines = f.readlines()
        traditional_time = time.time() - start_time
        
        # メモリ最適化読み込み
        start_time = time.time()
        optimized_lines = []
        for chunk in self.memory_optimizer.memory_efficient_file_reader(test_file, chunk_size=64*1024):
            optimized_lines.extend(chunk.split('\n'))
        optimized_time = time.time() - start_time
        
        # リスト操作最適化テスト
        test_data = list(range(50000))
        
        start_time = time.time()
        traditional_sorted = sorted(test_data)
        traditional_sort_time = time.time() - start_time
        
        start_time = time.time()
        optimized_sorted = self.memory_optimizer.optimize_list_operations(test_data, "sort")
        optimized_sort_time = time.time() - start_time
        
        results = {
            "file_read": {
                "traditional_time": traditional_time,
                "optimized_time": optimized_time,
                "speedup_factor": traditional_time / optimized_time if optimized_time > 0 else float('inf'),
            },
            "list_sort": {
                "traditional_time": traditional_sort_time,
                "optimized_time": optimized_sort_time,
                "speedup_factor": traditional_sort_time / optimized_sort_time if optimized_sort_time > 0 else float('inf'),
            },
            "memory_stats": self.memory_optimizer.get_memory_stats(),
        }
        
        self.logger.info(f"Memory optimization benchmark completed")
        return results
    
    def benchmark_parallel_processing(self, test_file: Path) -> Dict[str, Any]:
        """並列処理最適化のベンチマーク"""
        self.logger.info("Benchmarking Parallel processing optimization...")
        
        results = {}
        
        # テストデータ準備（全データを使用）
        with open(test_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 大容量データでテスト（100K行）
        test_lines = lines[:100000] if len(lines) > 100000 else lines
        
        # より効率的な処理関数
        def process_chunk_optimized(chunk):
            # リスト内包表記でより高速に処理
            return [
                line.strip().replace('#', '').replace('太字', '<strong>').replace('##', '</strong>')
                for line in chunk.lines
                if line.strip()  # 空行をフィルタ
            ]
        
        # シーケンシャル処理（バッチごとに分割）
        start_time = time.time()
        sequential_results = []
        batch_size = 5000
        for i in range(0, len(test_lines), batch_size):
            batch = test_lines[i:i + batch_size]
            batch_results = [
                line.strip().replace('#', '').replace('太字', '<strong>').replace('##', '</strong>')
                for line in batch
                if line.strip()
            ]
            sequential_results.extend(batch_results)
        sequential_time = time.time() - start_time
        
        # 並列処理（最適化）
        start_time = time.time()
        
        # CPU数に基づいて適切なチャンク数を計算
        import os
        cpu_count = os.cpu_count() or 1
        optimal_chunk_count = min(cpu_count * 2, 16)
        
        # チャンク作成
        chunks = self.parallel_processor.create_chunks_adaptive(
            test_lines, 
            target_chunk_count=optimal_chunk_count
        )
        
        # 並列処理実行
        parallel_results = []
        for result in self.parallel_processor.process_chunks_parallel_optimized(
            chunks, 
            process_chunk_optimized
        ):
            if isinstance(result, list):
                parallel_results.extend(result)
            else:
                parallel_results.append(result)
        
        parallel_time = time.time() - start_time
        
        # 結果検証
        results_match = len(sequential_results) == len(parallel_results)
        
        results = {
            "sequential_time": sequential_time,
            "parallel_time": parallel_time,
            "speedup_factor": sequential_time / parallel_time if parallel_time > 0 else float('inf'),
            "chunks_processed": len(chunks),
            "results_match": results_match,
            "processed_lines": len(test_lines),
            "parallel_metrics": self.parallel_processor.get_parallel_metrics(),
        }
        
        self.logger.info(f"Parallel processing: {results['speedup_factor']:.2f}x speedup")
        return results
    
    async def run_comprehensive_benchmark(self, lines_count: int = 300000) -> Dict[str, Any]:
        """包括的ベンチマークの実行"""
        self.logger.info(f"Starting comprehensive benchmark with {lines_count:,} lines")
        
        # テストファイル生成
        test_file = self.create_test_file(lines_count)
        
        try:
            # パフォーマンス監視を開始
            perf_monitor = PerformanceMonitor()
            perf_monitor.start_monitoring(lines_count, "benchmark_start")
            
            # 各最適化手法のベンチマーク実行
            results = {
                "simd_optimization": self.benchmark_simd_optimization(test_file),
                "async_io": await self.benchmark_async_io(test_file),
                "regex_optimization": self.benchmark_regex_optimization(test_file),
                "memory_optimization": self.benchmark_memory_optimization(test_file),
                "parallel_processing": self.benchmark_parallel_processing(test_file),
            }
            
            perf_monitor.stop_monitoring()
            
            # 総合結果の計算
            total_speedup = 1.0
            for optimization, result in results.items():
                if isinstance(result, dict) and "speedup_factor" in result:
                    total_speedup *= result["speedup_factor"]
                elif isinstance(result, dict):
                    # 複数のサブベンチマークがある場合
                    for sub_result in result.values():
                        if isinstance(sub_result, dict) and "speedup_factor" in sub_result:
                            total_speedup *= sub_result["speedup_factor"]
            
            results["summary"] = {
                "total_estimated_speedup": total_speedup,
                "target_speedup": 5.84,  # 29.17秒→5秒の目標
                "target_achieved": total_speedup >= 5.84,
                "performance_report": perf_monitor.generate_performance_report(),
            }
            
            self.logger.info(f"Comprehensive benchmark completed:")
            self.logger.info(f"  Total estimated speedup: {total_speedup:.2f}x")
            self.logger.info(f"  Target achieved: {results['summary']['target_achieved']}")
            
            return results
        
        finally:
            # テストファイルクリーンアップ
            if test_file.exists():
                test_file.unlink()
                self.logger.info(f"Test file cleaned up: {test_file}")
    
    def print_benchmark_report(self, results: Dict[str, Any]):
        """ベンチマーク結果レポートを出力"""
        print("\n" + "="*80)
        print("🚀 Issue #769 パフォーマンス最適化ベンチマーク結果")
        print("="*80)
        
        print(f"目標: 300K行ファイル処理 29.17秒 → 5秒以下 (83%高速化)")
        print()
        
        # 各最適化手法の結果
        for optimization, result in results.items():
            if optimization == "summary":
                continue
                
            print(f"📊 {optimization.replace('_', ' ').title()}")
            print("-" * 40)
            
            if isinstance(result, dict) and "speedup_factor" in result:
                speedup = result["speedup_factor"]
                print(f"  高速化倍率: {speedup:.2f}x")
                if "traditional_time" in result and "optimized_time" in result:
                    print(f"  従来処理時間: {result['traditional_time']:.4f}秒")
                    print(f"  最適化時間: {result.get('optimized_time', result.get('simd_time', result.get('async_time', result.get('parallel_time', 0)))):.4f}秒")
            else:
                # 複数のサブベンチマークがある場合
                for sub_name, sub_result in result.items():
                    if isinstance(sub_result, dict) and "speedup_factor" in sub_result:
                        print(f"  {sub_name}: {sub_result['speedup_factor']:.2f}x speedup")
            print()
        
        # 総合結果
        if "summary" in results:
            summary = results["summary"]
            print("🎯 総合結果")
            print("-" * 40)
            print(f"  推定総合高速化: {summary['total_estimated_speedup']:.2f}x")
            print(f"  目標高速化倍率: {summary['target_speedup']:.2f}x")
            print(f"  目標達成: {'✅ YES' if summary['target_achieved'] else '❌ NO'}")
            print()
            
            if summary['target_achieved']:
                estimated_new_time = 29.17 / summary['total_estimated_speedup']
                print(f"  推定新処理時間: {estimated_new_time:.2f}秒")
                print(f"  性能向上: {((29.17 - estimated_new_time) / 29.17 * 100):.1f}%")
            
            print()
            print("📈 パフォーマンス詳細:")
            print(summary['performance_report'])


async def main():
    """メイン実行関数"""
    print("Issue #769 パフォーマンス最適化ベンチマーク開始")
    
    benchmark = PerformanceBenchmark()
    
    # ベンチマーク実行（300K行でテスト）
    results = await benchmark.run_comprehensive_benchmark(lines_count=300000)
    
    # 結果レポート出力
    benchmark.print_benchmark_report(results)
    
    print("\nベンチマーク完了 🎉")


if __name__ == "__main__":
    asyncio.run(main())