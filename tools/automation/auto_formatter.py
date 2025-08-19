"""
自動フォーマッター統合システム

Black, isort, autopep8を統合した
自動コード整形システム
"""

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FormatterResult:
    """フォーマッター実行結果"""

    tool: str
    success: bool
    files_changed: List[str]
    output: str
    error: str


class AutoFormatter:
    """自動フォーマッター統合管理"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.quality_rules = self._load_quality_rules()
        self.available_tools = self._detect_available_tools()

    def _load_quality_rules(self) -> Dict[str, Any]:
        """品質ルール読み込み"""
        rules_path = self.project_root / ".github" / "quality" / "quality_rules.yml"
        try:
            if rules_path.exists():
                with open(rules_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            return self._get_default_formatting_rules()
        except Exception as e:
            logger.error(f"Failed to load quality rules: {e}")
            return self._get_default_formatting_rules()

    def _get_default_formatting_rules(self) -> Dict[str, Any]:
        """デフォルトフォーマット設定"""
        return {
            "formatting": {
                "line_length": 88,
                "target_versions": ["py312", "py313"],
                "multi_line_output": 3,
                "include_trailing_comma": True,
                "force_grid_wrap": 0,
                "combine_as_imports": True,
            },
            "enforcement": {"auto_fix": True},
        }

    def _detect_available_tools(self) -> Dict[str, bool]:
        """利用可能なフォーマッターツール検出"""
        tools = {}

        for tool in ["black", "isort", "autopep8"]:
            tools[tool] = shutil.which(tool) is not None

        return tools

    def format_with_black(
        self, target_paths: List[Path], dry_run: bool = False
    ) -> FormatterResult:
        """Black でのフォーマット"""
        if not self.available_tools.get("black", False):
            return FormatterResult(
                tool="black",
                success=False,
                files_changed=[],
                output="",
                error="Black is not available",
            )

        try:
            # 品質ルールからBlack設定を取得
            formatting_rules = self.quality_rules.get("formatting", {})
            line_length = formatting_rules.get("line_length", 88)

            cmd = [
                "python3",
                "-m",
                "black",
                f"--line-length={line_length}",
                "--target-version=py312",
            ]

            if dry_run:
                cmd.extend(["--check", "--diff"])

            # パスを文字列として追加
            cmd.extend([str(path) for path in target_paths])

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )

            # 変更されたファイルを抽出
            files_changed = []
            if not dry_run and result.returncode == 0:
                # Black は変更したファイルを stdout に出力
                for line in result.stdout.split("\n"):
                    if line.startswith("reformatted "):
                        file_path = line.split(" ", 1)[1]
                        files_changed.append(file_path)

            return FormatterResult(
                tool="black",
                success=result.returncode == 0,
                files_changed=files_changed,
                output=result.stdout,
                error=result.stderr,
            )

        except Exception as e:
            logger.error(f"Black formatting failed: {e}")
            return FormatterResult(
                tool="black", success=False, files_changed=[], output="", error=str(e)
            )

    def format_with_isort(
        self, target_paths: List[Path], dry_run: bool = False
    ) -> FormatterResult:
        """isort でのフォーマット"""
        if not self.available_tools.get("isort", False):
            return FormatterResult(
                tool="isort",
                success=False,
                files_changed=[],
                output="",
                error="isort is not available",
            )

        try:
            # 品質ルールからisort設定を取得
            formatting_rules = self.quality_rules.get("formatting", {})

            cmd = [
                "python3",
                "-m",
                "isort",
                f"--line-length={formatting_rules.get('line_length', 88)}",
                f"--multi-line={formatting_rules.get('multi_line_output', 3)}",
            ]

            if formatting_rules.get("include_trailing_comma", True):
                cmd.append("--trailing-comma")

            if formatting_rules.get("combine_as_imports", True):
                cmd.append("--combine-as")

            if dry_run:
                cmd.extend(["--check-only", "--diff"])

            # パスを文字列として追加
            cmd.extend([str(path) for path in target_paths])

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )

            # 変更されたファイルを抽出
            files_changed = []
            if not dry_run and result.returncode == 0:
                # isort は変更したファイルを stderr に出力
                for line in result.stderr.split("\n"):
                    if "Fixing " in line:
                        file_path = line.split("Fixing ")[1]
                        files_changed.append(file_path)

            return FormatterResult(
                tool="isort",
                success=result.returncode == 0,
                files_changed=files_changed,
                output=result.stdout,
                error=result.stderr,
            )

        except Exception as e:
            logger.error(f"isort formatting failed: {e}")
            return FormatterResult(
                tool="isort", success=False, files_changed=[], output="", error=str(e)
            )

    def format_with_autopep8(
        self, target_paths: List[Path], dry_run: bool = False
    ) -> FormatterResult:
        """autopep8 でのフォーマット"""
        if not self.available_tools.get("autopep8", False):
            return FormatterResult(
                tool="autopep8",
                success=False,
                files_changed=[],
                output="",
                error="autopep8 is not available",
            )

        try:
            formatting_rules = self.quality_rules.get("formatting", {})
            line_length = formatting_rules.get("line_length", 88)

            cmd = [
                "autopep8",
                f"--max-line-length={line_length}",
                "--aggressive",
                "--aggressive",
            ]

            if dry_run:
                cmd.append("--diff")
            else:
                cmd.append("--in-place")

            cmd.append("--recursive")

            # パスを文字列として追加
            cmd.extend([str(path) for path in target_paths])

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )

            files_changed = []
            if not dry_run:
                # autopep8 は変更されたファイルのリストを返さないため、
                # 実行前後でファイルを比較する必要がある
                # ここでは簡易的に成功時は対象ファイル全てとする
                if result.returncode == 0:
                    files_changed = [str(path) for path in target_paths]

            return FormatterResult(
                tool="autopep8",
                success=result.returncode == 0,
                files_changed=files_changed,
                output=result.stdout,
                error=result.stderr,
            )

        except Exception as e:
            logger.error(f"autopep8 formatting failed: {e}")
            return FormatterResult(
                tool="autopep8",
                success=False,
                files_changed=[],
                output="",
                error=str(e),
            )

    def run_comprehensive_formatting(
        self,
        target_paths: Optional[List[Path]] = None,
        dry_run: bool = False,
        tools: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """包括的フォーマット実行"""

        if target_paths is None:
            target_paths = [self.project_root / "kumihan_formatter"]

        if tools is None:
            tools = ["black", "isort"]  # デフォルトは Black + isort

        results = []
        all_files_changed = set()

        # 品質ルールから自動修正設定確認
        auto_fix_enabled = self.quality_rules.get("enforcement", {}).get(
            "auto_fix", True
        )

        if not auto_fix_enabled and not dry_run:
            logger.warning(
                "Auto-fix is disabled in quality rules, running in dry-run mode"
            )
            dry_run = True

        # 各ツールを順次実行
        for tool in tools:
            if tool == "black" and self.available_tools.get("black", False):
                result = self.format_with_black(target_paths, dry_run)
                results.append(result)
                all_files_changed.update(result.files_changed)

            elif tool == "isort" and self.available_tools.get("isort", False):
                result = self.format_with_isort(target_paths, dry_run)
                results.append(result)
                all_files_changed.update(result.files_changed)

            elif tool == "autopep8" and self.available_tools.get("autopep8", False):
                result = self.format_with_autopep8(target_paths, dry_run)
                results.append(result)
                all_files_changed.update(result.files_changed)

            else:
                logger.warning(f"Tool {tool} is not available or not supported")

        # 結果サマリー生成
        successful_tools = [r for r in results if r.success]
        failed_tools = [r for r in results if not r.success]

        summary = {
            "total_tools": len(results),
            "successful_tools": len(successful_tools),
            "failed_tools": len(failed_tools),
            "files_changed": list(all_files_changed),
            "files_changed_count": len(all_files_changed),
            "dry_run": dry_run,
            "auto_fix_enabled": auto_fix_enabled,
        }

        return {
            "summary": summary,
            "results": [
                {
                    "tool": r.tool,
                    "success": r.success,
                    "files_changed": r.files_changed,
                    "output": r.output,
                    "error": r.error,
                }
                for r in results
            ],
        }

    def generate_diff_report(self, target_paths: List[Path]) -> str:
        """差分レポート生成"""
        diff_output = []

        # Black での差分
        black_result = self.format_with_black(target_paths, dry_run=True)
        if black_result.success and black_result.output:
            diff_output.append("=== Black Formatting Diff ===")
            diff_output.append(black_result.output)
            diff_output.append("")

        # isort での差分
        isort_result = self.format_with_isort(target_paths, dry_run=True)
        if isort_result.success and isort_result.output:
            diff_output.append("=== isort Import Sorting Diff ===")
            diff_output.append(isort_result.output)
            diff_output.append("")

        return "\n".join(diff_output)

    def save_formatting_report(
        self, report: Dict[str, Any], output_path: Optional[Path] = None
    ) -> Path:
        """フォーマット結果レポート保存"""
        if output_path is None:
            os.makedirs("tmp", exist_ok=True)
            output_path = Path("tmp") / "formatting_report.json"

        import json

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Formatting report saved to: {output_path}")
        return output_path


def main():
    """CLI エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Auto formatter")
    parser.add_argument("--path", type=str, help="Target path to format")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show diff without making changes"
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        choices=["black", "isort", "autopep8"],
        default=["black", "isort"],
        help="Tools to use",
    )
    parser.add_argument("--report", type=str, help="Output report file path")
    parser.add_argument("--diff", action="store_true", help="Show formatting diff")

    args = parser.parse_args()

    formatter = AutoFormatter()

    target_paths = [Path.cwd()]
    if args.path:
        target_paths = [Path(args.path)]

    if args.diff:
        diff_report = formatter.generate_diff_report(target_paths)
        print(diff_report)
        return 0

    report = formatter.run_comprehensive_formatting(
        target_paths=target_paths, dry_run=args.dry_run, tools=args.tools
    )

    if args.report:
        formatter.save_formatting_report(report, Path(args.report))
    else:
        import json

        print(json.dumps(report, indent=2, ensure_ascii=False))

    # 失敗したツールがあれば非ゼロで終了
    return 0 if report["summary"]["failed_tools"] == 0 else 1


if __name__ == "__main__":
    exit(main())
