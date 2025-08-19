"""
品質トレンド分析システム

時系列品質データの分析と
予測・トレンド可視化機能
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class QualityTrendAnalyzer:
    """品質トレンド分析管理"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        os.makedirs("tmp", exist_ok=True)

    def analyze_quality_trends(
        self, history_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """品質トレンド総合分析"""
        if not history_data:
            return {"status": "no_data", "message": "履歴データが不足しています"}

        # データ準備
        df = self._prepare_dataframe(history_data)

        if df.empty:
            return {"status": "invalid_data", "message": "有効なデータがありません"}

        # 各種トレンド分析
        quality_trend = self._analyze_quality_score_trend(df)
        coverage_trend = self._analyze_coverage_trend(df)
        performance_trend = self._analyze_performance_trend(df)

        # 予測分析
        predictions = self._generate_predictions(df)

        # 異常検知
        anomalies = self._detect_anomalies(df)

        return {
            "status": "success",
            "analysis_period": {
                "start_date": df["date"].min().isoformat(),
                "end_date": df["date"].max().isoformat(),
                "data_points": len(df),
            },
            "quality_score_trend": quality_trend,
            "coverage_trend": coverage_trend,
            "performance_trend": performance_trend,
            "predictions": predictions,
            "anomalies": anomalies,
            "overall_assessment": self._generate_overall_assessment(
                quality_trend, coverage_trend, performance_trend
            ),
        }

    def _prepare_dataframe(self, history_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """データフレーム準備"""
        records = []

        for entry in history_data:
            try:
                timestamp = entry.get("collection_timestamp")
                if not timestamp:
                    continue

                date = datetime.fromisoformat(timestamp)

                record = {
                    "date": date,
                    "quality_score": entry.get("quality_score", {}).get("score", 0),
                    "coverage": entry.get("coverage", {}).get("total_coverage", 0),
                    "startup_time": entry.get("performance", {}).get(
                        "startup_time_ms", 0
                    ),
                    "memory_usage": entry.get("performance", {}).get(
                        "memory_usage_mb", 0
                    ),
                    "lint_issues": entry.get("lint", {}).get("total_issues", 0),
                    "complexity_count": entry.get("complexity", {}).get(
                        "high_complexity_count", 0
                    ),
                }

                records.append(record)

            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid data entry: {e}")
                continue

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df = df.sort_values("date").reset_index(drop=True)

        return df

    def _analyze_quality_score_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """品質スコアトレンド分析"""
        if "quality_score" not in df.columns or df["quality_score"].empty:
            return {"status": "no_data"}

        # 基本統計
        current_score = df["quality_score"].iloc[-1]
        mean_score = df["quality_score"].mean()
        std_score = df["quality_score"].std()

        # トレンド計算
        days = (df["date"] - df["date"].min()).dt.days
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            days, df["quality_score"]
        )

        # トレンド方向判定
        if slope > 0.5:
            trend_direction = "improving"
        elif slope < -0.5:
            trend_direction = "declining"
        else:
            trend_direction = "stable"

        # 変動性評価
        volatility = "high" if std_score > 10 else "medium" if std_score > 5 else "low"

        return {
            "status": "analyzed",
            "current_score": current_score,
            "mean_score": mean_score,
            "trend_slope": slope,
            "trend_direction": trend_direction,
            "trend_strength": abs(r_value),
            "volatility": volatility,
            "p_value": p_value,
            "days_analyzed": len(df),
        }

    def _analyze_coverage_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """カバレッジトレンド分析"""
        if "coverage" not in df.columns or df["coverage"].empty:
            return {"status": "no_data"}

        # 基本統計
        current_coverage = df["coverage"].iloc[-1]
        mean_coverage = df["coverage"].mean()

        # トレンド計算
        days = (df["date"] - df["date"].min()).dt.days
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            days, df["coverage"]
        )

        # 目標達成状況
        target_achievement_rate = len(df[df["coverage"] >= 80]) / len(df) * 100
        minimum_compliance_rate = len(df[df["coverage"] >= 70]) / len(df) * 100

        return {
            "status": "analyzed",
            "current_coverage": current_coverage,
            "mean_coverage": mean_coverage,
            "trend_slope": slope,
            "trend_direction": (
                "improving"
                if slope > 0.1
                else "declining" if slope < -0.1 else "stable"
            ),
            "target_achievement_rate": target_achievement_rate,
            "minimum_compliance_rate": minimum_compliance_rate,
            "trend_strength": abs(r_value),
        }

    def _analyze_performance_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """パフォーマンストレンド分析"""
        startup_analysis = {}
        memory_analysis = {}

        if "startup_time" in df.columns and not df["startup_time"].empty:
            days = (df["date"] - df["date"].min()).dt.days
            slope, _, r_value, _, _ = stats.linregress(days, df["startup_time"])

            startup_analysis = {
                "current_startup_time": df["startup_time"].iloc[-1],
                "mean_startup_time": df["startup_time"].mean(),
                "trend_slope": slope,
                "trend_direction": (
                    "improving"
                    if slope < -5
                    else "declining" if slope > 5 else "stable"
                ),
                "target_compliance_rate": len(df[df["startup_time"] <= 600])
                / len(df)
                * 100,
            }

        if "memory_usage" in df.columns and not df["memory_usage"].empty:
            days = (df["date"] - df["date"].min()).dt.days
            slope, _, r_value, _, _ = stats.linregress(days, df["memory_usage"])

            memory_analysis = {
                "current_memory_usage": df["memory_usage"].iloc[-1],
                "mean_memory_usage": df["memory_usage"].mean(),
                "trend_slope": slope,
                "trend_direction": (
                    "improving"
                    if slope < -0.5
                    else "declining" if slope > 0.5 else "stable"
                ),
                "target_compliance_rate": len(df[df["memory_usage"] <= 32])
                / len(df)
                * 100,
            }

        return {
            "status": "analyzed",
            "startup_time": startup_analysis,
            "memory_usage": memory_analysis,
        }

    def _generate_predictions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """予測分析"""
        predictions = {}

        # 品質スコア予測
        if "quality_score" in df.columns and len(df) >= 3:
            days = (df["date"] - df["date"].min()).dt.days
            slope, intercept, _, _, _ = stats.linregress(days, df["quality_score"])

            # 7日後の予測
            future_days = days.iloc[-1] + 7
            predicted_score = slope * future_days + intercept
            predicted_score = max(0, min(100, predicted_score))  # 0-100に制限

            predictions["quality_score"] = {
                "predicted_value": predicted_score,
                "prediction_days": 7,
                "confidence": "medium" if abs(slope) > 0.1 else "low",
            }

        # カバレッジ予測
        if "coverage" in df.columns and len(df) >= 3:
            days = (df["date"] - df["date"].min()).dt.days
            slope, intercept, _, _, _ = stats.linregress(days, df["coverage"])

            future_days = days.iloc[-1] + 7
            predicted_coverage = slope * future_days + intercept
            predicted_coverage = max(0, min(100, predicted_coverage))

            predictions["coverage"] = {
                "predicted_value": predicted_coverage,
                "prediction_days": 7,
                "confidence": "medium" if abs(slope) > 0.1 else "low",
            }

        return predictions

    def _detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """異常検知"""
        anomalies = []

        for column in ["quality_score", "coverage", "startup_time", "memory_usage"]:
            if column not in df.columns or df[column].empty:
                continue

            # Z-score による異常検知
            z_scores = np.abs(stats.zscore(df[column].dropna()))
            anomaly_threshold = 2.0

            anomaly_indices = np.where(z_scores > anomaly_threshold)[0]

            for idx in anomaly_indices:
                if idx < len(df):
                    anomalies.append(
                        {
                            "date": df.iloc[idx]["date"].isoformat(),
                            "metric": column,
                            "value": df.iloc[idx][column],
                            "z_score": z_scores[idx],
                            "severity": "high" if z_scores[idx] > 3.0 else "medium",
                        }
                    )

        return anomalies

    def _generate_overall_assessment(
        self,
        quality_trend: Dict[str, Any],
        coverage_trend: Dict[str, Any],
        performance_trend: Dict[str, Any],
    ) -> Dict[str, Any]:
        """全体評価生成"""

        # トレンド方向スコア計算
        trend_score = 0

        if quality_trend.get("trend_direction") == "improving":
            trend_score += 3
        elif quality_trend.get("trend_direction") == "stable":
            trend_score += 1

        if coverage_trend.get("trend_direction") == "improving":
            trend_score += 2
        elif coverage_trend.get("trend_direction") == "stable":
            trend_score += 1

        startup_trend = performance_trend.get("startup_time", {}).get("trend_direction")
        if startup_trend == "improving":
            trend_score += 2
        elif startup_trend == "stable":
            trend_score += 1

        # 全体評価
        if trend_score >= 6:
            overall_status = "excellent"
            assessment = "品質が継続的に向上しています"
        elif trend_score >= 4:
            overall_status = "good"
            assessment = "品質は良好な状態を維持しています"
        elif trend_score >= 2:
            overall_status = "warning"
            assessment = "品質の安定性に注意が必要です"
        else:
            overall_status = "critical"
            assessment = "品質の低下傾向が見られます"

        return {
            "overall_status": overall_status,
            "trend_score": trend_score,
            "assessment": assessment,
            "recommendations": self._generate_recommendations(
                quality_trend, coverage_trend, performance_trend
            ),
        }

    def _generate_recommendations(
        self,
        quality_trend: Dict[str, Any],
        coverage_trend: Dict[str, Any],
        performance_trend: Dict[str, Any],
    ) -> List[str]:
        """改善推奨事項生成"""
        recommendations = []

        if quality_trend.get("trend_direction") == "declining":
            recommendations.append(
                "品質スコアの低下傾向を改善するため、コードレビューを強化してください"
            )

        if coverage_trend.get("trend_direction") == "declining":
            recommendations.append(
                "テストカバレッジの向上のため、単体テストを追加してください"
            )

        startup_trend = performance_trend.get("startup_time", {}).get("trend_direction")
        if startup_trend == "declining":
            recommendations.append(
                "起動時間の悪化を防ぐため、パフォーマンス最適化を検討してください"
            )

        memory_trend = performance_trend.get("memory_usage", {}).get("trend_direction")
        if memory_trend == "declining":
            recommendations.append(
                "メモリ使用量の増加を抑えるため、メモリリーク調査を実施してください"
            )

        if not recommendations:
            recommendations.append(
                "現在の品質レベルを維持し、継続的な改善を心がけてください"
            )

        return recommendations

    def generate_comprehensive_trend_chart(
        self, history_data: List[Dict[str, Any]]
    ) -> Path:
        """包括的トレンドチャート生成"""
        try:
            df = self._prepare_dataframe(history_data)

            if df.empty:
                return self._create_placeholder_chart("No Trend Data")

            # 4つのサブプロット
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

            # 品質スコア推移
            ax1.plot(
                df["date"],
                df["quality_score"],
                marker="o",
                color="#3B82F6",
                linewidth=2,
            )
            ax1.set_title("品質スコア推移", fontweight="bold")
            ax1.set_ylabel("スコア")
            ax1.grid(True, alpha=0.3)
            ax1.axhline(y=80, color="green", linestyle="--", alpha=0.7)

            # カバレッジ推移
            ax2.plot(
                df["date"], df["coverage"], marker="s", color="#10B981", linewidth=2
            )
            ax2.set_title("カバレッジ推移", fontweight="bold")
            ax2.set_ylabel("カバレッジ (%)")
            ax2.grid(True, alpha=0.3)
            ax2.axhline(y=70, color="red", linestyle="--", alpha=0.7)
            ax2.axhline(y=80, color="green", linestyle="--", alpha=0.7)

            # 起動時間推移
            ax3.plot(
                df["date"], df["startup_time"], marker="^", color="#8B5CF6", linewidth=2
            )
            ax3.set_title("起動時間推移", fontweight="bold")
            ax3.set_ylabel("起動時間 (ms)")
            ax3.grid(True, alpha=0.3)
            ax3.axhline(y=600, color="green", linestyle="--", alpha=0.7)

            # メモリ使用量推移
            ax4.plot(
                df["date"], df["memory_usage"], marker="d", color="#06B6D4", linewidth=2
            )
            ax4.set_title("メモリ使用量推移", fontweight="bold")
            ax4.set_ylabel("メモリ (MB)")
            ax4.grid(True, alpha=0.3)
            ax4.axhline(y=32, color="green", linestyle="--", alpha=0.7)

            # 日付フォーマット統一
            for ax in [ax1, ax2, ax3, ax4]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
                ax.tick_params(axis="x", rotation=45)

            plt.suptitle(
                "品質メトリクス包括的トレンド分析", fontsize=16, fontweight="bold"
            )
            plt.tight_layout()

            # 保存
            output_path = Path("tmp") / "comprehensive_trend_chart.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"Comprehensive trend chart generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate comprehensive trend chart: {e}")
            return self._create_placeholder_chart("Trend Chart Error")

    def _create_placeholder_chart(self, message: str) -> Path:
        """プレースホルダーチャート生成"""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            fontsize=16,
            transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"),
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        output_path = Path("tmp") / "placeholder_trend_chart.png"
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path


def main():
    """CLI エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Quality trend analyzer")
    parser.add_argument("--analyze", action="store_true", help="Perform trend analysis")
    parser.add_argument("--chart", action="store_true", help="Generate trend chart")
    parser.add_argument("--data", type=str, help="Input history data JSON file")

    args = parser.parse_args()

    analyzer = QualityTrendAnalyzer()

    # テストデータまたはファイルからデータ読み込み
    history_data = []
    if args.data and Path(args.data).exists():
        with open(args.data, "r") as f:
            history_data = json.load(f)

    if args.analyze:
        analysis = analyzer.analyze_quality_trends(history_data)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))

    if args.chart:
        chart_path = analyzer.generate_comprehensive_trend_chart(history_data)
        print(f"Trend chart generated: {chart_path}")

    if not args.analyze and not args.chart:
        print("Use --analyze or --chart option")

    return 0


if __name__ == "__main__":
    exit(main())
