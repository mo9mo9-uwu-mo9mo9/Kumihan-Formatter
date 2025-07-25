#!/usr/bin/env python3
"""
TDD根本原因分析スクリプト

245ファイルのテスト不足問題を分析し、分類・優先順位付けを行います。
根本的改善策の策定に必要なデータを提供します。
"""

import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


class TDDRootCauseAnalyzer:
    """TDD根本原因分析クラス"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.untested_files = []
        self.analysis_results = {}

    def collect_untested_files(self) -> List[Path]:
        """テスト不足ファイルの収集"""
        # 既存の分析結果ファイルから読み込み
        try:
            with open("tdd_analysis.txt", "r", encoding="utf-8") as f:
                content = f.read()

            # ファイルパスの抽出
            pattern = r"📄 (kumihan_formatter/[^\n]+\.py)"
            matches = re.findall(pattern, content)

            self.untested_files = [Path(match) for match in matches]
            return self.untested_files
        except FileNotFoundError:
            print("⚠️  tdd_analysis.txt not found. Generating new analysis...")
            # リアルタイム分析
            result = os.popen(
                "python3 scripts/enforce_tdd.py kumihan_formatter/"
            ).read()

            pattern = r"📄 (kumihan_formatter/[^\n]+\.py)"
            matches = re.findall(pattern, result)

            self.untested_files = [Path(match) for match in matches]
            return self.untested_files

    def categorize_files(self) -> Dict[str, List[Path]]:
        """ファイルをカテゴリ別に分類"""
        categories = {
            "GUI関連": [],
            "Core機能": [],
            "パフォーマンス系": [],
            "エラーハンドリング": [],
            "ユーティリティ": [],
            "バリデーション": [],
            "レンダリング": [],
            "キャッシング": [],
            "構文解析": [],
            "コマンド系": [],
            "その他": [],
        }

        for file_path in self.untested_files:
            path_str = str(file_path)

            if "gui_" in path_str or "ui/" in path_str:
                categories["GUI関連"].append(file_path)
            elif "/performance/" in path_str:
                categories["パフォーマンス系"].append(file_path)
            elif "/error_handling/" in path_str:
                categories["エラーハンドリング"].append(file_path)
            elif "/utilities/" in path_str or "/utils/" in path_str:
                categories["ユーティリティ"].append(file_path)
            elif "/validators/" in path_str or "validator" in path_str:
                categories["バリデーション"].append(file_path)
            elif "/rendering/" in path_str or "renderer" in path_str:
                categories["レンダリング"].append(file_path)
            elif "/caching/" in path_str or "cache" in path_str:
                categories["キャッシング"].append(file_path)
            elif "/syntax/" in path_str or "parser" in path_str:
                categories["構文解析"].append(file_path)
            elif "/commands/" in path_str:
                categories["コマンド系"].append(file_path)
            elif "/core/" in path_str:
                categories["Core機能"].append(file_path)
            else:
                categories["その他"].append(file_path)

        return categories

    def analyze_complexity(self, file_path: Path) -> Dict[str, int]:
        """ファイルの複雑さ分析"""
        try:
            content = file_path.read_text(encoding="utf-8")

            # 基本メトリクス
            lines = len(content.splitlines())
            classes = len(re.findall(r"^class\s+\w+", content, re.MULTILINE))
            functions = len(re.findall(r"^def\s+\w+", content, re.MULTILINE))
            imports = len(re.findall(r"^(import|from)\s+", content, re.MULTILINE))

            # 複雑度指標
            if_statements = len(re.findall(r"\bif\b", content))
            try_blocks = len(re.findall(r"\btry\b", content))
            async_funcs = len(re.findall(r"async def", content))

            return {
                "lines": lines,
                "classes": classes,
                "functions": functions,
                "imports": imports,
                "if_statements": if_statements,
                "try_blocks": try_blocks,
                "async_funcs": async_funcs,
                "complexity_score": lines
                + classes * 10
                + functions * 5
                + if_statements * 2,
            }
        except Exception:
            return {
                "lines": 0,
                "classes": 0,
                "functions": 0,
                "imports": 0,
                "if_statements": 0,
                "try_blocks": 0,
                "async_funcs": 0,
                "complexity_score": 0,
            }

    def prioritize_by_business_value(
        self, categories: Dict[str, List[Path]]
    ) -> Dict[str, int]:
        """ビジネス価値による優先順位付け"""
        priority_map = {
            "Core機能": 10,  # 最重要：システムの中核機能
            "コマンド系": 9,  # 重要：ユーザー直接操作
            "構文解析": 8,  # 重要：主要機能
            "レンダリング": 7,  # 中重要：出力品質
            "バリデーション": 6,  # 中重要：品質保証
            "エラーハンドリング": 5,  # 中重要：安定性
            "ユーティリティ": 4,  # 低重要：補助機能
            "キャッシング": 3,  # 低重要：パフォーマンス
            "パフォーマンス系": 2,  # 低重要：最適化
            "GUI関連": 1,  # 最低：UIは手動テスト主体
            "その他": 1,
        }
        return priority_map

    def calculate_test_effort(self, file_path: Path, complexity: Dict[str, int]) -> int:
        """テスト作成工数の見積もり（時間単位）"""
        base_effort = 2  # 基本工数 2時間

        # 複雑度による係数
        complexity_factor = min(complexity["complexity_score"] / 100, 3.0)

        # ファイルタイプによる係数
        path_str = str(file_path)
        if "gui_" in path_str or "/ui/" in path_str:
            type_factor = 3.0  # GUI は3倍困難
        elif "/performance/" in path_str:
            type_factor = 2.5  # パフォーマンス測定が必要
        elif "/error_handling/" in path_str:
            type_factor = 2.0  # エラーケースが多い
        else:
            type_factor = 1.0

        return int(base_effort * complexity_factor * type_factor)

    def generate_improvement_plan(self) -> Dict:
        """段階的改善計画の生成"""
        categories = self.categorize_files()
        priorities = self.prioritize_by_business_value(categories)

        # ファイル分析
        file_analysis = []
        for category, files in categories.items():
            for file_path in files:
                complexity = self.analyze_complexity(file_path)
                effort = self.calculate_test_effort(file_path, complexity)

                file_analysis.append(
                    {
                        "file": file_path,
                        "category": category,
                        "priority": priorities[category],
                        "complexity": complexity,
                        "effort_hours": effort,
                        "test_type": self._recommend_test_type(file_path, complexity),
                    }
                )

        # 優先順位でソート
        file_analysis.sort(key=lambda x: (-x["priority"], x["effort_hours"]))

        # 週次スケジュール生成（週20時間想定）
        weekly_schedule = self._generate_weekly_schedule(
            file_analysis, hours_per_week=20
        )

        return {
            "total_files": len(self.untested_files),
            "categories": {cat: len(files) for cat, files in categories.items()},
            "total_estimated_hours": sum(
                item["effort_hours"] for item in file_analysis
            ),
            "file_analysis": file_analysis,
            "weekly_schedule": weekly_schedule,
            "recommendations": self._generate_recommendations(
                categories, file_analysis
            ),
        }

    def _recommend_test_type(self, file_path: Path, complexity: Dict[str, int]) -> str:
        """推奨テストタイプの決定"""
        path_str = str(file_path)

        if "gui_" in path_str or "/ui/" in path_str:
            return "Manual/E2E"  # GUI は手動・E2Eテスト主体
        elif complexity["classes"] > 3 or complexity["functions"] > 10:
            return "Unit + Integration"  # 複雑なものは両方
        elif "/commands/" in path_str:
            return "Integration"  # コマンドは統合テスト
        else:
            return "Unit"  # 基本はユニットテスト

    def _generate_weekly_schedule(
        self, file_analysis: List[Dict], hours_per_week: int
    ) -> List[Dict]:
        """週次スケジュールの生成"""
        schedule = []
        current_week = 1
        current_hours = 0
        current_files = []

        for item in file_analysis:
            if current_hours + item["effort_hours"] > hours_per_week:
                # 週の上限を超える場合、次の週へ
                if current_files:
                    schedule.append(
                        {
                            "week": current_week,
                            "files": current_files.copy(),
                            "total_hours": current_hours,
                            "files_count": len(current_files),
                        }
                    )
                current_week += 1
                current_hours = 0
                current_files = []

            current_files.append(item)
            current_hours += item["effort_hours"]

        # 最後の週を追加
        if current_files:
            schedule.append(
                {
                    "week": current_week,
                    "files": current_files,
                    "total_hours": current_hours,
                    "files_count": len(current_files),
                }
            )

        return schedule

    def _generate_recommendations(
        self, categories: Dict[str, List[Path]], file_analysis: List[Dict]
    ) -> List[str]:
        """改善提案の生成"""
        recommendations = []

        # 1. GUI問題の解決提案
        gui_count = len(categories["GUI関連"])
        if gui_count > 20:
            recommendations.append(
                f"GUI関連ファイル{gui_count}個: E2Eテストフレームワーク導入を検討"
            )

        # 2. 高複雑度ファイルの対策
        high_complexity = [
            item
            for item in file_analysis
            if item["complexity"]["complexity_score"] > 300
        ]
        if high_complexity:
            recommendations.append(
                f"高複雑度ファイル{len(high_complexity)}個: リファクタリング優先検討"
            )

        # 3. カテゴリ別対策
        performance_count = len(categories["パフォーマンス系"])
        if performance_count > 30:
            recommendations.append(
                f"パフォーマンス系{performance_count}個: ベンチマークテスト自動化を検討"
            )

        # 4. 工数削減提案
        total_hours = sum(item["effort_hours"] for item in file_analysis)
        if total_hours > 500:
            recommendations.append(
                f"総工数{total_hours}時間: テストテンプレート・ジェネレータの導入を検討"
            )

        return recommendations


def main():
    """メイン処理"""
    analyzer = TDDRootCauseAnalyzer(Path("."))

    print("🔍 TDD根本原因分析開始")
    print("=" * 50)

    # 1. ファイル収集
    untested_files = analyzer.collect_untested_files()
    print(f"📊 テスト不足ファイル数: {len(untested_files)}")

    # 2. 包括的分析
    analysis = analyzer.generate_improvement_plan()

    # 3. 結果出力
    print("\n📋 カテゴリ別分析:")
    for category, count in analysis["categories"].items():
        if count > 0:
            print(f"  {category}: {count}ファイル")

    print(f"\n⏱️  総推定工数: {analysis['total_estimated_hours']}時間")
    print(f"📅 予想完了期間: {len(analysis['weekly_schedule'])}週間")

    print("\n🎯 改善提案:")
    for rec in analysis["recommendations"]:
        print(f"  • {rec}")

    print("\n📝 週次スケジュール（最初5週間）:")
    for week_data in analysis["weekly_schedule"][:5]:
        print(
            f"  Week {week_data['week']}: {week_data['files_count']}ファイル ({week_data['total_hours']}時間)"
        )
        for file_info in week_data["files"][:3]:  # 上位3ファイルのみ表示
            print(
                f"    - {file_info['file'].name} ({file_info['category']}, {file_info['effort_hours']}h)"
            )
        if len(week_data["files"]) > 3:
            print(f"    ... 他 {len(week_data['files']) - 3}ファイル")
        print()


if __name__ == "__main__":
    main()
