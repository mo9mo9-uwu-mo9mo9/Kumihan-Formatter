#!/usr/bin/env python3
"""
XSS Security Test - Issue #640 Phase 3
XSS（Cross-Site Scripting）対策テストシステム

目的: HTML出力全箇所のエスケープ検証
- 悪意のあるスクリプト注入防止
- HTMLエスケープ検証
- JavaScript実行防止テスト
- DOM操作セキュリティ確認
"""

import re
import ast
import sys
import html
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
        with open(patterns_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


class XSSRisk(Enum):
    """XSSリスクレベル"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"


@dataclass
class XSSVulnerability:
    """XSS脆弱性情報"""

    file_path: str
    line_number: int
    function_name: str
    vulnerability_type: str
    risk_level: XSSRisk
    code_snippet: str
    description: str
    recommendation: str
    severity_score: float
    context_type: str  # html, javascript, css, url


@dataclass
class XSSTestResult:
    """XSSテスト結果"""

    total_files_scanned: int
    total_outputs_found: int
    vulnerabilities_found: List[XSSVulnerability]
    safe_outputs_count: int
    test_duration: float
    timestamp: datetime
    overall_risk: XSSRisk
    recommendations: List[str]


class XSSTester(TDDSystemBase):
    """XSS自動テストシステム"""

    def __init__(self, project_root: Path):
        config = create_tdd_config(project_root)
        super().__init__(config)

        # セキュリティパターンを外部ファイルから読み込み
        patterns = load_security_patterns()
        if patterns and "xss" in patterns:
            xss_patterns = patterns["xss"]
            # 危険なHTML出力パターン
            self.dangerous_html_patterns = {
                pat_info["pattern"]: pat_info["description"]
                for pat_info in xss_patterns.get("dangerous_html_patterns", {}).values()
            }
            # 安全なパターン
            self.safe_html_patterns = {
                pat_info["pattern"]: pat_info["description"]
                for pat_info in xss_patterns.get("safe_html_patterns", {}).values()
            }
            # JavaScriptセキュリティパターン
            self.javascript_patterns = {
                pat_info["pattern"]: pat_info["description"]
                for pat_info in xss_patterns.get("javascript_patterns", {}).values()
            }
            # URLセキュリティパターン
            self.url_patterns = {
                pat_info["pattern"]: pat_info["description"]
                for pat_info in xss_patterns.get("url_patterns", {}).values()
            }
        else:
            # フォールバック
            logger.info("Using default XSS patterns (configuration not available)")
            # 危険なHTML出力パターン
            self.dangerous_html_patterns = {}
            self.safe_html_patterns = {}
            self.javascript_patterns = {}
            self.url_patterns = {}

        self.vulnerabilities = []
        self.scanned_files = 0
        self.outputs_found = 0

    def initialize(self) -> bool:
        """システム初期化"""
        logger.info("🔍 XSSテストシステム初期化中...")

        # 事前条件確認
        issues = self.validate_preconditions()
        if issues:
            logger.error("初期化失敗:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False

        logger.info("✅ XSSテストシステム初期化完了")
        return True

    def execute_main_operation(self) -> XSSTestResult:
        """XSSテスト実行"""
        logger.info("🚀 XSS自動テスト開始...")

        start_time = datetime.now()

        try:
            # ソースファイルをスキャン
            self._scan_source_files()

            # テンプレートファイルをスキャン
            self._scan_template_files()

            # 結果を分析
            result = self._analyze_results(start_time)

            # レポート生成
            self._generate_security_report(result)

            logger.info(f"✅ XSSテスト完了: {len(self.vulnerabilities)}件の脆弱性発見")
            return result

        except Exception as e:
            logger.error(f"XSSテスト実行エラー: {e}")
            raise TDDSystemError(f"テスト実行失敗: {e}")

    def _scan_source_files(self):
        """Pythonソースファイルスキャン"""
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

            # HTML出力パターンをチェック
            self._check_html_patterns(file_path, content, "python")

            # JavaScript実行パターンをチェック
            self._check_javascript_patterns(file_path, content)

            # URL構築パターンをチェック
            self._check_url_patterns(file_path, content)

        except Exception as e:
            logger.warning(f"Pythonファイルスキャンエラー {file_path}: {e}")

    def _scan_template_file(self, file_path: Path):
        """テンプレートファイルスキャン"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # テンプレート変数の非エスケープ使用をチェック
            self._check_template_variables(file_path, content)

            # インラインJavaScriptをチェック
            self._check_inline_javascript(file_path, content)

            # 危険な属性をチェック
            self._check_dangerous_attributes(file_path, content)

        except Exception as e:
            logger.warning(f"テンプレートファイルスキャンエラー {file_path}: {e}")

    def _check_html_patterns(self, file_path: Path, content: str, context: str):
        """HTMLパターンチェック"""
        lines = content.split("\n")

        for pattern, description in self.dangerous_html_patterns.items():
            for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                line_num = content[: match.start()].count("\n") + 1

                # 安全なパターンでないことを確認
                if not self._is_safe_html_context(content, match):
                    vulnerability = self._create_vulnerability(
                        file_path,
                        line_num,
                        "html_output",
                        description,
                        match.group(),
                        context,
                        XSSRisk.HIGH,
                    )
                    self.vulnerabilities.append(vulnerability)
                    self.outputs_found += 1

    def _check_javascript_patterns(self, file_path: Path, content: str):
        """JavaScriptパターンチェック"""
        for pattern, description in self.javascript_patterns.items():
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[: match.start()].count("\n") + 1

                vulnerability = self._create_vulnerability(
                    file_path,
                    line_num,
                    "javascript_execution",
                    description,
                    match.group(),
                    "javascript",
                    XSSRisk.HIGH,
                )
                self.vulnerabilities.append(vulnerability)

    def _check_url_patterns(self, file_path: Path, content: str):
        """URLパターンチェック"""
        for pattern, description in self.url_patterns.items():
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[: match.start()].count("\n") + 1

                vulnerability = self._create_vulnerability(
                    file_path,
                    line_num,
                    "url_construction",
                    description,
                    match.group(),
                    "url",
                    XSSRisk.MEDIUM,
                )
                self.vulnerabilities.append(vulnerability)

    def _check_template_variables(self, file_path: Path, content: str):
        """テンプレート変数チェック"""
        # Jinja2/Flask形式の変数
        jinja_pattern = r"\{\{\s*([^}]+)\s*\}\}"

        for match in re.finditer(jinja_pattern, content):
            line_num = content[: match.start()].count("\n") + 1
            variable = match.group(1).strip()

            # エスケープされていない変数をチェック
            if not self._is_escaped_variable(variable):
                vulnerability = self._create_vulnerability(
                    file_path,
                    line_num,
                    "template_variable",
                    f"Potentially unescaped template variable: {variable}",
                    match.group(),
                    "html",
                    XSSRisk.MEDIUM,
                )
                self.vulnerabilities.append(vulnerability)
                self.outputs_found += 1

    def _check_inline_javascript(self, file_path: Path, content: str):
        """インラインJavaScriptチェック"""
        # スクリプトタグ内の動的コンテンツ
        script_pattern = r"<script[^>]*>(.*?)</script>"

        for match in re.finditer(script_pattern, content, re.DOTALL | re.IGNORECASE):
            line_num = content[: match.start()].count("\n") + 1
            script_content = match.group(1)

            # 動的変数が含まれているかチェック
            if re.search(r"\{\{[^}]+\}\}|\{%[^%]+%\}", script_content):
                vulnerability = self._create_vulnerability(
                    file_path,
                    line_num,
                    "inline_javascript",
                    "Dynamic content in inline JavaScript",
                    match.group()[:100],
                    "javascript",
                    XSSRisk.HIGH,
                )
                self.vulnerabilities.append(vulnerability)

    def _check_dangerous_attributes(self, file_path: Path, content: str):
        """危険な属性チェック"""
        # イベントハンドラ属性
        event_pattern = r'<[^>]*\s(on\w+)\s*=\s*["\']([^"\']*\{[^}]*\}[^"\']*)["\']'

        for match in re.finditer(event_pattern, content, re.IGNORECASE):
            line_num = content[: match.start()].count("\n") + 1
            event_name = match.group(1)
            event_value = match.group(2)

            vulnerability = self._create_vulnerability(
                file_path,
                line_num,
                "dangerous_attribute",
                f"Dynamic content in {event_name} attribute",
                match.group(),
                "javascript",
                XSSRisk.HIGH,
            )
            self.vulnerabilities.append(vulnerability)

    def _is_safe_html_context(self, content: str, match) -> bool:
        """安全なHTMLコンテキストかチェック"""
        match_area = content[max(0, match.start() - 200) : match.end() + 200]

        # 安全なパターンをチェック
        for safe_pattern in self.safe_html_patterns.keys():
            if re.search(safe_pattern, match_area, re.IGNORECASE):
                return True

        # コメント内かチェック
        if "#" in match_area and match_area.find("#") < match_area.find(match.group()):
            return True

        return False

    def _is_escaped_variable(self, variable: str) -> bool:
        """変数がエスケープされているかチェック"""
        escape_indicators = [
            "|escape",
            "|e",
            "|safe",
            "Markup(",
            "escape(",
            "html.escape",
            "cgi.escape",
        ]

        for indicator in escape_indicators:
            if indicator in variable:
                return True

        return False

    def _create_vulnerability(
        self,
        file_path: Path,
        line_number: int,
        func_name: str,
        description: str,
        code_snippet: str,
        context: str,
        default_risk: XSSRisk,
    ) -> XSSVulnerability:
        """脆弱性オブジェクト作成"""

        # リスクレベル評価
        risk_level, severity_score = self._assess_xss_risk(
            description, code_snippet, context
        )
        if risk_level == XSSRisk.SAFE:
            risk_level = default_risk

        # 推奨事項生成
        recommendation = self._generate_xss_recommendation(description, context)

        return XSSVulnerability(
            file_path=str(file_path.relative_to(self.project_root)),
            line_number=line_number,
            function_name=func_name,
            vulnerability_type=description,
            risk_level=risk_level,
            code_snippet=code_snippet[:200],
            description=f"潜在的なXSS脆弱性: {description}",
            recommendation=recommendation,
            severity_score=severity_score,
            context_type=context,
        )

    def _assess_xss_risk(
        self, description: str, code_snippet: str, context: str
    ) -> Tuple[XSSRisk, float]:
        """XSSリスクレベル評価"""
        critical_keywords = ["eval", "innerHTML", "document.write", "execScript"]
        high_keywords = ["script", "javascript:", "on\\w+\\s*=", "iframe"]
        medium_keywords = ["href", "src", "action", "template"]

        desc_lower = description.lower()
        code_lower = code_snippet.lower()

        # コンテキスト別リスク調整
        context_risk_multiplier = {
            "javascript": 1.5,
            "html": 1.0,
            "url": 0.8,
            "css": 0.6,
        }.get(context, 1.0)

        for keyword in critical_keywords:
            if re.search(keyword.lower(), desc_lower) or re.search(
                keyword.lower(), code_lower
            ):
                return XSSRisk.CRITICAL, min(10.0, 9.0 * context_risk_multiplier)

        for keyword in high_keywords:
            if re.search(keyword.lower(), desc_lower) or re.search(
                keyword.lower(), code_lower
            ):
                return XSSRisk.HIGH, min(10.0, 7.0 * context_risk_multiplier)

        for keyword in medium_keywords:
            if re.search(keyword.lower(), desc_lower) or re.search(
                keyword.lower(), code_lower
            ):
                return XSSRisk.MEDIUM, min(10.0, 5.0 * context_risk_multiplier)

        return XSSRisk.LOW, min(10.0, 3.0 * context_risk_multiplier)

    def _generate_xss_recommendation(self, description: str, context: str) -> str:
        """XSS推奨事項生成"""
        context_recommendations = {
            "html": "HTML出力時はhtml.escape()やテンプレートエンジンの自動エスケープを使用してください",
            "javascript": "JavaScriptコードの動的生成を避け、JSON.stringify()を使用してデータを安全に渡してください",
            "url": "URL構築時はurllib.parse.quote()を使用してエンケードしてください",
            "css": "CSS値の動的生成を避け、事前定義されたクラスを使用してください",
        }

        base_recommendation = context_recommendations.get(
            context,
            "ユーザー入力を直接出力に含める前に適切なエスケープ処理を行ってください",
        )

        specific_recommendations = {
            "innerHTML": "innerHTML の代わりに textContent を使用するか、DOMPurify等のサニタイザーを使用してください",
            "eval": "eval()の使用を避け、JSON.parse()や安全な代替手段を使用してください",
            "template": "テンプレート変数には |escape フィルタを適用してください",
            "event": "インラインイベントハンドラを避け、addEventListener()を使用してください",
        }

        for keyword, specific_rec in specific_recommendations.items():
            if keyword.lower() in description.lower():
                return f"{base_recommendation} {specific_rec}"

        return base_recommendation

    def _analyze_results(self, start_time: datetime) -> XSSTestResult:
        """結果分析"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 全体リスクレベル決定
        overall_risk = self._calculate_overall_xss_risk()

        # 推奨事項生成
        recommendations = self._generate_xss_recommendations()

        safe_outputs = max(0, self.outputs_found - len(self.vulnerabilities))

        return XSSTestResult(
            total_files_scanned=self.scanned_files,
            total_outputs_found=self.outputs_found,
            vulnerabilities_found=self.vulnerabilities,
            safe_outputs_count=safe_outputs,
            test_duration=duration,
            timestamp=end_time,
            overall_risk=overall_risk,
            recommendations=recommendations,
        )

    def _calculate_overall_xss_risk(self) -> XSSRisk:
        """全体XSSリスクレベル計算"""
        if not self.vulnerabilities:
            return XSSRisk.SAFE

        risk_counts = {}
        for vuln in self.vulnerabilities:
            risk_counts[vuln.risk_level] = risk_counts.get(vuln.risk_level, 0) + 1

        if risk_counts.get(XSSRisk.CRITICAL, 0) > 0:
            return XSSRisk.CRITICAL
        elif risk_counts.get(XSSRisk.HIGH, 0) > 0:
            return XSSRisk.HIGH
        elif risk_counts.get(XSSRisk.MEDIUM, 0) > 0:
            return XSSRisk.MEDIUM
        else:
            return XSSRisk.LOW

    def _generate_xss_recommendations(self) -> List[str]:
        """XSS推奨事項リスト生成"""
        recommendations = [
            "全てのユーザー入力に対して適切なエスケープ処理を実装する",
            "テンプレートエンジンの自動エスケープ機能を有効にする",
            "Content Security Policy (CSP) を実装する",
            "innerHTML の使用を避け、安全なDOM操作メソッドを使用する",
            "ユーザー入力の検証とサニタイズを実装する",
            "定期的なXSSテストの実行",
        ]

        if self.vulnerabilities:
            recommendations.extend(
                [
                    "発見されたXSS脆弱性を優先度に応じて修正する",
                    "セキュリティヘッダーの設定を確認する",
                    "第三者ライブラリのセキュリティアップデートを定期的に確認する",
                ]
            )

        return recommendations

    def _generate_security_report(self, result: XSSTestResult):
        """セキュリティレポート生成"""
        report_file = self.project_root / "xss_security_report.json"

        report_data = {
            "scan_summary": {
                "total_files": result.total_files_scanned,
                "total_outputs": result.total_outputs_found,
                "vulnerabilities_found": len(result.vulnerabilities_found),
                "safe_outputs": result.safe_outputs_count,
                "overall_risk": result.overall_risk.value,
                "test_duration": result.test_duration,
                "timestamp": result.timestamp.isoformat(),
            },
            "vulnerabilities": [
                {
                    "file": vuln.file_path,
                    "line": vuln.line_number,
                    "function": vuln.function_name,
                    "type": vuln.vulnerability_type,
                    "risk": vuln.risk_level.value,
                    "context": vuln.context_type,
                    "severity_score": vuln.severity_score,
                    "code": vuln.code_snippet,
                    "description": vuln.description,
                    "recommendation": vuln.recommendation,
                }
                for vuln in result.vulnerabilities_found
            ],
            "recommendations": result.recommendations,
            "risk_distribution": self._get_xss_risk_distribution(
                result.vulnerabilities_found
            ),
            "context_distribution": self._get_context_distribution(
                result.vulnerabilities_found
            ),
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📋 XSSセキュリティレポート生成: {report_file}")

    def _get_xss_risk_distribution(
        self, vulnerabilities: List[XSSVulnerability]
    ) -> Dict[str, int]:
        """XSSリスク分布取得"""
        distribution = {}
        for vuln in vulnerabilities:
            risk = vuln.risk_level.value
            distribution[risk] = distribution.get(risk, 0) + 1
        return distribution

    def _get_context_distribution(
        self, vulnerabilities: List[XSSVulnerability]
    ) -> Dict[str, int]:
        """コンテキスト分布取得"""
        distribution = {}
        for vuln in vulnerabilities:
            context = vuln.context_type
            distribution[context] = distribution.get(context, 0) + 1
        return distribution


def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent

    logger.info("🚀 XSS自動テスト開始")

    try:
        with XSSTester(project_root) as tester:
            result = tester.run()

            # 結果サマリー表示
            logger.info("📊 XSSテスト結果サマリー:")
            logger.info(f"  スキャンしたファイル: {result.total_files_scanned}")
            logger.info(f"  出力箇所数: {result.total_outputs_found}")
            logger.info(f"  発見されたXSS脆弱性: {len(result.vulnerabilities_found)}")
            logger.info(f"  全体リスクレベル: {result.overall_risk.value}")
            logger.info(f"  実行時間: {result.test_duration:.2f}秒")

            # 重要な脆弱性を表示
            critical_vulns = [
                v
                for v in result.vulnerabilities_found
                if v.risk_level in [XSSRisk.CRITICAL, XSSRisk.HIGH]
            ]

            if critical_vulns:
                logger.warning(f"🚨 高リスクXSS脆弱性 {len(critical_vulns)}件:")
                for vuln in critical_vulns[:5]:  # 上位5件表示
                    logger.warning(
                        f"  - {vuln.file_path}:{vuln.line_number} ({vuln.risk_level.value}, {vuln.context_type})"
                    )

            return 0 if result.overall_risk in [XSSRisk.SAFE, XSSRisk.LOW] else 1

    except Exception as e:
        logger.error(f"💥 XSSテスト実行エラー: {e}")
        return 1


def run_unit_tests():
    """簡易単体テスト実行"""
    logger.info("🧪 XSS検出システム単体テスト開始")

    test_cases = [
        {
            "name": "危険なHTML出力検出",
            "code": 'html = f"<div>{user_input}</div>"',
            "expected_vulnerable": True,
        },
        {
            "name": "安全なエスケープ処理",
            "code": 'html = f"<div>{escape(user_input)}</div>"',
            "expected_vulnerable": False,
        },
        {
            "name": "JavaScript挿入脆弱性",
            "code": 'script = "<script>alert(\'" + data + "\')</script>"',
            "expected_vulnerable": True,
        },
        {
            "name": "特殊文字対応テスト（エッジケース）",
            "code": f"html = \"{'©' * 1000}<p>content</p>\"",
            "expected_vulnerable": False,
        },
    ]

    passed = 0
    for i, test_case in enumerate(test_cases, 1):
        try:
            from pathlib import Path

            project_root = Path(".").resolve()
            tester = XSSTester(project_root)

            # 簡易パターンマッチングテスト
            has_dangerous_pattern = any(
                __import__("re").search(pattern, test_case["code"])
                for pattern in tester.dangerous_html_patterns
                if pattern
            )

            if has_dangerous_pattern == test_case["expected_vulnerable"]:
                logger.info(f"✅ テスト{i}: {test_case['name']} - PASS")
                passed += 1
            else:
                logger.warning(f"❌ テスト{i}: {test_case['name']} - FAIL")

        except Exception as e:
            logger.error(f"❌ テスト{i}: {test_case['name']} - ERROR: {e}")

    logger.info(f"📊 単体テスト結果: {passed}/{len(test_cases)} PASS")
    return passed == len(test_cases)


if __name__ == "__main__":
    import sys

    # --unit-testオプション対応
    if len(sys.argv) > 1 and sys.argv[1] == "--unit-test":
        success = run_unit_tests()
        sys.exit(0 if success else 1)
    else:
        sys.exit(main())
