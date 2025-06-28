#!/usr/bin/env python3
"""
Kumihan-Formatter 記法検証・自動修正スクリプト

使用方法:
    # 検証のみ
    python dev/tools/syntax_fixer.py examples/*.txt
    
    # 修正のプレビュー
    python dev/tools/syntax_fixer.py examples/*.txt --preview
    
    # 自動修正の実行
    python dev/tools/syntax_fixer.py examples/*.txt --fix
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


@dataclass
class FixResult:
    """修正結果情報"""
    original_content: str
    fixed_content: str
    changes_made: List[str]
    errors_fixed: int


class SyntaxFixer:
    """記法検証・自動修正クラス"""
    
    def __init__(self):
        self.errors = []
    
    def fix_file(self, file_path: Path, preview_only: bool = False) -> FixResult:
        """ファイルの記法を自動修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            fixed_content = original_content
            changes_made = []
            
            # 修正処理
            fixed_content, block_changes = self._fix_malformed_blocks(fixed_content)
            changes_made.extend(block_changes)
            
            fixed_content, marker_changes = self._fix_consecutive_markers(fixed_content)
            changes_made.extend(marker_changes)
            
            fixed_content, color_changes = self._fix_color_attribute_order(fixed_content)
            changes_made.extend(color_changes)
            
            fixed_content, cleanup_changes = self._cleanup_empty_markers(fixed_content)
            changes_made.extend(cleanup_changes)
            
            # ファイルに書き込み（プレビューでない場合）
            if not preview_only and fixed_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
            
            return FixResult(
                original_content=original_content,
                fixed_content=fixed_content,
                changes_made=changes_made,
                errors_fixed=len(changes_made)
            )
            
        except Exception as e:
            return FixResult(
                original_content="",
                fixed_content="",
                changes_made=[f"ファイル処理エラー: {e}"],
                errors_fixed=0
            )
    
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
                    suggestion="代替表記を使用してください（例: [検証], [完了], [エラー]）"
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
        """不完全なブロック記法のチェック（強化版）"""
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
                content_lines = 0
                
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line == ';;;':
                        found_close = True
                        break
                    elif next_line and not next_line.startswith(';;;'):
                        content_lines += 1
                    elif next_line.startswith(';;;') and not next_line.endswith(';;;'):
                        # 新しいブロック開始 = 前のブロックが閉じられていない
                        break
                    j += 1
                
                if not found_close and content_lines > 0:
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        line_number=i + 1,
                        error_type="MALFORMED_BLOCK",
                        message=f"閉じマーカー ';;;' が見つかりません",
                        suggestion="ブロックの最後に ;;; を追加してください"
                    ))
                
                # 見出しブロックの特別処理
                if re.match(r'^;;;見出し[1-5]$', line):
                    # 見出しブロックで内容があるのに閉じマーカーがない場合
                    if j < len(lines) and lines[j].strip() and not lines[j].strip().startswith(';;;'):
                        # 次の行が内容で、その後に閉じマーカーがないパターン
                        k = j + 1
                        while k < len(lines) and lines[k].strip() == '':
                            k += 1
                        if k < len(lines) and lines[k].strip().startswith(';;;') and not lines[k].strip() == ';;;':
                            errors.append(ValidationError(
                                file_path=str(file_path),
                                line_number=i + 1,
                                error_type="MISSING_HEADING_CLOSER",
                                message=f"見出しブロックに閉じマーカーがありません",
                                suggestion=f"行 {j+1} の後に ;;; を追加してください"
                            ))
                
                i = j + 1 if found_close else len(lines)
            else:
                i += 1
        
        return errors
    
    def _fix_malformed_blocks(self, content: str) -> tuple[str, List[str]]:
        """不完全なブロック構造を修正（強化版）"""
        lines = content.split('\n')
        fixed_lines = []
        changes = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 各種ブロックの開始を検出（見出し、太字、枠線、ハイライト等）
            if re.match(r'^;;;(見出し[1-5]|太字|枠線|ハイライト|ネタバレ|折りたたみ)', stripped):
                fixed_lines.append(line)
                i += 1
                
                # 内容行を収集
                content_lines = []
                while i < len(lines):
                    current_line = lines[i]
                    current_stripped = current_line.strip()
                    
                    # 閉じマーカーを発見
                    if current_stripped == ';;;':
                        fixed_lines.extend(content_lines)
                        fixed_lines.append(current_line)
                        i += 1
                        break
                    # 新しいブロック開始 = 前のブロックが閉じられていない
                    elif current_stripped.startswith(';;;') and not current_stripped.endswith(';;;'):
                        # 閉じマーカーを追加してから新しいブロックを処理
                        fixed_lines.extend(content_lines)
                        fixed_lines.append(';;;')
                        changes.append(f"ブロックに閉じマーカーを追加: {stripped}")
                        break
                    # 内容行
                    else:
                        content_lines.append(current_line)
                        i += 1
                
                # ファイル終端でブロックが終わっていない場合
                if i >= len(lines) and content_lines:
                    fixed_lines.extend(content_lines)
                    fixed_lines.append(';;;')
                    changes.append(f"ファイル終端でブロックに閉じマーカーを追加: {stripped}")
            
            # 複合マーカー（color属性付き）の処理
            elif re.match(r'^;;;.*\+.*color=', stripped):
                # Color属性順序の修正
                fixed_line, color_fix = self._fix_single_color_line(line)
                if color_fix:
                    fixed_lines.append(fixed_line)
                    changes.append(color_fix)
                else:
                    fixed_lines.append(line)
                i += 1
            
            else:
                fixed_lines.append(line)
                i += 1
        
        return '\n'.join(fixed_lines), changes
    
    def _fix_single_color_line(self, line: str) -> tuple[str, str]:
        """単一行のcolor属性順序を修正"""
        # ;;;ハイライト+太字 color=#xxx パターンを修正
        pattern = r';;;ハイライト\+太字(\s+color=#[a-fA-F0-9]{6})'
        match = re.search(pattern, line)
        if match:
            color_value = match.group(1)
            fixed_line = re.sub(pattern, f';;;太字+ハイライト{color_value}', line)
            return fixed_line, f"color属性順序を修正: ハイライト+太字 → 太字+ハイライト"
        return line, ""
    
    def _fix_consecutive_markers(self, content: str) -> tuple[str, List[str]]:
        """連続するマーカーを統合"""
        lines = content.split('\n')
        fixed_lines = []
        changes = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 連続するブロックマーカーを検出（見出しは除外）
            if (line.startswith(';;;') and line.endswith(';;;') and line != ';;;' 
                and not re.match(r'^;;;見出し[1-5]$', line)):
                markers = [line]
                j = i + 1
                
                # 直後の行が別のブロックマーカーかチェック
                while j < len(lines):
                    next_line = lines[j].strip()
                    if (next_line.startswith(';;;') and next_line.endswith(';;;') 
                        and next_line != ';;;' and not re.match(r'^;;;見出し[1-5]$', next_line)):
                        markers.append(next_line)
                        j += 1
                    else:
                        break
                
                if len(markers) > 1:
                    # 複合マーカーに統合
                    combined = self._combine_markers(markers)
                    fixed_lines.append(combined)
                    changes.append(f"連続マーカーを統合: {' → '.join(markers)} → {combined}")
                    i = j
                else:
                    fixed_lines.append(lines[i])
                    i += 1
            else:
                fixed_lines.append(lines[i])
                i += 1
        
        return '\n'.join(fixed_lines), changes
    
    def _combine_markers(self, markers: List[str]) -> str:
        """マーカーを複合マーカーに統合"""
        keywords = []
        color_attr = ""
        
        for marker in markers:
            # ;;;を除去
            content = marker.strip()
            if content.startswith(';;;') and content.endswith(';;;'):
                content = content[3:-3]  # ;;;を前後から除去
            
            # color属性を抽出
            if 'color=' in content:
                parts = content.split()
                for part in parts:
                    if part.startswith('color='):
                        color_attr = part
                        break
                # color属性以外のキーワードを抽出
                content = ' '.join([p for p in parts if not p.startswith('color=')])
            
            if content.strip():
                keywords.append(content.strip())
        
        # 複合キーワードを作成
        combined_keyword = '+'.join(keywords)
        if color_attr:
            combined_keyword += f' {color_attr}'
        
        return f';;;{combined_keyword};;;'
    
    def _fix_color_attribute_order(self, content: str) -> tuple[str, List[str]]:
        """color属性の順序問題を修正"""
        lines = content.split('\n')
        fixed_lines = []
        changes = []
        
        for i, line in enumerate(lines):
            # color属性の後に+があるパターンを検出
            # パターン1: ;;;(何か) color=#xxx+(何か);;; (完全マーカー)
            # パターン2: ;;;(何か) color=#xxx+(何か) (ブロック開始行)
            color_pattern1 = r';;;([^;]*?)\s*color=(#[a-fA-F0-9]+)\+([^;]*?);;;'
            color_pattern2 = r';;;([^;]*?)\s*color=(#[a-fA-F0-9]+)\+([^;]*?)$'
            
            match = re.search(color_pattern1, line) or re.search(color_pattern2, line)
            if match:
                before_color = match.group(1).strip()  # color属性前の部分
                color_value = match.group(2)          # color値
                after_color = match.group(3).strip()  # color属性後のキーワード
                
                # +記号を除去
                if before_color.endswith('+'):
                    before_color = before_color[:-1].strip()
                
                # 正しい順序に修正
                if before_color and after_color:
                    # 両方にキーワード: after+before color=xxx
                    correct_order = f";;;{after_color}+{before_color} color={color_value};;;"
                elif after_color:
                    # 後ろにのみキーワード: after+ハイライト color=xxx
                    correct_order = f";;;{after_color}+ハイライト color={color_value};;;"
                else:
                    # 修正不要
                    correct_order = line
                
                if correct_order != line:
                    fixed_lines.append(correct_order)
                    changes.append(f"color属性順序を修正: 行 {i+1}")
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), changes
    
    def _cleanup_empty_markers(self, content: str) -> tuple[str, List[str]]:
        """不要な空マーカーを削除（強化版）"""
        lines = content.split('\n')
        fixed_lines = []
        changes = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 空の;;;マーカー
            if stripped == ';;;':
                # 前後の文脈を詳細に解析
                prev_line = lines[i-1].strip() if i > 0 else ""
                next_line = lines[i+1].strip() if i+1 < len(lines) else ""
                
                # 必要な閉じマーカーかチェック
                is_needed_closer = False
                
                # パターン1: ブロック内容の後の正当な閉じマーカー
                if prev_line and not prev_line.startswith(';;;') and prev_line != "":
                    is_needed_closer = True
                
                # パターン2: 複数行ブロックの終了マーカー
                j = i - 1
                while j >= 0 and lines[j].strip() == "":
                    j -= 1
                if j >= 0:
                    prev_content_line = lines[j].strip()
                    if prev_content_line and not prev_content_line.startswith(';;;'):
                        # さらに前を確認してブロック開始があるか
                        k = j - 1
                        while k >= 0:
                            check_line = lines[k].strip()
                            if check_line.startswith(';;;') and not check_line.endswith(';;;'):
                                is_needed_closer = True
                                break
                            elif check_line == ';;;':
                                break
                            k -= 1
                
                if is_needed_closer:
                    fixed_lines.append(line)
                else:
                    # 不要なマーカーを削除
                    changes.append(f"不要な空マーカーを削除: 行 {i+1}")
                    # 連続する空マーカーもスキップ
                    j = i + 1
                    while j < len(lines) and lines[j].strip() == ';;;':
                        changes.append(f"連続する不要な空マーカーを削除: 行 {j+1}")
                        j += 1
                    i = j - 1
            else:
                fixed_lines.append(line)
            
            i += 1
        
        return '\n'.join(fixed_lines), changes


