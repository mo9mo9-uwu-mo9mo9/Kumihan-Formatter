"""
lint コマンド実装

Issue #778: flake8自動修正ツール実装
Phase 3.1: 基本自動修正機能（E501, E226, F401）
"""

import subprocess
import click
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import ast
import logging

from kumihan_formatter.core.utilities.logger import get_logger


class Flake8AutoFixer:
    """flake8エラー自動修正エンジン"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = get_logger(__name__)
        self.config_path = config_path or ".flake8"
        self.max_line_length = self._get_max_line_length()
        self.fixes_applied = {
            "E501": 0,
            "E226": 0, 
            "F401": 0,
            "total": 0
        }
    
    def _get_max_line_length(self) -> int:
        """.flake8設定から行長制限を取得"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                content = config_file.read_text()
                match = re.search(r'max-line-length\s*=\s*(\d+)', content)
                if match:
                    return int(match.group(1))
        except Exception as e:
            self.logger.warning(f"Failed to read flake8 config: {e}")
        
        return 100  # デフォルト値
    
    def get_flake8_errors(self, file_path: str) -> List[Dict[str, str]]:
        """指定ファイルのflake8エラー一覧を取得"""
        try:
            result = subprocess.run([
                "python3", "-m", "flake8", 
                "--config", self.config_path,
                "--format", "%(path)s:%(row)d:%(col)d: %(code)s %(text)s",
                file_path
            ], capture_output=True, text=True, timeout=30)
            
            errors = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    match = re.match(r'(.+):(\d+):(\d+): (\w+) (.+)', line)
                    if match:
                        errors.append({
                            'file': match.group(1),
                            'line': int(match.group(2)),
                            'col': int(match.group(3)),
                            'code': match.group(4),
                            'message': match.group(5)
                        })
            
            return errors
        
        except subprocess.TimeoutExpired:
            self.logger.error(f"flake8 timeout for {file_path}")
            return []
        except Exception as e:
            self.logger.error(f"Failed to run flake8 on {file_path}: {e}")
            return []
    
    def fix_e501_line_too_long(self, content: str, line_num: int) -> str:
        """E501: 行が長すぎる場合の自動修正"""
        lines = content.split('\n')
        if line_num > len(lines):
            return content
        
        line = lines[line_num - 1]
        if len(line) <= self.max_line_length:
            return content
        
        # 修正パターン1: 関数引数の分割
        if '(' in line and ')' in line:
            fixed_line = self._split_function_call(line)
            if fixed_line != line:
                lines[line_num - 1] = fixed_line
                self.fixes_applied["E501"] += 1
                return '\n'.join(lines)
        
        # 修正パターン2: 文字列の分割
        if '"' in line or "'" in line:
            fixed_line = self._split_long_string(line)
            if fixed_line != line:
                lines[line_num - 1] = fixed_line
                self.fixes_applied["E501"] += 1
                return '\n'.join(lines)
        
        # 修正パターン3: 演算子での分割
        fixed_line = self._split_at_operators(line)
        if fixed_line != line:
            lines[line_num - 1] = fixed_line
            self.fixes_applied["E501"] += 1
            return '\n'.join(lines)
        
        return content
    
    def _split_function_call(self, line: str) -> str:
        """関数呼び出しの引数を複数行に分割"""
        indent = len(line) - len(line.lstrip())
        base_indent = ' ' * indent
        
        # 簡単な関数呼び出しパターンをマッチ
        match = re.match(r'(\s*)([^(]+)\((.*)\)(.*)$', line)
        if not match:
            return line
        
        prefix, func_name, args, suffix = match.groups()
        
        # 引数を分割
        if ',' in args:
            arg_parts = [arg.strip() for arg in args.split(',')]
            if len(arg_parts) > 1:
                # 複数行に分割
                result = f"{prefix}{func_name}(\n"
                for i, arg in enumerate(arg_parts):
                    if i == len(arg_parts) - 1:
                        result += f"{base_indent}    {arg}\n{base_indent}){suffix}"
                    else:
                        result += f"{base_indent}    {arg},\n"
                return result
        
        return line
    
    def _split_long_string(self, line: str) -> str:
        """長い文字列リテラルを複数行に分割"""
        # 簡単な文字列分割（改行で分割）
        if len(line) > self.max_line_length and ('"' in line or "'" in line):
            # これは複雑な実装が必要なので、一旦そのまま返す
            pass
        return line
    
    def _split_at_operators(self, line: str) -> str:
        """演算子位置で行を分割"""
        if len(line) <= self.max_line_length:
            return line
        
        # 一般的な演算子位置で分割
        operators = [' and ', ' or ', ' + ', ' - ', ' * ', ' / ', ' == ', ' != ']
        
        for op in operators:
            if op in line:
                parts = line.split(op)
                if len(parts) == 2:
                    indent = len(line) - len(line.lstrip())
                    first_part = parts[0].rstrip()
                    second_part = parts[1].lstrip()
                    
                    if len(first_part) < self.max_line_length:
                        return f"{first_part}{op.rstrip()}\n{' ' * (indent + 4)}{second_part}"
        
        return line
    
    def fix_e226_missing_whitespace(self, content: str, line_num: int, col: int) -> str:
        """E226: 演算子周辺の空白不足を修正"""
        lines = content.split('\n')
        if line_num > len(lines):
            return content
        
        line = lines[line_num - 1]
        
        # 演算子の前後に空白を追加
        operators = ['=', '+', '-', '*', '/', '==', '!=', '<=', '>=', '<', '>']
        
        for op in operators:
            # 演算子前後の空白チェック
            pattern = rf'(\w){re.escape(op)}(\w)'
            if re.search(pattern, line):
                fixed_line = re.sub(pattern, rf'\1 {op} \2', line)
                lines[line_num - 1] = fixed_line
                self.fixes_applied["E226"] += 1
                return '\n'.join(lines)
        
        return content
    
    def fix_f401_unused_import(self, content: str, line_num: int) -> str:
        """F401: 未使用importを削除"""
        lines = content.split('\n')
        if line_num > len(lines):
            return content
        
        line = lines[line_num - 1]
        
        # import文かどうかチェック
        if line.strip().startswith(('import ', 'from ')):
            # 簡単な未使用チェック（実際は複雑な解析が必要）
            try:
                # ASTで解析してimport名を取得
                tree = ast.parse(content)
                import_names = self._extract_import_names(line)
                
                # ファイル内で使用されているかチェック
                used = False
                for name in import_names:
                    if name in content and content.count(name) > 1:  # import行以外でも使用
                        used = True
                        break
                
                if not used:
                    # import行を削除
                    del lines[line_num - 1]
                    self.fixes_applied["F401"] += 1
                    return '\n'.join(lines)
                    
            except Exception as e:
                self.logger.debug(f"Failed to parse import: {e}")
        
        return content
    
    def _extract_import_names(self, import_line: str) -> List[str]:
        """import文から名前を抽出"""
        names = []
        
        if import_line.strip().startswith('import '):
            # import module
            module = import_line.replace('import ', '').strip()
            names.append(module.split('.')[0])
        
        elif import_line.strip().startswith('from '):
            # from module import name
            match = re.match(r'from\s+\S+\s+import\s+(.+)', import_line)
            if match:
                imports = match.group(1)
                for name in imports.split(','):
                    names.append(name.strip().split(' as ')[0])
        
        return names
    
    def fix_file(self, file_path: str, dry_run: bool = False) -> Dict[str, int]:
        """ファイルのflake8エラーを自動修正"""
        self.logger.info(f"Processing file: {file_path}")
        
        try:
            file_obj = Path(file_path)
            if not file_obj.exists():
                self.logger.error(f"File not found: {file_path}")
                return {"error": 1}
            
            original_content = file_obj.read_text(encoding='utf-8')
            content = original_content
            
            # flake8エラーを取得
            errors = self.get_flake8_errors(file_path)
            
            # 各エラーを修正
            for error in errors:
                error_code = error['code']
                
                if error_code == 'E501':
                    content = self.fix_e501_line_too_long(content, error['line'])
                elif error_code == 'E226':
                    content = self.fix_e226_missing_whitespace(content, error['line'], error['col'])
                elif error_code == 'F401':
                    content = self.fix_f401_unused_import(content, error['line'])
            
            # 修正内容を保存（dry_runでない場合）
            if not dry_run and content != original_content:
                file_obj.write_text(content, encoding='utf-8')
                self.logger.info(f"Fixed {file_path}")
            
            return self.fixes_applied
            
        except Exception as e:
            self.logger.error(f"Failed to fix file {file_path}: {e}")
            return {"error": 1}


