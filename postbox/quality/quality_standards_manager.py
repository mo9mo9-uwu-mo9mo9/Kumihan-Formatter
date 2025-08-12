#!/usr/bin/env python3
"""
Quality Standards Manager for Gemini Capability Enhancement
自動品質検証・改善提案システム
"""

import json
import os
import subprocess
import re
import ast
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import time
from datetime import datetime


class QualityLevel(Enum):
    """品質レベル"""
    EXCELLENT = "excellent"    # 90-100%
    GOOD = "good"             # 80-89%
    ACCEPTABLE = "acceptable"  # 70-79%
    POOR = "poor"             # 60-69%
    CRITICAL = "critical"     # <60%


class MetricType(Enum):
    """メトリクスタイプ"""
    TYPE_COVERAGE = "type_coverage"
    SYNTAX_ACCURACY = "syntax_accuracy"
    FORMAT_COMPLIANCE = "format_compliance"
    IMPORT_ORGANIZATION = "import_organization"
    DOCSTRING_COVERAGE = "docstring_coverage"
    ERROR_RATE = "error_rate"


@dataclass
class QualityMetric:
    """品質メトリクス"""
    metric_id: str
    name: str
    description: str
    current_value: float
    target_value: float
    measurement_method: str
    improvement_suggestions: List[str]
    severity: str
    last_measured: str


@dataclass
class QualityReport:
    """品質レポート"""
    report_id: str
    file_path: str
    timestamp: str
    overall_score: float
    quality_level: QualityLevel
    metrics: List[QualityMetric]
    violations: List[Dict[str, Any]]
    improvement_plan: List[Dict[str, Any]]
    estimated_improvement_time: int  # minutes


@dataclass
class ImprovementSuggestion:
    """改善提案"""
    suggestion_id: str
    title: str
    description: str
    priority: int
    estimated_effort: int  # minutes
    expected_impact: float  # 0.0-1.0
    implementation_steps: List[str]
    code_examples: List[str]
    validation_method: str