def show_diff_preview(original: str, fixed: str, file_path: str) -> None:
    """修正前後の差分をプレビュー表示"""
    import difflib
    
    original_lines = original.splitlines(keepends=True)
    fixed_lines = fixed.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        fixed_lines,
        fromfile=f"{file_path} (修正前)",
        tofile=f"{file_path} (修正後)",
        lineterm=''
    )
    
    print(f"\n📋 差分プレビュー: {file_path}")
    print("=" * 60)
    
    for line in diff:
        if line.startswith('+++'):
            print(f"\033[32m{line}\033[0m", end='')  # Green
        elif line.startswith('---'):
            print(f"\033[31m{line}\033[0m", end='')  # Red
        elif line.startswith('@@'):
            print(f"\033[36m{line}\033[0m", end='')  # Cyan
        elif line.startswith('+'):
            print(f"\033[92m{line}\033[0m", end='')  # Light green
        elif line.startswith('-'):
            print(f"\033[91m{line}\033[0m", end='')  # Light red
        else:
            print(line, end='')
    
    print("\n" + "=" * 60)


def format_fix_report(results: List[FixResult], file_paths: List[Path]) -> str:
    """修正結果のレポートをフォーマット"""
    if not results:
        return "[エラー] 修正結果がありません"
    
    total_files = len(results)
    total_changes = sum(result.errors_fixed for result in results)
    files_changed = sum(1 for result in results if result.errors_fixed > 0)
    
    report = []
    report.append(f"📊 修正結果サマリー")
    report.append(f"   - 処理ファイル数: {total_files}")
    report.append(f"   - 修正したファイル数: {files_changed}")
    report.append(f"   - 総修正箇所数: {total_changes}")
    report.append("")
    
    for i, (result, file_path) in enumerate(zip(results, file_paths)):
        if result.errors_fixed > 0:
            report.append(f"✅ {file_path}: {result.errors_fixed} 箇所修正")
            for change in result.changes_made:
                report.append(f"   - {change}")
        else:
            report.append(f"✨ {file_path}: 修正不要")
        
        if i < len(results) - 1:
            report.append("")
    
    return "\n".join(report)


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


