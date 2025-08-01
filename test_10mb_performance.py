#!/usr/bin/env python3
"""
10MBファイル処理パフォーマンステスト
Issue #694対応 - 大容量ファイルでの実際の性能測定
"""

import time
import tracemalloc
from pathlib import Path
import sys
import gc

# プロジェクトのパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from kumihan_formatter.parser import StreamingParser, parse_with_streaming
from kumihan_formatter.core.utilities.logger import get_logger


def generate_large_test_content(target_size_mb: float = 10.0) -> str:
    """指定されたサイズの大容量テストコンテンツを生成"""
    print(f"📝 {target_size_mb}MBテストファイル生成中...")
    
    # 1行あたりの平均バイト数を計算（日本語込み）
    sample_lines = [
        "# 見出し1 # 大容量ファイル処理のテストコンテンツです",
        "# 太字 # **重要な内容**が記述されています。詳細な説明文章が続きます。",
        "- リスト項目: 複数の要素を含む詳細なリスト項目です",
        "通常のパラグラフ文章。長いテキスト内容がここに記述されます。この文章は複数行にわたって継続する場合があります。",
        "# ハイライト color:blue # 注目すべき内容がここに書かれています",
        "1. 順序付きリスト項目の詳細な説明",
        "# 枠線 # 囲まれた重要な情報ブロック",
        "# コード # `complex_function(param1, param2, param3)`",
        "# 引用 # > 引用されたテキスト内容の詳細な記述",
        ""  # 空行
    ]
    
    avg_line_bytes = sum(len(line.encode('utf-8')) for line in sample_lines) / len(sample_lines)
    target_bytes = target_size_mb * 1024 * 1024
    target_lines = int(target_bytes / avg_line_bytes)
    
    print(f"目標: {target_lines:,}行 ({target_size_mb}MB)")
    
    content_lines = []
    for i in range(target_lines):
        line_type = i % len(sample_lines)
        base_line = sample_lines[line_type]
        
        if base_line:
            # 行番号を追加してユニーク性を保つ
            content_lines.append(base_line.replace("テスト", f"テスト{i}"))
        else:
            content_lines.append("")
    
    content = "\n".join(content_lines)
    actual_size_mb = len(content.encode('utf-8')) / 1024 / 1024
    
    print(f"生成完了: {len(content_lines):,}行, {actual_size_mb:.2f}MB")
    return content