class QualityChecker:
    """品質チェッカー"""
    
    def __init__(self):
        self.checkers = {
            MetricType.TYPE_COVERAGE: self._check_type_coverage,
            MetricType.SYNTAX_ACCURACY: self._check_syntax_accuracy,
            MetricType.FORMAT_COMPLIANCE: self._check_format_compliance,
            MetricType.IMPORT_ORGANIZATION: self._check_import_organization,
            MetricType.DOCSTRING_COVERAGE: self._check_docstring_coverage,
        }
    
    def check_file_quality(self, file_path: str) -> Dict[str, Any]:
        """ファイル品質チェック"""
        
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 各メトリクスのチェック実行
            for metric_type, checker_func in self.checkers.items():
                try:
                    metric_result = checker_func(file_path, content)
                    results[metric_type.value] = metric_result
                except Exception as e:
                    results[metric_type.value] = {
                        "error": str(e),
                        "score": 0.0
                    }
        
        except Exception as e:
            return {"error": f"Failed to read file: {e}"}
        
        return results
    
    def _check_type_coverage(self, file_path: str, content: str) -> Dict[str, Any]:
        """型注釈カバレッジチェック"""
        
        try:
            tree = ast.parse(content)
            
            total_functions = 0
            typed_functions = 0
            total_args = 0
            typed_args = 0
            violations = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    total_functions += 1
                    func_name = node.name
                    line_num = node.lineno
                    
                    # 返り値型チェック
                    has_return_annotation = node.returns is not None
                    if has_return_annotation:
                        typed_functions += 1
                    else:
                        violations.append({
                            "type": "missing_return_type",
                            "function": func_name,
                            "line": line_num,
                            "description": f"Function '{func_name}' missing return type annotation"
                        })
                    
                    # 引数型チェック
                    for arg in node.args.args:
                        total_args += 1
                        if arg.annotation:
                            typed_args += 1
                        else:
                            violations.append({
                                "type": "missing_arg_type",
                                "function": func_name,
                                "argument": arg.arg,
                                "line": line_num,
                                "description": f"Argument '{arg.arg}' in '{func_name}' missing type annotation"
                            })
            
            # カバレッジ計算
            function_coverage = typed_functions / total_functions if total_functions > 0 else 1.0
            arg_coverage = typed_args / total_args if total_args > 0 else 1.0
            overall_coverage = (function_coverage + arg_coverage) / 2
            
            return {
                "score": overall_coverage,
                "function_coverage": function_coverage,
                "argument_coverage": arg_coverage,
                "total_functions": total_functions,
                "typed_functions": typed_functions,
                "total_args": total_args,
                "typed_args": typed_args,
                "violations": violations
            }
        
        except SyntaxError as e:
            return {
                "score": 0.0,
                "error": f"Syntax error: {e}",
                "violations": [{"type": "syntax_error", "line": e.lineno, "description": str(e)}]
            }
    
    def _check_syntax_accuracy(self, file_path: str, content: str) -> Dict[str, Any]:
        """構文正確性チェック"""
        
        try:
            ast.parse(content)
            return {
                "score": 1.0,
                "violations": []
            }
        except SyntaxError as e:
            return {
                "score": 0.0,
                "violations": [{
                    "type": "syntax_error",
                    "line": e.lineno,
                    "column": e.offset,
                    "description": str(e),
                    "text": e.text.strip() if e.text else ""
                }]
            }
    
    def _check_format_compliance(self, file_path: str, content: str) -> Dict[str, Any]:
        """フォーマット準拠チェック"""
        
        violations = []
        score = 1.0
        
        try:
            # Black チェック
            result = subprocess.run(
                ['black', '--check', '--quiet', file_path],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                violations.append({
                    "type": "black_format",
                    "description": "Code does not comply with Black formatting",
                    "tool": "black"
                })
                score -= 0.5
        except (subprocess.TimeoutExpired, FileNotFoundError):
            violations.append({
                "type": "black_unavailable",
                "description": "Black formatter not available or timeout",
                "tool": "black"
            })
            score -= 0.1
        
        try:
            # isort チェック
            result = subprocess.run(
                ['isort', '--check-only', '--quiet', file_path],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                violations.append({
                    "type": "import_order",
                    "description": "Import statements are not properly ordered",
                    "tool": "isort"
                })
                score -= 0.3
        except (subprocess.TimeoutExpired, FileNotFoundError):
            violations.append({
                "type": "isort_unavailable",
                "description": "isort not available or timeout",
                "tool": "isort"
            })
            score -= 0.1
        
        return {
            "score": max(0.0, score),
            "violations": violations
        }
    
    def _check_import_organization(self, file_path: str, content: str) -> Dict[str, Any]:
        """インポート整理チェック"""
        
        try:
            tree = ast.parse(content)
            
            imports = []
            violations = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append({
                        "type": type(node).__name__,
                        "line": node.lineno,
                        "module": getattr(node, 'module', None),
                        "names": [alias.name for alias in node.names]
                    })
            
            # 重複インポートチェック
            seen_imports = set()
            for imp in imports:
                import_key = (imp["module"], tuple(imp["names"]))
                if import_key in seen_imports:
                    violations.append({
                        "type": "duplicate_import",
                        "line": imp["line"],
                        "description": f"Duplicate import: {imp['module']} - {imp['names']}"
                    })
                seen_imports.add(import_key)
            
            # スコア計算
            score = 1.0 - (len(violations) * 0.1)
            
            return {
                "score": max(0.0, score),
                "total_imports": len(imports),
                "violations": violations
            }
        
        except SyntaxError:
            return {
                "score": 0.0,
                "violations": [{"type": "syntax_error", "description": "Cannot parse file for import analysis"}]
            }
    
    def _check_docstring_coverage(self, file_path: str, content: str) -> Dict[str, Any]:
        """ドキュメント文字列カバレッジチェック"""
        
        try:
            tree = ast.parse(content)
            
            total_items = 0
            documented_items = 0
            violations = []
            
            # モジュールレベルのdocstring
            if ast.get_docstring(tree):
                documented_items += 1
            else:
                violations.append({
                    "type": "missing_module_docstring",
                    "line": 1,
                    "description": "Module missing docstring"
                })
            total_items += 1
            
            # クラス・関数のdocstring
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    total_items += 1
                    if ast.get_docstring(node):
                        documented_items += 1
                    else:
                        violations.append({
                            "type": "missing_class_docstring",
                            "line": node.lineno,
                            "name": node.name,
                            "description": f"Class '{node.name}' missing docstring"
                        })
                
                elif isinstance(node, ast.FunctionDef):
                    # プライベート関数は除外（オプション）
                    if not node.name.startswith('_'):
                        total_items += 1
                        if ast.get_docstring(node):
                            documented_items += 1
                        else:
                            violations.append({
                                "type": "missing_function_docstring",
                                "line": node.lineno,
                                "name": node.name,
                                "description": f"Function '{node.name}' missing docstring"
                            })
            
            coverage = documented_items / total_items if total_items > 0 else 1.0
            
            return {
                "score": coverage,
                "total_items": total_items,
                "documented_items": documented_items,
                "coverage": coverage,
                "violations": violations
            }
        
        except SyntaxError:
            return {
                "score": 0.0,
                "violations": [{"type": "syntax_error", "description": "Cannot parse file for docstring analysis"}]
            }


class QualityStandardsManager:
    """品質基準管理システム"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "postbox/quality/quality_config.json"
        self.quality_checker = QualityChecker()
        self.standards_config = self._load_standards_config()
        self.improvement_templates = self._initialize_improvement_templates()
    
    def evaluate_file_quality(self, file_path: str) -> QualityReport:
        """ファイル品質評価"""
        
        print(f"🔍 品質評価開始: {file_path}")
        
        # 品質チェック実行
        check_results = self.quality_checker.check_file_quality(file_path)
        
        if "error" in check_results:
            return self._create_error_report(file_path, check_results["error"])
        
        # メトリクス生成
        metrics = self._generate_metrics(file_path, check_results)
        
        # 総合スコア計算
        overall_score = self._calculate_overall_score(metrics)
        
        # 品質レベル決定
        quality_level = self._determine_quality_level(overall_score)
        
        # 違反事項の統合
        violations = self._aggregate_violations(check_results)
        
        # 改善計画生成
        improvement_plan = self._generate_improvement_plan(metrics, violations)
        
        # 改善時間推定
        estimated_time = self._estimate_improvement_time(improvement_plan)
        
        report = QualityReport(
            report_id=f"qr_{int(time.time())}_{Path(file_path).stem}",
            file_path=file_path,
            timestamp=datetime.now().isoformat(),
            overall_score=overall_score,
            quality_level=quality_level,
            metrics=metrics,
            violations=violations,
            improvement_plan=improvement_plan,
            estimated_improvement_time=estimated_time
        )
        
        print(f"✅ 品質評価完了: スコア {overall_score:.2f}, レベル {quality_level.value}")
        return report
    
    def generate_improvement_suggestions(self, report: QualityReport) -> List[ImprovementSuggestion]:
        """改善提案生成"""
        
        suggestions = []
        
        # メトリクス別の改善提案
        for metric in report.metrics:
            if metric.current_value < metric.target_value:
                suggestion = self._create_metric_improvement_suggestion(metric, report)
                if suggestion:
                    suggestions.append(suggestion)
        
        # 違反事項別の改善提案
        violation_types = set(v.get('type', 'unknown') for v in report.violations)
        for violation_type in violation_types:
            suggestion = self._create_violation_improvement_suggestion(violation_type, report)
            if suggestion:
                suggestions.append(suggestion)
        
        # 優先度順でソート
        suggestions.sort(key=lambda x: (-x.priority, -x.expected_impact))
        
        return suggestions
    
    def auto_apply_improvements(self, file_path: str, suggestions: List[ImprovementSuggestion]) -> Dict[str, Any]:
        """自動改善適用"""
        
        print(f"🔧 自動改善適用開始: {file_path}")
        
        results = {
            "file_path": file_path,
            "applied_improvements": [],
            "failed_improvements": [],
            "before_score": 0.0,
            "after_score": 0.0,
            "improvement_delta": 0.0
        }
        
        # 改善前のスコア取得
        before_report = self.evaluate_file_quality(file_path)
        results["before_score"] = before_report.overall_score
        
        # 自動適用可能な改善の実行
        for suggestion in suggestions:
            try:
                if self._can_auto_apply(suggestion):
                    success = self._apply_suggestion(file_path, suggestion)
                    if success:
                        results["applied_improvements"].append({
                            "suggestion_id": suggestion.suggestion_id,
                            "title": suggestion.title,
                            "impact": suggestion.expected_impact
                        })
                    else:
                        results["failed_improvements"].append({
                            "suggestion_id": suggestion.suggestion_id,
                            "title": suggestion.title,
                            "reason": "Application failed"
                        })
                else:
                    results["failed_improvements"].append({
                        "suggestion_id": suggestion.suggestion_id,
                        "title": suggestion.title,
                        "reason": "Manual intervention required"
                    })
            
            except Exception as e:
                results["failed_improvements"].append({
                    "suggestion_id": suggestion.suggestion_id,
                    "title": suggestion.title,
                    "reason": f"Error: {e}"
                })
        
        # 改善後のスコア取得
        if results["applied_improvements"]:
            after_report = self.evaluate_file_quality(file_path)
            results["after_score"] = after_report.overall_score
            results["improvement_delta"] = after_report.overall_score - before_report.overall_score
        
        print(f"✅ 自動改善完了: {len(results['applied_improvements'])}件適用")
        return results
    
    def _load_standards_config(self) -> Dict[str, Any]:
        """品質基準設定読み込み"""
        
        default_config = {
            "target_scores": {
                "type_coverage": 0.95,
                "syntax_accuracy": 1.0,
                "format_compliance": 1.0,
                "import_organization": 0.9,
                "docstring_coverage": 0.8
            },
            "weights": {
                "type_coverage": 0.3,
                "syntax_accuracy": 0.3,
                "format_compliance": 0.2,
                "import_organization": 0.1,
                "docstring_coverage": 0.1
            },
            "quality_thresholds": {
                "excellent": 0.9,
                "good": 0.8,
                "acceptable": 0.7,
                "poor": 0.6
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # マージ
                for key, value in loaded_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
            except Exception as e:
                print(f"⚠️ 設定ファイル読み込みエラー: {e}")
        
        return default_config
    
    def _initialize_improvement_templates(self) -> Dict[str, Any]:
        """改善テンプレート初期化"""
        
        return {
            "type_coverage": {
                "template": "Add type annotations: {function_name}({args}: Any) -> {return_type}:",
                "auto_applicable": True,
                "validation": "mypy --strict"
            },
            "format_compliance": {
                "template": "Apply formatting: black {file_path} && isort {file_path}",
                "auto_applicable": True,
                "validation": "black --check && isort --check-only"
            },
            "docstring_coverage": {
                "template": 'Add docstring: """Description of {item_name}"""',
                "auto_applicable": False,  # 内容が必要なため
                "validation": "manual_review"
            },
            "syntax_error": {
                "template": "Fix syntax error at line {line}: {description}",
                "auto_applicable": False,
                "validation": "python -m py_compile"
            }
        }
    
    def _generate_metrics(self, file_path: str, check_results: Dict[str, Any]) -> List[QualityMetric]:
        """メトリクス生成"""
        
        metrics = []
        current_time = datetime.now().isoformat()
        
        for metric_type, result in check_results.items():
            if isinstance(result, dict) and 'score' in result:
                target_value = self.standards_config["target_scores"].get(metric_type, 0.8)
                
                metric = QualityMetric(
                    metric_id=f"{metric_type}_{Path(file_path).stem}",
                    name=metric_type.replace('_', ' ').title(),
                    description=f"{metric_type} quality measurement",
                    current_value=result['score'],
                    target_value=target_value,
                    measurement_method=f"automated_{metric_type}_check",
                    improvement_suggestions=self._get_metric_suggestions(metric_type, result),
                    severity=self._determine_metric_severity(result['score'], target_value),
                    last_measured=current_time
                )
                metrics.append(metric)
        
        return metrics
    
    def _get_metric_suggestions(self, metric_type: str, result: Dict[str, Any]) -> List[str]:
        """メトリクス別改善提案"""
        
        suggestions = []
        violations = result.get('violations', [])
        
        if metric_type == 'type_coverage':
            if violations:
                suggestions.append("Add missing type annotations to functions and arguments")
                suggestions.append("Import typing modules (Any, Dict, List, Optional)")
                suggestions.append("Use 'Any' type for unknown parameter types")
        
        elif metric_type == 'format_compliance':
            suggestions.append("Run 'black' formatter to fix code formatting")
            suggestions.append("Run 'isort' to organize import statements")
        
        elif metric_type == 'docstring_coverage':
            suggestions.append("Add docstrings to public functions and classes")
            suggestions.append("Include module-level docstring")
        
        elif metric_type == 'syntax_accuracy':
            if violations:
                suggestions.append("Fix syntax errors identified by Python parser")
                suggestions.append("Check indentation consistency")
        
        return suggestions
    
    def _determine_metric_severity(self, current: float, target: float) -> str:
        """メトリクス重要度判定"""
        
        ratio = current / target if target > 0 else 1.0
        
        if ratio >= 0.9:
            return "low"
        elif ratio >= 0.7:
            return "medium"
        else:
            return "high"
    
    def _calculate_overall_score(self, metrics: List[QualityMetric]) -> float:
        """総合スコア計算"""
        
        if not metrics:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric in metrics:
            # メトリクス名から重みを取得
            metric_key = metric.name.lower().replace(' ', '_')
            weight = self.standards_config["weights"].get(metric_key, 0.1)
            
            weighted_sum += metric.current_value * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """品質レベル判定"""
        
        thresholds = self.standards_config["quality_thresholds"]
        
        if score >= thresholds["excellent"]:
            return QualityLevel.EXCELLENT
        elif score >= thresholds["good"]:
            return QualityLevel.GOOD
        elif score >= thresholds["acceptable"]:
            return QualityLevel.ACCEPTABLE
        elif score >= thresholds["poor"]:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def _aggregate_violations(self, check_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """違反事項統合"""
        
        all_violations = []
        
        for metric_type, result in check_results.items():
            if isinstance(result, dict) and 'violations' in result:
                for violation in result['violations']:
                    violation_entry = violation.copy()
                    violation_entry['metric_type'] = metric_type
                    all_violations.append(violation_entry)
        
        return all_violations
    
    def _generate_improvement_plan(self, metrics: List[QualityMetric], violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """改善計画生成"""
        
        plan = []
        
        # メトリクス基準の改善項目
        for metric in metrics:
            if metric.current_value < metric.target_value:
                improvement_item = {
                    "type": "metric_improvement",
                    "metric_name": metric.name,
                    "current_value": metric.current_value,
                    "target_value": metric.target_value,
                    "priority": self._calculate_improvement_priority(metric),
                    "suggestions": metric.improvement_suggestions,
                    "estimated_effort": self._estimate_metric_improvement_effort(metric)
                }
                plan.append(improvement_item)
        
        # 違反基準の改善項目
        violation_groups = {}
        for violation in violations:
            vtype = violation.get('type', 'unknown')
            if vtype not in violation_groups:
                violation_groups[vtype] = []
            violation_groups[vtype].append(violation)
        
        for violation_type, violation_list in violation_groups.items():
            improvement_item = {
                "type": "violation_fix",
                "violation_type": violation_type,
                "count": len(violation_list),
                "priority": self._calculate_violation_priority(violation_type, len(violation_list)),
                "violations": violation_list,
                "estimated_effort": len(violation_list) * 2  # 1件あたり2分と仮定
            }
            plan.append(improvement_item)
        
        # 優先度順でソート
        plan.sort(key=lambda x: -x["priority"])
        
        return plan
    
    def _estimate_improvement_time(self, improvement_plan: List[Dict[str, Any]]) -> int:
        """改善時間推定"""
        
        total_minutes = 0
        
        for item in improvement_plan:
            total_minutes += item.get("estimated_effort", 5)
        
        return total_minutes
    
    def _calculate_improvement_priority(self, metric: QualityMetric) -> int:
        """改善優先度計算"""
        
        gap = metric.target_value - metric.current_value
        severity_weight = {"high": 3, "medium": 2, "low": 1}.get(metric.severity, 1)
        
        return int(gap * 10 * severity_weight)
    
    def _estimate_metric_improvement_effort(self, metric: QualityMetric) -> int:
        """メトリクス改善工数推定"""
        
        gap = metric.target_value - metric.current_value
        base_effort = {
            "Type Coverage": 3,      # 分/不足項目
            "Syntax Accuracy": 5,    # 分/エラー
            "Format Compliance": 1,   # 分（自動）
            "Import Organization": 2, # 分（自動）
            "Docstring Coverage": 8   # 分/欠如項目
        }.get(metric.name, 5)
        
        return int(gap * 10 * base_effort)  # gap * 想定違反数 * 基本工数
    
    def _calculate_violation_priority(self, violation_type: str, count: int) -> int:
        """違反優先度計算"""
        
        type_priorities = {
            "syntax_error": 10,
            "missing_return_type": 7,
            "missing_arg_type": 6,
            "missing_docstring": 4,
            "format_issue": 3,
            "import_order": 2
        }
        
        base_priority = type_priorities.get(violation_type, 5)
        return base_priority + min(count, 5)  # 件数ボーナス（最大5）
    
    def _create_error_report(self, file_path: str, error_message: str) -> QualityReport:
        """エラーレポート作成"""
        
        return QualityReport(
            report_id=f"error_{int(time.time())}_{Path(file_path).stem}",
            file_path=file_path,
            timestamp=datetime.now().isoformat(),
            overall_score=0.0,
            quality_level=QualityLevel.CRITICAL,
            metrics=[],
            violations=[{"type": "evaluation_error", "description": error_message}],
            improvement_plan=[{
                "type": "fix_evaluation_error",
                "priority": 10,
                "description": error_message,
                "estimated_effort": 10
            }],
            estimated_improvement_time=10
        )
    
    def _create_metric_improvement_suggestion(self, metric: QualityMetric, report: QualityReport) -> Optional[ImprovementSuggestion]:
        """メトリクス改善提案作成"""
        
        if metric.current_value >= metric.target_value:
            return None
        
        metric_key = metric.name.lower().replace(' ', '_')
        template = self.improvement_templates.get(metric_key, {})
        
        return ImprovementSuggestion(
            suggestion_id=f"metric_{metric.metric_id}_{int(time.time())}",
            title=f"Improve {metric.name}",
            description=f"Increase {metric.name} from {metric.current_value:.2f} to {metric.target_value:.2f}",
            priority=self._calculate_improvement_priority(metric),
            estimated_effort=self._estimate_metric_improvement_effort(metric),
            expected_impact=(metric.target_value - metric.current_value),
            implementation_steps=metric.improvement_suggestions,
            code_examples=self._get_code_examples(metric_key),
            validation_method=template.get("validation", "manual_check")
        )
    
    def _create_violation_improvement_suggestion(self, violation_type: str, report: QualityReport) -> Optional[ImprovementSuggestion]:
        """違反改善提案作成"""
        
        violations = [v for v in report.violations if v.get('type') == violation_type]
        if not violations:
            return None
        
        return ImprovementSuggestion(
            suggestion_id=f"violation_{violation_type}_{int(time.time())}",
            title=f"Fix {violation_type.replace('_', ' ').title()} Issues",
            description=f"Resolve {len(violations)} {violation_type} violations",
            priority=self._calculate_violation_priority(violation_type, len(violations)),
            estimated_effort=len(violations) * 2,
            expected_impact=0.1 * len(violations),
            implementation_steps=[f"Fix {violation_type} in {len(violations)} locations"],
            code_examples=self._get_violation_code_examples(violation_type),
            validation_method="automated_check"
        )
    
    def _get_code_examples(self, metric_type: str) -> List[str]:
        """コード例取得"""
        
        examples = {
            "type_coverage": [
                "def function(param: Any) -> None:",
                "def process(data: Dict[str, Any]) -> List[Any]:",
                "from typing import Any, Dict, List"
            ],
            "format_compliance": [
                "# Run: black file.py",
                "# Run: isort file.py"
            ],
            "docstring_coverage": [
                '"""Module description."""',
                'def function():\n    """Function description."""'
            ]
        }
        
        return examples.get(metric_type, [])
    
    def _get_violation_code_examples(self, violation_type: str) -> List[str]:
        """違反コード例取得"""
        
        examples = {
            "syntax_error": ["# Fix syntax errors as indicated by Python parser"],
            "missing_return_type": ["def function() -> None:"],
            "missing_arg_type": ["def function(param: Any):"]
        }
        
        return examples.get(violation_type, [])
    
    def _can_auto_apply(self, suggestion: ImprovementSuggestion) -> bool:
        """自動適用可能判定"""
        
        auto_applicable_types = [
            "format_compliance",
            "import_organization"
        ]
        
        return any(t in suggestion.suggestion_id for t in auto_applicable_types)
    
    def _apply_suggestion(self, file_path: str, suggestion: ImprovementSuggestion) -> bool:
        """提案適用"""
        
        try:
            if "format" in suggestion.suggestion_id.lower():
                # Black + isort 実行
                subprocess.run(['black', file_path], check=True, capture_output=True)
                subprocess.run(['isort', file_path], check=True, capture_output=True)
                return True
            
            # その他の自動適用は今後実装
            return False
        
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def save_report(self, report: QualityReport, output_dir: str = "tmp/quality_reports") -> str:
        """レポート保存"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{report.report_id}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 品質レポート保存: {filepath}")
        return filepath


def main():
    """テスト実行"""
    
    # テスト用のサンプルファイル作成
    test_file = "tmp/test_quality_sample.py"
    os.makedirs("tmp", exist_ok=True)
    
    sample_code = '''#!/usr/bin/env python3
import os
import json
from typing import Any

def process_data(data, options):
    """データ処理関数"""
    return data * 2

class DataProcessor:
    def __init__(self, config):
        self.config = config
    
    def process(self, items):
        results = []
        for item in items:
            processed = self.transform(item)
            results.append(processed)
        return results
'''
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(sample_code)
    
    print("🧪 QualityStandardsManager テスト実行")
    
    manager = QualityStandardsManager()
    
    # 品質評価テスト
    print("\n=== 品質評価テスト ===")
    report = manager.evaluate_file_quality(test_file)
    
    print(f"ファイル: {report.file_path}")
    print(f"総合スコア: {report.overall_score:.2f}")
    print(f"品質レベル: {report.quality_level.value}")
    print(f"メトリクス数: {len(report.metrics)}")
    print(f"違反事項: {len(report.violations)}件")
    print(f"改善計画: {len(report.improvement_plan)}項目")
    
    # メトリクス詳細
    print("\n=== メトリクス詳細 ===")
    for metric in report.metrics:
        print(f"{metric.name}: {metric.current_value:.2f}/{metric.target_value:.2f}")
    
    # 改善提案テスト
    print("\n=== 改善提案テスト ===")
    suggestions = manager.generate_improvement_suggestions(report)
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion.title}")
        print(f"   優先度: {suggestion.priority}, 予想効果: {suggestion.expected_impact:.2f}")
        print(f"   推定時間: {suggestion.estimated_effort}分")
    
    # レポート保存テスト
    print("\n=== レポート保存テスト ===")
    saved_path = manager.save_report(report)
    print(f"レポート保存完了: {saved_path}")
    
    # 自動改善テスト（フォーマットのみ）
    print("\n=== 自動改善テスト ===")
    format_suggestions = [s for s in suggestions if 'format' in s.title.lower()]
    if format_suggestions:
        auto_results = manager.auto_apply_improvements(test_file, format_suggestions[:1])
        print(f"適用された改善: {len(auto_results['applied_improvements'])}件")
        print(f"失敗した改善: {len(auto_results['failed_improvements'])}件")
        print(f"スコア改善: {auto_results['improvement_delta']:.3f}")
    
    print("\n🎉 QualityStandardsManager テスト完了")


if __name__ == "__main__":
    main()