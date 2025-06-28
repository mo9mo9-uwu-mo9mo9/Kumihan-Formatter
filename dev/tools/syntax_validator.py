#!/usr/bin/env python3
"""
Kumihan-Formatter 記法検証スクリプト

使用方法:
    # 基本的な記法チェック（検証のみ）
    python dev/tools/syntax_validator.py <file.txt>
    python dev/tools/syntax_validator.py examples/*.txt
    
    # 自動修正機能付きの新ツール（推奨）
    python dev/tools/syntax_fixer.py examples/*.txt --fix --preview
    
注意: macOSではD&D機能が制限されるため、コマンドライン使用を推奨
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, NamedTuple, Dict, Any
from dataclasses import dataclass
from enum import Enum

try:
    import yaml
except ImportError:
    yaml = None


class ValidationMode(Enum):
    """検証モード"""
    TOLERANT = "tolerant"      # 寛容モード（現行）
    STRICT = "strict"          # 厳格モード
    ERROR_SAMPLE = "error-sample"  # エラーサンプル専用


@dataclass
class ValidationError:
    """検証エラー情報"""
    file_path: str
    line_number: int
    error_type: str
    message: str
    suggestion: str = ""


class SyntaxValidator:
    """
    Kumihan記法検証クラス（品質保証の中核ツール）

    設計ドキュメント:
    - 記法仕様: /SPEC.md#Kumihan記法基本構文
    - アーキテクチャ: /CONTRIBUTING.md#テスト戦略
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - ValidationMode: 検証モード定義（tolerant/strict/error-sample）
    - ValidationError: 検証エラー情報
    - QualityAnalyzer: 品質メトリクス収集で使用
    - .validation-config.yml: 設定ファイル

    責務:
    - Kumihan記法の構文検証（3モード対応）
    - ファイルパターンによる自動モード判定
    - エラー詳細レポートの生成
    - 品質ゲートシステムとの連携
    """
    
    def __init__(self, mode: ValidationMode = ValidationMode.TOLERANT, config_path: Path = None):
        self.errors = []
        self.mode = mode
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: Path = None) -> Dict[str, Any]:
        """検証設定を読み込み"""
        default_config = {
            "file_patterns": {
                "strict_mode": [
                    "examples/*.txt",
                    "examples/templates/*.txt"
                ],
                "error_samples": [
                    "**/記法エラーサンプル.txt",
                    "**/error-*.txt",
                    "記法ツール/**/サンプルファイル/記法エラーサンプル.txt"
                ],
                "tolerant_mode": [
                    "記法ツール/**/*.txt"
                ]
            },
            "strict_rules": {
                "require_closing_markers": True,
                "check_attribute_order": True,
                "detect_markdown_syntax": True,
                "check_empty_blocks": True
            }
        }
        
        if config_path and config_path.exists() and yaml:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception:
                pass  # デフォルト設定を使用
        
        return default_config
    
    def _determine_mode_for_file(self, file_path: Path) -> ValidationMode:
        """ファイルパスに基づいて検証モードを決定"""
        if self.mode != ValidationMode.TOLERANT:
            return self.mode  # 明示的にモードが指定されている場合
        
        file_str = str(file_path)
        
        # エラーサンプルファイルの判定
        for pattern in self.config["file_patterns"]["error_samples"]:
            if self._match_pattern(file_str, pattern):
                return ValidationMode.ERROR_SAMPLE
        
        # 厳格モードファイルの判定
        for pattern in self.config["file_patterns"]["strict_mode"]:
            if self._match_pattern(file_str, pattern):
                return ValidationMode.STRICT
        
        return ValidationMode.TOLERANT
    
    def _match_pattern(self, file_path: str, pattern: str) -> bool:
        """シンプルなパターンマッチング"""
        import fnmatch
        return fnmatch.fnmatch(file_path, pattern)
    
    def validate_file(self, file_path: Path) -> List[ValidationError]:
        """ファイルの記法を検証"""
        errors = []
        file_mode = self._determine_mode_for_file(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # エラーサンプルファイルの場合は専用チェック
            if file_mode == ValidationMode.ERROR_SAMPLE:
                errors.extend(self._check_error_sample_validity(file_path, lines))
            else:
                errors.extend(self._check_unsupported_syntax(file_path, lines, file_mode))
                errors.extend(self._check_invalid_markers(file_path, lines, file_mode))
                errors.extend(self._check_malformed_blocks(file_path, content, file_mode))
                
                # 厳格モードでの追加チェック
                if file_mode == ValidationMode.STRICT:
                    errors.extend(self._check_strict_rules(file_path, lines, content))
            
        except Exception as e:
            errors.append(ValidationError(
                file_path=str(file_path),
                line_number=0,
                error_type="FILE_ERROR",
                message=f"ファイル読み込みエラー: {e}"
            ))
        
        return errors
    
    def _check_error_sample_validity(self, file_path: Path, lines: List[str]) -> List[ValidationError]:
        """エラーサンプルファイル専用の検証"""
        errors = []
        error_count = 0
        
        # 意図的なエラーの検出
        for line_num, line in enumerate(lines, 1):
            # 未閉じブロックの検出
            if line.strip().startswith(';;;') and not line.strip().endswith(';;;'):
                # 次に閉じマーカーがあるかチェック
                found_close = False
                for j in range(line_num, len(lines)):
                    if lines[j].strip() == ';;;':
                        found_close = True
                        break
                if not found_close:
                    error_count += 1
            
            # 不正な組み合わせの検出
            if re.search(r'color=#[^;]*\+', line):
                error_count += 1
            
            # 目次マーカーの手動使用
            if ';;;目次;;;' in line:
                error_count += 1
        
        # エラーサンプルファイルなのにエラーが少ない場合は警告
        if error_count < 3:
            errors.append(ValidationError(
                file_path=str(file_path),
                line_number=1,
                error_type="ERROR_SAMPLE_VALIDATION",
                message=f"エラーサンプルファイルとしてエラーが少なすぎます（{error_count}個）",
                suggestion="意図的なエラーを追加するか、ファイル名を変更してください"
            ))
        
        return errors
    
    def _check_unsupported_syntax(self, file_path: Path, lines: List[str], mode: ValidationMode) -> List[ValidationError]:
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
            
            # 絵文字のチェック（厳格モードでのみ）
            if mode == ValidationMode.STRICT:
                emoji_pattern = re.compile(r'[\U00002600-\U000027BF]|[\U0001F300-\U0001F5FF]|[\U0001F600-\U0001F64F]|[\U0001F680-\U0001F6FF]|[\U0001F700-\U0001F77F]|[\U0001F780-\U0001F7FF]|[\U0001F800-\U0001F8FF]|[\U0001F900-\U0001F9FF]|[\U0001FA00-\U0001FA6F]|[\U0001FA70-\U0001FAFF]|[\U00002700-\U000027BF]')
                if emoji_pattern.search(line):
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        line_number=line_num,
                        error_type="EMOJI_USAGE",
                        message="絵文字の使用は推奨されません",
                        suggestion="代替表記を使用してください（例: [検証], [完了], [エラー]）"
                    ))
        
        return errors
    
    def _check_invalid_markers(self, file_path: Path, lines: List[str], mode: ValidationMode) -> List[ValidationError]:
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
    
    def _check_malformed_blocks(self, file_path: Path, content: str, mode: ValidationMode) -> List[ValidationError]:
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
    
    def _check_strict_rules(self, file_path: Path, lines: List[str], content: str) -> List[ValidationError]:
        """厳格モード専用のチェック"""
        errors = []
        
        # 空ブロックのチェック
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith(';;;') and not line.endswith(';;;'):
                # ブロック開始を検出
                j = i + 1
                content_lines = []
                while j < len(lines) and lines[j].strip() != ';;;':
                    if lines[j].strip():  # 空行でない
                        content_lines.append(lines[j])
                    j += 1
                
                if j < len(lines) and not content_lines:  # 閉じマーカーは見つかったが中身が空
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        line_number=i + 1,
                        error_type="EMPTY_BLOCK",
                        message="空のブロックは推奨されません",
                        suggestion="ブロック内にコンテンツを追加するか、ブロックを削除してください"
                    ))
                i = j + 1
            else:
                i += 1
        
        # 属性順序のチェック
        for line_num, line in enumerate(lines, 1):
            # color属性が最後にない場合
            if ';;;' in line and 'color=' in line and '+' in line:
                # color属性の後に+があるかチェック
                color_match = re.search(r'color=#[a-fA-F0-9]+', line)
                if color_match:
                    color_end = color_match.end()
                    remaining = line[color_end:]
                    if '+' in remaining or '＋' in remaining:
                        errors.append(ValidationError(
                            file_path=str(file_path),
                            line_number=line_num,
                            error_type="ATTRIBUTE_ORDER",
                            message="color属性は複合キーワードの最後に配置してください",
                            suggestion=";;;太字+ハイライト color=#ff0000;;; の形式を使用してください"
                        ))
        
        # 複数行ブロックの不適切な使用チェック
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith(';;;') and stripped.endswith(';;;') and len(stripped) > 6:
                # 単一行ブロック記法が複雑すぎる場合
                if '+' in stripped and len(stripped) > 50:
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        line_number=line_num,
                        error_type="COMPLEX_SINGLE_LINE",
                        message="複雑なブロック記法は複数行形式を推奨します",
                        suggestion=";;;キーワード\n内容\n;;; の形式を使用してください"
                    ))
        
        return errors


def format_error_report(errors: List[ValidationError]) -> str:
    """エラーレポートのフォーマット"""
    if not errors:
        return "[完了] 記法エラーはありません"
    
    report = []
    report.append(f"[エラー] {len(errors)} 個のエラーが見つかりました:\n")
    
    # ファイル別にグループ化
    files = {}
    for error in errors:
        if error.file_path not in files:
            files[error.file_path] = []
        files[error.file_path].append(error)
    
    for file_path, file_errors in files.items():
        report.append(f"[フォルダ] {file_path}:")
        for error in file_errors:
            line_info = f"Line {error.line_number}: " if error.line_number > 0 else ""
            report.append(f"   {line_info}{error.message}")
            if error.suggestion:
                report.append(f"      [ヒント] {error.suggestion}")
        report.append("")
    
    return "\n".join(report)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter 記法検証ツール",
        epilog="例: python dev/tools/syntax_validator.py examples/*.txt --mode=strict"
    )
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='検証するテキストファイル'
    )
    parser.add_argument(
        '--mode',
        choices=['tolerant', 'strict', 'error-sample'],
        default='tolerant',
        help='検証モード: tolerant(寛容), strict(厳格), error-sample(エラーサンプル専用)'
    )
    parser.add_argument(
        '--config',
        type=Path,
        help='検証設定ファイル（.validation-config.yml）のパス'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='エラーがない場合は出力しない'
    )
    
    args = parser.parse_args()
    
    # モードを設定
    mode = ValidationMode(args.mode)
    validator = SyntaxValidator(mode=mode, config_path=args.config)
    all_errors = []
    
    for file_path in args.files:
        if not file_path.exists():
            print(f"[警告] ファイルが見つかりません: {file_path}", file=sys.stderr)
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
                print(f"[エラー] {file_path}: {len(file_errors)} エラー")
            else:
                print(f"[完了] {file_path}: OK")
    
    # 総合レポート
    if all_errors:
        print("\n" + "="*50)
        print(format_error_report(all_errors))
        sys.exit(1)
    else:
        if not args.quiet:
            print(f"\n[完了] 検証完了: {len(args.files)} ファイル、エラーなし")


if __name__ == "__main__":
    main()