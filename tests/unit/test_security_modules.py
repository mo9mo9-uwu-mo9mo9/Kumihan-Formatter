"""
セキュリティモジュールの単体テスト

分離されたセキュリティモジュール群の動作確認
- input_validator分離モジュール群
- vulnerability_scanner分離モジュール群
- audit_logger分離モジュール群
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from kumihan_formatter.core.security.validation_types import (
    ValidationSeverity, ValidationRule, ValidationResult, ValidationConfig
)
from kumihan_formatter.core.security.security_matcher import SecurityPatternMatcher
from kumihan_formatter.core.security.advanced_validator import AdvancedInputValidator
from kumihan_formatter.core.security.validator_utils import quick_validate, get_input_validator

from kumihan_formatter.core.security.vuln_types import (
    RiskLevel, VulnerabilityType, ScanResult, ScannerConfig
)
from kumihan_formatter.core.security.dependency_scanner import DependencyScanner
from kumihan_formatter.core.security.code_pattern_scanner import CodePatternScanner

from kumihan_formatter.core.logging.audit_types import EventType, ActionResult, AuditRecord
from kumihan_formatter.core.logging.hash_chain import HashChain
from kumihan_formatter.core.monitoring.health_types import HealthStatus, HealthCheckResult


class TestValidationTypes:
    """validation_types.py のテスト"""

    def test_validation_severity_enum(self):
        """ValidationSeverity列挙型のテスト"""
        assert ValidationSeverity.CRITICAL.value == "critical"
        assert ValidationSeverity.HIGH.value == "high"
        assert ValidationSeverity.MEDIUM.value == "medium"
        assert ValidationSeverity.LOW.value == "low"

    def test_validation_rule_creation(self):
        """ValidationRuleデータクラスのテスト"""
        rule = ValidationRule(
            name="test_rule",
            pattern=r"<script>",
            message="XSS detected",
            severity=ValidationSeverity.HIGH
        )
        assert rule.name == "test_rule"
        assert rule.pattern == r"<script>"
        assert rule.severity == ValidationSeverity.HIGH

    def test_validation_result_creation(self):
        """ValidationResultデータクラスのテスト"""
        from datetime import datetime, timezone
        
        result = ValidationResult(
            is_valid=False,
            violations=[{"type": "XSS", "message": "Script tag detected"}],
            risk_score=85.5,
            processing_time_ms=12.34,
            input_hash="abc123",
            validation_timestamp=datetime.now(timezone.utc)
        )
        assert not result.is_valid
        assert result.risk_score == 85.5
        assert len(result.violations) == 1

    def test_validation_config_defaults(self):
        """ValidationConfig デフォルト値のテスト"""
        config = ValidationConfig()
        assert config.enable_unicode_normalization is True
        assert config.max_input_length == 1000000
        assert config.risk_threshold == 0.7


class TestSecurityPatternMatcher:
    """security_matcher.py のテスト"""

    def test_security_pattern_matcher_initialization(self):
        """SecurityPatternMatcher 初期化テスト"""
        matcher = SecurityPatternMatcher()
        assert matcher is not None

    def test_xss_detection(self):
        """XSS攻撃パターン検出テスト"""
        matcher = SecurityPatternMatcher()
        
        # XSSパターンのテスト
        xss_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]
        
        for malicious_input in xss_inputs:
            result = matcher.match_owasp_patterns(malicious_input)
            xss_violations = [v for v in result if v['attack_type'] == 'XSS']
            assert len(xss_violations) > 0, f"XSS not detected in: {malicious_input}"

    def test_sql_injection_detection(self):
        """SQL Injection攻撃パターン検出テスト"""
        matcher = SecurityPatternMatcher()
        
        sql_inputs = [
            "'; DROP TABLE users; --",
            "UNION SELECT * FROM passwords"
        ]
        
        for malicious_input in sql_inputs:
            result = matcher.match_owasp_patterns(malicious_input)
            sql_violations = [v for v in result if v['attack_type'] == 'SQL_INJECTION']
            assert len(sql_violations) > 0, f"SQL Injection not detected in: {malicious_input}"

    def test_clean_input_no_detection(self):
        """正常入力でのfalse positive回避テスト"""
        matcher = SecurityPatternMatcher()
        clean_input = "This is a normal text input without any malicious content."
        
        result = matcher.match_owasp_patterns(clean_input)
        
        # 一般的なテキストでは攻撃パターンは検出されないはず
        assert len(result) == 0


class TestAdvancedInputValidator:
    """advanced_validator.py のテスト"""

    def test_advanced_validator_initialization(self):
        """AdvancedInputValidator 初期化テスト"""
        validator = AdvancedInputValidator()
        assert validator is not None

    def test_validate_clean_input(self):
        """正常入力の検証テスト"""
        validator = AdvancedInputValidator()
        result = validator.validate_input("Clean text input", [])
        
        assert result.is_valid
        assert result.risk_score < 20  # 低リスク
        assert len(result.violations) == 0

    def test_validate_malicious_input(self):
        """悪意ある入力の検証テスト"""
        validator = AdvancedInputValidator()
        malicious_input = "<script>alert('xss')</script>"
        
        result = validator.validate_input(malicious_input, [])
        
        assert not result.is_valid
        assert result.risk_score > 0.2  # リスクあり（0.0-1.0スケール）
        assert len(result.violations) > 0

    def test_validation_statistics(self):
        """検証統計のテスト"""
        validator = AdvancedInputValidator()
        
        # 複数の検証を実行
        validator.validate_input("clean input 1", [])
        validator.validate_input("<script>alert(1)</script>", [])
        validator.validate_input("clean input 2", [])
        
        report = validator.get_validation_report()
        assert report["total_validations"] >= 3
        assert report["risk_analysis"]["high_risk_count"] >= 0


class TestValidatorUtils:
    """validator_utils.py のテスト"""

    def test_quick_validate_function(self):
        """quick_validate 関数のテスト"""
        # 正常入力
        assert quick_validate("Normal text") is True
        
        # 悪意ある入力
        assert quick_validate("<script>alert('xss')</script>") is False
        assert quick_validate("'; DROP TABLE users; --") is False

    def test_get_input_validator_factory(self):
        """get_input_validator ファクトリ関数のテスト"""
        validator = get_input_validator()
        assert isinstance(validator, AdvancedInputValidator)

    def test_quick_validate_with_specific_attacks(self):
        """特定攻撃タイプでのquick_validateテスト"""
        result = quick_validate(
            "'; DROP TABLE users; --", 
            attack_types=["SQL_INJECTION"]
        )
        assert result is False


class TestVulnerabilityTypes:
    """vuln_types.py のテスト"""

    def test_risk_level_enum(self):
        """RiskLevel 列挙型のテスト"""
        assert RiskLevel.CRITICAL.value == "CRITICAL"
        assert RiskLevel.HIGH.value == "HIGH"
        assert RiskLevel.MEDIUM.value == "MEDIUM"

    def test_vulnerability_type_enum(self):
        """VulnerabilityType 列挙型のテスト"""
        assert VulnerabilityType.DEPENDENCY.value == "dependency"
        assert VulnerabilityType.CODE_PATTERN.value == "code_pattern"

    def test_scan_result_creation(self):
        """ScanResult データクラスのテスト"""
        result = ScanResult(
            vulnerability_type=VulnerabilityType.CODE_PATTERN,
            risk_level=RiskLevel.HIGH,
            title="Test vulnerability",
            description="Test description",
            location="test.py:10",
            recommendation="Fix the issue"
        )
        assert result.vulnerability_type == VulnerabilityType.CODE_PATTERN
        assert result.risk_level == RiskLevel.HIGH

    def test_scanner_config_defaults(self):
        """ScannerConfig デフォルト値のテスト"""
        config = ScannerConfig()
        assert config.enable_dependency_scan is True
        assert config.enable_code_pattern_scan is True
        assert config.max_file_size > 0


class TestDependencyScanner:
    """dependency_scanner.py のテスト"""

    def test_dependency_scanner_initialization(self):
        """DependencyScanner 初期化テスト"""
        config = ScannerConfig()
        logger = Mock()
        scanner = DependencyScanner(config, logger)
        assert scanner is not None

    def test_parse_requirement_line(self):
        """要求行パース機能のテスト"""
        config = ScannerConfig()
        logger = Mock()
        scanner = DependencyScanner(config, logger)
        
        # バージョン指定あり
        result = scanner._parse_requirement_line("django==4.0.0")
        assert result["name"] == "django"
        assert result["version"] == "4.0.0"
        
        # パッケージ名のみ
        result = scanner._parse_requirement_line("requests")
        assert result["name"] == "requests"

    def test_scan_nonexistent_file(self):
        """存在しないファイルのスキャンテスト"""
        config = ScannerConfig()
        logger = Mock()
        scanner = DependencyScanner(config, logger)
        
        result = scanner.scan_requirements_file(Path("nonexistent.txt"))
        assert result == []


class TestCodePatternScanner:
    """code_pattern_scanner.py のテスト"""

    def test_code_pattern_scanner_initialization(self):
        """CodePatternScanner 初期化テスト"""
        config = ScannerConfig()
        logger = Mock()
        scanner = CodePatternScanner(config, logger)
        assert scanner is not None

    def test_dangerous_functions_patterns(self):
        """危険な関数パターンのテスト"""
        scanner = CodePatternScanner(ScannerConfig(), Mock())
        
        # 定義済み危険関数の確認
        assert "eval" in scanner.DANGEROUS_FUNCTIONS
        assert "exec" in scanner.DANGEROUS_FUNCTIONS
        assert scanner.DANGEROUS_FUNCTIONS["eval"]["risk_level"] == RiskLevel.CRITICAL

    def test_security_patterns(self):
        """セキュリティパターンのテスト"""
        scanner = CodePatternScanner(ScannerConfig(), Mock())
        
        # セキュリティパターンの存在確認
        assert len(scanner.SECURITY_PATTERNS) > 0
        
        # 特定のパターン確認
        pattern_titles = [p["title"] for p in scanner.SECURITY_PATTERNS]
        assert any("command injection" in title.lower() for title in pattern_titles)


class TestAuditTypes:
    """audit_types.py のテスト"""

    def test_event_type_constants(self):
        """EventType 定数のテスト"""
        assert EventType.AUTHENTICATION == "AUTHENTICATION"
        assert EventType.SECURITY_VIOLATION == "SECURITY_VIOLATION"

    def test_action_result_constants(self):
        """ActionResult 定数のテスト"""
        assert ActionResult.SUCCESS == "SUCCESS"
        assert ActionResult.FAILURE == "FAILURE"

    def test_audit_record_creation(self):
        """AuditRecord データクラスのテスト"""
        from datetime import datetime, timezone
        
        record = AuditRecord(
            event_id="test-123",
            timestamp=datetime.now(timezone.utc),
            sequence_number=1,
            event_type=EventType.USER_ACTION,
            user_id="user123",
            source_ip="192.168.1.1",
            user_agent="TestAgent/1.0",
            resource="/api/test",
            action="test_action",
            result=ActionResult.SUCCESS,
            details={"test": "data"},
            hash_value="abc123",
            previous_hash="def456"
        )
        
        assert record.event_id == "test-123"
        assert record.event_type == EventType.USER_ACTION
        assert record.result == ActionResult.SUCCESS

    def test_audit_record_to_dict(self):
        """AuditRecord の辞書変換テスト"""
        from datetime import datetime, timezone
        
        timestamp = datetime.now(timezone.utc)
        record = AuditRecord(
            event_id="test-123",
            timestamp=timestamp,
            sequence_number=1,
            event_type=EventType.USER_ACTION,
            user_id="user123",
            source_ip="192.168.1.1",
            user_agent="TestAgent/1.0",
            resource="/api/test",
            action="test_action",
            result=ActionResult.SUCCESS,
            details={"test": "data"},
            hash_value="abc123",
            previous_hash="def456"
        )
        
        data = record.to_dict()
        assert data["event_id"] == "test-123"
        assert data["timestamp"] == timestamp.isoformat()


class TestHashChain:
    """hash_chain.py のテスト"""

    def test_hash_chain_initialization(self):
        """HashChain 初期化テスト"""
        chain = HashChain()
        assert chain.current_hash == "genesis"
        assert chain.sequence_counter == 0

    def test_hash_chain_custom_initial(self):
        """カスタム初期ハッシュのテスト"""
        chain = HashChain("custom_genesis")
        assert chain.current_hash == "custom_genesis"

    def test_add_record_sequence(self):
        """レコード追加シーケンステスト"""
        from datetime import datetime, timezone
        
        chain = HashChain()
        record = AuditRecord(
            event_id="test-1",
            timestamp=datetime.now(timezone.utc),
            sequence_number=0,
            event_type=EventType.USER_ACTION,
            user_id="user123",
            source_ip=None,
            user_agent=None,
            resource=None,
            action="test",
            result=ActionResult.SUCCESS,
            details={},
            hash_value="",
            previous_hash=""
        )
        
        hash_value = chain.add_record(record)
        
        assert record.sequence_number == 1
        assert record.previous_hash == "genesis"
        assert record.hash_value == hash_value
        assert chain.current_hash == hash_value

    def test_verify_chain_empty(self):
        """空のチェーン検証テスト"""
        chain = HashChain()
        assert chain.verify_chain([]) is True


class TestHealthTypes:
    """health_types.py のテスト"""

    def test_health_status_enum(self):
        """HealthStatus 列挙型のテスト"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.WARNING.value == "warning"
        assert HealthStatus.CRITICAL.value == "critical"
        assert HealthStatus.UNKNOWN.value == "unknown"

    def test_health_check_result_creation(self):
        """HealthCheckResult データクラスのテスト"""
        result = HealthCheckResult(
            name="disk_space",
            status=HealthStatus.WARNING,
            message="Low disk space",
            timestamp=1234567890.0,
            duration_ms=15.5,
            details={"free_percent": 15.5},
            suggestions=["Free up space", "Monitor usage"]
        )
        
        assert result.name == "disk_space"
        assert result.status == HealthStatus.WARNING
        assert len(result.suggestions) == 2


