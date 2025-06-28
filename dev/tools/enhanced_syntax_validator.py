#!/usr/bin/env python3
"""
Enhanced Syntax Validator - 強化版記法検証ツール

現在のsyntax_validator.pyで検出できない問題を解決する強化版。
厳格モード、寛容モード、エラーサンプル専用モードを提供。

使用方法:
    python dev/tools/enhanced_syntax_validator.py <file.txt> [--mode=strict|tolerant|error-sample]
"""

import re
import sys
import argparse
import json
import fnmatch
from pathlib import Path
from typing import List, NamedTuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationMode(Enum):
    """検証モード"""
    STRICT = "strict"           # 厳格モード（examples/用）
    TOLERANT = "tolerant"       # 寛容モード（現行互換）
    ERROR_SAMPLE = "error-sample"  # エラーサンプル専用


@dataclass
class ValidationError:
    """検証エラー情報"""
    file_path: str
    line_number: int
    error_type: str
    message: str
    suggestion: str = ""
    severity: str = "ERROR"  # ERROR, WARNING, INFO


class EnhancedSyntaxValidator:
    """強化版記法検証クラス"""
    
    def __init__(self, mode: ValidationMode = ValidationMode.TOLERANT):
        self.mode = mode
        self.errors = []
    
    def validate_file(self, file_path: Path) -> List[ValidationError]:
        """ファイルの記法を検証"""
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # 基本チェック（全モード共通）
            errors.extend(self._check_unsupported_syntax(file_path, lines))
            errors.extend(self._check_invalid_markers(file_path, lines))
            
            # モード別チェック
            if self.mode == ValidationMode.STRICT:
                errors.extend(self._check_strict_rules(file_path, lines))
            elif self.mode == ValidationMode.ERROR_SAMPLE:
                errors.extend(self._check_error_sample_rules(file_path, lines))
            
            # 構造チェック（寛容モード以外）
            if self.mode != ValidationMode.TOLERANT:
                errors.extend(self._check_block_structure(file_path, lines))
                errors.extend(self._check_consecutive_markers(file_path, lines))
            
        except Exception as e:
            errors.append(ValidationError(
                file_path=str(file_path),
                line_number=0,
                error_type="FILE_ERROR",
                message=f"ファイル読み込みエラー: {e}"
            ))
        
        return errors
    
    def _check_unsupported_syntax(self, file_path: Path, lines: List[str]) -> List[ValidationError]:
        """非サポート記法のチェック（現行互換）"""
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
            
            # 絵文字のチェック（厳格モードのみ）
            if self.mode == ValidationMode.STRICT:
                emoji_pattern = re.compile(r'[\U00002600-\U000027BF]|[\U0001F300-\U0001F5FF]|[\U0001F600-\U0001F64F]|[\U0001F680-\U0001F6FF]|[\U0001F700-\U0001F77F]|[\U0001F780-\U0001F7FF]|[\U0001F800-\U0001F8FF]|[\U0001F900-\U0001F9FF]|[\U0001FA00-\U0001FA6F]|[\U0001FA70-\U0001FAFF]|[\U00002700-\U000027BF]')
                if emoji_pattern.search(line):
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        line_number=line_num,
                        error_type="EMOJI_USAGE",
                        message="絵文字の使用は推奨されません",
                        suggestion="代替表記を使用してください（例: [検証], [完了], [エラー]）",
                        severity="WARNING"
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
    
    def _check_strict_rules(self, file_path: Path, lines: List[str]) -> List[ValidationError]:
        """厳格モード専用のチェック"""
        errors = []
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 空行チェック（厳格モード）
            if self.mode == ValidationMode.STRICT:
                # 連続する空行の検出
                if line_num > 1 and not stripped and not lines[line_num - 2].strip():
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        line_number=line_num,
                        error_type="FORMATTING",
                        message="連続する空行は避けてください",
                        suggestion="空行は1行のみにしてください",
                        severity="WARNING"
                    ))
        
        return errors
    
    def _check_error_sample_rules(self, file_path: Path, lines: List[str]) -> List[ValidationError]:
        """エラーサンプル専用のチェック（問題を積極的に検出）"""
        errors = []
        
        # エラーサンプルでは、多くの問題が意図的に含まれているはず
        # 実際にエラーが検出されない場合は、サンプルファイル自体に問題がある可能性
        
        total_errors = 0
        total_errors += len(self._check_consecutive_markers(file_path, lines))
        total_errors += len(self._check_block_structure(file_path, lines))
        total_errors += len(self._check_malformed_blocks(file_path, lines))
        
        if total_errors == 0:
            errors.append(ValidationError(
                file_path=str(file_path),
                line_number=1,
                error_type="ERROR_SAMPLE_VALIDATION",
                message="エラーサンプルファイルでエラーが検出されませんでした",
                suggestion="意図的なエラーが含まれているか確認してください",
                severity="WARNING"
            ))
        
        return errors
    
    def _check_block_structure(self, file_path: Path, lines: List[str]) -> List[ValidationError]:
        """ブロック構造のチェック"""
        errors = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith(';;;') and not line.endswith(';;;'):
                # 複数行ブロックの開始を検出
                j = i + 1
                found_close = False
                has_content = False
                
                while j < len(lines):
                    current_line = lines[j].strip()
                    if current_line == ';;;':
                        found_close = True
                        break
                    elif current_line:  # 空行でない場合
                        has_content = True
                    j += 1
                
                # 閉じマーカーがない
                if not found_close:
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        line_number=i + 1,
                        error_type="MALFORMED_BLOCK",
                        message="閉じマーカー ';;;' が見つかりません",
                        suggestion="ブロックの最後に ;;; を追加してください"
                    ))
                
                # ブロック内にコンテンツがない
                elif not has_content:
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        line_number=i + 1,
                        error_type="EMPTY_BLOCK",
                        message="ブロック内にコンテンツがありません",
                        suggestion="ブロック内にコンテンツを追加するか、ブロックを削除してください",
                        severity="WARNING"
                    ))
                
                i = j + 1 if found_close else len(lines)
            else:
                i += 1
        
        return errors
    
    def _check_consecutive_markers(self, file_path: Path, lines: List[str]) -> List[ValidationError]:
        """連続マーカーのチェック"""
        errors = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 開始マーカーを検出
            if line.startswith(';;;') and not line.endswith(';;;'):
                # 次の行も開始マーカーかチェック
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith(';;;') and not next_line.endswith(';;;'):
                        errors.append(ValidationError(
                            file_path=str(file_path),
                            line_number=i + 2,  # 次の行の番号
                            error_type="CONSECUTIVE_MARKERS",
                            message="連続する開始マーカーが検出されました",
                            suggestion="前のブロックを ;;; で閉じてから新しいブロックを開始してください"
                        ))
            i += 1
        
        return errors
    
    def _check_malformed_blocks(self, file_path: Path, lines: List[str]) -> List[ValidationError]:
        """現行互換の不完全ブロックチェック"""
        errors = []
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
                        message="閉じマーカー ';;;' が見つかりません",
                        suggestion="ブロックの最後に ;;; を追加してください"
                    ))
                i = j + 1 if found_close else len(lines)
            else:
                i += 1
        
        return errors


