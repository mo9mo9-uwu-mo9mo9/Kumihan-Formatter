#!/usr/bin/env python3
"""
TDD Security Test Runner
Issue #640 Phase A.1: セキュリティテスト機能完全実装

セキュリティテストの実行とレポート生成を行います。
- SQLインジェクション検査
- XSS対策検証
- CSRF対策確認
- ファイルアップロード脆弱性テスト
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import logging

# ログ設定
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class SecurityTestResult:
    """セキュリティテスト結果クラス"""
    
    def __init__(self, test_name: str, status: str, message: str, details: Optional[Dict] = None):
        self.test_name = test_name
        self.status = status  # "PASS", "FAIL", "WARNING", "SKIP"
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()


class TDDSecurityTestRunner:
    """TDDセキュリティテスト実行クラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.source_dir = self.project_root / "kumihan_formatter"
        self.test_results: List[SecurityTestResult] = []
        self.report_file = self.project_root / ".tdd_logs" / f"security_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # レポートディレクトリ作成
        self.report_file.parent.mkdir(exist_ok=True)
    
    def run_all_security_tests(self) -> Dict[str, Any]:
        """全セキュリティテストを実行"""
        logger.info("🔒 TDDセキュリティテスト開始")
        
        start_time = time.time()
        
        # 各セキュリティテストを実行
        self._test_sql_injection()
        self._test_xss_protection()
        self._test_csrf_protection()
        self._test_file_upload_security()
        self._test_input_validation()
        self._test_output_encoding()
        self._test_path_traversal()
        self._test_command_injection()
        
        end_time = time.time()
        
        # 結果集計
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "PASS"])
        failed_tests = len([r for r in self.test_results if r.status == "FAIL"])
        warning_tests = len([r for r in self.test_results if r.status == "WARNING"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "warning_tests": warning_tests,
                "success_rate": success_rate,
                "execution_time": end_time - start_time
            },
            "test_results": [
                {
                    "test_name": result.test_name,
                    "status": result.status,
                    "message": result.message,
                    "details": result.details,
                    "timestamp": result.timestamp
                }
                for result in self.test_results
            ],
            "overall_security_status": self._determine_overall_status(success_rate, failed_tests),
            "recommendations": self._generate_recommendations(),
            "report_timestamp": datetime.now().isoformat()
        }
        
        # レポート保存
        self._save_report(report)
        
        # 結果出力
        self._print_results(report)
        
        logger.info(f"🎯 セキュリティテスト完了: {success_rate:.1f}%成功")
        
        return report
    
    def _test_sql_injection(self):
        """SQLインジェクション脆弱性テスト"""
        logger.info("🔍 SQLインジェクション検査開始")
        
        try:
            # データベース関連コードの検索
            sql_patterns = [
                r'SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*\+',  # SQL文字列連結
                r'\.execute\([^)]*%[^)]*\)',  # format使用
                r'f".*SELECT.*{.*}.*"',  # f-string使用
                r'".*\'\s*\+\s*.*\+\s*\'"',  # 文字列連結
            ]
            
            vulnerabilities = []
            for py_file in self.source_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    for pattern in sql_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            vulnerabilities.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "pattern": pattern,
                                "code": match.group()
                            })
                except Exception as e:
                    logger.warning(f"ファイル読み込みエラー {py_file}: {e}")
            
            if vulnerabilities:
                self.test_results.append(SecurityTestResult(
                    "SQL Injection Check",
                    "FAIL",
                    f"潜在的なSQLインジェクション脆弱性を{len(vulnerabilities)}件発見",
                    {"vulnerabilities": vulnerabilities}
                ))
            else:
                self.test_results.append(SecurityTestResult(
                    "SQL Injection Check",
                    "PASS",
                    "SQLインジェクション脆弱性は検出されませんでした"
                ))
                
        except Exception as e:
            self.test_results.append(SecurityTestResult(
                "SQL Injection Check",
                "FAIL",
                f"テスト実行エラー: {str(e)}"
            ))
    
    def _test_xss_protection(self):
        """XSS対策検証テスト"""
        logger.info("🔍 XSS対策検証開始")
        
        try:
            # HTML出力関連コードの検索
            xss_patterns = [
                r'\.write\([^)]*\+[^)]*\)',  # HTML文字列連結
                r'f"<.*{.*}.*>"',  # f-stringでのHTML生成
                r'"<.*"\s*\+\s*.*\+\s*".*>"',  # HTML文字列連結
                r'render_template\([^)]*\+[^)]*\)',  # テンプレート文字列連結
            ]
            
            vulnerabilities = []
            for py_file in self.source_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    for pattern in xss_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            vulnerabilities.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "pattern": pattern,
                                "code": match.group()
                            })
                except Exception as e:
                    logger.warning(f"ファイル読み込みエラー {py_file}: {e}")
            
            if vulnerabilities:
                self.test_results.append(SecurityTestResult(
                    "XSS Protection Check",
                    "WARNING",
                    f"潜在的なXSS脆弱性を{len(vulnerabilities)}件発見",
                    {"vulnerabilities": vulnerabilities}
                ))
            else:
                self.test_results.append(SecurityTestResult(
                    "XSS Protection Check",
                    "PASS",
                    "XSS脆弱性は検出されませんでした"
                ))
                
        except Exception as e:
            self.test_results.append(SecurityTestResult(
                "XSS Protection Check",
                "FAIL",
                f"テスト実行エラー: {str(e)}"
            ))
    
    def _test_csrf_protection(self):
        """CSRF対策確認テスト"""
        logger.info("🔍 CSRF対策確認開始")
        
        try:
            # フォーム処理・状態変更関連コードの検索
            csrf_patterns = [
                r'request\.form\[',  # フォーム処理
                r'request\.args\[',  # GET パラメータ処理
                r'@app\.route.*methods.*POST',  # POSTルート
                r'def.*post\(',  # POST処理関数
            ]
            
            potential_issues = []
            csrf_protection_found = False
            
            for py_file in self.source_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    
                    # CSRF保護の有無確認
                    if 'csrf' in content.lower() or 'token' in content.lower():
                        csrf_protection_found = True
                    
                    for pattern in csrf_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            potential_issues.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "pattern": pattern,
                                "code": match.group()
                            })
                except Exception as e:
                    logger.warning(f"ファイル読み込みエラー {py_file}: {e}")
            
            if potential_issues and not csrf_protection_found:
                self.test_results.append(SecurityTestResult(
                    "CSRF Protection Check",
                    "WARNING",
                    f"CSRF保護が不十分な可能性があります（{len(potential_issues)}件の潜在的問題）",
                    {"potential_issues": potential_issues}
                ))
            elif potential_issues and csrf_protection_found:
                self.test_results.append(SecurityTestResult(
                    "CSRF Protection Check",
                    "PASS",
                    "CSRF保護が実装されています",
                    {"potential_issues": potential_issues}
                ))
            else:
                self.test_results.append(SecurityTestResult(
                    "CSRF Protection Check",
                    "PASS",
                    "フォーム処理が検出されていないため、CSRF脆弱性のリスクは低いです"
                ))
                
        except Exception as e:
            self.test_results.append(SecurityTestResult(
                "CSRF Protection Check",
                "FAIL",
                f"テスト実行エラー: {str(e)}"
            ))
    
    def _test_file_upload_security(self):
        """ファイルアップロードセキュリティテスト"""
        logger.info("🔍 ファイルアップロードセキュリティ検査開始")
        
        try:
            # ファイルアップロード関連コードの検索
            upload_patterns = [
                r'save\(',  # ファイル保存
                r'open\([^)]*wb[^)]*\)',  # バイナリファイル書き込み
                r'\.write\(',  # ファイル書き込み
                r'upload',  # アップロード関連
            ]
            
            upload_functions = []
            for py_file in self.source_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    for pattern in upload_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            upload_functions.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "pattern": pattern,
                                "code": match.group()
                            })
                except Exception as e:
                    logger.warning(f"ファイル読み込みエラー {py_file}: {e}")
            
            if upload_functions:
                self.test_results.append(SecurityTestResult(
                    "File Upload Security Check",
                    "WARNING",
                    f"ファイルアップロード機能を{len(upload_functions)}件検出。セキュリティ検証が必要です",
                    {"upload_functions": upload_functions}
                ))
            else:
                self.test_results.append(SecurityTestResult(
                    "File Upload Security Check",
                    "PASS",
                    "ファイルアップロード機能は検出されませんでした"
                ))
                
        except Exception as e:
            self.test_results.append(SecurityTestResult(
                "File Upload Security Check",
                "FAIL",
                f"テスト実行エラー: {str(e)}"
            ))
    
    def _test_input_validation(self):
        """入力値検証テスト"""
        logger.info("🔍 入力値検証テスト開始")
        
        try:
            # 入力処理関連コードの検索
            input_patterns = [
                r'input\(',  # ユーザー入力
                r'sys\.argv',  # コマンドライン引数
                r'request\.',  # Web リクエスト
                r'json\.loads\(',  # JSON パース
            ]
            
            input_functions = []
            validation_found = False
            
            for py_file in self.source_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    
                    # バリデーション関数の有無確認
                    if any(keyword in content.lower() for keyword in ['validate', 'sanitize', 'escape', 'filter']):
                        validation_found = True
                    
                    for pattern in input_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            input_functions.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "pattern": pattern,
                                "code": match.group()
                            })
                except Exception as e:
                    logger.warning(f"ファイル読み込みエラー {py_file}: {e}")
            
            if input_functions and not validation_found:
                self.test_results.append(SecurityTestResult(
                    "Input Validation Check",
                    "WARNING",
                    f"入力処理を{len(input_functions)}件検出。バリデーション実装を確認してください",
                    {"input_functions": input_functions}
                ))
            elif input_functions and validation_found:
                self.test_results.append(SecurityTestResult(
                    "Input Validation Check",
                    "PASS",
                    f"入力処理{len(input_functions)}件でバリデーション実装を確認",
                    {"input_functions": input_functions}
                ))
            else:
                self.test_results.append(SecurityTestResult(
                    "Input Validation Check",
                    "PASS",
                    "外部入力処理は検出されませんでした"
                ))
                
        except Exception as e:
            self.test_results.append(SecurityTestResult(
                "Input Validation Check",
                "FAIL",
                f"テスト実行エラー: {str(e)}"
            ))
    
    def _test_output_encoding(self):
        """出力エンコーディングテスト"""
        logger.info("🔍 出力エンコーディングテスト開始")
        
        try:
            # 出力処理の検索
            output_patterns = [
                r'print\(',  # 標準出力
                r'write\(',  # ファイル書き込み
                r'return.*["\'].*["\']',  # 文字列返却
            ]
            
            output_functions = []
            encoding_specified = False
            
            for py_file in self.source_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    
                    # エンコーディング指定の確認
                    if 'encoding=' in content or 'utf-8' in content:
                        encoding_specified = True
                    
                    for pattern in output_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            output_functions.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "code": match.group()[:50] + "..." if len(match.group()) > 50 else match.group()
                            })
                except Exception as e:
                    logger.warning(f"ファイル読み込みエラー {py_file}: {e}")
            
            if encoding_specified:
                self.test_results.append(SecurityTestResult(
                    "Output Encoding Check",
                    "PASS",
                    f"適切なエンコーディングが指定されています（出力処理{len(output_functions)}件）"
                ))
            else:
                self.test_results.append(SecurityTestResult(
                    "Output Encoding Check",
                    "WARNING",
                    f"エンコーディング指定を確認してください（出力処理{len(output_functions)}件）"
                ))
                
        except Exception as e:
            self.test_results.append(SecurityTestResult(
                "Output Encoding Check",
                "FAIL",
                f"テスト実行エラー: {str(e)}"
            ))
    
    def _test_path_traversal(self):
        """パストラバーサル脆弱性テスト"""
        logger.info("🔍 パストラバーサル脆弱性テスト開始")
        
        try:
            # ファイルパス操作の検索
            path_patterns = [
                r'open\([^)]*\.\.[^)]*\)',  # 相対パス使用
                r'os\.path\.join\([^)]*\.\.[^)]*\)',  # パス結合
                r'Path\([^)]*\.\.[^)]*\)',  # Pathlib使用
            ]
            
            vulnerabilities = []
            safe_path_usage = False
            
            for py_file in self.source_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    
                    # 安全なパス処理の確認
                    if any(keyword in content for keyword in ['resolve()', 'abspath', 'realpath']):
                        safe_path_usage = True
                    
                    for pattern in path_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            vulnerabilities.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "code": match.group()
                            })
                except Exception as e:
                    logger.warning(f"ファイル読み込みエラー {py_file}: {e}")
            
            if vulnerabilities and not safe_path_usage:
                self.test_results.append(SecurityTestResult(
                    "Path Traversal Check",
                    "FAIL",
                    f"パストラバーサル脆弱性の可能性があります（{len(vulnerabilities)}件）",
                    {"vulnerabilities": vulnerabilities}
                ))
            elif vulnerabilities and safe_path_usage:
                self.test_results.append(SecurityTestResult(
                    "Path Traversal Check",
                    "WARNING",
                    f"パス操作を確認してください（{len(vulnerabilities)}件、安全な処理も確認済み）",
                    {"vulnerabilities": vulnerabilities}
                ))
            else:
                self.test_results.append(SecurityTestResult(
                    "Path Traversal Check",
                    "PASS",
                    "パストラバーサル脆弱性は検出されませんでした"
                ))
                
        except Exception as e:
            self.test_results.append(SecurityTestResult(
                "Path Traversal Check",
                "FAIL",
                f"テスト実行エラー: {str(e)}"
            ))
    
    def _test_command_injection(self):
        """コマンドインジェクション脆弱性テスト"""
        logger.info("🔍 コマンドインジェクション脆弱性テスト開始")
        
        try:
            # システムコマンド実行の検索
            command_patterns = [
                r'os\.system\(',  # os.system使用
                r'subprocess\..*shell=True',  # shell=True使用
                r'eval\(',  # eval使用
                r'exec\(',  # exec使用
            ]
            
            vulnerabilities = []
            for py_file in self.source_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    for pattern in command_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            vulnerabilities.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "pattern": pattern,
                                "code": match.group()
                            })
                except Exception as e:
                    logger.warning(f"ファイル読み込みエラー {py_file}: {e}")
            
            if vulnerabilities:
                self.test_results.append(SecurityTestResult(
                    "Command Injection Check",
                    "FAIL",
                    f"コマンドインジェクション脆弱性の可能性があります（{len(vulnerabilities)}件）",
                    {"vulnerabilities": vulnerabilities}
                ))
            else:
                self.test_results.append(SecurityTestResult(
                    "Command Injection Check",
                    "PASS",
                    "コマンドインジェクション脆弱性は検出されませんでした"
                ))
                
        except Exception as e:
            self.test_results.append(SecurityTestResult(
                "Command Injection Check",
                "FAIL",
                f"テスト実行エラー: {str(e)}"
            ))
    
    def _determine_overall_status(self, success_rate: float, failed_tests: int) -> str:
        """総合セキュリティ状況を判定"""
        if failed_tests == 0 and success_rate >= 90:
            return "EXCELLENT"
        elif failed_tests == 0 and success_rate >= 80:
            return "GOOD"
        elif failed_tests <= 2 and success_rate >= 70:
            return "ACCEPTABLE"
        else:
            return "NEEDS_IMPROVEMENT"
    
    def _generate_recommendations(self) -> List[str]:
        """推奨事項を生成"""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if r.status == "FAIL"]
        warning_tests = [r for r in self.test_results if r.status == "WARNING"]
        
        if failed_tests:
            recommendations.append("重大なセキュリティ問題を即座に修正してください")
            for test in failed_tests:
                recommendations.append(f"- {test.test_name}: {test.message}")
        
        if warning_tests:
            recommendations.append("警告レベルのセキュリティ問題を確認してください")
            for test in warning_tests:
                recommendations.append(f"- {test.test_name}: {test.message}")
        
        recommendations.extend([
            "定期的なセキュリティテストの実行を継続してください",
            "新機能追加時は必ずセキュリティ検証を実施してください",
            "セキュリティ関連のドキュメントを最新に保ってください"
        ])
        
        return recommendations
    
    def _save_report(self, report: Dict[str, Any]):
        """レポートをJSONファイルに保存"""
        try:
            with open(self.report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"📋 セキュリティレポート保存: {self.report_file}")
        except Exception as e:
            logger.error(f"レポート保存エラー: {e}")
    
    def _print_results(self, report: Dict[str, Any]):
        """結果をコンソールに出力"""
        summary = report["test_summary"]
        
        print(f"\n🔒 TDD Security Test Results")
        print(f"=" * 50)
        print(f"総テスト数: {summary['total_tests']}")
        print(f"成功: {summary['passed_tests']}")
        print(f"失敗: {summary['failed_tests']}")
        print(f"警告: {summary['warning_tests']}")
        print(f"成功率: {summary['success_rate']:.1f}%")
        print(f"実行時間: {summary['execution_time']:.2f}秒")
        print(f"総合評価: {report['overall_security_status']}")
        
        print(f"\n📋 テスト詳細")
        print(f"-" * 30)
        for result in self.test_results:
            status_emoji = {
                "PASS": "✅",
                "FAIL": "❌", 
                "WARNING": "⚠️",
                "SKIP": "⏭️"
            }
            print(f"{status_emoji.get(result.status, '❓')} {result.test_name}: {result.message}")
        
        if report["test_summary"]["failed_tests"] > 0:
            print(f"\n🚨 緊急対応が必要な問題があります！")
            sys.exit(1)
        elif report["test_summary"]["warning_tests"] > 0:
            print(f"\n⚠️ 確認が必要な問題があります。")
            sys.exit(0)
        else:
            print(f"\n🎉 セキュリティテスト完全通過！")
            sys.exit(0)


def main():
    """メイン実行関数"""
    runner = TDDSecurityTestRunner()
    
    try:
        report = runner.run_all_security_tests()
        return report
    except Exception as e:
        logger.error(f"セキュリティテスト実行エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()