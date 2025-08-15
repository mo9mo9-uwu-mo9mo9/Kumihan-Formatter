#!/usr/bin/env python3
"""環境検証・修復システム

Gemini実行前に必要な環境をチェック・自動修復し、環境起因の失敗を事前に防止する。
主な対象: ライブラリ依存関係、型スタブファイル、設定ファイル等

主要機能:
- 必須Pythonパッケージの検証・インストール
- 外部ライブラリ型スタブファイルの自動インストール
- プロジェクト固有設定の検証
- 実行環境の総合チェック・修復

Created: 2025-08-15 (Issue #823 Gemini失敗対策)
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import importlib.util

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """検証ステータス"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    FIXED = "fixed"


class DependencyType(Enum):
    """依存関係タイプ"""
    PYTHON_PACKAGE = "python_package"
    TYPE_STUB = "type_stub"
    SYSTEM_COMMAND = "system_command"
    CONFIG_FILE = "config_file"


@dataclass
class Dependency:
    """依存関係情報"""
    name: str
    type: DependencyType
    required_version: Optional[str] = None
    install_command: Optional[str] = None
    check_command: Optional[str] = None
    critical: bool = True
    description: str = ""


@dataclass
class ValidationResult:
    """検証結果"""
    dependency: Dependency
    status: ValidationStatus
    current_version: Optional[str] = None
    error_message: Optional[str] = None
    fix_attempted: bool = False
    fix_successful: bool = False


