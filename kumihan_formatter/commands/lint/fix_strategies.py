"""
Fix strategies module for flake8 auto-fixer.

Issue #778: flake8自動修正ツール - 修正戦略とサポート機能
Technical Debt Reduction: auto_fixer.py分割による可読性向上
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List

from kumihan_formatter.core.utilities.logger import get_logger


class Flake8FixStrategies:
    """
    Flake8エラーの個別修正戦略を提供するクラス

    機能:
    - 各エラーコードに対する具体的な修正方法
    - レポート生成機能
    - HTML出力機能
    """

    def __init__(self, max_line_length: int = 100):
        self.logger = get_logger(__name__)
        self.max_line_length = max_line_length
        self._last_fix_count = 0

    def get_last_fix_count(self) -> int:
        """最後の修正で適用された修正数を取得"""
        return self._last_fix_count

    def fix_e501_line_too_long(self, content: str, line_num: int) -> str:
        """E501: 行が長すぎる場合の自動修正"""
        self._last_fix_count = 0
        lines = content.split("\n")
        if line_num > len(lines):
            return content

        line = lines[line_num - 1]
        if len(line) <= self.max_line_length:
            return content

        # 様々な分割方法を試行
        fixed_line = self._split_function_call(line)
        if fixed_line != line:
            lines[line_num - 1] = fixed_line
            self._last_fix_count = 1
            return "\n".join(lines)

        fixed_line = self._split_long_string(line)
        if fixed_line != line:
            lines[line_num - 1] = fixed_line
            self._last_fix_count = 1
            return "\n".join(lines)

        fixed_line = self._split_at_operators(line)
        if fixed_line != line:
            lines[line_num - 1] = fixed_line
            self._last_fix_count = 1
            return "\n".join(lines)

        return content

    def _split_function_call(self, line: str) -> str:
        """関数呼び出しの引数を複数行に分割"""
        indent = len(line) - len(line.lstrip())
        base_indent = " " * indent

        # 簡単な関数呼び出しパターンをマッチ
        match = re.match(r"(\s*)([^(]+)\((.*)\)(.*)$", line)
        if not match:
            return line

        prefix, func_name, args, suffix = match.groups()
        if "," not in args or len(line) <= self.max_line_length:
            return line

        arg_parts = [arg.strip() for arg in args.split(",") if arg.strip()]
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
        # 簡単な文字列分割実装
        if len(line) > self.max_line_length and ('"' in line or "'" in line):
            # 文字列の開始位置を見つける
            quote_start = -1
            quote_char = None
            for i, char in enumerate(line):
                if char in ['"', "'"]:
                    quote_start = i
                    quote_char = char
                    break

            if quote_start >= 0:
                # 80%の位置で分割を試みる
                split_pos = int(self.max_line_length * 0.8)
                if split_pos > quote_start:
                    # インデントを保持
                    indent = len(line) - len(line.lstrip())
                    base_indent = " " * indent

                    # 単純な分割（改善の余地あり）
                    part1 = line[:split_pos]
                    part2 = line[split_pos:]

                    # 文字列連結の形式で返す
                    if quote_char and quote_char in part1 and quote_char in part2:
                        return (
                            f"{part1}{quote_char} \\\n"
                            f"{base_indent}    {quote_char}{part2.lstrip()}"
                        )

        return line

    def _split_at_operators(self, line: str) -> str:
        """演算子位置で行を分割"""
        if len(line) <= self.max_line_length:
            return line

        operators = [" and ", " or ", " + ", " - ", " * ", " / ", " == ", " != "]
        for op in operators:
            parts = line.split(op)
            if len(parts) == 2:
                indent = len(line) - len(line.lstrip())
                first_part = parts[0].rstrip()
                second_part = parts[1].lstrip()

                if len(first_part) < self.max_line_length:
                    return (
                        f"{first_part}{op.rstrip()} \\\n"
                        f"{' ' * (indent + 4)}{second_part}"
                    )

        return line

    def fix_e226_missing_whitespace(self, content: str, line_num: int, col: int) -> str:
        """E226: 演算子周辺の空白不足を修正"""
        self._last_fix_count = 0
        lines = content.split("\n")
        if line_num > len(lines):
            return content

        line = lines[line_num - 1]
        operators = ["==", "!=", "<=", ">=", "+=", "-=", "*=", "/="]

        for op in operators:
            if op in line:
                pattern = r"(\w)(" + re.escape(op) + r")(\w)"
                fixed_line = re.sub(pattern, rf"\1 {op} \3", line)
                lines[line_num - 1] = fixed_line
                self._last_fix_count = 1
                return "\n".join(lines)

        return content

    def fix_f401_unused_import(self, content: str, line_num: int) -> str:
        """F401: 未使用importを削除"""
        self._last_fix_count = 0
        lines = content.split("\n")
        if line_num > len(lines):
            return content

        line = lines[line_num - 1]
        import_names = self._extract_import_names(line)

        if import_names and self._is_import_unused(content, import_names, line_num):
            # import行を削除
            del lines[line_num - 1]
            self._last_fix_count = 1
            return "\n".join(lines)

        return content

    def _is_import_unused(
        self, content: str, import_names: List[str], line_num: int
    ) -> bool:
        """インポートが未使用かどうかを判定"""
        # AST解析を試行
        if self._check_usage_with_ast(content, import_names, line_num):
            return False

        # フォールバック: 文字列チェック
        return self._check_usage_with_fallback(content, import_names)

    def _check_usage_with_ast(
        self, content: str, import_names: List[str], line_num: int
    ) -> bool:
        """ASTを使用した使用状況チェック"""
        try:
            tree = ast.parse(content)

            # 使用されている名前を収集
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    used_names.add(node.attr)

            # 未使用かチェック
            for name in import_names:
                if name in used_names:
                    # import行以外でも使用されているかチェック
                    if content.count(name) > 1:
                        return True
            return False
        except Exception:
            return False

    def _check_usage_with_fallback(self, content: str, import_names: List[str]) -> bool:
        """フォールバック: 文字列チェック"""
        for name in import_names:
            # より厳密なチェック: 単語境界を考慮
            pattern = r"\b" + re.escape(name) + r"\b"
            matches = list(re.finditer(pattern, content))
            # import行以外での使用をチェック
            if len(matches) > 1:
                return False
        return True

    def fix_e704_multiple_statements(self, content: str, line_num: int) -> str:
        """E704: 複数文を複数行に分割"""
        self._last_fix_count = 0
        lines = content.split("\n")
        if line_num > len(lines):
            return content

        line = lines[line_num - 1]
        statements = []
        current_statement = ""
        i = 0
        in_string = False
        quote_char = None

        while i < len(line):
            char = line[i]

            if not in_string and char in ['"', "'"]:
                in_string = True
                quote_char = char
            elif in_string and char == quote_char:
                # エスケープされたクォートでないかチェック
                if i == 0 or line[i - 1] != "\\":
                    in_string = False
                    quote_char = None
            elif not in_string and char == ";":
                # セミコロンで文を分割
                if current_statement.strip():
                    statements.append(current_statement.strip())
                current_statement = ""
                i += 1
                continue

            current_statement += char
            i += 1

        # 最後の文を追加
        if current_statement.strip():
            statements.append(current_statement.strip())

        # 複数文がある場合は分割
        if len(statements) > 1:
            indent = len(line) - len(line.lstrip())
            base_indent = " " * indent

            # 複数行に分割
            new_lines = []
            for stmt in statements:
                new_lines.append(f"{base_indent}{stmt}")

            # 元の行を置き換え
            lines[line_num - 1 : line_num] = new_lines
            self._last_fix_count = 1
            return "\n".join(lines)

        return content

    def generate_fix_report(
        self, fixes_applied: Dict[str, int], file_path: str
    ) -> Dict[str, Any]:
        """修正レポートを生成"""
        import datetime

        report: Dict[str, Any] = {
            "file": file_path,
            "timestamp": datetime.datetime.now().isoformat(),
            "fixes": fixes_applied.copy(),
            "total_fixes": sum(fixes_applied.values()),
            "success": True,
        }

        # 修正の詳細
        details: List[Dict[str, Any]] = []
        for error_code, count in fixes_applied.items():
            if count > 0 and error_code != "total":
                detail = {
                    "error_code": error_code,
                    "fixes_count": count,
                    "description": self._get_error_description(error_code),
                }
                details.append(detail)

        report["details"] = details
        return report

    def _get_error_description(self, error_code: str) -> str:
        """エラーコードの説明を取得"""
        descriptions = {
            "E501": "Line too long - 長い行を複数行に分割",
            "E226": "Missing whitespace around operator - 演算子周辺の空白を追加",
            "F401": "Imported but unused - 未使用importを削除",
            "E704": "Multiple statements on one line - 複数文を分割",
            "E702": "Multiple statements on one line - 複数文を分割",
            "E302": "Expected 2 blank lines - 空行を追加",
        }
        return descriptions.get(error_code, f"Unknown error: {error_code}")

    def generate_html_report(
        self, reports: List[Dict[str, Any]], output_path: str
    ) -> None:
        """HTML形式の修正レポートを生成"""
        import datetime

        html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flake8 Auto-Fix Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
        }}
        .header {{
            background: #2c3e50; color: white; padding: 20px; border-radius: 5px;
        }}
        .summary {{
            background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px;
        }}
        .file-report {{ border: 1px solid #ddd; margin: 15px 0; border-radius: 5px; }}
        .file-header {{ background: #3498db; color: white; padding: 10px; }}
        .file-content {{ padding: 15px; }}
        .fix-item {{ background: #e8f5e8; padding: 8px; margin: 5px 0;
                     border-left: 4px solid #27ae60; }}
        .stats {{ display: flex; gap: 20px; }}
        .stat-item {{ text-align: center; }}
        .stat-number {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .timestamp {{ color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔧 Flake8 Auto-Fix Report</h1>
        <p>Kumihan-Formatter Issue #778 - Phase 3.2</p>
        <p class="timestamp">Generated: {timestamp}</p>
    </div>
    <div class="summary">
        <h2>📊 Summary</h2>
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{total_files}</div>
                <div>Files Processed</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_fixes}</div>
                <div>Total Fixes</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{success_rate}%</div>
                <div>Success Rate</div>
            </div>
        </div>
    </div>
    <div class="files">
        <h2>📁 File Reports</h2>
        {file_reports}
    </div>
</body>
</html>"""

        total_files = len(reports)
        total_fixes = sum(report.get("total_fixes", 0) for report in reports)
        success_files = sum(1 for report in reports if report.get("success", False))
        success_rate = round(
            (success_files / total_files * 100) if total_files > 0 else 0
        )

        file_reports_html = ""
        for report in reports:
            file_html = f"""
            <div class="file-report">
                <div class="file-header">
                    <strong>{report['file']}</strong>
                    <span style="float: right;">
                        {report['total_fixes']} fixes applied
                    </span>
                </div>
                <div class="file-content">
                    {self._generate_fixes_html(report.get('details', []))}
                </div>
            </div>
            """
            file_reports_html += file_html

        html_content = html_template.format(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_files=total_files,
            total_fixes=total_fixes,
            success_rate=success_rate,
            file_reports=file_reports_html,
        )

        try:
            Path(output_path).write_text(html_content, encoding="utf-8")
            self.logger.info(f"HTML report generated: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")

    def _generate_fixes_html(self, details: List[Dict[str, Any]]) -> str:
        """Generate HTML for fix details"""
        if not details:
            return "<p>No fixes applied.</p>"

        html = ""
        for detail in details:
            html += f"""
            <div style="margin: 10px 0; padding: 10px; border-left: 3px solid #28a745;">
                <strong>{detail['error_code']}</strong>: {detail['description']}
                <span style="float: right;">{detail['fixes_count']} fixes</span>
            </div>
            """
        return html

    def _extract_import_names(self, import_line: str) -> List[str]:
        """Extract names from import statement"""
        names = []

        if import_line.strip().startswith("import "):
            # import module
            module = import_line.replace("import ", "").strip()
            names.append(module.split(".")[0])

        elif import_line.strip().startswith("from "):
            # from module import name
            match = re.match(r"from\s+\S+\s+import\s+(.+)", import_line)
            if match:
                imports = match.group(1)
                for name in imports.split(","):
                    names.append(name.strip().split(" as ")[0])

        return names
