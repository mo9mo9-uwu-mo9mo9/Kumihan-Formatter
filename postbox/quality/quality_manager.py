#!/usr/bin/env python3
"""
統合品質管理システム
Claude ↔ Gemini協業での品質保証統一管理
"""

import os
import json
import datetime
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class QualityLevel(Enum):
    """品質レベル定義"""
    EXCELLENT = "excellent"     # 優秀（95%以上）
    GOOD = "good"              # 良好（80-94%）
    ACCEPTABLE = "acceptable"   # 許容（60-79%）
    POOR = "poor"              # 不良（40-59%）
    CRITICAL = "critical"       # 重大（40%未満）

class CheckType(Enum):
    """チェック種別"""
    SYNTAX = "syntax"           # 構文チェック
    TYPE_CHECK = "type_check"   # 型チェック
    LINT = "lint"              # リントチェック
    FORMAT = "format"          # フォーマットチェック
    SECURITY = "security"       # セキュリティチェック
    PERFORMANCE = "performance" # パフォーマンスチェック
    TEST = "test"              # テストチェック

@dataclass
class QualityMetrics:
    """品質メトリクス"""
    overall_score: float        # 総合スコア (0.0-1.0)
    syntax_score: float        # 構文品質
    type_score: float          # 型安全性
    lint_score: float          # コード品質
    format_score: float        # フォーマット品質
    security_score: float      # セキュリティ品質
    performance_score: float   # パフォーマンス品質
    test_coverage: float       # テストカバレッジ

    error_count: int           # エラー総数
    warning_count: int         # 警告総数
    fixed_count: int           # 修正済み数

    quality_level: QualityLevel
    improvement_suggestions: List[str]

@dataclass
class QualityResult:
    """品質チェック結果"""
    check_type: CheckType
    passed: bool
    score: float
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]
    execution_time: float

