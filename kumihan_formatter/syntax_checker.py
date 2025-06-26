"""Kumihan markup syntax checker

This module provides comprehensive syntax validation for Kumihan markup files.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Any, NamedTuple
from dataclasses import dataclass
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class SyntaxError:
    """Represents a syntax error in Kumihan markup"""
    line_number: int
    column: int
    severity: ErrorSeverity
    error_type: str
    message: str
    context: str
    suggestion: str = ""


class KumihanSyntaxChecker:
    """Kumihan markup syntax checker"""
    
    # Valid keywords
    VALID_KEYWORDS = {
        '太字', 'イタリック', '枠線', 'ハイライト', 
        '見出し1', '見出し2', '見出し3', '見出し4', '見出し5',
        '折りたたみ', 'ネタバレ', '目次', '画像'
    }
    
    # Keywords that accept color attribute
    COLOR_KEYWORDS = {'ハイライト'}
    
    # Keywords that accept alt attribute  
    ALT_KEYWORDS = {'画像'}
    
    def __init__(self):
        self.errors: List[SyntaxError] = []
        self.current_file = ""
    
    def check_file(self, file_path: Path) -> List[SyntaxError]:
        """Check a single file for syntax errors"""
        self.errors.clear()
        self.current_file = str(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            self.errors.append(SyntaxError(
                line_number=1,
                column=1,
                severity=ErrorSeverity.ERROR,
                error_type="encoding",
                message="ファイルのエンコーディングが UTF-8 ではありません",
                context=str(file_path)
            ))
            return self.errors
        except FileNotFoundError:
            self.errors.append(SyntaxError(
                line_number=1,
                column=1,
                severity=ErrorSeverity.ERROR,
                error_type="file-not-found", 
                message="ファイルが見つかりません",
                context=str(file_path)
            ))
            return self.errors
        
        lines = content.splitlines()
        self._check_syntax(lines)
        
        return self.errors
    
    def _check_syntax(self, lines: List[str]) -> None:
        """Check syntax for all lines"""
        in_block = False
        block_start_line = 0
        block_keywords = []
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for block markers
            if stripped.startswith(';;;'):
                if stripped == ';;;':
                    # Block end marker
                    if not in_block:
                        self._add_error(
                            line_num, 1, ErrorSeverity.ERROR,
                            "unmatched-block-end",
                            "ブロック開始マーカーなしに ;;; が見つかりました",
                            line
                        )
                    else:
                        in_block = False
                        block_keywords.clear()
                else:
                    # Block start marker or keyword line
                    if in_block:
                        # Check for multi-line syntax error
                        self._check_multiline_syntax(line_num, stripped, block_start_line, block_keywords)
                    else:
                        # Start of new block
                        in_block = True
                        block_start_line = line_num
                        block_keywords = self._parse_keywords(stripped[3:])
                        self._check_block_keywords(line_num, stripped)
            
            # Check for other syntax issues
            self._check_line_syntax(line_num, line)
        
        # Check for unclosed blocks
        if in_block:
            self._add_error(
                block_start_line, 1, ErrorSeverity.ERROR,
                "unclosed-block",
                "ブロックが ;;; で閉じられていません",
                lines[block_start_line - 1] if block_start_line <= len(lines) else "",
                "ブロックの最後に ;;; を追加してください"
            )
    
    def _check_multiline_syntax(self, line_num: int, stripped: str, block_start_line: int, existing_keywords: List[str]) -> None:
        """Check for invalid multi-line syntax patterns"""
        keywords = self._parse_keywords(stripped[3:])
        
        if keywords:
            # This is a multi-line syntax error
            combined_keywords = existing_keywords + keywords
            suggestion = f";;;{'+'.join(combined_keywords)}"
            
            self._add_error(
                line_num, 1, ErrorSeverity.ERROR,
                "multiline-syntax",
                f"複数行記法は無効です。行 {block_start_line} からのブロックを1行にまとめてください",
                stripped,
                suggestion
            )
    
    def _check_block_keywords(self, line_num: int, line: str) -> None:
        """Check block keyword syntax"""
        keyword_part = line[3:].strip()
        
        if not keyword_part:
            self._add_error(
                line_num, 4, ErrorSeverity.ERROR,
                "empty-keyword",
                "キーワードが指定されていません",
                line
            )
            return
        
        # Parse compound keywords
        keywords = self._parse_keywords(keyword_part)
        
        # Check each keyword
        for keyword in keywords:
            self._check_single_keyword(line_num, keyword, line)
        
        # Check keyword combination validity
        self._check_keyword_combination(line_num, keywords, line)
    
    def _parse_keywords(self, keyword_part: str) -> List[str]:
        """Parse compound keywords separated by + or ＋"""
        if not keyword_part:
            return []
        
        # Split by + or ＋
        keywords = re.split(r'[+＋]', keyword_part)
        
        # Clean and validate
        result = []
        for kw in keywords:
            kw = kw.strip()
            if kw:
                result.append(kw)
        
        return result
    
    def _check_single_keyword(self, line_num: int, keyword: str, context: str) -> None:
        """Check a single keyword for validity"""
        # Check for color attribute
        if ' color=' in keyword:
            base_keyword, color_part = keyword.split(' color=', 1)
            base_keyword = base_keyword.strip()
            
            if base_keyword not in self.COLOR_KEYWORDS:
                self._add_error(
                    line_num, 1, ErrorSeverity.ERROR,
                    "invalid-color-usage",
                    f"'{base_keyword}' キーワードはcolor属性をサポートしていません",
                    context,
                    f"color属性は {', '.join(self.COLOR_KEYWORDS)} でのみ使用可能です"
                )
            
            # Check color format
            if not re.match(r'^#[0-9a-fA-F]{6}$', color_part):
                self._add_error(
                    line_num, 1, ErrorSeverity.WARNING,
                    "invalid-color-format",
                    f"色の形式が正しくありません: {color_part}",
                    context,
                    "色は #RRGGBB 形式で指定してください（例: #ff0000）"
                )
        
        # Check for alt attribute
        elif ' alt=' in keyword:
            base_keyword, alt_part = keyword.split(' alt=', 1)
            base_keyword = base_keyword.strip()
            
            if base_keyword not in self.ALT_KEYWORDS:
                self._add_error(
                    line_num, 1, ErrorSeverity.ERROR,
                    "invalid-alt-usage", 
                    f"'{base_keyword}' キーワードはalt属性をサポートしていません",
                    context,
                    f"alt属性は {', '.join(self.ALT_KEYWORDS)} でのみ使用可能です"
                )
        
        else:
            # Check base keyword validity
            if keyword not in self.VALID_KEYWORDS:
                self._add_error(
                    line_num, 1, ErrorSeverity.ERROR,
                    "unknown-keyword",
                    f"未知のキーワードです: '{keyword}'",
                    context,
                    f"有効なキーワード: {', '.join(sorted(self.VALID_KEYWORDS))}"
                )
    
    def _check_keyword_combination(self, line_num: int, keywords: List[str], context: str) -> None:
        """Check if keyword combination is valid"""
        # Remove attributes for base keyword check
        base_keywords = []
        for kw in keywords:
            if ' color=' in kw:
                base_keywords.append(kw.split(' color=')[0].strip())
            elif ' alt=' in kw:
                base_keywords.append(kw.split(' alt=')[0].strip())
            else:
                base_keywords.append(kw)
        
        # Check for duplicate keywords
        seen = set()
        for kw in base_keywords:
            if kw in seen:
                self._add_error(
                    line_num, 1, ErrorSeverity.WARNING,
                    "duplicate-keyword",
                    f"重複するキーワードがあります: '{kw}'",
                    context,
                    "重複するキーワードを削除してください"
                )
            seen.add(kw)
        
        # Check for conflicting heading levels
        headings = [kw for kw in base_keywords if kw.startswith('見出し')]
        if len(headings) > 1:
            self._add_error(
                line_num, 1, ErrorSeverity.ERROR,
                "multiple-headings",
                f"複数の見出しレベルが指定されています: {', '.join(headings)}",
                context,
                "見出しレベルは1つだけ指定してください"
            )
    
    def _check_line_syntax(self, line_num: int, line: str) -> None:
        """Check individual line for syntax issues"""
        # Check for invalid ;;; usage (but allow list item syntax: - ;;;keyword;;; text)
        if ';;;' in line and not line.strip().startswith(';;;'):
            # Check if it's a valid list item syntax
            stripped = line.strip()
            is_list_item = (stripped.startswith('- ;;;') and stripped.count(';;;') >= 2) or \
                          (re.match(r'^\d+\.\s+;;;', stripped) and stripped.count(';;;') >= 2)
            if not is_list_item:
                self._add_error(
                    line_num, line.find(';;;') + 1, ErrorSeverity.WARNING,
                    "inline-marker",
                    ";;; は行頭でのみ有効です（リスト内記法以外）",
                    line,
                    ";;; は行の先頭に配置するか、リスト内記法 '- ;;;キーワード;;; テキスト' を使用してください"
                )
        
        # Check for empty block markers with spaces
        stripped = line.strip()
        if re.match(r'^;;;[\s]+$', stripped):
            self._add_error(
                line_num, 1, ErrorSeverity.ERROR,
                "invalid-block-marker",
                "空白文字が含まれた無効なブロックマーカーです",
                line,
                "単純に ;;; のみ記述してください"
            )
    
    def _add_error(self, line_num: int, column: int, severity: ErrorSeverity,
                   error_type: str, message: str, context: str, suggestion: str = "") -> None:
        """Add an error to the list"""
        self.errors.append(SyntaxError(
            line_number=line_num,
            column=column,
            severity=severity,
            error_type=error_type,
            message=message,
            context=context,
            suggestion=suggestion
        ))


def check_files(file_paths: List[Path], verbose: bool = False) -> Dict[str, List[SyntaxError]]:
    """Check multiple files for syntax errors"""
    checker = KumihanSyntaxChecker()
    results = {}
    
    for file_path in file_paths:
        if verbose:
            print(f"Checking {file_path}...")
        
        errors = checker.check_file(file_path)
        if errors:
            results[str(file_path)] = errors
    
    return results


def format_error_report(results: Dict[str, List[SyntaxError]], show_suggestions: bool = True) -> str:
    """Format error report as string"""
    if not results:
        return "✅ 記法エラーは見つかりませんでした。"
    
    report = []
    total_errors = sum(len(errors) for errors in results.values())
    
    report.append(f"🔍 {len(results)} ファイルで {total_errors} 個の記法エラーが見つかりました:\n")
    
    for file_path, errors in results.items():
        report.append(f"📁 {file_path}")
        
        # Group by severity
        by_severity = {}
        for error in errors:
            if error.severity not in by_severity:
                by_severity[error.severity] = []
            by_severity[error.severity].append(error)
        
        for severity in [ErrorSeverity.ERROR, ErrorSeverity.WARNING, ErrorSeverity.INFO]:
            if severity in by_severity:
                for error in by_severity[severity]:
                    icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}[severity.value]
                    report.append(f"  {icon} Line {error.line_number}: {error.message}")
                    
                    if error.context:
                        report.append(f"     Context: {error.context}")
                    
                    if show_suggestions and error.suggestion:
                        report.append(f"     💡 Suggestion: {error.suggestion}")
                    
                    report.append("")
        
        report.append("")
    
    return "\n".join(report)


def main():
    """CLI entry point for syntax checker"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kumihan記法 構文チェッカー")
    parser.add_argument("files", nargs="+", type=Path, help="チェックするファイルパス")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細な出力")
    parser.add_argument("--no-suggestions", action="store_true", help="修正提案を表示しない")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="出力形式")
    
    args = parser.parse_args()
    
    # Check files
    results = check_files(args.files, args.verbose)
    
    if args.format == "json":
        import json
        json_results = {}
        for file_path, errors in results.items():
            json_results[file_path] = [
                {
                    "line": error.line_number,
                    "column": error.column,
                    "severity": error.severity.value,
                    "type": error.error_type,
                    "message": error.message,
                    "context": error.context,
                    "suggestion": error.suggestion
                }
                for error in errors
            ]
        print(json.dumps(json_results, ensure_ascii=False, indent=2))
    else:
        print(format_error_report(results, not args.no_suggestions))
    
    # Exit with appropriate code
    if results:
        error_count = sum(1 for errors in results.values() 
                         for error in errors if error.severity == ErrorSeverity.ERROR)
        sys.exit(1 if error_count > 0 else 0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()