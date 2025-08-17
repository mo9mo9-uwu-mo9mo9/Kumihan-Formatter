"""
Automatic fixer core module for lint command.

Issue #778: flake8自動修正ツール - Flake8AutoFixerクラス分離
Technical Debt Reduction: auto_fixer.py分割による可読性向上
"""

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger


class Flake8AutoFixerCore:
    """
    Flake8エラーの自動修正を行うクラスのコア機能

    Issue #778: flake8自動修正ツール
    Phase 3.1: E501, E226, F401エラーの自動修正
    Phase 3.2: E704, 複合エラー処理, HTML レポート
    Phase 3.3: 品質監視機能, リアルタイム統計
    """

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
        except Exception:
            pass
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

            errors: List[Dict[str, Any]] = []
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
        except Exception as e:
            self.logger.error(f"Failed to get flake8 errors: {e}")
            return []

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

        # selectリストがある場合、それ以外はスキップ
        select_codes = config_settings.get("select_codes", [])
        if select_codes and error_code not in select_codes:
            self.logger.debug(f"Skipping {error_code} (not in select list)")
            return False

        return True

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

    def fix_file(self, file_path: str, dry_run: bool = False) -> Dict[str, Any]:
        """Fix flake8 errors in file (Phase 3.3 quality monitoring)"""
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

            # Get flake8 errors and filter by type if specified
            all_errors = self.get_flake8_errors(file_path)

            if self.error_types:
                filtered_errors = [
                    error for error in all_errors if error["code"] in self.error_types
                ]
            else:
                filtered_errors = all_errors

            total_errors = len(filtered_errors)

            # 最適な修正順序で並び替え
            _ = self.get_optimized_fix_order(filtered_errors)

            # 各エラーを順番に修正は統合されたクラスで実行
            # この関数は基本的なコア機能のみを提供し、実際の修正は統合クラスで行う

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

            # 基本レポート生成
            return {
                "file": file_path,
                "total_fixes": total_fixes,
                "success": True,
            }

        except Exception as e:
            self.logger.error(f"Failed to fix file {file_path}: {e}")
            return {
                "error": 1,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