def get_default_validation_config() -> Dict:
    """デフォルトの検証設定を返す（優先度順）"""
    return {
        'validation_modes': {
            # 最優先: エラーサンプル
            'error_sample': {
                'patterns': [
                    '記法ツール/サンプルファイル/記法エラーサンプル.txt',
                    '**/記法エラーサンプル.txt',
                    '**/*error*.txt',
                    '**/エラー*.txt',
                    'dev/tests/test_files/malformed*.txt'
                ]
            },
            # 次: 厳格モード
            'strict': {
                'patterns': [
                    'examples/*.txt',
                    'examples/templates/*.txt',
                    'examples/showcase/*.txt'
                ]
            },
            # 最後: 寛容モード（より具体的でないパターン）
            'tolerant': {
                'patterns': [
                    '記法ツール/**/*.txt',
                    'dev/tools/**/*.txt',
                    'test_*.txt',
                    'temp_*.txt'
                ]
            }
        }
    }


def determine_validation_mode(file_path: Path, config: Dict = None) -> ValidationMode:
    """設定ファイルとファイルパスから適切な検証モードを判定"""
    if config is None:
        config = get_default_validation_config()
    
    path_str = str(file_path)
    validation_modes = config.get('validation_modes', {})
    
    # 設定ファイルのパターンマッチング
    for mode_name, mode_config in validation_modes.items():
        patterns = mode_config.get('patterns', [])
        for pattern in patterns:
            if fnmatch.fnmatch(path_str, pattern):
                try:
                    return ValidationMode(mode_name.replace('-', '_'))
                except ValueError:
                    continue
    
    # フォールバック: ファイルパスベースの判定
    path_str_lower = path_str.lower()
    
    # エラーサンプル専用
    if 'エラー' in path_str_lower or 'error' in path_str_lower:
        return ValidationMode.ERROR_SAMPLE
    
    # 厳格モード（examples配下）
    if 'examples' in path_str_lower or 'templates' in path_str_lower:
        return ValidationMode.STRICT
    
    # デフォルトは寛容モード
    return ValidationMode.TOLERANT


