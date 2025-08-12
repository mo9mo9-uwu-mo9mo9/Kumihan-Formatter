#!/usr/bin/env python3
"""
ComprehensiveQualityValidator
統合品質検証システム - セキュリティ・パフォーマンス・統合テスト・企業レベル品質基準
自動テスト生成・統合テスト実行・セキュリティ検証・パフォーマンス評価
"""

import os
import json
import time
import ast
import subprocess
import datetime
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import concurrent.futures
import threading

class ValidationCategory(Enum):
    """検証カテゴリ"""
    SECURITY = "security"          # セキュリティ検証
    PERFORMANCE = "performance"    # パフォーマンス検証
    INTEGRATION = "integration"    # 統合テスト
    COMPLIANCE = "compliance"      # コンプライアンス検証
    RELIABILITY = "reliability"    # 信頼性検証
    SCALABILITY = "scalability"    # スケーラビリティ検証

class ValidationSeverity(Enum):
    """検証重要度"""
    CRITICAL = "critical"   # 重大
    HIGH = "high"          # 高
    MEDIUM = "medium"      # 中
    LOW = "low"           # 低
    INFO = "info"         # 情報

class ValidationStatus(Enum):
    """検証ステータス"""
    PASSED = "passed"       # 合格
    FAILED = "failed"       # 不合格
    WARNING = "warning"     # 警告
    SKIPPED = "skipped"     # スキップ
    ERROR = "error"         # エラー

@dataclass
class ValidationRule:
    """検証ルール"""
    rule_id: str
    category: ValidationCategory
    severity: ValidationSeverity
    name: str
    description: str
    
    check_function: str  # 実行する検証関数名
    parameters: Dict[str, Any]
    threshold: Optional[float] = None
    timeout_seconds: int = 60
    
    auto_fix_available: bool = False
    enterprise_required: bool = False

@dataclass
class ValidationResult:
    """検証結果"""
    rule: ValidationRule
    status: ValidationStatus
    score: float
    execution_time: float
    
    details: Dict[str, Any]
    findings: List[str]
    recommendations: List[str]
    
    timestamp: str
    
    # メトリクス
    metrics: Optional[Dict[str, Any]] = None
    
    # 修正情報
    auto_fix_applied: bool = False
    manual_action_required: bool = False

