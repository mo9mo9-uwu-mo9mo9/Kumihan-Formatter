"""
システムヘルスチェックシステム - 統合インターフェース

巨大ファイル分割完了（Issue: 909行→2ファイル分離）
=======================================================

分割結果:
- health_types.py: 基本型・データクラス（51行）
- health_checker.py: 統合インターフェース（本ファイル, 450行程度）

合計削減効果: 909行 → 501行（408行削減 + 責任分離達成）

システム全体のヘルス状態を監視し、問題の早期発見と対応を支援するヘルスチェックシステム
"""

import json
import os
import platform
import socket
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger

# 分離されたコンポーネントのインポート（後方互換性完全確保）
from .health_types import AlertSeverity, HealthAlert, HealthCheckResult, HealthStatus


class HealthChecker:
    """システムヘルスチェック管理クラス
    
    システム全体のヘルス状態を監視し、問題の早期発見と対応を支援します。
    """

    def __init__(
        self,
        check_interval: int = 60,
        alert_threshold: int = 3,
        enable_auto_recovery: bool = True,
        log_directory: Optional[Path] = None,
    ):
        """ヘルスチェッカーを初期化

        Args:
            check_interval: チェック間隔（秒）
            alert_threshold: アラート閾値
            enable_auto_recovery: 自動復旧機能の有効化
            log_directory: ログディレクトリ
        """
        self.check_interval = check_interval
        self.alert_threshold = alert_threshold
        self.enable_auto_recovery = enable_auto_recovery
        self.log_directory = log_directory or Path("tmp/health_logs")
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # ログ設定
        self.logger = get_logger(self.__class__.__name__)
        
        # 状態管理
        self._checks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self._results: Dict[str, HealthCheckResult] = {}
        self._alerts: Dict[str, HealthAlert] = {}
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # デフォルトヘルスチェック登録
        self._register_default_checks()

    def register_check(self, name: str, check_func: Callable[[], HealthCheckResult]) -> None:
        """ヘルスチェック関数を登録

        Args:
            name: チェック名
            check_func: チェック関数
        """
        with self._lock:
            self._checks[name] = check_func
            self.logger.info(f"Health check '{name}' registered")

    def unregister_check(self, name: str) -> bool:
        """ヘルスチェック関数を登録解除

        Args:
            name: チェック名

        Returns:
            解除成功した場合True
        """
        with self._lock:
            if name in self._checks:
                del self._checks[name]
                if name in self._results:
                    del self._results[name]
                self.logger.info(f"Health check '{name}' unregistered")
                return True
            return False

    def run_single_check(self, name: str) -> Optional[HealthCheckResult]:
        """単一ヘルスチェックを実行

        Args:
            name: チェック名

        Returns:
            チェック結果（存在しない場合はNone）
        """
        with self._lock:
            if name not in self._checks:
                return None
            
            check_func = self._checks[name]
            
        try:
            start_time = time.time()
            result = check_func()
            duration_ms = (time.time() - start_time) * 1000
            
            # 実行時間を更新
            result.duration_ms = duration_ms
            result.timestamp = time.time()
            
            with self._lock:
                self._results[name] = result
                
            self._process_check_result(result)
            return result
            
        except Exception as e:
            error_result = HealthCheckResult(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Check execution failed: {str(e)}",
                timestamp=time.time(),
                duration_ms=0,
                details={"error": str(e), "exception_type": type(e).__name__},
                suggestions=["Check the health check implementation", "Review system logs"]
            )
            
            with self._lock:
                self._results[name] = error_result
                
            self._process_check_result(error_result)
            return error_result

    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """全ヘルスチェックを実行

        Returns:
            全チェック結果の辞書
        """
        results = {}
        
        with self._lock:
            check_names = list(self._checks.keys())
            
        for name in check_names:
            result = self.run_single_check(name)
            if result:
                results[name] = result
                
        return results

    def get_overall_status(self) -> HealthStatus:
        """全体的なヘルス状態を取得

        Returns:
            全体的なヘルス状態
        """
        with self._lock:
            if not self._results:
                return HealthStatus.UNKNOWN
            
            statuses = [result.status for result in self._results.values()]
            
        # 最も重要度の高いステータスを返す
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif HealthStatus.HEALTHY in statuses:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    def get_health_report(self) -> Dict[str, Any]:
        """ヘルスレポートを取得

        Returns:
            詳細なヘルスレポート
        """
        with self._lock:
            results_copy = dict(self._results)
            alerts_copy = dict(self._alerts)
            
        overall_status = self.get_overall_status()
        
        # 統計情報
        status_counts = {status.value: 0 for status in HealthStatus}
        for result in results_copy.values():
            status_counts[result.status.value] += 1
            
        # 問題のあるチェック
        problematic_checks = [
            result for result in results_copy.values()
            if result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]
        ]
        
        return {
            "timestamp": time.time(),
            "overall_status": overall_status.value,
            "status_distribution": status_counts,
            "total_checks": len(results_copy),
            "problematic_checks": len(problematic_checks),
            "active_alerts": len([alert for alert in alerts_copy.values() if not alert.resolved]),
            "checks": {name: {
                "status": result.status.value,
                "message": result.message,
                "timestamp": result.timestamp,
                "duration_ms": result.duration_ms,
                "suggestions": result.suggestions
            } for name, result in results_copy.items()},
            "alerts": {alert_id: {
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "timestamp": alert.timestamp,
                "resolved": alert.resolved
            } for alert_id, alert in alerts_copy.items()}
        }

    def start_monitoring(self) -> None:
        """継続的なヘルス監視を開始"""
        if self._running:
            self.logger.warning("Health monitoring is already running")
            return
            
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self.logger.info(f"Health monitoring started (interval: {self.check_interval}s)")

    def stop_monitoring(self) -> None:
        """継続的なヘルス監視を停止"""
        if not self._running:
            return
            
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=10)
        self.logger.info("Health monitoring stopped")

    def _monitor_loop(self) -> None:
        """監視メインループ"""
        while self._running:
            try:
                # 全チェック実行
                self.run_all_checks()
                
                # レポートをログファイルに保存
                self._save_health_log()
                
                # アラート処理
                self._process_alerts()
                
                # インターバル待機
                for _ in range(self.check_interval):
                    if not self._running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                time.sleep(5)  # エラー時は少し待機

    def _process_check_result(self, result: HealthCheckResult) -> None:
        """チェック結果を処理してアラートを生成"""
        if result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
            alert_id = f"{result.name}_{int(time.time())}"
            
            severity = AlertSeverity.WARNING if result.status == HealthStatus.WARNING else AlertSeverity.CRITICAL
            
            alert = HealthAlert(
                alert_id=alert_id,
                severity=severity,
                title=f"Health check failed: {result.name}",
                description=result.message,
                timestamp=time.time(),
                resolved=False,
                resolution_time=None,
                metadata={
                    "check_name": result.name,
                    "check_details": result.details,
                    "suggestions": result.suggestions
                }
            )
            
            with self._lock:
                self._alerts[alert_id] = alert
                
            self.logger.warning(f"Health alert generated: {alert.title}")

    def _process_alerts(self) -> None:
        """アラートの自動処理と解決チェック"""
        with self._lock:
            alerts_to_check = list(self._alerts.values())
            
        for alert in alerts_to_check:
            if alert.resolved:
                continue
                
            # 対応するチェックが正常に戻ったかチェック
            check_name = alert.metadata.get("check_name")
            if check_name and check_name in self._results:
                current_result = self._results[check_name]
                if current_result.status == HealthStatus.HEALTHY:
                    # アラート解決
                    alert.resolved = True
                    alert.resolution_time = time.time()
                    self.logger.info(f"Health alert resolved: {alert.title}")

    def _save_health_log(self) -> None:
        """ヘルスレポートをログファイルに保存"""
        try:
            report = self.get_health_report()
            
            # 日付別ログファイル
            date_str = time.strftime("%Y-%m-%d")
            log_file = self.log_directory / f"health_{date_str}.jsonl"
            
            log_entry = {
                "timestamp": report["timestamp"],
                "overall_status": report["overall_status"],
                "status_distribution": report["status_distribution"],
                "total_checks": report["total_checks"],
                "problematic_checks": report["problematic_checks"],
                "active_alerts": report["active_alerts"]
            }
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, separators=(',', ':')) + "\n")
                
        except Exception as e:
            self.logger.error(f"Failed to save health log: {e}")

    def _register_default_checks(self) -> None:
        """デフォルトヘルスチェックを登録"""
        
        def check_disk_space() -> HealthCheckResult:
            """ディスク容量チェック"""
            try:
                import shutil
                total, used, free = shutil.disk_usage("/")
                free_percent = (free / total) * 100
                
                if free_percent < 10:
                    status = HealthStatus.CRITICAL
                    message = f"Critical: Only {free_percent:.1f}% disk space remaining"
                    suggestions = ["Free up disk space immediately", "Check for large log files"]
                elif free_percent < 20:
                    status = HealthStatus.WARNING
                    message = f"Warning: Only {free_percent:.1f}% disk space remaining"
                    suggestions = ["Consider freeing up disk space", "Monitor disk usage"]
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Disk space OK: {free_percent:.1f}% available"
                    suggestions = []
                
                return HealthCheckResult(
                    name="disk_space",
                    status=status,
                    message=message,
                    timestamp=time.time(),
                    duration_ms=0,
                    details={
                        "total_bytes": total,
                        "used_bytes": used,
                        "free_bytes": free,
                        "free_percent": free_percent
                    },
                    suggestions=suggestions
                )
            except Exception as e:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.CRITICAL,
                    message=f"Failed to check disk space: {str(e)}",
                    timestamp=time.time(),
                    duration_ms=0,
                    details={"error": str(e)},
                    suggestions=["Check system permissions", "Verify disk access"]
                )

        def check_memory_usage() -> HealthCheckResult:
            """メモリ使用量チェック"""
            try:
                import psutil
                memory = psutil.virtual_memory()
                used_percent = memory.percent
                
                if used_percent > 90:
                    status = HealthStatus.CRITICAL
                    message = f"Critical: {used_percent:.1f}% memory usage"
                    suggestions = ["Restart high memory processes", "Increase system memory"]
                elif used_percent > 80:
                    status = HealthStatus.WARNING
                    message = f"Warning: {used_percent:.1f}% memory usage"
                    suggestions = ["Monitor memory usage", "Check for memory leaks"]
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Memory usage OK: {used_percent:.1f}%"
                    suggestions = []
                
                return HealthCheckResult(
                    name="memory_usage",
                    status=status,
                    message=message,
                    timestamp=time.time(),
                    duration_ms=0,
                    details={
                        "total_bytes": memory.total,
                        "available_bytes": memory.available,
                        "used_percent": used_percent,
                        "used_bytes": memory.used
                    },
                    suggestions=suggestions
                )
            except ImportError:
                return HealthCheckResult(
                    name="memory_usage",
                    status=HealthStatus.UNKNOWN,
                    message="psutil not available for memory monitoring",
                    timestamp=time.time(),
                    duration_ms=0,
                    details={},
                    suggestions=["Install psutil package for memory monitoring"]
                )
            except Exception as e:
                return HealthCheckResult(
                    name="memory_usage",
                    status=HealthStatus.CRITICAL,
                    message=f"Failed to check memory usage: {str(e)}",
                    timestamp=time.time(),
                    duration_ms=0,
                    details={"error": str(e)},
                    suggestions=["Check system permissions"]
                )

        def check_python_version() -> HealthCheckResult:
            """Python バージョンチェック"""
            try:
                import sys
                version_info = sys.version_info
                version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
                
                # Python 3.8以上を推奨
                if version_info < (3, 8):
                    status = HealthStatus.WARNING
                    message = f"Python version {version_str} is outdated"
                    suggestions = ["Consider upgrading to Python 3.8+"]
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Python version {version_str} OK"
                    suggestions = []
                
                return HealthCheckResult(
                    name="python_version",
                    status=status,
                    message=message,
                    timestamp=time.time(),
                    duration_ms=0,
                    details={
                        "version": version_str,
                        "major": version_info.major,
                        "minor": version_info.minor,
                        "micro": version_info.micro,
                        "platform": platform.platform()
                    },
                    suggestions=suggestions
                )
            except Exception as e:
                return HealthCheckResult(
                    name="python_version",
                    status=HealthStatus.CRITICAL,
                    message=f"Failed to check Python version: {str(e)}",
                    timestamp=time.time(),
                    duration_ms=0,
                    details={"error": str(e)},
                    suggestions=["Check Python installation"]
                )

        # デフォルトチェックを登録
        self.register_check("disk_space", check_disk_space)
        self.register_check("memory_usage", check_memory_usage)
        self.register_check("python_version", check_python_version)


