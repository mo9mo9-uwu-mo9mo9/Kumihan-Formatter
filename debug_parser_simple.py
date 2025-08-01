#!/usr/bin/env python3
"""
簡単なパーサーデバッグ - 各行の処理状況を詳細追跡
"""

import sys
import time
from kumihan_formatter.parser import Parser

def debug_line_by_line(file_path: str, max_lines: int = 170):
    """行単位でパーサーの動作を詳細追跡"""
    
    print(f"🔍 行単位デバッグ開始: {file_path} (最大{max_lines}行)")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 徐々に行数を増やしてテスト
    for test_size in [10, 20, 50, 80, 100, 120, 150, 170]:
        if test_size > len(lines):
            continue
            
        print(f"\n📊 {test_size}行テスト:")
        
        test_text = ''.join(lines[:test_size])
        parser = Parser()
        
        start_time = time.time()
        timeout = 5.0  # 5秒でタイムアウト
        
        try:
            # タイムアウト付きでパース実行
            class TimeoutException(Exception):
                pass
            
            def timeout_handler():
                raise TimeoutException(f"Timeout after {timeout} seconds")
            
            import signal
            signal.signal(signal.SIGALRM, lambda signum, frame: timeout_handler())
            signal.alarm(int(timeout))
            
            result = parser.parse(test_text)
            signal.alarm(0)  # タイマー解除
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"   ✅ 成功: {execution_time:.3f}秒, {len(result)}ノード")
            
            if execution_time > 2.0:
                print(f"   ⚠️  遅延検出: {test_size}行で{execution_time:.2f}秒")
                # この行数で問題があるとして詳細分析
                analyze_problematic_lines(lines[:test_size])
                break
                
        except TimeoutException:
            print(f"   ❌ タイムアウト: {test_size}行で{timeout}秒超過")
            # 問題のある行を分析
            analyze_problematic_lines(lines[:test_size])
            break
        except Exception as e:
            signal.alarm(0)
            print(f"   ❌ エラー: {e}")
            break

def analyze_problematic_lines(lines):
    """問題のある行パターンを分析"""
    print(f"\n🔬 問題分析 ({len(lines)}行):")
    
    block_starts = []
    block_ends = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # ブロック開始マーカー検出
        if stripped.startswith('#') and stripped.endswith('#') and len(stripped) > 2:
            # ブロック終了マーカーでないかチェック
            if stripped != '##':
                block_starts.append((i+1, stripped))
        
        # ブロック終了マーカー検出
        if stripped == '##':
            block_ends.append(i+1)
    
    print(f"   ブロック開始: {len(block_starts)}個")
    print(f"   ブロック終了: {len(block_ends)}個")
    
    if len(block_starts) != len(block_ends):
        print(f"   🚨 不一致: 開始{len(block_starts)} vs 終了{len(block_ends)}")
        
        print(f"\n   📝 ブロック開始一覧:")
        for line_no, content in block_starts:
            print(f"      {line_no}: {content}")
        
        print(f"\n   📝 ブロック終了一覧:")
        for line_no in block_ends:
            print(f"      {line_no}: ##")
    
    # 連続する空行やその他の問題をチェック
    empty_sequences = []
    current_empty = 0
    
    for i, line in enumerate(lines):
        if line.strip() == '':
            current_empty += 1
        else:
            if current_empty > 3:  # 3行以上の連続空行
                empty_sequences.append((i-current_empty+1, current_empty))
            current_empty = 0
    
    if empty_sequences:
        print(f"\n   📊 長い空行シーケンス:")
        for start_line, count in empty_sequences:
            print(f"      {start_line}行目から{count}行の空行")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "01_basic_features.txt"
    
    debug_line_by_line(file_path)