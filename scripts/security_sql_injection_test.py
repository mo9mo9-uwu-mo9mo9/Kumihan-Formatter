#!/usr/bin/env python3
"""
SQL Injection Security Test - Issue #640 Phase 3
SQLインジェクション自動テストシステム

目的: 全入力フィールドの自動SQLインジェクションテスト
- 悪意のあるSQLパターン検出
- パラメータ化クエリ検証
- 入力サニタイズ確認
- セキュリティレポート生成
"""

import re
import ast
import sys
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from scripts.tdd_system_base import TDDSystemBase, create_tdd_config, TDDSystemError
from scripts.secure_subprocess import secure_run
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

# 設定ファイル読み込み
def load_security_patterns():
    """セキュリティパターン設定を読み込み"""
    patterns_file = Path(__file__).parent / "security_patterns.json"
    if patterns_file.exists():
        import json
        with open(patterns_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

class SQLInjectionRisk(Enum):
    """SQLインジェクションリスク レベル"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"

@dataclass
class SQLInjectionVulnerability:
    """SQLインジェクション脆弱性情報"""
    file_path: str
    line_number: int
    function_name: str
    vulnerability_type: str
    risk_level: SQLInjectionRisk
    code_snippet: str
    description: str
    recommendation: str
    severity_score: float  # 0-10

@dataclass
class SQLInjectionTestResult:
    """SQLインジェクションテスト結果"""
    total_files_scanned: int
    total_functions_scanned: int
    vulnerabilities_found: List[SQLInjectionVulnerability]
    safe_functions_count: int
    test_duration: float
    timestamp: datetime
    overall_risk: SQLInjectionRisk
    recommendations: List[str]

class SQLInjectionTester(TDDSystemBase):
    """SQLインジェクション自動テストシステム"""
    
    def __init__(self, project_root: Path):
        config = create_tdd_config(project_root)
        super().__init__(config)
        
        # セキュリティパターンを外部ファイルから読み込み
        patterns = load_security_patterns()
        if patterns and 'sql_injection' in patterns:
            sql_patterns = patterns['sql_injection']
            # 危険なSQLパターン
            self.dangerous_sql_patterns = {
                pat_info['pattern']: pat_info['description'] 
                for pat_info in sql_patterns.get('dangerous_patterns', {}).values()
            }
            # 安全なSQLパターン
            self.safe_sql_patterns = {
                pat_info['pattern']: pat_info['description'] 
                for pat_info in sql_patterns.get('safe_patterns', {}).values()
            }
        else:
            # フォールバック: 基本的なパターンを提供
            self.dangerous_sql_patterns = {
                r"[\"']?\s*\+\s*[\"']?": "String concatenation in SQL query",
                r"\.format\s*\(": "String formatting in SQL query",
                r"%s|%d|%[A-Za-z]": "Printf-style formatting in SQL query"
            }
            self.safe_sql_patterns = {
                r"execute\s*\([^,]+,\s*\[": "Parameterized query with list",
                r"execute\s*\([^,]+,\s*\(": "Parameterized query with tuple", 
                r"executemany\s*\(": "Batch parameterized execution"
            }
            logger.info("Using default SQL injection patterns (configuration not available)")
        
        # スキャン対象ファイル
        self.scan_patterns = [
            "**/*.py",
            "!tests/**",
            "!venv/**",
            "!.venv/**",
        ]
        
        self.vulnerabilities = []
        self.scanned_files = 0
        self.scanned_functions = 0
    
    def initialize(self) -> bool:
        """システム初期化"""
        logger.info("🔍 SQLインジェクションテストシステム初期化中...")
        
        # 事前条件確認
        issues = self.validate_preconditions()
        if issues:
            logger.error("初期化失敗:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        
        logger.info("✅ SQLインジェクションテストシステム初期化完了")
        return True
    
    def execute_main_operation(self) -> SQLInjectionTestResult:
        """SQLインジェクションテスト実行"""
        logger.info("🚀 SQLインジェクション自動テスト開始...")
        
        start_time = datetime.now()
        
        try:
            # ソースファイルをスキャン
            self._scan_source_files()
            
            # 結果を分析
            result = self._analyze_results(start_time)
            
            # レポート生成
            self._generate_security_report(result)
            
            logger.info(f"✅ SQLインジェクションテスト完了: {len(self.vulnerabilities)}件の脆弱性発見")
            return result
            
        except Exception as e:
            logger.error("SQLインジェクションテスト実行エラーが発生しました")
            raise TDDSystemError(f"テスト実行失敗: {e}")
    
    def _scan_source_files(self):
        """ソースファイルスキャン"""
        logger.info("📁 ソースファイルスキャン開始...")
        
        for pattern in self.scan_patterns:
            if pattern.startswith('!'):
                continue  # 除外パターンは後で処理
                
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and self._should_scan_file(file_path):
                    self._scan_file(file_path)
                    self.scanned_files += 1
        
        logger.info(f"📊 スキャン完了: {self.scanned_files}ファイル、{self.scanned_functions}関数")
    
    def _should_scan_file(self, file_path: Path) -> bool:
        """ファイルをスキャンすべきかチェック"""
        file_str = str(file_path)
        
        # 除外パターンのチェック
        exclude_patterns = [
            "tests/", "venv/", ".venv/", "__pycache__/",
            ".git/", "build/", "dist/", ".tox/",
        ]
        
        for pattern in exclude_patterns:
            if pattern in file_str:
                return False
        
        return True
    
    def _scan_file(self, file_path: Path):
        """個別ファイルスキャン"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ASTを使用して関数を抽出
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        self._scan_function(file_path, node, content)
                        self.scanned_functions += 1
                        
            except SyntaxError:
                # 構文エラーの場合は文字列ベースのスキャン
                self._scan_content_patterns(file_path, content)
                
        except Exception as e:
            logger.warning(f"ファイルスキャンエラー {file_path}: {e}")
    
    def _scan_function(self, file_path: Path, func_node: ast.FunctionDef, content: str):
        """関数内のSQLインジェクション脆弱性スキャン"""
        func_name = func_node.name
        
        # 関数のソースコード取得
        lines = content.split('\n')
        func_start = func_node.lineno - 1
        func_end = func_node.end_lineno if hasattr(func_node, 'end_lineno') else len(lines)
        func_content = '\n'.join(lines[func_start:func_end])
        
        # 危険なパターンをチェック
        for pattern, description in self.dangerous_sql_patterns.items():
            matches = re.finditer(pattern, func_content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                # 安全なパターンでないことを確認
                if not self._is_safe_context(func_content, match):
                    vulnerability = self._create_vulnerability(
                        file_path, func_start + match.start(), func_name,
                        description, match.group(), func_content
                    )
                    self.vulnerabilities.append(vulnerability)
    
    def _scan_content_patterns(self, file_path: Path, content: str):
        """コンテンツパターンスキャン（AST解析失敗時のフォールバック）"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in self.dangerous_sql_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    if not self._is_safe_line(line):
                        vulnerability = self._create_vulnerability(
                            file_path, line_num, "unknown_function",
                            description, line.strip(), line
                        )
                        self.vulnerabilities.append(vulnerability)
    
    def _is_safe_context(self, func_content: str, match) -> bool:
        """安全なコンテキストかどうかチェック"""
        # マッチした部分の前後をチェック
        match_area = func_content[max(0, match.start()-100):match.end()+100]
        
        # 安全なパターンがあるかチェック
        for safe_pattern in self.safe_sql_patterns.keys():
            if re.search(safe_pattern, match_area, re.IGNORECASE):
                return True
        
        # コメント内かどうかチェック
        if '#' in match_area and match_area.find('#') < match_area.find(match.group()):
            return True
        
        # 文字列リテラル内でない実際のクエリかチェック
        return False
    
    def _is_safe_line(self, line: str) -> bool:
        """行が安全かどうかチェック"""
        # コメント行
        if line.strip().startswith('#'):
            return True
        
        # 安全なパターンを含む
        for safe_pattern in self.safe_sql_patterns.keys():
            if re.search(safe_pattern, line, re.IGNORECASE):
                return True
        
        return False
    
    def _create_vulnerability(self, file_path: Path, line_number: int, 
                            func_name: str, description: str, 
                            code_snippet: str, context: str) -> SQLInjectionVulnerability:
        """脆弱性オブジェクト作成"""
        
        # リスクレベル決定
        risk_level, severity_score = self._assess_risk(description, code_snippet)
        
        # 推奨事項生成
        recommendation = self._generate_recommendation(description)
        
        return SQLInjectionVulnerability(
            file_path=str(file_path.relative_to(self.project_root)),
            line_number=line_number,
            function_name=func_name,
            vulnerability_type=description,
            risk_level=risk_level,
            code_snippet=code_snippet[:200],  # 200文字制限
            description=f"潜在的なSQLインジェクション脆弱性: {description}",
            recommendation=recommendation,
            severity_score=severity_score
        )
    
    def _assess_risk(self, description: str, code_snippet: str) -> Tuple[SQLInjectionRisk, float]:
        """リスクレベル評価"""
        # キーワードベースのリスク評価
        critical_keywords = ['exec', 'eval', 'system']
        high_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        medium_keywords = ['format', 'f-string', 'concatenation']
        
        description_lower = description.lower()
        code_lower = code_snippet.lower()
        
        for keyword in critical_keywords:
            if keyword.lower() in description_lower or keyword.lower() in code_lower:
                return SQLInjectionRisk.CRITICAL, 9.0
        
        for keyword in high_keywords:
            if keyword.lower() in description_lower or keyword.lower() in code_lower:
                return SQLInjectionRisk.HIGH, 7.0
        
        for keyword in medium_keywords:
            if keyword.lower() in description_lower or keyword.lower() in code_lower:
                return SQLInjectionRisk.MEDIUM, 5.0
        
        return SQLInjectionRisk.LOW, 3.0
    
    def _generate_recommendation(self, description: str) -> str:
        """推奨事項生成"""
        recommendations = {
            'String concatenation': 'パラメータ化クエリを使用してください。例: cursor.execute("SELECT * FROM table WHERE id = ?", (user_id,))',
            'String formatting': 'パラメータ化クエリを使用してください。% や .format() の代わりにプレースホルダーを使用',
            'f-string': 'f-stringの代わりにパラメータ化クエリを使用してください',
            'exec() function': 'exec()の使用を避け、安全な代替手段を検討してください',
            'eval() function': 'eval()の使用を避け、安全な代替手段を検討してください',
            'Dynamic': 'クエリを動的に構築する代わりに、事前定義されたクエリとパラメータを使用してください',
        }
        
        for keyword, recommendation in recommendations.items():
            if keyword.lower() in description.lower():
                return recommendation
        
        return 'パラメータ化クエリを使用し、ユーザー入力を直接SQL文字列に組み込まないでください'
    
    def _analyze_results(self, start_time: datetime) -> SQLInjectionTestResult:
        """結果分析"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 全体リスクレベル決定
        overall_risk = self._calculate_overall_risk()
        
        # 推奨事項生成
        recommendations = self._generate_recommendations()
        
        safe_functions = self.scanned_functions - len([v for v in self.vulnerabilities])
        
        return SQLInjectionTestResult(
            total_files_scanned=self.scanned_files,
            total_functions_scanned=self.scanned_functions,
            vulnerabilities_found=self.vulnerabilities,
            safe_functions_count=safe_functions,
            test_duration=duration,
            timestamp=end_time,
            overall_risk=overall_risk,
            recommendations=recommendations
        )
    
    def _calculate_overall_risk(self) -> SQLInjectionRisk:
        """全体リスクレベル計算"""
        if not self.vulnerabilities:
            return SQLInjectionRisk.SAFE
        
        risk_counts = {}
        for vuln in self.vulnerabilities:
            risk_counts[vuln.risk_level] = risk_counts.get(vuln.risk_level, 0) + 1
        
        if risk_counts.get(SQLInjectionRisk.CRITICAL, 0) > 0:
            return SQLInjectionRisk.CRITICAL
        elif risk_counts.get(SQLInjectionRisk.HIGH, 0) > 0:
            return SQLInjectionRisk.HIGH
        elif risk_counts.get(SQLInjectionRisk.MEDIUM, 0) > 0:
            return SQLInjectionRisk.MEDIUM
        else:
            return SQLInjectionRisk.LOW
    
    def _generate_recommendations(self) -> List[str]:
        """推奨事項リスト生成"""
        recommendations = [
            "全てのデータベースクエリでパラメータ化クエリを使用する",
            "ユーザー入力を直接SQL文字列に組み込まない",
            "入力データの検証とサニタイズを実装する",
            "最小権限の原則でデータベースアクセス権限を設定する",
            "定期的なセキュリティテストの実行",
        ]
        
        if self.vulnerabilities:
            recommendations.append("発見された脆弱性を優先度に応じて修正する")
            recommendations.append("コードレビューでセキュリティ観点を強化する")
        
        return recommendations
    
    def _generate_security_report(self, result: SQLInjectionTestResult):
        """セキュリティレポート生成"""
        report_file = self.project_root / "sql_injection_security_report.json"
        
        report_data = {
            "scan_summary": {
                "total_files": result.total_files_scanned,
                "total_functions": result.total_functions_scanned,
                "vulnerabilities_found": len(result.vulnerabilities_found),
                "safe_functions": result.safe_functions_count,
                "overall_risk": result.overall_risk.value,
                "test_duration": result.test_duration,
                "timestamp": result.timestamp.isoformat()
            },
            "vulnerabilities": [
                {
                    "file": vuln.file_path,
                    "line": vuln.line_number,
                    "function": vuln.function_name,
                    "type": vuln.vulnerability_type,
                    "risk": vuln.risk_level.value,
                    "severity_score": vuln.severity_score,
                    "code": vuln.code_snippet,
                    "description": vuln.description,
                    "recommendation": vuln.recommendation
                }
                for vuln in result.vulnerabilities_found
            ],
            "recommendations": result.recommendations,
            "risk_distribution": self._get_risk_distribution(result.vulnerabilities_found)
        }
        
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 セキュリティレポート生成: {report_file}")
    
    def _get_risk_distribution(self, vulnerabilities: List[SQLInjectionVulnerability]) -> Dict[str, int]:
        """リスク分布取得"""
        distribution = {}
        for vuln in vulnerabilities:
            risk = vuln.risk_level.value
            distribution[risk] = distribution.get(risk, 0) + 1
        return distribution

def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent
    
    logger.info("🚀 SQLインジェクション自動テスト開始")
    
    try:
        with SQLInjectionTester(project_root) as tester:
            result = tester.run()
            
            # 結果サマリー表示
            logger.info("📊 テスト結果サマリー:")
            logger.info(f"  スキャンしたファイル: {result.total_files_scanned}")
            logger.info(f"  スキャンした関数: {result.total_functions_scanned}")
            logger.info(f"  発見された脆弱性: {len(result.vulnerabilities_found)}")
            logger.info(f"  全体リスクレベル: {result.overall_risk.value}")
            logger.info(f"  実行時間: {result.test_duration:.2f}秒")
            
            # 重要な脆弱性を表示
            critical_vulns = [v for v in result.vulnerabilities_found 
                            if v.risk_level in [SQLInjectionRisk.CRITICAL, SQLInjectionRisk.HIGH]]
            
            if critical_vulns:
                logger.warning(f"🚨 高リスク脆弱性 {len(critical_vulns)}件:")
                for vuln in critical_vulns[:5]:  # 上位5件表示
                    logger.warning(f"  - {vuln.file_path}:{vuln.line_number} ({vuln.risk_level.value})")
            
            return 0 if result.overall_risk in [SQLInjectionRisk.SAFE, SQLInjectionRisk.LOW] else 1
            
    except Exception as e:
        logger.error("💥 SQLインジェクションテスト実行エラーが発生しました")
        return 1

if __name__ == "__main__":
    sys.exit(main())