class TestModuleIntegration:
    """分離されたモジュールの統合テスト"""

    def test_input_validator_integration(self):
        """input_validator統合インターフェースのテスト"""
        from kumihan_formatter.core.security.input_validator import (
            ValidationSeverity, AdvancedInputValidator, quick_validate
        )
        
        # 統合インターフェースから正常にimportできること
        assert ValidationSeverity.HIGH.value == "high"
        assert callable(quick_validate)
        
        # 基本動作確認
        validator = AdvancedInputValidator()
        result = validator.validate_input("test", [])
        assert isinstance(result.is_valid, bool)

    def test_vulnerability_scanner_integration(self):
        """vulnerability_scanner統合インターフェースのテスト"""
        from kumihan_formatter.core.security.vulnerability_scanner import (
            RiskLevel, VulnerabilityScanner, quick_scan
        )
        
        # 統合インターフェースから正常にimportできること
        assert RiskLevel.HIGH.value == "HIGH"
        assert callable(quick_scan)
        
        # スキャナー初期化確認
        scanner = VulnerabilityScanner()
        assert scanner.config is not None

    def test_audit_logger_integration(self):
        """audit_logger統合インターフェースのテスト"""
        from kumihan_formatter.core.logging.audit_logger import (
            EventType, AuditLogger, get_audit_logger
        )
        
        # 統合インターフェースから正常にimportできること
        assert EventType.USER_ACTION == "USER_ACTION"
        assert callable(get_audit_logger)
        
        # ロガー初期化確認
        logger = get_audit_logger(log_directory=Path("tmp/test_audit"))
        assert logger is not None

    def test_health_checker_integration(self):
        """health_checker統合インターフェースのテスト"""
        from kumihan_formatter.core.monitoring.health_checker import (
            HealthStatus, HealthChecker, get_health_checker
        )
        
        # 統合インターフェースから正常にimportできること
        assert HealthStatus.HEALTHY.value == "healthy"
        assert callable(get_health_checker)
        
        # ヘルスチェッカー初期化確認
        checker = get_health_checker()
        assert checker is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])