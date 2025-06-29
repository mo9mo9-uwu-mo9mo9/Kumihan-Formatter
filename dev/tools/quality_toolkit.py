#!/usr/bin/env python3
"""
Kumihan-Formatter 品質管理統合ツールキット

品質管理、トレンド監視、メトリクス収集を統合したツール。
プロジェクトの品質を包括的に管理・監視する。

使用方法:
    # 品質メトリクス収集・分析
    python dev/tools/quality_toolkit.py --analyze
    
    # 品質ゲートチェック
    python dev/tools/quality_toolkit.py --gate-check
    
    # 品質レポート生成
    python dev/tools/quality_toolkit.py --report
    
    # 品質保守（清掃・最適化）
    python dev/tools/quality_toolkit.py --maintenance
    
    # トレンド監視・履歴記録
    python dev/tools/quality_toolkit.py --trend-snapshot
    
    # 統合品質チェック（推奨）
    python dev/tools/quality_toolkit.py --full-check
"""

import sys
import json
import argparse
import sqlite3
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class QualityMetrics:
    """品質メトリクス"""
    total_score: float
    syntax_pass_rate: float
    test_pass_rate: float
    test_coverage: float
    performance_score: float
    file_count: int
    test_count: int
    complexity_score: float


@dataclass
class QualitySnapshot:
    """品質スナップショット（履歴記録用）"""
    timestamp: str
    commit_hash: str
    branch_name: str
    metrics: QualityMetrics


@dataclass
class QualityGateResult:
    """品質ゲート結果"""
    passed: bool
    failed_checks: List[str]
    warnings: List[str]
    metrics: QualityMetrics