class EnvironmentValidator:
    """環境検証・修復システム"""

    def __init__(self, reports_dir: Optional[Path] = None) -> None:
        """
        初期化処理

        Args:
            reports_dir: レポートディレクトリ
        """
        self.reports_dir = reports_dir or Path(__file__).parent
        self.validation_results_path = self.reports_dir / "environment_validation.json"
        self.dependencies = self._create_dependency_list()
        self.auto_fix_enabled = True

    def _create_dependency_list(self) -> List[Dependency]:
        """依存関係リストを作成"""
        return [
            # 基本Pythonパッケージ
            Dependency(
                name="mypy",
                type=DependencyType.PYTHON_PACKAGE,
                install_command="python3 -m pip install mypy",
                check_command="python3 -m mypy --version",
                critical=True,
                description="型チェッカー"
            ),
            Dependency(
                name="flake8",
                type=DependencyType.PYTHON_PACKAGE,
                install_command="python3 -m pip install flake8",
                check_command="python3 -m flake8 --version",
                critical=True,
                description="コード品質チェッカー"
            ),
            Dependency(
                name="black",
                type=DependencyType.PYTHON_PACKAGE,
                install_command="python3 -m pip install black",
                check_command="python3 -m black --version",
                critical=False,
                description="コードフォーマッター"
            ),
            Dependency(
                name="isort",
                type=DependencyType.PYTHON_PACKAGE,
                install_command="python3 -m pip install isort",
                check_command="python3 -m isort --version",
                critical=False,
                description="インポート整理ツール"
            ),

            # よく使用される外部ライブラリの型スタブ
            Dependency(
                name="pandas-stubs",
                type=DependencyType.TYPE_STUB,
                install_command="python3 -m pip install pandas-stubs",
                check_command="python3 -c 'import pandas; print(\"OK\")'",
                critical=False,
                description="Pandas型スタブ"
            ),
            Dependency(
                name="types-requests",
                type=DependencyType.TYPE_STUB,
                install_command="python3 -m pip install types-requests",
                critical=False,
                description="Requests型スタブ"
            ),
            Dependency(
                name="types-PyYAML",
                type=DependencyType.TYPE_STUB,
                install_command="python3 -m pip install types-PyYAML",
                critical=False,
                description="PyYAML型スタブ"
            ),

            # プロジェクト固有設定ファイル
            Dependency(
                name="pyproject.toml",
                type=DependencyType.CONFIG_FILE,
                check_command="ls pyproject.toml",
                critical=True,
                description="プロジェクト設定ファイル"
            ),
            Dependency(
                name="CLAUDE.md",
                type=DependencyType.CONFIG_FILE,
                check_command="ls CLAUDE.md",
                critical=False,
                description="Claude設定ファイル"
            )
        ]

    def check_python_package(self, dependency: Dependency) -> ValidationResult:
        """
        Pythonパッケージの検証

        Args:
            dependency: 依存関係情報

        Returns:
            検証結果
        """
        result = ValidationResult(dependency=dependency, status=ValidationStatus.FAIL)

        try:
            # パッケージのインポートテスト
            spec = importlib.util.find_spec(dependency.name)
            if spec is not None:
                result.status = ValidationStatus.PASS
                result.current_version = self._get_package_version(dependency.name)
            else:
                result.error_message = f"パッケージ '{dependency.name}' が見つかりません"

        except ImportError as e:
            result.error_message = f"インポートエラー: {e}"
        except Exception as e:
            result.error_message = f"検証エラー: {e}"

        return result

    def check_type_stub(self, dependency: Dependency) -> ValidationResult:
        """
        型スタブファイルの検証

        Args:
            dependency: 依存関係情報

        Returns:
            検証結果
        """
        result = ValidationResult(dependency=dependency, status=ValidationStatus.FAIL)

        try:
            # 型スタブパッケージのインポートテスト
            stub_name = dependency.name.replace('-stubs', '').replace('types-', '')
            spec = importlib.util.find_spec(stub_name)

            if spec is not None:
                # MyPyでの型チェックテスト
                test_result = self._test_mypy_type_recognition(stub_name)
                if test_result:
                    result.status = ValidationStatus.PASS
                else:
                    result.status = ValidationStatus.WARNING
                    result.error_message = f"型スタブが不完全またはMyPyで認識されません"
            else:
                result.error_message = f"基盤ライブラリ '{stub_name}' が見つかりません"

        except Exception as e:
            result.error_message = f"型スタブ検証エラー: {e}"

        return result

    def check_system_command(self, dependency: Dependency) -> ValidationResult:
        """
        システムコマンドの検証

        Args:
            dependency: 依存関係情報

        Returns:
            検証結果
        """
        result = ValidationResult(dependency=dependency, status=ValidationStatus.FAIL)

        if dependency.check_command:
            try:
                subprocess.run(
                    dependency.check_command.split(),
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10
                )
                result.status = ValidationStatus.PASS

            except subprocess.CalledProcessError as e:
                result.error_message = f"コマンド実行失敗: {e}"
            except subprocess.TimeoutExpired:
                result.error_message = "コマンド実行タイムアウト"
            except Exception as e:
                result.error_message = f"システムコマンド検証エラー: {e}"
        else:
            result.error_message = "チェックコマンドが定義されていません"

        return result

    def check_config_file(self, dependency: Dependency) -> ValidationResult:
        """
        設定ファイルの検証

        Args:
            dependency: 依存関係情報

        Returns:
            検証結果
        """
        result = ValidationResult(dependency=dependency, status=ValidationStatus.FAIL)

        try:
            file_path = Path(dependency.name)
            if file_path.exists():
                # ファイルサイズと読み込み可能性をチェック
                if file_path.stat().st_size > 0:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(100)  # 最初の100文字を読み取り
                    result.status = ValidationStatus.PASS
                else:
                    result.status = ValidationStatus.WARNING
                    result.error_message = "ファイルが空です"
            else:
                result.error_message = f"ファイル '{dependency.name}' が見つかりません"

        except Exception as e:
            result.error_message = f"設定ファイル検証エラー: {e}"

        return result

    def _get_package_version(self, package_name: str) -> Optional[str]:
        """パッケージバージョンを取得"""
        try:
            import pkg_resources  # type: ignore[import-not-found]
            version = pkg_resources.get_distribution(package_name).version
            return str(version) if version is not None else None
        except Exception:
            return None

    def _test_mypy_type_recognition(self, package_name: str) -> bool:
        """MyPyでの型認識テスト"""
        try:
            # 簡単なテストコードでMyPy実行
            test_code = f"import {package_name}\nprint('test')\n"

            with open("temp_type_test.py", "w") as f:
                f.write(test_code)

            result = subprocess.run(
                ["python3", "-m", "mypy", "temp_type_test.py", "--ignore-missing-imports"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # ファイル削除
            Path("temp_type_test.py").unlink(missing_ok=True)

            return result.returncode == 0

        except Exception:
            return False

    def validate_dependency(self, dependency: Dependency) -> ValidationResult:
        """
        単一依存関係の検証

        Args:
            dependency: 依存関係情報

        Returns:
            検証結果
        """
        if dependency.type == DependencyType.PYTHON_PACKAGE:
            return self.check_python_package(dependency)
        elif dependency.type == DependencyType.TYPE_STUB:
            return self.check_type_stub(dependency)
        elif dependency.type == DependencyType.SYSTEM_COMMAND:
            return self.check_system_command(dependency)
        elif dependency.type == DependencyType.CONFIG_FILE:
            return self.check_config_file(dependency)
        else:
            return ValidationResult(
                dependency=dependency,
                status=ValidationStatus.FAIL,
                error_message="未知の依存関係タイプ"
            )

    def attempt_fix(self, result: ValidationResult) -> bool:
        """
        問題の自動修復を試行

        Args:
            result: 検証結果

        Returns:
            修復成功か
        """
        if not self.auto_fix_enabled or not result.dependency.install_command:
            return False

        result.fix_attempted = True

        try:
            logger.info(f"自動修復実行: {result.dependency.name}")

            subprocess.run(
                result.dependency.install_command.split(),
                capture_output=True,
                text=True,
                check=True,
                timeout=120  # 2分タイムアウト
            )

            # 修復後に再検証
            recheck_result = self.validate_dependency(result.dependency)
            if recheck_result.status == ValidationStatus.PASS:
                result.status = ValidationStatus.FIXED
                result.fix_successful = True
                logger.info(f"自動修復成功: {result.dependency.name}")
                return True
            else:
                logger.warning(f"自動修復後も問題が残存: {result.dependency.name}")
                return False

        except subprocess.CalledProcessError as e:
            logger.error(f"自動修復失敗: {result.dependency.name} - {e}")
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"自動修復タイムアウト: {result.dependency.name}")
            return False
        except Exception as e:
            logger.error(f"自動修復エラー: {result.dependency.name} - {e}")
            return False

    def validate_all_dependencies(self, attempt_fixes: bool = True) -> List[ValidationResult]:
        """
        全依存関係の検証

        Args:
            attempt_fixes: 自動修復を試行するか

        Returns:
            検証結果リスト
        """
        results = []

        for dependency in self.dependencies:
            logger.info(f"検証中: {dependency.name}")
            result = self.validate_dependency(dependency)

            # 失敗した場合の自動修復試行
            if (attempt_fixes and
                result.status == ValidationStatus.FAIL and
                dependency.install_command):

                fix_success = self.attempt_fix(result)
                if not fix_success and dependency.critical:
                    logger.error(f"重要な依存関係の修復に失敗: {dependency.name}")

            results.append(result)

        return results

    def get_critical_failures(self, results: List[ValidationResult]) -> List[ValidationResult]:
        """
        重要な失敗を取得

        Args:
            results: 検証結果リスト

        Returns:
            重要な失敗のリスト
        """
        return [
            result for result in results
            if (result.dependency.critical and
                result.status in [ValidationStatus.FAIL])
        ]

    def generate_environment_report(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        環境検証レポートを生成

        Args:
            results: 検証結果リスト

        Returns:
            環境レポート
        """
        critical_failures = self.get_critical_failures(results)

        status_counts = {}
        for status in ValidationStatus:
            status_counts[status.value] = sum(
                1 for result in results if result.status == status
            )

        type_summary = {}
        for dep_type in DependencyType:
            type_results = [r for r in results if r.dependency.type == dep_type]
            type_summary[dep_type.value] = {
                "total": len(type_results),
                "passed": sum(1 for r in type_results if r.status in [ValidationStatus.PASS, ValidationStatus.FIXED]),
                "failed": sum(1 for r in type_results if r.status == ValidationStatus.FAIL)
            }

        # 修復統計
        fix_stats = {
            "attempted": sum(1 for r in results if r.fix_attempted),
            "successful": sum(1 for r in results if r.fix_successful),
            "failed": sum(1 for r in results if r.fix_attempted and not r.fix_successful)
        }

        report = {
            "report_generated": f"{__import__('datetime').datetime.now().isoformat()}",
            "overall_status": "PASS" if not critical_failures else "FAIL",
            "total_dependencies": len(results),
            "critical_failures": len(critical_failures),
            "status_summary": status_counts,
            "type_summary": type_summary,
            "fix_statistics": fix_stats,
            "critical_failure_details": [
                {
                    "name": result.dependency.name,
                    "type": result.dependency.type.value,
                    "error": result.error_message,
                    "fix_attempted": result.fix_attempted
                }
                for result in critical_failures
            ],
            "recommendations": self._generate_recommendations(results)
        }

        # レポートを保存
        try:
            with open(self.validation_results_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"環境レポートの保存に失敗: {e}")

        return report

    def _generate_recommendations(self, results: List[ValidationResult]) -> List[str]:
        """推奨事項を生成"""
        recommendations = []

        # 重要な失敗への対処
        critical_failures = self.get_critical_failures(results)
        if critical_failures:
            recommendations.append("重要な依存関係の問題を最優先で解決してください:")
            for result in critical_failures:
                if result.dependency.install_command:
                    recommendations.append(f"  実行: {result.dependency.install_command}")
                else:
                    recommendations.append(f"  手動で {result.dependency.name} を解決してください")

        # 型スタブの不足
        stub_failures = [
            r for r in results
            if (r.dependency.type == DependencyType.TYPE_STUB and
                r.status == ValidationStatus.FAIL)
        ]
        if stub_failures:
            recommendations.append("型スタブファイルをインストールしてMyPyエラーを減らしてください:")
            for result in stub_failures:
                if result.dependency.install_command:
                    recommendations.append(f"  実行: {result.dependency.install_command}")

        # 自動修復の有効化
        if not self.auto_fix_enabled:
            recommendations.append("auto_fix_enabled=True に設定して自動修復を有効化してください")

        # 成功時のメンテナンス推奨
        if not critical_failures:
            recommendations.append("環境は良好です。定期的に依存関係を更新してください:")
            recommendations.append("  python3 -m pip install --upgrade mypy flake8 black isort")

        return recommendations

    def is_environment_ready_for_gemini(self) -> Tuple[bool, List[str]]:
        """
        Gemini実行に適した環境かを判定

        Returns:
            (環境準備完了か, 問題リスト)
        """
        results = self.validate_all_dependencies(attempt_fixes=True)
        critical_failures = self.get_critical_failures(results)

        if critical_failures:
            issues = [
                f"{result.dependency.name}: {result.error_message}"
                for result in critical_failures
            ]
            return False, issues

        # 警告レベルの問題をチェック
        warnings = [
            result for result in results
            if result.status == ValidationStatus.WARNING
        ]

        warning_messages = [
            f"{result.dependency.name}: {result.error_message}"
            for result in warnings
        ]

        return True, warning_messages

    def prepare_environment_for_task(self, task_description: str) -> Tuple[bool, Dict[str, Any]]:
        """
        特定タスクのための環境準備

        Args:
            task_description: タスク説明

        Returns:
            (準備成功か, 準備レポート)
        """
        # タスク固有の依存関係を特定
        task_lower = task_description.lower()
        required_deps = []

        # MyPy関連タスク
        if any(keyword in task_lower for keyword in ["mypy", "型注釈", "type annotation"]):
            required_deps.extend(["mypy", "pandas-stubs", "types-requests"])

        # Lint関連タスク
        if any(keyword in task_lower for keyword in ["lint", "flake8", "black", "isort"]):
            required_deps.extend(["flake8", "black", "isort"])

        # 外部ライブラリ関連
        if "pandas" in task_lower:
            required_deps.append("pandas-stubs")
        if "requests" in task_lower:
            required_deps.append("types-requests")

        # 特定依存関係の検証・修復
        filtered_deps = [dep for dep in self.dependencies if dep.name in required_deps]
        if not filtered_deps:  # 特定要求がない場合は最低限の依存関係
            filtered_deps = [dep for dep in self.dependencies if dep.critical]

        results = []
        for dependency in filtered_deps:
            result = self.validate_dependency(dependency)
            if result.status == ValidationStatus.FAIL:
                self.attempt_fix(result)
            results.append(result)

        # 準備成功判定
        critical_failures = [r for r in results if r.dependency.critical and r.status == ValidationStatus.FAIL]
        success = len(critical_failures) == 0

        report = {
            "task_description": task_description,
            "required_dependencies": [dep.name for dep in filtered_deps],
            "preparation_successful": success,
            "dependency_results": [asdict(result) for result in results]
        }

        return success, report


def main() -> None:
    """メイン処理（テスト用）"""
    logging.basicConfig(level=logging.INFO)

    validator = EnvironmentValidator()

    print("=== 環境検証開始 ===")
    results = validator.validate_all_dependencies()

    print(f"\n検証完了: {len(results)}件")
    for result in results:
        status_symbol = "✅" if result.status == ValidationStatus.PASS else "❌"
        print(f"{status_symbol} {result.dependency.name}: {result.status.value}")
        if result.error_message:
            print(f"   エラー: {result.error_message}")

    # 環境レポート生成
    report = validator.generate_environment_report(results)
    print(f"\n=== 環境レポート ===")
    print(f"全体ステータス: {report['overall_status']}")
    print(f"重要な失敗: {report['critical_failures']}件")

    if report['recommendations']:
        print("\n推奨事項:")
        for rec in report['recommendations']:
            print(f"  - {rec}")

    # Gemini実行準備確認
    ready, issues = validator.is_environment_ready_for_gemini()
    print(f"\nGemini実行準備: {'完了' if ready else '未完了'}")
    if issues:
        print("問題:")
        for issue in issues:
            print(f"  - {issue}")


if __name__ == "__main__":
    main()
