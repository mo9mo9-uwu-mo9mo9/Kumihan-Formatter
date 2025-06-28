#!/usr/bin/env python3
"""
品質ゲート自動判定システム

使用方法:
    # 基本的な品質ゲートチェック
    python dev/tools/quality_gates.py
    
    # 特定の設定ファイルを使用
    python dev/tools/quality_gates.py --config=custom-gates.yml
    
    # JSONレポート出力
    python dev/tools/quality_gates.py --output=gate-results.json
    
    # CI/CD環境での使用
    python dev/tools/quality_gates.py --ci-mode
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
try:
    import yaml
except ImportError:
    yaml = None

# 品質メトリクス収集ツールをインポート
try:
    from quality_metrics import QualityAnalyzer, QualityMetrics
except ImportError:
    # パスを追加して再試行
    sys.path.append(str(Path(__file__).parent))
    from quality_metrics import QualityAnalyzer, QualityMetrics


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
    rule_name: str
    passed: bool
    actual_value: float
    threshold: float
    operator: str
    weight: float
    critical: bool
    message: str
    improvement_suggestion: str = ""


@dataclass
class QualityGateReport:
    """品質ゲートレポート"""
    timestamp: str
    project_name: str
    overall_passed: bool
    critical_passed: bool
    quality_score: float
    gate_results: List[QualityGateResult]
    summary: Dict[str, Any]
    recommendations: List[str]


class QualityGateChecker:
    """品質ゲートチェッカー"""
    
    def __init__(self, config_path: Path = None):
        self.config = self._load_config(config_path)
        self.rules = self._parse_rules()
        self.analyzer = QualityAnalyzer()
    
    def _load_config(self, config_path: Path = None) -> Dict[str, Any]:
        """設定を読み込み"""
        default_config = {
            "quality_gates": {
                "syntax_quality": {
                    "metric": "syntax_pass_rate",
                    "operator": ">=",
                    "threshold": 95.0,
                    "weight": 3.0,
                    "critical": True,
                    "description": "記法エラーが5%以下であること"
                },
                "performance_conversion": {
                    "metric": "conversion_time_avg",
                    "operator": "<=",
                    "threshold": 5.0,
                    "weight": 2.0,
                    "critical": False,
                    "description": "平均変換時間が5秒以下であること"
                },
                "performance_max": {
                    "metric": "conversion_time_max",
                    "operator": "<=",
                    "threshold": 10.0,
                    "weight": 1.5,
                    "critical": False,
                    "description": "最大変換時間が10秒以下であること"
                },
                "test_quality": {
                    "metric": "test_pass_rate",
                    "operator": ">=",
                    "threshold": 100.0,
                    "weight": 2.5,
                    "critical": True,
                    "description": "全てのテストが通過すること"
                },
                "overall_quality": {
                    "metric": "overall_quality_score",
                    "operator": ">=",
                    "threshold": 80.0,
                    "weight": 2.0,
                    "critical": False,
                    "description": "総合品質スコアが80点以上であること"
                },
                "file_count": {
                    "metric": "txt_files",
                    "operator": ">=",
                    "threshold": 3.0,
                    "weight": 0.5,
                    "critical": False,
                    "description": "最低3つのテキストファイルが存在すること"
                },
                "syntax_errors": {
                    "metric": "syntax_errors",
                    "operator": "<=",
                    "threshold": 2.0,
                    "weight": 2.0,
                    "critical": False,
                    "description": "記法エラーが2個以下であること"
                }
            },
            "thresholds": {
                "warning_score": 70.0,
                "critical_score": 50.0,
                "performance_degradation": 20.0
            },
            "notifications": {
                "slack_webhook": "",
                "email_alerts": False,
                "github_issues": True
            }
        }
        
        if config_path and config_path.exists() and yaml:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    # 深いマージ
                    for key, value in user_config.items():
                        if key in default_config and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                print(f"⚠️ 設定ファイル読み込みエラー: {e}")
        
        return default_config
    
    def _parse_rules(self) -> List[QualityGateRule]:
        """設定からルールをパース"""
        rules = []
        
        for rule_name, rule_config in self.config["quality_gates"].items():
            rule = QualityGateRule(
                name=rule_name,
                metric=rule_config["metric"],
                operator=rule_config["operator"],
                threshold=rule_config["threshold"],
                weight=rule_config.get("weight", 1.0),
                critical=rule_config.get("critical", False),
                description=rule_config.get("description", "")
            )
            rules.append(rule)
        
        return rules
    
    def check_quality_gates(self, target_dir: Path = None) -> QualityGateReport:
        """品質ゲートチェックを実行"""
        if target_dir is None:
            target_dir = Path.cwd()
        
        print("🚪 品質ゲートチェックを開始...")
        
        # メトリクス収集
        metrics = self.analyzer.analyze_project(target_dir)
        
        # 各ルールをチェック
        gate_results = []
        critical_failures = []
        
        for rule in self.rules:
            result = self._evaluate_rule(rule, metrics)
            gate_results.append(result)
            
            if not result.passed and rule.critical:
                critical_failures.append(result)
        
        # 総合評価
        overall_passed = len(critical_failures) == 0
        critical_passed = len(critical_failures) == 0
        
        # レポート生成
        report = QualityGateReport(
            timestamp=datetime.now().isoformat(),
            project_name=metrics.project_name,
            overall_passed=overall_passed,
            critical_passed=critical_passed,
            quality_score=metrics.overall_quality_score,
            gate_results=gate_results,
            summary=self._generate_summary(gate_results),
            recommendations=self._generate_recommendations(gate_results, metrics)
        )
        
        return report
    
    def _evaluate_rule(self, rule: QualityGateRule, metrics: QualityMetrics) -> QualityGateResult:
        """個別ルールを評価"""
        # メトリクスから値を取得
        actual_value = getattr(metrics, rule.metric, 0)
        
        # 比較演算
        if rule.operator == ">=":
            passed = actual_value >= rule.threshold
        elif rule.operator == "<=":
            passed = actual_value <= rule.threshold
        elif rule.operator == ">":
            passed = actual_value > rule.threshold
        elif rule.operator == "<":
            passed = actual_value < rule.threshold
        elif rule.operator == "==":
            passed = abs(actual_value - rule.threshold) < 0.001
        else:
            passed = False
        
        # メッセージ生成
        status = "✅ PASS" if passed else "❌ FAIL"
        message = f"{status} {rule.description} (実際: {actual_value:.1f}, 閾値: {rule.threshold:.1f})"
        
        # 改善提案生成
        improvement_suggestion = self._generate_improvement_suggestion(rule, actual_value, passed)
        
        return QualityGateResult(
            rule_name=rule.name,
            passed=passed,
            actual_value=actual_value,
            threshold=rule.threshold,
            operator=rule.operator,
            weight=rule.weight,
            critical=rule.critical,
            message=message,
            improvement_suggestion=improvement_suggestion
        )
    
    def _generate_improvement_suggestion(self, rule: QualityGateRule, actual_value: float, passed: bool) -> str:
        """改善提案を生成"""
        if passed:
            return ""
        
        suggestions = {
            "syntax_pass_rate": "記法チェックツールを実行して、エラーを修正してください",
            "conversion_time_avg": "パフォーマンスボトルネックを特定し、最適化を実装してください",
            "conversion_time_max": "大きなファイルの処理を最適化するか、分割を検討してください",
            "test_pass_rate": "失敗したテストを確認し、コードまたはテストを修正してください",
            "overall_quality_score": "各品質項目を個別に改善して、総合スコアを向上させてください",
            "txt_files": "プロジェクトにテキストファイルのサンプルを追加してください",
            "syntax_errors": f"記法エラーを{int(actual_value - rule.threshold)}個減らす必要があります"
        }
        
        return suggestions.get(rule.metric, "詳細な分析を実行して、改善点を特定してください")
    
    def _generate_summary(self, gate_results: List[QualityGateResult]) -> Dict[str, Any]:
        """サマリーを生成"""
        total_rules = len(gate_results)
        passed_rules = sum(1 for result in gate_results if result.passed)
        critical_rules = sum(1 for result in gate_results if result.critical)
        critical_passed = sum(1 for result in gate_results if result.critical and result.passed)
        
        return {
            "total_rules": total_rules,
            "passed_rules": passed_rules,
            "failed_rules": total_rules - passed_rules,
            "pass_rate": (passed_rules / total_rules * 100) if total_rules > 0 else 0,
            "critical_rules": critical_rules,
            "critical_passed": critical_passed,
            "critical_pass_rate": (critical_passed / critical_rules * 100) if critical_rules > 0 else 0
        }
    
    def _generate_recommendations(self, gate_results: List[QualityGateResult], metrics: QualityMetrics) -> List[str]:
        """推奨事項を生成"""
        recommendations = []
        
        # 失敗したクリティカルルールに基づく推奨事項
        critical_failures = [r for r in gate_results if not r.passed and r.critical]
        
        if critical_failures:
            recommendations.append("🚨 クリティカルな品質ゲートが失敗しています。即座に対応が必要です。")
            for failure in critical_failures:
                recommendations.append(f"   • {failure.improvement_suggestion}")
        
        # 品質スコアに基づく推奨事項
        if metrics.overall_quality_score < 70:
            recommendations.append("📉 総合品質スコアが低いです。複数の改善項目に取り組んでください。")
        elif metrics.overall_quality_score < 85:
            recommendations.append("📊 品質は良好ですが、さらなる改善の余地があります。")
        
        # パフォーマンスに基づく推奨事項
        if metrics.conversion_time_avg > 3.0:
            recommendations.append("⚡ 変換パフォーマンスの最適化を検討してください。")
        
        # テストに基づく推奨事項
        if metrics.test_pass_rate < 100:
            recommendations.append("🧪 テストの安定性向上に取り組んでください。")
        
        if not recommendations:
            recommendations.append("🌟 全ての品質ゲートを通過しています。素晴らしい品質です！")
        
        return recommendations


def format_gate_report(report: QualityGateReport, format_type: str = 'detailed') -> str:
    """品質ゲートレポートのフォーマット"""
    if format_type == 'json':
        return json.dumps(asdict(report), indent=2, ensure_ascii=False)
    
    elif format_type == 'summary':
        status = "✅ PASS" if report.overall_passed else "❌ FAIL"
        return f"""
