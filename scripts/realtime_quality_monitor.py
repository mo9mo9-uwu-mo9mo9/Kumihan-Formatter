#!/usr/bin/env python3
"""
Real-time Quality Monitor - Issue #640 Phase 2
リアルタイム品質監視システム

目的: コード変更のリアルタイム品質監視
- ファイル変更検知 → 即座に品質メトリクス更新
- 品質劣化の即座な通知
- VS Code統合表示
- TDDサイクル進捗の可視化
"""

import os
import sys
import time
import json
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from queue import Queue, Empty
import signal
import hashlib

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

@dataclass
class QualitySnapshot:
    """品質スナップショット"""
    timestamp: datetime
    commit_hash: str
    coverage_percentage: float
    test_count: int
    failed_tests: int
    complexity_score: float
    code_lines: int
    quality_score: float
    violations: List[str]
    tdd_phase: Optional[str]

@dataclass
class QualityAlert:
    """品質アラート"""
    alert_type: str  # "degradation", "improvement", "violation"
    severity: str   # "critical", "warning", "info"
    message: str
    before_value: float
    after_value: float
    threshold: float
    file_path: Optional[str]
    timestamp: datetime

class RealTimeQualityMonitor:
    """リアルタイム品質監視システム"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.monitor_config = self._load_monitor_config()
        
        # ディレクトリ設定
        self.quality_data_dir = project_root / ".quality_data"
        self.quality_data_dir.mkdir(exist_ok=True)
        
        # ファイルパス設定
        self.snapshots_file = self.quality_data_dir / "quality_snapshots.json"
        self.alerts_file = self.quality_data_dir / "quality_alerts.json"
        self.vscode_status_file = self.quality_data_dir / "vscode_status.json"
        
        # 監視状態
        self.running = False
        self.file_change_queue = Queue()
        self.quality_history = []
        self.current_snapshot = None
        self.last_file_hashes = {}
        
        # アラート設定
        self.alert_thresholds = {
            "coverage_drop": 5.0,      # カバレッジ5%以上の低下
            "complexity_increase": 3.0, # 複雑度3以上の増加
            "test_failure": 1,          # テスト失敗1件以上
            "quality_score_drop": 10.0  # 品質スコア10以上の低下
        }
        
        # シグナルハンドラー設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start_monitoring(self):
        """監視開始"""
        logger.info("🔍 リアルタイム品質監視を開始...")
        self.running = True
        
        # 初期スナップショット作成
        self._create_initial_snapshot()
        
        # 監視スレッド開始
        threads = [
            threading.Thread(target=self._file_watcher, daemon=True),
            threading.Thread(target=self._quality_analyzer, daemon=True),
            threading.Thread(target=self._alert_processor, daemon=True),
            threading.Thread(target=self._vscode_updater, daemon=True),
        ]
        
        for thread in threads:
            thread.start()
        
        logger.info("✅ リアルタイム品質監視開始完了")
        
        try:
            # メインループ
            while self.running:
                self._display_monitoring_status()
                time.sleep(10)  # 10秒間隔で状況表示
                
        except KeyboardInterrupt:
            self._shutdown()
    
    def _load_monitor_config(self) -> Dict:
        """監視設定読み込み"""
        default_config = {
            "watch_patterns": [
                "kumihan_formatter/**/*.py",
                "tests/**/*.py",
                "pyproject.toml",
                "Makefile"
            ],
            "ignore_patterns": [
                "**/__pycache__/**",
                "**/*.pyc",
                ".tdd_logs/**",
                ".quality_data/**"
            ],
            "quality_check_interval": 5,  # 秒
            "vscode_update_interval": 2,  # 秒
            "alert_cooldown": 30,         # 秒
            "snapshot_retention_days": 7
        }
        
        config_file = self.project_root / ".quality_monitor_config.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"設定ファイル読み込み失敗: {e}")
        
        return default_config
    
    def _file_watcher(self):
        """ファイル変更監視"""
        logger.info("👀 ファイル変更監視開始")
        
        while self.running:
            try:
                changed_files = self._detect_file_changes()
                
                for file_path in changed_files:
                    logger.debug(f"ファイル変更検出: {file_path}")
                    self.file_change_queue.put({
                        "type": "file_change",
                        "file_path": file_path,
                        "timestamp": datetime.now()
                    })
                
                time.sleep(1)  # 1秒間隔で監視
                
            except Exception as e:
                logger.error(f"ファイル監視エラー: {e}")
                time.sleep(5)
    
    def _detect_file_changes(self) -> List[Path]:
        """ファイル変更検出"""
        changed_files = []
        
        # 監視対象ファイル取得
        watch_files = set()
        for pattern in self.monitor_config["watch_patterns"]:
            matched_files = self.project_root.glob(pattern)
            watch_files.update(matched_files)
        
        # 除外パターンでフィルタリング
        for ignore_pattern in self.monitor_config["ignore_patterns"]:
            ignore_files = set(self.project_root.glob(ignore_pattern))
            watch_files -= ignore_files
        
        # ハッシュ比較で変更検出
        current_hashes = {}
        for file_path in watch_files:
            if file_path.is_file():
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                        file_hash = hashlib.md5(content).hexdigest()
                        current_hashes[str(file_path)] = file_hash
                        
                        # 変更検出
                        if str(file_path) in self.last_file_hashes:
                            if self.last_file_hashes[str(file_path)] != file_hash:
                                changed_files.append(file_path)
                        else:
                            # 新規ファイル
                            changed_files.append(file_path)
                            
                except Exception as e:
                    logger.debug(f"ファイルハッシュ計算失敗 {file_path}: {e}")
        
        self.last_file_hashes = current_hashes
        return changed_files
    
    def _quality_analyzer(self):
        """品質分析処理"""
        logger.info("📊 品質分析処理開始")
        
        last_analysis = datetime.now()
        
        while self.running:
            try:
                # ファイル変更があるかチェック
                has_changes = False
                try:
                    event = self.file_change_queue.get(timeout=1)
                    if event["type"] == "file_change":
                        has_changes = True
                        # キューをクリア（複数変更を一度に処理）
                        while True:
                            try:
                                self.file_change_queue.get_nowait()
                            except Empty:
                                break
                except Empty:
                    pass
                
                # 定期的または変更時に品質分析実行
                now = datetime.now()
                time_since_last = (now - last_analysis).total_seconds()
                
                if has_changes or time_since_last >= self.monitor_config["quality_check_interval"]:
                    new_snapshot = self._create_quality_snapshot()
                    
                    if new_snapshot:
                        self._process_quality_snapshot(new_snapshot)
                        last_analysis = now
                
                time.sleep(0.5)  # CPU使用率を抑制
                
            except Exception as e:
                logger.error(f"品質分析エラー: {e}")
                time.sleep(5)
    
    def _create_quality_snapshot(self) -> Optional[QualitySnapshot]:
        """品質スナップショット作成"""
        try:
            logger.debug("品質スナップショット作成中...")
            
            # カバレッジ・テスト実行
            coverage_cmd = [
                sys.executable, "-m", "pytest",
                "--cov=kumihan_formatter",
                "--cov-report=json:temp_coverage.json",
                "--tb=no", "-q", "--disable-warnings"
            ]
            
            result = subprocess.run(coverage_cmd, capture_output=True, text=True, 
                                  cwd=self.project_root, timeout=60)
            
            # メトリクス解析
            coverage_percentage = 0.0
            test_count = 0
            failed_tests = 0
            
            # カバレッジデータ
            coverage_file = self.project_root / "temp_coverage.json"
            if coverage_file.exists():
                try:
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                        coverage_percentage = coverage_data["totals"]["percent_covered"]
                except:
                    pass
                finally:
                    coverage_file.unlink(missing_ok=True)
            
            # テスト結果解析
            if result.stdout:
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if " passed" in line or " failed" in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == "passed" and i > 0:
                                try:
                                    test_count += int(parts[i-1])
                                except ValueError:
                                    pass
                            elif part == "failed" and i > 0:
                                try:
                                    failed_tests += int(parts[i-1])
                                except ValueError:
                                    pass
            
            # 追加メトリクス
            complexity_score = self._calculate_complexity()
            code_lines = self._count_source_lines()
            quality_score = self._calculate_quality_score(
                coverage_percentage, test_count, failed_tests, complexity_score
            )
            
            # 品質違反検出
            violations = self._detect_quality_violations(
                coverage_percentage, complexity_score, failed_tests
            )
            
            # TDDフェーズ取得
            tdd_phase = self._get_current_tdd_phase()
            
            # コミットハッシュ取得
            commit_hash = self._get_commit_hash()
            
            snapshot = QualitySnapshot(
                timestamp=datetime.now(),
                commit_hash=commit_hash,
                coverage_percentage=coverage_percentage,
                test_count=test_count,
                failed_tests=failed_tests,
                complexity_score=complexity_score,
                code_lines=code_lines,
                quality_score=quality_score,
                violations=violations,
                tdd_phase=tdd_phase
            )
            
            logger.debug(f"スナップショット作成完了: カバレッジ{coverage_percentage:.1f}%")
            return snapshot
            
        except subprocess.TimeoutExpired:
            logger.warning("品質分析タイムアウト")
            return None
        except Exception as e:
            logger.error(f"スナップショット作成失敗: {e}")
            return None
    
    def _process_quality_snapshot(self, snapshot: QualitySnapshot):
        """品質スナップショット処理"""
        # 履歴に追加
        self.quality_history.append(snapshot)
        
        # 古いデータ削除（保持期間を超えたもの）
        cutoff_date = datetime.now() - timedelta(days=self.monitor_config["snapshot_retention_days"])
        self.quality_history = [s for s in self.quality_history if s.timestamp > cutoff_date]
        
        # アラート生成
        if self.current_snapshot:
            alerts = self._generate_alerts(self.current_snapshot, snapshot)
            for alert in alerts:
                self._send_alert(alert)
        
        # 現在のスナップショット更新
        self.current_snapshot = snapshot
        
        # スナップショット保存
        self._save_snapshots()
    
    def _generate_alerts(self, before: QualitySnapshot, after: QualitySnapshot) -> List[QualityAlert]:
        """アラート生成"""
        alerts = []
        
        # カバレッジ低下チェック
        coverage_drop = before.coverage_percentage - after.coverage_percentage
        if coverage_drop >= self.alert_thresholds["coverage_drop"]:
            alerts.append(QualityAlert(
                alert_type="degradation",
                severity="warning",
                message=f"テストカバレッジが{coverage_drop:.1f}%低下しました",
                before_value=before.coverage_percentage,
                after_value=after.coverage_percentage,
                threshold=self.alert_thresholds["coverage_drop"],
                file_path=None,
                timestamp=datetime.now()
            ))
        
        # 複雑度増加チェック
        complexity_increase = after.complexity_score - before.complexity_score
        if complexity_increase >= self.alert_thresholds["complexity_increase"]:
            alerts.append(QualityAlert(
                alert_type="degradation",
                severity="warning",
                message=f"コード複雑度が{complexity_increase:.1f}増加しました",
                before_value=before.complexity_score,
                after_value=after.complexity_score,
                threshold=self.alert_thresholds["complexity_increase"],
                file_path=None,
                timestamp=datetime.now()
            ))
        
        # テスト失敗チェック
        if after.failed_tests > before.failed_tests:
            alerts.append(QualityAlert(
                alert_type="violation",
                severity="critical",
                message=f"テスト失敗が{after.failed_tests - before.failed_tests}件増加しました",
                before_value=float(before.failed_tests),
                after_value=float(after.failed_tests),
                threshold=float(self.alert_thresholds["test_failure"]),
                file_path=None,
                timestamp=datetime.now()
            ))
        
        # 品質スコア低下チェック
        quality_drop = before.quality_score - after.quality_score
        if quality_drop >= self.alert_thresholds["quality_score_drop"]:
            alerts.append(QualityAlert(
                alert_type="degradation",
                severity="warning",
                message=f"品質スコアが{quality_drop:.1f}低下しました",
                before_value=before.quality_score,
                after_value=after.quality_score,
                threshold=self.alert_thresholds["quality_score_drop"],
                file_path=None,
                timestamp=datetime.now()
            ))
        
        # 改善の場合もアラート
        if coverage_drop < -5.0:  # 5%以上向上
            alerts.append(QualityAlert(
                alert_type="improvement",
                severity="info",
                message=f"テストカバレッジが{-coverage_drop:.1f}%向上しました",
                before_value=before.coverage_percentage,
                after_value=after.coverage_percentage,
                threshold=5.0,
                file_path=None,
                timestamp=datetime.now()
            ))
        
        return alerts
    
    def _send_alert(self, alert: QualityAlert):
        """アラート送信"""
        logger.info(f"🚨 {alert.severity.upper()}: {alert.message}")
        
        # デスクトップ通知（macOS）
        try:
            if sys.platform == "darwin":
                icon = "⚠️" if alert.severity == "warning" else "🚨" if alert.severity == "critical" else "📈"
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{alert.message}" with title "{icon} 品質監視アラート" sound name "Glass"'
                ], check=False)
        except:
            pass
        
        # アラート履歴保存
        self._save_alert(alert)
    
    def _alert_processor(self):
        """アラート処理スレッド"""
        logger.info("🚨 アラート処理開始")
        
        while self.running:
            try:
                # アラート処理ロジック（将来の拡張用）
                time.sleep(5)
            except Exception as e:
                logger.error(f"アラート処理エラー: {e}")
                time.sleep(5)
    
    def _vscode_updater(self):
        """VS Code統合更新"""
        logger.info("💻 VS Code統合更新開始")
        
        while self.running:
            try:
                if self.current_snapshot:
                    self._update_vscode_status()
                    
                time.sleep(self.monitor_config["vscode_update_interval"])
                
            except Exception as e:
                logger.error(f"VS Code更新エラー: {e}")
                time.sleep(5)
    
    def _update_vscode_status(self):
        """VS Codeステータス更新"""
        if not self.current_snapshot:
            return
            
        # VS Code拡張用のステータスファイル更新
        status_data = {
            "timestamp": self.current_snapshot.timestamp.isoformat(),
            "coverage": {
                "percentage": self.current_snapshot.coverage_percentage,
                "status": self._get_coverage_status(self.current_snapshot.coverage_percentage)
            },
            "tests": {
                "total": self.current_snapshot.test_count,
                "failed": self.current_snapshot.failed_tests,
                "passed": self.current_snapshot.test_count - self.current_snapshot.failed_tests
            },
            "quality": {
                "score": self.current_snapshot.quality_score,
                "complexity": self.current_snapshot.complexity_score,
                "violations": self.current_snapshot.violations
            },
            "tdd": {
                "phase": self.current_snapshot.tdd_phase,
                "status": self._get_tdd_status()
            },
            "alerts": self._get_recent_alerts()
        }
        
        with open(self.vscode_status_file, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
    
    def _get_coverage_status(self, percentage: float) -> str:
        """カバレッジステータス取得"""
        if percentage >= 90:
            return "excellent"
        elif percentage >= 75:
            return "good"
        elif percentage >= 60:
            return "fair"
        else:
            return "poor"
    
    def _get_tdd_status(self) -> str:
        """TDDステータス取得"""
        session_file = self.project_root / ".tdd_session.json"
        if session_file.exists():
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session = json.load(f)
                    return f"active_{session.get('current_phase', 'unknown')}"
            except:
                pass
        return "inactive"
    
    def _get_recent_alerts(self) -> List[Dict]:
        """最近のアラート取得"""
        alerts_file = self.alerts_file
        if not alerts_file.exists():
            return []
            
        try:
            with open(alerts_file, "r", encoding="utf-8") as f:
                all_alerts = json.load(f)
                
            # 最近1時間のアラート
            recent_cutoff = datetime.now() - timedelta(hours=1)
            recent_alerts = []
            
            for alert_data in all_alerts[-10:]:  # 最新10件
                alert_time = datetime.fromisoformat(alert_data["timestamp"])
                if alert_time > recent_cutoff:
                    recent_alerts.append(alert_data)
                    
            return recent_alerts
            
        except Exception as e:
            logger.debug(f"アラート履歴読み込み失敗: {e}")
            return []
    
    def _calculate_complexity(self) -> float:
        """複雑度計算"""
        try:
            # Pythonファイルの行数ベース簡易計算
            py_files = list((self.project_root / "kumihan_formatter").rglob("*.py"))
            if not py_files:
                return 0.0
                
            total_lines = 0
            total_functions = 0
            
            for py_file in py_files[:20]:  # サンプリング
                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        lines = [l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]
                        total_lines += len(lines)
                        total_functions += content.count('def ')
                except:
                    continue
            
            return total_lines / max(total_functions, 1)
            
        except Exception as e:
            logger.debug(f"複雑度計算失敗: {e}")
            return 10.0
    
    def _count_source_lines(self) -> int:
        """ソースコード行数カウント"""
        try:
            py_files = list((self.project_root / "kumihan_formatter").rglob("*.py"))
            total_lines = 0
            
            for py_file in py_files:
                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        lines = [l for l in f if l.strip() and not l.strip().startswith('#')]
                        total_lines += len(lines)
                except:
                    continue
                    
            return total_lines
            
        except Exception as e:
            logger.debug(f"行数計算失敗: {e}")
            return 0
    
    def _calculate_quality_score(self, coverage: float, test_count: int, failed_tests: int, complexity: float) -> float:
        """品質スコア計算"""
        # カバレッジ40% + テスト成功率30% + 複雑度30%
        coverage_score = min(coverage / 100, 1.0) * 40
        
        test_success_rate = (test_count - failed_tests) / max(test_count, 1)
        test_score = test_success_rate * 30
        
        complexity_score = max(0, (20 - complexity) / 20) * 30
        
        return coverage_score + test_score + complexity_score
    
    def _detect_quality_violations(self, coverage: float, complexity: float, failed_tests: int) -> List[str]:
        """品質違反検出"""
        violations = []
        
        if coverage < 70:
            violations.append(f"カバレッジ不足: {coverage:.1f}% < 70%")
        
        if complexity > 15:
            violations.append(f"複雑度超過: {complexity:.1f} > 15")
        
        if failed_tests > 0:
            violations.append(f"テスト失敗: {failed_tests}件")
        
        return violations
    
    def _get_current_tdd_phase(self) -> Optional[str]:
        """現在のTDDフェーズ取得"""
        session_file = self.project_root / ".tdd_session.json"
        if session_file.exists():
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session = json.load(f)
                    return session.get("current_phase")
            except:
                pass
        return None
    
    def _get_commit_hash(self) -> str:
        """コミットハッシュ取得"""
        try:
            result = subprocess.run(["git", "rev-parse", "HEAD"], 
                                  capture_output=True, text=True, cwd=self.project_root)
            return result.stdout.strip()[:8]
        except:
            return "unknown"
    
    def _create_initial_snapshot(self):
        """初期スナップショット作成"""
        logger.info("📸 初期品質スナップショット作成中...")
        snapshot = self._create_quality_snapshot()
        if snapshot:
            self.current_snapshot = snapshot
            self.quality_history.append(snapshot)
            self._save_snapshots()
            logger.info(f"✅ 初期スナップショット作成完了: カバレッジ{snapshot.coverage_percentage:.1f}%")
        else:
            logger.warning("初期スナップショット作成に失敗しました")
    
    def _save_snapshots(self):
        """スナップショット保存"""
        try:
            snapshots_data = [asdict(s) for s in self.quality_history]
            # datetime を文字列に変換
            for snapshot in snapshots_data:
                snapshot["timestamp"] = snapshot["timestamp"].isoformat()
                
            with open(self.snapshots_file, "w", encoding="utf-8") as f:
                json.dump(snapshots_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"スナップショット保存失敗: {e}")
    
    def _save_alert(self, alert: QualityAlert):
        """アラート保存"""
        try:
            alerts_data = []
            if self.alerts_file.exists():
                with open(self.alerts_file, "r", encoding="utf-8") as f:
                    alerts_data = json.load(f)
            
            alert_dict = asdict(alert)
            alert_dict["timestamp"] = alert.timestamp.isoformat()
            alerts_data.append(alert_dict)
            
            # 最新100件のみ保持
            alerts_data = alerts_data[-100:]
            
            with open(self.alerts_file, "w", encoding="utf-8") as f:
                json.dump(alerts_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"アラート保存失敗: {e}")
    
    def _display_monitoring_status(self):
        """監視状況表示"""
        if not self.current_snapshot:
            return
            
        snapshot = self.current_snapshot
        
        print(f"\r🔍 品質監視中 | カバレッジ: {snapshot.coverage_percentage:.1f}% | "
              f"品質スコア: {snapshot.quality_score:.1f} | "
              f"テスト: {snapshot.test_count - snapshot.failed_tests}/{snapshot.test_count} | "
              f"TDD: {snapshot.tdd_phase or 'inactive'}", end="", flush=True)
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"\nシグナル {signum} 受信。監視を停止中...")
        self._shutdown()
    
    def _shutdown(self):
        """監視停止"""
        logger.info("🛑 リアルタイム品質監視を停止中...")
        self.running = False
        
        # 最終スナップショット保存
        if self.current_snapshot:
            self._save_snapshots()
        
        logger.info("👋 リアルタイム品質監視停止完了")

def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent
    
    monitor = RealTimeQualityMonitor(project_root)
    
    logger.info("🚀 リアルタイム品質監視システム起動 - Issue #640 Phase 2")
    
    # 監視開始
    monitor.start_monitoring()

if __name__ == "__main__":
    main()