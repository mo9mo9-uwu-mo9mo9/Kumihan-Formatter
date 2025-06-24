#!/usr/bin/env python3
"""
絵文字・特殊文字使用チェックツール

使用方法:
    python dev/tools/emoji_checker.py <file.py>
    python dev/tools/emoji_checker.py --check-all
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, NamedTuple, Dict
from dataclasses import dataclass


@dataclass
class EmojiViolation:
    """絵文字使用違反情報"""
    file_path: str
    line_number: int
    line_content: str
    emoji_found: str
    suggested_replacement: str = ""


class EmojiChecker:
    """絵文字・特殊文字チェッククラス"""
    
    def __init__(self):
        # 絵文字パターン（基本的なUnicode絵文字範囲）
        self.emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F]|'  # 顔文字
            r'[\U0001F300-\U0001F5FF]|'  # その他のシンボル
            r'[\U0001F680-\U0001F6FF]|'  # 乗り物と建物
            r'[\U0001F1E0-\U0001F1FF]|'  # 国旗
            r'[\U00002600-\U000027BF]|'  # その他のシンボル
            r'[\U0001F900-\U0001F9FF]|'  # 補助絵文字
            r'[\U00002700-\U000027BF]'   # Dingbats
        )
        
        # よく使用される絵文字と推奨代替表現
        self.replacement_map = {
            '🔍': '[検証]',
            '📝': '[処理]', 
            '🎨': '[生成]',
            '⚠️': '[警告]',
            '✅': '[完了]',
            '❌': '[エラー]',
            '💡': '[ヒント]',
            '🚀': '[開始]',
            '📁': '[フォルダ]',
            '🌐': '[ブラウザ]',
            '🖱️': '',
            '🏗️': '[構築]',
            '📚': '[ドキュメント]',
            '🔧': '[設定]',
            '🐍': '[Python]',
            '⏳': '[待機]',
            '🏠': '',
            '📄': '[ファイル]',
            '🖼️': '[画像]',
            '📊': '[統計]',
            '🏷️': '[キーワード]',
            '🧪': '[テスト]',
            '📑': '',
            '📏': '',
            '🔢': '',
            '🔄': '[更新]',
            '👀': '[監視]',
            '👋': '',
        }
        
        # チェック対象外ファイル
        self.excluded_files = {
            'README.md',           # ユーザー向け文書は除外
            'CHANGELOG.md',        # 既存の変更履歴
            'docs/INDEX.md',       # トップレベル文書
        }
    
    def check_file(self, file_path: Path) -> List[EmojiViolation]:
        """単一ファイルの絵文字使用をチェック"""
        violations = []
        
        # 除外ファイルのチェック
        if any(str(file_path).endswith(excluded) for excluded in self.excluded_files):
            return violations
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            for line_num, line in enumerate(lines, 1):
                emojis = self.emoji_pattern.findall(line)
                for emoji in emojis:
                    suggestion = self.replacement_map.get(emoji, '[適切なタグ]')
                    violations.append(EmojiViolation(
                        file_path=str(file_path),
                        line_number=line_num,
                        line_content=line.strip(),
                        emoji_found=emoji,
                        suggested_replacement=suggestion
                    ))
                        
        except Exception as e:
            print(f"警告: ファイル読み込みエラー {file_path}: {e}")
        
        return violations
    
    def check_directory(self, directory: Path, extensions: List[str] = None) -> List[EmojiViolation]:
        """ディレクトリ内のファイルをチェック"""
        if extensions is None:
            extensions = ['.py', '.sh', '.command', '.md']
            
        all_violations = []
        
        for ext in extensions:
            files = directory.rglob(f'*{ext}')
            for file_path in files:
                # テストファイルやキャッシュは除外
                if any(part in str(file_path) for part in ['.git', '__pycache__', '.pytest_cache', 'node_modules']):
                    continue
                    
                violations = self.check_file(file_path)
                all_violations.extend(violations)
        
        return all_violations


def format_violations_report(violations: List[EmojiViolation]) -> str:
    """違反レポートのフォーマット"""
    if not violations:
        return "[完了] 絵文字の使用は検出されませんでした"
    
    report = []
    report.append(f"[警告] {len(violations)} 個の絵文字使用が検出されました:\n")
    
    # ファイル別にグループ化
    files = {}
    for violation in violations:
        if violation.file_path not in files:
            files[violation.file_path] = []
        files[violation.file_path].append(violation)
    
    for file_path, file_violations in files.items():
        report.append(f"📁 {file_path}:")
        for violation in file_violations:
            report.append(f"   行 {violation.line_number}: {violation.emoji_found} → {violation.suggested_replacement}")
            if len(violation.line_content) < 80:
                report.append(f"      内容: {violation.line_content}")
            else:
                report.append(f"      内容: {violation.line_content[:77]}...")
        report.append("")
    
    return '\n'.join(report)


def main():
    parser = argparse.ArgumentParser(description='絵文字・特殊文字使用チェックツール')
    parser.add_argument('files', nargs='*', help='チェック対象ファイル')
    parser.add_argument('--check-all', action='store_true', help='プロジェクト全体をチェック')
    parser.add_argument('--extensions', nargs='*', default=['.py', '.sh', '.command'], 
                        help='チェック対象拡張子 (--check-all使用時)')
    
    args = parser.parse_args()
    
    checker = EmojiChecker()
    all_violations = []
    
    if args.check_all:
        # プロジェクト全体をチェック
        project_root = Path(__file__).parent.parent.parent
        print(f"[処理] プロジェクト全体をチェック中: {project_root}")
        all_violations = checker.check_directory(project_root, args.extensions)
    elif args.files:
        # 指定されたファイルをチェック
        for file_path in args.files:
            path = Path(file_path)
            if path.exists():
                violations = checker.check_file(path)
                all_violations.extend(violations)
            else:
                print(f"[警告] ファイルが見つかりません: {file_path}")
    else:
        parser.print_help()
        return 1
    
    # 結果表示
    report = format_violations_report(all_violations)
    print(report)
    
    # 絵文字が見つかった場合は終了コード1
    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())