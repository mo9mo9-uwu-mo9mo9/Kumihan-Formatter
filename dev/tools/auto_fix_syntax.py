#!/usr/bin/env python3
"""
Kumihan記法の構文エラー自動修正ツール

今回の修正作業で特定されたパターンを自動で修正します。
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


class KumihanSyntaxAutoFixer:
    """Kumihan記法の構文エラー自動修正クラス"""
    
    def __init__(self):
        self.fixes_applied = []
    
    def fix_missing_closing_markers(self, content: str) -> str:
        """見出しブロックの閉じマーカー不足を修正"""
        lines = content.split('\n')
        fixed_lines = []
        in_heading_block = False
        
        for i, line in enumerate(lines):
            # 見出しブロックの開始を検出
            if re.match(r'^;;;見出し[1-5]$', line.strip()):
                # 前のブロックが閉じられていない場合は閉じる
                if in_heading_block and fixed_lines and fixed_lines[-1].strip() != ';;;':
                    fixed_lines.append(';;;')
                    self.fixes_applied.append(f"Line {len(fixed_lines)}: Added missing closing marker")
                
                fixed_lines.append(line)
                in_heading_block = True
            
            # 次の行が内容の場合、現在の見出しブロックに閉じマーカーを追加
            elif in_heading_block and line.strip() and not line.strip().startswith(';;;'):
                fixed_lines.append(line)
                # 次の行をチェックして、必要なら閉じマーカーを追加
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if not next_line.startswith(';;;') and next_line:
                        fixed_lines.append(';;;')
                        self.fixes_applied.append(f"Line {len(fixed_lines)}: Added closing marker for heading block")
                        in_heading_block = False
            else:
                fixed_lines.append(line)
                if line.strip() == ';;;':
                    in_heading_block = False
        
        return '\n'.join(fixed_lines)
    
    def fix_duplicate_markers(self, content: str) -> str:
        """不要な重複マーカーを削除"""
        # 連続する;;; ;;; パターンを;;; に変換
        pattern = r'^;;;\n;;;$'
        fixed_content = re.sub(pattern, ';;;', content, flags=re.MULTILINE)
        
        if fixed_content != content:
            self.fixes_applied.append("Removed duplicate ;;; markers")
        
        return fixed_content
    
    def fix_color_attribute_order(self, content: str) -> str:
        """Color属性の順序を修正"""
        # ;;;ハイライト+太字 color=#xxx パターンを ;;;太字+ハイライト color=#xxx に変換
        pattern = r';;;ハイライト\+太字(\s+color=#[a-fA-F0-9]{6})'
        replacement = r';;;太字+ハイライト\1'
        
        fixed_content = re.sub(pattern, replacement, content)
        
        if fixed_content != content:
            self.fixes_applied.append("Fixed color attribute order (ハイライト+太字 → 太字+ハイライト)")
        
        return fixed_content
    
    def fix_standalone_markers(self, content: str) -> str:
        """問題のある独立マーカーを修正"""
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            if line.strip() == ';;;':
                # 前後の文脈をチェックして不要な独立マーカーを特定
                prev_line = lines[i-1].strip() if i > 0 else ''
                next_line = lines[i+1].strip() if i < len(lines) - 1 else ''
                
                # 不要なパターン: ブロック終了直後にさらに;;;がある
                if prev_line == ';;;' or (prev_line and not prev_line.startswith(';;;')):
                    # このマーカーは必要
                    fixed_lines.append(line)
                else:
                    # 不要なマーカーとして削除
                    self.fixes_applied.append(f"Line {i+1}: Removed unnecessary standalone ;;; marker")
                    continue
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def auto_fix_file(self, file_path: Path) -> bool:
        """ファイルの構文エラーを自動修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            self.fixes_applied = []
            
            # 各修正を順次適用
            content = self.fix_color_attribute_order(content)
            content = self.fix_duplicate_markers(content)
            content = self.fix_missing_closing_markers(content)
            content = self.fix_standalone_markers(content)
            
            # 変更があった場合のみファイルを更新
            if content != original_content:
                # バックアップを作成
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # 修正版を保存
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Fixed {file_path}")
                print(f"   Backup saved as {backup_path}")
                for fix in self.fixes_applied:
                    print(f"   - {fix}")
                return True
            else:
                print(f"✨ No fixes needed for {file_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            return False


def main():
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("Usage: python auto_fix_syntax.py <file1> [file2] ...")
        print("       python auto_fix_syntax.py examples/**/*.txt")
        sys.exit(1)
    
    fixer = KumihanSyntaxAutoFixer()
    fixed_count = 0
    
    for file_arg in sys.argv[1:]:
        file_path = Path(file_arg)
        if file_path.exists() and file_path.suffix == '.txt':
            if fixer.auto_fix_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  Skipping {file_arg} (not found or not .txt file)")
    
    print(f"\n🎉 Auto-fix completed! Fixed {fixed_count} files.")


if __name__ == "__main__":
    main()