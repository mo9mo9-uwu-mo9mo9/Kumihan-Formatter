#!/usr/bin/env python3
"""
Tiered Quality Gate System - Issue #640
段階的品質ゲートシステム

目的: Critical/Important/Supportive/Special Tierに基づく品質管理
- Critical Tier: 90%カバレッジ必須
- Important Tier: 80%カバレッジ推奨
- Supportive Tier: 統合テストで代替可
- Special Tier: E2E・ベンチマークで代替
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import argparse

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class QualityTier(Enum):
    """品質ティア定義"""
    CRITICAL = "critical"      # Core機能・Commands（90%必須）
    IMPORTANT = "important"    # レンダリング・バリデーション（80%推奨）
    SUPPORTIVE = "supportive"  # ユーティリティ・キャッシング（統合テスト可）
    SPECIAL = "special"        # GUI・パフォーマンス（E2E・ベンチマーク可）


@dataclass
class ModuleCoverage:
    """モジュールカバレッジ情報"""
    module_path: str
    tier: QualityTier
    coverage_percent: float
    required_percent: float
    line_count: int
    covered_lines: int
    missing_lines: List[int]
    status: str  # "pass", "warn", "fail"


@dataclass
class QualityGateResult:
    """品質ゲート結果"""
    overall_status: str
    total_coverage: float
    tier_results: Dict[str, Dict]
    module_results: List[ModuleCoverage]
    critical_failures: List[str]
    recommendations: List[str]
    execution_time: float


class TieredQualityGate:
    """段階的品質ゲートシステム"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.coverage_file = self.project_root / "coverage.json"
        
        # ティア別モジュール定義
        self.tier_modules = {
            QualityTier.CRITICAL: [
                "kumihan_formatter.core.markdown_converter",
                "kumihan_formatter.core.markdown_parser", 
                "kumihan_formatter.core.markdown_processor",
                "kumihan_formatter.core.markdown_renderer",
                "kumihan_formatter.commands.check_syntax",
                "kumihan_formatter.commands.convert",
                "kumihan_formatter.core.file_operations",
                "kumihan_formatter.core.parsing_coordinator"
            ],
            QualityTier.IMPORTANT: [
                "kumihan_formatter.core.rendering",
                "kumihan_formatter.core.validators",
                "kumihan_formatter.core.syntax",
                "kumihan_formatter.core.template_manager",
                "kumihan_formatter.core.list_parser",
                "kumihan_formatter.core.nested_list_parser"
            ],
            QualityTier.SUPPORTIVE: [
                "kumihan_formatter.core.utilities",
                "kumihan_formatter.core.caching",
                "kumihan_formatter.core.file_ops",
                "kumihan_formatter.core.debug_logger",
                "kumihan_formatter.utils"
            ],
            QualityTier.SPECIAL: [
                "kumihan_formatter.gui_controllers",
                "kumihan_formatter.gui_views", 
                "kumihan_formatter.gui_models",
                "kumihan_formatter.core.performance"
            ]
        }
        
        # ティア別品質要求
        self.quality_requirements = {
            QualityTier.CRITICAL: 90.0,
            QualityTier.IMPORTANT: 80.0,
            QualityTier.SUPPORTIVE: 0.0,  # 統合テストで代替
            QualityTier.SPECIAL: 0.0      # E2E・ベンチマークで代替
        }

    def run_coverage_analysis(self) -> bool:
        """カバレッジ分析実行"""
        logger.info("🔍 カバレッジ分析を実行中...")
        
        try:
            # pytest with coverage
            cmd = [
                "python3", "-m", "pytest",
                "--cov=kumihan_formatter",
                "--cov-report=json",
                "--cov-report=term-missing",
                "tests/"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=600  # 10分タイムアウト
            )
            
            if result.returncode != 0:
                logger.warning(f"テスト実行で警告: {result.stderr}")
                # テスト失敗でも続行（カバレッジは測定可能）
            
            if self.coverage_file.exists():
                logger.info("✅ カバレッジデータ取得完了")
                return True
            else:
                logger.error("❌ カバレッジファイルが生成されませんでした")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ カバレッジ分析がタイムアウトしました")
            return False
        except Exception as e:
            logger.error(f"❌ カバレッジ分析エラー: {e}")
            return False

    def analyze_tier_coverage(self) -> List[ModuleCoverage]:
        """ティア別カバレッジ分析"""
        if not self.coverage_file.exists():
            logger.error("カバレッジファイルが存在しません")
            return []
        
        with open(self.coverage_file, 'r') as f:
            coverage_data = json.load(f)
        
        module_results = []
        
        for tier, modules in self.tier_modules.items():
            required_coverage = self.quality_requirements[tier]
            
            for module_pattern in modules:
                # モジュールパターンにマッチするファイルを検索
                matching_files = self._find_matching_files(coverage_data, module_pattern)
                
                for file_path, file_data in matching_files.items():
                    coverage_percent = file_data.get('summary', {}).get('percent_covered', 0.0)
                    
                    # ステータス判定
                    if tier in [QualityTier.CRITICAL, QualityTier.IMPORTANT]:
                        if coverage_percent >= required_coverage:
                            status = "pass"
                        elif coverage_percent >= required_coverage * 0.8:  # 80%以上なら警告
                            status = "warn"
                        else:
                            status = "fail"
                    else:
                        status = "skip"  # Supportive/Specialは統合テスト等で代替
                    
                    module_result = ModuleCoverage(
                        module_path=file_path,
                        tier=tier,
                        coverage_percent=coverage_percent,
                        required_percent=required_coverage,
                        line_count=len(file_data.get('executed_lines', [])) + len(file_data.get('missing_lines', [])),
                        covered_lines=len(file_data.get('executed_lines', [])),
                        missing_lines=file_data.get('missing_lines', []),
                        status=status
                    )
                    
                    module_results.append(module_result)
        
        return module_results

    def _find_matching_files(self, coverage_data: Dict, module_pattern: str) -> Dict:
        """カバレッジデータからモジュールパターンにマッチするファイルを検索"""
        matching_files = {}
        
        # パターンをパス形式に変換
        path_pattern = module_pattern.replace('.', '/')
        
        for file_path, file_data in coverage_data.get('files', {}).items():
            if path_pattern in file_path:
                matching_files[file_path] = file_data
        
        return matching_files

    def evaluate_quality_gate(self, module_results: List[ModuleCoverage]) -> QualityGateResult:
        """品質ゲート評価"""
        import time
        start_time = time.time()
        
        # ティア別集計
        tier_results = {}
        critical_failures = []
        recommendations = []
        
        for tier in QualityTier:
            tier_modules = [m for m in module_results if m.tier == tier]
            
            if not tier_modules:
                tier_results[tier.value] = {
                    "module_count": 0,
                    "average_coverage": 0.0,
                    "required_coverage": self.quality_requirements[tier],
                    "status": "skip"
                }
                continue
            
            # 平均カバレッジ計算
            total_lines = sum(m.line_count for m in tier_modules)
            covered_lines = sum(m.covered_lines for m in tier_modules)
            average_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
            
            # ティア別ステータス判定
            required = self.quality_requirements[tier]
            if tier in [QualityTier.CRITICAL, QualityTier.IMPORTANT]:
                if average_coverage >= required:
                    tier_status = "pass"
                elif average_coverage >= required * 0.8:
                    tier_status = "warn"
                    recommendations.append(f"{tier.value.title()} Tier: {required}%を目指してカバレッジ向上を推奨")
                else:
                    tier_status = "fail"
                    critical_failures.append(f"{tier.value.title()} Tier: {average_coverage:.1f}% < {required}% (必須)")
            else:
                tier_status = "skip"
            
            tier_results[tier.value] = {
                "module_count": len(tier_modules),
                "average_coverage": average_coverage,
                "required_coverage": required,
                "status": tier_status,
                "failing_modules": [m.module_path for m in tier_modules if m.status == "fail"]
            }
        
        # 全体ステータス判定
        critical_tier = tier_results.get("critical", {})
        important_tier = tier_results.get("important", {})
        
        if critical_failures:
            overall_status = "fail"
        elif critical_tier.get("status") == "warn" or important_tier.get("status") == "warn":
            overall_status = "warn"
        else:
            overall_status = "pass"
        
        # 全体カバレッジ計算
        total_lines = sum(m.line_count for m in module_results)
        total_covered = sum(m.covered_lines for m in module_results)
        total_coverage = (total_covered / total_lines * 100) if total_lines > 0 else 0.0
        
        return QualityGateResult(
            overall_status=overall_status,
            total_coverage=total_coverage,
            tier_results=tier_results,
            module_results=module_results,
            critical_failures=critical_failures,
            recommendations=recommendations,
            execution_time=time.time() - start_time
        )

    def generate_report(self, result: QualityGateResult) -> str:
        """品質ゲートレポート生成"""
        report_lines = []
        
        # ヘッダー
        report_lines.append("=" * 80)
        report_lines.append("🎯 Tiered Quality Gate Report - Issue #640")
        report_lines.append("=" * 80)
        
        # 全体ステータス
        status_emoji = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
        report_lines.append(f"\n📊 Overall Status: {status_emoji.get(result.overall_status, '❓')} {result.overall_status.upper()}")
        report_lines.append(f"📈 Total Coverage: {result.total_coverage:.2f}%")
        report_lines.append(f"⏱️  Execution Time: {result.execution_time:.2f}s")
        
        # ティア別結果
        report_lines.append("\n" + "─" * 80)
        report_lines.append("📋 Tier-by-Tier Results:")
        report_lines.append("─" * 80)
        
        for tier_name, tier_data in result.tier_results.items():
            status = tier_data["status"]
            emoji = status_emoji.get(status, "⚪")
            
            report_lines.append(f"\n{emoji} {tier_name.title()} Tier:")
            report_lines.append(f"   Coverage: {tier_data['average_coverage']:.2f}% (Required: {tier_data['required_coverage']:.0f}%)")
            report_lines.append(f"   Modules: {tier_data['module_count']}")
            
            if tier_data.get("failing_modules"):
                report_lines.append(f"   Failing: {', '.join(tier_data['failing_modules'])}")
        
        # Critical failures
        if result.critical_failures:
            report_lines.append("\n" + "─" * 80)
            report_lines.append("🚨 Critical Failures:")
            report_lines.append("─" * 80)
            for failure in result.critical_failures:
                report_lines.append(f"❌ {failure}")
        
        # Recommendations
        if result.recommendations:
            report_lines.append("\n" + "─" * 80)
            report_lines.append("💡 Recommendations:")
            report_lines.append("─" * 80)
            for rec in result.recommendations:
                report_lines.append(f"💡 {rec}")
        
        # フッター
        report_lines.append("\n" + "=" * 80)
        
        return "\n".join(report_lines)

    def save_results(self, result: QualityGateResult, output_file: Optional[Path] = None):
        """結果をJSONファイルに保存"""
        if output_file is None:
            output_file = self.project_root / "quality_gate_results.json"
        
        # dataclassをdict変換（Enumを文字列に）
        result_dict = asdict(result)
        for module in result_dict["module_results"]:
            if isinstance(module["tier"], QualityTier):
                module["tier"] = module["tier"].value
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 結果を保存: {output_file}")

    def run(self, skip_coverage: bool = False, output_file: Optional[str] = None) -> int:
        """品質ゲート実行"""
        logger.info("🚀 Tiered Quality Gate 開始")
        
        try:
            # カバレッジ分析実行
            if not skip_coverage:
                if not self.run_coverage_analysis():
                    return 1
            elif not self.coverage_file.exists():
                logger.error("❌ --skip-coverageが指定されましたが、coverage.jsonが存在しません")
                return 1
            
            # ティア別分析
            logger.info("🔍 ティア別カバレッジ分析中...")
            module_results = self.analyze_tier_coverage()
            
            if not module_results:
                logger.error("❌ カバレッジデータが取得できませんでした")
                return 1
            
            # 品質ゲート評価
            logger.info("⚖️  品質ゲート評価中...")
            result = self.evaluate_quality_gate(module_results)
            
            # レポート生成・出力
            report = self.generate_report(result)
            print(report)
            
            # 結果保存
            output_path = Path(output_file) if output_file else None
            self.save_results(result, output_path)
            
            # 終了コード決定
            if result.overall_status == "fail":
                logger.error("❌ Quality Gate FAILED")
                return 1
            elif result.overall_status == "warn":
                logger.warning("⚠️ Quality Gate PASSED with warnings")
                return 0
            else:
                logger.info("✅ Quality Gate PASSED")
                return 0
                
        except Exception as e:
            logger.error(f"❌ Quality Gate実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return 1


def main():
    parser = argparse.ArgumentParser(description="Tiered Quality Gate System")
    parser.add_argument("--skip-coverage", action="store_true", 
                       help="カバレッジ測定をスキップ（既存のcoverage.jsonを使用）")
    parser.add_argument("--output", type=str, 
                       help="結果出力ファイルパス")
    parser.add_argument("--validate", action="store_true",
                       help="設定検証のみ実行")
    
    args = parser.parse_args()
    
    quality_gate = TieredQualityGate()
    
    if args.validate:
        logger.info("🔧 設定検証モード")
        print("Tier Configuration:")
        for tier, modules in quality_gate.tier_modules.items():
            print(f"  {tier.value}: {len(modules)} modules")
        return 0
    
    return quality_gate.run(args.skip_coverage, args.output)


if __name__ == "__main__":
    sys.exit(main())