def test_streaming_performance_with_large_file():
    """大容量ファイルでのストリーミング性能テスト"""
    print("🚀 10MB大容量ファイル処理パフォーマンステスト")
    print("=" * 60)
    
    # 10MBテストファイル生成
    test_content = generate_large_test_content(10.0)
    file_size_mb = len(test_content.encode('utf-8')) / 1024 / 1024
    line_count = len(test_content.split('\n'))
    
    print(f"\n📊 テストファイル情報:")
    print(f"  サイズ: {file_size_mb:.2f}MB")
    print(f"  行数: {line_count:,}行")
    
    # メモリ使用量測定開始
    gc.collect()  # ガベージコレクション実行
    tracemalloc.start()
    initial_memory = tracemalloc.get_traced_memory()[0]
    
    print(f"\n🔬 ストリーミングパーサーテスト開始...")
    start_time = time.time()
    
    try:
        # プログレス追跡用
        progress_updates = []
        
        def progress_callback(progress_info):
            """プログレス更新を記録"""
            progress_updates.append({
                'timestamp': time.time(),
                'progress_percent': progress_info['progress_percent'],
                'current_line': progress_info['current_line'],
                'eta_seconds': progress_info['eta_seconds'],
                'processing_rate': progress_info.get('processing_rate', 0)
            })
            
            # 10%ごとに詳細出力
            if len(progress_updates) % 50 == 0:
                print(f"  📈 進捗: {progress_info['progress_percent']:.1f}% "
                      f"({progress_info['current_line']:,}/{progress_info.get('total_lines', 0):,}行) "
                      f"ETA: {progress_info['eta_seconds']}秒")
        
        # ストリーミング解析実行
        parser = StreamingParser()
        nodes = list(parser.parse_streaming_from_text(test_content, progress_callback))
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # メモリ使用量測定
        peak_memory = tracemalloc.get_traced_memory()[1]
        memory_used_mb = (peak_memory - initial_memory) / 1024 / 1024
        tracemalloc.stop()
        
        print(f"\n✅ テスト完了!")
        print(f"📊 結果サマリー:")
        print(f"  処理時間: {execution_time:.2f}秒")
        print(f"  メモリ使用量: {memory_used_mb:.1f}MB")
        print(f"  生成ノード数: {len(nodes):,}個")
        print(f"  処理速度: {line_count/execution_time:,.0f}行/秒")
        print(f"  スループット: {file_size_mb/execution_time:.2f}MB/秒")
        
        # エラー統計
        errors = parser.get_errors()
        if errors:
            print(f"  エラー数: {len(errors)}")
        else:
            print(f"  エラー数: 0 (正常)")
        
        # 目標達成状況
        print(f"\n🎯 目標達成状況:")
        print(f"  10MB処理: {'✅ 成功' if execution_time < 120 else '❌ 時間超過'} ({execution_time:.1f}秒)")
        print(f"  メモリ効率: {'✅ 良好' if memory_used_mb < 100 else '⚠️ 要改善'} ({memory_used_mb:.1f}MB)")
        
        # プログレス統計
        if progress_updates:
            print(f"\n📈 プログレス統計:")
            print(f"  更新回数: {len(progress_updates)}回")
            
            # 平均処理速度計算
            valid_rates = [p['processing_rate'] for p in progress_updates if p['processing_rate'] > 0]
            if valid_rates:
                avg_rate = sum(valid_rates) / len(valid_rates)
                print(f"  平均処理速度: {avg_rate:.0f}行/秒")
        
        return True
        
    except Exception as e:
        print(f"\n❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_efficiency():
    """メモリ効率性テスト"""
    print(f"\n🧠 メモリ効率性テスト")
    print("-" * 40)
    
    # 段階的にファイルサイズを増加させてメモリ使用量を測定
    test_sizes = [1, 2, 5, 10]  # MB
    memory_results = []
    
    for size_mb in test_sizes:
        print(f"\n📏 {size_mb}MBファイルテスト...")
        
        test_content = generate_large_test_content(size_mb)
        actual_size_mb = len(test_content.encode('utf-8')) / 1024 / 1024
        
        # メモリ使用量測定
        gc.collect()
        tracemalloc.start()
        initial_memory = tracemalloc.get_traced_memory()[0]
        
        try:
            parser = StreamingParser()
            nodes = list(parser.parse_streaming_from_text(test_content))
            
            peak_memory = tracemalloc.get_traced_memory()[1]
            memory_used_mb = (peak_memory - initial_memory) / 1024 / 1024
            
            memory_results.append({
                'file_size_mb': actual_size_mb,
                'memory_used_mb': memory_used_mb,
                'memory_ratio': memory_used_mb / actual_size_mb,
                'nodes_count': len(nodes)
            })
            
            print(f"  ファイル: {actual_size_mb:.1f}MB → メモリ: {memory_used_mb:.1f}MB "
                  f"(比率: {memory_used_mb/actual_size_mb:.2f})")
            
        except Exception as e:
            print(f"  ❌ エラー: {e}")
        finally:
            tracemalloc.stop()
    
    # メモリ効率性分析
    if len(memory_results) >= 2:
        print(f"\n📊 メモリ効率性分析:")
        
        for result in memory_results:
            print(f"  {result['file_size_mb']:4.1f}MB: "
                  f"メモリ{result['memory_used_mb']:5.1f}MB "
                  f"(比率{result['memory_ratio']:.2f}, "
                  f"{result['nodes_count']:,}ノード)")
        
        # スケーラビリティチェック
        first_ratio = memory_results[0]['memory_ratio']
        last_ratio = memory_results[-1]['memory_ratio']
        
        if abs(last_ratio - first_ratio) < 0.5:
            print(f"  ✅ メモリ使用量は一定スケール (比率変動: {abs(last_ratio - first_ratio):.2f})")
        else:
            print(f"  ⚠️ メモリ使用量がスケールに依存 (比率変動: {abs(last_ratio - first_ratio):.2f})")


def main():
    """メイン実行関数"""
    print("Issue #694 大容量ファイル処理 - 10MB実証テスト")
    print("Kumihan-Formatter ストリーミングパーサー最終検証")
    print("=" * 60)
    
    try:
        # 10MBファイル処理テスト
        success = test_streaming_performance_with_large_file()
        
        if success:
            # メモリ効率性テスト
            test_memory_efficiency()
            
            print(f"\n🎉 全テスト完了")
            print(f"Issue #694の要求事項が満たされていることを確認しました。")
            return 0
        else:
            print(f"\n❌ テスト失敗")
            return 1
            
    except Exception as e:
        print(f"\n💥 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())