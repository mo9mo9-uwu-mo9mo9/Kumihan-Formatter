#!/usr/bin/env python3
"""
Kumihan-Formatter 品質管理ツールキット - 統合版

このツールは以下の機能を統合しています:
- quality_gates.py: 品質ゲート自動判定
- quality_maintenance.py: 品質保守・監視
- quality_metrics.py: 品質メトリクス収集・分析
- quality_report_generator.py: 品質レポート生成

使用方法:
    # 品質メトリクス収集・分析
    python dev/tools/quality_manager.py --analyze
    
    # 品質ゲートチェック
    python dev/tools/quality_manager.py --gate-check
    
    # 品質レポート生成
    python dev/tools/quality_manager.py --report
    
    # 品質保守（清掃・最適化）
    python dev/tools/quality_manager.py --maintenance
    
    # 統合品質チェック（推奨）
    python dev/tools/quality_manager.py --full-check
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import time

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class QualityMetrics:
    """品質メトリクス"""
    # コードメトリクス
    total_files: int
    total_lines: int
    code_coverage: float
    test_pass_rate: float
    
    # 複雑度メトリクス
    cyclomatic_complexity: float
    maintainability_index: float
    
    # プロジェクト健全性
    dead_code_ratio: float
    duplication_ratio: float
    technical_debt_hours: float
    
    # パフォーマンス
    build_time_seconds: float
    test_time_seconds: float
    
    # 品質スコア（総合）
    quality_score: float
    
    # タイムスタンプ
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class QualityGateRule:
    """品質ゲートルール"""
    name: str
    metric: str
    operator: str  # '>=', '<=', '==', '>', '<'
    threshold: float
    weight: float = 1.0
    critical: bool = False
    description: str = ""


@dataclass
class QualityGateResult:
    """品質ゲート結果"""
    rule: QualityGateRule
    actual_value: float
    passed: bool
    score: float
    message: str


class QualityAnalyzer:
    """品質分析エンジン"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.data_dir = project_root / "dev" / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def collect_metrics(self) -> QualityMetrics:
        """品質メトリクスを収集"""
        print("📊 品質メトリクス収集中...")
        
        # ファイル統計
        total_files, total_lines = self._count_source_files()
        
        # テスト関連メトリクス
        code_coverage, test_pass_rate, test_time = self._analyze_tests()
        
        # コード複雑度分析
        complexity, maintainability = self._analyze_complexity()
        
        # プロジェクト健全性
        dead_code_ratio, duplication_ratio = self._analyze_code_health()
        
        # ビルド時間
        build_time = self._measure_build_time()
        
        # 技術的負債推定
        tech_debt = self._estimate_technical_debt(
            total_lines, complexity, duplication_ratio
        )
        
        # 総合品質スコア計算
        quality_score = self._calculate_quality_score(
            code_coverage, test_pass_rate, complexity, 
            maintainability, dead_code_ratio, duplication_ratio
        )
        
        return QualityMetrics(
            total_files=total_files,
            total_lines=total_lines,
            code_coverage=code_coverage,
            test_pass_rate=test_pass_rate,
            cyclomatic_complexity=complexity,
            maintainability_index=maintainability,
            dead_code_ratio=dead_code_ratio,
            duplication_ratio=duplication_ratio,
            technical_debt_hours=tech_debt,
            build_time_seconds=build_time,
            test_time_seconds=test_time,
            quality_score=quality_score
        )
    
    def _count_source_files(self) -> Tuple[int, int]:
        """ソースファイル統計"""
        python_files = list(self.project_root.glob("**/*.py"))
        # テストファイルやビルド成果物を除外
        source_files = [
            f for f in python_files 
            if not any(part in str(f) for part in [
                "__pycache__", ".egg-info", "dist/", "build/",
                ".venv", ".tox"
            ])
        ]
        
        total_lines = 0
        for file_path in source_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 空行とコメント行を除いた実行可能行数
                    code_lines = [
                        line for line in lines 
                        if line.strip() and not line.strip().startswith('#')
                    ]
                    total_lines += len(code_lines)
            except Exception:
                pass
        
        return len(source_files), total_lines
    
    def _analyze_tests(self) -> Tuple[float, float, float]:
        """テスト分析"""
        start_time = time.time()
        
        try:
            # pytest実行（カバレッジ付き）
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "--cov=kumihan_formatter", "--cov-report=term-missing",
                "--tb=short", "-q"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=300)
            
            test_time = time.time() - start_time
            
            # カバレッジ解析
            coverage = 0.0
            if "TOTAL" in result.stdout:
                for line in result.stdout.split('\n'):
                    if "TOTAL" in line:
                        parts = line.split()
                        if len(parts) >= 4 and parts[-1].endswith('%'):
                            coverage = float(parts[-1].rstrip('%'))
                            break
            
            # テスト成功率
            pass_rate = 100.0 if result.returncode == 0 else 0.0
            
            # 部分的成功の場合のパース
            if result.returncode != 0 and "failed" in result.stdout:
                # "X failed, Y passed" パターンを解析
                import re
                match = re.search(r'(\d+) failed.*?(\d+) passed', result.stdout)
                if match:
                    failed = int(match.group(1))
                    passed = int(match.group(2))
                    total = failed + passed
                    pass_rate = (passed / total * 100) if total > 0 else 0.0
            
            return coverage, pass_rate, test_time
            
        except Exception as e:
            print(f"⚠️  テスト実行エラー: {e}")
            return 0.0, 0.0, 0.0
    
    def _analyze_complexity(self) -> Tuple[float, float]:
        """コード複雑度分析（簡易版）"""
        total_complexity = 0
        file_count = 0
        
        for py_file in self.project_root.glob("kumihan_formatter/**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 簡易的な循環的複雑度計算
                complexity = content.count('if ') + content.count('elif ') + \
                           content.count('for ') + content.count('while ') + \
                           content.count('except ') + content.count('and ') + \
                           content.count('or ')
                
                total_complexity += complexity
                file_count += 1
                
            except Exception:
                pass
        
        avg_complexity = total_complexity / file_count if file_count > 0 else 0
        
        # 保守性指数（簡易計算）
        # 高い複雑度 = 低い保守性
        maintainability = max(0, 100 - (avg_complexity * 2))
        
        return avg_complexity, maintainability
    
    def _analyze_code_health(self) -> Tuple[float, float]:
        """コード健全性分析"""
        # 簡易的なデッドコード・重複検出
        python_files = list(self.project_root.glob("kumihan_formatter/**/*.py"))
        
        total_functions = 0
        unused_functions = 0
        total_lines = 0
        duplicate_lines = 0
        
        function_calls = set()
        function_definitions = set()
        line_hashes = {}
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    total_lines += len(lines)
                
                for line in lines:
                    line = line.strip()
                    
                    # 関数定義
                    if line.startswith('def '):
                        func_name = line.split('(')[0].replace('def ', '')
                        function_definitions.add(func_name)
                        total_functions += 1
                    
                    # 関数呼び出し（簡易検出）
                    if '(' in line and ')' in line:
                        for func in function_definitions:
                            if f'{func}(' in line:
                                function_calls.add(func)
                    
                    # 重複行検出
                    if line and not line.startswith('#'):
                        line_hash = hash(line)
                        if line_hash in line_hashes:
                            duplicate_lines += 1
                        else:
                            line_hashes[line_hash] = 1
                            
            except Exception:
                pass
        
        # 未使用関数の推定
        for func in function_definitions:
            if func not in function_calls and not func.startswith('_'):
                unused_functions += 1
        
        dead_code_ratio = (unused_functions / total_functions * 100) if total_functions > 0 else 0
        duplication_ratio = (duplicate_lines / total_lines * 100) if total_lines > 0 else 0
        
        return dead_code_ratio, duplication_ratio
    
    def _measure_build_time(self) -> float:
        """ビルド時間測定"""
        start_time = time.time()
        
        try:
            # 簡単なインポートテストでビルド時間を代替
            result = subprocess.run([
                sys.executable, "-c", "import kumihan_formatter; print('OK')"
            ], cwd=self.project_root, capture_output=True, timeout=60)
            
            return time.time() - start_time
            
        except Exception:
            return 0.0
    
    def _estimate_technical_debt(self, total_lines: int, complexity: float, duplication: float) -> float:
        """技術的負債推定（時間）"""
        # 簡易的な負債時間計算
        # 複雑度と重複率から推定
        complexity_debt = (complexity - 10) * 0.1 if complexity > 10 else 0
        duplication_debt = duplication * 0.05
        line_debt = total_lines * 0.001
        
        return max(0, complexity_debt + duplication_debt + line_debt)
    
    def _calculate_quality_score(self, coverage: float, pass_rate: float, 
                                complexity: float, maintainability: float,
                                dead_code: float, duplication: float) -> float:
        """総合品質スコア計算"""
        # 重み付き平均で品質スコア算出
        weights = {
            'coverage': 0.25,
            'pass_rate': 0.25,
            'maintainability': 0.20,
            'complexity': 0.15,  # 低いほど良い（逆転）
            'dead_code': 0.10,   # 低いほど良い（逆転）
            'duplication': 0.05  # 低いほど良い（逆転）
        }
        
        # スコア正規化（0-100）
        normalized_scores = {
            'coverage': coverage,
            'pass_rate': pass_rate,
            'maintainability': maintainability,
            'complexity': max(0, 100 - complexity * 2),  # 複雑度を逆転
            'dead_code': max(0, 100 - dead_code * 2),    # デッドコードを逆転
            'duplication': max(0, 100 - duplication * 2) # 重複を逆転
        }
        
        # 重み付き合計
        quality_score = sum(
            normalized_scores[metric] * weight 
            for metric, weight in weights.items()
        )
        
        return min(100, max(0, quality_score))


class QualityGateManager:
    """品質ゲート管理"""
    
    def __init__(self):
        self.default_rules = [
            QualityGateRule("コードカバレッジ", "code_coverage", ">=", 70.0, 2.0, True, "テストカバレッジが70%以上必要"),
            QualityGateRule("テスト成功率", "test_pass_rate", ">=", 95.0, 2.0, True, "テスト成功率が95%以上必要"),
            QualityGateRule("品質スコア", "quality_score", ">=", 80.0, 1.5, False, "総合品質スコアが80点以上推奨"),
            QualityGateRule("循環的複雑度", "cyclomatic_complexity", "<=", 15.0, 1.0, False, "平均複雑度が15以下推奨"),
            QualityGateRule("デッドコード率", "dead_code_ratio", "<=", 5.0, 1.0, False, "デッドコード率が5%以下推奨"),
            QualityGateRule("重複率", "duplication_ratio", "<=", 3.0, 0.5, False, "コード重複率が3%以下推奨"),
        ]
    
    def evaluate_gates(self, metrics: QualityMetrics, rules: Optional[List[QualityGateRule]] = None) -> List[QualityGateResult]:
        """品質ゲート評価"""
        if rules is None:
            rules = self.default_rules
        
        results = []
        
        for rule in rules:
            actual_value = getattr(metrics, rule.metric, 0)
            passed = self._evaluate_rule(actual_value, rule.operator, rule.threshold)
            
            # スコア計算（合格なら満点、不合格なら重みに応じた減点）
            score = rule.weight if passed else 0
            
            # メッセージ生成
            status = "✅ 合格" if passed else "❌ 不合格"
            message = f"{status}: {rule.name} = {actual_value:.1f} (閾値: {rule.operator} {rule.threshold})"
            
            results.append(QualityGateResult(
                rule=rule,
                actual_value=actual_value,
                passed=passed,
                score=score,
                message=message
            ))
        
        return results
    
    def _evaluate_rule(self, value: float, operator: str, threshold: float) -> bool:
        """ルール評価"""
        if operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == "==":
            return abs(value - threshold) < 0.01
        else:
            return False


class QualityReportGenerator:
    """品質レポート生成"""
    
    def generate_comprehensive_report(self, metrics: QualityMetrics, 
                                    gate_results: List[QualityGateResult]) -> str:
        """包括的品質レポート生成"""
        report_lines = []
        
        # ヘッダー
        report_lines.append("=" * 60)
        report_lines.append("🔍 Kumihan-Formatter 品質レポート")
        report_lines.append("=" * 60)
        report_lines.append(f"生成日時: {metrics.timestamp}")
        report_lines.append("")
        
        # 総合品質スコア
        report_lines.append("📊 総合品質スコア")
        report_lines.append("-" * 30)
        score_emoji = "🟢" if metrics.quality_score >= 80 else "🟡" if metrics.quality_score >= 60 else "🔴"
        report_lines.append(f"{score_emoji} 品質スコア: {metrics.quality_score:.1f}/100")
        report_lines.append("")
        
        # コードメトリクス
        report_lines.append("📈 コードメトリクス")
        report_lines.append("-" * 30)
        report_lines.append(f"📁 総ファイル数: {metrics.total_files:,}")
        report_lines.append(f"📝 総行数: {metrics.total_lines:,}")
        report_lines.append(f"🧪 コードカバレッジ: {metrics.code_coverage:.1f}%")
        report_lines.append(f"✅ テスト成功率: {metrics.test_pass_rate:.1f}%")
        report_lines.append("")
        
        # 複雑度・保守性
        report_lines.append("🔧 複雑度・保守性")
        report_lines.append("-" * 30)
        report_lines.append(f"🌀 循環的複雑度: {metrics.cyclomatic_complexity:.1f}")
        report_lines.append(f"🛠️  保守性指数: {metrics.maintainability_index:.1f}")
        report_lines.append(f"💀 デッドコード率: {metrics.dead_code_ratio:.1f}%")
        report_lines.append(f"📄 重複コード率: {metrics.duplication_ratio:.1f}%")
        report_lines.append("")
        
        # パフォーマンス
        report_lines.append("⚡ パフォーマンス")
        report_lines.append("-" * 30)
        report_lines.append(f"🏗️  ビルド時間: {metrics.build_time_seconds:.2f}秒")
        report_lines.append(f"🧪 テスト時間: {metrics.test_time_seconds:.2f}秒")
        report_lines.append(f"💳 技術的負債: {metrics.technical_debt_hours:.1f}時間")
        report_lines.append("")
        
        # 品質ゲート結果
        report_lines.append("🚦 品質ゲート結果")
        report_lines.append("-" * 30)
        
        passed_count = sum(1 for result in gate_results if result.passed)
        total_count = len(gate_results)
        critical_failed = any(result.rule.critical and not result.passed for result in gate_results)
        
        report_lines.append(f"合格率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
        
        if critical_failed:
            report_lines.append("🚨 重要な品質ゲートが不合格です！")
        
        report_lines.append("")
        
        for result in gate_results:
            report_lines.append(result.message)
            if result.rule.description:
                report_lines.append(f"   💡 {result.rule.description}")
        
        report_lines.append("")
        
        # 推奨事項
        report_lines.append("💡 推奨事項")
        report_lines.append("-" * 30)
        
        recommendations = self._generate_recommendations(metrics, gate_results)
        for rec in recommendations:
            report_lines.append(f"• {rec}")
        
        return "\n".join(report_lines)
    
    def _generate_recommendations(self, metrics: QualityMetrics, 
                                gate_results: List[QualityGateResult]) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        # 品質スコアベースの推奨
        if metrics.quality_score < 70:
            recommendations.append("総合品質スコアが低いです。テストカバレッジと保守性の向上を検討してください")
        
        # 個別メトリクスの推奨
        if metrics.code_coverage < 70:
            recommendations.append("テストカバレッジが不足しています。テストケースの追加を検討してください")
        
        if metrics.cyclomatic_complexity > 15:
            recommendations.append("コードが複雑です。関数の分割やリファクタリングを検討してください")
        
        if metrics.dead_code_ratio > 5:
            recommendations.append("未使用コードが多いです。デッドコードの削除を検討してください")
        
        if metrics.duplication_ratio > 3:
            recommendations.append("重複コードが多いです。共通化できる部分がないか確認してください")
        
        if metrics.technical_debt_hours > 10:
            recommendations.append("技術的負債が蓄積しています。定期的なリファクタリングを計画してください")
        
        # 品質ゲート不合格への対応
        failed_critical = [r for r in gate_results if r.rule.critical and not r.passed]
        if failed_critical:
            recommendations.append("重要な品質ゲートが不合格です。リリース前に必ず修正してください")
        
        if not recommendations:
            recommendations.append("品質状態は良好です。現在のレベルを維持してください")
        
        return recommendations


class QualityMaintenanceManager:
    """品質保守管理"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def perform_maintenance(self) -> Dict[str, Any]:
        """品質保守実行"""
        results = {}
        
        print("🧹 品質保守作業開始...")
        
        # キャッシュクリーンアップ
        results['cache_cleanup'] = self._cleanup_caches()
        
        # 未使用ファイル検出
        results['unused_files'] = self._detect_unused_files()
        
        # パフォーマンス最適化
        results['optimization'] = self._optimize_performance()
        
        return results
    
    def _cleanup_caches(self) -> Dict[str, int]:
        """キャッシュクリーンアップ"""
        removed_items = 0
        
        cache_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            ".pytest_cache",
            ".hypothesis",
            ".coverage",
            "*.egg-info"
        ]
        
        for pattern in cache_patterns:
            for item in self.project_root.glob(pattern):
                try:
                    if item.is_file():
                        item.unlink()
                        removed_items += 1
                    elif item.is_dir():
                        import shutil
                        shutil.rmtree(item)
                        removed_items += 1
                except Exception:
                    pass
        
        return {"removed_items": removed_items}
    
    def _detect_unused_files(self) -> List[str]:
        """未使用ファイル検出"""
        # 簡易的な未使用ファイル検出
        # TODO: より詳細な依存関係分析を実装
        unused_files = []
        
        return unused_files
    
    def _optimize_performance(self) -> Dict[str, str]:
        """パフォーマンス最適化"""
        optimizations = []
        
        # 大きなファイルの特定
        large_files = []
        for py_file in self.project_root.glob("**/*.py"):
            if py_file.stat().st_size > 50000:  # 50KB以上
                large_files.append(str(py_file))
        
        if large_files:
            optimizations.append(f"大きなファイル({len(large_files)}個)の分割を検討")
        
        return {"suggestions": optimizations}


def main():
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter 品質管理ツールキット",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--analyze', action='store_true', help='品質メトリクス分析')
    parser.add_argument('--gate-check', action='store_true', help='品質ゲートチェック')
    parser.add_argument('--report', action='store_true', help='品質レポート生成')
    parser.add_argument('--maintenance', action='store_true', help='品質保守実行')
    parser.add_argument('--full-check', action='store_true', help='統合品質チェック')
    parser.add_argument('--output', help='結果出力ファイル')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent.parent
    
    # 何も指定されない場合はフルチェック
    if not any([args.analyze, args.gate_check, args.report, args.maintenance]):
        args.full_check = True
    
    # 品質分析
    if args.analyze or args.full_check:
        analyzer = QualityAnalyzer(project_root)
        metrics = analyzer.collect_metrics()
        
        print("📊 品質メトリクス収集完了")
        print(f"品質スコア: {metrics.quality_score:.1f}/100")
        
        # メトリクス保存
        metrics_file = project_root / "dev" / "data" / "current_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(asdict(metrics), f, indent=2)
    
    # 品質ゲートチェック
    if args.gate_check or args.full_check:
        if 'metrics' not in locals():
            # メトリクスが未収集の場合は読み込み
            metrics_file = project_root / "dev" / "data" / "current_metrics.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
                    metrics = QualityMetrics(**data)
            else:
                print("❌ メトリクスファイルが見つかりません。--analyze を先に実行してください")
                return 1
        
        gate_manager = QualityGateManager()
        gate_results = gate_manager.evaluate_gates(metrics)
        
        print("\n🚦 品質ゲートチェック結果:")
        passed_count = sum(1 for r in gate_results if r.passed)
        critical_failed = any(r.rule.critical and not r.passed for r in gate_results)
        
        for result in gate_results:
            print(f"  {result.message}")
        
        print(f"\n合格率: {passed_count}/{len(gate_results)}")
        
        if critical_failed:
            print("🚨 重要な品質ゲートが不合格です！")
            return 1
    
    # レポート生成
    if args.report or args.full_check:
        if 'metrics' not in locals() or 'gate_results' not in locals():
            print("❌ メトリクス・ゲート結果が必要です。--analyze --gate-check を先に実行してください")
            return 1
        
        report_generator = QualityReportGenerator()
        report = report_generator.generate_comprehensive_report(metrics, gate_results)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"📄 レポートを {args.output} に出力しました")
        else:
            print("\n" + report)
    
    # 保守作業
    if args.maintenance or args.full_check:
        maintenance_manager = QualityMaintenanceManager(project_root)
        maintenance_results = maintenance_manager.perform_maintenance()
        
        print("\n🧹 品質保守完了:")
        print(f"  キャッシュクリーンアップ: {maintenance_results['cache_cleanup']['removed_items']}項目削除")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())