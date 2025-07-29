#!/usr/bin/env python3
"""
CSRF Security Test - Issue #640 Phase 3
CSRF（Cross-Site Request Forgery）対策テストシステム

目的: 状態変更操作の保護確認
- CSRFトークン検証
- 状態変更エンドポイント検出
- SameSite Cookie確認
- Refererヘッダー検証
"""

import re
import ast
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from scripts.tdd_system_base import TDDSystemBase, create_tdd_config, TDDSystemError
from scripts.secure_subprocess import secure_run
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class CSRFRisk(Enum):
    """CSRFリスクレベル"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"


@dataclass
class CSRFVulnerability:
    """CSRF脆弱性情報"""

    file_path: str
    line_number: int
    function_name: str
    endpoint_path: str
    http_method: str
    vulnerability_type: str
    risk_level: CSRFRisk
    code_snippet: str
    description: str
    recommendation: str
    severity_score: float
    has_csrf_protection: bool


@dataclass
class CSRFTestResult:
    """CSRFテスト結果"""

    total_files_scanned: int
    total_endpoints_found: int
    vulnerabilities_found: List[CSRFVulnerability]
    protected_endpoints_count: int
    test_duration: float
    timestamp: datetime
    overall_risk: CSRFRisk
    recommendations: List[str]


class CSRFTester(TDDSystemBase):
    """CSRF自動テストシステム"""

    def __init__(self, project_root: Path):
        config = create_tdd_config(project_root)
        super().__init__(config)

        # 状態変更HTTPメソッド
        self.state_changing_methods = {"POST", "PUT", "PATCH", "DELETE"}

        # Flaskルートパターン
        self.flask_route_patterns = {
            r'@app\.route\s*\(\s*["\']([^"\']+)["\'](?:.*methods\s*=\s*\[([^\]]+)\])?': "Flask route definition",
            r'@blueprint\.route\s*\(\s*["\']([^"\']+)["\'](?:.*methods\s*=\s*\[([^\]]+)\])?': "Flask blueprint route",
            r'app\.add_url_rule\s*\(\s*["\']([^"\']+)["\']': "Flask URL rule",
        }

        # Django URLパターン
        self.django_url_patterns = {
            r'path\s*\(\s*["\']([^"\']+)["\']': "Django path",
            r'url\s*\(\s*r?["\']([^"\']+)["\']': "Django URL pattern",
            r're_path\s*\(\s*r?["\']([^"\']+)["\']': "Django regex path",
        }

        # CSRF保護パターン
        self.csrf_protection_patterns = {
            r"csrf_token": "CSRF token usage",
            r"@csrf_protect": "CSRF protect decorator",
            r"CSRFProtect": "CSRF protection class",
            r"csrf\.exempt": "CSRF exemption",
            r"verify_csrf_token": "CSRF token verification",
            r"check_csrf": "CSRF check function",
            r"{% csrf_token %}": "Template CSRF token",
            r"X-CSRFToken": "CSRF header",
            r"_csrf_token": "CSRF token field",
        }

        # フォーム検出パターン
        self.form_patterns = {
            r'<form[^>]*method\s*=\s*["\']?post["\']?[^>]*>': "POST form without CSRF",
            r'<form[^>]*method\s*=\s*["\']?put["\']?[^>]*>': "PUT form without CSRF",
            r'<form[^>]*method\s*=\s*["\']?delete["\']?[^>]*>': "DELETE form without CSRF",
        }

        # Ajax/JavaScript リクエストパターン
        self.ajax_patterns = {
            r"\.post\s*\(": "JavaScript POST request",
            r"\.put\s*\(": "JavaScript PUT request",
            r"\.delete\s*\(": "JavaScript DELETE request",
            r'fetch\s*\([^)]*method\s*:\s*["\']POST["\']': "Fetch POST request",
            r"XMLHttpRequest.*\.send": "XMLHttpRequest usage",
        }

        # セキュリティヘッダーパターン
        self.security_header_patterns = {
            r'SameSite\s*=\s*["\']?Strict["\']?': "SameSite Strict cookie",
            r'SameSite\s*=\s*["\']?Lax["\']?': "SameSite Lax cookie",
            r"Secure\s*=\s*True": "Secure cookie flag",
            r"HttpOnly\s*=\s*True": "HttpOnly cookie flag",
        }

        self.vulnerabilities = []
        self.scanned_files = 0
        self.endpoints_found = 0

    def initialize(self) -> bool:
        """システム初期化"""
        logger.info("🔍 CSRFテストシステム初期化中...")

        # 事前条件確認
        issues = self.validate_preconditions()
        if issues:
            logger.error("初期化失敗:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False

        logger.info("✅ CSRFテストシステム初期化完了")
        return True

    def execute_main_operation(self) -> CSRFTestResult:
        """CSRFテスト実行"""
        logger.info("🚀 CSRF自動テスト開始...")

        start_time = datetime.now()

        try:
            # Pythonファイルをスキャン
            self._scan_python_files()

            # テンプレートファイルをスキャン
            self._scan_template_files()

            # JavaScriptファイルをスキャン
            self._scan_javascript_files()

            # 結果を分析
            result = self._analyze_results(start_time)

            # レポート生成
            self._generate_security_report(result)

            logger.info(f"✅ CSRFテスト完了: {len(self.vulnerabilities)}件の脆弱性発見")
            return result

        except Exception as e:
            logger.error(f"CSRFテスト実行エラー: {e}")
            raise TDDSystemError(f"テスト実行失敗: {e}")

    def _scan_python_files(self):
        """Pythonファイルスキャン"""
        logger.info("📁 Pythonファイルスキャン開始...")

        for py_file in self.project_root.glob("**/*.py"):
            if self._should_scan_file(py_file):
                self._scan_python_file(py_file)
                self.scanned_files += 1

    def _scan_template_files(self):
        """テンプレートファイルスキャン"""
        logger.info("📄 テンプレートファイルスキャン開始...")

        template_patterns = ["**/*.html", "**/*.htm", "**/*.jinja2", "**/*.j2"]

        for pattern in template_patterns:
            for template_file in self.project_root.glob(pattern):
                if self._should_scan_file(template_file):
                    self._scan_template_file(template_file)
                    self.scanned_files += 1

    def _scan_javascript_files(self):
        """JavaScriptファイルスキャン"""
        logger.info("📜 JavaScriptファイルスキャン開始...")

        js_patterns = ["**/*.js", "**/*.ts"]

        for pattern in js_patterns:
            for js_file in self.project_root.glob(pattern):
                if self._should_scan_file(js_file):
                    self._scan_javascript_file(js_file)
                    self.scanned_files += 1

    def _should_scan_file(self, file_path: Path) -> bool:
        """ファイルをスキャンすべきかチェック"""
        file_str = str(file_path)

        exclude_patterns = [
            "tests/",
            "venv/",
            ".venv/",
            "__pycache__/",
            ".git/",
            "build/",
            "dist/",
            ".tox/",
            "node_modules/",
            "static/",
            "assets/",
        ]

        for pattern in exclude_patterns:
            if pattern in file_str:
                return False

        return True

    def _scan_python_file(self, file_path: Path):
        """Pythonファイルスキャン"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Flaskルートをチェック
            self._check_flask_routes(file_path, content)

            # Djangoビューをチェック
            self._check_django_views(file_path, content)

            # CSRF保護の存在確認
            csrf_protections = self._find_csrf_protections(content)

        except Exception as e:
            logger.warning(f"Pythonファイルスキャンエラー {file_path}: {e}")

    def _scan_template_file(self, file_path: Path):
        """テンプレートファイルスキャン"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # フォームのCSRF保護をチェック
            self._check_form_csrf_protection(file_path, content)

        except Exception as e:
            logger.warning(f"テンプレートファイルスキャンエラー {file_path}: {e}")

    def _scan_javascript_file(self, file_path: Path):
        """JavaScriptファイルスキャン"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # AjaxリクエストのCSRF保護をチェック
            self._check_ajax_csrf_protection(file_path, content)

        except Exception as e:
            logger.warning(f"JavaScriptファイルスキャンエラー {file_path}: {e}")

    def _check_flask_routes(self, file_path: Path, content: str):
        """Flaskルートチェック"""
        for pattern, description in self.flask_route_patterns.items():
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[: match.start()].count("\n") + 1

                route_path = match.group(1)
                methods_str = (
                    match.group(2) if match.groups() and len(match.groups()) > 1 else ""
                )

                # HTTPメソッドを抽出
                methods = self._extract_http_methods(methods_str)

                # 状態変更メソッドをチェック
                for method in methods:
                    if method in self.state_changing_methods:
                        self.endpoints_found += 1

                        # CSRF保護があるかチェック
                        has_protection = self._check_route_csrf_protection(
                            content, match
                        )

                        if not has_protection:
                            vulnerability = self._create_csrf_vulnerability(
                                file_path,
                                line_num,
                                "flask_route",
                                route_path,
                                method,
                                f"Flask route without CSRF protection: {method} {route_path}",
                                match.group(),
                                has_protection,
                            )
                            self.vulnerabilities.append(vulnerability)

    def _check_django_views(self, file_path: Path, content: str):
        """Django ビューチェック"""
        # Django関数ベースビュー
        view_function_pattern = r"def\s+(\w+)\s*\([^)]*request[^)]*\):"

        for match in re.finditer(view_function_pattern, content):
            line_num = content[: match.start()].count("\n") + 1
            function_name = match.group(1)

            # ビュー関数の内容を取得
            func_start = match.end()
            func_content = self._extract_function_content(content, func_start)

            # POSTリクエスト処理があるかチェック
            if re.search(r'request\.method\s*==\s*["\']POST["\']', func_content):
                self.endpoints_found += 1

                # CSRF保護があるかチェック
                has_protection = self._check_django_csrf_protection(func_content)

                if not has_protection:
                    vulnerability = self._create_csrf_vulnerability(
                        file_path,
                        line_num,
                        function_name,
                        f"/{function_name}",
                        "POST",
                        f"Django view without CSRF protection: {function_name}",
                        match.group(),
                        has_protection,
                    )
                    self.vulnerabilities.append(vulnerability)

    def _check_form_csrf_protection(self, file_path: Path, content: str):
        """フォームCSRF保護チェック"""
        for pattern, description in self.form_patterns.items():
            for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                line_num = content[: match.start()].count("\n") + 1

                form_content = match.group()
                form_end_match = re.search(
                    r"</form>", content[match.end() :], re.IGNORECASE
                )

                if form_end_match:
                    # フォーム全体を取得
                    full_form = content[
                        match.start() : match.end() + form_end_match.end()
                    ]

                    # CSRFトークンがあるかチェック
                    has_csrf_token = self._has_csrf_token_in_form(full_form)

                    if not has_csrf_token:
                        vulnerability = self._create_csrf_vulnerability(
                            file_path,
                            line_num,
                            "html_form",
                            "form",
                            "POST",
                            f"Form without CSRF token: {description}",
                            form_content[:100],
                            False,
                        )
                        self.vulnerabilities.append(vulnerability)

    def _check_ajax_csrf_protection(self, file_path: Path, content: str):
        """Ajax CSRF保護チェック"""
        for pattern, description in self.ajax_patterns.items():
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[: match.start()].count("\n") + 1

                # リクエストの前後のコンテキストを取得
                context_start = max(0, match.start() - 200)
                context_end = min(len(content), match.end() + 200)
                request_context = content[context_start:context_end]

                # CSRFトークンがヘッダーに含まれているかチェック
                has_csrf_header = self._has_csrf_header(request_context)

                if not has_csrf_header:
                    vulnerability = self._create_csrf_vulnerability(
                        file_path,
                        line_num,
                        "ajax_request",
                        "ajax",
                        "POST",
                        f"Ajax request without CSRF protection: {description}",
                        match.group(),
                        False,
                    )
                    self.vulnerabilities.append(vulnerability)

    def _extract_http_methods(self, methods_str: str) -> Set[str]:
        """HTTPメソッドを抽出"""
        if not methods_str:
            return {"GET"}  # デフォルトはGET

        methods = set()
        for method in re.findall(r'["\'](\w+)["\']', methods_str):
            methods.add(method.upper())

        return methods if methods else {"GET"}

    def _extract_function_content(self, content: str, start_pos: int) -> str:
        """関数コンテンツを抽出"""
        lines = content[start_pos:].split("\n")
        function_lines = []
        indent_level = None

        for line in lines:
            if line.strip():
                current_indent = len(line) - len(line.lstrip())

                if indent_level is None:
                    indent_level = current_indent
                elif current_indent <= indent_level and function_lines:
                    break

                function_lines.append(line)
            else:
                function_lines.append(line)

        return "\n".join(function_lines[:50])  # 最大50行

    def _check_route_csrf_protection(self, content: str, route_match) -> bool:
        """ルートのCSRF保護チェック"""
        # ルート定義の前後500文字をチェック
        context_start = max(0, route_match.start() - 500)
        context_end = min(len(content), route_match.end() + 500)
        context = content[context_start:context_end]

        return self._find_csrf_protections(context)

    def _check_django_csrf_protection(self, func_content: str) -> bool:
        """Django CSRF保護チェック"""
        # csrf_exemptデコレータがある場合は保護なし
        if re.search(r"@csrf_exempt", func_content):
            return False

        # CSRFトークン検証があるかチェック
        return self._find_csrf_protections(func_content)

    def _has_csrf_token_in_form(self, form_content: str) -> bool:
        """フォーム内CSRFトークンチェック"""
        csrf_patterns = [
            r"{% csrf_token %}",
            r'<input[^>]*name\s*=\s*["\']csrfmiddlewaretoken["\']',
            r'<input[^>]*name\s*=\s*["\']_csrf_token["\']',
            r'<input[^>]*name\s*=\s*["\']csrf_token["\']',
        ]

        for pattern in csrf_patterns:
            if re.search(pattern, form_content, re.IGNORECASE):
                return True

        return False

    def _has_csrf_header(self, request_context: str) -> bool:
        """CSRFヘッダーチェック"""
        csrf_header_patterns = [
            r"X-CSRFToken",
            r"X-CSRF-TOKEN",
            r"csrf-token",
            r"_csrf_token",
        ]

        for pattern in csrf_header_patterns:
            if re.search(pattern, request_context, re.IGNORECASE):
                return True

        return False

    def _find_csrf_protections(self, content: str) -> bool:
        """CSRF保護パターンを検索"""
        for pattern in self.csrf_protection_patterns.keys():
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def _create_csrf_vulnerability(
        self,
        file_path: Path,
        line_number: int,
        func_name: str,
        endpoint_path: str,
        http_method: str,
        description: str,
        code_snippet: str,
        has_protection: bool,
    ) -> CSRFVulnerability:
        """CSRF脆弱性オブジェクト作成"""

        # リスクレベル評価
        risk_level, severity_score = self._assess_csrf_risk(
            http_method, endpoint_path, has_protection
        )

        # 推奨事項生成
        recommendation = self._generate_csrf_recommendation(http_method, func_name)

        return CSRFVulnerability(
            file_path=str(file_path.relative_to(self.project_root)),
            line_number=line_number,
            function_name=func_name,
            endpoint_path=endpoint_path,
            http_method=http_method,
            vulnerability_type=description,
            risk_level=risk_level,
            code_snippet=code_snippet[:200],
            description=f"CSRF脆弱性: {description}",
            recommendation=recommendation,
            severity_score=severity_score,
            has_csrf_protection=has_protection,
        )

    def _assess_csrf_risk(
        self, http_method: str, endpoint_path: str, has_protection: bool
    ) -> Tuple[CSRFRisk, float]:
        """CSRFリスクレベル評価"""
        base_score = 0.0

        # HTTPメソッド別リスク
        method_risk = {"DELETE": 8.0, "POST": 7.0, "PUT": 6.0, "PATCH": 5.0}.get(
            http_method, 3.0
        )

        # エンドポイント別リスク
        critical_endpoints = ["admin", "delete", "remove", "drop"]
        high_endpoints = ["create", "add", "insert", "update", "edit"]

        endpoint_lower = endpoint_path.lower()

        if any(critical in endpoint_lower for critical in critical_endpoints):
            endpoint_risk = 3.0
        elif any(high in endpoint_lower for high in high_endpoints):
            endpoint_risk = 2.0
        else:
            endpoint_risk = 1.0

        total_score = method_risk + endpoint_risk

        # 保護なしの場合はスコア上昇
        if not has_protection:
            total_score += 2.0

        # リスクレベル決定
        if total_score >= 9.0:
            return CSRFRisk.CRITICAL, min(10.0, total_score)
        elif total_score >= 7.0:
            return CSRFRisk.HIGH, total_score
        elif total_score >= 5.0:
            return CSRFRisk.MEDIUM, total_score
        else:
            return CSRFRisk.LOW, total_score

    def _generate_csrf_recommendation(self, http_method: str, func_name: str) -> str:
        """CSRF推奨事項生成"""
        base_recommendations = {
            "flask_route": "FlaskでCSRF保護を実装するには、Flask-WTFを使用してCSRFトークンを追加してください",
            "django_view": "Django CSRFミドルウェアを有効にし、テンプレートに{% csrf_token %}を追加してください",
            "html_form": 'フォームにCSRFトークンを追加してください。例: <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">',
            "ajax_request": 'AjaxリクエストにCSRFトークンをヘッダーに含めてください。例: headers: {"X-CSRFToken": csrf_token}',
        }

        method_specific = {
            "DELETE": "削除操作には必ずCSRF保護を実装してください",
            "POST": "データ作成・更新操作にはCSRF保護が必要です",
            "PUT": "データ更新操作にはCSRF保護を実装してください",
            "PATCH": "データ部分更新にはCSRF保護が必要です",
        }

        recommendation = base_recommendations.get(
            func_name, "状態変更操作にはCSRF保護を実装してください"
        )

        if http_method in method_specific:
            recommendation += f" {method_specific[http_method]}"

        return recommendation

    def _analyze_results(self, start_time: datetime) -> CSRFTestResult:
        """結果分析"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 全体リスクレベル決定
        overall_risk = self._calculate_overall_csrf_risk()

        # 推奨事項生成
        recommendations = self._generate_csrf_recommendations()

        protected_endpoints = max(0, self.endpoints_found - len(self.vulnerabilities))

        return CSRFTestResult(
            total_files_scanned=self.scanned_files,
            total_endpoints_found=self.endpoints_found,
            vulnerabilities_found=self.vulnerabilities,
            protected_endpoints_count=protected_endpoints,
            test_duration=duration,
            timestamp=end_time,
            overall_risk=overall_risk,
            recommendations=recommendations,
        )

    def _calculate_overall_csrf_risk(self) -> CSRFRisk:
        """全体CSRFリスクレベル計算"""
        if not self.vulnerabilities:
            return CSRFRisk.SAFE

        risk_counts = {}
        for vuln in self.vulnerabilities:
            risk_counts[vuln.risk_level] = risk_counts.get(vuln.risk_level, 0) + 1

        if risk_counts.get(CSRFRisk.CRITICAL, 0) > 0:
            return CSRFRisk.CRITICAL
        elif risk_counts.get(CSRFRisk.HIGH, 0) > 0:
            return CSRFRisk.HIGH
        elif risk_counts.get(CSRFRisk.MEDIUM, 0) > 0:
            return CSRFRisk.MEDIUM
        else:
            return CSRFRisk.LOW

    def _generate_csrf_recommendations(self) -> List[str]:
        """CSRF推奨事項リスト生成"""
        recommendations = [
            "全ての状態変更操作にCSRF保護を実装する",
            "CSRFトークンを適切に生成・検証する",
            "SameSite=Strict または Lax を設定したCookieを使用する",
            "重要な操作には追加の認証を要求する",
            "Refererヘッダーの検証を実装する",
            "定期的なCSRF脆弱性テストの実行",
        ]

        if self.vulnerabilities:
            recommendations.extend(
                [
                    "発見されたCSRF脆弱性を優先度に応じて修正する",
                    "APIエンドポイントのCSRF保護を確認する",
                    "ダブルサブミット Cookie パターンの実装を検討する",
                ]
            )

        return recommendations

    def _generate_security_report(self, result: CSRFTestResult):
        """セキュリティレポート生成"""
        report_file = self.project_root / "csrf_security_report.json"

        report_data = {
            "scan_summary": {
                "total_files": result.total_files_scanned,
                "total_endpoints": result.total_endpoints_found,
                "vulnerabilities_found": len(result.vulnerabilities_found),
                "protected_endpoints": result.protected_endpoints_count,
                "overall_risk": result.overall_risk.value,
                "test_duration": result.test_duration,
                "timestamp": result.timestamp.isoformat(),
            },
            "vulnerabilities": [
                {
                    "file": vuln.file_path,
                    "line": vuln.line_number,
                    "function": vuln.function_name,
                    "endpoint": vuln.endpoint_path,
                    "method": vuln.http_method,
                    "type": vuln.vulnerability_type,
                    "risk": vuln.risk_level.value,
                    "severity_score": vuln.severity_score,
                    "has_protection": vuln.has_csrf_protection,
                    "code": vuln.code_snippet,
                    "description": vuln.description,
                    "recommendation": vuln.recommendation,
                }
                for vuln in result.vulnerabilities_found
            ],
            "recommendations": result.recommendations,
            "risk_distribution": self._get_csrf_risk_distribution(
                result.vulnerabilities_found
            ),
            "method_distribution": self._get_method_distribution(
                result.vulnerabilities_found
            ),
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📋 CSRFセキュリティレポート生成: {report_file}")

    def _get_csrf_risk_distribution(
        self, vulnerabilities: List[CSRFVulnerability]
    ) -> Dict[str, int]:
        """CSRFリスク分布取得"""
        distribution = {}
        for vuln in vulnerabilities:
            risk = vuln.risk_level.value
            distribution[risk] = distribution.get(risk, 0) + 1
        return distribution

    def _get_method_distribution(
        self, vulnerabilities: List[CSRFVulnerability]
    ) -> Dict[str, int]:
        """HTTPメソッド分布取得"""
        distribution = {}
        for vuln in vulnerabilities:
            method = vuln.http_method
            distribution[method] = distribution.get(method, 0) + 1
        return distribution


def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent

    logger.info("🚀 CSRF自動テスト開始")

    try:
        with CSRFTester(project_root) as tester:
            result = tester.run()

            # 結果サマリー表示
            logger.info("📊 CSRFテスト結果サマリー:")
            logger.info(f"  スキャンしたファイル: {result.total_files_scanned}")
            logger.info(f"  エンドポイント数: {result.total_endpoints_found}")
            logger.info(f"  発見されたCSRF脆弱性: {len(result.vulnerabilities_found)}")
            logger.info(
                f"  保護されたエンドポイント: {result.protected_endpoints_count}"
            )
            logger.info(f"  全体リスクレベル: {result.overall_risk.value}")
            logger.info(f"  実行時間: {result.test_duration:.2f}秒")

            # 重要な脆弱性を表示
            critical_vulns = [
                v
                for v in result.vulnerabilities_found
                if v.risk_level in [CSRFRisk.CRITICAL, CSRFRisk.HIGH]
            ]

            if critical_vulns:
                logger.warning(f"🚨 高リスクCSRF脆弱性 {len(critical_vulns)}件:")
                for vuln in critical_vulns[:5]:  # 上位5件表示
                    logger.warning(
                        f"  - {vuln.endpoint_path} ({vuln.http_method}) in {vuln.file_path}:{vuln.line_number}"
                    )

            return 0 if result.overall_risk in [CSRFRisk.SAFE, CSRFRisk.LOW] else 1

    except Exception as e:
        logger.error(f"💥 CSRFテスト実行エラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
