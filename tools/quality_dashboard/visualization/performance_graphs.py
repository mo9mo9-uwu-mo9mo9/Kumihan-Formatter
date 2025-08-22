"""
パフォーマンスグラフ生成

起動時間、メモリ使用量、処理速度の
視覚的な分析・追跡システム
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class PerformanceGraphGenerator:
    """パフォーマンスグラフ生成管理"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        os.makedirs("tmp", exist_ok=True)

    def generate_startup_time_graph(self, history_data: List[Dict[str, Any]]) -> Path:
        """起動時間推移グラフ生成"""
        try:
            if not history_data:
                return self._create_placeholder_graph("No Startup Time Data")

            # データ準備
            dates = []
            startup_times = []

            for entry in history_data:
                timestamp = entry.get("collection_timestamp")
                performance = entry.get("performance", {})
                startup_time = performance.get("startup_time_ms", 0)

                if timestamp and startup_time is not None:
                    try:
                        date = datetime.fromisoformat(timestamp)
                        dates.append(date)
                        startup_times.append(startup_time)
                    except ValueError:
                        continue

            if not dates:
                return self._create_placeholder_graph("No Valid Startup Data")

            # DataFrame作成
            df = pd.DataFrame({"date": dates, "startup_time": startup_times})
            df = df.sort_values("date")

            # グラフ作成
            fig, ax = plt.subplots(figsize=(12, 6))

            # 線グラフ
            ax.plot(
                df["date"],
                df["startup_time"],
                marker="o",
                linewidth=2,
                markersize=6,
                color="#8B5CF6",
                label="起動時間",
            )

            # 目標ライン
            ax.axhline(y=600, color="green", linestyle="--", alpha=0.7, label="目標 (600ms)")
            ax.axhline(y=1000, color="red", linestyle="--", alpha=0.7, label="限界 (1000ms)")

            # 範囲塗りつぶし
            ax.fill_between(df["date"], df["startup_time"], alpha=0.3, color="#8B5CF6")

            # スタイリング
            ax.set_title("起動時間推移", fontsize=16, fontweight="bold", pad=20)
            ax.set_xlabel("日付", fontsize=12)
            ax.set_ylabel("起動時間 (ms)", fontsize=12)

            # 日付フォーマット
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))

            # グリッドと凡例
            ax.grid(True, alpha=0.3)
            ax.legend()

            plt.xticks(rotation=45)
            plt.tight_layout()

            # 保存
            output_path = Path("tmp") / "startup_time_graph.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"Startup time graph generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate startup time graph: {e}")
            return self._create_placeholder_graph("Startup Graph Error")

    def generate_memory_usage_graph(self, history_data: List[Dict[str, Any]]) -> Path:
        """メモリ使用量推移グラフ生成"""
        try:
            if not history_data:
                return self._create_placeholder_graph("No Memory Usage Data")

            # データ準備
            dates = []
            memory_usages = []

            for entry in history_data:
                timestamp = entry.get("collection_timestamp")
                performance = entry.get("performance", {})
                memory_usage = performance.get("memory_usage_mb", 0)

                if timestamp and memory_usage is not None:
                    try:
                        date = datetime.fromisoformat(timestamp)
                        dates.append(date)
                        memory_usages.append(memory_usage)
                    except ValueError:
                        continue

            if not dates:
                return self._create_placeholder_graph("No Valid Memory Data")

            # DataFrame作成
            df = pd.DataFrame({"date": dates, "memory_usage": memory_usages})
            df = df.sort_values("date")

            # グラフ作成
            fig, ax = plt.subplots(figsize=(12, 6))

            # エリアグラフ
            ax.fill_between(
                df["date"],
                df["memory_usage"],
                alpha=0.6,
                color="#06B6D4",
                label="メモリ使用量",
            )
            ax.plot(df["date"], df["memory_usage"], color="#0891B2", linewidth=2)

            # 目標ライン
            ax.axhline(y=32, color="green", linestyle="--", alpha=0.7, label="目標 (32MB)")
            ax.axhline(y=50, color="red", linestyle="--", alpha=0.7, label="限界 (50MB)")

            # スタイリング
            ax.set_title("メモリ使用量推移", fontsize=16, fontweight="bold", pad=20)
            ax.set_xlabel("日付", fontsize=12)
            ax.set_ylabel("メモリ使用量 (MB)", fontsize=12)
            ax.set_ylim(0, None)

            # 日付フォーマット
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))

            # グリッドと凡例
            ax.grid(True, alpha=0.3)
            ax.legend()

            plt.xticks(rotation=45)
            plt.tight_layout()

            # 保存
            output_path = Path("tmp") / "memory_usage_graph.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"Memory usage graph generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate memory usage graph: {e}")
            return self._create_placeholder_graph("Memory Graph Error")

    def generate_performance_comparison_chart(self, current_metrics: Dict[str, Any]) -> Path:
        """パフォーマンス比較チャート生成"""
        try:
            performance = current_metrics.get("performance", {})

            if not performance:
                return self._create_placeholder_graph("No Performance Data")

            # データ準備
            metrics = ["起動時間", "メモリ使用量"]
            current_values = [
                performance.get("startup_time_ms", 0),
                performance.get("memory_usage_mb", 0),
            ]
            target_values = [
                performance.get("startup_threshold_ms", 600),
                performance.get("memory_threshold_mb", 32),
            ]

            # 正規化（パーセンテージ）
            normalized_current = []
            normalized_target = []

            for current, target in zip(current_values, target_values):
                if target > 0:
                    normalized_current.append((current / target) * 100)
                    normalized_target.append(100)  # 目標は100%
                else:
                    normalized_current.append(0)
                    normalized_target.append(100)

            # チャート作成
            fig, ax = plt.subplots(figsize=(10, 6))

            x = range(len(metrics))
            width = 0.35

            # バー作成
            bars1 = ax.bar(
                [i - width / 2 for i in x],
                normalized_current,
                width,
                label="現在値",
                color=["#EF4444" if v > 100 else "#10B981" for v in normalized_current],
            )
            bars2 = ax.bar(
                [i + width / 2 for i in x],
                normalized_target,
                width,
                label="目標値",
                color="#3B82F6",
                alpha=0.7,
            )

            # 値をバー上に表示
            for bar, current, target in zip(bars1, current_values, target_values):
                unit = "ms" if "time" in bar.get_label() else "MB"
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 5,
                    f"{current:.1f}{unit}",
                    ha="center",
                    va="bottom",
                    fontweight="bold",
                )

            # スタイリング
            ax.set_title("パフォーマンス目標との比較", fontsize=16, fontweight="bold", pad=20)
            ax.set_xlabel("パフォーマンス指標", fontsize=12)
            ax.set_ylabel("目標値に対する割合 (%)", fontsize=12)
            ax.set_xticks(x)
            ax.set_xticklabels(metrics)

            # 100%ライン
            ax.axhline(y=100, color="gray", linestyle="-", alpha=0.5, label="目標ライン")

            # グリッドと凡例
            ax.grid(True, alpha=0.3)
            ax.legend()

            plt.tight_layout()

            # 保存
            output_path = Path("tmp") / "performance_comparison_chart.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"Performance comparison chart generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate performance comparison chart: {e}")
            return self._create_placeholder_graph("Comparison Chart Error")

    def generate_performance_radar_chart(self, current_metrics: Dict[str, Any]) -> Path:
        """パフォーマンスレーダーチャート生成"""
        try:
            import numpy as np

            performance = current_metrics.get("performance", {})
            quality_score = current_metrics.get("quality_score", {})

            # データ準備
            categories = [
                "起動時間",
                "メモリ効率",
                "品質スコア",
                "カバレッジ",
                "コード品質",
            ]

            # 各指標を0-100のスケールに正規化
            startup_score = max(
                0, 100 - (performance.get("startup_time_ms", 1000) / 10)
            )  # 1000ms→0点
            memory_score = max(0, 100 - (performance.get("memory_usage_mb", 50) * 2))  # 50MB→0点
            quality_score_val = quality_score.get("score", 0)
            coverage_score = current_metrics.get("coverage", {}).get("total_coverage", 0)
            lint_score = max(0, 100 - current_metrics.get("lint", {}).get("total_issues", 0) * 10)

            values = [
                startup_score,
                memory_score,
                quality_score_val,
                coverage_score,
                lint_score,
            ]

            # レーダーチャート作成
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            values += values[:1]  # 閉じるために最初の値を追加
            angles += angles[:1]

            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection="polar"))

            # プロット
            ax.plot(angles, values, "o-", linewidth=2, color="#3B82F6", label="現在値")
            ax.fill(angles, values, alpha=0.25, color="#3B82F6")

            # 目標値（80点）をグレーで表示
            target_values = [80] * len(categories) + [80]
            ax.plot(
                angles,
                target_values,
                "--",
                linewidth=1,
                color="gray",
                alpha=0.7,
                label="目標 (80点)",
            )

            # カテゴリラベル
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 100)

            # スタイリング
            ax.set_title("パフォーマンス総合評価", fontsize=16, fontweight="bold", pad=30)
            ax.grid(True)
            ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))

            plt.tight_layout()

            # 保存
            output_path = Path("tmp") / "performance_radar_chart.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"Performance radar chart generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate performance radar chart: {e}")
            return self._create_placeholder_graph("Radar Chart Error")

    def _create_placeholder_graph(self, message: str) -> Path:
        """プレースホルダーグラフ生成"""
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

        output_path = Path("tmp") / "placeholder_performance_graph.png"
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path


