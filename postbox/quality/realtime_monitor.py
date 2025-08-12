#!/usr/bin/env python3
"""
Enhanced RealtimeQualityMonitor
既存QualityMonitorを拡張したリアルタイム品質監視システム
ファイル変更検知・インクリメンタル品質評価・ホットリロード対応
"""

import os
import json
import time
import threading
import datetime
import hashlib
from typing import Dict, List, Any, Optional, Set, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

# 既存システムのインポート
try:
    from .quality_manager import QualityManager, QualityMetrics, CheckType
    from ..monitoring.quality_monitor import QualityMonitor, QualityAlert, AlertLevel
except ImportError:
    # フォールバック用
    import sys
    sys.path.append('postbox')
    try:
        from quality.quality_manager import QualityManager, QualityMetrics, CheckType
        from monitoring.quality_monitor import QualityMonitor, QualityAlert, AlertLevel
    except ImportError:
        print("⚠️ 品質管理モジュールが見つかりません。モック実装を使用します。")
        QualityManager = None
        QualityMonitor = None

class RealtimeQualityLevel(Enum):
    """リアルタイム品質レベル"""
    EXCELLENT = "excellent"     # 優秀（95%以上）- 即座リリース可能
    GOOD = "good"              # 良好（85-94%）- マージ可能
    ACCEPTABLE = "acceptable"   # 許容（75-84%）- レビュー推奨
    WARNING = "warning"        # 警告（65-74%）- 修正必要
    CRITICAL = "critical"       # 重大（65%未満）- 即座修正必須

