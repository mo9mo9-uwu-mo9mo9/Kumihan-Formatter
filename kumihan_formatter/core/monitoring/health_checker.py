"""
システムヘルスチェックモジュール

システムヘルスチェック・アプリケーションヘルスチェック・自動診断・
アラート機能を提供する包括的ヘルス監視システム
"""

import importlib
import json
import platform
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Collection, Dict, List, Optional, cast

import psutil

from kumihan_formatter.core.utilities.logger import get_logger


class HealthStatus(Enum):
    """ヘルス状態列挙型"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """アラート重要度列挙型"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class HealthCheckResult:
    """ヘルスチェック結果データ"""

    name: str
    status: HealthStatus
    message: str
    timestamp: float
    duration_ms: float
    details: Dict[str, Any]
    suggestions: List[str]


@dataclass
class HealthAlert:
    """ヘルスアラートデータ"""

    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    timestamp: float
    resolved: bool
    resolution_time: Optional[float]
    metadata: Dict[str, Any]


class HealthChecker:
    """システムヘルスチェックシステム

    システムヘルスチェック・アプリケーションヘルスチェック・自動診断・
    アラート機能を提供する包括的ヘルス監視システム
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        check_interval: float = 60.0,
        enable_auto_checking: bool = False,
        alert_thresholds: Optional[Dict[str, float]] = None,
    ):
        """ヘルスチェックシステム初期化

        Args:
            output_dir: レポート出力ディレクトリ
            check_interval: 自動チェック間隔（秒）
            enable_auto_checking: 自動チェック有効化
            alert_thresholds: アラート閾値設定
        """
        self.logger = get_logger(__name__)
        self.output_dir = output_dir or Path("tmp")
        self.check_interval = check_interval
        self.enable_auto_checking = enable_auto_checking

        # 閾値設定
        self.alert_thresholds = alert_thresholds or {
            "cpu_usage_percent": 85.0,
            "memory_usage_percent": 90.0,
            "disk_usage_percent": 95.0,
            "response_time_ms": 5000.0,
            "error_rate_percent": 5.0,
        }

        # 状態管理
        self.check_results: Dict[str, deque[HealthCheckResult]] = {}
        self.active_alerts: Dict[str, HealthAlert] = {}
        self.alert_handlers: List[Callable[[HealthAlert], None]] = []
        self.custom_checks: Dict[str, Callable[[], HealthCheckResult]] = {}

        # スレッド制御
        self.check_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        self.results_lock = threading.Lock()

        # 依存関係チェック設定
        self.dependencies = {
            "python_version": {"min_version": "3.8", "max_version": "3.12"},
            "required_modules": ["psutil", "json", "pathlib"],
            "optional_modules": ["yaml", "requests", "opentelemetry"],
        }

        # 出力ディレクトリ作成
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 自動チェック開始
        if self.enable_auto_checking:
            self.start_auto_checking()

        self.logger.info(f"HealthChecker初期化完了 - 出力先: {self.output_dir}")

    def start_auto_checking(self) -> None:
        """自動ヘルスチェック開始"""
        if self.check_thread and self.check_thread.is_alive():
            return

        self.shutdown_event.clear()
        self.check_thread = threading.Thread(
            target=self._auto_check_loop, name="HealthAutoChecker", daemon=True
        )
        self.check_thread.start()
        self.logger.info(f"自動ヘルスチェック開始 - 間隔: {self.check_interval}秒")

    def stop_auto_checking(self) -> None:
        """自動ヘルスチェック停止"""
        self.shutdown_event.set()
        if self.check_thread and self.check_thread.is_alive():
            self.check_thread.join(timeout=5.0)
        self.logger.info("自動ヘルスチェック停止")

    def _auto_check_loop(self) -> None:
        """自動チェックループ"""
        while not self.shutdown_event.is_set():
            try:
                # 全体ヘルスチェック実行
                self.run_comprehensive_check()

                # 待機（中断可能）
                if self.shutdown_event.wait(self.check_interval):
                    break

            except Exception as e:
                self.logger.error(f"自動ヘルスチェックエラー: {e}")
                # エラー時は短縮間隔で継続
                if self.shutdown_event.wait(10.0):
                    break

    def check_system_health(self) -> HealthCheckResult:
        """システムヘルスチェック

        Returns:
            システムヘルス結果
        """
        start_time = time.time()

        try:
            details: Dict[str, Any] = {}
            suggestions: List[str] = []
            overall_status = HealthStatus.HEALTHY

            # CPU使用率チェック
            cpu_percent = psutil.cpu_percent(interval=1.0)
            details["cpu_usage_percent"] = cpu_percent

            if cpu_percent > self.alert_thresholds["cpu_usage_percent"]:
                overall_status = HealthStatus.CRITICAL
                suggestions.append(f"CPU使用率が高すぎます ({cpu_percent:.1f}%)")
                self._create_alert(
                    "high_cpu_usage",
                    AlertSeverity.CRITICAL,
                    "高CPU使用率検出",
                    f"CPU使用率: {cpu_percent:.1f}%",
                    {"cpu_percent": cpu_percent},
                )
            elif cpu_percent > self.alert_thresholds["cpu_usage_percent"] * 0.8:
                overall_status = max(
                    overall_status, HealthStatus.WARNING, key=lambda x: x.value
                )
                suggestions.append(f"CPU使用率が上昇しています ({cpu_percent:.1f}%)")

            # メモリ使用量チェック
            memory = psutil.virtual_memory()
            details["memory_usage_percent"] = memory.percent
            details["memory_available_mb"] = memory.available / 1024 / 1024

            if memory.percent > self.alert_thresholds["memory_usage_percent"]:
                overall_status = HealthStatus.CRITICAL
                suggestions.append(f"メモリ使用率が高すぎます ({memory.percent:.1f}%)")
                self._create_alert(
                    "high_memory_usage",
                    AlertSeverity.CRITICAL,
                    "高メモリ使用率検出",
                    f"メモリ使用率: {memory.percent:.1f}%",
                    {"memory_percent": memory.percent},
                )
            elif memory.percent > self.alert_thresholds["memory_usage_percent"] * 0.8:
                overall_status = max(
                    overall_status, HealthStatus.WARNING, key=lambda x: x.value
                )
                suggestions.append(
                    f"メモリ使用率が上昇しています ({memory.percent:.1f}%)"
                )

            # ディスク使用量チェック
            disk_usage = psutil.disk_usage("/")
            disk_percent = disk_usage.percent
            details["disk_usage_percent"] = disk_percent
            details["disk_free_gb"] = disk_usage.free / 1024 / 1024 / 1024

            if disk_percent > self.alert_thresholds["disk_usage_percent"]:
                overall_status = HealthStatus.CRITICAL
                suggestions.append(f"ディスク使用率が高すぎます ({disk_percent:.1f}%)")
                self._create_alert(
                    "high_disk_usage",
                    AlertSeverity.CRITICAL,
                    "高ディスク使用率検出",
                    f"ディスク使用率: {disk_percent:.1f}%",
                    {"disk_percent": disk_percent},
                )
            elif disk_percent > self.alert_thresholds["disk_usage_percent"] * 0.8:
                overall_status = max(
                    overall_status, HealthStatus.WARNING, key=lambda x: x.value
                )
                suggestions.append(
                    f"ディスク使用率が上昇しています ({disk_percent:.1f}%)"
                )

            # プロセス数チェック
            process_count = len(psutil.pids())
            details["process_count"] = process_count

            # システム情報
            details["platform"] = str(platform.system())
            details["python_version"] = str(platform.python_version())
            details["architecture"] = str(platform.machine())

            # 稼働時間
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            details["uptime_hours"] = uptime_seconds / 3600

            duration_ms = (time.time() - start_time) * 1000

            message = f"システムヘルス: {overall_status.value.upper()}"
            if suggestions:
                message += f" - {len(suggestions)}個の改善提案"

            return HealthCheckResult(
                name="system_health",
                status=overall_status,
                message=message,
                timestamp=time.time(),
                duration_ms=duration_ms,
                details=details,
                suggestions=suggestions,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"システムヘルスチェックエラー: {e}")

            return HealthCheckResult(
                name="system_health",
                status=HealthStatus.CRITICAL,
                message=f"システムヘルスチェック失敗: {str(e)}",
                timestamp=time.time(),
                duration_ms=duration_ms,
                details={"error": str(e)},
                suggestions=["システムヘルスチェック機能の確認が必要です"],
            )

    def check_application_health(self) -> HealthCheckResult:
        """アプリケーションヘルスチェック

        Returns:
            アプリケーションヘルス結果
        """
        start_time = time.time()

        try:
            details: Dict[str, Any] = {}
            suggestions: List[str] = []
            overall_status = HealthStatus.HEALTHY

            # 現在のプロセス情報
            process = psutil.Process()

            # プロセス状態
            details["process_status"] = str(process.status())
            details["process_pid"] = int(process.pid)
            details["process_threads"] = int(process.num_threads())

            # メモリ使用量
            memory_info = process.memory_info()
            app_memory_mb = memory_info.rss / 1024 / 1024
            details["app_memory_mb"] = app_memory_mb

            if app_memory_mb > 1024:  # 1GB以上
                overall_status = HealthStatus.WARNING
                suggestions.append(
                    f"アプリケーションメモリ使用量が多いです ({app_memory_mb:.1f}MB)"
                )

            # CPU使用率
            app_cpu_percent = float(process.cpu_percent())
            details["app_cpu_percent"] = app_cpu_percent

            # 実行時間
            create_time = float(process.create_time())
            runtime_hours = (time.time() - create_time) / 3600
            details["runtime_hours"] = float(runtime_hours)

            # オープンファイル数（権限がある場合のみ）
            try:
                open_files = int(len(process.open_files()))
                details["open_files"] = open_files

                if open_files > 1000:
                    overall_status = HealthStatus.WARNING
                    suggestions.append(f"オープンファイル数が多いです ({open_files}個)")

            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            # Python GC状態
            import gc

            gc_stats = gc.get_stats()
            details["gc_collections"] = sum(stat["collections"] for stat in gc_stats)
            details["gc_uncollectable"] = sum(
                stat["uncollectable"] for stat in gc_stats
            )

            if int(details["gc_uncollectable"]) > 0:
                overall_status = max(
                    overall_status, HealthStatus.WARNING, key=lambda x: x.value
                )
                suggestions.append("回収不能なオブジェクトが検出されました")

            # スレッド数
            active_threads = int(threading.active_count())
            details["active_threads"] = active_threads

            if active_threads > 50:
                overall_status = HealthStatus.WARNING
                suggestions.append(
                    f"アクティブスレッド数が多いです ({active_threads}個)"
                )

            duration_ms = (time.time() - start_time) * 1000

            message = f"アプリケーションヘルス: {overall_status.value.upper()}"
            if suggestions:
                message += f" - {len(suggestions)}個の改善提案"

            return HealthCheckResult(
                name="application_health",
                status=overall_status,
                message=message,
                timestamp=time.time(),
                duration_ms=duration_ms,
                details=details,
                suggestions=suggestions,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"アプリケーションヘルスチェックエラー: {e}")

            return HealthCheckResult(
                name="application_health",
                status=HealthStatus.CRITICAL,
                message=f"アプリケーションヘルスチェック失敗: {str(e)}",
                timestamp=time.time(),
                duration_ms=duration_ms,
                details={"error": str(e)},
                suggestions=["アプリケーション状態の詳細確認が必要です"],
            )

    def check_dependencies(self) -> HealthCheckResult:
        """依存関係チェック

        Returns:
            依存関係チェック結果
        """
        start_time = time.time()

        try:
            details: Dict[str, Any] = {}
            suggestions: List[str] = []
            overall_status = HealthStatus.HEALTHY

            # Pythonバージョンチェック
            current_version = str(platform.python_version())
            details["python_version"] = current_version

            python_version_deps = cast(Dict[str, Any], self.dependencies["python_version"])
            min_version = str(python_version_deps["min_version"])
            max_version = str(python_version_deps["max_version"])

            if current_version < min_version or current_version > max_version:
                overall_status = HealthStatus.WARNING
                suggestions.append(
                    f"Python バージョン要確認: {current_version} (推奨: {min_version}-{max_version})"
                )

            # 必須モジュールチェック
            required_modules = cast(List[str], self.dependencies["required_modules"])
            missing_required: List[str] = []
            available_modules: Dict[str, str] = {}

            for module_name in required_modules:
                try:
                    module = importlib.import_module(module_name)
                    version = getattr(module, "__version__", "unknown")
                    available_modules[module_name] = version
                except ImportError:
                    missing_required.append(module_name)

            details["available_modules"] = available_modules
            details["missing_required_modules"] = missing_required

            if missing_required:
                overall_status = HealthStatus.CRITICAL
                suggestions.append(f"必須モジュール不足: {', '.join(missing_required)}")

            # オプションモジュールチェック
            optional_modules = cast(List[str], self.dependencies["optional_modules"])
            missing_optional: List[str] = []

            for module_name in optional_modules:
                try:
                    module = importlib.import_module(module_name)
                    version = getattr(module, "__version__", "unknown")
                    available_modules[module_name] = version
                except ImportError:
                    missing_optional.append(module_name)

            details["missing_optional_modules"] = missing_optional

            if missing_optional:
                suggestions.append(
                    f"オプションモジュール不足: {', '.join(missing_optional)}"
                )

            duration_ms = (time.time() - start_time) * 1000

            message = f"依存関係: {overall_status.value.upper()}"
            message += f" - {len(available_modules)}個のモジュール利用可能"

            return HealthCheckResult(
                name="dependencies",
                status=overall_status,
                message=message,
                timestamp=time.time(),
                duration_ms=duration_ms,
                details=details,
                suggestions=suggestions,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"依存関係チェックエラー: {e}")

            return HealthCheckResult(
                name="dependencies",
                status=HealthStatus.CRITICAL,
                message=f"依存関係チェック失敗: {str(e)}",
                timestamp=time.time(),
                duration_ms=duration_ms,
                details={"error": str(e)},
                suggestions=["依存関係の手動確認が必要です"],
            )

    def check_disk_space(self) -> HealthCheckResult:
        """ディスクスペースチェック

        Returns:
            ディスクスペースチェック結果
        """
        start_time = time.time()

        try:
            details: Dict[str, Any] = {}
            suggestions: List[str] = []
            overall_status = HealthStatus.HEALTHY

            # プロジェクトディレクトリのディスク使用量
            project_path = Path.cwd()
            disk_usage = psutil.disk_usage(str(project_path))

            free_gb = disk_usage.free / 1024 / 1024 / 1024
            usage_percent = (disk_usage.used / disk_usage.total) * 100

            details["disk_path"] = str(project_path)
            details["total_gb"] = disk_usage.total / 1024 / 1024 / 1024
            details["used_gb"] = disk_usage.used / 1024 / 1024 / 1024
            details["free_gb"] = free_gb
            details["usage_percent"] = usage_percent

            # 警告レベル判定
            if usage_percent > 95:
                overall_status = HealthStatus.CRITICAL
                suggestions.append(
                    f"ディスク容量が不足しています (使用率: {usage_percent:.1f}%)"
                )
            elif usage_percent > 85:
                overall_status = HealthStatus.WARNING
                suggestions.append(
                    f"ディスク容量が少なくなっています (使用率: {usage_percent:.1f}%)"
                )

            if free_gb < 1.0:
                overall_status = HealthStatus.CRITICAL
                suggestions.append(
                    f"利用可能ディスク容量が1GB未満です ({free_gb:.2f}GB)"
                )

            # 一時ディレクトリチェック
            tmp_dir = Path("tmp")
            if tmp_dir.exists():
                tmp_size = self._calculate_directory_size(tmp_dir)
                details["tmp_directory_mb"] = tmp_size / 1024 / 1024

                if tmp_size > 100 * 1024 * 1024:  # 100MB以上
                    suggestions.append(
                        "一時ディレクトリが大きくなっています。クリーンアップを検討してください"
                    )

            duration_ms = (time.time() - start_time) * 1000

            message = f"ディスクスペース: {overall_status.value.upper()} - {free_gb:.1f}GB利用可能"

            return HealthCheckResult(
                name="disk_space",
                status=overall_status,
                message=message,
                timestamp=time.time(),
                duration_ms=duration_ms,
                details=details,
                suggestions=suggestions,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"ディスクスペースチェックエラー: {e}")

            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.CRITICAL,
                message=f"ディスクスペースチェック失敗: {str(e)}",
                timestamp=time.time(),
                duration_ms=duration_ms,
                details={"error": str(e)},
                suggestions=["ディスクスペースの手動確認が必要です"],
            )

    def _calculate_directory_size(self, directory: Path) -> int:
        """ディレクトリサイズ計算

        Args:
            directory: 対象ディレクトリ

        Returns:
            ディレクトリサイズ（バイト）
        """
        total_size = 0
        try:
            for path in directory.rglob("*"):
                if path.is_file():
                    total_size += path.stat().st_size
        except Exception as e:
            self.logger.error(f"ディレクトリサイズ計算エラー ({directory}): {e}")

        return total_size

    def register_custom_check(
        self, name: str, check_func: Callable[[], HealthCheckResult]
    ) -> None:
        """カスタムヘルスチェック登録

        Args:
            name: チェック名
            check_func: チェック関数
        """
        self.custom_checks[name] = check_func
        self.logger.info(f"カスタムヘルスチェック登録: {name}")

    def unregister_custom_check(self, name: str) -> None:
        """カスタムヘルスチェック登録解除

        Args:
            name: チェック名
        """
        if name in self.custom_checks:
            del self.custom_checks[name]
            self.logger.info(f"カスタムヘルスチェック登録解除: {name}")

    def add_alert_handler(self, handler: Callable[[HealthAlert], None]) -> None:
        """アラートハンドラ追加

        Args:
            handler: アラート処理関数
        """
        self.alert_handlers.append(handler)
        self.logger.info("アラートハンドラ追加")

    def _create_alert(
        self,
        alert_id: str,
        severity: AlertSeverity,
        title: str,
        description: str,
        metadata: Dict[str, Any],
    ) -> None:
        """アラート生成

        Args:
            alert_id: アラートID
            severity: 重要度
            title: アラートタイトル
            description: アラート説明
            metadata: メタデータ
        """
        # 既存アラートが解決済みでない場合はスキップ
        if alert_id in self.active_alerts and not self.active_alerts[alert_id].resolved:
            return

        alert = HealthAlert(
            alert_id=alert_id,
            severity=severity,
            title=title,
            description=description,
            timestamp=time.time(),
            resolved=False,
            resolution_time=None,
            metadata=metadata,
        )

        self.active_alerts[alert_id] = alert

        # アラートハンドラ実行
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"アラートハンドラ実行エラー: {e}")

        self.logger.warning(f"ヘルスアラート発生: {title} ({severity.value})")

    def resolve_alert(self, alert_id: str) -> bool:
        """アラート解決

        Args:
            alert_id: アラートID

        Returns:
            解決成功フラグ
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = time.time()
            self.logger.info(f"ヘルスアラート解決: {alert.title}")
            return True
        return False

    def run_comprehensive_check(self) -> Dict[str, HealthCheckResult]:
        """包括的ヘルスチェック実行

        Returns:
            全チェック結果
        """
        try:
            results = {}

            # 標準チェック実行
            standard_checks = [
                ("system", self.check_system_health),
                ("application", self.check_application_health),
                ("dependencies", self.check_dependencies),
                ("disk_space", self.check_disk_space),
            ]

            for check_name, check_func in standard_checks:
                try:
                    result = check_func()
                    results[check_name] = result
                    self._record_check_result(result)
                except Exception as e:
                    self.logger.error(f"ヘルスチェック実行エラー ({check_name}): {e}")
                    results[check_name] = HealthCheckResult(
                        name=check_name,
                        status=HealthStatus.CRITICAL,
                        message=f"チェック実行失敗: {str(e)}",
                        timestamp=time.time(),
                        duration_ms=0,
                        details={"error": str(e)},
                        suggestions=["チェック機能の確認が必要です"],
                    )

            # カスタムチェック実行
            for check_name, check_func in self.custom_checks.items():
                try:
                    result = check_func()
                    results[f"custom_{check_name}"] = result
                    self._record_check_result(result)
                except Exception as e:
                    self.logger.error(
                        f"カスタムヘルスチェック実行エラー ({check_name}): {e}"
                    )
                    results[f"custom_{check_name}"] = HealthCheckResult(
                        name=f"custom_{check_name}",
                        status=HealthStatus.CRITICAL,
                        message=f"カスタムチェック実行失敗: {str(e)}",
                        timestamp=time.time(),
                        duration_ms=0,
                        details={"error": str(e)},
                        suggestions=["カスタムチェック機能の確認が必要です"],
                    )

            self.logger.info(
                f"包括的ヘルスチェック完了 - {len(results)}個のチェック実行"
            )
            return results

        except Exception as e:
            self.logger.error(f"包括的ヘルスチェックエラー: {e}")
            return {
                "error": HealthCheckResult(
                    name="comprehensive_check",
                    status=HealthStatus.CRITICAL,
                    message=f"包括的ヘルスチェック失敗: {str(e)}",
                    timestamp=time.time(),
                    duration_ms=0,
                    details={"error": str(e)},
                    suggestions=["ヘルスチェックシステムの確認が必要です"],
                )
            }

    def _record_check_result(self, result: HealthCheckResult) -> None:
        """チェック結果記録

        Args:
            result: ヘルスチェック結果
        """
        with self.results_lock:
            if result.name not in self.check_results:
                self.check_results[result.name] = deque(maxlen=100)  # 最大100件保持

            self.check_results[result.name].append(result)

    def get_health_summary(self, hours_back: float = 24.0) -> Dict[str, Any]:
        """ヘルス状態サマリ取得

        Args:
            hours_back: 遡る時間（時間）

        Returns:
            ヘルス状態サマリ
        """
        try:
            cutoff_time = time.time() - (hours_back * 3600)
            summary = {
                "timestamp": datetime.now().isoformat(),
                "time_range_hours": hours_back,
                "overall_status": HealthStatus.HEALTHY.value,
                "check_summary": {},
                "active_alerts": len(
                    [a for a in self.active_alerts.values() if not a.resolved]
                ),
                "resolved_alerts": len(
                    [a for a in self.active_alerts.values() if a.resolved]
                ),
            }

            worst_status = HealthStatus.HEALTHY

            with self.results_lock:
                for check_name, results in self.check_results.items():
                    recent_results = [r for r in results if r.timestamp >= cutoff_time]

                    if not recent_results:
                        continue

                    latest_result = recent_results[-1]

                    # 最悪の状態を全体状態とする
                    if latest_result.status.value > worst_status.value:
                        worst_status = latest_result.status

                    check_summary = cast(Dict[str, Any], summary["check_summary"])
                    check_summary[check_name] = {
                        "latest_status": latest_result.status.value,
                        "latest_message": latest_result.message,
                        "check_count": len(recent_results),
                        "avg_duration_ms": sum(r.duration_ms for r in recent_results)
                        / len(recent_results),
                        "suggestion_count": len(latest_result.suggestions),
                    }

            summary["overall_status"] = worst_status.value

            return summary

        except Exception as e:
            self.logger.error(f"ヘルス状態サマリ取得エラー: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": HealthStatus.CRITICAL.value,
                "error": str(e),
            }

    def generate_health_report(self) -> Path:
        """ヘルスレポート生成

        Returns:
            生成されたレポートファイルパス
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.output_dir / f"health_report_{timestamp}.json"

            # 包括的チェック実行
            check_results = self.run_comprehensive_check()

            # ヘルス状態サマリ取得
            health_summary = self.get_health_summary()

            # レポートデータ構築
            report_data = {
                "report_timestamp": datetime.now().isoformat(),
                "health_summary": health_summary,
                "detailed_results": {
                    name: asdict(result) for name, result in check_results.items()
                },
                "active_alerts": {
                    aid: asdict(alert)
                    for aid, alert in self.active_alerts.items()
                    if not alert.resolved
                },
                "alert_history": {
                    aid: asdict(alert)
                    for aid, alert in self.active_alerts.items()
                    if alert.resolved
                },
                "configuration": {
                    "alert_thresholds": self.alert_thresholds,
                    "check_interval": self.check_interval,
                    "auto_checking_enabled": self.enable_auto_checking,
                    "custom_checks": list(self.custom_checks.keys()),
                },
            }

            # JSONファイルとして出力
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"ヘルスレポート生成完了: {report_file}")
            return report_file

        except Exception as e:
            self.logger.error(f"ヘルスレポート生成エラー: {e}")
            raise

    def shutdown(self) -> None:
        """ヘルスチェックシステム終了処理"""
        try:
            # 自動チェック停止
            self.stop_auto_checking()

            # 最終レポート生成
            if self.check_results:
                report_file = self.generate_health_report()
                self.logger.info(f"終了時ヘルスレポート生成: {report_file}")

            self.logger.info("HealthChecker終了処理完了")

        except Exception as e:
            self.logger.error(f"終了処理エラー: {e}")

    def __enter__(self) -> "HealthChecker":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()