def main():
    """CLI エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Performance graph generator")
    parser.add_argument(
        "--type",
        choices=["startup", "memory", "comparison", "radar"],
        default="startup",
        help="Graph type",
    )
    parser.add_argument("--data", type=str, help="Input data JSON file")

    args = parser.parse_args()

    generator = PerformanceGraphGenerator()

    # テストデータまたはファイルからデータ読み込み
    if args.data and Path(args.data).exists():
        with open(args.data, "r") as f:
            data = json.load(f)
    else:
        # サンプルデータ
        data = {
            "performance": {
                "startup_time_ms": 450,
                "memory_usage_mb": 28.5,
                "startup_threshold_ms": 600,
                "memory_threshold_mb": 32,
            },
            "quality_score": {"score": 85},
            "coverage": {"total_coverage": 73},
            "lint": {"total_issues": 2},
        }

    if args.type == "startup":
        graph_path = generator.generate_startup_time_graph([])
    elif args.type == "memory":
        graph_path = generator.generate_memory_usage_graph([])
    elif args.type == "comparison":
        graph_path = generator.generate_performance_comparison_chart(data)
    elif args.type == "radar":
        graph_path = generator.generate_performance_radar_chart(data)

    print(f"Graph generated: {graph_path}")

    return 0


if __name__ == "__main__":
    exit(main())
