"""
lint コマンド実装

Issue #778: flake8自動修正ツール実装
Phase 3.1: 基本自動修正機能（E501, E226, F401）
"""

import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click

from kumihan_formatter.core.utilities.logger import get_logger


class Flake8AutoFixer:
    """flake8エラー自動修正エンジン"""

    def __init__(
        self, config_path: Optional[str] = None, error_types: Optional[List[str]] = None
    ):
        self.logger = get_logger(__name__)
        self.config_path = config_path or ".flake8"
        self.max_line_length = self._get_max_line_length()
        self.error_types = error_types  # 修正対象のエラータイプリスト
        self.fixes_applied = {
            "E501": 0,
            "E226": 0,
            "F401": 0,
            "E704": 0,
            "E702": 0,
            "total": 0,
        }

        # Phase 3.3: Quality monitoring
        self.quality_metrics = {
            "files_processed": 0,
            "errors_detected": 0,
            "errors_fixed": 0,
            "fix_success_rate": 0.0,
            "processing_time": 0.0,
            "average_errors_per_file": 0.0,
        }

    def _get_max_line_length(self) -> int:
        """.flake8設定から行長制限を取得"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                content = config_file.read_text()
                match = re.search(r"max-line-length\s*=\s*(\d+)", content)
                if match:
                    return int(match.group(1))
        except Exception as e:
            self.logger.warning(f"Failed to read flake8 config: {e}")

        return 100  # デフォルト値

    def get_flake8_errors(self, file_path: str) -> List[Dict[str, Any]]:
        """指定ファイルのflake8エラー一覧を取得"""
        try:
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "flake8",
                    "--config",
                    self.config_path,
                    "--format",
                    "%(path)s:%(row)d:%(col)d: %(code)s %(text)s",
                    file_path,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            errors = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    match = re.match(r"(.+):(\d+):(\d+): (\w+) (.+)", line)
                    if match:
                        errors.append(
                            {
                                "file": match.group(1),
                                "line": int(match.group(2)),
                                "col": int(match.group(3)),
                                "code": match.group(4),
                                "message": match.group(5),
                            }
                        )

            # stderrも確認（エラー出力はstderrに行く場合がある）
            if result.stderr and not errors:
                for line in result.stderr.strip().split("\n"):
                    if line.strip():
                        match = re.match(r"(.+):(\d+):(\d+): (\w+) (.+)", line)
                        if match:
                            errors.append(
                                {
                                    "file": match.group(1),
                                    "line": int(match.group(2)),
                                    "col": int(match.group(3)),
                                    "code": match.group(4),
                                    "message": match.group(5),
                                }
                            )

            self.logger.debug(f"Found {len(errors)} flake8 errors in {file_path}")
            return errors

        except subprocess.TimeoutExpired:
            self.logger.error(f"flake8 timeout for {file_path}")
            return []
        except Exception as e:
            self.logger.error(f"Failed to run flake8 on {file_path}: {e}")
            return []

    def fix_e501_line_too_long(self, content: str, line_num: int) -> str:
        """E501: 行が長すぎる場合の自動修正"""
        lines = content.split("\n")
        if line_num > len(lines):
            return content

        line = lines[line_num - 1]
        if len(line) <= self.max_line_length:
            return content

        # 修正パターン1: 関数引数の分割
        if "(" in line and ")" in line:
            fixed_line = self._split_function_call(line)
            if fixed_line != line:
                lines[line_num - 1] = fixed_line
                self.fixes_applied["E501"] += 1
                return "\n".join(lines)

        # 修正パターン2: 文字列の分割
        if '"' in line or "'" in line:
            fixed_line = self._split_long_string(line)
            if fixed_line != line:
                lines[line_num - 1] = fixed_line
                self.fixes_applied["E501"] += 1
                return "\n".join(lines)

        # 修正パターン3: 演算子での分割
        fixed_line = self._split_at_operators(line)
        if fixed_line != line:
            lines[line_num - 1] = fixed_line
            self.fixes_applied["E501"] += 1
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

        # 引数を分割
        if "," in args:
            arg_parts = [arg.strip() for arg in args.split(",")]
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

        # 一般的な演算子位置で分割
        operators = [" and ", " or ", " + ", " - ", " * ", " / ", " == ", " != "]

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
        lines = content.split("\n")
        if line_num > len(lines):
            return content

        line = lines[line_num - 1]

        # 演算子の前後に空白を追加
        operators = ["=", "+", "-", "*", "/", "==", "!=", "<=", ">=", "<", ">"]

        for op in operators:
            # 演算子前後の空白チェック
            pattern = rf"(\w){re.escape(op)}(\w)"
            if re.search(pattern, line):
                fixed_line = re.sub(pattern, rf"\1 {op} \2", line)
                lines[line_num - 1] = fixed_line
                self.fixes_applied["E226"] += 1
                return "\n".join(lines)

        return content

    def fix_f401_unused_import(self, content: str, line_num: int) -> str:
        """F401: 未使用importを削除"""
        lines = content.split("\n")
        if line_num > len(lines):
            return content

        line = lines[line_num - 1]

        # import文かどうかチェック
        if line.strip().startswith(("import ", "from ")):
            # import名を抽出
            import_names = self._extract_import_names(line)

            # 使用状況をチェック
            if self._is_import_unused(content, import_names, line_num):
                # import行を削除
                del lines[line_num - 1]
                self.fixes_applied["F401"] += 1
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
            import ast

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

        except (SyntaxError, Exception) as e:
            self.logger.debug(f"AST parsing failed, using fallback: {e}")
            return False

    def _check_usage_with_fallback(self, content: str, import_names: List[str]) -> bool:
        """フォールバック: 文字列チェック"""
        import re

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
        lines = content.split("\n")
        if line_num > len(lines):
            return content

        line = lines[line_num - 1]

        # セミコロンで区切られた複数文をチェック
        if ";" in line and not line.strip().startswith("#"):
            # 文字列内のセミコロンは除外
            in_string = False
            quote_char = None
            statements = []
            current_statement = ""

            i = 0
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
                self.fixes_applied["E702"] = self.fixes_applied.get("E702", 0) + 1
                return "\n".join(lines)

        return content

    def analyze_error_dependencies(
        self, errors: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """エラー間の依存関係を分析"""
        dependencies: Dict[str, List[str]] = {}

        for error in errors:
            error_code = error["code"]
            line_num = error["line"]

            # E501とE704の依存関係
            if error_code == "E501":
                # 同じ行にE704がある場合、E704を先に修正
                for other_error in errors:
                    if (
                        other_error["line"] == line_num
                        and other_error["code"] == "E704"
                    ):
                        dependencies[error_code] = dependencies.get(error_code, [])
                        dependencies[error_code].append("E704")

            # F401とE302の依存関係
            elif error_code == "E302":
                # 近くにF401がある場合、F401を先に修正
                for other_error in errors:
                    if (
                        abs(int(other_error["line"]) - int(line_num)) <= 2
                        and other_error["code"] == "F401"
                    ):
                        dependencies[error_code] = dependencies.get(error_code, [])
                        dependencies[error_code].append("F401")

        return dependencies

    def get_optimized_fix_order(
        self, errors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """最適な修正順序を計算"""
        # 依存関係に基づいて修正順序を決定
        priority_order = ["F401", "E704", "E501", "E226", "E302"]

        sorted_errors = []
        for priority_code in priority_order:
            for error in errors:
                if error["code"] == priority_code:
                    sorted_errors.append(error)

        # 残りのエラーを追加
        for error in errors:
            if error not in sorted_errors:
                sorted_errors.append(error)

        return sorted_errors

    def sync_with_flake8_config(self, config_path: str) -> Dict[str, Any]:
        """flake8設定ファイルとの同期"""
        config_settings = {
            "max_line_length": 100,
            "ignore_codes": [],
            "select_codes": [],
            "exclude_patterns": [],
        }

        try:
            config_file = Path(config_path)
            if config_file.exists():
                content = config_file.read_text()

                # max-line-lengthの取得
                match = re.search(r"max-line-length\s*=\s*(\d+)", content)
                if match:
                    config_settings["max_line_length"] = int(match.group(1))

                # ignoreパターンの取得
                ignore_match = re.search(r"ignore\s*=\s*([^\n]+)", content)
                if ignore_match:
                    ignore_codes = [
                        code.strip() for code in ignore_match.group(1).split(",")
                    ]
                    config_settings["ignore_codes"] = ignore_codes

                # selectパターンの取得
                select_match = re.search(r"select\s*=\s*([^\n]+)", content)
                if select_match:
                    select_codes = [
                        code.strip() for code in select_match.group(1).split(",")
                    ]
                    config_settings["select_codes"] = select_codes

                # excludeパターンの取得
                exclude_match = re.search(r"exclude\s*=\s*([^\n]+)", content)
                if exclude_match:
                    exclude_patterns = [
                        pattern.strip() for pattern in exclude_match.group(1).split(",")
                    ]
                    config_settings["exclude_patterns"] = exclude_patterns

                self.logger.info(f"Loaded flake8 config: {config_settings}")

        except Exception as e:
            self.logger.warning(f"Failed to sync with flake8 config: {e}")

        return config_settings

    def should_fix_error(
        self, error_code: str, config_settings: Dict[str, Any]
    ) -> bool:
        """設定に基づいてエラーを修正すべきかチェック"""
        # ignoreリストにある場合はスキップ
        ignore_codes = config_settings.get("ignore_codes", [])
        if error_code in ignore_codes:
            self.logger.debug(f"Skipping {error_code} (in ignore list)")
            return False

        # selectリストが指定されている場合はそれに含まれるもののみ修正
        select_codes = config_settings.get("select_codes", [])
        if select_codes:
            # エラーコードの先頭文字をチェック（E, W, F, C）
            error_prefix = error_code[0] if error_code else ""
            if error_prefix not in select_codes and error_code not in select_codes:
                self.logger.debug(f"Skipping {error_code} (not in select list)")
                return False

        self.logger.debug(f"Will fix {error_code}")
        return True

    def generate_fix_report(
        self, fixes_applied: Dict[str, int], file_path: str
    ) -> Dict[str, Any]:
        """修正レポートを生成"""
        report = {
            "file": file_path,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "fixes": fixes_applied.copy(),
            "total_fixes": sum(fixes_applied.values()),
            "success": True,
        }

        # 修正の詳細
        report["details"] = []
        for error_code, count in fixes_applied.items():
            if count > 0 and error_code != "total":
                detail = {
                    "error_code": error_code,
                    "fixes_count": count,
                    "description": self._get_error_description(error_code),
                }
                report["details"].append(detail)

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

    def update_quality_metrics(
        self, errors_detected: int, errors_fixed: int, processing_time: float
    ) -> None:
        """Phase 3.3: Quality monitoring metrics update"""
        self.quality_metrics["files_processed"] += 1
        self.quality_metrics["errors_detected"] += errors_detected
        self.quality_metrics["errors_fixed"] += errors_fixed
        self.quality_metrics["processing_time"] += processing_time

        # Calculate derived metrics
        if self.quality_metrics["files_processed"] > 0:
            self.quality_metrics["average_errors_per_file"] = (
                self.quality_metrics["errors_detected"]
                / self.quality_metrics["files_processed"]
            )

        if self.quality_metrics["errors_detected"] > 0:
            self.quality_metrics["fix_success_rate"] = (
                self.quality_metrics["errors_fixed"]
                / self.quality_metrics["errors_detected"]
                * 100
            )

    def get_quality_report(self) -> Dict[str, Any]:
        """Phase 3.3: Generate quality monitoring report"""
        return {
            "quality_metrics": self.quality_metrics.copy(),
            "performance": {
                "avg_processing_time_per_file": (
                    self.quality_metrics["processing_time"]
                    / max(self.quality_metrics["files_processed"], 1)
                ),
                "errors_per_second": (
                    self.quality_metrics["errors_detected"]
                    / max(self.quality_metrics["processing_time"], 0.1)
                ),
                "fixes_per_second": (
                    self.quality_metrics["errors_fixed"]
                    / max(self.quality_metrics["processing_time"], 0.1)
                ),
            },
            "summary": {
                "total_files": self.quality_metrics["files_processed"],
                "total_errors": self.quality_metrics["errors_detected"],
                "total_fixes": self.quality_metrics["errors_fixed"],
                "overall_success_rate": round(
                    self.quality_metrics["fix_success_rate"], 2
                ),
            },
        }

    def generate_html_report(
        self, reports: List[Dict[str, Any]], output_path: str
    ) -> None:
        """HTML形式の修正レポートを生成"""
        html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flake8 Auto-Fix Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
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
                    <span style="float: right;">{report['total_fixes']} fixes applied</span>
                </div>
                <div class="file-content">
                    {self._generate_fixes_html(report.get('details', []))}
                </div>
            </div>
            """
            file_reports_html += file_html

        html_content = html_template.format(
            timestamp=__import__("datetime")
            .datetime.now()
            .strftime("%Y-%m-%d %H:%M:%S"),
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
        """修正詳細のHTML生成"""
        if not details:
            return "<p>No fixes applied.</p>"

        html = ""
        for detail in details:
            html += f"""
            <div class="fix-item">
                <strong>{detail['error_code']}</strong>: {detail['description']}
                <span style="float: right;">{detail['fixes_count']} fixes</span>
            </div>
            """
        return html

    def _extract_import_names(self, import_line: str) -> List[str]:
        """import文から名前を抽出"""
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

    def fix_file(self, file_path: str, dry_run: bool = False) -> Dict[str, Any]:
        """ファイルのflake8エラーを自動修正（Phase 3.3品質監視対応）"""
        import time

        start_time = time.time()

        self.logger.info(f"Processing file: {file_path}")

        try:
            file_obj = Path(file_path)
            if not file_obj.exists():
                self.logger.error(f"File not found: {file_path}")
                return {"error": 1}

            original_content = file_obj.read_text(encoding="utf-8")
            content = original_content

            # flake8設定と同期
            config_settings = self.sync_with_flake8_config(self.config_path)

            # flake8エラーを取得
            errors = self.get_flake8_errors(file_path)
            total_errors = len(errors)

            # 設定に基づいてフィルタリング
            filtered_errors = [
                error
                for error in errors
                if self.should_fix_error(error["code"], config_settings)
            ]

            # --typeオプションによるエラータイプフィルタリング
            if self.error_types:
                filtered_errors = [
                    error
                    for error in filtered_errors
                    if error["code"] in self.error_types
                ]

            # 最適な修正順序で並び替え
            optimized_errors = self.get_optimized_fix_order(filtered_errors)

            # 各エラーを順番に修正
            for error in optimized_errors:
                error_code = error["code"]

                if error_code == "E501":
                    content = self.fix_e501_line_too_long(content, int(error["line"]))
                elif error_code == "E226":
                    content = self.fix_e226_missing_whitespace(
                        content, int(error["line"]), int(error["col"])
                    )
                elif error_code == "F401":
                    content = self.fix_f401_unused_import(content, int(error["line"]))
                elif error_code in ["E704", "E702"]:
                    content = self.fix_e704_multiple_statements(
                        content, int(error["line"])
                    )

            # 修正内容を保存（dry_runでない場合）
            if not dry_run and content != original_content:
                file_obj.write_text(content, encoding="utf-8")
                self.logger.info(f"Fixed {file_path}")

            # Phase 3.3: Quality monitoring update
            processing_time = time.time() - start_time
            total_fixes = sum(
                self.fixes_applied.get(code, 0)
                for code in ["E501", "E226", "F401", "E704", "E702"]
            )
            self.update_quality_metrics(total_errors, total_fixes, processing_time)

            # 修正レポート生成
            self.generate_fix_report(self.fixes_applied, file_path)

            return self.fixes_applied

        except Exception as e:
            self.logger.error(f"Failed to fix file {file_path}: {e}")
            import traceback

            self.logger.debug(f"Traceback: {traceback.format_exc()}")
            return {
                "error": 1,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "file_path": file_path,
            }


def _setup_logger(verbose: bool) -> Any:
    """ロガーをセットアップ"""
    logger = get_logger(__name__)
    if verbose:
        logger.setLevel(logging.DEBUG)
    return logger


def _get_target_files(files: Tuple[str, ...]) -> Tuple[str, ...]:
    """対象ファイルを取得"""
    if not files:
        # デフォルト対象：Pythonファイル
        files = tuple(
            str(p) for p in Path(".").rglob("*.py") if not str(p).startswith(".")
        )
    return files


def _run_flake8_check(files: Tuple[str, ...], config: Optional[str]) -> None:
    """flake8チェックを実行"""
    logger = get_logger(__name__)
    logger.info("Running flake8 check...")
    try:
        result = subprocess.run(
            ["python3", "-m", "flake8", "--config", config or ".flake8", *files],
            timeout=60,
        )
        click.echo(f"flake8 check completed with exit code: {result.returncode}")
    except subprocess.TimeoutExpired:
        click.echo("flake8 check timed out", err=True)
    except Exception as e:
        click.echo(f"Failed to run flake8: {e}", err=True)


def _parse_error_types(type_str: Optional[str]) -> Optional[List[str]]:
    """エラータイプを解析"""
    if type_str:
        error_types = [t.strip() for t in type_str.split(",")]
        click.echo(f"Fixing only specified error types: {', '.join(error_types)}")
        return error_types
    return None


def _display_phase_info(advanced: bool, quality_monitoring: bool) -> None:
    """Phase機能の情報を表示"""
    if advanced:
        click.echo("🚀 Advanced mode enabled (Phase 3.2)")
        click.echo(
            "Features: E704 (multiple statements), error dependency analysis, HTML reports"
        )

    if quality_monitoring:
        click.echo("📊 Quality monitoring enabled (Phase 3.3)")
        click.echo("Features: Real-time metrics, performance analysis, quality reports")


def _process_files(
    fixer: "Flake8AutoFixer",
    files: Tuple[str, ...],
    dry_run: bool,
    report: Optional[str],
) -> Tuple[Dict[str, int], List[Any]]:
    """ファイルを処理して修正を適用"""
    total_fixes = {"E501": 0, "E226": 0, "F401": 0, "E704": 0, "E702": 0, "total": 0}
    reports = []

    with click.progressbar(files, label="Fixing files") as file_list:
        for file_path in file_list:
            if file_path.endswith(".py"):
                fixes = fixer.fix_file(file_path, dry_run=dry_run)

                if "error" not in fixes:
                    # Phase 3.2: E704/E702を集計に追加
                    for code in ["E501", "E226", "F401", "E704", "E702"]:
                        total_fixes[code] += fixes.get(code, 0)
                    total_fixes["total"] += sum(
                        fixes.get(code, 0)
                        for code in ["E501", "E226", "F401", "E704", "E702"]
                    )

                    # レポート用データ収集
                    if report:
                        file_report = fixer.generate_fix_report(fixes, file_path)
                        reports.append(file_report)

    return total_fixes, reports


def _display_results(
    total_fixes: Dict[str, int], files: Tuple[str, ...], dry_run: bool, advanced: bool
) -> None:
    """結果を表示"""
    # 結果表示
    if dry_run:
        click.echo("Dry run completed. No files were modified.")
    else:
        click.echo("Auto-fix completed.")

    click.echo("Fixes applied:")
    click.echo(f"  E501 (line too long): {total_fixes['E501']}")
    click.echo(f"  E226 (missing whitespace): {total_fixes['E226']}")
    click.echo(f"  F401 (unused import): {total_fixes['F401']}")

    # Phase 3.2機能の結果表示
    if advanced:
        click.echo(f"  E704 (multiple statements): {total_fixes['E704']}")
        click.echo(f"  E702 (multiple statements): {total_fixes['E702']}")

    click.echo(f"  Total fixes: {total_fixes['total']}")

    # 統計情報
    if advanced and total_fixes["total"] > 0:
        py_files = [f for f in files if f.endswith(".py")]
        success_rate = round((total_fixes["total"] / len(py_files) * 100))
        click.echo("📈 Processing statistics:")
        click.echo(f"  Files processed: {len(py_files)}")
        click.echo(
            f"  Average fixes per file: {round(total_fixes['total'] / len(py_files), 1)}"
        )
        click.echo(f"  Success rate: {success_rate}%")


def _display_quality_report(fixer: "Flake8AutoFixer") -> None:
    """品質監視レポートを表示"""
    quality_report = fixer.get_quality_report()
    click.echo("\n📊 Quality Monitoring Report (Phase 3.3)")
    click.echo("=" * 50)

    summary = quality_report["summary"]
    click.echo(f"Total Files Processed: {summary['total_files']}")
    click.echo(f"Total Errors Detected: {summary['total_errors']}")
    click.echo(f"Total Fixes Applied: {summary['total_fixes']}")
    click.echo(f"Overall Success Rate: {summary['overall_success_rate']}%")

    performance = quality_report["performance"]
    click.echo("\nPerformance Metrics:")
    click.echo(
        f"  Avg Processing Time: {performance['avg_processing_time_per_file']:.3f}s per file"
    )
    click.echo(
        f"  Error Detection Rate: {performance['errors_per_second']:.1f} errors/sec"
    )
    click.echo(
        f"  Fix Application Rate: {performance['fixes_per_second']:.1f} fixes/sec"
    )

    metrics = quality_report["quality_metrics"]
    click.echo("\nQuality Metrics:")
    click.echo(f"  Average Errors per File: {metrics['average_errors_per_file']:.1f}")
    click.echo(f"  Total Processing Time: {metrics['processing_time']:.3f}s")


@click.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option("--fix", is_flag=True, help="自動修正を実行する")
@click.option(
    "--dry-run", is_flag=True, help="修正内容を表示のみ（実際には変更しない）"
)
@click.option("--config", "-c", help="flake8設定ファイルのパス")
@click.option("--verbose", "-v", is_flag=True, help="詳細ログを表示")
@click.option("--report", "-r", help="HTML修正レポートの出力先ファイル")
@click.option(
    "--advanced", is_flag=True, help="Phase 3.2: 高度修正機能を有効にする（E704対応）"
)
@click.option(
    "--quality-monitoring", is_flag=True, help="Phase 3.3: 品質監視機能を有効にする"
)
@click.option(
    "--type", "-t", help="修正するエラータイプを指定（カンマ区切り） 例: E501,E226,F401"
)
def lint_command(
    files: Tuple[str, ...],
    fix: bool,
    dry_run: bool,
    config: Optional[str],
    verbose: bool,
    report: Optional[str],
    advanced: bool,
    quality_monitoring: bool,
    type: Optional[str],
) -> None:
    """コードの品質チェックと自動修正

    Issue #778: flake8自動修正ツール
    Phase 3.1: E501, E226, F401エラーの自動修正
    Phase 3.2: E704, 複合エラー処理, HTML レポート
    Phase 3.3: 品質監視機能, リアルタイム統計
    """
    _setup_logger(verbose)
    files = _get_target_files(files)

    if not fix:
        _run_flake8_check(files, config)
        return

    # 自動修正実行
    error_types = _parse_error_types(type)
    fixer = Flake8AutoFixer(config, error_types)

    _display_phase_info(advanced, quality_monitoring)

    total_fixes, reports = _process_files(fixer, files, dry_run, report)

    # HTML レポート生成
    if report and reports:
        fixer.generate_html_report(reports, report)
        click.echo(f"📊 HTML report generated: {report}")

    _display_results(total_fixes, files, dry_run, advanced)

    # Phase 3.3: Quality monitoring report
    if quality_monitoring:
        _display_quality_report(fixer)
