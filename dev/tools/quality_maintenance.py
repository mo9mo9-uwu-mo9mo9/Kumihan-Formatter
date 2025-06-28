#!/usr/bin/env python3
"""
品質システム運用監視・保守ツール

品質データのバックアップ、定期実行、システム健全性チェックなどを行う
"""

import json
import os
import shutil
import subprocess
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
# import schedule
import time

from quality_trend_tracker import QualityTrendTracker
from quality_report_generator import QualityReportGenerator


class QualityMaintenanceSystem:
    """品質システム保守管理"""
    
    def __init__(self, config_path: Path = None):
        self.config = self._load_config(config_path)
        self.tracker = QualityTrendTracker()
        self.report_generator = QualityReportGenerator(self.tracker)
        self.backup_dir = Path("dev/data/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, config_path: Path = None) -> Dict[str, Any]:
        """保守設定を読み込み"""
        default_config = {
            "backup": {
                "enabled": True,
                "retention_days": 90,
                "frequency_hours": 24
            },
            "monitoring": {
                "health_check_interval": 6,  # hours
                "alert_threshold": 5.0,  # quality score drop
                "notification_email": "",
                "slack_webhook": ""
            },
            "maintenance": {
                "cleanup_old_data": True,
                "vacuum_database": True,
                "generate_weekly_reports": True
            },
            "thresholds": {
                "min_quality_score": 70.0,
                "max_db_size_mb": 100,
                "max_log_files": 50
            }
        }
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception:
                pass
        
        return default_config
    
    def backup_quality_data(self) -> str:
        """品質データのバックアップ"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"quality_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            backup_path.mkdir(exist_ok=True)
            
            # データベースバックアップ
            db_path = Path("dev/data/quality_history.db")
            if db_path.exists():
                shutil.copy2(db_path, backup_path / "quality_history.db")
            
            # 設定ファイルバックアップ
            config_files = [
                "dev/data/current_metrics.json",
                ".github/workflows/quality-monitoring.yml"
            ]
            
            for config_file in config_files:
                src_path = Path(config_file)
                if src_path.exists():
                    dst_path = backup_path / src_path.name
                    shutil.copy2(src_path, dst_path)
            
            # メタデータ作成
            metadata = {
                "backup_timestamp": timestamp,
                "backup_type": "automatic",
                "files_backed_up": list(backup_path.glob("*")),
                "total_size_bytes": sum(f.stat().st_size for f in backup_path.glob("*")),
                "retention_until": (datetime.now() + timedelta(days=self.config['backup']['retention_days'])).isoformat()
            }
            
            with open(backup_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ バックアップ完了: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            print(f"❌ バックアップ失敗: {e}")
            return ""
    
    def cleanup_old_backups(self) -> int:
        """古いバックアップの削除"""
        retention_days = self.config['backup']['retention_days']
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        removed_count = 0
        
        for backup_dir in self.backup_dir.glob("quality_backup_*"):
            if backup_dir.is_dir():
                metadata_file = backup_dir / "metadata.json"
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        backup_time = datetime.fromisoformat(metadata['backup_timestamp'])
                        
                        if backup_time < cutoff_date:
                            shutil.rmtree(backup_dir)
                            removed_count += 1
                            print(f"🗑️  古いバックアップを削除: {backup_dir.name}")
                    
                    except Exception as e:
                        print(f"⚠️ バックアップメタデータ読み込み失敗: {backup_dir.name} - {e}")
        
        print(f"✅ 古いバックアップ削除完了: {removed_count}件")
        return removed_count
    
    def health_check(self) -> Dict[str, Any]:
        """システム健全性チェック"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }
        
        # データベース健全性チェック
        db_health = self._check_database_health()
        health_status["checks"]["database"] = db_health
        
        # 品質データ整合性チェック
        data_integrity = self._check_data_integrity()
        health_status["checks"]["data_integrity"] = data_integrity
        
        # ディスク使用量チェック
        disk_usage = self._check_disk_usage()
        health_status["checks"]["disk_usage"] = disk_usage
        
        # 品質トレンドチェック
        quality_trend = self._check_quality_trend()
        health_status["checks"]["quality_trend"] = quality_trend
        
        # 全体ステータス判定
        failed_checks = [name for name, check in health_status["checks"].items() if not check["status"]]
        
        if failed_checks:
            health_status["overall_status"] = "warning" if len(failed_checks) == 1 else "critical"
            health_status["failed_checks"] = failed_checks
        
        return health_status
    
    def _check_database_health(self) -> Dict[str, Any]:
        """データベース健全性チェック"""
        try:
            db_path = Path("dev/data/quality_history.db")
            
            if not db_path.exists():
                return {"status": False, "message": "データベースファイルが存在しません"}
            
            # データベース接続テスト
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM quality_snapshots")
                record_count = cursor.fetchone()[0]
            
            # データベースサイズチェック
            db_size_mb = db_path.stat().st_size / (1024 * 1024)
            max_size_mb = self.config['thresholds']['max_db_size_mb']
            
            if db_size_mb > max_size_mb:
                return {
                    "status": False,
                    "message": f"データベースサイズが上限を超過: {db_size_mb:.1f}MB > {max_size_mb}MB",
                    "record_count": record_count,
                    "size_mb": db_size_mb
                }
            
            return {
                "status": True,
                "message": "データベースは健全です",
                "record_count": record_count,
                "size_mb": db_size_mb
            }
            
        except Exception as e:
            return {"status": False, "message": f"データベースエラー: {e}"}
    
    def _check_data_integrity(self) -> Dict[str, Any]:
        """データ整合性チェック"""
        try:
            recent_snapshots = self.tracker.get_recent_snapshots(days=7)
            
            if len(recent_snapshots) == 0:
                return {"status": False, "message": "直近7日間のデータが存在しません"}
            
            # データの一貫性チェック
            invalid_scores = [s for s in recent_snapshots if s.total_score < 0 or s.total_score > 100]
            
            if invalid_scores:
                return {
                    "status": False,
                    "message": f"無効なスコアデータが{len(invalid_scores)}件あります",
                    "recent_count": len(recent_snapshots)
                }
            
            return {
                "status": True,
                "message": "データ整合性は良好です",
                "recent_count": len(recent_snapshots)
            }
            
        except Exception as e:
            return {"status": False, "message": f"データ整合性チェックエラー: {e}"}
    
    def _check_disk_usage(self) -> Dict[str, Any]:
        """ディスク使用量チェック"""
        try:
            data_dir = Path("dev/data")
            total_size = sum(f.stat().st_size for f in data_dir.rglob("*") if f.is_file())
            total_size_mb = total_size / (1024 * 1024)
            
            # ログファイル数チェック
            log_files = list(data_dir.glob("*.log"))
            max_log_files = self.config['thresholds']['max_log_files']
            
            issues = []
            if len(log_files) > max_log_files:
                issues.append(f"ログファイル数が上限を超過: {len(log_files)} > {max_log_files}")
            
            return {
                "status": len(issues) == 0,
                "message": "ディスク使用量は正常です" if not issues else "; ".join(issues),
                "total_size_mb": total_size_mb,
                "log_file_count": len(log_files)
            }
            
        except Exception as e:
            return {"status": False, "message": f"ディスク使用量チェックエラー: {e}"}
    
    def _check_quality_trend(self) -> Dict[str, Any]:
        """品質トレンドチェック"""
        try:
            trends = self.tracker.analyze_trends(days=7)
            
            if trends.get('trend') == 'insufficient_data':
                return {"status": False, "message": "トレンド分析用のデータが不足しています"}
            
            # 品質劣化チェック
            degradation = self.tracker.detect_quality_degradation()
            
            if degradation and degradation.get('degradation_detected'):
                return {
                    "status": False,
                    "message": f"品質劣化を検出: -{degradation['degradation_amount']:.1f}ポイント",
                    "trend": trends['trend'],
                    "latest_score": degradation['latest_score']
                }
            
            # 最小品質スコアチェック
            min_score = self.config['thresholds']['min_quality_score']
            latest_score = trends.get('latest_score', 0)
            
            if latest_score < min_score:
                return {
                    "status": False,
                    "message": f"品質スコアが最小閾値を下回っています: {latest_score:.1f} < {min_score}",
                    "trend": trends['trend'],
                    "latest_score": latest_score
                }
            
            return {
                "status": True,
                "message": "品質トレンドは良好です",
                "trend": trends['trend'],
                "latest_score": latest_score
            }
            
        except Exception as e:
            return {"status": False, "message": f"品質トレンドチェックエラー: {e}"}
    
    def vacuum_database(self) -> bool:
        """データベース最適化"""
        try:
            db_path = Path("dev/data/quality_history.db")
            
            if not db_path.exists():
                print("❌ データベースファイルが存在しません")
                return False
            
            with sqlite3.connect(db_path) as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
            
            print("✅ データベース最適化完了")
            return True
            
        except Exception as e:
            print(f"❌ データベース最適化失敗: {e}")
            return False
    
    def generate_weekly_report(self) -> str:
        """週次品質レポート生成"""
        try:
            report = self.tracker.generate_trend_report(days=7)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = Path(f"dev/data/weekly_report_{timestamp}.md")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"✅ 週次レポート生成完了: {report_path}")
            return str(report_path)
            
        except Exception as e:
            print(f"❌ 週次レポート生成失敗: {e}")
            return ""
    
    def run_scheduled_maintenance(self):
        """定期保守実行"""
        print(f"🔧 定期保守開始: {datetime.now()}")
        
        # バックアップ
        if self.config['backup']['enabled']:
            self.backup_quality_data()
            self.cleanup_old_backups()
        
        # データベース最適化
        if self.config['maintenance']['vacuum_database']:
            self.vacuum_database()
        
        # 健全性チェック
        health = self.health_check()
        print(f"🏥 システム健全性: {health['overall_status']}")
        
        if health['overall_status'] != 'healthy':
            print("⚠️ 健全性チェックで問題が検出されました:")
            for check_name, check_result in health['checks'].items():
                if not check_result['status']:
                    print(f"  - {check_name}: {check_result['message']}")
        
        # 週次レポート
        if self.config['maintenance']['generate_weekly_reports']:
            # 月曜日に実行
            if datetime.now().weekday() == 0:
                self.generate_weekly_report()
        
        print(f"✅ 定期保守完了: {datetime.now()}")


