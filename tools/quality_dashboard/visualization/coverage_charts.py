"""
カバレッジ可視化チャート生成

モジュール別カバレッジ分析と
視覚的チャート生成システム
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib

matplotlib.use("Agg")  # GUI環境不要のbackend
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class CoverageChartGenerator:
    """カバレッジチャート生成管理"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        os.makedirs("tmp", exist_ok=True)

    def generate_module_coverage_chart(self, coverage_data: Dict[str, Any]) -> Path:
        """モジュール別カバレッジチャート生成"""
        try:
            module_coverage = coverage_data.get("module_coverage", {})

            if not module_coverage:
                logger.warning("No module coverage data available")
                return self._create_placeholder_chart("No Coverage Data")

            # データ準備
            modules = list(module_coverage.keys())
            coverages = list(module_coverage.values())

            # 日本語フォント設定（利用可能な場合）
            try:
                plt.rcParams["font.family"] = "DejaVu Sans"
            except:
                pass

            # チャート作成
            fig, ax = plt.subplots(figsize=(12, 8))

            # 棒グラフ
            bars = ax.bar(
                modules, coverages, color=self._get_coverage_colors(coverages)
            )

            # 閾値ライン
            ax.axhline(
                y=70, color="red", linestyle="--", alpha=0.7, label="最小閾値 (70%)"
            )
            ax.axhline(
                y=80, color="orange", linestyle="--", alpha=0.7, label="目標 (80%)"
            )
            ax.axhline(
                y=90, color="green", linestyle="--", alpha=0.7, label="優秀 (90%)"
            )

            # スタイリング
            ax.set_title(
                "モジュール別テストカバレッジ", fontsize=16, fontweight="bold", pad=20
            )
            ax.set_xlabel("モジュール", fontsize=12)
            ax.set_ylabel("カバレッジ (%)", fontsize=12)
            ax.set_ylim(0, 100)

            # 値をバー上に表示
            for bar, coverage in zip(bars, coverages):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 1,
                    f"{coverage:.1f}%",
                    ha="center",
                    va="bottom",
                    fontweight="bold",
                )

            # グリッドと凡例
            ax.grid(True, alpha=0.3)
            ax.legend()

            # X軸ラベル回転
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            # 保存
            output_path = Path("tmp") / "module_coverage_chart.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"Module coverage chart generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate module coverage chart: {e}")
            return self._create_placeholder_chart("Chart Generation Error")

    def generate_coverage_trend_chart(self, history_data: List[Dict[str, Any]]) -> Path:
        """カバレッジ推移チャート生成"""
        try:
            if not history_data:
                return self._create_placeholder_chart("No Historical Data")

            # データ準備
            dates = []
            coverages = []

            for entry in history_data:
                timestamp = entry.get("collection_timestamp")
                coverage = entry.get("coverage", {}).get("total_coverage", 0)

                if timestamp and coverage is not None:
                    try:
                        date = datetime.fromisoformat(timestamp)
                        dates.append(date)
                        coverages.append(coverage)
                    except ValueError:
                        continue

            if not dates:
                return self._create_placeholder_chart("No Valid Date Data")

            # DataFrame作成
            df = pd.DataFrame({"date": dates, "coverage": coverages})
            df = df.sort_values("date")

            # チャート作成
            fig, ax = plt.subplots(figsize=(12, 6))

            # 線グラフ
            ax.plot(
                df["date"],
                df["coverage"],
                marker="o",
                linewidth=2,
                markersize=6,
                color="#3B82F6",
                label="カバレッジ推移",
            )

            # 閾値ライン
            ax.axhline(
                y=70, color="red", linestyle="--", alpha=0.7, label="最小閾値 (70%)"
            )
            ax.axhline(
                y=80, color="green", linestyle="--", alpha=0.7, label="目標 (80%)"
            )

            # 範囲塗りつぶし
            ax.fill_between(df["date"], df["coverage"], alpha=0.3, color="#3B82F6")

            # スタイリング
            ax.set_title("テストカバレッジ推移", fontsize=16, fontweight="bold", pad=20)
            ax.set_xlabel("日付", fontsize=12)
            ax.set_ylabel("カバレッジ (%)", fontsize=12)
            ax.set_ylim(0, 100)

            # 日付フォーマット
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))

            # グリッドと凡例
            ax.grid(True, alpha=0.3)
            ax.legend()

            plt.xticks(rotation=45)
            plt.tight_layout()

            # 保存
            output_path = Path("tmp") / "coverage_trend_chart.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"Coverage trend chart generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate coverage trend chart: {e}")
            return self._create_placeholder_chart("Trend Chart Error")

    def generate_coverage_heatmap(self, coverage_data: Dict[str, Any]) -> Path:
        """カバレッジヒートマップ生成"""
        try:
            module_coverage = coverage_data.get("module_coverage", {})

            if not module_coverage:
                return self._create_placeholder_chart("No Module Data for Heatmap")

            # データを2次元グリッドに変換（簡易版）
            modules = list(module_coverage.keys())
            coverages = list(module_coverage.values())

            # 適切なグリッドサイズ計算
            n_modules = len(modules)
            grid_size = int(n_modules**0.5) + 1

            # グリッドデータ作成
            grid_data = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
            module_labels = [["" for _ in range(grid_size)] for _ in range(grid_size)]

            for i, (module, coverage) in enumerate(module_coverage.items()):
                row = i // grid_size
                col = i % grid_size
                if row < grid_size and col < grid_size:
                    grid_data[row][col] = coverage
                    module_labels[row][col] = module[:8]  # 短縮

            # ヒートマップ作成
            fig, ax = plt.subplots(figsize=(10, 8))

            im = ax.imshow(grid_data, cmap="RdYlGn", vmin=0, vmax=100)

            # ラベル設定
            for i in range(grid_size):
                for j in range(grid_size):
                    if module_labels[i][j]:
                        text = ax.text(
                            j,
                            i,
                            f"{module_labels[i][j]}\n{grid_data[i][j]:.1f}%",
                            ha="center",
                            va="center",
                            color="black",
                            fontsize=8,
                        )

            # カラーバー
            cbar = plt.colorbar(im)
            cbar.set_label("カバレッジ (%)", rotation=270, labelpad=20)

            # スタイリング
            ax.set_title(
                "モジュール別カバレッジヒートマップ",
                fontsize=14,
                fontweight="bold",
                pad=20,
            )
            ax.set_xticks([])
            ax.set_yticks([])

            plt.tight_layout()

            # 保存
            output_path = Path("tmp") / "coverage_heatmap.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"Coverage heatmap generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate coverage heatmap: {e}")
            return self._create_placeholder_chart("Heatmap Generation Error")

    def _get_coverage_colors(self, coverages: List[float]) -> List[str]:
        """カバレッジに基づく色配列生成"""
        colors = []
        for coverage in coverages:
            if coverage >= 90:
                colors.append("#10B981")  # 緑
            elif coverage >= 80:
                colors.append("#3B82F6")  # 青
            elif coverage >= 70:
                colors.append("#F59E0B")  # 黄
            else:
                colors.append("#EF4444")  # 赤
        return colors

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

        output_path = Path("tmp") / "placeholder_chart.png"
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path


def main():
    """CLI エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Coverage chart generator")
    parser.add_argument(
        "--type",
        choices=["module", "trend", "heatmap"],
        default="module",
        help="Chart type",
    )
    parser.add_argument("--data", type=str, help="Input data JSON file")

    args = parser.parse_args()

    generator = CoverageChartGenerator()

    # テストデータまたはファイルからデータ読み込み
    if args.data and Path(args.data).exists():
        with open(args.data, "r") as f:
            data = json.load(f)
    else:
        # サンプルデータ
        data = {
            "module_coverage": {
                "core": 85.5,
                "core_parser": 92.3,
                "core_rendering": 78.1,
                "cli": 72.4,
                "config": 88.9,
            }
        }

    if args.type == "module":
        chart_path = generator.generate_module_coverage_chart(data)
    elif args.type == "trend":
        # 履歴データが必要
        chart_path = generator.generate_coverage_trend_chart([])
    elif args.type == "heatmap":
        chart_path = generator.generate_coverage_heatmap(data)

    print(f"Chart generated: {chart_path}")

    return 0


if __name__ == "__main__":
    exit(main())
