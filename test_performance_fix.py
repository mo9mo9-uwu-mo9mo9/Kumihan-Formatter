#!/usr/bin/env python3
"""
Issue #693 パフォーマンス修正の検証スクリプト
200行超ファイルでの処理時間を測定
"""

import time
import sys
from pathlib import Path
from kumihan_formatter.core.block_parser.block_parser import BlockParser
from kumihan_formatter.core.keyword_parser import KeywordParser

def create_large_test_file(lines: int) -> list[str]:
    """大きなテストファイルを生成"""
    content = []
    
    # 多様なパターンを含む大ファイルを生成
    for i in range(lines):
        if i % 10 == 0:
            content.append(f"# 見出し{i//10 + 1} # セクション{i}")
        elif i % 7 == 0:
            content.append(f"# 太字 # 重要な内容 第{i}行")
        elif i % 5 == 0:
            content.append("# ハイライト #")
            content.append(f"重要な情報です。行番号: {i}")
            content.append("##")
        else:
            content.append(f"通常のテキスト行です。行番号: {i}")
    
    return content

def benchmark_parser(lines_count: int, iterations: int = 3) -> float:
    """パーサーのベンチマーク実行"""
    print(f"📊 {lines_count}行のファイルでベンチマーク開始...")
    
    # テストデータ準備
    test_lines = create_large_test_file(lines_count)
    
    # パーサー初期化
    keyword_parser = KeywordParser()
    block_parser = BlockParser(keyword_parser)
    
    total_time = 0.0
    
    for i in range(iterations):
        print(f"  実行 {i+1}/{iterations}...", end=" ")
        
        start_time = time.perf_counter()
        
        # 実際の解析処理
        current_index = 0
        parsed_nodes = []
        
        while current_index < len(test_lines):
            line = test_lines[current_index].strip()
            
            if block_parser.is_opening_marker(line):
                node, next_index = block_parser.parse_new_format_marker(test_lines, current_index)
                if node:
                    parsed_nodes.append(node)
                current_index = next_index
            elif line:
                node, next_index = block_parser.parse_paragraph(test_lines, current_index)
                if node:
                    parsed_nodes.append(node)
                current_index = next_index
            else:
                current_index += 1
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        total_time += execution_time
        
        print(f"{execution_time:.3f}秒 (ノード数: {len(parsed_nodes)})")
    
    average_time = total_time / iterations
    print(f"  ✅ 平均実行時間: {average_time:.3f}秒")
    return average_time

def main():
    """メイン実行関数"""
    print("🚀 Issue #693 パフォーマンス修正検証")
    print("=" * 50)
    
    # 様々なファイルサイズでテスト（シナリオ文章規模まで）
    test_sizes = [50, 100, 200, 300, 500, 1000, 2000, 5000, 10000, 20000]
    results = {}
    
    for size in test_sizes:
        try:
            avg_time = benchmark_parser(size)
            results[size] = avg_time
            
            # パフォーマンス評価
            if avg_time > 120:
                print(f"⚠️  {size}行で2分タイムアウト超過!")
                break
            elif avg_time > 60:
                print(f"🔴 {size}行で1分超過 - 重大なパフォーマンス問題")
            elif avg_time > 10:
                print(f"🟡 {size}行で10秒超過 - パフォーマンス低下")
            elif avg_time > 1:
                print(f"🟠 {size}行で1秒超過 - 軽微な低下")
            else:
                print(f"✅ {size}行 - 良好なパフォーマンス")
                
            # 20万文字相当の推定（1行約10文字として）
            char_estimate = size * 10
            if char_estimate >= 200000:
                print(f"   📝 推定文字数: {char_estimate:,}文字（シナリオ文章規模）")
                
        except Exception as e:
            print(f"❌ {size}行でエラー: {e}")
            break
        
        print()
    
    # 結果サマリー
    print("📈 パフォーマンス結果サマリー")
    print("-" * 50)
    for size, time_taken in results.items():
        status = "🟢" if time_taken < 1 else "🟠" if time_taken < 10 else "🟡" if time_taken < 60 else "🔴"
        char_estimate = size * 10
        char_info = f" ({char_estimate:,}文字)" if char_estimate >= 10000 else ""
        print(f"{status} {size:5d}行: {time_taken:7.3f}秒{char_info}")
    
    # 大規模ファイル対応状況
    print("\n🎯 大規模ファイル対応状況")
    print("-" * 30)
    large_sizes = [size for size in results.keys() if size >= 1000]
    if large_sizes:
        max_size = max(large_sizes)
        max_time = results[max_size]
        max_chars = max_size * 10
        print(f"✅ 最大処理: {max_size:,}行 ({max_chars:,}文字) - {max_time:.3f}秒")
        
        if max_chars >= 200000:
            print(f"🎉 20万文字超シナリオ対応: 完全対応済み")
        elif max_chars >= 100000:
            print(f"⚡ 10万文字超文書対応: 高速処理確認")
        else:
            print(f"📄 中規模文書対応: 基本性能確認")
    
    # Issue #693 の検証
    if 200 in results:
        time_200 = results[200]
        if time_200 < 10:
            print("\n🎉 Issue #693 修正成功!")
            print(f"   200行の処理時間: {time_200:.3f}秒 (< 10秒)")
        else:
            print(f"\n⚠️  Issue #693 未解決")
            print(f"   200行の処理時間: {time_200:.3f}秒 (> 10秒)")

if __name__ == "__main__":
    main()