class QualityToolkit:
    """品質管理統合ツールキット"""
    
    # 品質ゲート基準値
    QUALITY_GATES = {
        'min_test_coverage': 70.0,
        'min_test_pass_rate': 95.0,
        'min_syntax_pass_rate': 98.0,
        'max_complexity_score': 50.0,
        'min_total_score': 75.0
    }
    
    def __init__(self, project_root: Optional[Path] = None):
        """初期化"""
        self.project_root = project_root or Path.cwd()
        self.history_db = self.project_root / "dev" / "data" / "quality_history.db"
        self.history_db.parent.mkdir(parents=True, exist_ok=True)
        self._init_history_db()
    
    def _init_history_db(self):
        """履歴データベースを初期化"""
        with sqlite3.connect(self.history_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    commit_hash TEXT,
                    branch_name TEXT,
                    total_score REAL,
                    syntax_pass_rate REAL,
                    test_pass_rate REAL,
                    test_coverage REAL,
                    performance_score REAL,
                    complexity_score REAL,
                    file_count INTEGER,
                    test_count INTEGER
                )
            """)
            conn.commit()
    
    def collect_metrics(self) -> QualityMetrics:
        """品質メトリクスを収集"""
        print("品質メトリクスを収集中...")
        
        # 基本メトリクス
        file_count = len(list(self.project_root.glob("**/*.py")))
        test_count = len(list(self.project_root.glob("**/test_*.py")))
        
        # テストカバレッジ取得
        test_coverage = self._get_test_coverage()
        
        # テスト成功率取得
        test_pass_rate = self._get_test_pass_rate()
        
        # 構文チェック成功率
        syntax_pass_rate = self._get_syntax_pass_rate()
        
        # パフォーマンススコア（簡易版）
        performance_score = self._get_performance_score()
        
        # 複雑度スコア
        complexity_score = self._get_complexity_score()
        
        # 総合スコア計算
        total_score = (
            test_coverage * 0.3 +
            test_pass_rate * 0.25 +
            syntax_pass_rate * 0.2 +
            performance_score * 0.15 +
            max(0, 100 - complexity_score) * 0.1
        )
        
        return QualityMetrics(
            total_score=total_score,
            syntax_pass_rate=syntax_pass_rate,
            test_pass_rate=test_pass_rate,
            test_coverage=test_coverage,
            performance_score=performance_score,
            file_count=file_count,
            test_count=test_count,
            complexity_score=complexity_score
        )
    
    def _get_test_coverage(self) -> float:
        """テストカバレッジを取得"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "--cov=kumihan_formatter",
                "--cov-report=json:coverage.json",
                "-q"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=120)
            
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                coverage = coverage_data['totals']['percent_covered']
                coverage_file.unlink()  # クリーンアップ
                return coverage
        except Exception as e:
            print(f"カバレッジ取得エラー: {e}")
        
        return 0.0
    
    def _get_test_pass_rate(self) -> float:
        """テスト成功率を取得"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "--tb=no", "-q"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=120)
            
            output = result.stdout + result.stderr
            
            # 成功/失敗の数を解析
            import re
            passed_match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)
            
            passed = int(passed_match.group(1)) if passed_match else 0
            failed = int(failed_match.group(1)) if failed_match else 0
            
            total = passed + failed
            return (passed / total * 100) if total > 0 else 100.0
            
        except Exception as e:
            print(f"テスト実行エラー: {e}")
            return 0.0
    
    def _get_syntax_pass_rate(self) -> float:
        """構文チェック成功率を取得"""
        try:
            # Python構文チェック
            python_files = list(self.project_root.glob("**/*.py"))
            if not python_files:
                return 100.0
            
            valid_files = 0
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        compile(f.read(), str(py_file), 'exec')
                    valid_files += 1
                except SyntaxError:
                    pass
                except Exception:
                    pass  # その他のエラーは構文エラーではない
            
            return (valid_files / len(python_files)) * 100
            
        except Exception:
            return 0.0
    
    def _get_performance_score(self) -> float:
        """パフォーマンススコア取得（簡易版）"""
        try:
            # サンプルファイルでの変換時間測定
            sample_file = self.project_root / "examples" / "sample.txt"
            if not sample_file.exists():
                return 75.0  # デフォルト値
            
            start_time = time.time()
            result = subprocess.run([
                sys.executable, "-m", "kumihan_formatter.cli",
                str(sample_file), "-o", "/tmp"
            ], cwd=self.project_root, capture_output=True, timeout=30)
            
            execution_time = time.time() - start_time
            
            # 5秒以内なら100点、10秒で50点、それ以上は0点
            if execution_time <= 5:
                return 100.0
            elif execution_time <= 10:
                return 100 - ((execution_time - 5) * 10)
            else:
                return 0.0
                
        except Exception:
            return 50.0  # デフォルト値
    
    def _get_complexity_score(self) -> float:
        """複雑度スコア取得"""
        try:
            # 単純な複雑度指標（関数の平均行数）
            python_files = list(self.project_root.glob("kumihan_formatter/**/*.py"))
            
            total_functions = 0
            total_lines = 0
            
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    import re
                    functions = re.findall(r'def \w+\([^)]*\):', content)
                    total_functions += len(functions)
                    total_lines += len(content.splitlines())
                    
                except Exception:
                    continue
            
            if total_functions == 0:
                return 0.0
            
            avg_lines_per_function = total_lines / total_functions
            
            # 15行以下なら複雑度0、25行で50、50行で100
            if avg_lines_per_function <= 15:
                return 0.0
            elif avg_lines_per_function <= 50:
                return (avg_lines_per_function - 15) * (100 / 35)
            else:
                return 100.0
                
        except Exception:
            return 25.0  # デフォルト値
    
    def check_quality_gates(self, metrics: QualityMetrics) -> QualityGateResult:
        """品質ゲートをチェック"""
        failed_checks = []
        warnings = []
        
        # 必須チェック
        if metrics.test_coverage < self.QUALITY_GATES['min_test_coverage']:
            failed_checks.append(f"テストカバレッジ不足: {metrics.test_coverage:.1f}% < {self.QUALITY_GATES['min_test_coverage']}%")
        
        if metrics.test_pass_rate < self.QUALITY_GATES['min_test_pass_rate']:
            failed_checks.append(f"テスト成功率不足: {metrics.test_pass_rate:.1f}% < {self.QUALITY_GATES['min_test_pass_rate']}%")
        
        if metrics.syntax_pass_rate < self.QUALITY_GATES['min_syntax_pass_rate']:
            failed_checks.append(f"構文エラー率高: {metrics.syntax_pass_rate:.1f}% < {self.QUALITY_GATES['min_syntax_pass_rate']}%")
        
        if metrics.total_score < self.QUALITY_GATES['min_total_score']:
            failed_checks.append(f"総合スコア不足: {metrics.total_score:.1f} < {self.QUALITY_GATES['min_total_score']}")
        
        # 警告レベルチェック
        if metrics.complexity_score > self.QUALITY_GATES['max_complexity_score']:
            warnings.append(f"複雑度高: {metrics.complexity_score:.1f} > {self.QUALITY_GATES['max_complexity_score']}")
        
        if metrics.performance_score < 70:
            warnings.append(f"パフォーマンス注意: {metrics.performance_score:.1f}")
        
        passed = len(failed_checks) == 0
        return QualityGateResult(passed, failed_checks, warnings, metrics)
    
    def save_snapshot(self, metrics: QualityMetrics) -> QualitySnapshot:
        """品質スナップショットを保存"""
        # Git情報取得
        try:
            commit_hash = subprocess.run([
                "git", "rev-parse", "HEAD"
            ], capture_output=True, text=True, cwd=self.project_root).stdout.strip()
            
            branch_name = subprocess.run([
                "git", "branch", "--show-current"
            ], capture_output=True, text=True, cwd=self.project_root).stdout.strip()
        except Exception:
            commit_hash = "unknown"
            branch_name = "unknown"
        
        snapshot = QualitySnapshot(
            timestamp=datetime.now().isoformat(),
            commit_hash=commit_hash,
            branch_name=branch_name,
            metrics=metrics
        )
        
        # データベースに保存
        with sqlite3.connect(self.history_db) as conn:
            conn.execute("""
                INSERT INTO quality_snapshots 
                (timestamp, commit_hash, branch_name, total_score, syntax_pass_rate,
                 test_pass_rate, test_coverage, performance_score, complexity_score,
                 file_count, test_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.timestamp,
                snapshot.commit_hash,
                snapshot.branch_name,
                metrics.total_score,
                metrics.syntax_pass_rate,
                metrics.test_pass_rate,
                metrics.test_coverage,
                metrics.performance_score,
                metrics.complexity_score,
                metrics.file_count,
                metrics.test_count
            ))
            conn.commit()
        
        return snapshot
    
    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """トレンド分析を実行"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.history_db) as conn:
            cursor = conn.execute("""
                SELECT timestamp, total_score, test_coverage, complexity_score
                FROM quality_snapshots 
                WHERE timestamp > ?
                ORDER BY timestamp
            """, (cutoff_date,))
            
            rows = cursor.fetchall()
        
        if len(rows) < 2:
            return {"trend": "insufficient_data", "message": "履歴データが不足しています"}
        
        # トレンド計算
        first_score = rows[0][1]
        last_score = rows[-1][1]
        score_change = last_score - first_score
        
        first_coverage = rows[0][2]
        last_coverage = rows[-1][2]
        coverage_change = last_coverage - first_coverage
        
        # トレンド判定
        if score_change > 5:
            trend = "improving"
        elif score_change < -5:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "score_change": score_change,
            "coverage_change": coverage_change,
            "data_points": len(rows),
            "period_days": days
        }
    
    def perform_maintenance(self) -> Dict[str, Any]:
        """品質保守を実行"""
        results = {}
        
        # 古いテストファイルのクリーンアップ
        test_artifacts = list(self.project_root.glob("**/.pytest_cache"))
        test_artifacts.extend(self.project_root.glob("**/__pycache__"))
        
        cleaned_dirs = 0
        for artifact in test_artifacts:
            if artifact.is_dir():
                try:
                    import shutil
                    shutil.rmtree(artifact)
                    cleaned_dirs += 1
                except Exception:
                    pass
        
        results['cleaned_cache_dirs'] = cleaned_dirs
        
        # 一時ファイルのクリーンアップ
        temp_files = list(self.project_root.glob("**/*.tmp"))
        temp_files.extend(self.project_root.glob("**/.coverage"))
        temp_files.extend(self.project_root.glob("**/coverage.json"))
        
        cleaned_files = 0
        for temp_file in temp_files:
            try:
                temp_file.unlink()
                cleaned_files += 1
            except Exception:
                pass
        
        results['cleaned_temp_files'] = cleaned_files
        
        # 履歴データベースの最適化
        try:
            with sqlite3.connect(self.history_db) as conn:
                conn.execute("VACUUM")
                conn.commit()
            results['db_optimized'] = True
        except Exception:
            results['db_optimized'] = False
        
        return results
    
    def generate_report(self, metrics: QualityMetrics, gate_result: QualityGateResult,
                       trend_analysis: Optional[Dict] = None) -> str:
        """品質レポートを生成"""
        report = []
        report.append("# 品質管理レポート\n")
        
        # 総合スコア
        status = "✅ 合格" if gate_result.passed else "❌ 不合格"
        report.append(f"## 品質ゲート: {status}")
        report.append(f"**総合スコア**: {metrics.total_score:.1f}/100\n")
        
        # メトリクス詳細
        report.append("## 品質メトリクス")
        report.append("| 項目 | 値 | 基準 | 状態 |")
        report.append("|------|----|----- |------|")
        
        metrics_data = [
            ("テストカバレッジ", f"{metrics.test_coverage:.1f}%", "≥70%", 
             "✅" if metrics.test_coverage >= 70 else "❌"),
            ("テスト成功率", f"{metrics.test_pass_rate:.1f}%", "≥95%",
             "✅" if metrics.test_pass_rate >= 95 else "❌"),
            ("構文正確性", f"{metrics.syntax_pass_rate:.1f}%", "≥98%",
             "✅" if metrics.syntax_pass_rate >= 98 else "❌"),
            ("パフォーマンス", f"{metrics.performance_score:.1f}", "≥70",
             "✅" if metrics.performance_score >= 70 else "⚠️"),
            ("複雑度", f"{metrics.complexity_score:.1f}", "≤50",
             "✅" if metrics.complexity_score <= 50 else "⚠️"),
        ]
        
        for name, value, threshold, status in metrics_data:
            report.append(f"| {name} | {value} | {threshold} | {status} |")
        
        report.append("")
        
        # 問題と警告
        if gate_result.failed_checks:
            report.append("## ❌ 品質ゲート失敗項目")
            for check in gate_result.failed_checks:
                report.append(f"- {check}")
            report.append("")
        
        if gate_result.warnings:
            report.append("## ⚠️ 警告項目")
            for warning in gate_result.warnings:
                report.append(f"- {warning}")
            report.append("")
        
        # トレンド分析
        if trend_analysis:
            trend_emoji = {
                "improving": "📈",
                "declining": "📉", 
                "stable": "➡️",
                "insufficient_data": "❓"
            }
            
            emoji = trend_emoji.get(trend_analysis["trend"], "❓")
            report.append(f"## {emoji} トレンド分析（過去{trend_analysis.get('period_days', 30)}日）")
            
            if trend_analysis["trend"] != "insufficient_data":
                report.append(f"- **スコア変化**: {trend_analysis['score_change']:+.1f}")
                report.append(f"- **カバレッジ変化**: {trend_analysis['coverage_change']:+.1f}%")
                report.append(f"- **データポイント**: {trend_analysis['data_points']}個")
            else:
                report.append(f"- {trend_analysis['message']}")
            
            report.append("")
        
        # 推奨アクション
        report.append("## 推奨アクション")
        if gate_result.passed:
            report.append("- ✅ 品質基準を満たしています。現在の開発プラクティスを継続してください。")
        else:
            report.append("- ❗ 品質基準を満たしていません。以下の改善が必要です：")
            for check in gate_result.failed_checks[:3]:  # 上位3つの問題
                report.append(f"  - {check}")
        
        if gate_result.warnings:
            report.append("- ⚠️ 以下の警告への対応を検討してください：")
            for warning in gate_result.warnings[:2]:  # 上位2つの警告
                report.append(f"  - {warning}")
        
        return "\n".join(report)


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="品質管理統合ツールキット")
    parser.add_argument("--analyze", action="store_true", help="品質メトリクス分析")
    parser.add_argument("--gate-check", action="store_true", help="品質ゲートチェック")
    parser.add_argument("--report", action="store_true", help="品質レポート生成")
    parser.add_argument("--maintenance", action="store_true", help="品質保守実行")
    parser.add_argument("--trend-snapshot", action="store_true", help="品質スナップショット保存")
    parser.add_argument("--full-check", action="store_true", help="統合品質チェック")
    parser.add_argument("--output", "-o", type=Path, help="レポート出力ファイル")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="プロジェクトルートディレクトリ")
    
    args = parser.parse_args()
    
    if not any([args.analyze, args.gate_check, args.report, args.maintenance,
                args.trend_snapshot, args.full_check]):
        parser.print_help()
        return
    
    toolkit = QualityToolkit(args.project_root)
    
    # メトリクス収集
    if any([args.analyze, args.gate_check, args.report, args.full_check, args.trend_snapshot]):
        metrics = toolkit.collect_metrics()
        print(f"品質メトリクス収集完了: 総合スコア {metrics.total_score:.1f}/100")
    
    # 品質ゲートチェック
    if any([args.gate_check, args.report, args.full_check]):
        gate_result = toolkit.check_quality_gates(metrics)
        status = "合格" if gate_result.passed else "不合格"
        print(f"品質ゲート結果: {status}")
    
    # スナップショット保存
    if args.trend_snapshot or args.full_check:
        snapshot = toolkit.save_snapshot(metrics)
        print(f"品質スナップショット保存: {snapshot.timestamp}")
    
    # トレンド分析
    if args.report or args.full_check:
        trend_analysis = toolkit.get_trend_analysis()
    else:
        trend_analysis = None
    
    # 保守実行
    if args.maintenance or args.full_check:
        maintenance_result = toolkit.perform_maintenance()
        print(f"保守実行完了: {maintenance_result}")
    
    # レポート生成
    if args.report or args.full_check:
        report = toolkit.generate_report(metrics, gate_result, trend_analysis)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"レポート保存: {args.output}")
        else:
            print("\n" + report)
    
    # 終了コード
    if any([args.gate_check, args.full_check]):
        sys.exit(0 if gate_result.passed else 1)


if __name__ == "__main__":
    main()