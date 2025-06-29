#!/usr/bin/env python3
"""
Kumihan-Formatter 記法ツールキット - 統合版

このツールは以下の機能を統合しています:
- syntax_validator.py: 記法検証
- enhanced_syntax_validator.py: 高度な記法検証
- syntax_diagnostic.py: 診断機能
- syntax_fixer.py: 自動修正機能

使用方法:
    # 基本的な記法チェック（検証のみ）
    python dev/tools/syntax_toolkit.py <file.txt>
    python dev/tools/syntax_toolkit.py examples/*.txt
    
    # 詳細診断
    python dev/tools/syntax_toolkit.py <file.txt> --diagnostic
    
    # 修正のプレビュー
    python dev/tools/syntax_toolkit.py examples/*.txt --preview
    
    # 自動修正の実行
    python dev/tools/syntax_toolkit.py examples/*.txt --fix
    
    # 高度な検証（厳格モード）
    python dev/tools/syntax_toolkit.py examples/*.txt --strict
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


@dataclass
class FixResult:
    """修正結果情報"""
    original_content: str
    fixed_content: str
    changes_made: List[str]
    errors_fixed: int


@dataclass
class DiagnosticResult:
    """診断結果情報"""
    file_path: str
    total_lines: int
    syntax_coverage: float
    complexity_score: int
    recommendations: List[str]


class SyntaxToolkit:
    """
    Kumihan記法ツールキット統合クラス
    
    機能:
    - 記法検証（基本・高度）
    - 自動修正
    - 診断機能
    - レポート生成
    """
    
    def __init__(self, mode: ValidationMode = ValidationMode.TOLERANT):
        self.mode = mode
        self.errors = []
        self.warnings = []
        
        # 基本記法パターン
        self.patterns = {
            'block_start': re.compile(r'^\s*;;;'),
            'block_end': re.compile(r'^\s*;;;\s*$'),
            'list_item': re.compile(r'^\s*[-・]\s+'),
            'numbered_list': re.compile(r'^\s*\d+\.\s+'),
            'keyword_list': re.compile(r'^\s*[-・]\s+;;;(.+?);;;\s+(.+)'),
            'image_marker': re.compile(r'^\s*;;;([^;]+\.(png|jpg|jpeg|gif|svg));;;\s*$'),
            'toc_marker': re.compile(r'^\s*;;;目次;;;\s*$'),
        }
        
        # 有効なキーワード
        self.valid_keywords = {
            '太字', 'イタリック', '枠線', 'ハイライト', 
            '見出し1', '見出し2', '見出し3', '見出し4', '見出し5',
            '折りたたみ', 'ネタバレ', '目次', '画像'
        }
    
    def validate_file(self, file_path: Path) -> List[ValidationError]:
        """ファイルの記法を検証"""
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            errors.append(ValidationError(
                str(file_path), 0, "file_error", f"ファイル読み込みエラー: {e}"
            ))
            return errors
        
        in_block = False
        block_start_line = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()
            
            # 空行は無視
            if not line.strip():
                continue
                
            # ブロック開始の検証
            if self.patterns['block_start'].match(line):
                if in_block:
                    errors.append(ValidationError(
                        str(file_path), line_num, "nested_block",
                        "ブロックが入れ子になっています",
                        f"行{block_start_line}のブロックを先に閉じてください"
                    ))
                else:
                    in_block = True
                    block_start_line = line_num
                    
                    # キーワード検証
                    keyword_errors = self._validate_keywords(file_path, line_num, line)
                    errors.extend(keyword_errors)
            
            # ブロック終了の検証
            elif self.patterns['block_end'].match(line):
                if not in_block:
                    errors.append(ValidationError(
                        str(file_path), line_num, "orphan_block_end",
                        "対応するブロック開始マーカーがありません"
                    ))
                else:
                    in_block = False
            
            # その他の記法検証
            elif not in_block:
                self._validate_line_syntax(file_path, line_num, line, errors)
        
        # 未閉ブロックの検証
        if in_block:
            errors.append(ValidationError(
                str(file_path), block_start_line, "unclosed_block",
                "ブロックが閉じられていません",
                "行末に ;;; を追加してください"
            ))
        
        return errors
    
    def _validate_keywords(self, file_path: Path, line_num: int, line: str) -> List[ValidationError]:
        """キーワードの検証"""
        errors = []
        
        # ;;; の後のキーワード部分を抽出
        match = re.match(r'^\s*;;;(.+?)(?:\s*$)', line)
        if not match:
            return errors
            
        keyword_part = match.group(1).strip()
        
        # 目次マーカーの特別処理
        if keyword_part == '目次':
            errors.append(ValidationError(
                str(file_path), line_num, "manual_toc",
                "目次マーカーは手動で記述しないでください",
                "見出しがあれば自動生成されます"
            ))
            return errors
        
        # 画像マーカーの処理
        if self.patterns['image_marker'].match(line):
            return errors
            
        # 複合キーワードの分析
        keywords = self._parse_compound_keywords(keyword_part)
        
        for keyword in keywords:
            if keyword.startswith('ハイライト color='):
                # 色指定の検証
                color_part = keyword.replace('ハイライト color=', '')
                if not re.match(r'^#[0-9a-fA-F]{6}$', color_part):
                    errors.append(ValidationError(
                        str(file_path), line_num, "invalid_color",
                        f"無効な色指定: {color_part}",
                        "色は #RRGGBB 形式で指定してください"
                    ))
            elif keyword not in self.valid_keywords:
                errors.append(ValidationError(
                    str(file_path), line_num, "unknown_keyword",
                    f"未知のキーワード: {keyword}",
                    f"有効なキーワード: {', '.join(sorted(self.valid_keywords))}"
                ))
        
        return errors
    
    def _parse_compound_keywords(self, keyword_part: str) -> List[str]:
        """複合キーワードを解析"""
        keywords = []
        parts = re.split(r'[+＋]', keyword_part)
        
        for part in parts:
            part = part.strip()
            if 'color=' in part:
                # ハイライト color=#xxx の形式
                if part.startswith('ハイライト'):
                    keywords.append(part)
                else:
                    keywords.append('ハイライト ' + part)
            else:
                keywords.append(part)
        
        return keywords
    
    def _validate_line_syntax(self, file_path: Path, line_num: int, line: str, errors: List[ValidationError]):
        """行単位の記法検証"""
        # リスト項目の検証
        if self.patterns['list_item'].match(line) or self.patterns['numbered_list'].match(line):
            # キーワード付きリストの検証
            keyword_match = self.patterns['keyword_list'].match(line)
            if keyword_match:
                keywords_part = keyword_match.group(1)
                keyword_errors = self._validate_keywords(file_path, line_num, f';;;{keywords_part};;;')
                errors.extend(keyword_errors)
    
    def fix_file(self, file_path: Path, preview_only: bool = False) -> FixResult:
        """ファイルの記法を自動修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            return FixResult(
                original_content="",
                fixed_content="",
                changes_made=[f"ファイル読み込みエラー: {e}"],
                errors_fixed=0
            )
        
        fixed_content = original_content
        changes_made = []
        errors_fixed = 0
        
        lines = fixed_content.split('\n')
        
        for i, line in enumerate(lines):
            original_line = line
            
            # 基本的な修正
            if ';;; ' in line and line.strip().endswith(';;;'):
                # スペースの正規化
                line = re.sub(r';;;(\s+)', r';;; ', line)
                line = re.sub(r'(\s+);;;$', r' ;;;', line)
                
            # 全角＋を半角+に変換
            if '＋' in line:
                line = line.replace('＋', '+')
                
            # 変更があった場合
            if line != original_line:
                lines[i] = line
                changes_made.append(f"行{i+1}: スペース・記号の正規化")
                errors_fixed += 1
        
        fixed_content = '\n'.join(lines)
        
        # プレビューモードでない場合、実際にファイルを更新
        if not preview_only and errors_fixed > 0:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
            except Exception as e:
                changes_made.append(f"ファイル書き込みエラー: {e}")
        
        return FixResult(
            original_content=original_content,
            fixed_content=fixed_content,
            changes_made=changes_made,
            errors_fixed=errors_fixed
        )
    
    def diagnose_file(self, file_path: Path) -> DiagnosticResult:
        """ファイルの診断を実行"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return DiagnosticResult(
                str(file_path), 0, 0.0, 0, 
                ["ファイル読み込みエラー"]
            )
        
        lines = content.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        
        # 記法使用率の計算
        syntax_lines = 0
        for line in lines:
            if (self.patterns['block_start'].match(line) or 
                self.patterns['list_item'].match(line) or 
                self.patterns['numbered_list'].match(line)):
                syntax_lines += 1
        
        syntax_coverage = (syntax_lines / total_lines * 100) if total_lines > 0 else 0
        
        # 複雑度スコア（簡易版）
        complexity_score = 0
        in_block = False
        for line in lines:
            if self.patterns['block_start'].match(line):
                complexity_score += 1
                if '+' in line or '＋' in line:
                    complexity_score += 2  # 複合キーワードはより複雑
                in_block = True
            elif self.patterns['block_end'].match(line):
                in_block = False
            elif in_block:
                complexity_score += 0.5  # ブロック内容
        
        # レコメンデーション生成
        recommendations = []
        if syntax_coverage < 20:
            recommendations.append("記法の使用率が低いです。見出しやリストの活用を検討してください")
        if complexity_score > 50:
            recommendations.append("複雑な記法が多用されています。シンプルな表現も検討してください")
        
        return DiagnosticResult(
            str(file_path),
            total_lines,
            syntax_coverage,
            int(complexity_score),
            recommendations
        )
    
    def generate_report(self, files: List[Path], include_diagnostics: bool = False) -> str:
        """複数ファイルのレポートを生成"""
        report_lines = []
        report_lines.append("=== Kumihan記法ツールキット レポート ===")
        report_lines.append("")
        
        total_errors = 0
        total_files = len(files)
        
        for file_path in files:
            report_lines.append(f"📄 {file_path}")
            report_lines.append("-" * 50)
            
            # 検証結果
            errors = self.validate_file(file_path)
            total_errors += len(errors)
            
            if not errors:
                report_lines.append("✅ 記法チェック: 問題なし")
            else:
                report_lines.append(f"❌ 記法エラー: {len(errors)}件")
                for error in errors[:5]:  # 最初の5件のみ表示
                    report_lines.append(f"  • {error.line_number}行目: {error.message}")
                if len(errors) > 5:
                    report_lines.append(f"  ... 他{len(errors) - 5}件")
            
            # 診断結果（オプション）
            if include_diagnostics:
                diag = self.diagnose_file(file_path)
                report_lines.append(f"📊 記法使用率: {diag.syntax_coverage:.1f}%")
                report_lines.append(f"📈 複雑度スコア: {diag.complexity_score}")
                
                if diag.recommendations:
                    report_lines.append("💡 推奨事項:")
                    for rec in diag.recommendations:
                        report_lines.append(f"  • {rec}")
            
            report_lines.append("")
        
        # サマリー
        report_lines.append("=== サマリー ===")
        report_lines.append(f"対象ファイル: {total_files}件")
        report_lines.append(f"総エラー数: {total_errors}件")
        
        if total_errors == 0:
            report_lines.append("🎉 すべてのファイルが正常です！")
        else:
            report_lines.append("⚠️  修正が必要なファイルがあります")
        
        return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Kumihan記法ツールキット - 検証・修正・診断統合ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 基本的な検証
  python dev/tools/syntax_toolkit.py examples/*.txt
  
  # 自動修正（プレビュー）
  python dev/tools/syntax_toolkit.py examples/*.txt --preview
  
  # 自動修正（実行）
  python dev/tools/syntax_toolkit.py examples/*.txt --fix
  
  # 診断付きレポート
  python dev/tools/syntax_toolkit.py examples/*.txt --diagnostic --report
  
  # 厳格モード
  python dev/tools/syntax_toolkit.py examples/*.txt --strict
        """
    )
    
    parser.add_argument('files', nargs='+', help='検証対象ファイル')
    parser.add_argument('--fix', action='store_true', help='自動修正を実行')
    parser.add_argument('--preview', action='store_true', help='修正のプレビューのみ表示')
    parser.add_argument('--diagnostic', action='store_true', help='診断機能を有効化')
    parser.add_argument('--strict', action='store_true', help='厳格モードで検証')
    parser.add_argument('--report', action='store_true', help='詳細レポートを生成')
    
    args = parser.parse_args()
    
    # モード設定
    mode = ValidationMode.STRICT if args.strict else ValidationMode.TOLERANT
    toolkit = SyntaxToolkit(mode)
    
    # ファイルリスト処理
    files = []
    for file_pattern in args.files:
        path = Path(file_pattern)
        if path.is_file():
            files.append(path)
        else:
            # グロブパターン対応
            files.extend(Path('.').glob(file_pattern))
    
    if not files:
        print("❌ 対象ファイルが見つかりません")
        return 1
    
    # レポートモード
    if args.report:
        report = toolkit.generate_report(files, args.diagnostic)
        print(report)
        return 0
    
    # 各ファイルの処理
    total_errors = 0
    
    for file_path in files:
        print(f"\n📄 {file_path}")
        print("=" * 50)
        
        # 修正モード
        if args.fix or args.preview:
            result = toolkit.fix_file(file_path, preview_only=args.preview)
            
            if result.errors_fixed > 0:
                print(f"🔧 修正項目: {result.errors_fixed}件")
                for change in result.changes_made:
                    print(f"  • {change}")
                
                if args.preview:
                    print("\n📝 修正後の内容（プレビュー）:")
                    print("-" * 30)
                    print(result.fixed_content[:500] + "..." if len(result.fixed_content) > 500 else result.fixed_content)
                else:
                    print("✅ ファイルを修正しました")
            else:
                print("✨ 修正の必要がありません")
        
        # 診断モード
        elif args.diagnostic:
            diag = toolkit.diagnose_file(file_path)
            print(f"📊 記法使用率: {diag.syntax_coverage:.1f}%")
            print(f"📈 複雑度スコア: {diag.complexity_score}")
            print(f"📏 総行数: {diag.total_lines}")
            
            if diag.recommendations:
                print("💡 推奨事項:")
                for rec in diag.recommendations:
                    print(f"  • {rec}")
        
        # 基本検証モード
        else:
            errors = toolkit.validate_file(file_path)
            total_errors += len(errors)
            
            if not errors:
                print("✅ 記法チェック: 問題なし")
            else:
                print(f"❌ 記法エラー: {len(errors)}件")
                for error in errors:
                    print(f"  {error.line_number}行目: {error.message}")
                    if error.suggestion:
                        print(f"    💡 {error.suggestion}")
    
    # 最終結果
    if not (args.fix or args.preview or args.diagnostic):
        print(f"\n=== 検証結果 ===")
        print(f"対象ファイル: {len(files)}件")
        print(f"総エラー数: {total_errors}件")
        
        if total_errors == 0:
            print("🎉 すべてのファイルが正常です！")
            return 0
        else:
            print("⚠️  修正が必要なファイルがあります")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())