class SecurityValidator:
    """セキュリティ検証システム"""
    
    def __init__(self):
        self.security_rules = self._load_security_rules()
        
    def _load_security_rules(self) -> List[ValidationRule]:
        """セキュリティルール読み込み"""
        
        rules = [
            ValidationRule(
                rule_id="SEC001",
                category=ValidationCategory.SECURITY,
                severity=ValidationSeverity.CRITICAL,
                name="危険な関数使用チェック",
                description="eval, exec, subprocess等の危険な関数の使用を検出",
                check_function="check_dangerous_functions",
                parameters={"patterns": [r"eval\s*\(", r"exec\s*\(", r"subprocess\.call.*shell=True"]},
                enterprise_required=True
            ),
            
            ValidationRule(
                rule_id="SEC002",
                category=ValidationCategory.SECURITY,
                severity=ValidationSeverity.HIGH,
                name="機密情報ハードコーディング",
                description="パスワード、APIキー等の機密情報のハードコーディングを検出",
                check_function="check_hardcoded_secrets",
                parameters={"patterns": [r"password\s*=\s*[\"']", r"api_key\s*=\s*[\"']", r"secret\s*=\s*[\"']"]},
                enterprise_required=True
            ),
            
            ValidationRule(
                rule_id="SEC003",
                category=ValidationCategory.SECURITY,
                severity=ValidationSeverity.MEDIUM,
                name="SQLインジェクション脆弱性",
                description="SQLインジェクション脆弱性の可能性を検出",
                check_function="check_sql_injection",
                parameters={"patterns": [r"execute\s*\(\s*[\"'].*%.*[\"']", r"query\s*\+\s*"]},
                enterprise_required=False
            ),
            
            ValidationRule(
                rule_id="SEC004",
                category=ValidationCategory.SECURITY,
                severity=ValidationSeverity.MEDIUM,
                name="暗号化設定検証",
                description="適切な暗号化設定の使用を検証",
                check_function="check_crypto_usage",
                parameters={"weak_algorithms": ["md5", "sha1", "des"]},
                enterprise_required=True
            )
        ]
        
        return rules
    
    def validate_security(self, file_paths: List[str]) -> List[ValidationResult]:
        """セキュリティ検証実行"""
        
        results = []
        
        for rule in self.security_rules:
            print(f"🔒 セキュリティチェック: {rule.name}")
            
            start_time = time.time()
            
            try:
                # 検証関数実行
                check_method = getattr(self, rule.check_function)
                findings = check_method(file_paths, rule.parameters)
                
                execution_time = time.time() - start_time
                
                # 結果判定
                if findings:
                    status = ValidationStatus.FAILED if rule.severity in [
                        ValidationSeverity.CRITICAL, ValidationSeverity.HIGH
                    ] else ValidationStatus.WARNING
                    score = 0.0 if status == ValidationStatus.FAILED else 0.5
                else:
                    status = ValidationStatus.PASSED
                    score = 1.0
                
                recommendations = self._generate_security_recommendations(rule, findings)
                
                result = ValidationResult(
                    rule=rule,
                    status=status,
                    score=score,
                    execution_time=execution_time,
                    details={"files_checked": len(file_paths)},
                    findings=findings,
                    recommendations=recommendations,
                    timestamp=datetime.datetime.now().isoformat(),
                    manual_action_required=len(findings) > 0
                )
                
                results.append(result)
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                result = ValidationResult(
                    rule=rule,
                    status=ValidationStatus.ERROR,
                    score=0.0,
                    execution_time=execution_time,
                    details={"error": str(e)},
                    findings=[f"検証エラー: {str(e)}"],
                    recommendations=["検証システムの確認が必要です"],
                    timestamp=datetime.datetime.now().isoformat()
                )
                
                results.append(result)
        
        return results
    
    def check_dangerous_functions(self, file_paths: List[str], params: Dict[str, Any]) -> List[str]:
        """危険な関数使用チェック"""
        
        findings = []
        patterns = params.get("patterns", [])
        
        for file_path in file_paths:
            if not file_path.endswith('.py'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import re
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(f"{file_path}:{line_num} - 危険な関数使用: {match.group()}")
                        
            except Exception as e:
                findings.append(f"{file_path} - 読み込みエラー: {str(e)}")
        
        return findings
    
    def check_hardcoded_secrets(self, file_paths: List[str], params: Dict[str, Any]) -> List[str]:
        """機密情報ハードコーディングチェック"""
        
        findings = []
        patterns = params.get("patterns", [])
        
        for file_path in file_paths:
            if not file_path.endswith('.py'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import re
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(f"{file_path}:{line_num} - 機密情報ハードコーディング疑い: {match.group()}")
                        
            except Exception as e:
                findings.append(f"{file_path} - 読み込みエラー: {str(e)}")
        
        return findings
    
    def check_sql_injection(self, file_paths: List[str], params: Dict[str, Any]) -> List[str]:
        """SQLインジェクション脆弱性チェック"""
        
        findings = []
        patterns = params.get("patterns", [])
        
        for file_path in file_paths:
            if not file_path.endswith('.py'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import re
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(f"{file_path}:{line_num} - SQLインジェクション脆弱性疑い: {match.group()}")
                        
            except Exception as e:
                findings.append(f"{file_path} - 読み込みエラー: {str(e)}")
        
        return findings
    
    def check_crypto_usage(self, file_paths: List[str], params: Dict[str, Any]) -> List[str]:
        """暗号化設定検証"""
        
        findings = []
        weak_algorithms = params.get("weak_algorithms", [])
        
        for file_path in file_paths:
            if not file_path.endswith('.py'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for weak_algo in weak_algorithms:
                    if weak_algo.lower() in content.lower():
                        findings.append(f"{file_path} - 弱い暗号化アルゴリズム使用疑い: {weak_algo}")
                        
            except Exception as e:
                findings.append(f"{file_path} - 読み込みエラー: {str(e)}")
        
        return findings
    
    def _generate_security_recommendations(self, rule: ValidationRule, findings: List[str]) -> List[str]:
        """セキュリティ推奨事項生成"""
        
        if not findings:
            return ["セキュリティチェック合格"]
        
        recommendations = []
        
        if rule.rule_id == "SEC001":
            recommendations.extend([
                "eval(), exec() の使用を避け、より安全な代替手段を使用してください",
                "subprocess.call() では shell=False を使用してください",
                "入力値の適切な検証・サニタイゼーションを実装してください"
            ])
        elif rule.rule_id == "SEC002":
            recommendations.extend([
                "機密情報は環境変数や設定ファイルから読み込んでください",
                "設定ファイルはバージョン管理から除外してください",
                "機密情報管理システム（HashiCorp Vault等）の使用を検討してください"
            ])
        elif rule.rule_id == "SEC003":
            recommendations.extend([
                "SQLクエリにはパラメータ化クエリを使用してください",
                "ORM（SQLAlchemy等）の使用を検討してください",
                "入力値の適切な検証・エスケープを実装してください"
            ])
        elif rule.rule_id == "SEC004":
            recommendations.extend([
                "SHA-256以上の強力なハッシュアルゴリズムを使用してください",
                "AES-256等の現代的な暗号化アルゴリズムを使用してください",
                "暗号化ライブラリ（cryptography等）の最新版を使用してください"
            ])
        
        return recommendations

class PerformanceValidator:
    """パフォーマンス検証システム"""
    
    def __init__(self):
        self.performance_rules = self._load_performance_rules()
        
    def _load_performance_rules(self) -> List[ValidationRule]:
        """パフォーマンスルール読み込み"""
        
        rules = [
            ValidationRule(
                rule_id="PERF001",
                category=ValidationCategory.PERFORMANCE,
                severity=ValidationSeverity.MEDIUM,
                name="非効率なループパターン",
                description="range(len())等の非効率なループパターンを検出",
                check_function="check_inefficient_loops",
                parameters={"patterns": [r"for\s+\w+\s+in\s+range\(len\(", r"while.*len\(.*\)"]},
                auto_fix_available=True
            ),
            
            ValidationRule(
                rule_id="PERF002",
                category=ValidationCategory.PERFORMANCE,
                severity=ValidationSeverity.LOW,
                name="大量のファイルI/O",
                description="ループ内でのファイルI/O等のパフォーマンス問題を検出",
                check_function="check_file_io_patterns",
                parameters={"patterns": [r"for.*open\(", r"while.*open\("]},
                auto_fix_available=False
            ),
            
            ValidationRule(
                rule_id="PERF003",
                category=ValidationCategory.PERFORMANCE,
                severity=ValidationSeverity.HIGH,
                name="メモリリーク可能性",
                description="メモリリークの可能性があるパターンを検出",
                check_function="check_memory_leaks",
                parameters={"patterns": [r"global\s+\w+\s*=\s*\[\]", r".*\.append\(.*\)\s*$"]},
                enterprise_required=True
            ),
            
            ValidationRule(
                rule_id="PERF004",
                category=ValidationCategory.PERFORMANCE,
                severity=ValidationSeverity.MEDIUM,
                name="CPU集約的処理",
                description="CPU集約的な処理パターンを検出",
                check_function="check_cpu_intensive",
                parameters={"time_threshold": 1.0},  # 1秒以上
                threshold=1.0,
                timeout_seconds=30
            )
        ]
        
        return rules
    
    def validate_performance(self, file_paths: List[str]) -> List[ValidationResult]:
        """パフォーマンス検証実行"""
        
        results = []
        
        for rule in self.performance_rules:
            print(f"⚡ パフォーマンスチェック: {rule.name}")
            
            start_time = time.time()
            
            try:
                # 検証関数実行
                check_method = getattr(self, rule.check_function)
                findings = check_method(file_paths, rule.parameters)
                
                execution_time = time.time() - start_time
                
                # 結果判定
                if findings:
                    status = ValidationStatus.WARNING
                    score = 0.7  # パフォーマンス問題は警告レベル
                else:
                    status = ValidationStatus.PASSED
                    score = 1.0
                
                recommendations = self._generate_performance_recommendations(rule, findings)
                
                result = ValidationResult(
                    rule=rule,
                    status=status,
                    score=score,
                    execution_time=execution_time,
                    details={"files_checked": len(file_paths)},
                    findings=findings,
                    recommendations=recommendations,
                    timestamp=datetime.datetime.now().isoformat(),
                    auto_fix_applied=False,
                    manual_action_required=len(findings) > 0
                )
                
                results.append(result)
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                result = ValidationResult(
                    rule=rule,
                    status=ValidationStatus.ERROR,
                    score=0.0,
                    execution_time=execution_time,
                    details={"error": str(e)},
                    findings=[f"検証エラー: {str(e)}"],
                    recommendations=["検証システムの確認が必要です"],
                    timestamp=datetime.datetime.now().isoformat()
                )
                
                results.append(result)
        
        return results
    
    def check_inefficient_loops(self, file_paths: List[str], params: Dict[str, Any]) -> List[str]:
        """非効率なループパターンチェック"""
        
        findings = []
        patterns = params.get("patterns", [])
        
        for file_path in file_paths:
            if not file_path.endswith('.py'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import re
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(f"{file_path}:{line_num} - 非効率なループ: {match.group().strip()}")
                        
            except Exception as e:
                findings.append(f"{file_path} - 読み込みエラー: {str(e)}")
        
        return findings
    
    def check_file_io_patterns(self, file_paths: List[str], params: Dict[str, Any]) -> List[str]:
        """ファイルI/Oパターンチェック"""
        
        findings = []
        patterns = params.get("patterns", [])
        
        for file_path in file_paths:
            if not file_path.endswith('.py'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import re
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(f"{file_path}:{line_num} - ループ内ファイルI/O: {match.group().strip()}")
                        
            except Exception as e:
                findings.append(f"{file_path} - 読み込みエラー: {str(e)}")
        
        return findings
    
    def check_memory_leaks(self, file_paths: List[str], params: Dict[str, Any]) -> List[str]:
        """メモリリークパターンチェック"""
        
        findings = []
        patterns = params.get("patterns", [])
        
        for file_path in file_paths:
            if not file_path.endswith('.py'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import re
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(f"{file_path}:{line_num} - メモリリーク可能性: {match.group().strip()}")
                        
            except Exception as e:
                findings.append(f"{file_path} - 読み込みエラー: {str(e)}")
        
        return findings
    
    def check_cpu_intensive(self, file_paths: List[str], params: Dict[str, Any]) -> List[str]:
        """CPU集約的処理チェック"""
        
        findings = []
        time_threshold = params.get("time_threshold", 1.0)
        
        # CPU集約的な処理パターンを検出
        cpu_patterns = [
            r"while\s+True:",
            r"for.*range\(\s*\d{4,}\s*\)",  # 大きなrange
            r"time\.sleep\s*\(\s*[0-9]+\s*\)"   # 長いsleep
        ]
        
        for file_path in file_paths:
            if not file_path.endswith('.py'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import re
                for pattern in cpu_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(f"{file_path}:{line_num} - CPU集約的処理疑い: {match.group().strip()}")
                        
            except Exception as e:
                findings.append(f"{file_path} - 読み込みエラー: {str(e)}")
        
        return findings
    
    def _generate_performance_recommendations(self, rule: ValidationRule, findings: List[str]) -> List[str]:
        """パフォーマンス推奨事項生成"""
        
        if not findings:
            return ["パフォーマンスチェック合格"]
        
        recommendations = []
        
        if rule.rule_id == "PERF001":
            recommendations.extend([
                "enumerate() を使用してインデックスと値を同時に取得してください",
                "リスト内包表記やmap(), filter()の使用を検討してください",
                "NumPyやPandasのベクトル化された操作を活用してください"
            ])
        elif rule.rule_id == "PERF002":
            recommendations.extend([
                "ファイルの一括読み込み・書き込みを検討してください",
                "with文を使用したリソース管理を徹底してください",
                "メモリマップドファイルの使用を検討してください"
            ])
        elif rule.rule_id == "PERF003":
            recommendations.extend([
                "グローバル変数の使用を最小限に抑えてください",
                "適切なスコープでの変数定義を心がけてください",
                "ガベージコレクションの動作を理解して設計してください"
            ])
        elif rule.rule_id == "PERF004":
            recommendations.extend([
                "非同期処理（async/await）の使用を検討してください",
                "マルチプロセシング・マルチスレッドの活用を検討してください",
                "処理の分割・バッチ化を検討してください"
            ])
        
        return recommendations

class IntegrationTestGenerator:
    """統合テスト自動生成システム"""
    
    def __init__(self):
        self.test_templates = self._load_test_templates()
        
    def generate_integration_tests(self, file_paths: List[str]) -> List[ValidationResult]:
        """統合テスト自動生成・実行"""
        
        results = []
        
        for file_path in file_paths:
            if not file_path.endswith('.py'):
                continue
                
            print(f"🧪 統合テスト生成: {file_path}")
            
            start_time = time.time()
            
            try:
                # ファイル解析
                module_info = self._analyze_module(file_path)
                
                # テストケース生成
                test_cases = self._generate_test_cases(module_info)
                
                # テスト実行
                test_results = self._execute_tests(test_cases, file_path)
                
                execution_time = time.time() - start_time
                
                # 結果評価
                passed_tests = len([r for r in test_results if r["status"] == "passed"])
                total_tests = len(test_results)
                score = passed_tests / total_tests if total_tests > 0 else 1.0
                
                status = ValidationStatus.PASSED if score >= 0.8 else ValidationStatus.WARNING
                
                findings = []
                if score < 1.0:
                    failed_tests = [r for r in test_results if r["status"] != "passed"]
                    findings = [f"失敗テスト: {t['name']} - {t['error']}" for t in failed_tests]
                
                result = ValidationResult(
                    rule=ValidationRule(
                        rule_id="INT001",
                        category=ValidationCategory.INTEGRATION,
                        severity=ValidationSeverity.MEDIUM,
                        name="統合テスト",
                        description="自動生成された統合テスト",
                        check_function="generate_integration_tests",
                        parameters={}
                    ),
                    status=status,
                    score=score,
                    execution_time=execution_time,
                    details={
                        "total_tests": total_tests,
                        "passed_tests": passed_tests,
                        "functions_tested": len(module_info.get("functions", [])),
                        "classes_tested": len(module_info.get("classes", []))
                    },
                    findings=findings,
                    recommendations=self._generate_test_recommendations(score, module_info),
                    timestamp=datetime.datetime.now().isoformat(),
                    metrics={"test_coverage": score}
                )
                
                results.append(result)
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                result = ValidationResult(
                    rule=ValidationRule(
                        rule_id="INT001",
                        category=ValidationCategory.INTEGRATION,
                        severity=ValidationSeverity.MEDIUM,
                        name="統合テスト",
                        description="自動生成された統合テスト",
                        check_function="generate_integration_tests",
                        parameters={}
                    ),
                    status=ValidationStatus.ERROR,
                    score=0.0,
                    execution_time=execution_time,
                    details={"error": str(e)},
                    findings=[f"テスト生成エラー: {str(e)}"],
                    recommendations=["モジュール構造の確認が必要です"],
                    timestamp=datetime.datetime.now().isoformat()
                )
                
                results.append(result)
        
        return results
    
    def _analyze_module(self, file_path: str) -> Dict[str, Any]:
        """モジュール解析"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # AST解析
            tree = ast.parse(content)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "returns": ast.get_source_segment(content, node.returns) if node.returns else None,
                        "is_public": not node.name.startswith('_')
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({
                        "name": node.name,
                        "methods": methods,
                        "is_public": not node.name.startswith('_')
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    else:
                        imports.append(node.module)
            
            return {
                "file_path": file_path,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "has_main": "if __name__ == '__main__':" in content
            }
            
        except Exception as e:
            print(f"⚠️ モジュール解析エラー: {e}")
            return {"file_path": file_path, "functions": [], "classes": [], "imports": []}
    
    def _generate_test_cases(self, module_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """テストケース生成"""
        
        test_cases = []
        
        # 関数テストケース生成
        for func in module_info.get("functions", []):
            if func["is_public"]:
                test_cases.append({
                    "type": "function",
                    "name": f"test_{func['name']}",
                    "target": func["name"],
                    "test_code": self._generate_function_test(func)
                })
        
        # クラステストケース生成
        for cls in module_info.get("classes", []):
            if cls["is_public"]:
                test_cases.append({
                    "type": "class",
                    "name": f"test_{cls['name']}",
                    "target": cls["name"],
                    "test_code": self._generate_class_test(cls)
                })
        
        # インポートテスト
        if module_info.get("imports"):
            test_cases.append({
                "type": "import",
                "name": "test_imports",
                "target": "imports",
                "test_code": self._generate_import_test(module_info["imports"])
            })
        
        return test_cases
    
    def _generate_function_test(self, func_info: Dict[str, Any]) -> str:
        """関数テストコード生成"""
        
        func_name = func_info["name"]
        args = func_info["args"]
        
        # 簡単なテストコード生成
        test_args = []
        for arg in args:
            if arg == "self":
                continue
            elif "file" in arg.lower() or "path" in arg.lower():
                test_args.append("'test_file.txt'")
            elif "num" in arg.lower() or "count" in arg.lower():
                test_args.append("10")
            elif "str" in arg.lower() or "text" in arg.lower():
                test_args.append("'test_string'")
            else:
                test_args.append("None")
        
        args_str = ", ".join(test_args)
        
        return f"""
def test_{func_name}():
    \"\"\"自動生成されたテスト: {func_name}\"\"\"
    try:
        result = {func_name}({args_str})
        assert result is not None, "関数は値を返すべきです"
        return True
    except Exception as e:
        print(f"テストエラー: {{e}}")
        return False
"""
    
    def _generate_class_test(self, class_info: Dict[str, Any]) -> str:
        """クラステストコード生成"""
        
        class_name = class_info["name"]
        
        return f"""
def test_{class_name}():
    \"\"\"自動生成されたテスト: {class_name}\"\"\"
    try:
        instance = {class_name}()
        assert instance is not None, "クラスのインスタンス化ができるべきです"
        return True
    except Exception as e:
        print(f"テストエラー: {{e}}")
        return False
"""
    
    def _generate_import_test(self, imports: List[str]) -> str:
        """インポートテストコード生成"""
        
        import_statements = []
        for imp in imports:
            if imp:
                import_statements.append(f"import {imp}")
        
        imports_str = "; ".join(import_statements)
        
        return f"""
def test_imports():
    \"\"\"自動生成されたテスト: インポート\"\"\"
    try:
        {imports_str}
        return True
    except ImportError as e:
        print(f"インポートエラー: {{e}}")
        return False
"""
    
    def _execute_tests(self, test_cases: List[Dict[str, Any]], module_path: str) -> List[Dict[str, Any]]:
        """テスト実行"""
        
        results = []
        
        # 一時テストファイル作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(f"import sys\n")
            temp_file.write(f"sys.path.append('{os.path.dirname(module_path)}')\n")
            temp_file.write(f"from {os.path.splitext(os.path.basename(module_path))[0]} import *\n\n")
            
            for test_case in test_cases:
                temp_file.write(test_case["test_code"])
                temp_file.write("\n")
            
            # メイン実行部分
            temp_file.write("\nif __name__ == '__main__':\n")
            for test_case in test_cases:
                temp_file.write(f"    print('{test_case['name']}:', {test_case['name']}())\n")
            
            temp_file_path = temp_file.name
        
        try:
            # テスト実行
            result = subprocess.run(
                ["python3", temp_file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 結果解析
            if result.returncode == 0:
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines:
                    if ':' in line:
                        test_name, test_result = line.split(':', 1)
                        status = "passed" if "True" in test_result else "failed"
                        results.append({
                            "name": test_name.strip(),
                            "status": status,
                            "output": test_result.strip(),
                            "error": None
                        })
            else:
                # エラーの場合
                for test_case in test_cases:
                    results.append({
                        "name": test_case["name"],
                        "status": "error",
                        "output": "",
                        "error": result.stderr
                    })
            
        except subprocess.TimeoutExpired:
            for test_case in test_cases:
                results.append({
                    "name": test_case["name"],
                    "status": "timeout",
                    "output": "",
                    "error": "テストタイムアウト"
                })
        
        except Exception as e:
            for test_case in test_cases:
                results.append({
                    "name": test_case["name"],
                    "status": "error",
                    "output": "",
                    "error": str(e)
                })
        
        finally:
            # 一時ファイル削除
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        return results
    
    def _generate_test_recommendations(self, score: float, module_info: Dict[str, Any]) -> List[str]:
        """テスト推奨事項生成"""
        
        recommendations = []
        
        if score < 0.5:
            recommendations.append("テストが多数失敗しています。コードの基本構造を確認してください")
        elif score < 0.8:
            recommendations.append("一部のテストが失敗しています。エラーメッセージを確認してください")
        else:
            recommendations.append("基本的なテストは通過しています")
        
        if len(module_info.get("functions", [])) > 10:
            recommendations.append("関数が多数あります。単体テストの作成を検討してください")
        
        if len(module_info.get("classes", [])) > 5:
            recommendations.append("クラスが多数あります。統合テストの詳細化を検討してください")
        
        return recommendations
    
    def _load_test_templates(self) -> Dict[str, str]:
        """テストテンプレート読み込み"""
        # 基本的なテストテンプレート
        return {
            "function": "基本関数テストテンプレート",
            "class": "基本クラステストテンプレート",
            "integration": "統合テストテンプレート"
        }

class ComprehensiveQualityValidator:
    """包括的品質検証システム"""
    
    def __init__(self):
        self.security_validator = SecurityValidator()
        self.performance_validator = PerformanceValidator()
        self.integration_test_generator = IntegrationTestGenerator()
        
        self.data_dir = Path("postbox/quality/comprehensive")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.results_path = self.data_dir / "validation_results.json"
        self.summary_path = self.data_dir / "validation_summary.json"
        
        print("🔍 ComprehensiveQualityValidator 初期化完了")
    
    def validate_comprehensive_quality(self, file_paths: List[str], 
                                     enterprise_mode: bool = False,
                                     categories: Optional[List[ValidationCategory]] = None) -> Dict[str, Any]:
        """包括的品質検証実行"""
        
        print(f"🔍 包括的品質検証開始: {len(file_paths)}ファイル")
        if enterprise_mode:
            print("🏢 企業レベル品質基準適用")
        
        start_time = time.time()
        all_results = []
        
        # カテゴリ選択
        if categories is None:
            categories = [ValidationCategory.SECURITY, ValidationCategory.PERFORMANCE, ValidationCategory.INTEGRATION]
        
        # 並列実行でパフォーマンス向上
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            if ValidationCategory.SECURITY in categories:
                futures["security"] = executor.submit(self.security_validator.validate_security, file_paths)
            
            if ValidationCategory.PERFORMANCE in categories:
                futures["performance"] = executor.submit(self.performance_validator.validate_performance, file_paths)
            
            if ValidationCategory.INTEGRATION in categories:
                futures["integration"] = executor.submit(self.integration_test_generator.generate_integration_tests, file_paths)
            
            # 結果取得
            category_results = {}
            for category, future in futures.items():
                try:
                    results = future.result(timeout=300)  # 5分タイムアウト
                    category_results[category] = results
                    all_results.extend(results)
                    print(f"✅ {category} 検証完了: {len(results)}件")
                except concurrent.futures.TimeoutError:
                    print(f"⏰ {category} 検証タイムアウト")
                    category_results[category] = []
                except Exception as e:
                    print(f"❌ {category} 検証エラー: {e}")
                    category_results[category] = []
        
        total_execution_time = time.time() - start_time
        
        # 総合評価
        summary = self._generate_comprehensive_summary(all_results, enterprise_mode, total_execution_time)
        
        # 結果保存
        self._save_validation_results(all_results, summary)
        
        return {
            "summary": summary,
            "results_by_category": category_results,
            "all_results": all_results,
            "execution_time": total_execution_time
        }
    
    def _generate_comprehensive_summary(self, results: List[ValidationResult], 
                                      enterprise_mode: bool, execution_time: float) -> Dict[str, Any]:
        """包括的サマリー生成"""
        
        if not results:
            return {
                "overall_status": ValidationStatus.ERROR.value,
                "overall_score": 0.0,
                "message": "検証結果なし"
            }
        
        # カテゴリ別集計
        category_scores = {}
        category_status = {}
        
        for category in ValidationCategory:
            category_results = [r for r in results if r.rule.category == category]
            if category_results:
                scores = [r.score for r in category_results]
                category_scores[category.value] = sum(scores) / len(scores)
                
                # 最も厳しいステータスを採用
                statuses = [r.status for r in category_results]
                if ValidationStatus.FAILED in statuses:
                    category_status[category.value] = ValidationStatus.FAILED.value
                elif ValidationStatus.ERROR in statuses:
                    category_status[category.value] = ValidationStatus.ERROR.value
                elif ValidationStatus.WARNING in statuses:
                    category_status[category.value] = ValidationStatus.WARNING.value
                else:
                    category_status[category.value] = ValidationStatus.PASSED.value
        
        # 総合スコア計算（重み付き）
        weights = {
            ValidationCategory.SECURITY.value: 0.4,
            ValidationCategory.PERFORMANCE.value: 0.3,
            ValidationCategory.INTEGRATION.value: 0.3
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for category, score in category_scores.items():
            weight = weights.get(category, 0.2)
            weighted_score += score * weight
            total_weight += weight
        
        overall_score = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # 企業レベル品質基準適用
        if enterprise_mode:
            enterprise_threshold = 0.9
            overall_status = ValidationStatus.PASSED if overall_score >= enterprise_threshold else ValidationStatus.FAILED
        else:
            if overall_score >= 0.8:
                overall_status = ValidationStatus.PASSED
            elif overall_score >= 0.6:
                overall_status = ValidationStatus.WARNING
            else:
                overall_status = ValidationStatus.FAILED
        
        # 統計
        total_rules = len(results)
        passed_rules = len([r for r in results if r.status == ValidationStatus.PASSED])
        failed_rules = len([r for r in results if r.status == ValidationStatus.FAILED])
        warning_rules = len([r for r in results if r.status == ValidationStatus.WARNING])
        
        # 推奨事項
        recommendations = self._generate_comprehensive_recommendations(
            results, overall_score, enterprise_mode
        )
        
        return {
            "overall_status": overall_status.value,
            "overall_score": overall_score,
            "enterprise_mode": enterprise_mode,
            "execution_time": execution_time,
            "category_scores": category_scores,
            "category_status": category_status,
            "statistics": {
                "total_rules": total_rules,
                "passed_rules": passed_rules,
                "failed_rules": failed_rules,
                "warning_rules": warning_rules,
                "success_rate": passed_rules / total_rules if total_rules > 0 else 0.0
            },
            "recommendations": recommendations,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def _generate_comprehensive_recommendations(self, results: List[ValidationResult], 
                                             overall_score: float, enterprise_mode: bool) -> List[str]:
        """包括的推奨事項生成"""
        
        recommendations = []
        
        # 総合スコアに基づく推奨事項
        if overall_score < 0.5:
            recommendations.append("品質が基準を大幅に下回っています。緊急の改善が必要です")
        elif overall_score < 0.7:
            recommendations.append("品質改善が必要です。重要な問題から優先的に対応してください")
        elif overall_score < 0.9:
            recommendations.append("基本的な品質は確保されています。細かい改善を継続してください")
        else:
            recommendations.append("優秀な品質レベルです。現在の水準を維持してください")
        
        # カテゴリ別推奨事項
        security_results = [r for r in results if r.rule.category == ValidationCategory.SECURITY]
        if any(r.status == ValidationStatus.FAILED for r in security_results):
            recommendations.append("セキュリティ問題が検出されました。早急な対応が必要です")
        
        performance_results = [r for r in results if r.rule.category == ValidationCategory.PERFORMANCE]
        if any(r.status == ValidationStatus.WARNING for r in performance_results):
            recommendations.append("パフォーマンス改善の余地があります。最適化を検討してください")
        
        integration_results = [r for r in results if r.rule.category == ValidationCategory.INTEGRATION]
        if any(r.status == ValidationStatus.FAILED for r in integration_results):
            recommendations.append("統合テストが失敗しています。コンポーネント間の連携を確認してください")
        
        # 企業モード固有の推奨事項
        if enterprise_mode and overall_score < 0.9:
            recommendations.append("企業レベル品質基準に到達していません。コンプライアンス要件を確認してください")
        
        return recommendations
    
    def _save_validation_results(self, results: List[ValidationResult], summary: Dict[str, Any]) -> None:
        """検証結果保存"""
        
        try:
            # 詳細結果保存（最新のみ）
            results_data = []
            for result in results:
                result_dict = asdict(result)
                # ValidationRule内のEnum値を文字列に変換
                result_dict["rule"]["category"] = result.rule.category.value
                result_dict["rule"]["severity"] = result.rule.severity.value
                result_dict["status"] = result.status.value
                results_data.append(result_dict)
            
            with open(self.results_path, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            # サマリー履歴保存
            summaries = []
            if self.summary_path.exists():
                with open(self.summary_path, 'r', encoding='utf-8') as f:
                    summaries = json.load(f)
            
            summaries.append(summary)
            
            # 履歴サイズ制限（最新100件）
            if len(summaries) > 100:
                summaries = summaries[-100:]
            
            with open(self.summary_path, 'w', encoding='utf-8') as f:
                json.dump(summaries, f, indent=2, ensure_ascii=False)
            
            print(f"📊 検証結果保存完了: {self.results_path}")
            
        except Exception as e:
            print(f"⚠️ 結果保存エラー: {e}")

def main():
    """テスト実行"""
    print("🧪 ComprehensiveQualityValidator テスト開始")
    
    validator = ComprehensiveQualityValidator()
    
    # テストファイル
    test_files = [
        "kumihan_formatter/core/utilities/logger.py",
        "postbox/quality/quality_manager.py"
    ]
    
    # 包括的品質検証実行
    print("\n=== 基本品質検証 ===")
    result = validator.validate_comprehensive_quality(test_files)
    
    summary = result["summary"]
    print(f"\n📊 検証結果サマリー:")
    print(f"   総合ステータス: {summary['overall_status']}")
    print(f"   総合スコア: {summary['overall_score']:.3f}")
    print(f"   実行時間: {summary['execution_time']:.2f}秒")
    print(f"   成功率: {summary['statistics']['success_rate']:.1%}")
    
    # 企業レベル品質検証
    print("\n=== 企業レベル品質検証 ===")
    enterprise_result = validator.validate_comprehensive_quality(
        test_files, 
        enterprise_mode=True
    )
    
    enterprise_summary = enterprise_result["summary"]
    print(f"   企業レベルステータス: {enterprise_summary['overall_status']}")
    print(f"   企業レベルスコア: {enterprise_summary['overall_score']:.3f}")
    
    # 推奨事項表示
    if summary.get("recommendations"):
        print(f"\n💡 推奨事項:")
        for rec in summary["recommendations"][:3]:
            print(f"   - {rec}")
    
    print("✅ ComprehensiveQualityValidator テスト完了")

if __name__ == "__main__":
    main()