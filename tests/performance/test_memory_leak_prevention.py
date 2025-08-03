#!/usr/bin/env python3
"""
メモリリーク防止検証テスト
Issue #694対応 - 長時間処理・反復処理でのメモリ安定性確認
"""

import gc
import time
import tracemalloc
from pathlib import Path
import sys
import psutil
import threading

# プロジェクトのパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from kumihan_formatter.parser import Parser, parse_with_error_config
from kumihan_formatter.core.utilities.performance_metrics import PerformanceMonitor
from kumihan_formatter.core.utilities.logger import get_logger


class MemoryLeakDetector:
    """メモリリーク検出器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.process = psutil.Process()
        self.initial_memory = None
        self.memory_history = []
    
    def start_tracking(self):
        """メモリ追跡開始"""
        gc.collect()  # 初期ガベージコレクション
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024
        self.memory_history = [self.initial_memory]
        
        tracemalloc.start()
        self.logger.info(f"Memory tracking started: {self.initial_memory:.1f}MB")
    
    def record_memory_usage(self, label: str = ""):
        """現在のメモリ使用量を記録"""
        current_memory = self.process.memory_info().rss / 1024 / 1024
        self.memory_history.append(current_memory)
        
        if label:
            self.logger.debug(f"Memory usage [{label}]: {current_memory:.1f}MB")
        
        return current_memory
    
    def detect_leak(self, tolerance_mb: float = 10.0) -> tuple[bool, str]:
        """メモリリークを検出"""
        if len(self.memory_history) < 3:
            return False, "追跡データ不足"
        
        # 初期メモリとの差分チェック
        current_memory = self.memory_history[-1]
        memory_growth = current_memory - self.initial_memory
        
        # メモリ増加傾向の分析
        recent_samples = self.memory_history[-10:]  # 直近10サンプル
        
        if len(recent_samples) >= 3:
            # 線形回帰で増加傾向を判定
            growth_trend = self._calculate_memory_trend(recent_samples)
            
            if memory_growth > tolerance_mb:
                return True, f"メモリ増加: {memory_growth:.1f}MB (許容値: {tolerance_mb}MB)"
            elif growth_trend > 1.0:  # 1MB/sample以上の増加傾向
                return True, f"メモリ増加傾向検出: {growth_trend:.2f}MB/iteration"
        
        return False, f"メモリ安定: 増加{memory_growth:.1f}MB"
    
    def _calculate_memory_trend(self, memory_values: list) -> float:
        """メモリ増加傾向を計算"""
        if len(memory_values) < 2:
            return 0.0
        
        n = len(memory_values)
        x_avg = sum(range(n)) / n
        y_avg = sum(memory_values) / n
        
        numerator = sum((i - x_avg) * (memory_values[i] - y_avg) for i in range(n))
        denominator = sum((i - x_avg) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def get_memory_summary(self) -> dict:
        """メモリ使用量サマリーを取得"""
        if not self.memory_history:
            return {}
        
        current_memory = self.memory_history[-1]
        peak_memory = max(self.memory_history)
        min_memory = min(self.memory_history)
        
        return {
            'initial_mb': self.initial_memory,
            'current_mb': current_memory,
            'peak_mb': peak_memory,
            'min_mb': min_memory,
            'growth_mb': current_memory - self.initial_memory,
            'peak_growth_mb': peak_memory - self.initial_memory,
            'samples_count': len(self.memory_history)
        }


def generate_test_content(size_kb: int = 100) -> str:
    """指定サイズのテストコンテンツ生成"""
    target_bytes = size_kb * 1024
    
    sample_lines = [
        "# 見出し1 # メモリリークテスト用コンテンツ",
        "# 太字 # **重要な情報**の記述",
        "- リスト項目: 詳細な説明文",
        "通常のパラグラフ。長いテキスト内容がここに記述されます。",
        "# ハイライト # 注目すべき内容",
        "1. 順序付きリスト項目",
        ""
    ]
    
    # 目標サイズまでコンテンツを生成
    content_lines = []
    current_size = 0
    line_counter = 0
    
    while current_size < target_bytes:
        line_template = sample_lines[line_counter % len(sample_lines)]
        line = line_template.replace("テスト", f"テスト{line_counter}")
        content_lines.append(line)
        current_size += len(line.encode('utf-8'))
        line_counter += 1
    
    return "\n".join(content_lines)


def test_repeated_parsing():
    """反復解析でのメモリリークテスト"""
    print("🔄 反復解析メモリリークテスト")
    print("-" * 40)
    
    detector = MemoryLeakDetector()
    detector.start_tracking()
    
    # テストコンテンツ準備
    test_content = generate_test_content(500)  # 500KB
    print(f"テストコンテンツ: {len(test_content)} 文字")
    
    iterations = 20
    results = []
    
    for i in range(iterations):
        print(f"反復 {i+1}/{iterations}...")
        
        # 解析実行
        start_time = time.time()
        parser = Parser()
        nodes = parser.parse_streaming_from_text(test_content)
        end_time = time.time()
        
        # メモリ使用量記録
        memory_mb = detector.record_memory_usage(f"iteration_{i+1}")
        
        results.append({
            'iteration': i + 1,
            'memory_mb': memory_mb,
            'nodes_count': len(nodes),
            'duration_seconds': end_time - start_time
        })
        
        # ガベージコレクション実行
        del parser, nodes
        gc.collect()
        
        # 少し待機
        time.sleep(0.1)
    
    # リーク検出
    has_leak, leak_message = detector.detect_leak(tolerance_mb=50.0)
    
    print(f"\n📊 反復解析結果:")
    print(f"  反復回数: {iterations}")
    print(f"  メモリリーク: {'❌ 検出' if has_leak else '✅ なし'}")
    print(f"  詳細: {leak_message}")
    
    # メモリサマリー
    memory_summary = detector.get_memory_summary()
    print(f"  初期メモリ: {memory_summary['initial_mb']:.1f}MB")
    print(f"  最終メモリ: {memory_summary['current_mb']:.1f}MB")
    print(f"  ピークメモリ: {memory_summary['peak_mb']:.1f}MB")
    print(f"  メモリ増加: {memory_summary['growth_mb']:.1f}MB")
    
    return not has_leak


def test_long_running_processing():
    """長時間処理でのメモリ安定性テスト"""
    print("\n⏱️ 長時間処理メモリ安定性テスト")
    print("-" * 40)
    
    detector = MemoryLeakDetector()
    detector.start_tracking()
    
    # 複数サイズのファイルで連続処理
    test_sizes = [100, 250, 500, 1000, 2000]  # KB
    
    for size_kb in test_sizes:
        print(f"処理中: {size_kb}KBファイル...")
        
        # テストコンテンツ生成
        test_content = generate_test_content(size_kb)
        
        # ストリーミング解析実行
        parser = Parser()
        start_time = time.time()
        
        nodes = parser.parse_streaming_from_text(test_content)
        
        end_time = time.time()
        
        # メモリ記録
        memory_mb = detector.record_memory_usage(f"{size_kb}KB_file")
        
        print(f"  完了: {len(nodes)}ノード, {end_time - start_time:.2f}秒, {memory_mb:.1f}MB")
        
        # リソースクリーンアップ
        del parser, nodes, test_content
        gc.collect()
    
    # 最終メモリリーク検出
    has_leak, leak_message = detector.detect_leak(tolerance_mb=30.0)
    
    print(f"\n📊 長時間処理結果:")
    print(f"  メモリリーク: {'❌ 検出' if has_leak else '✅ なし'}")
    print(f"  詳細: {leak_message}")
    
    memory_summary = detector.get_memory_summary()
    print(f"  初期メモリ: {memory_summary['initial_mb']:.1f}MB")
    print(f"  最終メモリ: {memory_summary['current_mb']:.1f}MB")
    print(f"  ピークメモリ: {memory_summary['peak_mb']:.1f}MB")
    print(f"  メモリ増加: {memory_summary['growth_mb']:.1f}MB")
    
    return not has_leak


def test_concurrent_processing():
    """並行処理でのメモリ安定性テスト"""
    print("\n🔀 並行処理メモリ安定性テスト")
    print("-" * 40)
    
    detector = MemoryLeakDetector()
    detector.start_tracking()
    
    # 複数スレッドで同時処理
    thread_count = 3
    results = {}
    errors = []
    
    def worker_thread(thread_id: int):
        """ワーカースレッド関数"""
        try:
            test_content = generate_test_content(200)  # 200KB
            
            for i in range(5):  # 各スレッドで5回処理
                parser = Parser()
                nodes = parser.parse_streaming_from_text(test_content)
                
                results[f"thread_{thread_id}_iter_{i}"] = len(nodes)
                
                del parser, nodes
                gc.collect()
                time.sleep(0.1)
                
        except Exception as e:
            errors.append(f"Thread {thread_id}: {e}")
    
    # スレッド実行
    threads = []
    for i in range(thread_count):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads.append(thread)
        thread.start()
    
    # スレッド完了待機
    for thread in threads:
        thread.join()
    
    # メモリリーク検出
    has_leak, leak_message = detector.detect_leak(tolerance_mb=40.0)
    
    print(f"\n📊 並行処理結果:")
    print(f"  スレッド数: {thread_count}")
    print(f"  処理完了: {len(results)}")
    print(f"  エラー数: {len(errors)}")
    print(f"  メモリリーク: {'❌ 検出' if has_leak else '✅ なし'}")
    print(f"  詳細: {leak_message}")
    
    if errors:
        print("  エラー詳細:")
        for error in errors:
            print(f"    - {error}")
    
    memory_summary = detector.get_memory_summary()
    print(f"  初期メモリ: {memory_summary['initial_mb']:.1f}MB")
    print(f"  最終メモリ: {memory_summary['current_mb']:.1f}MB")
    print(f"  ピークメモリ: {memory_summary['peak_mb']:.1f}MB")
    print(f"  メモリ増加: {memory_summary['growth_mb']:.1f}MB")
    
    return not has_leak and len(errors) == 0


def main():
    """メイン実行関数"""
    print("Issue #694 メモリリーク防止検証テスト")
    print("Kumihan-Formatter ストリーミングパーサー安定性確認")
    print("=" * 60)
    
    test_results = []
    
    try:
        # 1. 反復解析テスト
        result1 = test_repeated_parsing()
        test_results.append(("反復解析", result1))
        
        # 2. 長時間処理テスト
        result2 = test_long_running_processing()
        test_results.append(("長時間処理", result2))
        
        # 3. 並行処理テスト
        result3 = test_concurrent_processing()
        test_results.append(("並行処理", result3))
        
        # 最終結果
        print("\n" + "=" * 60)
        print("🏆 メモリリーク防止検証結果")
        print("=" * 60)
        
        all_passed = True
        for test_name, passed in test_results:
            status = "✅ 合格" if passed else "❌ 不合格"
            print(f"{test_name:12}: {status}")
            all_passed = all_passed and passed
        
        print(f"\n総合結果: {'✅ 全テスト合格' if all_passed else '❌ 一部テスト不合格'}")
        
        if all_passed:
            print("Issue #694 メモリリーク防止要件を満たしています。")
            return 0
        else:
            print("メモリリーク対策の追加検討が必要です。")
            return 1
            
    except Exception as e:
        print(f"\n💥 テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())