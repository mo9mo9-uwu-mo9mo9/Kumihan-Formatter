#!/usr/bin/env python3
"""
パフォーマンス測定スクリプト - Issue #1172対応
最適化の最終フェーズとして性能測定・ボトルネック特定を実行
"""

import time
import sys
import tracemalloc
import os
from pathlib import Path
import tempfile

# プロジェクトルートを追加
sys.path.insert(0, '/Users/m2_macbookair_3911/GitHub/Kumihan-Formatter')

def measure_parsing_performance():
    """パーシング性能測定"""
    try:
        from kumihan_formatter.parser import Parser
        
        parser = Parser()
        
        # 小規模テスト（基本性能）
        small_content = """
        # 見出し #テスト見出し##
        
        これは小規模なテストコンテンツです。
        
        # 太字 #重要な情報##
        # イタリック #斜体テキスト##
        """
        
        print("=== パーシング性能測定 ===")
        
        # 小規模テスト
        start_time = time.time()
        small_result = parser.parse(small_content)
        small_time = time.time() - start_time
        print(f"小規模テスト: {small_time:.4f}秒")
        
        # 中規模テスト
        medium_content = []
        for i in range(100):
            medium_content.append(f"# 見出し{i} #タイトル{i}##")
            medium_content.append(f"これは{i}番目の段落です。" * 10)
            medium_content.append("")
        medium_text = "\n".join(medium_content)
        
        start_time = time.time()
        medium_result = parser.parse(medium_text)
        medium_time = time.time() - start_time
        print(f"中規模テスト (100セクション): {medium_time:.4f}秒")
        
        # 大規模テスト
        large_content = []
        for i in range(1000):
            large_content.append(f"# 見出し{i} #大規模タイトル{i}##")
            large_content.append(f"大規模テストの{i}番目の段落です。" * 5)
        large_text = "\n".join(large_content)
        
        start_time = time.time()
        large_result = parser.parse(large_text)
        large_time = time.time() - start_time
        print(f"大規模テスト (1000セクション): {large_time:.4f}秒")
        
        return {
            'small_time': small_time,
            'medium_time': medium_time,
            'large_time': large_time,
            'results': [small_result, medium_result, large_result]
        }
        
    except ImportError as e:
        print(f"パーサーのインポートエラー: {e}")
        return None


def measure_rendering_performance():
    """レンダリング性能測定"""
    try:
        from kumihan_formatter.renderer import Renderer
        
        renderer = Renderer()
        
        # テストデータ準備
        test_data = []
        for i in range(500):
            test_data.append({
                'type': 'heading',
                'level': 1,
                'content': f'見出し{i}'
            })
            test_data.append({
                'type': 'text',
                'content': f'テキストコンテンツ {i}' * 10
            })
        
        print("=== レンダリング性能測定 ===")
        
        start_time = time.time()
        if hasattr(renderer, 'render'):
            result = renderer.render(test_data)
        else:
            result = "レンダラーにrenderメソッドが存在しません"
        render_time = time.time() - start_time
        
        print(f"レンダリング時間 (500要素): {render_time:.4f}秒")
        
        return {
            'render_time': render_time,
            'result_size': len(str(result)) if result else 0
        }
        
    except ImportError as e:
        print(f"レンダラーのインポートエラー: {e}")
        return None


def measure_memory_usage():
    """メモリ使用量測定"""
    print("=== メモリ使用量測定 ===")
    
    tracemalloc.start()
    
    try:
        from kumihan_formatter.parser import Parser
        
        parser = Parser()
        
        # 大量のデータ処理でメモリ使用量を測定
        large_content = "大量テストデータ " * 50000
        
        snapshot_before = tracemalloc.take_snapshot()
        
        result = parser.parse(large_content)
        
        snapshot_after = tracemalloc.take_snapshot()
        
        # メモリ差分計算
        top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
        
        total_memory = sum(stat.size_diff for stat in top_stats)
        print(f"総メモリ使用量差分: {total_memory / 1024 / 1024:.2f} MB")
        
        # トップ10のメモリ使用を表示
        print("\nトップ10メモリ使用:")
        for index, stat in enumerate(top_stats[:10], 1):
            print(f"{index}. {stat}")
        
        return {
            'total_memory_mb': total_memory / 1024 / 1024,
            'top_stats': top_stats[:10]
        }
        
    except ImportError as e:
        print(f"メモリ測定でインポートエラー: {e}")
        return None
    finally:
        tracemalloc.stop()


