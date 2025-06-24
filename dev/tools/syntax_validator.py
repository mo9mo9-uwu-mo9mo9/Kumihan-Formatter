#!/usr/bin/env python3
"""
Kumihan-Formatter 記法検証スクリプト

使用方法:
    python dev/tools/syntax_validator.py <file.txt>
    python dev/tools/syntax_validator.py examples/*.txt
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, NamedTuple
from dataclasses import dataclass


@dataclass
class ValidationError:
    """検証エラー情報"""
    file_path: str
    line_number: int
    error_type: str
    message: str
    suggestion: str = ""


class SyntaxValidator:
    """記法検証クラス"""
    
    def __init__(self):
        self.errors = []
    
    def validate_file(self, file_path: Path) -> List[ValidationError]:
        """ファイルの記法を検証"""
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            errors.extend(self._check_unsupported_syntax(file_path, lines))
            errors.extend(self._check_invalid_markers(file_path, lines))
            errors.extend(self._check_malformed_blocks(file_path, content))
            
        except Exception as e:
            errors.append(ValidationError(
                file_path=str(file_path),
                line_number=0,
                error_type="FILE_ERROR",
                message=f"ファイル読み込みエラー: {e}"
            ))
        
        return errors
    
    def _check_unsupported_syntax(self, file_path: Path, lines: List[str]) -> List[ValidationError]:
        """非サポート記法のチェック"""
        errors = []
        in_block = False
        
        for line_num, line in enumerate(lines, 1):
            # ブロック内かどうかを確認
            stripped = line.strip()
            if stripped.startswith(';;;') and not stripped.endswith(';;;'):
                in_block = True
            elif stripped == ';;;' and in_block:
                in_block = False
                continue
            
            # ブロック内では非サポート記法チェックをスキップ
            if in_block:
                continue
            
            # 行頭 # 記法のチェック
            if re.match(r'^#[^!]', line):
                errors.append(ValidationError(
                    file_path=str(file_path),
                    line_number=line_num,
                    error_type="UNSUPPORTED_SYNTAX",
                    message="行頭 # 記法は非サポートです",
                    suggestion=";;;見出し1;;; などのブロック記法を使用してください"
                ))
            
            # Markdown風記法のチェック
            if re.search(r'\*\*[^*]+\*\*', line):
                errors.append(ValidationError(
                    file_path=str(file_path),
                    line_number=line_num,
                    error_type="UNSUPPORTED_SYNTAX",
                    message="**太字** 記法は非サポートです",
                    suggestion=";;;太字;;; ブロック記法を使用してください"
                ))
            
            # 絵文字のチェック
            emoji_pattern = re.compile(r'[\U00002600-\U000027BF]|[\U0001F300-\U0001F5FF]|[\U0001F600-\U0001F64F]|[\U0001F680-\U0001F6FF]|[\U0001F700-\U0001F77F]|[\U0001F780-\U0001F7FF]|[\U0001F800-\U0001F8FF]|[\U0001F900-\U0001F9FF]|[\U0001FA00-\U0001FA6F]|[\U0001FA70-\U0001FAFF]|[\U00002700-\U000027BF]')
            if emoji_pattern.search(line):
                errors.append(ValidationError(
                    file_path=str(file_path),
                    line_number=line_num,
                    error_type="EMOJI_USAGE",
                    message="絵文字の使用は推奨されません",
                    suggestion="代替表記を使用してください（例: 🔍→[検証], ✅→[完了], ❌→[エラー]）"
                ))
        
        return errors
    
    def _check_invalid_markers(self, file_path: Path, lines: List[str]) -> List[ValidationError]:
        """不正なマーカーのチェック"""
        errors = []
        
        for line_num, line in enumerate(lines, 1):
            # color属性の誤組み合わせ
            if re.search(r'color=#[^;]*\+', line):
                errors.append(ValidationError(
                    file_path=str(file_path),
                    line_number=line_num,
                    error_type="INVALID_MARKER",
                    message="color属性の後に + は使用できません",
                    suggestion=";;;太字+ハイライト color=#ff0000;;; の形式を使用してください"
                ))
            
            # 目次マーカーの手動使用
            if ';;;目次;;;' in line:
                errors.append(ValidationError(
                    file_path=str(file_path),
                    line_number=line_num,
                    error_type="INVALID_MARKER",
                    message=";;;目次;;; は自動生成専用です",
                    suggestion="目次マーカーは削除してください"
                ))
        
        return errors
    
    def _check_malformed_blocks(self, file_path: Path, content: str) -> List[ValidationError]:
        """不完全なブロック記法のチェック"""
        errors = []
        lines = content.splitlines()
        
        # 開始マーカーのみで終了マーカーがないパターン
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith(';;;') and not line.endswith(';;;'):
                # 複数行ブロックの開始を検出
                j = i + 1
                found_close = False
                while j < len(lines):
                    if lines[j].strip() == ';;;':
                        found_close = True
                        break
                    j += 1
                
                if not found_close:
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        line_number=i + 1,
                        error_type="MALFORMED_BLOCK",
                        message=f"閉じマーカー ';;;' が見つかりません",
                        suggestion="ブロックの最後に ;;; を追加してください"
                    ))
                i = j + 1 if found_close else len(lines)
            else:
                i += 1
        
        return errors


def format_error_report(errors: List[ValidationError]) -> str:
    """エラーレポートのフォーマット"""
    if not errors:
        return "✅ 記法エラーはありません"
    
    report = []
    report.append(f"❌ {len(errors)} 個のエラーが見つかりました:\n")
    
    # ファイル別にグループ化
    files = {}
    for error in errors:
        if error.file_path not in files:
            files[error.file_path] = []
        files[error.file_path].append(error)
    
    for file_path, file_errors in files.items():
        report.append(f"📁 {file_path}:")
        for error in file_errors:
            line_info = f"Line {error.line_number}: " if error.line_number > 0 else ""
            report.append(f"   {line_info}{error.message}")
            if error.suggestion:
                report.append(f"      💡 {error.suggestion}")
        report.append("")
    
    return "\n".join(report)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter 記法検証ツール",
        epilog="例: python dev/tools/syntax_validator.py examples/*.txt"
    )
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='検証するテキストファイル'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='エラーがない場合は出力しない'
    )
    
    args = parser.parse_args()
    
    validator = SyntaxValidator()
    all_errors = []
    
    for file_path in args.files:
        if not file_path.exists():
            print(f"⚠️  ファイルが見つかりません: {file_path}", file=sys.stderr)
            continue
        
        if not file_path.suffix.lower() == '.txt':
            if not args.quiet:
                print(f"⏭️  スキップ: {file_path} (.txt ファイルではありません)")
            continue
        
        errors = validator.validate_file(file_path)
        all_errors.extend(errors)
        
        if not args.quiet or errors:
            file_errors = [e for e in errors if e.file_path == str(file_path)]
            if file_errors:
                print(f"❌ {file_path}: {len(file_errors)} エラー")
            else:
                print(f"✅ {file_path}: OK")
    
    # 総合レポート
    if all_errors:
        print("\n" + "="*50)
        print(format_error_report(all_errors))
        sys.exit(1)
    else:
        if not args.quiet:
            print(f"\n✅ 検証完了: {len(args.files)} ファイル、エラーなし")


if __name__ == "__main__":
    main()