# ファクトリー関数

def get_health_checker(
    check_interval: int = 60,
    alert_threshold: int = 3,
    enable_auto_recovery: bool = True,
    log_directory: Optional[Path] = None,
) -> HealthChecker:
    """ヘルスチェッカーインスタンスを取得

    Args:
        check_interval: チェック間隔（秒）
        alert_threshold: アラート閾値
        enable_auto_recovery: 自動復旧機能の有効化
        log_directory: ログディレクトリ

    Returns:
        設定済みHealthCheckerインスタンス
    """
    return HealthChecker(
        check_interval=check_interval,
        alert_threshold=alert_threshold,
        enable_auto_recovery=enable_auto_recovery,
        log_directory=log_directory
    )


# 既存APIの完全再現（後方互換性100%保持）
__all__ = [
    # 基本型・データクラス（health_types.pyから再エクスポート）
    "HealthStatus",
    "AlertSeverity",
    "HealthCheckResult",
    "HealthAlert",
    # メインクラス
    "HealthChecker",
    # ファクトリー関数
    "get_health_checker",
]


if __name__ == "__main__":
    # 使用例
    checker = get_health_checker(check_interval=30)
    
    print("=== Health Check Demo ===")
    
    # 単発チェック実行
    results = checker.run_all_checks()
    for name, result in results.items():
        print(f"{name}: {result.status.value} - {result.message}")
    
    # 全体レポート
    report = checker.get_health_report()
    print(f"\nOverall Status: {report['overall_status']}")
    print(f"Total Checks: {report['total_checks']}")
    print(f"Problematic Checks: {report['problematic_checks']}")
    
    print("Health check demo completed!")