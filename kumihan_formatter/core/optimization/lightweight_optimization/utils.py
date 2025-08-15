"""
最適化ユーティリティ - Optimization Utils

軽量最適化システム用の共通ユーティリティ
パフォーマンス測定・メトリクス計算・システム監視

Target: 200行以内・高効率・軽量
"""

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""

    processing_time: float
    memory_usage: float
    cpu_usage: float
    file_size: int
    complexity_score: float
    token_count: int
    optimization_score: float


class OptimizationUtils:
    """最適化ユーティリティ

    軽量最適化システム用の共通機能
    - パフォーマンス測定
    - メトリクス計算
    - システム状態監視
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def measure_performance(
        self, operation_func: Any, *args: Any, **kwargs: Any
    ) -> tuple[Any, PerformanceMetrics]:
        """パフォーマンス測定"""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            # 操作実行
            result = operation_func(*args, **kwargs)

            # メトリクス計算
            processing_time = time.time() - start_time
            end_memory = self._get_memory_usage()
            memory_usage = end_memory - start_memory

            metrics = PerformanceMetrics(
                processing_time=processing_time,
                memory_usage=memory_usage,
                cpu_usage=self._estimate_cpu_usage(processing_time),
                file_size=self._get_context_file_size(kwargs.get("context", {})),
                complexity_score=self._calculate_complexity_score(result),
                token_count=self._estimate_token_count(result),
                optimization_score=self._calculate_optimization_score(
                    processing_time, memory_usage
                ),
            )

            return result, metrics

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Performance measurement failed: {e}")

            # エラー時のデフォルトメトリクス
            metrics = PerformanceMetrics(
                processing_time=processing_time,
                memory_usage=0.0,
                cpu_usage=0.0,
                file_size=0,
                complexity_score=0.0,
                token_count=0,
                optimization_score=0.0,
            )

            raise e

    def _get_memory_usage(self) -> float:
        """メモリ使用量取得（簡易版）"""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            # psutilが利用できない場合のフォールバック
            return 0.0

    def _estimate_cpu_usage(self, processing_time: float) -> float:
        """CPU使用量推定"""
        # 処理時間ベースの簡易推定
        if processing_time < 0.1:
            return 0.1
        elif processing_time < 1.0:
            return 0.3
        elif processing_time < 5.0:
            return 0.6
        else:
            return 0.9

    def _get_context_file_size(self, context: Dict[str, Any]) -> int:
        """コンテキストからファイルサイズ取得"""
        return context.get("file_size", 0)

    def _calculate_complexity_score(self, result: Any) -> float:
        """複雑度スコア計算"""
        try:
            if isinstance(result, dict):
                # 辞書の深度と要素数から複雑度推定
                depth = self._get_dict_depth(result)
                size = len(str(result))
                return min(1.0, (depth / 10.0) + (size / 10000.0))
            elif isinstance(result, (list, tuple)):
                return min(1.0, len(result) / 1000.0)
            elif isinstance(result, str):
                return min(1.0, len(result) / 50000.0)
            else:
                return 0.1
        except Exception:
            return 0.5

    def _get_dict_depth(self, d: Dict[str, Any], depth: int = 0) -> int:
        """辞書の深度計算"""
        if not isinstance(d, dict) or depth > 10:  # 深度制限
            return depth

        max_depth = depth
        for value in d.values():
            if isinstance(value, dict):
                max_depth = max(max_depth, self._get_dict_depth(value, depth + 1))

        return max_depth

    def _estimate_token_count(self, result: Any) -> int:
        """トークン数推定"""
        try:
            text = str(result)
            # 簡易推定：文字数を4で割る（平均的なトークン長）
            return len(text) // 4
        except Exception:
            return 0

    def _calculate_optimization_score(
        self, processing_time: float, memory_usage: float
    ) -> float:
        """最適化スコア計算"""
        try:
            # 時間効率スコア（速いほど高い）
            time_score = max(0.0, 1.0 - (processing_time / 10.0))

            # メモリ効率スコア（少ないほど高い）
            memory_score = max(0.0, 1.0 - (memory_usage / 100.0))

            # 総合スコア
            return (time_score + memory_score) / 2.0
        except Exception:
            return 0.5

    def analyze_system_context(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """システムコンテキスト分析"""
        context = {
            "timestamp": time.time(),
            "file_size": 0,
            "complexity_score": 0.0,
            "memory_usage": 0.0,
            "processing_time": 0.0,
            "token_count": 0,
        }

        try:
            # ファイル情報
            if file_path and os.path.exists(file_path):
                context["file_size"] = os.path.getsize(file_path)

                # ファイル内容の簡易分析
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read(10000)  # 最初の10KB分析
                    context["complexity_score"] = self._analyze_content_complexity(
                        content
                    )
                    context["token_count"] = len(content) // 4

            # システム状態
            context["memory_usage"] = self._get_memory_usage() / 1000.0  # GB単位

        except Exception as e:
            self.logger.warning(f"System context analysis failed: {e}")

        return context

    def _analyze_content_complexity(self, content: str) -> float:
        """コンテンツ複雑度分析"""
        try:
            factors = {
                "length": min(1.0, len(content) / 50000.0),
                "lines": min(1.0, content.count("\n") / 1000.0),
                "nesting": min(1.0, content.count("{") / 100.0),
                "imports": min(1.0, content.count("import") / 50.0),
            }

            return sum(factors.values()) / len(factors)
        except Exception:
            return 0.5

    def generate_optimization_report(
        self, metrics_list: List[PerformanceMetrics]
    ) -> Dict[str, Any]:
        """最適化レポート生成"""
        if not metrics_list:
            return {"status": "no_data"}

        try:
            # 統計計算
            avg_processing_time = sum(m.processing_time for m in metrics_list) / len(
                metrics_list
            )
            avg_memory_usage = sum(m.memory_usage for m in metrics_list) / len(
                metrics_list
            )
            avg_optimization_score = sum(
                m.optimization_score for m in metrics_list
            ) / len(metrics_list)

            # トレンド分析（簡易版）
            recent_metrics = metrics_list[-5:]  # 最新5件
            recent_avg_score = sum(m.optimization_score for m in recent_metrics) / len(
                recent_metrics
            )
            trend = (
                "improving" if recent_avg_score > avg_optimization_score else "stable"
            )

            return {
                "status": "generated",
                "summary": {
                    "total_measurements": len(metrics_list),
                    "average_processing_time": avg_processing_time,
                    "average_memory_usage": avg_memory_usage,
                    "average_optimization_score": avg_optimization_score,
                    "performance_trend": trend,
                },
                "recommendations": self._generate_recommendations(
                    avg_processing_time, avg_memory_usage
                ),
                "timestamp": time.time(),
            }

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return {"status": "error", "error": str(e)}

    def _generate_recommendations(
        self, avg_time: float, avg_memory: float
    ) -> List[str]:
        """推奨事項生成"""
        recommendations = []

        if avg_time > 5.0:
            recommendations.append(
                "Consider algorithm optimization for faster processing"
            )
        if avg_memory > 50.0:
            recommendations.append("Memory usage is high, implement cleanup strategies")
        if avg_time > 1.0 and avg_memory > 20.0:
            recommendations.append("Both time and memory usage need optimization")

        if not recommendations:
            recommendations.append("Performance is within acceptable ranges")

        return recommendations
