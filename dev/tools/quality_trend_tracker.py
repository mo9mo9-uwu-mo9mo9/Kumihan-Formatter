#!/usr/bin/env python3
"""
品質トレンド監視システム

品質メトリクスの履歴を記録し、トレンド分析や劣化検出を行う
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import argparse


@dataclass
class QualitySnapshot:
    """品質スナップショット"""
    timestamp: str
    commit_hash: str
    branch_name: str
    total_score: float
    syntax_pass_rate: float
    test_pass_rate: float
    test_coverage: float
    performance_score: float
    file_count: int
    test_count: int
    
    # 詳細メトリクス
    conversion_time_avg: float
    conversion_time_max: float
    syntax_errors: int
    failed_tests: int
    
    # メタデータ
    environment: str  # CI, local, etc.
    version: str
    
    @classmethod
    def from_quality_metrics(cls, metrics_data: Dict[str, Any], 
                           commit_hash: str = "", branch_name: str = "", 
                           environment: str = "local", version: str = ""):
        """品質メトリクスデータからスナップショットを作成"""
        return cls(
            timestamp=datetime.now().isoformat(),
            commit_hash=commit_hash,
            branch_name=branch_name,
            total_score=metrics_data.get('overall_quality_score', 0.0),
            syntax_pass_rate=metrics_data.get('syntax_pass_rate', 0.0),
            test_pass_rate=metrics_data.get('test_pass_rate', 0.0),
            test_coverage=metrics_data.get('test_coverage', 0.0),
            performance_score=100.0 - (metrics_data.get('conversion_time_avg', 0.0) * 20),
            file_count=metrics_data.get('total_files', 0),
            test_count=metrics_data.get('passed_count', 0) + metrics_data.get('failed_count', 0),
            conversion_time_avg=metrics_data.get('conversion_time_avg', 0.0),
            conversion_time_max=metrics_data.get('conversion_time_max', 0.0),
            syntax_errors=metrics_data.get('syntax_errors', 0),
            failed_tests=metrics_data.get('failed_count', 0),
            environment=environment,
            version=version
        )


class QualityTrendTracker:
    """品質トレンド追跡システム"""
    
    def __init__(self, db_path: Path = None):
        if db_path is None:
            db_path = Path("dev/data/quality_history.db")
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    commit_hash TEXT,
                    branch_name TEXT,
                    total_score REAL NOT NULL,
                    syntax_pass_rate REAL,
                    test_pass_rate REAL,
                    test_coverage REAL,
                    performance_score REAL,
                    file_count INTEGER,
                    test_count INTEGER,
                    conversion_time_avg REAL,
                    conversion_time_max REAL,
                    syntax_errors INTEGER,
                    failed_tests INTEGER,
                    environment TEXT,
                    version TEXT,
                    raw_data TEXT  -- JSON形式で元データも保存
                )
            """)
            
            # インデックス作成
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON quality_snapshots(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_branch ON quality_snapshots(branch_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_commit ON quality_snapshots(commit_hash)")
    
    def record_snapshot(self, snapshot: QualitySnapshot, raw_data: Dict[str, Any] = None):
        """品質スナップショットを記録"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO quality_snapshots (
                    timestamp, commit_hash, branch_name, total_score,
                    syntax_pass_rate, test_pass_rate, test_coverage, performance_score,
                    file_count, test_count, conversion_time_avg, conversion_time_max,
                    syntax_errors, failed_tests, environment, version, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.timestamp, snapshot.commit_hash, snapshot.branch_name,
                snapshot.total_score, snapshot.syntax_pass_rate, snapshot.test_pass_rate,
                snapshot.test_coverage, snapshot.performance_score, snapshot.file_count,
                snapshot.test_count, snapshot.conversion_time_avg, snapshot.conversion_time_max,
                snapshot.syntax_errors, snapshot.failed_tests, snapshot.environment,
                snapshot.version, json.dumps(raw_data) if raw_data else None
            ))
    
    def get_recent_snapshots(self, days: int = 30, branch: str = None) -> List[QualitySnapshot]:
        """最近の品質スナップショットを取得"""
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = """
            SELECT timestamp, commit_hash, branch_name, total_score,
                   syntax_pass_rate, test_pass_rate, test_coverage, performance_score,
                   file_count, test_count, conversion_time_avg, conversion_time_max,
                   syntax_errors, failed_tests, environment, version
            FROM quality_snapshots 
            WHERE timestamp >= ?
        """
        params = [since_date]
        
        if branch:
            query += " AND branch_name = ?"
            params.append(branch)
        
        query += " ORDER BY timestamp DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
            
        return [QualitySnapshot(*row) for row in rows]
    
    def analyze_trends(self, days: int = 30, branch: str = None) -> Dict[str, Any]:
        """品質トレンドを分析"""
        snapshots = self.get_recent_snapshots(days, branch)
        
        if len(snapshots) < 2:
            return {
                "trend": "insufficient_data",
                "message": "トレンド分析には最低2つのデータポイントが必要です",
                "snapshots_count": len(snapshots)
            }
        
        # 最新と最古のスナップショットで比較
        latest = snapshots[0]
        oldest = snapshots[-1]
        
        score_change = latest.total_score - oldest.total_score
        test_change = latest.test_pass_rate - oldest.test_pass_rate
        coverage_change = latest.test_coverage - oldest.test_coverage
        
        # トレンド判定
        if score_change >= 5.0:
            trend = "improving"
            trend_emoji = "📈"
        elif score_change <= -5.0:
            trend = "declining"
            trend_emoji = "📉"
        else:
            trend = "stable"
            trend_emoji = "➡️"
        
        # 平均品質スコア
        avg_score = sum(s.total_score for s in snapshots) / len(snapshots)
        
        return {
            "trend": trend,
            "trend_emoji": trend_emoji,
            "score_change": score_change,
            "test_change": test_change,
            "coverage_change": coverage_change,
            "average_score": avg_score,
            "latest_score": latest.total_score,
            "oldest_score": oldest.total_score,
            "snapshots_count": len(snapshots),
            "period_days": days,
            "analysis_date": datetime.now().isoformat()
        }
    
    def detect_quality_degradation(self, threshold: float = 5.0, 
                                 recent_count: int = 5) -> Optional[Dict[str, Any]]:
        """品質劣化を検出"""
        recent_snapshots = self.get_recent_snapshots(days=7)[:recent_count]
        
        if len(recent_snapshots) < recent_count:
            return None
        
        # 最新のスコアと平均スコアを比較
        latest_score = recent_snapshots[0].total_score
        avg_score = sum(s.total_score for s in recent_snapshots[1:]) / (len(recent_snapshots) - 1)
        
        degradation = avg_score - latest_score
        
        if degradation >= threshold:
            return {
                "degradation_detected": True,
                "severity": "high" if degradation >= 10.0 else "medium",
                "degradation_amount": degradation,
                "latest_score": latest_score,
                "average_score": avg_score,
                "threshold": threshold,
                "detection_time": datetime.now().isoformat(),
                "affected_snapshots": len(recent_snapshots)
            }
        
        return {
            "degradation_detected": False,
            "latest_score": latest_score,
            "average_score": avg_score,
            "degradation_amount": degradation
        }
    
    def generate_trend_report(self, days: int = 30, branch: str = None) -> str:
        """品質トレンドレポートを生成"""
        trends = self.analyze_trends(days, branch)
        degradation = self.detect_quality_degradation()
        recent_snapshots = self.get_recent_snapshots(days, branch)[:10]
        
        # データ不足の場合の処理
        if trends.get('trend') == 'insufficient_data':
            return f"""
🔍 Kumihan-Formatter 品質トレンドレポート
{'=' * 50}
生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
分析期間: 直近{days}日間

⚠️ データ不足
-------------
{trends['message']}
記録されたスナップショット数: {trends['snapshots_count']}

トレンド分析には最低2つのデータポイントが必要です。
継続的に品質メトリクスを記録してください。
"""
        
        trend_emoji = trends.get('trend_emoji', '❓')
        
        report = f"""
🔍 Kumihan-Formatter 品質トレンドレポート
{'=' * 50}
生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
分析期間: 直近{days}日間
対象ブランチ: {branch or '全ブランチ'}

📊 トレンド分析
--------------
{trend_emoji} 総合トレンド: {trends['trend']}
品質スコア変化: {trends['score_change']:+.1f} ({trends['oldest_score']:.1f} → {trends['latest_score']:.1f})
テスト合格率変化: {trends['test_change']:+.1f}%
カバレッジ変化: {trends['coverage_change']:+.1f}%
期間平均スコア: {trends['average_score']:.1f}/100

🚨 品質劣化検出
---------------
"""
        
        if degradation and degradation.get('degradation_detected'):
            report += f"""❌ 品質劣化を検出しました！
重要度: {degradation['severity']}
劣化量: -{degradation['degradation_amount']:.1f}ポイント
最新スコア: {degradation['latest_score']:.1f}/100
平均スコア: {degradation['average_score']:.1f}/100
検出時刻: {degradation['detection_time']}
"""
        else:
            report += "✅ 品質劣化は検出されていません\n"
        
        report += f"""
📈 最近の品質スナップショット
----------------------------
"""
        for i, snapshot in enumerate(recent_snapshots[:5]):
            timestamp = datetime.fromisoformat(snapshot.timestamp).strftime('%m-%d %H:%M')
            report += f"{i+1}. {timestamp} | スコア: {snapshot.total_score:.1f} | テスト: {snapshot.test_pass_rate:.1f}% | ブランチ: {snapshot.branch_name}\n"
        
        if len(recent_snapshots) > 5:
            report += f"... 他{len(recent_snapshots)-5}件\n"
        
        report += f"""
📋 統計サマリー
--------------
記録されたスナップショット数: {len(recent_snapshots)}
分析対象期間: {days}日間
データ品質: {'良好' if len(recent_snapshots) >= 5 else '不十分（5件未満）'}

💡 推奨アクション
----------------
"""
        
        if trends['trend'] == 'declining':
            report += "- 🔴 品質低下トレンドです。原因調査と改善措置が必要です\n"
        elif trends['trend'] == 'improving':
            report += "- 🟢 品質向上トレンドです。現在の開発方針を継続してください\n"
        else:
            report += "- 🟡 品質は安定しています。継続的な監視を推奨します\n"
        
        if degradation and degradation.get('degradation_detected'):
            report += "- 🚨 緊急: 品質劣化が検出されました。即座の対応が必要です\n"
        
        return report
    
    def export_data(self, output_path: Path, format: str = "json", days: int = 30):
        """品質データをエクスポート"""
        snapshots = self.get_recent_snapshots(days)
        
        if format == "json":
            data = {
                "export_date": datetime.now().isoformat(),
                "period_days": days,
                "snapshots": [asdict(s) for s in snapshots]
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            import csv
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if snapshots:
                    writer = csv.DictWriter(f, fieldnames=list(asdict(snapshots[0]).keys()))
                    writer.writeheader()
                    for snapshot in snapshots:
                        writer.writerow(asdict(snapshot))


def main():
    parser = argparse.ArgumentParser(description="品質トレンド監視システム")
    parser.add_argument('command', choices=['record', 'analyze', 'report', 'export'], 
                       help='実行するコマンド')
    parser.add_argument('--metrics-file', type=Path, 
                       help='品質メトリクスJSONファイル')
    parser.add_argument('--commit', default="", help='コミットハッシュ')
    parser.add_argument('--branch', default="", help='ブランチ名')
    parser.add_argument('--environment', default="local", help='実行環境')
    parser.add_argument('--days', type=int, default=30, help='分析期間（日数）')
    parser.add_argument('--output', type=Path, help='出力ファイルパス')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', 
                       help='エクスポート形式')
    
    args = parser.parse_args()
    
    tracker = QualityTrendTracker()
    
    if args.command == 'record':
        if not args.metrics_file or not args.metrics_file.exists():
            print("❌ エラー: --metrics-file が必要です")
            return
        
        with open(args.metrics_file, 'r', encoding='utf-8') as f:
            metrics_data = json.load(f)
        
        snapshot = QualitySnapshot.from_quality_metrics(
            metrics_data, args.commit, args.branch, args.environment
        )
        tracker.record_snapshot(snapshot, metrics_data)
        print(f"✅ 品質スナップショットを記録しました: {snapshot.total_score:.1f}/100")
    
    elif args.command == 'analyze':
        trends = tracker.analyze_trends(args.days, args.branch)
        print(f"📊 品質トレンド分析 (直近{args.days}日間)")
        print(f"トレンド: {trends['trend_emoji']} {trends['trend']}")
        print(f"スコア変化: {trends['score_change']:+.1f}")
        print(f"平均スコア: {trends['average_score']:.1f}/100")
    
    elif args.command == 'report':
        report = tracker.generate_trend_report(args.days, args.branch)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 レポートを出力しました: {args.output}")
        else:
            print(report)
    
    elif args.command == 'export':
        if not args.output:
            print("❌ エラー: --output が必要です")
            return
        
        tracker.export_data(args.output, args.format, args.days)
        print(f"📁 データをエクスポートしました: {args.output}")


if __name__ == "__main__":
    main()