@click.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--fix', is_flag=True, help='自動修正を実行する')
@click.option('--dry-run', is_flag=True, help='修正内容を表示のみ（実際には変更しない）')
@click.option('--config', '-c', help='flake8設定ファイルのパス')
@click.option('--verbose', '-v', is_flag=True, help='詳細ログを表示')
def lint_command(files: Tuple[str, ...], fix: bool, dry_run: bool, config: Optional[str], verbose: bool) -> None:
    """コードの品質チェックと自動修正
    
    Issue #778: flake8自動修正ツール
    Phase 3.1: E501, E226, F401エラーの自動修正
    """
    logger = get_logger(__name__)
    
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    if not files:
        # デフォルト対象：Pythonファイル
        files = tuple(str(p) for p in Path('.').rglob('*.py') if not str(p).startswith('.'))
    
    if not fix:
        # --fixオプションなしの場合は通常のflake8実行
        logger.info("Running flake8 check...")
        try:
            result = subprocess.run([
                "python3", "-m", "flake8",
                "--config", config or ".flake8",
                *files
            ], timeout=60)
            click.echo(f"flake8 check completed with exit code: {result.returncode}")
        except subprocess.TimeoutExpired:
            click.echo("flake8 check timed out", err=True)
        except Exception as e:
            click.echo(f"Failed to run flake8: {e}", err=True)
        return
    
    # 自動修正実行
    fixer = Flake8AutoFixer(config)
    total_fixes = {"E501": 0, "E226": 0, "F401": 0, "total": 0}
    
    with click.progressbar(files, label="Fixing files") as file_list:
        for file_path in file_list:
            if file_path.endswith('.py'):
                fixes = fixer.fix_file(file_path, dry_run=dry_run)
                
                if "error" not in fixes:
                    for code in ["E501", "E226", "F401"]:
                        total_fixes[code] += fixes.get(code, 0)
                    total_fixes["total"] += sum(fixes.get(code, 0) for code in ["E501", "E226", "F401"])
    
    # 結果表示
    if dry_run:
        click.echo("Dry run completed. No files were modified.")
    else:
        click.echo("Auto-fix completed.")
    
    click.echo(f"Fixes applied:")
    click.echo(f"  E501 (line too long): {total_fixes['E501']}")
    click.echo(f"  E226 (missing whitespace): {total_fixes['E226']}")
    click.echo(f"  F401 (unused import): {total_fixes['F401']}")
    click.echo(f"  Total fixes: {total_fixes['total']}")


def create_lint_command():
    """lintコマンドのファクトリ関数"""
    return lint_command