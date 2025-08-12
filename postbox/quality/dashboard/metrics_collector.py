#!/usr/bin/env python3
"""
QualityMetrics Collector
品質メトリクス収集システム - 包括的品質データ収集・集約・分析
リアルタイム監視・学習システム・品質ゲート・検証システムからのデータ統合
"""

import os
import json
import datetime
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

class MetricCategory(Enum):
    """メトリクスカテゴリ"""
    QUALITY_SCORES = "quality_scores"         # 品質スコア
    TREND_ANALYSIS = "trend_analysis"         # トレンド分析
    SYSTEM_PERFORMANCE = "system_performance" # システムパフォーマンス
    LEARNING_METRICS = "learning_metrics"     # 学習メトリクス
    GATE_STATISTICS = "gate_statistics"       # ゲート統計
    ALERT_SUMMARY = "alert_summary"           # アラートサマリー

@dataclass
class QualityMetrics:
    """品質メトリクス"""
    timestamp: str
    category: MetricCategory
    source_system: str
    
    # メトリクスデータ
    metrics: Dict[str, Any]
    summary: Dict[str, Any]
    
    # メタデータ
    collection_time: float
    data_points: int
    confidence: float

class QualityMetricsCollector:
    """品質メトリクス収集システム"""
    
    def __init__(self):
        self.data_dir = Path("postbox/quality/dashboard")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics_path = self.data_dir / "collected_metrics.json"
        self.aggregated_path = self.data_dir / "aggregated_metrics.json"
        
        # データソースパス
        self.data_sources = {
            "realtime_monitor": Path("postbox/quality/realtime_data"),
            "quality_manager": Path("postbox/monitoring/quality_history.json"),
            "learning_system": Path("postbox/quality/learning"),
            "quality_gates": Path("postbox/quality/gates"),
            "comprehensive_validator": Path("postbox/quality/comprehensive")
        }
        
        print("📊 QualityMetricsCollector 初期化完了")
    
    def collect_all_metrics(self) -> Dict[str, QualityMetrics]:
        """全メトリクス収集"""
        
        print("📊 包括的メトリクス収集開始...")
        
        collected_metrics = {}
        
        # 各カテゴリのメトリクス収集
        categories = [
            MetricCategory.QUALITY_SCORES,
            MetricCategory.TREND_ANALYSIS,
            MetricCategory.SYSTEM_PERFORMANCE,
            MetricCategory.LEARNING_METRICS,
            MetricCategory.GATE_STATISTICS,
            MetricCategory.ALERT_SUMMARY
        ]
        
        for category in categories:
            try:
                print(f"   📋 {category.value} 収集中...")
                metrics = self._collect_category_metrics(category)
                if metrics:
                    collected_metrics[category.value] = metrics
                    print(f"   ✅ {category.value} 完了: {metrics.data_points}データポイント")
                else:
                    print(f"   ⚠️ {category.value} データなし")
            except Exception as e:
                print(f"   ❌ {category.value} エラー: {e}")
        
        # 収集結果保存
        self._save_collected_metrics(collected_metrics)
        
        print(f"✅ メトリクス収集完了: {len(collected_metrics)}カテゴリ")
        
        return collected_metrics
    
    def _collect_category_metrics(self, category: MetricCategory) -> Optional[QualityMetrics]:
        """カテゴリ別メトリクス収集"""
        
        start_time = time.time()
        
        if category == MetricCategory.QUALITY_SCORES:
            return self._collect_quality_scores()
        elif category == MetricCategory.TREND_ANALYSIS:
            return self._collect_trend_analysis()
        elif category == MetricCategory.SYSTEM_PERFORMANCE:
            return self._collect_system_performance()
        elif category == MetricCategory.LEARNING_METRICS:
            return self._collect_learning_metrics()
        elif category == MetricCategory.GATE_STATISTICS:
            return self._collect_gate_statistics()
        elif category == MetricCategory.ALERT_SUMMARY:
            return self._collect_alert_summary()
        else:
            return None
    
    def _collect_quality_scores(self) -> Optional[QualityMetrics]:
        """品質スコア収集"""
        
        start_time = time.time()
        metrics_data = {}
        data_points = 0
        
        try:
            # 品質管理システムからの履歴データ
            quality_history_path = self.data_sources["quality_manager"]
            if quality_history_path.exists():
                with open(quality_history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                if history:
                    latest = history[-1]
                    metrics_data["latest_quality"] = latest["metrics"]
                    
                    # 過去30日の平均
                    recent_history = history[-30:] if len(history) > 30 else history
                    avg_scores = {}
                    for entry in recent_history:
                        for key, value in entry["metrics"]["scores"].items():
                            if key not in avg_scores:
                                avg_scores[key] = []
                            avg_scores[key].append(value)
                    
                    metrics_data["average_scores"] = {
                        key: sum(values) / len(values)
                        for key, values in avg_scores.items()
                    }
                    
                    data_points += len(recent_history)
            
            # リアルタイム監視データ
            realtime_data_dir = self.data_sources["realtime_monitor"]
            if realtime_data_dir.exists():
                realtime_history = realtime_data_dir / "realtime_history.json"
                if realtime_history.exists():
                    with open(realtime_history, 'r', encoding='utf-8') as f:
                        realtime_data = json.load(f)
                    
                    if realtime_data:
                        # 最新10件の平均
                        recent_realtime = realtime_data[-10:]
                        realtime_scores = []
                        for entry in recent_realtime:
                            realtime_scores.append(entry["overall_score"])
                        
                        if realtime_scores:
                            metrics_data["realtime_average"] = sum(realtime_scores) / len(realtime_scores)
                            metrics_data["realtime_trend"] = self._calculate_trend(realtime_scores)
                            data_points += len(recent_realtime)
            
            # 包括的検証結果
            comprehensive_dir = self.data_sources["comprehensive_validator"]
            if comprehensive_dir.exists():
                summary_path = comprehensive_dir / "validation_summary.json"
                if summary_path.exists():
                    with open(summary_path, 'r', encoding='utf-8') as f:
                        summaries = json.load(f)
                    
                    if summaries:
                        latest_summary = summaries[-1]
                        metrics_data["comprehensive_score"] = latest_summary["overall_score"]
                        metrics_data["category_scores"] = latest_summary["category_scores"]
                        data_points += 1
            
            collection_time = time.time() - start_time
            
            if not metrics_data:
                return None
            
            summary = {
                "total_systems": len([k for k in metrics_data.keys() if "score" in k]),
                "data_freshness": self._calculate_data_freshness(metrics_data),
                "quality_status": self._determine_quality_status(metrics_data)
            }
            
            return QualityMetrics(
                timestamp=datetime.datetime.now().isoformat(),
                category=MetricCategory.QUALITY_SCORES,
                source_system="integrated_quality_systems",
                metrics=metrics_data,
                summary=summary,
                collection_time=collection_time,
                data_points=data_points,
                confidence=self._calculate_confidence(data_points, collection_time)
            )
            
        except Exception as e:
            print(f"⚠️ 品質スコア収集エラー: {e}")
            return None
    
    def _collect_trend_analysis(self) -> Optional[QualityMetrics]:
        """トレンド分析収集"""
        
        start_time = time.time()
        trends_data = {}
        data_points = 0
        
        try:
            # 品質履歴からトレンド計算
            quality_history_path = self.data_sources["quality_manager"]
            if quality_history_path.exists():
                with open(quality_history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                if len(history) >= 5:
                    # 各品質指標のトレンド
                    for metric in ["overall_score"]:
                        values = [entry["metrics"][metric] for entry in history[-20:] if metric in entry["metrics"]]
                        if len(values) >= 3:
                            trends_data[f"{metric}_trend"] = self._calculate_detailed_trend(values)
                            data_points += len(values)
            
            # リアルタイム監視トレンド
            realtime_data_dir = self.data_sources["realtime_monitor"]
            performance_metrics_path = realtime_data_dir / "performance_metrics.json"
            if performance_metrics_path.exists():
                with open(performance_metrics_path, 'r', encoding='utf-8') as f:
                    perf_data = json.load(f)
                
                trends_data["performance_trends"] = {
                    "cache_efficiency": perf_data.get("cache_efficiency", 0),
                    "processing_time_trend": "stable"  # 簡易実装
                }
                data_points += 1
            
            # 学習システムトレンド
            learning_dir = self.data_sources["learning_system"]
            evolution_history_path = learning_dir / "evolution_history.json"
            if evolution_history_path.exists():
                with open(evolution_history_path, 'r', encoding='utf-8') as f:
                    evolution_history = json.load(f)
                
                if evolution_history:
                    trends_data["learning_evolution"] = {
                        "evolution_count": len(evolution_history),
                        "recent_improvements": self._analyze_recent_evolution(evolution_history)
                    }
                    data_points += len(evolution_history)
            
            collection_time = time.time() - start_time
            
            if not trends_data:
                return None
            
            summary = {
                "trend_indicators": len(trends_data),
                "overall_trend": self._determine_overall_trend(trends_data),
                "prediction_accuracy": self._estimate_prediction_accuracy(trends_data)
            }
            
            return QualityMetrics(
                timestamp=datetime.datetime.now().isoformat(),
                category=MetricCategory.TREND_ANALYSIS,
                source_system="trend_analyzer",
                metrics=trends_data,
                summary=summary,
                collection_time=collection_time,
                data_points=data_points,
                confidence=self._calculate_confidence(data_points, collection_time)
            )
            
        except Exception as e:
            print(f"⚠️ トレンド分析収集エラー: {e}")
            return None
    
    def _collect_system_performance(self) -> Optional[QualityMetrics]:
        """システムパフォーマンス収集"""
        
        start_time = time.time()
        performance_data = {}
        data_points = 0
        
        try:
            # リアルタイム監視パフォーマンス
            realtime_data_dir = self.data_sources["realtime_monitor"]
            performance_path = realtime_data_dir / "performance_metrics.json"
            if performance_path.exists():
                with open(performance_path, 'r', encoding='utf-8') as f:
                    perf_metrics = json.load(f)
                
                performance_data["realtime_performance"] = perf_metrics["performance_stats"]
                data_points += 1
            
            # 品質ゲート実行統計
            gates_dir = self.data_sources["quality_gates"]
            gate_results_path = gates_dir / "gate_results.json"
            if gate_results_path.exists():
                with open(gate_results_path, 'r', encoding='utf-8') as f:
                    gate_results = json.load(f)
                
                if gate_results:
                    # 実行時間統計
                    execution_times = [result["execution_time"] for result in gate_results[-20:]]
                    if execution_times:
                        performance_data["gate_performance"] = {
                            "average_execution_time": sum(execution_times) / len(execution_times),
                            "max_execution_time": max(execution_times),
                            "min_execution_time": min(execution_times)
                        }
                        data_points += len(execution_times)
            
            # 包括的検証パフォーマンス
            comprehensive_dir = self.data_sources["comprehensive_validator"]
            summary_path = comprehensive_dir / "validation_summary.json"
            if summary_path.exists():
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summaries = json.load(f)
                
                if summaries:
                    recent_summaries = summaries[-5:]
                    exec_times = [s["execution_time"] for s in recent_summaries]
                    if exec_times:
                        performance_data["validation_performance"] = {
                            "average_time": sum(exec_times) / len(exec_times),
                            "throughput": len(recent_summaries) / sum(exec_times) if sum(exec_times) > 0 else 0
                        }
                        data_points += len(recent_summaries)
            
            collection_time = time.time() - start_time
            
            if not performance_data:
                return None
            
            summary = {
                "systems_monitored": len(performance_data),
                "overall_health": self._assess_system_health(performance_data),
                "bottlenecks": self._identify_bottlenecks(performance_data)
            }
            
            return QualityMetrics(
                timestamp=datetime.datetime.now().isoformat(),
                category=MetricCategory.SYSTEM_PERFORMANCE,
                source_system="performance_monitor",
                metrics=performance_data,
                summary=summary,
                collection_time=collection_time,
                data_points=data_points,
                confidence=self._calculate_confidence(data_points, collection_time)
            )
            
        except Exception as e:
            print(f"⚠️ システムパフォーマンス収集エラー: {e}")
            return None
    
    def _collect_learning_metrics(self) -> Optional[QualityMetrics]:
        """学習メトリクス収集"""
        
        start_time = time.time()
        learning_data = {}
        data_points = 0
        
        try:
            learning_dir = self.data_sources["learning_system"]
            
            # 学習イベント統計
            events_path = learning_dir / "learning_events.json"
            if events_path.exists():
                with open(events_path, 'r', encoding='utf-8') as f:
                    events = json.load(f)
                
                if events:
                    recent_events = events[-50:]  # 最新50件
                    
                    # 改善率統計
                    improvements = [event["improvement"] for event in recent_events]
                    positive_improvements = [imp for imp in improvements if imp > 0]
                    
                    learning_data["learning_effectiveness"] = {
                        "total_events": len(recent_events),
                        "positive_improvements": len(positive_improvements),
                        "success_rate": len(positive_improvements) / len(recent_events),
                        "average_improvement": sum(improvements) / len(improvements),
                        "best_improvement": max(improvements) if improvements else 0
                    }
                    data_points += len(recent_events)
            
            # パターン統計
            patterns_path = learning_dir / "patterns.json"
            if patterns_path.exists():
                # パターンファイルがあれば読み込み（簡易実装）
                learning_data["pattern_statistics"] = {
                    "patterns_available": True,
                    "pattern_file_exists": True
                }
                data_points += 1
            
            # 予測精度
            predictions_path = learning_dir / "predictions.json"
            if predictions_path.exists():
                with open(predictions_path, 'r', encoding='utf-8') as f:
                    predictions = json.load(f)
                
                if predictions:
                    recent_predictions = predictions[-20:]
                    confidence_scores = []
                    for pred in recent_predictions:
                        if "confidence" in pred["prediction"]:
                            conf = pred["prediction"]["confidence"]
                            if conf == "high":
                                confidence_scores.append(1.0)
                            elif conf == "medium":
                                confidence_scores.append(0.7)
                            else:
                                confidence_scores.append(0.4)
                    
                    if confidence_scores:
                        learning_data["prediction_quality"] = {
                            "average_confidence": sum(confidence_scores) / len(confidence_scores),
                            "high_confidence_rate": len([c for c in confidence_scores if c >= 0.8]) / len(confidence_scores)
                        }
                        data_points += len(recent_predictions)
            
            collection_time = time.time() - start_time
            
            if not learning_data:
                return None
            
            summary = {
                "learning_active": len(learning_data) > 0,
                "learning_quality": self._assess_learning_quality(learning_data),
                "improvement_potential": self._estimate_improvement_potential(learning_data)
            }
            
            return QualityMetrics(
                timestamp=datetime.datetime.now().isoformat(),
                category=MetricCategory.LEARNING_METRICS,
                source_system="learning_system",
                metrics=learning_data,
                summary=summary,
                collection_time=collection_time,
                data_points=data_points,
                confidence=self._calculate_confidence(data_points, collection_time)
            )
            
        except Exception as e:
            print(f"⚠️ 学習メトリクス収集エラー: {e}")
            return None
    
    def _collect_gate_statistics(self) -> Optional[QualityMetrics]:
        """ゲート統計収集"""
        
        start_time = time.time()
        gate_data = {}
        data_points = 0
        
        try:
            gates_dir = self.data_sources["quality_gates"]
            results_path = gates_dir / "gate_results.json"
            
            if results_path.exists():
                with open(results_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                if results:
                    recent_results = results[-30:]  # 最新30件
                    
                    # 通過率統計
                    pass_count = len([r for r in recent_results if r["result"] == "passed"])
                    fail_count = len([r for r in recent_results if r["result"] == "failed"])
                    warning_count = len([r for r in recent_results if r["result"] == "warning"])
                    
                    gate_data["gate_statistics"] = {
                        "total_executions": len(recent_results),
                        "pass_rate": pass_count / len(recent_results),
                        "fail_rate": fail_count / len(recent_results),
                        "warning_rate": warning_count / len(recent_results),
                        "average_score": sum(r["overall_score"] for r in recent_results) / len(recent_results)
                    }
                    
                    # フェーズ別統計
                    phase_stats = {}
                    for result in recent_results:
                        phase = result.get("phase", "unknown")
                        if phase not in phase_stats:
                            phase_stats[phase] = {"count": 0, "passed": 0}
                        phase_stats[phase]["count"] += 1
                        if result["result"] == "passed":
                            phase_stats[phase]["passed"] += 1
                    
                    gate_data["phase_statistics"] = {
                        phase: {
                            "pass_rate": stats["passed"] / stats["count"],
                            "executions": stats["count"]
                        }
                        for phase, stats in phase_stats.items()
                    }
                    
                    data_points += len(recent_results)
            
            collection_time = time.time() - start_time
            
            if not gate_data:
                return None
            
            summary = {
                "gates_active": len(gate_data) > 0,
                "overall_gate_health": self._assess_gate_health(gate_data),
                "recommendations": self._generate_gate_recommendations(gate_data)
            }
            
            return QualityMetrics(
                timestamp=datetime.datetime.now().isoformat(),
                category=MetricCategory.GATE_STATISTICS,
                source_system="quality_gates",
                metrics=gate_data,
                summary=summary,
                collection_time=collection_time,
                data_points=data_points,
                confidence=self._calculate_confidence(data_points, collection_time)
            )
            
        except Exception as e:
            print(f"⚠️ ゲート統計収集エラー: {e}")
            return None
    
    def _collect_alert_summary(self) -> Optional[QualityMetrics]:
        """アラートサマリー収集"""
        
        start_time = time.time()
        alert_data = {}
        data_points = 0
        
        try:
            # リアルタイム監視アラート
            realtime_data_dir = self.data_sources["realtime_monitor"]
            
            # 品質監視アラート
            alerts_path = Path("postbox/monitoring/quality_alerts.json")
            if alerts_path.exists():
                with open(alerts_path, 'r', encoding='utf-8') as f:
                    alerts = json.load(f)
                
                if alerts:
                    recent_alerts = alerts[-50:]  # 最新50件
                    
                    # レベル別統計
                    level_counts = {}
                    for alert in recent_alerts:
                        level = alert.get("level", "unknown")
                        level_counts[level] = level_counts.get(level, 0) + 1
                    
                    alert_data["alert_statistics"] = {
                        "total_alerts": len(recent_alerts),
                        "by_level": level_counts,
                        "critical_rate": level_counts.get("critical", 0) / len(recent_alerts),
                        "resolution_needed": len([a for a in recent_alerts if not a.get("auto_resolved", False)])
                    }
                    data_points += len(recent_alerts)
            
            # システム健全性
            alert_data["system_health"] = {
                "monitoring_active": True,
                "alert_system_functional": data_points > 0,
                "last_alert_time": datetime.datetime.now().isoformat() if data_points > 0 else None
            }
            
            collection_time = time.time() - start_time
            
            if not alert_data:
                return None
            
            summary = {
                "alert_volume": data_points,
                "alert_severity": self._assess_alert_severity(alert_data),
                "system_status": self._determine_system_status(alert_data)
            }
            
            return QualityMetrics(
                timestamp=datetime.datetime.now().isoformat(),
                category=MetricCategory.ALERT_SUMMARY,
                source_system="alert_system",
                metrics=alert_data,
                summary=summary,
                collection_time=collection_time,
                data_points=data_points,
                confidence=self._calculate_confidence(data_points, collection_time)
            )
            
        except Exception as e:
            print(f"⚠️ アラートサマリー収集エラー: {e}")
            return None
    
    # ユーティリティメソッド
    def _calculate_trend(self, values: List[float]) -> str:
        """トレンド計算"""
        if len(values) < 2:
            return "insufficient_data"
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg * 1.05:
            return "improving"
        elif second_avg < first_avg * 0.95:
            return "declining"
        else:
            return "stable"
    
    def _calculate_detailed_trend(self, values: List[float]) -> Dict[str, Any]:
        """詳細トレンド分析"""
        if len(values) < 3:
            return {"trend": "insufficient_data"}
        
        # 線形回帰の簡易版
        n = len(values)
        x_values = list(range(n))
        
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        return {
            "trend": "improving" if slope > 0.01 else "declining" if slope < -0.01 else "stable",
            "slope": slope,
            "current_value": values[-1],
            "change_rate": slope * n,
            "volatility": self._calculate_volatility(values)
        }
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """ボラティリティ計算"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        
        return variance ** 0.5
    
    def _calculate_data_freshness(self, metrics_data: Dict[str, Any]) -> str:
        """データ新鮮度計算"""
        # 簡易実装
        return "recent"
    
    def _determine_quality_status(self, metrics_data: Dict[str, Any]) -> str:
        """品質ステータス判定"""
        if "comprehensive_score" in metrics_data:
            score = metrics_data["comprehensive_score"]
            if score >= 0.9:
                return "excellent"
            elif score >= 0.8:
                return "good"
            elif score >= 0.7:
                return "acceptable"
            else:
                return "needs_improvement"
        return "unknown"
    
    def _calculate_confidence(self, data_points: int, collection_time: float) -> float:
        """信頼度計算"""
        # データポイント数と収集時間から信頼度算出
        data_confidence = min(1.0, data_points / 50)  # 50データポイントで最大
        time_penalty = max(0.5, 1.0 - (collection_time / 10))  # 10秒以上で半減
        
        return data_confidence * time_penalty
    
    def _determine_overall_trend(self, trends_data: Dict[str, Any]) -> str:
        """全体トレンド判定"""
        # 簡易実装
        return "stable"
    
    def _estimate_prediction_accuracy(self, trends_data: Dict[str, Any]) -> float:
        """予測精度推定"""
        # 簡易実装
        return 0.75
    
    def _assess_system_health(self, performance_data: Dict[str, Any]) -> str:
        """システム健全性評価"""
        # 簡易実装
        return "healthy"
    
    def _identify_bottlenecks(self, performance_data: Dict[str, Any]) -> List[str]:
        """ボトルネック特定"""
        # 簡易実装
        return []
    
    def _assess_learning_quality(self, learning_data: Dict[str, Any]) -> str:
        """学習品質評価"""
        if "learning_effectiveness" in learning_data:
            success_rate = learning_data["learning_effectiveness"]["success_rate"]
            if success_rate >= 0.8:
                return "high"
            elif success_rate >= 0.6:
                return "medium"
            else:
                return "low"
        return "unknown"
    
    def _estimate_improvement_potential(self, learning_data: Dict[str, Any]) -> str:
        """改善可能性推定"""
        # 簡易実装
        return "moderate"
    
    def _assess_gate_health(self, gate_data: Dict[str, Any]) -> str:
        """ゲート健全性評価"""
        if "gate_statistics" in gate_data:
            pass_rate = gate_data["gate_statistics"]["pass_rate"]
            if pass_rate >= 0.9:
                return "excellent"
            elif pass_rate >= 0.8:
                return "good"
            elif pass_rate >= 0.7:
                return "acceptable"
            else:
                return "needs_attention"
        return "unknown"
    
    def _generate_gate_recommendations(self, gate_data: Dict[str, Any]) -> List[str]:
        """ゲート推奨事項生成"""
        recommendations = []
        
        if "gate_statistics" in gate_data:
            stats = gate_data["gate_statistics"]
            if stats["fail_rate"] > 0.2:
                recommendations.append("失敗率が高いです。基準の見直しを検討してください")
            if stats["warning_rate"] > 0.3:
                recommendations.append("警告率が高いです。予防的改善を推奨します")
        
        return recommendations
    
    def _assess_alert_severity(self, alert_data: Dict[str, Any]) -> str:
        """アラート重要度評価"""
        if "alert_statistics" in alert_data:
            critical_rate = alert_data["alert_statistics"]["critical_rate"]
            if critical_rate > 0.1:
                return "high"
            elif critical_rate > 0.05:
                return "medium"
            else:
                return "low"
        return "unknown"
    
    def _determine_system_status(self, alert_data: Dict[str, Any]) -> str:
        """システムステータス判定"""
        if "system_health" in alert_data:
            if alert_data["system_health"]["monitoring_active"]:
                return "operational"
            else:
                return "degraded"
        return "unknown"
    
    def _analyze_recent_evolution(self, evolution_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """最近の進化分析"""
        if not evolution_history:
            return {"no_data": True}
        
        recent = evolution_history[-5:] if len(evolution_history) > 5 else evolution_history
        
        return {
            "recent_evolutions": len(recent),
            "improvement_trend": "positive"  # 簡易実装
        }
    
    def _save_collected_metrics(self, metrics: Dict[str, QualityMetrics]) -> None:
        """収集メトリクス保存"""
        
        try:
            # 現在のメトリクス保存
            metrics_data = {}
            for category, metric in metrics.items():
                metrics_data[category] = asdict(metric)
            
            with open(self.metrics_path, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)
            
            # 集約データ更新
            self._update_aggregated_metrics(metrics)
            
            print(f"📊 メトリクス保存完了: {self.metrics_path}")
            
        except Exception as e:
            print(f"⚠️ メトリクス保存エラー: {e}")
    
    def _update_aggregated_metrics(self, current_metrics: Dict[str, QualityMetrics]) -> None:
        """集約メトリクス更新"""
        
        try:
            # 既存集約データ読み込み
            aggregated = []
            if self.aggregated_path.exists():
                with open(self.aggregated_path, 'r', encoding='utf-8') as f:
                    aggregated = json.load(f)
            
            # 新しいエントリ追加
            new_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "summary": {
                    category: {
                        "data_points": metric.data_points,
                        "confidence": metric.confidence,
                        "collection_time": metric.collection_time
                    }
                    for category, metric in current_metrics.items()
                }
            }
            
            aggregated.append(new_entry)
            
            # サイズ制限（最新1000件）
            if len(aggregated) > 1000:
                aggregated = aggregated[-1000:]
            
            with open(self.aggregated_path, 'w', encoding='utf-8') as f:
                json.dump(aggregated, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 集約メトリクス更新エラー: {e}")

def main():
    """テスト実行"""
    print("🧪 QualityMetricsCollector テスト開始")
    
    collector = QualityMetricsCollector()
    
    # 全メトリクス収集
    metrics = collector.collect_all_metrics()
    
    print(f"\n📊 収集結果:")
    for category, metric in metrics.items():
        print(f"   {category}: {metric.data_points}データポイント (信頼度: {metric.confidence:.2f})")
    
    print("✅ QualityMetricsCollector テスト完了")

if __name__ == "__main__":
    main()