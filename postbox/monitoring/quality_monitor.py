#!/usr/bin/env python3
"""
品質監視システム
Claude ↔ Gemini協業でのリアルタイム品質監視・傾向分析
"""

import os
import json
import datetime
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

class AlertLevel(Enum):
    """アラートレベル"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class QualityAlert:
    """品質アラート"""
    timestamp: str
    level: AlertLevel
    category: str
    message: str
    details: Dict[str, Any]
    affected_files: List[str]
    ai_agent: str
    auto_resolved: bool = False

@dataclass
class QualityTrend:
    """品質傾向データ"""
    period: str  # daily, weekly, monthly
    average_score: float
    error_rate: float
    improvement_rate: float
    regression_count: int
    quality_gates_passed: int
    quality_gates_failed: int

class QualityMonitor:
    """品質監視システム"""

    def __init__(self, check_interval: int = 300):  # 5分間隔
        self.check_interval = check_interval
        self.monitoring_active = False
        self.alerts_path = Path("postbox/monitoring/quality_alerts.json")
        self.trends_path = Path("postbox/monitoring/quality_trends.json")
        self.config_path = Path("postbox/monitoring/monitor_config.json")

        # ディレクトリ作成
        for path in [self.alerts_path, self.trends_path, self.config_path]:
            path.parent.mkdir(parents=True, exist_ok=True)

        self.config = self._load_config()
        self.thresholds = self.config.get("thresholds", {})
        self.subscribers: List[Callable] = []

        print("📊 QualityMonitor 初期化完了")

    def start_monitoring(self) -> None:
        """監視開始"""
        if self.monitoring_active:
            print("⚠️ 監視は既に開始されています")
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        print(f"🚀 品質監視開始 (間隔: {self.check_interval}秒)")

    def stop_monitoring(self) -> None:
        """監視停止"""
        self.monitoring_active = False
        print("⏹️ 品質監視停止")

    def _monitor_loop(self) -> None:
        """監視ループ"""
        while self.monitoring_active:
            try:
                self._run_quality_check()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"⚠️ 監視エラー: {e}")
                time.sleep(30)  # エラー時は30秒待機

    def _run_quality_check(self) -> None:
        """品質チェック実行"""

        # 品質履歴データ読み込み
        history_path = Path("postbox/monitoring/quality_history.json")
        if not history_path.exists():
            return

        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)

            if not history:
                return

            # 最新データ分析
            latest = history[-1]
            recent = history[-5:] if len(history) >= 5 else history

            # アラート検出
            alerts = self._detect_alerts(latest, recent)

            # アラート保存・通知
            for alert in alerts:
                self._save_alert(alert)
                self._notify_subscribers(alert)

            # 傾向分析
            self._analyze_trends(history)

        except Exception as e:
            print(f"⚠️ 品質チェック実行エラー: {e}")

    def _detect_alerts(self, latest: Dict, recent: List[Dict]) -> List[QualityAlert]:
        """アラート検出"""
        alerts = []
        current_time = datetime.datetime.now().isoformat()

        # 1. 品質スコア急低下
        if len(recent) >= 3:
            scores = [r["metrics"]["overall_score"] for r in recent[-3:]]
            if scores[-1] < scores[0] - 0.2:  # 20%以上低下
                alerts.append(QualityAlert(
                    timestamp=current_time,
                    level=AlertLevel.WARNING,
                    category="quality_degradation",
                    message=f"品質スコア急低下: {scores[0]:.3f} → {scores[-1]:.3f}",
                    details={"score_trend": scores},
                    affected_files=latest.get("target_files", []),
                    ai_agent=latest.get("ai_agent", "unknown")
                ))

        # 2. エラー数閾値超過
        error_count = latest["metrics"]["error_count"]
        if error_count > self.thresholds.get("max_errors", 10):
            alerts.append(QualityAlert(
                timestamp=current_time,
                level=AlertLevel.ERROR,
                category="high_error_count",
                message=f"エラー数閾値超過: {error_count}件",
                details={"error_count": error_count, "threshold": self.thresholds.get("max_errors", 10)},
                affected_files=latest.get("target_files", []),
                ai_agent=latest.get("ai_agent", "unknown")
            ))

        # 3. 品質スコア最低基準割れ
        overall_score = latest["metrics"]["overall_score"]
        if overall_score < self.thresholds.get("minimum_score", 0.7):
            alerts.append(QualityAlert(
                timestamp=current_time,
                level=AlertLevel.CRITICAL,
                category="quality_below_minimum",
                message=f"品質スコア最低基準割れ: {overall_score:.3f}",
                details={"score": overall_score, "minimum": self.thresholds.get("minimum_score", 0.7)},
                affected_files=latest.get("target_files", []),
                ai_agent=latest.get("ai_agent", "unknown")
            ))

        # 4. 特定スコア異常
        scores = latest["metrics"]["scores"]
        for check_type, score in scores.items():
            threshold = self.thresholds.get(f"min_{check_type}", 0.5)
            if score < threshold:
                alerts.append(QualityAlert(
                    timestamp=current_time,
                    level=AlertLevel.WARNING,
                    category=f"{check_type}_low",
                    message=f"{check_type}スコア低下: {score:.3f}",
                    details={"check_type": check_type, "score": score, "threshold": threshold},
                    affected_files=latest.get("target_files", []),
                    ai_agent=latest.get("ai_agent", "unknown")
                ))

        # 5. 連続的な品質低下
        if len(recent) >= 5:
            recent_scores = [r["metrics"]["overall_score"] for r in recent]
            if all(recent_scores[i] >= recent_scores[i+1] for i in range(len(recent_scores)-1)):
                alerts.append(QualityAlert(
                    timestamp=current_time,
                    level=AlertLevel.ERROR,
                    category="continuous_degradation",
                    message="連続的な品質低下を検出",
                    details={"score_trend": recent_scores},
                    affected_files=latest.get("target_files", []),
                    ai_agent=latest.get("ai_agent", "unknown")
                ))

        return alerts

    def _analyze_trends(self, history: List[Dict]) -> None:
        """傾向分析"""

        now = datetime.datetime.now()

        # 日次傾向
        daily_trend = self._calculate_period_trend(history, 1)

        # 週次傾向
        weekly_trend = self._calculate_period_trend(history, 7)

        # 月次傾向
        monthly_trend = self._calculate_period_trend(history, 30)

        trends_data = {
            "last_updated": now.isoformat(),
            "daily": asdict(daily_trend) if daily_trend else None,
            "weekly": asdict(weekly_trend) if weekly_trend else None,
            "monthly": asdict(monthly_trend) if monthly_trend else None
        }

        # 傾向データ保存
        with open(self.trends_path, 'w', encoding='utf-8') as f:
            json.dump(trends_data, f, indent=2, ensure_ascii=False)

    def _calculate_period_trend(self, history: List[Dict], days: int) -> Optional[QualityTrend]:
        """期間別傾向計算"""

        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)

        # 期間内データフィルタリング
        period_data = []
        for entry in history:
            try:
                entry_time = datetime.datetime.fromisoformat(entry["timestamp"])
                if entry_time >= cutoff:
                    period_data.append(entry)
            except:
                continue

        if not period_data:
            return None

        # 統計計算
        scores = [d["metrics"]["overall_score"] for d in period_data]
        error_counts = [d["metrics"]["error_count"] for d in period_data]

        avg_score = sum(scores) / len(scores)
        error_rate = sum(error_counts) / len(error_counts)

        # 改善率計算 (前半と後半の比較)
        if len(scores) >= 4:
            mid = len(scores) // 2
            first_half_avg = sum(scores[:mid]) / mid
            second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
            improvement_rate = (second_half_avg - first_half_avg) / first_half_avg if first_half_avg > 0 else 0
        else:
            improvement_rate = 0

        # 回帰カウント
        regression_count = 0
        for i in range(1, len(scores)):
            if scores[i] < scores[i-1] - 0.05:  # 5%以上の低下
                regression_count += 1

        period_name = f"{days}日間"

        return QualityTrend(
            period=period_name,
            average_score=avg_score,
            error_rate=error_rate,
            improvement_rate=improvement_rate,
            regression_count=regression_count,
            quality_gates_passed=0,  # 実装時に追加
            quality_gates_failed=0   # 実装時に追加
        )

    def _save_alert(self, alert: QualityAlert) -> None:
        """アラート保存"""

        # 既存アラート読み込み
        alerts = []
        if self.alerts_path.exists():
            try:
                with open(self.alerts_path, 'r', encoding='utf-8') as f:
                    alerts = json.load(f)
            except:
                alerts = []

        # 新しいアラート追加
        alerts.append(asdict(alert))

        # サイズ制限（最新100件）
        if len(alerts) > 100:
            alerts = alerts[-100:]

        # 保存
        with open(self.alerts_path, 'w', encoding='utf-8') as f:
            json.dump(alerts, f, indent=2, ensure_ascii=False)

    def _notify_subscribers(self, alert: QualityAlert) -> None:
        """サブスクライバー通知"""
        for callback in self.subscribers:
            try:
                callback(alert)
            except Exception as e:
                print(f"⚠️ 通知エラー: {e}")

    def subscribe_to_alerts(self, callback: Callable[[QualityAlert], None]) -> None:
        """アラート購読"""
        self.subscribers.append(callback)
        print(f"📬 アラート購読追加: {len(self.subscribers)}件")

    def get_current_status(self) -> Dict[str, Any]:
        """現在のステータス取得"""

        # 最新品質データ
        history_path = Path("postbox/monitoring/quality_history.json")
        latest_quality = None

        if history_path.exists():
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                if history:
                    latest_quality = history[-1]
            except:
                pass

        # アラート統計
        alert_stats = self._get_alert_statistics()

        # 傾向データ
        trends = None
        if self.trends_path.exists():
            try:
                with open(self.trends_path, 'r', encoding='utf-8') as f:
                    trends = json.load(f)
            except:
                pass

        return {
            "monitoring_active": self.monitoring_active,
            "latest_quality": latest_quality,
            "alert_statistics": alert_stats,
            "trends": trends,
            "subscribers_count": len(self.subscribers),
            "last_check": datetime.datetime.now().isoformat()
        }

    def _get_alert_statistics(self) -> Dict[str, Any]:
        """アラート統計"""

        if not self.alerts_path.exists():
            return {"total": 0}

        try:
            with open(self.alerts_path, 'r', encoding='utf-8') as f:
                alerts = json.load(f)

            # 24時間以内のアラート
            cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
            recent_alerts = []

            for alert in alerts:
                try:
                    alert_time = datetime.datetime.fromisoformat(alert["timestamp"])
                    if alert_time >= cutoff:
                        recent_alerts.append(alert)
                except:
                    continue

            # レベル別統計
            level_counts = {}
            for alert in recent_alerts:
                level = alert.get("level", "unknown")
                level_counts[level] = level_counts.get(level, 0) + 1

            return {
                "total": len(alerts),
                "recent_24h": len(recent_alerts),
                "by_level": level_counts,
                "latest": alerts[-1] if alerts else None
            }

        except Exception as e:
            return {"error": f"統計取得エラー: {str(e)}"}

    def _load_config(self) -> Dict[str, Any]:
        """設定読み込み"""

        default_config = {
            "thresholds": {
                "minimum_score": 0.7,
                "max_errors": 10,
                "max_warnings": 20,
                "min_syntax": 0.9,
                "min_type_check": 0.8,
                "min_lint": 0.8,
                "min_format": 0.9,
                "min_security": 0.9,
                "min_performance": 0.7,
                "min_test": 0.5
            },
            "alerts": {
                "email_notifications": False,
                "slack_notifications": False,
                "console_output": True
            },
            "monitoring": {
                "check_interval": 300,
                "auto_resolve_alerts": True,
                "trend_analysis_enabled": True
            }
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except:
                pass
        else:
            # デフォルト設定保存
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)

        return default_config

def console_alert_handler(alert: QualityAlert) -> None:
    """コンソールアラートハンドラー"""
    level_icons = {
        AlertLevel.INFO: "ℹ️",
        AlertLevel.WARNING: "⚠️",
        AlertLevel.ERROR: "❌",
        AlertLevel.CRITICAL: "🚨"
    }

    icon = level_icons.get(alert.level, "📋")
    print(f"{icon} [{alert.level.value.upper()}] {alert.category}: {alert.message}")
    if alert.affected_files:
        print(f"    影響ファイル: {', '.join(alert.affected_files[:3])}")

def main():
    """テスト実行"""
    monitor = QualityMonitor(check_interval=10)  # 10秒間隔でテスト

    # コンソール通知設定
    monitor.subscribe_to_alerts(console_alert_handler)

    # 監視開始
    monitor.start_monitoring()

    print("📊 品質監視テスト開始 (10秒後に停止)")
    time.sleep(10)

    # ステータス確認
    status = monitor.get_current_status()
    print(f"\n📋 現在のステータス:")
    print(f"監視状態: {status['monitoring_active']}")
    print(f"サブスクライバー: {status['subscribers_count']}件")

    # 監視停止
    monitor.stop_monitoring()

if __name__ == "__main__":
    main()
