#!/usr/bin/env python3
"""段階的品質基準システム

Geminiの成果物を段階的な品質基準で検証し、徐々にstrict modeに近づけるシステム。
一気にMyPy strict modeで検証せず、段階的に品質を向上させることで成功率を改善する。

品質レベル:
- Basic: 基本的な構文チェック・実行可能性
- Intermediate: 中程度の型注釈・lint対応
- Strict: MyPy strict mode完全対応

Created: 2025-08-15 (Issue #823 Gemini失敗対策)
"""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """品質レベル"""
    BASIC = "basic"              # 基本レベル（構文・実行可能性）
    INTERMEDIATE = "intermediate"  # 中間レベル（型注釈・lint）
    STRICT = "strict"            # 厳格レベル（MyPy strict mode）


class ValidationResult(Enum):
    """検証結果"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class QualityConfig:
    """品質設定"""
    level: QualityLevel
    description: str
    mypy_flags: List[str]
    flake8_flags: List[str]
    required_for_production: bool
    auto_promote_threshold: float  # 次レベルへの自動昇格閾値


@dataclass
class ValidationReport:
    """検証レポート"""
    level: QualityLevel
    result: ValidationResult
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]
    suggestions: List[str]
    next_level_ready: bool


class QualityStandardsSystem:
    """段階的品質基準システム"""

    def __init__(self, reports_dir: Optional[Path] = None) -> None:
        """
        初期化処理

        Args:
            reports_dir: レポートディレクトリ
        """
        self.reports_dir = reports_dir or Path(__file__).parent
        self.quality_configs = self._create_quality_configs()
        self.validation_history_path = self.reports_dir / "quality_validation_history.json"
        self.validation_history = self._load_validation_history()

    def _create_quality_configs(self) -> Dict[QualityLevel, QualityConfig]:
        """品質設定を作成"""
        return {
            QualityLevel.BASIC: QualityConfig(
                level=QualityLevel.BASIC,
                description="基本品質レベル - 構文・実行可能性重視",
                mypy_flags=[
                    "--ignore-missing-imports",
                    "--allow-untyped-defs",
                    "--allow-untyped-calls",
                    "--allow-incomplete-defs",
                    "--allow-any-generics",
                    "--no-warn-return-any",
                    "--disable-error-code=import-untyped"
                ],
                flake8_flags=[
                    "--max-line-length=120",
                    "--ignore=E501,W503,F401",  # 長い行、改行位置、未使用import許可
                    "--max-complexity=20"
                ],
                required_for_production=False,
                auto_promote_threshold=0.8
            ),

            QualityLevel.INTERMEDIATE: QualityConfig(
                level=QualityLevel.INTERMEDIATE,
                description="中間品質レベル - 型注釈・lint対応",
                mypy_flags=[
                    "--ignore-missing-imports",
                    "--allow-untyped-calls",
                    "--allow-any-generics",
                    "--warn-unused-ignores",
                    "--disable-error-code=import-untyped,operator"
                ],
                flake8_flags=[
                    "--max-line-length=100",
                    "--ignore=E501,F401",  # 長い行、未使用import許可
                    "--max-complexity=15"
                ],
                required_for_production=False,
                auto_promote_threshold=0.9
            ),

            QualityLevel.STRICT: QualityConfig(
                level=QualityLevel.STRICT,
                description="厳格品質レベル - MyPy strict mode完全対応",
                mypy_flags=[
                    "--strict",
                    "--warn-unreachable",
                    "--warn-redundant-casts"
                ],
                flake8_flags=[
                    "--max-line-length=88",
                    "--max-complexity=10"
                ],
                required_for_production=True,
                auto_promote_threshold=1.0
            )
        }

    def _load_validation_history(self) -> List[Dict[str, Any]]:
        """検証履歴を読み込み"""
        if not self.validation_history_path.exists():
            return []

        try:
            with open(self.validation_history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    return []
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"検証履歴の読み込みに失敗: {e}")
            return []

    def _save_validation_history(self) -> None:
        """検証履歴を保存"""
        try:
            with open(self.validation_history_path, "w", encoding="utf-8") as f:
                json.dump(self.validation_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"検証履歴の保存に失敗: {e}")

    def determine_appropriate_level(self, task_description: str,
                                  estimated_complexity: float = 0.5) -> QualityLevel:
        """
        タスクに適した品質レベルを判定

        Args:
            task_description: タスク説明
            estimated_complexity: 推定複雑度 (0.0-1.0)

        Returns:
            適切な品質レベル
        """
        task_lower = task_description.lower()

        # 高複雑度タスクは中間レベルから開始
        if estimated_complexity > 0.8:
            return QualityLevel.INTERMEDIATE

        # 型注釈関連タスクは基本レベルから開始
        type_annotation_keywords = [
            "型注釈", "type annotation", "mypy", "no-untyped-def"
        ]
        if any(keyword in task_lower for keyword in type_annotation_keywords):
            return QualityLevel.BASIC

        # 外部ライブラリ関連は基本レベル
        external_lib_keywords = [
            "pandas", "plotly", "numpy", "requests", "library stubs"
        ]
        if any(keyword in task_lower for keyword in external_lib_keywords):
            return QualityLevel.BASIC

        # 単純な修正は中間レベル
        simple_keywords = [
            "lint", "format", "black", "isort", "flake8"
        ]
        if any(keyword in task_lower for keyword in simple_keywords):
            return QualityLevel.INTERMEDIATE

        # デフォルトは基本レベル
        return QualityLevel.BASIC

    def validate_with_mypy(self, file_paths: List[str],
                          quality_level: QualityLevel) -> Tuple[ValidationResult, List[str]]:
        """
        MyPy検証を実行

        Args:
            file_paths: 検証対象ファイルパス
            quality_level: 品質レベル

        Returns:
            (検証結果, エラーメッセージリスト)
        """
        config = self.quality_configs[quality_level]

        try:
            # MyPy実行
            cmd = ["python3", "-m", "mypy"] + config.mypy_flags + file_paths
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                return ValidationResult.PASS, []
            else:
                errors = result.stdout.strip().split('\n') if result.stdout.strip() else []

                # エラー数に基づいて判定
                if len(errors) <= 3:  # 軽微なエラー
                    return ValidationResult.WARNING, errors
                else:
                    return ValidationResult.FAIL, errors

        except subprocess.TimeoutExpired:
            return ValidationResult.FAIL, ["MyPy実行タイムアウト"]
        except Exception as e:
            return ValidationResult.FAIL, [f"MyPy実行エラー: {e}"]

    def validate_with_flake8(self, file_paths: List[str],
                           quality_level: QualityLevel) -> Tuple[ValidationResult, List[str]]:
        """
        Flake8検証を実行

        Args:
            file_paths: 検証対象ファイルパス
            quality_level: 品質レベル

        Returns:
            (検証結果, エラーメッセージリスト)
        """
        config = self.quality_configs[quality_level]

        try:
            # Flake8実行
            cmd = ["python3", "-m", "flake8"] + config.flake8_flags + file_paths
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                return ValidationResult.PASS, []
            else:
                errors = result.stdout.strip().split('\n') if result.stdout.strip() else []

                # エラー数に基づいて判定
                if len(errors) <= 5:  # 軽微なエラー
                    return ValidationResult.WARNING, errors
                else:
                    return ValidationResult.FAIL, errors

        except subprocess.TimeoutExpired:
            return ValidationResult.FAIL, ["Flake8実行タイムアウト"]
        except Exception as e:
            return ValidationResult.FAIL, [f"Flake8実行エラー: {e}"]

    def validate_syntax(self, file_paths: List[str]) -> Tuple[ValidationResult, List[str]]:
        """
        構文検証を実行

        Args:
            file_paths: 検証対象ファイルパス

        Returns:
            (検証結果, エラーメッセージリスト)
        """
        errors = []

        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source_code = f.read()

                # 構文チェック
                compile(source_code, file_path, "exec")

            except SyntaxError as e:
                errors.append(f"{file_path}:{e.lineno}: {e.msg}")
            except Exception as e:
                errors.append(f"{file_path}: 読み込みエラー - {e}")

        if errors:
            return ValidationResult.FAIL, errors
        else:
            return ValidationResult.PASS, []

    def comprehensive_validation(self, file_paths: List[str],
                               quality_level: QualityLevel,
                               task_id: str = "") -> ValidationReport:
        """
        包括的品質検証を実行

        Args:
            file_paths: 検証対象ファイルパス
            quality_level: 品質レベル
            task_id: タスクID

        Returns:
            検証レポート
        """
        errors: List[str] = []
        warnings: List[str] = []
        overall_result = ValidationResult.PASS

        # 1. 構文検証
        syntax_result, syntax_errors = self.validate_syntax(file_paths)
        if syntax_result == ValidationResult.FAIL:
            errors.extend(syntax_errors)
            overall_result = ValidationResult.FAIL

        # 構文エラーがある場合は以降の検証をスキップ
        if syntax_result == ValidationResult.FAIL:
            return ValidationReport(
                level=quality_level,
                result=ValidationResult.FAIL,
                errors=errors,
                warnings=warnings,
                metrics={"syntax_errors": len(syntax_errors)},
                suggestions=["構文エラーを修正してください"],
                next_level_ready=False
            )

        # 2. Flake8検証
        flake8_result, flake8_errors = self.validate_with_flake8(file_paths, quality_level)
        if flake8_result == ValidationResult.FAIL:
            errors.extend(flake8_errors)
            overall_result = ValidationResult.FAIL
        elif flake8_result == ValidationResult.WARNING:
            warnings.extend(flake8_errors)
            if overall_result == ValidationResult.PASS:
                overall_result = ValidationResult.WARNING

        # 3. MyPy検証
        mypy_result, mypy_errors = self.validate_with_mypy(file_paths, quality_level)
        if mypy_result == ValidationResult.FAIL:
            errors.extend(mypy_errors)
            overall_result = ValidationResult.FAIL
        elif mypy_result == ValidationResult.WARNING:
            warnings.extend(mypy_errors)
            if overall_result == ValidationResult.PASS:
                overall_result = ValidationResult.WARNING

        # メトリクス計算
        metrics = {
            "total_files": len(file_paths),
            "syntax_errors": 0,  # 構文エラー時は既に早期リターンするため常に0
            "flake8_issues": len(flake8_errors),
            "mypy_issues": len(mypy_errors),
            "total_issues": len(errors) + len(warnings)
        }

        # 改善提案生成
        suggestions = self._generate_suggestions(quality_level, errors, warnings)

        # 次レベル準備状況判定
        next_level_ready = (
            overall_result == ValidationResult.PASS and
            len(warnings) <= 2  # 軽微な警告のみ
        )

        # 検証履歴に記録
        history_entry = {
            "timestamp": f"{__import__('datetime').datetime.now().isoformat()}",
            "task_id": task_id,
            "quality_level": quality_level.value,
            "result": overall_result.value,
            "metrics": metrics,
            "next_level_ready": next_level_ready
        }
        self.validation_history.append(history_entry)
        self._save_validation_history()

        return ValidationReport(
            level=quality_level,
            result=overall_result,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            suggestions=suggestions,
            next_level_ready=next_level_ready
        )

    def _generate_suggestions(self, quality_level: QualityLevel,
                            errors: List[str], warnings: List[str]) -> List[str]:
        """
        改善提案を生成

        Args:
            quality_level: 品質レベル
            errors: エラーリスト
            warnings: 警告リスト

        Returns:
            改善提案リスト
        """
        suggestions = []

        all_issues = errors + warnings

        # MyPy関連の提案
        mypy_issues = [issue for issue in all_issues if "mypy" in issue.lower() or "type" in issue.lower()]
        if mypy_issues:
            suggestions.append("型注釈を追加・修正してください")
            if quality_level == QualityLevel.BASIC:
                suggestions.append("基本レベルから開始し、段階的に型注釈を完善してください")

        # Flake8関連の提案
        flake8_issues = [issue for issue in all_issues if any(code in issue for code in ["E", "F", "W"])]
        if flake8_issues:
            suggestions.append("コードスタイル・lint問題を修正してください")
            suggestions.append("python3 -m black <ファイル> でフォーマットを自動修正できます")

        # import関連の提案
        import_issues = [issue for issue in all_issues if "import" in issue.lower()]
        if import_issues:
            suggestions.append("未使用importを削除、不足importを追加してください")
            suggestions.append("python3 -m isort <ファイル> でimport順序を修正できます")

        # 複雑度関連の提案
        complexity_issues = [issue for issue in all_issues if "complex" in issue.lower()]
        if complexity_issues:
            suggestions.append("関数・メソッドを小さく分割して複雑度を下げてください")

        # レベル別の提案
        if quality_level == QualityLevel.BASIC:
            suggestions.append("基本レベル通過後、中間レベルに進んでください")
        elif quality_level == QualityLevel.INTERMEDIATE:
            suggestions.append("中間レベル通過後、厳格レベル（production ready）に進んでください")

        return suggestions

    def get_next_quality_level(self, current_level: QualityLevel) -> Optional[QualityLevel]:
        """
        次の品質レベルを取得

        Args:
            current_level: 現在の品質レベル

        Returns:
            次の品質レベル
        """
        level_order = [QualityLevel.BASIC, QualityLevel.INTERMEDIATE, QualityLevel.STRICT]

        try:
            current_index = level_order.index(current_level)
            if current_index < len(level_order) - 1:
                return level_order[current_index + 1]
        except ValueError:
            pass

        return None

    def should_auto_promote(self, task_id: str, current_level: QualityLevel) -> bool:
        """
        自動昇格すべきかを判定

        Args:
            task_id: タスクID
            current_level: 現在の品質レベル

        Returns:
            自動昇格すべきか
        """
        config = self.quality_configs[current_level]

        # 最近の検証履歴を確認
        recent_validations = [
            entry for entry in self.validation_history[-10:]  # 最近10件
            if entry.get("quality_level") == current_level.value
        ]

        if len(recent_validations) < 3:  # 最低3回の検証が必要
            return False

        # 成功率計算
        success_count = sum(
            1 for entry in recent_validations
            if entry.get("result") == "pass" and entry.get("next_level_ready", False)
        )

        success_rate = success_count / len(recent_validations)

        return success_rate >= config.auto_promote_threshold

    def generate_quality_report(self) -> Dict[str, Any]:
        """
        品質レポートを生成

        Returns:
            品質レポート
        """
        # 最近の検証統計
        recent_validations = self.validation_history[-50:]  # 最近50件

        level_stats = {}
        for level in QualityLevel:
            level_validations = [
                v for v in recent_validations
                if v.get("quality_level") == level.value
            ]

            if level_validations:
                pass_count = sum(1 for v in level_validations if v.get("result") == "pass")
                success_rate = pass_count / len(level_validations)

                level_stats[level.value] = {
                    "total_validations": len(level_validations),
                    "pass_count": pass_count,
                    "success_rate": success_rate,
                    "avg_issues": sum(v.get("metrics", {}).get("total_issues", 0) for v in level_validations) / len(level_validations)
                }
            else:
                level_stats[level.value] = {
                    "total_validations": 0,
                    "pass_count": 0,
                    "success_rate": 0.0,
                    "avg_issues": 0.0
                }

        report = {
            "report_generated": f"{__import__('datetime').datetime.now().isoformat()}",
            "total_validations": len(recent_validations),
            "level_statistics": level_stats,
            "recommendations": self._generate_quality_recommendations(level_stats)
        }

        return report

    def _generate_quality_recommendations(self, level_stats: Dict[str, Any]) -> List[str]:
        """品質改善推奨事項を生成"""
        recommendations = []

        # 各レベルの成功率をチェック
        for level_name, stats in level_stats.items():
            success_rate = stats["success_rate"]

            if success_rate < 0.5:
                recommendations.append(
                    f"{level_name}レベルの成功率が低い({success_rate:.1%}) - "
                    f"品質基準の見直しまたは指示の改善が必要"
                )
            elif success_rate > 0.8:
                recommendations.append(
                    f"{level_name}レベルの成功率が高い({success_rate:.1%}) - "
                    f"より高い品質レベルへの挑戦を推奨"
                )

        # 全体的な推奨
        basic_success = level_stats.get("basic", {}).get("success_rate", 0)
        if basic_success < 0.7:
            recommendations.append("基本レベルでの成功率向上が優先課題です")

        return recommendations


def main() -> None:
    """メイン処理（テスト用）"""
    logging.basicConfig(level=logging.INFO)

    system = QualityStandardsSystem()

    # テスト用ファイル作成
    test_file = Path("test_quality.py")
    test_content = '''
def hello_world():
    print("Hello, World!")
    return "success"

def add_numbers(a, b):
    return a + b
'''

    try:
        with open(test_file, "w") as f:
            f.write(test_content)

        # 各品質レベルでの検証テスト
        for level in QualityLevel:
            print(f"\n=== {level.value}レベル検証 ===")
            report = system.comprehensive_validation([str(test_file)], level, f"test_{level.value}")

            print(f"結果: {report.result.value}")
            print(f"エラー数: {len(report.errors)}")
            print(f"警告数: {len(report.warnings)}")
            print(f"次レベル準備: {report.next_level_ready}")

            if report.suggestions:
                print("提案:")
                for suggestion in report.suggestions:
                    print(f"  - {suggestion}")

    finally:
        # テストファイル削除
        if test_file.exists():
            test_file.unlink()

    # 品質レポート生成
    quality_report = system.generate_quality_report()
    print("\n=== 品質レポート ===")
    print(json.dumps(quality_report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
