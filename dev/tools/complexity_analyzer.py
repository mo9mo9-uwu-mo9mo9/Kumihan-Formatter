#!/usr/bin/env python3
"""
記法複雑度分析スクリプト
"""

import re
import sys
import subprocess
from pathlib import Path


def analyze_syntax_complexity(file_path):
    """ファイルの記法複雑度を分析"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 複合マーカーの使用頻度
    complex_markers = re.findall(r';;;[^;]*\+[^;]*;;;', content)
    
    # color属性の使用頻度  
    color_attrs = re.findall(r'color=#[a-fA-F0-9]{3,6}', content)
    
    # ネストしたリストの深度
    lines = content.splitlines()
    max_indent = 0
    for line in lines:
        if line.strip().startswith('-'):
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent)
    
    return {
        'complex_markers': len(complex_markers),
        'color_attributes': len(color_attrs),
        'max_list_depth': max_indent // 2  # 2スペース = 1レベル
    }


def get_changed_txt_files():
    """変更されたテキストファイルを取得"""
    try:
        result = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'], 
                              capture_output=True, text=True)
        changed_files = [f for f in result.stdout.strip().split('\n') 
                        if f.endswith('.txt') and Path(f).exists()]
        return changed_files
    except Exception as e:
        print(f'Git差分取得エラー: {e}')
        return []


def main():
    """メイン関数"""
    changed_files = get_changed_txt_files()
    
    if not changed_files:
        print('✅ 分析対象のテキストファイルなし')
        return
    
    for file_path in changed_files:
        try:
            stats = analyze_syntax_complexity(file_path)
            print(f'📈 {file_path}:')
            print(f'   複合マーカー: {stats["complex_markers"]} 個')
            print(f'   色指定: {stats["color_attributes"]} 個')
            print(f'   リスト最大深度: {stats["max_list_depth"]} レベル')
            
            # 複雑度の警告
            if stats['complex_markers'] > 10:
                print(f'   ⚠️  複合マーカーが多用されています ({stats["complex_markers"]} 個)')
            if stats['max_list_depth'] > 3:
                print(f'   ⚠️  リストの入れ子が深すぎます ({stats["max_list_depth"]} レベル)')
                
        except Exception as e:
            print(f'{file_path} の分析エラー: {e}')


if __name__ == '__main__':
    main()