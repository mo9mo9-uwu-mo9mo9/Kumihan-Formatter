#!/usr/bin/env python3
"""
品質監視システム - Issue #598 Phase 3-3

リアルタイム品質ダッシュボード・技術的負債管理システム
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QualityAlert:
    """品質アラート"""

    severity: str  # "low", "medium", "high", "critical"
    component: str
    message: str
    timestamp: datetime
    metric_value: float
    threshold: float


@dataclass
class QualityTrend:
    """品質トレンド"""

    metric_name: str
    values: List[Tuple[datetime, float]] = field(default_factory=list)
    trend_direction: str = "stable"  # "improving", "degrading", "stable"

    def add_measurement(self, value: float, timestamp: Optional[datetime] = None):
        """測定値を追加"""
        if timestamp is None:
            timestamp = datetime.now()
        self.values.append((timestamp, value))

        # 古いデータを削除（30日間保持）
        cutoff = timestamp - timedelta(days=30)
        self.values = [(t, v) for t, v in self.values if t > cutoff]

        # トレンド方向を更新
        self._update_trend()

    def _update_trend(self):
        """トレンド方向を更新"""
        if len(self.values) < 3:
            self.trend_direction = "stable"
            return

        recent_values = [v for _, v in self.values[-5:]]
        if len(recent_values) < 3:
            return

        # 線形回帰による傾向分析（簡易版）
        n = len(recent_values)
        x_sum = sum(range(n))
        y_sum = sum(recent_values)
        xy_sum = sum(i * v for i, v in enumerate(recent_values))
        x_sq_sum = sum(i * i for i in range(n))

        denominator = n * x_sq_sum - x_sum * x_sum
        if denominator == 0:
            self.trend_direction = "stable"
            return

        slope = (n * xy_sum - x_sum * y_sum) / denominator

        if slope > 0.1:
            self.trend_direction = "improving"
        elif slope < -0.1:
            self.trend_direction = "degrading"
        else:
            self.trend_direction = "stable"


@dataclass
class TechnicalDebtItem:
    """技術的負債項目"""

    file_path: str
    debt_type: str  # "complexity", "duplication", "test_coverage", "documentation"
    severity: str
    description: str
    estimated_hours: float
    priority: int
    created_date: datetime
    resolved: bool = False


class QualityMonitoringDashboard:
    """品質監視ダッシュボード"""

    def __init__(self, project_root: Path):
        """初期化

        Args:
            project_root: プロジェクトルートディレクトリ
        """
        self.project_root = project_root
        self.data_dir = project_root / ".quality_monitoring"
        self.data_dir.mkdir(exist_ok=True)

        self.alerts: List[QualityAlert] = []
        self.trends: Dict[str, QualityTrend] = {}
        self.technical_debt: List[TechnicalDebtItem] = []

        self._load_historical_data()

    def _load_historical_data(self):
        """履歴データを読み込み"""
        try:
            trends_file = self.data_dir / "quality_trends.json"
            if trends_file.exists():
                with open(trends_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for name, trend_data in data.items():
                        trend = QualityTrend(metric_name=name)
                        for timestamp_str, value in trend_data["values"]:
                            timestamp = datetime.fromisoformat(timestamp_str)
                            trend.values.append((timestamp, value))
                        trend.trend_direction = trend_data.get(
                            "trend_direction", "stable"
                        )
                        self.trends[name] = trend

            debt_file = self.data_dir / "technical_debt.json"
            if debt_file.exists():
                with open(debt_file, encoding="utf-8") as f:
                    debt_data = json.load(f)
                    for item_data in debt_data:
                        item = TechnicalDebtItem(
                            file_path=item_data["file_path"],
                            debt_type=item_data["debt_type"],
                            severity=item_data["severity"],
                            description=item_data["description"],
                            estimated_hours=item_data["estimated_hours"],
                            priority=item_data["priority"],
                            created_date=datetime.fromisoformat(
                                item_data["created_date"]
                            ),
                            resolved=item_data.get("resolved", False),
                        )
                        self.technical_debt.append(item)

        except Exception as e:
            logger.warning(f"履歴データ読み込みエラー: {e}")

    def _save_data(self):
        """データを保存"""
        try:
            # トレンドデータ保存
            trends_data = {}
            for name, trend in self.trends.items():
                trends_data[name] = {
                    "values": [(t.isoformat(), v) for t, v in trend.values],
                    "trend_direction": trend.trend_direction,
                }

            trends_file = self.data_dir / "quality_trends.json"
            with open(trends_file, "w", encoding="utf-8") as f:
                json.dump(trends_data, f, indent=2, ensure_ascii=False)

            # 技術的負債データ保存
            debt_data = []
            for item in self.technical_debt:
                debt_data.append(
                    {
                        "file_path": item.file_path,
                        "debt_type": item.debt_type,
                        "severity": item.severity,
                        "description": item.description,
                        "estimated_hours": item.estimated_hours,
                        "priority": item.priority,
                        "created_date": item.created_date.isoformat(),
                        "resolved": item.resolved,
                    }
                )

            debt_file = self.data_dir / "technical_debt.json"
            with open(debt_file, "w", encoding="utf-8") as f:
                json.dump(debt_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"データ保存エラー: {e}")

    def collect_quality_metrics(self) -> Dict[str, float]:
        """品質メトリクスを収集"""
        logger.info("📊 品質メトリクス収集中...")

        metrics = {}

        try:
            # テストカバレッジ
            coverage = self._get_test_coverage()
            metrics["test_coverage"] = coverage

            # コード品質（flake8スコア）
            code_quality = self._get_code_quality_score()
            metrics["code_quality"] = code_quality

            # 複雑度メトリクス
            complexity = self._get_complexity_metrics()
            metrics.update(complexity)

            # パフォーマンスメトリクス
            performance = self._get_performance_metrics()
            metrics.update(performance)

            # 技術的負債スコア
            debt_score = self._calculate_technical_debt_score()
            metrics["technical_debt_score"] = debt_score

            # メトリクスをトレンドに追加
            now = datetime.now()
            for name, value in metrics.items():
                if name not in self.trends:
                    self.trends[name] = QualityTrend(metric_name=name)
                self.trends[name].add_measurement(value, now)

            # アラート検査
            self._check_quality_alerts(metrics)

        except Exception as e:
            logger.error(f"メトリクス収集エラー: {e}")

        return metrics

    def _get_test_coverage(self) -> float:
        """テストカバレッジを取得"""
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--cov=kumihan_formatter",
                    "--cov-report=json",
                    "tests/",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, encoding="utf-8") as f:
                    coverage_data = json.load(f)
                return coverage_data.get("totals", {}).get("percent_covered", 0.0)

        except Exception:
            pass

        return 0.0

    def _get_code_quality_score(self) -> float:
        """コード品質スコアを取得"""
        try:
            # flake8によるコード品質チェック
            result = subprocess.run(
                [sys.executable, "-m", "flake8", "kumihan_formatter/", "--count"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            # エラー数からスコアを計算
            if result.stdout.strip():
                error_count = int(result.stdout.strip().split("\n")[-1])
                # ファイル数を概算（実際の実装では正確に計算）
                estimated_files = 100
                error_rate = error_count / estimated_files
                score = max(0, 100 - (error_rate * 10))
                return score

            return 100.0  # エラーなし

        except Exception:
            return 0.0

    def _get_complexity_metrics(self) -> Dict[str, float]:
        """複雑度メトリクスを取得"""
        try:
            # 簡易的な複雑度計算
            # 実際の実装では radon などを使用
            python_files = list(self.project_root.glob("kumihan_formatter/**/*.py"))

            total_lines = 0
            total_functions = 0

            for file_path in python_files:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    lines = content.split("\n")
                    total_lines += len([line for line in lines if line.strip()])
                    total_functions += content.count("def ")
                except Exception:
                    continue

            avg_function_length = total_lines / max(total_functions, 1)
            complexity_score = max(0, 100 - (avg_function_length - 10) * 2)

            return {
                "average_function_length": avg_function_length,
                "complexity_score": complexity_score,
            }

        except Exception:
            return {"complexity_score": 0.0}

    def _get_performance_metrics(self) -> Dict[str, float]:
        """パフォーマンスメトリクスを取得"""
        # 簡易的なパフォーマンス測定
        # 実際の実装ではより詳細なベンチマークを実行
        return {
            "performance_score": 85.0,  # 仮の値
            "memory_efficiency": 90.0,  # 仮の値
        }

    def _calculate_technical_debt_score(self) -> float:
        """技術的負債スコアを計算"""
        if not self.technical_debt:
            return 100.0

        # 未解決の負債項目の重み付きスコア
        total_weight = 0
        unresolved_weight = 0

        severity_weights = {"low": 1, "medium": 3, "high": 5, "critical": 10}

        for item in self.technical_debt:
            weight = severity_weights.get(item.severity, 1)
            total_weight += weight
            if not item.resolved:
                unresolved_weight += weight

        if total_weight == 0:
            return 100.0

        debt_ratio = unresolved_weight / total_weight
        return max(0, 100 - (debt_ratio * 100))

    def _check_quality_alerts(self, metrics: Dict[str, float]):
        """品質アラートをチェック"""
        now = datetime.now()

        # アラート閾値設定
        alert_thresholds = {
            "test_coverage": {"critical": 50, "high": 70, "medium": 80},
            "code_quality": {"critical": 60, "high": 75, "medium": 85},
            "complexity_score": {"critical": 50, "high": 70, "medium": 80},
            "technical_debt_score": {"critical": 40, "high": 60, "medium": 75},
        }

        for metric_name, value in metrics.items():
            if metric_name in alert_thresholds:
                thresholds = alert_thresholds[metric_name]

                severity = None
                threshold = None

                if value < thresholds["critical"]:
                    severity = "critical"
                    threshold = thresholds["critical"]
                elif value < thresholds["high"]:
                    severity = "high"
                    threshold = thresholds["high"]
                elif value < thresholds["medium"]:
                    severity = "medium"
                    threshold = thresholds["medium"]

                if severity:
                    # 重複アラート防止: 同じコンポーネントの最新アラートから1時間以内なら追加しない
                    recent_alerts = [
                        a
                        for a in self.alerts
                        if a.component == metric_name
                        and (now - a.timestamp).total_seconds() < 3600
                    ]

                    if not recent_alerts:
                        alert = QualityAlert(
                            severity=severity,
                            component=metric_name,
                            message=f"{metric_name}が閾値を下回りました: {value:.1f} < {threshold}",
                            timestamp=now,
                            metric_value=value,
                            threshold=threshold,
                        )
                        self.alerts.append(alert)

    def scan_technical_debt(self):
        """技術的負債をスキャン"""
        logger.info("🔍 技術的負債スキャン中...")

        # 既存の未解決負債をクリア（再スキャンのため）
        self.technical_debt = [item for item in self.technical_debt if item.resolved]

        try:
            # テストカバレッジ不足の検出
            self._scan_test_coverage_debt()

            # 複雑度の高い関数の検出
            self._scan_complexity_debt()

            # ドキュメント不足の検出
            self._scan_documentation_debt()

            # 重複コードの検出
            self._scan_duplication_debt()

        except Exception as e:
            logger.error(f"技術的負債スキャンエラー: {e}")

    def _scan_test_coverage_debt(self):
        """テストカバレッジ不足をスキャン"""
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--cov=kumihan_formatter",
                    "--cov-report=json",
                    "tests/",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, encoding="utf-8") as f:
                    coverage_data = json.load(f)

                files = coverage_data.get("files", {})
                for file_path, file_data in files.items():
                    coverage_percent = file_data.get("summary", {}).get(
                        "percent_covered", 0
                    )

                    if coverage_percent < 70:  # 70%未満を技術的負債とする
                        severity = "high" if coverage_percent < 50 else "medium"
                        debt = TechnicalDebtItem(
                            file_path=file_path,
                            debt_type="test_coverage",
                            severity=severity,
                            description=f"テストカバレッジ不足: {coverage_percent:.1f}%",
                            estimated_hours=2.0 + (70 - coverage_percent) * 0.1,
                            priority=1 if severity == "high" else 2,
                            created_date=datetime.now(),
                        )
                        self.technical_debt.append(debt)

        except Exception as e:
            logger.warning(f"テストカバレッジ負債スキャンエラー: {e}")

    def _scan_complexity_debt(self):
        """複雑度の高い関数をスキャン"""
        # 簡易的な複雑度スキャン
        # 実際の実装では radon などを使用
        python_files = list(self.project_root.glob("kumihan_formatter/**/*.py"))

        for file_path in python_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                lines = content.split("\n")

                # 関数の行数を簡易計算
                in_function = False
                function_start = 0
                indent_level = 0

                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith("def "):
                        if in_function and i - function_start > 50:
                            # 50行を超える関数を技術的負債とする
                            debt = TechnicalDebtItem(
                                file_path=str(file_path.relative_to(self.project_root)),
                                debt_type="complexity",
                                severity="medium",
                                description=f"長い関数: {i - function_start}行",
                                estimated_hours=1.0 + (i - function_start - 50) * 0.05,
                                priority=3,
                                created_date=datetime.now(),
                            )
                            self.technical_debt.append(debt)

                        in_function = True
                        function_start = i
                        indent_level = len(line) - len(line.lstrip())
                    elif (
                        in_function
                        and line.strip()
                        and len(line) - len(line.lstrip()) <= indent_level
                    ):
                        # 関数終了
                        if i - function_start > 50:
                            debt = TechnicalDebtItem(
                                file_path=str(file_path.relative_to(self.project_root)),
                                debt_type="complexity",
                                severity="medium",
                                description=f"長い関数: {i - function_start}行",
                                estimated_hours=1.0 + (i - function_start - 50) * 0.05,
                                priority=3,
                                created_date=datetime.now(),
                            )
                            self.technical_debt.append(debt)
                        in_function = False

            except Exception:
                continue

    def _scan_documentation_debt(self):
        """ドキュメント不足をスキャン"""
        python_files = list(self.project_root.glob("kumihan_formatter/**/*.py"))

        for file_path in python_files:
            try:
                content = file_path.read_text(encoding="utf-8")

                # クラスと関数の数を数える
                class_count = content.count("class ")
                function_count = content.count("def ")
                docstring_count = content.count('"""') + content.count("'''")

                # ドキュメント率を計算
                total_items = class_count + function_count
                if total_items > 0:
                    doc_ratio = docstring_count / (total_items * 2)  # 開始と終了で2つ

                    if doc_ratio < 0.5:  # 50%未満をドキュメント不足とする
                        debt = TechnicalDebtItem(
                            file_path=str(file_path.relative_to(self.project_root)),
                            debt_type="documentation",
                            severity="low",
                            description=f"ドキュメント不足: {doc_ratio:.1%}のカバレッジ",
                            estimated_hours=total_items * 0.3,
                            priority=4,
                            created_date=datetime.now(),
                        )
                        self.technical_debt.append(debt)

            except Exception:
                continue

    def _scan_duplication_debt(self):
        """重複コードをスキャン"""
        # 簡易的な重複検出
        # 実際の実装では より高度なアルゴリズムを使用
        pass

    def generate_dashboard_report(self) -> str:
        """ダッシュボードレポートを生成"""
        logger.info("📊 ダッシュボードレポート生成中...")

        metrics = self.collect_quality_metrics()

        report = []
        report.append("=" * 60)
        report.append("📊 品質監視ダッシュボード - Kumihan Formatter")
        report.append("=" * 60)
        report.append(f"⏰ 生成時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # メトリクス表示
        report.append("📈 品質メトリクス")
        report.append("-" * 30)
        for name, value in metrics.items():
            trend_indicator = ""
            if name in self.trends:
                trend_direction = self.trends[name].trend_direction
                trend_indicator = {
                    "improving": "📈",
                    "degrading": "📉",
                    "stable": "➡️",
                }.get(trend_direction, "")

            report.append(f"{name}: {value:.1f} {trend_indicator}")
        report.append("")

        # アラート表示
        if self.alerts:
            report.append("🚨 品質アラート")
            report.append("-" * 30)
            recent_alerts = [
                a
                for a in self.alerts
                if datetime.now() - a.timestamp < timedelta(hours=24)
            ]

            for alert in recent_alerts[-10:]:  # 最新10件
                severity_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                }.get(alert.severity, "⚪")

                report.append(
                    f"{severity_icon} [{alert.severity.upper()}] {alert.component}"
                )
                report.append(f"   {alert.message}")
                report.append(f"   {alert.timestamp.strftime('%H:%M:%S')}")
                report.append("")

        # 技術的負債サマリー
        unresolved_debt = [item for item in self.technical_debt if not item.resolved]
        if unresolved_debt:
            report.append("💸 技術的負債サマリー")
            report.append("-" * 30)

            debt_by_type = {}
            total_hours = 0
            for item in unresolved_debt:
                if item.debt_type not in debt_by_type:
                    debt_by_type[item.debt_type] = {"count": 0, "hours": 0}
                debt_by_type[item.debt_type]["count"] += 1
                debt_by_type[item.debt_type]["hours"] += item.estimated_hours
                total_hours += item.estimated_hours

            for debt_type, stats in debt_by_type.items():
                report.append(
                    f"{debt_type}: {stats['count']}件 ({stats['hours']:.1f}時間)"
                )

            report.append(f"合計: {len(unresolved_debt)}件 ({total_hours:.1f}時間)")
            report.append("")

        # 改善提案
        report.append("💡 改善提案")
        report.append("-" * 30)
        suggestions = self._generate_improvement_suggestions(metrics)
        for suggestion in suggestions:
            report.append(f"• {suggestion}")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

    def _generate_improvement_suggestions(self, metrics: Dict[str, float]) -> List[str]:
        """改善提案を生成"""
        suggestions = []

        if metrics.get("test_coverage", 0) < 80:
            suggestions.append(
                "テストカバレッジの向上: 特にCritical Tierの未テスト機能に注力"
            )

        if metrics.get("code_quality", 0) < 85:
            suggestions.append("コード品質の改善: flake8エラーの修正とリファクタリング")

        if metrics.get("complexity_score", 0) < 80:
            suggestions.append("複雑度の削減: 長い関数の分割と単純化")

        if metrics.get("technical_debt_score", 0) < 75:
            suggestions.append("技術的負債の計画的解消: 高優先度項目から段階的に対応")

        # トレンド分析による提案
        for name, trend in self.trends.items():
            if trend.trend_direction == "degrading":
                suggestions.append(f"{name}の悪化傾向を監視: 原因分析と対策検討が必要")

        if not suggestions:
            suggestions.append("品質指標は良好です。現在の水準を維持してください。")

        return suggestions

    def save_dashboard_report(self, output_file: Path):
        """ダッシュボードレポートを保存"""
        report = self.generate_dashboard_report()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"📄 ダッシュボードレポート保存: {output_file}")

        # 履歴データも保存
        self._save_data()


def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent

    logger.info("🚀 品質監視システム開始")

    # ダッシュボード初期化
    dashboard = QualityMonitoringDashboard(project_root)

    # 技術的負債スキャン
    dashboard.scan_technical_debt()

    # 品質メトリクス収集
    metrics = dashboard.collect_quality_metrics()

    # ダッシュボードレポート生成
    report_file = project_root / "quality_dashboard.txt"
    dashboard.save_dashboard_report(report_file)

    # コンソール出力
    print(dashboard.generate_dashboard_report())

    # 結果判定
    critical_alerts = [a for a in dashboard.alerts if a.severity == "critical"]
    if critical_alerts:
        logger.warning(f"🚨 {len(critical_alerts)}件の重要なアラートがあります")
        return 1

    logger.info("✅ 品質監視完了")
    return 0


if __name__ == "__main__":
    sys.exit(main())
