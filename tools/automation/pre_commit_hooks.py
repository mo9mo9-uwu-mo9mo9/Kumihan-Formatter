"""
pre-commitフック統合管理システム

既存の.pre-commit-config.yamlと連携し、
品質ルール（quality_rules.yml）を適用した
統合的な品質チェックを実行する
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HookResult:
    """フック実行結果"""

    hook_id: str
    success: bool
    output: str
    error: str
    execution_time: float


class PreCommitHookManager:
    """pre-commitフック統合管理"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.quality_rules_path = (
            self.project_root / ".github" / "quality" / "quality_rules.yml"
        )
        self.pre_commit_config_path = self.project_root / ".pre-commit-config.yaml"
        self.quality_rules = self._load_quality_rules()

        # 初期化時にディレクトリとファイル権限をチェック
        logger.debug(f"Project root: {self.project_root}")
        logger.debug(f"Pre-commit config: {self.pre_commit_config_path}")
        logger.debug(f"Quality rules: {self.quality_rules_path}")

    def _load_quality_rules(self) -> Dict[str, Any]:
        """品質ルール設定読み込み"""
        try:
            if self.quality_rules_path.exists():
                with open(self.quality_rules_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            logger.warning(f"Quality rules file not found: {self.quality_rules_path}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load quality rules: {e}")
            return {}

    def validate_pre_commit_config(self) -> bool:
        """pre-commit設定ファイル検証（強化版）"""
        try:
            # 設定ファイルの存在確認
            if not self.pre_commit_config_path.exists():
                logger.error(f"Pre-commit config file not found: {self.pre_commit_config_path}")
                return False

            # ファイル読み込み可能性チェック
            try:
                with open(self.pre_commit_config_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content.strip():
                        logger.error("Pre-commit config file is empty")
                        return False
            except PermissionError:
                logger.error(f"Permission denied reading: {self.pre_commit_config_path}")
                return False
            except UnicodeDecodeError as e:
                logger.error(f"File encoding error: {e}")
                return False

            # YAML構文チェック
            try:
                with open(self.pre_commit_config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    if config is None:
                        logger.error("Pre-commit config file contains invalid YAML (null)")
                        return False
            except yaml.YAMLError as e:
                logger.error(f"YAML syntax error in pre-commit config: {e}")
                return False

            # 基本構造チェック
            if not isinstance(config, dict):
                logger.error("Pre-commit config root must be a dictionary")
                return False

            repos = config.get("repos")
            if not repos:
                logger.error("Pre-commit config missing 'repos' section")
                return False

            if not isinstance(repos, list):
                logger.error("Pre-commit config 'repos' must be a list")
                return False

            # フック収集
            existing_hooks = []
            for i, repo in enumerate(repos):
                if not isinstance(repo, dict):
                    logger.warning(f"Repository {i} is not a dictionary")
                    continue

                hooks = repo.get("hooks", [])
                if not isinstance(hooks, list):
                    logger.warning(f"Repository {i} 'hooks' is not a list")
                    continue

                for j, hook in enumerate(hooks):
                    if not isinstance(hook, dict):
                        logger.warning(f"Hook {j} in repository {i} is not a dictionary")
                        continue

                    hook_id = hook.get("id")
                    if hook_id:
                        existing_hooks.append(hook_id)
                        logger.debug(f"Found hook: {hook_id}")

            # 必須フックの存在確認
            required_hooks = ["python-lint", "mypy-type-check", "claude-md-check"]
            missing_hooks = [
                hook for hook in required_hooks if hook not in existing_hooks
            ]

            if missing_hooks:
                logger.error(f"Missing required hooks: {missing_hooks}")
                logger.error(f"Found hooks: {existing_hooks}")
                return False

            # 成功ログ
            logger.info((
                f"Pre-commit config validation successful. Found {len(existing_hooks)} hooks.")
            )
            logger.debug(f"Required hooks verified: {required_hooks}")

            return True

        except Exception as e:
            logger.error((
                f"Unexpected error during pre-commit config validation: {type(e).__name__}: {e}")
            )
            return False

    def run_quality_hooks(
        self, staged_files: Optional[List[str]] = None
    ) -> List[HookResult]:
        """品質チェックフック実行"""
        results = []

        # 品質ルールに基づく実行対象フック決定
        target_hooks = self._get_target_hooks_from_rules()

        for hook_id in target_hooks:
            result = self._run_single_hook(hook_id, staged_files)
            results.append(result)

            # 品質ゲート: 重要なフックが失敗した場合は中断
            if not result.success and self._is_blocking_hook(hook_id):
                logger.error(f"Blocking hook failed: {hook_id}")
                break

        return results

    def _get_target_hooks_from_rules(self) -> List[str]:
        """品質ルールから実行対象フック決定"""
        default_hooks = ["python-lint", "mypy-type-check", "claude-md-check"]

        if not self.quality_rules:
            return default_hooks

        # 品質ルールの enforcement設定に基づく
        enforcement = self.quality_rules.get("enforcement", {})
        if enforcement.get("strict_mode", True):
            return default_hooks + ["kumihan-lint-fix", "smart-memory-cleanup"]

        return default_hooks

    def _run_single_hook(
        self, hook_id: str, staged_files: Optional[List[str]] = None
    ) -> HookResult:
        """単一フック実行"""
        import time

        start_time = time.time()

        try:
            cmd = ["pre-commit", "run", hook_id]
            if staged_files:
                cmd.extend(["--files"] + staged_files)
            else:
                cmd.append("--all-files")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300,  # 5分タイムアウト
            )

            execution_time = time.time() - start_time

            return HookResult(
                hook_id=hook_id,
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                execution_time=execution_time,
            )

        except subprocess.TimeoutExpired:
            logger.error(f"Hook {hook_id} timed out")
            return HookResult(
                hook_id=hook_id,
                success=False,
                output="",
                error="Hook execution timed out",
                execution_time=300.0,
            )
        except Exception as e:
            logger.error(f"Failed to run hook {hook_id}: {e}")
            return HookResult(
                hook_id=hook_id,
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time,
            )

    def _is_blocking_hook(self, hook_id: str) -> bool:
        """フックがブロッキング（失敗時中断）かどうか判定"""
        blocking_hooks = {"python-lint", "mypy-type-check"}

        # 品質ルールから動的判定
        strict_mode = self.quality_rules.get("enforcement", {}).get("strict_mode", True)

        if strict_mode and hook_id in blocking_hooks:
            return True

        return False

    def generate_hook_report(self, results: List[HookResult]) -> Dict[str, Any]:
        """フック実行結果レポート生成"""
        total_hooks = len(results)
        successful_hooks = sum(1 for r in results if r.success)
        failed_hooks = [r for r in results if not r.success]
        total_time = sum(r.execution_time for r in results)

        report = {
            "summary": {
                "total_hooks": total_hooks,
                "successful": successful_hooks,
                "failed": len(failed_hooks),
                "success_rate": (
                    successful_hooks / total_hooks if total_hooks > 0 else 0
                ),
                "total_execution_time": total_time,
            },
            "results": [
                {
                    "hook_id": r.hook_id,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "output": r.output if r.success else r.error,
                }
                for r in results
            ],
            "quality_gate_status": (
                "PASSED" if successful_hooks == total_hooks else "FAILED"
            ),
        }

        return report

    def save_report(
        self, report: Dict[str, Any], output_path: Optional[Path] = None
    ) -> Path:
        """レポートをファイルに保存"""
        if output_path is None:
            os.makedirs("tmp", exist_ok=True)
            output_path = Path("tmp") / "pre_commit_report.json"

        import json

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Pre-commit report saved to: {output_path}")
        return output_path


def main():
    """CLI エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Pre-commit hook manager")
    parser.add_argument(
        "--validate", action="store_true", help="Validate pre-commit config"
    )
    parser.add_argument("--run", action="store_true", help="Run quality hooks")
    parser.add_argument("--files", nargs="*", help="Specific files to check")
    parser.add_argument("--report", type=str, help="Output report file path")

    args = parser.parse_args()

    manager = PreCommitHookManager()

    if args.validate:
        valid = manager.validate_pre_commit_config()
        status = 'PASSED' if valid else 'FAILED'
        print(f"Pre-commit config validation: {status}")

        # 詳細情報を追加で出力
        if valid:
            print("✅ All required hooks are present and configuration is valid.")
        else:
            print("❌ Pre-commit configuration validation failed. Check logs for details.")

        return 0 if valid else 1

    if args.run:
        results = manager.run_quality_hooks(args.files)
        report = manager.generate_hook_report(results)

        if args.report:
            manager.save_report(report, Path(args.report))
        else:
            import json

            print(json.dumps(report, indent=2, ensure_ascii=False))

        return 0 if report["quality_gate_status"] == "PASSED" else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    exit(main())