🚪 品質ゲート結果: {status}
==============================
プロジェクト: {report.project_name}
時刻: {report.timestamp}

📊 サマリー:
- 合格率: {report.summary['pass_rate']:.1f}% ({report.summary['passed_rules']}/{report.summary['total_rules']})
- クリティカル: {report.summary['critical_pass_rate']:.1f}% ({report.summary['critical_passed']}/{report.summary['critical_rules']})
- 品質スコア: {report.quality_score:.1f}/100

🎯 推奨事項:
{chr(10).join(f'• {rec}' for rec in report.recommendations)}
"""
    
    else:  # detailed
        gate_details = []
        for result in report.gate_results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            critical_mark = " 🚨" if result.critical else ""
            gate_details.append(f"  {status}{critical_mark} {result.rule_name}: {result.message}")
            if not result.passed and result.improvement_suggestion:
                gate_details.append(f"     💡 {result.improvement_suggestion}")
        
        return f"""
🚪 Kumihan-Formatter 品質ゲート詳細レポート
==========================================
プロジェクト: {report.project_name}
実行時刻: {report.timestamp}

📊 総合結果: {'✅ 全ゲート通過' if report.overall_passed else '❌ ゲート失敗'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 個別ゲート結果:
{chr(10).join(gate_details)}

📈 サマリー統計:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 総ルール数: {report.summary['total_rules']}
• 合格数: {report.summary['passed_rules']}
• 失敗数: {report.summary['failed_rules']}
• 合格率: {report.summary['pass_rate']:.1f}%
• クリティカル合格率: {report.summary['critical_pass_rate']:.1f}%
• 総合品質スコア: {report.quality_score:.1f}/100

🎯 推奨事項:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join(f'• {rec}' for rec in report.recommendations)}