class FileChangeType(Enum):
    """ファイル変更タイプ"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"

@dataclass
class FileQualitySnapshot:
    """ファイル品質スナップショット"""
    file_path: str
    timestamp: str
    file_hash: str
    quality_metrics: Dict[str, float]
    overall_score: float
    quality_level: RealtimeQualityLevel
    errors: List[str]
    warnings: List[str]
    change_type: FileChangeType
    previous_score: Optional[float] = None
    improvement: Optional[float] = None

@dataclass
class IncrementalQualityResult:
    """インクリメンタル品質評価結果"""
    file_snapshots: List[FileQualitySnapshot]
    overall_project_score: float
    changed_files_count: int
    improved_files: List[str]
    degraded_files: List[str]
    critical_files: List[str]
    recommendations: List[str]
    processing_time: float

class QualityFileWatcher(FileSystemEventHandler):
    """品質監視用ファイルウォッチャー"""
    
    def __init__(self, realtime_monitor: 'EnhancedRealtimeQualityMonitor'):
        self.realtime_monitor = realtime_monitor
        self.debounce_delay = 2.0  # 2秒のデバウンス
        self.pending_changes: Dict[str, float] = {}
        self.lock = threading.Lock()
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = event.src_path
        if self._should_monitor_file(file_path):
            self._schedule_quality_check(file_path, FileChangeType.MODIFIED)
    
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = event.src_path
        if self._should_monitor_file(file_path):
            self._schedule_quality_check(file_path, FileChangeType.CREATED)
    
    def _should_monitor_file(self, file_path: str) -> bool:
        """監視対象ファイルかチェック"""
        if not file_path.endswith('.py'):
            return False
        
        # 除外パターン
        exclude_patterns = [
            '__pycache__',
            '.pyc',
            'test_',
            '.git',
            'venv',
            'env',
            '.venv'
        ]
        
        for pattern in exclude_patterns:
            if pattern in file_path:
                return False
        
        return True
    
    def _schedule_quality_check(self, file_path: str, change_type: FileChangeType):
        """品質チェックをスケジュール（デバウンス機能付き）"""
        with self.lock:
            current_time = time.time()
            self.pending_changes[file_path] = current_time
            
            # デバウンス処理
            def delayed_check():
                time.sleep(self.debounce_delay)
                with self.lock:
                    if (file_path in self.pending_changes and 
                        current_time == self.pending_changes[file_path]):
                        del self.pending_changes[file_path]
                        self.realtime_monitor.process_file_change(file_path, change_type)
            
            # 新しいスレッドで遅延チェック実行
            threading.Thread(target=delayed_check, daemon=True).start()

class EnhancedRealtimeQualityMonitor:
    """強化版リアルタイム品質監視システム"""
    
    def __init__(self, watch_directories: Optional[List[str]] = None):
        self.watch_directories = watch_directories or ["kumihan_formatter/", "postbox/"]
        self.monitoring_active = False
        self.file_quality_cache: Dict[str, FileQualitySnapshot] = {}
        
        # パス設定
        self.data_dir = Path("postbox/quality/realtime_data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.snapshots_path = self.data_dir / "file_snapshots.json"
        self.realtime_history_path = self.data_dir / "realtime_history.json"
        self.performance_metrics_path = self.data_dir / "performance_metrics.json"
        
        # 既存システム連携
        if QualityManager:
            self.quality_manager = QualityManager()
        else:
            self.quality_manager = MockQualityManager()
            
        if QualityMonitor:
            self.base_monitor = QualityMonitor(check_interval=60)  # 1分間隔で基本監視
        else:
            self.base_monitor = MockQualityMonitor()
        
        # ファイルシステム監視設定
        self.observer = Observer()
        self.file_watcher = QualityFileWatcher(self)
        
        # パフォーマンス統計
        self.performance_stats = {
            "files_processed": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # 購読者
        self.subscribers: List[Callable] = []
        
        print("🚀 EnhancedRealtimeQualityMonitor 初期化完了")
    
    def start_realtime_monitoring(self) -> None:
        """リアルタイム監視開始"""
        if self.monitoring_active:
            print("⚠️ リアルタイム監視は既に開始されています")
            return
        
        print("🔍 リアルタイム品質監視開始...")
        
        # ベース監視システム開始
        if hasattr(self.base_monitor, 'start_monitoring'):
            self.base_monitor.start_monitoring()
        
        # ファイルシステム監視開始
        for watch_dir in self.watch_directories:
            if os.path.exists(watch_dir):
                self.observer.schedule(self.file_watcher, watch_dir, recursive=True)
                print(f"📁 監視ディレクトリ追加: {watch_dir}")
        
        self.observer.start()
        self.monitoring_active = True
        
        # 初期品質スナップショット作成
        self._create_initial_snapshot()
        
        print("✅ リアルタイム品質監視開始完了")
    
    def stop_realtime_monitoring(self) -> None:
        """リアルタイム監視停止"""
        if not self.monitoring_active:
            return
        
        print("⏹️ リアルタイム品質監視停止中...")
        
        self.monitoring_active = False
        self.observer.stop()
        self.observer.join()
        
        if hasattr(self.base_monitor, 'stop_monitoring'):
            self.base_monitor.stop_monitoring()
        
        # 最終統計保存
        self._save_performance_metrics()
        
        print("✅ リアルタイム品質監視停止完了")
    
    def process_file_change(self, file_path: str, change_type: FileChangeType) -> None:
        """ファイル変更処理"""
        start_time = time.time()
        
        try:
            print(f"🔍 ファイル変更検知: {file_path} ({change_type.value})")
            
            # ファイル品質評価
            snapshot = self._evaluate_file_quality(file_path, change_type)
            
            # キャッシュ更新
            previous_snapshot = self.file_quality_cache.get(file_path)
            self.file_quality_cache[file_path] = snapshot
            
            # 改善/劣化分析
            if previous_snapshot:
                snapshot.previous_score = previous_snapshot.overall_score
                snapshot.improvement = snapshot.overall_score - previous_snapshot.overall_score
            
            # アラート検出・通知
            alerts = self._detect_realtime_alerts(snapshot, previous_snapshot)
            for alert in alerts:
                self._notify_subscribers(alert)
            
            # 履歴保存
            self._save_snapshot_to_history(snapshot)
            
            processing_time = time.time() - start_time
            self.performance_stats["files_processed"] += 1
            self.performance_stats["total_processing_time"] += processing_time
            self.performance_stats["average_processing_time"] = (
                self.performance_stats["total_processing_time"] / 
                self.performance_stats["files_processed"]
            )
            
            print(f"✅ ファイル評価完了: {snapshot.quality_level.value} "
                  f"(スコア: {snapshot.overall_score:.3f}, 処理時間: {processing_time:.2f}s)")
            
        except Exception as e:
            print(f"❌ ファイル変更処理エラー: {file_path} - {e}")
    
    def _evaluate_file_quality(self, file_path: str, change_type: FileChangeType) -> FileQualitySnapshot:
        """ファイル品質評価"""
        
        # ファイルハッシュ計算
        file_hash = self._calculate_file_hash(file_path)
        
        # キャッシュチェック
        cached_snapshot = self.file_quality_cache.get(file_path)
        if cached_snapshot and cached_snapshot.file_hash == file_hash:
            self.performance_stats["cache_hits"] += 1
            print(f"📋 キャッシュヒット: {file_path}")
            cached_snapshot.change_type = change_type
            cached_snapshot.timestamp = datetime.datetime.now().isoformat()
            return cached_snapshot
        
        self.performance_stats["cache_misses"] += 1
        
        # 品質チェック実行
        try:
            if hasattr(self.quality_manager, 'run_comprehensive_check'):
                metrics = self.quality_manager.run_comprehensive_check([file_path], "realtime")
                
                quality_scores = {
                    "syntax": metrics.syntax_score,
                    "type_check": metrics.type_score,
                    "lint": metrics.lint_score,
                    "format": metrics.format_score,
                    "security": metrics.security_score,
                    "performance": metrics.performance_score
                }
                
                overall_score = metrics.overall_score
                errors = [f"エラー数: {metrics.error_count}"]
                warnings = [f"警告数: {metrics.warning_count}"]
                
            else:
                # フォールバック実装
                quality_scores = self._basic_quality_check(file_path)
                overall_score = sum(quality_scores.values()) / len(quality_scores)
                errors = []
                warnings = []
            
        except Exception as e:
            print(f"⚠️ 品質チェックエラー: {e}")
            quality_scores = {"basic": 0.5}
            overall_score = 0.5
            errors = [f"品質チェックエラー: {str(e)}"]
            warnings = []
        
        # 品質レベル決定
        quality_level = self._determine_quality_level(overall_score)
        
        return FileQualitySnapshot(
            file_path=file_path,
            timestamp=datetime.datetime.now().isoformat(),
            file_hash=file_hash,
            quality_metrics=quality_scores,
            overall_score=overall_score,
            quality_level=quality_level,
            errors=errors,
            warnings=warnings,
            change_type=change_type
        )
    
    def _basic_quality_check(self, file_path: str) -> Dict[str, float]:
        """基本的な品質チェック（フォールバック用）"""
        scores = {}
        
        try:
            # 構文チェック
            import subprocess
            result = subprocess.run(
                ["python3", "-m", "py_compile", file_path],
                capture_output=True,
                text=True
            )
            scores["syntax"] = 1.0 if result.returncode == 0 else 0.0
            
        except Exception:
            scores["syntax"] = 0.5
        
        try:
            # ファイル読み込み・基本分析
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            # 基本メトリクス
            scores["readability"] = min(1.0, 1.0 - (len(lines) / 1000))  # 行数による可読性
            scores["basic_structure"] = 0.8 if any(line.strip().startswith('def ') for line in lines) else 0.6
            
        except Exception:
            scores["readability"] = 0.5
            scores["basic_structure"] = 0.5
        
        return scores
    
    def _determine_quality_level(self, overall_score: float) -> RealtimeQualityLevel:
        """品質レベル決定"""
        if overall_score >= 0.95:
            return RealtimeQualityLevel.EXCELLENT
        elif overall_score >= 0.85:
            return RealtimeQualityLevel.GOOD
        elif overall_score >= 0.75:
            return RealtimeQualityLevel.ACCEPTABLE
        elif overall_score >= 0.65:
            return RealtimeQualityLevel.WARNING
        else:
            return RealtimeQualityLevel.CRITICAL
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """ファイルハッシュ計算"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return f"error_{int(time.time())}"
    
    def _detect_realtime_alerts(self, current_snapshot: FileQualitySnapshot, 
                              previous_snapshot: Optional[FileQualitySnapshot]) -> List[QualityAlert]:
        """リアルタイムアラート検出"""
        alerts = []
        current_time = datetime.datetime.now().isoformat()
        
        # 品質レベル低下アラート
        if current_snapshot.quality_level == RealtimeQualityLevel.CRITICAL:
            alerts.append(QualityAlert(
                timestamp=current_time,
                level=AlertLevel.CRITICAL,
                category="quality_critical",
                message=f"品質レベル重大: {current_snapshot.file_path}",
                details={"score": current_snapshot.overall_score},
                affected_files=[current_snapshot.file_path],
                ai_agent="realtime_monitor"
            ))
        
        # 品質劣化アラート
        if (previous_snapshot and current_snapshot.improvement and 
            current_snapshot.improvement < -0.1):  # 10%以上低下
            alerts.append(QualityAlert(
                timestamp=current_time,
                level=AlertLevel.WARNING,
                category="quality_degradation",
                message=f"品質劣化検出: {current_snapshot.file_path}",
                details={
                    "previous_score": previous_snapshot.overall_score,
                    "current_score": current_snapshot.overall_score,
                    "degradation": abs(current_snapshot.improvement)
                },
                affected_files=[current_snapshot.file_path],
                ai_agent="realtime_monitor"
            ))
        
        return alerts
    
    def _create_initial_snapshot(self) -> None:
        """初期品質スナップショット作成"""
        print("📸 初期品質スナップショット作成中...")
        
        initial_files = []
        for watch_dir in self.watch_directories:
            if os.path.exists(watch_dir):
                for root, dirs, files in os.walk(watch_dir):
                    for file in files:
                        if file.endswith('.py'):
                            initial_files.append(os.path.join(root, file))
        
        print(f"📁 初期対象ファイル: {len(initial_files)}件")
        
        # 最初の10ファイルのみ処理（パフォーマンス考慮）
        for file_path in initial_files[:10]:
            try:
                self.process_file_change(file_path, FileChangeType.CREATED)
            except Exception as e:
                print(f"⚠️ 初期スナップショット作成エラー: {file_path} - {e}")
        
        print("✅ 初期品質スナップショット作成完了")
    
    def _save_snapshot_to_history(self, snapshot: FileQualitySnapshot) -> None:
        """スナップショットを履歴に保存"""
        try:
            history = []
            if self.realtime_history_path.exists():
                with open(self.realtime_history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            history.append(asdict(snapshot))
            
            # 履歴サイズ制限（最新1000件）
            if len(history) > 1000:
                history = history[-1000:]
            
            with open(self.realtime_history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 履歴保存エラー: {e}")
    
    def _save_performance_metrics(self) -> None:
        """パフォーマンス統計保存"""
        try:
            metrics_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "performance_stats": self.performance_stats,
                "cache_efficiency": (
                    self.performance_stats["cache_hits"] / 
                    max(self.performance_stats["cache_hits"] + self.performance_stats["cache_misses"], 1)
                )
            }
            
            with open(self.performance_metrics_path, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ パフォーマンス統計保存エラー: {e}")
    
    def _notify_subscribers(self, alert: QualityAlert) -> None:
        """購読者への通知"""
        for callback in self.subscribers:
            try:
                callback(alert)
            except Exception as e:
                print(f"⚠️ 通知エラー: {e}")
    
    def subscribe_to_realtime_alerts(self, callback: Callable[[QualityAlert], None]) -> None:
        """リアルタイムアラート購読"""
        self.subscribers.append(callback)
        print(f"📬 リアルタイムアラート購読追加: {len(self.subscribers)}件")
    
    def get_project_quality_overview(self) -> Dict[str, Any]:
        """プロジェクト品質概要取得"""
        if not self.file_quality_cache:
            return {"status": "no_data", "message": "品質データがありません"}
        
        snapshots = list(self.file_quality_cache.values())
        
        # 品質レベル集計
        level_counts = {}
        for snapshot in snapshots:
            level = snapshot.quality_level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # 平均スコア計算
        avg_score = sum(s.overall_score for s in snapshots) / len(snapshots)
        
        # 最近の変更分析
        recent_changes = [s for s in snapshots if s.improvement is not None]
        improved_count = len([s for s in recent_changes if s.improvement > 0])
        degraded_count = len([s for s in recent_changes if s.improvement < 0])
        
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_files": len(snapshots),
            "average_score": avg_score,
            "quality_distribution": level_counts,
            "recent_changes": {
                "improved": improved_count,
                "degraded": degraded_count,
                "stable": len(recent_changes) - improved_count - degraded_count
            },
            "performance": self.performance_stats,
            "monitoring_active": self.monitoring_active
        }

# Mock classes for testing without dependencies
class MockQualityManager:
    def run_comprehensive_check(self, files, agent):
        return type('MockMetrics', (), {
            'syntax_score': 0.9,
            'type_score': 0.8,
            'lint_score': 0.85,
            'format_score': 0.95,
            'security_score': 0.9,
            'performance_score': 0.8,
            'overall_score': 0.85,
            'error_count': 2,
            'warning_count': 5
        })()

class MockQualityMonitor:
    def start_monitoring(self): pass
    def stop_monitoring(self): pass

def realtime_console_alert_handler(alert: QualityAlert) -> None:
    """リアルタイムコンソールアラートハンドラー"""
    level_icons = {
        AlertLevel.INFO: "ℹ️",
        AlertLevel.WARNING: "⚠️",
        AlertLevel.ERROR: "❌",
        AlertLevel.CRITICAL: "🚨"
    }
    
    icon = level_icons.get(alert.level, "📋")
    print(f"🔍 REALTIME {icon} [{alert.level.value.upper()}] {alert.category}: {alert.message}")
    if alert.affected_files:
        print(f"    影響ファイル: {alert.affected_files[0]}")

def main():
    """テスト実行"""
    print("🧪 EnhancedRealtimeQualityMonitor テスト開始")
    
    monitor = EnhancedRealtimeQualityMonitor(["kumihan_formatter/core/utilities/"])
    
    # アラート購読
    monitor.subscribe_to_realtime_alerts(realtime_console_alert_handler)
    
    # 監視開始
    monitor.start_realtime_monitoring()
    
    print("📊 リアルタイム監視テスト中... (10秒間)")
    
    # テスト用ファイル変更シミュレーション
    test_file = "kumihan_formatter/core/utilities/logger.py"
    if os.path.exists(test_file):
        print(f"🔄 テストファイル処理: {test_file}")
        monitor.process_file_change(test_file, FileChangeType.MODIFIED)
    
    time.sleep(10)
    
    # 概要確認
    overview = monitor.get_project_quality_overview()
    print("\n📊 プロジェクト品質概要:")
    print(f"   監視ファイル数: {overview.get('total_files', 0)}")
    print(f"   平均品質スコア: {overview.get('average_score', 0):.3f}")
    print(f"   処理ファイル数: {overview.get('performance', {}).get('files_processed', 0)}")
    
    # 監視停止
    monitor.stop_realtime_monitoring()
    
    print("✅ EnhancedRealtimeQualityMonitor テスト完了")

if __name__ == "__main__":
    main()