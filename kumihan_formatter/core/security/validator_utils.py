"""
入力検証システム - ユーティリティ関数

入力検証に関連するユーティリティ関数とエイリアス
input_validator.pyから分離（Issue: 巨大ファイル分割 - 1017行→100行程度）
"""

from typing import Any, List, Optional

from .advanced_validator import AdvancedInputValidator
from .validation_types import ValidationConfig, ValidationRule, ValidationSeverity


# 後方互換性エイリアス
SecureInputValidator = AdvancedInputValidator


def get_input_validator(
    config: Optional[ValidationConfig] = None,
) -> AdvancedInputValidator:
    """入力検証器のファクトリー関数"""
    return AdvancedInputValidator(config=config)


def quick_validate(input_data: Any, attack_types: Optional[List[str]] = None) -> bool:
    """クイック検証（シンプルAPI）"""
    validator = AdvancedInputValidator()
    
    if attack_types is None:
        attack_types = ["SQL_INJECTION", "XSS", "COMMAND_INJECTION"]
    
    # 基本的な攻撃パターンのみをチェック
    rules = []
    if "SQL_INJECTION" in attack_types:
        rules.append(
            ValidationRule(
                name="quick_sql_check",
                pattern=r"(?i)(union\s+select|drop\s+table|insert\s+into)",
                message="SQL injection detected",
                severity=ValidationSeverity.CRITICAL,
            )
        )
    
    if "XSS" in attack_types:
        rules.append(
            ValidationRule(
                name="quick_xss_check",
                pattern=r"<script|javascript:",
                message="XSS attack detected",
                severity=ValidationSeverity.HIGH,
            )
        )
    
    if "COMMAND_INJECTION" in attack_types:
        rules.append(
            ValidationRule(
                name="quick_cmd_check",
                pattern=r"[;&|`]",
                message="Command injection detected",
                severity=ValidationSeverity.CRITICAL,
            )
        )
    
    result = validator.validate_input(input_data, rules)
    return result.is_valid


def _demo_advanced_validator() -> None:
    """高度入力検証システムのデモ（開発・テスト用）"""
    print("=== Advanced Input Validator Demo ===")
    
    validator = AdvancedInputValidator()
    
    # テストケース
    test_cases = [
        ("SELECT * FROM users", "SQL Injection"),
        ("<script>alert('xss')</script>", "XSS Attack"),
        ("../../etc/passwd", "Path Traversal"),
        ("https://localhost/admin", "SSRF"),
        ("normal input text", "Clean Input"),
    ]
    
    for test_input, description in test_cases:
        print(f"\n--- Testing: {description} ---")
        print(f"Input: {test_input}")
        
        result = validator.validate_input(test_input, [])
        print(f"Valid: {result.is_valid}")
        print(f"Risk Score: {result.risk_score:.2f}")
        print(f"Processing Time: {result.processing_time_ms:.2f}ms")
        
        if result.violations:
            print("Violations:")
            for violation in result.violations:
                print(
                    f"  - {violation['attack_type']}: {violation.get('message', 'N/A')}"
                )
    
    # 統計レポート
    print("\n--- Validation Statistics ---")
    report = validator.get_validation_report()
    print(f"Total Validations: {report['total_validations']}")
    print(
        f"Average Processing Time: "
        f"{report['performance']['avg_processing_time_ms']:.2f}ms"
    )
    
    # レポート出力
    validator.export_validation_report("demo_validation_report.json")
    print(
        "Detailed report exported to tmp/validation_reports/demo_validation_report.json"
    )


__all__ = [
    "SecureInputValidator",
    "get_input_validator", 
    "quick_validate",
    "_demo_advanced_validator"
]