def create_backup(file_path: Path) -> Path:
    """バックアップファイルを作成"""
    import time
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f".backup_{timestamp}.txt")
    
    with open(file_path, 'r', encoding='utf-8') as src:
        content = src.read()
    
    with open(backup_path, 'w', encoding='utf-8') as dst:
        dst.write(content)
    
    return backup_path


def show_progress_bar(current: int, total: int, file_name: str, width: int = 40) -> None:
    """プログレスバーを表示"""
    progress = current / total
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    percent = progress * 100
    
    # ファイル名を適切な長さに調整
    display_name = file_name[:30] + "..." if len(file_name) > 33 else file_name
    
    print(f"\r進捗: [{bar}] {percent:5.1f}% ({current:3d}/{total:3d}) {display_name}", end="", flush=True)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter 記法検証・自動修正ツール（強化版）",
        epilog="例: python dev/tools/syntax_fixer.py examples/*.txt --fix --preview"
    )
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='処理するテキストファイル'
    )
    parser.add_argument(
        '--fix', '-f',
        action='store_true',
        help='自動修正を実行'
    )
    parser.add_argument(
        '--preview', '-p',
        action='store_true',
        help='修正内容をプレビュー表示'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='詳細出力を抑制'
    )
    parser.add_argument(
        '--batch', '-b',
        action='store_true',
        help='大量ファイルのバッチ処理モード（進捗表示）'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='修正前にバックアップファイルを作成'
    )
    
    args = parser.parse_args()
    
    fixer = SyntaxFixer()
    fix_results = []
    validation_errors = []
    backup_files = []
    
    # ファイルのフィルタリング（.txtファイルのみ）
    valid_files = []
    for file_path in args.files:
        if not file_path.exists():
            print(f"⚠️  ファイルが見つかりません: {file_path}", file=sys.stderr)
            continue
        
        if not file_path.suffix.lower() == '.txt':
            if not args.quiet:
                print(f"⏭️  スキップ: {file_path} (.txt ファイルではありません)")
            continue
        
        valid_files.append(file_path)
    
    if not valid_files:
        print("❌ 処理対象のファイルがありません")
        sys.exit(1)
    
    # バッチモードの初期化
    if args.batch and len(valid_files) > 1:
        print(f"📦 バッチ処理開始: {len(valid_files)} ファイル")
        if args.fix and args.backup:
            print("💾 バックアップ作成モード有効")
        print()
    
    # メインファイル処理ループ
    for i, file_path in enumerate(valid_files, 1):
        # バッチモードでのプログレスバー表示
        if args.batch and len(valid_files) > 1 and not args.quiet:
            show_progress_bar(i, len(valid_files), file_path.name)
        
        try:
            # バックアップ作成（修正モード且つバックアップ有効時）
            if args.fix and args.backup and not args.preview:
                backup_path = create_backup(file_path)
                backup_files.append(backup_path)
            
            if args.fix:
                # 自動修正モード
                result = fixer.fix_file(file_path, preview_only=args.preview)
                fix_results.append(result)
                
                if args.preview and result.original_content != result.fixed_content:
                    show_diff_preview(result.original_content, result.fixed_content, str(file_path))
                
                if not args.quiet and not args.batch:
                    if result.errors_fixed > 0:
                        mode = "プレビュー" if args.preview else "修正"
                        print(f"🔧 {file_path}: {result.errors_fixed} 箇所{mode}")
                    else:
                        print(f"✨ {file_path}: 修正不要")
            else:
                # 検証のみモード
                errors = fixer.validate_file(file_path)
                validation_errors.extend(errors)
                
                if not args.quiet and not args.batch:
                    file_errors = [e for e in errors if e.file_path == str(file_path)]
                    if file_errors:
                        print(f"❌ {file_path}: {len(file_errors)} エラー")
                    else:
                        print(f"✅ {file_path}: OK")
        
        except Exception as e:
            if args.batch:
                print(f"\n❌ エラー: {file_path}: {e}")
            else:
                print(f"❌ エラー: {file_path}: {e}", file=sys.stderr)
    
    # バッチモード完了表示
    if args.batch and len(valid_files) > 1:
        print("\n📦 バッチ処理完了")
        if backup_files:
            print(f"💾 作成されたバックアップ: {len(backup_files)} ファイル")
    
    # 結果レポート
    if args.fix:
        if fix_results and not args.quiet:
            print("\n" + "="*60)
            print(format_fix_report(fix_results, valid_files))
            
            if backup_files:
                print(f"\n💾 バックアップファイル:")
                for backup_file in backup_files[:5]:  # 最初の5つのみ表示
                    print(f"   📄 {backup_file}")
                if len(backup_files) > 5:
                    print(f"   ... 他 {len(backup_files) - 5} ファイル")
            
            if args.preview:
                print("\n💡 実際の修正を行うには --preview を外して実行してください")
    else:
        if validation_errors:
            print("\n" + "="*60)
            print(format_error_report(validation_errors))
            print("\n💡 自動修正を行うには --fix オプションを使用してください")
            sys.exit(1)
        elif not args.quiet:
            print(f"\n✅ 検証完了: {len(valid_files)} ファイル、エラーなし")


if __name__ == "__main__":
    main()