def main():
    parser = argparse.ArgumentParser(description="品質システム保守ツール")
    parser.add_argument('command', choices=[
        'backup', 'cleanup', 'health-check', 'vacuum', 
        'weekly-report', 'scheduled', 'daemon'
    ], help='実行するコマンド')
    parser.add_argument('--config', type=Path, help='設定ファイルパス')
    
    args = parser.parse_args()
    
    maintenance = QualityMaintenanceSystem(args.config)
    
    if args.command == 'backup':
        maintenance.backup_quality_data()
    
    elif args.command == 'cleanup':
        maintenance.cleanup_old_backups()
    
    elif args.command == 'health-check':
        health = maintenance.health_check()
        print(json.dumps(health, indent=2, ensure_ascii=False))
    
    elif args.command == 'vacuum':
        maintenance.vacuum_database()
    
    elif args.command == 'weekly-report':
        maintenance.generate_weekly_report()
    
    elif args.command == 'scheduled':
        maintenance.run_scheduled_maintenance()
    
    elif args.command == 'daemon':
        print("🤖 品質保守デーモン開始...")
        print("⚠️ デーモンモードは簡易版です（scheduleライブラリ未インストール）")
        
        # 簡易スケジューラー
        last_maintenance = datetime.now() - timedelta(hours=25)  # 初回実行のため
        
        try:
            while True:
                now = datetime.now()
                
                # 24時間ごとに保守実行
                if (now - last_maintenance).total_seconds() >= 24 * 3600:
                    maintenance.run_scheduled_maintenance()
                    last_maintenance = now
                
                # 6時間ごとにハートビート
                if now.minute == 0 and now.second < 10:  # 毎時0分頃
                    print(f"💓 ハートビート: {now}")
                
                time.sleep(60)  # 1分間隔でチェック
        except KeyboardInterrupt:
            print("\n🛑 品質保守デーモン停止")


if __name__ == "__main__":
    main()