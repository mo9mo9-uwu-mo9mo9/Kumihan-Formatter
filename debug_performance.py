#!/usr/bin/env python3
"""
Kumihan-Formatter パフォーマンスデバッグスクリプト
パーサーのボトルネックを特定し、詳細な実行プロファイルを生成
"""

import cProfile
import io
import pstats
import time
from pathlib import Path

from kumihan_formatter.parser import Parser


def profile_parser_performance(file_path: str, max_lines: int = None):
    """パーサーのパフォーマンスを詳細プロファイル"""
    
    print(f"🔍 プロファイリング開始: {file_path}")
    
    # ファイル読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    if max_lines:
        lines = text.split('\n')[:max_lines]
        text = '\n'.join(lines)
        print(f"📄 制限: {max_lines}行のみ処理")
    
    print(f"📊 データサイズ: {len(text)}文字, {len(text.split(chr(10)))}行")
    
    # パフォーマンステスト
    parser = Parser()
    
    # タイムテスト
    start_time = time.time()
    try:
        print("⏱️  基本実行テスト...")
        result = parser.parse(text)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"✅ 実行完了: {execution_time:.2f}秒, {len(result)}ノード生成")
        
        if execution_time > 10:
            print("🚨 警告: 10秒以上の実行時間")
            
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        return
    
    # 詳細プロファイリング
    print("\n🔬 詳細プロファイリング実行...")
    profiler = cProfile.Profile()
    profiler.enable()
    
    try:
        parser = Parser()  # 新しいインスタンス
        result = parser.parse(text)
        
        profiler.disable()
        
        # プロファイル結果の分析
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats(20)  # 上位20関数を表示
        
        print("\n📈 実行時間上位20関数:")
        print(s.getvalue())
        
        # 特定の関数の詳細分析
        print("\n🎯 ボトルネック関数詳細:")
        ps.sort_stats('tottime')
        ps.print_stats(10)  # 自身の実行時間でソート
        
        # メモリ使用量チェック
        import tracemalloc
        tracemalloc.start()
        
        parser = Parser()
        result = parser.parse(text)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\n💾 メモリ使用量:")
        print(f"   現在: {current / 1024 / 1024:.2f} MB")
        print(f"   ピーク: {peak / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        profiler.disable()
        print(f"❌ プロファイリングエラー: {e}")


def test_incremental_parsing():
    """段階的パース処理テスト - どの行数で問題が発生するか特定"""
    
    file_path = "01_basic_features.txt"
    
    if not Path(file_path).exists():
        print(f"❌ ファイルが見つかりません: {file_path}")
        return
    
    print(f"📈 段階的パース処理テスト: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    test_sizes = [10, 20, 50, 80, 100, 120, 150, total_lines]
    
    for size in test_sizes:
        if size > total_lines:
            continue
            
        print(f"\n🧪 {size}行テスト:")
        
        test_lines = lines[:size]
        test_text = ''.join(test_lines)
        
        parser = Parser()
        start_time = time.time()
        
        try:
            result = parser.parse(test_text)
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"   ✅ 実行時間: {execution_time:.3f}秒, ノード数: {len(result)}")
            
            if execution_time > 5:
                print(f"   🚨 遅延検出: {size}行で{execution_time:.2f}秒")
                # この段階で詳細プロファイルを実行
                profile_parser_performance(file_path, size)
                break
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
            break


if __name__ == "__main__":
    print("🚀 Kumihan-Formatter パフォーマンスデバッグ開始\n")
    
    # 段階的テスト実行
    test_incremental_parsing()
    
    print("\n🏁 パフォーマンスデバッグ完了")