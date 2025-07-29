#!/usr/bin/env python3
"""
File Upload Security Test - Issue #640 Phase 3
ファイルアップロードセキュリティテストシステム

目的: 悪意のあるファイルアップロード対策テスト
- 悪意のあるファイル検出
- アップロード制限検証
- ファイルタイプ偽装検出
- サイズ制限テスト
"""

import re
import os
import sys
import mimetypes
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import tempfile
import subprocess

from scripts.tdd_system_base import TDDSystemBase, create_tdd_config, TDDSystemError
from scripts.secure_subprocess import secure_run
from scripts.security_utils import (
    load_security_config,
    calculate_statistical_confidence,
    should_scan_file,
    get_required_validations,
)
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class FileUploadRisk(Enum):
    """ファイルアップロードリスクレベル"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"


@dataclass
class FileUploadVulnerability:
    """ファイルアップロード脆弱性情報"""

    file_path: str
    line_number: int
    function_name: str
    vulnerability_type: str
    risk_level: FileUploadRisk
    code_snippet: str
    description: str
    recommendation: str
    severity_score: float
    dangerous_extensions: List[str]
    missing_validations: List[str]


@dataclass
class FileUploadTestResult:
    """ファイルアップロードテスト結果"""

    total_files_scanned: int
    total_upload_handlers_found: int
    vulnerabilities_found: List[FileUploadVulnerability]
    secure_handlers_count: int
    test_duration: float
    timestamp: datetime
    overall_risk: FileUploadRisk
    recommendations: List[str]
    malicious_file_tests: Dict[str, bool]


class FileUploadTester(TDDSystemBase):
    """ファイルアップロード自動テストシステム"""

    def __init__(self, project_root: Path):
        config = create_tdd_config(project_root)
        super().__init__(config)

        # セキュリティ設定を外部から読み込み
        security_config = load_security_config()

        patterns_file = Path(__file__).parent / "security_patterns.json"
        if patterns_file.exists():
            with open(patterns_file, "r", encoding="utf-8") as f:
                import json

                patterns = json.load(f)
                file_upload_patterns = patterns.get("file_upload", {})

                # 危険なファイル拡張子
                self.dangerous_extensions = set(
                    file_upload_patterns.get("dangerous_extensions", [])
                )

                # ファイルアップロード処理パターン
                self.upload_handler_patterns = {
                    pat_info["pattern"]: pat_info["description"]
                    for pat_info in file_upload_patterns.get(
                        "upload_handler_patterns", {}
                    ).values()
                }

                # セキュリティ検証パターン
                self.security_validation_patterns = {
                    pat_info["pattern"]: pat_info["description"]
                    for pat_info in file_upload_patterns.get(
                        "security_validation_patterns", {}
                    ).values()
                }

                # 悪意のあるファイルパターン
                self.malicious_file_patterns = {
                    pat_info["pattern"]: pat_info["description"]
                    for pat_info in file_upload_patterns.get(
                        "malicious_file_patterns", {}
                    ).values()
                }
        else:
            logger.warning("セキュリティパターン設定ファイルが見つかりません")
            self.dangerous_extensions = set()
            self.upload_handler_patterns = {}
            self.security_validation_patterns = {}
            self.malicious_file_patterns = {}

        # ファイルサイズ制限
        self.max_file_size = security_config.get("file_upload", {}).get(
            "max_file_size", 5242880
        )

        self.vulnerabilities = []
        self.scanned_files = 0
        self.upload_handlers_found = 0
        self.malicious_test_results = {}

    def initialize(self) -> bool:
        """システム初期化"""
        logger.info("🔍 ファイルアップロードテストシステム初期化中...")

        # 事前条件確認
        issues = self.validate_preconditions()
        if issues:
            logger.error("初期化失敗:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False

        logger.info("✅ ファイルアップロードテストシステム初期化完了")
        return True

    def execute_main_operation(self) -> FileUploadTestResult:
        """ファイルアップロードテスト実行"""
        logger.info("🚀 ファイルアップロード自動テスト開始...")

        start_time = datetime.now()

        try:
            # ソースファイルをスキャン
            self._scan_source_files()

            # 悪意のあるファイルテスト実行
            self._run_malicious_file_tests()

            # 結果を分析
            result = self._analyze_results(start_time)

            # レポート生成
            self._generate_security_report(result)

            logger.info(
                f"✅ ファイルアップロードテスト完了: {len(self.vulnerabilities)}件の脆弱性発見"
            )
            return result

        except Exception as e:
            logger.error(f"ファイルアップロードテスト実行エラー: {e}")
            raise TDDSystemError(f"テスト実行失敗: {e}")

    def _scan_source_files(self):
        """Pythonソースファイルスキャン"""
        logger.info("📁 Pythonファイルスキャン開始...")

        for py_file in self.project_root.glob("**/*.py"):
            if self._should_scan_file(py_file):
                self._scan_python_file(py_file)
                self.scanned_files += 1

    def _should_scan_file(self, file_path: Path) -> bool:
        """ファイルをスキャンすべきかチェック"""
        return should_scan_file(file_path)

    def _scan_python_file(self, file_path: Path):
        """Pythonファイルスキャン"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # ファイルアップロードハンドラーを検出
            self._detect_upload_handlers(file_path, content)

        except Exception as e:
            logger.warning(f"Pythonファイルスキャンエラー {file_path}: {e}")

    def _detect_upload_handlers(self, file_path: Path, content: str):
        """ファイルアップロードハンドラー検出"""
        lines = content.split("\n")

        for pattern, description in self.upload_handler_patterns.items():
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[: match.start()].count("\n") + 1
                self.upload_handlers_found += 1

                # この処理の周辺コードを取得
                context_start = max(0, line_num - 10)
                context_end = min(len(lines), line_num + 10)
                context_lines = lines[context_start:context_end]
                context = "\n".join(context_lines)

                # セキュリティ検証の有無をチェック
                security_checks = self._analyze_security_validations(context)

                # 脆弱性評価
                if security_checks["missing_validations"]:
                    vulnerability = self._create_upload_vulnerability(
                        file_path,
                        line_num,
                        "file_upload_handler",
                        description,
                        match.group(),
                        security_checks,
                    )
                    self.vulnerabilities.append(vulnerability)

    def _analyze_security_validations(self, context: str) -> Dict:
        """セキュリティ検証分析"""
        found_validations = []
        missing_validations = []

        # 実装されている検証をチェック
        for pattern, validation_type in self.security_validation_patterns.items():
            if re.search(pattern, context, re.IGNORECASE):
                found_validations.append(validation_type)

        # 必須検証項目を外部設定から取得
        required_validations = get_required_validations("file_upload")

        # 不足している検証を特定
        for required in required_validations:
            if not any(
                required.lower() in found.lower() for found in found_validations
            ):
                missing_validations.append(required)

        # 危険な拡張子許可チェック
        dangerous_extensions_allowed = []
        for ext in self.dangerous_extensions:
            if ext in context.lower():
                dangerous_extensions_allowed.append(ext)

        # 悪意のあるファイル名パターンチェック
        malicious_patterns_found = []
        for pattern, description in self.malicious_file_patterns.items():
            if re.search(pattern, context, re.IGNORECASE):
                malicious_patterns_found.append(description)

        return {
            "found_validations": found_validations,
            "missing_validations": missing_validations,
            "dangerous_extensions_allowed": dangerous_extensions_allowed,
            "malicious_patterns_found": malicious_patterns_found,
            "has_path_traversal_protection": '".." not in' in context
            or "secure_filename" in context,
            "has_size_limit": any("size" in v.lower() for v in found_validations),
            "has_mime_validation": any("mime" in v.lower() for v in found_validations),
        }

    def _run_malicious_file_tests(self):
        """悪意のあるファイルテスト実行"""
        logger.info("🔍 悪意のあるファイルテスト実行中...")

        # テスト用の悪意のあるファイルパターン
        malicious_tests = {
            "executable_disguised_as_image": {
                "filename": "innocent.jpg.exe",
                "content": b"MZ\x90\x00",  # PE header
                "expected_blocked": True,
            },
            "script_in_filename": {
                "filename": '<script>alert("xss")</script>.txt',
                "content": b"normal content",
                "expected_blocked": True,
            },
            "path_traversal": {
                "filename": "../../../etc/passwd",
                "content": b"malicious content",
                "expected_blocked": True,
            },
            "double_extension": {
                "filename": "document.pdf.exe",
                "content": b"%PDF-1.4 fake pdf header",
                "expected_blocked": True,
            },
            "null_byte_injection": {
                "filename": "safe.txt\x00.exe",
                "content": b"seemingly safe",
                "expected_blocked": True,
            },
            "oversized_file": {
                "filename": "huge.txt",
                "content": b"A" * (10 * 1024 * 1024),  # 10MB
                "expected_blocked": True,
            },
        }

        for test_name, test_data in malicious_tests.items():
            try:
                result = self._test_malicious_file(test_name, test_data)
                self.malicious_test_results[test_name] = result
                logger.debug(
                    f"悪意ファイルテスト {test_name}: {'PASS' if result else 'FAIL'}"
                )
            except Exception as e:
                logger.warning(f"悪意ファイルテスト {test_name} エラー: {e}")
                self.malicious_test_results[test_name] = False

    def _test_malicious_file(self, test_name: str, test_data: Dict) -> bool:
        """個別悪意ファイルテスト"""
        # 一時ファイル作成
        with tempfile.NamedTemporaryFile(delete=False, suffix=".test") as temp_file:
            temp_file.write(test_data["content"])
            temp_path = Path(temp_file.name)

        try:
            # ファイル検証テスト（模擬）
            validation_result = self._simulate_file_validation(
                test_data["filename"], temp_path, test_data["content"]
            )

            # テスト結果評価
            if test_data["expected_blocked"]:
                return validation_result["blocked"]
            else:
                return not validation_result["blocked"]

        finally:
            # 一時ファイル削除
            temp_path.unlink(missing_ok=True)

    def _simulate_file_validation(
        self, filename: str, file_path: Path, content: bytes
    ) -> Dict:
        """ファイル検証シミュレーション"""
        blocked_reasons = []

        # 拡張子チェック
        file_ext = Path(filename).suffix.lower()
        if file_ext in self.dangerous_extensions:
            blocked_reasons.append(f"Dangerous extension: {file_ext}")

        # ファイル名検証
        for pattern, description in self.malicious_file_patterns.items():
            if re.search(pattern, filename):
                blocked_reasons.append(f"Malicious filename pattern: {description}")

        # MIMEタイプチェック（簡易）
        guessed_type, _ = mimetypes.guess_type(filename)
        if content.startswith(b"MZ"):  # PE executable
            if guessed_type != "application/octet-stream":
                blocked_reasons.append("MIME type mismatch: executable disguised")

        # サイズチェック
        if len(content) > self.max_file_size:
            blocked_reasons.append(
                f"File too large: {len(content)} bytes > {self.max_file_size}"
            )

        # パストラバーサルチェック
        if ".." in filename or filename.startswith("/"):
            blocked_reasons.append("Path traversal attempt detected")

        return {
            "blocked": len(blocked_reasons) > 0,
            "reasons": blocked_reasons,
            "filename": filename,
            "size": len(content),
            "detected_type": guessed_type,
        }

    def _create_upload_vulnerability(
        self,
        file_path: Path,
        line_number: int,
        func_name: str,
        description: str,
        code_snippet: str,
        security_analysis: Dict,
    ) -> FileUploadVulnerability:
        """ファイルアップロード脆弱性オブジェクト作成"""

        # リスクレベル評価
        risk_level, severity_score = self._assess_upload_risk(security_analysis)

        # 推奨事項生成
        recommendation = self._generate_upload_recommendation(security_analysis)

        return FileUploadVulnerability(
            file_path=str(file_path.relative_to(self.project_root)),
            line_number=line_number,
            function_name=func_name,
            vulnerability_type=description,
            risk_level=risk_level,
            code_snippet=code_snippet[:200],
            description=f"ファイルアップロード脆弱性: {description}",
            recommendation=recommendation,
            severity_score=severity_score,
            dangerous_extensions=security_analysis.get(
                "dangerous_extensions_allowed", []
            ),
            missing_validations=security_analysis.get("missing_validations", []),
        )

    def _assess_upload_risk(
        self, security_analysis: Dict
    ) -> Tuple[FileUploadRisk, float]:
        """ファイルアップロードリスクレベル評価"""
        base_score = 0.0
        missing = security_analysis.get("missing_validations", [])
        dangerous_ext = security_analysis.get("dangerous_extensions_allowed", [])

        # 必須検証不足によるリスク
        if "File extension validation" in missing:
            base_score += 3.0
        if "MIME type validation" in missing:
            base_score += 2.5
        if "File size check" in missing:
            base_score += 2.0
        if "Secure filename function" in missing:
            base_score += 2.5

        # 危険な拡張子許可によるリスク
        if dangerous_ext:
            base_score += len(dangerous_ext) * 1.0

        # パストラバーサル保護なし
        if not security_analysis.get("has_path_traversal_protection", False):
            base_score += 2.0

        # 悪意のあるパターン発見
        if security_analysis.get("malicious_patterns_found"):
            base_score += 3.0

        # リスクレベル決定
        if base_score >= 8.0:
            return FileUploadRisk.CRITICAL, min(10.0, base_score)
        elif base_score >= 6.0:
            return FileUploadRisk.HIGH, base_score
        elif base_score >= 4.0:
            return FileUploadRisk.MEDIUM, base_score
        elif base_score >= 2.0:
            return FileUploadRisk.LOW, base_score
        else:
            return FileUploadRisk.SAFE, base_score

    def _generate_upload_recommendation(self, security_analysis: Dict) -> str:
        """ファイルアップロード推奨事項生成"""
        recommendations = []

        missing = security_analysis.get("missing_validations", [])

        if "File extension validation" in missing:
            recommendations.append("許可する拡張子のホワイトリストを実装してください")

        if "MIME type validation" in missing:
            recommendations.append(
                "MIMEタイプ検証とファイルマジックナンバーチェックを追加してください"
            )

        if "File size check" in missing:
            recommendations.append("ファイルサイズ制限を実装してください")

        if "Secure filename function" in missing:
            recommendations.append(
                "secure_filename()等を使用してファイル名をサニタイズしてください"
            )

        if not security_analysis.get("has_path_traversal_protection", False):
            recommendations.append("パストラバーサル攻撃対策を実装してください")

        base_recommendation = (
            "ファイルアップロード処理にセキュリティ検証を追加してください。"
        )

        if recommendations:
            return base_recommendation + " 具体的には: " + "、".join(recommendations)
        else:
            return base_recommendation

    def _analyze_results(self, start_time: datetime) -> FileUploadTestResult:
        """結果分析"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 全体リスクレベル決定
        overall_risk = self._calculate_overall_upload_risk()

        # 推奨事項生成
        recommendations = self._generate_upload_recommendations()

        secure_handlers = max(0, self.upload_handlers_found - len(self.vulnerabilities))

        return FileUploadTestResult(
            total_files_scanned=self.scanned_files,
            total_upload_handlers_found=self.upload_handlers_found,
            vulnerabilities_found=self.vulnerabilities,
            secure_handlers_count=secure_handlers,
            test_duration=duration,
            timestamp=end_time,
            overall_risk=overall_risk,
            recommendations=recommendations,
            malicious_file_tests=self.malicious_test_results,
        )

    def _calculate_overall_upload_risk(self) -> FileUploadRisk:
        """全体ファイルアップロードリスクレベル計算"""
        if not self.vulnerabilities:
            return FileUploadRisk.SAFE

        risk_counts = {}
        for vuln in self.vulnerabilities:
            risk_counts[vuln.risk_level] = risk_counts.get(vuln.risk_level, 0) + 1

        if risk_counts.get(FileUploadRisk.CRITICAL, 0) > 0:
            return FileUploadRisk.CRITICAL
        elif risk_counts.get(FileUploadRisk.HIGH, 0) > 0:
            return FileUploadRisk.HIGH
        elif risk_counts.get(FileUploadRisk.MEDIUM, 0) > 0:
            return FileUploadRisk.MEDIUM
        else:
            return FileUploadRisk.LOW

    def _generate_upload_recommendations(self) -> List[str]:
        """ファイルアップロード推奨事項リスト生成"""
        recommendations = [
            "すべてのファイルアップロードに拡張子ホワイトリストを実装する",
            "MIMEタイプ検証とファイルマジックナンバーチェックを追加する",
            "ファイルサイズ制限を設定する",
            "secure_filename()を使用してファイル名をサニタイズする",
            "アップロードファイルを実行可能ディレクトリ外に保存する",
            "ウイルススキャン機能の統合を検討する",
            "定期的なファイルアップロードセキュリティテストの実行",
        ]

        if self.vulnerabilities:
            recommendations.extend(
                [
                    "発見されたファイルアップロード脆弱性を優先度に応じて修正する",
                    "Content Security Policy (CSP) の設定を確認する",
                    "アップロードファイルの隔離とサンドボックス実行を検討する",
                ]
            )

        return recommendations

    def _generate_security_report(self, result: FileUploadTestResult):
        """セキュリティレポート生成"""
        report_file = self.project_root / "file_upload_security_report.json"

        report_data = {
            "scan_summary": {
                "total_files": result.total_files_scanned,
                "total_upload_handlers": result.total_upload_handlers_found,
                "vulnerabilities_found": len(result.vulnerabilities_found),
                "secure_handlers": result.secure_handlers_count,
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
                    "severity_score": vuln.severity_score,
                    "dangerous_extensions": vuln.dangerous_extensions,
                    "missing_validations": vuln.missing_validations,
                    "code": vuln.code_snippet,
                    "description": vuln.description,
                    "recommendation": vuln.recommendation,
                }
                for vuln in result.vulnerabilities_found
            ],
            "malicious_file_tests": {
                "results": result.malicious_file_tests,
                "passed_tests": sum(
                    1 for passed in result.malicious_file_tests.values() if passed
                ),
                "total_tests": len(result.malicious_file_tests),
            },
            "recommendations": result.recommendations,
            "risk_distribution": self._get_upload_risk_distribution(
                result.vulnerabilities_found
            ),
            "validation_distribution": self._get_validation_distribution(
                result.vulnerabilities_found
            ),
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📋 ファイルアップロードセキュリティレポート生成: {report_file}")

    def _get_upload_risk_distribution(
        self, vulnerabilities: List[FileUploadVulnerability]
    ) -> Dict[str, int]:
        """ファイルアップロードリスク分布取得"""
        distribution = {}
        for vuln in vulnerabilities:
            risk = vuln.risk_level.value
            distribution[risk] = distribution.get(risk, 0) + 1
        return distribution

    def _get_validation_distribution(
        self, vulnerabilities: List[FileUploadVulnerability]
    ) -> Dict[str, int]:
        """検証不足分布取得"""
        distribution = {}
        for vuln in vulnerabilities:
            for missing in vuln.missing_validations:
                distribution[missing] = distribution.get(missing, 0) + 1
        return distribution


def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent

    logger.info("🚀 ファイルアップロード自動テスト開始")

    try:
        with FileUploadTester(project_root) as tester:
            result = tester.run()

            # 結果サマリー表示
            logger.info("📊 ファイルアップロードテスト結果サマリー:")
            logger.info(f"  スキャンしたファイル: {result.total_files_scanned}")
            logger.info(
                f"  アップロードハンドラー数: {result.total_upload_handlers_found}"
            )
            logger.info(f"  発見された脆弱性: {len(result.vulnerabilities_found)}")
            logger.info(f"  セキュアなハンドラー: {result.secure_handlers_count}")
            logger.info(f"  全体リスクレベル: {result.overall_risk.value}")
            logger.info(
                f"  悪意ファイルテスト: {sum(result.malicious_file_tests.values())}/{len(result.malicious_file_tests)} passed"
            )
            logger.info(f"  実行時間: {result.test_duration:.2f}秒")

            # 重要な脆弱性を表示
            critical_vulns = [
                v
                for v in result.vulnerabilities_found
                if v.risk_level in [FileUploadRisk.CRITICAL, FileUploadRisk.HIGH]
            ]

            if critical_vulns:
                logger.warning(
                    f"🚨 高リスクファイルアップロード脆弱性 {len(critical_vulns)}件:"
                )
                for vuln in critical_vulns[:5]:  # 上位5件表示
                    logger.warning(
                        f"  - {vuln.file_path}:{vuln.line_number} ({vuln.risk_level.value})"
                    )
                    logger.warning(
                        f"    不足検証: {', '.join(vuln.missing_validations)}"
                    )

            return (
                0
                if result.overall_risk in [FileUploadRisk.SAFE, FileUploadRisk.LOW]
                else 1
            )

    except Exception as e:
        logger.error(f"💥 ファイルアップロードテスト実行エラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