class QualityManager:
    """統合品質管理システム"""

    def __init__(self):
        self.standards_path = Path("postbox/quality/standards.json")
        self.results_path = Path("postbox/monitoring/quality_results.json")
        self.history_path = Path("postbox/monitoring/quality_history.json")

        # ディレクトリ作成
        for path in [self.standards_path, self.results_path, self.history_path]:
            path.parent.mkdir(parents=True, exist_ok=True)

        self.standards = self._load_standards()
        self.thresholds = self.standards.get("thresholds", {})

        print("🎯 QualityManager 初期化完了")

    def run_comprehensive_check(self, target_files: List[str],
                              ai_agent: str = "claude") -> QualityMetrics:
        """包括的品質チェック実行"""

        print(f"🔍 包括的品質チェック開始 ({ai_agent}) - 対象: {len(target_files)}ファイル")

        start_time = datetime.datetime.now()
        results = {}

        # 各種チェック実行
        for check_type in CheckType:
            print(f"  📋 {check_type.value} チェック実行中...")
            result = self._run_quality_check(check_type, target_files)
            results[check_type.value] = result

        # メトリクス計算
        metrics = self._calculate_metrics(results, target_files)

        # 結果保存
        execution_time = (datetime.datetime.now() - start_time).total_seconds()
        self._save_quality_result(metrics, ai_agent, execution_time, target_files)

        # 改善提案生成
        metrics.improvement_suggestions = self._generate_improvements(metrics, results)

        print(f"✅ 品質チェック完了: {metrics.quality_level.value} (スコア: {metrics.overall_score:.3f})")

        return metrics

    def _run_quality_check(self, check_type: CheckType, target_files: List[str]) -> QualityResult:
        """個別品質チェック実行"""

        start_time = datetime.datetime.now()

        try:
            if check_type == CheckType.SYNTAX:
                return self._check_syntax(target_files)
            elif check_type == CheckType.TYPE_CHECK:
                return self._check_types(target_files)
            elif check_type == CheckType.LINT:
                return self._check_lint(target_files)
            elif check_type == CheckType.FORMAT:
                return self._check_format(target_files)
            elif check_type == CheckType.SECURITY:
                return self._check_security(target_files)
            elif check_type == CheckType.PERFORMANCE:
                return self._check_performance(target_files)
            elif check_type == CheckType.TEST:
                return self._check_tests(target_files)
            else:
                raise ValueError(f"未対応のチェック種別: {check_type}")

        except Exception as e:
            execution_time = (datetime.datetime.now() - start_time).total_seconds()
            return QualityResult(
                check_type=check_type,
                passed=False,
                score=0.0,
                errors=[f"チェック実行エラー: {str(e)}"],
                warnings=[],
                details={"error": str(e)},
                execution_time=execution_time
            )

    def _check_syntax(self, target_files: List[str]) -> QualityResult:
        """構文チェック"""
        errors = []
        warnings = []
        total_files = len(target_files)
        passed_files = 0

        for file_path in target_files:
            try:
                result = subprocess.run(
                    ["python3", "-m", "py_compile", file_path],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    passed_files += 1
                else:
                    errors.append(f"{file_path}: {result.stderr.strip()}")

            except Exception as e:
                errors.append(f"{file_path}: 構文チェック実行エラー - {str(e)}")

        score = passed_files / total_files if total_files > 0 else 1.0

        return QualityResult(
            check_type=CheckType.SYNTAX,
            passed=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            details={"passed_files": passed_files, "total_files": total_files},
            execution_time=0.0
        )

    def _check_types(self, target_files: List[str]) -> QualityResult:
        """型チェック (mypy)"""
        errors = []
        warnings = []

        try:
            # まず個別ファイルをチェック
            for file_path in target_files:
                result = subprocess.run(
                    ["python3", "-m", "mypy", "--strict", file_path],
                    capture_output=True,
                    text=True
                )

                for line in result.stdout.split('\n'):
                    if 'error:' in line:
                        errors.append(line.strip())
                    elif 'warning:' in line or 'note:' in line:
                        warnings.append(line.strip())

            # スコア計算 (エラー率ベース)
            total_lines = sum(self._count_file_lines(f) for f in target_files if os.path.exists(f))
            error_rate = len(errors) / max(total_lines, 1) if total_lines > 0 else 1.0
            score = max(0.0, 1.0 - error_rate)

        except Exception as e:
            errors.append(f"mypy実行エラー: {str(e)}")
            score = 0.0

        return QualityResult(
            check_type=CheckType.TYPE_CHECK,
            passed=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            details={"total_lines": total_lines, "error_rate": error_rate},
            execution_time=0.0
        )

    def _check_lint(self, target_files: List[str]) -> QualityResult:
        """リントチェック (flake8)"""
        errors = []
        warnings = []

        try:
            for file_path in target_files:
                result = subprocess.run(
                    ["python3", "-m", "flake8", file_path],
                    capture_output=True,
                    text=True
                )

                for line in result.stdout.split('\n'):
                    if line.strip():
                        if any(code in line for code in ['E', 'F']):  # Error codes
                            errors.append(line.strip())
                        else:  # Warnings
                            warnings.append(line.strip())

            # スコア計算
            total_files = len(target_files)
            error_rate = len(errors) / max(total_files, 1)
            score = max(0.0, 1.0 - error_rate)

        except Exception as e:
            errors.append(f"flake8実行エラー: {str(e)}")
            score = 0.0

        return QualityResult(
            check_type=CheckType.LINT,
            passed=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            details={"error_rate": error_rate},
            execution_time=0.0
        )

    def _check_format(self, target_files: List[str]) -> QualityResult:
        """フォーマットチェック (black)"""
        errors = []
        warnings = []

        try:
            for file_path in target_files:
                result = subprocess.run(
                    ["python3", "-m", "black", "--check", file_path],
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    errors.append(f"{file_path}: フォーマット不適合")

            score = 1.0 - (len(errors) / max(len(target_files), 1))

        except Exception as e:
            errors.append(f"black実行エラー: {str(e)}")
            score = 0.0

        return QualityResult(
            check_type=CheckType.FORMAT,
            passed=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            details={},
            execution_time=0.0
        )

    def _check_security(self, target_files: List[str]) -> QualityResult:
        """セキュリティチェック (基本的なパターンマッチング)"""
        errors = []
        warnings = []

        # 危険なパターン
        dangerous_patterns = [
            r"eval\s*\(",
            r"exec\s*\(",
            r"subprocess\.call\s*\(",
            r"os\.system\s*\(",
            r"shell=True",
            r"password\s*=\s*[\"']",
            r"secret\s*=\s*[\"']",
            r"api_key\s*=\s*[\"']"
        ]

        import re

        for file_path in target_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for pattern in dangerous_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            warnings.append(f"{file_path}: 潜在的セキュリティリスク - {pattern}")

                except Exception as e:
                    errors.append(f"{file_path}: セキュリティチェックエラー - {str(e)}")

        # スコア計算
        total_issues = len(errors) + len(warnings)
        score = max(0.0, 1.0 - (total_issues / max(len(target_files), 1)))

        return QualityResult(
            check_type=CheckType.SECURITY,
            passed=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            details={"total_issues": total_issues},
            execution_time=0.0
        )

    def _check_performance(self, target_files: List[str]) -> QualityResult:
        """パフォーマンスチェック (基本的な最適化パターン)"""
        warnings = []
        errors = []

        performance_issues = [
            r"for\s+\w+\s+in\s+range\(len\(",  # range(len()) パターン
            r"\.append\s*\(\s*\)\s*\n.*for",   # 非効率なループ
            r"time\.sleep\s*\(\s*[0-9]+\s*\)"  # 長いsleep
        ]

        import re

        for file_path in target_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for pattern in performance_issues:
                        if re.search(pattern, content):
                            warnings.append(f"{file_path}: パフォーマンス改善可能 - {pattern}")

                except Exception as e:
                    errors.append(f"{file_path}: パフォーマンスチェックエラー - {str(e)}")

        score = max(0.0, 1.0 - (len(warnings) / max(len(target_files), 1)))

        return QualityResult(
            check_type=CheckType.PERFORMANCE,
            passed=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            details={},
            execution_time=0.0
        )

    def _check_tests(self, target_files: List[str]) -> QualityResult:
        """テストチェック"""
        errors = []
        warnings = []

        # テストファイル存在チェック
        test_files = []
        source_files = []

        for file_path in target_files:
            if 'test' in file_path.lower():
                test_files.append(file_path)
            else:
                source_files.append(file_path)

        # テストカバレッジ計算
        coverage_ratio = len(test_files) / max(len(source_files), 1) if source_files else 1.0

        if coverage_ratio < 0.3:
            warnings.append(f"テストカバレッジ不足: {coverage_ratio:.1%}")

        score = min(1.0, coverage_ratio)

        return QualityResult(
            check_type=CheckType.TEST,
            passed=coverage_ratio >= 0.5,
            score=score,
            errors=errors,
            warnings=warnings,
            details={"coverage_ratio": coverage_ratio, "test_files": len(test_files)},
            execution_time=0.0
        )

    def _calculate_metrics(self, results: Dict[str, QualityResult],
                          target_files: List[str]) -> QualityMetrics:
        """品質メトリクス計算"""

        # 各種スコア集計
        scores = {}
        total_errors = 0
        total_warnings = 0

        for check_type, result in results.items():
            scores[check_type] = result.score
            total_errors += len(result.errors)
            total_warnings += len(result.warnings)

        # 総合スコア計算 (重み付き平均)
        weights = {
            "syntax": 0.2,
            "type_check": 0.25,
            "lint": 0.2,
            "format": 0.1,
            "security": 0.15,
            "performance": 0.05,
            "test": 0.05
        }

        overall_score = sum(scores.get(k, 0) * w for k, w in weights.items())

        # 品質レベル決定
        if overall_score >= 0.95:
            quality_level = QualityLevel.EXCELLENT
        elif overall_score >= 0.80:
            quality_level = QualityLevel.GOOD
        elif overall_score >= 0.60:
            quality_level = QualityLevel.ACCEPTABLE
        elif overall_score >= 0.40:
            quality_level = QualityLevel.POOR
        else:
            quality_level = QualityLevel.CRITICAL

        return QualityMetrics(
            overall_score=overall_score,
            syntax_score=scores.get("syntax", 0),
            type_score=scores.get("type_check", 0),
            lint_score=scores.get("lint", 0),
            format_score=scores.get("format", 0),
            security_score=scores.get("security", 0),
            performance_score=scores.get("performance", 0),
            test_coverage=scores.get("test", 0),
            error_count=total_errors,
            warning_count=total_warnings,
            fixed_count=0,  # 修正システムと連携時に更新
            quality_level=quality_level,
            improvement_suggestions=[]
        )

    def _generate_improvements(self, metrics: QualityMetrics,
                             results: Dict[str, QualityResult]) -> List[str]:
        """改善提案生成"""

        suggestions = []

        # スコア別改善提案
        if metrics.syntax_score < 0.8:
            suggestions.append("🔧 構文エラーの修正が必要です")

        if metrics.type_score < 0.7:
            suggestions.append("📝 型注釈の追加・修正を推奨します")

        if metrics.lint_score < 0.8:
            suggestions.append("🎯 コード品質の改善が必要です (flake8)")

        if metrics.format_score < 0.9:
            suggestions.append("💅 コードフォーマットの統一が必要です (black)")

        if metrics.security_score < 0.9:
            suggestions.append("🔒 セキュリティリスクの確認・修正を推奨します")

        if metrics.performance_score < 0.8:
            suggestions.append("⚡ パフォーマンス最適化を検討してください")

        if metrics.test_coverage < 0.5:
            suggestions.append("🧪 テストカバレッジの向上が必要です")

        # 総合的な提案
        if metrics.overall_score < 0.6:
            suggestions.append("🚨 総合品質が基準を下回っています。優先的な改善が必要です")

        return suggestions

    def _save_quality_result(self, metrics: QualityMetrics, ai_agent: str,
                           execution_time: float, target_files: List[str]) -> None:
        """品質結果保存"""

        result_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "ai_agent": ai_agent,
            "execution_time": execution_time,
            "target_files": target_files,
            "metrics": {
                "overall_score": metrics.overall_score,
                "quality_level": metrics.quality_level.value,
                "error_count": metrics.error_count,
                "warning_count": metrics.warning_count,
                "scores": {
                    "syntax": metrics.syntax_score,
                    "type_check": metrics.type_score,
                    "lint": metrics.lint_score,
                    "format": metrics.format_score,
                    "security": metrics.security_score,
                    "performance": metrics.performance_score,
                    "test": metrics.test_coverage
                }
            }
        }

        # 履歴更新
        history = []
        if self.history_path.exists():
            try:
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = []

        history.append(result_entry)

        # 履歴サイズ制限
        if len(history) > 50:
            history = history[-50:]

        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def _count_file_lines(self, file_path: str) -> int:
        """ファイル行数カウント"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except:
            return 0

    def _load_standards(self) -> Dict[str, Any]:
        """品質基準読み込み"""

        default_standards = {
            "thresholds": {
                "minimum_overall_score": 0.7,
                "minimum_type_score": 0.8,
                "minimum_lint_score": 0.8,
                "maximum_error_count": 10,
                "minimum_test_coverage": 0.5
            },
            "weights": {
                "syntax": 0.2,
                "type_check": 0.25,
                "lint": 0.2,
                "format": 0.1,
                "security": 0.15,
                "performance": 0.05,
                "test": 0.05
            },
            "automation": {
                "auto_fix_format": True,
                "auto_fix_simple_types": True,
                "auto_fix_imports": True
            }
        }

        if self.standards_path.exists():
            try:
                with open(self.standards_path, 'r', encoding='utf-8') as f:
                    user_standards = json.load(f)
                default_standards.update(user_standards)
            except:
                pass
        else:
            # デフォルト設定保存
            with open(self.standards_path, 'w', encoding='utf-8') as f:
                json.dump(default_standards, f, indent=2, ensure_ascii=False)

        return default_standards

    def get_quality_report(self) -> Dict[str, Any]:
        """品質レポート生成"""

        if not self.history_path.exists():
            return {"error": "品質履歴データなし"}

        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)

            if not history:
                return {"error": "品質履歴データなし"}

            # 統計計算
            recent_results = history[-10:]  # 最新10件

            avg_overall = sum(r["metrics"]["overall_score"] for r in recent_results) / len(recent_results)
            avg_errors = sum(r["metrics"]["error_count"] for r in recent_results) / len(recent_results)

            quality_trend = []
            if len(history) >= 5:
                for i in range(len(history) - 4):
                    batch = history[i:i+5]
                    batch_avg = sum(r["metrics"]["overall_score"] for r in batch) / 5
                    quality_trend.append(batch_avg)

            return {
                "current_quality": {
                    "overall_score": recent_results[-1]["metrics"]["overall_score"],
                    "quality_level": recent_results[-1]["metrics"]["quality_level"],
                    "error_count": recent_results[-1]["metrics"]["error_count"]
                },
                "trends": {
                    "average_overall_score": avg_overall,
                    "average_error_count": avg_errors,
                    "quality_trend": quality_trend
                },
                "recommendations": self._generate_recommendations(recent_results),
                "total_checks": len(history)
            }

        except Exception as e:
            return {"error": f"レポート生成エラー: {str(e)}"}

    def _generate_recommendations(self, recent_results: List[Dict]) -> List[str]:
        """改善推奨事項生成"""

        recommendations = []

        # 傾向分析
        if len(recent_results) >= 3:
            scores = [r["metrics"]["overall_score"] for r in recent_results[-3:]]
            if all(scores[i] > scores[i+1] for i in range(len(scores)-1)):
                recommendations.append("📉 品質スコアが低下傾向にあります。改善が必要です")
            elif all(scores[i] < scores[i+1] for i in range(len(scores)-1)):
                recommendations.append("📈 品質スコアが向上しています。引き続き維持してください")

        # エラー率分析
        recent_errors = [r["metrics"]["error_count"] for r in recent_results]
        avg_errors = sum(recent_errors) / len(recent_errors)

        if avg_errors > 20:
            recommendations.append("🚨 エラー数が多すぎます。基本的な品質チェックを強化してください")
        elif avg_errors > 10:
            recommendations.append("⚠️ エラー数がやや多めです。定期的な品質チェックを推奨します")

        return recommendations

def main():
    """テスト実行"""
    qm = QualityManager()

    test_files = [
        "kumihan_formatter/core/utilities/logger.py",
        "kumihan_formatter/config/base_config.py"
    ]

    metrics = qm.run_comprehensive_check(test_files, "claude")

    print(f"\n📊 品質チェック結果:")
    print(f"総合スコア: {metrics.overall_score:.3f}")
    print(f"品質レベル: {metrics.quality_level.value}")
    print(f"エラー数: {metrics.error_count}")
    print(f"警告数: {metrics.warning_count}")

    if metrics.improvement_suggestions:
        print(f"\n💡 改善提案:")
        for suggestion in metrics.improvement_suggestions:
            print(f"  {suggestion}")

if __name__ == "__main__":
    main()