{'🌟 おめでとうございます！全ての品質基準を満たしています。' if report.overall_passed else '⚠️ 品質向上のため、上記の推奨事項に取り組んでください。'}
"""


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter 品質ゲート自動判定システム",
        epilog="例: python dev/tools/quality_gates.py --config=custom-gates.yml --output=results.json"
    )
    parser.add_argument(
        '--config',
        type=Path,
        help='品質ゲート設定ファイル'
    )
    parser.add_argument(
        '--target-dir',
        type=Path,
        default=Path.cwd(),
        help='分析対象ディレクトリ'
    )
    parser.add_argument(
        '--format',
        choices=['detailed', 'summary', 'json'],
        default='detailed',
        help='レポート形式'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='出力ファイルパス'
    )
    parser.add_argument(
        '--ci-mode',
        action='store_true',
        help='CI/CD環境モード（失敗時に非ゼロ終了コード）'
    )
    
    args = parser.parse_args()
    
    try:
        # 品質ゲートチェック実行
        checker = QualityGateChecker(config_path=args.config)
        report = checker.check_quality_gates(args.target_dir)
        
        # レポート生成
        formatted_report = format_gate_report(report, args.format)
        
        # 出力
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(formatted_report)
            print(f"📄 品質ゲートレポートを出力しました: {args.output}")
        else:
            print(formatted_report)
        
        # CI/CDモードでの終了コード制御
        if args.ci_mode:
            if not report.overall_passed:
                print("\n🚨 品質ゲートチェックに失敗しました")
                sys.exit(1)
            else:
                print("\n🎉 全ての品質ゲートを通過しました！")
                sys.exit(0)
    
    except Exception as e:
        print(f"❌ 品質ゲートチェックでエラーが発生しました: {e}")
        if args.ci_mode:
            sys.exit(1)


if __name__ == "__main__":
    main()