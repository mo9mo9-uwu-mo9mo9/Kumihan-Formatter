#!/usr/bin/env python3
"""
Issue #759対応: 大規模ファイル処理パフォーマンスベンチマーク

並列処理×真のストリーミング統合実装の性能測定
目標: 300K行ファイルを23.41秒 → 5秒以下 (78.6%改善)
"""

import time
import traceback
from pathlib import Path
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from kumihan_formatter.parser import Parser
from kumihan_formatter.core.utilities.logger import get_logger


class PerformanceBenchmark:
    """パフォーマンスベンチマーククラス"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.results = {}
        
    def run_comprehensive_benchmark(self):
        """包括的なパフォーマンスベンチマーク実行"""
        
        print("=" * 80)
        print("Issue #759: 大規模ファイル処理 パフォーマンスベンチマーク")
        print("=" * 80)
        print(f"目標: 300K行ファイル処理時間 23.41秒 → 5秒以下 (78.6%改善)")
        print()
        
        # テストファイル定義
        test_files = [
            ("1k_test_file.kumihan", "1K行", "baseline"),
            ("10k_test_file.kumihan", "10K行", "medium"),
            ("50k_test_file.kumihan", "50K行", "large"),
            ("300k_test_file.kumihan", "300K行", "target")
        ]
        
        # パーサー方式定義
        parsing_methods = [
            ("traditional", "従来方式", self.test_traditional_parse),
            ("optimized", "最適化版", self.test_optimized_parse),
            ("streaming", "ストリーミング", self.test_streaming_parse),
            ("parallel_streaming", "並列ストリーミング", self.test_parallel_streaming),
            ("hybrid", "ハイブリッド", self.test_hybrid_parse)
        ]
        
        # ベンチマーク実行
        for file_path, file_desc, file_category in test_files:
            if not Path(file_path).exists():
                print(f"⚠️  テストファイル未発見: {file_path}")
                continue
                
            print(f"\n📁 {file_desc} ファイル: {file_path}")
            print("-" * 60)
            
            file_size = Path(file_path).stat().st_size / 1024 / 1024  # MB
            print(f"ファイルサイズ: {file_size:.1f} MB")
            
            file_results = {}
            
            for method_id, method_name, test_func in parsing_methods:
                try:
                    print(f"\n🔄 {method_name} テスト実行中...")
                    
                    result = test_func(file_path)
                    file_results[method_id] = result
                    
                    # 結果表示
                    self.display_result(method_name, result)
                    
                    # メモリクリア
                    import gc
                    gc.collect()
                    
                except Exception as e:
                    print(f"❌ {method_name} エラー: {e}")
                    self.logger.error(f"Benchmark error in {method_name}: {e}")
                    file_results[method_id] = {"error": str(e)}
            
            self.results[file_path] = file_results
            
            # ファイル別パフォーマンス分析
            self.analyze_file_performance(file_desc, file_results)
        
        # 全体結果分析
        self.generate_comprehensive_report()

    def test_traditional_parse(self, file_path: str) -> dict:
        """従来方式のパフォーマンステスト"""
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        parser = Parser()
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        nodes = list(parser.parse(content))
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        
        return {
            "method": "traditional",
            "duration": end_time - start_time,
            "nodes_count": len(nodes),
            "memory_start": start_memory,
            "memory_end": end_memory,
            "memory_delta": end_memory - start_memory
        }

    def test_optimized_parse(self, file_path: str) -> dict:
        """最適化版のパフォーマンステスト"""
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        parser = Parser()
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        nodes = list(parser.parse_optimized(content))
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        
        return {
            "method": "optimized",
            "duration": end_time - start_time,
            "nodes_count": len(nodes),
            "memory_start": start_memory,
            "memory_end": end_memory,
            "memory_delta": end_memory - start_memory
        }

    def test_streaming_parse(self, file_path: str) -> dict:
        """ストリーミング版のパフォーマンステスト"""
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        parser = Parser()
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        nodes = list(parser.parse_streaming_from_text(content))
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        
        return {
            "method": "streaming",
            "duration": end_time - start_time,
            "nodes_count": len(nodes),
            "memory_start": start_memory,
            "memory_end": end_memory,
            "memory_delta": end_memory - start_memory
        }

    def test_parallel_streaming(self, file_path: str) -> dict:
        """並列ストリーミング版のパフォーマンステスト"""
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        parser = Parser()
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # プログレス情報を収集
        progress_info = []
        def progress_callback(info):
            progress_info.append(info)
            
        nodes = list(parser.parse_parallel_streaming(content, progress_callback))
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        
        return {
            "method": "parallel_streaming",
            "duration": end_time - start_time,
            "nodes_count": len(nodes),
            "memory_start": start_memory,
            "memory_end": end_memory,
            "memory_delta": end_memory - start_memory,
            "progress_updates": len(progress_info)
        }

    def test_hybrid_parse(self, file_path: str) -> dict:
        """ハイブリッド版のパフォーマンステスト"""
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        parser = Parser()
        
        nodes = list(parser.parse_hybrid_optimized(file_path))
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        
        return {
            "method": "hybrid",
            "duration": end_time - start_time,
            "nodes_count": len(nodes),
            "memory_start": start_memory,
            "memory_end": end_memory,
            "memory_delta": end_memory - start_memory
        }

    def get_memory_usage(self) -> float:
        """現在のメモリ使用量をMBで取得"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0  # psutil未利用環境

    def display_result(self, method_name: str, result: dict):
        """結果表示"""
        if "error" in result:
            print(f"   ❌ エラー: {result['error']}")
            return
            
        duration = result['duration']
        nodes = result['nodes_count']
        memory_delta = result.get('memory_delta', 0)
        
        print(f"   ⏱️  処理時間: {duration:.2f}秒")
        print(f"   📊 ノード数: {nodes:,}")
        print(f"   💾 メモリ差分: {memory_delta:.1f}MB")
        print(f"   ⚡ 処理速度: {nodes/duration:.0f} nodes/sec")

    def analyze_file_performance(self, file_desc: str, results: dict):
        """ファイル別パフォーマンス分析"""
        print(f"\n📈 {file_desc} パフォーマンス分析:")
        print("-" * 40)
        
        # エラーのない結果のみを分析
        valid_results = {k: v for k, v in results.items() if "error" not in v}
        
        if not valid_results:
            print("   ⚠️  有効な結果がありません")
            return
            
        # 最速・最遅の特定
        fastest = min(valid_results.items(), key=lambda x: x[1]['duration'])
        slowest = max(valid_results.items(), key=lambda x: x[1]['duration'])
        
        print(f"   🏆 最速: {fastest[0]} ({fastest[1]['duration']:.2f}秒)")
        print(f"   🐌 最遅: {slowest[0]} ({slowest[1]['duration']:.2f}秒)")
        
        # 改善率計算
        if len(valid_results) >= 2:
            improvement = (slowest[1]['duration'] - fastest[1]['duration']) / slowest[1]['duration'] * 100
            print(f"   📊 最大改善率: {improvement:.1f}%")

    def generate_comprehensive_report(self):
        """包括的レポート生成"""
        print("\n" + "=" * 80)
        print("📋 総合パフォーマンスレポート")
        print("=" * 80)
        
        # 300K行ファイルの結果に焦点
        target_file = "300k_test_file.kumihan"
        if target_file in self.results:
            target_results = self.results[target_file]
            print(f"\n🎯 300K行ファイル (目標ファイル) 結果:")
            print("-" * 50)
            
            baseline_time = 23.41  # 従来の処理時間
            
            for method, result in target_results.items():
                if "error" in result:
                    continue
                    
                duration = result['duration']
                improvement = (baseline_time - duration) / baseline_time * 100
                
                print(f"   {method:20}: {duration:6.2f}秒 ({improvement:+5.1f}%)")
                
                # 目標達成チェック
                if duration <= 5.0:
                    print(f"      ✅ 目標達成！ (5秒以下)")
                else:
                    remaining = (duration - 5.0) / duration * 100
                    print(f"      ⏳ 目標まで: {remaining:.1f}%改善が必要")
        
        # 全体的な傾向分析
        print(f"\n📊 全体傾向:")
        print("-" * 30)
        
        method_performance = {}
        for file_path, file_results in self.results.items():
            for method, result in file_results.items():
                if "error" not in result:
                    if method not in method_performance:
                        method_performance[method] = []
                    method_performance[method].append(result['duration'])
        
        for method, durations in method_performance.items():
            avg_duration = sum(durations) / len(durations)
            print(f"   {method:20}: 平均 {avg_duration:.2f}秒")
        
        print(f"\n🎉 Issue #759 実装完了レポート生成!")


def main():
    """メイン実行"""
    
    # 必要なファイルの存在確認
    required_files = [
        "1k_test_file.kumihan",
        "10k_test_file.kumihan", 
        "50k_test_file.kumihan",
        "300k_test_file.kumihan"
    ]
    
    missing_files = [f for f in required_files if not Path(f).exists()]
    if missing_files:
        print("❌ 必要なテストファイルが見つかりません:")
        for f in missing_files:
            print(f"   - {f}")
        print("\n先に generate_large_test_file.py を実行してください。")
        return 1
    
    # ベンチマーク実行
    benchmark = PerformanceBenchmark()
    try:
        benchmark.run_comprehensive_benchmark()
        return 0
    except Exception as e:
        print(f"\n❌ ベンチマーク実行エラー: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)