def format_error_report(errors: List[ValidationError], mode: ValidationMode) -> str:
    """エラーレポートのフォーマット"""
    if not errors:
        return f"[完了] 記法エラーはありません（モード: {mode.value}）"
    
    report = []
    report.append(f"[エラー] {len(errors)} 個のエラーが見つかりました（モード: {mode.value}）:\n")
    
    # ファイル別にグループ化
    files = {}
    for error in errors:
        if error.file_path not in files:
            files[error.file_path] = []
        files[error.file_path].append(error)
    
    for file_path, file_errors in files.items():
        report.append(f"[フォルダ] {file_path}:")
        for error in file_errors:
            severity_prefix = f"[{error.severity}] " if error.severity != "ERROR" else ""
            line_info = f"Line {error.line_number}: " if error.line_number > 0 else ""
            report.append(f"   {severity_prefix}{line_info}{error.message}")
            if error.suggestion:
                report.append(f"      [ヒント] {error.suggestion}")
        report.append("")
    
    return "\n".join(report)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Enhanced Syntax Validator - 強化版記法検証ツール",
        epilog="例: python dev/tools/enhanced_syntax_validator.py examples/*.txt --mode=strict"
    )
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='検証するテキストファイル'
    )
    parser.add_argument(
        '--mode',
        choices=['strict', 'tolerant', 'error-sample'],
        help='検証モード（指定しない場合はファイルパスから自動判定）'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='エラーがない場合は出力しない'
    )
    
    args = parser.parse_args()
    
    all_errors = []
    results = []
    
    for file_path in args.files:
        if not file_path.exists():
            print(f"[警告] ファイルが見つかりません: {file_path}", file=sys.stderr)
            continue
        
        if not file_path.suffix.lower() == '.txt':
            if not args.quiet:
                print(f"⏭️  スキップ: {file_path} (.txt ファイルではありません)")
            continue
        
        # 検証モードの決定
        mode = ValidationMode(args.mode) if args.mode else determine_validation_mode(file_path)
        
        validator = EnhancedSyntaxValidator(mode)
        errors = validator.validate_file(file_path)
        all_errors.extend(errors)
        
        # ファイル別結果
        file_errors = [e for e in errors if e.file_path == str(file_path)]
        if file_errors:
            error_count = len([e for e in file_errors if e.severity == "ERROR"])
            warning_count = len([e for e in file_errors if e.severity == "WARNING"])
            status = f"{error_count} エラー, {warning_count} 警告" if warning_count > 0 else f"{error_count} エラー"
            print(f"❌ {file_path}: {status} (モード: {mode.value})")
        else:
            if not args.quiet:
                print(f"✅ {file_path}: OK (モード: {mode.value})")
    
    # 総合レポート
    if all_errors:
        error_count = len([e for e in all_errors if e.severity == "ERROR"])
        if error_count > 0:
            print("\n" + "="*50)
            print(format_error_report(all_errors, mode))
            sys.exit(1)
        else:
            print(f"\n[完了] 警告のみ: {len(args.files)} ファイル")
    else:
        if not args.quiet:
            print(f"\n[完了] 検証完了: {len(args.files)} ファイル、エラーなし")


if __name__ == "__main__":
    main()