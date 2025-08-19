"""
Gemini協業最適化ツール

Issue #922 Phase 4経験に基づくタスク難易度自動判定と
協業戦略最適化システム
"""

import json
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TaskComplexity:
    """タスク複雑度評価結果"""

    level: str  # SIMPLE, MODERATE, COMPLEX
    confidence: float  # 判定信頼度 (0.0-1.0)
    strategy: str  # gemini_collaboration, split_and_gemini, claude_direct
    reasons: List[str]  # 判定根拠
    file_count: int
    estimated_tokens: int


@dataclass
class CollaborationHistory:
    """協業履歴データ"""

    phase_name: str
    task_description: str
    complexity: TaskComplexity
    method_used: str  # gemini, claude_direct
    success: bool
    execution_time: float
    tokens_saved: int
    error_message: Optional[str] = None


class GeminiCollaborationOptimizer:
    """Gemini協業最適化システム"""

    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or Path("tmp/gemini_collaboration_history.json")
        self.history: List[CollaborationHistory] = []
        self._load_history()

        # Issue #922 Phase 4で確立されたルール
        self.claude_required_keywords = [
            "memory", "security", "parallel", "async", "optimization",
            "threading", "crypto", "auth", "vulnerability", "performance"
        ]

        self.gemini_suitable_extensions = [
            ".yaml", ".yml", ".json", ".toml", ".md", ".html", ".txt", ".csv"
        ]

        self.gemini_suitable_keywords = [
            "config", "template", "docs", "documentation", "test", "mock", "fixture"
        ]

    def evaluate_task_complexity(
        self,
        task_description: str,
        file_list: List[str]
    ) -> TaskComplexity:
        """タスク複雑度評価"""

        reasons = []
        complexity_score = 0.0
        file_count = len(file_list)

        # キーワード分析
        desc_lower = task_description.lower()

        # Claude必須キーワードチェック
        claude_keywords_found = []
        for keyword in self.claude_required_keywords:
            if keyword in desc_lower:
                claude_keywords_found.append(keyword)
                complexity_score += 2.0

        if claude_keywords_found:
            reasons.append(f"Claude必須キーワード検出: {claude_keywords_found}")

        # Gemini適合キーワードチェック
        gemini_keywords_found = []
        for keyword in self.gemini_suitable_keywords:
            if keyword in desc_lower:
                gemini_keywords_found.append(keyword)
                complexity_score -= 0.5

        if gemini_keywords_found:
            reasons.append(f"Gemini適合キーワード検出: {gemini_keywords_found}")

        # ファイル拡張子分析
        gemini_extensions = []
        complex_extensions = []

        for file_path in file_list:
            path = Path(file_path)
            ext = path.suffix.lower()

            if ext in self.gemini_suitable_extensions:
                gemini_extensions.append(ext)
                complexity_score -= 0.3
            elif ext == ".py":
                # Pythonファイルは内容に依存
                if any(keyword in path.name.lower()
                       for keyword in self.claude_required_keywords):
                    complex_extensions.append(file_path)
                    complexity_score += 1.0
                else:
                    complexity_score += 0.2

        if gemini_extensions:
            reasons.append(f"Gemini適合拡張子: {set(gemini_extensions)}")

        if complex_extensions:
            reasons.append(f"複雑なPythonファイル: {complex_extensions}")

        # ファイル数による評価
        if file_count > 4:
            complexity_score += 1.5
            reasons.append(f"大量ファイル ({file_count}個) - 分割推奨")
        elif file_count > 2:
            complexity_score += 0.5
            reasons.append(f"中程度のファイル数 ({file_count}個)")

        # 複雑度レベル判定
        if complexity_score >= 2.0 or claude_keywords_found:
            level = "COMPLEX"
            strategy = "claude_direct"
            confidence = min(0.9, 0.6 + complexity_score * 0.1)
        elif complexity_score >= 0.5 or file_count > 2:
            level = "MODERATE"
            if file_count > 3:
                strategy = "split_and_gemini"
            else:
                strategy = "gemini_collaboration"
            confidence = 0.7
        else:
            level = "SIMPLE"
            strategy = "gemini_collaboration"
            confidence = max(0.8, 1.0 - complexity_score * 0.2)

        # Token推定
        estimated_tokens = self._estimate_tokens(file_count, level)

        return TaskComplexity(
            level=level,
            confidence=confidence,
            strategy=strategy,
            reasons=reasons,
            file_count=file_count,
            estimated_tokens=estimated_tokens
        )

    def _estimate_tokens(self, file_count: int, complexity_level: str) -> int:
        """Token使用量推定"""
        base_tokens = {
            "SIMPLE": 500,
            "MODERATE": 1000,
            "COMPLEX": 2000
        }

        return base_tokens[complexity_level] + (file_count * 300)

    def suggest_strategy(self, task_complexity: TaskComplexity) -> Dict[str, Any]:
        """戦略提案"""

        suggestion = {
            "recommended_method": task_complexity.strategy,
            "complexity_level": task_complexity.level,
            "confidence": task_complexity.confidence,
            "reasons": task_complexity.reasons,
            "estimated_tokens": task_complexity.estimated_tokens
        }

        # 具体的な提案
        if task_complexity.strategy == "claude_direct":
            suggestion["action"] = "Claude直接実装を推奨"
            suggestion["rationale"] = "技術的複雑度またはセキュリティ要件のため"

        elif task_complexity.strategy == "split_and_gemini":
            suggestion["action"] = f"{task_complexity.file_count}ファイルを2-3個ずつに分割してGemini協業"
            suggestion["rationale"] = "ファイル数が多いため分割実装が効率的"

        else:  # gemini_collaboration
            suggestion["action"] = "Gemini協業を推奨"
            suggestion["rationale"] = "シンプルなタスクでToken節約効果が高い"

        # 履歴ベースの調整
        success_rate = self._calculate_success_rate(task_complexity.level)
        suggestion["historical_success_rate"] = success_rate

        if success_rate < 0.7:
            suggestion["warning"] = f"{task_complexity.level}レベルでの成功率が低いため注意が必要"

        return suggestion

    def record_execution(
        self,
        phase_name: str,
        task_description: str,
        complexity: TaskComplexity,
        method_used: str,
        success: bool,
        execution_time: float,
        tokens_saved: int = 0,
        error_message: Optional[str] = None
    ) -> None:
        """実行結果記録"""

        history_entry = CollaborationHistory(
            phase_name=phase_name,
            task_description=task_description,
            complexity=complexity,
            method_used=method_used,
            success=success,
            execution_time=execution_time,
            tokens_saved=tokens_saved,
            error_message=error_message
        )

        self.history.append(history_entry)
        self._save_history()

        logger.info(f"Recorded collaboration history: {phase_name} - {'Success' if success else 'Failed'}")

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得"""

        if not self.history:
            return {"message": "履歴データなし"}

        total_entries = len(self.history)
        successful_entries = sum(1 for h in self.history if h.success)
        total_tokens_saved = sum(h.tokens_saved for h in self.history)

        # 複雑度別統計
        complexity_stats = {}
        for level in ["SIMPLE", "MODERATE", "COMPLEX"]:
            level_entries = [h for h in self.history if h.complexity.level == level]
            if level_entries:
                level_success = sum(1 for h in level_entries if h.success)
                complexity_stats[level] = {
                    "total": len(level_entries),
                    "success": level_success,
                    "success_rate": level_success / len(level_entries),
                    "avg_tokens_saved": sum(h.tokens_saved for h in level_entries) / len(level_entries)
                }

        # 手法別統計
        method_stats = {}
        for method in ["gemini", "claude_direct"]:
            method_entries = [h for h in self.history if h.method_used == method]
            if method_entries:
                method_success = sum(1 for h in method_entries if h.success)
                method_stats[method] = {
                    "total": len(method_entries),
                    "success": method_success,
                    "success_rate": method_success / len(method_entries)
                }

        return {
            "total_executions": total_entries,
            "overall_success_rate": successful_entries / total_entries,
            "total_tokens_saved": total_tokens_saved,
            "complexity_breakdown": complexity_stats,
            "method_breakdown": method_stats,
            "recent_failures": [
                {
                    "phase": h.phase_name,
                    "error": h.error_message,
                    "complexity": h.complexity.level
                }
                for h in self.history[-5:] if not h.success
            ]
        }

    def _calculate_success_rate(self, complexity_level: str) -> float:
        """複雑度別成功率計算"""
        level_entries = [h for h in self.history if h.complexity.level == complexity_level]
        if not level_entries:
            return 0.8  # デフォルト値

        successful = sum(1 for h in level_entries if h.success)
        return successful / len(level_entries)

    def _load_history(self) -> None:
        """履歴データ読み込み"""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.history = []
                for entry in data:
                    complexity = TaskComplexity(**entry["complexity"])
                    history_entry = CollaborationHistory(
                        **{k: v for k, v in entry.items() if k != "complexity"},
                        complexity=complexity
                    )
                    self.history.append(history_entry)

                logger.info(f"Loaded {len(self.history)} history entries")

            except Exception as e:
                logger.error(f"Failed to load history: {e}")
                self.history = []

    def _save_history(self) -> None:
        """履歴データ保存"""
        try:
            os.makedirs("tmp", exist_ok=True)

            data = []
            for entry in self.history:
                entry_dict = asdict(entry)
                data.append(entry_dict)

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def generate_recommendations_report(self) -> Dict[str, Any]:
        """推奨事項レポート生成"""
        stats = self.get_statistics()

        recommendations = []

        # 成功率ベースの推奨
        if stats.get("overall_success_rate", 0) < 0.8:
            recommendations.append(
                "全体成功率が80%未満です。タスク事前評価の精度向上を検討してください。"
            )

        # 複雑度別推奨
        complexity_stats = stats.get("complexity_breakdown", {})
        for level, data in complexity_stats.items():
            if data["success_rate"] < 0.7:
                recommendations.append(
                    f"{level}レベルタスクの成功率が低いです。Claude直接実装を優先してください。"
                )

        # Token節約効果
        total_saved = stats.get("total_tokens_saved", 0)
        if total_saved > 5000:
            recommendations.append(
                f"優秀なToken節約効果 ({total_saved} tokens)。現在の戦略を継続してください。"
            )

        return {
            "statistics": stats,
            "recommendations": recommendations,
            "timestamp": time.time(),
            "report_version": "1.0"
        }


def main():
    """CLI エントリーポイント"""
    import argparse

    os.makedirs("tmp", exist_ok=True)

    parser = argparse.ArgumentParser(description="Gemini collaboration optimizer")
    parser.add_argument(
        "--evaluate", nargs=2,
        metavar=("DESCRIPTION", "FILES"),
        help="Evaluate task complexity (description, comma-separated files)"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show collaboration statistics"
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Generate recommendations report"
    )
    parser.add_argument(
        "--record", nargs=6,
        metavar=("PHASE", "DESCRIPTION", "METHOD", "SUCCESS", "TIME", "TOKENS"),
        help="Record execution result"
    )

    args = parser.parse_args()

    optimizer = GeminiCollaborationOptimizer()

    if args.evaluate:
        description, files_str = args.evaluate
        file_list = [f.strip() for f in files_str.split(",")]

        complexity = optimizer.evaluate_task_complexity(description, file_list)
        suggestion = optimizer.suggest_strategy(complexity)

        print("=== タスク複雑度評価 ===")
        print(f"複雑度レベル: {complexity.level}")
        print(f"信頼度: {complexity.confidence:.1%}")
        print(f"推奨戦略: {suggestion['action']}")
        print(f"理由: {suggestion['rationale']}")
        print(f"推定Token: {complexity.estimated_tokens}")
        print("\n根拠:")
        for reason in complexity.reasons:
            print(f"  - {reason}")

        # 結果保存
        result_path = "tmp/task_evaluation.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump({
                "complexity": asdict(complexity),
                "suggestion": suggestion
            }, f, indent=2, ensure_ascii=False)

        print(f"\n詳細結果保存: {result_path}")

    elif args.stats:
        stats = optimizer.get_statistics()

        print("=== Gemini協業統計 ===")
        print(json.dumps(stats, indent=2, ensure_ascii=False))

        stats_path = "tmp/collaboration_stats.json"
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        print(f"\n統計データ保存: {stats_path}")

    elif args.report:
        report = optimizer.generate_recommendations_report()

        print("=== 推奨事項レポート ===")
        for rec in report["recommendations"]:
            print(f"• {rec}")

        report_path = "tmp/collaboration_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\nレポート保存: {report_path}")

    elif args.record:
        phase, desc, method, success_str, time_str, tokens_str = args.record

        # 簡易的な複雑度評価（記録用）
        complexity = TaskComplexity(
            level="UNKNOWN",
            confidence=0.5,
            strategy=method,
            reasons=["Manual recording"],
            file_count=1,
            estimated_tokens=int(tokens_str)
        )

        optimizer.record_execution(
            phase_name=phase,
            task_description=desc,
            complexity=complexity,
            method_used=method,
            success=success_str.lower() == "true",
            execution_time=float(time_str),
            tokens_saved=int(tokens_str)
        )

        print(f"実行結果を記録しました: {phase}")

    else:
        print("No action specified. Use --help for usage information.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