def measure_file_processing_performance():
    """ファイル処理性能測定"""
    print("=== ファイル処理性能測定 ===")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # テストファイル作成
        test_files = []
        for i in range(10):
            test_file = os.path.join(temp_dir, f'test_{i}.txt')
            with open(test_file, 'w', encoding='utf-8') as f:
                content = f"""
                # ファイル{i} #ファイル{i}のタイトル##
                
                これはファイル{i}の内容です。
                """ * 100  # 各ファイルを大きくする
            test_files.append(test_file)
        
        # ファイル処理時間測定
        from kumihan_formatter.parser import Parser
        
        parser = Parser()
        
        start_time = time.time()
        
        results = []
        for test_file in test_files:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            result = parser.parse(content)
            results.append(result)
        
        total_time = time.time() - start_time
        
        print(f"10ファイル処理時間: {total_time:.4f}秒")
        print(f"1ファイルあたり平均: {total_time/10:.4f}秒")
        
        return {
            'total_time': total_time,
            'average_per_file': total_time / 10,
            'files_processed': len(test_files)
        }
        
    except ImportError as e:
        print(f"ファイル処理測定でインポートエラー: {e}")
        return None
    finally:
        # クリーンアップ
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def analyze_bottlenecks():
    """ボトルネック分析"""
    print("\n=== ボトルネック分析 ===")
    
    # システム情報
    print(f"Python バージョン: {sys.version}")
    print(f"プラットフォーム: {sys.platform}")
    
    try:
        import psutil
        process = psutil.Process()
        print(f"現在のメモリ使用量: {process.memory_info().rss / 1024 / 1024:.2f} MB")
        print(f"CPU使用率: {process.cpu_percent()}%")
    except ImportError:
        print("psutil が利用できないため、詳細なシステム情報は表示されません")
    
    # 推奨最適化ポイント
    recommendations = [
        "大規模ファイル処理時のメモリ効率化",
        "正規表現パターンマッチングの最適化",
        "AST構築プロセスの高速化",
        "並列処理の活用検討",
        "キャッシュ機能の効果的利用"
    ]
    
    print("\n推奨最適化ポイント:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")


def main():
    """メイン実行関数"""
    print("Kumihan-Formatter パフォーマンス測定開始")
    print("=" * 50)
    
    results = {}
    
    # パーシング性能測定
    parsing_results = measure_parsing_performance()
    if parsing_results:
        results['parsing'] = parsing_results
    
    print()
    
    # レンダリング性能測定
    rendering_results = measure_rendering_performance()
    if rendering_results:
        results['rendering'] = rendering_results
    
    print()
    
    # メモリ使用量測定
    memory_results = measure_memory_usage()
    if memory_results:
        results['memory'] = memory_results
    
    print()
    
    # ファイル処理性能測定
    file_results = measure_file_processing_performance()
    if file_results:
        results['file_processing'] = file_results
    
    # ボトルネック分析
    analyze_bottlenecks()
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("パフォーマンス測定完了")
    
    if results:
        print("\n=== 結果サマリー ===")
        for category, data in results.items():
            print(f"\n[{category.upper()}]")
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        if 'time' in key:
                            print(f"  {key}: {value:.4f}秒")
                        elif 'memory' in key or 'mb' in key:
                            print(f"  {key}: {value:.2f} MB")
                        else:
                            print(f"  {key}: {value}")


if __name__ == '__main__':
    main()